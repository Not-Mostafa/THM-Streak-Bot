import os
import sys
import json
import datetime
import re
import requests
from seleniumbase import Driver
from keepstreak import keep_streak

print("[+] TryHackMe Streak Bot starting")

# Global tracking arrays for execution sync
execution_logs = []
run_started_at = datetime.datetime.now(datetime.timezone.utc)

def write_log(message):
    print(message)
    execution_logs.append(message)

def send_discord_payload(success, context_summary, image_path=None):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[!] DISCORD_WEBHOOK_URL missing in execution environment variables.")
        return

    if success is None:
        status_text = "IN PROGRESS"
        color = 3447003
    elif success:
        status_text = "SUCCESS"
        color = 3066993
    else:
        status_text = "FAILED"
        color = 15158332

    discord_user_id = os.getenv("DISCORD_USER_ID", "").strip()
    if discord_user_id and not re.fullmatch(r"\d{17,20}", discord_user_id):
        print("[!] DISCORD_USER_ID is not a valid numeric Discord snowflake; sending without a mention.")
        discord_user_id = ""
    repository = os.getenv("GITHUB_REPOSITORY", "local run")
    run_id = os.getenv("GITHUB_RUN_ID")
    run_url = f"https://github.com/{repository}/actions/runs/{run_id}" if run_id else "local run"
    elapsed = datetime.datetime.now(datetime.timezone.utc) - run_started_at
    elapsed_seconds = int(elapsed.total_seconds())

    # Keep layout footprint compact inside discord code snippet windows
    log_chunk = "\n".join(execution_logs[-20:])[-900:]
    
    payload = {
        "content": f"<@{discord_user_id}>" if discord_user_id else "",
        "allowed_mentions": {"users": [discord_user_id]} if discord_user_id else {"parse": []},
        "embeds": [{
            "title": "TryHackMe Streak Bot",
            "description": f"**Status:** {status_text}\n\n**Summary:**\n{context_summary}",
            "color": color,
            "fields": [
                {
                    "name": "Execution Details",
                    "value": (
                        f"**Repository:** `{repository}`\n"
                        f"**Run:** {run_url}\n"
                        f"**Elapsed:** `{elapsed_seconds}s`\n"
                        f"**Rooms:** `polkit`, `rppsempire`, `bashscripting`"
                    )
                },
                {
                    "name": "Recent logs",
                    "value": f"```text\n{log_chunk}\n```"
                }
            ],
            "footer": {"text": "Executed via GitHub Actions Sync Runner"},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }]
    }

    try:
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img:
                payload["embeds"][0]["image"] = {"url": f"attachment://{os.path.basename(image_path)}"}
                files = {
                    "payload_json": (None, json.dumps(payload), "application/json"),
                    "file": (os.path.basename(image_path), img, "image/png")
                }
                response = requests.post(webhook_url, files=files, timeout=15)
        else:
            response = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        response.raise_for_status()
        print("[+] Discord monitoring transmission complete.")
    except requests.HTTPError as discord_err:
        response_text = discord_err.response.text[:500] if discord_err.response is not None else ""
        print(f"[!] Discord webhook rejected the payload: {discord_err}; response: {response_text}")
    except Exception as discord_err:
        print(f"[!] Failed pushing metrics to Discord webhook: {discord_err}")


def send_live_update(message):
    write_log(f"[+] {message}")
    send_discord_payload(None, message)

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
            raise ValueError("AUTH_COOKIES is missing or empty. Add a valid cookie JSON array.")

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
        send_discord_payload(status_success, status_details, screenshot_name)
        
        with open("tryhackmebot.log", "a") as disk_log:
            disk_log.write("\n".join(execution_logs) + "\n\n")

        if not status_success:
            sys.exit(1)

if __name__ == "__main__":
    main()
