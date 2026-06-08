import unittest
import sys
import types


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
    def __init__(self, elements=None, api_result=None):
        self.elements = elements or []
        self.api_result = api_result

    def find_elements(self, _by, _selector):
        return self.elements

    def execute_script(self, _script, *_args):
        return None

    def set_script_timeout(self, _timeout):
        return None

    def get_cookies(self):
        return []

    def execute_async_script(self, _script, _room_name, _csrf_token):
        return self.api_result


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

    def test_click_named_control_does_not_click_next(self):
        element = FakeElement(text="Next")
        clicked, _ = keepstreak._click_named_control(
            FakeDriver([element]),
            keepstreak.COMPLETE_LABELS,
            contains=True,
        )

        self.assertFalse(clicked)
        self.assertFalse(element.clicked)

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


if __name__ == "__main__":
    unittest.main()
