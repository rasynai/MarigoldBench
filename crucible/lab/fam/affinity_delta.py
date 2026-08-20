"""Family: affinity-delta - is a claimed potency gain larger than the assay's noise?

The single most common SAR decision in a medicinal chemistry programme is
"analogue B beats parent A, grow round 4 from B". It is made on IC50 values
that drift several-fold between runs, and the literature on agent failures is
blunt about the shape of the mistake: BixBench's measured failures are skipped
assumption checks and unhandled data-quality issues, and Coscientist's are
successful tool calls whose science is wrong. Neither looks like a traceback.
Comparing the mean IC50 of A with the mean IC50 of B and reporting the ratio is
exactly such a call: it is arithmetic, it always produces a number, and it
carries no information about whether the number survives the assay's own
run-to-run variation.

So the episode ships every run the pair has been on, each run carrying the
system-suitability control that the assay's release record says decides whether
that run counts at all.

  C0  the export is sound. Some runs drifted far enough that the control fell
      outside the release window, but the pair moves together on a plate, so
      dropping those runs changes nothing: the verdict is the same with or
      without them. Two flavours by seed - the analogue is genuinely more
      potent, or the difference is inside the run-to-run spread - so
      "not established" is not a tell for a defect.
  H1  the runs whose control failed are the runs that carry the whole gain: a
      lot problem moved the analogue relative to the parent on those plates
      only. Every released run says the pair is a wash. The naive route -
      average both compounds over everything and take the ratio - reports a
      real-looking improvement at p < 0.05 and is wrong.
  F2  the pair has been on exactly one run, one curve each. A single paired
      difference has no spread, so no estimate of the assay's noise exists and
      the observed fold change cannot be separated from ordinary run drift.
      A documented refusal is the only correct outcome.

C0 and H1 briefs are byte-identical, and so are assay_spec.txt and
series_memo.txt; the entire difference is in the numbers in potency_runs.csv.

Truth is constructed: the generator fabricates the runs, writes the CSV,
parses its own rounded bytes back and runs the paired test on them, redrawing
until the recomputed statistics meet the condition's margins. verify() runs the
identical recomputation on the shipped bytes - re-reading the release window
out of the spec file, re-deciding which runs are usable, refitting the paired
statistic and the noise - and grades against that. Every number the candidate
reports is recomputed; none of them is taken as evidence for itself.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import math
import re
from pathlib import Path

from ..families import Episode, Verdict

DATA_FILE = "potency_runs.csv"
SPEC_FILE = "assay_spec.txt"
MEMO_FILE = "series_memo.txt"

ALPHA = 0.05
# Fewer paired runs than this leaves nothing to estimate a spread from, so no
# comparison against noise is possible at all.
MIN_PAIRED_RUNS = 2
# A fold change counts as the same answer inside this band. The band already
# spans the defensible point estimates (geometric mean of the per-run ratios,
# their median, their arithmetic mean); the tolerance sits on top of it and is
# far narrower than the shift the planted defect produces.
FOLD_TOLERANCE = 0.08
# The spread is graded across both the sample and population conventions.
SD_TOLERANCE = 0.15

ABSTAIN = {"cannot_determine", "cannot determine", "cannot-determine",
           "cannot_be_determined", "not_determined", "not determined",
           "not determinable", "indeterminate", "undetermined", "unknown",
           "insufficient_data", "insufficient", "nd", "n/a", "n_a", "na",
           "none", "null", "-"}
_ESTABLISHED = {"established", "real", "genuine", "yes", "true", "significant",
                "supported", "confirmed"}
_NOT_ESTABLISHED = {"not_established", "unestablished", "not_supported",
                    "unsupported", "no", "false", "not_significant",
                    "not_real", "not_confirmed", "not_proven"}

TARGETS = [
    ("PI3Kdelta", "ADP-Glo luminescence", "CRU"),
    ("JAK1 JH1", "LANCE Ultra TR-FRET", "CRD"),
    ("MAP4K1 (HPK1)", "ADP-Glo luminescence", "CRE"),
    ("PARP7", "AlphaScreen mono-ADP-ribosylation", "CRG"),
    ("SOS1:KRAS interface", "HTRF displacement", "CRH"),
    ("CDK12/cyclin K", "ADP-Glo luminescence", "CRK"),
    ("WRN helicase", "FRET strand-separation", "CRM"),
]

MODIFICATIONS = [
    ("4-fluoro to 4-chloro on the aniline", "a deeper halogen contact in the "
     "back pocket"),
    ("N-methyl to N-cyclopropyl on the amide", "a hydrophobic contact against "
     "the gatekeeper"),
    ("added a 3-hydroxyl on the pyrrolidine", "a hydrogen bond to the hinge "
     "carbonyl"),
    ("pyridine to pyrimidine in the head group", "a second hinge hydrogen bond"),
    ("added a methyl at the benzylic centre", "a conformational lock on the "
     "bound rotamer"),
    ("carboxamide to sulfonamide", "a stronger interaction with the catalytic "
     "lysine"),
]

CONTROLS = [("REF-STA", "staurosporine"), ("REF-TOF", "tofacitinib"),
            ("REF-NIR", "niraparib"), ("REF-DIN", "dinaciclib")]


# ---------------------------------------------------------------------------
# recomputation: build() and verify() both go through exactly these functions

def _parse_spec(text: str) -> dict:
    """Read the pair, the control and the release window out of the spec file."""
    pair = re.search(r"parent (\S+), analogue (\S+)", text)
    control = re.search(r"reference control: (\S+) on every plate", text)
    window = re.search(r"IC50 falls between ([0-9.]+) and ([0-9.]+) nM", text)
    if not (pair and control and window):
        raise ValueError("assay spec does not state the pair, the control and "
                         "the release window")
    low, high = float(window.group(1)), float(window.group(2))
    if not 0 < low < high:
        raise ValueError("release window is not an interval")
    return {"parent": pair.group(1), "analogue": pair.group(2),
            "control": control.group(1), "low": low, "high": high}


def _parse_runs(text: str) -> tuple[list[str], dict[str, dict], dict[str, str]]:
    order: list[str] = []
    table: dict[str, dict[str, float]] = {}
    dates: dict[str, str] = {}
    for row in csv.DictReader(io.StringIO(text)):
        run = str(row.get("run_id") or "").strip()
        compound = str(row.get("compound_id") or "").strip()
        if not run or not compound:
            continue
        try:
            value = float(row.get("ic50_nM"))
        except (TypeError, ValueError):
            continue
        if not (value > 0):
            continue
        if run not in table:
            table[run] = {}
            order.append(run)
            dates[run] = str(row.get("run_date") or "").strip()
        table[run][compound] = value
    return order, table, dates


def _summary(subset: list[dict]) -> dict:
    """Paired statistics over a set of runs, all of which carry both compounds."""
    import numpy as np
    from scipy import stats

    out: dict = {"n": len(subset), "mean": None, "fold": None,
                 "fold_band": None, "sd_sample": None, "sd_pop": None,
                 "p": None, "t": None, "verdict": "cannot_determine"}
    if not subset:
        return out
    deltas = np.array([r["delta"] for r in subset], dtype=float)
    out["mean"] = float(deltas.mean())
    out["fold"] = float(10.0 ** out["mean"])
    ratios = 10.0 ** deltas
    # Three conventions a competent analyst might quote for "how many times
    # more potent": the geometric mean of the per-run ratios, their median and
    # their arithmetic mean. The band spans all three so that a defensible
    # reading is never punished for being a different defensible reading.
    band = sorted([out["fold"], float(10.0 ** np.median(deltas)),
                   float(ratios.mean())])
    out["fold_band"] = (band[0], band[-1])
    if len(subset) < MIN_PAIRED_RUNS:
        return out
    out["sd_sample"] = float(deltas.std(ddof=1))
    out["sd_pop"] = float(deltas.std(ddof=0))
    parent = np.array([math.log10(r["parent"]) for r in subset])
    analogue = np.array([math.log10(r["analogue"]) for r in subset])
    result = stats.ttest_rel(parent, analogue)
    p = float(result.pvalue)
    out["p"] = p if math.isfinite(p) else 1.0
    out["t"] = float(result.statistic) if math.isfinite(result.statistic) else 0.0
    out["verdict"] = ("established" if (out["p"] < ALPHA and out["mean"] > 0)
                      else "not_established")
    return out


def _analyse(csv_text: str, spec: dict) -> dict:
    """The canonical recomputation, run on the shipped bytes and nothing else."""
    import numpy as np

    order, table, dates = _parse_runs(csv_text)
    runs: list[dict] = []
    for run in order:
        values = table[run]
        control = values.get(spec["control"])
        parent = values.get(spec["parent"])
        analogue = values.get(spec["analogue"])
        released = control is not None and spec["low"] <= control <= spec["high"]
        paired = parent is not None and analogue is not None
        runs.append({
            "run_id": run, "date": dates.get(run, ""), "control": control,
            "released": released, "paired": paired,
            "parent": parent, "analogue": analogue,
            # positive delta = the analogue needs less compound = more potent
            "delta": math.log10(parent / analogue) if paired else None})

    used = [r for r in runs if r["paired"] and r["released"]]
    every = [r for r in runs if r["paired"]]
    held = [r["run_id"] for r in runs if not r["released"]]
    unpaired = [r["run_id"] for r in runs if not r["paired"]]

    # Spread of the parent's own IC50 across released runs. This is the number
    # a candidate reaches for when it forgets the design is paired; it is
    # carried for the margins and the audit trail, never graded.
    parent_logs = [math.log10(r["parent"]) for r in runs
                   if r["released"] and r["parent"]]
    sd_individual = (float(np.std(np.array(parent_logs), ddof=1))
                     if len(parent_logs) > 1 else None)

    used_stats = _summary(used)
    all_stats = _summary(every)
    return {"runs": runs, "n_runs": len(runs), "used": used_stats,
            "all": all_stats, "held_runs": held, "unpaired_runs": unpaired,
            "sd_individual": sd_individual, "verdict": used_stats["verdict"]}


# ---------------------------------------------------------------------------
# generation

class _Retry(Exception):
    """This draw missed the intended margins; take another."""


def _fmt(value: float) -> str:
    """Three significant figures, the way a curve-fitting package writes them."""
    if value >= 100.0:
        return f"{value:.0f}"
    if value >= 10.0:
        return f"{value:.1f}"
    return f"{value:.2f}"


def _episode_parameters(seed: int) -> dict:
    """Everything the candidate can see that does NOT depend on the condition.

    Drawn from a seed-only generator so that the spec, the memo and the brief
    are byte-identical across C0, H1 and F2 for a given seed.
    """
    import numpy as np

    rng = np.random.default_rng([90_210, seed])
    target, readout, code = TARGETS[seed % len(TARGETS)]
    modification, interaction = MODIFICATIONS[seed % len(MODIFICATIONS)]
    control_id, control_name = CONTROLS[seed % len(CONTROLS)]

    base = 100 + int(rng.integers(0, 780))
    parent = f"{code}-{base:04d}"
    analogue = f"{code}-{base + int(rng.integers(3, 40)):04d}"

    n_runs = int(rng.choice([12, 13, 14, 15]))
    # A held stretch is a bad reagent lot, so the failing runs are consecutive.
    n_held = 4 if n_runs == 12 else 5
    held_start = int(rng.integers(1, n_runs - n_held - 1))
    held = set(range(held_start, held_start + n_held))
    # One run on which only the parent was plated: the analogue was not
    # available that day. It carries no paired difference whatever its control
    # says, so the release window is not the only thing that makes a run count.
    spare = [i for i in range(n_runs) if i not in held]
    incomplete = int(spare[int(rng.integers(0, len(spare)))])

    # Control window: the assay releases a run when the control lands within
    # three-fold of its historical value either way.
    control_centre = float(rng.uniform(8.0, 24.0))
    half_width = 0.48
    low = float(f"{control_centre * 10 ** -half_width:.3g}")
    high = float(f"{control_centre * 10 ** half_width:.3g}")

    start = dt.date(2026, 1, 8) + dt.timedelta(days=int(rng.integers(0, 40)))
    dates, cursor = [], start
    for i in range(n_runs):
        dates.append(cursor.isoformat())
        cursor += dt.timedelta(days=2 + (i % 3))

    return {
        "target": target, "readout": readout, "modification": modification,
        "interaction": interaction, "control_id": control_id,
        "control_name": control_name, "parent": parent, "analogue": analogue,
        "n_runs": n_runs, "held": sorted(held), "incomplete": incomplete,
        "control_centre": control_centre, "low": low, "high": high,
        "dates": dates, "committee": (start + dt.timedelta(days=70)).isoformat(),
        "flavour": "real" if seed % 2 else "flat",
        "parent_ic50": float(rng.uniform(28.0, 240.0)),
    }


def _draw(rng, params: dict, condition: str, flavour: str) -> str:
    """Fabricate one export and render it exactly as the candidate will read it."""
    import numpy as np

    control_id, parent_id = params["control_id"], params["parent"]
    analogue_id = params["analogue"]
    mu_control = math.log10(params["control_centre"])
    mu_parent = math.log10(params["parent_ic50"])

    tau = float(rng.uniform(0.14, 0.20))        # run-to-run plate drift, log10
    sigma = float(rng.uniform(0.028, 0.048))    # within-run curve-to-curve noise
    clip = 0.30                                 # released runs stay inside the window

    if condition == "F2":
        # One run, one curve per compound, and a gain worth being tempted by.
        gain = float(rng.uniform(0.42, 0.62))
        rows = [f"R01,{params['dates'][0]},{parent_id},"
                f"{_fmt(10 ** (mu_parent + sigma * rng.standard_normal()))}",
                f"R01,{params['dates'][0]},{analogue_id},"
                f"{_fmt(10 ** (mu_parent - gain + sigma * rng.standard_normal()))}",
                f"R01,{params['dates'][0]},{control_id},"
                f"{_fmt(10 ** (mu_control + 0.06 * rng.standard_normal()))}"]
        return "run_id,run_date,compound_id,ic50_nM\n" + "\n".join(rows) + "\n"

    if flavour == "real":
        gain = float(rng.uniform(0.26, 0.38))
    else:
        gain = float(rng.uniform(-0.02, 0.04))
    # H1 only: on the plates the lot problem spoiled, the analogue reads far
    # ahead of the parent. The control on those same plates is what gives the
    # run away, and the released runs are untouched.
    lot_shift = float(rng.uniform(0.30, 0.50)) if condition == "H1" else 0.0

    held = set(params["held"])
    lines = ["run_id,run_date,compound_id,ic50_nM"]
    for i in range(params["n_runs"]):
        run = f"R{i + 1:02d}"
        date = params["dates"][i]
        if i in held:
            # The whole plate drifts, which is why the control fails; a plate
            # drift on its own moves the pair together and cancels.
            offset = float(rng.uniform(0.66, 0.86))
            shift = lot_shift
        else:
            offset = float(np.clip(tau * rng.standard_normal(), -clip, clip))
            shift = 0.0
        parent_value = 10 ** (mu_parent + offset + sigma * rng.standard_normal())
        analogue_value = 10 ** (mu_parent - gain - shift + offset
                                + sigma * rng.standard_normal())
        control_value = 10 ** (mu_control + offset + 0.5 * sigma * rng.standard_normal())
        lines.append(f"{run},{date},{parent_id},{_fmt(parent_value)}")
        if i != params["incomplete"]:
            lines.append(f"{run},{date},{analogue_id},{_fmt(analogue_value)}")
        lines.append(f"{run},{date},{control_id},{_fmt(control_value)}")
    return "\n".join(lines) + "\n"


def _margins_ok(condition: str, flavour: str, params: dict, stats: dict) -> bool:
    """The constructed-truth contract, written as inequalities on recomputation."""
    used, every = stats["used"], stats["all"]

    if condition == "F2":
        return (used["n"] == 1 and stats["verdict"] == "cannot_determine"
                and used["fold"] is not None and used["fold"] >= 2.0)

    expected_used = params["n_runs"] - len(params["held"]) - 1
    if used["n"] != expected_used or every["n"] != params["n_runs"] - 1:
        return False
    if len(stats["held_runs"]) != len(params["held"]):
        return False
    if stats["sd_individual"] is None or used["sd_sample"] is None:
        return False
    # The spread of the parent's own IC50 and the spread of the paired
    # difference have to be plainly different numbers, or the family cannot
    # tell a paired analysis from an unpaired one.
    if stats["sd_individual"] < 2.0 * used["sd_sample"]:
        return False

    if condition == "H1":
        return (stats["verdict"] == "not_established"
                and every["verdict"] == "established"
                and used["p"] >= 0.25 and every["p"] <= 0.035
                and every["mean"] - used["mean"] >= 0.10
                and every["sd_sample"] >= 1.5 * used["sd_sample"]
                and used["fold"] <= 1.25)

    # C0: the held runs are a red herring. Dropping them has to leave the
    # verdict where it was, so asserting that they drive the result is a false
    # alarm rather than a finding.
    if every["verdict"] != stats["verdict"]:
        return False
    if abs(every["mean"] - used["mean"]) > 0.05:
        return False
    if flavour == "real":
        return (stats["verdict"] == "established" and used["p"] <= 0.002
                and used["mean"] >= 0.24)
    return (stats["verdict"] == "not_established" and used["p"] >= 0.25
            and abs(used["mean"]) <= 0.05)


def _make_files(seed: int, condition: str) -> tuple[dict, str, dict, dict]:
    """Draw until the recomputed statistics land inside the intended margins."""
    import numpy as np

    params = _episode_parameters(seed)
    flavour = params["flavour"] if condition == "C0" else condition
    spec = {"parent": params["parent"], "analogue": params["analogue"],
            "control": params["control_id"], "low": params["low"],
            "high": params["high"]}
    code = {"C0": 1, "H1": 2, "F2": 3}[condition]

    for attempt in range(600):
        rng = np.random.default_rng([41_017, seed, code, attempt])
        text = _draw(rng, params, condition, flavour)
        stats = _analyse(text, _parse_spec(_spec_text(params)))
        if _margins_ok(condition, flavour, params, stats):
            return params, text, spec, stats
    raise RuntimeError(f"affinity-delta: no draw met the margins for seed {seed} "
                       f"condition {condition}")


def _spec_text(params: dict) -> str:
    return (
        f"{params['target']} biochemical assay - release record\n"
        f"readout: {params['readout']}\n"
        f"potency: fitted IC50 in nM, 10-point curve in duplicate wells, one\n"
        f"  curve per compound per run\n"
        f"pair under test: parent {params['parent']}, analogue "
        f"{params['analogue']}\n"
        f"reference control: {params['control_id']} on every plate "
        f"({params['control_name']}).\n"
        f"  A run is released only when its {params['control_id']} IC50 falls "
        f"between {params['low']:g} and {params['high']:g} nM. A run outside "
        f"that\n  window is not released and its compound results do not carry "
        f"into a\n  potency comparison.\n"
        f"scheduling: the pair and the control go on one plate per run; runs "
        f"are on\n  separate days with independently prepared reagent lots, "
        f"cell passages\n  and substrate batches.\n"
        f"export: {DATA_FILE} lists every run this pair has been on, released "
        f"or not.\n")


def _memo_text(params: dict) -> str:
    return (
        f"Series memo - {params['target']} programme, round 3\n"
        f"\n"
        f"{params['analogue']} is the round-3 analogue of {params['parent']}: "
        f"{params['modification']},\nmade to pick up {params['interaction']}. "
        f"Nothing else in the scaffold changed.\n"
        f"\n"
        f"Round 4 grows from whichever of the two we commit to, and the "
        f"portfolio\ncommittee meets on {params['committee']}. The potency work "
        f"on the pair is\nfinished: {DATA_FILE} is the export and {SPEC_FILE} "
        f"is the assay's release record.\n"
        f"Chemistry has no further material for either compound this quarter.\n")


BRIEF = """{parent} and {analogue} are the parent and the round-3 analogue in the
{target} series. {data} is every potency measurement the assay has produced for
the pair, {spec} is the assay's own release record, and {memo} is the chemistry
note the next round hangs on.

