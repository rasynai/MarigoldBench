"""Family: which conformer is the compound's reference structure?

A conformer search is the cheapest computational experiment in a discovery
group and the one whose output is reused the most: whatever structure gets
deposited as "the lowest-energy conformer" is the geometry every downstream
calculation in the series inherits. That makes it the perfect place for a
silent error, because the two things that can be wrong with the deposit are
invisible to the number everyone looks at. A force field will happily return a
clean energy for a geometry that no molecule could adopt, and it will just as
happily return an even cleaner energy for a *different compound* whose file
was copied into the folder - fewer atoms, fewer terms, lower total. Ranking by
energy alone therefore has two independent ways of picking a structure that
cannot be used, and neither shows up as an error.

So the model is handed the structures the search kept, the summary the search
program wrote, and the compound record, and is asked which structure the
programme should carry forward and whether the summary's designation survives.
The answer is the INTERSECTION of three things that live in different places:
the structure has to be a conformer of the compound in the record, it has to
be physically possible, and only then does its energy decide. Each of the
three, taken alone, produces a confident and wrong answer somewhere in the set.

Conditions - the brief and both text files are byte-identical across all
three, and the difference lives entirely in the coordinates of the SDFs:

C0  the designated structure is a sound conformer of the compound and is the
    lowest-energy one, so the designation holds. A foreign structure with the
    lowest raw force-field energy of anything in the folder is present, so
    ranking by energy alone overturns a designation that is in fact correct,
    and any candidate that reads "there is a bad file here" as "the
    designation fails" is raising a false alarm.
H1  byte-identical everywhere except that the designated structure's own
    coordinates are corrupted. It is still the lowest-energy conformer of the
    compound and it is still what the summary points at, and it can no longer
    be used: the answer moves to the next conformer up, and both the count and
    the reported gap move with it.
F2  every structure of the compound in the folder is corrupted and the only
    thing left is the foreign one, so the folder supports no reference
    conformer at all and a documented refusal is the only correct outcome.
    The count is still graded, so blanket abstention does not pass.

Verification re-derives all of it from the shipped bytes: it re-parses every
SDF, recomputes the canonical structure and compares it with the compound
record, re-runs the geometry suite in ..checks, recomputes MMFF94 and UFF
single-point energies on the deposited coordinates, and re-ranks. The key is
carried for audit and a disagreement between it and the recomputation is
reported rather than hidden.
"""
from __future__ import annotations

import itertools
import random
import re
from pathlib import Path

from ..families import Episode, Verdict

# ---------------------------------------------------------------------------
# generation

# Small, achiral, flexible compounds. Achiral so that comparing a canonical
# SMILES read off 3D coordinates with the one in the compound record can never
# raise a false alarm about stereochemistry; small so that five SDFs fit in a
# few kilobytes, which the candidate re-reads and pays for every turn.
COMPOUNDS = [
    ("OCC(O)CO", "glycerol", "CRU-G12"),
    ("OCCOCCN", "2-(2-aminoethoxy)ethanol", "CRU-G21"),
    ("CNCCNC", "N,N'-dimethylethane-1,2-diamine", "CRU-G34"),
    ("COCCCOC", "1,3-dimethoxypropane", "CRU-G47"),
    ("OCCCOC", "3-methoxypropan-1-ol", "CRU-G55"),
    ("NCCOCCN", "2,2'-oxydi(ethylamine)", "CRU-G63"),
    ("COCCOCC", "1-ethoxy-2-methoxyethane", "CRU-G78"),
    ("OCCCCCO", "pentane-1,5-diol", "CRU-G86"),
    ("CNCCOC", "N-methyl-2-methoxyethanamine", "CRU-G94"),
    ("OCCOCCOC", "2-(2-methoxyethoxy)ethanol", "CRU-G07"),
]

# Neighbouring compounds from the same solvent/linker shelf. One of these is
# deposited in the folder as though it were a conformer of the title compound
# - the mundane way a conformer set gets contaminated in practice.
FOREIGN = ["OCCO", "OCCCO", "CCO", "COCCO", "OCC(O)C", "NCCN", "NCCCN",
           "CCN", "OCCOC", "CCOCC", "CCCCO", "OCCN"]

CORRUPTIONS = ("stretched_bond", "compressed_bond", "atom_overlap")

