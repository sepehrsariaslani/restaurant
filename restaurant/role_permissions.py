"""Shared role and POS Profile checks for restaurant API entrypoints."""

from __future__ import annotations

from functools import wraps

import frappe
from frappe import _
from frappe.utils import cint


RESTAURANT_ROLE_IDS = frozenset(
	{
		"Restaurant Manager",
		"Restaurant Supervisor",
		"Restaurant Cashier",
		"Restaurant Waiter",
		"Restaurant Chef",
	}
)

SYSTEM_ADMIN_ROLES = frozenset({"System Manager", "Administrator"})
FINANCE_ADMIN_ROLES = frozenset({"System Manager", "Administrator", "Accounts Manager"})
LEGACY_MANAGEMENT_ROLES = frozenset({"Desk User", "Website Manager"})

CAPABILITY_ROLES = {
	"pos_read": frozenset({"Restaurant Manager", "Restaurant Supervisor", "Restaurant Cashier"}),
	"pos_sell": frozenset({"Restaurant Manager", "Restaurant Cashier"}),
	"pos_manage": frozenset({"Restaurant Manager"}),
	"cashbox_read": frozenset({"Restaurant Manager", "Restaurant Supervisor", "Restaurant Cashier"}),
	"cashbox_invoice_read": frozenset({"Restaurant Manager", "Restaurant Cashier"}),
	"cashbox_write": frozenset({"Restaurant Manager", "Restaurant Cashier"}),
	"pos_profile_assign_users": frozenset({"Restaurant Manager"}),
	"table_read": frozenset({"Restaurant Manager", "Restaurant Supervisor", "Restaurant Waiter"}),
	"table_write": frozenset({"Restaurant Manager", "Restaurant Supervisor", "Restaurant Waiter"}),
	"table_pay": frozenset({"Restaurant Manager", "Restaurant Cashier"}),
	"table_manage": frozenset({"Restaurant Manager"}),
	"reservation_read": frozenset({"Restaurant Manager", "Restaurant Supervisor", "Restaurant Waiter"}),
	"reservation_write": frozenset({"Restaurant Manager", "Restaurant Supervisor", "Restaurant Waiter"}),
	"kitchen_read": frozenset({"Restaurant Manager", "Restaurant Supervisor", "Restaurant Chef"}),
	"kitchen_write": frozenset({"Restaurant Manager", "Restaurant Supervisor", "Restaurant Chef"}),
	"kitchen_close": frozenset({"Restaurant Manager", "Restaurant Supervisor"}),
	"courier_read": frozenset({"Restaurant Manager", "Restaurant Supervisor"}),
	"courier_write": frozenset({"Restaurant Manager", "Restaurant Supervisor"}),
	"catalog_read": frozenset({"Restaurant Manager", "Restaurant Cashier", "Restaurant Waiter", "Restaurant Chef"}),
	"catalog_write": frozenset({"Restaurant Manager"}),
	"inventory_read": frozenset({"Restaurant Manager"}),
	"inventory_write": frozenset({"Restaurant Manager"}),
	"restaurant_settings": frozenset({"Restaurant Manager"}),
	"restaurant_reports": frozenset({"Restaurant Manager", "Restaurant Supervisor"}),
}

ROLE_DOCTYPE_PERMISSIONS = {
	"Restaurant Manager": {
		"Restaurant Order": {"read", "write", "create", "delete", "report", "print"},
		"Restaurant Table": {"read", "write", "create", "delete", "report"},
		"Restaurant Table Session": {"read", "write", "create", "delete", "report"},
		"Restaurant Table Order": {"read", "write", "create", "delete", "report"},
		"Restaurant Table Request": {"read", "write", "create", "delete", "report"},
		"Restaurant Table Reservation": {"read", "write", "create", "delete", "report"},
		"Restaurant Reservation": {"read", "write", "create", "delete", "report"},
		"Restaurant Courier": {"read", "write", "create", "delete", "report"},
		"Restaurant Production Ticket": {"read", "write", "create"},
		"Restaurant Menu Category": {"read", "write", "create", "delete", "report"},
		"Restaurant Menu Subcategory": {"read", "write", "create", "delete", "report"},
		"Restaurant Menu Item": {"read", "write", "create", "delete", "report"},
		"Product Builder Template": {"read", "write", "create", "delete", "report"},
		"Restaurant Modifier Group": {"read", "write", "create", "delete", "report"},
		"Restaurant Inventory Purchase Order": {"read", "write", "create", "delete", "report"},
		"Restaurant Order Loss Entry": {"read", "write", "create", "report"},
		"Restaurant Branch Production Settings": {"read", "write", "create", "delete"},
		"Restaurant Branch Schedule": {"read", "write", "create", "delete"},
		"Restaurant Customer Review": {"read", "write", "create", "report"},
		"Restaurant Customer Voice": {"read", "write", "create", "delete", "report"},
		"Restaurant Survey Question": {"read", "write", "create", "delete", "report"},
		"Restaurant Survey Invitation": {"read", "write", "create", "delete", "report"},
		"Restaurant Survey Response": {"read", "report"},
	},
	"Restaurant Supervisor": {
		"Restaurant Table": {"read"},
		"Restaurant Table Session": {"read"},
		"Restaurant Table Order": {"read"},
		"Restaurant Table Request": {"read"},
		"Restaurant Table Reservation": {"read"},
		"Restaurant Reservation": {"read"},
	},
	"Restaurant Cashier": {
	},
	"Restaurant Waiter": {
		"Restaurant Table": {"read"},
		"Restaurant Table Session": {"read"},
		"Restaurant Table Order": {"read"},
		"Restaurant Table Request": {"read"},
		"Restaurant Table Reservation": {"read"},
		"Restaurant Reservation": {"read"},
		"Restaurant Menu Item": {"read"},
	},
	"Restaurant Chef": {
		# Kitchen data is exposed through the field-limited KDS API. These
		# documents also carry prices, customer information, or recipe costs.
	},
}


