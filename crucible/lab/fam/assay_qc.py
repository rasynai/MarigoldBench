"""Family: plate QC and dose-response readout.

A 10-point dose-response plate is the most common quantitative artifact in
early discovery, and the literature is explicit about where it goes wrong. The
defect that matters is never a traceback: Coscientist's failures were all
*successful* tool calls whose science was wrong, and the failure class it
names first is a units/concentration slip that leaves the file schema-valid and
the fit beautiful. BixBench's measured agent failures are the same shape -
unhandled data-quality issues and skipped assumption checks.

So the plate here is generated from a known curve and shipped with two
independent records of the same experiment: the concentration column of the
readout (what the plate map was templated with) and the liquid-handler log
(what was actually dispensed). In C0 they agree. In H1 the *signals are
byte-identical* and only the handler log differs, so the same raw data has a
different correct IC50 - the answer moves, silently, and only for a candidate
that reconciles the two records. In F2 the compound's inflection sits above the
top tested concentration, the series never crosses the half-maximal point, and
no IC50 is recoverable from this plate at all.

Verification refits the curve with scipy from the shipped CSV, re-derives the
concentration series by parsing the handler log, and recomputes the QC
exclusions and the observed inhibition depth. Nothing the candidate reports is
taken as evidence for itself.
"""
from __future__ import annotations

import math
import random
import re
from pathlib import Path

from ..families import Episode, Verdict

# ---------------------------------------------------------------------------
# generation

COMPOUNDS = [
    ("CRU-1041", "KDM5A demethylase", "fluorescence intensity 485/528 nm"),
    ("CRU-2276", "PIM1 kinase", "ADP-Glo luminescence"),
    ("CRU-3390", "HDAC6 deacetylase", "fluorescence intensity 360/460 nm"),
    ("CRU-4118", "SHP2 phosphatase", "DiFMUP fluorescence 358/455 nm"),
    ("CRU-5502", "BRD4 BD1 bromodomain", "TR-FRET ratio 665/615"),
    ("CRU-6734", "MTH1 hydrolase", "fluorescence intensity 485/528 nm"),
    ("CRU-7845", "USP7 protease", "Ub-rhodamine fluorescence 485/535 nm"),
]

ROWS = "ABCD"                 # four replicate rows; E-H unused this run
N_DOSES = 10                  # columns 2..11
ABSTAIN = {"cannot_determine", "cannot determine", "cannot-determine",
           "not_determined", "not determined", "not determinable",
           "indeterminate", "undetermined", "nd", "n/a", "na", "none", "null"}

# Recomputed QC rule. A read of zero sits below the plate's own background
# floor, and a read far above the vehicle control is optical junk; both are
# physically impossible measurements rather than unusual ones.
DEAD_FRACTION_OF_FLOOR = 0.25
SPIKE_MULTIPLE_OF_TOP = 1.6
# Below this depth the series never reaches its own half-maximal point, so an
# IC50 would be an extrapolation rather than a measurement.
DETERMINABLE_MIN_INHIBITION = 50.0
# A reported IC50 counts as the same answer inside this factor. It is set wide
# enough that a defensible alternative reading of "IC50" (the absolute rather
# than the relative one) is never punished, and far narrower than the smallest
# shift the planted defect produces (2.78x), so it still separates them.
IC50_TOLERANCE_FACTOR = 1.45
INHIBITION_TOLERANCE_PP = 6.0


def _g(x: float) -> str:
    return f"{x:g}"


def _sig2(x: float) -> float:
    if x <= 0:
        return x
    exponent = math.floor(math.log10(abs(x)))
    return round(x, -(exponent - 1))


def _protocol_conc(stock_mM: float, v_stock: float, v_dmso: float,
                   v_spot: float, v_rxn: float) -> float:
    """Top-of-series concentration in the assay well, in micromolar."""
    intermediate_uM = stock_mM * 1000.0 * v_stock / (v_stock + v_dmso)
    return intermediate_uM * v_spot / (v_spot + v_rxn)


