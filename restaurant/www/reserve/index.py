import frappe


def get_context(context):
	"""Public online reservation page (guest access)."""
	context.no_cache = 1
	context.show_sidebar = False
	return context
