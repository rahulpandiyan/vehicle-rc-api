"""Vehicle RC lookup API backed by VahanX.

Public surface
--------------
Web UI:      GET  /
Single:      GET  /api/v1/vehicle/<registration>
             GET  /api/v1/vehicle?registration=MH12AB1234
             POST /api/v1/vehicle        {"registration": "MH12AB1234"}
Health:      GET  /api/v1/health
OpenAPI:     GET  /api/v1/openapi.json
Legacy:      GET  /vehicle?query=...            (flat response, used by the UI)
"""

import hmac
import html as html_lib
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone

import requests
from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import HTTPException

from frontend import INDEX_HTML

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_VERSION = "1.0.0"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# API keys are optional. VahanX itself needs no key; this is only an optional
# gate for deployments that want to restrict who can call the wrapper.
_api_keys_env = os.environ.get("API_KEYS", "")
_api_key_env = os.environ.get("API_KEY", "")
if _api_keys_env:
    VALID_API_KEYS = {k.strip() for k in _api_keys_env.split(",") if k.strip()}
elif _api_key_env:
    VALID_API_KEYS = {_api_key_env.strip()}
else:
    VALID_API_KEYS = set()

# Open by default. Setting API_KEY / API_KEYS turns protection on; it can also
# be forced on or off explicitly with REQUIRE_API_KEY=1/0.
AUTH_REQUIRED = _env_flag("REQUIRE_API_KEY", default=bool(VALID_API_KEYS))
UI_API_KEY = _api_key_env.strip() or next(iter(VALID_API_KEYS), "")

# VahanX configuration (free, no provider API key required)
VAHANX_BASE = os.environ.get("VAHANX_BASE", "https://vahanx.in").rstrip("/")
VAHANX_TIMEOUT = int(os.environ.get("VAHANX_TIMEOUT", 15))
# Tokens are short-lived; caching avoids a slow page fetch on every lookup.
VAHANX_TOKEN_TTL = int(os.environ.get("VAHANX_TOKEN_TTL", 600))

CACHE_TTL = int(os.environ.get("CACHE_TTL", 3600))
LOOKUP_WAIT = VAHANX_TIMEOUT * 2 + 5

# Requests allowed per client IP per window. Set RATE_LIMIT=0 to disable.
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "120"))
RATE_WINDOW = int(os.environ.get("RATE_WINDOW", "60"))

VAHANX_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://vahanx.in/rc-search",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

# Matches standard Indian state plates (e.g. DL01AB1234, MH12A1) and Bharat (BH)
# series (e.g. 22BH1234AA).
REGEX = re.compile(
    r"^[A-Z]{2}\s?\d{1,2}\s?[A-Z]{0,3}\s?\d{1,4}$|^\d{2}\s?BH\s?\d{4}\s?[A-Z]{1,2}$",
    re.I,
)
REGEX_STRIP = re.compile(r"[\s-]+")

_local = threading.local()
_cache = {}
_cache_lock = threading.Lock()
_inflight = {}
_inflight_lock = threading.Lock()
_rate_hits = {}
_rate_lock = threading.Lock()

_boot = time.time()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class VehicleNotFound(ValueError):
    """Raised when VahanX has no record for the registration number."""


class InvalidRegistration(ValueError):
    """Raised when the registration number does not match an Indian plate."""


class VahanxUnavailable(RuntimeError):
    """Raised when VahanX cannot be reached or returns an unexpected status."""


