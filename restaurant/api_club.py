# Copyright (c) 2026, Restaurant and contributors
"""Customer club, SMS, wallet/cashback, referral, campaigns and surveys.

Reuses ERPNext base doctypes wherever they exist (``Customer`` holds the
membership/referral/tier fields, ``Mode of Payment`` for wallet payments,
``Notification Log`` for dissatisfaction alerts). Restaurant-specific doctypes
(wallets, wallet transactions, SMS log, campaigns, survey questions/responses)
only exist because ERPNext has no equivalent.

All endpoints are re-exported into ``restaurant.api`` via the star-import at
the bottom of ``api.py`` and are called by the SPA as
``/api/method/restaurant.api.<endpoint>``.
"""

import json
import random

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime, today

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_ensure_management_access,
	_has_column,
	_table_columns_from_rows,
)

__all__ = [
	"CLUB_REPORT_KEYS",
	"club_build_report_bi",
	"DEFAULT_SMS_TEMPLATES",
	"CUSTOMER_KINDS",
	"VOICE_TYPES",
	"VOICE_STATUSES",
	# provisioning / jobs
	"_club_ensure_ops_ready",
	"run_daily_customer_club_jobs",
	"club_apply_settle_effects",
	"club_apply_fulfillment_effects",
	# boot
	"get_management_club_boot",
	"update_management_club_settings",
	# customers & membership
	"list_management_club_customers",
	"save_management_club_customer",
	"assign_management_membership_codes",
	"export_management_customers_excel",
	"import_management_customers_excel",
	# tiers & segmentation
	"compute_management_customer_segments",
	# sms
	"get_management_sms_templates",
	"set_management_sms_templates",
	"send_management_sms",
	"list_management_sms_messages",
	"get_management_sms_kind_stats",
	# customer voice (complaints & suggestions)
	"list_management_customer_voices",
	"save_management_customer_voice",
	"update_management_customer_voice_status",
	"delete_management_customer_voice",
	"submit_public_voice",
	# loyalty points
	"list_management_point_entries",
	"redeem_management_points",
	"adjust_management_points",
	"redeem_my_points",
	"get_customer_club_summary",
	# wallet
	"list_management_wallets",
	"get_management_wallet_detail",
	"charge_management_wallet",
	"transfer_management_wallet",
	"adjust_management_wallet",
	# referral
	"get_management_referral_summary",
	# campaigns
	"list_management_campaigns",
	"save_management_campaign",
	"update_management_campaign_status",
	"get_management_campaign_stats",
	"list_management_coupons",
	"save_management_coupon",
	# surveys (management + public)
	"list_management_survey_questions",
	"save_management_survey_question",
	"delete_management_survey_question",
	"get_public_survey",
	"submit_public_survey",
	"list_management_survey_responses",
	# reports
	"get_management_report_customer_analytics",
	"get_management_report_campaign_performance",
	"get_management_report_wallet_summary",
	"get_management_report_credit_transactions",
	"get_management_report_care_feedback",
	"get_management_report_survey_analytics",
]

CLUB_DOCTYPES = {
	"wallet": "Restaurant Customer Wallet",
	"wallet_txn": "Restaurant Wallet Transaction",
	"sms": "Restaurant SMS Message",
	"campaign": "Restaurant Campaign",
	"survey_question": "Restaurant Survey Question",
	"survey_response": "Restaurant Survey Response",
	"voice": "Restaurant Customer Voice",
	"point_entry": "Restaurant Loyalty Point Entry",
}

CUSTOMER_TIERS = ["VIP", "عمده‌فروش", "عادی", "جدید"]
CUSTOMER_SEGMENTS = ["جدید", "وفادار", "بالقوه", "در خطر ریزش", "خفته"]
CUSTOMER_KINDS = ["حقیقی", "حقوقی", "سازمانی"]
VOICE_TYPES = ["شکایت", "انتقاد", "پیشنهاد", "درخواست", "تقدیر"]
VOICE_STATUSES = ["جدید", "در حال رسیدگی", "پاسخ داده‌شده", "بسته"]
POINT_KINDS = ["کسب", "استفاده", "تبدیل به اعتبار", "انقضا", "تعدیل دستی"]
LOYALTY_TIERS = ["طلایی", "نقره‌ای", "برنزی"]
# منشور ارتباط با مشتری: گروه‌بندی آماری پیامک‌ها
SMS_KIND_CLASSES = {
	"تبلیغاتی": ["کمپین", "انبوه"],
	"اطلاع‌رسانی": ["دستی", "خوش‌آمدگویی", "تبریک تولد"],
	"یادآوری": ["یادآوری خرید"],
}
SMS_KINDS = ["دستی", "انبوه", "تبریک تولد", "خوش‌آمدگویی", "یادآوری خرید", "کمپین"]
SMS_STATUS = ["در صف", "ارسال‌شده", "ناموفق", "بدون درگاه"]
CAMPAIGN_STATUSES = ["پیش‌نویس", "فعال", "متوقف", "پایان‌یافته"]
CAMPAIGN_BONUS_TYPES = ["تخفیف", "کش‌بک", "امتیاز"]
WALLET_KINDS = ["شارژ", "پرداخت", "کش‌بک", "پاداش معرف", "انتقال ارسال", "انتقال دریافت", "تعدیل دستی", "تبدیل امتیاز"]
CLUB_REPORT_KEYS = {
	"customer-analytics",
	"campaign-performance",
	"wallet-summary",
	"credit-transactions",
	"care-feedback",
	"survey-analytics",
}

DEFAULT_SMS_TEMPLATES = {
	"welcome": "سلام {name} عزیز! به باشگاه مشتریان ما خوش آمدید. کد اشتراک شما: {membership_code}",
	"birthday": "{name} عزیز، تولدتان مبارک! اعضای باشگاه مشتریان ما امروز یک هدیه ویژه برای شما دارند.",
	"inactive": "{name} عزیز، مدتی است که ندیدیمتان! برای بازگشت شما پیشنهاد ویژه داریم.",
	"bulk_default": "سلام {name} عزیز، {message}",
}


# ---------------------------------------------------------------------------
# Lazy bridges (import-cycle safety — see api_inventory for the full story)
# ---------------------------------------------------------------------------


def _club_fp_call(helper_name, *args, **kwargs):
	from restaurant import api_feature_pack

	return getattr(api_feature_pack, helper_name)(*args, **kwargs)


def _club_parse_json(value, fallback=None):
	if fallback is None:
		fallback = {}
	if isinstance(value, (dict, list)):
		return value if isinstance(value, type(fallback)) or not isinstance(fallback, (dict, list)) else value
	try:
		parsed = json.loads(str(value or "").strip() or "null")
	except Exception:
		return fallback
	return parsed if parsed is not None else fallback


def _club_parse_payload(payload):
	if payload is None:
		payload = {}
	if isinstance(payload, str):
		payload = _club_parse_json(payload, {})
	if not isinstance(payload, dict):
		try:
			payload = dict(frappe.form_dict or {})
		except Exception:
			payload = {}
	return payload or {}


def _club_list(value):
	if isinstance(value, str):
		parsed = _club_parse_json(value, [])
		if isinstance(parsed, list):
			return parsed
		return [row.strip() for row in value.split(",") if row.strip()]
	return list(value or []) if isinstance(value, (list, tuple)) else []


# ---------------------------------------------------------------------------
# Custom field provisioning (runtime, idempotent)
# ---------------------------------------------------------------------------


def _club_ensure_customer_fields():
	_club_fp_call(
		"_fp_ensure_custom_fields",
		"Customer",
		[
			{"fieldname": "restaurant_club_section", "label": _("باشگاه مشتریان"), "fieldtype": "Section Break"},
			{"fieldname": "restaurant_membership_code", "label": _("کد اشتراک"), "fieldtype": "Data", "unique": 1},
			{"fieldname": "restaurant_birth_date", "label": _("تاریخ تولد"), "fieldtype": "Date"},
			{"fieldname": "restaurant_customer_tier", "label": _("سطح مشتری"), "fieldtype": "Select", "options": "\n" + "\n".join(CUSTOMER_TIERS)},
			{"fieldname": "restaurant_customer_segment", "label": _("خوشه رفتاری"), "fieldtype": "Select", "options": "\n" + "\n".join(CUSTOMER_SEGMENTS), "in_list_view": 0},
			{"fieldname": "restaurant_referral_code", "label": _("کد معرف"), "fieldtype": "Data", "unique": 1},
			{"fieldname": "restaurant_referred_by", "label": _("معرف (مشتری)"), "fieldtype": "Link", "options": "Customer"},
			{"fieldname": "restaurant_customer_kind", "label": _("نوع مشتری"), "fieldtype": "Select", "options": "\n" + "\n".join(CUSTOMER_KINDS)},
			{"fieldname": "restaurant_organization", "label": _("سازمان مادر"), "fieldtype": "Link", "options": "Customer"},
			{"fieldname": "restaurant_loyalty_points", "label": _("امتیاز وفاداری"), "fieldtype": "Int", "read_only": 1},
		],
		anchor_candidates=["customer_details", "mobile_no", "customer_name"],
	)


def _club_ensure_sales_order_fields():
	_club_fp_call(
		"_fp_ensure_custom_fields",
		"Sales Order",
		[
			{"fieldname": "restaurant_referral_code", "label": _("کد معرف استفاده‌شده"), "fieldtype": "Data"},
			{"fieldname": "restaurant_cashback_credited", "label": _("کش‌بک اعمال شد"), "fieldtype": "Check"},
			{"fieldname": "restaurant_kitchen_started_at", "label": _("شروع آماده‌سازی"), "fieldtype": "Datetime"},
			{"fieldname": "restaurant_kitchen_ready_at", "label": _("آماده شد"), "fieldtype": "Datetime"},
			{"fieldname": "restaurant_points_earned", "label": _("امتیاز کسب‌شده"), "fieldtype": "Int"},
			{"fieldname": "restaurant_organization", "label": _("سازمان"), "fieldtype": "Link", "options": "Customer"},
			{"fieldname": "restaurant_org_member", "label": _("معین سازمانی"), "fieldtype": "Data"},
			{"fieldname": "restaurant_waiter", "label": _("گارسون"), "fieldtype": "Link", "options": "User"},
			{"fieldname": "restaurant_waiter_name", "label": _("نام گارسون"), "fieldtype": "Data"},
		],
		anchor_candidates=["restaurant_packaging_fee", "restaurant_status"],
	)


def _club_ensure_settings_fields():
	_club_fp_call(
		"_fp_ensure_custom_fields",
		"Restaurant Web Settings",
		[
			{"fieldname": "restaurant_club_section", "label": _("باشگاه مشتریان و وفاداری"), "fieldtype": "Section Break"},
			{"fieldname": "restaurant_club_enabled", "label": _("باشگاه مشتریان فعال است"), "fieldtype": "Check", "default": "1"},
			{"fieldname": "restaurant_cashback_percent", "label": _("درصد کش‌بک خرید"), "fieldtype": "Percent"},
			{"fieldname": "restaurant_cashback_min_order", "label": _("حداقل فاکتور برای کش‌بک"), "fieldtype": "Currency"},
			{"fieldname": "restaurant_wallet_mode_of_payment", "label": _("روش پرداخت کیف پول"), "fieldtype": "Link", "options": "Mode of Payment"},
			{"fieldname": "restaurant_referral_referrer_reward", "label": _("پاداش معرف"), "fieldtype": "Currency"},
			{"fieldname": "restaurant_referral_referee_reward", "label": _("پاداش شخص معرفی‌شده"), "fieldtype": "Currency"},
			{"fieldname": "restaurant_sms_enabled", "label": _("ارسال پیامک فعال است"), "fieldtype": "Check"},
			{"fieldname": "restaurant_sms_templates_json", "label": _("قالب‌های پیامک (JSON)"), "fieldtype": "Long Text"},
			{"fieldname": "restaurant_survey_alert_threshold", "label": _("آستانه هشدار نارضایتی (امتیاز)"), "fieldtype": "Int", "default": "3"},
			{"fieldname": "restaurant_survey_alert_users_json", "label": _("کاربران دریافت‌کننده هشدار نظرسنجی (JSON)"), "fieldtype": "Long Text"},
			{"fieldname": "restaurant_points_section", "label": _("سیستم امتیازدهی وفاداری"), "fieldtype": "Section Break"},
			{"fieldname": "restaurant_points_enabled", "label": _("امتیازدهی فعال است"), "fieldtype": "Check"},
			{"fieldname": "restaurant_points_rial_per_point", "label": _("هر چند ریال خرید = ۱ امتیاز"), "fieldtype": "Currency"},
			{"fieldname": "restaurant_points_rial_value", "label": _("ارزش هر امتیاز هنگام استفاده (ریال)"), "fieldtype": "Currency"},
			{"fieldname": "restaurant_points_expiry_days", "label": _("مدت اعتبار امتیاز (روز، ۰ = بدون انقضا)"), "fieldtype": "Int"},
			{"fieldname": "restaurant_points_min_redeem", "label": _("حداقل امتیاز قابل استفاده"), "fieldtype": "Int"},
			{"fieldname": "restaurant_points_gold_threshold", "label": _("آستانه طلایی (امتیاز)"), "fieldtype": "Int"},
			{"fieldname": "restaurant_points_silver_threshold", "label": _("آستانه نقره‌ای (امتیاز)"), "fieldtype": "Int"},
			{"fieldname": "restaurant_points_bronze_threshold", "label": _("آستانه برنزی (امتیاز)"), "fieldtype": "Int"},
		],
		anchor_candidates=["restaurant_inventory_section", "restaurant_ops_feature_section"],
	)


def _club_ensure_ops_ready():
	_club_ensure_customer_fields()
	_club_ensure_sales_order_fields()
	_club_ensure_settings_fields()


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------


def _club_setting(fieldname, default=""):
	try:
		return frappe.db.get_single_value("Restaurant Web Settings", fieldname) or default
	except Exception:
		return default


def _club_set_setting(fieldname, value):
	frappe.db.set_single_value("Restaurant Web Settings", fieldname, value, update_modified=True)


def _club_get_sms_templates():
	raw = _club_setting("restaurant_sms_templates_json", "")
	custom = _club_parse_json(raw, {})
	templates = dict(DEFAULT_SMS_TEMPLATES)
	if isinstance(custom, dict):
		for key, value in custom.items():
			if isinstance(value, str) and value.strip():
				templates[key] = value.strip()
	return templates


def _club_club_settings():
	alert_users = _club_parse_json(_club_setting("restaurant_survey_alert_users_json", ""), [])
	return {
		"club_enabled": cint(_club_setting("restaurant_club_enabled", 1)) == 1,
		"cashback_percent": flt(_club_setting("restaurant_cashback_percent", 0)),
		"cashback_min_order": flt(_club_setting("restaurant_cashback_min_order", 0)),
		"wallet_mode_of_payment": (_club_setting("restaurant_wallet_mode_of_payment", "") or "").strip(),
		"referral_referrer_reward": flt(_club_setting("restaurant_referral_referrer_reward", 0)),
		"referral_referee_reward": flt(_club_setting("restaurant_referral_referee_reward", 0)),
		"sms_enabled": cint(_club_setting("restaurant_sms_enabled", 0)) == 1,
		"sms_templates": _club_get_sms_templates(),
		"survey_alert_threshold": cint(_club_setting("restaurant_survey_alert_threshold", 3)) or 3,
		"survey_alert_users": alert_users if isinstance(alert_users, list) else [],
		"points_enabled": cint(_club_setting("restaurant_points_enabled", 0)) == 1,
		"points_rial_per_point": flt(_club_setting("restaurant_points_rial_per_point", 100000)) or 100000,
		"points_rial_value": flt(_club_setting("restaurant_points_rial_value", 5000)) or 5000,
		"points_expiry_days": cint(_club_setting("restaurant_points_expiry_days", 180)),
		"points_min_redeem": cint(_club_setting("restaurant_points_min_redeem", 0)),
		"points_gold_threshold": cint(_club_setting("restaurant_points_gold_threshold", 500)) or 500,
		"points_silver_threshold": cint(_club_setting("restaurant_points_silver_threshold", 200)) or 200,
		"points_bronze_threshold": cint(_club_setting("restaurant_points_bronze_threshold", 50)) or 50,
		"customer_kinds": CUSTOMER_KINDS,
		"voice_types": VOICE_TYPES,
		"voice_statuses": VOICE_STATUSES,
		"sms_kind_classes": sorted(SMS_KIND_CLASSES.keys()),
	}


