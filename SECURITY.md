# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | Yes                |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
responsibly:

1. **Do not** open a public issue.
2. Email the maintainers or open a private security advisory on GitHub.
3. Include a description of the vulnerability, steps to reproduce, and any
   potential impact.

We will acknowledge your report within 48 hours and provide a fix timeline.

## API Keys & Credentials

This project may use API keys for Best Buy, Walmart, Amazon, and Google Sheets.

* **Never** commit API keys, tokens, or credentials to the repository.
* Store all secrets in environment variables or a `.env` file (which is
  git-ignored).
* If you accidentally commit a secret, rotate it immediately and notify
  the maintainers.

## Rate Limiting & Terms of Service

* Always use official APIs when available.
* Respect rate limits and robots.txt directives.
* This tool is for personal, non-commercial research use.
* Users are responsible for complying with each retailer's Terms of Service.
