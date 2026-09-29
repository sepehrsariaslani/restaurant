"""Customer-managed recurring meal orders, backed by canonical ERPNext Sales Orders."""

import json
from calendar import monthrange

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime

DOCTYPE = "Restaurant Recurring Order"
WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]

__all__ = [
	"create_my_recurring_order",
	"list_my_recurring_orders",
	"pause_my_recurring_order",
	"place_my_recurring_order",
	"skip_my_recurring_order",
	"run_due_recurring_orders",
]


def _json(value, fallback):
	if isinstance(value, (list, dict)):
		return value
	try:
		return json.loads(value) if value else fallback
	except (TypeError, ValueError):
		return fallback


def _customer(customer_token):
	from restaurant.customer_account import _require_customer

	return _require_customer(customer_token)


def _contract_for(customer):
	from restaurant.api_org import (
		ORG_CONTRACT_DOCTYPE,
		ORG_MEMBER_DOCTYPE,
		_org_active_contract,
		_org_get_contract,
		_org_resolve_member_for_customer,
	)

	if not frappe.db.exists("Customer", customer) or not frappe.db.exists("DocType", ORG_CONTRACT_DOCTYPE):
		return None
	organization = frappe.db.get_value("Customer", customer, "restaurant_organization") or ""
	if not organization and frappe.db.get_value("Customer", customer, "restaurant_customer_kind") == "سازمانی":
		organization = customer
	if not organization and frappe.db.exists("DocType", ORG_MEMBER_DOCTYPE):
		member_name = _org_resolve_member_for_customer(customer)
		if member_name:
			organization = frappe.db.get_value(ORG_MEMBER_DOCTYPE, member_name, "organization") or ""
	if not organization:
		return None
	name = _org_active_contract(organization)
	contract = _org_get_contract(name) if name else None
	return contract if contract and contract.get("invoice_mode") == "ماهانه" else None


def _weekday_index(date_value):
	# Gregorian Monday=0; Persian week starts Saturday.
	return (getdate(date_value).weekday() + 2) % 7


def _next_date(frequency, weekdays, after_date):
	current = getdate(after_date)
	if frequency == "روزانه":
		return add_days(current, 1)
	if frequency == "هفتگی":
		indices = {_ for _ in (_weekday_index_of_name(day) for day in weekdays) if _ is not None}
		for offset in range(1, 8):
			candidate = add_days(current, offset)
			if _weekday_index(candidate) in indices:
				return candidate
		return add_days(current, 7)
	month = current.month + 1
	year = current.year + (1 if month > 12 else 0)
	month = 1 if month > 12 else month
	return current.replace(year=year, month=month, day=min(current.day, monthrange(year, month)[1]))


def _weekday_index_of_name(name):
	try:
		return WEEKDAYS.index(name)
	except ValueError:
		return None


def _next_datetime(frequency, weekdays, after_date, clock):
	date_value = _next_date(frequency, weekdays, after_date)
	return f"{date_value} {clock}"


def _payload(doc):
	return {
		"name": doc.name,
		"settlement_mode": doc.settlement_mode,
		"frequency": doc.frequency,
		"weekdays": _json(doc.weekdays, []),
		"delivery_time": str(doc.delivery_time or ""),
		"start_date": str(doc.start_date or ""),
		"end_date": str(doc.end_date or ""),
		"next_run_at": str(doc.next_run_at or ""),
		"pending_date": str(doc.pending_date or ""),
		"status": doc.status,
		"order_type": doc.order_type,
		"branch": doc.branch,
		"items": _json(doc.items_json, []),
		"last_order": doc.last_order or "",
		"last_error": doc.last_error or "",
	}


def _identity_customer(identity):
	return identity.get("customer") or ""