_SAVEABLE_CLUB_SETTINGS = [
	"restaurant_club_enabled",
	"restaurant_cashback_percent",
	"restaurant_cashback_min_order",
	"restaurant_wallet_mode_of_payment",
	"restaurant_referral_referrer_reward",
	"restaurant_points_enabled",
	"restaurant_points_rial_per_point",
	"restaurant_points_rial_value",
	"restaurant_points_expiry_days",
	"restaurant_points_min_redeem",
	"restaurant_points_gold_threshold",
	"restaurant_points_silver_threshold",
	"restaurant_points_bronze_threshold",
	"restaurant_referral_referee_reward",
	"restaurant_sms_enabled",
	"restaurant_survey_alert_threshold",
]


# ---------------------------------------------------------------------------
# Customer helpers (ERPNext Customer)
# ---------------------------------------------------------------------------


def _club_customer_mobile(customer_name):
	if not customer_name:
		return ""
	for fieldname in ("mobile_no", "customer_primary_mobile"):
		if _has_column("Customer", fieldname):
			value = frappe.db.get_value("Customer", customer_name, fieldname)
			if value:
				return (value or "").strip()
	return ""


def _club_customer_extra_fields():
	fields = []
	for fieldname in (
		"restaurant_membership_code",
		"restaurant_birth_date",
		"restaurant_customer_tier",
		"restaurant_customer_segment",
		"restaurant_referral_code",
		"restaurant_referred_by",
		"restaurant_customer_kind",
		"restaurant_organization",
		"mobile_no",
		"customer_primary_mobile",
	):
		if _has_column("Customer", fieldname):
			fields.append(fieldname)
	return fields


def _club_unique_code(prefix, fieldname, length=6):
	for _attempt in range(20):
		code = "{}-{}".format(prefix, "".join(str(random.randint(0, 9)) for _ in range(length)))
		if not frappe.db.exists("Customer", {fieldname: code}):
			return code
	return "{}-{}".format(prefix, frappe.generate_hash(length=8).upper())


def _club_assign_membership_code(customer_name):
	code = ""
	if _has_column("Customer", "restaurant_membership_code"):
		code = (frappe.db.get_value("Customer", customer_name, "restaurant_membership_code") or "").strip()
	if not code and _has_column("Customer", "restaurant_membership_code"):
		code = _club_unique_code("MBR", "restaurant_membership_code")
		frappe.db.set_value("Customer", customer_name, "restaurant_membership_code", code, update_modified=False)
	return code


def _club_assign_referral_code(customer_name):
	code = ""
	if _has_column("Customer", "restaurant_referral_code"):
		code = (frappe.db.get_value("Customer", customer_name, "restaurant_referral_code") or "").strip()
	if not code and _has_column("Customer", "restaurant_referral_code"):
		code = _club_unique_code("REF", "restaurant_referral_code")
		frappe.db.set_value("Customer", customer_name, "restaurant_referral_code", code, update_modified=False)
	return code


def _club_customer_stats_batch(customer_names):
	"""{customer: {orders, total_spent, first_order, last_order}} from submitted Sales Orders."""
	names = [name for name in set(customer_names or []) if name]
	if not names or not frappe.db.exists("DocType", "Sales Order"):
		return {}
	rows = frappe.db.sql(
		"""
		SELECT customer, COUNT(*) AS orders, COALESCE(SUM(grand_total),0) AS total_spent,
			   MIN(transaction_date) AS first_order, MAX(transaction_date) AS last_order
		FROM `tabSales Order`
		WHERE customer IN %(names)s AND docstatus = 1 AND status != 'Cancelled'
		GROUP BY customer
		""",
		{"names": tuple(names)},
		as_dict=True,
	)
	result = {}
	for row in rows:
		result[row["customer"]] = {
			"orders": cint(row.get("orders")),
			"total_spent": flt(row.get("total_spent")),
			"first_order": str(row.get("first_order") or ""),
			"last_order": str(row.get("last_order") or ""),
		}
	return result


def _club_wallet_map(customer_names):
	names = [name for name in set(customer_names or []) if name]
	if not names or not frappe.db.exists("DocType", CLUB_DOCTYPES["wallet"]):
		return {}
	rows = frappe.get_all(
		CLUB_DOCTYPES["wallet"],
		filters={"customer": ["in", names]},
		fields=["customer", "name", "balance", "total_charged", "total_spent", "status"],
	)
	return {row["customer"]: row for row in rows}


# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_club_boot():
	_ensure_management_access()
	_club_ensure_ops_ready()

	customers_total = frappe.db.count("Customer", {"disabled": 0}) or 0
	members = 0
	if _has_column("Customer", "restaurant_membership_code"):
		members = frappe.db.count(
			"Customer", [["disabled", "=", 0], ["restaurant_membership_code", "!=", ""]]
		) or 0

	wallet_balance = 0.0
	wallets_count = 0
	if frappe.db.exists("DocType", CLUB_DOCTYPES["wallet"]):
		row = frappe.db.sql(
			"SELECT COUNT(*) AS count, COALESCE(SUM(balance),0) AS balance FROM `tabRestaurant Customer Wallet`",
			as_dict=True,
		)
		wallets_count = cint(row[0].get("count")) if row else 0
		wallet_balance = flt(row[0].get("balance")) if row else 0.0

	sms_sent_month = 0
	sms_failed_month = 0
	if frappe.db.exists("DocType", CLUB_DOCTYPES["sms"]):
		rows = frappe.get_all(
			CLUB_DOCTYPES["sms"],
			filters={"sent_at": [">=", add_days(today(), -30)]},
			fields=["status", "COUNT(*) AS count"],
			group_by="status",
		)
		for row in rows:
			if row.get("status") == "ارسال‌شده":
				sms_sent_month = cint(row.get("count"))
			elif row.get("status") in ("ناموفق", "بدون درگاه"):
				sms_failed_month += cint(row.get("count"))

	active_campaigns = frappe.db.count(CLUB_DOCTYPES["campaign"], {"status": "فعال"}) or 0

	survey_avg = 0.0
	survey_count = 0
	if frappe.db.exists("DocType", CLUB_DOCTYPES["survey_response"]):
		row = frappe.db.sql(
			"""
			SELECT COUNT(*) AS count, COALESCE(AVG(overall_rating),0) AS avg_rating
			FROM `tabRestaurant Survey Response`
			WHERE entry_date >= %(df)s
			""",
			{"df": add_days(now_datetime(), -30)},
			as_dict=True,
		)
		survey_count = cint(row[0].get("count")) if row else 0
		survey_avg = flt(row[0].get("avg_rating"), 1) if row else 0.0

	voices_open = 0
	voices_total_month = 0
	if frappe.db.exists("DocType", CLUB_DOCTYPES["voice"]):
		voices_open = frappe.db.count(CLUB_DOCTYPES["voice"], {"status": ["in", ["جدید", "در حال رسیدگی"]]}) or 0
		voices_total_month = frappe.db.count(
			CLUB_DOCTYPES["voice"], {"creation": [">=", add_days(now_datetime(), -30)]}
		) or 0

	points_outstanding = 0
	if frappe.db.exists("DocType", CLUB_DOCTYPES["point_entry"]):
		row = frappe.db.sql(
			"SELECT COALESCE(SUM(points),0) AS balance FROM `tabRestaurant Loyalty Point Entry`",
			as_dict=True,
		)
		points_outstanding = cint(row[0].get("balance")) if row else 0

	customers_org = 0
	if _has_column("Customer", "restaurant_customer_kind"):
		customers_org = frappe.db.count("Customer", {"disabled": 0, "restaurant_customer_kind": "سازمانی"}) or 0

	return {
		"kpis": {
			"customers_total": cint(customers_total),
			"members_with_code": cint(members),
			"customers_org": cint(customers_org),
			"wallets_count": wallets_count,
			"wallet_balance_total": wallet_balance,
			"sms_sent_30d": sms_sent_month,
			"sms_failed_30d": sms_failed_month,
			"active_campaigns": cint(active_campaigns),
			"survey_count_30d": survey_count,
			"survey_avg_30d": survey_avg,
			"voices_open": cint(voices_open),
			"voices_30d": cint(voices_total_month),
			"points_outstanding": cint(points_outstanding),
		},
		"settings": _club_club_settings(),
		"tiers": CUSTOMER_TIERS,
		"segments": CUSTOMER_SEGMENTS,
		"sms_kinds": SMS_KINDS,
		"campaign_statuses": CAMPAIGN_STATUSES,
		"campaign_bonus_types": CAMPAIGN_BONUS_TYPES,
		"wallet_kinds": WALLET_KINDS,
		"mode_of_payments": frappe.get_all("Mode of Payment", pluck="name", order_by="name", limit_page_length=100),
	}


# ---------------------------------------------------------------------------
# Customers & membership codes
# ---------------------------------------------------------------------------


@frappe.whitelist()
def update_management_club_settings(payload=None):
	"""Update loyalty settings (cashback, wallet MoP, referral rewards, alert threshold)."""
	_ensure_management_access()
	_club_ensure_settings_fields()
	payload = _club_parse_json(payload, {})
	collected = {}
	for key in _SAVEABLE_CLUB_SETTINGS:
		if key not in payload:
			continue
		value = payload.get(key)
		if key in ("restaurant_club_enabled", "restaurant_sms_enabled", "restaurant_points_enabled"):
			value = cint(value)
		elif key == "restaurant_survey_alert_threshold":
			value = min(max(cint(value), 1), 5) or 3
		elif key in ("restaurant_cashback_percent", "restaurant_cashback_min_order", "restaurant_referral_referrer_reward", "restaurant_referral_referee_reward", "restaurant_points_rial_per_point", "restaurant_points_rial_value"):
			value = flt(value)
		elif key in ("restaurant_points_expiry_days", "restaurant_points_min_redeem", "restaurant_points_gold_threshold", "restaurant_points_silver_threshold", "restaurant_points_bronze_threshold"):
			value = max(cint(value), 0)
		elif key == "restaurant_wallet_mode_of_payment":
			value = (value or "").strip()
			if value and not frappe.db.exists("Mode of Payment", value):
				frappe.throw(_("روش پرداخت یافت نشد: {0}").format(value))
		_club_set_setting(key, value)
		collected[key] = value
	if "restaurant_survey_alert_users_json" in payload:
		users = payload.get("restaurant_survey_alert_users_json")
		if not isinstance(users, list):
			users = _club_list(users)
		_club_set_setting("restaurant_survey_alert_users_json", json.dumps(users, ensure_ascii=False))
		collected["restaurant_survey_alert_users_json"] = users
	frappe.db.commit()
	return {"status": "success", "saved": collected, "settings": _club_club_settings()}


@frappe.whitelist()
def list_management_club_customers(search="", tier="", segment="", kind="", organization="", limit=100, offset=0):
	"""Customers with membership code, tier, segment, wallet and purchase stats."""
	_ensure_management_access()
	limit = min(max(cint(limit) or 100, 1), 500)
	offset = max(cint(offset) or 0, 0)

	fields = ["name", "customer_name", "disabled"] + _club_customer_extra_fields()
	where = ["disabled = 0"]
	params = {"limit": limit, "offset": offset}
	search = (search or "").strip()
	if search:
		clauses = ["customer_name LIKE %(needle)s", "name LIKE %(needle)s"]
		for mobile_col in ("mobile_no", "customer_primary_mobile"):
			if mobile_col in fields:
				clauses.append(f"COALESCE({mobile_col},'') LIKE %(needle)s")
		where.append("(" + " OR ".join(clauses) + ")")
		params["needle"] = f"%{search}%"
	if tier and _has_column("Customer", "restaurant_customer_tier"):
		where.append("COALESCE(restaurant_customer_tier,'') = %(tier)s")
		params["tier"] = tier
	if segment and _has_column("Customer", "restaurant_customer_segment"):
		where.append("COALESCE(restaurant_customer_segment,'') = %(segment)s")
		params["segment"] = segment
	if kind and _has_column("Customer", "restaurant_customer_kind"):
		where.append("COALESCE(restaurant_customer_kind,'') = %(kind)s")
		params["kind"] = kind
	if organization and _has_column("Customer", "restaurant_organization"):
		where.append("COALESCE(restaurant_organization,'') = %(organization)s")
		params["organization"] = organization

	rows = frappe.db.sql(
		"""
		SELECT {select_fields}
		FROM `tabCustomer`
		WHERE {where}
		ORDER BY customer_name
		LIMIT %(limit)s OFFSET %(offset)s
		""".format(
			select_fields=", ".join(fields),
			where=" AND ".join(where),
		),
		params,
		as_dict=True,
	)

	names = [row["name"] for row in rows]
	stats = _club_customer_stats_batch(names)
	wallets = _club_wallet_map(names)
	points_map = _club_points_map(names)

	items = []
	for row in rows:
		code = row.get("restaurant_membership_code") or ""
		if not code:
			code = _club_assign_membership_code(row["name"])
		stat = stats.get(row["name"], {})
		wallet = wallets.get(row["name"], {})
		point_info = points_map.get(row["name"], {})
		items.append(
			{
				"name": row["name"],
				"customer_name": row.get("customer_name") or row["name"],
				"mobile": (row.get("mobile_no") or row.get("customer_primary_mobile") or "").strip(),
				"membership_code": code,
				"birth_date": str(row.get("restaurant_birth_date") or ""),
				"tier": row.get("restaurant_customer_tier") or "عادی",
				"segment": row.get("restaurant_customer_segment") or "",
				"kind": row.get("restaurant_customer_kind") or "حقیقی",
				"organization": row.get("restaurant_organization") or "",
				"referral_code": row.get("restaurant_referral_code") or _club_assign_referral_code(row["name"]),
				"referred_by": row.get("restaurant_referred_by") or "",
				"orders": stat.get("orders", 0),
				"total_spent": flt(stat.get("total_spent", 0)),
				"last_order": stat.get("last_order", ""),
				"first_order": stat.get("first_order", ""),
				"wallet_balance": flt(wallet.get("balance", 0)),
				"has_wallet": bool(wallet),
				"points_balance": cint(point_info.get("balance", 0)),
				"loyalty_tier": point_info.get("loyalty_tier", ""),
			}
		)
	frappe.db.commit()
	return {"customers": items, "count": len(items)}


