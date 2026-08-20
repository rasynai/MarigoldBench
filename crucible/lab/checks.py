"""Recomputed physical and statistical checks.

The benchmark never trusts a submitted number; it re-derives the finding from
the submitted artifact (GOAL.md bar B2). These are the re-derivations.

The geometry suite follows the PoseBusters result that a pose can be excellent
on the metric everyone reports and still be physically impossible: DiffDock
reaches 38% at RMSD <= 2 A but only 12% when validity is required as well, and
0.92% on targets far from its training distribution. Conjunction is the
difficulty engine, so each check is orthogonal and reported separately.

Every check that gates a task must have a MEASURED false-alarm rate on
known-good inputs (`false_alarm_rate` below). A check whose false-alarm rate
is unknown cannot support a clean-control condition, because a model's false
alarm is then indistinguishable from the check's.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

# Covalent radii (A) for the elements a small molecule realistically contains.
COVALENT_RADII = {
    "H": 0.31, "B": 0.84, "C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57,
    "Si": 1.11, "P": 1.07, "S": 1.05, "Cl": 1.02, "Br": 1.20, "I": 1.39,
}
BOND_TOLERANCE = 0.25        # fraction; a bond >25% off its covalent sum is broken
CLASH_FACTOR = 0.75          # non-bonded atoms closer than 0.75*(r1+r2) clash
PLANARITY_TOLERANCE = 0.25   # A, max deviation from the plane of an aromatic ring
ENERGY_RATIO_LIMIT = 100.0   # UFF energy vs relaxed ensemble


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    value: Any = None

    def as_dict(self) -> dict:
        return {"check": self.name, "passed": self.passed,
                "detail": self.detail, "value": self.value}


def _distance(a, b) -> float:
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))


def check_molecule_geometry(mol_block: str) -> list[CheckResult]:
    """Physical validity of a 3D small-molecule pose, from the artifact alone."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    results: list[CheckResult] = []
    mol = Chem.MolFromMolBlock(mol_block, sanitize=False, removeHs=False)
    if mol is None:
        return [CheckResult("parseable", False, "molblock could not be parsed")]
    results.append(CheckResult("parseable", True, "molblock parsed"))

    try:
        Chem.SanitizeMol(mol)
        results.append(CheckResult("sanitizable", True, "valences and aromaticity consistent"))
    except Exception as exc:  # noqa: BLE001
        results.append(CheckResult("sanitizable", False, f"sanitization failed: {exc}"))
        return results

    if mol.GetNumConformers() == 0:
        results.append(CheckResult("has_3d", False, "no conformer"))
        return results
    conf = mol.GetConformer()
    results.append(CheckResult("has_3d", True, f"{mol.GetNumAtoms()} atoms"))

    # 1. bond lengths against covalent radii
    worst_bond, worst_ratio = None, 1.0
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtom(), bond.GetEndAtom()
        ri = COVALENT_RADII.get(i.GetSymbol())
        rj = COVALENT_RADII.get(j.GetSymbol())
        if ri is None or rj is None:
            continue
        expected = ri + rj
        actual = _distance(conf.GetAtomPosition(i.GetIdx()),
                           conf.GetAtomPosition(j.GetIdx()))
        ratio = actual / expected if expected else 1.0
        if abs(ratio - 1.0) > abs(worst_ratio - 1.0):
            worst_ratio, worst_bond = ratio, f"{i.GetSymbol()}{i.GetIdx()}-{j.GetSymbol()}{j.GetIdx()}"
    ok = abs(worst_ratio - 1.0) <= BOND_TOLERANCE
    results.append(CheckResult(
        "bond_lengths", ok,
        f"worst bond {worst_bond} at {100 * (worst_ratio - 1):+.0f}% of covalent sum"
        f" (limit +/-{100 * BOND_TOLERANCE:.0f}%)", round(worst_ratio, 3)))

    # 2. internal steric clashes between atoms not bonded or 1-3 related
    clash = None
    n = mol.GetNumAtoms()
    for i in range(n):
        for j in range(i + 1, n):
            path = Chem.GetShortestPath(mol, i, j)
            if len(path) and len(path) <= 3:      # bonded or angle-related
                continue
            ai, aj = mol.GetAtomWithIdx(i), mol.GetAtomWithIdx(j)
            ri = COVALENT_RADII.get(ai.GetSymbol())
            rj = COVALENT_RADII.get(aj.GetSymbol())
            if ri is None or rj is None:
                continue
            d = _distance(conf.GetAtomPosition(i), conf.GetAtomPosition(j))
            if d < CLASH_FACTOR * (ri + rj):
                clash = (f"{ai.GetSymbol()}{i}-{aj.GetSymbol()}{j} at {d:.2f} A"
                         f" (< {CLASH_FACTOR:.2f} x {ri + rj:.2f})")
                break
        if clash:
            break
    results.append(CheckResult("no_internal_clash", clash is None,
                               clash or "no non-bonded pair below the clash threshold"))

    # 3. aromatic ring planarity
    worst_plane, worst_dev = None, 0.0
    for ring in mol.GetRingInfo().AtomRings():
        if not all(mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring):
            continue
        points = [conf.GetAtomPosition(idx) for idx in ring]
        cx = sum(p.x for p in points) / len(points)
        cy = sum(p.y for p in points) / len(points)
        cz = sum(p.z for p in points) / len(points)
        # plane normal from the first three ring atoms
        (p0, p1, p2) = points[0], points[1], points[2]
        u = (p1.x - p0.x, p1.y - p0.y, p1.z - p0.z)
        v = (p2.x - p0.x, p2.y - p0.y, p2.z - p0.z)
        nx, ny, nz = (u[1] * v[2] - u[2] * v[1],
                      u[2] * v[0] - u[0] * v[2],
                      u[0] * v[1] - u[1] * v[0])
        norm = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        for p in points:
            dev = abs((p.x - cx) * nx + (p.y - cy) * ny + (p.z - cz) * nz) / norm
            if dev > worst_dev:
                worst_dev, worst_plane = dev, tuple(ring)
    ok = worst_dev <= PLANARITY_TOLERANCE
    results.append(CheckResult(
        "aromatic_planarity", ok,
        f"max out-of-plane deviation {worst_dev:.2f} A"
        f" (limit {PLANARITY_TOLERANCE} A)" + (f" in ring {worst_plane}" if worst_plane else ""),
        round(worst_dev, 3)))

    # 4. internal energy against a relaxed ensemble of the same molecule
    try:
        probe = Chem.Mol(mol)
        pose_energy = _uff_energy(probe)
        relaxed = _relaxed_energy(Chem.MolFromSmiles(Chem.MolToSmiles(mol)))
        ratio = pose_energy / relaxed if relaxed and relaxed > 0 else float("inf")
        ok = ratio <= ENERGY_RATIO_LIMIT
        results.append(CheckResult("internal_energy", ok,
                                   f"UFF energy ratio {ratio:.1f} vs relaxed ensemble"
                                   f" (limit {ENERGY_RATIO_LIMIT:.0f})", round(ratio, 2)))
    except Exception as exc:  # noqa: BLE001
        results.append(CheckResult("internal_energy", True,
                                   f"not evaluated ({type(exc).__name__})"))
    return results


