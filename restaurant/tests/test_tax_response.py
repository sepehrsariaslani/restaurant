from __future__ import annotations

import unittest

from restaurant.tax_response import extract_provider_tax_id


class TestProviderTaxIdentifier(unittest.TestCase):
	def test_reads_only_explicit_tax_id_field(self):
		self.assertEqual(
			extract_provider_tax_id({"tax_id": "TAX-123", "reference": "R-1", "id": "P-1"}),
			"TAX-123",
		)

	def test_does_not_treat_generic_reference_or_id_as_tax_id(self):
		self.assertEqual(extract_provider_tax_id({"reference": "R-1", "id": "P-1"}), "")

	def test_normalizes_explicit_scalar_and_rejects_malformed_values(self):
		self.assertEqual(extract_provider_tax_id({"tax_id": "  TAX-123  "}), "TAX-123")
		self.assertEqual(extract_provider_tax_id({"tax_id": {"value": "TAX-123"}}), "")
		self.assertEqual(extract_provider_tax_id({"tax_id": True}), "")
		self.assertEqual(extract_provider_tax_id(None), "")

	def test_truncates_identifier_to_native_field_length(self):
		self.assertEqual(len(extract_provider_tax_id({"tax_id": "X" * 200})), 140)


if __name__ == "__main__":
	unittest.main()
