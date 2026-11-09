from unittest.mock import patch

import wiz_central_toolkit.godfatherwiz.__main__ as godfatherwiz_cli
import wiz_central_toolkit.godfatherwiz.lib.cli as godfatherwiz_lib_cli
import wiz_central_toolkit.readwiz.__main__ as readwiz_cli
import wiz_central_toolkit.rustwiz.__main__ as rustwiz_cli


def test_readwiz_cli_verbs(capsys):
    with patch("sys.argv", ["readwiz", "verbs"]):
        readwiz_cli.main()

    captured = capsys.readouterr()
    assert "ALLOW" in captured.out or "[ALLOW]" in captured.out


def test_readwiz_cli_check_allow(capsys):
    with patch("sys.argv", ["readwiz", "check", "ls -la"]):
        readwiz_cli.main()

    captured = capsys.readouterr()
    assert "ALLOW" in captured.out


def test_readwiz_cli_check_deny(capsys):
    with patch("sys.argv", ["readwiz", "check", "rm -rf /"]):
        readwiz_cli.main()

    captured = capsys.readouterr()
    assert "DENIED" in captured.out


def test_rustwiz_cli_help(capsys):
    with patch("sys.argv", ["rustwiz", "--help"]):
        rustwiz_cli.main()

    captured = capsys.readouterr()
    assert "rustwiz" in captured.out.lower() or "usage" in captured.out.lower()


def test_godfatherwiz_cli_status(capsys):
    with patch("sys.argv", ["godfatherwiz", "status"]):
        godfatherwiz_lib_cli._dispatch()

    captured = capsys.readouterr()
    assert "write_wizard reachable" in captured.out
    assert "python_wizard reachable" in captured.out
    # status probes the installed fleet only: citizens that are
    # not installed (Pro's truthwiz, bootwiz, repairwiz) are
    # never probed, so their names never appear in the output.
    assert "truthwiz" not in captured.out
    assert "bootwiz" not in captured.out
    assert "repairwiz" not in captured.out
