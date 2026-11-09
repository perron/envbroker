# Security Policy

This project is a small local command-line tool. It does not phone home and does not require an API key.

## Reporting a vulnerability

Please open a [GitHub issue](https://github.com/perron/envbroker/issues) and mention that it is a security report. Do not include secrets, tokens, or private file contents in the issue.

If the report includes a working exploit against this tool, describe the impact and a minimal reproduction without pasting live credentials.

## Notes for this tool

envbroker is a local secret broker, not a vault service.

- There is no `get` or `print` command.
- Values are written to a JSON store with mode 0600 (default `~/.envbroker/store.json`). A store with group or world bits set is refused.
- `run` injects named secrets into a child environment and redacts those values from captured stdout/stderr.
- Redaction is best-effort and will not catch secrets that a child writes to a file, a socket, or a modified spelling.
- `run` captures child output (it is not a TTY passthrough), so it is a poor fit for long-running interactive commands.
- envbroker never reads your shell profile, browser cookies, or other credential files.

## Supported versions

The `master` branch and the latest tagged release, when one exists, are supported.
