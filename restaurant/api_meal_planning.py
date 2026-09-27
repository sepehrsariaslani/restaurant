"""Customer nutrition estimates and saved meal plans over native restaurant Items."""

import json
import math

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

PROFILE_DOCTYPE = "Restaurant Customer Nutrition Profile"
PLAN_DOCTYPE = "Restaurant Customer Meal Plan"
WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
MEAL_SLOTS = ["صبحانه", "میان‌وعده", "ناهار", "شام"]
ACTIVITY_FACTORS = {"کم‌تحرک": 1.2, "فعالیت سبک": 1.375, "فعالیت متوسط": 1.55, "فعالیت زیاد": 1.725}
GOALS = {"کاهش وزن", "افزایش وزن", "حفظ وزن"}
FORMULA_SEX = {"زن", "مرد", "ترجیح می‌دهم انتخاب نکنم"}


def _json(value, fallback):
	if isinstance(value, (list, dict)):
		return value
	try:
		return json.loads(value) if value else fallback
	except (TypeError, ValueError):
		return fallback


def _identity(customer_token):
	from restaurant.customer_account import _require_customer

	return _require_customer(customer_token)


def _clean_tags(value, limit=80):
	if not isinstance(value, list):
		return []
	result = []
	for item in value[:limit]:
		text = str(item or "").strip()[:140]
		if text and text not in result:
			result.append(text)
	return result


def calculate_targets(profile):
	"""Return transparent estimates. Missing inputs are unknown, never treated as zero."""
	profile = profile or {}
	height = flt(profile.get("height_cm") or 0)
	weight = flt(profile.get("weight_kg") or 0)
	age = cint(profile.get("age_years") or 0)
	bmi = round(weight / ((height / 100) ** 2), 1) if age >= 18 and height > 0 and weight > 0 else None
	result = {"bmi": bmi, "bmi_label": "", "bmi_note": "BMI شاخص غربالگری است و تشخیص پزشکی نیست.", "maintenance_kcal": None, "calorie_target_kcal": None, "protein_reference_g": None, "estimate_available": False, "estimate_note": "برای برآورد، سن، قد، وزن، فعالیت و گزینهٔ محاسبه را کامل کنید."}
	if bmi is not None:
		if bmi < 18.5:
			result["bmi_label"] = "پایین‌تر از بازهٔ مرجع بزرگسالان"
		elif bmi < 25:
			result["bmi_label"] = "در بازهٔ مرجع بزرگسالان"
		elif bmi < 30:
			result["bmi_label"] = "بالاتر از بازهٔ مرجع بزرگسالان"
		else:
			result["bmi_label"] = "نیازمند بررسی تخصصی"
	if cint(profile.get("needs_specialist")):
		result["estimate_note"] = "برای این شرایط، هدف کالری را با متخصص تغذیه تعیین کنید."
		return result
	sex = str(profile.get("formula_sex") or "")
	activity = str(profile.get("activity_level") or "")
	goal = str(profile.get("goal") or "")
	if age and age < 18:
		result["estimate_note"] = "برآورد خودکار این صفحه برای افراد ۱۸ سال به بالا طراحی شده است."
		return result
	manual_protein = flt(profile.get("protein_target_g") or 0)
	result["protein_reference_g"] = round(manual_protein, 1) if manual_protein > 0 else (round(weight * 0.8, 1) if age >= 18 and weight > 0 else None)
	if goal == "کاهش وزن" and bmi is not None and bmi < 18.5:
		result["estimate_note"] = "با توجه به BMI پایین‌تر از بازهٔ مرجع، هدف کاهش وزن را با متخصص تعیین کنید."
		return result
	if age <= 0:
		manual_target = cint(profile.get("calorie_target") or 0)
		if manual_target > 0:
			result["calorie_target_kcal"] = manual_target
			result["estimate_note"] = "هدف کالری دستی ذخیره شده است؛ برای پیشنهاد خودکار، سن بزرگسال را هم ثبت کنید."
		return result
	if height <= 0 or weight <= 0 or age <= 0 or sex not in {"زن", "مرد"} or activity not in ACTIVITY_FACTORS or goal not in GOALS:
		if flt(profile.get("calorie_target") or 0) > 0:
			result["calorie_target_kcal"] = cint(profile.get("calorie_target"))
			result["estimate_note"] = "هدف کالری دستی شما استفاده می‌شود."
			result["estimate_available"] = True
		return result
	# Mifflin-St Jeor resting-energy estimate multiplied by a broad activity factor.
	resting = (10 * weight) + (6.25 * height) - (5 * age) + (5 if sex == "مرد" else -161)
	maintenance = round(resting * ACTIVITY_FACTORS[activity])
	goal_delta = {"کاهش وزن": -0.1, "افزایش وزن": 0.1, "حفظ وزن": 0}[goal]
	target = round(maintenance * (1 + goal_delta))
	manual_target = cint(profile.get("calorie_target") or 0)
	result.update({
		"maintenance_kcal": maintenance,
		"calorie_target_kcal": manual_target or target,
		"estimate_available": True,
		"estimate_note": "برآورد تقریبی است؛ تغییر وزن به عوامل دیگری هم وابسته است." if not manual_target else "هدف کالری دستی شما استفاده می‌شود.",
	})
	return result