@frappe.whitelist()
def save_management_club_customer(payload=None):
	"""Update club fields on an ERPNext Customer (or create a new one)."""
	_ensure_management_access()
	_club_ensure_customer_fields()
	payload = _club_parse_json(payload, {})

	name = (payload.get("name") or "").strip()
	customer_name = (payload.get("customer_name") or "").strip()
	if not customer_name:
		frappe.throw(_("نام مشتری الزامی است."))

	created = False
	if name and frappe.db.exists("Customer", name):
		doc = frappe.get_doc("Customer", name)
	else:
		if frappe.db.exists("Customer", {"customer_name": customer_name}):
			doc = frappe.get_doc("Customer", {"customer_name": customer_name})
		else:
			doc = frappe.new_doc("Customer")
			doc.customer_name = customer_name
			created = True
	doc.customer_name = customer_name
	if payload.get("mobile") is not None and _has_column("Customer", "mobile_no"):
		doc.mobile_no = (payload.get("mobile") or "").strip()
	field_map = {
		"birth_date": "restaurant_birth_date",
		"tier": "restaurant_customer_tier",
		"segment": "restaurant_customer_segment",
		"kind": "restaurant_customer_kind",
		"organization": "restaurant_organization",
	}
	for key, fieldname in field_map.items():
		if payload.get(key) is not None and _has_column("Customer", fieldname):
			value = (payload.get(key) or "").strip()
			if key == "tier" and value and value not in CUSTOMER_TIERS:
				value = ""
			if key == "segment" and value and value not in CUSTOMER_SEGMENTS:
				value = ""
			if key == "kind" and value and value not in CUSTOMER_KINDS:
				value = ""
			if key == "organization" and value and not frappe.db.exists("Customer", value):
				frappe.throw(_("مشتری سازمانی یافت نشد: {0}").format(value))
			setattr(doc, fieldname, value)
	doc.save(ignore_permissions=True)

	membership_code = _club_assign_membership_code(doc.name)
	referral_code = _club_assign_referral_code(doc.name)
	frappe.db.commit()
	return {
		"status": "success",
		"created": created,
		"customer": doc.name,
		"membership_code": membership_code,
		"referral_code": referral_code,
	}


@frappe.whitelist()
def assign_management_membership_codes():
	"""Backfill membership + referral codes for every active customer."""
	_ensure_management_access()
	_club_ensure_customer_fields()
	names = frappe.get_all("Customer", filters={"disabled": 0}, pluck="name", limit_page_length=0)
	assigned_membership = 0
	assigned_referral = 0
	for name in names:
		if _club_assign_membership_code(name):
			assigned_membership += 1
		if _club_assign_referral_code(name):
			assigned_referral += 1
	frappe.db.commit()
	return {
		"status": "success",
		"customers": len(names),
		"membership_assigned": assigned_membership,
		"referral_assigned": assigned_referral,
	}


CUSTOMER_EXPORT_COLUMNS = [
	"customer_name",
	"mobile",
	"membership_code",
	"tier",
	"segment",
	"birth_date",
	"total_spent",
	"orders",
]
CUSTOMER_IMPORT_HEADER_ALIASES = {
	"customer_name": ["customer_name", "name", "نام مشتری", "نام"],
	"mobile": ["mobile", "موبایل", "شماره موبایل", "موبایل مشتری"],
	"tier": ["tier", "سطح", "سطح مشتری"],
	"segment": ["segment", "خوشه", "گروه رفتاری"],
	"birth_date": ["birth_date", "birthday", "تاریخ تولد", "تولد"],
}


@frappe.whitelist()
def export_management_customers_excel(search=""):
	_ensure_management_access()
	payload = list_management_club_customers(search=search, limit=1000)
	data = [list(CUSTOMER_EXPORT_COLUMNS)]
	for row in payload["customers"]:
		data.append(
			[
				row["customer_name"],
				row["mobile"],
				row["membership_code"],
				row["tier"],
				row["segment"],
				row["birth_date"],
				flt(row["total_spent"]),
				cint(row["orders"]),
			]
		)
	try:
		from frappe.utils.xlsxutils import make_xlsx
	except Exception:
		frappe.throw(_("خروجی اکسل روی این سرور در دسترس نیست (xlsxutils)."))
	xlsx_file = make_xlsx(data, "Customers")
	file_name = "restaurant-customers-{}.xlsx".format(now_datetime().strftime("%Y%m%d-%H%M%S"))
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"content": xlsx_file.getvalue(),
			"is_private": 1,
			"folder": "Home",
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"status": "success",
		"file_url": file_doc.file_url,
		"file_name": file_doc.file_name,
		"rows": max(len(data) - 1, 0),
		"columns": list(CUSTOMER_EXPORT_COLUMNS),
	}


def _club_normalize_import_headers(header_row):
	mapping = {}
	for key, aliases in CUSTOMER_IMPORT_HEADER_ALIASES.items():
		normalized = {alias.strip().lower() for alias in aliases}
		for idx, cell in enumerate(header_row or []):
			if str(cell or "").strip().lower() in normalized:
				mapping[idx] = key
	return mapping


@frappe.whitelist()
def import_management_customers_excel(file_url=None, file_name=None, dry_run=0):
	"""Bulk import club customers from an uploaded .xlsx/.csv file."""
	_ensure_management_access()
	_club_ensure_customer_fields()

	raw = _club_fp_call("_fp_load_upload_content", file_url=file_url)
	rows = _club_fp_call("_fp_parse_tabular_rows", raw, file_name=file_name or (file_url or ""))
	if len(rows) < 2:
		frappe.throw(_("فایل بارگذاری‌شده سطر داده ندارد."))
	header_mapping = _club_normalize_import_headers(rows[0])
	if "customer_name" not in header_mapping.values() or not header_mapping:
		frappe.throw(
			_("سرستون‌ها شناسایی نشد. ستون نام مشتری (customer_name) الزامی است.")
		)

	records = []
	for row in rows[1:]:
		if not any(str(cell or "").strip() for cell in row):
			continue
		record = {}
		for idx, key in header_mapping.items():
			if idx < len(row):
				record[key] = row[idx]
		if (record.get("customer_name") or "").strip():
			records.append(record)
	if not records:
		frappe.throw(_("فایل بارگذاری‌شده سطر داده ندارد."))

	summary = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
	for index, record in enumerate(records, start=2):
		try:
			if cint(dry_run):
				summary["created"] += 1
				continue
			result = save_management_club_customer(record)
			if result.get("created"):
				summary["created"] += 1
			else:
				summary["updated"] += 1
		except Exception as error:
			summary["errors"].append(
				{"row": index, "customer": record.get("customer_name") or "", "message": str(error)[:180]}
			)
	return {"status": "success", "dry_run": cint(dry_run), "total_rows": len(records), **summary}


# ---------------------------------------------------------------------------
# Tiers & automatic (rule-based) segmentation
# ---------------------------------------------------------------------------


def _club_segment_for_stats(stat):
	if not stat or not stat.get("orders"):
		return "بالقوه"
	today_ = getdate(today())
	last = getdate(stat.get("last_order")) if stat.get("last_order") else None
	first = getdate(stat.get("first_order")) if stat.get("first_order") else None
	if last and (today_ - last).days > 90:
		return "خفته"
	if last and (today_ - last).days > 45:
		return "در خطر ریزش"
	if first and (today_ - first).days <= 30 and stat.get("orders", 0) <= 2:
		return "جدید"
	if stat.get("orders", 0) >= 5:
		return "وفادار"
	return "بالقوه"


def _club_tier_for_stats(stat):
	if not stat or not stat.get("orders"):
		return "جدید"
	total = flt(stat.get("total_spent"))
	orders = cint(stat.get("orders"))
	avg = total / orders if orders else 0.0
	if total >= 50000000 or (orders >= 10 and avg >= 3000000):
		return "VIP"
	if avg >= 10000000:
		return "عمده‌فروش"
	first = getdate(stat.get("first_order")) if stat.get("first_order") else None
	if first and (getdate(today()) - first).days <= 30:
		return "جدید"
	return "عادی"


@frappe.whitelist()
def compute_management_customer_segments():
	"""Recompute tiers and behavior segments for all customers from purchase history."""
	_ensure_management_access()
	_club_ensure_customer_fields()
	names = frappe.get_all("Customer", filters={"disabled": 0}, pluck="name", limit_page_length=0)
	stats = _club_customer_stats_batch(names)
	segments = {key: 0 for key in CUSTOMER_SEGMENTS}
	tiers = {key: 0 for key in CUSTOMER_TIERS}
	updated = 0
	for name in names:
		stat = stats.get(name, {})
		segment = _club_segment_for_stats(stat)
		tier = _club_tier_for_stats(stat)
		segments[segment] = segments.get(segment, 0) + 1
		tiers[tier] = tiers.get(tier, 0) + 1
		updates = {}
		if _has_column("Customer", "restaurant_customer_segment"):
			updates["restaurant_customer_segment"] = segment
		if _has_column("Customer", "restaurant_customer_tier"):
			updates["restaurant_customer_tier"] = tier
		if updates:
			frappe.db.set_value("Customer", name, updates, update_modified=False)
			updated += 1
	frappe.db.commit()
	return {"status": "success", "customers": len(names), "updated": updated, "segments": segments, "tiers": tiers}


# ---------------------------------------------------------------------------
# SMS center
# ---------------------------------------------------------------------------


def _club_send_sms_now(mobile, message):
	"""Try to send via Frappe SMS Settings; return (status, note)."""
	settings = _club_club_settings()
	if not settings["sms_enabled"]:
		return "بدون درگاه", _("ارسال پیامک در تنظیمات باشگاه غیرفعال است.")
	try:
		sms_module = frappe.get_module("frappe.core.doctype.sms_settings.sms_settings")
		sms_module.send_sms([mobile], message)
		return "ارسال‌شده", ""
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Restaurant SMS send failed")
		return "ناموفق", str(exc)[:160]


def _club_render_sms(template, customer_name="", membership_code="", message=""):
	text = template or ""
	return (
		text.replace("{name}", customer_name or "")
		.replace("{membership_code}", membership_code or "")
		.replace("{message}", message or "")
		.strip()
	)


def _club_log_sms(*, mobile, message, kind, customer="", template_key="", campaign="", status_note=("در صف", "")):
	doc = frappe.new_doc(CLUB_DOCTYPES["sms"])
	doc.customer = customer or None
	doc.mobile = mobile
	doc.kind = kind
	doc.template_key = template_key or ""
	doc.campaign = campaign or None
	doc.message = message
	status, note = status_note
	doc.status = status
	doc.provider_note = note or ""
	doc.sent_at = now_datetime() if status == "ارسال‌شده" else None
	doc.insert(ignore_permissions=True)
	return doc


@frappe.whitelist()
def get_management_sms_templates():
	_ensure_management_access()
	settings = _club_club_settings()
	return {
		"templates": settings["sms_templates"],
		"defaults": DEFAULT_SMS_TEMPLATES,
		"sms_enabled": settings["sms_enabled"],
		"kinds": SMS_KINDS,
	}


@frappe.whitelist()
def set_management_sms_templates(payload=None):
	_ensure_management_access()
	_club_ensure_settings_fields()
	payload = _club_parse_json(payload, {})
	allowed = set(DEFAULT_SMS_TEMPLATES.keys()) | {"inactive", "welcome", "birthday", "bulk_default"}
	current = _club_get_sms_templates()
	for key, value in (payload.get("templates") or {}).items():
		if key in allowed and isinstance(value, str) and value.strip():
			current[key] = value.strip()
	_club_set_setting("restaurant_sms_templates_json", json.dumps(current, ensure_ascii=False))
	if "sms_enabled" in payload:
		_club_set_setting("restaurant_sms_enabled", cint(payload.get("sms_enabled")))
	frappe.db.commit()
	return {"status": "success", "templates": current, "sms_enabled": cint(_club_setting("restaurant_sms_enabled", 0))}


@frappe.whitelist()
def send_management_sms(payload=None):
	"""Personalized bulk/custom SMS to a filtered group of customers."""
	_ensure_management_access()
	_club_ensure_settings_fields()
	payload = _club_parse_json(payload, {})

	kind = (payload.get("kind") or "دستی").strip()
	if kind not in SMS_KINDS:
		frappe.throw(_("نوع پیامک نامعتبر است."))
	message_body = (payload.get("message") or "").strip()
	template_key = (payload.get("template_key") or "").strip()
	campaign = (payload.get("campaign") or "").strip()

	templates = _club_get_sms_templates()
	template = templates.get(template_key) if template_key else ""

	# Resolve recipients
	mobiles = [m.strip() for m in _club_list(payload.get("mobiles")) if m and m.strip()]
	customers_data = []
	if not mobiles:
		filters = {"disabled": 0}
		segment = (payload.get("segment") or "").strip()
		tier = (payload.get("tier") or "").strip()
		if segment and _has_column("Customer", "restaurant_customer_segment"):
			filters["restaurant_customer_segment"] = segment
		if tier and _has_column("Customer", "restaurant_customer_tier"):
			filters["restaurant_customer_tier"] = tier
		rows = frappe.get_all(
			"Customer",
			filters=filters,
			fields=["name", "customer_name"] + _club_customer_extra_fields(),
			limit_page_length=1000,
		)
		for row in rows:
			mobile = (row.get("mobile_no") or row.get("customer_primary_mobile") or "").strip()
			if mobile:
				customers_data.append(
					{
						"name": row["name"],
						"customer_name": row.get("customer_name") or row["name"],
						"mobile": mobile,
						"membership_code": row.get("restaurant_membership_code") or "",
					}
				)
	else:
		for mobile in mobiles:
			customer_name = ""
			for fieldname in ("mobile_no", "customer_primary_mobile"):
				if _has_column("Customer", fieldname):
					found = frappe.db.get_value("Customer", {fieldname: mobile}, ["name", "customer_name"], as_dict=True)
					if found:
						customer_name = found.get("customer_name") or found.get("name") or ""
						break
			membership_code = frappe.db.get_value("Customer", customer_name, "restaurant_membership_code") if (customer_name and _has_column("Customer", "restaurant_membership_code")) else ""
			customers_data.append(
				{
					"name": customer_name,
					"customer_name": customer_name,
					"mobile": mobile,
					"membership_code": membership_code or "",
				}
			)

	if not customers_data:
		frappe.throw(_("هیچ گیرنده‌ای با موبایل معتبر یافت نشد."))

	if not message_body and not template:
		frappe.throw(_("متن پیامک یا قالب انتخاب نشده است."))

	sent = failed = queued = 0
	logs = []
	for row in customers_data:
		text = (
			_club_render_sms(template, row["customer_name"], row["membership_code"], message_body)
			if template
			else _club_render_sms(templates.get("bulk_default", "{message}"), row["customer_name"], row["membership_code"], message_body)
		)
		status, note = _club_send_sms_now(row["mobile"], text)
		if status == "ارسال‌شده":
			sent += 1
		elif status == "در صف":
			queued += 1
		else:
			failed += 1
		log = _club_log_sms(
			mobile=row["mobile"],
			message=text,
			kind=kind,
			customer=row["name"],
			template_key=template_key,
			campaign=campaign,
			status_note=(status, note),
		)
		if len(logs) < 5:
			logs.append(log.name)

	frappe.db.commit()
	return {
		"status": "success",
		"total": len(customers_data),
		"sent": sent,
		"failed": failed,
		"queued": queued,
		"sample_logs": logs,
	}