class VahanxRateLimited(RuntimeError):
    """Raised when VahanX itself rate-limits the lookup."""

    def __init__(self, message: str, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


def _retry_after_value(exc, default: int = 60) -> str:
    """Use VahanX's Retry-After when present, otherwise a safe default."""
    try:
        return str(max(1, int(float(exc.retry_after))))
    except (TypeError, ValueError, AttributeError):
        return str(default)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normalize_number(number: str) -> str:
    return REGEX_STRIP.sub("", number or "").upper()


def is_valid_number(number: str) -> bool:
    return bool(REGEX.match(number.strip()))


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _request_id() -> str:
    rid = getattr(request, "_request_id", None)
    if rid is None:
        rid = uuid.uuid4().hex[:12]
        request._request_id = rid
    return rid


def _cache_get(key: str):
    with _cache_lock:
        hit = _cache.get(key)
        if hit and hit["ts"] + CACHE_TTL > time.time():
            return hit["data"]
        if hit:
            _cache.pop(key, None)
    return None


def _cache_set(key: str, data):
    with _cache_lock:
        _cache[key] = {"ts": time.time(), "data": data}


def _valid_value(value) -> bool:
    if value is None or value == "":
        return False
    return not (isinstance(value, str) and value.strip().upper() == "NA")


# Display labels used for the nested "vehicle_details" object.
_DETAIL_LABELS = [
    ("Owner Name", "owner_name"),
    ("Owner Serial No", "owner_serial"),
    ("Registration Number", "registration_number"),
    ("Model Name", "make"),
    ("Maker Model", "model"),
    ("Vehicle Class", "vehicle_class"),
    ("Fuel Type", "fuel_type"),
    ("Fuel Norms", "fuel_norms"),
    ("Registration Date", "registration_date"),
    ("Insurance Company", "insurance_company"),
    ("Insurance No", "insurance_no"),
    ("Insurance Expiry", "insurance_upto"),
    ("Insurance Upto", "insurance_upto"),
    ("Fitness Upto", "fitness_upto"),
    ("Tax Upto", "tax_upto"),
    ("Financer Name", "financier"),
    ("Registered RTO", "rto"),
    ("Address", "address"),
    ("City Name", "city"),
    ("Phone", "phone"),
    ("Chassis Number", "chassis"),
    ("Engine Number", "engine"),
    ("Cubic Capacity", "cubic_capacity"),
    ("Seating Capacity", "seating_capacity"),
    ("Permit Type", "permit_type"),
    ("Blacklist Status", "blacklist_status"),
    ("NOC Details", "noc_details"),
]


def _make_vehicle_result(number: str, details: dict) -> dict:
    """Convert canonical vehicle fields into the legacy flat response shape."""
    nested = {}
    for label, key in _DETAIL_LABELS:
        value = details.get(key)
        if _valid_value(value):
            nested[label] = value

    result = {
        "status": "success",
        "found": True,
        "source": "vahanx",
        "Registration_Number": details.get("registration_number") or number,
        "Make_Name": details.get("make"),
        "Maker_Name": details.get("make"),
        "Model_Name": details.get("model"),
        "Vehicle_Class": details.get("vehicle_class"),
        "Fuel_Type": details.get("fuel_type"),
        "Fuel_Norms": details.get("fuel_norms"),
        "Registration_Date": details.get("registration_date"),
        "Owner_Name": details.get("owner_name"),
        "Owner_Serial_No": details.get("owner_serial"),
        "Chassis_Number": details.get("chassis"),
        "Engine_Number": details.get("engine"),
        "Insurance_Company": details.get("insurance_company"),
        "Insurance_No": details.get("insurance_no"),
        "Insurance_Upto": details.get("insurance_upto"),
        "Insurance_Expiry": details.get("insurance_upto"),
        "Fitness_Upto": details.get("fitness_upto"),
        "Tax_Upto": details.get("tax_upto"),
        "Registered_RTO": details.get("rto"),
        "City_Name": details.get("city"),
        "Phone": details.get("phone"),
        "Address": details.get("address"),
        "Cubic_Capacity": details.get("cubic_capacity"),
        "Seating_Capacity": details.get("seating_capacity"),
        "Permit_Type": details.get("permit_type"),
        "Blacklist_Status": details.get("blacklist_status"),
        "NOC_Details": details.get("noc_details"),
        "Financer_Name": details.get("financier"),
        "vehicle_details": nested,
    }
    return {k: v for k, v in result.items() if _valid_value(v)}


def _prune(value):
    """Recursively drop None/empty/NA leaves and empty containers."""
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            item = _prune(item)
            if isinstance(item, dict) and not item:
                continue
            if _valid_value(item):
                cleaned[key] = item
        return cleaned
    return value


def _pick(result: dict, *keys):
    for key in keys:
        value = result.get(key)
        if _valid_value(value):
            return value
    return None


def public_vehicle(result: dict) -> dict:
    """Map the legacy flat record to a stable, grouped v1 payload."""
    return _prune({
        "registration_number": _pick(result, "Registration_Number"),
        "owner": {
            "name": _pick(result, "Owner_Name"),
            "serial": _pick(result, "Owner_Serial_No"),
            "phone": _pick(result, "Phone"),
            "address": _pick(result, "Address"),
        },
        "vehicle": {
            "maker": _pick(result, "Make_Name", "Maker_Name"),
            "model": _pick(result, "Model_Name"),
            "class": _pick(result, "Vehicle_Class"),
            "fuel_type": _pick(result, "Fuel_Type"),
            "fuel_norms": _pick(result, "Fuel_Norms"),
            "chassis_number": _pick(result, "Chassis_Number"),
            "engine_number": _pick(result, "Engine_Number"),
            "cubic_capacity": _pick(result, "Cubic_Capacity"),
            "seating_capacity": _pick(result, "Seating_Capacity"),
        },
        "registration": {
            "date": _pick(result, "Registration_Date"),
            "rto": _pick(result, "Registered_RTO"),
            "city": _pick(result, "City_Name"),
            "permit_type": _pick(result, "Permit_Type"),
            "blacklist_status": _pick(result, "Blacklist_Status"),
            "noc_details": _pick(result, "NOC_Details"),
            "financier": _pick(result, "Financer_Name"),
        },
        "insurance": {
            "company": _pick(result, "Insurance_Company"),
            "policy_number": _pick(result, "Insurance_No"),
            "valid_upto": _pick(result, "Insurance_Upto", "Insurance_Expiry"),
        },
        "validity": {
            "insurance_upto": _pick(result, "Insurance_Upto", "Insurance_Expiry"),
            "fitness_upto": _pick(result, "Fitness_Upto"),
            "tax_upto": _pick(result, "Tax_Upto"),
        },
    })


# ---------------------------------------------------------------------------
# VahanX lookup
# ---------------------------------------------------------------------------
def _vahanx_session() -> requests.Session:
    sess = getattr(_local, "vahanx_sess", None)
    if sess is None:
        sess = requests.Session()
        sess.headers.update(VAHANX_HEADERS)
        _local.vahanx_sess = sess
    return sess


def _vahanx_session_token(sess: requests.Session, force: bool = False) -> str:
    now = time.time()
    cached = getattr(_local, "vahanx_token", None)
    cached_ts = getattr(_local, "vahanx_token_ts", 0.0)
    if not force and cached and cached_ts + VAHANX_TOKEN_TTL > now:
        return cached

    resp = sess.get(f"{VAHANX_BASE}/rc-search", timeout=VAHANX_TIMEOUT)
    if resp.status_code == 429:
        raise VahanxRateLimited(
            "VahanX rate limit reached, try again later",
            retry_after=resp.headers.get("Retry-After"),
        )
    if resp.status_code != 200:
        raise VahanxUnavailable(
            f"VahanX returned HTTP {resp.status_code} while creating a session"
        )
    match = re.search(r'window\.VX_ST\s*=\s*\{.*?rc:\s*"([^"]+)"', resp.text, re.S)
    if not match:
        raise VahanxUnavailable(
            "VahanX session token not found (page structure may have changed)"
        )

    _local.vahanx_token = match.group(1)
    _local.vahanx_token_ts = now
    return _local.vahanx_token


def _strip_html(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment or "")
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


# Labels rendered on the VahanX RC result page.
_VAHANX_LABELS = {
    "Owner Name", "Owner Serial No", "Registration Number", "Model Name",
    "Maker Model", "Vehicle Class", "Fuel Type", "Fuel Norms",
    "Registration Date", "Insurance Company", "Insurance No", "Insurance Expiry",
    "Insurance Upto", "Fitness Upto", "Tax Upto", "Financer Name",
    "Registered RTO", "Address", "City Name", "Phone", "Chassis Number",
    "Engine Number", "Cubic Capacity", "Seating Capacity", "Permit Type",
    "Blacklist Status", "NOC Details",
}


def _parse_vahanx_page(page: str) -> dict:
    """Extract label/value pairs from both VahanX card layouts.

    Anchoring each search on an exact label avoids pairing a value with a
    neighbouring card's label (the page contains several label-like spans).
    """
    values = {}
    for label in _VAHANX_LABELS:
        escaped = re.escape(label)

        # Layout 1: <span>LABEL</span> <p>VALUE</p>
        match = re.search(
            r"<span[^>]*>\s*" + escaped + r"\s*</span>\s*"
            r"<p[^>]*>((?:(?!</p>).)*?)</p>",
            page, re.S | re.I,
        )

        # Layout 2: <div class="hrcd-cardbody"><p>VALUE</p><span>LABEL</span></div>
        if not match:
            match = re.search(
                r"<p[^>]*>((?:(?!</p>).)*?)</p>\s*"
                r"<span[^>]*>\s*" + escaped + r"\s*</span>",
                page, re.S | re.I,
            )

        if match:
            value = _strip_html(match.group(1))
            if value:
                values[label] = value

    return values


def _vahanx_to_canonical(values: dict, number: str) -> dict:
    return {
        "registration_number": values.get("Registration Number") or number,
        "owner_name": values.get("Owner Name"),
        "owner_serial": values.get("Owner Serial No"),
        "make": values.get("Model Name"),
        "model": values.get("Maker Model"),
        "vehicle_class": values.get("Vehicle Class"),
        "fuel_type": values.get("Fuel Type"),
        "fuel_norms": values.get("Fuel Norms"),
        "registration_date": values.get("Registration Date"),
        "insurance_company": values.get("Insurance Company"),
        "insurance_no": values.get("Insurance No"),
        "insurance_upto": values.get("Insurance Upto") or values.get("Insurance Expiry"),
        "fitness_upto": values.get("Fitness Upto"),
        "tax_upto": values.get("Tax Upto"),
        "rto": values.get("Registered RTO"),
        "chassis": values.get("Chassis Number"),
        "engine": values.get("Engine Number"),
        "city": values.get("City Name"),
        "phone": values.get("Phone"),
        "address": values.get("Address"),
        "cubic_capacity": values.get("Cubic Capacity"),
        "seating_capacity": values.get("Seating Capacity"),
        "permit_type": values.get("Permit Type"),
        "blacklist_status": values.get("Blacklist Status"),
        "noc_details": values.get("NOC Details"),
        "financier": values.get("Financer Name"),
    }


def vahanx_lookup(number: str) -> dict:
    last_error = None
    for attempt in range(2):
        sess = _vahanx_session()
        try:
            token = _vahanx_session_token(sess, force=attempt > 0)
            resp = sess.get(
                f"{VAHANX_BASE}/rc-search/{number}",
                params={"t": token},
                timeout=VAHANX_TIMEOUT,
                allow_redirects=True,
            )
        except VahanxRateLimited:
            raise
        except (VahanxUnavailable, requests.exceptions.RequestException) as exc:
            last_error = exc
            _local.vahanx_sess = None
            _local.vahanx_token = None
            continue

        if resp.status_code == 429:
            raise VahanxRateLimited(
                "VahanX rate limit reached, try again later",
                retry_after=resp.headers.get("Retry-After"),
            )
        if resp.status_code != 200:
            last_error = VahanxUnavailable(f"VahanX returned HTTP {resp.status_code}")
            _local.vahanx_sess = None
            _local.vahanx_token = None
            continue

        values = _parse_vahanx_page(resp.text)
        if values.get("Registration Number") and (
            values.get("Model Name") or values.get("Maker Model")
        ):
            return _make_vehicle_result(
                number, _vahanx_to_canonical(values, number)
            )

        # A missing record leaves only the generic RTO card, so refresh the
        # session once (token may have expired) before declaring "not found".
        _local.vahanx_token = None

    if last_error is not None:
        raise VahanxUnavailable(f"VahanX lookup failed: {last_error}")
    raise VehicleNotFound(f"VahanX has no record for {number}")


def lookup(number: str, use_cache: bool = True):
    norm = normalize_number(number)
    if not is_valid_number(norm):
        raise InvalidRegistration("Invalid Indian vehicle registration number")

    key = norm
    if use_cache:
        hit = _cache_get(key)
        if hit is not None:
            return hit, True

    with _inflight_lock:
        holder = _inflight.get(key)
        if holder is None:
            holder = {
                "event": threading.Event(),
                "result": None,
                "owner": threading.get_ident(),
            }
            _inflight[key] = holder
            am_owner = True
        else:
            am_owner = False

    if not am_owner:
        holder["event"].wait(timeout=LOOKUP_WAIT)
        res = holder["result"]
        if isinstance(res, Exception):
            raise res
        return res, False

    try:
        result = vahanx_lookup(norm)
        holder["result"] = result
    except Exception as exc:
        holder["result"] = exc
        raise
    finally:
        holder["event"].set()
        with _inflight_lock:
            _inflight.pop(key, None)

    if use_cache:
        _cache_set(key, result)
    return result, False


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def is_authorized() -> bool:
    if not AUTH_REQUIRED:
        return True

    provided_key = request.args.get("key") or request.args.get("api_key")

    if not provided_key:
        provided_key = request.headers.get("X-API-KEY")
    if not provided_key and request.headers.get("Authorization"):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:].strip()

    if not provided_key and request.is_json:
        body = request.get_json(silent=True) or {}
        provided_key = body.get("key") or body.get("api_key")

    if not provided_key and request.form:
        provided_key = request.form.get("key") or request.form.get("api_key")

    if not provided_key:
        return False

    provided_key = provided_key.strip()
    return any(hmac.compare_digest(provided_key, key) for key in VALID_API_KEYS)