def _profile_payload(doc):
	if not doc:
		return {"exists": False, "profile": None, "targets": calculate_targets({})}
	profile = {
		"age_years": cint(doc.age_years or 0),
		"formula_sex": doc.formula_sex or "",
		"height_cm": flt(doc.height_cm or 0),
		"weight_kg": flt(doc.weight_kg or 0),
		"goal_weight_kg": flt(doc.goal_weight_kg or 0),
		"activity_level": doc.activity_level or "",
		"goal": doc.goal or "",
		"calorie_target": cint(doc.calorie_target or 0),
		"protein_target_g": flt(doc.protein_target_g or 0),
		"needs_specialist": cint(doc.needs_specialist or 0),
		"specialist_reason": doc.specialist_reason or "",
		"allergens": _json(doc.allergens_json, []),
		"liked_items": _json(doc.liked_items_json, []),
		"disliked_items": _json(doc.disliked_items_json, []),
		"liked_ingredients": _json(doc.liked_ingredients_json, []),
		"disliked_ingredients": _json(doc.disliked_ingredients_json, []),
		"consent": cint(doc.consent or 0),
	}
	return {"exists": True, "profile": profile, "targets": calculate_targets(profile)}


def _meal_plan_payload(doc):
	return {
		"name": doc.name,
		"title": doc.title or "",
		"branch": doc.branch or "",
		"weekdays": _json(doc.weekdays_json, []),
		"active": cint(doc.active),
		"last_cart_prepared_date": str(doc.last_cart_prepared_date or ""),
		"items": [
			{
				"name": row.name,
				"meal_slot": row.meal_slot,
				"source_type": row.source_type,
				"item_code": row.item_code or "",
				"qty": flt(row.qty or 1),
				"customization": _json(row.customization_json, {}),
				"manual_name": row.manual_name or "",
				"manual_quantity": row.manual_quantity or "",
				"nutrition": {
					"kcal": flt(row.kcal) if row.kcal not in (None, "") and (row.source_type != "ثبت دستی" or cint(row.manual_kcal_known)) else None,
					"protein_g": flt(row.protein_g) if row.protein_g not in (None, "") and (row.source_type != "ثبت دستی" or cint(row.manual_protein_known)) else None,
					"carb_g": flt(row.carb_g) if row.source_type == "وی‌درخت" and row.carb_g not in (None, "") else None,
					"fat_g": flt(row.fat_g) if row.source_type == "وی‌درخت" and row.fat_g not in (None, "") else None,
				},
			}
			for row in doc.get("items", [])
		],
	}


def _get_profile(customer):
	name = frappe.db.get_value(PROFILE_DOCTYPE, {"customer": customer}, "name")
	return frappe.get_doc(PROFILE_DOCTYPE, name) if name else None


def _owned_plan(name, customer, active=None):
	filters = {"name": name, "customer": customer}
	if active is not None:
		filters["active"] = active
	if not frappe.db.exists(PLAN_DOCTYPE, filters):
		frappe.throw(_("این برنامه در حساب شما پیدا نشد."), frappe.PermissionError)
	return frappe.get_doc(PLAN_DOCTYPE, name)


def _validate_plan_run(doc, today, weekday):
	if not cint(doc.active):
		frappe.throw(_("برنامهٔ فعال پیدا نشد."))
	if weekday not in _json(doc.weekdays_json, []):
		frappe.throw(_("این برنامه برای امروز زمان‌بندی نشده است."))
	if str(doc.last_cart_prepared_date or "") == str(today):
		frappe.throw(_("اقلام این برنامه امروز پیش‌تر به سبد فرستاده شده‌اند."))


def _get_catalog(branch):
	from restaurant.api import get_menu_items

	first = get_menu_items(branch=branch, page=1, page_size=200) or {}
	items = list(first.get("items") or [])
	total_pages = min(max(cint((first.get("pagination") or {}).get("total_pages") or 1), 1), 50)
	for page in range(2, total_pages + 1):
		result = get_menu_items(branch=branch, page=page, page_size=200) or {}
		items.extend(result.get("items") or [])
	return _attach_direct_bom_ingredients(items)