@frappe.whitelist()
def list_management_sms_messages(kind="", status="", date_from="", date_to="", search="", limit=100, offset=0):
	_ensure_management_access()
	filters = {}
	if kind and kind in SMS_KINDS:
		filters["kind"] = kind
	if status and status in SMS_STATUS:
		filters["status"] = status
	rows = frappe.get_all(
		CLUB_DOCTYPES["sms"],
		filters=filters,
		fields=["name", "customer", "mobile", "kind", "template_key", "campaign", "message", "status", "provider_note", "sent_at", "creation"],
		order_by="creation desc",
		limit_start=cint(offset) or 0,
		limit_page_length=min(max(cint(limit) or 100, 1), 400),
	)
	search = (search or "").strip().lower()
	items = []
	for row in rows:
		if date_from and str(row.get("creation") or "")[:10] < str(date_from):
			continue
		if date_to and str(row.get("creation") or "")[:10] > str(date_to):
			continue
		if search and search not in (row.get("mobile") or "").lower() and search not in (row.get("customer") or "").lower():
			continue
		items.append(
			{
				**row,
				"sent_at": str(row.get("sent_at") or ""),
				"creation": str(row.get("creation") or ""),
			}
		)
	summary_rows = frappe.get_all(
		CLUB_DOCTYPES["sms"],
		fields=["status", "COUNT(*) AS count"],
		group_by="status",
	)
	return {
		"messages": items,
		"count": len(items),
		"summary": {row.get("status"): cint(row.get("count")) for row in summary_rows},
	}


@frappe.whitelist()
def get_management_sms_kind_stats(date_from="", date_to=""):
	"""منشور ارتباط با مشتری: آمار پیامک‌ها به تفکیک تبلیغاتی / اطلاع‌رسانی / یادآوری."""
	_ensure_management_access()
	date_to = str(date_to or today())
	date_from = str(date_from or add_days(date_to, -29))
	rows = frappe.db.sql(
		"""
		SELECT kind, status, COUNT(*) AS count
		FROM `tabRestaurant SMS Message`
		WHERE creation BETWEEN %(df)s AND %(dt)s + INTERVAL 1 DAY
		GROUP BY kind, status
		""",
		{"df": date_from, "dt": date_to},
		as_dict=True,
	)
	by_kind = {}
	for row in rows:
		kind = (row.get("kind") or "دستی").strip() or "دستی"
		entry = by_kind.setdefault(kind, {"kind": kind, "total": 0, "sent": 0, "failed": 0, "queued": 0})
		entry["total"] += cint(row.get("count"))
		if row.get("status") == "ارسال‌شده":
			entry["sent"] += cint(row.get("count"))
		elif row.get("status") in ("ناموفق", "بدون درگاه"):
			entry["failed"] += cint(row.get("count"))
		else:
			entry["queued"] += cint(row.get("count"))

	classes = []
	for class_label, kinds in SMS_KIND_CLASSES.items():
		kind_rows = [by_kind.get(k, {"kind": k, "total": 0, "sent": 0, "failed": 0, "queued": 0}) for k in kinds]
		total = sum(r["total"] for r in kind_rows)
		sent = sum(r["sent"] for r in kind_rows)
		classes.append(
			{
				"class": class_label,
				"kinds": [{**r, "success_rate": flt(r["sent"] * 100.0 / r["total"], 1) if r["total"] else 0} for r in kind_rows],
				"total": total,
				"sent": sent,
				"failed": sum(r["failed"] for r in kind_rows),
				"queued": sum(r["queued"] for r in kind_rows),
				"success_rate": flt(sent * 100.0 / total, 1) if total else 0,
			}
		)
	return {
		"date_from": date_from,
		"date_to": date_to,
		"classes": classes,
		"grand_total": sum(c["total"] for c in classes),
		"grand_sent": sum(c["sent"] for c in classes),
	}


# ---------------------------------------------------------------------------
# Customer voice (شکایات، انتقاد، پیشنهاد، درخواست، تقدیر) — منشور ارتباط با مشتری
# ---------------------------------------------------------------------------


def _serialize_voice(row):
	customer_name = ""
	if row.get("customer"):
		customer_name = frappe.db.get_value("Customer", row["customer"], "customer_name") or ""
	return {
		"name": row.get("name"),
		"customer": row.get("customer") or "",
		"customer_name": row.get("customer_name") or customer_name or "",
		"mobile": row.get("mobile") or "",
		"sales_order": row.get("sales_order") or "",
		"order_code": row.get("order_code") or "",
		"type": row.get("type") or "شکایت",
		"subject": row.get("subject") or "",
		"message": row.get("message") or "",
		"status": row.get("status") or "جدید",
		"response": row.get("response") or "",
		"responded_by": row.get("responded_by") or "",
		"responded_at": str(row.get("responded_at") or ""),
		"creation": str(row.get("creation") or ""),
	}


@frappe.whitelist()
def list_management_customer_voices(type="", status="", date_from="", date_to="", search="", limit=100, offset=0):
	"""لیست صدای مشتری (ثبت مراجعه/شکایت/پیشنهاد) با فیلتر و آمار تجمیعی."""
	_ensure_management_access()
	if not frappe.db.exists("DocType", CLUB_DOCTYPES["voice"]):
		return {"voices": [], "count": 0, "summary": {"by_type": {}, "by_status": {}}}
	filters = {}
	if type and type in VOICE_TYPES:
		filters["type"] = type
	if status and status in VOICE_STATUSES:
		filters["status"] = status
	rows = frappe.get_all(
		CLUB_DOCTYPES["voice"],
		filters=filters,
		fields=["name", "customer", "customer_name", "mobile", "sales_order", "order_code", "type", "subject", "message", "status", "response", "responded_by", "responded_at", "creation"],
		order_by="creation desc",
		limit_start=cint(offset) or 0,
		limit_page_length=min(max(cint(limit) or 100, 1), 400),
	)
	search = (search or "").strip().lower()
	items = []
	for row in rows:
		entry = str(row.get("creation") or "")[:10]
		if date_from and entry < str(date_from):
			continue
		if date_to and entry > str(date_to):
			continue
		if search:
			haystack = " ".join(
				str(part or "")
				for part in (row.get("customer_name"), row.get("mobile"), row.get("subject"), row.get("order_code"))
			).lower()
			if search not in haystack:
				continue
		items.append(_serialize_voice(row))

	summary_rows = frappe.get_all(
		CLUB_DOCTYPES["voice"],
		fields=["type", "status", "COUNT(*) AS count"],
		group_by="type, status",
	)
	by_type = {}
	by_status = {}
	for row in summary_rows:
		by_type[row.get("type") or "-"] = by_type.get(row.get("type") or "-", 0) + cint(row.get("count"))
		by_status[row.get("status") or "-"] = by_status.get(row.get("status") or "-", 0) + cint(row.get("count"))
	return {"voices": items, "count": len(items), "summary": {"by_type": by_type, "by_status": by_status}}


@frappe.whitelist()
def save_management_customer_voice(payload=None):
	"""ثبت دستی مراجعه/شکایت/پیشنهاد توسط ادمین."""
	_ensure_management_access()
	if not frappe.db.exists("DocType", CLUB_DOCTYPES["voice"]):
		frappe.throw(_("ماژول صدای مشتری هنوز آماده نیست (migrate لازم است)."))
	payload = _club_parse_json(payload, {})
	subject = (payload.get("subject") or "").strip()
	if not subject:
		frappe.throw(_("موضوع پیام الزامی است."))
	type_ = (payload.get("type") or "شکایت").strip()
	if type_ not in VOICE_TYPES:
		type_ = "شکایت"

	name = (payload.get("name") or "").strip()
	if name and frappe.db.exists(CLUB_DOCTYPES["voice"], name):
		doc = frappe.get_doc(CLUB_DOCTYPES["voice"], name)
	else:
		doc = frappe.new_doc(CLUB_DOCTYPES["voice"])
		customer = (payload.get("customer") or "").strip()
		mobile = (payload.get("mobile") or "").strip()
		if not customer and mobile:
			customer = frappe.db.get_value("Customer", {"mobile_no": mobile}, "name") or ""
			if not customer and _has_column("Customer", "customer_primary_mobile"):
				customer = frappe.db.get_value("Customer", {"customer_primary_mobile": mobile}, "name") or ""
		doc.customer = customer
		doc.customer_name = (payload.get("customer_name") or "").strip() or (
			frappe.db.get_value("Customer", customer, "customer_name") if customer else ""
		)
		doc.mobile = mobile or (_club_customer_mobile(customer) if customer else "")
	doc.type = type_
	doc.subject = subject
	if payload.get("message") is not None:
		doc.message = (payload.get("message") or "").strip()
	if payload.get("status") and payload.get("status") in VOICE_STATUSES:
		doc.status = payload.get("status")
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()
	return {"status": "success", "voice": _serialize_voice(doc.as_dict())}


@frappe.whitelist()
def update_management_customer_voice_status(payload=None):
	"""تغییر وضعیت و ثبت پاسخ برای صدای مشتری."""
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	name = (payload.get("name") or "").strip()
	if not name or not frappe.db.exists(CLUB_DOCTYPES["voice"], name):
		frappe.throw(_("پیام یافت نشد: {0}").format(name or "-"))
	status = (payload.get("status") or "").strip()
	response = (payload.get("response") or "").strip()
	if status and status not in VOICE_STATUSES:
		frappe.throw(_("وضعیت نامعتبر است."))
	updates = {}
	if status:
		updates["status"] = status
	updates["response"] = response
	if response or status == "پاسخ داده‌شده":
		updates["responded_by"] = frappe.session.user
		updates["responded_at"] = now_datetime()
	frappe.db.set_value(CLUB_DOCTYPES["voice"], name, updates, update_modified=True)
	frappe.db.commit()
	row = frappe.get_doc(CLUB_DOCTYPES["voice"], name)
	return {"status": "success", "voice": _serialize_voice(row.as_dict())}


