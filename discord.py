import os
import sys
import json
import datetime
import requests
from seleniumbase import Driver


def send_discord_payload(success, context_summary, image_path=None,run_started_at='Null',execution_logs=[]):
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
            "title": "🛡️ TryHackMe Automation Sync Execution",
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
                    "name": "📋 Active Application Logs",
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
                files = {
                    "payload_json": (None, json.dumps(payload), "application/json"),
                    "file": (os.path.basename(image_path), img, "image/png")
                }
                payload["embeds"][0]["image"] = {"url": f"attachment://{os.path.basename(image_path)}"}
                response = requests.post(webhook_url, files=files, timeout=15)
        else:
            response = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        response.raise_for_status()
        print("[+] Discord monitoring transmission complete.")
    except Exception as discord_err:
        print(f"[!] Critical structural failure pushing metrics to Discord webhook: {discord_err}")

