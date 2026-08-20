"""Family: the Hill slope diagnoses the mechanism, but the slope you measure
depends on how you pooled the plates - and the standard pipeline pools wrong.

Written to the collaborator critique archived at analysis/collab/hardening__gpt.md
and hardening__gemini.md. Their shared diagnosis of the first family batch was
that it consisted of "canonical audit recipes with a conspicuous local defect",
and that we had "confused using a complex tool with solving a complex scientific
problem". The prescription was to ship *several superficially adequate analyses
that imply different decisions, plus data or controls that make exactly one of
them defensible*, with F2 carrying an explicit impossibility witness rather than
a complaint about data quality.

The science this family turns on is elementary and, for exactly that reason,
routinely got wrong: the Hill slope of an inhibition curve is a statement about
mechanism. A slope indistinguishable from unity is what a single reversible site
produces. A slope far above unity is what compound aggregation, detergent-like
membrane/protein disruption or stoichiometric depletion produce, and in that
regime the midpoint of the curve is a critical concentration rather than an
affinity - so an "IC50" read off it is not a potency at all. A slope far below
unity is what two or more sites of different affinity produce, and again one
number does not summarise the compound.

The difficulty does not live in knowing that. It lives in the fact that the same
84 wells support three analyses that every screening group runs, that all three
fit well, and that they disagree about the slope:

  1. pool the raw signal from the three plate preparations and fit a
     four-parameter logistic. The preparations have different amplitudes, so
     this fit is dominated by the amplitude mismatch and its R-squared, around
     0.72 in H1, is the only loud thing in the workspace;
  2. normalise each plate to its own vehicle and no-enzyme wells, average the
     wells at each concentration, and fit the seven means - the textbook
     pipeline. Across seeds 1-40 its R-squared never drops below 0.995 and its
     slope stays inside 0.90 to 1.18 in EVERY condition, including the one where
     the compound is not a single-site inhibitor at all. This is the
     naive-competent path and it is confidently wrong;
  3. normalise each plate to its own wells and fit a stratified model - one
     shared slope, one midpoint and one pair of asymptotes per preparation. This
     is the only analysis that can separate a genuinely steep curve from three
     well-behaved curves whose midpoints sit at different concentrations, because
     averaging a family of steep curves with dispersed midpoints reproduces a
     shallow one almost exactly. Analysis 2 destroys, in its first step, the
     information it would need.

The generator does not trust an approximation for that last point. It sizes the
dispersion by averaging the noiseless mixture at the concentrations it is about
to run, fitting it, and bisecting until the averaged slope hits a drawn target
near unity - so the trap is measured into place rather than estimated.

What makes exactly one of them defensible is a control that is present in every
condition with the same filename, the same columns and the same number of rows:
a reference standard with a certificated potency and a certificated slope of
1.00, run at the same concentrations on the same three preparations. It does two
independent jobs.

  * It calibrates the potency. Every preparation reads the standard weak by the
    same factor it reads the candidate weak, so the candidate's potency is only
    defensible when it is bridged through the standard back to the certificate.
    The unbridged geometric mean is high by the preparation drift - well outside
    tolerance - so the number a competent-but-unbridged analysis reports fails
    in C0 as well as in H1. Over-correction is punished symmetrically: the
    bridge is a fact about the shipped standard wells, not a free parameter.
  * It calibrates the dispersion. Preparation-to-preparation midpoint scatter is
    normal; the question is how much. The standard answers it. In C0 the
    candidate's midpoints scatter exactly as much as the standard's, so the
    scatter is the assay. In H1 the candidate's midpoints scatter several times
    more than the standard's on the same plates, so the scatter is the compound
    - which is what licenses the stratified reading of the slope instead of the
    averaged one.

Conditions:

  C0  the candidate really is a well-behaved single-site inhibitor. The
      stratified slope, the averaged slope and the standard all agree. Calling
      a mechanism problem here is a false alarm and fails.
  H1  the candidate's true slope is far above unity and its midpoint moves
      several-fold between preparations, which is what a compound coming out of
      solution does. The generator sizes the dispersion so that the AVERAGED
      curve reproduces a slope near unity with an excellent fit: the naive path
      reports a single-site potency and progresses the compound, and both are
      wrong. The stratified slope recovers the real one and the progression call
      flips to NO.
  F2  the concentrations actually run form two widely separated blocks with the
      inflection in the gap between them, so every well sits on a plateau and no
      concentration is between 12% and 88% inhibition. Neither the slope nor the
      midpoint is identified. The witness is constructed, not asserted: the
      generator scans the slope, keeps every value whose lack of fit against the
      replicate wells is inside the cap, refits at the two ends of that set and
      ships both parameter vectors with their midpoints, their residual RMS and
      their lack-of-fit ratio. Across seeds 1-40 the two slopes always differ by
      at least threefold and the midpoints by up to eighty. The same ladder also
      fails to recover the reference standard's certificated slope of 1.00, which
      the candidate can check for itself without being told to. A documented
      refusal is the only defensible outcome.

This build always makes the H1 slope steep, because dispersed midpoints can only
ever make an averaged curve SHALLOWER than the curves it averages - so a shallow
truth cannot be masked by that mechanism, and inventing a second masking route
for it would buy variety in one string at the cost of a second thing to get
wrong. The verifier does not assume the direction: it grades against the sign of
the recomputed departure from unity, so the shallow branch is live if any future
change makes it fire.

Verification never reads a self-reported number as evidence. It re-normalises the
shipped wells, refits the stratified model with scipy, scans the slope to an
admissible set, refits the standard, bridges the potency, and then decides which
regime it is in from WHETHER THE ADMISSIBLE SET AGREES WITH ITSELF rather than
from the condition label. Two earlier criteria were wrong and are worth recording
because both looked right: a profile-likelihood interval, which is fooled by the
flexibility a shallow model has on an unbracketed ladder; and a cap on the width
of the interval, which fails a sound instance whose compound is so steep that no
instrument can bound its slope from above even though every admissible slope says
the same thing about the mechanism. Grading against the recomputation rather than
the key means a generator that drifts shows up as a disagreement in the self-test
instead of propagating into a campaign as a wrong answer key.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "unidentifiable",
           "not identifiable", "none", "n_a", "na", "null", "unknown"}

TARGETS = [
    ("CRU-9301", "MTH1 hydrolase", "fluorescence intensity 485/528 nm", "STD-114"),
    ("CRU-9302", "NAMPT transferase", "absorbance 340 nm", "STD-207"),
    ("CRU-9303", "USP7 hydrolase", "fluorescence intensity 360/460 nm", "STD-331"),
    ("CRU-9304", "PRMT5 methyltransferase", "luminescence, relative light units", "STD-402"),
    ("CRU-9305", "ALDH1A1 dehydrogenase", "fluorescence intensity 340/450 nm", "STD-518"),
    ("CRU-9306", "SHP2 phosphatase", "fluorescence intensity 430/545 nm", "STD-626"),
]

PLATES = ("P1", "P2", "P3")
N_DOSES = 7
WELLS_PER_DOSE = 4            # per preparation
CONTROL_WELLS = 4             # per control type per preparation
DOSE_STEP = 2.5
F2_GAP = 250.0                # each block sits this far from the inflection
F2_STEP = 2.0                 # spacing inside each block

PROGRESS_THRESHOLD_UM = 0.5
THRESHOLD_GUARD = 1.6         # keep the truth this far off the threshold, so a
                              # candidate whose fit differs from the verifier's
                              # in the third digit cannot lose the decision to
                              # arithmetic rather than to judgement
UNITY_FOLD = 1.80             # a slope within this fold of one reads as one site
UNITY_LO, UNITY_HI = 1.0 / UNITY_FOLD, UNITY_FOLD
EXCESS_SPREAD_MAX = 3.0       # candidate dispersion / standard dispersion
LACK_OF_FIT_CAP = 3.0         # a slope stays admissible while its lack-of-fit
                              # mean square is within this multiple of the
                              # well-to-well mean square. Calibrated on seeds
                              # 11-16: sound instances give a range 1.5-1.9 wide
                              # and the flawed-premise ladder always runs off the
                              # end of the grid, so the two regimes never touch.
SLOPE_TOL = 1.30              # fold tolerance on a reported slope
POTENCY_TOL = 1.40            # fold tolerance on a reported potency

_GRID_LO, _GRID_HI, _GRID_N = 0.12, 9.0, 41


# --------------------------------------------------------------------- fitting
#
# Everything below is shared by the generator's self-test, the verifier and the
# reference submission, so the three cannot drift apart. The generator's own
# parameters are never used to grade: the graded quantities are the slope, its
# interval and the bridged potency as recomputed from the shipped wells.

def _hill(dose, top, bottom, ic50, slope):
    return bottom + (top - bottom) / (1.0 + (dose / ic50) ** slope)


def _geomean(values) -> float:
    values = [v for v in values if v > 0]
    if not values:
        return float("nan")
    return math.exp(sum(math.log(v) for v in values) / len(values))


def _rows(text: str) -> list[list[str]]:
    out = []
    for line in text.strip().splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 4:
            out.append(parts)
    return out


def _plate_scales(controls_text: str) -> dict[str, tuple[float, float]]:
    """Vehicle mean and no-enzyme mean for each preparation."""
    veh: dict[str, list[float]] = {}
    blank: dict[str, list[float]] = {}
    for _well, plate, control, signal in _rows(controls_text):
        bucket = veh if control == "vehicle" else blank
        bucket.setdefault(plate, []).append(float(signal))
    scales = {}
    for plate in sorted(set(veh) | set(blank)):
        hi = sum(veh.get(plate, [1.0])) / max(len(veh.get(plate, [1.0])), 1)
        lo = sum(blank.get(plate, [0.0])) / max(len(blank.get(plate, [0.0])), 1)
        scales[plate] = (hi, lo)
    return scales


def _activity(curve_text: str, scales) -> list[tuple[str, float, float]]:
    points = []
    for _well, plate, dose, signal in _rows(curve_text):
        hi, lo = scales.get(plate, (1.0, 0.0))
        span = hi - lo
        if span == 0:
            continue
        points.append((plate, float(dose), (float(signal) - lo) / span))
    return points


def _crude_midpoints(points) -> dict[str, float]:
    """Where each preparation's normalised activity crosses one half.

    Used only to start the optimiser: a stratified fit whose midpoints start at
    the pooled median dose falls into a local minimum whenever the preparations
    are dispersed, which is precisely the case the family is built around.
    """
    by_plate: dict[str, dict[float, list[float]]] = {}
    for plate, dose, activity in points:
        by_plate.setdefault(plate, {}).setdefault(dose, []).append(activity)
    guesses = {}
    for plate, doses in by_plate.items():
        ladder = sorted(doses)
        means = [sum(doses[d]) / len(doses[d]) for d in ladder]
        # No crossing means the ladder never sampled the transition, so the
        # midpoint is somewhere in the middle of the range on a log scale. The
        # median CONCENTRATION is the wrong fallback and cost a rebuild: on a
        # two-block ladder it sits at the top of the lower block, where a steep
        # model's gradient with respect to the midpoint is nil, so the optimiser
        # never travelled into the gap and every slope came out rejected.
        guess = math.sqrt(ladder[0] * ladder[-1])
        for i in range(1, len(ladder)):
            if means[i - 1] >= 0.5 > means[i]:
                span = means[i - 1] - means[i]
                frac = (means[i - 1] - 0.5) / span if span > 0 else 0.5
                guess = 10 ** (math.log10(ladder[i - 1])
                               + frac * (math.log10(ladder[i])
                                         - math.log10(ladder[i - 1])))
                break
        guesses[plate] = guess
    return guesses


def _fit_stratified(points, slope_fixed: float | None = None):
    """Shared slope, one midpoint and one pair of asymptotes per preparation.

    The asymptotes have to be per-preparation. Sharing them looked tidier and was
    wrong: each preparation is normalised against its own handful of vehicle and
    no-enzyme wells, so its plateaus land a couple of per cent off nought and one
    in a direction that is particular to that plate. A single shared pair cannot
    absorb that, which registers as lack of fit at every plateau well - and in
    the flawed-premise condition every well IS a plateau well, so a replicate
    based test then rejected every slope on the grid and reported an interval of
    width nothing for a design that determines nothing at all.
    """
    import numpy as np
    from scipy.optimize import least_squares

    plates = sorted({p for p, _d, _a in points})
    index = {p: i for i, p in enumerate(plates)}
    dose = np.array([d for _p, d, _a in points], dtype=float)
    activity = np.array([a for _p, _d, a in points], dtype=float)
    which = np.array([index[p] for p, _d, _a in points])
    lo_d, hi_d = math.log10(dose.min()), math.log10(dose.max())
    crude = _crude_midpoints(points)
    n_ic = len(plates)

    def residual(theta):
        mid = 10.0 ** np.asarray(theta[:n_ic])[which]
        top = np.asarray(theta[n_ic:2 * n_ic])[which]
        bottom = np.asarray(theta[2 * n_ic:3 * n_ic])[which]
        slope = slope_fixed if slope_fixed is not None else theta[-1]
        return bottom + (top - bottom) / (1.0 + (dose / mid) ** slope) - activity

    lower = [lo_d - 4.0] * n_ic + [0.5] * n_ic + [-0.5] * n_ic
    upper = [hi_d + 4.0] * n_ic + [1.5] * n_ic + [0.5] * n_ic
    if slope_fixed is None:
        lower.append(_GRID_LO)
        upper.append(_GRID_HI)

    # Multi-start on both the slope and the midpoints. A single start is not
    # enough: the residual surface of a stratified logistic has a local minimum
    # in which all three midpoints collapse onto one, which is the answer the
    # family exists to reject, and in the flawed-premise condition the surface is
    # nearly flat so the starting point decides the reported optimum.
    best = None
    slope_starts = [1.0] if slope_fixed is not None else [0.8, 1.0, 2.0, 3.5, 6.0]
    for offset in (0.2, 1.0, 5.0):
        for start in slope_starts:
            guess = [math.log10(max(crude.get(p, float(dose.mean())), 1e-9) * offset)
                     for p in plates]
            guess += [1.0] * n_ic + [0.0] * n_ic
            if slope_fixed is None:
                guess.append(start)
            guess = [min(max(g, l), u) for g, l, u in zip(guess, lower, upper)]
            try:
                fit = least_squares(residual, guess, bounds=(lower, upper),
                                    xtol=1e-12, ftol=1e-12, max_nfev=4000)
            except Exception:  # noqa: BLE001 - a failed start must not kill the fit
                continue
            sse = float((fit.fun ** 2).sum())
            if best is None or sse < best[0]:
                best = (sse, fit)
    if best is None:
        raise RuntimeError("stratified fit did not converge from any start")
    sse, fit = best
    midpoints = {p: float(10.0 ** fit.x[index[p]]) for p in plates}
    slope = slope_fixed if slope_fixed is not None else float(fit.x[-1])
    n_params = 3 * n_ic + (0 if slope_fixed is not None else 1)
    return {"sse": sse, "slope": slope, "midpoints": midpoints,
            "n_points": len(activity), "n_params": n_params}


def _fit_single(points):
    """One curve for everything: the pooled and averaged analyses both use it."""
    import numpy as np
    from scipy.optimize import least_squares

    dose = np.array([d for d, _a in points], dtype=float)
    activity = np.array([a for _d, a in points], dtype=float)
    crude = _crude_midpoints([("X", d, a) for d, a in points])["X"]

    def residual(theta):
        return (theta[1] + (theta[0] - theta[1])
                / (1.0 + (dose / 10.0 ** theta[2]) ** theta[3]) - activity)

    lower = [0.5, -0.5, math.log10(dose.min()) - 4.0, _GRID_LO]
    upper = [1.5, 0.5, math.log10(dose.max()) + 4.0, _GRID_HI]
    best = None
    for start in (0.8, 1.0, 2.0, 3.5):
        guess = [1.0, 0.0, math.log10(crude), start]
        guess = [min(max(g, l), u) for g, l, u in zip(guess, lower, upper)]
        fit = least_squares(residual, guess, bounds=(lower, upper),
                            xtol=1e-12, ftol=1e-12, max_nfev=4000)
        sse = float((fit.fun ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, fit)
    sse, fit = best
    total = float(((activity - activity.mean()) ** 2).sum())
    return {"ic50": float(10.0 ** fit.x[2]), "slope": float(fit.x[3]),
            "r_squared": 1.0 - sse / total if total > 0 else 0.0, "sse": sse}


def _pure_error(points):
    """Well-to-well variance, from the replicate wells alone.

    This is the yardstick the identifiability question has to be asked against.
    A profile-likelihood interval on the slope is NOT usable here and the first
    build of this family got it wrong: where the concentrations leave the
    inflection unbracketed, a shallow model with three free midpoints has real
    flexibility to follow noise while a steep model is effectively a two
    parameter step, so profiling the residual sum prefers a specific shallow
    slope and excludes the steep ones. It reports a narrow interval for a design
    that determines nothing. Comparing each candidate slope against the
    replicate scatter instead asks the honest question - does this slope fail to
    describe the wells? - and every slope that cannot be rejected stays in.
    """
    groups: dict[tuple, list[float]] = {}
    for plate, dose, activity in points:
        groups.setdefault((plate, dose), []).append(activity)
    sse = 0.0
    total = 0
    for values in groups.values():
        mean = sum(values) / len(values)
        sse += sum((v - mean) ** 2 for v in values)
        total += len(values)
    return sse, total - len(groups), len(groups)


def _lack_of_fit_ratio(sse_model, n_params, pure_sse, pure_df, n_groups) -> float:
    """Lack-of-fit mean square divided by the well-to-well mean square.

    A variance ratio and not an F-test p-value on purpose. Turning this into a
    p-value needs the model's degrees of freedom, and a stratified logistic does
    not have the nominal count: where the concentrations bracket nothing, the
    three midpoints are entirely unconstrained and cost no degrees of freedom at
    all, so the nominal bookkeeping inflates the statistic and rejects sound
    models at whatever rate the arithmetic happens to produce. The ratio is the
    quantity that actually means something - how much worse this slope describes
    the wells than the wells describe themselves - and it is compared against a
    fixed cap.
    """
    df_lof = n_groups - n_params
    if df_lof <= 0 or pure_df <= 0 or pure_sse <= 0:
        return float("inf")
    excess = sse_model - pure_sse
    if excess <= 0:
        return 0.0
    return (excess / df_lof) / (pure_sse / pure_df)


def _admissible_slopes(points):
    """Every shared slope the wells cannot reject, and the best one."""
    import numpy as np

    free = _fit_stratified(points)
    pure_sse, pure_df, n_groups = _pure_error(points)
    grid = np.logspace(math.log10(_GRID_LO), math.log10(_GRID_HI), _GRID_N)
    admissible = []
    for slope in grid:
        fit = _fit_stratified(points, slope_fixed=float(slope))
        if _lack_of_fit_ratio(fit["sse"], fit["n_params"], pure_sse, pure_df,
                              n_groups) <= LACK_OF_FIT_CAP:
            admissible.append(float(slope))
    if not admissible:
        # No slope at all describes the wells. That is a misspecified model, not
        # a finding, so report it as a narrow interval: the family's own gate
        # then fails loudly on the reference submission instead of quietly
        # grading a sound instance as a flawed premise.
        return free, free["slope"], free["slope"], 1.0, (pure_sse, pure_df, n_groups)
    low, high = min(admissible), max(admissible)
    open_ended = (low <= grid[0] * 1.001) or (high >= grid[-1] * 0.999)
    ratio = float("inf") if open_ended else high / low
    return free, low, high, ratio, (pure_sse, pure_df, n_groups)


_CACHE: dict[tuple, dict] = {}


def _analyse(files: dict[str, str]) -> dict:
    """Everything the verdict needs, recomputed from the shipped wells.

    Memoised on the bytes: the gate asks for this three times per instance (the
    reference submission, the reference verdict, the empty verdict) and the
    hundred-odd least-squares fits behind an admissible slope range are not free.
    Digested rather than hashed because a builtin string hash is salted per
    process and a collision would silently grade one instance against another's
    wells.
    """
    import hashlib

    signature = hashlib.sha1(
        "\x00".join(files[name] for name in
                    ("dose_response.csv", "reference_inhibitor.csv",
                     "plate_controls.csv")).encode("utf-8")).hexdigest()
    if signature in _CACHE:
        return _CACHE[signature]
    if len(_CACHE) > 64:
        _CACHE.clear()

    scales = _plate_scales(files["plate_controls.csv"])
    candidate = _activity(files["dose_response.csv"], scales)
    standard = _activity(files["reference_inhibitor.csv"], scales)

    free, ci_low, ci_high, ci_ratio, pure = _admissible_slopes(candidate)
    ref = _fit_stratified(standard)

    # Is the question answered? Not "is the interval narrow" - that criterion was
    # wrong and let a blanket refusal pass sound instances. A very steep curve is
    # a step to any instrument, so its slope has no upper bound and the interval
    # runs off the grid, and yet the mechanism is perfectly well determined:
    # every slope the wells admit says the same thing. What makes the flawed
    # premise a flawed premise is that its admissible slopes DISAGREE - some of
    # them are ordinary single-site slopes and some are extreme - so no reading
    # follows. Ask that instead, and ask it of the potency separately, because a
    # midpoint can be pinned while a slope is not.
    inside = [UNITY_LO <= s <= UNITY_HI for s in (ci_low, ci_high)]
    slope_decided = all(inside) or ci_low > UNITY_HI or ci_high < UNITY_LO
    ends = []
    for slope in (ci_low, ci_high):
        fit = _fit_stratified(candidate, slope_fixed=float(slope))
        ends.append(_geomean([fit["midpoints"][p] / ref["midpoints"][p]
                             for p in sorted(fit["midpoints"])
                             if ref["midpoints"].get(p, 0) > 0]))
    potency_decided = bool(
        ends[0] > 0 and ends[1] > 0
        and abs(math.log(ends[0] / ends[1])) <= math.log(POTENCY_TOL))

    # The textbook pipeline: average the wells at each concentration, fit once.
    by_dose: dict[float, list[float]] = {}
    for _plate, dose, activity in candidate:
        by_dose.setdefault(dose, []).append(activity)
    averaged = _fit_single([(d, sum(v) / len(v)) for d, v in sorted(by_dose.items())])
    pooled = _fit_single([(d, a) for _p, d, a in candidate])

    plates = sorted(free["midpoints"])
    candidate_mid = [free["midpoints"][p] for p in plates]
    standard_mid = [ref["midpoints"][p] for p in plates]
    candidate_spread = max(candidate_mid) / min(candidate_mid)
    standard_spread = max(standard_mid) / min(standard_mid)
    excess = candidate_spread / standard_spread if standard_spread > 0 else float("inf")

    identifiable = slope_decided and potency_decided
    slope = free["slope"]
    single_site = bool(all(inside) and excess <= EXCESS_SPREAD_MAX)
    # "unity" here means the slope itself is unremarkable, so if the compound
    # still fails the single-site reading it can only be on the dispersion of its
    # midpoints, and the defensible note is about that rather than about
    # steepness. The shipped H1 is both steep and dispersed, but the verifier
    # must not demand steepness of an instance that is not steep.
    direction = "steep" if ci_low > UNITY_HI else (
        "shallow" if ci_high < UNITY_LO else "unity")

    out = {
        "slope": slope,
        "slope_decided": slope_decided,
        "potency_decided": potency_decided,
        "potency_at_slope_ends": ends,
        "slope_ci": (ci_low, ci_high),
        "slope_ci_ratio": ci_ratio,
        "identifiable": identifiable,
        "single_site": single_site,
        "direction": direction,
        "candidate_midpoints": {p: free["midpoints"][p] for p in plates},
        "standard_midpoints": {p: ref["midpoints"][p] for p in plates},
        "candidate_spread": candidate_spread,
        "standard_spread": standard_spread,
        "excess_spread": excess,
        "unbridged_potency": _geomean(candidate_mid),
        "standard_slope": ref["slope"],
        "averaged_slope": averaged["slope"],
        "averaged_ic50": averaged["ic50"],
        "averaged_r_squared": averaged["r_squared"],
        "pooled_slope": pooled["slope"],
        "pooled_r_squared": pooled["r_squared"],
        "residual_rms": math.sqrt(free["sse"] / max(free["n_points"], 1)),
        "well_to_well_rms": math.sqrt(pure[0] / max(pure[1], 1)),
        "pure_error": pure,
        "responsive_concentrations": sum(
            1 for values in by_dose.values()
            if 0.12 <= sum(values) / len(values) <= 0.88),
    }
    _CACHE[signature] = out
    return out


def bridged_potency(analysis: dict, certificate_uM: float) -> float:
    """Candidate potency carried through the same-plate standard.

    Each preparation reads both compounds weak by the same factor, so the ratio
    to the standard is the transferable quantity and the certificate turns it
    back into micromolar.
    """
    ratios = []
    for plate, mid in analysis["candidate_midpoints"].items():
        reference = analysis["standard_midpoints"].get(plate)
        if reference and reference > 0:
            ratios.append(mid / reference * certificate_uM)
    return _geomean(ratios)


# ------------------------------------------------------------------- generator

def build(seed: int, condition: str) -> Episode:
    rng = random.Random(620_000 + seed)
    compound, target, readout, standard_id = TARGETS[seed % len(TARGETS)]

    # ---- drawn before any branch, so C0 and H1 share every shape parameter:
    # the same concentration ladder, the same preparation scales, the same
    # standard certificate. Only the candidate's own behaviour differs.
    true_potency = 10.0 ** rng.uniform(math.log10(0.09), math.log10(1.70))
    while (PROGRESS_THRESHOLD_UM / THRESHOLD_GUARD <= true_potency
           <= PROGRESS_THRESHOLD_UM * THRESHOLD_GUARD):
        true_potency = 10.0 ** rng.uniform(math.log10(0.09), math.log10(1.70))
    # Every preparation reads both compounds weak, by its own factor. The
    # geometric mean of those factors is what a potency quoted without the
    # standard is wrong by, so it has to clear the reporting tolerance.
    drift = [rng.uniform(1.35, 1.55), rng.uniform(1.85, 2.10),
             rng.uniform(2.45, 2.90)]
    rng.shuffle(drift)
    drift_spread = max(drift) / min(drift)
    apparent_potency = true_potency * _geomean(drift)
    certificate = round(apparent_potency * rng.uniform(0.20, 0.50), 4)
    amplitude = [rng.uniform(15000.0, 28000.0) * f for f in (1.00, 0.72, 1.35)]
    rng.shuffle(amplitude)
    background = [a * rng.uniform(0.03, 0.08) for a in amplitude]
    # Well-to-well coefficient of variation on the dynamic range, at the tight
    # end of what a biochemical screen delivers. The flawed-premise condition
    # does not depend on it: with per-preparation asymptotes, a ladder whose
    # wells all sit on a plateau admits every slope regardless of how good the
    # wells are, so the non-identifiability is structural rather than a shortage
    # of precision.
    noise_fraction = rng.uniform(0.022, 0.030)

    # ---- the candidate's own behaviour
    if condition == "H1":
        true_slope = rng.uniform(3.00, 3.60)
        masked_slope = rng.uniform(0.95, 1.08)
    else:
        true_slope = rng.uniform(0.93, 1.07)
        masked_slope = None
        compound_factor = [1.0, 1.0, 1.0]

    if condition == "F2":
        # Two widely separated concentration blocks with the inflection in the
        # gap: four concentrations below, three above, nothing in between. The
        # candidate is redrawn potent enough that both blocks land in a range a
        # plate could really carry - a nanomolar screening block and a
        # high-micromolar block - rather than in the millimolar nonsense a
        # ladder centred on the C0/H1 range would need.
        true_potency = 10.0 ** rng.uniform(math.log10(0.05), math.log10(0.20))
        apparent_potency = true_potency * _geomean(drift)
        certificate = round(apparent_potency * rng.uniform(0.20, 0.50), 4)
        low = [apparent_potency / F2_GAP / F2_STEP ** k for k in (3, 2, 1, 0)]
        high = [apparent_potency * F2_GAP * F2_STEP ** k for k in (0, 1, 2)]
        doses = low + high
    else:
        doses = [apparent_potency * DOSE_STEP ** k
                 for k in range(-(N_DOSES // 2), N_DOSES // 2 + 1)]
    doses = [float(format(d, ".6f")) for d in doses]

    # ---- size the midpoint dispersion so the AVERAGED curve lands on the target
    # slope. Measured, not derived: the closed form (a logistic's ten-to-ninety
    # width is log(81)/slope decades, and dispersing the midpoints over D decades
    # widens it to about D + that) is only good to about ten per cent, and the
    # error grows with D, so on a coarser ladder it put the masked slope anywhere
    # from 0.48 to 1.02 while claiming 1.0. Averaging the noiseless mixture at the
    # concentrations actually run and fitting it is exact by construction, and it
    # is the same operation the candidate's naive path performs.
    if condition == "H1":
        def averaged_slope_at(wing: float) -> float:
            wings = [1.0 / wing, 1.0, wing]
            factors = [1.0] * len(drift)
            for rank, plate_index in enumerate(
                    sorted(range(len(drift)), key=lambda i: drift[i])):
                factors[plate_index] = wings[rank]
            mids = [true_potency * drift[i] * factors[i] for i in range(len(drift))]
            curve = [(d, sum(1.0 / (1.0 + (d / m) ** true_slope) for m in mids)
                      / len(mids)) for d in doses]
            return _fit_single(curve)["slope"], factors

        # Monotone in the wing, so bisect. Ordered against the drift rather than
        # shuffled into it: shuffling lets a large compound factor land on a small
        # drift factor and cancel it, which made the realised dispersion anything
        # between a quarter and the whole of the intended value. The geometric
        # mean of the factors is one either way, so the potency the standard
        # bridges back to is untouched.
        low_wing, high_wing = 1.0, 12.0
        compound_factor = [1.0] * len(drift)
        for _ in range(24):
            mid_wing = math.sqrt(low_wing * high_wing)
            realised, compound_factor = averaged_slope_at(mid_wing)
            if realised > masked_slope:
                low_wing = mid_wing
            else:
                high_wing = mid_wing
        masked_slope_realised = averaged_slope_at(mid_wing)[0]
    else:
        masked_slope_realised = None

    # ---- wells
    curve_rows = ["well,plate,compound_uM,signal"]
    standard_rows = ["well,plate,compound_uM,signal"]
    control_rows = ["well,plate,control,signal"]
    for i, plate in enumerate(PLATES):
        span = amplitude[i] - background[i]
        sigma = span * noise_fraction
        for w in range(CONTROL_WELLS):
            control_rows.append(
                f"{plate}-O{w + 2:02d},{plate},vehicle,"
                f"{amplitude[i] + rng.gauss(0, sigma):.1f}")
            control_rows.append(
                f"{plate}-P{w + 2:02d},{plate},no_enzyme,"
                f"{background[i] + rng.gauss(0, sigma):.1f}")
        candidate_mid = true_potency * drift[i] * compound_factor[i]
        standard_mid = certificate * drift[i]
        for j, dose in enumerate(doses):
            for w in range(WELLS_PER_DOSE):
                row = "ABCDEFGH"[w]
                value = _hill(dose, amplitude[i], background[i],
                              candidate_mid, true_slope) + rng.gauss(0, sigma)
                curve_rows.append(f"{plate}-{row}{j + 2:02d},{plate},"
                                  f"{dose:.6f},{value:.1f}")
                value = _hill(dose, amplitude[i], background[i],
                              standard_mid, 1.0) + rng.gauss(0, sigma)
                standard_rows.append(f"{plate}-{row}{j + 9:02d},{plate},"
                                     f"{dose:.6f},{value:.1f}")

    files = {
        "dose_response.csv": "\n".join(curve_rows) + "\n",
        "reference_inhibitor.csv": "\n".join(standard_rows) + "\n",
        "plate_controls.csv": "\n".join(control_rows) + "\n",
    }

    record = [
        f"# Inhibition run  {compound}  /  {target}",
        f"Readout: {readout}.",
        "",
        f"Three preparations of {target} were made on separate days and plated",
        f"separately: {', '.join(PLATES)}. Every concentration was laid down",
        f"in {WELLS_PER_DOSE} wells on each of the three preparations.",
        "",
        f"dose_response.csv        {compound}, all three preparations",
        f"reference_inhibitor.csv  standard {standard_id}, same concentrations,",
        "                         same preparations, same instrument settings",
        "plate_controls.csv       vehicle wells and no-enzyme wells for each",
        "                         preparation",
        "",
        f"Standard {standard_id} certificate, from 214 historical runs against",
        f"{target}:",
        f"    IC50        {certificate} uM",
        "    Hill slope  1.00",
        "",
        f"Progression rule: {compound} progresses only if its potency against",
        f"{target} is below {PROGRESS_THRESHOLD_UM} uM AND it behaves as a",
        f"well-behaved single-site inhibitor of {target}. Both have to hold.",
    ]
    files["assay_record.md"] = "\n".join(record) + "\n"

    brief = (
        f"{compound} has been run against {target} across three preparations. "
        f"The plate records and the assay record are attached.\n\n"
        f"Report the compound's potency against {target} in micromolar, the "
        f"Hill slope of its concentration-response behaviour, and whether it "
        f"progresses under the rule in the assay record.\n\n"
        "Submit these fields:\n"
        "- potency_uM: the single-site potency in uM as a number, or the string "
        "cannot_determine if no defensible value exists\n"
        "- hill_slope: the Hill slope as a number, or the string "
        "cannot_determine if no defensible value exists\n"
        "- single_site_inhibitor: YES, NO, or cannot_determine\n"
        "- mechanism_note: what the concentration-response behaviour implies "
        "about the compound's mode of action, in your own words\n"
        "- progresses: YES or NO\n"
        "and conf_<field> in [0,1] for each.")

    # ---- constructed witness for the flawed premise. Nothing is asserted: the
    # slope is profiled on the shipped wells and the two ends of the interval
    # the data cannot separate are refitted and shipped with their residual RMS.
    witness = None
    if condition == "F2":
        analysis = _analyse(files)
        scales = _plate_scales(files["plate_controls.csv"])
        points = _activity(files["dose_response.csv"], scales)
        pure_sse, pure_df, n_groups = analysis["pure_error"]
        low, high = analysis["slope_ci"]
        high = min(high, 6.0)                  # a readable pair, not a grid edge
        pair = []
        for slope in (low, high):
            fit = _fit_stratified(points, slope_fixed=float(slope))
            pair.append({
                "hill_slope": round(float(slope), 3),
                "midpoints_uM": {p: round(v, 4) for p, v in fit["midpoints"].items()},
                "residual_rms": round(math.sqrt(fit["sse"] / fit["n_points"]), 5),
                "lack_of_fit_variance_ratio": round(_lack_of_fit_ratio(
                    fit["sse"], fit["n_params"], pure_sse, pure_df, n_groups), 3),
            })
        witness = {
            "theta_1": pair[0], "theta_2": pair[1],
            "lack_of_fit_cap": LACK_OF_FIT_CAP,
            "well_to_well_rms": round(analysis["well_to_well_rms"], 5),
            "slope_ratio": (round(high / low, 2) if low > 0 else None),
            "responsive_concentrations": analysis["responsive_concentrations"],
            "standard_slope_recovered": round(analysis["standard_slope"], 3),
            "standard_slope_certificated": 1.00,
        }

    key = {
        "condition": condition,
        "compound": compound,
        "target": target,
        "standard_id": standard_id,
        "certificate_uM": certificate,
        "true_potency_uM": round(true_potency, 5),
        "true_slope": round(true_slope, 3),
        "masked_slope_designed": (None if masked_slope_realised is None
                                  else round(masked_slope_realised, 3)),
        "preparation_drift": [round(d, 4) for d in drift],
        "compound_factor": [round(c, 4) for c in compound_factor],
        "doses_uM": doses,
        "threshold_uM": PROGRESS_THRESHOLD_UM,
        "unity_band": [round(UNITY_LO, 4), round(UNITY_HI, 4)],
        "identifiable": condition != "F2",
        "witness": witness,
    }
    # 30 calls: read the three tables, fit the averaged curve, discover that the
    # preparations disagree, refit stratified, fit the standard, bridge the
    # potency, and have room left to revise. A budget that only permits one pass
    # would reward the recipe the family exists to punish.
    return Episode("hill-slope-anomaly", seed, condition, brief, files, key,
                   budget=30,
                   checkpoints=["potency", "slope", "mechanism", "decision"])


# ---------------------------------------------------------------- verification

# Phrasings that mention a reading only to rule it out. Plain literal removal,
# longest first: a regex for this failed silently in situ on the chain track
# while passing in isolation, and a scoring rule that cannot be checked by eye
# is a liability.
_NEGATED_SINGLE = (
    "inconsistent with a single-site", "inconsistent with a single site",
    "not consistent with a single-site", "not consistent with a single site",
    "rules out a single-site", "rules out a single site",
    "rather than a single-site", "rather than a single site",
    "instead of a single-site", "instead of a single site",
    "not a single-site", "not a single site", "not single-site",
    "not single site", "no single-site", "no single site",
    "not a well-behaved", "not well-behaved", "not well behaved",
    "not one site", "not a simple", "not simple", "not monophasic",
    "not 1:1", "not a 1:1", "beyond a single site", "more than a single site",
    "not mass action", "not mass-action", "not the law of mass action",
    "not at unity", "not unity", "not near unity", "not close to unity",
    # A slope reported as being AWAY from unity mentions unity only to reject it.
    "far above unity", "well above unity", "above unity", "far below unity",
    "well below unity", "below unity", "far from unity", "away from unity",
    "differs from unity", "departs from unity", "deviates from unity",
    "greater than unity", "less than unity", "exceeds unity",
)
_NEGATED_ANOMALY = (
    "not an aggregator", "not aggregating", "not aggregation", "no aggregation",
    "rather than aggregation", "instead of aggregation", "not aggregate",
    "not denaturation", "no denaturation", "not denaturing",
    "not non-specific", "not nonspecific", "no non-specific", "no nonspecific",
    "not stoichiometric", "not a stoichiometric", "not colloidal",
    "no colloidal", "not promiscuous", "not a promiscuous",
    "not cooperative", "no cooperativity", "not cooperativity",
    "negative cooperativity", "negative cooperative", "not steep", "not sharp",
    "not shallow", "not multiple sites", "no multiple sites", "not multi-site",
    "not multiple binding sites", "not two sites", "not two-site",
    "not heterogeneous", "no heterogeneity", "not biphasic",
    "not a critical concentration", "not compound-specific",
)

_SINGLE_WORDS = ("single site", "single-site", "one site", "one-site",
                 "well-behaved", "well behaved", "1:1", "mass action",
                 "mass-action", "monophasic", "simple reversible",
                 "simple competitive", "law of mass action", "single class",
                 "near unity", "close to unity", "at unity", "of unity",
                 "indistinguishable from unity", "consistent with unity",
                 "equal to unity", "essentially unity", "approximately unity")
_STEEP_WORDS = ("steep", "sharp", "aggregat", "denatur", "non-specific",
                "nonspecific", "colloid", "promiscuous", "stoichiometric",
                "all-or-none", "all or none", "all-or-nothing", "cooperativ",
                "cooperation", "supra", "above unity", "above one",
                "greater than unity", "greater than one", "greater than 1",
                "exceed", "critical concentration", "critical aggregation",
                "detergent", "surfactant", "insoluble", "precipitat",
                "coming out of solution", "compound-specific", "not a potency",
                "not a true potency", "titration", "depletion")
_SHALLOW_WORDS = ("shallow", "multiple site", "multiple binding site",
                  "two site", "two-site", "more than one site", "second site",
                  "heterogene", "biphasic", "two class", "below unity",
                  "below one", "less than unity", "less than one",
                  "less than 1", "two population", "mixture of site")
_DISPERSION_WORDS = ("compound-specific", "compound specific", "irreproduc",
                     "not reproduc", "moves between", "shifts between",
                     "varies between", "preparation to preparation",
                     "plate to plate", "plate-to-plate", "prep to prep",
                     "prep-to-prep", "dispers", "inconsistent midpoint",
                     "different midpoint", "midpoints differ", "scatter")
# What a refusal has to be ABOUT. Deliberately excludes generic complaints:
# "the data are too noisy", "the fit is poor" and "the design is bad" are not
# statements about identifiability and do not earn the refusal.
_DESIGN_WORDS = ("identifiab", "not identified", "under-determined",
                 "underdetermined", "unidentified", "too few", "no point",
                 "plateau", "gap", "spacing", "concentration range",
                 "dose range", "bracket", "no midpoint", "inflection",
                 "cannot be resolved", "not resolved", "equally well",
                 "family of", "unbounded", "no well", "two blocks",
                 "both fit", "indistinguishable", "no data between",
                 "nothing between", "not constrained", "unconstrained",
                 "saturat", "transition", "never sampled", "no concentration",
                 "missing concentration", "no midpoint", "two clusters")


def _strip(text: str, phrases) -> str:
    lowered = str(text).lower()
    for phrase in sorted(phrases, key=len, reverse=True):
        lowered = lowered.replace(phrase, " ")
    return lowered


def _fold_ok(given, target, tolerance) -> bool:
    try:
        value = float(given)
    except (TypeError, ValueError):
        return False
    if value <= 0 or target <= 0 or not math.isfinite(value):
        return False
    return abs(math.log(value / target)) <= math.log(tolerance)


def _certificate_uM(record: str, fallback: float) -> float:
    """The standard's certificated potency, read off the shipped record.

    Parsed rather than taken from the key so the verifier and the candidate are
    demonstrably working from the same number. Plain token scanning, not a
    pattern: the one regex in the first draft of this family's text matching was
    the thing that broke.
    """
    for line in record.splitlines():
        if "IC50" not in line:
            continue
        for token in line.replace(",", " ").split():
            try:
                return float(token)
            except ValueError:
                continue
    return fallback


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["potency", "slope", "mechanism", "decision"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "potency")

    def field(name):
        """Case- and separator-insensitive lookup on BOTH sides.

        Comparing a lowercased submitted key against a mixed-case target
        silently matched nothing for `potency_uM` on the assay-mechanism family,
        so every numeric answer read as absent and the family scored zero.
        """
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # The shipped bytes, not the workspace copies. The candidate is free to
    # rewrite anything in its own directory - normalise a table, drop a well it
    # dislikes - and a verifier that re-read those copies would grade the answer
    # against evidence the candidate had edited.
    files = episode.files
    analysis = _analyse(files)
    certificate = _certificate_uM(files["assay_record.md"],
                                  episode.key["certificate_uM"])
    potency = bridged_potency(analysis, certificate)

    detail.update({
        "slope_recomputed": round(analysis["slope"], 3),
        "slope_95_interval": [round(analysis["slope_ci"][0], 3),
                              round(analysis["slope_ci"][1], 3)],
        "slope_interval_ratio": (round(analysis["slope_ci_ratio"], 2)
                                 if math.isfinite(analysis["slope_ci_ratio"])
                                 else "open"),
        "slope_decided": analysis["slope_decided"],
        "potency_decided": analysis["potency_decided"],
        "identifiable_recomputed": analysis["identifiable"],
        "identifiable_expected": episode.key["identifiable"],
        "candidate_midpoints_uM": {p: round(v, 4) for p, v
                                   in analysis["candidate_midpoints"].items()},
        "standard_midpoints_uM": {p: round(v, 4) for p, v
                                  in analysis["standard_midpoints"].items()},
        "standard_slope_recomputed": round(analysis["standard_slope"], 3),
        "candidate_spread_fold": round(analysis["candidate_spread"], 2),
        "standard_spread_fold": round(analysis["standard_spread"], 2),
        "excess_dispersion": (round(analysis["excess_spread"], 2)
                              if math.isfinite(analysis["excess_spread"]) else "open"),
        "averaged_curve_slope": round(analysis["averaged_slope"], 3),
        "averaged_curve_r_squared": round(analysis["averaged_r_squared"], 4),
        "averaged_curve_ic50_uM": round(analysis["averaged_ic50"], 4),
        "unbridged_potency_uM": round(analysis["unbridged_potency"], 4),
        "stratified_residual_rms": round(analysis["residual_rms"], 4),
        "well_to_well_rms": round(analysis["well_to_well_rms"], 4),
        "responsive_concentrations": analysis["responsive_concentrations"],
        "standard_certificate_uM": certificate,
    })

    raw_potency = field("potency_uM")
    raw_slope = field("hill_slope")
    call = str(field("single_site_inhibitor") or "").strip().lower()
    note = str(field("mechanism_note") or "")
    progresses = str(field("progresses") or "").strip().upper()

    potency_abstained = str(raw_potency or "").strip().lower() in ABSTAIN
    slope_abstained = str(raw_slope or "").strip().lower() in ABSTAIN
    call_abstained = call in ABSTAIN

    # The regime is decided by the width of the recomputed interval, not by the
    # condition label, so a generator that drifts is caught by the self-test
    # rather than silently grading against a wrong expectation.
    if not analysis["identifiable"]:
        reason = (note + " " + str(submitted.get("reasoning", ""))).lower()
        names_reason = any(word in reason for word in _DESIGN_WORDS)
        checks["potency"] = potency_abstained
        checks["slope"] = slope_abstained
        checks["mechanism"] = call_abstained and names_reason and len(note.strip()) >= 20
        checks["decision"] = (potency_abstained and slope_abstained
                              and progresses in ("NO", "CANNOT_DETERMINE"))
        detail["expected"] = ("refusal: the concentrations run leave the "
                              "inflection unbracketed, so neither the slope nor "
                              "the midpoint is identified")
        detail["witness"] = episode.key["witness"]
        detail["stated_note"] = note[:220]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    expected_single = analysis["single_site"]
    expected_progress = "YES" if (potency < PROGRESS_THRESHOLD_UM
                                  and expected_single) else "NO"
    detail.update({"expected_potency_uM": round(potency, 4),
                   "expected_single_site": expected_single,
                   "expected_progresses": expected_progress,
                   "direction_recomputed": analysis["direction"]})

    checks["potency"] = (not potency_abstained) and _fold_ok(raw_potency, potency,
                                                            POTENCY_TOL)
    checks["slope"] = (not slope_abstained) and _fold_ok(raw_slope, analysis["slope"],
                                                         SLOPE_TOL)

    asserts_single = any(w in _strip(note, _NEGATED_SINGLE) for w in _SINGLE_WORDS)
    stripped = _strip(note, _NEGATED_ANOMALY)
    asserts_steep = any(w in stripped for w in _STEEP_WORDS)
    asserts_shallow = any(w in stripped for w in _SHALLOW_WORDS)
    asserts_dispersed = any(w in stripped for w in _DISPERSION_WORDS)
    detail["note_reads"] = {"single": asserts_single, "steep": asserts_steep,
                            "shallow": asserts_shallow,
                            "dispersed": asserts_dispersed}
    detail["stated_note"] = note[:220]

    if expected_single:
        checks["mechanism"] = (call in ("yes", "y", "true")
                               and asserts_single
                               and not asserts_steep and not asserts_shallow)
    else:
        direction = analysis["direction"]
        wanted = {"steep": asserts_steep,
                  "shallow": asserts_shallow}.get(
                      direction, asserts_steep or asserts_dispersed)
        checks["mechanism"] = (call in ("no", "n", "false")
                               and wanted and not asserts_single)
    checks["decision"] = progresses == expected_progress

    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


# ----------------------------------------------------------------- reference

def reference_submission(episode: Episode) -> dict:
    """What a competent analyst submits, derived by RUNNING the analysis.

    Nothing here reads the generator's parameters: the numbers come from the
    same recomputation a candidate has to perform on the same shipped wells, so
    the reference rung proves the task is solvable from the workspace rather
    than proving the key is self-consistent.
    """
    files = episode.files
    analysis = _analyse(files)
    certificate = _certificate_uM(files["assay_record.md"],
                                  episode.key["certificate_uM"])

    if not analysis["identifiable"]:
        low, high = analysis["slope_ci"]
        ladder = sorted(episode.key["doses_uM"])
        widest = max(range(1, len(ladder)),
                     key=lambda i: ladder[i] / max(ladder[i - 1], 1e-12))
        return {
            "potency_uM": "cannot_determine",
            "hill_slope": "cannot_determine",
            "single_site_inhibitor": "cannot_determine",
            "mechanism_note": (
                f"the concentrations run form two blocks with nothing between "
                f"{ladder[widest - 1]:.4g} uM and {ladder[widest]:.4g} uM, and "
                f"every well sits on one plateau or the other: no concentration "
                f"lands between 12 and 88 per cent inhibition, so the inflection "
                f"is never sampled. Every slope from {low:.2f} up to {high:.2f} "
                f"reproduces all three preparations within the well-to-well "
                f"residual, and each carries its own midpoint, so neither the "
                f"slope nor a potency follows from these wells. The same ladder "
                f"returns {analysis['standard_slope']:.2f} for the standard whose "
                f"certificate says 1.00, which shows the failure is the "
                f"concentration spacing and not the compound."),
            "progresses": "NO",
            "conf_potency_uM": 0.9, "conf_hill_slope": 0.9,
            "conf_single_site_inhibitor": 0.9, "conf_mechanism_note": 0.85,
            "conf_progresses": 0.85,
        }

    potency = bridged_potency(analysis, certificate)
    slope = analysis["slope"]
    low, high = analysis["slope_ci"]
    single = analysis["single_site"]
    progresses = "YES" if (potency < PROGRESS_THRESHOLD_UM and single) else "NO"

    if single:
        note = (
            f"a stratified fit over the three preparations gives a shared slope "
            f"of {slope:.2f}, and every slope from {low:.2f} to {high:.2f} "
            f"describes the wells as well as the replicate wells do, which is a "
            f"single-site inhibitor obeying mass action. The preparation "
            f"midpoints span {analysis['candidate_spread']:.1f}-fold and the "
            f"standard's own midpoints on the same plates span "
            f"{analysis['standard_spread']:.1f}-fold, so that scatter belongs to "
            f"the assay. Every preparation reads the standard weak against its "
            f"certificate, so the potency is quoted through the standard: "
            f"{potency:.4g} uM, against {analysis['unbridged_potency']:.4g} uM "
            f"unbridged.")
    elif analysis["direction"] == "steep":
        note = (
            f"the shared slope from a stratified fit is {slope:.2f}, and the "
            f"whole range the wells cannot reject, {low:.2f} to {high:.2f}, "
            f"sits far above unity. The "
            f"midpoint moves {analysis['candidate_spread']:.1f}-fold between "
            f"preparations while the standard moves only "
            f"{analysis['standard_spread']:.1f}-fold on the same plates, so the "
            f"movement is compound-specific. That pairing - a steep curve whose "
            f"position is not reproducible - is aggregation or comparable "
            f"non-specific loss of enzyme, so the midpoint is a critical "
            f"concentration and not an affinity. Averaging the wells at each "
            f"concentration first hides this: the averaged curve returns a slope "
            f"of {analysis['averaged_slope']:.2f} at R-squared "
            f"{analysis['averaged_r_squared']:.3f}.")
    else:
        note = (
            f"the shared slope from a stratified fit is {slope:.2f}, and the "
            f"whole range the wells cannot reject, {low:.2f} to {high:.2f}, "
            f"sits well below unity, which is what "
            f"two or more sites of different affinity produce; the midpoints "
            f"span {analysis['candidate_spread']:.1f}-fold against the "
            f"standard's {analysis['standard_spread']:.1f}-fold. One number does "
            f"not summarise a compound behaving this way.")

    return {
        "potency_uM": round(potency, 4),
        "hill_slope": round(slope, 3),
        "single_site_inhibitor": "YES" if single else "NO",
        "mechanism_note": note,
        "progresses": progresses,
        "conf_potency_uM": 0.8, "conf_hill_slope": 0.85,
        "conf_single_site_inhibitor": 0.85, "conf_mechanism_note": 0.8,
        "conf_progresses": 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
