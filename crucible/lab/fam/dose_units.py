"""Family: reconciling one exposure figure across incompatible units and bases.

The literature reads (`analysis/literature2/deep/`) converge on one shape of
hard tool-use task: the tools succeed and the science fails at the *handoff*.
ChemCrow's difficulty came from "unit/representation handoffs" where one tool's
output is another's input; Coscientist's every consequential failure was a
successful call whose result was mis-carried; the OSWorld and Coscientist reads
both name a silent units mismatch as the planted defect that lands in the
5-40% band precisely because it never raises a traceback.

So this family ships a small pharmacokinetic package in which the same physical
quantity is recorded four times on four different bases:

    bioanalysis.csv        ug/L, WHOLE BLOOD, assigned against calibrators
                           weighed out as the salt
    compound_registry.txt  a free-base mass fraction and a potency in uM
    dpk_protocol.txt       a blood/plasma ratio, plus the haematocrit and the
                           red-cell/plasma partition data that determine it
    formulation_prep.txt   a gravimetric prep whose mass and volume pin the
                           free-base fraction independently of the structure

and asks for ONE number: the free base, in plasma, in nM, at a stated
timepoint. Every conversion on the path is recoverable from primitives, and
every one of them is also *recorded* somewhere as a finished factor - which is
what makes the three conditions possible without touching the brief:

    C0  the recorded factors agree with the primitives; asserting a problem is
        a false alarm
    H1  one recorded factor is stale: it matches neither the structure nor the
        masses, and the answer computed from the primitives differs from the
        answer computed from the record by >=8%
    F2  the counterion is not recorded anywhere, so the salt basis of the
        bioanalytical numbers cannot be resolved and no free-base molar
        concentration exists to report

Nothing here is hardcoded: the generator draws primitives, and both the key and
the verdict come from the same `_recompute` pass over the shipped bytes, so a
generator bug surfaces as a disagreement in the self-test rather than as a
wrong key in the campaign.
"""
from __future__ import annotations

import random
import re
import zlib
from pathlib import Path

from ..families import Episode, Verdict

# Basic amines: every one of them is dispensed as a salt in practice, so a
# salt-basis bioanalytical record is the ordinary case rather than a contrivance.
COMPOUNDS = [
    "CCN(CC)CCOC(=O)c1ccc(N)cc1",
    "CCN(CC)CC(=O)Nc1c(C)cccc1C",
    "CC(C)NCC(O)COc1cccc2ccccc12",
    "COCCc1ccc(OCC(O)CNC(C)C)cc1",
    "CN(C)CCOC(c1ccccc1)c1ccccc1",
    "CC(C)NCC(O)COc1ccc(CC(N)=O)cc1",
    "COc1ccc(C(CN(C)C)C2(O)CCCCC2)cc1",
    "CC(NC(C)(C)C)C(=O)c1cccc(Cl)c1",
]

# Counterions are given as the neutral acid, which is exactly the mass that
# enters the salt formula weight. All mono-protic, so a 1:2 base:acid record is
# a real salt form rather than a chemistry error; the rejection loop below
# throws out any pairing whose free-base fraction leaves the realistic band.
COUNTERIONS = [
    ("hydrochloride", "Cl"),
    ("hydrobromide", "Br"),
    ("methanesulfonate", "CS(=O)(=O)O"),
    ("benzenesulfonate", "OS(=O)(=O)c1ccccc1"),
    ("4-methylbenzenesulfonate", "Cc1ccc(cc1)S(=O)(=O)O"),
]

TIMEPOINTS = [0.5, 1.0, 2.0, 4.0, 8.0, 24.0]
SHAPE = [0.55, 1.00, 0.78, 0.47, 0.21, 0.032]
REQUESTABLE = [1.0, 2.0, 4.0, 8.0]

# Separation floors. Every wrong path enumerated in the module docstring must
# land further from the truth than the verifier's tolerance, or the task would
# be scored by rounding luck rather than by reasoning.
TOL_VALUE = 0.025          # relative, on the reconciled concentration
TOL_COVERAGE = 0.03        # relative, on the potency multiple
TOL_HONEST = 0.05          # the two submitted numbers must agree with each other
TOL_AGREE = 0.01           # recorded vs recomputed: beyond this the record is stale

