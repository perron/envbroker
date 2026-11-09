"""Keep secrets out of an agent's context. Values are never printed."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

__version__ = "0.1.0"

NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
# There is no `get` or `print` command on purpose.


def default_store() -> Path:
    return Path.home() / ".envbroker" / "store.json"


def validate_name(name: str) -> str:
    if not NAME_RE.match(name):
        raise ValueError("secret names must match [A-Z][A-Z0-9_]*")
    return name


def load_store(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    mode = path.stat().st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ValueError(f"store {path} must be mode 600 (group or other bits are set)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError("store is not a string-to-string JSON object")
    return data


def save_store(path: Path, data: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)
    os.chmod(path, 0o600)


def redact(text: str, secrets: list[str]) -> str:
    """Best-effort redaction if a child process prints a secret anyway."""
    out = text
    for secret in secrets:
        if secret and secret in out:
            out = out.replace(secret, "******")
    return out


def cmd_set(store_path: Path, name: str, value: str) -> int:
    validate_name(name)
    if not value:
        print("error: empty secret refused", file=sys.stderr)
        return 1
    data = load_store(store_path) if store_path.exists() else {}
    data[name] = value
    save_store(store_path, data)
    print(f"stored {name}")
    return 0


def cmd_list(store_path: Path) -> int:
    data = load_store(store_path) if store_path.exists() else {}
    if not data:
        print("no secrets stored")
        return 0
    for name in sorted(data):
        print(name)
    return 0


def cmd_has(store_path: Path, name: str) -> int:
    validate_name(name)
    data = load_store(store_path) if store_path.exists() else {}
    if name in data:
        print(f"{name}: present")
        return 0
    print(f"{name}: missing")
    return 1


def cmd_run(store_path: Path, names: list[str], command: list[str]) -> int:
    if not command:
        print("error: missing command after --", file=sys.stderr)
        return 1
    data = load_store(store_path)
    missing = [name for name in names if name not in data]
    if missing:
        print(f"error: missing secrets: {', '.join(missing)}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    values = []
    for name in names:
        validate_name(name)
        env[name] = data[name]
        values.append(data[name])
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    # Never echo raw child output if it contains a secret; redact first.
    sys.stdout.write(redact(result.stdout, values))
    sys.stderr.write(redact(result.stderr, values))
    return int(result.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="envbroker",
        description="Run commands with secrets injected, without ever printing the values.",
    )
    parser.add_argument("--store", help="store file (default: ~/.envbroker/store.json)")
    parser.add_argument("--version", action="version", version=f"envbroker {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_set = sub.add_parser("set", help="read a secret value from stdin and store it (value is never echoed)")
    p_set.add_argument("name")
    p_set.add_argument("--value-file", help="read the value from this file instead of stdin")

    sub.add_parser("list", help="list secret names only")

    p_has = sub.add_parser("has", help="exit 0 if the named secret exists")
    p_has.add_argument("name")

    p_run = sub.add_parser("run", help="run a command with named secrets in its environment")
    p_run.add_argument("--with", dest="names", action="append", required=True, help="secret name to inject (repeatable)")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="command to run, preferably after --")

    args = parser.parse_args(argv)
    store = Path(args.store) if args.store else default_store()
    try:
        if args.cmd == "set":
            if args.value_file:
                value = Path(args.value_file).read_text(encoding="utf-8").rstrip("\n")
            else:
                value = sys.stdin.read().rstrip("\n")
            return cmd_set(store, args.name, value)
        if args.cmd == "list":
            return cmd_list(store)
        if args.cmd == "has":
            return cmd_has(store, args.name)
        if args.cmd == "run":
            command = list(args.command)
            if command and command[0] == "--":
                command = command[1:]
            return cmd_run(store, list(args.names), command)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
