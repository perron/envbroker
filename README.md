# envbroker

Keep secrets out of an agent's context window. Store a value once, refer to
it by name, and inject it only into a child process environment. envbroker
has no `get` or `print` command, and it redacts a value if a child process
prints it anyway.

Do not put API keys or PATs in MCP configs or chat logs. Point the agent at
`envbroker run --with NAME -- your-command` instead.

## Install

```bash
python3 -m pip install -e .
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
