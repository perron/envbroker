import os
import stat
from pathlib import Path
import envbroker.cli as eb


SECRET = "s3cret-value-for-tests-only"


def test_set_list_has_never_prints_value(tmp_path, capsys):
    store = tmp_path / "store.json"
    value_file = tmp_path / "in.txt"
    value_file.write_text(SECRET)
    assert eb.main(["--store", str(store), "set", "DEMO_TOKEN", "--value-file", str(value_file)]) == 0
    mode = store.stat().st_mode
    assert mode & (stat.S_IRWXG | stat.S_IRWXO) == 0
    assert eb.main(["--store", str(store), "list"]) == 0
    assert eb.main(["--store", str(store), "has", "DEMO_TOKEN"]) == 0
    out = capsys.readouterr().out
    err = capsys.readouterr().err
    assert "DEMO_TOKEN" in out
    assert SECRET not in out
    assert SECRET not in err
    assert eb.main(["--store", str(store), "has", "MISSING_TOKEN"]) == 1


def test_run_injects_and_redacts(tmp_path, capsys):
    store = tmp_path / "store.json"
    value_file = tmp_path / "in.txt"
    value_file.write_text(SECRET)
    eb.main(["--store", str(store), "set", "DEMO_TOKEN", "--value-file", str(value_file)])
    capsys.readouterr()
    script = tmp_path / "child.py"
    script.write_text("import os\nprint('present' if os.environ.get('DEMO_TOKEN') else 'missing')\nprint(os.environ['DEMO_TOKEN'])\n")
    code = eb.main(["--store", str(store), "run", "--with", "DEMO_TOKEN", "--", "python3", str(script)])
    assert code == 0
    captured = capsys.readouterr()
    assert "present" in captured.out
    assert SECRET not in captured.out
    assert SECRET not in captured.err
    assert "******" in captured.out


def test_run_missing_secret(tmp_path, capsys):
    store = tmp_path / "store.json"
    store.write_text("{}\n")
    os.chmod(store, 0o600)
    assert eb.main(["--store", str(store), "run", "--with", "DEMO_TOKEN", "--", "true"]) == 1
    assert "missing secrets" in capsys.readouterr().err