def _attach_direct_bom_ingredients(items, boms=None, bom_items=None, ingredient_items=None):
	"""Expose first-level recipe ingredients without walking nested BOMs."""
	if not items:
		return items
	if boms is None or bom_items is None or ingredient_items is None:
		parent_codes = list(dict.fromkeys(str(item.get("name") or "").strip() for item in items if item.get("name")))
		if not parent_codes:
			return items
		try:
			boms = frappe.get_all(
				"BOM",
				filters={"item": ["in", parent_codes], "docstatus": 1, "is_active": 1},
				fields=["name", "item", "is_default", "is_active", "docstatus", "modified"],
				order_by="is_default desc, modified desc",
				limit_page_length=5000,
				ignore_permissions=True,
			)
			bom_names = list(dict.fromkeys(str(row.get("name") or "") for row in boms if row.get("name")))
			bom_items = frappe.get_all(
				"BOM Item",
				filters={"parent": ["in", bom_names]},
				fields=["parent", "item_code", "item_name", "idx"],
				order_by="parent asc, idx asc",
				limit_page_length=20000,
				ignore_permissions=True,
			) if bom_names else []
			ingredient_codes = list(dict.fromkeys(str(row.get("item_code") or "") for row in bom_items if row.get("item_code")))
			component_fields = ["name", "item_name"]
			if frappe.db.has_column("Item", "restaurant_nutrition_kcal"):
				component_fields.append("restaurant_nutrition_kcal")
			if frappe.db.has_column("Item", "restaurant_allergen_tags"):
				component_fields.append("restaurant_allergen_tags")
			ingredient_items = frappe.get_all(
				"Item",
				filters={"name": ["in", ingredient_codes]},
				fields=component_fields,
				limit_page_length=20000,
				ignore_permissions=True,
			) if ingredient_codes else []
		except Exception:
			# A menu still works if recipe metadata is unavailable on a site.
			return items

	selected_bom_by_product = {}
	for bom in sorted(
		boms or [],
		key=lambda row: (cint(row.get("is_default")), str(row.get("modified") or ""), str(row.get("name") or "")),
		reverse=True,
	):
		if cint(bom.get("docstatus")) != 1 or cint(bom.get("is_active")) != 1:
			continue
		product_code = str(bom.get("item") or "").strip()
		if product_code and product_code not in selected_bom_by_product:
			selected_bom_by_product[product_code] = str(bom.get("name") or "")

	component_rows_by_bom = {}
	for row in bom_items or []:
		component_rows_by_bom.setdefault(str(row.get("parent") or ""), []).append(row)
	component_by_code = {str(row.get("name") or ""): row for row in ingredient_items or [] if row.get("name")}

	for product in items:
		product_code = str(product.get("name") or "").strip()
		bom_name = selected_bom_by_product.get(product_code)
		if not bom_name:
			product.setdefault("nutrition_ingredient_tags", [])
			product.setdefault("ingredient_composition_available", False)
			continue
		all_direct_tags = _clean_tags(product.get("ingredient_tags") or [])
		nutrition_tags = []
		component_allergens = _clean_tags(product.get("allergen_ingredient_tags") or [])
		for component in component_rows_by_bom.get(bom_name, []):
			component_code = str(component.get("item_code") or "").strip()
			master = component_by_code.get(component_code, {})
			label = str(master.get("item_name") or component.get("item_name") or component_code).strip()
			if label and label not in all_direct_tags:
				all_direct_tags.append(label)
			component_allergens.extend(_split_stored_tags(master.get("restaurant_allergen_tags")))
			try:
				kcal = float(master.get("restaurant_nutrition_kcal"))
			except (TypeError, ValueError, OverflowError):
				kcal = 0
			if label and math.isfinite(kcal) and kcal > 0 and label not in nutrition_tags:
				nutrition_tags.append(label)
		product["ingredient_tags"] = all_direct_tags
		product["nutrition_ingredient_tags"] = nutrition_tags
		product["allergen_ingredient_tags"] = _clean_tags(component_allergens)
		product["allergens"] = _clean_tags((product.get("allergens") or []) + component_allergens)
		product["ingredient_composition_available"] = bool(component_rows_by_bom.get(bom_name))
	return items


def _split_stored_tags(value):
	if isinstance(value, list):
		return _clean_tags(value)
	return _clean_tags([part.strip() for part in str(value or "").replace("\n", ",").split(",")])


def _valid_customer_branch(branch):
	branch = str(branch or "").strip()
	if not branch:
		return False
	from restaurant.api import get_branches

	for row in (get_branches() or {}).get("branches") or []:
		branch_id = str(row.get("id") or row.get("name") or "").strip()
		if branch_id.casefold() == branch.casefold():
			return (
				str(row.get("company") or "").strip().casefold() == branch_id.casefold()
				and cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1) == 1
			)
	return False


def _recommendation_block_reason(item, allergens, disliked_items, disliked_ingredients):
	product_allergens = {str(tag).casefold() for tag in (item.get("allergens") or [])}
	product_ingredients = {str(tag).casefold() for tag in (item.get("ingredient_tags") or [])}
	if not _nutrition_is_complete(item):
		if _is_beverage(item):
			return "نوشیدنیِ بدون کالریِ قابل استفاده وارد ترکیب غذایی نمی‌شود."
		return "مقدار کالری و پروتئین قابل استفاده برای محاسبهٔ ترکیب ثبت نشده است."
	if allergens & (product_allergens | product_ingredients):
		return "با حساسیت ثبت‌شدهٔ مشتری تطابق دارد."
	# Unknown safety data cannot be treated as safe when the customer has declared
	# restrictions. A selected direct BOM gives us the known first-level recipe;
	# items without either source remain excluded. The UI still discloses review state.
	if allergens and not item.get("allergen_reviewed") and not item.get("ingredient_composition_available"):
		return "اطلاعات حساسیت‌زای محصول برای بررسی حساسیت شما بازبینی نشده است."
	if item.get("name") in disliked_items or disliked_ingredients & product_ingredients:
		return "با انتخاب‌های نامطلوب مشتری تطابق دارد."
	if disliked_ingredients and not item.get("ingredients_reviewed") and not item.get("ingredient_composition_available"):
		return "مواد تشکیل‌دهنده برای بررسی انتخاب‌های نامطلوب شما بازبینی نشده است."
	return ""


def _nutrition_is_complete(item):
	nutrition = item.get("nutrition") or {}
	kcal = nutrition.get("kcal")
	protein = nutrition.get("protein_g")
	if kcal in (None, "") or protein in (None, ""):
		return False
	try:
		kcal = float(kcal)
		protein = float(protein)
	except (TypeError, ValueError, OverflowError):
		return False
	return math.isfinite(kcal) and kcal > 0 and math.isfinite(protein) and protein >= 0


