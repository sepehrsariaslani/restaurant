import frappe


def get_context(context):
	"""Dedicated courier PWA (guest access, mobile + access code login)."""
	context.no_cache = 1
	context.show_sidebar = False
	return context