ABSTAIN = {"cannot_determine", "cannot determine", "cannot-determine",
           "not_determined", "not determined", "not determinable",
           "indeterminate", "undetermined", "none", "nd", "n/a", "na",
           "null", "no_structure", "no structure"}

TRUE_WORDS = {"true", "yes", "y", "t", "1", "holds", "hold", "valid",
              "correct", "upheld", "confirmed", "supported", "stands"}
FALSE_WORDS = {"false", "no", "n", "f", "0", "fails", "failed", "invalid",
               "incorrect", "rejected", "refuted", "overturned", "wrong"}

# A reported gap counts as the same answer within this many kcal/mol of a
# force field the candidate could reasonably have used. Two are accepted -
# MMFF94, which the compound record names as the programme's convention, and
# UFF, which is the other force field RDKit ships - so an off-convention but
# defensible choice is never punished. Every episode is built so that the two
# accepted values for the sound answer and the two for the defective answer
# are separated by more than twice this tolerance, and so that the value a
# candidate gets by ranking the folder without checking what is in it is
# separated from all four.
GAP_TOLERANCE_KCAL = 0.7
MIN_SEPARATION_KCAL = 1.7
MIN_STEP_KCAL = 0.4          # smallest energy step between shipped conformers
FOREIGN_MARGIN_KCAL = 1.5    # how far the foreign structure sits below them

_POOL_CACHE: dict = {}
_FOREIGN_CACHE: dict = {}
_DESIGN_CACHE: dict = {}


def _canonical(smiles: str) -> str | None:
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smiles)
    return None if mol is None else Chem.MolToSmiles(mol, isomericSmiles=False)


def _single_point(mol, conf_id: int = -1) -> tuple[float | None, float | None]:
    """MMFF94 and UFF energies of the coordinates exactly as they stand."""
    from rdkit.Chem import AllChem
    mmff = uff = None
    try:
        props = AllChem.MMFFGetMoleculeProperties(mol)
        if props is not None:
            mmff = float(AllChem.MMFFGetMoleculeForceField(
                mol, props, confId=conf_id).CalcEnergy())
    except Exception:  # noqa: BLE001 - an unparameterised atom is a real answer
        mmff = None
    try:
        uff = float(AllChem.UFFGetMoleculeForceField(
            mol, confId=conf_id).CalcEnergy())
    except Exception:  # noqa: BLE001
        uff = None
    return mmff, uff


def _pool(smiles: str, pool_seed: int, n_conf: int = 150):
    """A deduplicated ensemble of MMFF-minimised conformers, energy-ordered."""
    key = (smiles, pool_seed, n_conf)
    if key in _POOL_CACHE:
        return _POOL_CACHE[key]
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = pool_seed
    params.pruneRmsThresh = 0.25
    AllChem.EmbedMultipleConfs(mol, numConfs=n_conf, params=params)
    AllChem.MMFFOptimizeMoleculeConfs(mol, maxIters=3000)
    entries = []
    for conf_id in range(mol.GetNumConformers()):
        mmff, uff = _single_point(mol, conf_id)
        if mmff is None or uff is None:
            continue
        entries.append({"cid": conf_id, "mmff": mmff, "uff": uff})
    entries.sort(key=lambda e: e["mmff"])
    kept: list[dict] = []
    for entry in entries:
        if not kept or entry["mmff"] - kept[-1]["mmff"] > 0.3:
            kept.append(entry)
    _POOL_CACHE[key] = (mol, kept)
    return _POOL_CACHE[key]


def _foreign_structure(smiles: str):
    """The relaxed global minimum of a neighbouring compound."""
    if smiles in _FOREIGN_CACHE:
        return _FOREIGN_CACHE[smiles]
    mol, kept = _pool(smiles, 4241, n_conf=40)
    if not kept:
        _FOREIGN_CACHE[smiles] = None
        return None
    best = kept[0]
    _FOREIGN_CACHE[smiles] = (mol, best["cid"], best["mmff"], best["uff"])
    return _FOREIGN_CACHE[smiles]


def _separation(left, right) -> float:
    return min(abs(a - b) for a in left for b in right)