@frappe.whitelist()
def delete_management_customer_voice(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not name or not frappe.db.exists(CLUB_DOCTYPES["voice"], name):
		frappe.throw(_("پیام یافت نشد: {0}").format(name or "-"))
	frappe.delete_doc(CLUB_DOCTYPES["voice"], name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "deleted": name}


@frappe.whitelist(allow_guest=True)
def submit_public_voice(payload=None):
	"""ثبت شکایت/پیشنهاد از سمت مشتری (با کد سفارش اختیاری)."""
	if not frappe.db.exists("DocType", CLUB_DOCTYPES["voice"]):
		frappe.throw(_("در حال حاضر امکان ثبت پیام وجود ندارد."))
	payload = _club_parse_json(payload, {})
	subject = (payload.get("subject") or "").strip()
	message = (payload.get("message") or "").strip()
	mobile = (payload.get("mobile") or "").strip()
	if not subject or not message:
		frappe.throw(_("موضوع و متن پیام الزامی است."))
	if not mobile:
		frappe.throw(_("شماره موبایل الزامی است."))
	type_ = (payload.get("type") or "شکایت").strip()
	if type_ not in VOICE_TYPES:
		type_ = "شکایت"

	order_code = (payload.get("order_code") or "").strip()
	sales_order = ""
	customer = ""
	if order_code:
		match = _club_verify_survey_order(order_code, mobile)
		if not match:
			frappe.throw(_("کد سفارش با این شماره موبایل تطابق ندارد."))
		sales_order = match.get("sales_order")
		customer = match.get("customer")
	elif _has_column("Customer", "mobile_no"):
		customer = frappe.db.get_value("Customer", {"mobile_no": mobile}, "name") or ""

	doc = frappe.new_doc(CLUB_DOCTYPES["voice"])
	doc.customer = customer
	doc.customer_name = (payload.get("customer_name") or "").strip() or (
		frappe.db.get_value("Customer", customer, "customer_name") if customer else ""
	)
	doc.mobile = mobile
	doc.order_code = sales_order or order_code
	doc.sales_order = sales_order
	doc.type = type_
	doc.subject = subject[:140]
	doc.message = message[:2000]
	doc.status = "جدید"
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()
	return {"status": "success", "voice": doc.name}


# ---------------------------------------------------------------------------
# Loyalty points (امتیازدهی: کسب بر اساس مبلغ فاکتور، استفاده، انقضا، سطح‌بندی)
# ---------------------------------------------------------------------------


def _club_loyalty_tier(lifetime_points):
	"""دسته‌بندی امتیازات: طلایی / نقره‌ای / برنزی بر اساس مجموع امتیاز کسب‌شده."""
	settings = _club_club_settings()
	points = cint(lifetime_points)
	if settings["points_gold_threshold"] > 0 and points >= settings["points_gold_threshold"]:
		return "طلایی"
	if settings["points_silver_threshold"] > 0 and points >= settings["points_silver_threshold"]:
		return "نقره‌ای"
	if settings["points_bronze_threshold"] > 0 and points >= settings["points_bronze_threshold"]:
		return "برنزی"
	return ""


def _club_points_map(customer_names):
	"""Batch: balance + lifetime earned + loyalty tier for a list of customers."""
	if not customer_names or not frappe.db.exists("DocType", CLUB_DOCTYPES["point_entry"]):
		return {}
	out = {}
	rows = frappe.db.sql(
		"""
		SELECT customer,
			COALESCE(SUM(points),0) AS balance,
			COALESCE(SUM(CASE WHEN kind = 'کسب' THEN points ELSE 0 END),0) AS lifetime
		FROM `tabRestaurant Loyalty Point Entry`
		WHERE customer IN %(names)s
		GROUP BY customer
		""",
		{"names": tuple(customer_names)},
		as_dict=True,
	)
	for row in rows:
		out[row["customer"]] = {
			"balance": cint(row.get("balance")),
			"lifetime": cint(row.get("lifetime")),
			"loyalty_tier": _club_loyalty_tier(row.get("lifetime")),
		}
	return out


def _club_points_balance(customer_name):
	if not customer_name or not frappe.db.exists("DocType", CLUB_DOCTYPES["point_entry"]):
		return 0
	row = frappe.db.sql(
		"SELECT COALESCE(SUM(points),0) AS balance FROM `tabRestaurant Loyalty Point Entry` WHERE customer = %(c)s",
		{"c": customer_name},
		as_dict=True,
	)
	return cint(row[0].get("balance")) if row else 0


def _club_sync_customer_points_field(customer_name):
	if not _has_column("Customer", "restaurant_loyalty_points"):
		return
	balance = _club_points_balance(customer_name)
	frappe.db.set_value("Customer", customer_name, "restaurant_loyalty_points", balance, update_modified=False)
	return balance


def _club_point_entry(*, customer, points, kind, note="", sales_order="", expiry_date=""):
	if not frappe.db.exists("DocType", CLUB_DOCTYPES["point_entry"]):
		return ""
	if kind not in POINT_KINDS:
		kind = "کسب"
	doc = frappe.new_doc(CLUB_DOCTYPES["point_entry"])
	doc.customer = customer
	doc.points = cint(points)
	doc.kind = kind
	doc.note = (note or "")[:500]
	doc.sales_order = sales_order or ""
	if expiry_date:
		doc.expiry_date = expiry_date
	doc.flags.ignore_permissions = True
	doc.save()
	_club_sync_customer_points_field(customer)
	return doc.name


def _club_process_points_earning(so_name):
	"""نحوه محاسبه امتیاز بر اساس مبلغ فاکتور — idempotent per order."""
	settings = _club_club_settings()
	if not settings["club_enabled"] or not settings["points_enabled"]:
		return 0
	ratio = flt(settings["points_rial_per_point"])
	if ratio <= 0 or not frappe.db.exists("Sales Order", so_name):
		return 0
	already = 0
	if _has_column("Sales Order", "restaurant_points_earned"):
		already = cint(frappe.db.get_value("Sales Order", so_name, "restaurant_points_earned"))
	if already:
		return 0
	customer = frappe.db.get_value("Sales Order", so_name, "customer") or ""
	if not customer:
		return 0
	grand_total = flt(frappe.db.get_value("Sales Order", so_name, "grand_total"))
	points = int(grand_total // ratio)
	if points <= 0:
		if _has_column("Sales Order", "restaurant_points_earned"):
			frappe.db.set_value("Sales Order", so_name, "restaurant_points_earned", -1, update_modified=False)
		return 0
	expiry = ""
	if settings["points_expiry_days"] > 0:
		expiry = str(add_days(today(), settings["points_expiry_days"]))
	_club_point_entry(
		customer=customer,
		points=points,
		kind="کسب",
		note=_("کسب امتیاز از سفارش {0}").format(so_name),
		sales_order=so_name,
		expiry_date=expiry,
	)
	if _has_column("Sales Order", "restaurant_points_earned"):
		frappe.db.set_value("Sales Order", so_name, "restaurant_points_earned", points, update_modified=False)
	return points


def _club_expire_points():
	"""ابطال/انقضای امتیازهای سررسیدشده (اجرا توسط job روزانه)."""
	if not frappe.db.exists("DocType", CLUB_DOCTYPES["point_entry"]):
		return 0
	expired_rows = frappe.db.sql(
		"""
		SELECT customer,
			COALESCE(SUM(CASE WHEN kind = 'کسب' AND expiry_date IS NOT NULL AND expiry_date != '' AND expiry_date < %(today)s THEN points ELSE 0 END),0) AS expired_earned,
			COALESCE(SUM(CASE WHEN kind IN ('استفاده','تبدیل به اعتبار') THEN -points ELSE 0 END),0) AS consumed,
			COALESCE(SUM(CASE WHEN kind = 'انقضا' THEN -points ELSE 0 END),0) AS already_expired
		FROM `tabRestaurant Loyalty Point Entry`
		GROUP BY customer
		HAVING expired_earned - consumed - already_expired > 0
		""",
		{"today": today()},
		as_dict=True,
	)
	count = 0
	for row in expired_rows:
		pending = cint(row.get("expired_earned")) - cint(row.get("consumed")) - cint(row.get("already_expired"))
		if pending <= 0:
			continue
		_club_point_entry(
			customer=row["customer"],
			points=-pending,
			kind="انقضا",
			note=_("انقضای خودکار {0} امتیاز سررسیدشده").format(pending),
		)
		count += 1
	return count


@frappe.whitelist()
def list_management_point_entries(customer="", kind="", date_from="", date_to="", limit=100, offset=0):
	"""دفتر امتیاز: تاریخچه کسب/استفاده/انقضا امتیازها با فیلتر."""
	_ensure_management_access()
	if not frappe.db.exists("DocType", CLUB_DOCTYPES["point_entry"]):
		return {"entries": [], "count": 0}
	filters = {}
	if customer:
		filters["customer"] = customer
	if kind and kind in POINT_KINDS:
		filters["kind"] = kind
	rows = frappe.get_all(
		CLUB_DOCTYPES["point_entry"],
		filters=filters,
		fields=["name", "customer", "points", "kind", "note", "sales_order", "expiry_date", "creation"],
		order_by="creation desc",
		limit_start=cint(offset) or 0,
		limit_page_length=min(max(cint(limit) or 100, 1), 400),
	)
	items = []
	for row in rows:
		entry = str(row.get("creation") or "")[:10]
		if date_from and entry < str(date_from):
			continue
		if date_to and entry > str(date_to):
			continue
		items.append(
			{
				**row,
				"customer_name": frappe.db.get_value("Customer", row["customer"], "customer_name") or row["customer"],
				"expiry_date": str(row.get("expiry_date") or ""),
				"creation": str(row.get("creation") or ""),
			}
		)
	return {"entries": items, "count": len(items), "kinds": POINT_KINDS}


@frappe.whitelist()
def redeem_management_points(payload=None):
	"""نحوه استفاده امتیاز: تبدیل امتیاز مشتری به اعتبار کیف پول (توسط ادمین)."""
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	customer = (payload.get("customer") or "").strip()
	if not customer or not frappe.db.exists("Customer", customer):
		frappe.throw(_("مشتری یافت نشد."))
	points = cint(payload.get("points") or 0)
	return _redeem_points_core(customer, points)


def _redeem_points_core(customer, points):
	settings = _club_club_settings()
	if not settings["points_enabled"]:
		frappe.throw(_("سیستم امتیازدهی غیرفعال است."))
	points = cint(points)
	if points <= 0:
		frappe.throw(_("تعداد امتیاز باید بزرگ‌تر از صفر باشد."))
	if settings["points_min_redeem"] > 0 and points < settings["points_min_redeem"]:
		frappe.throw(_("حداقل امتیاز قابل استفاده {0} امتیاز است.").format(settings["points_min_redeem"]))
	balance = _club_points_balance(customer)
	if points > balance:
		frappe.throw(_("موجودی امتیاز کافی نیست (موجودی: {0}).").format(balance))
	amount = flt(points * flt(settings["points_rial_value"]), 2)
	if amount <= 0:
		frappe.throw(_("ارزش ریالی امتیاز تنظیم نشده است."))
	_club_point_entry(
		customer=customer,
		points=-points,
		kind="تبدیل به اعتبار",
		note=_("تبدیل {0} امتیاز به {1} ریال اعتبار").format(points, amount),
	)
	wallet = _club_get_or_create_wallet(customer)
	_club_wallet_txn(
		wallet=wallet,
		customer=customer,
		kind="تبدیل امتیاز",
		direction="واریز",
		amount=amount,
		note=_("تبدیل {0} امتیاز به اعتبار کیف پول").format(points),
	)
	frappe.db.commit()
	return {
		"status": "success",
		"points_used": points,
		"amount_credited": amount,
		"points_balance": _club_points_balance(customer),
		"wallet_balance": flt(frappe.db.get_value(CLUB_DOCTYPES["wallet"], wallet, "balance")),
	}


@frappe.whitelist()
def adjust_management_points(payload=None):
	"""تعدیل دستی امتیاز مشتری (مثبت/منفی) با شرح."""
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	customer = (payload.get("customer") or "").strip()
	if not customer or not frappe.db.exists("Customer", customer):
		frappe.throw(_("مشتری یافت نشد."))
	points = cint(payload.get("points") or 0)
	if not points:
		frappe.throw(_("مقدار امتیاز تعدیل نمی‌تواند صفر باشد."))
	note = (payload.get("note") or "").strip()
	_club_point_entry(customer=customer, points=points, kind="تعدیل دستی", note=note or _("تعدیل دستی توسط اپراتور"))
	frappe.db.commit()
	return {"status": "success", "points_balance": _club_points_balance(customer)}


@frappe.whitelist(allow_guest=True)
def redeem_my_points(mobile="", points=0):
	"""تبدیل امتیاز به اعتبار توسط خود مشتری از داشبورد مشتری."""
	settings = _club_club_settings()
	if not settings["club_enabled"] or not settings["points_enabled"]:
		frappe.throw(_("سیستم امتیازدهی فعال نیست."))
	mobile = (mobile or "").strip()
	if not mobile:
		frappe.throw(_("شماره موبایل الزامی است."))
	customer = ""
	for fieldname in ("mobile_no", "customer_primary_mobile"):
		if _has_column("Customer", fieldname):
			customer = frappe.db.get_value("Customer", {fieldname: mobile, "disabled": 0}, "name") or ""
			if customer:
				break
	if not customer:
		frappe.throw(_("مشتری با این شماره یافت نشد."))
	return _redeem_points_core(customer, cint(points))


def club_apply_fulfillment_effects(so_name):
	"""کش‌بک + امتیاز برای سفارش‌های آنلاین هنگام تحویل — idempotent."""
	try:
		club_apply_settle_effects(so_name, None, None)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant club fulfillment effects failed")


def get_customer_club_summary(customer_name):
	"""Guest-dashboard enrichment: wallet balance, points balance and loyalty tier."""
	out = {"wallet_balance": 0.0, "points_balance": 0, "loyalty_tier": "", "points_enabled": False, "points_rial_value": 0.0, "points_min_redeem": 0, "points_expiry_days": 0}
	if not customer_name or not frappe.db.exists("Customer", customer_name):
		return out
	settings = _club_club_settings()
	out["points_enabled"] = settings["points_enabled"]
	out["points_rial_value"] = flt(settings["points_rial_value"])
	out["points_min_redeem"] = cint(settings["points_min_redeem"])
	out["points_expiry_days"] = cint(settings["points_expiry_days"])
	if frappe.db.exists("DocType", CLUB_DOCTYPES["wallet"]):
		wallet_name = frappe.db.get_value(CLUB_DOCTYPES["wallet"], {"customer": customer_name}, "name")
		if wallet_name:
			out["wallet_balance"] = flt(frappe.db.get_value(CLUB_DOCTYPES["wallet"], wallet_name, "balance"))
	if frappe.db.exists("DocType", CLUB_DOCTYPES["point_entry"]):
		info = _club_points_map([customer_name]).get(customer_name, {})
		out["points_balance"] = cint(info.get("balance", 0))
		out["loyalty_tier"] = info.get("loyalty_tier", "")
	return out


# ---------------------------------------------------------------------------
# Wallet (electronic credit card) + cashback
# ---------------------------------------------------------------------------


def _club_get_or_create_wallet(customer_name):
	existing = frappe.db.get_value(CLUB_DOCTYPES["wallet"], {"customer": customer_name}, "name")
	if existing:
		return frappe.get_doc(CLUB_DOCTYPES["wallet"], existing)
	doc = frappe.new_doc(CLUB_DOCTYPES["wallet"])
	doc.customer = customer_name
	doc.balance = 0
	doc.status = "فعال"
	doc.insert(ignore_permissions=True)
	return doc


def _club_wallet_txn(*, wallet, customer, kind, direction, amount, note="", reference_doctype="", reference_name=""):
	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("مبلغ باید بزرگ‌تر از صفر باشد."))
	if wallet.get("status") != "فعال":
		frappe.throw(_("کیف پول این مشتری مسدود است."))
	if direction == "برداشت" and flt(wallet.balance) < amount - 0.009:
		frappe.throw(_("موجودی کیف پول کافی نیست."))
	wallet.balance = flt(wallet.balance) + (amount if direction == "واریز" else -amount)
	field_map = {
		"شارژ": "total_charged",
		"پرداخت": "total_spent",
		"انتقال ارسال": None,
		"انتقال دریافت": None,
		"کش‌بک": "total_rewards",
		"پاداش معرف": "total_rewards",
	}
	counter_field = field_map.get(kind)
	if counter_field:
		wallet.set(counter_field, flt(wallet.get(counter_field)) + amount)
	wallet.save(ignore_permissions=True)
	txn = frappe.new_doc(CLUB_DOCTYPES["wallet_txn"])
	txn.wallet = wallet.name
	txn.customer = customer
	txn.kind = kind
	txn.direction = direction
	txn.amount = amount
	txn.balance_after = flt(wallet.balance)
	txn.reference_doctype = reference_doctype or ""
	txn.reference_name = reference_name or ""
	txn.note = note or ""
	txn.entry_date = now_datetime()
	txn.insert(ignore_permissions=True)
	return txn


@frappe.whitelist()
def list_management_wallets(search="", limit=100, offset=0):
	_ensure_management_access()
	filters = {}
	rows = frappe.get_all(
		CLUB_DOCTYPES["wallet"],
		filters=filters,
		fields=["name", "customer", "balance", "total_charged", "total_spent", "total_rewards", "status", "modified"],
		order_by="balance desc",
		limit_start=cint(offset) or 0,
		limit_page_length=min(max(cint(limit) or 100, 1), 400),
	)
	search = (search or "").strip().lower()
	wallets = []
	for row in rows:
		customer_name = frappe.db.get_value("Customer", row["customer"], "customer_name") or row["customer"]
		if search and search not in customer_name.lower() and search not in row["customer"].lower():
			continue
		tier = frappe.db.get_value("Customer", row["customer"], "restaurant_customer_tier") if _has_column("Customer", "restaurant_customer_tier") else ""
		wallets.append(
			{
				"wallet": row["name"],
				"customer": row["customer"],
				"customer_name": customer_name,
				"tier": tier or "",
				"balance": flt(row["balance"]),
				"total_charged": flt(row["total_charged"]),
				"total_spent": flt(row["total_spent"]),
				"total_rewards": flt(row["total_rewards"]),
				"status": row.get("status") or "فعال",
				"modified": str(row.get("modified") or ""),
			}
		)
	return {"wallets": wallets, "count": len(wallets)}


@frappe.whitelist()
def get_management_wallet_detail(customer=""):
	_ensure_management_access()
	customer = (customer or "").strip()
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("مشتری یافت نشد: {0}").format(customer or "-"))
	wallet = _club_get_or_create_wallet(customer)
	txns = frappe.get_all(
		CLUB_DOCTYPES["wallet_txn"],
		filters={"customer": customer},
		fields=["name", "kind", "direction", "amount", "balance_after", "reference_doctype", "reference_name", "note", "entry_date"],
		order_by="creation desc",
		limit_page_length=100,
	)
	return {
		"wallet": {
			"name": wallet.name,
			"customer": wallet.customer,
			"customer_name": frappe.db.get_value("Customer", customer, "customer_name") or customer,
			"balance": flt(wallet.balance),
			"total_charged": flt(wallet.total_charged),
			"total_spent": flt(wallet.total_spent),
			"total_rewards": flt(wallet.total_rewards),
			"status": wallet.get("status") or "فعال",
		},
		"transactions": [
			{**row, "amount": flt(row["amount"]), "balance_after": flt(row["balance_after"]), "entry_date": str(row.get("entry_date") or "")}
			for row in txns
		],
		"points": {
			"balance": _club_points_balance(customer),
			"settings": {
				"enabled": _club_club_settings()["points_enabled"],
				"rial_value": _club_club_settings()["points_rial_value"],
				"min_redeem": _club_club_settings()["points_min_redeem"],
			},
		},
		"point_entries": (list_management_point_entries(customer=customer, limit=20).get("entries") if frappe.db.exists("DocType", CLUB_DOCTYPES["point_entry"]) else []),
		"count": len(txns),
	}


@frappe.whitelist()
def charge_management_wallet(payload=None):
	"""Charge a customer's wallet (electronic credit card top-up)."""
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	customer = (payload.get("customer") or "").strip()
	amount = flt(payload.get("amount"))
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("مشتری یافت نشد: {0}").format(customer or "-"))
	wallet = _club_get_or_create_wallet(customer)
	txn = _club_wallet_txn(
		wallet=wallet,
		customer=customer,
		kind="شارژ",
		direction="واریز",
		amount=amount,
		note=(payload.get("note") or "").strip(),
	)
	frappe.db.commit()
	return {"status": "success", "txn": txn.name, "balance": flt(wallet.balance)}


@frappe.whitelist()
def transfer_management_wallet(payload=None):
	"""Transfer credit between two customer wallets."""
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	from_customer = (payload.get("from_customer") or "").strip()
	to_customer = (payload.get("to_customer") or "").strip()
	amount = flt(payload.get("amount"))
	if from_customer == to_customer:
		frappe.throw(_("مبدأ و مقصد انتقال نمی‌توانند یکسان باشند."))
	for customer in (from_customer, to_customer):
		if not frappe.db.exists("Customer", customer):
			frappe.throw(_("مشتری یافت نشد: {0}").format(customer or "-"))
	note = (payload.get("note") or "").strip()
	from_wallet = _club_get_or_create_wallet(from_customer)
	to_wallet = _club_get_or_create_wallet(to_customer)
	out_txn = _club_wallet_txn(
		wallet=from_wallet,
		customer=from_customer,
		kind="انتقال ارسال",
		direction="برداشت",
		amount=amount,
		note=note or _("انتقال به {0}").format(to_customer),
		reference_doctype=CLUB_DOCTYPES["wallet_txn"],
	)
	in_txn = _club_wallet_txn(
		wallet=to_wallet,
		customer=to_customer,
		kind="انتقال دریافت",
		direction="واریز",
		amount=amount,
		note=note or _("دریافت از {0}").format(from_customer),
		reference_doctype=CLUB_DOCTYPES["wallet_txn"],
		reference_name=out_txn.name,
	)
	frappe.db.commit()
	return {"status": "success", "out_txn": out_txn.name, "in_txn": in_txn.name}


