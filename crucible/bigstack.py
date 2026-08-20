"""Run generator and verifier code on a thread with a large C stack.

`ensemble_disagreement.build` segfaults on this platform roughly five times in
eight on the default main-thread stack, and passes six for six on a 64 MB one.
The Python side is shallow (a recursion limit of 120 holds through a full
build), so the stack being exhausted is the C stack, not the Python one - the
signature of recursive deallocation of a transient deeply nested structure.
It reproduces identically on CPython 3.11 and 3.14 and with numpy blocked, so
it is neither an interpreter bug we can wait out nor a bad extension.

A crash cannot corrupt a recorded outcome (a dead process writes no file), but
it can kill a campaign worker mid-episode and it stops the family gate from
certifying a family that is otherwise sound. Both callers route through here.

Wrap the process's WHOLE body, not each build: a per-call thread still leaves
the collection of that call's garbage to whichever thread runs the next GC
pass, and if that is the small-stacked main thread the recursive free crashes
there instead. Measured: per-call wrapping still segfaults; one long-lived
big-stack thread that also does its own collecting does not.

    from crucible.bigstack import call
    sys.exit(call(main))
"""
from __future__ import annotations

import threading
from typing import Any, Callable

STACK_BYTES = 64 * 1024 * 1024


def call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Call `fn` on a big-stack thread, re-raising its exception here."""
    box: dict[str, Any] = {}

    def target() -> None:
        try:
            box["value"] = fn(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 - forwarded to the caller
            box["error"] = exc

    previous = threading.stack_size()
    for size in (STACK_BYTES, 32 * 1024 * 1024, 0):
        try:
            threading.stack_size(size)
            break
        except (ValueError, RuntimeError):
            continue
    try:
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join()
    finally:
        try:
            threading.stack_size(previous)
        except (ValueError, RuntimeError):
            pass
    if "error" in box:
        raise box["error"]
    return box["value"]