def _uff_energy(mol) -> float:
    from rdkit.Chem import AllChem
    field = AllChem.UFFGetMoleculeForceField(mol)
    return field.CalcEnergy()


def _relaxed_energy(mol, n_conf: int = 8) -> float:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 0xC0FFEE
    AllChem.EmbedMultipleConfs(mol, numConfs=n_conf, params=params)
    energies = []
    for conf_id in range(mol.GetNumConformers()):
        field = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id)
        field.Minimize(maxIts=400)
        energies.append(field.CalcEnergy())
    return min(energies) if energies else 0.0


def check_ligand_protein_clash(mol_block: str, pdb_text: str,
                               factor: float = CLASH_FACTOR) -> CheckResult:
    """Does the ligand interpenetrate the receptor?"""
    from rdkit import Chem
    mol = Chem.MolFromMolBlock(mol_block, sanitize=False, removeHs=False)
    if mol is None or mol.GetNumConformers() == 0:
        return CheckResult("no_protein_clash", False, "ligand pose unreadable")
    conf = mol.GetConformer()
    ligand = [(mol.GetAtomWithIdx(i).GetSymbol(), conf.GetAtomPosition(i))
              for i in range(mol.GetNumAtoms())
              if mol.GetAtomWithIdx(i).GetSymbol() != "H"]
    worst = None
    for line in pdb_text.splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            px, py, pz = float(line[30:38]), float(line[38:46]), float(line[46:54])
        except ValueError:
            continue
        element = (line[76:78].strip() or line[12:16].strip()[:1]).capitalize()
        rp = COVALENT_RADII.get(element)
        if rp is None or element == "H":
            continue
        for symbol, pos in ligand:
            rl = COVALENT_RADII.get(symbol)
            if rl is None:
                continue
            d = math.dist((pos.x, pos.y, pos.z), (px, py, pz))
            if d < factor * (rl + rp):
                worst = f"{symbol} at {d:.2f} A from receptor {element}"
                break
        if worst:
            break
    return CheckResult("no_protein_clash", worst is None,
                       worst or "no ligand-receptor pair below the clash threshold")


def false_alarm_rate(check_fn, known_good: list) -> float:
    """Fraction of known-good artifacts a check wrongly rejects.

    Required before a check may gate a clean-control condition: PoseBusters
    reports 2/85 and 2/308 on experimental structures, and an unmeasured rate
    makes a model's false alarm indistinguishable from the instrument's.
    """
    if not known_good:
        return float("nan")
    failures = 0
    for artifact in known_good:
        results = check_fn(artifact)
        if isinstance(results, CheckResult):
            results = [results]
        if any(not r.passed for r in results):
            failures += 1
    return failures / len(known_good)


# ------------------------------------------------------------ statistics

def scaffold_split(smiles_list: list[str], test_fraction: float = 0.2,
                   seed: int = 0) -> tuple[list[int], list[int]]:
    """Bemis-Murcko scaffold split: the honest split for molecular ML.

    A random split lets near-duplicate analogues straddle train and test and
    inflates held-out performance - the leakage that molecular-ML critiques
    identify as the field's dominant reporting error, and the judgment call a
    model-building task is built around.
    """
    from collections import defaultdict

    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold

    buckets: dict[str, list[int]] = defaultdict(list)
    for index, smiles in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smiles)
        key = "" if mol is None else MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
        buckets[key].append(index)
    groups = sorted(buckets.values(), key=len, reverse=True)
    n_test_target = int(round(test_fraction * len(smiles_list)))
    test: list[int] = []
    train: list[int] = []
    for group in groups:
        if len(test) < n_test_target:
            test += group
        else:
            train += group
    return sorted(train), sorted(test)
