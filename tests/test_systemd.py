import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from insales_scraper import cli, systemd

runner = CliRunner()


@pytest.fixture
def unit_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "systemd" / "user" / "inscrap.service"
    monkeypatch.setattr(systemd, "UNIT_PATH", path)
    return path


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    recorded: list[list[str]] = []
    monkeypatch.setattr(
        systemd.subprocess, "run", lambda cmd, **_: recorded.append(cmd)
    )
    monkeypatch.setattr(systemd.shutil, "which", lambda _: "/usr/bin/inscrap")
    return recorded


def test_install_writes_unit(unit_path: Path, calls: list[list[str]], tmp_path: Path):
    systemd.install_service("https://shop.test", tmp_path / "out.json")

    text = unit_path.read_text(encoding="utf-8")
    assert (
        f'ExecStart="/usr/bin/inscrap" "run" "https://shop.test" "-o" "{tmp_path / "out.json"}"'
        in text
    )
    assert "Restart=on-failure" in text
    assert "WantedBy=default.target" in text


def test_install_calls_systemctl_in_order(
    unit_path: Path, calls: list[list[str]], tmp_path: Path
):
    systemd.install_service("https://shop.test", tmp_path / "out.json")

    assert calls == [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "--now", "inscrap.service"],
    ]


def test_install_makes_absolute_output(
    unit_path: Path,
    calls: list[list[str]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)

    systemd.install_service("https://shop.test", Path("out.json"))

    assert f'"{tmp_path / "out.json"}"' in unit_path.read_text(encoding="utf-8")


def test_install_overwrites_existing_unit(
    unit_path: Path, calls: list[list[str]], tmp_path: Path
):
    systemd.install_service("https://old.test", tmp_path / "out.json")
    systemd.install_service("https://new.test", tmp_path / "out.json")

    text = unit_path.read_text(encoding="utf-8")
    assert "new.test" in text
    assert "old.test" not in text


def test_install_without_executable(
    unit_path: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(systemd.shutil, "which", lambda _: None)

    with pytest.raises(RuntimeError, match="not found"):
        systemd.install_service("https://shop.test", tmp_path / "out.json")

    assert not unit_path.exists()


def test_install_systemctl_failure(
    unit_path: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    def fail(cmd, **_):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(systemd.shutil, "which", lambda _: "/usr/bin/inscrap")
    monkeypatch.setattr(systemd.subprocess, "run", fail)

    with pytest.raises(subprocess.CalledProcessError):
        systemd.install_service("https://shop.test", tmp_path / "out.json")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("plain", '"plain"'),
        ("", '""'),
        ('a"b', '"a\\"b"'),
        ("a\\b", '"a\\\\b"'),
        ("100%", '"100%%"'),
        ("$HOME", '"$$HOME"'),
        ("a b", '"a b"'),
    ],
)
def test_quote(raw: str, expected: str):
    assert systemd._quote(raw) == expected


def test_uninstall_removes_unit(unit_path: Path, calls: list[list[str]]):
    unit_path.parent.mkdir(parents=True)
    unit_path.write_text("x")

    systemd.uninstall_service()

    assert not unit_path.exists()
    assert calls == [
        ["systemctl", "--user", "disable", "--now", "inscrap.service"],
        ["systemctl", "--user", "daemon-reload"],
    ]


def test_uninstall_not_installed(unit_path: Path, calls: list[list[str]]):
    with pytest.raises(RuntimeError, match="not installed"):
        systemd.uninstall_service()

    assert calls == []


def test_uninstall_keeps_unit_if_disable_fails(
    unit_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def fail(cmd, **_):
        raise subprocess.CalledProcessError(1, cmd)

    unit_path.parent.mkdir(parents=True)
    unit_path.write_text("x")
    monkeypatch.setattr(systemd.subprocess, "run", fail)

    with pytest.raises(subprocess.CalledProcessError):
        systemd.uninstall_service()

    assert unit_path.exists()


@pytest.mark.parametrize(
    "command", [["install-service", "https://shop.test", "-o", "o"], ["uninstall"]]
)
def test_cli_not_linux(
    command: list[str], monkeypatch: pytest.MonkeyPatch, calls: list[list[str]]
):
    monkeypatch.setattr(cli.platform, "system", lambda: "Windows")

    result = runner.invoke(cli.app, command)

    assert "Linux" in result.output
    assert calls == []


@pytest.mark.parametrize(
    "command", [["install-service", "https://shop.test", "-o", "o"], ["uninstall"]]
)
def test_cli_no_systemctl(
    command: list[str], monkeypatch: pytest.MonkeyPatch, calls: list[list[str]]
):
    monkeypatch.setattr(cli.platform, "system", lambda: "Linux")
    monkeypatch.setattr(cli.shutil, "which", lambda _: None)

    result = runner.invoke(cli.app, command)

    assert "Systemd" in result.output
    assert calls == []


def test_cli_install_executable_missing(
    unit_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cli.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        cli.shutil, "which", lambda name: "/bin/x" if name == "systemctl" else None
    )

    result = runner.invoke(cli.app, ["install-service", "https://shop.test", "-o", "o"])

    assert result.exit_code == 0
    assert "inscrap" in result.output


def test_cli_uninstall_not_installed(unit_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cli.platform, "system", lambda: "Linux")
    monkeypatch.setattr(cli.shutil, "which", lambda _: "/bin/systemctl")

    result = runner.invoke(cli.app, ["uninstall"])

    assert result.exit_code == 0
