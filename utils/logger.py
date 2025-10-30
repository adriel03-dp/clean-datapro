import logging
from typing import Optional

try:
    from rich.logging import RichHandler
except Exception:  # keep fallback if rich isn't installed yet
    RichHandler = None  # type: ignore


def get_logger(name: str = __name__, level: int = logging.INFO, use_rich: Optional[bool] = True) -> logging.Logger:
    """
    Return a configured logger.

    If `rich` is installed and `use_rich` is True, uses RichHandler for nicer console output.
    """
    handlers = []
    if use_rich and RichHandler is not None:
        handler = RichHandler()
        handlers.append(handler)
    else:
        handler = logging.StreamHandler()
        handlers.append(handler)

    logging.basicConfig(level=level, format="%(message)s", handlers=handlers)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


if __name__ == "__main__":
    log = get_logger("cleandatapro.demo")
    log.info("This is an info message from CleanDataPro logger demo.")
