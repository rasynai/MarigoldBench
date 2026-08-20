"""The OpenRouter ceiling must be able to fire.

CORR-008 was a spend guard that read $0.00 through 1,151 calls because it
summed a field nothing wrote. A ceiling with no test that trips it is that bug
waiting to happen again, so these tests assert the guard's two halves: that a
per-call cost recorded by the gateway is the number we bank, and that spend on
ONE OpenRouter system counts against the others.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crucible.lab.campaign import (LABEL, OPENROUTER_CEILING_USD,
                                   OPENROUTER_SYSTEMS, episode_cost,
                                   openrouter_spend)


def test_gateway_cost_is_preferred_over_the_price_table():
    """A billed number wins; the table is only a fallback."""
    billed = episode_cost("deepseek", {"billed_usd": 0.4242,
                                       "input_tokens": 10_000_000})
    assert billed == 0.4242
    estimated = episode_cost("deepseek", {"input_tokens": 1_000_000,
                                          "output_tokens": 0})
    assert 0.6 < estimated < 0.7          # the $0.66/Mtok fallback


def test_spend_on_one_system_counts_against_every_other(tmp_path: Path):
    """One ceiling, shared. Two systems at $60 each must trip a $95 cap."""
    for name in OPENROUTER_SYSTEMS[:2]:
        folder = tmp_path / "runs" / LABEL / "systems" / name / "outcomes"
        folder.mkdir(parents=True)
        (folder / "e.json").write_text(json.dumps({"cost_usd": 60.0}),
                                       encoding="utf-8")
    total = openrouter_spend(tmp_path)
    assert total == 120.0
    assert total >= OPENROUTER_CEILING_USD, "a shared ceiling that cannot fire"


def test_censored_episodes_are_charged(tmp_path: Path):
    """An episode that died still burned tokens; it must count."""
    name = OPENROUTER_SYSTEMS[0]
    root = tmp_path / "runs" / LABEL / "systems" / name
    (root / "censored").mkdir(parents=True)
    (root / "censored" / "e.json").write_text(json.dumps({"cost_usd": 7.5}),
                                              encoding="utf-8")
    assert openrouter_spend(tmp_path) == 7.5


if __name__ == "__main__":
    import subprocess
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
