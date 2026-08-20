"""Task families discovered at import time.

Families live one-per-module so they can be authored, reviewed and rejected
independently; anything that fails its gates is simply absent from REGISTRY
rather than needing to be surgically removed from a shared file.
"""
from __future__ import annotations

import importlib
import pkgutil


def load_all() -> dict:
    found: dict[str, dict] = {}
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{__name__}.{info.name}")
        except Exception as exc:  # noqa: BLE001 - a broken family must not
            print(f"[fam] skipping {info.name}: {type(exc).__name__}: {exc}")
            continue          # take the whole benchmark down
        family = getattr(module, "FAMILY", None)
        if isinstance(family, dict) and "build" in family and "verify" in family:
            found[info.name.replace("_", "-")] = family
    return found
