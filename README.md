# TryHackMe Streak Bot

Automates a daily TryHackMe room activity from GitHub Actions.

## What It Does

Each workflow run:

1. Authenticates with TryHackMe using the saved `AUTH_COOKIES`.
2. Opens the [polkit](https://tryhackme.com/room/polkit), [rppsempire](https://tryhackme.com/room/rppsempire),
   and [bashscripting](https://tryhackme.com/room/bashscripting) rooms.
3. Resets progress and submits a completion once in each room.
4. Sends detailed real-time Discord updates as each room starts, resets, submits, and finishes.
5. Sends a final Discord success or failure report with a screenshot.
6. Uploads the log and screenshots as GitHub Actions artifacts.

You must join all three rooms before running the bot.

## Setup

1. Fork this repository.
2. In the fork, open **Settings > Secrets and variables > Actions**.
3. Add these repository secrets:

| Secret | Required | Description |
| --- | --- | --- |
| `AUTH_COOKIES` | Yes | JSON array of cookies from an authenticated TryHackMe browser session. |
| `DISCORD_WEBHOOK_URL` | Yes for Discord updates | Discord webhook URL used for live and final status messages. |
| `DISCORD_USER_ID` | Yes for pings | Your numeric Discord user ID. The webhook mentions this account in every update. |

The workflow runs every day at **4:00 AM Egypt time**. It uses two UTC cron
triggers plus an `Africa/Cairo` time guard so daylight-saving changes are handled.

You can also run it manually from **Actions > TryHackMe Streak Bot > Run workflow**.

## Monitoring

Discord receives pinged progress messages throughout the run. Messages include
the current room/action, elapsed time, repository, workflow run link, room list,
and recent logs. The final result includes each room's result and a screenshot.
The GitHub Actions run also uploads `tryhackmebot.log` and generated PNG
screenshots in the `thm-bot-logs` artifact.

## Local Run

Install dependencies and provide the same environment variables:

```powershell
python -m pip install -r requirements.txt
$env:AUTH_COOKIES = Get-Content cookies.json -Raw
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."
$env:DISCORD_USER_ID = "123456789012345678"
python main.py
```

## Troubleshooting

- Refresh `AUTH_COOKIES` if authentication fails or the cookies expire.
- Confirm the account has joined all three configured rooms.
- Check `tryhackmebot.log`, the final screenshot, and the GitHub Actions logs.
- TryHackMe may rate-limit or challenge GitHub Actions IP addresses.

## Disclaimer

Use responsibly and in accordance with TryHackMe's terms of service.