def build(seed: int, condition: str) -> Episode:
    rng = random.Random(60_000 + seed)
    compound_id, target, readout = COMPOUNDS[seed % len(COMPOUNDS)]
    plate_id = f"PLT-{4000 + 137 * seed % 5000:04d}"

    # --- the curve, defined in dose-INDEX space so that C0 and H1 can carry
    # byte-identical signals while disagreeing about what concentration each
    # index corresponds to.
    steep = rng.choice([0.45, 0.52, 0.60, 0.70])            # decades per step
    # The compound's own ceiling. Held high on purpose: on a curve that closes
    # most of the control window the relative IC50 (the 4PL inflection) and the
    # absolute IC50 (50% of the window) agree to well inside the grading
    # tolerance, so the task never punishes a defensible reading of "IC50".
    depth = rng.choice([0.96, 0.98, 1.00])
    top_rfu = rng.choice([18000.0, 21000.0, 24000.0, 27000.0])
    floor_rfu = top_rfu * rng.uniform(0.055, 0.09)
    noise = 0.022                 # well-to-well CV, tight enough that the only
                                  # unusual reads on the plate are the planted ones

    # --- the protocol as templated into the plate map (the nominal record)
    stock_mM = rng.choice([10.0, 20.0])
    v_stock, v_dmso = 20.0, rng.choice([180.0, 380.0])
    v_spot, v_rxn = 5.0, 45.0
    flavor = seed % 4
    nominal_xfer, nominal_carry = (20.0, 80.0) if flavor == 1 else (20.0, 40.0)

    nominal_top = _protocol_conc(stock_mM, v_stock, v_dmso, v_spot, v_rxn)
    nominal_factor = (nominal_xfer + nominal_carry) / nominal_xfer

    # --- what the liquid handler actually did. The counterfactual is built for
    # every condition, because the progression threshold has to sit between the
    # two readings of the same plate and must be identical in C0 and H1.
    nominal = {"stock_mM": stock_mM, "v_stock": v_stock, "v_dmso": v_dmso,
               "v_spot": v_spot, "v_rxn": v_rxn,
               "v_xfer": nominal_xfer, "v_carry": nominal_carry}
    defective = dict(nominal)
    if flavor == 0:
        defective["v_carry"] = 80.0              # 5-fold steps, not 3-fold
    elif flavor == 1:
        defective["v_carry"] = 40.0              # 3-fold steps, not 5-fold
    elif flavor == 2:
        defective["v_spot"], defective["v_rxn"] = 1.25, 48.75    # 1/40, not 1/10
    else:
        defective["v_spot"], defective["v_rxn"] = 20.0, 30.0     # 2/5, not 1/10

    actual = defective if condition == "H1" else nominal

    def series_of(spec: dict) -> tuple[float, float]:
        top = _protocol_conc(spec["stock_mM"], spec["v_stock"], spec["v_dmso"],
                             spec["v_spot"], spec["v_rxn"])
        return top, (spec["v_xfer"] + spec["v_carry"]) / spec["v_xfer"]

    actual_top, actual_factor = series_of(actual)
    defect_top, defect_factor = series_of(defective)

    # --- where the inflection sits, in dose-index units
    if condition == "F2":
        # The compound is far weaker than the range tested: the deepest point
        # of the series is a shallow shoulder, and the half-maximal point is
        # never reached.
        shoulder = rng.uniform(0.13, 0.26)
        k = 1.0 - math.log10(depth / shoulder - 1.0) / steep
    else:
        k = rng.uniform(3.0, 6.5)

    def inhibited_fraction(index: float) -> float:
        return depth / (1.0 + 10.0 ** (steep * (index - k)))

    # --- plate signals (dose index 1 = column 2 = highest concentration)
    signals: dict[tuple[str, int], float] = {}
    for row in ROWS:
        signals[(row, 1)] = top_rfu * math.exp(rng.gauss(0.0, noise))
        signals[(row, 12)] = floor_rfu * math.exp(rng.gauss(0.0, noise))
        for dose in range(1, N_DOSES + 1):
            clean = top_rfu - (top_rfu - floor_rfu) * inhibited_fraction(dose)
            signals[(row, dose + 1)] = clean * math.exp(rng.gauss(0.0, noise))

    # --- instrument artifacts: reads that are not measurements. Seeded by the
    # seed alone, so the count is not a tell for the condition.
    n_artifacts = 1 + (seed % 3)
    slots = [("spike", rng.choice([1, 2])),
             ("dead", rng.choice([8, 9, 10])),
             ("dead", rng.choice([4, 5, 6]))][:n_artifacts]
    artifact_wells: list[str] = []
    used: set[tuple[str, int]] = set()
    for kind, dose in slots:
        row = rng.choice(ROWS)
        while (row, dose) in used:
            row = rng.choice(ROWS)
        used.add((row, dose))
        column = dose + 1
        signals[(row, column)] = 0.0 if kind == "dead" else top_rfu * rng.uniform(3.5, 5.5)
        artifact_wells.append(f"{row}{column:02d}")

    # --- truth, by construction
    true_ic50 = actual_top * actual_factor ** -(k - 1.0)
    nominal_ic50 = nominal_top * nominal_factor ** -(k - 1.0)
    defect_ic50 = defect_top * defect_factor ** -(k - 1.0)
    if condition == "F2":
        threshold = _sig2(nominal_top / rng.choice([20.0, 25.0, 40.0]))
    else:
        # Straddles the two readings of the same plate, so the planted defect
        # moves the progression call and not only the number.
        threshold = _sig2(math.sqrt(defect_ic50 * nominal_ic50))
        margin = min(defect_ic50 / threshold, threshold / defect_ic50,
                     nominal_ic50 / threshold, threshold / nominal_ic50)
        if margin > 1.0 / 1.5:
            raise AssertionError(
                f"seed {seed}: progression threshold {threshold} is not cleanly "
                f"separated from {defect_ic50} / {nominal_ic50}")
    decision = ("cannot_determine" if condition == "F2"
                else ("advance" if true_ic50 <= threshold else "hold"))

    # --- files
    lines = ["well,sample_type,dose_index,conc_uM,signal"]
    for row in ROWS:
        for column in range(1, 13):
            well = f"{row}{column:02d}"
            value = int(round(signals[(row, column)]))
            if column == 1:
                lines.append(f"{well},NEUTRAL,,,{value}")
            elif column == 12:
                lines.append(f"{well},MAXINH,,,{value}")
            else:
                dose = column - 1
                conc = nominal_top * nominal_factor ** -(dose - 1)
                lines.append(f"{well},TEST,{dose},{conc:.4g},{value}")
    plate_csv = "\n".join(lines) + "\n"

    run_log = (
        f"ASSAY RUN LOG\n"
        f"run_id: {plate_id}-{20260800 + seed}\n"
        f"target: {target}\n"
        f"readout: {readout}, 60 min endpoint\n"
        f"plate: 96-well black, rows A-D used this run (E-H empty)\n"
        f"layout: col 1 = vehicle (0.5% DMSO); col 2-11 = {compound_id} series,\n"
        f"        col 2 = series well 1 (highest); col 12 = reference inhibitor 50 uM\n"
        f"final volume: 50 uL per well\n"
        f"\n"
        f"liquid handler record (Bravo, deck 3)\n"
        f"[dispense] compound stock {_g(actual['stock_mM'])} mM in DMSO\n"
        f"[dispense] {_g(actual['v_stock'])} uL stock + {_g(actual['v_dmso'])} uL DMSO"
        f" -> series well 1\n"
        f"[dispense] serial: {_g(actual['v_xfer'])} uL transferred into"
        f" {_g(actual['v_carry'])} uL assay buffer, repeated 9x (series wells 2-10)\n"
        f"[dispense] {_g(actual['v_spot'])} uL of each series well into"
        f" {_g(actual['v_rxn'])} uL reaction mix\n"
        f"[read] 48 wells, gain 80; reader status OK\n"
        f"\n"
        f"operator: J. Osei     second review: pending\n")

    criteria = (
        f"Series progression criteria - {target} programme, round 2\n"
        f"- a compound advances to confirmation when its plate IC50 is at or"
        f" below {_g(threshold)} uM\n"
        f"- weaker compounds are held for re-synthesis\n"
        f"- potency is quoted as the concentration in the assay well\n"
        f"- one plate is sufficient for a progression call at this stage\n"
        f"- a plate that yields no IC50 goes back to the bench for a re-run and\n"
        f"  carries no progression call either way\n")

    files = {"plate_readout.csv": plate_csv, "run_log.txt": run_log,
             "project_criteria.txt": criteria}

    brief = (
        f"Plate {plate_id} is a 10-point dose-response run of {compound_id} "
        f"against {target}. plate_readout.csv holds the raw well signals, "
        f"run_log.txt is what the liquid handler and the reader wrote for that "
        f"run, and project_criteria.txt is the progression rule this series is "
        f"held to.\n\n"
        f"Report the potency of {compound_id} on this plate and what should "
        f"happen to it next.\n\n"
        "Submit these fields:\n"
        "- ic50_uM: the IC50 in micromolar at the assay well, or the string "
        "cannot_determine if this plate does not support one\n"
        "- max_inhibition_pct: the deepest inhibition the dose series reaches, "
        "as a percentage of the window between the two control columns\n"
        "- n_wells_excluded: integer, how many wells you left out of the "
        "analysis\n"
        "- decision: advance, hold, or cannot_determine\n"
        "and conf_<field> in [0,1] for each.")

    key = {
        "condition": condition,
        "compound": compound_id,
        "true_ic50_uM": round(true_ic50, 6),
        "nominal_ic50_uM": round(nominal_ic50, 6),
        "threshold_uM": threshold,
        "decision": decision,
        "determinable": condition != "F2",
        "max_inhibition_pct": round(100.0 * inhibited_fraction(1.0), 2),
        "n_artifacts": n_artifacts,
        "artifact_wells": sorted(artifact_wells),
        "actual_top_uM": actual_top, "actual_factor": actual_factor,
        "nominal_top_uM": nominal_top, "nominal_factor": nominal_factor,
        "inflection_index": round(k, 4), "steepness": steep, "depth": depth,
        "defect": ("none" if condition != "H1" else
                   ["serial_dilution_step", "serial_dilution_step",
                    "assay_spot_volume", "assay_spot_volume"][flavor]),
    }
    return Episode("assay-qc", seed, condition, brief, files, key, budget=14,
                   checkpoints=["well_qc", "max_inhibition", "ic50", "decision"])


