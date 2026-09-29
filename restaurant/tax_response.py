from __future__ import annotations

from collections.abc import Mapping


def extract_provider_tax_id(response) -> str:
	"""Return only the gateway field explicitly named ``tax_id``.

	Generic ``id`` and ``reference`` values are not reliable tax-authority
	identifiers. The complete provider payload remains available in the native
	submission response for audit and manual review.
	"""
	if not isinstance(response, Mapping):
		return ""

	value = response.get("tax_id")
	if isinstance(value, bool) or not isinstance(value, (str, int)):
		return ""
	return str(value).strip()[:140]
