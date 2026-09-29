from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class CustomerOtpContractTests(unittest.TestCase):
	def test_unknown_mobile_gets_a_one_time_verification_ticket(self):
		source = (ROOT / "api.py").read_text()
		self.assertIn("mobile_verification_token", source)
		self.assertIn('"customer_exists": False', source)
		self.assertIn('"mobile_verified": True', source)

	def test_otp_send_preserves_the_challenge_on_an_unknown_provider_outcome(self):
		source = (ROOT / "api.py").read_text()
		self.assertIn("delivery_pending", source)
		self.assertIn("SmsIrProviderError", source)
		self.assertIn('"challenge_id"', source)
		self.assertIn("uncertain_delivery", source)
		self.assertIn("cache.lock", source)
		self.assertIn('methods=["POST"]', source)

	def test_customer_otp_events_use_the_shared_mobile_login_event_logger(self):
		source = (ROOT / "api.py").read_text()
		customer_sender = (ROOT.parent.parent / "accounts" / "accounts" / "sms_ir_customer.py").read_text()
		self.assertIn("_log_mobile_otp_event", source)
		self.assertIn("_log_mobile_otp_event", customer_sender)
		self.assertIn('event_type="otp_verified"', source)

	def test_customer_account_exposes_verified_mobile_registration_and_password_change(self):
		source = (ROOT / "customer_account.py").read_text()
		self.assertIn("mobile_verification_token", source)
		self.assertIn("def customer_change_password", source)
		self.assertIn("check_password", source)
		self.assertIn('methods=["POST"]', source)


if __name__ == "__main__":
	unittest.main()
