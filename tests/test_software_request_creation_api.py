import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from backend.app.routers.software import (
    create_software_request,
    get_software_request,
    list_software_requests,
    update_software_request_status,
)
from backend.app.schemas import (
    SoftwareRequestCreateRequest,
    SoftwareRequestStatusUpdateRequest,
)


def _request_context() -> SimpleNamespace:
    state = SimpleNamespace(
        software_request_store={},
        software_request_counter=0,
        mongo_collections={},
    )
    return SimpleNamespace(app=SimpleNamespace(state=state))


class SoftwareRequestCreationApiTests(unittest.TestCase):
    def test_creates_two_service_requests_with_expected_ids_and_statuses(self):
        request = _request_context()

        first = create_software_request(
            SoftwareRequestCreateRequest(
                employee_id="EMP-7701",
                software_name="Visual Studio Code",
                metadata={
                    "business_justification": "Python development",
                    "device_id": "LT-0099",
                },
            ),
            request,
        )
        second = create_software_request(
            SoftwareRequestCreateRequest(
                employee_id="EMP-7702",
                software_name="Corporate VPN Client",
                metadata={
                    "business_justification": "Remote secure access",
                    "manager_approval": "approved",
                },
            ),
            request,
        )

        self.assertTrue(first.request_id.startswith("REQ-"))
        self.assertTrue(second.request_id.startswith("REQ-"))
        self.assertNotEqual(first.request_id, second.request_id)
        self.assertTrue(first.service_now_ref.startswith("RITM"))
        self.assertTrue(second.service_now_ref.startswith("RITM"))
        self.assertEqual(first.status, "requested")
        self.assertEqual(second.status, "queued")

        records = list_software_requests(request)
        record_ids = {item["request_id"] for item in records}
        self.assertIn(first.request_id, record_ids)
        self.assertIn(second.request_id, record_ids)

    def test_updates_request_status_through_mock_lifecycle(self):
        request = _request_context()

        created = create_software_request(
            SoftwareRequestCreateRequest(
                employee_id="EMP-8801",
                software_name="Microsoft Teams",
                metadata={"device_id": "LT-2011"},
            ),
            request,
        )

        request_id = created.request_id
        for status in ["approved", "provisioning", "completed"]:
            updated = update_software_request_status(
                request_id,
                SoftwareRequestStatusUpdateRequest(status=status),
                request,
            )
            self.assertEqual(updated["status"], status)

        detail = get_software_request(request_id, request)
        self.assertEqual(detail["status"], "completed")
        self.assertTrue(detail["updated_at"])

    def test_rejects_invalid_lifecycle_transition(self):
        request = _request_context()

        created = create_software_request(
            SoftwareRequestCreateRequest(
                employee_id="EMP-8802",
                software_name="Adobe Reader",
                metadata={},
            ),
            request,
        )

        request_id = created.request_id
        update_software_request_status(
            request_id,
            SoftwareRequestStatusUpdateRequest(status="completed"),
            request,
        )

        with self.assertRaises(HTTPException):
            update_software_request_status(
                request_id,
                SoftwareRequestStatusUpdateRequest(status="requested"),
                request,
            )


if __name__ == "__main__":
    unittest.main()