def _item_description(item):
	values = [
		item.get("title"), item.get("name"), item.get("category_title"), item.get("subcategory_title"),
		item.get("category"), item.get("subcategory"), item.get("item_group_path"),
	]
	values.extend(item.get("tags") or [])
	values.extend(item.get("meal_slots") or [])
	return " ".join(str(value or "") for value in values).casefold().replace("ي", "ی").replace("ك", "ک")


def _is_beverage(item):
	beverage_groups = {"بار", "بار سرد", "بار گرم", "سردنوش", "دم‌نوش", "دمنوش", "آبمیوه", "نوشیدنی"}
	category_values = {
		str(item.get(field) or "").strip().casefold().replace("ي", "ی").replace("ك", "ک")
		for field in ("category_title", "subcategory_title", "category", "subcategory")
	}
	if category_values & beverage_groups:
		return True
	text = _item_description(item)
	return any(token in text for token in (
		"بار سرد", "بار گرم", "سردنوش", "گرم نوش", "گرم‌نوش", "دم‌نوش", "دمنوش",
		"آبمیوه", "آب میوه", "اسموتی", "میلک شیک", "آیس تی", "ماچا", "نوشیدنی", "کافه",
		"آب معدنی", "آب واتا", "واتا", "نوشابه", "دلستر", "دوغ", "شربت", "موهیتو", "لیموناد", "قهوه", "چای",
		"اسپرسو", "آمریکانو", "لته", "موکاچینو", "water", "beverage", "drink", "espresso", "americano", "latte", "coffee", "tea",
	))


def _infer_meal_slots(item):
	if _is_beverage(item):
		# Calorie-bearing drinks such as smoothies and milk-based drinks can be
		# considered for a snack. Zero-calorie water/tea remains outside meals.
		return ["میان‌وعده"] if _nutrition_is_complete(item) else []
	explicit = [str(slot).strip() for slot in (item.get("meal_slots") or []) if str(slot).strip() in MEAL_SLOTS]
	if explicit:
		return explicit
	text = _item_description(item)
	if any(token in text for token in ("صبحانه", "املت", "نیمرو", "عدسی", "پنکیک", "اوتمیل", "تخم مرغ", "تخممرغ")):
		return ["صبحانه"]
	if any(token in text for token in ("میان وعده", "میان‌وعده", "اسنک", "دسر", "میوه", "کیک", "کوکی", "شیرینی", "آجیل")):
		return ["میان‌وعده"]
	if "ناهار" in text:
		return ["ناهار"]
	if "شام" in text:
		return ["شام"]
	# An unclassified, nutritionally reviewed main dish can fit lunch or dinner;
	# it must never be assigned to breakfast/snack solely because it lacks tags.
	return ["ناهار", "شام"]


def _suggestion_candidates_for_slot(items, slot):
	"""Use configured meal slots or conservative food-category inference."""
	return [item for item in items if slot in _infer_meal_slots(item)]


def _order_block_reason(item, allergens, disliked_items, disliked_ingredients):
	product_allergens = {str(tag).casefold() for tag in (item.get("allergens") or [])}
	product_ingredients = {str(tag).casefold() for tag in (item.get("ingredient_tags") or [])}
	if item.get("name") in disliked_items or disliked_ingredients & product_ingredients:
		return "این محصول با انتخاب‌های نامطلوب ثبت‌شدهٔ شما تطابق دارد."
	if allergens & (product_allergens | product_ingredients):
		return "با حساسیت ثبت‌شدهٔ شما تطابق دارد."
	if not item.get("allergen_reviewed") and not item.get("ingredient_composition_available"):
		return "اطلاعات حساسیت‌زای این محصول بازبینی نشده است."
	return ""


def _normalize_plan_item(row):
	if not isinstance(row, dict):
		frappe.throw(_("قلم برنامه معتبر نیست."))
	meal_slot = str(row.get("meal_slot") or "").strip()
	if meal_slot not in MEAL_SLOTS:
		frappe.throw(_("وعدهٔ انتخاب‌شده معتبر نیست."))
	source_type = str(row.get("source_type") or "وی‌درخت").strip()
	if source_type not in {"وی‌درخت", "ثبت دستی"}:
		frappe.throw(_("نوع قلم برنامه معتبر نیست."))
	qty = flt(row.get("qty") or 1)
	if qty <= 0 or qty > 40:
		frappe.throw(_("تعداد هر قلم باید بین ۱ تا ۴۰ باشد."))
	customization = row.get("customization") or {}
	if not isinstance(customization, dict):
		frappe.throw(_("سفارشی‌سازی محصول معتبر نیست."))
	result = {"meal_slot": meal_slot, "source_type": source_type, "qty": qty, "customization_json": json.dumps(customization, ensure_ascii=False)}
	if source_type == "وی‌درخت":
		item_code = str(row.get("item_code") or "").strip()
		if not item_code or not frappe.db.exists("Item", item_code):
			frappe.throw(_("محصول انتخاب‌شده در منو پیدا نشد."))
		result.update({"item_code": item_code, "manual_name": "", "manual_quantity": "", "kcal": None, "protein_g": None, "carb_g": None, "fat_g": None})
	else:
		name = str(row.get("manual_name") or "").strip()[:120]
		if not name:
			frappe.throw(_("نام خوراک ثبت‌شدهٔ دستی را وارد کنید."))
		nutrition = row.get("nutrition") if isinstance(row.get("nutrition"), dict) else {}
		values = {}
		for key, field in (("kcal", "kcal"), ("protein_g", "protein_g"), ("carb_g", "carb_g"), ("fat_g", "fat_g")):
			raw = nutrition.get(key)
			if raw in (None, ""):
				values[field] = None
				continue
			value = flt(raw)
			if value < 0 or value > 10000:
				frappe.throw(_("مقادیر تغذیه‌ای باید بین صفر تا ۱۰۰۰۰ باشند."))
			values[field] = value
		result.update({
			"item_code": None,
			"manual_name": name,
			"manual_quantity": str(row.get("manual_quantity") or "").strip()[:80],
			"manual_kcal_known": int(values["kcal"] is not None),
			"manual_protein_known": int(values["protein_g"] is not None),
			"manual_nutrition_complete": int(values["kcal"] is not None and values["protein_g"] is not None),
			**values,
		})
	return result


