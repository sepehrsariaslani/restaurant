import frappe


def get_context(context):
	"""Public organization accountant portal (guest access, code-based)."""
	context.no_cache = 1
	context.show_sidebar = False
	return context