def _ensure_order_fields():
	from restaurant import api_feature_pack

	api_feature_pack._fp_ensure_custom_fields(
		"Sales Order",
		[
			{"fieldname": "restaurant_recurring_schedule", "label": _("برنامه سفارش تکرارشونده"), "fieldtype": "Link", "options": DOCTYPE},
			{"fieldname": "restaurant_recurring_run_date", "label": _("تاریخ نوبت تکراری"), "fieldtype": "Date"},
		],
		anchor_candidates=["restaurant_organization", "restaurant_status"],
	)


@frappe.whitelist(allow_guest=True)
def create_my_recurring_order(customer_token=None, payload=None):
	identity = _customer(customer_token)
	_ensure_order_fields()
	data = _json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("اطلاعات برنامهٔ سفارش معتبر نیست."))
	frequency = str(data.get("frequency") or "").strip()
	if frequency not in {"روزانه", "هفتگی", "ماهانه"}:
		frappe.throw(_("تناوب سفارش را انتخاب کنید."))
	weekdays = [day for day in WEEKDAYS if day in set(data.get("weekdays") or [])]
	if frequency == "هفتگی" and not weekdays:
		frappe.throw(_("برای برنامهٔ هفتگی حداقل یک روز انتخاب کنید."))
	settlement_mode = str(data.get("settlement_mode") or "تأیید هر نوبت").strip()
	if settlement_mode not in {"تأیید هر نوبت", "فاکتور ماهانه سازمان"}:
		frappe.throw(_("روش تسویه معتبر نیست."))
	customer = _identity_customer(identity)
	if settlement_mode == "فاکتور ماهانه سازمان" and not _contract_for(customer):
		frappe.throw(_("تسویهٔ ماهانه فقط برای مشتری سازمانی با قرارداد فعال و صدور فاکتور ماهانه در دسترس است."))
	items = data.get("items") or []
	if not isinstance(items, list) or not items or len(items) > 80:
		frappe.throw(_("سبد تکرارشونده باید دست‌کم یک قلم و حداکثر ۸۰ قلم داشته باشد."))
	from restaurant.api import _normalize_cart_items
	items = _normalize_cart_items(items)
	if not items:
		frappe.throw(_("اقلام سبد سفارش قابل استفاده نیستند."))
	context = data.get("context") or {}
	if not isinstance(context, dict):
		context = {}
	order_type = str(context.get("order_type") or "").strip()
	if order_type not in {"delivery", "pickup", "dine_in"}:
		frappe.throw(_("روش دریافت سفارش را ابتدا انتخاب کنید."))
	branch = str(context.get("branch") or "").strip()
	if not branch:
		frappe.throw(_("شعبهٔ سفارش را انتخاب کنید."))
	if order_type == "delivery":
		address = context.get("address") if isinstance(context.get("address"), dict) else {}
		if len(str(address.get("address_line") or address.get("address") or "").strip()) < 8 or address.get("lat") in (None, "") or address.get("lng") in (None, ""):
			frappe.throw(_("برای برنامهٔ ارسال، نشانی ذخیره‌شده همراه موقعیت نقشه لازم است."))
	start_date = getdate(data.get("start_date") or getdate())
	if start_date < getdate():
		frappe.throw(_("تاریخ شروع نمی‌تواند در گذشته باشد."))
	end_date = getdate(data.get("end_date")) if data.get("end_date") else None
	if end_date and end_date < start_date:
		frappe.throw(_("تاریخ پایان باید بعد از تاریخ شروع باشد."))
	clock = str(data.get("delivery_time") or "").strip()[:8]
	if not clock:
		frappe.throw(_("زمان دریافت را مشخص کنید."))
	if frequency == "هفتگی" and WEEKDAYS[_weekday_index(start_date)] not in weekdays:
		start_date = _next_date(frequency, weekdays, add_days(start_date, -1))
	if start_date == getdate() and clock <= now_datetime().strftime("%H:%M:%S"):
		frappe.throw(_("زمان شروع باید در آینده باشد."))
	context.update({"branch": branch, "organization": customer if settlement_mode == "فاکتور ماهانه سازمان" else ""})
	doc = frappe.get_doc({
		"doctype": DOCTYPE,
		"customer": customer,
		"customer_name": frappe.db.get_value("Customer", customer, "customer_name") or customer,
		"mobile": identity.get("mobile") or "",
		"settlement_mode": settlement_mode,
		"frequency": frequency,
		"weekdays": json.dumps(weekdays, ensure_ascii=False),
		"delivery_time": clock,
		"start_date": start_date,
		"end_date": end_date,
		"next_run_at": f"{start_date} {clock}",
		"status": "فعال",
		"order_type": order_type,
		"branch": branch,
		"items_json": json.dumps(items, ensure_ascii=False),
		"context_json": json.dumps(context, ensure_ascii=False),
		"note": str(data.get("note") or "")[:500],
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "schedule": _payload(doc)}


@frappe.whitelist(allow_guest=True)
def list_my_recurring_orders(customer_token=None):
	identity = _customer(customer_token)
	customer = _identity_customer(identity)
	rows = frappe.get_all(DOCTYPE, filters={"customer": customer}, fields=["name"], order_by="creation desc", limit_page_length=100, ignore_permissions=True)
	return {"schedules": [_payload(frappe.get_doc(DOCTYPE, row.name)) for row in rows], "monthly_billing_available": bool(_contract_for(customer))}


@frappe.whitelist(allow_guest=True)
def pause_my_recurring_order(customer_token=None, name=""):
	identity = _customer(customer_token)
	customer = _identity_customer(identity)
	if not frappe.db.exists(DOCTYPE, {"name": name, "customer": customer}):
		frappe.throw(_("برنامهٔ سفارش یافت نشد."))
	doc = frappe.get_doc(DOCTYPE, name)
	if doc.status == "متوقف":
		doc.status = "فعال"
		doc.pending_date = None
	else:
		doc.status = "متوقف"
		doc.pending_date = None
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "schedule": _payload(doc)}


