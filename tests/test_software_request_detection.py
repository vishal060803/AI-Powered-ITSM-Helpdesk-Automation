import unittest

from backend.app.chat_assistant import (
    classify_request,
    detect_software_provisioning_request,
)
from backend.app.software_catalog import extract_software_name


class SoftwareRequestDetectionTests(unittest.TestCase):
    def test_extracts_known_software_name(self):
        self.assertEqual(
            extract_software_name("Please install VSCode on my laptop."),
            "Visual Studio Code",
        )
        self.assertEqual(
            extract_software_name("I need Microsoft Teams for calls."),
            "Microsoft Teams",
        )

    def test_detects_provisioning_request_with_employee_context(self):
        detected = detect_software_provisioning_request(
            "Please install Adobe Reader on my device.",
            employee_id="EMP-5501",
            context={"department": "Finance", "device_id": "LT-8842"},
        )

        self.assertTrue(detected["is_provisioning_request"])
        self.assertEqual(detected["software_name"], "Adobe Reader")
        self.assertEqual(detected["employee_context"]["employee_id"], "EMP-5501")
        self.assertEqual(detected["employee_context"]["department"], "Finance")
        self.assertEqual(detected["employee_context"]["device_id"], "LT-8842")
        self.assertIn("Adobe Reader", detected["summary"])

    def test_classification_returns_service_request_summary(self):
        analysis = classify_request(
            "Need Corporate VPN client installation for remote access.",
            employee_id="EMP-6602",
            context={"location": "Bangalore", "manager_approval": "pending"},
        )

        self.assertEqual(analysis.intent, "service_request")
        self.assertEqual(analysis.category, "Software")
        self.assertEqual(analysis.sub_category, "Provisioning")
        self.assertIn("Corporate VPN Client", analysis.summary)
        self.assertIn("EMP-6602", analysis.summary)
        self.assertIn("Context captured", analysis.suggested_resolution)


if __name__ == "__main__":
    unittest.main()

