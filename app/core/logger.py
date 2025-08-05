import logging

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Set up and return a logger instance for the application.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    logger = logging.getLogger("gitlab_repo_sculptor")
    return logger