def _place_schedule_order(doc, run_date, customer_token=None):
	from restaurant.api import place_order
	from restaurant.order_review import internal_order_creation

	# Scheduled monthly runs are created by the background worker, so there is
	# no browser session token to carry through place_order. Issue a short-lived
	# server-side customer session from the already-owned recurring-order record
	# so the same verified-customer discounts and referral snapshot are applied.
	if not customer_token:
		from restaurant.customer_account import issue_customer_session

		if not frappe.db.exists("Customer", doc.customer) or cint(
			frappe.db.get_value("Customer", doc.customer, "disabled") or 0
		):
			frappe.throw(_("حساب مشتری این برنامه دیگر فعال نیست."))
		customer_token = issue_customer_session(doc.customer, doc.mobile or "")

	items = _json(doc.items_json, [])
	context = _json(doc.context_json, {})
	context["scheduled_for"] = str(run_date)
	context["recurring_schedule"] = doc.name
	context["recurring_run_date"] = str(run_date)
	if doc.order_type == "delivery":
		context["delivery_time_type"] = "scheduled"
		context["delivery_time"] = str(doc.delivery_time or "")
	else:
		context["pickup_time_type"] = "scheduled"
		context["pickup_time"] = str(doc.delivery_time or "")
	address = context.get("address") if isinstance(context.get("address"), dict) else {}
	with internal_order_creation():
		return place_order(
			customer_info={"name": doc.customer_name, "mobile": doc.mobile},
			order_type="delivery" if doc.order_type == "delivery" else "dine_in" if doc.order_type == "dine_in" else "takeaway",
			items=items,
			address=address.get("address_line") or address.get("address") or "",
			note=doc.note or "",
			delivery_mode="delivery" if doc.order_type == "delivery" else "",
			delivery_address_snapshot=address if doc.order_type == "delivery" else None,
			order_context=context,
			customer_token=customer_token,
			commit=False,
		)


