import logging

from rich.logging import RichHandler

from .cli import app
from .config import default_config
from .console import console

logging.basicConfig(
    level=default_config.level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
)
logger = logging.getLogger(__name__)


def main():
    logger.debug("Starting CLI module")
    app()
