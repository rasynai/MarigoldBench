"""Sandboxed execution of model-authored instance generators.

The authored artifact is a Python module defining gen(seed, condition) ->
dict. It runs in an isolated interpreter (python -I) in a temp directory
with a timeout, stdlib only, and returns the instance payload as JSON.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

DRIVER = """
import json, sys
sys.path.insert(0, ".")
import genmod
payload = genmod.gen({seed}, {condition!r})
print(json.dumps(payload))
"""

REQUIRED_KEYS = {"prompt", "artifacts", "truth", "reference_answer", "weak_answer"}


def run_generator(generator_src: str, seed: int, condition: str,
                  timeout: int = 60) -> dict:
    with tempfile.TemporaryDirectory(prefix="crucible2-gen-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "genmod.py").write_text(generator_src, encoding="utf-8")
        (tmp_path / "driver.py").write_text(
            DRIVER.format(seed=seed, condition=condition), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-I", "driver.py"], cwd=tmp,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout,
        )
    if result.returncode != 0:
        raise RuntimeError(f"generator failed ({seed},{condition}): "
                           f"{(result.stderr or '')[-800:]}")
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError(f"generator output not JSON: {result.stdout[:300]}") from exc
    missing = REQUIRED_KEYS - set(payload)
    if missing:
        raise RuntimeError(f"generator payload missing keys: {sorted(missing)}")
    if not isinstance(payload["artifacts"], dict) or not payload["artifacts"]:
        raise RuntimeError("generator produced no artifacts")
    return payload