def _advance(doc, run_date, order_name=""):
	clock = str(doc.delivery_time or "")
	doc.last_run_at = now_datetime()
	doc.last_order = order_name or doc.last_order
	doc.pending_date = None
	doc.last_error = ""
	next_date = _next_date(doc.frequency, _json(doc.weekdays, []), run_date)
	if doc.end_date and next_date > getdate(doc.end_date):
		doc.status = "متوقف"
		doc.next_run_at = None
	else:
		doc.next_run_at = f"{next_date} {clock}"


@frappe.whitelist(allow_guest=True)
def place_my_recurring_order(customer_token=None, name="", branch=""):
	identity = _customer(customer_token)
	customer = _identity_customer(identity)
	if not frappe.db.exists(DOCTYPE, {"name": name, "customer": customer}):
		frappe.throw(_("برنامهٔ سفارش یافت نشد."))
	frappe.db.sql(f"select name from `tab{DOCTYPE}` where name=%s and customer=%s for update", (name, customer))
	doc = frappe.get_doc(DOCTYPE, name)
	if doc.settlement_mode != "تأیید هر نوبت" or doc.status != "منتظر تأیید مشتری" or not doc.pending_date:
		frappe.throw(_("این نوبت در حال حاضر برای تأیید آماده نیست."))
	from restaurant.api import _check_cart_branch_availability
	from restaurant.api_meal_planning import _get_catalog, _valid_customer_branch

	branch = str(branch or doc.branch or "").strip()
	if not _valid_customer_branch(branch):
		frappe.throw(_("شعبهٔ انتخاب‌شده معتبر یا فعال نیست."))
	context = _json(doc.context_json, {})
	if branch != doc.branch:
		from restaurant.api import get_branches

		branch_row = next((row for row in (get_branches() or {}).get("branches", []) if str(row.get("id") or row.get("name") or "").strip() == branch), None)
		if doc.order_type == "delivery":
			from restaurant.api import _validate_customer_delivery_branch

			_validate_customer_delivery_branch(branch, context.get("address") if isinstance(context.get("address"), dict) else {})
		elif doc.order_type == "pickup" and not (branch_row or {}).get("pickup_available"):
			frappe.throw(_("تحویل حضوری از شعبهٔ انتخاب‌شده در دسترس نیست."))
		elif doc.order_type == "dine_in":
			frappe.throw(_("برای تحویل روی میز، انتخاب شعبه در این برنامه قابل تغییر نیست؛ برنامه را از شعبهٔ درست بسازید."))
	items = _json(doc.items_json, [])
	availability = _check_cart_branch_availability(items, branch)
	warnings = [
		{"item_slug": row.get("item_slug"), "item_title": row.get("item_title"), "reason": "این محصول در شعبهٔ انتخابی موجود نیست."}
		for row in (availability.get("unavailable_items") or [])
	]
	catalog = _get_catalog(branch)
	by_slug = {str(row.get("slug") or "").strip().casefold(): row for row in catalog if row.get("slug")}
	cart_items = []
	for row in items:
		slug = str(row.get("item_slug") or row.get("slug") or "").strip()
		product = by_slug.get(slug.casefold())
		if not product:
			if not any(warning.get("item_slug") == slug for warning in warnings):
				warnings.append({"item_slug": slug, "item_title": row.get("item_title") or slug, "reason": "محصول یا قیمت فعلی در منوی شعبه پیدا نشد."})
			continue
		price = product.get("base_price")
		if price is None or flt(price) <= 0:
			warnings.append({"item_slug": slug, "item_title": product.get("title") or slug, "reason": "قیمت فعلی این محصول در دسترس نیست."})
			continue
		cart_items.append({
			"item_slug": product.get("slug"),
			"item_title": product.get("title") or product.get("name"),
			"qty": flt(row.get("qty") or 1),
			"customization": row.get("customization") or {},
			"note": row.get("note") or "",
			"base_price": flt(price),
		})
	if warnings or not cart_items:
		return {"status": "needs_review", "warnings": warnings or [{"reason": "قلم سفارش‌پذیری در این نوبت پیدا نشد."}], "schedule": _payload(doc)}
	context["branch"] = branch
	if doc.note:
		context["customer_note"] = doc.note
	doc.branch = branch
	doc.context_json = json.dumps(context, ensure_ascii=False)
	_advance(doc, doc.pending_date)
	if doc.next_run_at:
		doc.status = "فعال"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "cart_items": cart_items, "order_context": context, "schedule": _payload(doc)}