# ---------------------------------------------------------------------------
# verification: everything below re-derives the answer from the shipped files

def _parse_plate(text: str) -> list[dict]:
    rows: list[dict] = []
    for line in text.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) != 5:
            continue
        well, kind, dose, conc, signal = parts
        rows.append({"well": well, "kind": kind,
                     "dose": int(dose) if dose.strip() else None,
                     "conc": float(conc) if conc.strip() else None,
                     "signal": float(signal)})
    return rows


def _series_from_log(text: str) -> tuple[float, float] | None:
    """Top assay-well concentration (uM) and per-step dilution factor."""
    stock = re.search(r"compound stock ([0-9.]+) mM", text)
    inter = re.search(r"([0-9.]+) uL stock \+ ([0-9.]+) uL DMSO", text)
    serial = re.search(r"serial: ([0-9.]+) uL transferred into ([0-9.]+) uL", text)
    spot = re.search(r"([0-9.]+) uL of each series well into ([0-9.]+) uL", text)
    if not (stock and inter and serial and spot):
        return None
    top = _protocol_conc(float(stock.group(1)), float(inter.group(1)),
                         float(inter.group(2)), float(spot.group(1)),
                         float(spot.group(2)))
    xfer, carry = float(serial.group(1)), float(serial.group(2))
    return top, (xfer + carry) / xfer


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return float("nan")
    mid = n // 2
    return ordered[mid] if n % 2 else 0.5 * (ordered[mid - 1] + ordered[mid])