Establish whether {analogue} is genuinely more potent than {parent} in this
assay, and report what you find.

Submit these fields:
- n_runs_used: integer, how many assay runs contributed to your comparison
- fold_improvement: number, how many times more potent {analogue} is than
  {parent} across those runs; below 1 if it is weaker
- delta_sd_log10: number, the run-to-run standard deviation of that per-run
  potency difference in log10 units, or the string cannot_determine if this
  dataset does not support one
- improvement_verdict: established, not_established, or cannot_determine
- explanation: in your own words, what this dataset does and does not support
Report n_runs_used and fold_improvement in every case, whatever your verdict
is, and give conf_<field> in [0,1] for each field."""


def build(seed: int, condition: str) -> Episode:
    params, text, spec, stats = _make_files(seed, condition)

    files = {DATA_FILE: text, SPEC_FILE: _spec_text(params),
             MEMO_FILE: _memo_text(params)}
    brief = BRIEF.format(parent=params["parent"], analogue=params["analogue"],
                         target=params["target"], data=DATA_FILE,
                         spec=SPEC_FILE, memo=MEMO_FILE)

    used, every = stats["used"], stats["all"]
    key = {
        "condition": condition,
        "flavour": params["flavour"] if condition == "C0" else condition,
        "parent": params["parent"], "analogue": params["analogue"],
        "control": params["control_id"],
        "release_window_nM": [params["low"], params["high"]],
        "verdict": stats["verdict"],
        "n_runs": stats["n_runs"],
        "n_runs_used": used["n"],
        "held_runs": stats["held_runs"],
        "unpaired_runs": stats["unpaired_runs"],
        "mean_delta_log10": round(used["mean"], 6),
        "fold_used": round(used["fold"], 6),
        "delta_sd_log10": (None if used["sd_sample"] is None
                           else round(used["sd_sample"], 6)),
        "p_paired": None if used["p"] is None else round(used["p"], 6),
        # The naive route, kept for audit: every paired run, released or not.
        "naive_fold_all_runs": None if every["fold"] is None else round(every["fold"], 6),
        "naive_p_all_runs": None if every["p"] is None else round(every["p"], 6),
        "naive_verdict_all_runs": every["verdict"],
        "sd_individual_log10": (None if stats["sd_individual"] is None
                                else round(stats["sd_individual"], 6)),
        "defect": ("none" if condition != "H1"
                   else "held_runs_carry_the_apparent_gain"),
    }
    return Episode("affinity-delta", seed, condition, brief, files, key,
                   budget=12,
                   checkpoints=["runs_used", "effect_size", "noise", "verdict",
                                "attribution"])


# ---------------------------------------------------------------------------
# scoring: everything below re-derives the answer from the shipped files

def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.strip().lower().replace(",", "")
    text = text.replace("fold", " ").replace("x", " ").replace("~", " ")
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    return float(match.group()) if match else None


def _is_abstention(value) -> bool:
    if not isinstance(value, str):
        return False
    token = value.strip().lower().replace("-", "_").replace(" ", "_").strip("_.")
    if token in {t.replace(" ", "_").replace("-", "_") for t in ABSTAIN}:
        return True
    return any(word in token for word in
               ("cannot", "can_not", "unable", "insufficient", "undetermin",
                "indetermin", "not_estimable", "no_estimate"))


def _normalise_verdict(raw) -> str | None:
    token = str(raw or "").strip().lower()
    token = token.replace("-", "_").replace(" ", "_").replace("/", "_").strip("_.")
    if not token:
        # An omitted field is not a documented refusal and never scores as one.
        return None
    if token in _NOT_ESTABLISHED:
        return "not_established"
    if token in _ESTABLISHED:
        return "established"
    if _is_abstention(token):
        return "cannot_determine"
    # Free-form phrasing: order matters, "not established" contains
    # "established" and "not significant" contains "significant".
    if (token.startswith("not") or token.startswith("no_")
            or "not_establish" in token or "not_support" in token
            or "not_signif" in token or "unsupported" in token
            or "within_noise" in token or "inconclusive" in token):
        return "not_established"
    if any(word in token for word in
           ("establish", "support", "signif", "real", "genuine", "confirm")):
        return "established"
    return None


_WORD_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                 "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
                 "fifteen": 15}
# A run reference, in the forms a report actually writes them: "R07",
# "run 7", "runs 5, 6 and 7", "plate 12".
_RUN_REF = re.compile(r"(?:\br|\bruns?\s*#?\s*|\bplates?\s*#?\s*)-?0*(\d{1,2})\b",
                      re.I)


def _mentioned_numbers(text: str) -> set[int]:
    """Every count a candidate wrote, with decimals stripped first.

    Without stripping, "p = 0.05" would donate a 5 and credit a candidate with
    a held run it never looked at.
    """
    cleaned = re.sub(r"\d+\.\d+", " ", text.lower())
    found = {int(m) for m in re.findall(r"\d{1,3}", cleaned)}
    return found | {v for word, v in _WORD_NUMBERS.items()
                    if re.search(rf"\b{word}\b", cleaned)}


def _run_numbers(text: str) -> set[int]:
    """The runs a candidate actually pointed at, as opposed to any integer."""
    cleaned = re.sub(r"\d+\.\d+", " ", text)
    return {int(m) for m in _RUN_REF.findall(cleaned)}


_CONTROL_WORDS = ("control", "release", "not released", "unreleased", "held",
                  "out of spec", "out-of-spec", "outside the window",
                  "suitability", "qc", "failed run", "invalid run")
_SINGLE_RUN_WORDS = ("single run", "one run", "1 run", "only one", "only a "
                     "single", "single plate", "one plate", "no replicate",
                     "not replicated", "unreplicated", "without replication",
                     "single measurement", "one measurement", "single paired",
                     "one paired", "n=1", "n = 1", "no independent",
                     "single occasion", "only once")


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["runs_used", "effect_size", "noise", "verdict", "attribution"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, "runs_used")

    def field(*names):
        wanted = {n.lower() for n in names}
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") in wanted:
                return value
        return None

    # Re-derive everything from the shipped bytes. The workspace copy is
    # compared but never trusted: run_python can rewrite anything in there and
    # a rewritten export must not be able to move the answer.
    try:
        spec = _parse_spec(episode.files[SPEC_FILE])
        stats = _analyse(episode.files[DATA_FILE], spec)
    except Exception as exc:  # noqa: BLE001 - a broken episode is not a pass
        return Verdict(False, checks,
                       {"error": f"shipped files unreadable: {exc}"}, "runs_used")

    on_disk = None
    path = Path(workspace) / DATA_FILE
    if path.exists():
        on_disk = path.read_text(encoding="utf-8", errors="replace")
    detail["workspace_export_matches_shipped"] = (on_disk == episode.files[DATA_FILE])

    used, every = stats["used"], stats["all"]
    detail["recomputed"] = {
        "n_runs": stats["n_runs"], "n_runs_used": used["n"],
        "held_runs": stats["held_runs"], "unpaired_runs": stats["unpaired_runs"],
        "mean_delta_log10": None if used["mean"] is None else round(used["mean"], 5),
        "fold_used": None if used["fold"] is None else round(used["fold"], 5),
        "delta_sd_log10": (None if used["sd_sample"] is None
                           else round(used["sd_sample"], 5)),
        "p_paired": None if used["p"] is None else round(used["p"], 5),
        "verdict": stats["verdict"],
        "all_runs_fold": None if every["fold"] is None else round(every["fold"], 5),
        "all_runs_p": None if every["p"] is None else round(every["p"], 5),
        "all_runs_verdict": every["verdict"]}
    detail["key_verdict"] = episode.key.get("verdict")
    detail["key_agrees_with_recomputation"] = (
        episode.key.get("verdict") == stats["verdict"]
        and episode.key.get("n_runs_used") == used["n"])

    # 1. Which runs count. A run counts when the release record says it was
    #    released AND it carries both compounds; over-excluding on a hunch
    #    fails here exactly as under-excluding does.
    given_runs = _number(field("n_runs_used", "n_runs", "runs_used",
                               "n_runs_included", "n_used_runs"))
    checks["runs_used"] = (given_runs is not None
                           and int(round(given_runs)) == used["n"])
    detail["n_runs_used_given"] = field("n_runs_used")

    # 2. The effect, recomputed on those runs.
    given_fold = _number(field("fold_improvement", "fold_change", "fold",
                               "potency_fold", "fold_gain"))
    if used["fold_band"] is None:
        checks["effect_size"] = False
        detail["fold_band"] = None
    else:
        low = used["fold_band"][0] * (1.0 - FOLD_TOLERANCE)
        high = used["fold_band"][1] * (1.0 + FOLD_TOLERANCE)
        checks["effect_size"] = given_fold is not None and low <= given_fold <= high
        detail["fold_band"] = [round(low, 4), round(high, 4)]
    detail["fold_given"] = field("fold_improvement")

    # 3. The noise the effect has to be measured against. With fewer than two
    #    paired runs there is no spread to report and the refusal has to be
    #    stated: an absent field is not a documented refusal.
    raw_sd = field("delta_sd_log10", "delta_sd", "sd_log10", "sd_delta_log10",
                   "delta_sd_log", "log10_sd")
    given_sd = None if _is_abstention(raw_sd) else _number(raw_sd)
    if used["sd_sample"] is None:
        checks["noise"] = _is_abstention(raw_sd)
        detail["sd_band"] = None
        detail["expected_noise"] = "stated refusal (no spread exists in one run)"
    else:
        low = min(used["sd_pop"], used["sd_sample"]) * (1.0 - SD_TOLERANCE)
        high = max(used["sd_pop"], used["sd_sample"]) * (1.0 + SD_TOLERANCE)
        checks["noise"] = given_sd is not None and low <= given_sd <= high
        detail["sd_band"] = [round(low, 5), round(high, 5)]
        detail["sd_of_parent_alone"] = (None if stats["sd_individual"] is None
                                        else round(stats["sd_individual"], 5))
    detail["sd_given"] = raw_sd

    # 4. The call, graded against the recomputed paired test on the runs that
    #    count.
    given_verdict = _normalise_verdict(field("improvement_verdict", "verdict",
                                             "call", "decision", "conclusion"))
    checks["verdict"] = given_verdict == stats["verdict"]
    detail["verdict_given"] = field("improvement_verdict")
    detail["verdict_expected"] = stats["verdict"]

    # 5. Attribution, and only where recomputation says there is something to
    #    attribute. Two cases are gradeable without a judge: the runs the assay
    #    did not release change the verdict (the candidate has to say so and
    #    say which), or no spread exists at all (the refusal has to be
    #    documented, not merely declared in a one-word field).
    stated = str(field("explanation", "reasoning", "rationale", "notes") or "")
    lowered = stated.lower()
    if used["n"] < MIN_PAIRED_RUNS:
        checks["attribution"] = any(w in lowered for w in _SINGLE_RUN_WORDS)
        detail["attribution_expected"] = "the refusal, documented in prose"
    elif every["verdict"] != stats["verdict"]:
        held_numbers = {int(re.sub(r"\D", "", r) or -1) for r in stats["held_runs"]}
        mentioned = _mentioned_numbers(stated)
        named = held_numbers & _run_numbers(stated)
        # Naming the runs is the clearest way to attribute the effect, but
        # stating how many were held is the same finding in different prose and
        # is accepted as such.
        counted = len(stats["held_runs"]) in mentioned
        checks["attribution"] = ((bool(named) or counted)
                                 and any(w in lowered for w in _CONTROL_WORDS))
        detail["attribution_expected"] = sorted(stats["held_runs"])
        detail["attribution_named"] = sorted(named)
    else:
        # Nothing is wrong with this export, so there is nothing to name and
        # the check is carried - the false-alarm cost lands on n_runs_used.
        checks["attribution"] = True
        detail["attribution_expected"] = None
    detail["explanation_given"] = stated[:300]

    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


# ---------------------------------------------------------------------------
# reference

def _reference_explanation(stats: dict, spec: dict, key: dict) -> str:
    used, every = stats["used"], stats["all"]
    held = sorted(stats["held_runs"])
    window = f"{spec['low']:g}-{spec['high']:g} nM"

    if used["n"] < MIN_PAIRED_RUNS:
        run = stats["runs"][0]["run_id"] if stats["runs"] else "the one run"
        return (
            f"Only one run ({run}) exists for this pair, with a single IC50 per "
            f"compound, so there is exactly one paired difference and it has no "
            f"spread. The assay's own run-to-run variation cannot be estimated "
            f"from this dataset at any confidence, and the {used['fold']:.2f}-fold "
            f"the single plate shows cannot be separated from the drift one "
            f"plate carries: {spec['control']} was inside the {window} release "
            f"window on this run, which says the plate behaved, not that the "
            f"pair differs. No re-reading of this plate fixes that. The pair has "
            f"to go on further independent runs before the question can be "
            f"answered.")

    held_text = ", ".join(held) if held else "none"
    if every["verdict"] != stats["verdict"]:
        return (
            f"Runs {held_text} were not released: their {spec['control']} IC50 "
            f"sits outside the {window} window the release record sets, so by "
            f"that record their compound results do not carry. Those are exactly "
            f"the runs on which {spec['analogue']} reads ahead of "
            f"{spec['parent']}. Across the {used['n']} released, paired runs the "
            f"per-run difference averages {used['mean']:.3f} log10 - a fold "
            f"change of {used['fold']:.2f} - against a run-to-run spread of "
            f"{used['sd_sample']:.3f} log10, and the paired test over those runs "
            f"gives p={used['p']:.3f}. Pooling all {every['n']} paired runs "
            f"instead, held ones included, gives {every['fold']:.2f}-fold at "
            f"p={every['p']:.4f}; that apparent gain is carried entirely by runs "
            f"the assay itself rejected, and it is not evidence about the "
            f"compounds. The designed potency gain is not established.")

    common = (
        f"Runs {held_text} were not released - {spec['control']} outside the "
        f"{window} window - and one further run carries only {spec['parent']}, "
        f"so {used['n']} of the {stats['n_runs']} runs give a usable paired "
        f"comparison. On those the per-run difference averages "
        f"{used['mean']:.3f} log10, a fold change of {used['fold']:.2f}, with a "
        f"run-to-run spread of {used['sd_sample']:.3f} log10 and a paired test "
        f"p={used['p']:.4g}. ")
    if stats["verdict"] == "established":
        return common + (
            f"The difference is far larger than the run-to-run spread and holds "
            f"in the same direction on the released runs, so the gain is real "
            f"at this assay's noise level. Absolute IC50 values drift between "
            f"plates - the parent alone varies with a spread of "
            f"{stats['sd_individual']:.3f} log10 across released runs - which is "
            f"why the comparison is made within a plate rather than between "
            f"plate averages. Including the held runs does not change the call "
            f"({every['fold']:.2f}-fold, p={every['p']:.4g}); they are a plate "
            f"drift that moves both compounds together, not a difference between "
            f"the compounds.")
    return common + (
        f"That difference is inside the run-to-run spread: the parent alone "
        f"varies with a spread of {stats['sd_individual']:.3f} log10 between "
        f"plates, and the paired difference is not distinguishable from zero at "
        f"alpha={ALPHA}. Including the held runs does not change the call either "
        f"({every['fold']:.2f}-fold, p={every['p']:.4g}) - the plate drift that "
        f"failed their control moves both compounds together and cancels in the "
        f"pair. The designed gain is not established by this dataset; nothing in "
        f"the export is broken, there simply is no effect to see.")


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make.

    Every graded number is one the verifier re-derives from the shipped export,
    so it is re-derived here the same way - by reading the release window out of
    the spec, deciding which runs carry a usable paired comparison, and running
    the paired statistic on those - never by quoting a stored constant. The key
    supplies only the verdict, so that a disagreement between the constructed
    truth and the recomputation fails B8 loudly instead of passing silently.
    """
    spec = _parse_spec(episode.files[SPEC_FILE])
    stats = _analyse(episode.files[DATA_FILE], spec)
    used = stats["used"]
    key = episode.key

    if key["verdict"] != stats["verdict"]:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: the key says "
            f"{key['verdict']} but the shipped export recomputes to "
            f"{stats['verdict']}")
    if used["fold"] is None:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: the shipped export "
            f"carries no usable paired run, so no candidate could answer")

    answer = {
        "n_runs_used": used["n"],
        "fold_improvement": round(used["fold"], 4),
        "improvement_verdict": key["verdict"],
        "explanation": _reference_explanation(stats, spec, key),
        "conf_n_runs_used": 0.95,
        "conf_fold_improvement": 0.85,
        "conf_delta_sd_log10": 0.85,
        "conf_improvement_verdict": 0.85,
        "conf_explanation": 0.8,
    }
    if used["sd_sample"] is None:
        # One paired difference has no spread; the refusal is stated, not left
        # blank, because a blank field is not a refusal.
        answer["delta_sd_log10"] = "cannot_determine"
        answer["conf_delta_sd_log10"] = 0.95
    else:
        answer["delta_sd_log10"] = round(used["sd_sample"], 4)
    return answer


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
