"""Food Partner order mapping facade for native Restaurant records."""

import frappe


@frappe.whitelist()
def get_snappfood_modifier_groups(item_name=""):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import get_snappfood_modifier_groups as _get_modifier_groups

	_ensure_management_access()
	return _get_modifier_groups(item_name=item_name)


@frappe.whitelist()
def get_snappfood_bom_alternatives(item_name=""):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import get_snappfood_bom_alternatives as _get_bom_alternatives

	_ensure_management_access()
	return _get_bom_alternatives(item_name=item_name)


@frappe.whitelist()
def save_snappfood_modifier_mapping(payload=None):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import save_snappfood_modifier_mapping as _save_modifier_mapping

	_ensure_management_access()
	if isinstance(payload, str):
		payload = frappe.parse_json(payload or "{}")
	if not isinstance(payload, dict):
		payload = {}
	return _save_modifier_mapping(
		item_name=payload.get("item_name") or "",
		parent_item=payload.get("parent_item") or "",
		group_name=payload.get("group_name") or "",
		option_name=payload.get("option_name") or "",
		mapping_mode=payload.get("mapping_mode") or "modifier",
		product_id=payload.get("product_id") or "",
		external_id=payload.get("external_id") or "",
		variation_id=payload.get("variation_id") or "",
		product_hash_id=payload.get("product_hash_id") or "",
		variation_hash_id=payload.get("variation_hash_id") or "",
		menu_item_id=payload.get("menu_item_id") or "",
		bom_name=payload.get("bom_name") or "",
		ingredient_key=payload.get("ingredient_key") or "",
		alternative_item=payload.get("alternative_item") or "",
		product_level_identity=payload.get("product_level_identity"),
	)


def _make_credit_sales_invoice_without_payment(restaurant_api, sales_order_name):
	"""Submit a non-POS credit invoice without running payment reward hooks."""
	restaurant_api._ensure_sales_invoice_secondary_customer_field()
	make_sales_invoice = frappe.get_attr(
		"erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice"
	)
	sales_invoice = make_sales_invoice(sales_order_name)
	if isinstance(sales_invoice, dict):
		sales_invoice["is_pos"] = 0
		sales_invoice["update_stock"] = 0
		sales_invoice = frappe.get_doc(sales_invoice)
	else:
		sales_invoice.is_pos = 0
		sales_invoice.update_stock = 0

	if sales_invoice.meta.has_field("restaurant_secondary_customer"):
		sales_invoice.restaurant_secondary_customer = (
			frappe.db.get_value("Sales Order", sales_order_name, "restaurant_secondary_customer") or ""
		).strip()
	if sales_invoice.meta.has_field("dont_create_loyalty_points"):
		sales_invoice.dont_create_loyalty_points = 1
	if sales_invoice.meta.has_field("payments"):
		sales_invoice.payments = []

	from restaurant import api_club

	discount_account = api_club._club_club_settings().get("discount_expense_account")
	invoice_discount = float(
		sales_invoice.get("discount_amount") or sales_invoice.get("additional_discount_amount") or 0
	)
	if (
		discount_account
		and invoice_discount > 0
		and sales_invoice.meta.has_field("additional_discount_account")
	):
		sales_invoice.additional_discount_account = discount_account
		if sales_invoice.meta.has_field("is_cash_or_non_trade_discount"):
			sales_invoice.is_cash_or_non_trade_discount = 1

	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert()
	sales_invoice.submit()

	# Persist the unpaid credit state without invoking the settle hook that awards
	# cashback and points, even though no payment was received.
	restaurant_api._set_sales_order_payment_method(sales_order_name, "credit")
	restaurant_api._save_management_pos_payment(
		sales_order_name,
		{
			"method": "credit",
			"provider": "manual",
			"status": "pending",
			"reference_no": "",
			"rrn": "",
			"provider_payload": {},
		},
		run_auto_flow=False,
	)
	return sales_invoice


