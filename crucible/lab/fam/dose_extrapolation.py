"""Family: recommending a dose from a dose-escalation exposure study.

Written against the collaborator critique of the first family batch
(analysis/collab/hardening__gpt.md), which diagnosed the saturation exactly:
the early families were "canonical audit recipes with a conspicuous local
defect", and frontier models execute those reliably. The prescription was to
stop hiding an answer and instead ship *several superficially adequate
analyses that imply different decisions, plus controls that make exactly one
of them defensible*, with F2 backed by an explicit non-identifiability witness
rather than by poor data quality.

So the observable here - a single-ascending-dose exposure table - is
deliberately compatible with three analyses that every PK group runs and that
disagree about the dose:

  * dose proportionality (exposure = k x dose), the assumption behind every
    "scale the dose by the exposure ratio" calculation;
  * the regulatory empirical power model (exposure = c x dose^g), which
    absorbs mild super-proportionality without any mechanism;
  * capacity-limited elimination, where a Michaelis-Menten pathway makes
    single-dose exposure rise as a x dose + b x dose^2 - the closed form for
    one-compartment saturable elimination - so clearance falls as dose rises.

The generator's liberty is stated plainly: it imposes that exposure-dose law
and lets the concentration profile follow it (the terminal half-life lengthens
with dose because the elimination rate constant is scaled by the same capacity
term) rather than integrating the Michaelis-Menten differential equation. That
is why the verifier grades the OBSERVABLE - the trapezoidal exposures actually
present in the shipped file, and the structures that survive a replicate-based
lack-of-fit test against them - and never the generator's own parameters.

All three fit an exposure table with a high R^2. They imply different doses,
and - because the study protocol names a maximum permitted dose - they imply
different GO/NO-GO verdicts. The naive competent pipeline (assume
proportionality, or fit a straight line and extrapolate) overshoots the dose
badly whenever a metabolic pathway is saturating inside the studied range, and
lands on the wrong side of the dose cap: it reports that the required exposure
is out of reach when in fact a much smaller dose delivers it.

What makes exactly one analysis defensible is a control that is PRESENT IN
EVERY CONDITION with the same filenames, the same columns, the same row count
and the same numeric precision; only its values differ. `mass_balance.csv`
reports the urinary recovery of parent drug and of the metabolite M1 over the
complete collection interval, so the amount metabolised is measured directly.
Under a capacity-limited pathway that amount approaches a ceiling and the
metabolised fraction falls with the SAME capacity constant that governs the
exposure curve, which is why the mechanistic model - not the empirical power
model - is the one licensed to extrapolate. Under first-order metabolism the
recovered amount is a constant fraction of the dose at every level, so
claiming saturation in C0 is a false alarm that the data refute.

The three conditions differ in what the data can support, not in how they look:

  C0  exposure is dose-proportional across the studied range; proportional
      extrapolation is adequate and asserting capacity limitation is wrong.
  H1  a pathway saturates INSIDE the studied range. The requested exposure sits
      just above the studied doses, where the mechanistic and empirical curves
      have already separated and only the mechanistic one still fits the data,
      so the answer is a much smaller dose than proportionality implies and the
      verdict on the dose cap inverts.
  F2  the studied range shows only mild super-proportionality and the requested
      exposure lies far beyond every measured dose. Two admissible kinetic
      structures reproduce every measured exposure to well within the observed
      between-subject scatter and then diverge above the top studied dose: they
      disagree about the required dose and about whether the dose cap suffices.
      Both parameter vectors are emitted as the impossibility witness, and the
      verifier re-derives them, so "not determinable" is a provable statement
      about the design rather than an opinion about data quality. The urinary
      control cannot rescue F2, and the record says why: M1 is formed before
      the parent reaches the circulation as well as after, so a complete
      collection measures total metabolic conversion and is blind to WHERE the
      capacity sits - it establishes that a pathway saturates without fixing
      the kinetic structure to extrapolate with.

The grading tolerances were set from measurement, not taste. Over seeds 11-16
on H1 the answer moves by at most 4% across every reasonable way of fitting the
mechanistic curve (log or raw residuals, per subject or per dose mean,
exposure-per-mg regression, quadratic with a free intercept), while proportional
scaling misses the dose by 177-301%, the power model by 21-27% and scaling off
the top level by 23-33%; the exposure at the dose cap moves by at most 10%
across those same fits and by 28-78% under the straight-line readings. The
tolerances sit in that gap, so a candidate is never marked wrong for a
defensible fitting choice and never right for a straight-line reading.

Verification recomputes the exposures themselves - trapezoidal AUC per subject
from the concentration-time file - rather than reading the generator's own
kinetic parameters, because a generator and a verifier that share one wrong
assumption agree perfectly and are still wrong. It then refits all three
structures with scipy, applies a replicate-based lack-of-fit test to decide
which structures the data admit, and declares the extrapolation determinable
only when every admitted structure agrees at the requested exposure. The
condition is therefore derived from the shipped numbers, not read off the key.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "n/a",
           "null", "no defensible value", "not identifiable", "unidentifiable"}

# id, indication, molecular weight (g/mol) used for the urinary molar balance
COMPOUNDS = [
    ("CRU-4401", "oncology, oral once daily", 412.5),
    ("CRU-4402", "antiviral, oral twice daily", 366.4),
    ("CRU-4403", "inflammation, oral once daily", 478.9),
    ("CRU-4404", "metabolic, oral once daily", 344.8),
    ("CRU-4405", "CNS, oral once daily", 391.2),
    ("CRU-4406", "haematology, oral once daily", 455.6),
]

# Realistic five-step escalation ladders; the top/bottom ratio is ~35x, which
# is what makes an empirical power model and a mechanistic saturable model
# separable inside the studied range when saturation is strong.
LADDERS = [
    [10, 25, 60, 150, 350],
    [15, 40, 100, 250, 600],
    [5, 15, 40, 100, 250],
    [20, 50, 120, 300, 700],
    [8, 20, 50, 125, 300],
    [12, 30, 75, 200, 500],
]

TIMES = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 24.0, 48.0)
N_SUBJECTS = 3
LLOQ = 0.1                # ng/mL; nothing emitted may round below the assay floor
LOF_ALPHA = 0.01          # a structure is admitted unless lack of fit is this significant
DOSE_TOL = 0.12           # grading tolerance on the recommended dose
EXPOSURE_TOL = 0.15       # grading tolerance on the exposure at the dose cap
# Determinability is tied to the SAME tolerances the answer is graded to, so
# the rule is exactly "an answer is reportable iff every structure the data
# admit agrees to the accuracy the answer is held to". A looser agreement band
# than the grading band would mark a candidate wrong for preferring one of two
# structures the verifier itself called interchangeable.


# --------------------------------------------------------------- observables

def _auc_pairs(conc_text: str) -> list[tuple[float, float]]:
    """(dose, AUC0-48) per subject, integrated from the concentration file.

    This is the observable the whole task turns on, so it is recomputed here
    from the shipped rows rather than taken from any summary column or from the
    generator's kinetic parameters.
    """
    profiles: dict[tuple[str, float], list[tuple[float, float]]] = {}
    for line in conc_text.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 4:
            continue
        try:
            dose = float(parts[1])
            time = float(parts[2])
            conc = float(parts[3])
        except ValueError:
            continue
        profiles.setdefault((parts[0], dose), []).append((time, conc))
    pairs = []
    for (_subject, dose), points in profiles.items():
        points.sort()
        auc = 0.0
        for (t0, c0), (t1, c1) in zip(points, points[1:]):
            auc += 0.5 * (c0 + c1) * (t1 - t0)
        pairs.append((dose, auc))
    return sorted(pairs)


def _metabolite_ceiling(mass_text: str) -> dict:
    """Direct measurement of metabolic capacity from the urinary molar balance.

    Reported for diagnosis and for the reference answer's justification; the
    numeric verdict does not depend on it, so a plausible-but-different
    reading of this file cannot flip a grade.
    """
    rows: dict[float, list[tuple[float, float]]] = {}
    for line in mass_text.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 5:
            continue
        try:
            rows.setdefault(float(parts[1]), []).append(
                (float(parts[2]), float(parts[4])))
        except ValueError:
            continue
    if not rows:
        return {}
    fractions = {}
    for dose in sorted(rows):
        molar = sum(d for d, _m in rows[dose]) / len(rows[dose])
        metabolite = sum(m for _d, m in rows[dose]) / len(rows[dose])
        fractions[dose] = metabolite / molar if molar else 0.0
    doses = sorted(fractions)
    low, high = fractions[doses[0]], fractions[doses[-1]]
    return {"metabolised_fraction_low_dose": round(low, 4),
            "metabolised_fraction_top_dose": round(high, 4),
            "fraction_ratio": round(high / low, 4) if low else 0.0}


# ------------------------------------------------------------------- fitting
#
# Every fit is done on log exposure. Exposure spans ~150x across the ladder and
# the scatter is multiplicative, so unweighted least squares on the raw scale
# would be decided almost entirely by the top dose group and the lack-of-fit
# test would be meaningless.

def _fit_proportional(doses, aucs):
    """AUC = k*D. One parameter, and the log-scale estimate of k is the
    geometric mean of the observed exposure per mg. Returned as a 1-tuple so
    every structure carries the same shaped parameter vector."""
    import numpy as np
    k = np.exp(np.mean(np.log(np.asarray(aucs)) - np.log(np.asarray(doses))))
    return (float(k),)


def _fit_power(doses, aucs):
    from scipy import stats
    import numpy as np
    fit = stats.linregress(np.log(np.asarray(doses)), np.log(np.asarray(aucs)))
    return float(math.exp(fit.intercept)), float(fit.slope)


def _fit_saturable(doses, aucs):
    """AUC = a*D + b*D^2, the closed form for a Michaelis-Menten elimination
    pathway. Fitted in log parameters so positivity holds without bounds."""
    import numpy as np
    from scipy.optimize import least_squares

    d = np.asarray(doses, dtype=float)
    a_obs = np.asarray(aucs, dtype=float)
    y = np.log(a_obs)
    slope, intercept = np.polyfit(d, a_obs / d, 1)
    a0 = max(float(intercept), float(a_obs.min() / d.max()) * 1e-3)
    b0 = max(float(slope), a0 / (1e4 * float(d.max())))

    def residual(theta):
        a, b = np.exp(theta)
        return np.log(a * d + b * d * d) - y

    solution = least_squares(residual, np.log([a0, b0]), xtol=1e-12, ftol=1e-12)
    a, b = (float(v) for v in np.exp(solution.x))
    return a, b


def _predict(structure, theta, dose):
    if structure == "proportional":
        return theta[0] * dose
    if structure == "power":
        return theta[0] * dose ** theta[1]
    return theta[0] * dose + theta[1] * dose * dose


def _solve(structure, theta, target):
    """Dose delivering `target` exposure under a structure."""
    if structure == "proportional":
        return target / theta[0]
    if structure == "power":
        return (target / theta[0]) ** (1.0 / theta[1])
    a, b = theta
    return (-a + math.sqrt(a * a + 4.0 * b * target)) / (2.0 * b)


def _lack_of_fit(doses, aucs, structure, theta, n_params):
    """Replicate-based lack-of-fit F test on log exposure.

    Pure error comes from the within-dose scatter, so the test asks whether a
    structure's systematic departure from the dose means is larger than the
    between-subject variability actually observed - not whether R^2 is high.
    """
    import numpy as np
    from scipy import stats

    d = np.asarray(doses, dtype=float)
    y = np.log(np.asarray(aucs, dtype=float))
    levels = sorted(set(d.tolist()))
    ss_pure = 0.0
    for level in levels:
        block = y[d == level]
        ss_pure += float(((block - block.mean()) ** 2).sum())
    df_pure = len(y) - len(levels)
    predicted = np.array([_predict(structure, theta, float(x)) for x in d])
    ss_res = float(((y - np.log(predicted)) ** 2).sum())
    ss_lof = max(ss_res - ss_pure, 0.0)
    df_lof = len(levels) - n_params
    if df_lof <= 0 or df_pure <= 0 or ss_pure <= 0:
        return {"f": 0.0, "p": 1.0, "ss_res": ss_res}
    f_stat = (ss_lof / df_lof) / (ss_pure / df_pure)
    return {"f": float(f_stat), "p": float(stats.f.sf(f_stat, df_lof, df_pure)),
            "ss_res": ss_res}


def analyse(pairs, target_auc: float, max_dose: float) -> dict:
    """The whole scientific decision, from the exposures alone.

    Model selection is parsimony first: if dose proportionality survives the
    lack-of-fit test there is no unexplained curvature and the extrapolation is
    proportional. Otherwise every curved structure the data admit is carried
    forward, and the requested exposure is only reportable if they agree there
    - which is precisely the question of whether the requested exposure lies
    inside the range these data support.
    """
    doses = [d for d, _a in pairs]
    aucs = [a for _d, a in pairs]

    theta_l = _fit_proportional(doses, aucs)
    theta_p = _fit_saturable(doses, aucs)
    theta_w = _fit_power(doses, aucs)
    lof_l = _lack_of_fit(doses, aucs, "proportional", theta_l, 1)
    lof_p = _lack_of_fit(doses, aucs, "saturable", theta_p, 2)
    lof_w = _lack_of_fit(doses, aucs, "power", theta_w, 2)

    out = {
        "top_dose": max(doses),
        "top_exposure": max(aucs),
        "theta_proportional": [round(v, 6) for v in theta_l],
        "theta_saturable": [round(v, 8) for v in theta_p],
        "theta_power": [round(v, 6) for v in theta_w],
        "lof_proportional": round(lof_l["f"], 2),
        "lof_saturable": round(lof_p["f"], 2),
        "lof_power": round(lof_w["f"], 2),
        "p_proportional": round(lof_l["p"], 5),
        "p_saturable": round(lof_p["p"], 5),
        "p_power": round(lof_w["p"], 5),
        "dose_if_proportional": round(_solve("proportional", theta_l, target_auc), 2),
        "dose_if_saturable": round(_solve("saturable", theta_p, target_auc), 2),
        "dose_if_power": round(_solve("power", theta_w, target_auc), 2),
    }

    if lof_l["p"] >= LOF_ALPHA:
        out.update({"capacity_limited": False, "structure": "proportional",
                    "admitted": ["proportional"], "determinable": True,
                    "dose_mg": _solve("proportional", theta_l, target_auc),
                    "exposure_at_max_dose": _predict("proportional", theta_l, max_dose)})
    else:
        admitted = []
        if lof_p["p"] >= LOF_ALPHA:
            admitted.append(("saturable", theta_p))
        if lof_w["p"] >= LOF_ALPHA:
            admitted.append(("power", theta_w))
        out["capacity_limited"] = True
        out["admitted"] = [name for name, _t in admitted]
        if not admitted:
            out.update({"structure": None, "determinable": False,
                        "dose_mg": None, "exposure_at_max_dose": None})
        else:
            solved = [_solve(name, theta, target_auc) for name, theta in admitted]
            capped = [_predict(name, theta, max_dose) for name, theta in admitted]
            spread_dose = max(solved) / min(solved)
            spread_cap = max(capped) / min(capped)
            verdicts = {value <= max_dose for value in solved}
            agree = (spread_dose - 1.0 <= DOSE_TOL
                     and spread_cap - 1.0 <= EXPOSURE_TOL
                     and len(verdicts) == 1)
            out["dose_spread"] = round(spread_dose, 4)
            out["exposure_spread_at_max_dose"] = round(spread_cap, 4)
            out["verdicts_agree"] = len(verdicts) == 1
            preferred = next((t for n, t in admitted if n == "saturable"), admitted[0][1])
            preferred_name = "saturable" if any(
                n == "saturable" for n, _t in admitted) else admitted[0][0]
            out.update({
                "structure": preferred_name if agree else None,
                "determinable": agree,
                "dose_mg": _solve(preferred_name, preferred, target_auc) if agree else None,
                "exposure_at_max_dose":
                    _predict(preferred_name, preferred, max_dose) if agree else None,
            })

    if out["determinable"]:
        out["target_reachable"] = bool(out["dose_mg"] <= max_dose)
    else:
        out["target_reachable"] = None
    return out


# ----------------------------------------------------------------- generation

def _profile(times, ka: float, ke: float) -> list[float]:
    return [math.exp(-ke * t) - math.exp(-ka * t) for t in times]


def _trapz(times, values) -> float:
    return sum(0.5 * (values[i] + values[i + 1]) * (times[i + 1] - times[i])
               for i in range(len(times) - 1))


def _terminal_half_life(times, values) -> float:
    """Log-linear regression through the last three points, the way a PK
    report derives it - so the column agrees with the profile it came from."""
    tail = [(t, v) for t, v in zip(times, values) if v > 0][-3:]
    if len(tail) < 2:
        return 0.0
    n = len(tail)
    mean_t = sum(t for t, _v in tail) / n
    mean_y = sum(math.log(v) for _t, v in tail) / n
    num = sum((t - mean_t) * (math.log(v) - mean_y) for t, v in tail)
    den = sum((t - mean_t) ** 2 for t, _v in tail)
    slope = num / den if den else -0.1
    return math.log(2.0) / max(-slope, 1e-6)


def _nice_dose(low: float, high: float) -> float | None:
    """A round permitted-dose value strictly inside (low, high)."""
    if high <= low:
        return None
    middle = math.sqrt(low * high)
    for step in (250.0, 100.0, 50.0, 25.0, 10.0, 5.0):
        candidates = [step * n for n in range(1, 4001)
                      if low < step * n < high]
        if candidates:
            return min(candidates, key=lambda v: abs(v - middle))
    return None


def _emit(rng, compound, mw, doses, exposure_at, ka, ke_at, met_fraction_at):
    """Write the three data files and return them with the recomputed AUCs."""
    conc_rows = ["subject_id,dose_mg,time_h,conc_ng_per_mL"]
    summary_rows = ["subject_id,dose_mg,cmax_ng_per_mL,tmax_h,"
                    "auc_0_48_h_ng_per_mL,t_half_h"]
    mass_rows = ["subject_id,dose_mg,dose_umol,parent_umol,m1_umol"]
    pairs: list[tuple[float, float]] = []

    for level, dose in enumerate(doses):
        shape = _profile(TIMES, ka, ke_at(dose))
        scale = exposure_at(dose) / _trapz(TIMES, shape)
        for replicate in range(N_SUBJECTS):
            subject = f"S{level + 1}{'ABC'[replicate]}"
            between = math.exp(rng.gauss(0.0, 0.075))
            values = []
            for index, base in enumerate(shape):
                assay = math.exp(rng.gauss(0.0, 0.03)) if index else 1.0
                values.append(round(scale * base * between * assay, 1))
            for time, value in zip(TIMES, values):
                conc_rows.append(f"{subject},{dose:g},{time:g},"
                                 f"{format(value, '.1f')}")
            auc = _trapz(TIMES, values)
            peak = max(values)
            tmax = TIMES[values.index(peak)]
            pairs.append((float(dose), auc))
            summary_rows.append(
                f"{subject},{dose:g},{format(peak, '.1f')},{format(tmax, '.1f')},"
                f"{format(auc, '.1f')},"
                f"{format(_terminal_half_life(TIMES, values), '.2f')}")

            molar = dose * 1000.0 / mw
            metabolite = molar * met_fraction_at(dose) * math.exp(rng.gauss(0, 0.05))
            recovered = molar * 0.945 * math.exp(rng.gauss(0, 0.02))
            parent = max(recovered - metabolite, molar * 0.02)
            mass_rows.append(
                f"{subject},{dose:g},{format(molar, '.2f')},"
                f"{format(parent, '.2f')},{format(metabolite, '.2f')}")

    files = {
        "plasma_conc.csv": "\n".join(conc_rows) + "\n",
        "pk_summary.csv": "\n".join(summary_rows) + "\n",
        "mass_balance.csv": "\n".join(mass_rows) + "\n",
    }
    emitted = [float(row.split(",")[3]) for row in conc_rows[1:]]
    return files, sorted(pairs), min(v for v in emitted if v > 0), max(emitted)


def _round_sig(value: float, digits: int = 3) -> float:
    if value <= 0:
        return value
    exponent = math.floor(math.log10(value))
    factor = 10 ** (digits - 1 - exponent)
    return round(value * factor) / factor


def build(seed: int, condition: str) -> Episode:
    compound, indication, mw = COMPOUNDS[seed % len(COMPOUNDS)]
    doses = LADDERS[(seed + 2) % len(LADDERS)]
    top = float(doses[-1])

    attempt = 0
    while True:
        attempt += 1
        if attempt > 240:
            raise RuntimeError(f"dose-extrapolation: no admissible instance for "
                               f"seed {seed} condition {condition}")
        rng = random.Random(880_000 + 991 * seed + 37 * attempt
                            + {"C0": 0, "H1": 1, "F2": 2}[condition])

        ka = rng.uniform(0.9, 1.6)
        ke0 = math.log(2.0) / rng.uniform(6.0, 9.0)
        met_low = rng.uniform(0.58, 0.72)
        # Exposure scale, fixed by asking what the last sample of the lowest
        # dose level reads: that keeps every emitted concentration above the
        # assay floor without truncating the profile, and the draw is made the
        # same way in every condition so the magnitudes overlap and the
        # condition cannot be read off the size of the numbers.
        tail = rng.uniform(0.5, 1.6)
        low_scale = tail / math.exp(-ke0 * TIMES[-1])
        unit = low_scale * _trapz(TIMES, _profile(TIMES, ka, ke0)) / doses[0]

        if condition == "C0":
            capacity = None                        # first-order throughout
        elif condition == "H1":
            capacity = top / rng.uniform(2.6, 6.0)  # saturating inside the range
        else:
            capacity = top / rng.uniform(0.30, 1.00)  # only mildly super-proportional

        def boost(dose, capacity=capacity):
            return 1.0 if capacity is None else 1.0 + dose / capacity

        files, pairs, lowest, highest = _emit(
            rng, compound, mw, doses, ka=ka,
            exposure_at=lambda d: unit * d * boost(d),
            ke_at=lambda d: ke0 / boost(d),
            met_fraction_at=lambda d: met_low / boost(d))
        if lowest < 2 * LLOQ or highest > 25000.0:
            continue

        fitted = analyse(pairs, target_auc=1.0, max_dose=top)
        # The requested exposure, expressed as a multiple of the top studied
        # dose, then converted to an exposure through the FITTED curve so the
        # verifier's refit lands on the same dose.
        if condition == "C0":
            wanted_dose = top * rng.uniform(1.4, 2.3)
            structure, theta = "proportional", tuple(fitted["theta_proportional"])
        elif condition == "H1":
            wanted_dose = top * rng.uniform(1.25, 1.5)
            structure, theta = "saturable", tuple(fitted["theta_saturable"])
        else:
            wanted_dose = top * rng.uniform(2.0, 2.8)
            structure, theta = "saturable", tuple(fitted["theta_saturable"])
        target = _round_sig(_predict(structure, theta, wanted_dose), 3)

        # The dose cap is a fact about the toxicology cover, so it has to be a
        # round number and at least the top dose already given.
        probe = analyse(pairs, target_auc=target, max_dose=top)
        dose_sat = probe["dose_if_saturable"]
        dose_prop = probe["dose_if_proportional"]
        dose_pow = probe["dose_if_power"]
        if condition == "C0":
            reachable = rng.random() < 0.5
            cap = (_nice_dose(dose_prop * 1.15, dose_prop * 2.2) if reachable
                   else _nice_dose(max(top, dose_prop * 0.45), dose_prop / 1.15))
        elif condition == "H1":
            cap = _nice_dose(dose_sat * 1.12, min(dose_prop, dose_pow) / 1.05)
        else:
            cap = _nice_dose(dose_sat * 1.10, dose_pow / 1.10)
        if cap is None or cap < top:
            continue

        result = analyse(pairs, target_auc=target, max_dose=cap)

        # Acceptance: the instance must be the condition it claims to be, as
        # judged by the same recomputation the verifier will run.
        if condition == "C0":
            ok = (result["capacity_limited"] is False
                  and result["determinable"]
                  and result["p_proportional"] >= 0.05
                  and abs(result["dose_mg"] / cap - 1.0) > 0.12)
        elif condition == "H1":
            # Scaling the dose off the exposure per mg seen at the TOP level -
            # the most defensible of the straight-line readings, since it uses
            # the level nearest the answer - must also miss.
            a_hat, b_hat = result["theta_saturable"]
            dose_from_top = target / (a_hat + b_hat * top)
            ok = (result["capacity_limited"] is True
                  and result["determinable"]
                  and result["structure"] == "saturable"
                  and result["p_proportional"] < 1e-4
                  and result["p_power"] < 0.002
                  and result["p_saturable"] >= 0.05
                  # every route a straight-line reading takes must miss the
                  # dose by more than the grading tolerance AND land on the
                  # wrong side of the cap
                  and dose_prop / result["dose_mg"] - 1.0 > 0.30
                  and dose_pow / result["dose_mg"] - 1.0 > 0.20
                  and dose_from_top / result["dose_mg"] - 1.0 > 0.18
                  and dose_prop > cap and dose_pow > cap
                  and result["dose_mg"] < cap / 1.10
                  and result["target_reachable"] is True)
        else:
            spread_cap = (_predict("power", tuple(result["theta_power"]), cap)
                          / _predict("saturable", tuple(result["theta_saturable"]), cap))
            ok = (result["capacity_limited"] is True
                  and result["determinable"] is False
                  and result["p_proportional"] < LOF_ALPHA
                  and result["p_saturable"] >= 0.05
                  and result["p_power"] >= 0.05
                  and dose_pow / dose_sat - 1.0 > 0.25
                  and max(spread_cap, 1.0 / spread_cap) > 1.35
                  and dose_sat < cap < dose_pow)
        if not ok:
            continue

        witness = None
        if condition == "F2":
            import numpy as np
            theta_p = tuple(result["theta_saturable"])
            theta_w = tuple(result["theta_power"])
            levels: dict[float, list[float]] = {}
            for dose, auc in pairs:
                levels.setdefault(dose, []).append(auc)
            # Observational equivalence is already established by the two
            # lack-of-fit tests above, which is the rigorous form of the claim.
            # This bounds the same thing directly, so the witness can be read
            # without rerunning the tests: the two curves agree inside the
            # studied doses to within a tenth, and the accepted instance has
            # them disagreeing by a third or more above them.
            deviation = max(
                abs(_predict("saturable", theta_p, dose)
                    / _predict("power", theta_w, dose) - 1.0)
                for dose in levels)
            scatter = float(np.mean([np.std(np.log(v), ddof=1)
                                     for v in levels.values()]))
            if deviation > 0.10:
                continue
            witness = {
                "theta_capacity_limited": {"a_h_ng_per_mL_per_mg": theta_p[0],
                                           "b_h_ng_per_mL_per_mg2": theta_p[1]},
                "theta_power_model": {"c": theta_w[0], "g": theta_w[1]},
                "max_relative_disagreement_inside_studied_doses": round(deviation, 5),
                "observed_log_scatter": round(scatter, 5),
                "dose_under_capacity_limited_mg": round(dose_sat, 1),
                "dose_under_power_model_mg": round(dose_pow, 1),
                "exposure_at_cap_capacity_limited":
                    round(_predict("saturable", theta_p, cap), 1),
                "exposure_at_cap_power_model":
                    round(_predict("power", theta_w, cap), 1),
            }
        break

    protocol = "\n".join([
        f"# Clinical pharmacology record  {compound}",
        f"Programme: {indication}.",
        f"Molecular weight {mw:g} g/mol.",
        "",
        "Study: single ascending dose, healthy volunteers, oral solution.",
        f"Dose levels (mg): {', '.join(str(d) for d in doses)}.",
        f"{N_SUBJECTS} subjects per level, one dose per subject.",
        "Plasma sampling at 0, 0.5, 1, 2, 4, 8, 12, 24 and 48 h "
        "(plasma_conc.csv).",
        "Subject summaries in pk_summary.csv. Exposure throughout this "
        "programme means the area under the plasma concentration-time curve "
        "from 0 to 48 h by the linear trapezoidal rule over the sampled "
        "points, in h*ng/mL.",
        "Urine was collected quantitatively over the whole 0-48 h interval; "
        "recovery of unchanged drug and of the metabolite M1 is in "
        "mass_balance.csv in micromoles. Recovery of the administered dose in "
        "these two forms is complete within assay error at every level, and "
        "M1 is formed from the parent before it reaches the systemic "
        "circulation as well as after.",
        "Bioanalytical assay validated from 0.1 to 25000 ng/mL.",
        "",
        f"Exposure required for the programme: {target:g} h*ng/mL.",
        f"Highest dose permitted by the toxicology cover: {cap:g} mg.",
        "",
        "The lead compound of this chemical series showed exposure increasing "
        "in proportion to dose across its whole studied range.",
    ]) + "\n"

    brief = (
        f"{compound} has completed the single ascending dose study recorded in "
        "clinical_record.md. The plasma concentrations, the subject summaries "
        "and the urinary recovery data are attached.\n\n"
        "The programme needs the dose that delivers the exposure named in the "
        "record. Report that dose, and report the exposure the highest "
        "permitted dose would deliver.\n\n"
        "Submit these fields:\n"
        "- dose_mg: the dose in mg that delivers the required exposure, as a "
        "number, or the string cannot_determine if no defensible value follows "
        "from these data\n"
        "- exposure_at_max_dose: the 0-48 h exposure in h*ng/mL expected at the "
        "highest permitted dose, as a number, or the string cannot_determine\n"
        "- exposure_basis: what governs the relationship between dose and "
        "exposure for this compound over the range that matters here, in your "
        "own words\n"
        "- target_reachable: YES if the required exposure can be delivered "
        "within the highest permitted dose, NO if it cannot, or the string "
        "cannot_determine\n"
        "and conf_<field> in [0,1] for each.")

    files["clinical_record.md"] = protocol
    key = {
        "condition": condition,
        "compound": compound,
        "doses_mg": doses,
        "target_auc": target,
        "max_dose_mg": cap,
        "capacity_limited": condition != "C0",
        "determinable": condition != "F2",
        "witness": witness,
        "intended_dose_mg": None if condition == "F2" else round(result["dose_mg"], 2),
        "intended_reachable": result["target_reachable"],
        "naive_dose_if_proportional_mg": round(dose_prop, 2),
        "naive_dose_if_power_mg": round(dose_pow, 2),
    }
    # 26 calls: reading three files, integrating the profiles, fitting and
    # comparing several structures, and checking the urinary balance against
    # the exposure curve cannot be done in one linear pass, and a first attempt
    # that assumes proportionality has to be discovered and revised.
    return Episode("dose-extrapolation", seed, condition, brief, files, key,
                   budget=26,
                   checkpoints=["exposure_basis", "dose", "cap_exposure",
                                "decision"])


# --------------------------------------------------------------- verification

def _normalise(text) -> str:
    """Lower-case, hyphen- and underscore-insensitive, single-spaced.

    Every phrase list below is written in space form and matched against this,
    so "dose-proportional", "dose proportional" and "dose_proportional" are one
    phrase. Without it a scoring rule silently depends on a candidate's
    hyphenation.
    """
    flat = str(text or "").lower().replace("-", " ").replace("_", " ")
    return " ".join(flat.split())


# Phrases that mention a reading only to rule it out. Plain substring removal
# on purpose: a regex for exactly this failed silently in situ on the chain
# track while passing in isolation, and a scoring rule that cannot be checked
# by eye is a liability.
NEGATED = (
    "not dose proportional", "not proportional", "no longer proportional",
    "no longer dose proportional", "not linear", "not a linear",
    "no longer linear", "not first order", "not constant clearance",
    "rather than proportional", "instead of proportional",
    "rather than linear", "instead of linear", "not simply proportional",
    "not strictly proportional", "deviates from proportional",
    "departs from proportional", "departure from proportional",
    "deviation from proportional", "not saturable", "not saturated",
    "no saturation", "not saturating", "not capacity limited",
    "no capacity limit", "not nonlinear", "not non linear",
    "rather than saturable", "instead of saturable",
    "no evidence of saturation", "no evidence for saturation",
    "without saturation", "no sign of saturation",
)

SATURATION_WORDS = (
    "saturab", "saturat", "capacity limit", "capacity of the", "michaelis",
    "menten", "nonlinear", "non linear", "supraproportional",
    "supra proportional", "super proportional", "superproportional",
    "non proportional", "nonproportional", "disproportional",
    "greater than proportional", "more than proportional",
    "greater than dose proportional", "more than dose proportional",
    "faster than proportional", "steeper than proportional",
    "supralinear", "supra linear", "superlinear", "super linear",
    "faster than linear", "more than linear", "greater than linear",
    "steeper than linear", "disproportionate", "clearance decreases",
    "decreasing clearance", "falling clearance", "clearance falls",
    "reduced clearance at", "zero order", "concentration dependent clearance",
    "dose dependent clearance",
)

PROPORTIONAL_WORDS = (
    "dose proportional", "proportional to dose", "proportionality",
    "proportional", "linear", "first order", "constant clearance",
    "clearance is constant", "dose independent clearance",
    # A negated saturation claim ("no evidence of saturation, exposure per mg
    # is flat") asserts proportionality without using the word, and the
    # negation strip removes the only phrase it did use.
    "independent of dose", "dose independent", "per mg is flat",
    "per mg was flat", "per mg is constant", "per mg was constant",
    "per mg is unchanged", "per mg does not change", "per mg did not change",
    "does not change with dose", "did not change with dose",
    "no change with dose", "unchanged with dose", "unchanged across the dose",
    "constant across the dose", "same across the dose", "same at all dose",
)

# A refusal has to be about the extrapolation (first group) and has to say
# what about the extrapolation is unsettled (second group). A bare "cannot be
# determined" is silence with a label on it and fails.
IDENTIFIABILITY_WORDS = (
    "identifiab", "not identified", "under determined", "underdetermined",
    "cannot be determined", "cannot determine", "not determinable",
    "beyond the", "outside the", "above the highest", "above the top",
    "above every", "higher than any", "extrapolat", "no unique", "not unique",
    "equally well", "both fit", "indistinguishable", "cannot distinguish",
    "cannot be distinguished", "two models", "either model", "competing",
    "diverge", "disagree", "unsupported", "not supported by", "no measured",
    "not constrained", "does not constrain", "do not constrain",
)

UNSETTLED_WORDS = (
    "model", "curve", "shape", "structure", "mechanism", "kinetic",
    "relationship", "diverge", "disagree", "equally well", "both fit",
    "indistinguishable", "power", "saturab", "saturat", "capacity",
    "second order", "quadratic", "form of", "functional", "extrapolat",
)


def _strip_negated(text: str) -> str:
    lowered = _normalise(text)
    for phrase in NEGATED:
        lowered = lowered.replace(phrase, " ")
    return lowered


def _reads_saturation(text: str) -> bool:
    return any(word in text for word in SATURATION_WORDS)


def _reads_proportional(text: str) -> bool:
    """True only if proportionality is asserted rather than mentioned.

    Every saturation phrase is removed first, because "non linear" contains
    "linear" and "greater than proportional" contains "proportional": without
    this a correct answer matches both sides and scores as a hedge.
    """
    residue = text
    for word in SATURATION_WORDS:
        residue = residue.replace(word, " ")
    return any(word in residue for word in PROPORTIONAL_WORDS)


ABSTAIN_PHRASES = ("cannot be determined", "cannot be established",
                   "cannot determine", "can not be determined",
                   "not determinable", "not determined by these",
                   "no defensible", "not identifiable", "unidentifiable",
                   "indeterminate", "insufficient to determine",
                   "cannot be quoted", "cannot be recommended")


def _abstains(value) -> bool:
    """A stated refusal, never silence: an absent or empty field is not one."""
    text = _normalise(value)
    if not text:
        return False
    return (text in ABSTAIN or text.replace(" ", "_") in ABSTAIN
            or any(phrase in text for phrase in ABSTAIN_PHRASES))


def _verdict_word(text: str):
    """Parse the go/no-go word. Returns True, False, None for an abstention, or
    the string 'unparsed'. Abstention phrasings are tested first, because an
    answer opening with "cannot be determined" reads as a refusal of the
    target under a plain no/not prefix rule."""
    stripped = text.strip().strip('".').lower()
    if not stripped:
        return "unparsed"
    if _abstains(stripped):
        return None
    if stripped.startswith(("yes", "true", "achievable", "reachable",
                            "attainable")):
        return True
    if stripped.startswith(("no", "false", "not ", "unreach", "unachiev",
                            "unattain", "cannot", "can not")):
        return False
    return "unparsed"


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip().replace(",", "")
    for suffix in ("mg", "h*ng/ml", "h.ng/ml", "ng/ml", "h*ng/mL"):
        if text.lower().endswith(suffix):
            text = text[: -len(suffix)].strip()
    try:
        return float(text)
    except ValueError:
        return None


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    order = ["exposure_basis", "dose", "cap_exposure", "decision"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, order[0])

    def field(name: str):
        """Case- and separator-insensitive lookup on BOTH sides: comparing a
        lowercased key against a mixed-case target silently matched nothing
        once, and every numeric answer then read as absent."""
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # Recompute the exposures from the shipped concentration rows, then re-derive
    # which structures the data admit. The canonical bytes are the episode's, so
    # a candidate that rewrites a workspace file cannot move the truth.
    pairs = _auc_pairs(episode.files["plasma_conc.csv"])
    result = analyse(pairs, key["target_auc"], key["max_dose_mg"])
    balance = _metabolite_ceiling(episode.files["mass_balance.csv"])
    detail["recomputed"] = {k: result[k] for k in (
        "capacity_limited", "determinable", "structure", "admitted",
        "p_proportional", "p_saturable", "p_power", "dose_if_proportional",
        "dose_if_saturable", "dose_if_power", "top_dose", "top_exposure")}
    detail["urinary_balance"] = balance
    detail["expected_from_key"] = {"capacity_limited": key["capacity_limited"],
                                   "determinable": key["determinable"]}
    detail["target_auc"] = key["target_auc"]
    detail["max_dose_mg"] = key["max_dose_mg"]

    basis_text = str(field("exposure_basis") or "")
    stated = _strip_negated(basis_text)
    says_saturation = _reads_saturation(stated)
    says_proportional = _reads_proportional(stated)
    detail["stated_basis"] = stated[:220]
    detail["read_as"] = {"saturation": says_saturation,
                         "proportional": says_proportional}

    given_dose = field("dose_mg")
    given_cap = field("exposure_at_max_dose")
    given_reach = str(field("target_reachable") or "")
    reach = _verdict_word(given_reach)
    dose_abstains = _abstains(given_dose)
    cap_abstains = _abstains(given_cap)

    if not result["determinable"]:
        # The only defensible outcome is a refusal that is ABOUT the
        # extrapolation, and silence is not a refusal: an absent field fails.
        reason = (basis_text + " " + str(submitted.get("reasoning", "") or "")
                  + " " + str(field("notes") or "")).lower()
        names_reason = any(word in reason for word in IDENTIFIABILITY_WORDS)
        names_unsettled = any(word in reason for word in UNSETTLED_WORDS)
        checks["exposure_basis"] = (names_reason and names_unsettled
                                    and not says_proportional
                                    and bool(basis_text.strip()))
        detail["refusal_reads"] = {"limit": names_reason,
                                   "what_is_unsettled": names_unsettled}
        checks["dose"] = dose_abstains
        checks["cap_exposure"] = cap_abstains
        checks["decision"] = reach is None
        detail["expected"] = ("refusal: two admissible kinetic structures fit "
                              "the studied doses and disagree above them")
        detail["witness"] = key["witness"]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    if result["capacity_limited"]:
        checks["exposure_basis"] = says_saturation and not says_proportional
    else:
        checks["exposure_basis"] = says_proportional and not says_saturation

    expected_dose = result["dose_mg"]
    expected_cap = result["exposure_at_max_dose"]
    value = _number(given_dose)
    checks["dose"] = (value is not None and value > 0
                      and abs(value / expected_dose - 1.0) <= DOSE_TOL)
    capped = _number(given_cap)
    checks["cap_exposure"] = (capped is not None and capped > 0
                              and abs(capped / expected_cap - 1.0) <= EXPOSURE_TOL)
    checks["decision"] = reach is result["target_reachable"]
    detail.update({"expected_dose_mg": round(expected_dose, 2),
                   "given_dose_mg": value,
                   "expected_exposure_at_max_dose": round(expected_cap, 1),
                   "given_exposure_at_max_dose": capped,
                   "expected_target_reachable":
                       "YES" if result["target_reachable"] else "NO",
                   "given_target_reachable": given_reach[:40]})
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


def reference_submission(episode: Episode) -> dict:
    """The submission a competent clinical pharmacologist would make.

    Derived by integrating the shipped profiles and refitting - the same route a
    candidate must take - so B8 proves the task is solvable from the workspace
    rather than from the key.
    """
    key = episode.key
    pairs = _auc_pairs(episode.files["plasma_conc.csv"])
    result = analyse(pairs, key["target_auc"], key["max_dose_mg"])
    balance = _metabolite_ceiling(episode.files["mass_balance.csv"])

    if not result["determinable"]:
        return {
            "dose_mg": "cannot_determine",
            "exposure_at_max_dose": "cannot_determine",
            "target_reachable": "cannot_determine",
            "exposure_basis": (
                "exposure rises more than proportionally with dose across the "
                f"studied levels up to {result['top_dose']:g} mg, but the "
                "requested exposure lies well above every measured exposure. "
                "A capacity-limited elimination curve and an empirical power "
                "curve both reproduce the measured exposures to within the "
                "between-subject scatter and then diverge above the top "
                f"studied dose: they require {result['dose_if_saturable']:g} mg "
                f"and {result['dose_if_power']:g} mg respectively and they "
                "disagree about whether the permitted dose suffices, so no "
                "unique dose is identifiable from these data and the "
                "extrapolation is not supported."),
            "conf_dose_mg": 0.9, "conf_exposure_at_max_dose": 0.9,
            "conf_target_reachable": 0.9, "conf_exposure_basis": 0.9,
        }

    if result["capacity_limited"]:
        basis = (
            "elimination is capacity-limited over the studied range: exposure "
            "rises with the square of dose as well as with dose, the terminal "
            "half-life lengthens at the higher levels, and the urinary "
            "recovery of M1 approaches a ceiling so the metabolised fraction "
            f"falls from {balance.get('metabolised_fraction_low_dose')} at the "
            f"lowest level to {balance.get('metabolised_fraction_top_dose')} at "
            "the top level, which fixes the same capacity constant that the "
            "exposure curve implies. Scaling the dose in proportion to the "
            "required exposure therefore overshoots.")
    else:
        basis = (
            "exposure is dose-proportional over the studied range: exposure per "
            "mg is flat across the levels within the between-subject scatter, "
            "the terminal half-life does not change with dose, and the urinary "
            "recovery of M1 stays at a constant fraction of the dose "
            f"({balance.get('metabolised_fraction_low_dose')} at the lowest "
            f"level, {balance.get('metabolised_fraction_top_dose')} at the top), "
            "so clearance is dose-independent and proportional scaling holds "
            "over the requested range.")
    return {
        "dose_mg": round(result["dose_mg"], 1),
        "exposure_at_max_dose": round(result["exposure_at_max_dose"], 1),
        "target_reachable": "YES" if result["target_reachable"] else "NO",
        "exposure_basis": basis,
        "conf_dose_mg": 0.8, "conf_exposure_at_max_dose": 0.8,
        "conf_target_reachable": 0.85, "conf_exposure_basis": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