def get_user_roles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return set()
	return set(frappe.get_roles(user) or [])


def is_system_administrator(user: str | None = None) -> bool:
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & SYSTEM_ADMIN_ROLES)


def is_limited_restaurant_manager(user: str | None = None) -> bool:
	roles = get_user_roles(user)
	return "Restaurant Manager" in roles and not bool(roles & SYSTEM_ADMIN_ROLES)


def restaurant_role_names(user: str | None = None) -> set[str]:
	return get_user_roles(user) & RESTAURANT_ROLE_IDS


def require_restaurant_capability(capability: str, user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = get_user_roles(user)
	if is_system_administrator(user):
		return True

	restaurant_roles = roles & RESTAURANT_ROLE_IDS
	if restaurant_roles:
		if restaurant_roles & CAPABILITY_ROLES.get(capability, frozenset()):
			return True
		frappe.throw(_("نقش شما اجازهٔ این عملیات رستوران را ندارد."), frappe.PermissionError)

	if roles & LEGACY_MANAGEMENT_ROLES:
		return True
	frappe.throw(_("نقش شما اجازهٔ این عملیات رستوران را ندارد."), frappe.PermissionError)


def require_finance_admin(fn):
	"""Restrict financial APIs to system or Accounts managers."""
	@wraps(fn)
	def wrapped(*args, **kwargs):
		if not get_user_roles() & FINANCE_ADMIN_ROLES:
			frappe.throw(_("مدیریت تنظیمات مالیاتی و حسابداری به مدیر مالی نیاز دارد."), frappe.PermissionError)
		previous = getattr(frappe.flags, "restaurant_finance_access_checked", False)
		frappe.flags.restaurant_finance_access_checked = True
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.flags.restaurant_finance_access_checked = previous
	return wrapped


def _profile_user_names(profile_doc) -> set[str]:
	users: set[str] = set()
	for fieldname in ("applicable_for_users", "users", "allowed_users"):
		for row in profile_doc.get(fieldname) or []:
			user = str(row.get("user") or row.get("default_user") or "").strip()
			if user:
				users.add(user)
		if users:
			break
	return users


def assigned_pos_profiles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	if not frappe.db.exists("DocType", "POS Profile"):
		return set()
	profile_names = frappe.get_all("POS Profile", pluck="name", ignore_permissions=True, limit_page_length=1000)
	assigned = set()
	for profile_name in profile_names:
		try:
			profile = frappe.get_doc("POS Profile", profile_name)
		except Exception:
			continue
		if user in _profile_user_names(profile):
			assigned.add(profile_name)
	return assigned


def require_pos_profile_access(profile_name: str, user: str | None = None, capability: str = "cashbox_read") -> str:
	user = user or frappe.session.user
	profile_name = str(profile_name or "").strip()
	if not profile_name or not frappe.db.exists("POS Profile", profile_name):
		frappe.throw(_("یک POS Profile معتبر انتخاب کنید."), frappe.ValidationError)
	require_restaurant_capability(capability, user=user)
	if capability in {"pos_sell", "cashbox_write"} and cint(
		frappe.db.get_value("POS Profile", profile_name, "disabled") or 0
	):
		frappe.throw(_("این POS Profile غیرفعال است و برای عملیات جدید قابل استفاده نیست."), frappe.PermissionError)
	roles = get_user_roles(user)
	if "Restaurant Cashier" in roles and "Restaurant Manager" not in roles and not is_system_administrator(user):
		if profile_name not in assigned_pos_profiles(user):
			frappe.throw(_("این POS Profile به حساب شما تخصیص داده نشده است."), frappe.PermissionError)
	return profile_name


def require_restaurant_staff_user(user: str) -> bool:
	if not frappe.db.exists("User", user):
		return False
	return bool(restaurant_role_names(user)) and not bool(get_user_roles(user) & SYSTEM_ADMIN_ROLES)


def require_capability(capability: str):
	"""Decorate an API entrypoint with one explicit restaurant capability."""

	def decorate(fn):
		@wraps(fn)
		def wrapped(*args, **kwargs):
			require_restaurant_capability(capability)
			previous = getattr(frappe.flags, "restaurant_api_capability_checked", False)
			previous_capability = getattr(frappe.flags, "restaurant_api_capability", None)
			frappe.flags.restaurant_api_capability_checked = True
			frappe.flags.restaurant_api_capability = capability
			try:
				return fn(*args, **kwargs)
			finally:
				frappe.flags.restaurant_api_capability_checked = previous
				frappe.flags.restaurant_api_capability = previous_capability

		return wrapped

	return decorate