@frappe.whitelist()
def adjust_management_wallet(payload=None):
	"""Manual signed adjustment (تعدیل دستی) on a wallet."""
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	customer = (payload.get("customer") or "").strip()
	amount = flt(payload.get("amount"))
	if not amount:
		frappe.throw(_("مبلغ تعدیل را وارد کنید (مثبت یا منفی)."))
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("مشتری یافت نشد: {0}").format(customer or "-"))
	wallet = _club_get_or_create_wallet(customer)
	txn = _club_wallet_txn(
		wallet=wallet,
		customer=customer,
		kind="تعدیل دستی",
		direction="واریز" if amount > 0 else "برداشت",
		amount=abs(amount),
		note=(payload.get("note") or "").strip(),
	)
	frappe.db.commit()
	return {"status": "success", "txn": txn.name, "balance": flt(wallet.balance)}


def _club_wallet_mode_match(splits, split_details, mode_of_payment_name):
	"""True when a POS payment used the configured wallet Mode of Payment."""
	mode = (mode_of_payment_name or "").strip()
	if not mode:
		return False
	for split in splits or []:
		if (split.get("mode_of_payment") or "").strip() == mode:
			return True
	for row in split_details or []:
		if (row.get("mode_of_payment") or "").strip() == mode:
			return True
	return False


