"""Family: which of two compounds is more potent, when each was measured in a
different assay batch and the linking evidence is partly unusable.

Written against the collaborator critiques (analysis/collab/hardening__gpt.md,
hardening__gemini.md). Their shared diagnosis was that the first families were
"canonical audit recipes with a conspicuous local defect": find the anomaly,
apply the textbook correction, done. The prescription was to ship *several
superficially adequate analyses that imply different decisions, plus data that
make exactly one defensible*. So this family is built so that the textbook
correction is itself a trap:

    analysis 1  compare the two reported IC50 values           -> decision X
    analysis 2  bridge the batches on the reference compounds
                and correct                                    -> decision X
    analysis 3  bridge the batches on the reference compounds
                that are actually measurements                 -> decision Y

Both of the first two are things a competent analyst does. Only the third is
defensible, and it is the only one that reaches the right answer in H1.

The mechanism is censoring, not a typo. Each run fits an IC50 from a fixed
dilution series, so a compound weaker than the top concentration tested has no
midpoint inside the sampled range and the fit returns a compressed
extrapolation: the reported number moves with the truth at a fraction of the
true slope. Six of the nine reference compounds are weaker than the top
concentration in both run-sets, so their batch-to-batch ratio is attenuated to
a fraction of the real batch shift. They are the MAJORITY of the reference
panel, which is why "average the bridges" - a majority vote over ratios that
look mutually consistent - lands on a shift far too small to reverse the naive
comparison. The three references that sit inside the tested range imply a shift
five to seven times larger than the other six do, and the whole task is
deciding which subgroup is evidence.

The conditions are separated by exactly one latent quantity, the batch shift:

  C0  the shift is negligible, so the reported numbers are already comparable
      and the raw ordering is the right answer. Asserting a large shift here is
      a false alarm and fails on the recomputed shift, so the family punishes
      over-correction and under-correction in the same instance shape.
  H1  the shift is large and points against the raw ordering. Raw comparison
      and whole-panel bridging both return the WRONG compound; only the
      in-range bridges recover the true one.
  F2  no compound whatsoever appears in both run-sets. The observation model is
      m(c, b) = theta_c + phi_b, so with a disconnected compound-by-batch
      design the contrast theta_A - theta_B is confounded with phi_B - phi_A
      exactly. The generator emits two parameter vectors that reproduce EVERY
      shipped observation to machine precision and imply opposite winners, so
      the refusal is a provable statement about the design rather than an
      opinion about data quality.

Shape is matched across conditions on purpose: identical filenames, identical
column count, identical row count (62), identical numeric precision, the same
nine reference identifiers in run-set A, the same count of out-of-range
reference values, and the same single aberrant replicate. C0 and H1 share one
noise realisation (common random numbers) and differ only in the shift. Nothing
about which condition an instance is can be read off the surface of the files.

Verification never reads the generator's parameters for the graded quantities.
It re-derives, from the shipped table alone: which compounds link the two
run-sets, which of those are inside the calibrated range, the shift implied by
them, both candidates on one scale, the resulting ratio and the resulting
winner. The generator's beta and gamma are never consulted - a generator and
verifier sharing one wrong assumption agree perfectly and are still wrong.
"""
from __future__ import annotations

import math
import random
import re
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "n/a",
           "null", "not_possible", "not possible", "unknown", "undetermined"}

# target, readout, top concentration of the dilution series in nM
TARGETS = [
    ("MAP4K4 kinase", "ADP-Glo luminescence", 5000.0),
    ("SYK kinase", "TR-FRET 665/615 ratio", 10000.0),
    ("ROCK2 kinase", "ADP-Glo luminescence", 3000.0),
    ("PDE4B hydrolase", "IMAP fluorescence polarisation", 8000.0),
    ("JAK2 kinase", "TR-FRET 665/615 ratio", 6000.0),
    ("MTH1 hydrolase", "malachite green absorbance", 4000.0),
]

N_REF = 9                  # reference compounds per run-set
N_REF_IN_RANGE = 3         # ... of which are inside the tested range
CAND_REPS = 4
REF_REPS = 3
SHIFT_TOL = 0.15           # log10 units, on the reported batch shift
RATIO_TOL_LOG = 0.15       # log10 units, on the reported candidate ratio
MATERIAL_SHIFT = 0.15      # log10; below this the run-sets are comparable