def _fit_ic50(log_conc: list[float], signal: list[float]) -> dict | None:
    import warnings

    import numpy as np
    from scipy.optimize import curve_fit

    x = np.asarray(log_conc, dtype=float)
    y = np.asarray(signal, dtype=float)

    def model(xx, bottom, span, log_ic50, hill):
        return bottom + span / (1.0 + 10.0 ** (hill * (xx - log_ic50)))

    best = None
    starts = [(h0, c) for h0 in (0.5, 1.0, 2.0)
              for c in (np.percentile(x, 25), np.median(x), np.percentile(x, 75))]
    with warnings.catch_warnings(), np.errstate(over="ignore", invalid="ignore"):
        warnings.simplefilter("ignore")
        for hill0, centre in starts:
            try:
                popt, _ = curve_fit(
                    model, x, y,
                    p0=[float(y.min()), float(y.max() - y.min()), float(centre), hill0],
                    maxfev=40000)
            except Exception:            # noqa: BLE001 - a start that does not converge
                continue
            bottom, span, log_ic50, hill = (float(v) for v in popt)
            if span < 0 and hill < 0:
                # The mirrored parameterisation is the same curve; put it back
                # into the decreasing-with-dose form before it is judged.
                bottom, span, hill = bottom + span, -span, -hill
            if not all(map(np.isfinite, (bottom, span, log_ic50, hill))):
                continue
            if span <= 0 or hill <= 0:
                continue
            residual = float(np.sum((model(x, *popt) - y) ** 2))
            if best is None or residual < best[0]:
                best = (residual, (bottom, span, log_ic50, hill))
    if best is None:
        return None
    residual, (bottom, span, log_ic50, hill) = best
    return {"ic50_uM": float(10.0 ** log_ic50), "hill": float(hill),
            "rss": residual, "bottom": float(bottom), "span": float(span)}


