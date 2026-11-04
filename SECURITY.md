# Security policy

## Supported versions

Only the latest release of `pindo-cli` receives security fixes. Upgrade with:

```bash
pipx upgrade pindo-cli
```

## Reporting a vulnerability

Please **do not** open a public issue. Report it privately through
[GitHub security advisories](https://github.com/pindoio/pindo-cli/security/advisories/new)
or by email to team@pindo.io. Include steps to reproduce and the affected
version (`pindo --version`). We aim to reply within a few working days.

## How the CLI handles your credentials

- `pindo login` saves your API token to `~/.pindo/config.toml`. The file is
  created with mode `0600` and its folder with mode `0700`, so only your user
  account can read them. `pindo logout` deletes the file.
- Your password is only sent to the Pindo API, over HTTPS. It is never stored.
- `--debug` output redacts passwords and tokens, but it still shows request
  URLs and response bodies, so review it before sharing it.
- On shared machines, prefer the `PINDO_TOKEN` environment variable from a
  secret store over a saved config file.
