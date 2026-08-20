"""Windowless subprocess execution.

On Windows every console subprocess gets a console window, even when the parent
has none. This project spawns a lot of them - sandboxed model code, scheduled
task registration, git and gate checks - and each one flashes a window that
steals focus from whoever is using the machine. That is not a cosmetic problem;
it makes the machine unusable while a campaign runs.

Import `run` from here instead of calling `subprocess.run` directly.
"""
from __future__ import annotations

import subprocess
import sys

CREATE_NO_WINDOW = 0x08000000


def hidden_kwargs() -> dict:
    """Flags that suppress the console for a child process on Windows."""
    if sys.platform != "win32":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {"creationflags": CREATE_NO_WINDOW, "startupinfo": startupinfo}


def run(args, **kwargs):
    """subprocess.run with the console suppressed.

    Caller-supplied creationflags are OR-ed rather than overwritten so an
    explicit DETACHED_PROCESS still works.
    """
    flags = kwargs.pop("creationflags", 0)
    hidden = hidden_kwargs()
    if hidden:
        hidden["creationflags"] |= flags
        kwargs.setdefault("startupinfo", hidden["startupinfo"])
        kwargs["creationflags"] = hidden["creationflags"]
    elif flags:
        kwargs["creationflags"] = flags
    return subprocess.run(args, **kwargs)