def _fmt(x: float) -> str:
    return format(x, ".1f")


# ------------------------------------------------------------------ generation

def build(seed: int, condition: str) -> Episode:
    # Identity stream: everything that appears in the brief or in the surface
    # of the workspace. Drawn before any branch on condition, so C0, H1 and F2
    # are byte-identical in the brief and identical in file shape.
    rng_id = random.Random(830_000 + seed)
    target, readout, ceiling = TARGETS[seed % len(TARGETS)]
    base = 4100 + 13 * seed
    cand_1, cand_2 = f"CRU-{base + 1}", f"CRU-{base + 6}"
    pool = [f"REF-{k:02d}" for k in range(3, 42)]
    rng_id.shuffle(pool)
    refs_a = sorted(pool[:N_REF])
    refs_b_alt = sorted(pool[N_REF:2 * N_REF])
    lot_a = f"EL-{rng_id.randrange(2100, 2199)}"
    lot_b = f"EL-{rng_id.randrange(2200, 2299)}"
    day_a = rng_id.randrange(4, 16)
    day_b = day_a + rng_id.randrange(9, 21)
    month = rng_id.randrange(2, 9)
    reader = rng_id.choice(["Envision-2104", "PHERAstar-FSX", "Spark-20M"])

    # Latent-parameter stream. Every condition draws the same values in the
    # same order; only which of them is used differs.
    rng_par = random.Random(832_000 + seed)
    L = math.log10(ceiling)
    gamma = round(rng_par.uniform(0.14, 0.20), 3)    # slope of an out-of-range fit
    sigma = round(rng_par.uniform(0.050, 0.070), 4)  # replicate noise, log10
    shift_mag = round(rng_par.uniform(0.62, 0.78), 3)
    sign_shift_h1 = rng_par.choice((1, -1))
    sign_gap_c0 = rng_par.choice((1, -1))
    gap_c0 = round(rng_par.uniform(0.18, 0.26), 3)
    shift_frac_c0 = rng_par.uniform(0.10, 0.30)
    # In-range references sit 20-100x below the top concentration; out-of-range
    # ones sit far enough above it that no shift in play can bring them back
    # inside, so the usable subset is the same three compounds in every
    # condition and the count of out-of-range values never betrays the arm.
    in_range_t = [round(rng_par.uniform(L - 2.00, L - 1.30), 4)
                  for _ in range(N_REF_IN_RANGE)]
    out_range_t = [round(rng_par.uniform(L + 1.10, L + 1.60), 4)
                   for _ in range(N_REF - N_REF_IN_RANGE)]
    alt_in_range_t = [round(rng_par.uniform(L - 2.00, L - 1.30), 4)
                      for _ in range(N_REF_IN_RANGE)]
    alt_out_range_t = [round(rng_par.uniform(L + 1.10, L + 1.60), 4)
                       for _ in range(N_REF - N_REF_IN_RANGE)]
    anchor = round(rng_par.uniform(L - 2.20, L - 1.60), 4)
    which_in_range = rng_par.sample(range(N_REF), N_REF_IN_RANGE)
    aberrant_ref = refs_a[which_in_range[0]]
    aberrant_rep = rng_par.randrange(1, REF_REPS + 1)
    aberration = round(rng_par.uniform(0.34, 0.46), 3)

    # The one latent difference between the arms.
    if condition == "H1":
        # The whole-panel bridge is attenuated to (2/3)(1 - gamma) of the real
        # shift once six of nine references are compressed; the candidate gap
        # is set safely inside that error so BOTH naive analyses land on the
        # wrong side of zero, while the true gap stays many replicate standard
        # errors from a tie.
        shift = shift_mag * sign_shift_h1
        naive_error = (2.0 / 3.0) * (1.0 - gamma) * shift_mag
        gap = round(max(0.17, min(0.26, 0.55 * naive_error)), 3) * -sign_shift_h1
    elif condition == "C0":
        shift = round(gap_c0 * shift_frac_c0, 3) * rng_par.choice((1, -1))
        gap = gap_c0 * sign_gap_c0
    else:
        shift = shift_mag * sign_shift_h1
        gap = gap_c0 * sign_gap_c0

    t_first, t_second = anchor, round(anchor + gap, 4)

    # Noise stream: identical draw order and identical seed in every condition,
    # so C0 and H1 are one realisation apart in the shift alone.
    rng_noise = random.Random(833_000 + seed)

    rows = ["run_set,run_id,compound_id,role,replicate,ic50_nM"]

    def emit(run_set: str, compound: str, role: str, true_log: float,
             n_rep: int, spike_rep: int | None = None) -> None:
        for rep in range(1, n_rep + 1):
            x = true_log + (shift if run_set == "RS-B" else 0.0)
            x += rng_noise.gauss(0.0, sigma)
            if spike_rep == rep:
                x += aberration
            if x > L:
                # No midpoint inside the sampled range: the fit is anchored by
                # the top of the dilution series and returns a compressed
                # extrapolation above it.
                x = L + gamma * (x - L)
            rows.append(f"{run_set},{run_set}-R{rep},{compound},{role},{rep},"
                        f"{_fmt(10.0 ** x)}")

    emit("RS-A", cand_1, "candidate", t_first, CAND_REPS)
    emit("RS-B", cand_2, "candidate", t_second, CAND_REPS)

    ref_t: dict[str, float] = {}
    pool_in, pool_out = list(in_range_t), list(out_range_t)
    for index, ref in enumerate(refs_a):
        ref_t[ref] = pool_in.pop() if index in which_in_range else pool_out.pop()
    for ref in refs_a:
        emit("RS-A", ref, "reference", ref_t[ref], REF_REPS,
             aberrant_rep if ref == aberrant_ref else None)

    if condition == "F2":
        # Same row count, same column count, same number of out-of-range
        # values: only the identifiers differ, and no compound spans the two
        # run-sets. That is the impossibility witness.
        alt_t: dict[str, float] = {}
        pool_in, pool_out = list(alt_in_range_t), list(alt_out_range_t)
        for index, ref in enumerate(refs_b_alt):
            alt_t[ref] = pool_in.pop() if index in which_in_range else pool_out.pop()
        for ref in refs_b_alt:
            emit("RS-B", ref, "reference", alt_t[ref], REF_REPS)
    else:
        for ref in refs_a:
            emit("RS-B", ref, "reference", ref_t[ref], REF_REPS)

    table = "\n".join(rows) + "\n"

    log = [
        f"# Potency record  {target}",
        f"Readout: {readout}.",
        "",
        "Two run-sets are reported in potency_runs.csv.",
        f"  RS-A   enzyme lot {lot_a}   reader {reader}   2026-{month:02d}-{day_a:02d}",
        f"  RS-B   enzyme lot {lot_b}   reader {reader}   2026-{month:02d}-{day_b:02d}",
        "",
        "Compound handling was the same for both run-sets: a 10-point 3-fold",
        f"dilution series with a top concentration of {_fmt(ceiling)} nM and a",
        f"bottom concentration of {_fmt(ceiling / 3.0 ** 9)} nM.",
        "",
        "Each ic50_nM entry is the midpoint returned by the plate fitting",
        "routine for that run; the routine reports a value for every curve it",
        "is given.",
        "",
        "Reference compounds are carried on the plates to follow assay",
        "performance. They are ordinary compounds from the archive and their",
        "potencies span the whole range of the series.",
        "",
        f"To be recorded: which of {cand_1} and {cand_2} is the more potent",
        f"inhibitor of {target}, and by how much.",
    ]
    log_text = "\n".join(log) + "\n"

    brief = (
        f"Two candidate inhibitors of {target}, {cand_1} and {cand_2}, have "
        f"been run in the potency assay. The per-run fitted IC50 values are in "
        f"potency_runs.csv and the assay record is in assay_log.md.\n\n"
        f"Report which candidate is the more potent inhibitor of {target} and "
        f"by how much.\n\n"
        "Submit these fields:\n"
        f"- more_potent_compound: the compound_id of the more potent of the two "
        "candidates, or the string cannot_determine if no defensible answer "
        "exists\n"
        f"- ic50_ratio: {cand_1}'s IC50 divided by {cand_2}'s IC50 with both "
        "candidates placed on one common scale, as a number, or the string "
        "cannot_determine\n"
        "- batch_shift_log10: the systematic difference in reported log10 IC50 "
        "between the two run-sets, signed as RS-B minus RS-A, as a number, or "
        "the string cannot_determine\n"
        "- supporting_compound_ids: the compound_ids whose data you treated as "
        "evidence for how the two run-sets relate, as a comma-separated list, "
        "empty if you relied on none\n"
        "- comparability_basis: what makes the two candidates' numbers "
        "comparable, or why they cannot be compared, in your own words\n"
        "and conf_<field> in [0,1] for each.")

    files = {"potency_runs.csv": table, "assay_log.md": log_text}

    key = {
        "condition": condition,
        "candidates": [cand_1, cand_2],
        "candidate_run_sets": {cand_1: "RS-A", cand_2: "RS-B"},
        "ceiling_nM": ceiling,
        "target": target,
        "linked": condition != "F2",
        "shift_tolerance": SHIFT_TOL,
        "ratio_tolerance_log10": RATIO_TOL_LOG,
    }
    if condition == "F2":
        key["witness"] = _witness(table, cand_1, cand_2)
    else:
        key["witness"] = None

    # 24 calls: reading two files, aggregating replicates, ranking the
    # reference panel against the tested range and re-deriving the comparison
    # takes several rounds of python, and the first aggregation has to be
    # revised once the range check lands.
    return Episode("batch-effect-potency", seed, condition, brief, files, key,
                   budget=24,
                   checkpoints=["bridge_evidence", "batch_shift", "comparison",
                                "ratio"])


