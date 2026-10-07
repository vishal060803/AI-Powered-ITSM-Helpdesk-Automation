import unittest

from backend.app.chat_assistant import (
    build_assistant_reply,
    build_grounded_answer,
    build_incident_payload,
    classify_request,
)


class ChatAssistantReplyTests(unittest.TestCase):
    def test_build_assistant_reply_includes_stepwise_guidance_and_final_suggestion(self):
        question = "My password has to be reseted."
        results = [
            {
                "title": "Reset a password or resolve an account lockout",
                "category": "Identity",
                "sub_category": "Password and account access",
                "text": "Use the approved password-reset portal. Complete identity verification using MFA. Choose a new password that meets the organization's requirements. If the account is locked, follow the portal's unlock option. After the reset, sign in to required applications and update your approved prompts.",
            }
        ]

        reply = build_assistant_reply(question, results)

        self.assertIn("1)", reply)
        self.assertIn("forgot password", reply.lower())
        self.assertIn("Final suggestion", reply)
        self.assertNotIn("Identify", reply)
        self.assertNotIn("Update ServiceNow", reply)

    def test_build_grounded_answer_returns_source_names_and_confidence(self):
        question = "I cannot connect to VPN after the update."
        results = [
            {
                "title": "VPN connection troubleshooting",
                "category": "Network",
                "sub_category": "VPN",
                "text": "Confirm the device date and time are correct. Open the approved VPN client and complete MFA. If authentication still fails, contact the Network Support team with the exact error and client version.",
                "distance": 0.12,
            }
        ]

        grounded = build_grounded_answer(question, results)

        self.assertIn("VPN connection troubleshooting", grounded["answer"])
        self.assertEqual(grounded["sources"][0], "VPN connection troubleshooting")
        self.assertGreaterEqual(grounded["confidence"], 0.7)
        self.assertTrue(grounded["is_supported"])

    def test_build_grounded_answer_refuses_unsupported_queries(self):
        grounded = build_grounded_answer("How do I hack into the secure server?", [])

        self.assertFalse(grounded["is_supported"])
        self.assertIn("I cannot answer confidently", grounded["answer"])
        self.assertEqual(grounded["sources"], [])
        self.assertLessEqual(grounded["confidence"], 0.3)

    def test_build_grounded_answer_refuses_low_confidence_matches(self):
        grounded = build_grounded_answer(
            "How can I optimize kernel scheduling for custom firmware?",
            [
                {
                    "title": "VPN connection troubleshooting",
                    "category": "Network",
                    "sub_category": "VPN",
                    "text": "Check approved VPN client settings and retry MFA.",
                    "distance": 0.72,
                }
            ],
        )

        self.assertFalse(grounded["is_supported"])
        self.assertIn("cannot answer confidently", grounded["answer"])
        self.assertLess(grounded["confidence"], 0.6)

    def test_classify_request_unknown_question_escalates_with_low_confidence(self):
        analysis = classify_request("Need help with a custom internal plugin behavior that is not documented.")

        self.assertEqual(analysis.intent, "knowledge_question")
        self.assertEqual(analysis.sub_category, "Unknown")
        self.assertIn("escalate", analysis.suggested_resolution.lower())
        self.assertLess(analysis.confidence, 0.6)

    def test_classify_request_extracts_structured_fields(self):
        analysis = classify_request("I cannot connect to VPN since this morning. Authentication keeps failing.")

        self.assertEqual(analysis.intent, "incident")
        self.assertEqual(analysis.category, "Network")
        self.assertEqual(analysis.sub_category, "VPN")
        self.assertEqual(analysis.priority, "P2")
        self.assertEqual(analysis.urgency, "High")
        self.assertEqual(analysis.assignment_group, "Network Support")
        self.assertIn("VPN", analysis.summary)
        self.assertIn("vpn", analysis.suggested_resolution.lower())
        self.assertGreaterEqual(analysis.confidence, 0.8)

    def test_build_incident_payload_maps_servicenow_fields(self):
        analysis = classify_request("I cannot connect to VPN since this morning. Authentication keeps failing.")
        payload = build_incident_payload(analysis, "I cannot connect to VPN since this morning. Authentication keeps failing.")

        self.assertEqual(payload["short_description"], analysis.summary)
        self.assertEqual(payload["category"], "Network")
        self.assertEqual(payload["priority"], "P2")
        self.assertEqual(payload["urgency"], "High")
        self.assertEqual(payload["assignment_group"], "Network Support")
        self.assertIn("I cannot connect to VPN", payload["description"])
        self.assertGreaterEqual(payload["confidence"], 0.8)
        self.assertIn("assignment_group", payload["service_now_fields"])


if __name__ == "__main__":
    unittest.main()