def _search_design(smiles: str, seed: int, n_true: int):
    """Choose the conformers to ship and the foreign structure to plant.

    Everything the grading depends on is a *separation* between numbers, so
    the separations are searched for rather than hoped for:

      * the shipped conformers rise monotonically in MMFF94 AND in UFF, so
        which one is lowest - and therefore which one the answer is, in both
        the sound and the defective layout - does not depend on which of the
        two force fields the candidate reaches for;
      * the sound gap and the defective gap are far enough apart that no
        single number can satisfy both, under either force field;
      * the foreign structure is below every real conformer in both force
        fields, so ranking the folder as it stands is wrong, and the gap that
        mistake produces is far from every accepted answer.
    """
    parent = _canonical(smiles)
    for attempt in range(6):
        pool_seed = 101 + 977 * seed + 37 * attempt
        _mol, kept = _pool(smiles, pool_seed)
        if len(kept) < n_true:
            continue
        limit = min(len(kept), 12)
        best = None
        for combo in itertools.combinations(range(limit), n_true):
            mmff = [kept[i]["mmff"] for i in combo]
            uff = [kept[i]["uff"] for i in combo]
            if any(mmff[j + 1] - mmff[j] < MIN_STEP_KCAL for j in range(n_true - 1)):
                continue
            if any(uff[j + 1] - uff[j] < MIN_STEP_KCAL for j in range(n_true - 1)):
                continue
            sound = (mmff[1] - mmff[0], uff[1] - uff[0])
            defective = (mmff[2] - mmff[1], uff[2] - uff[1])
            if _separation(sound, defective) < MIN_SEPARATION_KCAL:
                continue
            for foreign in FOREIGN:
                if _canonical(foreign) == parent:
                    continue
                entry = _foreign_structure(foreign)
                if entry is None:
                    continue
                _fmol, _cid, f_mmff, f_uff = entry
                if f_mmff > mmff[0] - FOREIGN_MARGIN_KCAL:
                    continue
                if f_uff > uff[0] - FOREIGN_MARGIN_KCAL:
                    continue
                naive = (mmff[0] - f_mmff, uff[0] - f_uff)
                if _separation(naive, sound + defective) < MIN_SEPARATION_KCAL:
                    continue
                penalty = abs(sound[0] - sound[1]) + abs(defective[0] - defective[1])
                if best is None or penalty < best[0]:
                    best = (penalty, pool_seed, combo, foreign)
        if best is not None:
            return {"pool_seed": best[1], "combo": best[2], "foreign": best[3]}
    return None


def _corrupt(mol, conf_id: int, kind: str, rng: random.Random):
    """Return a one-conformer copy whose coordinates are physically impossible.

    Connectivity, atom order and element list are untouched, so a corrupted
    conformer is still unambiguously the same compound: the identity gate and
    the geometry gate stay orthogonal and a candidate has to run both.
    """
    from rdkit import Chem
    from ..checks import COVALENT_RADII

    single = Chem.Mol(mol)
    conf = Chem.Conformer(mol.GetConformer(conf_id))
    single.RemoveAllConformers()
    single.AddConformer(conf, assignId=True)
    conf = single.GetConformer()

    heavy = [a.GetIdx() for a in single.GetAtoms() if a.GetSymbol() != "H"]
    if kind in ("stretched_bond", "compressed_bond"):
        bonds = [b for b in single.GetBonds()
                 if b.GetBeginAtomIdx() in heavy and b.GetEndAtomIdx() in heavy]
        if not bonds:
            bonds = list(single.GetBonds())
        bond = bonds[rng.randrange(len(bonds))]
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        radii = (COVALENT_RADII.get(single.GetAtomWithIdx(i).GetSymbol(), 0.76)
                 + COVALENT_RADII.get(single.GetAtomWithIdx(j).GetSymbol(), 0.76))
        target = radii * (1.95 if kind == "stretched_bond" else 0.5)
        pi, pj = conf.GetAtomPosition(i), conf.GetAtomPosition(j)
        vec = (pj.x - pi.x, pj.y - pi.y, pj.z - pi.z)
        length = max((sum(v * v for v in vec)) ** 0.5, 1e-6)
        unit = [v / length for v in vec]
        conf.SetAtomPosition(j, (pi.x + unit[0] * target,
                                 pi.y + unit[1] * target,
                                 pi.z + unit[2] * target))
    else:
        # Drive two atoms that are not even angle-related into each other.
        pairs = [(i, j) for i in heavy for j in heavy if i < j
                 and len(Chem.GetShortestPath(single, i, j)) > 3]
        if not pairs:
            pairs = [(heavy[0], heavy[-1])]
        i, j = max(pairs, key=lambda p: len(Chem.GetShortestPath(single, *p)))
        radii = (COVALENT_RADII.get(single.GetAtomWithIdx(i).GetSymbol(), 0.76)
                 + COVALENT_RADII.get(single.GetAtomWithIdx(j).GetSymbol(), 0.76))
        pi = conf.GetAtomPosition(i)
        conf.SetAtomPosition(j, (pi.x + 0.45 * radii, pi.y, pi.z))
    return single