def _witness(table: str, cand_1: str, cand_2: str) -> dict:
    """Two parameter vectors that reproduce every shipped observation exactly.

    The observation model is m(c, b) = theta_c + phi_b. With no compound in
    both run-sets, adding d to theta_c for every compound in RS-B and
    subtracting d from phi_B leaves every predicted observation unchanged, so
    theta_1 - theta_2 for a cross-run-set pair is not identified. Mirroring the
    second candidate across the first flips the winner while changing nothing
    that was measured. Computed from the table that was actually written, not
    asserted.
    """
    medians, _ = _medians(table)
    m1 = medians.get((cand_1, "RS-A"))
    m2 = medians.get((cand_2, "RS-B"))
    if m1 is None or m2 is None:
        return {}
    # Mirror the second candidate across the first: same distance, other side.
    phi = round(2.0 * (m2 - m1), 6)
    return {
        "model": "log10 ic50(compound, run_set) = theta_compound + phi_run_set",
        "theta_1": {"phi_RS_A": 0.0, "phi_RS_B": 0.0,
                    "log10_ic50": {cand_1: round(m1, 6), cand_2: round(m2, 6)},
                    "implied_more_potent": cand_1 if m1 < m2 else cand_2},
        "theta_2": {"phi_RS_A": 0.0, "phi_RS_B": phi,
                    "log10_ic50": {cand_1: round(m1, 6),
                                   cand_2: round(m2 - phi, 6)},
                    "implied_more_potent": cand_2 if m1 < m2 else cand_1},
        "note": ("every RS-B compound's theta moves by -phi_RS_B, so all "
                 "predicted observations are identical under both vectors"),
    }