FILE_STEMS = ("compound_registry", "bioanalysis_notes", "bioanalysis",
              "dpk_protocol", "formulation_prep")
NONE_TOKENS = {"none", "no", "na", "n_a", "nil", "null", "nothing",
               "none_all_records_agree", "consistent"}
ABSTAIN_TOKENS = {"cannot_determine", "cannot determine", "undetermined",
                  "not_determinable", "unknown", "none", "n_a", "na"}


# --------------------------------------------------------------------------
# primitives

def _mw(smiles: str) -> float:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"unparseable SMILES {smiles!r}")
    return Descriptors.MolWt(mol)


def _fraction(mw_free: float, mw_counter: float, n: int) -> float:
    return mw_free / (mw_free + n * mw_counter)


def _primitives(seed: int) -> dict:
    """Draw one instance's physical primitives, rejecting degenerate draws.

    The rejection loop is the difficulty guarantee: it enforces that skipping a
    correction, inverting one, or trusting the stale record all land outside
    the verifier's tolerance, for BOTH the sound and the defective variant of
    this seed.
    """
    rng = random.Random(41_000 + seed)
    smiles = COMPOUNDS[seed % len(COMPOUNDS)]
    mw_free = _mw(smiles)

    for _ in range(400):
        cname, csmiles = COUNTERIONS[rng.randrange(len(COUNTERIONS))]
        mw_counter = _mw(csmiles)
        n_sound = rng.choice([1, 2])
        n_alt = 3 - n_sound
        f_sound = _fraction(mw_free, mw_counter, n_sound)
        f_alt = _fraction(mw_free, mw_counter, n_alt)

        haematocrit = round(rng.uniform(0.40, 0.48), 3)
        rb_sound = round(rng.choice([rng.uniform(0.68, 0.85),
                                     rng.uniform(1.18, 1.75)]), 3)
        rb_alt = round(rng.choice([rng.uniform(0.68, 0.85),
                                   rng.uniform(1.18, 1.75)]), 3)
        variant = "registry" if seed % 2 == 0 else "protocol"

        # Operative (fraction, ratio) pairs for the sound and defective files.
        pairs = {"C0": (f_sound, rb_sound)}
        if variant == "registry":
            pairs["H1"] = (f_alt, rb_sound)
        else:
            pairs["H1"] = (f_sound, rb_alt)

        ok = True
        for f, rb in pairs.values():
            kbc = 1.0 + (rb - 1.0) / haematocrit
            ok &= 0.50 <= f <= 0.92                 # skipping the salt basis is >=8% wrong
            ok &= abs(rb - 1.0) >= 0.15             # skipping the matrix basis is >=15% wrong
            ok &= abs(f / rb - 1.0) >= 0.10         # the two do not cancel each other
            ok &= 0.20 <= kbc <= 4.0                # the partition data stay measurable
        # The stale record must move the answer, and C0 and H1 must not agree.
        stale_ratio = (f_sound / f_alt) if variant == "registry" else (rb_alt / rb_sound)
        ok &= abs(stale_ratio - 1.0) >= 0.08
        if not ok:
            continue

        c_zero = round(rng.uniform(900.0, 3600.0), 1)
        jitter = [round(s * rng.uniform(0.94, 1.06), 4) for s in SHAPE]
        profile = [round(c_zero * j, 1) for j in jitter]
        ratios = [max(a, b) / min(a, b) for a, b in zip(profile, profile[1:])]
        if min(ratios) < 1.20:                      # the wrong timepoint is clearly wrong
            continue

        return {
            "smiles": smiles, "mw_free": mw_free,
            "counterion_name": cname, "counterion_smiles": csmiles,
            "mw_counter": mw_counter,
            "n_sound": n_sound, "n_alt": n_alt,
            "f_sound": f_sound, "f_alt": f_alt,
            "haematocrit": haematocrit,
            "rb_sound": rb_sound, "rb_alt": rb_alt,
            "variant": variant,
            "profile": profile,
            "requested_h": REQUESTABLE[seed % len(REQUESTABLE)],
            "ic50_uM": round(rng.uniform(0.008, 0.9), 4),
            "study_id": f"PKX-{3000 + 7 * seed + rng.randrange(90)}",
            "compound_id": f"CID-{4000 + 13 * seed + rng.randrange(900)}",
            "lot": f"L-{2100 + 11 * seed}",
            "plasma_low": round(rng.uniform(150.0, 320.0), 1),
            "level_gap": round(rng.uniform(4.2, 6.4), 3),
            "vehicle_mL": round(rng.choice([10.0, 20.0, 25.0, 50.0]), 1),
            "salt_mg": round(rng.uniform(28.0, 96.0), 1),
        }
    raise RuntimeError(f"dose-units: no admissible draw for seed {seed}")


