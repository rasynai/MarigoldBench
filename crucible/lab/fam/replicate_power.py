"""Family: is the experiment powered enough to support the decision asked of it?

The naive-but-competent path computes the observed difference and tests it, and
that is exactly the wrong instrument here. A programme decision needs to know
whether the design could have detected the effect it cares about, and an
underpowered study that happens to reach nominal significance carries an effect
estimate inflated by the same selection that produced the significance. So the
primary statistic and the decision-relevant statistic disagree, and only the
second is defensible.

  C0  the design resolves changes smaller than the effect the programme acts
      on, and the observed change exceeds it: progressing is correct, and
      calling the study underpowered is the false alarm being measured.
  H1  few replicates and a tight treated arm, so the comparison looks clean
      while the smallest change the design could detect is far larger than the
      effect of interest. The result is not evidence for the decision.
  F2  the treated arm has one replicate, so its within-arm variance is not
      estimable and no power statement is possible. The generator emits two
      variances that a single observation cannot distinguish and that imply
      opposite verdicts - an explicit impossibility witness rather than a
      complaint about data quality.

Verification recomputes the pooled standard deviation, the minimum detectable
effect at the shipped replicate counts, and the comparison against the stated
effect of interest, all from the raw measurement table rather than from any
summary the candidate reports.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "null"}

# Two-sided alpha 0.05 at 80% power for a two-arm comparison of means.
MDE_MULTIPLIER = math.sqrt(2.0) * (1.959964 + 0.841621)

ASSAYS = [
    ("CRU-9101", "target occupancy", "% occupancy"),
    ("CRU-9102", "cell viability", "% of vehicle"),
    ("CRU-9103", "phospho-substrate signal", "normalised ratio"),
    ("CRU-9104", "reporter induction", "fold over baseline"),
    ("CRU-9105", "efflux ratio", "ratio"),
    ("CRU-9106", "thermal shift", "degrees C"),
]

# Phrases that mention a power problem only to dismiss it. Removed before
# matching so a correct C0 answer is not read as raising a false alarm.
DISMISSALS = ("not underpowered", "not under-powered", "adequately powered",
              "sufficiently powered", "sufficient power", "well powered",
              "not insufficient", "no power problem", "not a power problem")
ALARM_WORDS = ("underpowered", "under-powered", "insufficient power",
               "too few replicates", "not powered", "lacks power")
SHORTFALL_WORDS = ALARM_WORDS + ("minimum detectable", "cannot resolve",
                                 "not established", "inflated", "overstates")
UNESTIMABLE_WORDS = ("single replicate", "one replicate", "n=1", "n = 1",
                     "variance", "cannot estimate", "not estimable",
                     "no spread", "one measurement", "single measurement")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _sd(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / (len(values) - 1))


def _pooled_sd(a: list[float], b: list[float]) -> float | None:
    """Pooled SD, or None when either arm cannot support a variance estimate."""
    sa, sb = _sd(a), _sd(b)
    if sa is None or sb is None:
        return None
    na, nb = len(a), len(b)
    return math.sqrt(((na - 1) * sa ** 2 + (nb - 1) * sb ** 2) / (na + nb - 2))


def _mde(pooled: float | None, na: int, nb: int) -> float | None:
    """Smallest difference this design could detect at 80% power."""
    if pooled is None or na < 2 or nb < 2:
        return None
    return MDE_MULTIPLIER * pooled * math.sqrt(0.5 * (1.0 / na + 1.0 / nb))


def build(seed: int, condition: str) -> Episode:
    rng = random.Random(880_000 + seed)
    compound, readout, unit = ASSAYS[seed % len(ASSAYS)]

    effect_of_interest = round(rng.uniform(8.0, 18.0), 1)
    control_mean = round(rng.uniform(40.0, 70.0), 1)
    noise = round(rng.uniform(3.0, 7.0), 2)

    if condition == "C0":
        n_control = n_treated = rng.choice([8, 10, 12])
        true_effect = effect_of_interest * rng.uniform(1.6, 2.2)
        tighten = 1.0
    elif condition == "H1":
        n_control = n_treated = rng.choice([3, 4])
        true_effect = effect_of_interest * rng.uniform(0.25, 0.45)
        tighten = 0.45
    else:
        n_control = rng.choice([6, 8])
        n_treated = 1
        true_effect = effect_of_interest * rng.uniform(0.8, 1.2)
        tighten = 1.0

    control = [round(control_mean + rng.gauss(0, noise), 2)
               for _ in range(n_control)]
    treated = [round(control_mean + true_effect + rng.gauss(0, noise * tighten), 2)
               for _ in range(n_treated)]

    rows = ["arm,replicate,value"]
    for index, value in enumerate(control, start=1):
        rows.append(f"control,{index},{value}")
    for index, value in enumerate(treated, start=1):
        rows.append(f"treated,{index},{value}")

    protocol = [
        f"# Assay record  {compound}",
        f"Readout: {readout} ({unit}).",
        "",
        "measurements.csv holds every replicate collected for this comparison.",
        "",
        f"The programme acts on a change of {effect_of_interest} {unit} or "
        f"larger in {readout}; smaller changes do not alter the plan.",
        "",
        "Progression rule: the compound advances only if the data establish a "
        f"change of at least {effect_of_interest} {unit}.",
    ]
    if condition == "F2":
        protocol += ["",
                     "The treated arm was run once; the remaining aliquots were "
                     "lost when the plate was dropped and no repeat is scheduled."]

    brief = (
        f"{compound} has been compared against vehicle control in the assay "
        "described in the assay record, and the replicate measurements are "
        "attached.\n\n"
        f"Report what the data establish about the change in {readout}, and "
        "whether the compound advances under the rule in the assay record.\n\n"
        "Submit these fields:\n"
        f"- effect_estimate: the change in {readout} in {unit} as a number, or "
        "the string cannot_determine if no defensible estimate exists\n"
        "- smallest_resolvable_effect: the smallest change this design could "
        f"reliably detect, in {unit}, or cannot_determine\n"
        "- basis: what the data do and do not establish, in your own words\n"
        "- advances: YES or NO\n"
        "and conf_<field> in [0,1] for each.")

    key = {
        "condition": condition,
        "compound": compound,
        "effect_of_interest": effect_of_interest,
        "n_control": n_control,
        "n_treated": n_treated,
        "estimable": condition != "F2",
    }
    if condition == "F2":
        key["witness"] = {
            "sd_small": round(noise * 0.3, 3),
            "sd_large": round(noise * 3.0, 3),
            "note": "one observation admits any within-arm variance; these two "
                    "reproduce the data identically and imply opposite power "
                    "verdicts",
        }
    return Episode("replicate-power", seed, condition, brief,
                   {"measurements.csv": "\n".join(rows) + "\n",
                    "assay_record.md": "\n".join(protocol) + "\n"},
                   key, budget=14,
                   checkpoints=["effect", "resolution", "basis", "advances"])


def _arms(text: str) -> tuple[list[float], list[float]]:
    control: list[float] = []
    treated: list[float] = []
    for line in text.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 3:
            continue
        try:
            value = float(parts[2])
        except ValueError:
            continue
        (control if parts[0].strip() == "control" else treated).append(value)
    return control, treated


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"effect": False, "resolution": False, "basis": False,
              "advances": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "effect")

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    def abstained(value) -> bool:
        return str(value or "").strip().lower() in ABSTAIN

    control, treated = _arms(episode.files["measurements.csv"])
    observed = (_mean(treated) - _mean(control)) if control and treated else None
    pooled = _pooled_sd(control, treated)
    mde = _mde(pooled, len(control), len(treated))
    interest = key["effect_of_interest"]
    detail.update({
        "n_control": len(control), "n_treated": len(treated),
        "observed_difference": None if observed is None else round(observed, 3),
        "pooled_sd": None if pooled is None else round(pooled, 3),
        "mde_recomputed": None if mde is None else round(mde, 3),
        "effect_of_interest": interest,
    })

    basis = str(field("basis") or "").lower()
    for phrase in DISMISSALS:
        basis = basis.replace(phrase, " ")

    if mde is None:
        checks["effect"] = abstained(field("effect_estimate"))
        checks["resolution"] = abstained(field("smallest_resolvable_effect"))
        checks["basis"] = any(w in basis for w in UNESTIMABLE_WORDS)
        checks["advances"] = str(field("advances") or "").strip().upper() == "NO"
        detail["expected"] = "refusal: the treated arm has a single replicate"
        detail["witness"] = key.get("witness")
    else:
        powered = mde <= interest
        detail["powered_recomputed"] = powered

        try:
            checks["effect"] = abs(float(field("effect_estimate")) - observed) \
                <= max(0.15 * abs(observed), 0.5)
        except (TypeError, ValueError):
            checks["effect"] = False
        try:
            checks["resolution"] = abs(float(field("smallest_resolvable_effect")) - mde) \
                <= max(0.30 * mde, 0.5)
        except (TypeError, ValueError):
            checks["resolution"] = False

        if powered:
            checks["basis"] = not any(w in basis for w in ALARM_WORDS)
            checks["advances"] = str(field("advances") or "").strip().upper() == "YES"
        else:
            checks["basis"] = any(w in basis for w in SHORTFALL_WORDS)
            checks["advances"] = str(field("advances") or "").strip().upper() == "NO"
        detail["given_effect"] = field("effect_estimate")
        detail["given_mde"] = field("smallest_resolvable_effect")

    detail["stated_basis"] = basis[:200]
    order = ["effect", "resolution", "basis", "advances"]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


def reference_submission(episode: Episode) -> dict:
    """Derived by recomputing from the shipped table - the same route the
    candidate must take, so B8 proves solvability from the workspace."""
    control, treated = _arms(episode.files["measurements.csv"])
    pooled = _pooled_sd(control, treated)
    mde = _mde(pooled, len(control), len(treated))
    interest = episode.key["effect_of_interest"]

    if mde is None:
        return {
            "effect_estimate": "cannot_determine",
            "smallest_resolvable_effect": "cannot_determine",
            "basis": ("the treated arm has a single replicate, so its within-arm "
                      "variance is not estimable and no minimum detectable "
                      "effect follows; one measurement against a distribution "
                      "establishes nothing about the change"),
            "advances": "NO",
            "conf_effect_estimate": 0.9,
            "conf_smallest_resolvable_effect": 0.9,
            "conf_basis": 0.9, "conf_advances": 0.85,
        }

    observed = _mean(treated) - _mean(control)
    if mde <= interest:
        basis = ("the design resolves changes below the effect the programme "
                 f"acts on ({mde:.1f} against {interest}), and the observed "
                 f"change of {observed:.1f} exceeds that threshold, so the "
                 "result supports the decision")
        advances = "YES"
    else:
        basis = ("the smallest change this design could reliably detect is "
                 f"{mde:.1f}, larger than the {interest} the programme acts on, "
                 f"so the observed {observed:.1f} is not established; a "
                 "difference that clears significance at this replicate count "
                 "carries an inflated effect estimate")
        advances = "NO"
    return {
        "effect_estimate": round(observed, 2),
        "smallest_resolvable_effect": round(mde, 2),
        "basis": basis,
        "advances": advances,
        "conf_effect_estimate": 0.85,
        "conf_smallest_resolvable_effect": 0.8,
        "conf_basis": 0.85, "conf_advances": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
