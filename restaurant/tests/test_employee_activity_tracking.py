import unittest

from restaurant.activity_tracking.constants import STATUS_ACTIVE, STATUS_IDLE
from restaurant.activity_tracking.service import _normalize_route_context, _normalize_status, _parse_role_list


class TestEmployeeActivityTrackingHelpers(unittest.TestCase):
    def test_parse_role_list_supports_lines_and_commas(self):
        parsed = _parse_role_list("Desk User\nSystem Manager,HR Manager")
        self.assertEqual(parsed, {"Desk User", "System Manager", "HR Manager"})

    def test_normalize_status_uses_inactive_seconds(self):
        settings = {"idle_after_minutes": 10}
        self.assertEqual(_normalize_status({"inactive_seconds": 700}, settings), STATUS_IDLE)
        self.assertEqual(_normalize_status({"inactive_seconds": 120}, settings), STATUS_ACTIVE)

    def test_normalize_status_prioritizes_hint(self):
        settings = {"idle_after_minutes": 10}
        payload = {"status_hint": "idle", "inactive_seconds": 10}
        self.assertEqual(_normalize_status(payload, settings), STATUS_IDLE)

    def test_route_context_respects_tracking_flags(self):
        payload = {"route": "app/point-of-sale", "is_pos": 1}
        context = _normalize_route_context(payload, {"track_pos_routes": 0, "track_desk_routes": 1})
        self.assertEqual(context["ignore"], True)

        payload = {"route": "app/sales-order", "is_pos": 0}
        context = _normalize_route_context(payload, {"track_pos_routes": 1, "track_desk_routes": 0})
        self.assertEqual(context["ignore"], True)


if __name__ == "__main__":
    unittest.main()