# --------------------------------------------------------------------------
# files

def _registry_text(p: dict, condition: str) -> str:
    head = ("Compound registry entry\n"
            f"compound_id: {p['compound_id']}\n"
            f"free_base_smiles: {p['smiles']}\n")
    if condition == "F2":
        body = ("salt_form: acid addition salt; counterion identity and\n"
                "  stoichiometry are not on file (supplier CoA outstanding)\n")
    else:
        n = p["n_alt"] if (condition == "H1" and p["variant"] == "registry") else p["n_sound"]
        body = (f"salt_form: {p['counterion_name']} salt\n"
                f"counterion_smiles: {p['counterion_smiles']}\n"
                f"stoichiometry: 1 base : {n} counterion\n"
                f"free_base_fraction: {p['f_sound']:.4f}\n")
    tail = (f"target_ic50: {p['ic50_uM']:.4f} uM (free base, biochemical assay)\n"
            f"solid_lot: {p['lot']}\n"
            "registry maintained by Analytical Sciences; fields are entered at\n"
            "first registration and revised on request.\n")
    return head + body + tail


def _protocol_text(p: dict, condition: str) -> str:
    rb_true = p["rb_alt"] if (condition == "H1" and p["variant"] == "protocol") else p["rb_sound"]
    kbc = 1.0 + (rb_true - 1.0) / p["haematocrit"]
    cp_a = p["plasma_low"]
    cp_b = round(cp_a * p["level_gap"], 1)
    rows = "\n".join(f"{lab},{cp:.1f},{cp * kbc:.1f}"
                     for lab, cp in (("A", cp_a), ("B", cp_b)))
    return (f"Study {p['study_id']} - distribution section\n"
            "species: rat (male, n=3 per timepoint)\n"
            "matrix collected and assayed in the PK phase: whole blood (K2EDTA)\n"
            f"haematocrit measured in this cohort: {p['haematocrit']:.3f}\n"
            f"blood_to_plasma_ratio: {p['rb_sound']:.3f}\n"
            "\n"
            "In vitro partitioning: blank blood from the same cohort spiked at two\n"
            "levels, incubated 60 min at 37 C, then plasma and packed red cells\n"
            "separated and assayed on the same run.\n"
            "level,plasma_ug_per_L,red_cells_ug_per_L\n"
            f"{rows}\n")


def _prep_text(p: dict, condition: str) -> str:
    strength_free = p["f_sound"] * p["salt_mg"] / p["vehicle_mL"]
    if condition == "H1" and p["variant"] == "registry":
        strength_free = p["f_alt"] * p["salt_mg"] / p["vehicle_mL"]
    head = (f"Dose formulation record, study {p['study_id']}\n"
            f"solid lot: {p['lot']}\n"
            f"mass weighed: {p['salt_mg']:.1f} mg of the as-received solid\n"
            f"vehicle: 0.5% methylcellulose, made to {p['vehicle_mL']:.1f} mL\n")
    if condition == "F2":
        nominal = p["salt_mg"] / p["vehicle_mL"]
        body = f"nominal strength: {nominal:.3f} mg/mL of the as-received solid\n"
    else:
        body = ("free-base strength of the dosing solution: "
                f"{strength_free:.3f} mg/mL\n")
    return head + body + ("dose administered: 5 mL/kg by oral gavage\n"
                          "prepared and released by Formulation Support\n")