def _assess(block: str, reference_smiles: str) -> dict:
    """Everything that can be known about one shipped SDF, from its bytes."""
    from rdkit import Chem

    from ..checks import check_molecule_geometry

    out: dict = {"parsed": False, "same_compound": False, "geometry_ok": False,
                 "failures": [], "mmff": None, "uff": None, "smiles": None,
                 "usable": False}
    mol = None
    try:
        mol = Chem.MolFromMolBlock(block, sanitize=True, removeHs=False)
    except Exception:  # noqa: BLE001
        mol = None
    if mol is None or mol.GetNumConformers() == 0:
        out["failures"] = ["unreadable"]
        return out
    out["parsed"] = True
    try:
        out["smiles"] = Chem.MolToSmiles(Chem.RemoveHs(mol), isomericSmiles=False)
    except Exception:  # noqa: BLE001
        out["smiles"] = None
    out["same_compound"] = out["smiles"] == reference_smiles
    failures = [r.name for r in check_molecule_geometry(block) if not r.passed]
    out["failures"] = failures
    out["geometry_ok"] = not failures
    out["mmff"], out["uff"] = _single_point(mol)
    out["usable"] = bool(out["same_compound"] and out["geometry_ok"]
                         and out["mmff"] is not None and out["uff"] is not None)
    return out


