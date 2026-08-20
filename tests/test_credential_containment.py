"""The sandbox must not see credentials, and the gate must catch them if it does.

CORR-013: a model ran `print(os.environ)` inside the tool sandbox. The sandbox
had inherited the harness's environment, so four live provider keys were
printed into the episode transcript - and handed back to the provider as
conversation context on the next turn. Two mechanisms now stand in the way, and
both are tested here, because a containment claim with no failing case is the
CORR-008 spend guard again.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crucible.leakgate import CREDENTIAL_PATTERNS, _credential_scan  # noqa: E402
from crucible.lab.tools import SECRET_MARKERS, ToolBelt, _sandbox_env, run_python  # noqa: E402

CANARY = "sk-ant-api03-" + "CanaryMustNotEscapeTheSandbox0123456789"


def test_sandbox_environment_excludes_every_secret_shaped_variable():
    os.environ["ANTHROPIC_API_KEY"] = CANARY
    os.environ["SOMETHING_ELSE_TOKEN"] = CANARY
    try:
        env = _sandbox_env()
    finally:
        os.environ.pop("SOMETHING_ELSE_TOKEN", None)
    assert CANARY not in env.values()
    assert not [k for k in env if any(m in k.upper() for m in SECRET_MARKERS)]
    assert "PATH" in env, "the sandbox still needs to be able to run python"


def test_model_authored_code_cannot_read_a_key():
    os.environ["ANTHROPIC_API_KEY"] = CANARY
    belt = ToolBelt(workspace=Path(tempfile.mkdtemp()), budget=3)
    out = run_python(belt, "import os\nprint(dict(os.environ))")
    assert out["exit_code"] == 0, out["stderr"]
    assert "Canary" not in out["stdout"]
    assert "ANTHROPIC_API_KEY" not in out["stdout"]


def test_the_gate_fires_on_a_planted_credential(tmp_path: Path):
    """Every pattern we claim to detect must actually be detected."""
    samples = {
        "anthropic": "sk-ant-api03-" + "A" * 30,
        "openai": "sk-proj-" + "B" * 30,
        "openrouter": "sk-or-v1-" + "c" * 40,
        "nvidia": "nvapi-" + "D" * 30,
        "xai": "xai-" + "E" * 40,
        "huggingface": "hf_" + "F" * 34,
        "google_oauth": "ya29." + "G" * 40,
        # Assembled from fragments so this test file does not itself trip the
        # gate it is testing - every other sample is already a concatenation.
        "private_key": "-----BEGIN " + "RSA PRIVATE KEY" + "-----",
    }
    assert set(samples) == set(CREDENTIAL_PATTERNS), "a pattern has no test case"
    for name, value in samples.items():
        target = tmp_path / f"{name}.json"
        target.write_text('{"transcript": "' + value + '"}', encoding="utf-8")
        found, _ = _credential_scan(tmp_path, [f"{name}.json"])
        assert any(name in f for f in found), f"{name} slipped past the gate"
        target.unlink()


def test_the_gate_is_quiet_on_clean_data(tmp_path: Path):
    (tmp_path / "clean.json").write_text(
        '{"transcript": "ANTHROPIC_API_KEY is read from the environment"}',
        encoding="utf-8")
    found, _ = _credential_scan(tmp_path, ["clean.json"])
    assert not found


if __name__ == "__main__":
    import subprocess
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
