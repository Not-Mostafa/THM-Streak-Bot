# Security Policy

## Reporting a vulnerability

Please report security issues privately to the repository owner instead of
opening a public issue. Include reproduction steps and the potential impact.

## Secret handling

- Store TryHackMe cookies and Discord webhook URLs only in GitHub Actions
  secrets or local environment variables.
- Never commit cookie exports, `.env` files, screenshots, or runtime logs.
- Rotate TryHackMe session cookies and Discord webhooks immediately if they are
  exposed.
- Review workflow changes carefully before running them with repository secrets.