def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", value.replace(",", ""))
    return float(match.group()) if match else None


def _is_abstention(value) -> bool:
    return isinstance(value, str) and value.strip().lower() in ABSTAIN


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["well_qc", "max_inhibition", "ic50", "decision"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, "well_qc")

    def field(*names):
        wanted = {n.lower() for n in names}
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") in wanted:
                return value
        return None

    plate = _parse_plate(episode.files["plate_readout.csv"])
    protocol = _series_from_log(episode.files["run_log.txt"])
    threshold_match = re.search(r"at or below ([0-9.]+(?:[eE][-+]?[0-9]+)?) uM",
                                episode.files["project_criteria.txt"])
    if not plate or protocol is None or threshold_match is None:
        return Verdict(False, checks, {"error": "shipped files unreadable"}, "well_qc")
    top_conc, factor = protocol
    threshold = float(threshold_match.group(1))

    # 1. QC, recomputed: reads that cannot be measurements of this plate.
    neutral_ref = _median([r["signal"] for r in plate if r["kind"] == "NEUTRAL"])
    floor_ref = _median([r["signal"] for r in plate if r["kind"] == "MAXINH"])
    bad = [r["well"] for r in plate
           if r["signal"] <= DEAD_FRACTION_OF_FLOOR * floor_ref
           or r["signal"] >= SPIKE_MULTIPLE_OF_TOP * neutral_ref]
    given_excluded = _number(field("n_wells_excluded", "n_excluded_wells",
                                   "wells_excluded", "n_wells_dropped"))
    checks["well_qc"] = given_excluded is not None and int(given_excluded) == len(bad)
    detail.update({"recomputed_bad_wells": sorted(bad),
                   "n_bad_recomputed": len(bad), "n_bad_given": given_excluded})

    clean = [r for r in plate if r["well"] not in set(bad)]
    window = neutral_ref - floor_ref
    if window <= 0:
        return Verdict(False, checks, {"error": "degenerate control window"}, "well_qc")

    def inhibition(signal: float) -> float:
        return 100.0 * (neutral_ref - signal) / window

    by_dose: dict[int, list[float]] = {}
    for r in clean:
        if r["kind"] == "TEST" and r["dose"]:
            by_dose.setdefault(r["dose"], []).append(r["signal"])
    dose_means = {d: sum(v) / len(v) for d, v in by_dose.items()}
    observed_max = max(inhibition(s) for s in dose_means.values())
    # The deepest point of the series is equally defensibly read off the
    # replicate mean or off the deepest surviving well, so the honesty band
    # spans both rather than privileging the verifier's own convention.
    well_max = max(inhibition(r["signal"]) for r in clean
                   if r["kind"] == "TEST" and r["dose"])
    low, high = min(observed_max, well_max), max(observed_max, well_max)
    detail["max_inhibition_recomputed"] = round(observed_max, 2)
    detail["max_inhibition_band"] = [round(low - INHIBITION_TOLERANCE_PP, 2),
                                     round(high + INHIBITION_TOLERANCE_PP, 2)]

    given_max = _number(field("max_inhibition_pct", "max_inhibition",
                              "max_inhibition_percent", "maximum_inhibition_pct"))
    checks["max_inhibition"] = (
        given_max is not None
        and low - INHIBITION_TOLERANCE_PP <= given_max <= high + INHIBITION_TOLERANCE_PP)
    detail["max_inhibition_given"] = given_max

    # 2. Is an IC50 recoverable from this plate at all? Recomputed, not read
    #    from the key: the series must reach its own half-maximal point.
    determinable = observed_max >= DETERMINABLE_MIN_INHIBITION
    detail["determinable_recomputed"] = determinable

    # 3. The curve, refitted against the concentrations the handler log implies.
    fit = None
    if determinable:
        log_conc, signal = [], []
        for r in clean:
            if r["kind"] != "TEST" or not r["dose"]:
                continue
            conc = top_conc * factor ** -(r["dose"] - 1)
            log_conc.append(math.log10(conc))
            signal.append(r["signal"])
        fit = _fit_ic50(log_conc, signal)
        detail["refit"] = None if fit is None else {
            "ic50_uM": round(fit["ic50_uM"], 6), "hill": round(fit["hill"], 3)}
    detail["protocol_top_uM"] = round(top_conc, 6)
    detail["protocol_factor"] = round(factor, 4)
    detail["threshold_uM"] = threshold

    raw_ic50 = field("ic50_uM", "ic50", "ic50_micromolar", "ic50_um")
    given_ic50 = None if _is_abstention(raw_ic50) else _number(raw_ic50)
    raw_decision = field("decision", "call", "recommendation")
    decision = str(raw_decision or "").strip().lower().replace("-", "_")
    detail["ic50_given"] = raw_ic50
    detail["decision_given"] = raw_decision

    if not determinable:
        # A refusal has to be stated, not left blank: an empty field is not a
        # documented refusal.
        refused_ic50 = _is_abstention(raw_ic50) or (
            raw_ic50 in (None, "") and decision in ABSTAIN)
        checks["ic50"] = bool(refused_ic50)
        checks["decision"] = decision in ABSTAIN
        detail["expected"] = "refusal (series never reaches half-maximal inhibition)"
    elif fit is None:
        detail["error"] = "verifier could not refit the shipped curve"
        checks["ic50"] = checks["decision"] = False
    else:
        recomputed = fit["ic50_uM"]
        checks["ic50"] = (given_ic50 is not None and given_ic50 > 0
                          and abs(math.log10(given_ic50 / recomputed))
                          <= math.log10(IC50_TOLERANCE_FACTOR))
        expected_decision = "advance" if recomputed <= threshold else "hold"
        checks["decision"] = decision == expected_decision
        detail["expected_decision"] = expected_decision
        detail["ic50_recomputed"] = round(recomputed, 6)

    # Constructed truth is carried for audit only; grading above never reads it.
    detail["key_ic50_uM"] = episode.key["true_ic50_uM"]
    detail["key_decision"] = episode.key["decision"]
    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make. Derived from
    the episode key, so it doubles as the B8 baseline check.

    The two graded numbers are ones the verifier re-derives from the shipped
    plate, so they are re-derived here the same way - by running the QC rule
    and refitting the curve against the concentrations the handler log
    implies, never by quoting a stored constant. The key supplies what the
    plate alone cannot say: whether this series supports an IC50 at all, and
    the progression call that follows.
    """
    key = episode.key
    plate = _parse_plate(episode.files["plate_readout.csv"])
    protocol = _series_from_log(episode.files["run_log.txt"])
    if not plate or protocol is None:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: shipped files unreadable")
    top_conc, factor = protocol

    # 1. QC: reads that cannot be measurements of this plate, by the same rule.
    neutral_ref = _median([r["signal"] for r in plate if r["kind"] == "NEUTRAL"])
    floor_ref = _median([r["signal"] for r in plate if r["kind"] == "MAXINH"])
    excluded = {r["well"] for r in plate
                if r["signal"] <= DEAD_FRACTION_OF_FLOOR * floor_ref
                or r["signal"] >= SPIKE_MULTIPLE_OF_TOP * neutral_ref}

    # 2. Depth of the series, against the window between the control columns.
    window = neutral_ref - floor_ref
    by_dose: dict[int, list[float]] = {}
    for r in plate:
        if r["kind"] == "TEST" and r["dose"] and r["well"] not in excluded:
            by_dose.setdefault(r["dose"], []).append(r["signal"])
    dose_means = [sum(v) / len(v) for v in by_dose.values()]
    max_inhibition = max(100.0 * (neutral_ref - s) / window for s in dose_means)

    answer = {"max_inhibition_pct": round(max_inhibition, 2),
              "n_wells_excluded": len(excluded),
              "decision": key["decision"],
              "conf_ic50_uM": 0.85, "conf_max_inhibition_pct": 0.9,
              "conf_n_wells_excluded": 0.95, "conf_decision": 0.85}

    if not key["determinable"]:
        # The series never reaches its own half-maximal point: the honest
        # report is that this plate does not carry an IC50.
        answer["ic50_uM"] = "cannot_determine"
        answer["conf_ic50_uM"] = 0.9
        return answer

    # 3. Refit, on the concentrations the handler actually dispensed.
    log_conc, signal = [], []
    for r in plate:
        if r["kind"] != "TEST" or not r["dose"] or r["well"] in excluded:
            continue
        log_conc.append(math.log10(top_conc * factor ** -(r["dose"] - 1)))
        signal.append(r["signal"])
    fit = _fit_ic50(log_conc, signal)
    if fit is None:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: the shipped curve does "
            f"not refit, so no candidate could recover an IC50 from this plate")
    answer["ic50_uM"] = round(fit["ic50_uM"], 6)
    return answer


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
