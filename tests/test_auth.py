import unittest

from backend.core.auth import SESSION_MAX_AGE, create_session_token, verify_session_token


class SessionTokenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.email = "admin@example.com"
        self.secret = "a-session-signing-secret-that-is-long-enough"
        self.token = create_session_token(self.email, self.secret, now=1_000)

    def test_accepts_valid_token_for_expected_user(self) -> None:
        self.assertTrue(
            verify_session_token(self.token, self.secret, self.email, now=1_001)
        )

    def test_rejects_expired_token(self) -> None:
        self.assertFalse(
            verify_session_token(
                self.token, self.secret, self.email, now=1_000 + SESSION_MAX_AGE
            )
        )

    def test_rejects_wrong_user_or_modified_token(self) -> None:
        self.assertFalse(
            verify_session_token(self.token, self.secret, "other@example.com", now=1_001)
        )
        replacement = "A" if self.token[0] != "A" else "B"
        modified_token = f"{replacement}{self.token[1:]}"
        self.assertFalse(
            verify_session_token(modified_token, self.secret, self.email, now=1_001)
        )

    def test_rejects_malformed_token(self) -> None:
        self.assertFalse(
            verify_session_token("not-a-session", self.secret, self.email, now=1_001)
        )


if __name__ == "__main__":
    unittest.main()