def _check_weekdays(customer, weekdays, exclude=""):
	if len(set(weekdays)) != len(weekdays):
		frappe.throw(_("روز هفته در برنامه تکراری انتخاب شده است."))
	rows = frappe.get_all(PLAN_DOCTYPE, filters={"customer": customer, "active": 1}, fields=["name", "weekdays_json"], limit_page_length=300, ignore_permissions=True)
	for row in rows:
		if row.name == exclude:
			continue
		conflict = set(_json(row.weekdays_json, [])) & set(weekdays)
		if conflict:
			frappe.throw(_("برای این روزها برنامهٔ فعال دیگری دارید: {0}").format("، ".join(sorted(conflict, key=WEEKDAYS.index))))


@frappe.whitelist(allow_guest=True)
def get_my_nutrition_workspace(customer_token=None, branch=""):
	identity = _identity(customer_token)
	customer = identity["customer"]
	profile = _profile_payload(_get_profile(customer))
	plans = frappe.get_all(PLAN_DOCTYPE, filters={"customer": customer}, fields=["name"], order_by="modified desc", limit_page_length=100, ignore_permissions=True)
	plan_payloads = [_meal_plan_payload(frappe.get_doc(PLAN_DOCTYPE, row.name)) for row in plans]
	branch = str(branch or "").strip()
	if branch and not _valid_customer_branch(branch):
		frappe.throw(_("شعبهٔ انتخاب‌شده برای سفارش مشتری معتبر نیست."))
	catalog = _get_catalog(branch) if branch else []
	today = getdate()
	today_weekday = WEEKDAYS[(today.weekday() + 2) % 7]
	return {"profile": profile, "plans": plan_payloads, "catalog": catalog, "branch": branch, "weekdays": WEEKDAYS, "meal_slots": MEAL_SLOTS, "today": str(today), "today_weekday": today_weekday}


@frappe.whitelist(allow_guest=True)
def save_my_nutrition_profile(customer_token=None, payload=None):
	identity = _identity(customer_token)
	customer = identity["customer"]
	data = _json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("اطلاعات پروفایل معتبر نیست."))
	if not cint(data.get("consent")):
		frappe.throw(_("برای ذخیرهٔ اطلاعات تغذیه‌ای، رضایت خود را ثبت کنید."))
	values = {}
	for field, label, low, high in (("age_years", "سن", 0, 120), ("height_cm", "قد", 0, 250), ("weight_kg", "وزن", 0, 350), ("goal_weight_kg", "وزن هدف", 0, 350), ("calorie_target", "هدف کالری", 0, 10000), ("protein_target_g", "هدف پروتئین", 0, 1000)):
		raw = data.get(field)
		if raw in (None, ""):
			values[field] = None if field in {"age_years", "height_cm", "weight_kg", "goal_weight_kg"} else 0
			continue
		value = flt(raw)
		if value < low or value > high:
			frappe.throw(_("مقدار «{0}» خارج از بازهٔ مجاز است.").format(label))
		if field == "age_years":
			value = cint(value)
		values[field] = value
	if values.get("age_years") and values["age_years"] < 18:
		data["needs_specialist"] = 1
	sex = str(data.get("formula_sex") or "").strip()
	goal = str(data.get("goal") or "").strip()
	activity = str(data.get("activity_level") or "").strip()
	if sex and sex not in FORMULA_SEX:
		frappe.throw(_("گزینهٔ محاسبهٔ انرژی معتبر نیست."))
	if goal and goal not in GOALS:
		frappe.throw(_("هدف انتخاب‌شده معتبر نیست."))
	if activity and activity not in ACTIVITY_FACTORS:
		frappe.throw(_("سطح فعالیت معتبر نیست."))
	values.update({
		"customer": customer,
		"formula_sex": sex,
		"goal": goal,
		"activity_level": activity,
		"needs_specialist": cint(data.get("needs_specialist")),
		"specialist_reason": str(data.get("specialist_reason") or "").strip()[:500],
		"allergens_json": json.dumps(_clean_tags(data.get("allergens"), 30), ensure_ascii=False),
		"liked_items_json": json.dumps(_clean_tags(data.get("liked_items")), ensure_ascii=False),
		"disliked_items_json": json.dumps(_clean_tags(data.get("disliked_items")), ensure_ascii=False),
		"liked_ingredients_json": json.dumps(_clean_tags(data.get("liked_ingredients")), ensure_ascii=False),
		"disliked_ingredients_json": json.dumps(_clean_tags(data.get("disliked_ingredients")), ensure_ascii=False),
		"consent": 1,
	})
	doc = _get_profile(customer)
	if doc:
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": PROFILE_DOCTYPE, **values})
		doc.insert(ignore_permissions=True)
	return _profile_payload(doc)