# ---------------------------------------------------------------- verification

def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return float("nan")
    mid = n // 2
    return ordered[mid] if n % 2 else 0.5 * (ordered[mid - 1] + ordered[mid])


def _medians(table: str) -> tuple[dict[tuple[str, str], float], dict]:
    """Per compound and run-set: median log10 IC50 and median raw IC50."""
    grouped: dict[tuple[str, str], list[float]] = {}
    for line in table.strip().splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            continue
        run_set, compound = parts[0], parts[2]
        try:
            value = float(parts[5])
        except ValueError:
            continue
        if value <= 0:
            continue
        grouped.setdefault((compound, run_set), []).append(value)
    medians = {pair: math.log10(_median(vals)) for pair, vals in grouped.items()}
    raw = {pair: _median(vals) for pair, vals in grouped.items()}
    return medians, {"raw": raw}


def _analyse(episode: Episode) -> dict:
    """Re-derive the whole answer from the shipped table.

    Deliberately independent of the generator's shift, compression slope and
    noise: it works from the observables (per-compound medians, the top
    concentration named in the assay record) so that a generator bug shows up
    as a disagreement rather than propagating into the grade.
    """
    key = episode.key
    table = episode.files["potency_runs.csv"]
    medians, extra = _medians(table)
    raw = extra["raw"]
    ceiling = float(key["ceiling_nM"])

    compounds: dict[str, set[str]] = {}
    for compound, run_set in medians:
        compounds.setdefault(compound, set()).add(run_set)
    candidates = list(key["candidates"])
    shared = sorted(c for c, sets in compounds.items()
                    if len(sets) >= 2 and c not in candidates)
    # A fitted midpoint above the top concentration tested is an extrapolation,
    # not a measurement, so it cannot carry a batch-to-batch ratio.
    in_range = {c for c in shared
                if all(raw[(c, rs)] <= ceiling for rs in compounds[c])}
    usable = sorted(in_range)

    per_compound = {c: round(medians[(c, "RS-B")] - medians[(c, "RS-A")], 4)
                    for c in shared
                    if (c, "RS-A") in medians and (c, "RS-B") in medians}
    shift = _median([per_compound[c] for c in usable]) if usable else None
    whole_panel = _median(list(per_compound.values())) if per_compound else None

    out: dict = {
        "shared_compounds": shared,
        "usable_bridges": usable,
        "excluded_out_of_range": sorted(set(shared) - in_range),
        "per_compound_shift": per_compound,
        "shift_recomputed": None if shift is None else round(shift, 4),
        "whole_panel_shift": None if whole_panel is None else round(whole_panel, 4),
        "identifiable": bool(usable),
        "ceiling_nM": ceiling,
    }

    if shift is None:
        out["ratio_log10"] = None
        out["more_potent"] = None
        return out

    def on_a_scale(compound: str) -> float | None:
        for run_set in ("RS-A", "RS-B"):
            if (compound, run_set) in medians:
                value = medians[(compound, run_set)]
                return value - (shift if run_set == "RS-B" else 0.0)
        return None

    first, second = candidates
    a, b = on_a_scale(first), on_a_scale(second)
    if a is None or b is None:
        out["ratio_log10"] = None
        out["more_potent"] = None
        return out
    out["ratio_log10"] = round(a - b, 4)
    out["adjusted_log10"] = {first: round(a, 4), second: round(b, 4)}
    out["more_potent"] = second if a > b else first
    return out