@frappe.whitelist(allow_guest=True)
def skip_my_recurring_order(customer_token=None, name=""):
	identity = _customer(customer_token)
	customer = _identity_customer(identity)
	if not frappe.db.exists(DOCTYPE, {"name": name, "customer": customer}):
		frappe.throw(_("برنامهٔ سفارش یافت نشد."))
	frappe.db.sql(f"select name from `tab{DOCTYPE}` where name=%s and customer=%s for update", (name, customer))
	doc = frappe.get_doc(DOCTYPE, name)
	if doc.settlement_mode != "تأیید هر نوبت" or doc.status != "منتظر تأیید مشتری" or not doc.pending_date:
		frappe.throw(_("نوبتی برای ردکردن وجود ندارد."))
	_advance(doc, doc.pending_date)
	if doc.next_run_at:
		doc.status = "فعال"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "schedule": _payload(doc)}


def run_due_recurring_orders():
	"""Each minute: bill approved monthly org schedules; queue personal runs for approval."""
	if not frappe.db.exists("DocType", DOCTYPE):
		return
	now = now_datetime()
	rows = frappe.get_all(DOCTYPE, filters={"status": "فعال", "next_run_at": ["<=", now]}, fields=["name"], order_by="next_run_at asc", limit_page_length=100, ignore_permissions=True)
	if rows:
		_ensure_order_fields()
	for row in rows:
		try:
			frappe.db.sql(
				f"UPDATE `tab{DOCTYPE}` SET status=%s WHERE name=%s AND status=%s AND next_run_at<=%s",
				("در حال اجرا", row.name, "فعال", now),
			)
			if getattr(getattr(frappe.db, "_cursor", None), "rowcount", 0) == 0:
				continue
			frappe.db.commit()
			doc = frappe.get_doc(DOCTYPE, row.name)
			run_date = getdate(doc.next_run_at)
			if doc.end_date and run_date > getdate(doc.end_date):
				doc.status = "متوقف"
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				continue
			if doc.settlement_mode == "تأیید هر نوبت":
				doc.pending_date = run_date
				doc.status = "منتظر تأیید مشتری"
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				continue
			if not _contract_for(doc.customer):
				doc.status = "نیازمند بررسی"
				doc.last_error = "قرارداد فعال با تسویهٔ ماهانه موجود نیست."
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				continue
			order_fields = {"restaurant_recurring_schedule": row.name, "restaurant_recurring_run_date": str(run_date)}
			if frappe.db.exists("Sales Order", order_fields):
				order_name = frappe.db.get_value("Sales Order", order_fields, "name")
			else:
				result = _place_schedule_order(doc, run_date)
				order_name = result.get("order_id") or ""
				for field, value in order_fields.items():
					if frappe.db.has_column("Sales Order", field):
						frappe.db.set_value("Sales Order", order_name, field, value, update_modified=False)
			_advance(doc, run_date, order_name)
			doc.status = "فعال" if doc.status == "در حال اجرا" else doc.status
			doc.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			try:
				doc = frappe.get_doc(DOCTYPE, row.name)
				doc.status = "نیازمند بررسی"
				doc.last_error = frappe.get_traceback()[-1000:]
				doc.save(ignore_permissions=True)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"Recurring restaurant order failed: {row.name}")