def _get_existing_order_financial_documents(sales_order_name):
	"""Return submitted invoices and payment records linked to a Sales Order."""
	invoice_items = frappe.get_all(
		"Sales Invoice Item",
		filters={"sales_order": sales_order_name, "docstatus": 1},
		fields=["parent"],
		ignore_permissions=True,
	)
	sales_invoices = sorted(
		{
			str(row.get("parent") or "").strip()
			for row in invoice_items
			if row.get("parent")
			and frappe.db.get_value("Sales Invoice", row.get("parent"), "docstatus") == 1
		}
	)

	payment_entry_names = set()
	if frappe.db.exists("DocType", "Payment Entry Reference"):
		references = [{"reference_doctype": "Sales Order", "reference_name": sales_order_name}]
		references.extend(
			{"reference_doctype": "Sales Invoice", "reference_name": invoice_name}
			for invoice_name in sales_invoices
		)
		for filters in references:
			rows = frappe.get_all(
				"Payment Entry Reference",
				filters={**filters, "docstatus": 1},
				fields=["parent"],
				ignore_permissions=True,
			)
			payment_entry_names.update(
				str(row.get("parent") or "").strip()
				for row in rows
				if row.get("parent")
			)
	payment_entries = sorted(
		name for name in payment_entry_names
		if frappe.db.get_value("Payment Entry", name, "docstatus") == 1
	)

	paid_payment_logs = []
	if frappe.db.exists("DocType", "Restaurant POS Payment Log"):
		paid_payment_logs = frappe.get_all(
			"Restaurant POS Payment Log",
			filters={
				"sales_order": sales_order_name,
				"status": ["in", ["paid", "settled", "success", "successful", "completed"]],
			},
			fields=["name", "status", "payment_method", "amount"],
			ignore_permissions=True,
		)

	return {
		"sales_invoices": sales_invoices,
		"payment_entries": payment_entries,
		"payment_logs": paid_payment_logs,
	}


