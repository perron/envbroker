# envbroker

Keep secrets out of an agent's context window. Store a value once, refer to
it by name, and inject it only into a child process environment. envbroker
has no `get` or `print` command, and it redacts a value if a child process
prints it anyway.

Do not put API keys or PATs in MCP configs or chat logs. Point the agent at
`envbroker run --with NAME -- your-command` instead.

## Install

Python 3.10 or later.

From a checkout:

```bash
python3 -m pip install .
python3 -m pip install -e ".[dev]"  # optional, for tests
```

## 30-second example

```bash
# The value is read from stdin or --value-file. It is never echoed.
printf 'demo-not-a-real-secret
' | envbroker --store ./store.json set DEMO_TOKEN

envbroker --store ./store.json list
envbroker --store ./store.json has DEMO_TOKEN

# The child sees DEMO_TOKEN. The agent sees only the command and names.
envbroker --store ./store.json run --with DEMO_TOKEN -- python3 -c 'import os; print("present" if os.environ.get("DEMO_TOKEN") else "missing")'
```

The default store is `~/.envbroker/store.json`, mode 0600. `--store` is
recommended in tests and project-local use. envbroker never reads your
shell profile, browser cookies, or other credential files.

## Credit

Motivated by public reports of coding agents swallowing live API keys from
MCP configs and chat logs. Original CLI; no source was copied from any
credential broker.

## Limits

- There is no `get` or `print` command. Names can be listed; values cannot.
- The store is a mode-0600 JSON file (default `~/.envbroker/store.json`). A store with group or world bits set is refused.
- `run` injects named secrets into a child environment and redacts those exact values from captured stdout and stderr. Redaction will not catch a secret written to a file, a socket, or a modified spelling.
- `run` captures child output (it is not a TTY passthrough), so it is a poor fit for long-running interactive commands.
- envbroker never reads your shell profile, browser cookies, or other credential files.

From GitHub you can also install with:

```bash
python3 -m pip install git+https://github.com/perron/envbroker.git
```

This package is not published to PyPI.

## License

MIT. See `LICENSE`. Please read `SECURITY.md` before filing a vulnerability report.