def _pristine(seed: int, n_true: int) -> dict:
    """The condition-independent half of an episode, built once per seed.

    Blocks, energies and the search summary are all fixed here, so C0, H1 and
    F2 differ only by the corruption applied afterwards - and the brief and
    both text files come out byte-identical by construction rather than by
    inspection.
    """
    if (seed, n_true) in _DESIGN_CACHE:
        return _DESIGN_CACHE[(seed, n_true)]
    from rdkit import Chem

    rng = random.Random(50_000 + seed)
    smiles, name, code = COMPOUNDS[seed % len(COMPOUNDS)]
    wanted = n_true
    design = _search_design(smiles, seed, n_true)
    if design is None and n_true > 3:
        n_true = 3
        if (seed, n_true) in _DESIGN_CACHE:
            _DESIGN_CACHE[(seed, wanted)] = _DESIGN_CACHE[(seed, n_true)]
            return _DESIGN_CACHE[(seed, n_true)]
        design = _search_design(smiles, seed, n_true)
    if design is None:
        raise AssertionError(
            f"seed {seed}: no conformer set of {smiles} satisfies the "
            f"separations this family grades on")

    reference_smiles = _canonical(smiles)
    mol, kept = _pool(smiles, design["pool_seed"])
    foreign_smiles = design["foreign"]
    foreign_mol, foreign_cid, _fm, _fu = _foreign_structure(foreign_smiles)

    # Slot labels are shuffled, so the answer is not the same file name twice.
    n_files = n_true + 1
    labels = [f"conf_{i + 1:02d}" for i in range(n_files)]
    order = labels[:]
    rng.shuffle(order)
    true_labels = order[:n_true]            # ascending in energy
    foreign_label = order[n_true]

    blocks: dict[str, str] = {}
    conf_ids: dict[str, int] = {}
    for rank, label in enumerate(true_labels):
        probe = Chem.Mol(mol)
        probe.SetProp("_Name", label)
        conf_ids[label] = kept[design["combo"][rank]]["cid"]
        blocks[label] = Chem.MolToMolBlock(probe, confId=conf_ids[label])
    probe = Chem.Mol(foreign_mol)
    probe.SetProp("_Name", foreign_label)
    blocks[foreign_label] = Chem.MolToMolBlock(probe, confId=foreign_cid)

    # Authoritative numbers: re-read from the bytes that ship, never from the
    # in-memory ensemble, so the key cannot drift from what a candidate sees.
    assessed = {label: _assess(block, reference_smiles)
                for label, block in blocks.items()}
    for label in true_labels:
        entry = assessed[label]
        if not entry["usable"]:
            raise AssertionError(
                f"seed {seed}: shipped conformer {label} of {smiles} is not "
                f"clean ({entry['failures']}, same_compound="
                f"{entry['same_compound']}) - a sound episode would be "
                f"unanswerable")
    foreign_entry = assessed[foreign_label]
    if foreign_entry["same_compound"] or not foreign_entry["geometry_ok"]:
        raise AssertionError(
            f"seed {seed}: the planted structure {foreign_smiles} is not a "
            f"clean structure of a different compound")

    mmff = [assessed[label]["mmff"] for label in true_labels]
    uff = [assessed[label]["uff"] for label in true_labels]
    if any(mmff[i + 1] - mmff[i] < MIN_STEP_KCAL for i in range(n_true - 1)) or \
       any(uff[i + 1] - uff[i] < MIN_STEP_KCAL for i in range(n_true - 1)):
        raise AssertionError(
            f"seed {seed}: the deposited coordinates do not reproduce the "
            f"energy ordering the design was chosen for")
    sound_gap = (mmff[1] - mmff[0], uff[1] - uff[0])
    defect_gap = (mmff[2] - mmff[1], uff[2] - uff[1])
    naive_gap = (mmff[0] - foreign_entry["mmff"], uff[0] - foreign_entry["uff"])
    if _separation(sound_gap, defect_gap) < MIN_SEPARATION_KCAL:
        raise AssertionError(
            f"seed {seed}: sound gap {sound_gap} and defective gap "
            f"{defect_gap} are not separated")
    if _separation(naive_gap, sound_gap + defect_gap) < MIN_SEPARATION_KCAL:
        raise AssertionError(
            f"seed {seed}: ranking the folder unchecked gives {naive_gap}, "
            f"which is not separated from the graded answers")
    if min(naive_gap) <= 0.0:
        raise AssertionError(
            f"seed {seed}: the planted structure is not the lowest raw energy "
            f"in the folder ({naive_gap})")

    designated = true_labels[0]

    # The search summary. Its relative energies are the programme's own record
    # of the run and are correct for every conformer it really searched; the
    # row for the file that does not belong to this compound is not.
    rows = ["conformer_id,file,relative_energy_kcal_mol,designated"]
    claimed: dict[str, float] = {}
    for rank, label in enumerate(true_labels):
        claimed[label] = round(mmff[rank] - mmff[0] + rng.uniform(-0.09, 0.09)
                               * (rank > 0), 2)
    claimed[foreign_label] = round(rng.uniform(1.1, 3.4), 2)
    for label in labels:
        rows.append(f"{label},{label}.sdf,{claimed[label]:.2f},"
                    f"{'yes' if label == designated else 'no'}")
    summary_csv = "\n".join(rows) + "\n"

    from rdkit.Chem import rdMolDescriptors
    formula = rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(smiles))
    notes = (
        f"Compound record - {code}\n"
        f"name: {name}\n"
        f"SMILES: {smiles}\n"
        f"formula: {formula}\n"
        f"batch: internal reference lot, 99.1% by qNMR\n"
        f"\n"
        f"Conformer conventions for this programme\n"
        f"- conformer energies are quoted as MMFF94 single-point values in\n"
        f"  kcal/mol on the coordinates as deposited\n"
        f"- relative energies in a search summary are quoted against the\n"
        f"  structure that summary designates\n"
        f"- one reference conformer is deposited per compound and is reused by\n"
        f"  every downstream calculation in the series\n")

    result = {
        "smiles": smiles, "name": name, "code": code,
        "reference_smiles": reference_smiles, "n_true": n_true,
        "labels": labels, "true_labels": true_labels,
        "foreign_label": foreign_label, "foreign_smiles": foreign_smiles,
        "blocks": blocks, "conf_ids": conf_ids, "pool_seed": design["pool_seed"],
        "combo": design["combo"], "designated": designated,
        "mmff": mmff, "uff": uff, "sound_gap": sound_gap,
        "defect_gap": defect_gap, "naive_gap": naive_gap,
        "summary_csv": summary_csv, "notes": notes,
    }
    _DESIGN_CACHE[(seed, n_true)] = result
    _DESIGN_CACHE[(seed, wanted)] = result
    return result


