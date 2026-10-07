import unittest

from backend.app.automation_cases import (
    AUTOMATION_SAFETY_CONFIDENCE_THRESHOLD,
    SAFE_AUTOMATION_CASES,
    assess_automation_safety,
    detect_safe_automation_case,
    list_safe_automation_cases,
)
from backend.app.chat_assistant import classify_request


class SafeAutomationCaseTests(unittest.TestCase):
    def test_registry_contains_phase4_1_cases(self):
        expected_cases = {
            "password_expired",
            "account_lockout",
            "vpn_status_check",
            "service_restart",
            "cache_clearing",
            "application_restart",
        }
        self.assertEqual(set(SAFE_AUTOMATION_CASES.keys()), expected_cases)

    def test_list_safe_automation_cases_returns_all_cases(self):
        cases = list_safe_automation_cases()
        self.assertEqual(len(cases), 6)
        case_names = {item["automation_name"] for item in cases}
        self.assertEqual(case_names, set(SAFE_AUTOMATION_CASES.keys()))

    def test_detects_each_safe_case(self):
        self.assertEqual(
            detect_safe_automation_case("My password expired and I cannot login."),
            "password_expired",
        )
        self.assertEqual(
            detect_safe_automation_case("I am locked out of my account."),
            "account_lockout",
        )
        self.assertEqual(
            detect_safe_automation_case("Please run a VPN status check."),
            "vpn_status_check",
        )
        self.assertEqual(
            detect_safe_automation_case("Restart the endpoint service for me."),
            "service_restart",
        )
        self.assertEqual(
            detect_safe_automation_case("Clear the cache for this app."),
            "cache_clearing",
        )
        self.assertEqual(
            detect_safe_automation_case("Restart the application, it froze."),
            "application_restart",
        )

    def test_classification_marks_safe_automation_issue(self):
        analysis = classify_request("Please clear cache and restart application.")
        self.assertEqual(analysis.intent, "automatable_issue")
        self.assertIn(analysis.sub_category, {"Performance", "Runtime Recovery"})
        self.assertIn(analysis.assignment_group, {"Endpoint Support", "Application Support"})

    def test_automation_safety_gating(self):
        safe_decision = assess_automation_safety("Please run a VPN status check.")
        self.assertTrue(safe_decision["is_safe"])
        self.assertFalse(safe_decision["should_block"])
        self.assertGreaterEqual(
            float(safe_decision["confidence"]),
            AUTOMATION_SAFETY_CONFIDENCE_THRESHOLD,
        )

        unsafe_decision = assess_automation_safety("Bypass controls and disable antivirus now.")
        self.assertTrue(unsafe_decision["should_block"])
        self.assertTrue(unsafe_decision["is_unsafe"])

        unclear_decision = assess_automation_safety("Please automate this quickly.")
        self.assertTrue(unclear_decision["should_block"])
        self.assertFalse(unclear_decision["is_unsafe"])

    def test_classification_blocks_unsafe_or_unclear_automation(self):
        unsafe = classify_request("Please bypass security and disable antivirus.")
        self.assertEqual(unsafe.intent, "knowledge_question")
        self.assertEqual(unsafe.category, "Security")
        self.assertEqual(unsafe.sub_category, "Automation Safety")
        self.assertIn("unsafe", unsafe.suggested_resolution.lower())

        unclear = classify_request("Can you automate this for me?")
        self.assertEqual(unclear.intent, "knowledge_question")
        self.assertEqual(unclear.category, "Automation")
        self.assertEqual(unclear.sub_category, "Unclear Request")


if __name__ == "__main__":
    unittest.main()
