"""Simulated laboratory: a benign cross-coupling yield response surface.

Source class SIMULATOR (guide 19.2). This module IS the truth zone for
Tracks D and E: the hidden coefficients below are never shown to any evaluated
system - agents see only the disclosed historical measurements returned by
`disclosed_measurements()`. Per the guide's claim boundaries, results on this
surface are "simulator-based experimental design", never real-world discovery.

The surface is deterministic; replicate noise is a pure hash of the condition
and replicate seed, so every outcome is exactly reproducible.
"""
from __future__ import annotations

import hashlib
import math

TEMP_RANGE = (40.0, 120.0)
CATALYSTS = ("Pd-A", "Pd-B", "Ni-C")
SOLVENTS = ("DMF", "toluene", "ethanol")
SUCCESS_THRESHOLD = 70.0  # percent yield

# ---- HIDDEN TRUTH (never disclosed to evaluated systems) -------------------
_BASE = {
    ("Pd-A", "DMF"): 45.0, ("Pd-A", "toluene"): 38.0, ("Pd-A", "ethanol"): 30.0,
    ("Pd-B", "DMF"): 62.0, ("Pd-B", "toluene"): 48.0, ("Pd-B", "ethanol"): 40.0,
    ("Ni-C", "DMF"): 35.0, ("Ni-C", "toluene"): 42.0, ("Ni-C", "ethanol"): 25.0,
}
_TEMP_OPT = {"Pd-A": 70.0, "Pd-B": 95.0, "Ni-C": 110.0}
_TEMP_AMP = 18.0
_TEMP_WIDTH = 15.0
_NOISE_SD = 1.2
# Only the Pd-B/DMF region can exceed the 70% threshold (max ~80% at 95 C).
# ---------------------------------------------------------------------------


def _noise(temp_c: float, catalyst: str, solvent: str, replicate_seed: int) -> float:
    key = f"{temp_c:.2f}|{catalyst}|{solvent}|{replicate_seed}".encode()
    digest = hashlib.sha256(key).digest()
    uniform = int.from_bytes(digest[:8], "big") / 2**64  # [0, 1)
    # Map to approximately normal via inverse-ish transform (sum of uniforms).
    uniform2 = int.from_bytes(digest[8:16], "big") / 2**64
    gaussian = math.sqrt(-2 * math.log(max(uniform, 1e-12))) * math.cos(2 * math.pi * uniform2)
    return gaussian * _NOISE_SD


def valid_condition(temp_c: float, catalyst: str, solvent: str) -> bool:
    return (
        TEMP_RANGE[0] <= temp_c <= TEMP_RANGE[1]
        and catalyst in CATALYSTS
        and solvent in SOLVENTS
    )


def simulate(temp_c: float, catalyst: str, solvent: str, replicate_seed: int = 1) -> float:
    """Measured percent yield for one experiment (deterministic)."""
    if not valid_condition(temp_c, catalyst, solvent):
        raise ValueError(f"condition outside the registered space: {temp_c}, {catalyst}, {solvent}")
    base = _BASE[(catalyst, solvent)]
    bump = _TEMP_AMP * math.exp(-((temp_c - _TEMP_OPT[catalyst]) ** 2) / (2 * _TEMP_WIDTH**2))
    value = base + bump + _noise(temp_c, catalyst, solvent, replicate_seed)
    return round(max(0.0, min(100.0, value)), 1)


DISCLOSED_CONDITIONS = [
    (50.0, "Pd-B", "DMF"),
    (70.0, "Pd-A", "DMF"),
    (80.0, "Pd-B", "toluene"),
    (90.0, "Pd-A", "ethanol"),
    (100.0, "Ni-C", "DMF"),
    (110.0, "Ni-C", "toluene"),
]


def disclosed_measurements() -> list[dict]:
    """Historical data every arm receives. None exceeds the threshold."""
    return [
        {
            "temp_c": temp,
            "catalyst": catalyst,
            "solvent": solvent,
            "yield_percent": simulate(temp, catalyst, solvent, replicate_seed=0),
        }
        for temp, catalyst, solvent in DISCLOSED_CONDITIONS
    ]


def disclosed_prompt() -> str:
    lines = [
        "Reaction system: benign C-C cross-coupling of substrate S1 (fixed substrate and product).",
        f"Tunable conditions: temperature {TEMP_RANGE[0]:.0f}-{TEMP_RANGE[1]:.0f} C, "
        f"catalyst in {list(CATALYSTS)}, solvent in {list(SOLVENTS)}.",
        f"Goal: find conditions with isolated yield >= {SUCCESS_THRESHOLD:.0f}%.",
        "Historical screening data (single runs):",
    ]
    for m in disclosed_measurements():
        lines.append(
            f"  T={m['temp_c']:.0f} C, catalyst={m['catalyst']}, solvent={m['solvent']}"
            f" -> {m['yield_percent']:.1f}% yield"
        )
    return "\n".join(lines)
