"""Pure lifecycle checks for customer recurring and one-off scheduled orders."""

import importlib.util
import sys
import types
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path


class RecurringOrderLifecycleTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe = types.ModuleType("frappe")
		frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
		frappe._ = lambda value: value
		utils = types.ModuleType("frappe.utils")
		utils.add_days = lambda value, days: (value if isinstance(value, date) else date.fromisoformat(str(value)[:10])) + timedelta(days=days)
		utils.cint = lambda value=0: int(float(value or 0))
		utils.flt = lambda value=0: float(value or 0)
		utils.getdate = lambda value=None: date(2026, 9, 26) if value is None else (value if isinstance(value, date) else date.fromisoformat(str(value)[:10]))
		utils.now_datetime = lambda: datetime(2026, 9, 26, 10, 0, 0)
		originals = {name: sys.modules.get(name) for name in ("frappe", "frappe.utils")}
		sys.modules["frappe"] = frappe
		sys.modules["frappe.utils"] = utils
		target = Path(__file__).resolve().parents[1] / "api_recurring.py"
		spec = importlib.util.spec_from_file_location("restaurant.api_recurring_test_target", target)
		cls.module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(cls.module)
		for name, value in originals.items():
			if value is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = value

	def test_one_time_daily_schedule_stops_after_its_only_date(self):
		schedule_date = date(2026, 9, 27)
		doc = types.SimpleNamespace(
			frequency="روزانه", weekdays="[]", delivery_time="13:00", end_date=schedule_date,
			status="منتظر تأیید مشتری", last_run_at=None, last_order="", pending_date=schedule_date,
			last_error="", next_run_at=f"{schedule_date} 13:00",
		)

		self.module._advance(doc, schedule_date, "SO-1")

		self.assertEqual(doc.status, "متوقف")
		self.assertIsNone(doc.next_run_at)
		self.assertEqual(doc.last_order, "SO-1")
		self.assertIsNone(doc.pending_date)

	def test_daily_schedule_continues_when_its_end_date_allows_another_run(self):
		schedule_date = date(2026, 9, 27)
		doc = types.SimpleNamespace(
			frequency="روزانه", weekdays="[]", delivery_time="13:00", end_date=date(2026, 9, 29),
			status="منتظر تأیید مشتری", last_run_at=None, last_order="", pending_date=schedule_date,
			last_error="", next_run_at=f"{schedule_date} 13:00",
		)

		self.module._advance(doc, schedule_date, "SO-2")

		self.assertEqual(doc.next_run_at, "2026-09-28 13:00")
		self.assertNotEqual(doc.status, "متوقف")


if __name__ == "__main__":
	unittest.main()
