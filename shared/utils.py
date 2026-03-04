"""I/O helpers for the Istari module file-based contract."""

from __future__ import annotations

import json
import os


def read_input(work_dir: str = ".") -> dict:
    path = os.path.join(work_dir, "input.json")
    with open(path) as f:
        return json.load(f)


def write_output(data: dict, work_dir: str = ".") -> None:
    path = os.path.join(work_dir, "output.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def write_artifact(filename: str, content: str | bytes, work_dir: str = ".") -> None:
    path = os.path.join(work_dir, filename)
    if isinstance(content, bytes):
        with open(path, "wb") as f:
            f.write(content)
    else:
        with open(path, "w") as f:
            f.write(content)
