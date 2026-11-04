# Contributing to pindo-cli

Thanks for helping! This guide covers the local setup, how the code is laid
out, and how changes get released.

## Setup

You need Python 3.10+ and [Poetry](https://python-poetry.org/) 2.x.

```bash
git clone https://github.com/pindoio/pindo-cli.git
cd pindo-cli
poetry install
poetry run pre-commit install   # runs ruff on every commit
```

Before opening a pull request, make sure these pass. CI runs the same checks
on Linux, macOS and Windows with Python 3.10 to 3.14.

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy
poetry run pytest --cov
```

All HTTP in the tests is mocked with [`responses`](https://github.com/getsentry/responses),
so the suite never touches the network. Tests marked `@pytest.mark.live` hit
the real API and only run with `pytest --run-live`.

## Code layout

| Module | Role |
|---|---|
| `pindo_cli/cli.py` | Click commands. Each one builds a client, calls one method and prints the result. |
| `pindo_cli/client.py` | `PindoClient`: one `requests.Session` with auth, timeouts, retries for safe requests, redacted debug logging, error handling and pagination. All endpoint paths are in `ENDPOINTS`. |
| `pindo_cli/config.py` | Token and base-URL resolution, and the private `~/.pindo/config.toml` file |
| `pindo_cli/output.py` | Table, CSV and JSON rendering shared by reports |
| `pindo_cli/reports/` | `pindo report ...` commands and their shared options |
| `pindo_cli/http.py` | Deprecated wrappers kept for the pre-0.3 Python API |

Guidelines:

- Keep commands thin. API logic belongs in `PindoClient`, which raises
  `PindoClientException` with a user-facing message, and `handle_errors`
  turns that into `Error: ...` with exit code 1.
- Never log secrets. Add any new sensitive field names to
  `client.SENSITIVE_KEYS`.
- Never retry requests that send messages or change data.
- Add a test with every behavior change.

## Commits and releases

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).
[python-semantic-release](https://python-semantic-release.readthedocs.io/)
reads them on every push to `master`:

| Commit type | Release |
|---|---|
| `fix:`, `perf:` | patch (1.1.0 → 1.1.1) |
| `feat:` | minor (1.1.0 → 1.2.0) |
| `feat!:` or a `BREAKING CHANGE:` footer | major (1.1.0 → 2.0.0) |
| `docs:`, `chore:`, `ci:`, `test:`, `refactor:`, `build:`, `style:` | no release |

When a release is due, the Release workflow bumps the version in
`pyproject.toml`, updates `CHANGELOG.md`, tags `vX.Y.Z`, creates the GitHub
release and publishes to PyPI with the `PYPI_TOKEN` repository secret.

Dependabot opens weekly pull requests for dependency updates and monthly ones
for GitHub Actions.
