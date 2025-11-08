import logging
from typing import Optional

try:
    from rich.logging import RichHandler
except Exception:
    RichHandler = None


def get_logger(
    name: str = __name__, level: int = logging.INFO, use_rich: Optional[bool] = True
) -> logging.Logger:
    handlers = []
    if use_rich and RichHandler is not None:
        handlers.append(RichHandler())
    else:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers
    )
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