# ---------------------------------------------------------------------------
# Request helpers
# ---------------------------------------------------------------------------
_LOOKUP_KEYS = (
    "registration",
    "registration_number",
    "query",
    "number",
    "reg_no",
    "search_term",
    "quiry",
)


def _request_payload() -> dict:
    """Merge body and query parameters; query string wins on conflicts."""
    payload = {}
    if request.method == "POST":
        if request.is_json:
            body = request.get_json(silent=True)
            if isinstance(body, dict):
                payload.update(body)
        if request.form:
            payload.update(request.form.to_dict())
    payload.update(request.args.to_dict())
    return payload


def _extract_number(payload: dict):
    for key in _LOOKUP_KEYS:
        value = payload.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


def _extract_use_cache(payload: dict) -> bool:
    value = payload.get("cache")
    if value is None:
        return True
    return str(value).strip().lower() not in {"no", "false", "0", "off"}


def _rate_limit_retry_after():
    """Return seconds to wait when the caller is over the limit, else None."""
    if RATE_LIMIT <= 0:
        return None

    forwarded = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded.split(",")[0].strip() or request.remote_addr or "unknown"
    now = time.time()

    with _rate_lock:
        # Keep the dict from growing without bound on long-running instances.
        if len(_rate_hits) > 5000:
            for ip in [ip for ip, hits in _rate_hits.items() if not hits]:
                _rate_hits.pop(ip, None)

        hits = [ts for ts in _rate_hits.get(client_ip, []) if ts > now - RATE_WINDOW]
        if len(hits) >= RATE_LIMIT:
            _rate_hits[client_ip] = hits
            return max(1, int(RATE_WINDOW - (now - hits[0])) + 1)
        hits.append(now)
        _rate_hits[client_ip] = hits
    return None


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------
def _meta(result: dict, cached: bool, elapsed_ms: int, request_id: str = None) -> dict:
    return {
        "source": result.get("source", "vahanx"),
        "cached": cached,
        "elapsed_ms": elapsed_ms,
        "fetched_at": _utc_now(),
        "request_id": request_id or _request_id(),
    }


