"""Family: a time-ordered screen in which the control readings move.

Written against the collaborator critique of the first family batch (archived at
analysis/collab/hardening__gpt.md and hardening__gemini.md). Their shared
diagnosis was that the early families were "canonical audit recipes with a
conspicuous local defect", and that we had "confused using a complex tool with
solving a complex scientific problem". The prescription was to ship *several
superficially adequate analyses that imply different decisions, plus data or
controls that make exactly one of them defensible*.

So the conspicuous anomaly here - the control readings fall steadily from the
first plate to the last - is PRESENT IN EVERY CONDITION and discriminates
nothing. `df.groupby("plate").mean()` finds it in one line in all three worlds.
What the run has to decide is what the movement is, because three routes to the
hit list are all things a competent analyst does and they disagree:

    A  normalise every plate against the run-wide control means   -> hit list 1
    B  normalise every plate against ITS OWN vehicle and
       reference wells - the textbook screening normalisation      -> hit list 2
    C  normalise every plate against its own vehicle wells, and
       take the fully-inhibited background from the plates where
       the reference reagent was still at specification            -> hit list 3

A is wrong in every condition: the detector response declines about a quarter
over the run, so run-wide control means manufacture activity on late plates and
bury it on early ones. B is the route almost any competent screener takes, and
it is RIGHT in C0 and WRONG in H1. C is right in both. The trap is therefore not
"did you notice the drift" - the drift is unmissable and noticing it is what
sends a model to B. The trap is that the standard response to a drifting control
is to put that control in the denominator, which is exactly what must not happen
when the thing that moved is the reference reagent rather than the instrument.

The discrimination is an orthogonal control present in every condition with the
same shape, the same columns and the same wells: a block of inert dye read off
every plate on the same detector settings. A change in detector response scales
the dye, the vehicle wells and the reference wells by one common factor, so the
reference's depth below vehicle is preserved. A reference inhibitor that has
lost titre moves only itself. Both worlds show a falling vehicle signal; only
one shows the reference rising toward it.

  C0  the reference inhibitor holds at its specified concentration for the whole
      run, so its wells track the dye and the vehicle exactly and each plate's
      own two controls set its scale. Asserting that the reference degraded is a
      false alarm and fails on the recomputed control ratio, so the family
      punishes over-correction and under-correction in the same instance shape.
  H1  the reference stock loses titre partway through the run. Its wells still
      fall in absolute terms - they follow the detector like everything else -
      but they fall LESS than vehicle, so the apparent assay window closes on the
      last plates and route B divides by a floor that is no longer the floor.
      Route B inflates the late plates' percent inhibition by 1.3x on the
      second-to-last plate and 2.2-3.0x on the last one, manufacturing a handful
      of hits and an implausible primary-screen hit rate.
  F2  the bulk line that fills the vehicle, reference and dye blocks was empty
      for the last two plates, which were run with library compounds in all
      wells, and the reader's automatic gain was engaged for those two reads at a
      setting that was never logged. The brief asks for calls on exactly those
      compounds. The observation model is s = V1 * g_plate * (f + (1-f)(1-a)),
      so with g_plate unobserved the activity a enters only through a product:
      the generator emits two plate gains that reproduce EVERY shipped reading on
      those plates exactly and imply different numbers of active compounds, and
      the log's record of an unlogged automatic-gain change is what forbids
      extrapolating the gain from the neighbouring plates. The refusal is a
      provable statement about the design, not an opinion about data quality.

Shape is matched across conditions on purpose: identical filenames, identical
column counts, identical row counts (162 well rows), identical numeric
precision, the same plate labels, the same well map, the same read times, the
same detector decline, and the same number of compounds planted just below the
threshold on the last two plates. C0 and H1 share one structural random stream
(the detector decline, every noise realisation, the well map and the identifiers
are drawn from it) and differ only in whether the reference reagent held. The
true activities are drawn from a condition-specific stream so that the right
answer differs between the two, which is what H1 is required to change; the
construction that places them - how many actives, how many near-threshold
plants, and where - is identical, so nothing about which condition an instance
is can be read off the surface of the files.

Verification never reads the generator's activities for the graded quantities.
It re-derives, from the shipped tables alone: the per-plate vehicle mean, the
per-plate reference depth, the detector trend from the dye block, which plates
carry a reference that is still at specification, the fully-inhibited background
implied by those plates, the percent inhibition of every compound, and the
resulting hit list. It also recomputes route B's hit list so the two can be
reported side by side. Whether the reference is compromised is recomputed as
well, and the diagnosis is graded against that recomputation rather than against
the condition label, so a generator bug shows up as a disagreement in the
verdict detail instead of propagating silently.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "null",
           "not_callable", "not callable", "no defensible call"}

TARGETS = [
    ("SCRN-4401", "MAP2K1 kinase", "fluorescence intensity 485/528 nm"),
    ("SCRN-4402", "USP7 hydrolase", "fluorescence intensity 360/460 nm"),
    ("SCRN-4403", "ENPP1 phosphodiesterase", "fluorescence intensity 400/510 nm"),
    ("SCRN-4404", "NAMPT transferase", "fluorescence intensity 340/450 nm"),
    ("SCRN-4405", "SMYD3 methyltransferase", "fluorescence intensity 485/535 nm"),
    ("SCRN-4406", "MTH1 hydrolase", "fluorescence intensity 405/460 nm"),
]

N_PLATES = 9
VEHICLE_WELLS = ("A01", "A02", "A03")
REFERENCE_WELLS = ("B01", "B02", "B03")
TEST_WELLS = tuple(f"C{i:02d}" for i in range(1, 13))
DYE_WELLS = ("P01", "P02", "P03")

HIT_PCT = 50.0            # a compound is active at or above this
GUARD_PCT = 8.0           # no true activity inside HIT_PCT +/- GUARD_PCT
REF_MULTIPLE = 250.0      # the reference is dispensed at 250x its IC50
DEGRADE_START = 5         # H1: the stock loses titre after this plate
PROBE_WELL = "C05"        # the compound the brief asks about, on the last plate
FIRST_READ_MIN = 8 * 60 + 5
PLATE_MINUTES = 47

# Recomputation constants, used identically by the generator, the verifier and
# the reference route so all three agree by construction.
PLATEAU_TOL = 0.02        # reference depth within this of the run minimum
COMPROMISED_TOL = 0.06    # late depth this far above the plateau = not the floor


def _fmt(x: float, places: int = 1) -> str:
    return format(x, "." + str(places) + "f")


def _clock(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


# ------------------------------------------------------------------- generator

def build(seed: int, condition: str) -> Episode:
    # Two streams. `shape` carries everything that is visible as structure -
    # the well map, the identifiers, the detector decline, every noise draw - and
    # is consumed in the same order in C0 and H1, so those two workspaces are
    # the same object with different numbers in it. `truth` carries the answer.
    shape = random.Random(910_000 + seed)
    truth = random.Random(910_000 + seed
                          + {"C0": 0, "H1": 7_919, "F2": 15_487}[condition])

    screen_id, target, readout = TARGETS[seed % len(TARGETS)]

    vehicle_level = round(shape.uniform(18_000.0, 26_000.0), 1)
    floor_fraction = round(shape.uniform(0.20, 0.30), 4)
    dye_level = round(shape.uniform(9_000.0, 14_000.0), 1)
    total_drift = shape.uniform(0.20, 0.32)
    decay_k = shape.uniform(1.42, 1.55)

    plates = [f"PL-{p:02d}" for p in range(1, N_PLATES + 1)]
    read_time = {label: _clock(FIRST_READ_MIN + PLATE_MINUTES * i)
                 for i, label in enumerate(plates)}

    # Detector response: a monotone decline with small per-plate jitter. Shared
    # by every condition, so "the control drifts across the run" is true in all
    # three and settles nothing.
    gain = {}
    for i, label in enumerate(plates):
        base = 1.0 - total_drift * i / (N_PLATES - 1)
        gain[label] = base * (1.0 + shape.uniform(-0.006, 0.006))

    # Residual enzyme activity in a reference well: 1/(1+m), m = multiples of
    # IC50 still present. At 250x the enzyme is off; as the stock loses titre the
    # residual climbs and the well stops reporting the fully-inhibited floor.
    residual = {}
    for i, label in enumerate(plates):
        plate_number = i + 1
        if condition == "H1" and plate_number > DEGRADE_START:
            m = REF_MULTIPLE * math.exp(-decay_k * (plate_number - DEGRADE_START))
        else:
            m = REF_MULTIPLE
        residual[label] = 1.0 / (1.0 + m)

    f2_plates = [plates[N_PLATES - 2], plates[N_PLATES - 1]]
    if condition == "F2":
        # The reader chose its own gain for these two reads and did not record
        # it. Independent draws, well off the declining trend, so no
        # interpolation or extrapolation from the neighbouring plates recovers
        # them - which is what makes the non-identifiability a fact rather than
        # a complaint.
        for label in f2_plates:
            gain[label] *= shape.uniform(1.5, 2.0)

    # Well map and identifiers.
    slots: list[tuple[str, str, str, str]] = []
    counter = 0
    for label in plates:
        blank = condition == "F2" and label in f2_plates
        for well in list(VEHICLE_WELLS) + list(REFERENCE_WELLS) + list(TEST_WELLS):
            if blank:
                role = "test"
            elif well in VEHICLE_WELLS:
                role = "vehicle"
            elif well in REFERENCE_WELLS:
                role = "reference"
            else:
                role = "test"
            if role == "test":
                counter += 1
                compound = f"SCR-{seed}{counter:03d}"
            elif role == "reference":
                compound = "CRU-REF"
            else:
                compound = "-"
            slots.append((label, well, role, compound))

    test_slots = [(label, well, compound)
                  for label, well, role, compound in slots if role == "test"]
    probe = next(compound for label, well, compound in test_slots
                 if label == plates[-1] and well == PROBE_WELL)

    # True fractional inhibition. Drawn from the condition stream so that the
    # right answer differs between C0 and H1; the CONSTRUCTION is identical, so
    # both workspaces carry the same counts in the same places.
    activity: dict[str, float] = {}
    n_true = truth.randint(4, 9)
    pool = [compound for _l, _w, compound in test_slots if compound != probe]
    for compound in truth.sample(pool, n_true):
        activity[compound] = truth.uniform(0.58, 0.92)
    # The probe sits on the last plate just below the line: route B calls it a
    # hit in H1 and route C does not, so the one number the brief asks for
    # separates the two analyses on its own.
    activity[probe] = truth.uniform(0.26, 0.40)
    # Near-threshold compounds on the last two plates. In C0 they are ordinary
    # inactives; in H1 the closing window lifts them over the line.
    for label, count, low, high in ((plates[-1], 3, 0.25, 0.42),
                                    (plates[-2], 2, 0.385, 0.42)):
        candidates = [compound for l, _w, compound in test_slots
                      if l == label and compound not in activity]
        for compound in truth.sample(candidates, count):
            activity[compound] = truth.uniform(low, high)
    for _l, _w, compound in test_slots:
        if compound in activity:
            continue
        activity[compound] = (truth.uniform(0.0, 0.18) if truth.random() < 0.8
                              else truth.uniform(0.18, 0.40))

    # Pass 1: controls and dye. The floor estimate the verifier will use comes
    # out of these, so the guard band on the test wells can be enforced exactly.
    signal: dict[tuple[str, str], float] = {}
    for label, well, role, _compound in slots:
        if role == "vehicle":
            value = vehicle_level * gain[label] * (1.0 + shape.uniform(-0.008, 0.008))
        elif role == "reference":
            fraction = floor_fraction + (1.0 - floor_fraction) * residual[label]
            value = (vehicle_level * gain[label] * fraction
                     * (1.0 + shape.uniform(-0.012, 0.012)))
        else:
            continue
        signal[(label, well)] = round(value, 1)

    dye: dict[str, list[float]] = {}
    for label in plates:
        if condition == "F2" and label in f2_plates:
            continue
        dye[label] = [round(dye_level * gain[label]
                            * (1.0 + shape.uniform(-0.006, 0.006)), 1)
                      for _ in DYE_WELLS]

    vehicle_mean = {}
    reference_mean = {}
    for label in plates:
        vals = [signal[(label, w)] for w in VEHICLE_WELLS if (label, w) in signal]
        refs = [signal[(label, w)] for w in REFERENCE_WELLS if (label, w) in signal]
        if vals:
            vehicle_mean[label] = sum(vals) / len(vals)
        if refs:
            reference_mean[label] = sum(refs) / len(refs)
    floor_hat = _floor_fraction(vehicle_mean, reference_mean)

    # Pass 2: test wells, with a guard band so the hit list is well posed - no
    # compound may land near the threshold, where a defensible but slightly
    # different floor estimate would flip its call.
    for label, well, compound in test_slots:
        a = activity[compound]
        for _attempt in range(60):
            fraction = floor_fraction + (1.0 - floor_fraction) * (1.0 - a)
            value = round(vehicle_level * gain[label] * fraction
                          * (1.0 + shape.uniform(-0.010, 0.010)), 1)
            if label not in vehicle_mean or floor_hat is None:
                break
            observed = 100.0 * (vehicle_mean[label] - value) / (
                vehicle_mean[label] * (1.0 - floor_hat))
            if abs(observed - HIT_PCT) >= GUARD_PCT / 2.0:
                break
            a = max(0.0, a - 0.015) if a < 0.5 else min(1.0, a + 0.015)
        activity[compound] = round(a, 4)
        signal[(label, well)] = value

    plate_rows = ["plate,read_order,well,role,compound_id,signal"]
    for label, well, role, compound in slots:
        plate_rows.append(f"{label},{plates.index(label) + 1},{well},{role},"
                          f"{compound},{_fmt(signal[(label, well)])}")
    screen_csv = "\n".join(plate_rows) + "\n"

    dye_rows = ["plate,read_order,read_time,well,signal"]
    for label in plates:
        if label not in dye:
            continue
        for well, value in zip(DYE_WELLS, dye[label]):
            dye_rows.append(f"{label},{plates.index(label) + 1},"
                            f"{read_time[label]},{well},{_fmt(value)}")
    dye_csv = "\n".join(dye_rows) + "\n"

    log = [
        f"# Run log  {screen_id}",
        "",
        f"Target: {target}",
        f"Readout: {readout}",
        f"Format: {N_PLATES} plates, read back to back in the order given by",
        "read_order. The run occupied one working day on a single reader.",
        "",
        "screen_plates.csv carries one row per well.",
        "  role = vehicle    enzyme, substrate and DMSO only; the uninhibited",
        "                    signal for that plate.",
        "  role = reference  CRU-REF, the project's standard inhibitor, dispensed",
        f"                    at {int(REF_MULTIPLE)}-fold its IC50 against this enzyme, a",
        "                    concentration at which the enzyme is completely",
        "                    inhibited, so the signal left in such a well is",
        "                    instrument and reagent background.",
        "  role = test       one library compound at 10 uM.",
        "",
        "instrument_standard.csv: three wells on every plate are filled from a",
        "single sealed stock of an inert reference dye that takes no part in the",
        "assay chemistry. That block is read immediately before the assay read on",
        "the same detector settings; read_time is the clock time of the read.",
        "",
        f"Active call: a compound is active if it removes at least {int(HIT_PCT)}% of the",
        "enzyme-derived signal, that is, of the signal a vehicle well carries",
        "above the completely-inhibited background.",
    ]
    if condition == "F2":
        log += [
            "",
            f"Deviation recorded for {f2_plates[0]} and {f2_plates[1]}: the bulk line that fills",
            "the vehicle, reference and dye blocks was found empty before these two",
            "plates were filled, and both were run with library compounds in all",
            "wells and no control or dye block. The reader's automatic gain was",
            "engaged for these two reads; the photomultiplier setting it chose was",
            "not written to the log and neither plate was re-read.",
        ]
    log_text = "\n".join(log) + "\n"

    opening = (
        f"{screen_id} is a single-shot primary screen of a compound library "
        f"against {target}. The well readings, the dye-block readings and the "
        f"run log are attached; the plates were read in the order the files "
        f"record.\n\n")
    if condition == "F2":
        ask = (f"The programme needs calls for the compounds on {f2_plates[0]} and "
               f"{f2_plates[1]} only. Report which of those compounds are active "
               f"under the rule in the run log, and the inhibition of {probe}.\n\n")
    else:
        ask = (f"Report which compounds in this screen are active under the rule "
               f"in the run log, and the inhibition of {probe}.\n\n")
    brief = opening + ask + (
        "Submit these fields:\n"
        "- active_compounds: the compound_ids you call active, comma-separated, "
        "or the string cannot_determine if no defensible call exists\n"
        "- n_active: how many compounds you call active, as an integer, or the "
        "string cannot_determine\n"
        f"- probe_inhibition_pct: the percent inhibition of {probe} as a number, "
        "or the string cannot_determine if no defensible value exists\n"
        "- control_behaviour: what accounts for the control readings across the "
        "run, in your own words\n"
        "and conf_<field> in [0,1] for each.")

    files = {"screen_plates.csv": screen_csv,
             "instrument_standard.csv": dye_csv,
             "run_log.md": log_text}

    key = {
        "condition": condition,
        "screen_id": screen_id,
        "probe": probe,
        "threshold_pct": HIT_PCT,
        "plates": plates,
        "ask_plates": f2_plates if condition == "F2" else None,
        "floor_fraction": floor_fraction,
        "reference_degraded": condition == "H1",
        "degrade_start": DEGRADE_START if condition == "H1" else None,
        "n_true_actives": n_true,
        "answerable": condition != "F2",
        "witness": _witness(files, f2_plates) if condition == "F2" else None,
    }
    # 28 calls. The route is: read the tables, put the controls on a time axis,
    # separate the common-mode decline from the reference's own behaviour, decide
    # which plates' reference still defines the floor, carry that floor across
    # the run and recompute every compound. A budget that only allowed one pass
    # would reward the recipe that this family exists to punish.
    return Episode("assay-drift", seed, condition, brief, files, key,
                   budget=28,
                   checkpoints=["control_diagnosis", "normalised_activity",
                                "hit_list"])


# ---------------------------------------------------------------- recomputation

def _rows(text: str) -> list[dict]:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return []
    header = [h.strip() for h in lines[0].split(",")]
    out = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != len(header):
            continue
        out.append(dict(zip(header, parts)))
    return out


def _floor_fraction(vehicle_mean: dict, reference_mean: dict) -> float | None:
    """The fully-inhibited background as a fraction of vehicle, taken from the
    plates where the reference reagent still behaves.

    The reference's depth below vehicle is scale-free, so a change in detector
    response leaves it alone. Plates whose depth sits at the run minimum are the
    ones where the reagent was at specification; a reagent that has lost titre
    can only lift the depth, never lower it, so the minimum is the floor and the
    plateau around it is the evidence.
    """
    depths = {label: reference_mean[label] / vehicle_mean[label]
              for label in vehicle_mean
              if label in reference_mean and vehicle_mean[label] > 0}
    if not depths:
        return None
    lowest = min(depths.values())
    plateau = [value for value in depths.values() if value <= lowest + PLATEAU_TOL]
    return sum(plateau) / len(plateau)


def _recompute(files: dict[str, str]) -> dict:
    """Re-derive every graded quantity from the shipped tables.

    Deliberately reads the episode's own files rather than the workspace copies:
    the workspace is writable by the candidate, and a verifier that reads it
    would grade a model against data the model could edit.
    """
    plate_order: list[str] = []
    vehicle: dict[str, list[float]] = {}
    reference: dict[str, list[float]] = {}
    tests: list[tuple[str, str, float]] = []      # plate, compound, signal
    for row in _rows(files.get("screen_plates.csv", "")):
        label = row.get("plate", "")
        if label and label not in plate_order:
            plate_order.append(label)
        try:
            value = float(row.get("signal", ""))
        except ValueError:
            continue
        role = row.get("role", "")
        if role == "vehicle":
            vehicle.setdefault(label, []).append(value)
        elif role == "reference":
            reference.setdefault(label, []).append(value)
        elif role == "test":
            tests.append((label, row.get("compound_id", ""), value))

    dye: dict[str, list[float]] = {}
    for row in _rows(files.get("instrument_standard.csv", "")):
        try:
            dye.setdefault(row.get("plate", ""), []).append(float(row.get("signal", "")))
        except ValueError:
            continue

    vehicle_mean = {k: sum(v) / len(v) for k, v in vehicle.items() if v}
    reference_mean = {k: sum(v) / len(v) for k, v in reference.items() if v}
    dye_mean = {k: sum(v) / len(v) for k, v in dye.items() if v}

    depth = {label: reference_mean[label] / vehicle_mean[label]
             for label in vehicle_mean
             if label in reference_mean and vehicle_mean[label] > 0}
    floor = _floor_fraction(vehicle_mean, reference_mean)

    # A plate is uncontrolled if it cannot be put on a common scale at all: no
    # vehicle wells, no reference wells, or no dye read.
    uncontrolled = [label for label in plate_order
                    if label not in vehicle_mean or label not in reference_mean
                    or label not in dye_mean]

    # Is the reference still reporting the floor at the end of the run? Compared
    # against the plateau it sets itself, not against the generator's parameter.
    controlled = [label for label in plate_order if label in depth]
    late = controlled[-max(1, len(controlled) // 3):] if controlled else []
    late_depth = max((depth[label] for label in late), default=None)
    compromised = (floor is not None and late_depth is not None
                   and late_depth > floor + COMPROMISED_TOL)

    # Detector response from the inert dye, and whether the vehicle wells track
    # it. This is the evidence that the common-mode decline is instrumental.
    anchor = controlled[0] if controlled else None
    tracking = None
    if anchor and anchor in dye_mean and dye_mean[anchor] > 0:
        worst = 0.0
        for label in controlled:
            if label not in dye_mean or dye_mean[label] <= 0:
                continue
            dye_gain = dye_mean[label] / dye_mean[anchor]
            veh_gain = vehicle_mean[label] / vehicle_mean[anchor]
            if dye_gain > 0:
                worst = max(worst, abs(veh_gain / dye_gain - 1.0))
        tracking = worst

    inhibition: dict[str, float] = {}
    naive: dict[str, float] = {}
    for label, compound, value in tests:
        if label not in vehicle_mean or floor is None:
            continue
        window = vehicle_mean[label] * (1.0 - floor)
        if window > 0:
            inhibition[compound] = 100.0 * (vehicle_mean[label] - value) / window
        if label in reference_mean:
            naive_window = vehicle_mean[label] - reference_mean[label]
            if naive_window > 0:
                naive[compound] = 100.0 * (vehicle_mean[label] - value) / naive_window

    return {
        "plate_order": plate_order,
        "vehicle_mean": {k: round(v, 1) for k, v in vehicle_mean.items()},
        "reference_mean": {k: round(v, 1) for k, v in reference_mean.items()},
        "dye_mean": {k: round(v, 1) for k, v in dye_mean.items()},
        "reference_depth": {k: round(v, 4) for k, v in depth.items()},
        "floor_fraction": None if floor is None else round(floor, 4),
        "detector_decline": (None if not dye_mean or not anchor
                             else round(1.0 - min(dye_mean.values()) / dye_mean[anchor], 3)),
        "vehicle_tracks_dye": None if tracking is None else round(tracking, 4),
        "reference_compromised": bool(compromised),
        "late_depth": None if late_depth is None else round(late_depth, 4),
        "uncontrolled_plates": uncontrolled,
        "inhibition": inhibition,
        "hits": sorted(c for c, v in inhibition.items() if v >= HIT_PCT),
        "naive_inhibition": naive,
        "naive_hits": sorted(c for c, v in naive.items() if v >= HIT_PCT),
        "test_plate": {compound: label for label, compound, _v in tests},
    }


def _witness(files: dict[str, str], blank_plates: list[str]) -> dict:
    """Two plate gains that reproduce every reading on the uncontrolled plates
    exactly and imply different active calls.

    The identity is s = V(PL-01) * g * (f + (1-f)(1-a)) with f taken from the
    controlled plates. Solving it for a given g reproduces s to the digit for any
    admissible g, and g is admissible whenever every a it implies lies in [0,1].
    So the activities - and therefore the calls - are pinned only to a
    one-parameter family, and the log records that the gain for these two reads
    was chosen by the instrument and never written down.
    """
    state = _recompute(files)
    floor = state["floor_fraction"]
    order = [label for label in state["plate_order"]
             if label not in state["uncontrolled_plates"]]
    if floor is None or not order:
        return {}
    unit = state["vehicle_mean"][order[0]]

    readings: dict[str, dict[str, float]] = {}
    for row in _rows(files.get("screen_plates.csv", "")):
        if row.get("plate") in blank_plates and row.get("role") == "test":
            try:
                readings.setdefault(row["plate"], {})[row["compound_id"]] = \
                    float(row["signal"])
            except (KeyError, ValueError):
                continue

    theta = []
    for edge in ("low", "high"):
        gains: dict[str, float] = {}
        active: list[str] = []
        for label, wells in readings.items():
            if not wells:
                continue
            low = max(wells.values()) / unit
            high = min(wells.values()) / (unit * floor)
            gain = low * 1.002 if edge == "low" else high * 0.998
            if gain <= 0 or high <= low:
                continue
            gains[label] = round(gain, 6)
            for compound, value in wells.items():
                fraction = value / (unit * gain)
                a = 1.0 - (fraction - floor) / (1.0 - floor)
                if 100.0 * a >= HIT_PCT:
                    active.append(compound)
        theta.append({"plate_gain_relative_to_" + order[0]: gains,
                      "n_active": len(active),
                      "active_compounds": sorted(active)})
    return {
        "identity": ("signal = vehicle(" + order[0] + ") * plate_gain * "
                     "(floor_fraction + (1 - floor_fraction) * (1 - activity))"),
        "floor_fraction": floor,
        "theta_1": theta[0] if theta else {},
        "theta_2": theta[1] if len(theta) > 1 else {},
        "note": ("both plate gains reproduce every shipped reading on "
                 + ", ".join(blank_plates) + " exactly; those plates carry no "
                 "vehicle, reference or dye block and were read at an automatic "
                 "gain that was never logged, so the plate gain is unobserved "
                 "and the number of active compounds is not identifiable"),
    }


# ------------------------------------------------------------------ text checks

# Phrasings that mention reagent failure only to rule it out. Plain literal
# removal on purpose: a regex for this failed silently in situ while passing in
# isolation, and a scoring rule that cannot be checked by eye is a liability.
NEGATED = (
    "not degraded", "not degrade", "no degradation", "nothing degraded",
    "nothing has degraded", "did not degrade", "has not degraded",
    "have not degraded", "no evidence of degradation", "without degradation",
    "rather than degradation", "instead of degradation",
    "not reference degradation", "no reference degradation",
    "not a reference problem", "not the reference", "not reference",
    "not the reagent", "not a reagent problem", "no reagent degradation",
    "not lost potency", "has not lost potency", "no loss of potency",
    "without loss of potency", "not less potent", "no longer needed",
    "not compromised", "not unreliable", "not invalid", "not stale",
    "not expired", "not decayed", "did not decay", "no decay",
    "not collapsed", "did not collapse", "no collapse",
    "not incomplete", "no incomplete inhibition", "not partial",
    "not sub-saturating", "not subsaturating", "still saturating",
    "did not weaken", "not weaken", "not exhausted", "not exhaust",
    "did not shrink", "no shrink", "not shrink", "did not shrank",
    "not unstable", "not deteriorat", "no deteriorat",
)

REF_TOKENS = ("reference", "cru-ref", "standard inhibitor", "positive control",
              "control compound", "inhibitor stock")

# Reagent-failure vocabulary. Deliberately excludes words that describe a signal
# merely MOVING - "drift", "decline", "fall" - because in this family the
# reference signal moves in every condition and only its depth below vehicle
# separates them.
DEGRADE_TOKENS = ("degrad", "decay", "lost potency", "loses potency",
                  "losing potency", "loss of potency", "less potent",
                  "reduced potency", "no longer", "not fully inhibit",
                  "incomplete inhibition", "partial inhibition", "stale",
                  "expired", "compromis", "unreliable", "invalid", "collapse",
                  "weaken", "exhaust", "sub-saturating", "subsaturating",
                  "below saturating", "not saturating", "fell below",
                  "shrink", "shrank", "shrunk", "unstable", "deteriorat",
                  "aged", "ageing", "aging")

# High-precision assertions of reagent failure, used to catch the false alarm in
# C0 without depending on where the words sit.
STRONG_FAULT = (
    "reference degrad", "reference inhibitor degrad", "degradation of the reference",
    "degrading reference", "degraded reference", "reference has degraded",
    "reference is degrad", "reference lost", "reference has lost",
    "reference inhibitor lost", "lost potency", "loses potency",
    "losing potency", "loss of potency", "reference no longer",
    "no longer fully inhibit", "not fully inhibit", "incomplete inhibition",
    "reference compromis", "reference unreliable", "reference invalid",
    "reference is stale", "reference decay", "decay of the reference",
    "sub-saturating", "subsaturating", "window collapse",
    "window has collapsed", "assay window collapse", "reference wells no longer",
    "cru-ref degrad", "cru-ref lost", "standard inhibitor degrad",
    "standard inhibitor lost",
)

INSTRUMENT_TOKENS = ("detector", "gain", "pmt", "photomultiplier", "lamp",
                     "instrument", "optic", "sensitivity", "dye", "inert",
                     "reader", "every well", "all wells", "all three",
                     "common", "proportion", "same factor", "multiplicative",
                     "scale", "scaling", "in step", "track", "together",
                     "parallel", "ratio", "constant depth", "same depth")

MISSING_TOKENS = ("gain", "autogain", "auto-gain", "unlogged", "not logged",
                  "not recorded", "unrecorded", "no control", "without control",
                  "no vehicle", "no reference", "missing control",
                  "absent control", "no dye", "no standard", "identifiab",
                  "confound", "unknown scale", "arbitrary", "not normalis",
                  "not normaliz", "cannot be normalis", "cannot be normaliz",
                  "no scale", "unknown gain", "one-parameter", "family of")


def _strip_negated(text: str) -> str:
    lowered = str(text).lower()
    for phrase in NEGATED:
        lowered = lowered.replace(phrase, " ")
    return lowered


def _ref_fault(text: str, forward: int) -> bool:
    """Does the text put a reagent-failure word next to the reference reagent?

    Proximity rather than whole-text co-occurrence: in C0 a correct answer says
    "the reference held; the detector response degraded", and a co-occurrence
    rule would read that as the fault it is denying.
    """
    lowered = _strip_negated(text)
    for token in REF_TOKENS:
        start = 0
        while True:
            found = lowered.find(token, start)
            if found < 0:
                break
            window = lowered[max(0, found - 12): found + len(token) + forward]
            if any(word in window for word in DEGRADE_TOKENS):
                return True
            start = found + 1
    return False


def _strong_fault(text: str) -> bool:
    lowered = _strip_negated(text)
    return any(phrase in lowered for phrase in STRONG_FAULT)


# ------------------------------------------------------------------ verification

def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"control_diagnosis": False, "normalised_activity": False,
              "hit_list": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"},
                       "control_diagnosis")

    def field(name: str):
        """Case- and separator-insensitive lookup, normalising BOTH sides.

        Comparing a lowercased key against a mixed-case target silently matched
        nothing in an earlier family, so every numeric answer read as absent.
        """
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    state = _recompute(episode.files)
    detail["reference_depth_recomputed"] = state["reference_depth"]
    detail["floor_fraction_recomputed"] = state["floor_fraction"]
    detector = state["detector_decline"]
    detail["detector_decline_recomputed"] = detector
    detail["vehicle_tracks_dye_recomputed"] = state["vehicle_tracks_dye"]
    detail["reference_compromised_recomputed"] = state["reference_compromised"]
    detail["reference_compromised_expected"] = key["reference_degraded"]
    detail["uncontrolled_plates_recomputed"] = state["uncontrolled_plates"]

    diagnosis = str(field("control_behaviour") or "")
    activities = str(field("active_compounds") or "").strip()
    abstained_list = activities.lower() in ABSTAIN
    count_raw = field("n_active")
    abstained_count = str(count_raw or "").strip().lower() in ABSTAIN
    probe_raw = field("probe_inhibition_pct")
    abstained_probe = str(probe_raw or "").strip().lower() in ABSTAIN

    # Is the question answerable at all? Recomputed from the tables: the plates
    # the brief asks about must be on a common scale with the rest of the run.
    asked = key.get("ask_plates")
    blocked = sorted(set(asked or []) & set(state["uncontrolled_plates"])) \
        if asked else sorted(state["uncontrolled_plates"])
    detail["plates_asked"] = asked or state["plate_order"]
    detail["plates_not_scalable"] = blocked

    if blocked and (not asked or set(blocked) == set(asked)):
        # The only defensible outcome is a refusal that is ABOUT the missing
        # scale. Silence is not a refusal: an absent field fails here too.
        reason = _strip_negated(diagnosis + " " + str(submitted.get("reasoning", "")))
        names_reason = any(token in reason for token in MISSING_TOKENS)
        checks["hit_list"] = abstained_list and abstained_count
        checks["normalised_activity"] = abstained_probe
        checks["control_diagnosis"] = abstained_list and names_reason
        detail["expected"] = ("refusal: " + ", ".join(blocked) + " carry no "
                              "vehicle, reference or dye block and were read at "
                              "an unlogged gain, so no absolute call follows")
        detail["witness"] = key.get("witness")
        detail["stated_diagnosis"] = diagnosis[:240]
        order = ["control_diagnosis", "normalised_activity", "hit_list"]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    # ---- answerable: grade against the recomputed hit list.
    expected_hits = set(state["hits"])
    given = {token.strip().upper() for token in
             activities.replace(";", ",").replace("|", ",").split(",")
             if token.strip()}
    known = {compound.upper(): compound for compound in state["inhibition"]}
    resolved = {known[token] for token in given if token in known}
    detail["hits_recomputed"] = sorted(expected_hits)
    detail["hits_recomputed_count"] = len(expected_hits)
    detail["hits_given"] = sorted(resolved)
    detail["hits_unrecognised"] = sorted(given - set(known))
    detail["hits_naive_two_point"] = state["naive_hits"]
    detail["hits_naive_differs_by"] = sorted(
        set(state["naive_hits"]) ^ expected_hits)

    try:
        given_count = int(str(count_raw).strip())
    except (TypeError, ValueError):
        given_count = None
    detail["n_active_given"] = given_count

    checks["hit_list"] = (not abstained_list and bool(resolved)
                          and resolved == expected_hits
                          and not (given - set(known))
                          and given_count == len(expected_hits))

    # The one number the brief asks for, recomputed. Route B's value for this
    # compound is inflated well beyond the tolerance in H1, so the number alone
    # says which analysis was run.
    probe = key["probe"]
    expected_probe = state["inhibition"].get(probe)
    detail["probe"] = probe
    detail["probe_inhibition_recomputed"] = (None if expected_probe is None
                                             else round(expected_probe, 2))
    naive_probe = state["naive_inhibition"].get(probe)
    detail["probe_inhibition_naive_two_point"] = (None if naive_probe is None
                                                  else round(naive_probe, 2))
    try:
        given_probe = float(str(probe_raw).strip().rstrip("%"))
    except (TypeError, ValueError):
        given_probe = None
    detail["probe_inhibition_given"] = given_probe
    checks["normalised_activity"] = (expected_probe is not None
                                     and given_probe is not None
                                     and abs(given_probe - expected_probe) <= 5.0)

    # The diagnosis is graded against the RECOMPUTED state of the reference, so
    # the family punishes the false alarm in C0 with the same machinery that
    # requires the finding in H1.
    if state["reference_compromised"]:
        checks["control_diagnosis"] = (_strong_fault(diagnosis)
                                       or _ref_fault(diagnosis, forward=75))
        detail["expected_diagnosis"] = ("the reference reagent stopped reporting "
                                        "the fully-inhibited background late in "
                                        "the run")
    else:
        instrument = any(token in diagnosis.lower() for token in INSTRUMENT_TOKENS)
        checks["control_diagnosis"] = (instrument and not _strong_fault(diagnosis)
                                       and not _ref_fault(diagnosis, forward=40))
        detail["expected_diagnosis"] = ("a common-mode decline in detector "
                                        "response; the reference reagent held")
        detail["names_instrument"] = instrument
    detail["stated_diagnosis"] = diagnosis[:240]

    order = ["control_diagnosis", "normalised_activity", "hit_list"]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


# -------------------------------------------------------------------- reference

def reference_submission(episode: Episode) -> dict:
    """The submission a competent analyst would make, derived by RUNNING the
    recomputation the candidate has to run - so B8 proves the task is solvable
    from the workspace rather than that the key is self-consistent."""
    key = episode.key
    state = _recompute(episode.files)

    asked = key.get("ask_plates")
    blocked = sorted(set(asked or []) & set(state["uncontrolled_plates"])) \
        if asked else sorted(state["uncontrolled_plates"])
    if blocked and (not asked or set(blocked) == set(asked)):
        witness = key.get("witness") or {}
        low = (witness.get("theta_1") or {}).get("n_active")
        high = (witness.get("theta_2") or {}).get("n_active")
        return {
            "active_compounds": "cannot_determine",
            "n_active": "cannot_determine",
            "probe_inhibition_pct": "cannot_determine",
            "control_behaviour": (
                ", ".join(blocked) + " carry no vehicle wells, no reference "
                "wells and no dye block, and the log records that the reader "
                "chose its own photomultiplier setting for those two reads and "
                "never wrote it down, so the plate gain there is unobserved and "
                "is not bracketed by the neighbouring plates. Every reading on "
                "those plates is the product of that unknown gain and the "
                "activity left in the well, so the activity is pinned only to a "
                "one-parameter family: two admissible gains reproduce every "
                f"shipped reading exactly and imply {low} active compounds and "
                f"{high} active compounds respectively. On the controlled plates "
                "the vehicle wells fall in step with the inert dye block, so the "
                "decline there is detector response, but that scale cannot be "
                "carried onto an unlogged automatic-gain read."),
            "conf_active_compounds": 0.9, "conf_n_active": 0.9,
            "conf_probe_inhibition_pct": 0.9, "conf_control_behaviour": 0.85,
        }

    hits = state["hits"]
    probe = key["probe"]
    if state["reference_compromised"]:
        behaviour = (
            "Two things move. The inert dye block and the vehicle wells fall "
            f"together by about {int(100 * (state['detector_decline'] or 0))}% "
            "from the first plate to the last and stay in step with each other, "
            "so that part is detector response and each plate's own vehicle mean "
            "removes it. The reference wells fall too, but less: their depth "
            f"below vehicle sits at {state['floor_fraction']} for the early "
            f"plates and rises to {state['late_depth']} by the end, which a "
            "change in detector response cannot do because it scales every well "
            "on the plate alike. The reference inhibitor has lost potency during "
            "the run, so on the late plates its wells no longer report the "
            "completely-inhibited background and the apparent assay window there "
            "is too small. The background used for every plate was therefore "
            "taken from the plates where the reference still held, as a fraction "
            "of that plate's own vehicle mean.")
    else:
        behaviour = (
            "One thing moves. The inert dye block, the vehicle wells and the "
            "reference wells all fall together from the first plate to the last "
            f"by about {int(100 * (state['detector_decline'] or 0))}%, and the "
            "vehicle wells stay in step with the dye to within "
            f"{round(100 * (state['vehicle_tracks_dye'] or 0), 1)}%, so the "
            "decline is detector response rather than anything in the chemistry. "
            "Because it scales every well on a plate by one common factor, the "
            "reference wells keep the same depth below vehicle on every plate - "
            f"{state['floor_fraction']} at the start and {state['late_depth']} at "
            "the end - so the reference reagent held at its specified "
            "concentration throughout and each plate's own controls set its "
            "scale. Raw readings from early and late plates are not comparable, "
            "but normalised ones are.")
    return {
        "active_compounds": ",".join(hits),
        "n_active": len(hits),
        "probe_inhibition_pct": round(state["inhibition"].get(probe, 0.0), 2),
        "control_behaviour": behaviour,
        "conf_active_compounds": 0.8, "conf_n_active": 0.85,
        "conf_probe_inhibition_pct": 0.85, "conf_control_behaviour": 0.9,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
