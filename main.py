import os
import sys
import json
import datetime
import requests
from seleniumbase import Driver
from keepstreak import *
from discord import *

print("[+] UPDATED RUNNER - CHROMIUM UNDETECTED WITH DISCORD METRICS")
# Global tracking arrays for execution sync
execution_logs = []
run_started_at = datetime.datetime.now(datetime.timezone.utc)

def write_log(message):
    print(message)
    execution_logs.append(message)

def send_live_update(message):
    write_log(f"[+] {message}")
    # uncomment to send live updates
    #send_discord_payload(None, message)

def main():
    start_time = datetime.datetime.now().strftime("%d-%m-%Y, %H:%M:%S")
    write_log(f"[+] Initializing automation track at {start_time}")
    screenshot_name = "thm_dashboard_state.png"
    status_success = False
    status_details = ""
    driver = None
    try:
        write_log("[+] Spinning up customized Undetected SeleniumBase Webdriver context...")
        driver = Driver(browser="chrome", headless=True, uc=True)
    except Exception as driver_init_err:
        msg = f"Failed to instantiate custom stealth Chrome framework context: {driver_init_err}"
        write_log(f"[!] {msg}")
        send_discord_payload(False, msg)
        sys.exit(1)

    try:
        write_log("[+] Setting domain scope mapping to TryHackMe baseline...")
        driver.get("https://tryhackme.com")
        driver.sleep(4)
        cookie_payload = os.getenv("AUTH_COOKIES")
        if cookie_payload and len(cookie_payload.strip()) > 20:
            write_log("[+] Loading JSON cookie matrix arrays...")
            cookies_list = json.loads(cookie_payload)
            for cookie in cookies_list:
                if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite']
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass # Bypass tracking mismatch constraints safely
            write_log("[+] Core session tokens injected. Querying target metrics portal directly...")
            driver.refresh()
            driver.sleep(5)
            driver.get("https://tryhackme.com/dashboard")
            driver.sleep(4)
        else:
            write_log("[!] AUTH_COOKIES secret missing or parsing as blank value. Routing to login fallback.")
            if 'login_form' in globals():
                login_form(driver)

        current_url = driver.current_url
        write_log(f"[+] Verification Landing Target: {current_url}")
        if "dashboard" in current_url or driver.is_element_visible("a[href='/logout']"):
            write_log("[+] Authentication gate verification confirmed. User profile dashboard reached.")
            # Executing streak maintenance module logic
            write_log("[+] Initializing user streak tracking tasks...")
            send_live_update("Authentication confirmed. Starting one reset and submit pass in each configured room.")
            room_results = keep_streak(driver, status_callback=send_live_update)
            write_log("[+] Streak verification processing finalized safely.")
            status_success = all(result["status"] == "success" for result in room_results)
            result_lines = [
                (
                    f"- **{result['room']}**: `{result['status']}` | "
                    f"reset `{result['reset']}` | submitted `{result['submitted']}` | "
                    f"streak `{result['streak']}`"
                )
                for result in room_results
            ]
            status_details = "Room execution results:\n" + "\n".join(result_lines)
        else:
            write_log("[!] Failed routing navigation parameters past security framework gates.")
            status_details = "Vercel or Cloudflare rejected context signature verification, or credentials payload expired."
    except Exception as general_runtime_err:
        msg = f"Fatal execution track processing anomaly encountered: {general_runtime_err}"
        write_log(f"[!] {msg}")
        status_details = msg

    finally:
        if driver:
            try:
                write_log("[+] Capturing runtime verification state layout image...")
                driver.save_screenshot(screenshot_name)
            except Exception as ss_err:
                write_log(f"[!] Failed exporting environment screen snapshot frame: {ss_err}")
            driver.quit()

        # Fire telemetry payloads to Discord
        send_discord_payload(status_success, status_details, screenshot_name,run_started_at,execution_logs)
        with open("tryhackmebot.log", "a") as disk_log:
            disk_log.write("\n".join(execution_logs) + "\n\n")
        if not status_success:
            sys.exit(1)
if __name__ == "__main__":
    main()
