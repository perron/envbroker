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

## 30-second quick start

```bash
# The value is read from stdin or --value-file. It is never echoed.
printf 'demo-not-a-real-secret
' | envbroker --store ./store.json set DEMO_TOKEN

envbroker --store ./store.json list
envbroker --store ./store.json has DEMO_TOKEN

# The child sees DEMO_TOKEN. The agent sees only the command and names.
envbroker --store ./store.json run --with DEMO_TOKEN -- python3 -c 'import os; print("present" if os.environ.get("DEMO_TOKEN") else "missing")'
```

Sample output from that exact example:

```
stored DEMO_TOKEN
$ envbroker --store ./store.json list
DEMO_TOKEN
$ envbroker --store ./store.json has DEMO_TOKEN
DEMO_TOKEN: present
$ envbroker --store ./store.json run --with DEMO_TOKEN -- python3 -c 'import os; print("present" if os.environ.get("DEMO_TOKEN") else "missing")'
present
```

The value was read from stdin and is not shown in the output. `run` prints `present` because the child process checked that `DEMO_TOKEN` was in its environment and printed that word, not the secret.

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

## Use it with your agent

You can point a coding agent at this repository and ask it to use the tool, adapt it, or write a small tool in the same style. That works with Claude Code, Codex, Cursor, Grok Bot, and anything else that can clone a git repo and run a Python CLI.

A short prompt you can paste:

> Clone https://github.com/perron/envbroker and read SECURITY.md first. Help me store a secret named DEMO_TOKEN in ./store.json from a value file, then run a command with it injected. Never print the secret value, never add a get/print command, and never read my shell profile or other credential files.

If you want a new tool in this style, say so explicitly: one job, standard-library Python, pytest first, no API key, and an honest Limits section.

## Contributing / how you can help

Bug reports, tight tests, and small honest features are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to run the suite and for pull request guidelines.

Good first issues:

- Add a `remove` command that deletes a name from the store and never prints the value.
- Document (and optionally add, behind a flag) a streaming `run` mode that does not capture child output, including the security trade-off.
- Refuse to start if the store path is a symlink pointing outside its parent directory.

If you are unsure whether an idea fits, open an issue before writing a large patch.

## License

MIT. See `LICENSE`. Please read `SECURITY.md` before filing a vulnerability report. Agents should also read `AGENTS.md`.
