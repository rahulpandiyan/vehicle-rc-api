# Vehicle RC API

A small Flask service that turns an Indian registration number into structured
vehicle Registration Certificate (RC) data — owner, vehicle, insurance, fitness,
tax and RTO details — using [VahanX](https://vahanx.in) as the live source.

Use it as the backend for a mobile or web app. It ships with a versioned JSON
API, a batch endpoint, an OpenAPI document, in-memory caching, and a ready-made
web page at `/`.

> **Unofficial.** VahanX is a public website, not an official API. This project
> scrapes its RC result page. Markup changes or upstream rate limits can break
> lookups; there is intentionally no fallback provider.

---

## Contents

- [Features](#features)
- [Quickstart](#quickstart)
- [Authentication](#authentication)
- [API reference](#api-reference)
- [Response schema](#response-schema)
- [Errors](#errors)
- [Client examples](#client-examples)
- [Rate limits and caching](#rate-limits-and-caching)
- [Configuration](#configuration)
- [How the lookup works](#how-the-lookup-works)
- [Project structure](#project-structure)
- [Tests](#tests)
- [Deploy to Vercel](#deploy-to-vercel)

---

## Features

- **One endpoint, structured data** — grouped `owner`, `vehicle`, `registration`,
  `insurance` and `validity` objects instead of provider-specific field names.
- **Single and batch lookups** — one plate per request or up to 10 at once.
- **Versioned API** — `/api/v1/...`, so future changes do not break your app.
- **Machine-readable contract** — OpenAPI 3.1 at `/api/v1/openapi.json`.
- **Three auth styles** — `X-API-KEY`, `Authorization: Bearer`, or `?key=`.
- **CORS enabled** — call it directly from a browser or a mobile app.
- **Fast repeats** — results are cached for 1 hour and concurrent lookups for the
  same plate share one upstream request.
- **Built-in web UI** — a search page at `/` for checking plates manually.
- **Consistent errors** — every failure has a stable `error.code`.

---

## Quickstart

```bash
git clone https://github.com/rahulpandiyan/vehicle-rc-api.git
cd vehicle-rc-api

python -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

python Vehicle.py
```

The server starts on **http://localhost:5000**.

```bash
curl http://localhost:5000/api/v1/health
```

```json
{
  "status": "ok",
  "data": {
    "provider": "vahanx",
    "version": "1.0.0",
    "cache_entries": 0,
    "uptime_s": 1,
    "rate_limit_per_minute": 120,
    "batch_max": 10
  }
}
```

If port 5000 is busy:

```bash
PORT=5051 python Vehicle.py
```

Open **http://localhost:5000** for the bundled search page. It starts empty — no
plate is pre-filled and no lookup runs on load. A deep link such as
`/?plate=MH12AB1234` fills the input and performs that one lookup.

---

## Authentication

Every lookup endpoint requires an API key. Send it in **one** of these ways:

| Method | Example |
| --- | --- |
| Header (recommended) | `X-API-KEY: Vehicle-key_s0undw4v3` |
| Bearer token | `Authorization: Bearer Vehicle-key_s0undw4v3` |
| Query parameter | `?key=Vehicle-key_s0undw4v3` |

The key defaults to `Vehicle-key_s0undw4v3` for local development. **Set your own
key in production:**

```bash
export API_KEY="$(openssl rand -hex 24)"
python Vehicle.py
```

To accept several keys during a rotation, use a comma-separated list (this
overrides `API_KEY`):

```bash
export API_KEYS="old-key,new-key"
```

`GET /api/v1/health`, `GET /api/v1/openapi.json` and the web UI are public.

> The web UI needs the key in the browser, so anyone who can open `/` can read
> it. For a real product, keep the API behind your own session/auth layer and
> do not expose the key to end users.

---

## API reference

Base URL examples below use `http://localhost:5000`. On Vercel, use your
deployment URL.

### Look up one vehicle (path)

```http
GET /api/v1/vehicle/{registration}
```

```bash
curl -H "X-API-KEY: $API_KEY" \
  http://localhost:5000/api/v1/vehicle/MH12AB1234
```

Spaces and hyphens are ignored, so `mh-12-ab-1234` and `MH 12 AB 1234` work too.

### Look up one vehicle (query string)

```http
GET /api/v1/vehicle?registration={registration}&cache=yes
```

```bash
curl -H "X-API-KEY: $API_KEY" \
  "http://localhost:5000/api/v1/vehicle?registration=MH12AB1234"
```

`registration` also accepts the aliases `registration_number`, `query`,
`number`, `reg_no`, `search_term` and `quiry`.

### Look up one vehicle (JSON body)

```http
POST /api/v1/vehicle
Content-Type: application/json

{ "registration": "MH12AB1234", "cache": "no" }
```

```bash
curl -X POST http://localhost:5000/api/v1/vehicle \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: $API_KEY" \
  -d '{"registration": "MH12AB1234"}'
```

### Batch lookup

```http
POST /api/v1/vehicles/batch
Content-Type: application/json

{ "registrations": ["MH12AB1234", "DL01AB1234"] }
```

```bash
curl -X POST http://localhost:5000/api/v1/vehicles/batch \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: $API_KEY" \
  -d '{"registrations": ["MH12AB1234", "DL01AB1234"]}'
```

- Maximum **10** plates per request (configurable with `BATCH_MAX`).
- A single string is accepted instead of an array.
- The endpoint returns **HTTP 200** with a per-item `status`; one bad plate does
  not fail the whole batch.
- `status` at the top level is `success`, `partial` or `error`.

```json
{
  "status": "partial",
  "count": 2,
  "succeeded": 1,
  "failed": 1,
  "results": [
    {
      "registration_number": "MH12AB1234",
      "status": "success",
      "found": true,
      "data": { "...": "..." },
      "meta": { "...": "..." }
    },
    {
      "registration_number": "DL01AB1234",
      "status": "error",
      "found": false,
      "error": {
        "code": "VEHICLE_NOT_FOUND",
        "message": "VahanX has no record for DL01AB1234"
      }
    }
  ]
}
```

### Health

```http
GET /api/v1/health
```

Public. Returns provider, version, cache size, uptime and the active limits.

### OpenAPI document

```http
GET /api/v1/openapi.json
```

Public. Import it into Postman, Insomnia, Swagger UI, or generate a client.

### Legacy endpoint

`GET /vehicle?key=...&query=...` is kept for the bundled web page. It returns the
old flat shape (`Owner_Name`, `Model_Name`, `Insurance_Upto`, ...). New
integrations should use `/api/v1`.

---

## Response schema

Single lookups return:

```json
{
  "status": "success",
  "found": true,
  "data": {
    "registration_number": "MH12AB1234",
    "owner": {
      "name": "TEST OWNER",
      "serial": "Second Owner",
      "phone": "(+91)00000 00000",
      "address": "EXAMPLE ADDRESS, MAHARASHTRA"
    },
    "vehicle": {
      "maker": "HONDA MOTORCYCLE & SCOOTER INDIA",
      "model": "HONDA ACTIVA 6G",
      "class": "M-CYCLE/SCOOTER(2WN)",
      "fuel_type": "PETROL",
      "fuel_norms": "BHARAT STAGE VI",
      "chassis_number": "CHASSISXXXXXXXXXX",
      "engine_number": "ENGINEXXXXXXXXX",
      "cubic_capacity": "109",
      "seating_capacity": "2"
    },
    "registration": {
      "date": "01-Jan-2020",
      "rto": "EXAMPLE RTO, MAHARASHTRA",
      "city": "Mumbai Central - 400001"
    },
    "insurance": {
      "company": "EXAMPLE INSURANCE CO. LTD.",
      "policy_number": "POLICYXXXXXXXXX",
      "valid_upto": "01-Jan-2027"
    },
    "validity": {
      "insurance_upto": "01-Jan-2027",
      "fitness_upto": "01-Jan-2035",
      "tax_upto": "01-Jan-2035"
    }
  },
  "meta": {
    "source": "vahanx",
    "cached": false,
    "elapsed_ms": 4210,
    "fetched_at": "2026-10-25T17:00:00Z",
    "request_id": "195aa8c1eed4"
  }
}
```

Field notes:

- **All values in the examples above are fictional placeholders**, not a real
  vehicle record.
- Missing or `NA` fields are **omitted** rather than returned as `null`. Always
  treat every field as optional and render only what you receive.
- Dates are strings in `DD-Mon-YYYY` form (for example `01-Jan-2027`); parse them
  in your app if you need expiry calculations.
- `meta.cached` tells you whether this response came from the in-memory cache.
- `meta.request_id` is also returned as the `X-Request-ID` response header; log it
  when reporting a failed lookup.

| Object | Fields |
| --- | --- |
| `owner` | `name`, `serial`, `phone`, `address` |
| `vehicle` | `maker`, `model`, `class`, `fuel_type`, `fuel_norms`, `chassis_number`, `engine_number`, `cubic_capacity`, `seating_capacity` |
| `registration` | `date`, `rto`, `city`, `permit_type`, `blacklist_status`, `noc_details`, `financier` |
| `insurance` | `company`, `policy_number`, `valid_upto` |
| `validity` | `insurance_upto`, `fitness_upto`, `tax_upto` |

---

## Errors

Errors use a stable shape:

```json
{
  "status": "error",
  "found": false,
  "error": {
    "code": "VEHICLE_NOT_FOUND",
    "message": "No RC record was found for DL01AB1234.",
    "details": { "registration_number": "DL01AB1234" }
  },
  "meta": { "request_id": "a9a292f2eb58" }
}
```

| HTTP | `error.code` | Meaning |
| --- | --- | --- |
| `400` | `INVALID_REGISTRATION` | Not a valid Indian plate format |
| `400` | `MISSING_REGISTRATION` | No registration number supplied |
| `400` | `INVALID_BODY` / `MISSING_REGISTRATIONS` | Malformed batch request |
| `400` | `BATCH_TOO_LARGE` | More than `BATCH_MAX` plates |
| `401` | `UNAUTHORIZED` | Missing or invalid API key |
| `404` | `VEHICLE_NOT_FOUND` | VahanX has no record for that plate |
| `404` | `NOT_FOUND` | Unknown API route |
| `405` | `METHOD_NOT_ALLOWED` | Wrong HTTP method |
| `429` | `RATE_LIMITED` | You exceeded the local rate limit |
| `429` | `UPSTREAM_RATE_LIMITED` | VahanX is rate-limiting this server |
| `502` | `UPSTREAM_UNAVAILABLE` | VahanX is unreachable or changed |

For `429`, respect the `Retry-After` header (seconds).

---

## Client examples

### JavaScript / TypeScript

```ts
const BASE = "http://localhost:5000";
const API_KEY = process.env.VEHICLE_API_KEY!;

async function getVehicle(registration: string) {
  const res = await fetch(
    `${BASE}/api/v1/vehicle/${encodeURIComponent(registration)}`,
    { headers: { "X-API-KEY": API_KEY } }
  );
  const body = await res.json();
  if (!res.ok || body.status === "error") {
    throw new Error(body.error?.message ?? `Lookup failed (${res.status})`);
  }
  return body.data; // { registration_number, owner, vehicle, ... }
}
```

### Python

```python
import os
import requests

BASE = "http://localhost:5000"
HEADERS = {"X-API-KEY": os.environ["VEHICLE_API_KEY"]}

response = requests.get(
    f"{BASE}/api/v1/vehicle/MH12AB1234",
    headers=HEADERS,
    timeout=30,
)
payload = response.json()

if response.ok:
    vehicle = payload["data"]
    print(vehicle["owner"]["name"], vehicle["vehicle"]["model"])
else:
    print(payload["error"]["code"], payload["error"]["message"])
```

### Dart / Flutter

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

const baseUrl = 'http://localhost:5000';
const apiKey = String.fromEnvironment('VEHICLE_API_KEY');

Future<Map<String, dynamic>> getVehicle(String registration) async {
  final res = await http.get(
    Uri.parse('$baseUrl/api/v1/vehicle/$registration'),
    headers: {'X-API-KEY': apiKey},
  );

  final body = jsonDecode(res.body) as Map<String, dynamic>;
  if (res.statusCode != 200 || body['status'] == 'error') {
    throw Exception(body['error']?['message'] ?? 'Lookup failed');
  }
  return body['data'] as Map<String, dynamic>;
}
```

> On Android, `localhost` means the device. Use your machine's LAN IP
> (for example `http://192.168.1.4:5000`) or a deployed URL.

---

## Rate limits and caching

- **Local rate limit:** 120 requests per client IP per 60 seconds by default.
  Every lookup request counts once, including a batch. Set `RATE_LIMIT=0` to
  disable it.
- **Response cache:** successful lookups are cached in memory for 1 hour
  (`CACHE_TTL`). Pass `cache=no` to force a fresh upstream lookup.
- **Request coalescing:** concurrent lookups for the same plate share one
  VahanX request instead of hammering the upstream.
- **VahanX token reuse:** the session token is reused for 10 minutes
  (`VAHANX_TOKEN_TTL`), so only the first lookup pays the extra page fetch.
- **Serverless:** cache and rate-limit state are per instance. On Vercel, expect
  cold starts and per-instance limits.

Typical latency: ~4–6 s for a cold lookup, ~0.3 s once cached.

---

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_KEY` | `Vehicle-key_s0undw4v3` | Key accepted by the API and injected into the UI |
| `API_KEYS` | _(empty)_ | Comma-separated accepted keys; overrides `API_KEY` |
| `RATE_LIMIT` | `120` | Requests per IP per window; `0` disables |
| `RATE_WINDOW` | `60` | Rate-limit window in seconds |
| `BATCH_MAX` | `10` | Maximum plates per batch request |
| `CACHE_TTL` | `3600` | Vehicle-result cache lifetime in seconds |
| `VAHANX_BASE` | `https://vahanx.in` | VahanX base URL |
| `VAHANX_TIMEOUT` | `15` | Upstream request timeout in seconds |
| `VAHANX_TOKEN_TTL` | `600` | How long a VahanX session token is reused |
| `PORT` | `5000` | Local server port |
| `FLASK_DEBUG` | `0` | Set to `1` for Flask debug mode |

---

## How the lookup works

1. `GET https://vahanx.in/rc-search` and read the short-lived token from
   `window.VX_ST.rc`.
2. `GET https://vahanx.in/rc-search/{NUMBER}?t={token}`.
3. Parse the returned HTML label/value pairs into canonical fields.
4. Cache the result and map it to the grouped API response.

The token is cached per worker for 10 minutes. If it expires, the lookup
refreshes it once.

VahanX has no public API contract, so **do not rely on undocumented behaviour**.
If the upstream page changes, `_parse_vahanx_page()` and `_VAHANX_LABELS` in
`Vehicle.py` are the places to update. The offline parser tests cover both known
layouts.

---

## Project structure

```
vehicle-rc-api/
├── Vehicle.py          # Flask app, VahanX client, v1 API, OpenAPI spec
├── frontend.py         # Bundled web UI (INDEX_HTML)
├── api/index.py        # Vercel serverless entrypoint
├── vercel.json         # Rewrites all routes to the function
├── requirements.txt
├── tests/
│   └── test_vehicle.py # Offline tests (network mocked)
└── README.md
```

---

## Tests

The suite runs entirely offline — VahanX calls are mocked.

```bash
python -m unittest discover -s tests -v
```

It covers the parser, the legacy endpoint, the v1 single/batch endpoints, auth,
validation, caching flags, error envelopes, CORS, and the OpenAPI document.

---

## Deploy to Vercel

1. Push this folder to GitHub (or use this folder as the repository root).
2. Import the repository at [vercel.com](https://vercel.com/) and deploy.
3. Set `API_KEY` (and optionally `API_KEYS`) under
   **Project Settings → Environment Variables**.
4. Open the deployment URL:
   - `/` — web UI
   - `/api/v1/health` — health check
   - `/api/v1/vehicle/MH12AB1234` — lookup
   - `/api/v1/openapi.json` — OpenAPI document

CLI alternative:

```bash
npx vercel
npx vercel --prod
```

Serverless functions have a time limit. A cold VahanX lookup can take a few
seconds because it fetches the session page first; later requests reuse the
cached token.

---

## License and disclaimer

Use responsibly and only for lawful purposes. Vehicle data belongs to the
respective authorities and VahanX; this project is an unofficial client. Verify
critical information (insurance, fitness, ownership) against official records.
