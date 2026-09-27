import json

import frappe


def execute():
	"""Preserve historic 1-5 feedback on a 1-10 display scale."""
	if frappe.db.exists("DocType", "Restaurant Customer Review"):
		if frappe.db.has_column("Restaurant Customer Review", "score_10"):
			frappe.db.sql(
				"""UPDATE `tabRestaurant Customer Review`
				SET score_10 = ROUND(rating * 2)
				WHERE COALESCE(score_10, 0) = 0 AND COALESCE(rating, 0) > 0"""
			)
		if frappe.db.has_column("Restaurant Customer Review", "moderation_status"):
			frappe.db.sql(
				"""UPDATE `tabRestaurant Customer Review`
				SET moderation_status = CASE WHEN is_approved = 1 THEN 'تأییدشده'
					WHEN COALESCE(moderation_status, '') = '' THEN 'در انتظار بررسی'
					ELSE moderation_status END"""
			)

	if frappe.db.exists("DocType", "Restaurant Survey Response") and frappe.db.has_column("Restaurant Survey Response", "overall_rating"):
		frappe.db.sql(
			"""UPDATE `tabRestaurant Survey Response`
			SET overall_rating = LEAST(10, GREATEST(1, overall_rating * 2))
			WHERE overall_rating BETWEEN 1 AND 5"""
		)
		if frappe.db.has_column("Restaurant Survey Response", "service_rating"):
			frappe.db.sql(
				"""UPDATE `tabRestaurant Survey Response`
				SET service_rating = LEAST(10, GREATEST(1, service_rating * 2))
				WHERE service_rating BETWEEN 1 AND 5"""
			)
		if frappe.db.has_column("Restaurant Survey Response", "answers_json"):
			for row in frappe.get_all("Restaurant Survey Response", fields=["name", "answers_json"], limit_page_length=0):
				try:
					answers = json.loads(row.get("answers_json") or "[]")
				except Exception:
					continue
				changed = False
				if isinstance(answers, list):
					for answer in answers:
						if not isinstance(answer, dict) or not str(answer.get("answer_type") or "").startswith("امتیاز"):
							continue
						try:
							value = int(answer.get("value") or 0)
						except (TypeError, ValueError):
							continue
						if 1 <= value <= 5:
							answer["value"] = value * 2
							answer["answer_type"] = "امتیاز ۱ تا ۱۰"
							changed = True
				if changed:
					frappe.db.set_value("Restaurant Survey Response", row.name, "answers_json", json.dumps(answers, ensure_ascii=False), update_modified=False)

	if frappe.db.exists("DocType", "Restaurant Survey Question"):
		if frappe.db.has_column("Restaurant Survey Question", "answer_type"):
			frappe.db.sql(
				"""UPDATE `tabRestaurant Survey Question`
				SET answer_type = 'امتیاز ۱ تا ۱۰'
				WHERE answer_type = 'امتیاز ۱ تا ۵'"""
			)
		if frappe.db.has_column("Restaurant Survey Question", "scope"):
			frappe.db.sql(
				"""UPDATE `tabRestaurant Survey Question`
				SET scope = 'سفارش'
				WHERE COALESCE(scope, '') = ''"""
			)

	threshold = frappe.db.get_single_value("Restaurant Web Settings", "restaurant_survey_alert_threshold") if frappe.db.exists("DocType", "Restaurant Web Settings") and frappe.db.has_column("Restaurant Web Settings", "restaurant_survey_alert_threshold") else None
	if threshold and 1 <= int(threshold) <= 5:
		frappe.db.set_single_value("Restaurant Web Settings", "restaurant_survey_alert_threshold", int(threshold) * 2)

	frappe.db.commit()