def _v1_error(status: int, code: str, message: str, **details):
    payload = {
        "status": "error",
        "found": False,
        "error": {"code": code, "message": message},
        "meta": {"request_id": _request_id()},
    }
    if details:
        payload["error"]["details"] = details
    response = jsonify(payload)
    response.status_code = status
    return response


def _error_from_exception(exc: Exception, norm: str):
    if isinstance(exc, VehicleNotFound):
        return _v1_error(
            404, "VEHICLE_NOT_FOUND",
            f"No RC record was found for {norm}.", registration_number=norm,
        )
    if isinstance(exc, InvalidRegistration):
        return _v1_error(400, "INVALID_REGISTRATION", str(exc))
    if isinstance(exc, VahanxRateLimited):
        response = _v1_error(
            429, "UPSTREAM_RATE_LIMITED",
            "The upstream data source is rate-limiting requests. Try again shortly.",
        )
        response.headers["Retry-After"] = _retry_after_value(exc)
        return response
    return _v1_error(
        502, "UPSTREAM_UNAVAILABLE",
        "The upstream data source is unavailable right now. Try again shortly.",
    )


def _v1_lookup_response(number: str, use_cache: bool):
    started = time.perf_counter()
    norm = normalize_number(str(number or ""))
    try:
        if not is_valid_number(norm):
            raise InvalidRegistration(
                f"'{number}' is not a valid Indian registration number."
            )
        result, cached = lookup(norm, use_cache)
    except (VehicleNotFound, InvalidRegistration, VahanxRateLimited) as exc:
        return _error_from_exception(exc, norm)
    except Exception as exc:  # noqa: BLE001 - reported as a 502 to the caller
        app.logger.warning("VahanX lookup failed for %s: %s", norm, exc)
        return _error_from_exception(exc, norm)

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return jsonify({
        "status": "success",
        "found": True,
        "data": public_vehicle(result),
        "meta": _meta(result, cached, elapsed_ms),
    })