_NUM = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def _num(raw) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).replace(",", "").strip()
    if text.lower() in ABSTAIN:
        return None
    found = _NUM.search(text)
    return float(found.group()) if found else None


def _is_abstention(raw) -> bool:
    text = str(raw if raw is not None else "").strip().lower()
    if not text:
        return False        # silence is not a refusal
    if text in ABSTAIN:
        return True
    return any(phrase in text for phrase in
               ("cannot be determined", "cannot determine", "not determinable",
                "cannot be established", "no defensible", "not identifiable",
                "not possible"))


def _canon(text: str) -> str:
    """One spelling per identifier: REF-04, ref 04 and REF4 are one compound."""
    squashed = re.sub(r"[^A-Z0-9]", "", str(text).upper())
    return re.sub(r"(?<=[A-Z])0+(?=\d)", "", squashed)


def _ids(raw, exclude: set[str]) -> set[str]:
    if raw is None:
        return set()
    parts = [str(x) for x in raw] if isinstance(raw, (list, tuple, set)) \
        else re.split(r"[,;/|\s]+", str(raw))
    out = set()
    for part in parts:
        token = part.strip().strip("[]()'\"")
        if not token or token.lower() in ABSTAIN:
            continue
        if any(ch.isdigit() for ch in token) and any(ch.isalpha() for ch in token):
            out.add(_canon(token))
    return {t for t in out if t not in exclude}


# Phrasings that mention an explanation only in order to rule it out. Plain
# literal removal on purpose: a regex for exactly this failed silently in situ
# on the chain track while passing in isolation, and a scoring rule that cannot
# be checked by eye is a liability.
NEGATED = (
    "not confounded", "is not confounded", "no confounding", "not a confound",
    "not unidentifiable", "not non-identifiable", "is identifiable",
    "are identifiable", "not unidentified",
    "there is no shortage of shared", "not the absence of shared",
    "compounds do appear in both", "compound does appear in both",
    "compounds appear in both", "shared compounds are present",
    "there are shared compounds", "there are common compounds",
    "common compounds are present", "bridging compounds are present",
    "there are bridging compounds",
)

