import unittest

from backend.app.chat_assistant import build_assistant_reply


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


if __name__ == "__main__":
    unittest.main()
