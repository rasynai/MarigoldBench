"""Isolated execution of model-authored chain generators.

Generators are untrusted code: they run in a separate interpreter (`python -I`,
no site packages, no inherited environment) inside a throwaway directory with a
wall-clock timeout, and may use only the standard library. The payload crosses
the boundary as JSON on stdout.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import sys
import tempfile
from pathlib import Path

DRIVER = '''
import json, sys
sys.path.insert(0, ".")
import genmod
payload = genmod.gen({seed}, {condition!r})
sys.stdout.write("<<<PAYLOAD>>>" + json.dumps(payload, default=str))
'''

BANNED_IMPORTS = ("subprocess", "socket", "shutil", "urllib", "requests",
                  "ctypes", "multiprocessing", "importlib", "pickle")


class GeneratorRejected(Exception):
    pass


def static_check(generator_src: str) -> None:
    lowered = generator_src.lower()
    for banned in BANNED_IMPORTS:
        if f"import {banned}" in lowered or f"from {banned}" in lowered:
            raise GeneratorRejected(f"generator imports forbidden module {banned!r}")
    if "def gen(" not in generator_src:
        raise GeneratorRejected("generator has no gen(seed, condition) function")
    for suspicious in ("open(", "__import__", "eval(", "exec("):
        if suspicious in generator_src:
            raise GeneratorRejected(f"generator uses forbidden construct {suspicious!r}")


def run_chain_generator(generator_src: str, seed: int, condition: str,
                        timeout: int = 90, attempts: int = 3) -> dict:
    """Execute the generator, retrying transient interpreter deaths.

    Under parallel builds the OS occasionally kills a child with no output at
    all. That presents as a non-zero exit with empty stderr and is not a defect
    in the template - a real syntax or runtime error always writes a traceback.
    Retrying only that case keeps load flakiness out of the validity verdict.
    """
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return _run_once(generator_src, seed, condition, timeout)
        except GeneratorRejected as exc:
            message = str(exc)
            transient = "raised at" in message and len(message.split(":", 2)[-1].strip()) < 12
            if not transient or attempt == attempts - 1:
                raise
            last = exc
            time.sleep(1.0 * (attempt + 1))
    raise last  # type: ignore[misc]


def _run_once(generator_src: str, seed: int, condition: str, timeout: int) -> dict:
    static_check(generator_src)
    with tempfile.TemporaryDirectory(prefix="crucible3-gen-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "genmod.py").write_text(generator_src, encoding="utf-8")
        (tmp_path / "driver.py").write_text(
            DRIVER.format(seed=seed, condition=condition), encoding="utf-8")
        env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
               "PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": "0"}
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-S", "driver.py"], cwd=tmp, env=env,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise GeneratorRejected(f"generator timed out after {timeout}s") from exc
    if result.returncode != 0:
        stderr = (result.stderr or "")
        if "AssertionError" in stderr:
            raise GeneratorRejected(
                f"generator asserted at ({seed},{condition}) - it could not construct a"
                f" valid instance for this seed. Do not assert; search a deterministic"
                f" candidate list and fall back. Detail: {stderr[-400:]}")
        raise GeneratorRejected(
            f"generator raised at ({seed},{condition}): {stderr[-900:]}")
    marker = "<<<PAYLOAD>>>"
    if marker not in result.stdout:
        raise GeneratorRejected(
            f"generator produced no payload marker; stdout head: {result.stdout[:300]!r}")
    blob = result.stdout.split(marker, 1)[1].strip()
    try:
        payload = json.loads(blob)
    except json.JSONDecodeError as exc:
        raise GeneratorRejected(f"payload is not valid JSON: {blob[:300]!r}") from exc
    if not isinstance(payload, dict):
        raise GeneratorRejected("payload is not a JSON object")
    return payload
