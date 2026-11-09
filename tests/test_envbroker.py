import os
import stat
from pathlib import Path
import io
import pytest
import envbroker.cli as eb


FAKE_TEST_VALUE = "not-a-real-secret-for-tests-only"


def test_help_and_version():
    with pytest.raises(SystemExit) as exc:
        eb.main(["--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        eb.main(["--version"])
    assert exc.value.code == 0


def test_set_list_has_never_prints_value(tmp_path, capsys):
    store = tmp_path / "store.json"
    value_file = tmp_path / "in.txt"
    value_file.write_text(FAKE_TEST_VALUE)
    assert eb.main(["--store", str(store), "set", "DEMO_TOKEN", "--value-file", str(value_file)]) == 0
    mode = store.stat().st_mode
    assert mode & (stat.S_IRWXG | stat.S_IRWXO) == 0
    assert eb.main(["--store", str(store), "list"]) == 0
    assert eb.main(["--store", str(store), "has", "DEMO_TOKEN"]) == 0
    out = capsys.readouterr().out
    err = capsys.readouterr().err
    assert "DEMO_TOKEN" in out
    assert FAKE_TEST_VALUE not in out
    assert FAKE_TEST_VALUE not in err
    assert eb.main(["--store", str(store), "has", "MISSING_TOKEN"]) == 1


def test_run_injects_and_redacts(tmp_path, capsys):
    store = tmp_path / "store.json"
    value_file = tmp_path / "in.txt"
    value_file.write_text(FAKE_TEST_VALUE)
    eb.main(["--store", str(store), "set", "DEMO_TOKEN", "--value-file", str(value_file)])
    capsys.readouterr()
    script = tmp_path / "child.py"
    script.write_text("import os\nprint('present' if os.environ.get('DEMO_TOKEN') else 'missing')\nprint(os.environ['DEMO_TOKEN'])\n")
    code = eb.main(["--store", str(store), "run", "--with", "DEMO_TOKEN", "--", "python3", str(script)])
    assert code == 0
    captured = capsys.readouterr()
    assert "present" in captured.out
    assert FAKE_TEST_VALUE not in captured.out
    assert FAKE_TEST_VALUE not in captured.err
    assert "******" in captured.out


def test_run_missing_secret(tmp_path, capsys):
    store = tmp_path / "store.json"
    store.write_text("{}\n")
    os.chmod(store, 0o600)
    assert eb.main(["--store", str(store), "run", "--with", "DEMO_TOKEN", "--", "true"]) == 1
    assert "missing secrets" in capsys.readouterr().err


def test_invalid_name(tmp_path, capsys):
    store = tmp_path / "store.json"
    value_file = tmp_path / "in.txt"
    value_file.write_text(FAKE_TEST_VALUE)
    assert eb.main(["--store", str(store), "set", "demo-token", "--value-file", str(value_file)]) == 1
    assert "secret names must match" in capsys.readouterr().err
    assert not store.exists()


def test_empty_value_refused(tmp_path, capsys):
    store = tmp_path / "store.json"
    value_file = tmp_path / "in.txt"
    value_file.write_text("")
    assert eb.main(["--store", str(store), "set", "DEMO_TOKEN", "--value-file", str(value_file)]) == 1
    assert "empty secret refused" in capsys.readouterr().err
    assert not store.exists()


def test_bad_store_permissions(tmp_path, capsys):
    store = tmp_path / "store.json"
    store.write_text("{}\n")
    os.chmod(store, 0o644)
    assert eb.main(["--store", str(store), "list"]) == 1
    assert "must be mode 600" in capsys.readouterr().err


def test_missing_value_file(tmp_path, capsys):
    store = tmp_path / "store.json"
    assert eb.main(["--store", str(store), "set", "DEMO_TOKEN", "--value-file", str(tmp_path / "nope.txt")]) == 1
    assert "error:" in capsys.readouterr().err


def test_list_empty(tmp_path, capsys):
    store = tmp_path / "store.json"
    assert eb.main(["--store", str(store), "list"]) == 0
    assert "no secrets stored" in capsys.readouterr().out


def test_redact_stderr(tmp_path, capsys):
    store = tmp_path / "store.json"
    value_file = tmp_path / "in.txt"
    value_file.write_text(FAKE_TEST_VALUE)
    eb.main(["--store", str(store), "set", "DEMO_TOKEN", "--value-file", str(value_file)])
    capsys.readouterr()
    script = tmp_path / "child.py"
    script.write_text("import os, sys\nsys.stderr.write(os.environ['DEMO_TOKEN'] + '\\n')\n")
    assert eb.main(["--store", str(store), "run", "--with", "DEMO_TOKEN", "--", "python3", str(script)]) == 0
    captured = capsys.readouterr()
    assert FAKE_TEST_VALUE not in captured.out
    assert FAKE_TEST_VALUE not in captured.err
    assert "******" in captured.err


def test_invalid_store_json(tmp_path, capsys):
    store = tmp_path / "store.json"
    store.write_text("{nope")
    os.chmod(store, 0o600)
    assert eb.main(["--store", str(store), "list"]) == 1
    assert "error:" in capsys.readouterr().err


def test_run_missing_command(tmp_path, capsys):
    store = tmp_path / "store.json"
    value_file = tmp_path / "in.txt"
    value_file.write_text(FAKE_TEST_VALUE)
    eb.main(["--store", str(store), "set", "DEMO_TOKEN", "--value-file", str(value_file)])
    capsys.readouterr()
    assert eb.main(["--store", str(store), "run", "--with", "DEMO_TOKEN"]) == 1
    assert "missing command" in capsys.readouterr().err


def test_set_from_stdin_never_echoes(tmp_path, capsys, monkeypatch):
    store = tmp_path / "store.json"
    monkeypatch.setattr("sys.stdin", io.StringIO(FAKE_TEST_VALUE + "\n"))
    assert eb.main(["--store", str(store), "set", "DEMO_TOKEN"]) == 0
    captured = capsys.readouterr()
    assert "stored DEMO_TOKEN" in captured.out
    assert FAKE_TEST_VALUE not in captured.out
    assert FAKE_TEST_VALUE not in captured.err
