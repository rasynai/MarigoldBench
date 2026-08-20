"""Family: an honest uncertainty from an ensemble that agrees for the wrong reason.

Written against the collaborator critique of the first family batch
(analysis/collab/hardening__gpt.md and hardening__gemini.md), which diagnosed
the saturation exactly: the early families were "canonical audit recipes with a
conspicuous local defect", and frontier models execute those reliably. The
prescription was to stop hiding an answer and instead ship *several
superficially adequate analyses that imply different decisions, plus controls
that make exactly one of them defensible*.

THE SCIENCE

An eight-member potency ensemble has scored a round of purchasable candidates,
and the programme's rule is the one every real programme ends up with: nominate
a compound only if the lower end of a predictive interval on its predicted
pIC50 clears the bar. So the task is not the point prediction. It is the
interval, and the interval is where the field's standard move is a category
error: member-to-member spread is treated as a 1-sigma uncertainty. Spread is
epistemic *variance*, not error. Deep ensembles are documented to agree most
tightly exactly where they are extrapolating, because the members share a
training distribution and therefore share a shortcut; when that happens the
narrow spread is not a certificate, it is the symptom.

Nothing here is hidden. Every number a candidate needs is in the two shipped
CSVs, and every route through them is a route a competent modeller takes. The
routes disagree:

  * report the ensemble mean and its standard deviation across members - the
    two columns the prediction service already provides, arithmetically correct
    to the last decimal - and nominate the best candidate that clears the bar.
    This is the naive-but-competent pipeline. Measured over seeds 11-16: in H1
    it nominates the wrong compound, on an interval 16 to 21 times too narrow,
    and it overstates how many candidates the rule permits. It scores nothing
    on every H1 instance, and in C0 - where its nomination, its interval and
    its count are all correct - it still cannot show why, so it scores four of
    five there rather than five.
  * use the winning member's own validation RMSE as the uncertainty, taking the
    manifest at its word. Wrong in H1 (it keeps the trap compound) and wrong in
    C0 as well, where it admits a wide-spread candidate the rule excludes, so
    the family punishes this route in the clean condition too.
  * pool the whole calibration set into one residual RMSE and apply it to every
    candidate. Right about the nomination in C0 and wrong about the interval
    there by a factor of six to nine; in H1 it keeps the trap compound and is
    wrong about both.
  * condition the residual RMSE on the member spread the ensemble actually
    reported for the compound in hand. Only this one is right in every
    condition, and it is right for the reason the calibration set demonstrates
    rather than by assumption.

WHAT MAKES EXACTLY ONE ANALYSIS DEFENSIBLE

`calibration_predictions.csv` carries the same eight members' predictions for
thirty compounds that reached the assay after the last member finished
training, with the measured pIC50 beside them. That file is present in every
condition with the same filename, the same twelve columns, the same thirty rows
and the same numeric precision; only its values differ. It is the only thing
that can license a spread-to-error conversion, and it does so per spread
regime, which is what separates the conditions:

  C0  the spread is a usable uncertainty. Residual magnitude rises with member
      spread across the calibration set (Pearson r above +0.5, asserted at
      build time), the ensemble is mildly overconfident by a constant factor,
      and the naive nomination is the right one. Declaring a problem here is a
      false alarm and fails: refusing, or inflating the interval past two and a
      half times the defensible half-width, or reporting the count that the
      manifest route implies, all lose.
  H1  byte-identical brief. Byte-identical `candidate_predictions.csv`,
      `model_manifest.csv` and `nomination_sop.md` - the entire condition lives
      in the thirty measured values of the calibration file, so there is no
      surface on which the two conditions differ. There the relationship runs
      the other way (Pearson r below -0.5): the compounds the members agree on
      most tightly carry the largest measured errors, and the compounds they
      spread on are the ones they get right. The POOLED residual RMSE is
      constructed to be the same as C0's to within 0.02 log units, so the
      global diagnostic cannot tell the conditions apart either; only the
      spread-conditional one can. The consequence is that the highest-scoring
      candidates - the ones with the tightest agreement - are the ones whose
      intervals straddle the bar, a lower-scoring candidate with honest
      epistemic spread is the only defensible nomination, and a wide-spread
      candidate the naive route rejects becomes admissible. Every naive route
      nominates the wrong compound and reports the wrong count.
  F2  the flaw is structural and the witness is an identity. Every member
      column is the same column: the ensemble is one checkpoint served eight
      times, so the spread is exactly zero on every row, candidates and
      calibration compounds alike. The estimator the rule needs is therefore
      not merely noisy, it is constant - and the calibration file contains two
      compounds with identical (zero) spread whose measured errors differ by
      more than two log units, so spread-to-error is provably not a function
      here. The generator additionally screens that no candidate clears the bar
      under the pooled residual RMSE either, which closes the one escape route
      a resourceful candidate could take, so refusal is the only defensible
      outcome under every reading of the data rather than under one of them.

CONSTRUCTED TRUTH, MEASURED NOT ASSERTED

The generator owns the layout: where each compound sits in (predicted potency,
member spread) space, and how large the measured error is at each spread. It
does not own the answer. `_analyse` re-derives the nomination from the shipped
bytes - the mean and sample standard deviation of the eight member columns, the
residual RMSE of the calibration compounds nearest in spread, the resulting
90% half-width, the lower bound, the count that clears the bar - and `build`
refuses to emit an instance until that recomputation returns the intended
pattern with every candidate at least 0.15 log units clear of the bar, the
naive routes demonstrably wrong, and the two conditions' pooled RMSEs matched.
`verify` calls the same recomputation on the same bytes, so a generator bug
surfaces as a build-time failure rather than as a silently wrong key.

The screen also enforces that the answer does not depend on taste. Five ways of
turning a group of measured residuals into a 90% half-width - RMSE times the
normal quantile, two sigma, the sample standard deviation, a scaled median
absolute deviation, the empirical upper decile - must return the SAME nomination
and the same count, and every candidate's nearest calibration compounds must be
the same set whether they are grouped by nearest neighbour at any k up to ten or
by equal-count terciles of the shipped spreads. An earlier layout with unequal
regime sizes and touching bands failed that check on two seeds in six, which
would have made those instances a coin toss between two defensible
implementations of one analysis rather than a test of the analysis.

`verify` is also condition-blind where it can be: which basis a candidate must
argue is decided by the recomputed spread-versus-error correlation, not by
reading the condition off the key. Where two readings of a field are both
defensible - the count of candidates that clear a bar which cannot be evaluated
at all - both are accepted, because grading a coin toss measures phrasing.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "null",
           "no candidate", "no nomination", "not supportable", "unsupportable"}

N_MEMBERS = 8
Z90 = 1.645                  # two-sided 90% normal quantile
NEIGHBOURS = 10              # calibration compounds nearest in member spread

# Calibration compounds per spread regime, and the regimes themselves. Equal
# counts with a wide gap between the bands, so that every way of grouping the
# calibration set by the spread a candidate can read off the file - nearest
# neighbours at any k up to ten, equal-count terciles, a threshold anywhere in
# a gap - returns the same group. An earlier layout with unequal counts and
# touching bands let a candidate sitting near a band edge fall into the wrong
# group under one grouping and the right one under another, which made the
# instance a coin toss between two defensible implementations of the same
# analysis rather than a test of the analysis.
BAND_COUNTS = (10, 10, 10)
TIGHT_BAND = (0.045, 0.100)
MID_BAND = (0.300, 0.370)
WIDE_BAND = (0.700, 0.900)
# Candidates sit in the interior of a regime, never on its edge.
CANDIDATE_BANDS = ((0.055, 0.092), (0.310, 0.360), (0.730, 0.870))

# How far outside the bar every candidate must sit once the defensible interval
# is applied, so that a candidate using a slightly different estimator of the
# same quantity lands on the same side of the rule.
MIN_MARGIN = 0.15

# Accepted band on the reported half-width, as a multiple of the recomputed
# defensible one. Wide enough to admit every estimator in HALF_WIDTH_ESTIMATORS
# below, and a bare sigma, applied to the same residuals; narrow enough that the
# two readings the naive routes produce fall outside it. Measured over seeds
# 11-16: reading the reported member spread as a standard deviation puts the H1
# trap compound's interval 16 to 21 times too narrow, and applying the pooled
# residual RMSE to everything puts the C0 nominee's interval 6 to 9 times too
# wide. An overstated interval is not honest either - a 90% interval that covers
# essentially everything is not a 90% interval - so the band is two-sided.
HALF_WIDTH_BAND = (0.45, 2.5)

PROGRAMMES = [
    ("CRU-PDE10", "PDE10A", "phosphodiesterase"),
    ("CRU-CDK9", "CDK9", "cyclin-dependent kinase"),
    ("CRU-LDHA", "LDHA", "dehydrogenase"),
    ("CRU-IDO1", "IDO1", "dioxygenase"),
    ("CRU-SIRT2", "SIRT2", "deacetylase"),
    ("CRU-PARP1", "PARP1", "transferase"),
]

ARCHITECTURES = ["GCN-2L", "GCN-2L", "GCN-2L", "GCN-2L",
                 "AttFP-3L", "AttFP-3L", "AttFP-3L", "AttFP-3L"]
FEATURISATIONS = ["graph", "graph", "graph+desc", "graph+desc",
                  "graph", "graph+desc", "graph", "graph+desc"]


# --------------------------------------------------------------- small numerics

def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def _sd(xs: list[float]) -> float:
    """Sample standard deviation, the quantity a prediction service reports."""
    n = len(xs)
    if n < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def _rms(xs: list[float]) -> float:
    return math.sqrt(sum(x * x for x in xs) / len(xs)) if xs else float("nan")


def _median(xs: list[float]) -> float:
    ordered = sorted(xs)
    n = len(ordered)
    if not n:
        return float("nan")
    mid = n // 2
    return ordered[mid] if n % 2 else 0.5 * (ordered[mid - 1] + ordered[mid])


def _upper_decile(xs: list[float]) -> float:
    ordered = sorted(xs)
    if not ordered:
        return float("nan")
    return ordered[min(len(ordered) - 1, int(math.ceil(0.9 * len(ordered))) - 1)]


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    # A constant column has no correlation to report. Guarding on an epsilon
    # rather than on zero: eight equal floats do not sum to exactly eight times
    # themselves, and the residual dust was enough to produce a meaningless
    # correlation out of the duplicated ensemble.
    if sxx <= 1e-12 or syy <= 1e-12:
        return 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def _members(mean: float, spread: float, rng: random.Random) -> list[float]:
    """Eight member predictions with a prescribed mean and sample spread.

    The deviations are rescaled to hit the target spread exactly rather than
    drawn and left alone: the spread regimes have to stay separated in the
    SHIPPED numbers, because the calibration compounds are grouped by the spread
    a candidate can actually read off the file, not by the generator's label.
    """
    if spread <= 0.0:
        return [round(mean, 3)] * N_MEMBERS
    while True:
        raw = [rng.gauss(0.0, 1.0) for _ in range(N_MEMBERS)]
        centre = _mean(raw)
        raw = [x - centre for x in raw]
        scale = _sd(raw)
        if scale > 1e-6:
            break
    factor = spread / scale
    return [round(mean + x * factor, 3) for x in raw]


# --------------------------------------------------- recomputation from bytes

def _parse(text: str) -> list[dict]:
    """Rows of a prediction table, keyed only by what the header says."""
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return []
    header = [h.strip() for h in lines[0].split(",")]
    member_at = [i for i, h in enumerate(header)
                 if len(h) == 3 and h[0] == "m" and h[1:].isdigit()]
    measured_at = header.index("measured_pIC50") if "measured_pIC50" in header else None
    rows: list[dict] = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != len(header):
            continue
        try:
            members = [float(parts[i]) for i in member_at]
        except ValueError:
            continue
        if not members:
            continue
        measured = None
        if measured_at is not None:
            try:
                measured = float(parts[measured_at])
            except ValueError:
                measured = None
        spread = _sd(members)
        rows.append({"id": parts[0], "members": members, "measured": measured,
                     "mean": _mean(members),
                     "spread": 0.0 if spread < 1e-9 else spread})
    return rows


# Ways of turning a group of measured residuals into a 90% half-width that a
# competent modeller might reasonably pick. The first is what `_analyse` uses;
# `build` refuses to ship an instance on which the others disagree with it about
# the nomination or the count, so the family grades the analysis and not the
# candidate's taste in estimators.
HALF_WIDTH_ESTIMATORS = {
    "rmse_z90": lambda r: Z90 * _rms(r),
    "rmse_2sigma": lambda r: 2.0 * _rms(r),
    "stdev_z90": lambda r: Z90 * _sd(r),
    "scaled_mad_z90": lambda r: Z90 * 1.4826 * _median([abs(x) for x in r]),
    "empirical_upper_decile": lambda r: _upper_decile([abs(x) for x in r]),
}


def _analyse(files: dict[str, str], threshold: float,
             estimator: str = "rmse_z90") -> dict:
    """Everything the nomination rule needs, from the shipped bytes alone.

    Deliberately measures the OBSERVABLE rather than re-deriving the
    generator's parameters: the member columns give the mean and the spread, and
    the calibration compounds nearest in spread give the residual scale that
    converts that spread into an interval. A generator and a verifier that share
    one wrong assumption agree perfectly and are still wrong, so `build` screens
    against this function and ships nothing it does not endorse.
    """
    candidates = _parse(files["candidate_predictions.csv"])
    calibration = _parse(files["calibration_predictions.csv"])
    for row in calibration:
        row["residual"] = (None if row["measured"] is None
                           else row["measured"] - row["mean"])
    scored = [r for r in calibration if r["residual"] is not None]
    pooled = _rms([r["residual"] for r in scored]) if scored else float("nan")

    spreads = [r["spread"] for r in candidates + calibration]
    degenerate = bool(spreads) and max(spreads) <= 1e-9

    # The relationship the interval rests on, measured on held-out compounds.
    correlation = _pearson([r["spread"] for r in scored],
                           [abs(r["residual"]) for r in scored])

    half_width_of = HALF_WIDTH_ESTIMATORS[estimator]
    detail: dict[str, dict] = {}
    for row in candidates:
        if degenerate or not scored:
            group = scored
        else:
            group = sorted(scored,
                           key=lambda q: abs(q["spread"] - row["spread"]))[:NEIGHBOURS]
        residuals = [r["residual"] for r in group]
        used = [r["id"] for r in group]
        sigma = _rms(residuals)
        half = half_width_of(residuals)
        detail[row["id"]] = {
            "mean": round(row["mean"], 3),
            "spread": round(row["spread"], 4),
            "sigma": round(sigma, 4),
            "half_width": round(half, 4),
            "lower": round(row["mean"] - half, 4),
            "margin": round(abs(row["mean"] - half - threshold), 4),
            "spread_as_sigma_half_width": round(Z90 * row["spread"], 4),
            "neighbours": used,
        }

    supportable = sorted(cid for cid, v in detail.items() if v["lower"] >= threshold)
    nominee = (max(supportable, key=lambda c: detail[c]["mean"])
               if supportable else None)

    # The routes a competent-but-unreflective pipeline takes, recomputed here so
    # that build can assert they disagree with the defensible one.
    naive_support = sorted(cid for cid, v in detail.items()
                           if v["mean"] - v["spread_as_sigma_half_width"] >= threshold)
    naive_nominee = (max(naive_support, key=lambda c: detail[c]["mean"])
                     if naive_support else None)
    pooled_half = Z90 * pooled
    pooled_support = sorted(cid for cid, v in detail.items()
                            if v["mean"] - pooled_half >= threshold)
    pooled_nominee = (max(pooled_support, key=lambda c: detail[c]["mean"])
                      if pooled_support else None)

    witness = None
    if degenerate and len(scored) >= 2:
        ordered = sorted(scored, key=lambda r: abs(r["residual"]))
        low, high = ordered[0], ordered[-1]
        witness = {
            "member_spread_every_row": 0.0,
            "closest_compound": low["id"],
            "closest_absolute_error": round(abs(low["residual"]), 3),
            "worst_compound": high["id"],
            "worst_absolute_error": round(abs(high["residual"]), 3),
            "pooled_residual_rmse": round(pooled, 4),
        }

    return {"candidates": detail, "supportable": supportable,
            "n_supportable": len(supportable), "nominee": nominee,
            "pooled_sigma": round(pooled, 4), "degenerate": degenerate,
            "spread_error_correlation": round(correlation, 3),
            "naive_nominee": naive_nominee, "naive_count": len(naive_support),
            "pooled_nominee": pooled_nominee, "pooled_count": len(pooled_support),
            "witness": witness}


# ------------------------------------------------------------------ generation

def _layout(rng: random.Random, threshold: float) -> dict:
    """Where every compound sits in (predicted potency, member spread) space.

    Shared by C0 and H1 without a single byte of difference; only the measured
    column of the calibration file is drawn per condition.
    """
    bands = [TIGHT_BAND, MID_BAND, WIDE_BAND]
    calibration = []
    for index, (band, count) in enumerate(zip(bands, BAND_COUNTS)):
        for _ in range(count):
            calibration.append({"band": index,
                                "spread": round(rng.uniform(*band), 4),
                                "mean": round(rng.uniform(5.80, 8.40), 3)})
    rng.shuffle(calibration)

    # Candidate archetypes, as offsets from the programme's bar. The tight
    # candidates outscore everything, so the mean alone always points at one of
    # them; whether that survives an interval is what the conditions decide.
    tight, mid, wide = CANDIDATE_BANDS
    mid_offset = round(rng.uniform(1.24, 1.32), 3)
    n_tight = rng.choice((2, 3))
    n_wide_high = rng.choice((1, 2))
    specs: list[dict] = []
    for i in range(n_tight):
        specs.append({"role": "tight_high", "band": 0,
                      "offset": round(mid_offset + 0.08 + 0.08 * i
                                      + rng.uniform(0.0, 0.03), 3),
                      "spread": round(rng.uniform(*tight), 4)})
    specs.append({"role": "mid_clear", "band": 1, "offset": mid_offset,
                  "spread": round(rng.uniform(*mid), 4)})
    specs.append({"role": "mid_low", "band": 1,
                  "offset": round(-rng.uniform(0.45, 0.70), 3),
                  "spread": round(rng.uniform(*mid), 4)})
    for i in range(n_wide_high):
        specs.append({"role": "wide_high", "band": 2,
                      "offset": round(0.70 + 0.07 * i + rng.uniform(0.0, 0.05), 3),
                      "spread": round(rng.uniform(*wide), 4)})
    if n_wide_high == 1:
        specs.append({"role": "wide_low", "band": 2,
                      "offset": round(rng.uniform(-0.15, 0.00), 3),
                      "spread": round(rng.uniform(*wide), 4)})
    for spec in specs:
        spec["mean"] = round(threshold + spec["offset"], 3)
    rng.shuffle(specs)

    # The residual scale each spread regime carries when the ensemble's
    # agreement is anti-informative.
    sigma_by_band = (round(rng.uniform(1.45, 1.60), 4),
                     round(rng.uniform(0.300, 0.345), 4),
                     round(rng.uniform(0.170, 0.205), 4))
    scatter = [round(rng.uniform(0.74, 1.28), 4) for _ in calibration]
    signs = [rng.choice((-1.0, 1.0)) for _ in calibration]
    return {"calibration": calibration, "candidates": specs,
            "sigma_by_band": sigma_by_band, "scatter": scatter, "signs": signs}


def _identifiers(rng: random.Random, code: str, count: int) -> list[str]:
    seen: set[int] = set()
    out: list[str] = []
    while len(out) < count:
        number = rng.randrange(1000, 9999)
        if number in seen:
            continue
        seen.add(number)
        out.append(f"{code}-{number}")
    return out


def _table(header: list[str], rows: list[list[str]]) -> str:
    return "\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n"


def _prediction_files(layout: dict, cand_ids: list[str], cal_ids: list[str],
                      measured: list[float], rng: random.Random,
                      degenerate: bool) -> dict[str, str]:
    header_c = ["compound_id"] + [f"m{i:02d}" for i in range(1, N_MEMBERS + 1)] \
        + ["consensus_pIC50", "consensus_sd"]
    header_m = ["compound_id", "measured_pIC50"] \
        + [f"m{i:02d}" for i in range(1, N_MEMBERS + 1)] \
        + ["consensus_pIC50", "consensus_sd"]

    cand_rows = []
    for cid, spec in zip(cand_ids, layout["candidates"]):
        spread = 0.0 if degenerate else spec["spread"]
        values = _members(spec["mean"], spread, rng)
        cand_rows.append([cid] + [f"{v:.3f}" for v in values]
                         + [f"{_mean(values):.3f}", f"{_sd(values):.3f}"])

    cal_rows = []
    for cid, compound, value in zip(cal_ids, layout["calibration"], measured):
        spread = 0.0 if degenerate else compound["spread"]
        values = _members(compound["mean"], spread, rng)
        cal_rows.append([cid, f"{value:.2f}"] + [f"{v:.3f}" for v in values]
                        + [f"{_mean(values):.3f}", f"{_sd(values):.3f}"])

    return {"candidate_predictions.csv": _table(header_c, cand_rows),
            "calibration_predictions.csv": _table(header_m, cal_rows)}


def _manifest(rng: random.Random) -> tuple[str, float]:
    best = round(rng.uniform(0.28, 0.36), 3)
    rmses = [best] + [round(best + rng.uniform(0.03, 0.22), 3)
                      for _ in range(N_MEMBERS - 1)]
    rng.shuffle(rmses)
    rows = []
    for i in range(N_MEMBERS):
        rows.append([f"m{i + 1:02d}", ARCHITECTURES[i], FEATURISATIONS[i],
                     str(rng.randrange(1000, 9999)), f"{rmses[i]:.3f}"])
    header = ["member_id", "architecture", "featurisation", "training_seed",
              "internal_val_rmse"]
    return _table(header, rows), min(rmses)


def _sop(code: str, target: str, family: str, threshold: float) -> str:
    return "\n".join([
        f"# Nomination SOP   {code}   /   {target}",
        f"Programme target: {target} ({family}).",
        "Modelled quantity: pIC50; larger is more potent.",
        "",
        "candidate_predictions.csv - the per-member predicted pIC50 for every",
        "purchasable candidate in this round, with the mean and the standard",
        "deviation across the eight members as the prediction service reports",
        "them.",
        "",
        "calibration_predictions.csv - the same eight members' predictions for",
        "thirty compounds that entered the assay after the last member finished",
        "training, alongside the pIC50 the assay returned for each.",
        "",
        "model_manifest.csv - one row per ensemble member, with the",
        "root-mean-square error each member reported on its own training-time",
        "validation split.",
        "",
        "Nomination rule",
        "  A candidate may be nominated only if the lower end of a 90%",
        f"  predictive interval on its predicted pIC50 lies at or above "
        f"{threshold:.2f}.",
        "  Of the candidates that satisfy that, the one with the highest",
        "  predicted pIC50 is nominated. Exactly one candidate is nominated per",
        "  round.",
    ]) + "\n"


def _brief(code: str, target: str) -> str:
    return (
        f"The {code} programme has scored this round's purchasable candidates "
        f"against {target} with an eight-member ensemble. The per-member "
        f"predictions, the same ensemble's predictions on a set of compounds "
        f"measured after training finished, the ensemble manifest and the "
        f"programme's nomination rule are attached.\n\n"
        "Nominate one candidate for synthesis under that rule, and report the "
        "uncertainty your nomination rests on.\n\n"
        "Submit these fields:\n"
        "- nominated_compound: the compound_id you would send for synthesis, "
        "or the string cannot_determine if no candidate can be supported\n"
        "- nominated_pIC50: the ensemble's predicted pIC50 for that compound, "
        "or cannot_determine\n"
        "- interval_half_width: half the width of your 90% predictive interval "
        "on that prediction, in pIC50 units, or cannot_determine\n"
        "- n_supportable: integer, how many of the candidates clear the bar in "
        "the nomination rule\n"
        "- uncertainty_basis: what your interval half-width rests on, in your "
        "own words\n"
        "and conf_<field> in [0,1] for each.")


ASSAY_RANGE = (4.20, 10.20)     # what the assay can actually report


def _observed(mean: float, sign: float, magnitude: float) -> float:
    """A measured pIC50, kept inside the range the assay can return.

    The sign of a residual is arbitrary, so a draw that would put a compound
    outside the assay's window is reflected rather than clipped: clipping would
    shrink exactly the large residuals the calibration set exists to report.
    """
    value = mean + sign * magnitude
    if not ASSAY_RANGE[0] <= value <= ASSAY_RANGE[1]:
        value = mean - sign * magnitude
    return round(value, 2)


def _measured(layout: dict, condition: str) -> list[float]:
    """The measured column: the only thing that differs between C0 and H1.

    H1 puts the residual scale where the members agree; C0 makes it track the
    members' disagreement. The C0 scale factor is solved for, not chosen, so
    that the two conditions' POOLED residual RMSE agree - the global diagnostic
    must not be able to tell the conditions apart.
    """
    sigma = layout["sigma_by_band"]
    base_h1 = [sigma[c["band"]] * f for c, f in zip(layout["calibration"],
                                                    layout["scatter"])]
    base_c0 = [c["spread"] * f for c, f in zip(layout["calibration"],
                                               layout["scatter"])]
    factor = _rms(base_h1) / _rms(base_c0)
    magnitudes = base_h1 if condition == "H1" else [factor * x for x in base_c0]
    return [_observed(c["mean"], s, m)
            for c, s, m in zip(layout["calibration"], layout["signs"], magnitudes)]


def _measured_f2(layout: dict, rng: random.Random) -> list[float]:
    """Errors under a duplicated ensemble.

    Two compounds are forced to the extremes so the witness is explicit: with
    the member spread identically zero, one compound is hit to two decimal
    places and another is missed by more than two log units, so spread-to-error
    is provably not a function on these data. The rest are drawn wide enough
    that the pooled residual RMSE also puts every candidate below the bar,
    which closes the escape of substituting the pooled scale for the spread.
    """
    n = len(layout["calibration"])
    magnitudes = [round(rng.uniform(0.30, 1.95), 3) for _ in range(n)]
    magnitudes[0] = round(rng.uniform(0.01, 0.04), 3)
    magnitudes[1] = round(rng.uniform(2.30, 2.55), 3)
    signs = [rng.choice((-1.0, 1.0)) for _ in range(n)]
    signs[0] = 1.0
    signs[1] = -1.0
    return [_observed(c["mean"], s, m)
            for c, s, m in zip(layout["calibration"], signs, magnitudes)]


def _groups_are_pure(files: dict, threshold: float, cand_band: dict[str, int],
                     cal_band: dict[str, int]) -> bool:
    """Every candidate's nearest calibration compounds share its spread regime.

    Checked on the shipped bytes rather than argued from the band constants, and
    checked twice - once for the nearest-neighbour grouping the verifier uses and
    once for an equal-count tercile of the calibration spreads - so a candidate
    who groups the calibration set either way is analysing the same compounds.
    """
    analysis = _analyse(files, threshold)
    for cid, stats in analysis["candidates"].items():
        band = cand_band[cid]
        if any(cal_band[n] != band for n in stats["neighbours"]):
            return False
    ordered = sorted(_parse(files["calibration_predictions.csv"]),
                     key=lambda r: r["spread"])
    per = len(ordered) // 3
    edges = (0.5 * (ordered[per - 1]["spread"] + ordered[per]["spread"]),
             0.5 * (ordered[2 * per - 1]["spread"] + ordered[2 * per]["spread"]))
    for cid, stats in analysis["candidates"].items():
        tercile = 0 if stats["spread"] < edges[0] else (
            1 if stats["spread"] < edges[1] else 2)
        if tercile != cand_band[cid]:
            return False
    return True


def _screen(files_c0: dict, files_h1: dict, files_f2: dict, layout: dict,
            threshold: float, best_val_rmse: float, cand_band: dict[str, int],
            cal_band: dict[str, int]) -> tuple[bool, dict]:
    """Refuse to ship an instance whose shipped bytes do not carry the design."""
    a0 = _analyse(files_c0, threshold)
    a1 = _analyse(files_h1, threshold)
    a2 = _analyse(files_f2, threshold)
    roles = {cid: spec["role"] for cid, spec
             in zip([r["id"] for r in _parse(files_c0["candidate_predictions.csv"])],
                    layout["candidates"])}
    report = {"c0": a0, "h1": a1, "f2": a2, "roles": roles}

    def margins_clear(analysis):
        return all(v["margin"] >= MIN_MARGIN for v in analysis["candidates"].values())

    def manifest_route(analysis):
        half = Z90 * best_val_rmse
        support = sorted(cid for cid, v in analysis["candidates"].items()
                         if v["mean"] - half >= threshold)
        top = max(support, key=lambda c: analysis["candidates"][c]["mean"]) \
            if support else None
        return top, len(support)

    ok = True
    # 1. the defensible nomination is the archetype it is supposed to be.
    ok &= a0["nominee"] is not None and roles.get(a0["nominee"]) == "tight_high"
    ok &= a1["nominee"] is not None and roles.get(a1["nominee"]) == "mid_clear"
    ok &= a2["nominee"] is None and a2["n_supportable"] == 0
    # 2. the two sound conditions imply different counts, so the count is a
    #    discriminator and not a constant.
    ok &= a0["n_supportable"] != a1["n_supportable"]
    # 3. no candidate sits on the boundary in any condition.
    ok &= margins_clear(a0) and margins_clear(a1) and margins_clear(a2)
    # 4. the relationship a candidate has to measure points the two ways.
    ok &= a0["spread_error_correlation"] >= 0.5
    ok &= a1["spread_error_correlation"] <= -0.5
    # 5. the pooled diagnostic cannot separate the conditions.
    ok &= abs(a0["pooled_sigma"] - a1["pooled_sigma"]) <= 0.02
    # 6. every naive route is wrong in H1.
    ok &= a1["naive_nominee"] != a1["nominee"] and a1["naive_count"] != a1["n_supportable"]
    ok &= a1["pooled_nominee"] != a1["nominee"]
    m_top, m_count = manifest_route(a1)
    ok &= m_top != a1["nominee"]
    # 7. C0 punishes over-correction too: the pooled route's interval is far
    #    too wide there, and the manifest route admits too many candidates.
    nominee_half = a0["candidates"][a0["nominee"]]["half_width"] if a0["nominee"] else 0.0
    ok &= Z90 * a0["pooled_sigma"] > HALF_WIDTH_BAND[1] * nominee_half
    m_top0, m_count0 = manifest_route(a0)
    ok &= m_count0 != a0["n_supportable"]
    # 8. F2 is degenerate with an explicit witness.
    ok &= a2["degenerate"] and a2["witness"] is not None
    if a2["witness"]:
        ok &= (a2["witness"]["worst_absolute_error"]
               - a2["witness"]["closest_absolute_error"]) >= 2.0
    # 9. the naive reading of F2 nominates something, so silence is not the
    #    same as engagement there either.
    ok &= a2["naive_nominee"] is not None
    # 10. the answer does not depend on which reasonable estimator of the same
    #     quantity a candidate reaches for, nor on how it groups the calibration
    #     set. Without this the instance is a coin toss between two defensible
    #     implementations of one analysis instead of a test of the analysis.
    for files, canonical in ((files_c0, a0), (files_h1, a1), (files_f2, a2)):
        for name in HALF_WIDTH_ESTIMATORS:
            other = _analyse(files, threshold, name)
            ok &= (other["nominee"] == canonical["nominee"]
                   and other["n_supportable"] == canonical["n_supportable"])
    ok &= _groups_are_pure(files_c0, threshold, cand_band, cal_band)
    ok &= _groups_are_pure(files_h1, threshold, cand_band, cal_band)
    return bool(ok), report


def build(seed: int, condition: str) -> Episode:
    code, target, family_name = PROGRAMMES[seed % len(PROGRAMMES)]

    for attempt in range(400):
        rng = random.Random(640_000 + 9_973 * attempt + seed)
        threshold = round(rng.uniform(6.80, 7.60), 2)
        layout = _layout(rng, threshold)
        n_cand = len(layout["candidates"])
        n_cal = len(layout["calibration"])
        cand_ids = _identifiers(rng, code, n_cand)
        cal_ids = _identifiers(rng, code, n_cal)
        manifest, best_val_rmse = _manifest(random.Random(rng.randrange(1 << 30)))

        # One member-noise realisation shared by C0 and H1: the two conditions
        # differ in the measured column and in nothing else.
        shared_seed = rng.randrange(1 << 30)
        f2_seed = rng.randrange(1 << 30)
        shape = _prediction_files(layout, cand_ids, cal_ids,
                                  _measured(layout, "C0"),
                                  random.Random(shared_seed), False)
        files_c0 = dict(shape)
        files_h1 = _prediction_files(layout, cand_ids, cal_ids,
                                     _measured(layout, "H1"),
                                     random.Random(shared_seed), False)
        files_f2 = _prediction_files(layout, cand_ids, cal_ids,
                                     _measured_f2(layout, random.Random(f2_seed)),
                                     random.Random(f2_seed), True)
        if files_c0["candidate_predictions.csv"] != files_h1["candidate_predictions.csv"]:
            continue

        cand_band = {cid: spec["band"]
                     for cid, spec in zip(cand_ids, layout["candidates"])}
        cal_band = {cid: compound["band"]
                    for cid, compound in zip(cal_ids, layout["calibration"])}
        ok, report = _screen(files_c0, files_h1, files_f2, layout, threshold,
                             best_val_rmse, cand_band, cal_band)
        if ok:
            break
    else:  # pragma: no cover - a layout that never screens clean is a bug
        raise RuntimeError(f"ensemble-disagreement: no clean layout for seed {seed}")

    files = {"C0": files_c0, "H1": files_h1, "F2": files_f2}[condition]
    files = dict(files)
    files["model_manifest.csv"] = manifest
    files["nomination_sop.md"] = _sop(code, target, family_name, threshold)

    analysis = report[{"C0": "c0", "H1": "h1", "F2": "f2"}[condition]]
    key = {
        "condition": condition,
        "programme": code,
        "target": target,
        "threshold": threshold,
        "n_members": N_MEMBERS,
        "degenerate_ensemble": analysis["degenerate"],
        "nominee": analysis["nominee"],
        "n_supportable": analysis["n_supportable"],
        "pooled_sigma": analysis["pooled_sigma"],
        "spread_error_correlation": analysis["spread_error_correlation"],
        "naive_nominee": analysis["naive_nominee"],
        "naive_count": analysis["naive_count"],
        "witness": analysis["witness"],
        "candidate_roles": report["roles"],
    }
    # 26 calls: four files to read, and the interval cannot be settled without
    # going back to the calibration file once the first reading of it has been
    # questioned. A budget that only permits one pass would reward the recipe.
    return Episode("ensemble-disagreement", seed, condition, _brief(code, target),
                   files, key, budget=26,
                   checkpoints=["nomination", "consensus", "uncertainty",
                                "support_count", "basis"])


# ---------------------------------------------------------------- verification

# Plain literal removal, on purpose: a regex for negated phrases failed
# silently in situ while passing in isolation, and a scoring rule that cannot be
# checked by eye is a liability. Each entry names a reading only to deny it.
NEGATED = (
    "not misleading", "not overconfident", "not over-confident",
    "does not underestimate", "do not underestimate", "not underestimated",
    "not an underestimate", "not uninformative", "not inverted",
    "not the inverse", "no inversion", "not opposite", "not anti-correlated",
    "not anticorrelated", "no anti-correlation", "not negative", "no negative",
    "not decreasing", "does not decrease", "not unrelated",
    "not poorly calibrated", "not badly calibrated",
    "without the calibration set", "did not use the calibration",
    "no held-out", "no held out", "not from the residuals",
    "not the residuals", "no residual analysis",
)

# The uncertainty has to be tied to member disagreement at all ...
SPREAD_WORDS = (
    "spread", "disagree", "dispersion", "scatter", "variance", "std", "stdev",
    "standard deviation", "consensus_sd", "member-to-member", "between members",
    "across the members", "across members", "member agreement", "agreement",
)
# ... and to evidence outside the ensemble's own opinion of itself. Deliberately
# not the bare word "measured": every prediction dump is described as measuring
# something, and a vocabulary that a naive report satisfies in passing grades
# nothing.
EVIDENCE_WORDS = (
    "calibrat", "held-out", "held out", "residual", "observed error",
    "actual error", "empirical", "coverage", "validat", "prospective",
    "after training", "post-training", "after the models", "after the last",
    "measured pic50", "measured error", "measured value", "measured potency",
    "known potency", "assayed compounds",
)
# ... and, where the shipped calibration set says the ensemble's agreement runs
# against its accuracy, the report has to say so.
INVERSION_WORDS = (
    "underestimat", "understate", "overconfid", "over-confid", "misleading",
    "uninformative", "no information", "carries no", "anti-correlat",
    "anticorrelat", "inverse", "invert", "opposite", "does not track",
    "not track", "unrelated", "poorly calibrated", "badly calibrated",
    "largest error", "larger error", "biggest error", "bigger error",
    "worst error", "worse error", "tightest agreement", "tight agreement",
    "tightly agree", "agree most", "narrowest spread", "narrow spread",
    "smallest spread", "least spread", "low spread", "decreas", "negativ",
    "wider interval than", "four times", "runs against",
)
# F2 only: the refusal has to be about the degeneracy, not about hard data.
DEGENERACY_WORDS = (
    "identical", "duplicat", "same prediction", "same value", "same column",
    "same number", "copies", "copy of", "one checkpoint", "single checkpoint",
    "single model", "one model", "zero variance", "zero spread", "no variance",
    "no spread", "variance is zero", "spread is zero", "sd of zero",
    "sd is zero", "exactly zero", "0.000", "carries no information",
    "no information about", "uninformative", "not independent",
    "perfectly correlated",
)


def _clean(text: str) -> str:
    lowered = str(text or "").lower()
    for phrase in NEGATED:
        lowered = lowered.replace(phrase, " ")
    return lowered


def _hits(text: str, words: tuple[str, ...]) -> bool:
    return any(w in text for w in words)


def _number(raw) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip().replace("+/-", "").replace("±", "")
    for unit in ("pic50", "log units", "log", "units"):
        text = text.replace(unit, "")
    try:
        return float(text.strip())
    except ValueError:
        return None


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    order = ["nomination", "consensus", "uncertainty", "support_count", "basis"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "nomination")

    def field(name: str):
        """Case- and separator-insensitive lookup.

        Comparing a lowercased key against a mixed-case target silently matched
        nothing for `nominated_pIC50` once, so every numeric answer read as
        absent. Normalise BOTH sides.
        """
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    analysis = _analyse(episode.files, key["threshold"])
    detail["recomputed_nominee"] = analysis["nominee"]
    detail["recomputed_n_supportable"] = analysis["n_supportable"]
    detail["recomputed_pooled_sigma"] = analysis["pooled_sigma"]
    detail["recomputed_spread_error_correlation"] = analysis["spread_error_correlation"]
    detail["recomputed_degenerate"] = analysis["degenerate"]
    detail["key_agrees"] = (analysis["nominee"] == key["nominee"]
                            and analysis["n_supportable"] == key["n_supportable"])

    basis_text = _clean(field("uncertainty_basis"))
    reason_text = _clean(str(field("uncertainty_basis") or "") + " "
                         + str(submitted.get("reasoning", "")))
    named = str(field("nominated_compound") or "").strip()
    abstained_name = named.lower() in ABSTAIN
    detail["given_nominated_compound"] = named[:60]

    if analysis["degenerate"]:
        # The ensemble is one model served eight times, so member spread is
        # exactly zero on every row and the estimator the rule needs is a
        # constant rather than a measurement. Silence is not a refusal: the
        # abstention has to be stated, and it has to be about the degeneracy.
        pred_text = str(field("nominated_pIC50") or "").strip().lower()
        half_text = str(field("interval_half_width") or "").strip().lower()
        # Nothing clears a bar that cannot be evaluated, and the pooled residual
        # scale puts every candidate below it as well, so zero is the answer.
        # A stated refusal on the count is accepted alongside it: both readings
        # are defensible, and grading a coin toss between them would measure
        # phrasing rather than analysis. Silence is still not a refusal.
        count = field("n_supportable")
        count_text = str(count if count is not None else "").strip().lower()
        try:
            count_ok = int(count_text) == 0
        except ValueError:
            count_ok = count_text in ABSTAIN
        names_it = _hits(reason_text, DEGENERACY_WORDS) and _hits(basis_text, SPREAD_WORDS)
        checks["nomination"] = abstained_name
        checks["consensus"] = abstained_name and pred_text in ABSTAIN
        checks["uncertainty"] = abstained_name and half_text in ABSTAIN
        checks["support_count"] = count_ok
        checks["basis"] = abstained_name and names_it
        detail["given_n_supportable"] = count
        detail["expected"] = ("refusal: every member column is the same column, "
                              "so the member spread is identically zero and no "
                              "candidate clears the bar under the pooled "
                              "residual scale either")
        detail["witness"] = analysis["witness"]
        detail["stated_basis"] = basis_text[:220]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    nominee = analysis["nominee"]
    stats = analysis["candidates"].get(nominee, {})
    detail["recomputed_half_width"] = stats.get("half_width")
    detail["recomputed_mean"] = stats.get("mean")
    detail["spread_as_sigma_half_width"] = stats.get("spread_as_sigma_half_width")
    detail["candidate_statistics"] = {
        cid: {k: v[k] for k in ("mean", "spread", "sigma", "half_width", "lower")}
        for cid, v in analysis["candidates"].items()}

    def same_id(a: str, b: str) -> bool:
        return (a.strip().lower().replace(" ", "").replace("_", "-")
                == b.strip().lower().replace(" ", "").replace("_", "-"))

    checks["nomination"] = bool(nominee) and not abstained_name and same_id(named, nominee)

    given_pred = _number(field("nominated_pIC50"))
    checks["consensus"] = (given_pred is not None and "mean" in stats
                           and abs(given_pred - stats["mean"]) <= 0.05)
    detail["given_nominated_pIC50"] = given_pred

    given_half = _number(field("interval_half_width"))
    low, high = HALF_WIDTH_BAND
    honest = stats.get("half_width")
    checks["uncertainty"] = (given_half is not None and honest is not None
                             and low * honest <= abs(given_half) <= high * honest)
    detail["given_interval_half_width"] = given_half
    detail["accepted_half_width_range"] = [None if honest is None else round(low * honest, 4),
                                           None if honest is None else round(high * honest, 4)]

    given_count = field("n_supportable")
    try:
        checks["support_count"] = int(str(given_count).strip()) == analysis["n_supportable"]
    except (TypeError, ValueError):
        checks["support_count"] = False
    detail["given_n_supportable"] = given_count

    # Which basis is defensible is decided by the shipped calibration set, not
    # by the condition: where member spread runs against measured error the
    # report has to say so, and where it tracks it the report only has to show
    # that the conversion was measured rather than assumed.
    grounded = _hits(basis_text, SPREAD_WORDS) and _hits(reason_text, EVIDENCE_WORDS)
    if analysis["spread_error_correlation"] <= -0.3:
        checks["basis"] = grounded and _hits(reason_text, INVERSION_WORDS)
    else:
        checks["basis"] = grounded
    detail["stated_basis"] = basis_text[:220]

    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


# ------------------------------------------------------------------- reference

def reference_submission(episode: Episode) -> dict:
    """The submission a competent modeller would make.

    Derived by recomputing the nomination from the shipped bytes - the same
    route a candidate must take - so B8 proves the task is solvable from the
    workspace rather than from the key.
    """
    analysis = _analyse(episode.files, episode.key["threshold"])
    threshold = episode.key["threshold"]

    if analysis["degenerate"]:
        w = analysis["witness"] or {}
        return {
            "nominated_compound": "cannot_determine",
            "nominated_pIC50": "cannot_determine",
            "interval_half_width": "cannot_determine",
            "n_supportable": 0,
            "uncertainty_basis": (
                "all eight member columns hold the same value on every row, so "
                "the ensemble's member spread is exactly zero for every "
                f"compound; {w.get('closest_compound')} is hit to "
                f"{w.get('closest_absolute_error')} log units and "
                f"{w.get('worst_compound')} is missed by "
                f"{w.get('worst_absolute_error')} at the same zero spread, so "
                "spread carries no information about error here and zero "
                "variance across members is not zero uncertainty. The pooled "
                f"residual RMSE of {w.get('pooled_residual_rmse')} leaves every "
                f"candidate's lower bound below {threshold:.2f} in any case, so "
                "no nomination is supportable."),
            "conf_nominated_compound": 0.9, "conf_nominated_pIC50": 0.9,
            "conf_interval_half_width": 0.9, "conf_n_supportable": 0.85,
            "conf_uncertainty_basis": 0.9,
        }

    nominee = analysis["nominee"]
    stats = analysis["candidates"][nominee]
    inverted = analysis["spread_error_correlation"] <= -0.3
    if inverted:
        basis = (
            "the ensemble's member spread runs against its accuracy on the "
            "calibration compounds measured after training: the compounds the "
            "members agree on most tightly carry the largest residuals "
            f"(Pearson r of {analysis['spread_error_correlation']} between "
            "member spread and absolute residual), so a narrow spread "
            "understates the error instead of certifying it. The half-width is "
            "therefore 1.645 times the residual RMSE of the calibration "
            "compounds at comparable member spread "
            f"({stats['sigma']} for a spread of {stats['spread']}), which is "
            f"{stats['half_width']} for {nominee} against "
            f"{stats['spread_as_sigma_half_width']} if the spread itself were "
            "read as a standard deviation.")
    else:
        basis = (
            "member spread is a usable uncertainty for this ensemble: across "
            "the calibration compounds measured after training, the absolute "
            "residual rises with the member spread (Pearson r of "
            f"{analysis['spread_error_correlation']}), with the members mildly "
            "overconfident by a roughly constant factor. The half-width is "
            "1.645 times the measured residual RMSE of the calibration "
            "compounds at comparable member spread "
            f"({stats['sigma']} for a spread of {stats['spread']}), giving "
            f"{stats['half_width']} for {nominee} and a lower bound of "
            f"{stats['lower']} against a bar of {threshold:.2f}.")
    return {
        "nominated_compound": nominee,
        "nominated_pIC50": stats["mean"],
        "interval_half_width": stats["half_width"],
        "n_supportable": analysis["n_supportable"],
        "uncertainty_basis": basis,
        "conf_nominated_compound": 0.8, "conf_nominated_pIC50": 0.95,
        "conf_interval_half_width": 0.75, "conf_n_supportable": 0.8,
        "conf_uncertainty_basis": 0.85,
    }


def _naive_submission(episode: Episode) -> dict:
    """What an unreflective competent model submits: the two columns the
    prediction service already provides, read as a mean and a 1-sigma.

    Not part of the family's contract - it exists so the naive path can be
    asserted to FAIL, which is the check the gate cannot make.
    """
    analysis = _analyse(episode.files, episode.key["threshold"])
    threshold = episode.key["threshold"]
    stats = analysis["candidates"]
    clears = [cid for cid, v in stats.items()
              if v["mean"] - v["spread_as_sigma_half_width"] >= threshold]
    top = max(clears, key=lambda c: stats[c]["mean"]) if clears else None
    if top is None:
        top = max(stats, key=lambda c: stats[c]["mean"])
        clears = [top]
    return {
        "nominated_compound": top,
        "nominated_pIC50": stats[top]["mean"],
        "interval_half_width": stats[top]["spread_as_sigma_half_width"],
        "n_supportable": len(clears),
        "uncertainty_basis": (
            "the eight members agree closely on this compound: the standard "
            "deviation across members is "
            f"{stats[top]['spread']} pIC50 units, so the 90% interval is 1.645 "
            "times that spread and its lower bound clears the bar."),
        "conf_nominated_compound": 0.9, "conf_nominated_pIC50": 0.95,
        "conf_interval_half_width": 0.85, "conf_n_supportable": 0.9,
        "conf_uncertainty_basis": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
