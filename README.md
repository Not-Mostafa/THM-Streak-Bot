# TryHackMe Streak Bot
[![TryHackMe Streak Bot](https://github.com/Not-Mostafa/THM-Streak-Bot/actions/workflows/thmbot.yml/badge.svg)](https://github.com/Not-Mostafa/THM-Streak-Bot/actions/workflows/thmbot.yml)

A small SeleniumBase automation that resets and verifies progress in a
configured set of TryHackMe rooms. It can run locally or once per day through
GitHub Actions, with an optional final Discord report.

> [!WARNING]
> This project automates activity on a third-party service. Use it only on your
> own account, review TryHackMe's terms before running it, and understand that
> changes to the TryHackMe interface can break the automation without warning.

## How it works

On each run, the bot:

1. Starts a headless Chrome session with SeleniumBase.
2. Loads the cookies supplied in `AUTH_COOKIES` and verifies dashboard access.
3. Visits each room configured in `keepstreak.py`.
4. Resets the room, completes one incomplete task, and verifies that room progress increased.
5. Writes `tryhackmebot.log`, captures `thm_dashboard_state.png`, and optionally
   sends one final detailed result to Discord.

The default rooms are:

- [polkit](https://tryhackme.com/room/polkit)
- [rppsempire](https://tryhackme.com/room/rppsempire)
- [bashscripting](https://tryhackme.com/room/bashscripting)

Join every configured room before running the bot.

## Requirements

- Python 3.11 or later
- Google Chrome or Chromium
- A valid authenticated TryHackMe cookie export
- A GitHub repository fork for scheduled runs

Discord notifications are optional.

## GitHub Actions setup

1. Fork this repository.
2. Open **Settings > Secrets and variables > Actions** in your fork.
3. Add the secrets below.
4. Open **Actions > TryHackMe Streak Bot > Run workflow** for a test run.

| Secret | Required | Description |
| --- | --- | --- |
| `AUTH_COOKIES` | Yes | A JSON array of cookies from an authenticated TryHackMe browser session. |
| `DISCORD_WEBHOOK_URL` | No | Discord webhook used for one final detailed result message. |
| `DISCORD_USER_ID` | No | Numeric Discord user ID to mention in webhook messages. |

The workflow is scheduled for **04:00 Africa/Cairo** each day. GitHub cron uses
UTC, so the workflow has two cron triggers and a timezone guard to account for
Egyptian daylight-saving changes. Manual runs bypass the time guard.

The run fails when authentication fails or when any configured room cannot be
reset, completed, and verified with a room-progress increase.
Diagnostics are uploaded as the `thm-bot-logs` artifact even after a failed run
and are retained for seven days.

## Cookie format

`AUTH_COOKIES` must be a JSON array, not a cookie-header string. Each item
should contain at least `name`, `value`, `domain`, and `path`:

```json
[
  {
    "name": "cookie_name",
    "value": "cookie_value",
    "domain": ".tryhackme.com",
    "path": "/"
  }
]
```

Export cookies only from a browser session you control. Treat the resulting
JSON as a password: never commit it, paste it into an issue, or include it in
logs. Refresh the `AUTH_COOKIES` secret whenever the session expires.

## Local development

Create a virtual environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
seleniumbase install chromedriver
```

Set the environment variables and run the bot:

```powershell
$env:AUTH_COOKIES = Get-Content cookies.json -Raw
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."
$env:DISCORD_USER_ID = "123456789012345678"
python main.py
```

Only `AUTH_COOKIES` is required. An example variable file is provided in
`.env.example`; the application does not load `.env` files automatically.

## Configuration

Edit the `ROOMS` list in `keepstreak.py` to change the rooms:

```python
ROOMS = [
    ("room-name", "https://tryhackme.com/room/room-name"),
]
```

Each entry contains the display name used in logs and its full room URL.

## Project structure

| Path | Purpose |
| --- | --- |
| `main.py` | Starts the browser, restores authentication, coordinates the run, and reports results. |
| `keepstreak.py` | Contains the configured rooms, reset logic, and progress verification. |
| `.github/workflows/thmbot.yml` | Runs the bot daily and uploads diagnostics. |
| `requirements.txt` | Python runtime dependencies. |

## Troubleshooting

**Authentication fails**

Refresh `AUTH_COOKIES`, confirm it is valid JSON, and verify the cookies belong
to the `.tryhackme.com` domain.

**A room action fails**

Confirm the account has joined the room. Then inspect `tryhackmebot.log`, the
final screenshot, and the Actions logs. TryHackMe UI changes may require
updating selectors in `keepstreak.py`.

**The scheduled workflow appears twice**

Two UTC cron events are expected. The timezone guard allows only the event that
lands at 04:00 in Cairo to run the bot.

**The browser does not start locally**

Install Chrome or Chromium, run `seleniumbase install chromedriver`, and make
sure the active Python environment contains the dependencies.

## Security

Read [SECURITY.md](SECURITY.md) before storing credentials or reporting a
vulnerability. Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
