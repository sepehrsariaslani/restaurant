import os

import frappe


def get_frontend_version(context=None):
	"""Cache-bust public assets from the actual built bundle timestamp."""
	if context is not None:
		# The SPA bundle version lives in rendered HTML, so caching the page shell
		# would keep serving the old frontend after a build.
		context.no_cache = 1

	try:
		asset_path = frappe.get_app_path("restaurant", "public", "frontend", "assets", "index.js")
		if os.path.exists(asset_path):
			return str(int(os.path.getmtime(asset_path)))
	except Exception:
		pass
	return frappe.utils.get_build_version()
