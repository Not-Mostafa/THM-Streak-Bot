import json
import time

from selenium.webdriver.common.by import By


ROOMS = [
    ("polkit", "https://tryhackme.com/room/polkit"),
    ("rppsempire", "https://tryhackme.com/room/rppsempire"),
    ("bashscripting", "https://tryhackme.com/room/bashscripting"),
]

RESET_LABELS = ("reset room progress", "reset progress")
CONFIRM_LABELS = ("yes", "confirm", "reset")
COMPLETE_LABELS = ("complete", "complete task", "submit", "submit answer")


def keep_streak(driver, status_callback=None):
    """Reset and complete each configured room once."""
    results = []
    for index, (room_name, room_url) in enumerate(ROOMS, start=1):
        _notify(status_callback, f"Starting room {index}/{len(ROOMS)}: {room_name}.")
        result = _keep_streak_room(driver, room_name, room_url, status_callback)
        results.append(result)
        _notify(
            status_callback,
            f"Finished room {index}/{len(ROOMS)}: {room_name} with status {result['status']}.",
        )
    return results


def _notify(status_callback, message):
    if status_callback:
        status_callback(message)
    else:
        print(f"[+] {message}")


def _write_log(message):
    print(message)
    with open("tryhackmebot.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{message}\n")


def _wait_for_room(driver, room_name):
    for _ in range(30):
        if driver.execute_script("return document.readyState") == "complete":
            # The room is a client-rendered app; allow its controls to mount.
            time.sleep(3)
            return
        time.sleep(1)
    raise TimeoutError(f"{room_name}: room page did not finish loading.")


def _reset_via_api(driver, room_name):
    """Use TryHackMe's authenticated same-origin reset action."""
    csrf_token = ""
    for cookie in driver.get_cookies():
        if cookie.get("name", "").lower() in {"_csrf", "csrf", "csrf-token", "xsrf-token"}:
            csrf_token = cookie.get("value", "")
            break

    script = """
        const roomCode = arguments[0];
        const suppliedCsrf = arguments[1];
        const done = arguments[arguments.length - 1];
        const csrfCookie = document.cookie
            .split("; ")
            .find((entry) => entry.startsWith("_csrf="));
        const headers = {};
        const csrf = suppliedCsrf || (
            csrfCookie ? decodeURIComponent(csrfCookie.split("=").slice(1).join("=")) : ""
        );
        if (csrf) {
            headers["CSRF-Token"] = csrf;
        }
        const body = new FormData();
        body.append("code", roomCode);

        fetch("/api/reset-progress", {
            method: "POST",
            credentials: "same-origin",
            headers,
            body
        })
        .then(async (response) => ({
            ok: response.ok,
            status: response.status,
            body: (await response.text()).slice(0, 300)
        }))
        .then(done)
        .catch((error) => done({ok: false, status: 0, body: String(error)}));
    """
    try:
        driver.set_script_timeout(20)
        result = driver.execute_async_script(script, room_name, csrf_token)
    except Exception as error:
        return False, f"browser API call failed: {error}"

    if result and result.get("ok"):
        try:
            response_body = json.loads(result.get("body") or "{}")
            if isinstance(response_body, dict) and response_body.get("success") is False:
                return False, f"HTTP {result.get('status')}: {result.get('body', '')}"
        except json.JSONDecodeError:
            pass
        return True, f"HTTP {result.get('status')}"
    return False, f"HTTP {result.get('status')}: {result.get('body', '')}"


def _visible_controls(driver):
    return driver.find_elements(
        By.CSS_SELECTOR,
        "button, a, [role='button'], [role='menuitem']",
    )


def _control_text(element):
    parts = [
        element.text,
        element.get_attribute("aria-label"),
        element.get_attribute("title"),
    ]
    return " ".join(part.strip() for part in parts if part).strip().lower()


def _control_search_text(element):
    parts = [
        _control_text(element),
        element.get_attribute("data-testid"),
        element.get_attribute("class"),
    ]
    return " ".join(part.strip() for part in parts if part).strip().lower()


