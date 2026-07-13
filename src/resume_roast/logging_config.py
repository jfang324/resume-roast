"""Application-level logging configuration.

Modules emit records via ``logging.getLogger(__name__)`` and never configure
handlers or levels; the app owns that decision. This is the one place handlers
are installed, called once from the CLI entry point.

Logs go to files under ``~/.resume-roast/logs`` — never the console, whose job
is the user-facing output. Problems and debug detail are split into two files:
``errors.log`` always captures WARNING and above; ``debug.log`` (which can
quote resume content) captures full DEBUG detail only under ``--debug``,
keeping raw payloads off disk otherwise.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from resume_roast.persistence.paths import storage_dir

_LOG_DIR_MODE = 0o700
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 5
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Handlers we installed, tracked so repeat calls (e.g. tests) replace rather
# than stack them.
_installed: list[logging.Handler] = []


def _rotating_handler(path: Path, level: int) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,  # don't create the file until something is actually logged
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_FORMAT))
    return handler


def configure_logging(debug: bool) -> None:
    """Route logging to files under ``~/.resume-roast/logs``.

    ``errors.log`` always captures WARNING and above; ``debug.log`` captures
    full DEBUG detail (system prompts, raw responses) only when `debug` is set.
    Idempotent: previously installed handlers are removed first, so repeat calls
    reconfigure cleanly.
    """
    root = logging.getLogger()
    for handler in _installed:
        root.removeHandler(handler)
        handler.close()
    _installed.clear()

    root.setLevel(logging.DEBUG if debug else logging.WARNING)

    log_dir = storage_dir() / "logs"
    log_dir.mkdir(mode=_LOG_DIR_MODE, parents=True, exist_ok=True)

    handlers = [_rotating_handler(log_dir / "errors.log", logging.WARNING)]
    if debug:
        handlers.append(_rotating_handler(log_dir / "debug.log", logging.DEBUG))

    for handler in handlers:
        root.addHandler(handler)
        _installed.append(handler)
