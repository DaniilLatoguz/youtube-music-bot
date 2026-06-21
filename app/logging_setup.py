"""Centralised logging configuration."""

import logging


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # aiogram's per-update INFO logs are noisy; keep them at WARNING.
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
