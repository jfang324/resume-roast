"""Shared JSON file primitives used by every persistence store."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast

from resume_roast.persistence.errors import InvalidJsonError, InvalidSchemaError, PersistenceError


def read_json_object(path: Path) -> dict[str, Any]:
    """Parse the JSON object stored at path.

    Raises InvalidJsonError if the file is not valid JSON, and
    InvalidSchemaError if the top-level value is not a JSON object. Missing
    files are the caller's concern: FileNotFoundError propagates as-is.
    """
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidJsonError(f"{path} does not contain valid JSON") from exc

    if not isinstance(data, dict):
        raise InvalidSchemaError(f"{path} does not contain a JSON object")

    return cast("dict[str, Any]", data)


def write_json_object(path: Path, data: dict[str, Any], *, secure: bool = False) -> None:
    """Atomically write data to path as indented JSON.

    Creates the parent directory if missing (mode 0700 best-effort). With
    secure=True, sets the written file's mode to 0600 best-effort. Windows
    chmod no-op semantics are acceptable. Environmental failures are wrapped
    in PersistenceError naming the path.
    """
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(data, tmp_file, indent=2)
            if secure:
                tmp_path.chmod(0o600)
            os.replace(tmp_path, path)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
    except OSError as exc:
        raise PersistenceError(f"failed to write {path}") from exc
