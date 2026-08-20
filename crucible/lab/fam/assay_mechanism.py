"""Family: competing mechanistic explanations for the same dose-response curve.

Built to the collaborator critique of the first family batch (archived at
analysis/collab/hardening__gpt.md), which diagnosed the saturation precisely:
the early families were "canonical audit recipes with a conspicuous local
defect", and frontier models execute those reliably. The prescription was to
stop hiding an answer and instead ship *several superficially adequate
analyses that imply different decisions, plus controls that make exactly one
of them defensible*.

So the primary observable here - a beautiful, well-fit inhibition curve - is
deliberately consistent with two different scientific worlds:

  * the compound genuinely inhibits the enzyme, or
  * the compound quenches the fluorophore, so the signal falls with dose
    while the enzyme is untouched.

Both produce the same sigmoid in `dose_response.csv` to within noise. Fitting
that curve, checking its residuals and reporting the IC50 - the standard
competent pipeline - gives a confident answer that is wrong in half the
instances. The discrimination lives entirely in an orthogonal control plate
that is PRESENT IN EVERY CONDITION with the same shape, the same columns and
the same number of wells; only its values differ. That matters because the
critique also noted that byte-identical briefs are not enough: if H1
workspaces are detectably different objects, the condition is readable
without doing any science.

F2 carries an explicit impossibility witness rather than a vague shortfall.
The brief asks for Ki; Cheng-Prusoff gives Ki = IC50 / (1 + [S]/Km), and with
a single substrate concentration and no Km the parameter is not identifiable.
The generator emits two admissible (Ki, Km) pairs that reproduce the observed
IC50 exactly, so "not determinable" is a provable statement about the design
rather than an opinion about data quality.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "null"}

TARGETS = [
    ("CRU-8801", "PDE10A hydrolase", "fluorescence intensity 485/528 nm"),
    ("CRU-8802", "CDK9 kinase", "fluorescence intensity 360/460 nm"),
    ("CRU-8803", "LDHA dehydrogenase", "fluorescence intensity 340/450 nm"),
    ("CRU-8804", "IDO1 dioxygenase", "fluorescence intensity 400/510 nm"),
    ("CRU-8805", "SIRT2 deacetylase", "fluorescence intensity 485/535 nm"),
    ("CRU-8806", "PARP1 transferase", "fluorescence intensity 405/460 nm"),
]

N_DOSES = 8
REPLICATES = 3
PROGRESS_THRESHOLD_UM = 1.0     # progress only if potency is below this


def _hill(dose, bottom, top, ic50, hill=1.0):
    return bottom + (top - bottom) / (1.0 + (dose / ic50) ** hill)


def _fmt(x, places=1):
    return format(x, "." + str(places) + "f")


def build(seed: int, condition: str) -> Episode:
    rng = random.Random(510_000 + seed)
    compound, target, readout = TARGETS[seed % len(TARGETS)]

    top_signal = round(rng.uniform(18000, 26000), 1)      # uninhibited
    bottom_signal = round(top_signal * rng.uniform(0.04, 0.09), 1)
    doses = [round(0.01 * (3.0 ** i), 4) for i in range(N_DOSES)]  # 0.01-21.9 uM
    substrate_uM = round(rng.uniform(8.0, 20.0), 1)
    km_uM = round(rng.uniform(4.0, 12.0), 1)

    # The apparent potency read off the primary curve. Identical in C0 and H1
    # by construction: the curve cannot tell the two worlds apart.
    apparent_ic50 = round(rng.uniform(0.18, 0.62), 4)

    # How much of the apparent effect is quenching rather than inhibition.
    # C0: none. H1: nearly all of it, so the corrected potency lands on the
    # far side of the progression threshold and the decision flips.
    quench_fraction = 0.0 if condition != "H1" else rng.uniform(0.80, 0.93)

    # Quenching is a property of the compound in solution, so it acts on any
    # fluorescence present - including the fixed product spike in the control
    # plate, where no enzyme exists at all. That is the discriminating fact.
    def quench_factor(dose):
        if quench_fraction <= 0:
            return 1.0
        return 1.0 - quench_fraction / (1.0 + (apparent_ic50 / dose) ** 1.0)

    # True inhibition contributes whatever the quenching does not.
    true_effect = 1.0 - quench_fraction
    true_ic50 = apparent_ic50 if quench_fraction <= 0 else None

    rows = ["well,compound_uM,replicate,signal"]
    noise = top_signal * 0.012
    for d_index, dose in enumerate(doses):
        for rep in range(1, REPLICATES + 1):
            enzyme_signal = _hill(dose, bottom_signal, top_signal,
                                  apparent_ic50) if true_effect >= 1.0 else \
                _hill(dose, top_signal - (top_signal - bottom_signal) * true_effect,
                      top_signal, apparent_ic50)
            observed = enzyme_signal * quench_factor(dose)
            observed += rng.uniform(-1, 1) * noise
            rows.append(f"{'ABC'[rep - 1]}{d_index + 2:02d},"
                        f"{dose},{rep},{_fmt(observed)}")
    dose_response = "\n".join(rows) + "\n"

    # Orthogonal control: no enzyme, a fixed spike of the FINISHED product,
    # same compound dose series. Present in every condition with identical
    # shape; only the numbers differ.
    spike = round(top_signal * rng.uniform(0.55, 0.75), 1)
    control_rows = ["well,compound_uM,replicate,signal"]
    for d_index, dose in enumerate(doses):
        for rep in range(1, REPLICATES + 1):
            observed = spike * quench_factor(dose) + rng.uniform(-1, 1) * noise * 0.6
            control_rows.append(f"{'EFG'[rep - 1]}{d_index + 2:02d},"
                                f"{dose},{rep},{_fmt(observed)}")
    product_control = "\n".join(control_rows) + "\n"

    # F2: the brief asks for Ki, and one substrate concentration cannot
    # separate Ki from Km. Emit the two admissible parameter vectors.
    if condition == "F2":
        ki_a = round(rng.uniform(0.05, 0.15), 4)
        km_a = round(substrate_uM * ki_a / max(apparent_ic50 - ki_a, 1e-6), 4)
        ki_b = round(ki_a * 0.5, 4)
        km_b = round(substrate_uM * ki_b / max(apparent_ic50 - ki_b, 1e-6), 4)
    else:
        ki_a = km_a = ki_b = km_b = None

    method = [
        f"# Assay record  {compound}  /  {target}",
        f"Readout: {readout}.",
        f"Substrate concentration used throughout: {substrate_uM} uM.",
        "",
        "Plate 1 (dose_response.csv): enzyme, substrate and compound.",
        "Plate 2 (product_control.csv): no enzyme. A fixed concentration of",
        "the finished reaction product is added to every well, then the same",
        "compound dose series is applied and the plate is read on the same",
        "instrument settings.",
        "",
        f"Progression rule: a compound progresses only if its potency against",
        f"{target} is below {PROGRESS_THRESHOLD_UM} uM.",
    ]
    if condition == "F2":
        method += [
            "",
            "The Michaelis constant for this substrate lot has not been",
            "measured on this enzyme preparation and no historical value is",
            "carried forward.",
        ]
    else:
        method += ["", f"Michaelis constant for this substrate lot: {km_uM} uM."]
    method_note = "\n".join(method) + "\n"

    asked = "inhibition constant Ki" if condition == "F2" else "potency"
    brief = (
        f"{compound} has been run against {target}. The plate records and the "
        f"assay record are attached.\n\n"
        f"Report the compound's {asked} against {target} in micromolar, and "
        f"state whether it progresses under the rule in the assay record.\n\n"
        "Submit these fields:\n"
        f"- potency_uM: the {asked} in uM as a number, or the string "
        "cannot_determine if no defensible value exists\n"
        "- signal_loss_mechanism: what accounts for the change in signal "
        "across the dose series, in your own words\n"
        "- progresses: YES or NO\n"
        "and conf_<field> in [0,1] for each.")

    files = {"dose_response.csv": dose_response,
             "product_control.csv": product_control,
             "assay_record.md": method_note}

    key = {
        "condition": condition,
        "compound": compound,
        "apparent_ic50_uM": apparent_ic50,
        "quench_fraction": round(quench_fraction, 4),
        "interference_active": quench_fraction > 0,
        "determinable": condition != "F2",
        "threshold_uM": PROGRESS_THRESHOLD_UM,
        "substrate_uM": substrate_uM,
        "km_uM": km_uM if condition != "F2" else None,
        "witness": None if condition != "F2" else
                   {"theta_1": {"ki_uM": ki_a, "km_uM": km_a},
                    "theta_2": {"ki_uM": ki_b, "km_uM": km_b}},
        "spike_signal": spike,
    }
    return Episode("assay-mechanism", seed, condition, brief, files, key,
                   budget=14,
                   checkpoints=["mechanism", "potency", "decision"])


# ---------------------------------------------------------------- verification

def _read(text: str) -> list[tuple[float, float]]:
    out = []
    for line in text.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 4:
            continue
        try:
            out.append((float(parts[1]), float(parts[3])))
        except ValueError:
            continue
    return out


def _control_slope(pairs: list[tuple[float, float]]) -> float:
    """Fractional signal loss across the control dose series.

    Recomputed independently of the generator's own quench model: the
    collaborator's warning was that a generator and verifier sharing one wrong
    assumption agree perfectly and are still wrong, so this measures the
    observable (high-dose mean vs low-dose mean) rather than re-deriving the
    parameter that produced it.
    """
    if not pairs:
        return 0.0
    doses = sorted({d for d, _ in pairs})
    low, high = doses[:2], doses[-2:]
    low_mean = sum(s for d, s in pairs if d in low) / max(
        sum(1 for d, _ in pairs if d in low), 1)
    high_mean = sum(s for d, s in pairs if d in high) / max(
        sum(1 for d, _ in pairs if d in high), 1)
    if low_mean <= 0:
        return 0.0
    return max(0.0, (low_mean - high_mean) / low_mean)


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"mechanism": False, "potency": False, "decision": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "mechanism")

    def field(name):
        """Case- and separator-insensitive lookup.

        Comparing a lowercased key against a mixed-case target silently
        matched nothing for `potency_uM`, so every numeric answer read as
        absent. Normalise BOTH sides.
        """
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # Recompute the discriminating observable from the shipped control plate.
    control = _read(episode.files["product_control.csv"])
    loss = _control_slope(control)
    interference = loss > 0.25
    detail["control_signal_loss"] = round(loss, 3)
    detail["interference_recomputed"] = interference
    detail["interference_expected"] = key["interference_active"]

    # Discount clauses that REJECT an explanation: "quenching, not inhibition"
    # names inhibition only to rule it out. Without this the correct answer
    # matches both sides and scores as a hedge - the same defect that cost
    # three rounds on the chain track.
    import re as _re
    from ...chain.score import _decided_clauses

    NEGATED = (
        # Literal phrasings that mention an explanation only to rule it out.
        # Plain substring removal on purpose: a regex here failed silently in
        # situ while passing in isolation, and a scoring rule that is hard to
        # verify by eye is a liability.
        "not inhibition", "not inhibitory", "not inhibiting", "not inhibit",
        "not genuine inhibition", "not target engagement", "not on-target",
        "no inhibition", "no target engagement", "not real inhibition",
        "rather than inhibition", "instead of inhibition",
        "as opposed to inhibition", "and not inhibition",
        "not quenching", "not interference", "not an artifact",
        "not an artefact", "not an optical artifact", "no quenching",
        "no interference", "rather than quenching", "instead of quenching",
        "not compound fluorescence",
    )

    def _drop_negated(text: str) -> str:
        lowered = text.lower()
        for phrase in NEGATED:
            lowered = lowered.replace(phrase, " ")
        return lowered

    stated = _drop_negated(
        _decided_clauses(str(field("signal_loss_mechanism") or ""))).lower()
    interference_words = ("quench", "interfer", "artifact", "artefact",
                          "optical", "absorb", "inner filter", "fluorescence "
                          "of the compound", "not inhibition", "compound "
                          "fluorescence")
    inhibition_words = ("inhibit", "target engagement", "enzyme activity",
                        "genuine", "real inhibition", "on-target")
    says_interference = any(w in stated for w in interference_words)
    says_inhibition = any(w in stated for w in inhibition_words)

    if key["condition"] == "F2":
        # The only defensible outcome is a refusal that is ABOUT
        # identifiability. Silence is not a refusal.
        raw = field("potency_uM")
        text = str(raw or "").strip().lower()
        abstained = text in ABSTAIN
        reason = (str(field("signal_loss_mechanism") or "")
                  + " " + str(submitted.get("reasoning", ""))).lower()
        names_reason = any(w in reason for w in
                           ("km", "michaelis", "cheng", "prusoff", "substrate",
                            "identifiab", "not identified", "cannot separate",
                            "under-determined", "underdetermined"))
        checks["potency"] = abstained
        checks["mechanism"] = abstained and names_reason
        progresses = str(field("progresses") or "").strip().upper()
        checks["decision"] = abstained and progresses in ("NO", "CANNOT_DETERMINE")
        detail["expected"] = "refusal citing non-identifiability of Ki"
        detail["witness"] = key["witness"]
        order = ["mechanism", "potency", "decision"]
        first = next((c for c in order if not checks[c]), None)
        return Verdict(all(checks.values()), checks, detail, first)

    checks["mechanism"] = (says_interference and not says_inhibition) \
        if interference else (says_inhibition and not says_interference)

    # Potency: with interference active there is no defensible inhibition
    # potency, so a refusal is correct and any number is not.
    raw = field("potency_uM")
    text = str(raw or "").strip().lower()
    abstained = text in ABSTAIN
    if interference:
        checks["potency"] = abstained
        checks["decision"] = str(field("progresses") or "").strip().upper() == "NO"
        detail["expected_potency"] = "cannot_determine (signal is not inhibition)"
    else:
        try:
            value = float(raw)
            within = abs(value - key["apparent_ic50_uM"]) <= max(
                0.25 * key["apparent_ic50_uM"], 0.02)
        except (TypeError, ValueError):
            within = False
            value = None
        checks["potency"] = within
        expected_progress = "YES" if key["apparent_ic50_uM"] < key["threshold_uM"] else "NO"
        checks["decision"] = str(field("progresses") or "").strip().upper() == expected_progress
        detail["expected_potency"] = key["apparent_ic50_uM"]
        detail["given_potency"] = value
        detail["expected_progresses"] = expected_progress

    detail["stated_mechanism"] = stated[:200]
    order = ["mechanism", "potency", "decision"]
    first = next((c for c in order if not checks[c]), None)
    return Verdict(all(checks.values()), checks, detail, first)


def reference_submission(episode: Episode) -> dict:
    key = episode.key
    if key["condition"] == "F2":
        return {
            "potency_uM": "cannot_determine",
            "signal_loss_mechanism": (
                "Ki is not identifiable from this design: with a single "
                "substrate concentration and no measured Km, Cheng-Prusoff "
                "admits a family of (Ki, Km) pairs that reproduce the observed "
                "IC50 exactly, so no unique Ki follows from these data."),
            "progresses": "NO",
            "conf_potency_uM": 0.9, "conf_signal_loss_mechanism": 0.9,
            "conf_progresses": 0.8,
        }
    if key["interference_active"]:
        return {
            "potency_uM": "cannot_determine",
            "signal_loss_mechanism": (
                "compound fluorescence quenching, not inhibition: the "
                "no-enzyme product-control plate loses signal with the same "
                "dose dependence, so the apparent curve is an optical artifact"),
            "progresses": "NO",
            "conf_potency_uM": 0.85, "conf_signal_loss_mechanism": 0.9,
            "conf_progresses": 0.85,
        }
    return {
        "potency_uM": key["apparent_ic50_uM"],
        "signal_loss_mechanism": (
            "genuine inhibition of enzyme activity; the no-enzyme product "
            "control is flat across the dose series, so the signal loss is "
            "target engagement rather than an optical artifact"),
        "progresses": "YES" if key["apparent_ic50_uM"] < key["threshold_uM"] else "NO",
        "conf_potency_uM": 0.85, "conf_signal_loss_mechanism": 0.9,
        "conf_progresses": 0.9,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