def _bioanalysis_text(p: dict) -> str:
    rows = "\n".join(
        f"S{i + 1:02d},{t:g},whole blood,{c:.1f}"
        for i, (t, c) in enumerate(zip(TIMEPOINTS, p["profile"])))
    return "sample_id,timepoint_h,matrix,conc_ug_per_L\n" + rows + "\n"


def _notes_text(p: dict) -> str:
    # Deterministic across processes: str.__hash__ is salted per interpreter,
    # and a run identifier that moved between build and re-scoring would break
    # replay for no gain.
    tag = 1100 + (zlib.crc32(p["study_id"].encode()) % 800)
    return (f"Bioanalytical run BA-{tag}\n"
            "method: protein precipitation, LC-MS/MS, positive ESI\n"
            f"calibrators and QCs: prepared gravimetrically from solid lot {p['lot']}\n"
            "  and assigned on the as-weighed basis of that solid\n"
            "reported unit: ug/L\n"
            "LLOQ: 2.0 ug/L; incurred sample reanalysis passed\n")


# --------------------------------------------------------------------------
# the recomputation both the key and the verdict come from

def _grab(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return match.group(1) if match else None


def _recompute(files: dict[str, str], brief: str) -> dict:
    """Derive the reconciled figure from the shipped bytes alone.

    This never sees the key. `build` fills the key from it and `verify` grades
    from it, so the two cannot drift apart, and a parsing or chemistry mistake
    shows up as a self-test failure instead of as a wrong answer in a campaign.
    """
    out: dict = {"determinable": False, "unreliable": [], "incomplete": []}
    registry = files.get("compound_registry.txt", "")
    protocol = files.get("dpk_protocol.txt", "")
    prep = files.get("formulation_prep.txt", "")
    assay = files.get("bioanalysis.csv", "")

    smiles = _grab(registry, r"free_base_smiles:\s*(\S+)")
    if not smiles:
        out["error"] = "no free-base structure on file"
        return out
    mw_free = _mw(smiles)
    out["mw_free"] = round(mw_free, 3)

    # --- basis 1: what fraction of the dosed/measured mass is free base?
    counter = _grab(registry, r"counterion_smiles:\s*(\S+)")
    stoich = _grab(registry, r"stoichiometry:\s*1\s*base\s*:\s*(\d+)")
    f_structural = None
    if counter and stoich:
        f_structural = _fraction(mw_free, _mw(counter), int(stoich))

    mass = _grab(prep, r"mass weighed:\s*([0-9.]+)\s*mg")
    volume = _grab(prep, r"made to\s*([0-9.]+)\s*mL")
    strength = _grab(prep, r"free-base strength of the dosing solution:\s*([0-9.]+)")
    f_gravimetric = None
    if mass and volume and strength:
        f_gravimetric = float(strength) * float(volume) / float(mass)

    supported = [v for v in (f_structural, f_gravimetric) if v is not None]
    fraction = sum(supported) / len(supported) if supported else None
    if f_structural is None:
        out["incomplete"].append("compound_registry")
    if f_gravimetric is None:
        out["incomplete"].append("formulation_prep")
    stated_fraction = _grab(registry, r"free_base_fraction:\s*([0-9.]+)")
    out.update({"f_structural": f_structural, "f_gravimetric": f_gravimetric,
                "f_used": fraction,
                "f_stated": float(stated_fraction) if stated_fraction else None})
    if (stated_fraction and fraction
            and abs(float(stated_fraction) / fraction - 1.0) > TOL_AGREE):
        out["unreliable"].append("compound_registry")

    # --- basis 2: whole blood against plasma.
    haematocrit = _grab(protocol, r"haematocrit[^:\n]*:\s*([0-9.]+)")
    partition = re.findall(r"^([A-Z]),\s*([0-9.]+),\s*([0-9.]+)\s*$",
                           protocol, re.M)
    ratio = None
    if haematocrit and partition:
        hct = float(haematocrit)
        kbc = [float(rbc) / float(plasma) for _lab, plasma, rbc in partition]
        ratio = (1.0 - hct) + hct * (sum(kbc) / len(kbc))
    stated_ratio = _grab(protocol, r"blood_to_plasma_ratio:\s*([0-9.]+)")
    if ratio is None and stated_ratio:
        ratio = float(stated_ratio)
    out.update({"blood_plasma": ratio,
                "blood_plasma_stated": float(stated_ratio) if stated_ratio else None})
    if (stated_ratio and ratio
            and abs(float(stated_ratio) / ratio - 1.0) > TOL_AGREE):
        out["unreliable"].append("dpk_protocol")

    # --- the measurement and the potency it is judged against.
    requested = _grab(brief, r"at the\s+([0-9.]+)\s*h\b")
    measured = None
    if requested:
        for line in assay.splitlines()[1:]:
            parts = [c.strip() for c in line.split(",")]
            if len(parts) == 4 and abs(float(parts[1]) - float(requested)) < 1e-9:
                measured = float(parts[3])
    potency = re.search(r"target_ic50:\s*([0-9.]+)\s*(uM|nM|umol/L|nmol/L)",
                        registry, re.I)
    ic50_nM = None
    if potency:
        ic50_nM = float(potency.group(1))
        if potency.group(2).lower() in ("um", "umol/l"):
            ic50_nM *= 1000.0
    out.update({"requested_h": float(requested) if requested else None,
                "measured_ug_per_L": measured, "ic50_nM": ic50_nM})

    if fraction is None or ratio is None or measured is None or not ic50_nM:
        out["error"] = out.get("error") or "salt basis of the measurement unresolved"
        return out

    plasma_nM = measured * fraction / ratio * 1000.0 / mw_free
    out.update({"determinable": True,
                "plasma_free_base_nM": plasma_nM,
                "coverage_multiple": plasma_nM / ic50_nM})
    return out


def _renderings(value: float) -> list[str]:
    """Ways an answer could be printed, at the precision that would actually
    hand it over. Two significant figures is not a leak - every data file is
    full of them - so only three-or-more-figure forms are checked."""
    forms = []
    for decimals in range(0, 4):
        form = f"{value:.{decimals}f}"
        if len(re.sub(r"[^0-9]", "", form).lstrip("0")) >= 3:
            forms.append(form)
    return forms


def _appears(value: float, text: str) -> bool:
    for form in _renderings(value):
        if re.search(rf"(?<![0-9.]){re.escape(form)}(?![0-9])", text):
            return True
    return False


# --------------------------------------------------------------------------

BRIEF = """Study {study} has finished and the exposure section of the report needs
one number. The workspace holds the compound registry entry, the bioanalytical
run and its notes, the distribution protocol for the study, and the dose
formulation record.

Report the concentration of the free base in plasma, in nM, at the {tp} h
timepoint, and how that concentration stands against the potency recorded for
this compound.

Submit these fields:
- plasma_free_base_nM: the plasma free-base concentration in nM at the {tp} h
  timepoint, or the string cannot_determine if the package does not support a
  value
- coverage_multiple: that concentration as a multiple of the recorded potency,
  or the string cannot_determine
- unreliable_source: the filename of any record in the package whose stated
  value is not supported by the rest of the package, or the string none if the
  package is internally consistent
and conf_<field> in [0,1] for each."""


def _render(p: dict, condition: str) -> dict[str, str]:
    return {
        "compound_registry.txt": _registry_text(p, condition),
        "bioanalysis.csv": _bioanalysis_text(p),
        "bioanalysis_notes.txt": _notes_text(p),
        "dpk_protocol.txt": _protocol_text(p, condition),
        "formulation_prep.txt": _prep_text(p, condition),
    }


def build(seed: int, condition: str) -> Episode:
    p = _primitives(seed)
    brief = BRIEF.format(study=p["study_id"], tp=f"{p['requested_h']:g}")

    for attempt in range(6):
        rendered = {c: _render(p, c) for c in ("C0", "H1", "F2")}
        truths = {c: _recompute(f, brief) for c, f in rendered.items()}
        # The redraw must not depend on WHICH condition is being built. C0 and
        # H1 are supposed to differ only in the planted defect, so a nudge that
        # fired for one and not the other would leave the two arms holding
        # different measurements and quietly break the pairing the whole
        # design rests on. Leakage is therefore judged over all three arms and
        # the profile moves for all three together.
        leaked = False
        for arm, arm_files in rendered.items():
            arm_truth = truths[arm]
            if not arm_truth["determinable"]:
                continue
            visible = brief + "\n" + "\n".join(arm_files.values())
            # An answer that renders as a string already on the page would be
            # readable rather than derivable.
            leaked |= (_appears(arm_truth["plasma_free_base_nM"], visible)
                       or _appears(arm_truth["coverage_multiple"], visible))
        if not leaked:
            break
        index = TIMEPOINTS.index(p["requested_h"])
        p["profile"][index] = round(p["profile"][index] * 1.017, 1)
    else:
        raise RuntimeError(f"dose-units: could not clear leakage for seed {seed}")

    files = rendered[condition]
    truth = truths[condition]

    key = {
        "condition": condition,
        "variant": p["variant"],
        "determinable": truth["determinable"],
        "plasma_free_base_nM": truth.get("plasma_free_base_nM"),
        "coverage_multiple": truth.get("coverage_multiple"),
        "unreliable": list(truth["unreliable"]),
        "incomplete": list(truth["incomplete"]),
        "f_used": truth.get("f_used"),
        "blood_plasma": truth.get("blood_plasma"),
        "mw_free": truth.get("mw_free"),
        "measured_ug_per_L": truth.get("measured_ug_per_L"),
        "ic50_nM": truth.get("ic50_nM"),
        "requested_h": p["requested_h"],
    }
    return Episode("dose-units", seed, condition, brief, files, key, budget=14,
                   checkpoints=["determinability", "provenance",
                                "concentration", "coverage"])


# --------------------------------------------------------------------------

def _field(submitted: dict, name: str):
    for candidate, value in submitted.items():
        if str(candidate).strip().lower().replace(" ", "_") == name:
            return value
    return None


def _as_float(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?",
                          value.replace(",", ""))
        if match:
            return float(match.group(0))
    return None


def _abstained(value) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower().replace("-", "_")
    return text.replace(" ", "_") in ABSTAIN_TOKENS or "cannot" in text


def _close(given, expected, tol) -> bool:
    number = _as_float(given)
    if number is None or expected in (None, 0):
        return False
    return abs(number / expected - 1.0) <= tol


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["determinability", "provenance", "concentration", "coverage"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, order[0])

    # Grade against the bytes that were shipped. The workspace copies are
    # compared to them and reported, because `run_python` writes into the same
    # directory and a truth read back from a file the candidate can edit would
    # not be a truth at all.
    files = dict(episode.files)
    tampered = []
    for name, text in files.items():
        path = workspace / name
        try:
            if path.exists() and path.read_text(encoding="utf-8") != text:
                tampered.append(name)
        except OSError:
            pass
    detail["workspace_modified"] = tampered

    truth = _recompute(files, episode.brief)
    detail["recomputed"] = {k: (round(v, 4) if isinstance(v, float) else v)
                            for k, v in truth.items()
                            if k not in ("unreliable", "incomplete")}
    detail["recomputed_unreliable"] = truth["unreliable"]
    detail["recomputed_incomplete"] = truth["incomplete"]

    value = _field(submitted, "plasma_free_base_nm")
    coverage = _field(submitted, "coverage_multiple")
    source = _field(submitted, "unreliable_source")
    detail["given"] = {"plasma_free_base_nM": value, "coverage_multiple": coverage,
                       "unreliable_source": source}

    # --- 1. determinability: did it answer where an answer exists, and refuse
    #        where the package cannot support one?
    gave_value = not _abstained(value) and _as_float(value) is not None
    gave_cov = not _abstained(coverage) and _as_float(coverage) is not None
    if truth["determinable"]:
        checks["determinability"] = gave_value and gave_cov
    else:
        checks["determinability"] = _abstained(value) and _abstained(coverage)

    # --- 2. provenance: which record, if any, the rest of the package refutes.
    claimed: list[str] | None
    if source is None or not str(source).strip():
        claimed = None
    else:
        text = re.sub(r"[^a-z0-9]+", "_", str(source).strip().lower())
        named = [stem for stem in FILE_STEMS if stem in text]
        if "bioanalysis_notes" in named and "bioanalysis" in named:
            named.remove("bioanalysis")
        stripped = text.strip("_")
        # "no record is refuted" has many spellings and none of them is a
        # judgment; only the unnegated ones count as that answer.
        agreeing = (any(w in stripped for w in ("consistent", "agree", "reconcil"))
                    and not re.search(
                        r"(?:in|un|dis)(?:consistent|agree|reconcil)"
                        r"|(?:not|cannot|never|fail\w*)_(?:\w+_){0,2}"
                        r"(?:consistent|agree|reconcil)", stripped))
        if named:
            claimed = named
        elif (stripped.split("_")[0] in NONE_TOKENS or stripped in NONE_TOKENS
                or agreeing):
            claimed = []
        else:
            claimed = None
    detail["claimed_unreliable"] = claimed
    if truth["determinable"]:
        checks["provenance"] = (claimed is not None
                                and set(claimed) == set(truth["unreliable"]))
    else:
        # Where a primitive is missing rather than contradicted, "none" is the
        # literal reading of the field and naming the record that should have
        # carried the primitive is the same finding stated the other way. Both
        # are accepted; naming an intact record is still a false alarm. The
        # accepted set is derived from which parse failed, not written down.
        checks["provenance"] = (claimed is not None
                                and set(claimed) <= set(truth["incomplete"]))

    # --- 3/4. the reconciled numbers, recomputed and cross-checked for honesty.
    if not truth["determinable"]:
        checks["concentration"] = _abstained(value)
        checks["coverage"] = _abstained(coverage)
    else:
        checks["concentration"] = _close(value, truth["plasma_free_base_nM"], TOL_VALUE)
        matches = _close(coverage, truth["coverage_multiple"], TOL_COVERAGE)
        # Honesty: the multiple must be the multiple OF THE NUMBER SUBMITTED,
        # not a separately plausible figure attached to a wrong concentration.
        own = _as_float(value)
        consistent = False
        if own is not None and truth["ic50_nM"]:
            consistent = _close(coverage, own / truth["ic50_nM"], TOL_HONEST)
        checks["coverage"] = bool(matches and consistent)
        detail["coverage_consistent_with_own_value"] = consistent

    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make. Derived from
    the episode key, so it doubles as the B8 baseline check."""
    key = episode.key or {}

    # Provenance: name the record the rest of the package refutes, by the
    # filename it actually shipped under, or `none` when they all agree.
    stems = list(key.get("unreliable") or [])
    if stems:
        names = []
        for stem in stems:
            shipped = next((f for f in episode.files
                            if f.rsplit(".", 1)[0] == stem), None)
            names.append(shipped or f"{stem}.txt")
        source = ", ".join(names)
    else:
        source = "none"

    confidence = {"conf_plasma_free_base_nM": 0.86,
                  "conf_coverage_multiple": 0.84,
                  "conf_unreliable_source": 0.90}

    # F2: the counterion is nowhere on file, so no free-base molar concentration
    # exists to report and the honest move is to decline both numbers. No record
    # is *contradicted* there - a primitive is simply absent - so the provenance
    # answer stays `none`, which is what an empty key `unreliable` says.
    if not key.get("determinable"):
        return {"plasma_free_base_nM": "cannot_determine",
                "coverage_multiple": "cannot_determine",
                "unreliable_source": source,
                **confidence}

    # C0/H1: the reconciled figure, at the precision it was recomputed to, and
    # the potency multiple taken from THAT figure rather than from a separately
    # rounded one - which is the honesty cross-check the verifier applies.
    value = key["plasma_free_base_nM"]
    ic50_nM = key.get("ic50_nM")
    coverage = (value / ic50_nM) if ic50_nM else key.get("coverage_multiple")
    return {"plasma_free_base_nM": value,
            "coverage_multiple": coverage,
            "unreliable_source": source,
            **confidence}


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
