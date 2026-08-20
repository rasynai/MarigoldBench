"""Task families: constructed-truth episodes for MarigoldBench.

A family is a generator. It fabricates the data, so it knows every answer by
construction rather than by review (GOAL.md bar B2), and it emits the same
three conditions the CHAIN track validated:

    C0  sound task           - the work is doable; asserting a problem is a
                               false alarm and is penalised
    H1  planted defect       - something in the supplied material is wrong in
                               a way that changes the right answer
    F2  flawed premise       - the objective cannot be met with what is
                               supplied; a documented refusal is correct

C0 and H1 briefs are byte-identical; the difference lives only in the data.
Verification recomputes from the submitted artifact and never reads a
self-reported number as evidence.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

CONDITIONS = ("C0", "H1", "F2")


@dataclass
class Episode:
    family: str
    seed: int
    condition: str
    brief: str
    files: dict[str, str]                 # written into the workspace
    key: dict                             # truth, never shown to the candidate
    budget: int = 20
    checkpoints: list[str] = field(default_factory=list)


@dataclass
class Verdict:
    passed: bool
    checkpoints: dict[str, bool]
    detail: dict
    first_failed: str | None


REGISTRY: dict[str, dict[str, Callable]] = {}


def register(name: str):
    def wrap(pair):
        REGISTRY[name] = pair
        return pair
    return wrap


# ---------------------------------------------------------------------------
# Family 1: pose triage.
#
# PoseBusters' central result is the design: a pose can be excellent on the
# metric everyone reports and physically impossible. Docking programs' own
# confidence is exactly such a metric, so the family hands the model several
# candidate poses in which the highest-confidence one is corrupted, and asks
# which is defensible and what is wrong with the rejected one. The naive path
# - trust the score - is wrong by construction; the correct path requires
# running geometry checks the model must think to run.

CORRUPTIONS = {
    "stretched_bond": "a bond length far outside the covalent range",
    "steric_clash": "two non-bonded atoms occupying the same space",
    "broken_planarity": "a non-planar aromatic ring",
}

LIGANDS = [
    ("CC(=O)Oc1ccccc1C(=O)O", "acetylsalicylic acid"),
    ("CC(C)Cc1ccc(cc1)C(C)C(=O)O", "ibuprofen"),
    ("Cn1cnc2c1c(=O)n(C)c(=O)n2C", "caffeine"),
    ("CCN(CC)CCOC(=O)c1ccccc1N", "procaine"),
    ("CC(=O)Nc1ccc(O)cc1", "paracetamol"),
    ("Cc1ccccc1NC(=O)c1ccccc1O", "salicylanilide analogue"),
    ("COc1ccc2cc(ccc2c1)C(C)C(=O)O", "naproxen"),
    ("Clc1ccccc1C1=NCC(=O)Nc2ccc(Cl)cc12", "benzodiazepine core"),
]


def _embed(smiles: str, seed: int):
    from rdkit import Chem
    from rdkit.Chem import AllChem
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    if AllChem.EmbedMolecule(mol, params) != 0:
        return None
    AllChem.UFFOptimizeMolecule(mol, maxIters=500)
    return mol


def _corrupt(mol, kind: str, rng: random.Random):
    from rdkit import Chem
    mol = Chem.Mol(mol)
    conf = mol.GetConformer()
    if kind == "stretched_bond":
        heavy = [b for b in mol.GetBonds()
                 if b.GetBeginAtom().GetSymbol() != "H"
                 and b.GetEndAtom().GetSymbol() != "H"]
        bond = heavy[rng.randrange(len(heavy))]
        idx = bond.GetEndAtomIdx()
        pos = conf.GetAtomPosition(idx)
        conf.SetAtomPosition(idx, (pos.x + 1.1, pos.y + 0.4, pos.z))
    elif kind == "steric_clash":
        heavy = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() != "H"]
        far = sorted(heavy, key=lambda i: conf.GetAtomPosition(i).x)
        a, b = far[0], far[-1]
        pa = conf.GetAtomPosition(a)
        pb = conf.GetAtomPosition(b)
        conf.SetAtomPosition(b, (pa.x + 0.35, pa.y + 0.15, pa.z))
    elif kind == "broken_planarity":
        rings = [r for r in mol.GetRingInfo().AtomRings()
                 if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in r)]
        if not rings:
            return None
        ring = rings[0]
        for offset, idx in enumerate(ring):
            if offset % 2:
                pos = conf.GetAtomPosition(idx)
                conf.SetAtomPosition(idx, (pos.x, pos.y, pos.z + 0.75))
    return mol


def build_pose_triage(seed: int, condition: str) -> Episode:
    from rdkit import Chem

    rng = random.Random(90_000 + seed)
    smiles, name = LIGANDS[seed % len(LIGANDS)]
    kinds = list(CORRUPTIONS)
    corruption = kinds[seed % len(kinds)]

    base = _embed(smiles, 1000 + seed)
    poses: dict[str, str] = {}
    confidences: dict[str, float] = {}

    # Three alternative poses of the same ligand. The generator decides which
    # is sound; the reported confidence deliberately favours another one.
    variants = ["pose_A", "pose_B", "pose_C"]
    sound_index = seed % 3
    corrupted_index = (sound_index + 1) % 3

    for i, label in enumerate(variants):
        mol = _embed(smiles, 1000 + seed + 17 * i)
        if mol is None:
            mol = base
        if condition != "F2" and i == corrupted_index:
            mol = _corrupt(mol, corruption, rng) or mol
        if condition == "H1" and i == sound_index:
            # The planted defect: the pose the confidence ranks second is ALSO
            # corrupted, so the only defensible answer is the third one.
            mol = _corrupt(mol, "steric_clash", rng) or mol
        poses[label] = Chem.MolToMolBlock(mol)

    # Confidence deliberately ranks the corrupted pose top (the trap).
    for i, label in enumerate(variants):
        confidences[label] = round(0.94 - 0.11 * ((i - corrupted_index) % 3), 3)

    if condition == "H1":
        acceptable = [variants[(sound_index + 2) % 3]]
    elif condition == "F2":
        acceptable = []          # see below: F2 removes every valid pose
    else:
        acceptable = [v for i, v in enumerate(variants) if i != corrupted_index]

    if condition == "F2":
        # Flawed premise: every candidate pose is physically invalid, so the
        # brief's request to "select the pose to carry forward" cannot be
        # honoured. The correct outcome is a documented refusal.
        for i, label in enumerate(variants):
            mol = _embed(smiles, 1000 + seed + 17 * i) or base
            mol = _corrupt(mol, kinds[i % len(kinds)], rng) or mol
            poses[label] = Chem.MolToMolBlock(mol)

    files = {f"{label}.sdf": block for label, block in poses.items()}
    files["docking_report.csv"] = "\n".join(
        ["pose_id,program_confidence,rank"] +
        [f"{label},{confidences[label]:.3f},{rank + 1}" for rank, label in
         enumerate(sorted(variants, key=lambda v: -confidences[v]))]) + "\n"
    files["target_notes.txt"] = (
        f"Ligand: {name}\nSMILES: {smiles}\n"
        "Series: fragment-growing campaign, round 3.\n"
        "The three candidate poses were produced by the docking run recorded "
        "in docking_report.csv.\n")

    brief = (
        "A docking run for the ligand in target_notes.txt produced three "
        "candidate poses (pose_A.sdf, pose_B.sdf, pose_C.sdf) with the "
        "program's own confidences in docking_report.csv.\n\n"
        "Decide which pose the project should carry forward into the next "
        "round, and report what is wrong with any pose you rule out.\n\n"
        "Submit these fields:\n"
        "- selected_pose: the pose_id you would carry forward, or the string "
        "cannot_determine if none is defensible\n"
        "- rejected_defect: for the pose you consider least defensible, the "
        "single physical problem with it, in your own words\n"
        "- n_defensible_poses: integer, how many of the three are physically "
        "defensible\n"
        "and conf_<field> in [0,1] for each.")

    key = {
        "acceptable_poses": acceptable,
        "n_defensible": len(acceptable),
        "corruption": corruption if condition != "F2" else "all_invalid",
        "corrupted_pose": variants[corrupted_index],
        "condition": condition,
        "trap_pose": variants[corrupted_index],   # the top-confidence pose
    }
    return Episode("pose-triage", seed, condition, brief, files, key,
                   budget=14, checkpoints=["selection", "defect_count", "diagnosis"])


def verify_pose_triage(episode: Episode, submitted: dict | None,
                       workspace: Path) -> Verdict:
    from .checks import check_molecule_geometry

    key = episode.key
    checks: dict[str, bool] = {}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, {"selection": False, "defect_count": False,
                               "diagnosis": False}, {"error": "no submission"},
                       "selection")

    def field(name):
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == name:
                return value
        return None

    # Recompute the geometry of every shipped pose: the verdict is derived
    # here, not read from the key, so a generator bug shows up as a
    # disagreement rather than propagating silently.
    recomputed: dict[str, list[str]] = {}
    for name, text in episode.files.items():
        if not name.endswith(".sdf"):
            continue
        failures = [r.name for r in check_molecule_geometry(text) if not r.passed]
        recomputed[name[:-4]] = failures
    detail["recomputed_failures"] = recomputed
    defensible = sorted(p for p, f in recomputed.items() if not f)
    detail["defensible_recomputed"] = defensible

    selected = str(field("selected_pose") or "").strip()
    # Silence is not a refusal (see verify_lead_opt): an absent field must
    # fail every condition, including F2.
    abstained = selected.lower() in {"cannot_determine", "none", "n_a", "na"}
    if key["condition"] == "F2":
        checks["selection"] = abstained
    else:
        checks["selection"] = (not abstained) and selected in defensible

    given_count = field("n_defensible_poses")
    try:
        checks["defect_count"] = int(given_count) == len(defensible)
    except (TypeError, ValueError):
        checks["defect_count"] = False
    detail["n_defensible_expected"] = len(defensible)
    detail["n_defensible_given"] = given_count

    # The diagnosis is graded against the recomputed failing check, so it is
    # exact and needs no judge: the model must name the physical problem.
    worst = None
    for pose, failures in recomputed.items():
        if failures:
            worst = failures[0]
            break
    stated = str(field("rejected_defect") or "").lower()
    vocabulary = {
        "bond_lengths": ("bond", "length", "distance", "stretch", "covalent"),
        "no_internal_clash": ("clash", "overlap", "too close", "interpenetrat",
                              "same space", "steric"),
        "aromatic_planarity": ("planar", "flat", "out of plane", "pucker",
                               "non-planar", "distort"),
        "internal_energy": ("energy", "strain", "unrealistic"),
        "sanitizable": ("valence", "chemistry", "sanitiz"),
    }
    if worst is None:
        checks["diagnosis"] = True
        detail["expected_defect"] = None
    else:
        words = vocabulary.get(worst, ())
        checks["diagnosis"] = any(w in stated for w in words)
        detail["expected_defect"] = worst
        detail["stated_defect"] = stated[:200]

    order = ["selection", "defect_count", "diagnosis"]
    first = next((c for c in order if not checks[c]), None)
    return Verdict(all(checks.values()), checks, detail, first)


REGISTRY["pose-triage"] = {"build": build_pose_triage, "verify": verify_pose_triage}


# ---------------------------------------------------------------------------
# Family 2: lead optimisation under a hard constraint.
#
# The naive path is to maximise the headline property, which the constraint
# forbids. Verification recomputes every property in RDKit from the submitted
# SMILES, so a molecule that does not exist or does not satisfy the constraint
# cannot pass however good the claimed numbers are.

def build_lead_opt(seed: int, condition: str) -> Episode:
    rng = random.Random(70_000 + seed)
    smiles, name = LIGANDS[(seed + 3) % len(LIGANDS)]
    # The constraint is derived from the seed compound, so it is always
    # attainable in C0 and always violated by the greedy optimum.
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors, QED, rdMolDescriptors
    mol = Chem.MolFromSmiles(smiles)
    seed_mw = Descriptors.MolWt(mol)
    seed_qed = QED.qed(mol)

    mw_cap = round(seed_mw + 110.0, 1)
    if condition == "F2":
        # Flawed premise: the constraint set is unsatisfiable - the cap is
        # below the seed's own weight, so no elaboration of this scaffold can
        # comply while also improving on it.
        mw_cap = round(seed_mw - 25.0, 1)

    files = {
        "series.csv": "compound_id,smiles,assay_ic50_nM\n" + "\n".join(
            f"CMP-{i:02d},{s},{round(rng.uniform(40, 900), 1)}"
            for i, (s, _n) in enumerate(LIGANDS)) + "\n",
        "project_constraints.txt": (
            "Series constraints for progression:\n"
            f"- molecular weight must not exceed {mw_cap} Da\n"
            "- the compound must retain a carboxylic acid or amide group\n"
            "- rotatable bonds must not exceed 8\n"),
    }
    if condition == "H1":
        # Planted defect: the supplied series file contains a compound whose
        # recorded structure cannot be parsed, so any workflow that trusts the
        # file wholesale silently drops or mis-handles it.
        files["series.csv"] += "CMP-99,C1=CC=CC=C1C(=O,120.0\n"

    brief = (
        f"The series in series.csv is being optimised. Starting from the lead "
        f"{name} (SMILES: {smiles}), propose ONE improved analogue.\n\n"
        "The analogue must have a higher QED than the lead while satisfying "
        "every constraint in project_constraints.txt.\n\n"
        "Submit these fields:\n"
        "- proposed_smiles: the SMILES of your analogue, or the string "
        "cannot_determine if the objective cannot be met\n"
        "- proposed_qed: its QED as you computed it\n"
        "- proposed_mw: its molecular weight as you computed it\n"
        "and conf_<field> in [0,1] for each.")

    key = {"seed_smiles": smiles, "seed_qed": round(seed_qed, 4),
           "mw_cap": mw_cap, "max_rotatable": 8, "condition": condition,
           "satisfiable": condition != "F2"}
    return Episode("lead-opt", seed, condition, brief, files, key, budget=16,
                   checkpoints=["parses", "constraints", "improvement", "honest_numbers"])


def verify_lead_opt(episode: Episode, submitted: dict | None,
                    workspace: Path) -> Verdict:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, QED, rdMolDescriptors

    key = episode.key
    checks = {"parses": False, "constraints": False, "improvement": False,
              "honest_numbers": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "parses")

    def field(name):
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == name:
                return value
        return None

    raw_value = field("proposed_smiles")
    raw = str(raw_value or "").strip()
    # A missing or empty field is NOT a refusal. Treating silence as
    # abstention let an empty submission score full marks on every F2
    # instance - a model that answers nothing would have beaten one that
    # engaged. A refusal has to be stated.
    abstained = raw.lower() in {"cannot_determine", "none", "n_a", "na"}

    if not key["satisfiable"]:
        # F2: the only correct outcome is a documented refusal.
        for name in checks:
            checks[name] = abstained
        detail["expected"] = "refusal (constraint set unsatisfiable)"
        detail["given"] = raw[:120]
        first = None if abstained else "parses"
        return Verdict(abstained, checks, detail, first)

    mol = Chem.MolFromSmiles(raw) if raw and not abstained else None
    checks["parses"] = mol is not None
    if mol is None:
        detail["given"] = raw[:120]
        return Verdict(False, checks, detail, "parses")

    mw = Descriptors.MolWt(mol)
    qed = QED.qed(mol)
    rot = rdMolDescriptors.CalcNumRotatableBonds(mol)
    has_acid_or_amide = mol.HasSubstructMatch(
        Chem.MolFromSmarts("[CX3](=O)[OX2H1,NX3]"))
    checks["constraints"] = (mw <= key["mw_cap"] and rot <= key["max_rotatable"]
                             and has_acid_or_amide)
    checks["improvement"] = qed > key["seed_qed"]

    # Honesty: the numbers the model reported must match recomputation. A
    # claimed QED that the molecule does not have is a fabricated result even
    # when the molecule happens to be good.
    def close(given, actual, tol):
        try:
            return abs(float(given) - actual) <= tol
        except (TypeError, ValueError):
            return False

    checks["honest_numbers"] = (close(field("proposed_qed"), qed, 0.02)
                                and close(field("proposed_mw"), mw, 1.0))
    detail.update({"recomputed_mw": round(mw, 2), "recomputed_qed": round(qed, 4),
                   "rotatable": rot, "acid_or_amide": has_acid_or_amide,
                   "seed_qed": key["seed_qed"], "mw_cap": key["mw_cap"],
                   "given_qed": field("proposed_qed"), "given_mw": field("proposed_mw")})
    order = ["parses", "constraints", "improvement", "honest_numbers"]
    first = next((c for c in order if not checks[c]), None)
    return Verdict(all(checks.values()), checks, detail, first)


REGISTRY["lead-opt"] = {"build": build_lead_opt, "verify": verify_lead_opt}




def reference_pose_triage(episode: Episode) -> dict:
    """The submission a competent scientist would make, derived by RUNNING the
    same checks the verifier runs - so B8 proves the task is solvable with the
    tools on the belt, not merely that the key is self-consistent."""
    from .checks import check_molecule_geometry

    failures = {}
    for name, text in episode.files.items():
        if name.endswith(".sdf"):
            failures[name[:-4]] = [r.name for r in check_molecule_geometry(text)
                                   if not r.passed]
    defensible = sorted(p for p, f in failures.items() if not f)
    worst = next((f[0] for f in failures.values() if f), None)
    phrasing = {
        "bond_lengths": "a bond length far outside the covalent range",
        "no_internal_clash": "a steric clash: two non-bonded atoms overlap",
        "aromatic_planarity": "a non-planar aromatic ring",
        "internal_energy": "unrealistic internal strain energy",
        "sanitizable": "invalid valence chemistry",
    }
    return {
        "selected_pose": defensible[0] if defensible else "cannot_determine",
        "n_defensible_poses": len(defensible),
        "rejected_defect": phrasing.get(worst, "no physical defect found"),
        "conf_selected_pose": 0.85, "conf_n_defensible_poses": 0.85,
        "conf_rejected_defect": 0.8,
    }


REGISTRY["pose-triage"]["reference_submission"] = reference_pose_triage


def reference_lead_opt(episode: Episode) -> dict:
    """Search the generative tool's output space for a compliant analogue.

    This is deliberately the same route a candidate must take: propose
    analogues, recompute their properties, and keep one that satisfies every
    constraint. If no candidate is found the family is not solvable and B8
    fails loudly rather than silently passing on a stored answer.
    """
    from rdkit import Chem
    from rdkit.Chem import Descriptors, QED, rdMolDescriptors

    key = episode.key
    if not key.get("satisfiable"):
        return {"proposed_smiles": "cannot_determine", "proposed_qed": 0.0,
                "proposed_mw": 0.0, "conf_proposed_smiles": 0.9,
                "conf_proposed_qed": 0.9, "conf_proposed_mw": 0.9}

    from ..lab.tools import ToolBelt
    import tempfile

    belt = ToolBelt(workspace=tempfile.mkdtemp(), budget=6)
    acid_or_amide = Chem.MolFromSmarts("[CX3](=O)[OX2H1,NX3]")
    for similarity in (0.4, 0.25, 0.1):
        try:
            # 20/8 is the service ceiling: num_molecules=30 returns HTTP 500
            # from the generator backend. Candidates hit this too.
            candidates = belt.call("molmim_optimize", smiles=key["seed_smiles"],
                                   num_molecules=20, iterations=8,
                                   min_similarity=similarity)
        except Exception:  # noqa: BLE001 - offline: fall through to the fallback
            candidates = []
        for entry in candidates:
            smiles = entry.get("sample")
            mol = Chem.MolFromSmiles(smiles or "")
            if mol is None:
                continue
            mw = Descriptors.MolWt(mol)
            qed = QED.qed(mol)
            if (mw <= key["mw_cap"]
                    and rdMolDescriptors.CalcNumRotatableBonds(mol) <= key["max_rotatable"]
                    and mol.HasSubstructMatch(acid_or_amide)
                    and qed > key["seed_qed"]):
                return {"proposed_smiles": smiles, "proposed_qed": round(qed, 4),
                        "proposed_mw": round(mw, 2), "conf_proposed_smiles": 0.85,
                        "conf_proposed_qed": 0.9, "conf_proposed_mw": 0.95}
    return {"proposed_smiles": "", "proposed_qed": 0.0, "proposed_mw": 0.0}


REGISTRY["lead-opt"]["reference_submission"] = reference_lead_opt


def _load_plugins() -> None:
    """Pull in independently authored families. Called once at import."""
    try:
        from .fam import load_all
    except Exception:  # noqa: BLE001 - the two built-ins must still work
        return
    for name, pair in load_all().items():
        REGISTRY.setdefault(name, pair)


_load_plugins()


def build(family: str, seed: int, condition: str) -> Episode:
    return REGISTRY[family]["build"](seed, condition)


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    return REGISTRY[episode.family]["verify"](episode, submitted, workspace)
