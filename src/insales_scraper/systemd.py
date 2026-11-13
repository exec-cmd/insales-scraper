# systemd.py
import logging
import shutil
import subprocess
from pathlib import Path

from platformdirs import user_config_path

from insales_scraper import console

from .config import default_config

logger = logging.getLogger(__name__)

UNIT_PATH = user_config_path() / "systemd" / "user" / "inscrap.service"


def _quote(arg: str) -> str:
    escaped = (
        arg.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("%", "%%")
        .replace("$", "$$")
    )
    return f'"{escaped}"'


def _systemctl(*args: str) -> None:
    subprocess.run(["systemctl", "--user", *args], check=True)


def install_service(
    url: str,
    output: Path,
    concurrency: int = default_config.max_concurrent_requests,
    retries: int = default_config.max_request_attempts,
    transport: str = default_config.transport_backend,
    fail_fast: bool = default_config.fail_on_request_error,
    proxy: str | None = default_config.proxy_url,
    interval: float = default_config.interval_between_runs_seconds,
    count: int = default_config.number_of_runs,
) -> None:
    executable = shutil.which("inscrap")
    if executable is None:
        raise RuntimeError("inscrap command not found in PATH")

    args = [
        executable,
        "run",
        url,
        "-o",
        str(output.resolve()),
        "-c",
        str(concurrency),
        "-r",
        str(retries),
        "-t",
        transport,
        "--interval",
        str(interval),
        "--count",
        str(count),
    ]
    if fail_fast:
        args.append("-f")
    if proxy:
        args += ["-p", proxy]

    command = " ".join(_quote(arg) for arg in args)

    UNIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNIT_PATH.write_text(
        "\n".join(
            [
                "[Unit]",
                "Description=Insales scraper",
                "",
                "[Service]",
                f"ExecStart={command}",
                "Restart=on-failure",
                "",
                "[Install]",
                "WantedBy=default.target",
                "",
            ]
        ),
        encoding="utf-8",
    )
    logger.info(f"unit written: {UNIT_PATH}")

    console.console.print(
        f"[green]Следующая команда записана в автозагрузку: {command}[/green]"
    )

    _systemctl("daemon-reload")
    _systemctl("enable", "--now", UNIT_PATH.name)


def uninstall_service() -> None:
    if not UNIT_PATH.exists():
        raise RuntimeError("Service not installed")

    _systemctl("disable", "--now", UNIT_PATH.name)
    UNIT_PATH.unlink()
    _systemctl("daemon-reload")