@frappe.whitelist(allow_guest=True)
def delete_my_nutrition_profile(customer_token=None):
	identity = _identity(customer_token)
	customer = identity["customer"]
	for row in frappe.get_all(PLAN_DOCTYPE, filters={"customer": customer}, fields=["name"], limit_page_length=500, ignore_permissions=True):
		frappe.delete_doc(PLAN_DOCTYPE, row.name, ignore_permissions=True, force=True)
	doc = _get_profile(customer)
	if doc:
		frappe.delete_doc(PROFILE_DOCTYPE, doc.name, ignore_permissions=True, force=True)
	return {"success": True}


@frappe.whitelist(allow_guest=True)
def suggest_my_meal_plans(customer_token=None, branch=""):
	identity = _identity(customer_token)
	profile_doc = _get_profile(identity["customer"])
	profile_payload = _profile_payload(profile_doc)
	if not profile_doc or not profile_doc.consent:
		return {"suggestions": [], "reason": "ابتدا پروفایل و رضایت خود را ثبت کنید."}
	if profile_payload["targets"].get("estimate_available") is False or profile_doc.needs_specialist:
		return {"suggestions": [], "reason": profile_payload["targets"].get("estimate_note") or "هدف تغذیه‌ای آماده نیست."}
	branch = str(branch or "").strip()
	if not branch:
		return {"suggestions": [], "reason": "برای پیشنهاد دقیق، ابتدا شعبه را انتخاب کنید."}
	if not _valid_customer_branch(branch):
		frappe.throw(_("شعبهٔ انتخاب‌شده برای پیشنهاد معتبر نیست."))
	catalog = _get_catalog(branch)
	allergens = {str(tag).casefold() for tag in _json(profile_doc.allergens_json, [])}
	disliked_items = set(_json(profile_doc.disliked_items_json, []))
	disliked_ingredients = {str(tag).casefold() for tag in _json(profile_doc.disliked_ingredients_json, [])}
	liked_items = set(_json(profile_doc.liked_items_json, []))
	liked_ingredients = {str(tag).casefold() for tag in _json(profile_doc.liked_ingredients_json, [])}
	eligible = []
	blocked_for_safety = 0
	for item in catalog:
		if _recommendation_block_reason(item, allergens, disliked_items, disliked_ingredients):
			if allergens and not item.get("allergen_reviewed"):
				blocked_for_safety += 1
			continue
		eligible.append(item)
	if not eligible:
		if blocked_for_safety:
			return {"suggestions": [], "reason": "برای رعایت حساسیت ثبت‌شدهٔ شما، محصولات این شعبه باید ابتدا از نظر آلرژن بازبینی شوند."}
		if catalog:
			return {
				"suggestions": [],
				"reason": "در منوی این شعبه محصولی با کالریِ بیشتر از صفر و مقدار پروتئین ثبت‌شده پیدا نشد؛ نوشیدنیِ بدون کالری وارد وعده نمی‌شود.",
			}
		return {"suggestions": [], "reason": "منوی فعالی برای این شعبه پیدا نشد."}
	targets = profile_payload["targets"]
	target_kcal = float(targets.get("calorie_target_kcal") or 0)
	if not target_kcal:
		return {"suggestions": [], "reason": "هدف کالری در پروفایل ثبت نشده است."}
	slot_shares = [("صبحانه", 0.25), ("ناهار", 0.35), ("شام", 0.3), ("میان‌وعده", 0.1)]
	suggestions = []
	for variant in range(3):
		chosen = []
		chosen_codes = set()
		chosen_ingredients = set()
		for slot, share in slot_shares:
			candidates = _suggestion_candidates_for_slot(eligible, slot)
			unused_candidates = [item for item in candidates if item.get("name") not in chosen_codes]
			if unused_candidates:
				candidates = unused_candidates
			if not candidates:
				continue
			protein_target = float(targets.get("protein_reference_g") or 0) * share
			def score(item):
				nutrition = item.get("nutrition") or {}
				nutrition_score = (
					abs(float(nutrition["kcal"]) - target_kcal * share)
					+ 2 * abs(float(nutrition["protein_g"]) - protein_target)
					if _nutrition_is_complete(item)
					else 250
				)
				ingredients = {str(tag).casefold() for tag in item.get("ingredient_tags", [])}
				return (
					nutrition_score
					+ (500 if item.get("name") in chosen_codes else 0)
					+ 15 * len(ingredients & chosen_ingredients)
					- (120 if item.get("name") in liked_items else 0)
					- (30 if liked_ingredients & ingredients else 0),
					str(item.get("name") or ""),
				)
			candidates.sort(key=score)
			item = candidates[min(variant, len(candidates) - 1)]
			chosen_codes.add(item.get("name"))
			chosen_ingredients.update(str(tag).casefold() for tag in item.get("ingredient_tags", []))
			chosen.append({
				"meal_slot": slot,
				"source_type": "وی‌درخت",
				"item_code": item.get("name"),
				"qty": 1,
				"customization": {},
				"nutrition_known": _nutrition_is_complete(item),
				"nutrition_verified": bool(item.get("nutrition_verified")),
				"allergen_reviewed": bool(item.get("allergen_reviewed")),
				"ingredients_reviewed": bool(item.get("ingredients_reviewed")),
			})
		if not chosen:
			continue
		covered_slots = list(dict.fromkeys(row["meal_slot"] for row in chosen))
		full_day = len(covered_slots) == len(slot_shares)
		suggestion_title = ["ترکیب متناسب با کالری", "ترکیب دوم", "ترکیب سوم"][variant]
		if not full_day:
			suggestion_title = f"{suggestion_title} · {len(covered_slots)} وعده"
			suggestions.append({
			"title": suggestion_title,
			"branch": branch,
			"nutrition_complete": all(row["nutrition_known"] for row in chosen),
			"nutrition_reviewed": all(row["nutrition_verified"] for row in chosen),
			"covered_slots": covered_slots,
			"full_day": full_day,
			"items": chosen,
		})
	has_unknown_nutrition = any(not suggestion["nutrition_complete"] for suggestion in suggestions)
	has_unreviewed_nutrition = any(not suggestion["nutrition_reviewed"] for suggestion in suggestions)
	has_unknown_safety = any(
		any(not row["allergen_reviewed"] or not row["ingredients_reviewed"] for row in suggestion["items"])
		for suggestion in suggestions
	)
	missing_slots = [slot for slot, _share in slot_shares if not any(slot in suggestion["covered_slots"] for suggestion in suggestions)]
	messages = []
	if has_unknown_nutrition:
		messages.append("کالری بعضی اقلام نامشخص است؛ جمع فقط از اطلاعات موجود محاسبه می‌شود.")
	if has_unreviewed_nutrition:
		messages.append("ترکیب بر پایهٔ کالری و پروتئین ثبت‌شدهٔ محصولات ساخته شده؛ بعضی مقادیر هنوز توسط مدیریت بازبینی نشده‌اند.")
	if has_unknown_safety:
		messages.append("اطلاعات آلرژن یا مواد اولیهٔ بعضی اقلام کامل نیست و پیش از سفارش دوباره بررسی می‌شود.")
	if missing_slots:
		messages.append(f"برای این شعبه غذای مناسبِ «{'، '.join(missing_slots)}» پیدا نشد، پس ترکیب همهٔ وعده‌های روز را پوشش نمی‌دهد.")
	if not messages:
		messages.append("هر چهار وعده با مقادیر تغذیه‌ای ثبت‌شده و متناسب با هدف روزانه چیده شده‌اند.")
	reason = " ".join(messages)
	return {"suggestions": suggestions, "reason": reason}