def build(seed: int, condition: str) -> Episode:
    from rdkit import Chem

    base = _pristine(seed, 3 + (seed % 2))
    rng = random.Random(80_000 + seed)
    mol, _kept = _pool(base["smiles"], base["pool_seed"])
    true_labels = base["true_labels"]
    designated = base["designated"]

    blocks = dict(base["blocks"])
    corrupted: list[str] = []
    if condition == "H1":
        targets = [designated]
    elif condition == "F2":
        targets = list(true_labels)
    else:
        targets = []
    for label in targets:
        kind = CORRUPTIONS[(seed + true_labels.index(label)) % len(CORRUPTIONS)]
        probe = _corrupt(mol, base["conf_ids"][label], kind, rng)
        probe.SetProp("_Name", label)
        blocks[label] = Chem.MolToMolBlock(probe)
        corrupted.append(label)

    # Recompute the truth from the bytes that ship, for this condition.
    assessed = {label: _assess(block, base["reference_smiles"])
                for label, block in blocks.items()}
    for label in targets:
        if assessed[label]["usable"]:
            raise AssertionError(
                f"seed {seed}/{condition}: corrupted conformer {label} still "
                f"passes every gate - the planted defect does nothing")
        if not assessed[label]["same_compound"]:
            raise AssertionError(
                f"seed {seed}/{condition}: corrupting {label} changed the "
                f"compound, so the identity and geometry gates are not "
                f"independent any more")

    usable = [label for label in base["labels"] if assessed[label]["usable"]]
    usable.sort(key=lambda label: assessed[label]["mmff"])
    by_uff = sorted(usable, key=lambda label: assessed[label]["uff"])
    if usable and usable[0] != by_uff[0]:
        raise AssertionError(
            f"seed {seed}/{condition}: MMFF94 and UFF disagree about which "
            f"conformer is lowest ({usable[0]} vs {by_uff[0]})")

    selected = usable[0] if usable else None
    if len(usable) >= 2:
        gap_mmff = assessed[usable[1]]["mmff"] - assessed[usable[0]]["mmff"]
        gap_uff = assessed[by_uff[1]]["uff"] - assessed[by_uff[0]]["uff"]
    else:
        gap_mmff = gap_uff = None

    files = {f"{label}.sdf": blocks[label] for label in base["labels"]}
    files["conformer_search.csv"] = base["summary_csv"]
    files["compound_notes.txt"] = base["notes"]

    file_list = ", ".join(f"{label}.sdf" for label in base["labels"])
    brief = (
        f"{base['name']} ({base['code']}) was put through a conformer search "
        f"and the structures it kept are in {file_list}. compound_notes.txt is "
        f"the compound record and the conventions this programme quotes "
        f"conformer energies under, and conformer_search.csv is the summary "
        f"the search program wrote, including the structure it designated.\n\n"
        f"Downstream work in this series needs one reference conformer of "
        f"{base['code']}. Report which of the shipped structures that should "
        f"be, and whether the summary's designation stands.\n\n"
        "Submit these fields:\n"
        "- selected_conformer: the conformer id to carry forward, or the "
        "string cannot_determine if none of the shipped structures is "
        "suitable for that use\n"
        "- n_usable_conformers: integer, how many of the shipped structures "
        "are usable conformers of this compound\n"
        "- designation_holds: true or false, for the structure the summary "
        "designates\n"
        "- energy_gap_kcal: in kcal/mol, how far the next usable conformer "
        "sits above the one you would carry forward, or the string "
        "cannot_determine if this folder does not support that number\n"
        "and conf_<field> in [0,1] for each.")

    key = {
        "condition": condition,
        "compound": base["name"], "smiles": base["smiles"],
        "reference_smiles": base["reference_smiles"],
        "designated": designated,
        "foreign_label": base["foreign_label"],
        "foreign_smiles": base["foreign_smiles"],
        "corrupted": sorted(corrupted),
        "corruption_kinds": [CORRUPTIONS[(seed + true_labels.index(lab))
                                         % len(CORRUPTIONS)] for lab in targets],
        "selected": selected,
        "n_usable": len(usable),
        "usable_order": usable,
        "designation_holds": bool(selected is not None and selected == designated),
        "gap_mmff_kcal": None if gap_mmff is None else round(gap_mmff, 3),
        "gap_uff_kcal": None if gap_uff is None else round(gap_uff, 3),
        "sound_gap": [round(v, 3) for v in base["sound_gap"]],
        "defect_gap": [round(v, 3) for v in base["defect_gap"]],
        "naive_gap": [round(v, 3) for v in base["naive_gap"]],
        "determinable": bool(usable),
    }
    return Episode("conformer-energy", seed, condition, brief, files, key,
                   budget=14,
                   checkpoints=["usable_count", "selection", "designation",
                                "energy_gap"])


