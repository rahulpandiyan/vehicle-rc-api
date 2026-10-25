"""Offline tests for the VahanX-only vehicle API (no network required).

Run with:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Vehicle  # noqa: E402


SAMPLE = Vehicle._make_vehicle_result("MH12AB1234", {
    "registration_number": "MH12AB1234",
    "owner_name": "TEST OWNER",
    "owner_serial": "Second Owner",
    "make": "HONDA MOTORCYCLE & SCOOTER INDIA",
    "model": "HONDA ACTIVA 6G",
    "vehicle_class": "M-CYCLE/SCOOTER(2WN)",
    "fuel_type": "PETROL",
    "registration_date": "01-Jan-2020",
    "insurance_upto": "01-Jan-2027",
    "fitness_upto": "01-Jan-2035",
    "rto": "EXAMPLE RTO, MAHARASHTRA",
})


class ApiTests(unittest.TestCase):
    def setUp(self):
        Vehicle._cache.clear()
        self.client = Vehicle.app.test_client()

    def tearDown(self):
        Vehicle._cache.clear()

    def test_lookup_success(self):
        with mock.patch.object(Vehicle, "vahanx_lookup", return_value=SAMPLE):
            response = self.client.get(
                "/vehicle?key=Vehicle-key_s0undw4v3&query=MH12AB1234&cache=no"
            )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["found"])
        self.assertEqual(data["source"], "vahanx")
        self.assertEqual(data["Registration_Number"], "MH12AB1234")
        self.assertEqual(data["Model_Name"], "HONDA ACTIVA 6G")
        self.assertEqual(data["Owner_Name"], "TEST OWNER")
        self.assertIn("Owner Name", data["vehicle_details"])

    def test_plate_is_normalized(self):
        with mock.patch.object(Vehicle, "vahanx_lookup", return_value=SAMPLE) as lookup:
            response = self.client.get(
                "/vehicle?key=Vehicle-key_s0undw4v3&query=mh-12-ab-1234&cache=no"
            )
        self.assertEqual(response.status_code, 200)
        lookup.assert_called_once_with("MH12AB1234")

    def test_alias_parameter_works(self):
        with mock.patch.object(Vehicle, "vahanx_lookup", return_value=SAMPLE):
            response = self.client.get(
                "/vehicle?key=Vehicle-key_s0undw4v3&number=MH12AB1234&cache=no"
            )
        self.assertEqual(response.status_code, 200)

    def test_not_found_returns_404(self):
        with mock.patch.object(
            Vehicle, "vahanx_lookup",
            side_effect=Vehicle.VehicleNotFound("VahanX has no record for DL01AB1234"),
        ):
            response = self.client.get(
                "/vehicle?key=Vehicle-key_s0undw4v3&query=DL01AB1234&cache=no"
            )
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data["found"])
        self.assertEqual(data["error"], "Vehicle not found")

    def test_provider_failure_returns_502(self):
        with mock.patch.object(
            Vehicle, "vahanx_lookup", side_effect=RuntimeError("boom")
        ):
            response = self.client.get(
                "/vehicle?key=Vehicle-key_s0undw4v3&query=MH12AB1234&cache=no"
            )
        self.assertEqual(response.status_code, 502)
        data = response.get_json()
        self.assertFalse(data["found"])
        self.assertEqual(data["error"], "Vehicle lookup failed")

    def test_missing_key_returns_401(self):
        response = self.client.get("/vehicle?query=MH12AB1234")
        self.assertEqual(response.status_code, 401)

    def test_invalid_registration_returns_400(self):
        response = self.client.get(
            "/vehicle?key=Vehicle-key_s0undw4v3&query=NOT-A-PLATE"
        )
        self.assertEqual(response.status_code, 400)

    def test_health(self):
        data = self.client.get("/health").get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["provider"], "vahanx")

    def test_home_serves_ui(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        body = response.get_data(as_text=True)
        self.assertIn("Vehicle RC Lookup", body)
        self.assertIn('name="api-key"', body)
        self.assertNotIn("__API_KEY__", body)

    def test_home_has_no_prefilled_plate(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="empty-state"', body)
        self.assertIn('placeholder="Enter registration number"', body)
        self.assertNotIn('value="MH12AB1234"', body)
        self.assertNotIn("data-plate=", body)


class V1ApiTests(unittest.TestCase):
    AUTH = {"X-API-KEY": "Vehicle-key_s0undw4v3"}

    def setUp(self):
        Vehicle._cache.clear()
        self.client = Vehicle.app.test_client()

    def tearDown(self):
        Vehicle._cache.clear()

    def test_path_lookup_returns_grouped_payload(self):
        with mock.patch.object(Vehicle, "vahanx_lookup", return_value=SAMPLE):
            response = self.client.get(
                "/api/v1/vehicle/mh-12-ab-1234?cache=no", headers=self.AUTH
            )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["found"])
        self.assertEqual(data["data"]["registration_number"], "MH12AB1234")
        self.assertEqual(data["data"]["owner"]["name"], "TEST OWNER")
        self.assertEqual(data["data"]["vehicle"]["model"], "HONDA ACTIVA 6G")
        self.assertEqual(data["data"]["insurance"]["valid_upto"], "01-Jan-2027")
        self.assertEqual(data["meta"]["source"], "vahanx")
        self.assertFalse(data["meta"]["cached"])
        self.assertIn("request_id", data["meta"])
        self.assertNotIn("Owner_Name", data["data"])

    def test_query_lookup_with_bearer_token(self):
        with mock.patch.object(Vehicle, "vahanx_lookup", return_value=SAMPLE):
            response = self.client.get(
                "/api/v1/vehicle?registration=MH12AB1234&cache=no",
                headers={"Authorization": "Bearer Vehicle-key_s0undw4v3"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["owner"]["name"], "TEST OWNER")

    def test_post_lookup_with_json(self):
        with mock.patch.object(Vehicle, "vahanx_lookup", return_value=SAMPLE):
            response = self.client.post(
                "/api/v1/vehicle",
                json={"registration": "MH12AB1234", "cache": "no"},
                headers=self.AUTH,
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["registration_number"], "MH12AB1234")

    def test_cached_flag_is_reported(self):
        with mock.patch.object(Vehicle, "vahanx_lookup", return_value=SAMPLE):
            self.client.get("/api/v1/vehicle/MH12AB1234", headers=self.AUTH)
            response = self.client.get("/api/v1/vehicle/MH12AB1234", headers=self.AUTH)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["meta"]["cached"])

    def test_missing_key_returns_401_envelope(self):
        response = self.client.get("/api/v1/vehicle/MH12AB1234")
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error"]["code"], "UNAUTHORIZED")

    def test_invalid_registration_returns_400_envelope(self):
        response = self.client.get(
            "/api/v1/vehicle?registration=NOT-A-PLATE", headers=self.AUTH
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "INVALID_REGISTRATION")

    def test_missing_registration_returns_400(self):
        response = self.client.get("/api/v1/vehicle", headers=self.AUTH)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"]["code"], "MISSING_REGISTRATION"
        )

    def test_not_found_returns_404_envelope(self):
        with mock.patch.object(
            Vehicle, "vahanx_lookup",
            side_effect=Vehicle.VehicleNotFound("no record"),
        ):
            response = self.client.get(
                "/api/v1/vehicle/DL01AB1234?cache=no", headers=self.AUTH
            )
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data["found"])
        self.assertEqual(data["error"]["code"], "VEHICLE_NOT_FOUND")

    def test_upstream_failure_returns_502_envelope(self):
        with mock.patch.object(
            Vehicle, "vahanx_lookup", side_effect=RuntimeError("boom")
        ):
            response = self.client.get(
                "/api/v1/vehicle/MH12AB1234?cache=no", headers=self.AUTH
            )
        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.get_json()["error"]["code"], "UPSTREAM_UNAVAILABLE"
        )

    def test_upstream_rate_limit_returns_429_envelope(self):
        with mock.patch.object(
            Vehicle, "vahanx_lookup",
            side_effect=Vehicle.VahanxRateLimited("slow down"),
        ):
            response = self.client.get(
                "/api/v1/vehicle/MH12AB1234?cache=no", headers=self.AUTH
            )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(
            response.get_json()["error"]["code"], "UPSTREAM_RATE_LIMITED"
        )
        self.assertEqual(response.headers["Retry-After"], "30")

    def test_batch_returns_per_item_results(self):
        def fake_lookup(number):
            if number == "DL01AB1234":
                raise Vehicle.VehicleNotFound("no record")
            result = dict(SAMPLE)
            result["Registration_Number"] = number
            return result

        with mock.patch.object(Vehicle, "vahanx_lookup", side_effect=fake_lookup):
            response = self.client.post(
                "/api/v1/vehicles/batch",
                json={"registrations": ["MH12AB1234", "DL01AB1234"]},
                headers=self.AUTH,
            )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "partial")
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["succeeded"], 1)
        self.assertEqual(data["failed"], 1)
        self.assertEqual(data["results"][0]["status"], "success")
        self.assertEqual(
            data["results"][1]["error"]["code"], "VEHICLE_NOT_FOUND"
        )

    def test_batch_rejects_too_many_items(self):
        response = self.client.post(
            "/api/v1/vehicles/batch",
            json={"registrations": ["MH12AB1234"] * (Vehicle.BATCH_MAX + 1)},
            headers=self.AUTH,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "BATCH_TOO_LARGE")

    def test_batch_accepts_a_single_string(self):
        with mock.patch.object(Vehicle, "vahanx_lookup", return_value=SAMPLE):
            response = self.client.post(
                "/api/v1/vehicles/batch",
                json={"registrations": "MH12AB1234"},
                headers=self.AUTH,
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["count"], 1)

    def test_batch_rejects_invalid_body(self):
        response = self.client.post(
            "/api/v1/vehicles/batch", json={"registrations": 123},
            headers=self.AUTH,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"]["code"], "MISSING_REGISTRATIONS"
        )

    def test_v1_health_is_public(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["data"]["version"], Vehicle.API_VERSION)

    def test_openapi_document_is_public_and_valid(self):
        response = self.client.get("/api/v1/openapi.json")
        self.assertEqual(response.status_code, 200)
        spec = response.get_json()
        self.assertEqual(spec["openapi"], "3.1.0")
        self.assertIn("/api/v1/vehicle/{registration}", spec["paths"])
        self.assertIn("ApiKeyAuth", spec["components"]["securitySchemes"])

    def test_unknown_api_route_returns_json(self):
        response = self.client.get("/api/v1/nope")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"]["code"], "NOT_FOUND")

    def test_cors_headers_are_present(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
        self.assertIn("X-Request-ID", response.headers)


class VahanxParserTests(unittest.TestCase):
    PAGE = """
    <div class="hrcd-cardbody"><p>TEST OWNER</p><span>Owner Name</span></div>
    <div class="col-sm-6 mb-4">
      <span class="text-muted d-block mb-1">Registration Number</span>
      <p class="fw-semibold text-dark mb-0 fs-6">MH12AB1234</p>
    </div>
    <div class="col-sm-6 mb-4">
      <span class="text-muted d-block mb-1">Model Name</span>
      <p class="fw-semibold text-dark mb-0 fs-6">HONDA MOTORCYCLE & SCOOTER INDIA</p>
    </div>
    <div class="col-sm-6 mb-4">
      <span class="text-muted d-block mb-1">Maker Model</span>
      <p class="fw-semibold text-dark mb-0 fs-6">HONDA ACTIVA 6G &amp; CO</p>
    </div>
    """

    def test_parses_both_layouts(self):
        values = Vehicle._parse_vahanx_page(self.PAGE)
        self.assertEqual(values["Owner Name"], "TEST OWNER")
        self.assertEqual(values["Registration Number"], "MH12AB1234")
        self.assertEqual(values["Maker Model"], "HONDA ACTIVA 6G & CO")

    def test_canonical_mapping(self):
        values = Vehicle._parse_vahanx_page(self.PAGE)
        canonical = Vehicle._vahanx_to_canonical(values, "MH12AB1234")
        self.assertEqual(canonical["make"], "HONDA MOTORCYCLE & SCOOTER INDIA")
        self.assertEqual(canonical["model"], "HONDA ACTIVA 6G & CO")

    def test_build_result_omits_empty_and_na(self):
        result = Vehicle._make_vehicle_result(
            "MH12AB1234",
            {"registration_number": "MH12AB1234", "make": "MAHINDRA", "permit_type": "NA"},
        )
        self.assertNotIn("NOC_Details", result)
        self.assertNotIn("Permit_Type", result)
        self.assertEqual(result["Make_Name"], "MAHINDRA")
        self.assertEqual(result["source"], "vahanx")


if __name__ == "__main__":
    unittest.main()