REFUSAL_REASON = (
    "no compound", "no shared", "no common", "no reference in common",
    "no overlap", "does not appear in both", "do not appear in both",
    "appears in only one", "appear in only one", "only in one run-set",
    "disjoint", "no bridg", "nothing links", "no link", "cannot be linked",
    "not linked", "confound", "not identifiab", "non-identifiab",
    "nonidentifiab", "unidentifiab", "cannot be separated",
    "cannot separate", "indistinguishable", "no way to place",
    "cannot be placed on", "no common scale",
)


def _drop_negated(text: str) -> str:
    lowered = text.lower()
    for phrase in NEGATED:
        lowered = lowered.replace(phrase, " ")
    return lowered


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    order = ["bridge_evidence", "batch_shift", "comparison", "ratio"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, order[0])

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    truth = _analyse(episode)
    detail.update({k: truth[k] for k in
                   ("shared_compounds", "usable_bridges", "excluded_out_of_range",
                    "shift_recomputed", "whole_panel_shift", "ratio_log10",
                    "more_potent", "identifiable")})

    candidate_ids = {_canon(c) for c in key["candidates"]}
    claimed = _ids(field("supporting_compound_ids"), candidate_ids)
    basis = str(field("comparability_basis") or "").strip()
    detail["claimed_bridges"] = sorted(claimed)

    if not truth["identifiable"]:
        # F2: nothing links the run-sets, so the cross-run-set contrast is
        # confounded with the run-set effect exactly. A documented refusal is
        # the only defensible outcome, and silence is not a refusal.
        reason = _drop_negated(basis + " " + str(submitted.get("reasoning", "")))
        names_reason = any(w in reason for w in REFUSAL_REASON)
        winner_out = _is_abstention(field("more_potent_compound"))
        shift_out = _is_abstention(field("batch_shift_log10"))
        ratio_out = _is_abstention(field("ic50_ratio"))
        checks["bridge_evidence"] = winner_out and not claimed
        checks["batch_shift"] = shift_out
        checks["ratio"] = ratio_out
        checks["comparison"] = winner_out and bool(basis) and names_reason
        detail["expected"] = ("refusal: no compound is measured in both "
                              "run-sets, so the candidate contrast is "
                              "confounded with the run-set effect")
        detail["witness"] = key.get("witness")
        detail["witness_holds"] = _witness_holds(episode)
        detail["stated_basis"] = basis[:220]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    # 1. Which compounds were treated as linking evidence. The whole panel of
    #    shared references looks self-consistent and is the majority, so
    #    claiming all of them fails on precision; the answer is the subset
    #    whose fitted midpoints are inside the concentration range tested.
    usable = {_canon(c) for c in truth["usable_bridges"]}
    precision = len(claimed & usable) / len(claimed) if claimed else 0.0
    recall = len(claimed & usable) / len(usable) if usable else 0.0
    checks["bridge_evidence"] = bool(claimed) and precision >= 0.75 and recall >= 0.5
    detail["bridge_precision"] = round(precision, 3)
    detail["bridge_recall"] = round(recall, 3)

    # 2. Honesty of the reported shift, recomputed from the usable bridges. In
    #    C0 the recomputed value is near zero, so an invented batch effect
    #    fails here even when the decision survives it.
    given_shift = _num(field("batch_shift_log10"))
    checks["batch_shift"] = (given_shift is not None
                             and abs(given_shift - truth["shift_recomputed"])
                             <= SHIFT_TOL)
    detail["given_shift"] = given_shift

    # 3. The decision.
    given_winner = str(field("more_potent_compound") or "").strip()
    checks["comparison"] = (bool(given_winner) and bool(basis)
                            and _canon(given_winner) == _canon(truth["more_potent"]))
    detail["given_more_potent"] = given_winner
    detail["stated_basis"] = basis[:220]

    # 4. The magnitude, signed, so a correction applied with the wrong sign or
    #    a comparison of raw numbers cannot pass on magnitude alone.
    given_ratio = _num(field("ic50_ratio"))
    if given_ratio is not None and given_ratio > 0:
        gap = abs(math.log10(given_ratio) - truth["ratio_log10"])
        checks["ratio"] = gap <= RATIO_TOL_LOG
        detail["given_ratio_log10"] = round(math.log10(given_ratio), 4)
    else:
        detail["given_ratio_log10"] = None
    detail["expected_ratio"] = round(10.0 ** truth["ratio_log10"], 4)

    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


