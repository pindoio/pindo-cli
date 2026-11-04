# pindo-cli

[![Tests](https://github.com/pindoio/pindo-cli/actions/workflows/ci.yaml/badge.svg)](https://github.com/pindoio/pindo-cli/actions/workflows/ci.yaml)
[![PyPI](https://img.shields.io/pypi/v/pindo-cli.svg)](https://pypi.org/project/pindo-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/pindo-cli.svg)](https://pypi.org/project/pindo-cli/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

The official command-line interface for [Pindo](https://www.pindo.io/), the SMS
platform. Log in once, then send test messages, check your balance, manage
your organization and pull reports from your terminal or from scripts.

- [Installation](#installation)
- [Quick start](#quick-start)
- [Commands](#commands)
- [Authentication and configuration](#authentication-and-configuration)
- [Reports](#reports)
- [Using the CLI in scripts](#using-the-cli-in-scripts)
- [Using the API directly](#using-the-api-directly)
- [Development](#development)

## Installation

Requires Python 3.10 or newer.

The recommended way is [pipx](https://pipx.pypa.io/) (or
[uv](https://docs.astral.sh/uv/)), which installs the `pindo` command in its
own isolated environment:

```bash
pipx install pindo-cli
```

```bash
uv tool install pindo-cli
```

Plain pip works too:

```bash
python -m pip install --upgrade pindo-cli
```

Check it worked:

```bash
pindo --version
```

## Quick start

```bash
pindo register                 # create an account (skip if you have one)
pindo login                    # saves your API token to ~/.pindo/config.toml
pindo balance                  # USD 71421.953
pindo sms --to +250781234567 --text "Hello from Pindo" --sender Pindo
```

Every command prompts for anything you leave out, and `pindo <command> --help`
(or `-h`) lists its options.

## Commands

| Command | What it does |
|---|---|
| `pindo login` | Log in and save your API token for later commands |
| `pindo logout` | Delete the saved token |
| `pindo token` | Print a new API token without saving it |
| `pindo refresh-token` | Request a fresh token and update the saved one |
| `pindo register` | Create a new Pindo account |
| `pindo forgot-password` | Email yourself a password-recovery token |
| `pindo recover-password` | Set a new password with that recovery token |
| `pindo sms` | Send a test SMS |
| `pindo balance` | Show your account balance |
| `pindo org` | Update your organization's name, delivery-report webhook and retry count |
| `pindo config show` | Show the active base URL, user and (masked) token, and where the token came from |
| `pindo config path` | Print the config file location |
| `pindo report ...` | Reporting commands (see [Reports](#reports)) |

Global options go **before** the command:

| Option | Meaning |
|---|---|
| `--debug` | Log every API request and response to stderr. Passwords and tokens are redacted. |
| `--base-url URL` | Talk to another API environment, e.g. staging |
| `-v`, `--version` | Show the version |
| `-h`, `--help` | Show help |

```bash
pindo --debug balance
```

Phone numbers must be in international format with the country code
(`+250781234567`). Spaces, dashes and brackets are stripped, and a missing
leading `+` is added.

## Authentication and configuration

`pindo login` stores your token in `~/.pindo/config.toml`. The file and its
folder can only be read by your user account. Every command that needs a token
looks for one in this order:

1. `--token` / `-t` on the command line
2. the `PINDO_TOKEN` environment variable (handy for CI and cron jobs)
3. the config file written by `pindo login`

| Environment variable | Purpose |
|---|---|
| `PINDO_TOKEN` | API token to use instead of the saved one |
| `PINDO_BASE_URL` | API base URL (default `https://api.pindo.io`) |
| `PINDO_CONFIG` | Use a different config file |

Run `pindo config show` to see which token is in use and where it came from.

## Reports

Reporting commands live under `pindo report` and all share these options:

| Option | Meaning |
|---|---|
| `--from DATE` / `--to DATE` | Date range. Accepts `2026-10-01`, `today`, `yesterday` or `30d`. Default: last 7 days. |
| `--page N` / `--per-page N` | Pagination (default page 1, 50 rows) |
| `--all` | Fetch every page |
| `-o`, `--output table\|csv\|json` | Output format (default `table`) |
| `-f`, `--file PATH` | Write to a file instead of the terminal |
| `--tz ZONE` | Timezone for dates, e.g. `Africa/Kigali` or `UTC` (default: your local zone) |

Run `pindo report --help` to see the available reports.

## Using the CLI in scripts

Errors are printed to stderr as a single `Error: ...` line, and the exit code
tells you what happened:

| Exit code | Meaning |
|---|---|
| `0` | Success |
| `1` | The API or the network returned an error (bad token, unknown email, server down, ...) |
| `2` | Invalid usage, e.g. a missing option or a malformed phone number |

```console
$ pindo balance --token wrong
Error: Unauthorized. Your token is invalid or expired; run `pindo login`. (HTTP 401)
$ echo $?
1
```

Read-only requests are retried automatically, with backoff, when the server
is temporarily unavailable (HTTP 429/502/503/504). Requests that send messages
or change data are never retried, so an SMS is never sent twice.

## Using the API directly

The CLI is a thin client for the Pindo REST API. Examples for sending SMS
(single and bulk), inbound messages, delivery-report webhooks and PindoVerify
in cURL, Python, Node.js, PHP, Ruby, Go, Java and C# are in
[docs/api.md](docs/api.md).

## Development

You need [Poetry](https://python-poetry.org/) 2.x.

```bash
git clone https://github.com/pindoio/pindo-cli.git
cd pindo-cli
poetry install
poetry run pre-commit install   # optional: lint and format on every commit
```

| Task | Command |
|---|---|
| Run the tests (all HTTP is mocked) | `poetry run pytest --cov` |
| Also run tests against the live API | `poetry run pytest --run-live` |
| Lint | `poetry run ruff check .` |
| Format | `poetry run ruff format .` |
| Type-check | `poetry run mypy` |
| Run the CLI from source | `poetry run pindo --help` |

See [CONTRIBUTING.md](CONTRIBUTING.md) for how the code is laid out and how
releases work. To report a security issue, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