def _click_named_control(driver, labels, contains=False):
    """Click one visible control whose text or accessible label matches."""
    normalized_labels = tuple(label.lower() for label in labels)
    for element in _visible_controls(driver):
        try:
            if not element.is_displayed() or not element.is_enabled():
                continue
            text = _control_text(element)
            search_text = _control_search_text(element)
            matches = (
                any(label in search_text for label in normalized_labels)
                if contains
                else text in normalized_labels
            )
            if not matches:
                continue
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            try:
                element.click()
            except Exception:
                driver.execute_script("arguments[0].click();", element)
            return True, text or search_text
        except Exception:
            continue
    return False, ""


def _reset_via_ui(driver):
    clicked, _ = _click_named_control(driver, RESET_LABELS, contains=True)
    if not clicked:
        _click_named_control(driver, ("settings", "room settings", "more options"), contains=True)
        time.sleep(1)
        clicked, _ = _click_named_control(driver, RESET_LABELS, contains=True)
    if not clicked:
        return False

    time.sleep(1)
    confirmed, _ = _click_named_control(driver, CONFIRM_LABELS)
    return confirmed


def _submit_completion(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    submitted, label = _click_named_control(driver, COMPLETE_LABELS)
    if not submitted:
        submitted, label = _click_named_control(driver, COMPLETE_LABELS, contains=True)
    return submitted, label


def _read_streak(driver):
    selectors = [
        (By.ID, "user-streak"),
        (By.CSS_SELECTOR, "[data-streak]"),
        (By.CSS_SELECTOR, "[class*='streak' i]"),
    ]
    for by, selector in selectors:
        for element in driver.find_elements(by, selector):
            try:
                value = element.get_attribute("data-streak") or element.text
                if value and value.strip():
                    return value.strip()
            except Exception:
                continue
    return "not found"


def _save_failure_diagnostics(driver, room_name):
    screenshot = f"{room_name}_failure.png"
    state_file = f"{room_name}_page_state.json"
    try:
        driver.save_screenshot(screenshot)
        controls = [_control_text(element) for element in _visible_controls(driver)]
        state = {
            "url": driver.current_url,
            "title": driver.title,
            "visible_controls": [text for text in controls if text][:100],
        }
        with open(state_file, "w", encoding="utf-8") as output:
            json.dump(state, output, indent=2)
    except Exception as error:
        _write_log(f"[!] {room_name}: could not save failure diagnostics: {error}")


def _keep_streak_room(driver, room_name, room_url, status_callback):
    """Run one reset and completion pass in a room."""
    reset_done = False
    submit_done = False
    streak_value = "not found"

    try:
        driver.get(room_url)
        _wait_for_room(driver, room_name)
        _write_log(f"[+] Navigated to {room_name} room")

        reset_done, reset_detail = _reset_via_api(driver, room_name)
        if reset_done:
            _notify(status_callback, f"{room_name}: room progress reset via API.")
        else:
            _write_log(f"[!] {room_name}: API reset failed ({reset_detail}); trying room controls.")
            reset_done = _reset_via_ui(driver)
            if reset_done:
                _notify(status_callback, f"{room_name}: room progress reset using room controls.")
            else:
                _notify(status_callback, f"{room_name}: failed to reset room progress.")

        driver.refresh()
        _wait_for_room(driver, room_name)
        submit_done, submit_label = _submit_completion(driver)
        if submit_done:
            _notify(status_callback, f"{room_name}: completion submitted using '{submit_label}'.")
        else:
            _notify(status_callback, f"{room_name}: failed to find a completion control.")

        driver.refresh()
        _wait_for_room(driver, room_name)
        streak_value = _read_streak(driver)
        _write_log(f"[+] {room_name}: streak value is {streak_value}")

        status = "success" if reset_done and submit_done else "failed"
        if status == "failed":
            _save_failure_diagnostics(driver, room_name)

        return {
            "room": room_name,
            "url": room_url,
            "reset": reset_done,
            "submitted": submit_done,
            "streak": streak_value,
            "status": status,
        }
    except KeyboardInterrupt:
        raise
    except Exception as error:
        _write_log(f"[!] {room_name}: unexpected error: {error}")
        _save_failure_diagnostics(driver, room_name)
        return {
            "room": room_name,
            "url": room_url,
            "reset": reset_done,
            "submitted": submit_done,
            "streak": streak_value,
            "status": "failed",
        }
