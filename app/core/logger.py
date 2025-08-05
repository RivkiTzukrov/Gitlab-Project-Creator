import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger("gitlab_repo_sculptor")