@frappe.whitelist()
def process_snappfood_delivered_order(order_name="", order_id="", order_date=""):
	"""Complete production, delivery, and credit invoicing for one delivered order."""
	from restaurant import api as restaurant_api
	from restaurant.order_review import require_order_approved
	from restaurant.snapp_sync import preview_snapp_orders

	restaurant_api._ensure_management_access()
	order_name = str(order_name or "").strip()
	order_id = str(order_id or "").strip()
	try:
		order_date = frappe.utils.getdate(order_date).strftime("%Y-%m-%d")
	except Exception:
		return {
			"status": "error",
			"outcome": "invalid_date",
			"sales_order": order_name,
			"order_id": order_id,
			"message": "تاریخ انتخاب‌شده معتبر نیست.",
		}
	if not order_name or not order_id:
		return {
			"status": "error",
			"outcome": "invalid_order",
			"sales_order": order_name,
			"order_id": order_id,
			"message": "شناسهٔ سفارش Food Partner و سفارش فروش حسابیار الزامی است.",
		}

	try:
		preview = preview_snapp_orders(
			from_date=order_date,
			to_date=order_date,
			force_refresh=1,
		)
	except Exception as exc:
		return {
			"status": "error",
			"outcome": "partner_check_failed",
			"sales_order": order_name,
			"order_id": order_id,
			"message": "وضعیت سفارش از Food Partner دوباره دریافت نشد.",
			"error": str(exc),
		}
	if preview.get("status") == "error" or preview.get("error"):
		return {
			"status": "error",
			"outcome": "partner_check_failed",
			"sales_order": order_name,
			"order_id": order_id,
			"message": "وضعیت سفارش از Food Partner دوباره دریافت نشد.",
			"error": preview.get("error") or "",
		}
	partner_order = next(
		(
			row for row in (preview.get("orders") or [])
			if str(row.get("order_id") or "").strip() == order_id
		),
		None,
	)
	if not partner_order:
		return {
			"status": "skipped",
			"outcome": "not_found",
			"sales_order": order_name,
			"order_id": order_id,
			"message": "این سفارش در پاسخ Food Partner برای تاریخ انتخاب‌شده پیدا نشد.",
		}
	partner_status = str(partner_order.get("status") or "").strip().lower()
	if partner_status != "delivered":
		return {
			"status": "skipped",
			"outcome": "not_delivered",
			"sales_order": order_name,
			"order_id": order_id,
			"partner_status": partner_status,
			"message": "وضعیت Food Partner تحویل‌شده نیست؛ هیچ سندی ساخته نشد.",
		}

	so_name = restaurant_api._resolve_sales_order_name(order_name)
	if not so_name or not frappe.db.exists("Sales Order", so_name):
		return {
			"status": "skipped",
			"outcome": "sales_order_missing",
			"sales_order": order_name,
			"order_id": order_id,
			"message": "سفارش فروش مرتبط در حسابیار پیدا نشد.",
		}
	if not restaurant_api._lock_pos_sales_order(so_name, require_active=False):
		return {
			"status": "skipped",
			"outcome": "sales_order_missing",
			"sales_order": so_name,
			"order_id": order_id,
			"message": "سفارش فروش پیدا نشد یا برای قفل‌گذاری در دسترس نیست.",
		}

	so_doc = frappe.get_doc("Sales Order", so_name)
	if int(so_doc.docstatus or 0) != 1:
		return {
			"status": "skipped",
			"outcome": "sales_order_inactive",
			"sales_order": so_name,
			"order_id": order_id,
			"message": "سفارش فروش پیش‌نویس یا لغوشده است؛ هیچ سند تازه‌ای ساخته نشد.",
		}
	external_source = str(so_doc.get("restaurant_external_source") or "").strip().lower()
	external_order_id = str(so_doc.get("restaurant_external_order_id") or "").strip()
	if external_source != "snapp_food" or external_order_id != order_id:
		return {
			"status": "skipped",
			"outcome": "order_link_mismatch",
			"sales_order": so_name,
			"order_id": order_id,
			"message": "شناسهٔ Food Partner با سفارش فروش حسابیار تطبیق ندارد.",
		}
	try:
		require_order_approved(so_name)
	except Exception as exc:
		return {
			"status": "skipped",
			"outcome": "review_required",
			"sales_order": so_name,
			"order_id": order_id,
			"message": "سفارش حسابیار هنوز تأیید نشده است؛ تولید و فاکتور انجام نشد.",
			"error": str(exc),
		}
	sales_order_status = str(so_doc.status or "").strip().lower()
	if (
		sales_order_status in {"cancelled", "canceled"}
		or restaurant_api._core_order_status(so_doc)
		in {"cancelled", "canceled", "rejected", "voided"}
	):
		return {
			"status": "skipped",
			"outcome": "sales_order_cancelled",
			"sales_order": so_name,
			"order_id": order_id,
			"message": "سفارش فروش حسابیار لغوشده است؛ هیچ سندی ساخته نشد.",
		}

	result = {
		"status": "error",
		"outcome": "incomplete",
		"sales_order": so_name,
		"order_id": order_id,
		"work_orders": [],
		"stock_entries": [],
		"delivery_note": "",
		"sales_invoice": "",
		"outstanding_amount": None,
	}
	try:
		financial_documents = _get_existing_order_financial_documents(so_name)
	except Exception as exc:
		return {
			**result,
			"outcome": "financial_check_failed",
			"message": "بررسی سوابق فاکتور و پرداخت سفارش ناموفق بود؛ برای جلوگیری از ثبت تکراری هیچ سندی ساخته نشد.",
			"error": str(exc),
		}

	payment_status = "".join(
		character
		for character in str(so_doc.get("restaurant_payment_status") or "").strip().lower()
		if character.isalnum()
	)
	paid_payment_statuses = {"paid", "settled", "partiallypaid", "partialpaid"}
	if (
		financial_documents["sales_invoices"]
		or financial_documents["payment_entries"]
		or financial_documents["payment_logs"]
		or payment_status in paid_payment_statuses
	):
		payment_log_names = [
			row.get("name")
			for row in financial_documents["payment_logs"]
			if row.get("name")
		]
		result.update(
			{
				"status": "review",
				"outcome": "existing_financial_record",
				"sales_invoices": financial_documents["sales_invoices"],
				"payment_entries": financial_documents["payment_entries"],
				"payment_logs": payment_log_names,
				"payment_status": payment_status,
				"message": "برای این سفارش سابقهٔ فاکتور یا پرداخت وجود دارد؛ تولید، رسید تحویل و فاکتور جدید ساخته نشد و سفارش برای بررسی جدا شد.",
			}
		)
		return result
	if sales_order_status in {"closed", "completed", "complete"}:
		result.update(
			{
				"status": "skipped",
				"outcome": "sales_order_inactive",
				"message": "سفارش فروش بسته یا تکمیل‌شده است و سابقهٔ مالیِ نیازمند بررسی پیدا نشد؛ سند تازه‌ای ساخته نشد.",
			}
		)
		return result

	try:
		previous_reward_skip = getattr(
			frappe.flags,
			"skip_unpaid_foodpartner_fulfillment_rewards",
			False,
		)
		frappe.flags.skip_unpaid_foodpartner_fulfillment_rewards = True
		try:
			auto_flow = restaurant_api._run_sales_order_auto_flow(
				so_name,
				trigger="manual",
				force=True,
				allow_negative_stock=True,
			)
		finally:
			frappe.flags.skip_unpaid_foodpartner_fulfillment_rewards = previous_reward_skip
		result["stock_entries"] = auto_flow.get("stock_entries") or []
		result["work_orders"] = restaurant_api._management_work_orders_by_sales_order([so_name]).get(so_name, [])
		if not auto_flow.get("ready_for_delivery"):
			result["outcome"] = "production_blocked"
			result["message"] = "تولید این سفارش هنوز آمادهٔ تحویل نیست؛ رسید تحویل و فاکتور ساخته نشد."
			result["error"] = "؛ ".join(str(error) for error in (auto_flow.get("errors") or []) if error)
			frappe.db.commit()
			return result

		frappe.db.savepoint("snapp_daily_delivery")
		try:
			delivery_note_name = str(auto_flow.get("delivery_note") or "").strip()
			if delivery_note_name and frappe.db.exists("Delivery Note", delivery_note_name):
				delivery_note_doc = frappe.get_doc("Delivery Note", delivery_note_name)
				if int(delivery_note_doc.docstatus or 0) == 0:
					restaurant_api._submit_stock_document(delivery_note_doc, allow_negative_stock=True)
				if int(delivery_note_doc.docstatus or 0) == 1:
					result["delivery_note"] = delivery_note_name
			if not result["delivery_note"]:
				delivery_note_name = restaurant_api._create_delivery_note_for_sales_order(
					so_name,
					fg_warehouse_map=auto_flow.get("fg_warehouse_map") or {},
					submit_doc=True,
					allow_negative_stock=True,
				)
				result["delivery_note"] = str(delivery_note_name or "").strip()
			fulfilled, delivery_note_names = restaurant_api._sales_order_stock_fulfillment(so_name)
			if not fulfilled:
				frappe.db.rollback(save_point="snapp_daily_delivery")
				_, persisted_delivery_notes = restaurant_api._sales_order_stock_fulfillment(so_name)
				result["delivery_note"] = persisted_delivery_notes[0] if persisted_delivery_notes else ""
				result["outcome"] = "delivery_incomplete"
				result["message"] = "رسید تحویل ثبت‌شده، همهٔ اقلام انبارشوندهٔ سفارش را پوشش نمی‌دهد. فاکتور فروش ساخته نشد."
				frappe.db.commit()
				return result
			if not result["delivery_note"] and delivery_note_names:
				result["delivery_note"] = delivery_note_names[0]
		except Exception as exc:
			frappe.db.rollback(save_point="snapp_daily_delivery")
			_, persisted_delivery_notes = restaurant_api._sales_order_stock_fulfillment(so_name)
			result.update(
				{
					"outcome": "delivery_failed",
					"delivery_note": persisted_delivery_notes[0] if persisted_delivery_notes else "",
					"message": "تولید انجام شد، اما ثبت رسید تحویل ناموفق بود؛ فاکتور فروش ساخته نشد.",
					"error": str(exc),
				}
			)
			frappe.db.commit()
			return result

		try:
			restaurant_api._set_restaurant_order_status(so_name, "delivered", force=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Food Partner Daily Order Status ({so_name})")

		frappe.db.savepoint("snapp_daily_invoice")
		try:
			sales_invoice_doc = _make_credit_sales_invoice_without_payment(
				restaurant_api,
				so_name,
			)
		except Exception as exc:
			frappe.db.rollback(save_point="snapp_daily_invoice")
			result.update(
				{
					"outcome": "invoice_failed",
					"message": "تولید و رسید تحویل ثبت شد، اما فاکتور فروش اعتباری ساخته نشد.",
					"error": str(exc),
				}
			)
			frappe.db.commit()
			return result
		sales_invoice_name = str(sales_invoice_doc.name or "").strip()
		if not sales_invoice_name or not frappe.db.exists("Sales Invoice", sales_invoice_name):
			frappe.db.rollback(save_point="snapp_daily_invoice")
			result["outcome"] = "invoice_missing"
			result["message"] = "فاکتور فروش اعتباری ایجاد نشد؛ رسید تحویل ثبت شد."
			frappe.db.commit()
			return result
		try:
			sales_invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice_name)
			outstanding_amount = float(
				frappe.db.get_value("Sales Invoice", sales_invoice_name, "outstanding_amount") or 0
			)
			payment_entry_rows = frappe.get_all(
				"Payment Entry Reference",
				filters={"reference_name": sales_invoice_name, "docstatus": 1},
				fields=["parent"],
				ignore_permissions=True,
			)
		except Exception as exc:
			frappe.db.rollback(save_point="snapp_daily_invoice")
			result["outcome"] = "invoice_validation_failed"
			result["message"] = "فاکتور ساخته شد، اما بررسی نهاییِ اعتباری و بدون‌پرداخت‌بودن آن ناموفق بود؛ رسید تحویل حفظ شد."
			result["error"] = str(exc)
			frappe.db.commit()
			return result
		if (
			int(sales_invoice_doc.docstatus or 0) != 1
			or int(sales_invoice_doc.get("is_pos") or 0) != 0
			or outstanding_amount <= 0
			or bool(sales_invoice_doc.get("payments"))
			or payment_entry_rows
		):
			frappe.db.rollback(save_point="snapp_daily_invoice")
			result["outcome"] = "invoice_not_credit"
			result["message"] = "فاکتور ساخته‌شده شرایط فاکتور اعتباریِ بدون پرداخت را ندارد؛ برای جلوگیری از ثبت نادرست بررسی کنید."
			frappe.db.commit()
			return result
		result.update(
			{
				"status": "success",
				"outcome": "completed",
				"sales_invoice": sales_invoice_name,
				"outstanding_amount": outstanding_amount,
				"message": "تولید، رسید تحویل و فاکتور فروش اعتباری ثبت شد؛ پرداختی ایجاد نشد.",
			}
		)
		frappe.db.commit()
		return result
	except Exception as exc:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Food Partner Daily Fulfillment")
		result.update(
			{
				"work_orders": [],
				"stock_entries": [],
				"delivery_note": "",
				"sales_invoice": "",
				"outstanding_amount": None,
				"rolled_back": True,
			}
		)
		result["outcome"] = "operation_failed"
		result["message"] = "عملیات این سفارش کامل نشد و تغییرات این اجرا بازگردانده شد؛ دوباره بررسی کنید."
		result["error"] = str(exc)
		return result
