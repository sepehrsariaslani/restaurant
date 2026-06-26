import frappe
from frappe import _
from frappe.model.document import Document

try:
	from frappe.utils import slugify
except ImportError:
	import re

	def slugify(text):
		text = text.lower().strip()
		text = re.sub(r"[^\w\s-]", "", text)
		text = re.sub(r"[\s_-]+", "-", text)
		text = re.sub(r"^-+|-+$", "", text)
		return text


class ProductBuilderTemplate(Document):
	def validate(self):
		self._ensure_slug()
		self._validate_steps()
		self._validate_unique_slug()

	def _ensure_slug(self):
		if not self.slug and self.title:
			self.slug = slugify(self.title)

	def _validate_steps(self):
		if not self.steps:
			frappe.throw(_("At least one step is required."))
		step_keys = [s.step_key for s in self.steps]
		if len(step_keys) != len(set(step_keys)):
			frappe.throw(_("Step keys must be unique within a template."))
		if self.flags.get("skip_builder_options_validation"):
			return
		for step in self.steps:
			options = self._get_step_options(step)
			if not options:
				frappe.throw(_("Step '{0}' must have at least one option.").format(step.step_title))
			option_keys = [o.option_key for o in options]
			if len(option_keys) != len(set(option_keys)):
				frappe.throw(_("Option keys must be unique within step '{0}'.").format(step.step_title))

	def _get_step_options(self, step):
		inline_options = getattr(step, "options", None)
		if inline_options:
			return inline_options
		if not getattr(step, "name", None):
			return []
		return frappe.get_all(
			"Product Builder Option",
			filters={
				"parent": step.name,
				"parenttype": "Product Builder Step",
				"parentfield": "options",
			},
			fields=["option_key"],
			order_by="sort_order asc, idx asc",
		)

	def _validate_unique_slug(self):
		existing = frappe.db.exists(
			"Product Builder Template",
			{"slug": self.slug, "name": ["!=", self.name]},
		)
		if existing:
			frappe.throw(_("A template with slug '{0}' already exists.").format(self.slug))

	def before_save(self):
		# Sort steps by sort_order
		self.steps.sort(key=lambda s: s.sort_order or 0)


def on_item_update(doc, method):
	"""Hook: When Item's is_customizable or builder_template changes, validate consistency."""
	if not doc.get("is_customizable") and doc.get("builder_template"):
		frappe.msgprint(
			_("Warning: Item '{0}' has a builder template linked but is not marked as customizable.").format(
				doc.name
			),
			indicator="orange",
		)