@frappe.whitelist(allow_guest=True)
def save_my_meal_plan(customer_token=None, payload=None):
	identity = _identity(customer_token)
	customer = identity["customer"]
	data = _json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("اطلاعات برنامه معتبر نیست."))
	profile = _get_profile(customer)
	if not profile or not profile.consent:
		frappe.throw(_("ابتدا پروفایل تغذیه‌ای و رضایت ذخیره‌سازی را ثبت کنید."))
	name = str(data.get("name") or "").strip()
	existing_doc = _owned_plan(name, customer) if name else None
	branch = str(data.get("branch") or "").strip()
	title = str(data.get("title") or "").strip()[:120]
	items = data.get("items") if isinstance(data.get("items"), list) else []
	requested_weekdays = data.get("weekdays") or []
	if not isinstance(requested_weekdays, list) or any(not isinstance(day, str) for day in requested_weekdays):
		frappe.throw(_("روزهای هفته معتبر نیستند."))
	weekdays = [day for day in WEEKDAYS if day in set(requested_weekdays)]
	if not title or not branch:
		frappe.throw(_("نام برنامه و شعبه را وارد کنید."))
	if not _valid_customer_branch(branch):
		frappe.throw(_("شعبهٔ انتخاب‌شده برای برنامه معتبر نیست."))
	if not items or len(items) > 80:
		frappe.throw(_("برنامه باید دست‌کم یک قلم و حداکثر ۸۰ قلم داشته باشد."))
	if len(weekdays) != len(set(requested_weekdays)):
		frappe.throw(_("یکی از روزهای هفته معتبر نیست."))
	frappe.db.sql("select name from `tabCustomer` where name=%s for update", customer)
	_check_weekdays(customer, weekdays, exclude=name)
	catalog_by_code = {row.get("name"): row for row in _get_catalog(branch)}
	normalized = [_normalize_plan_item(row) for row in items]
	profile = _get_profile(customer)
	profile_allergens = {str(tag).casefold() for tag in _json(profile.allergens_json, [])} if profile else set()
	for row in normalized:
		if row.get("source_type") != "وی‌درخت":
			continue
		product = catalog_by_code.get(row.get("item_code"))
		if not product:
			frappe.throw(_("یک محصول در شعبهٔ انتخابی موجود نیست؛ شعبه یا اقلام را بازبینی کنید."))
		if profile_allergens & (
			{str(tag).casefold() for tag in (product.get("allergens") or [])}
			| {str(tag).casefold() for tag in (product.get("ingredient_tags") or [])}
		):
			frappe.throw(_("این برنامه شامل محصولی با حساسیت ثبت‌شدهٔ شماست."))
		nutrition = product.get("nutrition") or {}
		row["kcal"] = nutrition.get("kcal")
		row["protein_g"] = nutrition.get("protein_g")
		row["carb_g"] = nutrition.get("carb_g")
		row["fat_g"] = nutrition.get("fat_g")
	if name:
		doc = existing_doc
	else:
		doc = frappe.get_doc({"doctype": PLAN_DOCTYPE, "customer": customer})
	doc.title = title
	doc.branch = branch
	doc.weekdays_json = json.dumps(weekdays, ensure_ascii=False)
	doc.active = cint(data.get("active", 1))
	doc.set("items", [])
	for row in normalized:
		doc.append("items", row)
	if name:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)
	return {"plan": _meal_plan_payload(doc)}


