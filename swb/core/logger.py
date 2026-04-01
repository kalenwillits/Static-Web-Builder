"""Logging configuration for swb."""

import logging
import sys

LOG_FORMAT = "%(levelname)s: %(message)s"
DEBUG_FORMAT = "%(levelname)s [%(name)s] %(message)s"


def setup_logger(verbose=False):
    """Configure the swb logger.

    Args:
        verbose: If True, set DEBUG level with module names in output.
    """
    level = logging.DEBUG if verbose else logging.INFO
    fmt = DEBUG_FORMAT if verbose else LOG_FORMAT

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))

    logger = logging.getLogger("swb")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


def get_logger(name=None):
    """Get a child logger for a module.

    Args:
        name: Module name (e.g., 'builder', 'deployer'). If None, returns root swb logger.
    """
    if name:
        return logging.getLogger(f"swb.{name}")
    return logging.getLogger("swb")
