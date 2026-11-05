"""
Centralised logging configuration.
"""
import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "ibm_watsonx_ai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


logger = logging.getLogger("grant_finder")