def _openapi_spec() -> dict:
    lookup_security = [
        {"ApiKeyAuth": []},
        {"BearerAuth": []},
        {"QueryKey": []},
    ]
    if not AUTH_REQUIRED:
        # An empty requirement means the endpoint can be called without a key.
        lookup_security.append({})
    vehicle_schema = {
        "type": "object",
        "properties": {
            "registration_number": {"type": "string", "example": "MH12AB1234"},
            "owner": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "serial": {"type": "string"},
                    "phone": {"type": "string"},
                    "address": {"type": "string"},
                },
            },
            "vehicle": {
                "type": "object",
                "properties": {
                    "maker": {"type": "string"},
                    "model": {"type": "string"},
                    "class": {"type": "string"},
                    "fuel_type": {"type": "string"},
                    "fuel_norms": {"type": "string"},
                    "chassis_number": {"type": "string"},
                    "engine_number": {"type": "string"},
                    "cubic_capacity": {"type": "string"},
                    "seating_capacity": {"type": "string"},
                },
            },
            "registration": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "example": "01-Jan-2020"},
                    "rto": {"type": "string"},
                    "city": {"type": "string"},
                    "permit_type": {"type": "string"},
                    "blacklist_status": {"type": "string"},
                    "noc_details": {"type": "string"},
                    "financier": {"type": "string"},
                },
            },
            "insurance": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "policy_number": {"type": "string"},
                    "valid_upto": {"type": "string", "example": "01-Jan-2027"},
                },
            },
            "validity": {
                "type": "object",
                "properties": {
                    "insurance_upto": {"type": "string"},
                    "fitness_upto": {"type": "string"},
                    "tax_upto": {"type": "string"},
                },
            },
        },
    }
    meta_schema = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "example": "vahanx"},
            "cached": {"type": "boolean"},
            "elapsed_ms": {"type": "integer"},
            "fetched_at": {"type": "string", "format": "date-time"},
            "request_id": {"type": "string"},
        },
    }
    error_schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "const": "error"},
            "found": {"type": "boolean", "const": False},
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {"type": "object"},
                },
                "required": ["code", "message"],
            },
            "meta": {"$ref": "#/components/schemas/Meta"},
        },
    }
    success_schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "const": "success"},
            "found": {"type": "boolean", "const": True},
            "data": {"$ref": "#/components/schemas/Vehicle"},
            "meta": {"$ref": "#/components/schemas/Meta"},
        },
    }
    single_responses = {
        "200": {
            "description": "Vehicle record found.",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LookupSuccess"}}},
        },
        "400": {"description": "Invalid registration number.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
        "401": {"description": "Missing or invalid API key.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
        "404": {"description": "No record for that registration number.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
        "429": {"description": "Local rate limit or upstream rate limit.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
        "502": {"description": "VahanX is unavailable.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
    }
    registration_param = {
        "name": "registration",
        "in": "query",
        "required": True,
        "schema": {"type": "string"},
        "example": "MH12AB1234",
        "description": "Registration number. Spaces and hyphens are ignored.",
    }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Vehicle RC API",
            "version": API_VERSION,
            "description": (
                "Indian vehicle Registration Certificate lookup backed by VahanX. "
                "No API key is required by default. If the deployment enables "
                "protection, send the key as X-API-KEY, a Bearer token, or a "
                "?key= query parameter."
            ),
        },
        "servers": [{"url": "/"}],
        "security": lookup_security,
        "tags": [
            {"name": "Lookup"},
            {"name": "System"},
        ],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-KEY"},
                "BearerAuth": {"type": "http", "scheme": "bearer"},
                "QueryKey": {"type": "apiKey", "in": "query", "name": "key"},
            },
            "schemas": {
                "Vehicle": vehicle_schema,
                "Meta": meta_schema,
                "Error": error_schema,
                "LookupSuccess": success_schema,
            },
        },
        "paths": {
            "/api/v1/vehicle/{registration}": {
                "get": {
                    "tags": ["Lookup"],
                    "summary": "Look up one vehicle",
                    "operationId": "getVehicle",
                    "parameters": [
                        {
                            "name": "registration",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "example": "MH12AB1234",
                        },
                        {
                            "name": "cache",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "enum": ["yes", "no"], "default": "yes"},
                        },
                    ],
                    "responses": single_responses,
                }
            },
            "/api/v1/vehicle": {
                "get": {
                    "tags": ["Lookup"],
                    "summary": "Look up one vehicle by query string",
                    "operationId": "getVehicleByQuery",
                    "parameters": [
                        registration_param,
                        {
                            "name": "cache",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "enum": ["yes", "no"], "default": "yes"},
                        },
                    ],
                    "responses": single_responses,
                },
                "post": {
                    "tags": ["Lookup"],
                    "summary": "Look up one vehicle with a JSON body",
                    "operationId": "postVehicle",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["registration"],
                                    "properties": {
                                        "registration": {"type": "string", "example": "MH12AB1234"},
                                        "cache": {"type": "string", "enum": ["yes", "no"]},
                                    },
                                }
                            }
                        },
                    },
                    "responses": single_responses,
                },
            },
            "/api/v1/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "Service health",
                    "operationId": "getHealth",
                    "security": [],
                    "responses": {
                        "200": {
                            "description": "Service is up.",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            },
            "/api/v1/openapi.json": {
                "get": {
                    "tags": ["System"],
                    "summary": "This OpenAPI document",
                    "operationId": "getOpenApi",
                    "security": [],
                    "responses": {"200": {"description": "OpenAPI 3.1 document."}},
                }
            },
        },
    }


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
class StripVercelPrefixMiddleware:
    """Normalizes PATH_INFO so Flask routes the actual requested path on Vercel."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_FORWARDED_PATH")
            or environ.get("HTTP_X_ORIGINAL_URI")
        )
        if matched_path:
            clean_path = matched_path.split("?")[0].strip()
            if clean_path and not clean_path.startswith("/api/index"):
                environ["PATH_INFO"] = clean_path
        else:
            path = environ.get("PATH_INFO", "")
            for prefix in ["/api/index.py", "/api/index"]:
                if path.startswith(prefix):
                    path = path[len(prefix):] or "/"
                    environ["PATH_INFO"] = path
                    break
        return self.wsgi_app(environ, start_response)


app.wsgi_app = StripVercelPrefixMiddleware(app.wsgi_app)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, X-API-KEY"
    )
    response.headers["Access-Control-Expose-Headers"] = "X-Request-ID, Retry-After"
    response.headers["Access-Control-Max-Age"] = "86400"
    response.headers["X-Request-ID"] = _request_id()
    return response


@app.errorhandler(HTTPException)
def handle_http_error(exc):
    if request.path.startswith(("/api", "/vehicle")):
        codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
        return _v1_error(
            exc.code or 500,
            codes.get(exc.code, "HTTP_ERROR"),
            exc.description or "Request failed.",
        )
    return exc


def _reject_if_limited():
    retry_after = _rate_limit_retry_after()
    if retry_after is None:
        return None
    response = _v1_error(
        429, "RATE_LIMITED",
        "Too many requests. Slow down and try again shortly.",
    )
    response.headers["Retry-After"] = str(retry_after)
    return response


def _reject_if_unauthorized():
    if is_authorized():
        return None
    return _v1_error(
        401, "UNAUTHORIZED",
        "Missing or invalid API key. Send X-API-KEY, Authorization: Bearer <key>, "
        "or ?key=<key>.",
    )


# ---------------------------------------------------------------------------
# Routes: UI and legacy API
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    page = INDEX_HTML.replace(
        "__API_KEY__", html_lib.escape(UI_API_KEY, quote=True)
    )
    return Response(page, mimetype="text/html")


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return "", 204


@app.route("/api", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/index", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/index.py", methods=["GET", "POST", "OPTIONS"])
def index():
    if request.method == "OPTIONS":
        return "", 204

    # Vercel may rewrite a vehicle lookup to the index function; auto-dispatch
    # when the vehicle parameter is present and the original path is missing.
    payload = _request_payload()
    if _extract_number(payload):
        return vehicle_info()

    return jsonify({
        "status": "ok",
        "message": "VEHICLE API WORKING",
        "name": "Vehicle RC API",
        "version": API_VERSION,
        "provider": "vahanx",
        "auth_required": AUTH_REQUIRED,
        "ui": "/",
        "openapi": "/api/v1/openapi.json",
        "endpoints": {
            "single": "/api/v1/vehicle/{registration}",
            "query": "/api/v1/vehicle?registration={registration}",
            "health": "/api/v1/health",
            "legacy": "/vehicle?query={registration}",
        },
    }), 200


@app.route("/vehicle", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/vehicle", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/index/vehicle", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/index.py/vehicle", methods=["GET", "POST", "OPTIONS"])
def vehicle_info():
    """Legacy flat response kept for the bundled web UI."""
    if request.method == "OPTIONS":
        return "", 204

    limited = _reject_if_limited()
    if limited is not None:
        return limited

    if not is_authorized():
        return jsonify({
            "status": "error",
            "error": "Unauthorized",
            "message": (
                "Invalid or missing API key. Usage: "
                "/vehicle?key={api_key}&query={vehicle_number}"
            ),
        }), 401

    payload = _request_payload()
    number = _extract_number(payload)
    use_cache = _extract_use_cache(payload)

    if not number:
        return jsonify({
            "status": "error",
            "error": "Missing search term",
            "message": (
                "Missing 'query' parameter. Usage: /vehicle?query={vehicle_number}"
            ),
        }), 400

    norm = normalize_number(number)
    if not is_valid_number(norm):
        return jsonify({
            "status": "error",
            "error": "Invalid registration number",
            "message": (
                f"'{number}' is not a valid Indian vehicle registration "
                "number format."
            ),
        }), 400

    try:
        result, _cached = lookup(norm, use_cache)
    except VehicleNotFound as exc:
        return jsonify({
            "status": "error",
            "found": False,
            "error": "Vehicle not found",
            "message": str(exc),
        }), 404
    except ValueError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    except VahanxRateLimited as exc:
        response = jsonify({
            "status": "error",
            "found": False,
            "error": "Upstream rate limit",
            "message": str(exc),
        })
        response.status_code = 429
        response.headers["Retry-After"] = _retry_after_value(exc)
        return response
    except Exception as exc:
        app.logger.warning("VahanX lookup failed for %s: %s", norm, exc)
        payload = {
            "status": "error",
            "found": False,
            "error": "Vehicle lookup failed",
            "message": "VahanX is unavailable right now. Please try again.",
        }
        if app.debug:
            payload["detail"] = str(exc)
        return jsonify(payload), 502

    return jsonify(result)


@app.route("/health")
@app.route("/api/health")
@app.route("/api/index/health")
@app.route("/api/index.py/health")
def health():
    return jsonify({
        "status": "ok",
        "provider": "vahanx",
        "cache_entries": len(_cache),
        "uptime_s": int(time.time() - _boot),
    })


# ---------------------------------------------------------------------------
# Routes: v1 API
# ---------------------------------------------------------------------------
@app.route("/api/v1/health", methods=["GET"])
def v1_health():
    return jsonify({
        "status": "ok",
        "data": {
            "provider": "vahanx",
            "version": API_VERSION,
            "auth_required": AUTH_REQUIRED,
            "cache_entries": len(_cache),
            "uptime_s": int(time.time() - _boot),
            "rate_limit_per_minute": RATE_LIMIT,
        },
        "meta": {"request_id": _request_id()},
    })


@app.route("/api/v1/openapi.json", methods=["GET"])
def v1_openapi():
    return jsonify(_openapi_spec())


@app.route("/api/v1/vehicle/<path:number>", methods=["GET"])
def v1_vehicle_path(number):
    limited = _reject_if_limited()
    if limited is not None:
        return limited
    unauthorized = _reject_if_unauthorized()
    if unauthorized is not None:
        return unauthorized
    return _v1_lookup_response(number, _extract_use_cache(request.args))


@app.route("/api/v1/vehicle", methods=["GET", "POST", "OPTIONS"])
def v1_vehicle():
    if request.method == "OPTIONS":
        return "", 204

    limited = _reject_if_limited()
    if limited is not None:
        return limited
    unauthorized = _reject_if_unauthorized()
    if unauthorized is not None:
        return unauthorized

    payload = _request_payload()
    number = _extract_number(payload)
    if not number:
        return _v1_error(
            400, "MISSING_REGISTRATION",
            "Provide a registration number via ?registration=, the JSON body, "
            "or the path /api/v1/vehicle/<registration>.",
        )
    return _v1_lookup_response(number, _extract_use_cache(payload))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0").strip().lower() in {
        "1", "true", "yes", "on",
    }
    print(f"Vehicle RC lookup running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