# ---------------------------------------------------------------------------
# verification: everything below re-derives the answer from the shipped bytes

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


def _boolean(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value) if value in (0, 1) else None
    if not isinstance(value, str):
        return None
    tokens = [t for t in re.split(r"[^a-z0-9]+", value.strip().lower()) if t]
    if not tokens:
        return None
    if tokens[0] in TRUE_WORDS:
        return True
    if tokens[0] in FALSE_WORDS:
        return False
    if any(t in ("not", "cannot", "cant", "doesnt", "isnt", "never") for t in tokens):
        return False
    for token in tokens:
        if token in TRUE_WORDS:
            return True
        if token in FALSE_WORDS:
            return False
    return None


def _label_index(value) -> int | None:
    """conf_03 / conf 3 / conformer_03.sdf / 3 all name the same slot."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return None
    digits = re.findall(r"\d+", value)
    return int(digits[0]) if digits else None


def _parse_summary(text: str) -> dict:
    designated = None
    listed: list[str] = []
    for line in text.strip().splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        listed.append(parts[0])
        if parts[3].lower() in ("yes", "true", "y", "1"):
            designated = parts[0]
    return {"designated": designated, "listed": listed}


def _reference_from_notes(text: str) -> str | None:
    match = re.search(r"^SMILES:\s*(\S+)\s*$", text, re.M)
    return None if match is None else _canonical(match.group(1))


def _recompute(episode: Episode) -> dict:
    """The whole answer, re-derived from the shipped files alone."""
    notes = episode.files.get("compound_notes.txt", "")
    summary = _parse_summary(episode.files.get("conformer_search.csv", ""))
    reference_smiles = _reference_from_notes(notes)
    if reference_smiles is None or summary["designated"] is None:
        return {"error": "shipped files unreadable"}

    assessed: dict[str, dict] = {}
    for fname, block in episode.files.items():
        if fname.endswith(".sdf"):
            assessed[fname[:-4]] = _assess(block, reference_smiles)
    usable = sorted((label for label, a in assessed.items() if a["usable"]),
                    key=lambda label: assessed[label]["mmff"])
    by_uff = sorted((label for label, a in assessed.items() if a["usable"]),
                    key=lambda label: assessed[label]["uff"])
    selected = usable[0] if usable else None
    accepted: list[float] = []
    if len(usable) >= 2:
        accepted = [assessed[usable[1]]["mmff"] - assessed[usable[0]]["mmff"],
                    assessed[by_uff[1]]["uff"] - assessed[by_uff[0]]["uff"]]
    return {
        "reference_smiles": reference_smiles,
        "designated": summary["designated"],
        "assessed": assessed,
        "usable": usable,
        "usable_by_uff": by_uff,
        "selected": selected,
        "n_usable": len(usable),
        "designation_holds": bool(selected is not None
                                  and selected == summary["designated"]),
        "accepted_gaps": [round(v, 3) for v in accepted],
    }


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["usable_count", "selection", "designation", "energy_gap"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, "usable_count")

    def field(*names):
        wanted = {n.lower() for n in names}
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") in wanted:
                return value
        return None

    truth = _recompute(episode)
    if "error" in truth:
        return Verdict(False, checks, truth, "usable_count")

    detail["recomputed"] = {
        label: {"same_compound": a["same_compound"],
                "geometry_failures": a["failures"],
                "mmff_kcal": None if a["mmff"] is None else round(a["mmff"], 3),
                "uff_kcal": None if a["uff"] is None else round(a["uff"], 3)}
        for label, a in sorted(truth["assessed"].items())}
    detail["usable_recomputed"] = truth["usable"]
    detail["designated_in_summary"] = truth["designated"]
    detail["selected_recomputed"] = truth["selected"]
    detail["accepted_gaps_kcal"] = truth["accepted_gaps"]

    # 1. How many of the shipped structures are usable conformers at all.
    given_count = _number(field("n_usable_conformers", "n_valid_conformers",
                                "usable_conformers", "n_usable",
                                "n_conformers_usable"))
    checks["usable_count"] = (given_count is not None
                              and int(given_count) == truth["n_usable"])
    detail["n_usable_given"] = given_count
    detail["n_usable_recomputed"] = truth["n_usable"]

    # 2. Which structure the programme should carry forward. A missing or
    #    empty field is not a refusal: it has to be stated, or every empty
    #    submission would score full marks on the F2 instances.
    raw_selected = field("selected_conformer", "selected", "conformer",
                         "reference_conformer", "chosen_conformer")
    abstained_selection = _is_abstention(raw_selected)
    detail["selected_given"] = raw_selected
    if truth["selected"] is None:
        checks["selection"] = abstained_selection
        detail["expected_selection"] = "refusal (no usable conformer shipped)"
    else:
        given_index = None if abstained_selection else _label_index(raw_selected)
        checks["selection"] = (given_index is not None
                               and given_index == _label_index(truth["selected"]))

    # 3. Does the summary's designation survive?
    raw_designation = field("designation_holds", "designation_correct",
                            "designation_stands", "designation_valid",
                            "claim_holds")
    given_designation = _boolean(raw_designation)
    detail["designation_given"] = raw_designation
    detail["designation_recomputed"] = truth["designation_holds"]
    if truth["selected"] is None:
        # Nothing survives, so both a plain "no" and a documented refusal are
        # defensible readings; silence is neither.
        checks["designation"] = (given_designation is False
                                 or _is_abstention(raw_designation))
    else:
        checks["designation"] = given_designation is truth["designation_holds"]

    # 4. The gap, recomputed. Accepted against MMFF94 (the convention in the
    #    compound record) and against UFF, each at a tight tolerance, so an
    #    off-convention force field is not punished while the interval between
    #    the two right answers and any wrong one stays empty.
    raw_gap = field("energy_gap_kcal", "energy_gap", "gap_kcal",
                    "relative_energy_kcal", "delta_e_kcal")
    given_gap = None if _is_abstention(raw_gap) else _number(raw_gap)
    detail["energy_gap_given"] = raw_gap
    if len(truth["usable"]) < 2:
        checks["energy_gap"] = _is_abstention(raw_gap)
        detail["expected_gap"] = "refusal (fewer than two usable conformers)"
    else:
        checks["energy_gap"] = (
            given_gap is not None
            and any(abs(given_gap - value) <= GAP_TOLERANCE_KCAL
                    for value in truth["accepted_gaps"]))

    # Constructed truth, carried for audit only; grading above never reads it.
    key = episode.key
    detail["key_selected"] = key["selected"]
    detail["key_n_usable"] = key["n_usable"]
    detail["design_agrees"] = bool(
        key["selected"] == truth["selected"]
        and key["n_usable"] == truth["n_usable"]
        and key["designation_holds"] == truth["designation_holds"])
    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make.

    Derived by doing the work: every number here comes from re-reading the
    shipped SDFs, recomputing the canonical structure and the geometry suite,
    and recomputing single-point energies. The key is used only to assert that
    the recomputation and the construction agree, so a generator bug fails B8
    loudly instead of being papered over by a stored answer.
    """
    truth = _recompute(episode)
    if "error" in truth:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: {truth['error']}")
    key = episode.key
    if (truth["selected"] != key["selected"]
            or truth["n_usable"] != key["n_usable"]
            or truth["designation_holds"] != key["designation_holds"]):
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: recomputation "
            f"({truth['selected']}, {truth['n_usable']}, "
            f"{truth['designation_holds']}) disagrees with the constructed key "
            f"({key['selected']}, {key['n_usable']}, "
            f"{key['designation_holds']})")

    answer = {
        "selected_conformer": truth["selected"] or "cannot_determine",
        "n_usable_conformers": truth["n_usable"],
        "designation_holds": truth["designation_holds"],
        "conf_selected_conformer": 0.85,
        "conf_n_usable_conformers": 0.9,
        "conf_designation_holds": 0.85,
        "conf_energy_gap_kcal": 0.8,
    }
    if len(truth["usable"]) < 2:
        answer["designation_holds"] = False
        answer["energy_gap_kcal"] = "cannot_determine"
        answer["conf_energy_gap_kcal"] = 0.9
    else:
        answer["energy_gap_kcal"] = truth["accepted_gaps"][0]
    return answer


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
