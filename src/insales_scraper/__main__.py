import logging

from rich.logging import RichHandler

from .cli import app
from .config import config
from .console import console

logging.basicConfig(
    level=config.level, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)]
)
logger = logging.getLogger(__name__)


def main():
    logger.debug("Starting CLI module")
    app()