@frappe.whitelist(allow_guest=True)
def delete_my_meal_plan(customer_token=None, name=""):
	identity = _identity(customer_token)
	doc = _owned_plan(name, identity["customer"])
	frappe.delete_doc(PLAN_DOCTYPE, doc.name, ignore_permissions=True, force=True)
	return {"success": True}


@frappe.whitelist(allow_guest=True)
def prepare_my_meal_plan_order(customer_token=None, name="", branch="", for_schedule=0, order_now=0):
	identity = _identity(customer_token)
	_owned_plan(name, identity["customer"], active=1)
	frappe.db.sql("select name from `tabRestaurant Customer Meal Plan` where name=%s and customer=%s for update", (name, identity["customer"]))
	doc = frappe.get_doc(PLAN_DOCTYPE, name)
	profile = _get_profile(identity["customer"])
	if not profile or not profile.consent:
		frappe.throw(_("پروفایل تغذیه‌ای یا رضایت ذخیره‌سازی شما موجود نیست."))
	today = getdate()
	for_schedule = cint(for_schedule)
	order_now = cint(order_now)
	if not for_schedule:
		if order_now:
			if not cint(doc.active):
				frappe.throw(_("برنامهٔ فعال پیدا نشد."))
			if str(doc.last_cart_prepared_date or "") == str(today):
				frappe.throw(_("این برنامه امروز پیش‌تر به سبد فرستاده شده است."))
		else:
			today_weekday = WEEKDAYS[(today.weekday() + 2) % 7]
			_validate_plan_run(doc, today, today_weekday)
	branch = str(branch or doc.branch or "").strip()
	if not _valid_customer_branch(branch):
		frappe.throw(_("شعبهٔ انتخاب‌شده معتبر یا فعال نیست."))
	catalog = {row.get("name"): row for row in _get_catalog(branch)}
	allergens = {str(tag).casefold() for tag in _json(profile.allergens_json, [])}
	disliked_items = set(_json(profile.disliked_items_json, []))
	disliked_ingredients = {str(tag).casefold() for tag in _json(profile.disliked_ingredients_json, [])}
	order_items = []
	warnings = []
	for row in doc.get("items", []):
		if row.source_type != "وی‌درخت":
			if row.source_type == "ثبت دستی":
				warnings.append({"item_code": "", "item_title": row.manual_name or "خوراک ثبت‌شده", "reason": "این قلم بیرون از منو ثبت شده و برای سفارش باید از محصولات شعبه انتخاب شود."})
			continue
		product = catalog.get(row.item_code)
		if not product or product.get("out_of_stock"):
			warnings.append({"item_code": row.item_code, "reason": "محصول در این شعبه ناموجود است."})
			continue
		if not product.get("slug"):
			warnings.append({"item_code": row.item_code, "reason": "شناسهٔ سفارش این محصول در منوی فعلی پیدا نشد."})
			continue
		block_reason = _order_block_reason(product, allergens, disliked_items, disliked_ingredients)
		if block_reason:
			warnings.append({"item_code": row.item_code, "reason": block_reason})
			continue
		if product.get("base_price") is None or flt(product.get("base_price") or 0) <= 0:
			warnings.append({"item_code": row.item_code, "reason": "قیمت فعلی محصول در دسترس نیست."})
			continue
		order_items.append({
			"item_slug": product.get("slug") or "",
			"item_title": product.get("title") or product.get("name"),
			"qty": flt(row.qty or 1),
			"customization": _json(row.customization_json, {}),
		"base_price": flt(product.get("base_price")),
		})
	can_order = bool(order_items) and not warnings
	if can_order and not for_schedule:
		doc.last_cart_prepared_date = str(today)
		doc.save(ignore_permissions=True)
	return {"branch": branch, "original_branch": doc.branch, "plan_title": doc.title, "run_date": str(today), "items": order_items, "warnings": warnings, "can_order": can_order, "prepared_for_schedule": bool(for_schedule), "ordered_outside_plan_weekday": bool(order_now)}


def invalidate_item_nutrition_reviews(doc, method=None):
	"""Recipe and disclosure edits invalidate the corresponding review flags."""
	previous = doc.get_doc_before_save()
	if not previous:
		return
	changed = lambda field: previous.get(field) != doc.get(field)
	if any(changed(field) for field in ("restaurant_nutrition_kcal", "restaurant_nutrition_protein_g", "restaurant_nutrition_carb_g", "restaurant_nutrition_fat_g")):
		doc.restaurant_nutrition_verified = 0
	if changed("restaurant_allergen_tags"):
		doc.restaurant_allergen_reviewed = 0
	if changed("restaurant_ingredient_tags"):
		doc.restaurant_ingredients_reviewed = 0
		doc.restaurant_allergen_reviewed = 0
