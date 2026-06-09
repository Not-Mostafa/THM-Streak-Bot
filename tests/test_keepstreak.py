import unittest
import sys
import types
from unittest.mock import patch


selenium = types.ModuleType("selenium")
selenium_webdriver = types.ModuleType("selenium.webdriver")
selenium_common = types.ModuleType("selenium.webdriver.common")
selenium_by = types.ModuleType("selenium.webdriver.common.by")


class By:
    CSS_SELECTOR = "css selector"
    ID = "id"


selenium_by.By = By
sys.modules.setdefault("selenium", selenium)
sys.modules.setdefault("selenium.webdriver", selenium_webdriver)
sys.modules.setdefault("selenium.webdriver.common", selenium_common)
sys.modules.setdefault("selenium.webdriver.common.by", selenium_by)

import keepstreak  # noqa: E402


class FakeElement:
    def __init__(self, text="", attributes=None):
        self.text = text
        self.attributes = attributes or {}
        self.clicked = False

    def get_attribute(self, name):
        return self.attributes.get(name)

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True

    def click(self):
        self.clicked = True


class FakeDriver:
    def __init__(self, elements=None, api_result=None, script_result=None, progress_results=None):
        self.elements = elements or []
        self.api_result = api_result
        self.script_result = script_result
        self.progress_results = list(progress_results or [])
        self.current_url = "https://tryhackme.com/room/polkit"
        self.title = "TryHackMe | Test Room"
        self.refreshed = False

    def find_elements(self, _by, _selector):
        return self.elements

    def execute_script(self, _script, *_args):
        if "document.readyState" in _script:
            return "complete"
        if "Room progress" in _script and self.progress_results:
            return self.progress_results.pop(0)
        return self.script_result

    def set_script_timeout(self, _timeout):
        return None

    def get_cookies(self):
        return []

    def execute_async_script(self, _script, _room_name, _csrf_token):
        return self.api_result

    def get(self, url):
        self.current_url = url

    def refresh(self):
        self.refreshed = True

    def save_screenshot(self, _path):
        return True


class KeepStreakTests(unittest.TestCase):
    def test_click_named_control_uses_accessible_label(self):
        element = FakeElement(attributes={"aria-label": "Reset Room Progress"})
        clicked, label = keepstreak._click_named_control(
            FakeDriver([element]),
            keepstreak.RESET_LABELS,
            contains=True,
        )

        self.assertTrue(clicked)
        self.assertTrue(element.clicked)
        self.assertIn("reset room progress", label)

    def test_click_named_control_matches_exact_text_despite_css_classes(self):
        element = FakeElement(text="Confirm", attributes={"class": "btn btn-danger"})
        clicked, _ = keepstreak._click_named_control(
            FakeDriver([element]),
            keepstreak.CONFIRM_LABELS,
        )

        self.assertTrue(clicked)
        self.assertTrue(element.clicked)

    def test_api_reset_accepts_success_response(self):
        driver = FakeDriver(api_result={"ok": True, "status": 200, "body": '{"success":true}'})

        success, detail = keepstreak._reset_via_api(driver, "polkit")

        self.assertTrue(success)
        self.assertEqual(detail, "HTTP 200")

    def test_api_reset_rejects_false_success_body(self):
        driver = FakeDriver(api_result={"ok": True, "status": 200, "body": '{"success":false}'})

        success, _ = keepstreak._reset_via_api(driver, "polkit")

        self.assertFalse(success)

    def test_api_reset_handles_no_response(self):
        success, detail = keepstreak._reset_via_api(FakeDriver(), "polkit")

        self.assertFalse(success)
        self.assertEqual(detail, "reset API returned no response")

    def test_read_room_progress_returns_percentage(self):
        self.assertEqual(keepstreak._read_room_progress(FakeDriver(script_result=16)), 16)

    def test_read_room_progress_can_be_unavailable(self):
        self.assertIsNone(keepstreak._read_room_progress(FakeDriver()))

    def test_read_streak_uses_accessible_label(self):
        driver = FakeDriver([FakeElement(attributes={"aria-label": "82 day streak"})])

        self.assertEqual(keepstreak._read_streak(driver), "82")

    def test_complete_one_task_clicks_complete_control(self):
        element = FakeElement(text="Complete")

        submitted, label = keepstreak._complete_one_task_via_ui(FakeDriver([element]))

        self.assertTrue(submitted)
        self.assertTrue(element.clicked)
        self.assertEqual(label, "complete")

    @patch("keepstreak.time.sleep")
    def test_room_is_successful_when_completion_and_progress_are_verified(self, _sleep):
        driver = FakeDriver(
            elements=[FakeElement(text="Complete")],
            api_result={"ok": True, "status": 200, "body": '{"success":true}'},
            progress_results=[0, 16],
        )

        result = keepstreak._keep_streak_room(
            driver,
            "polkit",
            "https://tryhackme.com/room/polkit",
            None,
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["reset"])
        self.assertTrue(result["submitted"])
        self.assertEqual(result["reset_progress"], 0)
        self.assertEqual(result["progress"], 16)

    @patch("keepstreak.time.sleep")
    def test_room_fails_when_reset_succeeds_but_no_completion_is_found(self, _sleep):
        driver = FakeDriver(
            api_result={"ok": True, "status": 200, "body": '{"success":true}'},
            progress_results=[0, 0],
        )

        result = keepstreak._keep_streak_room(
            driver,
            "polkit",
            "https://tryhackme.com/room/polkit",
            None,
        )

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["reset"])
        self.assertFalse(result["submitted"])
        self.assertEqual(result["progress"], 0)

    @patch("keepstreak.time.sleep")
    def test_room_fails_when_clicked_completion_does_not_increase_progress(self, _sleep):
        driver = FakeDriver(
            elements=[FakeElement(text="Complete")],
            api_result={"ok": True, "status": 200, "body": '{"success":true}'},
            progress_results=[16, 16],
        )

        result = keepstreak._keep_streak_room(
            driver,
            "polkit",
            "https://tryhackme.com/room/polkit",
            None,
        )

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["submitted"])
        self.assertEqual(result["reset_progress"], result["progress"])

    @patch("keepstreak.time.sleep")
    def test_room_fails_when_progress_cannot_be_verified(self, _sleep):
        driver = FakeDriver(
            elements=[FakeElement(text="Complete")],
            api_result={"ok": True, "status": 200, "body": '{"success":true}'},
            progress_results=[None, None],
        )

        result = keepstreak._keep_streak_room(
            driver,
            "polkit",
            "https://tryhackme.com/room/polkit",
            None,
        )

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["submitted"])
        self.assertIsNone(result["progress"])


if __name__ == "__main__":
    unittest.main()
