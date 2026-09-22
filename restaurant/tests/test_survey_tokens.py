import unittest

from restaurant.survey_tokens import generate_token, token_digest, token_is_valid


class TestSurveyTokens(unittest.TestCase):
	def test_generated_token_is_short_url_safe_and_not_a_mobile_number(self):
		token = generate_token()
		self.assertLessEqual(len(token), 25)
		self.assertRegex(token, r"^[A-Za-z0-9_-]+$")
		self.assertNotIn("09121234567", token)
		self.assertTrue(token_is_valid(token))

	def test_token_digest_is_deterministic_without_exposing_raw_token(self):
		token = generate_token()
		self.assertEqual(token_digest(token), token_digest(token))
		self.assertNotEqual(token_digest(token), token)
		self.assertFalse(token_is_valid("too short"))


if __name__ == "__main__":
	unittest.main()