def _witness_holds(episode: Episode) -> bool:
    """Do the two F2 parameter vectors really reproduce the same observations?

    Recorded in the verdict detail so that a broken witness is visible rather
    than assumed: the refusal is only defensible if the two vectors are
    genuinely observationally equivalent and genuinely disagree.
    """
    witness = episode.key.get("witness") or {}
    theta_1, theta_2 = witness.get("theta_1"), witness.get("theta_2")
    if not theta_1 or not theta_2:
        return False
    medians, _ = _medians(episode.files["potency_runs.csv"])
    # The design property that frees phi: no compound spans the two run-sets.
    spans: dict[str, set[str]] = {}
    for compound, run_set in medians:
        spans.setdefault(compound, set()).add(run_set)
    if any(len(sets) > 1 for sets in spans.values()):
        return False
    worst = 0.0
    for theta in (theta_1, theta_2):
        for compound, value in theta["log10_ic50"].items():
            run_set = next(iter(spans.get(compound, {""})))
            phi = theta["phi_RS_B"] if run_set == "RS-B" else theta["phi_RS_A"]
            observed = medians.get((compound, run_set))
            if observed is None:
                return False
            worst = max(worst, abs((value + phi) - observed))
    return (worst < 1e-6
            and theta_1["log10_ic50"] != theta_2["log10_ic50"]
            and theta_1["implied_more_potent"] != theta_2["implied_more_potent"])


def reference_submission(episode: Episode) -> dict:
    """The submission a competent analyst would make.

    Derived by re-deriving the answer from the shipped table - the same route a
    candidate has to take - so B8 shows the task is solvable from the workspace
    rather than from the key.
    """
    key = episode.key
    truth = _analyse(episode)
    first, second = key["candidates"]

    if not truth["identifiable"]:
        return {
            "more_potent_compound": "cannot_determine",
            "ic50_ratio": "cannot_determine",
            "batch_shift_log10": "cannot_determine",
            "supporting_compound_ids": "",
            "comparability_basis": (
                f"no compound is measured in both run-sets: RS-A and RS-B "
                f"share no identifier, so nothing links the two scales. "
                f"{first} is only in RS-A and {second} only in RS-B, and any "
                f"difference between them is confounded with the run-set "
                f"effect - moving every RS-B potency by a constant and moving "
                f"the run-set effect by the same constant reproduces every "
                f"reported value exactly and reverses which candidate wins, so "
                f"the comparison is not identifiable from these data"),
            "conf_more_potent_compound": 0.9, "conf_ic50_ratio": 0.9,
            "conf_batch_shift_log10": 0.9,
            "conf_supporting_compound_ids": 0.9,
            "conf_comparability_basis": 0.9,
        }

    shift = truth["shift_recomputed"]
    ratio = round(10.0 ** truth["ratio_log10"], 4)
    excluded = truth["excluded_out_of_range"]
    material = abs(shift) > MATERIAL_SHIFT
    if material:
        story = (f"the reference compounds whose fitted midpoints fall inside "
                 f"the concentration range tested read {abs(shift):.2f} log10 "
                 f"units {'higher' if shift > 0 else 'lower'} in RS-B than in "
                 f"RS-A, so the two run-sets are on different scales and the "
                 f"reported numbers cannot be compared as they stand")
    else:
        story = (f"the reference compounds whose fitted midpoints fall inside "
                 f"the concentration range tested agree between RS-B and RS-A "
                 f"to within {abs(shift):.2f} log10 units, so the reported "
                 f"numbers are already on one scale")
    return {
        "more_potent_compound": truth["more_potent"],
        "ic50_ratio": ratio,
        "batch_shift_log10": shift,
        "supporting_compound_ids": ",".join(truth["usable_bridges"]),
        "comparability_basis": (
            story + f". The remaining reference values ({', '.join(excluded)}) "
            f"sit above the top concentration of the dilution series, so those "
            f"midpoints are extrapolations rather than measurements and the "
            f"ratios built from them are compressed towards zero; they are not "
            f"evidence about the run-sets. After that adjustment "
            f"{truth['more_potent']} is the more potent of the two, by "
            f"{max(ratio, 1.0 / ratio):.2f}-fold"),
        "conf_more_potent_compound": 0.85, "conf_ic50_ratio": 0.8,
        "conf_batch_shift_log10": 0.8, "conf_supporting_compound_ids": 0.85,
        "conf_comparability_basis": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
