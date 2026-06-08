# Contributing

Thanks for helping improve TryHackMe Streak Bot.

## Development setup

1. Create and activate a Python virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Set `AUTH_COOKIES` to a valid TryHackMe cookie JSON array.
4. Run `python main.py`.

Keep secrets, cookie exports, screenshots, and logs out of commits. The
repository `.gitignore` excludes the common local files.

## Before opening a pull request

- Run `python -m unittest discover -s tests` and
  `python -m compileall main.py keepstreak.py`.
- Keep changes focused and document any user-facing behavior changes.
- Never include real TryHackMe cookies or Discord webhook URLs.