def club_apply_settle_effects(so_name, splits=None, payment_breakdown=None):
	"""Called from settle_pos_order AFTER successful payment: wallet debit + cashback.

	Idempotent — safe to call on retries.
	"""
	try:
		settings = _club_club_settings()
		if not settings["club_enabled"]:
			return
		if not frappe.db.exists("DocType", CLUB_DOCTYPES["wallet"]):
			return
		customer = frappe.db.get_value("Sales Order", so_name, "customer") if frappe.db.exists("Sales Order", so_name) else ""
		if not customer:
			return
		grand_total = flt(frappe.db.get_value("Sales Order", so_name, "grand_total"))

		# 1) Wallet payment deduction — only when the wallet Mode of Payment was used
		if settings["wallet_mode_of_payment"] and _club_wallet_mode_match(splits, payment_breakdown, settings["wallet_mode_of_payment"]):
			wallet_amount = 0.0
			for row in list(splits or []) + list(payment_breakdown or []):
				if (row.get("mode_of_payment") or "").strip() == settings["wallet_mode_of_payment"]:
					wallet_amount += flt(row.get("amount") or row.get("paid_amount") or 0)
			if wallet_amount > 0:
				exists = frappe.db.exists(
					CLUB_DOCTYPES["wallet_txn"],
					{"reference_name": so_name, "kind": "پرداخت", "customer": customer},
				)
				if not exists:
					wallet = _club_get_or_create_wallet(customer)
					_club_wallet_txn(
						wallet=wallet,
						customer=customer,
						kind="پرداخت",
						direction="برداشت",
						amount=min(wallet_amount, flt(wallet.balance)),
						note=_("پرداخت سفارش {0} با کیف پول").format(so_name),
						reference_doctype="Sales Order",
						reference_name=so_name,
					)

		# 2) Cashback on the settled amount
		credited = _has_column("Sales Order", "restaurant_cashback_credited") and cint(
			frappe.db.get_value("Sales Order", so_name, "restaurant_cashback_credited")
		)
		if settings["cashback_percent"] > 0 and not credited:
			if grand_total >= settings["cashback_min_order"] or settings["cashback_min_order"] <= 0:
				cashback = flt(grand_total * settings["cashback_percent"] / 100.0, 2)
				if cashback > 0:
					wallet = _club_get_or_create_wallet(customer)
					_club_wallet_txn(
						wallet=wallet,
						customer=customer,
						kind="کش‌بک",
						direction="واریز",
						amount=cashback,
						note=_("کش‌بک {0}٪ سفارش {1}").format(flt(settings["cashback_percent"], 1), so_name),
						reference_doctype="Sales Order",
						reference_name=so_name,
					)
				if _has_column("Sales Order", "restaurant_cashback_credited"):
					frappe.db.set_value("Sales Order", so_name, "restaurant_cashback_credited", 1, update_modified=False)

		# 3) Loyalty points earn on settled/fulfilled amount
		_club_process_points_earning(so_name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant club settle effects failed")


# ---------------------------------------------------------------------------
# Referral (brand ambassadors)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_referral_summary():
	_ensure_management_access()
	if not _has_column("Customer", "restaurant_referral_code"):
		return {"ambassadors": 0, "referrals": 0, "rewards_paid": 0.0, "top": []}
	ambassadors = frappe.db.count("Customer", [["restaurant_referral_code", "!=", ""]]) or 0
	referrals = frappe.db.count("Customer", [["restaurant_referred_by", "!=", ""]]) or 0
	reward_row = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(amount),0) AS amount FROM `tabRestaurant Wallet Transaction`
		WHERE kind = 'پاداش معرف'
		""",
		as_dict=True,
	) if frappe.db.exists("DocType", CLUB_DOCTYPES["wallet_txn"]) else []
	rewards_paid = flt(reward_row[0].get("amount")) if reward_row else 0.0
	top = frappe.db.sql(
		"""
		SELECT c.restaurant_referred_by AS referrer, c2.customer_name, COUNT(*) AS count
		FROM `tabCustomer` c
		LEFT JOIN `tabCustomer` c2 ON c2.name = c.restaurant_referred_by
		WHERE COALESCE(c.restaurant_referred_by,'') != ''
		GROUP BY c.restaurant_referred_by, c2.customer_name
		ORDER BY count DESC LIMIT 10
		""",
		as_dict=True,
	) if _has_column("Customer", "restaurant_referred_by") else []
	return {
		"ambassadors": cint(ambassadors),
		"referrals": cint(referrals),
		"rewards_paid": rewards_paid,
		"settings": {
			"referrer_reward": _club_club_settings()["referral_referrer_reward"],
			"referee_reward": _club_club_settings()["referral_referee_reward"],
		},
		"top": [{"referrer": row.get("referrer"), "customer_name": row.get("customer_name") or row.get("referrer"), "count": cint(row.get("count"))} for row in top],
	}


def _club_process_referral_reward(so_name):
	"""Credit referral wallets for a delivered order using a referral code (daily job)."""
	settings = _club_club_settings()
	if not settings["club_enabled"] or not _has_column("Sales Order", "restaurant_referral_code"):
		return False
	code, customer, status = frappe.db.get_value(
		"Sales Order", so_name, ["restaurant_referral_code", "customer", "restaurant_status"], as_dict=False
	) if frappe.db.exists("Sales Order", so_name) else ("", "", "")
	code = (code or "").strip()
	if not code or not customer:
		return False
	if status not in ("delivered", "served", "ready"):
		return False
	if not _has_column("Customer", "restaurant_referral_code"):
		return False
	referrer = frappe.db.get_value("Customer", {"restaurant_referral_code": code}, "name")
	if not referrer or referrer == customer:
		return False
	# only the referee's FIRST delivered order counts
	prev = frappe.db.count(
		"Sales Order",
		{
			"customer": customer,
			"docstatus": 1,
			"name": ["!=", so_name],
			"restaurant_referral_code": code,
		},
	)
	if prev:
		return False
	already = frappe.db.exists(CLUB_DOCTYPES["wallet_txn"], {"reference_name": so_name, "kind": "پاداش معرف"})
	if already:
		return False
	wallet_referrer = _club_get_or_create_wallet(referrer)
	if settings["referral_referrer_reward"] > 0:
		_club_wallet_txn(
			wallet=wallet_referrer,
			customer=referrer,
			kind="پاداش معرف",
			direction="واریز",
			amount=settings["referral_referrer_reward"],
			note=_("پاداش معرفی {0} (سفارش {1})").format(customer, so_name),
			reference_doctype="Sales Order",
			reference_name=so_name,
		)
	if settings["referral_referee_reward"] > 0:
		wallet_referee = _club_get_or_create_wallet(customer)
		_club_wallet_txn(
			wallet=wallet_referee,
			customer=customer,
			kind="پاداش معرف",
			direction="واریز",
			amount=settings["referral_referee_reward"],
			note=_("پاداش عضویت با کد معرف (سفارش {0})").format(so_name),
			reference_doctype="Sales Order",
			reference_name=so_name,
		)
	if _has_column("Customer", "restaurant_referred_by"):
		referred_by = frappe.db.get_value("Customer", customer, "restaurant_referred_by") or ""
		if not referred_by:
			frappe.db.set_value("Customer", customer, "restaurant_referred_by", referrer, update_modified=False)
	return True


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_management_campaigns(status=""):
	_ensure_management_access()
	filters = {}
	if status and status in CAMPAIGN_STATUSES:
		filters["status"] = status
	rows = frappe.get_all(
		CLUB_DOCTYPES["campaign"],
		filters=filters or {},
		fields=["name", "title", "coupon", "channels", "valid_from", "valid_to", "bonus_type", "bonus_value", "status", "target_segment", "min_order_amount", "modified"],
		order_by="creation desc",
		limit_page_length=200,
	)
	campaigns = []
	for row in rows:
		stats = _club_campaign_stats(row)
		campaigns.append({**row, "valid_from": str(row.get("valid_from") or ""), "valid_to": str(row.get("valid_to") or ""), "valid_to_readable": str(row.get("valid_to") or ""), **stats})
	return {"campaigns": campaigns, "count": len(campaigns)}


def _club_campaign_channels(row):
	return [c.strip() for c in (row.get("channels") or "").split(",") if c.strip()]


def _club_campaign_stats(row):
	coupon_code = (row.get("coupon") or "").strip()
	used_count = 0
	if coupon_code and frappe.db.exists("Restaurant Coupon", coupon_code):
		used_count = cint(frappe.db.get_value("Restaurant Coupon", coupon_code, "used_count") or 0)
	channels = _club_campaign_channels(row)
	order_count = 0
	revenue = 0.0
	if channels and frappe.db.exists("DocType", "Sales Order") and _has_column("Sales Order", "restaurant_order_type"):
		conditions = ["docstatus = 1", "status != 'Cancelled'"]
		params = {}
		if row.get("valid_from"):
			conditions.append("transaction_date >= %(df)s")
			params["df"] = row.get("valid_from")
		if row.get("valid_to"):
			conditions.append("transaction_date <= %(dt)s")
			params["dt"] = row.get("valid_to")
		conditions.append("COALESCE(restaurant_order_type,'') IN %(channels)s")
		params["channels"] = tuple(channels)
		result = frappe.db.sql(
			"""
			SELECT COUNT(*) AS count, COALESCE(SUM(grand_total),0) AS revenue
			FROM `tabSales Order`
			WHERE {conditions}
			""".format(
				conditions=" AND ".join(conditions)
			),
			params,
			as_dict=True,
		)
		order_count = cint(result[0].get("count")) if result else 0
		revenue = flt(result[0].get("revenue")) if result else 0.0
	bonus_budget = used_count * flt(row.get("bonus_value"))
	return {
		"participants": used_count,
		"channel_orders": order_count,
		"channel_revenue": flt(revenue),
		"bonus_budget": flt(bonus_budget),
		"conversion_hint": flt((used_count / order_count) * 100, 1) if order_count else 0.0,
	}


@frappe.whitelist()
def save_management_campaign(payload=None):
	"""Create/update an unlimited marketing campaign."""
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	name = (payload.get("name") or "").strip()
	title = (payload.get("title") or "").strip()
	if not title:
		frappe.throw(_("عنوان کمپین الزامی است."))

	if name and frappe.db.exists(CLUB_DOCTYPES["campaign"], name):
		doc = frappe.get_doc(CLUB_DOCTYPES["campaign"], name)
		created = False
	else:
		doc = frappe.new_doc(CLUB_DOCTYPES["campaign"])
		created = True
	doc.title = title
	coupon = (payload.get("coupon") or "").strip()
	if coupon and frappe.db.exists("Restaurant Coupon", coupon):
		doc.coupon = coupon
	elif not coupon:
		doc.coupon = None
	channels = payload.get("channels")
	if isinstance(channels, list):
		doc.channels = ", ".join([c.strip() for c in channels if c and c.strip()])
	elif channels is not None:
		doc.channels = (channels or "").strip()
	doc.valid_from = payload.get("valid_from") or None
	doc.valid_to = payload.get("valid_to") or None
	bonus_type = (payload.get("bonus_type") or "کش‌بک").strip()
	if bonus_type not in CAMPAIGN_BONUS_TYPES:
		bonus_type = "کش‌بک"
	doc.bonus_type = bonus_type
	doc.bonus_value = flt(payload.get("bonus_value"))
	target_segment = (payload.get("target_segment") or "").strip()
	doc.target_segment = target_segment
	doc.sms_text = (payload.get("sms_text") or "").strip()
	doc.min_order_amount = flt(payload.get("min_order_amount"))
	if payload.get("status") in CAMPAIGN_STATUSES:
		doc.status = payload.get("status")
	elif created:
		doc.status = "پیش‌نویس"
	doc.notes = (payload.get("notes") or "").strip()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "created": created, "name": doc.name}


@frappe.whitelist()
def update_management_campaign_status(payload=None):
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	name = (payload.get("name") or "").strip()
	status = (payload.get("status") or "").strip()
	if status not in CAMPAIGN_STATUSES:
		frappe.throw(_("وضعیت نامعتبر است: {0}").format(status or "-"))
	if not frappe.db.exists(CLUB_DOCTYPES["campaign"], name):
		frappe.throw(_("کمپین یافت نشد: {0}").format(name or "-"))
	frappe.db.set_value(CLUB_DOCTYPES["campaign"], name, "status", status, update_modified=False)
	frappe.db.commit()
	return {"status": "success", "name": name, "status": status}


@frappe.whitelist()
def get_management_campaign_stats(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(CLUB_DOCTYPES["campaign"], name):
		frappe.throw(_("کمپین یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc(CLUB_DOCTYPES["campaign"], name)
	return {"campaign": doc.title, **_club_campaign_stats(doc.as_dict()), "bonus_budget": _club_campaign_stats(doc.as_dict()).get("bonus_budget")}


# ---------------------------------------------------------------------------
# Smart surveys (per-order + custom questions + instant alerts)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_management_survey_questions(include_inactive=0):
	_ensure_management_access()
	filters = {} if cint(include_inactive) else {"is_active": 1}
	rows = frappe.get_all(
		CLUB_DOCTYPES["survey_question"],
		filters=filters,
		fields=["name", "question", "answer_type", "sort_order", "is_active"],
		order_by="sort_order asc, creation asc",
		limit_page_length=200,
	)
	return {"questions": rows, "count": len(rows)}


@frappe.whitelist()
def save_management_survey_question(payload=None):
	_ensure_management_access()
	payload = _club_parse_json(payload, {})
	name = (payload.get("name") or "").strip()
	question = (payload.get("question") or "").strip()
	if not question:
		frappe.throw(_("متن سوال الزامی است."))
	if name and frappe.db.exists(CLUB_DOCTYPES["survey_question"], name):
		doc = frappe.get_doc(CLUB_DOCTYPES["survey_question"], name)
	else:
		doc = frappe.new_doc(CLUB_DOCTYPES["survey_question"])
	doc.question = question
	answer_type = (payload.get("answer_type") or "امتیاز ۱ تا ۵").strip()
	doc.answer_type = answer_type if answer_type in ("امتیاز ۱ تا ۵", "بله/خیر", "متن آزاد") else "امتیاز ۱ تا ۵"
	doc.sort_order = cint(payload.get("sort_order"))
	doc.is_active = cint(payload.get("is_active", 1))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "name": doc.name}


@frappe.whitelist()
def delete_management_survey_question(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(CLUB_DOCTYPES["survey_question"], name):
		frappe.throw(_("سوال یافت نشد: {0}").format(name or "-"))
	frappe.delete_doc(CLUB_DOCTYPES["survey_question"], name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}


def _club_verify_survey_order(order_code, mobile):
	"""Return (Sales Order name, customer name) if the (order, mobile) pair matches."""
	order_code = (order_code or "").strip()
	mobile = (mobile or "").strip()
	if not order_code or not mobile:
		return None
	if not frappe.db.exists("DocType", "Sales Order"):
		return None
	candidates = [order_code]
	if not order_code.startswith("SO-"):
		candidates.append(f"SO-{order_code}")
	for so_name in candidates:
		if not frappe.db.exists("Sales Order", so_name):
			continue
		if cint(frappe.db.get_value("Sales Order", so_name, "docstatus")) != 1:
			continue
		customer = frappe.db.get_value("Sales Order", so_name, "customer") or ""
		order_mobile = _club_customer_mobile(customer)
		clean = lambda v: "".join(ch for ch in str(v or "") if ch.isdigit())
		if clean(order_mobile) and clean(mobile).endswith(clean(order_mobile)[-7:]):
			return {"sales_order": so_name, "customer": customer}
		if clean(mobile) and clean(order_mobile) and clean(order_mobile).endswith(clean(mobile)[-7:]):
			return {"sales_order": so_name, "customer": customer}
		if customer and not order_mobile:
			return {"sales_order": so_name, "customer": customer}
	return None


@frappe.whitelist(allow_guest=True)
def get_public_survey(order_code="", mobile=""):
	"""Public per-order survey form context (guest)."""
	match = _club_verify_survey_order(order_code, mobile)
	if not match:
		return {"valid": 0, "message": _("سفارش با این کد و شماره موبایل یافت نشد.")}
	answered = frappe.db.exists(
		CLUB_DOCTYPES["survey_response"],
		{"sales_order": match["sales_order"], "mobile": mobile},
	)
	questions = frappe.get_all(
		CLUB_DOCTYPES["survey_question"],
		filters={"is_active": 1},
		fields=["name", "question", "answer_type", "sort_order"],
		order_by="sort_order asc, creation asc",
		limit_page_length=100,
	)
	return {
		"valid": 1,
		"answered": 1 if answered else 0,
		"sales_order": match["sales_order"],
		"customer_name": frappe.db.get_value("Customer", match["customer"], "customer_name") if match["customer"] else "",
		"questions": questions,
	}


@frappe.whitelist(allow_guest=True)
def submit_public_survey(payload=None):
	"""Submit a guest survey per order; instant-alert managers on dissatisfaction."""
	payload = _club_parse_json(payload, {}) if isinstance(payload, str) else _club_parse_payload(payload)
	order_code = (payload.get("order_code") or "").strip()
	mobile = (payload.get("mobile") or "").strip()
	match = _club_verify_survey_order(order_code, mobile)
	if not match:
		frappe.throw(_("سفارش با این کد و شماره موبایل یافت نشد."))
	so_name = match["sales_order"]
	if frappe.db.exists(CLUB_DOCTYPES["survey_response"], {"sales_order": so_name, "mobile": mobile}):
		frappe.throw(_("برای این سفارش قبلاً نظرسنجی ثبت شده است. متشکریم!"))

	answers = payload.get("answers") or []
	overall = cint(payload.get("overall_rating"))
	if not overall:
		rated = [cint(a.get("value")) for a in answers if str(a.get("answer_type", "")).startswith("امتیاز") and cint(a.get("value"))]
		overall = round(sum(rated) / len(rated)) if rated else 0

	doc = frappe.new_doc(CLUB_DOCTYPES["survey_response"])
	doc.order_code = order_code
	doc.sales_order = so_name
	doc.customer = match["customer"] or None
	doc.mobile = mobile
	doc.overall_rating = max(1, min(5, overall or 1))
	doc.answers_json = json.dumps(answers, ensure_ascii=False)
	doc.comment = (payload.get("comment") or "").strip()
	doc.entry_date = now_datetime()
	doc.insert(ignore_permissions=True)

	settings = _club_club_settings()
	alerted = 0
	if doc.overall_rating <= settings["survey_alert_threshold"]:
		alerted = _club_alert_dissatisfaction(doc, threshold=settings["survey_alert_threshold"], users=settings["survey_alert_users"])
	doc.dissatisfaction_alerted = alerted
	if alerted:
		doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "name": doc.name, "alerted": alerted}


def _club_alert_dissatisfaction(doc, threshold=3, users=None):
	"""Instant alert to management users via ERPNext Notification Log."""
	recipients = [u for u in (users or []) if u]
	if not recipients:
		try:
			recipients = [
				row["parent"]
				for row in frappe.get_all(
					"Has Role",
					filters={"role": ["in", ["System Manager", "Restaurant Manager"]]},
					fields=["parent"],
				)
				if row.get("parent") not in ("Guest", "Administrator")
			][:5]
		except Exception:
			recipients = []
	alerted = 0
	subject = _("نارضایتی مشتری از سفارش {0}").format(doc.sales_order or doc.order_code)
	for user in recipients:
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"type": "Alert",
					"document_type": CLUB_DOCTYPES["survey_response"],
					"document_name": doc.name,
					"from_user": frappe.session.user if frappe.session.user != "Guest" else "Administrator",
					"for_user": user,
					"subject": subject,
					"email_content": _("امتیاز {0}: {1}").format(doc.overall_rating, doc.comment or "-"),
				}
			).insert(ignore_permissions=True)
			alerted = 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Restaurant survey alert failed")
	return alerted


@frappe.whitelist()
def list_management_survey_responses(date_from="", date_to="", search="", min_rating=0, max_rating=0):
	_ensure_management_access()
	filters = {}
	rows = frappe.get_all(
		CLUB_DOCTYPES["survey_response"],
		filters=filters,
		fields=["name", "order_code", "sales_order", "customer", "mobile", "overall_rating", "comment", "dissatisfaction_alerted", "entry_date", "answers_json"],
		order_by="creation desc",
		limit_page_length=500,
	)
	search = (search or "").strip().lower()
	min_rating = cint(min_rating)
	max_rating = cint(max_rating)
	items = []
	for row in rows:
		entry = str(row.get("entry_date") or "")[:10]
		if date_from and entry < str(date_from):
			continue
		if date_to and entry > str(date_to):
			continue
		if min_rating and cint(row.get("overall_rating")) < min_rating:
			continue
		if max_rating and cint(row.get("overall_rating")) > max_rating:
			continue
		try:
			answers = json.loads(row.get("answers_json") or "[]")
		except Exception:
			answers = []
		customer_name = frappe.db.get_value("Customer", row["customer"], "customer_name") if row.get("customer") else ""
		if search:
			haystack = " ".join(
				str(part or "")
				for part in (row.get("order_code"), row.get("mobile"), customer_name, row.get("comment"))
			).lower()
			if search not in haystack:
				continue
		items.append(
			{
				**{k: v for k, v in row.items() if k != "answers_json"},
				"customer_name": customer_name or row.get("customer") or "",
				"entry_date": str(row.get("entry_date") or ""),
				"answers": answers,
			}
		)
	return {"responses": items, "count": len(items)}


# ---------------------------------------------------------------------------
# Auto jobs (scheduler): birthday / welcome / inactive SMS + referral rewards
# ---------------------------------------------------------------------------


def run_daily_customer_club_jobs():
	"""Daily: birthday greetings, welcome SMS, inactive reminders, referral rewards."""
	settings = _club_club_settings()
	if not settings["club_enabled"]:
		return
	_club_ensure_ops_ready()
	templates = settings["sms_templates"]
	date_map = {"birthdays": 0, "welcomes": 0, "reminders": 0, "referrals": 0}
	today_ = getdate(today())

	if _has_column("Customer", "restaurant_birth_date"):
		rows = frappe.get_all(
			"Customer",
			filters={"disabled": 0, "restaurant_birth_date": ["is", "set"]},
			fields=["name", "customer_name", "restaurant_birth_date", "restaurant_membership_code"] + (
				["mobile_no"] if _has_column("Customer", "mobile_no") else []
			),
			limit_page_length=2000,
		)
		for row in rows:
			birth = getdate(row.get("restaurant_birth_date")) if row.get("restaurant_birth_date") else None
			if not birth or (birth.month, birth.day) != (today_.month, today_.day):
				continue
			mobile = _club_customer_mobile(row["name"])
			if not mobile:
				continue
			already = frappe.db.exists(
				CLUB_DOCTYPES["sms"],
				{"customer": row["name"], "kind": "تبریک تولد", "sent_at": [">=", f"{today_} 00:00:00"]},
			)
			if already:
				continue
			text = _club_render_sms(templates.get("birthday", ""), row.get("customer_name") or row["name"], row.get("restaurant_membership_code") or "")
			status, note = _club_send_sms_now(mobile, text)
			_club_log_sms(mobile=mobile, message=text, kind="تبریک تولد", customer=row["name"], template_key="birthday", status_note=(status, note))
			date_map["birthdays"] += 1

	yesterday = add_days(today_, -1)
	new_customers = frappe.get_all(
		"Customer",
		filters={"disabled": 0, "creation": [">=", f"{yesterday} 00:00:00"]},
		fields=["name", "customer_name"] + (
			["restaurant_membership_code"] if _has_column("Customer", "restaurant_membership_code") else []
		),
		limit_page_length=500,
	)
	for row in new_customers:
		already = frappe.db.exists(CLUB_DOCTYPES["sms"], {"customer": row["name"], "kind": "خوش‌آمدگویی"})
		if already:
			continue
		mobile = _club_customer_mobile(row["name"])
		if not mobile:
			continue
		_club_assign_membership_code(row["name"])
		code = frappe.db.get_value("Customer", row["name"], "restaurant_membership_code") if _has_column("Customer", "restaurant_membership_code") else ""
		text = _club_render_sms(templates.get("welcome", ""), row.get("customer_name") or row["name"], code or "")
		status, note = _club_send_sms_now(mobile, text)
		_club_log_sms(mobile=mobile, message=text, kind="خوش‌آمدگویی", customer=row["name"], template_key="welcome", status_note=(status, note))
		date_map["welcomes"] += 1

	if frappe.db.exists("DocType", "Sales Order"):
		inactive_before = add_days(today_, -30)
		stats_rows = frappe.db.sql(
			"""
			SELECT customer, MAX(transaction_date) AS last_order
			FROM `tabSales Order`
			WHERE docstatus = 1 AND status != 'Cancelled'
			GROUP BY customer
			HAVING last_order < %(cutoff)s
			""",
			{"cutoff": inactive_before},
			as_dict=True,
		)
		for row in stats_rows[:500]:
			customer = row.get("customer")
			last = getdate(row.get("last_order")) if row.get("last_order") else None
			if not customer or not last or (today_ - last).days > 40:
				continue
			already = frappe.db.exists(
				CLUB_DOCTYPES["sms"],
				{"customer": customer, "kind": "یادآوری خرید", "sent_at": [">=", f"{add_days(today_, -14)} 00:00:00"]},
			)
			if already:
				continue
			mobile = _club_customer_mobile(customer)
			if not mobile:
				continue
			customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
			code = frappe.db.get_value("Customer", customer, "restaurant_membership_code") if _has_column("Customer", "restaurant_membership_code") else ""
			text = _club_render_sms(templates.get("inactive", ""), customer_name, code or "")
			status, note = _club_send_sms_now(mobile, text)
			_club_log_sms(mobile=mobile, message=text, kind="یادآوری خرید", customer=customer, template_key="inactive", status_note=(status, note))
			date_map["reminders"] += 1

	if _has_column("Sales Order", "restaurant_referral_code"):
		candidates = frappe.get_all(
			"Sales Order",
			filters={
				"docstatus": 1,
				"restaurant_referral_code": ["!=", ""],
				"transaction_date": [">=", add_days(today_, -2)],
			},
			pluck="name",
			limit_page_length=200,
		)
		for so_name in candidates:
			try:
				if _club_process_referral_reward(so_name):
					date_map["referrals"] += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Referral reward failed for {so_name}")

	try:
		date_map["points_expired"] = cint(_club_expire_points())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant loyalty points expiry failed")

	frappe.db.commit()
	return date_map


# ---------------------------------------------------------------------------
# Report-center reports for the club domain
# ---------------------------------------------------------------------------


def _club_rfm_rows():
	names = frappe.get_all("Customer", filters={"disabled": 0}, pluck="name", limit_page_length=2000)
	stats = _club_customer_stats_batch(names)
	today_ = getdate(today())
	rows = []
	for name in names:
		stat = stats.get(name)
		if not stat or not stat.get("orders"):
			continue
		last = getdate(stat.get("last_order")) if stat.get("last_order") else None
		first = getdate(stat.get("first_order")) if stat.get("first_order") else None
		recency = (today_ - last).days if last else 9999
		tenure = max((today_ - first).days, 1) if first else 1
		frequency = cint(stat.get("orders"))
		monetary = flt(stat.get("total_spent"))
		clv = monetary / tenure * 365 if tenure else monetary
		segment = _club_segment_for_stats(stat)
		tier = _club_tier_for_stats(stat)
		customer_name = frappe.db.get_value("Customer", name, "customer_name") or name
		rows.append(
			{
				"customer": name,
				"customer_name": customer_name,
				"tier": tier,
				"segment": segment,
				"recency_days": recency,
				"frequency": frequency,
				"monetary": monetary,
				"avg_order": flt(monetary / max(frequency, 1)),
				"clv_yearly": flt(clv),
				"first_order": str(first or ""),
				"last_order": str(last or ""),
			}
		)
	rows.sort(key=lambda row: -row["monetary"])
	return rows


@frappe.whitelist()
def get_management_report_customer_analytics(date_from=None, date_to=None):
	_ensure_management_access()
	rows = _club_rfm_rows()
	summary = {
		"customers": len(rows),
		"avg_frequency": flt(sum(r["frequency"] for r in rows) / max(len(rows), 1), 1),
		"avg_clv": flt(sum(r["clv_yearly"] for r in rows) / max(len(rows), 1)),
		"total_revenue": flt(sum(r["monetary"] for r in rows)),
	}
	return _compose_management_report(
		"customer-analytics",
		"Customer Analytics (RFM / CLV)",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_campaign_performance(date_from=None, date_to=None):
	_ensure_management_access()
	campaign_rows = frappe.get_all(
		CLUB_DOCTYPES["campaign"],
		fields=["name", "title", "status", "channels", "valid_from", "valid_to", "bonus_type", "bonus_value", "coupon"],
		order_by="creation desc",
		limit_page_length=200,
	)
	rows = []
	for row in campaign_rows:
		stats = _club_campaign_stats(row)
		rows.append(
			{
				"campaign": row.get("name"),
				"title": row.get("title"),
				"status": row.get("status"),
				"participants": stats.get("participants"),
				"channel_orders": stats.get("channel_orders"),
				"revenue": stats.get("channel_revenue"),
				"bonus_budget": stats.get("bonus_budget"),
				"conversion_hint": stats.get("conversion_hint"),
			}
		)
	summary = {
		"campaigns": len(rows),
		"active": sum(1 for row in rows if row["status"] == "فعال"),
		"participants": sum(cint(row["participants"]) for row in rows),
		"revenue": flt(sum(flt(row["revenue"]) for row in rows)),
	}
	return _compose_management_report(
		"campaign-performance",
		"Campaign Performance",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_wallet_summary(date_from=None, date_to=None):
	_ensure_management_access()
	wallets = frappe.get_all(
		CLUB_DOCTYPES["wallet"],
		fields=["customer", "balance", "total_charged", "total_spent", "total_rewards"],
		limit_page_length=500,
	)
	rows = []
	for row in wallets:
		customer_name = frappe.db.get_value("Customer", row["customer"], "customer_name") or row["customer"]
		rows.append(
			{
				"customer": row["customer"],
				"customer_name": customer_name,
				"granted": flt(row["total_charged"]),
				"rewards": flt(row["total_rewards"]),
				"used": flt(row["total_spent"]),
				"balance": flt(row["balance"]),
			}
		)
	rows.sort(key=lambda row: -row["granted"])
	summary = {
		"wallets": len(rows),
		"granted": flt(sum(r["granted"] for r in rows)),
		"used": flt(sum(r["used"] for r in rows)),
		"balance": flt(sum(r["balance"] for r in rows)),
	}
	return _compose_management_report(
		"wallet-summary",
		"Customer Credit Summary",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_credit_transactions(date_from=None, date_to=None):
	_ensure_management_access()
	date_to = str(date_to or today())
	date_from = str(date_from or add_days(date_to, -29))
	rows = frappe.db.sql(
		"""
		SELECT customer, kind, direction, SUM(amount) AS amount, COUNT(*) AS count
		FROM `tabRestaurant Wallet Transaction`
		WHERE entry_date BETWEEN %(df)s AND %(dt)s + INTERVAL 1 DAY
		GROUP BY customer, kind, direction
		""",
		{"df": date_from, "dt": date_to},
		as_dict=True,
	)
	out = []
	for row in rows:
		customer_name = frappe.db.get_value("Customer", row["customer"], "customer_name") or row["customer"]
		out.append(
			{
				"customer": row.get("customer"),
				"customer_name": customer_name,
				"kind": row.get("kind"),
				"direction": row.get("direction"),
				"amount": flt(row.get("amount")),
				"count": cint(row.get("count")),
			}
		)
	out.sort(key=lambda row: -row["amount"])
	summary = {
		"rows": len(out),
		"total": flt(sum(r["amount"] for r in out)),
	}
	return _compose_management_report(
		"credit-transactions",
		"Credit Card Transactions",
		summary,
		out,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_care_feedback(date_from=None, date_to=None):
	_ensure_management_access()
	if not frappe.db.exists("DocType", "Restaurant Customer Review"):
		return _compose_management_report("care-feedback", "Site Feedback", {}, [], date_from=date_from, date_to=date_to, source="all", orders=[])
	date_to = str(date_to or today())
	date_from = str(date_from or add_days(date_to, -29))
	rows = frappe.db.sql(
		"""
		SELECT item, item_slug, COUNT(*) AS count, AVG(rating) AS avg_rating,
			   MIN(rating) AS min_rating, MAX(rating) AS max_rating
		FROM `tabRestaurant Customer Review`
		WHERE creation BETWEEN %(df)s AND %(dt)s + INTERVAL 1 DAY
		GROUP BY item, item_slug
		ORDER BY count DESC
		""",
		{"df": date_from, "dt": date_to},
		as_dict=True,
	)
	out = [
		{
			"item": row.get("item") or row.get("item_slug") or "",
			"count": cint(row.get("count")),
			"avg_rating": flt(row.get("avg_rating"), 2),
			"min_rating": cint(row.get("min_rating")),
			"max_rating": cint(row.get("max_rating")),
		}
		for row in rows
	]
	summary = {
		"items": len(out),
		"reviews": sum(r["count"] for r in out),
		"avg_rating": flt(sum(r["avg_rating"] * r["count"] for r in out) / max(sum(r["count"] for r in out), 1), 2),
	}
	return _compose_management_report(
		"care-feedback",
		"Site Feedback",
		summary,
		out,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_survey_analytics(date_from=None, date_to=None):
	_ensure_management_access()
	date_to = str(date_to or today())
	date_from = str(date_from or add_days(date_to, -29))
	rows = frappe.db.sql(
		"""
		SELECT DATE(entry_date) AS day, COUNT(*) AS count, AVG(overall_rating) AS avg_rating,
			   SUM(CASE WHEN overall_rating <= %(th)s THEN 1 ELSE 0 END) AS unhappy
		FROM `tabRestaurant Survey Response`
		WHERE entry_date BETWEEN %(df)s AND %(dt)s + INTERVAL 1 DAY
		GROUP BY DATE(entry_date)
		ORDER BY day ASC
		""",
		{"df": date_from, "dt": date_to, "th": _club_club_settings()["survey_alert_threshold"]},
		as_dict=True,
	)
	out = [
		{
			"day": str(row.get("day") or ""),
			"count": cint(row.get("count")),
			"avg_rating": flt(row.get("avg_rating"), 2),
			"unhappy": cint(row.get("unhappy")),
		}
		for row in rows
	]
	total = sum(r["count"] for r in out)
	summary = {
		"responses": total,
		"avg_rating": flt(sum(r["avg_rating"] * r["count"] for r in out) / max(total, 1), 2),
		"unhappy": sum(r["unhappy"] for r in out),
	}
	return _compose_management_report(
		"survey-analytics",
		"Survey Analytics",
		summary,
		out,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


def club_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	"""BI payload for club-domain reports."""
	kpis, charts, insights = [], [], []
	tables = [{"key": "report-table", "title": title, "columns": _table_columns_from_rows(rows), "rows": rows}]

	if report_key == "customer-analytics":
		by_tier = {}
		by_segment = {}
		for row in rows:
			by_tier[row["tier"]] = by_tier.get(row["tier"], 0) + 1
			by_segment[row["segment"]] = by_segment.get(row["segment"], 0) + 1
		active_90 = sum(1 for row in rows if row.get("recency_days", 9999) <= 90)
		churn_risk = sum(1 for row in rows if row.get("recency_days", 9999) > 45)
		kpis = [
			_bi_kpi("customers", _("مشتریان فعال (رکورد خرید)"), len(rows), "count", 0),
			_bi_kpi("active_90d", _("فعال ۹۰ روز اخیر"), active_90, "count", 0),
			_bi_kpi("churn_risk", _("در خطر ریزش/خفته"), churn_risk, "count", 0),
			_bi_kpi("avg_clv", _("میانگین ارزش طول عمر (CLV)"), flt(summary.get("avg_clv")), "money", 0),
		]
		charts = [
			{
				"key": "segments",
				"title": _("خوشه‌های رفتاری مشتریان"),
				"type": "bar",
				"unit": "count",
				"labels": list(by_segment.keys()),
				"series": [{"key": "count", "label": _("مشتری"), "color": "#3e8ed0", "values": list(by_segment.values())}],
			},
			{
				"key": "tiers",
				"title": _("سطوح مشتریان"),
				"type": "bar",
				"unit": "count",
				"labels": list(by_tier.keys()),
				"series": [{"key": "count", "label": _("مشتری"), "color": "#2f6f5c", "values": list(by_tier.values())}],
			},
		]
		if rows:
			insights.append({"key": "top-customer", "severity": "info", "text": _("ارزشمندترین مشتری: «{0}» ({1}).").format(rows[0].get("customer_name"), rows[0].get("tier"))})

	elif report_key == "campaign-performance":
		kpis = [
			_bi_kpi("campaigns", _("کمپین‌ها"), cint(summary.get("campaigns")), "count", 0),
			_bi_kpi("active", _("کمپین فعال"), cint(summary.get("active")), "count", 0),
			_bi_kpi("participants", _("شرکت‌کنندگان (استفاده از کد)"), cint(summary.get("participants")), "count", 0),
			_bi_kpi("revenue", _("فروش کانال هدف"), flt(summary.get("revenue")), "money", 0),
		]
		if rows:
			labels = [row.get("title") for row in rows[:10]]
			charts = [
				{
					"key": "campaign-revenue",
					"title": _("فروش به تفکیک کمپین"),
					"type": "bar",
					"unit": "money",
					"labels": labels,
					"series": [{"key": "revenue", "label": _("فروش"), "color": "#2f6f5c", "values": [flt(r.get("revenue")) for r in rows[:10]]}],
				}
			]

	elif report_key == "wallet-summary":
		kpis = [
			_bi_kpi("wallets", _("کیف پول‌های فعال"), cint(summary.get("wallets")), "count", 0),
			_bi_kpi("granted", _("اعتبار اعطاشده"), flt(summary.get("granted")), "money", 0),
			_bi_kpi("used", _("اعتبار مصرف‌شده"), flt(summary.get("used")), "money", 0),
			_bi_kpi("balance", _("مانده فعلی"), flt(summary.get("balance")), "money", 0),
		]

	elif report_key == "credit-transactions":
		by_kind = {}
		for row in rows:
			by_kind[row["kind"]] = by_kind.get(row["kind"], 0.0) + flt(row["amount"])
		kpis = [
			_bi_kpi("rows", _("اقلام تراکنش"), cint(summary.get("rows")), "count", 0),
			_bi_kpi("total", _("جمع تراکنش‌ها"), flt(summary.get("total")), "money", 0),
		]
		if by_kind:
			charts = [
				{
					"key": "txn-kinds",
					"title": _("تراکنش بر اساس نوع"),
					"type": "bar",
					"unit": "money",
					"labels": list(by_kind.keys()),
					"series": [{"key": "amount", "label": _("مبلغ"), "color": "#3e8ed0", "values": list(by_kind.values())}],
				}
			]

	elif report_key == "care-feedback":
		kpis = [
			_bi_kpi("reviews", _("نظرات ثبت‌شده"), cint(summary.get("reviews")), "count", 0),
			_bi_kpi("avg_rating", _("میانگین امتیاز"), flt(summary.get("avg_rating")), "number", 0),
			_bi_kpi("items", _("اقلام دارای نظر"), cint(summary.get("items")), "count", 0),
		]
		if rows:
			labels = [row.get("item") for row in rows[:10]]
			charts = [
				{
					"key": "review-items",
					"title": _("نظرات بر اساس محصول"),
					"type": "bar",
					"unit": "count",
					"labels": labels,
					"series": [{"key": "count", "label": _("نظر"), "color": "#2f6f5c", "values": [cint(r.get("count")) for r in rows[:10]]}],
				}
			]
			worst = min(rows, key=lambda r: r.get("avg_rating") or 5) if rows else None
			if worst:
				insights.append({"key": "lowest-rated", "severity": "warn", "text": _("کمترین میانگین امتیاز: «{0}» ({1}).").format(worst.get("item"), worst.get("avg_rating"))})

	elif report_key == "survey-analytics":
		kpis = [
			_bi_kpi("responses", _("پاسخ‌ها"), cint(summary.get("responses")), "count", 0),
			_bi_kpi("avg_rating", _("میانگین رضایت"), flt(summary.get("avg_rating")), "number", 0),
			_bi_kpi("unhappy", _("ناراضی‌ها"), cint(summary.get("unhappy")), "count", 0),
		]
		if rows:
			charts = [
				{
					"key": "survey-trend",
					"title": _("روند رضایت روزانه"),
					"type": "line",
					"unit": "number",
					"labels": [row.get("day") for row in rows],
					"series": [{"key": "avg", "label": _("میانگین امتیاز"), "color": "#2f6f5c", "values": [flt(r.get("avg_rating")) for r in rows]}],
				}
			]

	return {"kpis": kpis, "charts": charts, "tables": tables, "insights": insights}


# ---------------------------------------------------------------------------
# Discount coupons (lightweight management over the existing Restaurant Coupon)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_management_coupons(search="", include_inactive=0):
	"""Coupon list for campaign editor / club page."""
	_ensure_management_access()
	if not frappe.db.exists("DocType", "Restaurant Coupon"):
		return {"coupons": [], "count": 0}
	filters = {}
	if not cint(include_inactive):
		filters["is_active"] = 1
	rows = frappe.get_all(
		"Restaurant Coupon",
		filters=filters,
		fields=[
			"name", "coupon_code", "title", "is_active", "discount_type", "discount_value",
			"min_order_amount", "max_discount_amount", "valid_from", "valid_to",
			"usage_limit", "used_count", "customer_mobile", "description",
		],
		order_by="modified desc",
		limit_page_length=300,
	)
	search = (search or "").strip().lower()
	items = []
	for row in rows:
		if search and search not in (row.get("coupon_code") or "").lower() and search not in (row.get("title") or "").lower():
			continue
		items.append(
			{
				**row,
				"valid_from": str(row.get("valid_from") or "")[:10],
				"valid_to": str(row.get("valid_to") or "")[:10],
				"discount_value": flt(row.get("discount_value")),
				"min_order_amount": flt(row.get("min_order_amount")),
				"max_discount_amount": flt(row.get("max_discount_amount")),
				"usage_limit": cint(row.get("usage_limit")),
				"used_count": cint(row.get("used_count")),
			}
		)
	return {"coupons": items, "count": len(items)}


@frappe.whitelist()
def save_management_coupon(payload=None):
	"""Create/update a discount coupon (name = coupon_code)."""
	_ensure_management_access()
	if not frappe.db.exists("DocType", "Restaurant Coupon"):
		frappe.throw(_("داکتایپ کوپن تخفیف در سیستم موجود نیست."))
	payload = _club_parse_json(payload, {})
	code = (payload.get("coupon_code") or payload.get("name") or "").strip()
	if not code:
		frappe.throw(_("کد تخفیف الزامی است."))
	if frappe.db.exists("Restaurant Coupon", code):
		doc = frappe.get_doc("Restaurant Coupon", code)
	else:
		doc = frappe.new_doc("Restaurant Coupon")
		doc.coupon_code = code
	doc.title = (payload.get("title") or doc.title or code).strip()
	discount_type = (payload.get("discount_type") or doc.discount_type or "Percent").strip()
	if discount_type not in ("Percent", "Fixed"):
		frappe.throw(_("نوع تخفیف نامعتبر است: {0}").format(discount_type))
	doc.discount_type = discount_type
	doc.discount_value = flt(payload.get("discount_value", doc.discount_value))
	if doc.discount_value <= 0:
		frappe.throw(_("مقدار تخفیف باید بزرگ‌تر از صفر باشد."))
	if discount_type == "Percent" and doc.discount_value > 100:
		frappe.throw(_("تخفیف درصدی نمی‌تواند بیشتر از ۱۰۰ باشد."))
	for key in ("min_order_amount", "max_discount_amount"):
		if payload.get(key) is not None:
			setattr(doc, key, flt(payload.get(key)))
	for key in ("valid_from", "valid_to"):
		if payload.get(key) is not None:
			setattr(doc, key, (payload.get(key) or "").strip() or None)
	if payload.get("usage_limit") is not None:
		doc.usage_limit = cint(payload.get("usage_limit"))
	if payload.get("customer_mobile") is not None and _has_column("Restaurant Coupon", "customer_mobile"):
		doc.customer_mobile = (payload.get("customer_mobile") or "").strip()
	if payload.get("description") is not None:
		doc.description = (payload.get("description") or "").strip()
	if payload.get("is_active") is not None:
		doc.is_active = cint(payload.get("is_active"))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "coupon": doc.name}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _club_register_into_api_module():
	"""Push this module's public API onto ``restaurant.api``.

	Same safeguard as the inventory/feature packs: keeps endpoints resolvable as
	``restaurant.api.<name>`` regardless of which module gets imported first
	(e.g. by a migrate patch).
	"""
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_club_register_into_api_module()
