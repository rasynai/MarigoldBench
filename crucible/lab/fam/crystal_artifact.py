"""Family: is a deposited ligand pose a binding event or a lattice accident?

Built to the collaborator critique that killed the first family batch: an
episode with one conspicuous local defect is a recipe, and frontier models
execute recipes. The prescription was several *superficially adequate*
analyses that imply DIFFERENT decisions, plus material that makes exactly one
of them defensible.

The primary observable here is a fragment-bound crystal structure that is
excellent by every metric a structural chemist habitually quotes. The fragment
is buried in a well-packed pocket, its geometry is clean, it does not
interpenetrate the receptor, and the refinement summary reports a high
real-space correlation and an accepted density fit. Every one of those numbers
is equally good in all three conditions, so none of them discriminates - the
same trap as trusting a docking program's own confidence.

Two analyses that a competent model runs, each of which is on its own
sufficient-looking and each of which is wrong on one of the two H1 variants:

  * PROVENANCE. Split the residues lining the fragment by the chain they come
    from and ask which of those chains are together in solution. The deposited
    asymmetric unit holds three copies of the domain; the deposition records
    two biological assemblies, and a pocket whose walls come from chains that
    are never together in solution is a feature of the lattice, not of the
    protein. Which chain shares the assembly with A varies by seed, so the
    strong and popular prior that "A and B are the dimer" is wrong half the
    time and the record has to be read rather than assumed. A model that only
    checks provenance clears the variant where the pocket is honest but the
    density behind the fragment is not.
  * THE DENSITY BEHIND THE MODEL. Occupancy and B-factors say how much of the
    fragment is really there. A model that only checks those clears the
    variant where the fragment is fully occupied and well ordered inside a
    pocket that does not exist in solution.

So the answer requires the conjunction, and neither half is reachable from a
summary table: occupancy and B-factors live in fixed columns of the coordinate
file, and the assembly membership lives in the deposition's own remarks. The
naive-but-competent pipeline - parse every ATOM record, measure the contacts,
note the clean geometry and the accepted density fit - returns "genuine" with
high confidence on both H1 variants and returns a residue list that quietly
includes the lattice neighbour's wall.

C0 is deliberately imperfect where it does not matter: the fragment is
partially occupied (well above the project's floor), its B-factors run warmer
than the pocket, and it does brush one residue of the chain that is not in its
assembly. A model that reads any of that as grounds for rejection has raised a
false alarm and is penalised.

F2 carries an explicit impossibility witness rather than a shortfall in data
quality. The chain that forms half the pocket is reproduced, to 0.000 A, by a
space-group operator of the listed symmetry applied to chain A plus one lattice
translation - so it is a symmetry copy - while the deposition's assembly record
names it as an independent member of the biological unit alongside chain A. A
chain cannot be both: the asymmetric unit is by definition free of chains
related by space-group symmetry. Both readings reproduce every deposited number
exactly - the same coordinates, occupancies, B-factors and R-factors - and they
imply opposite verdicts, so the verdict is not identifiable from the entry. The
generator emits both readings as the witness and the verifier recomputes the
operator image and its RMSD itself.

Two implementation notes that are load-bearing:

  * Verification never re-derives the generator's parameters. It re-parses the
    shipped coordinate files, re-applies the symmetry operators, re-measures
    the contacts and re-averages the occupancy and B-factor columns, then
    decides - and it reads the shipped episode records rather than the
    workspace, so editing the entry cannot make an answer true. A generator
    and verifier that share one wrong assumption agree perfectly and are still
    wrong, so `build` runs the same analysis and refuses to emit an episode
    whose recomputed verdict is not the one the condition intends.
  * Negated phrases are removed by plain literal substring replacement. The
    shared clause splitter in chain/score.py discards any clause containing
    "fails", which is exactly the word a correct answer here uses ("the
    fragment fails the occupancy floor"), and a regex for this once failed
    silently in situ while passing in isolation.
"""
from __future__ import annotations

import math
import random
import re
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "undetermined", "none",
           "n_a", "na", "null", "unknown"}

RECEPTOR_FILE = "receptor.pdb"
LIGAND_PDB = "ligand.pdb"
LIGAND_FILE = "ligand.sdf"
REPORT_FILE = "refinement_report.txt"
NOTES_FILE = "structure_notes.md"


def deposition(files: dict) -> str:
    """The deposited records the verdict rests on, as one block of text.

    The protein and the fragment are split across two files for the mundane
    reason that every physical check on the belt wants a receptor without the
    ligand already in it - handed the whole entry, a clash check compares the
    fragment with itself and reports a 0.00 A contact. Splitting keeps the
    pose-quality bait honest: those checks really do pass, in every condition.
    """
    return files[RECEPTOR_FILE] + files[LIGAND_PDB]

# Project conventions. These are stated in the workspace because a verdict that
# depends on an unstated threshold is a taste judgment, not a finding.
CONTACT_CUTOFF = 8.0          # A, receptor atom to fragment atom
MIN_OCCUPANCY = 0.65
MAX_B_RATIO = 1.60
MIN_ASSEMBLY_FRACTION = 2.0 / 3.0
OPERATOR_RMSD_TOL = 0.05      # A; an exact symmetry copy lands at 0.000

N_RESIDUES = 26               # per chain, C-alpha trace
CHAINS = ("A", "B", "C")
LIGAND_CHAIN = "A"

# Space group P 21 21 2 (#18). Operator 2 is a pure two-fold about z with no
# axial translation, which is what makes an exact symmetry copy placeable
# anywhere in the a/b plane by choice of lattice translation alone.
SPACE_GROUP = "P 21 21 2"
SYMOP_TEXT = ("X,Y,Z", "-X,-Y,Z", "1/2-X,1/2+Y,-Z", "1/2+X,1/2-Y,-Z")


def _symops(a: float, b: float, c: float) -> list[tuple[tuple[int, int, int],
                                                        tuple[float, float, float]]]:
    """The four SMTRY operators of P 21 21 2 in orthogonal Cartesian form."""
    return [
        ((1, 1, 1), (0.0, 0.0, 0.0)),
        ((-1, -1, 1), (0.0, 0.0, 0.0)),
        ((-1, 1, -1), (a / 2.0, b / 2.0, 0.0)),
        ((1, -1, -1), (a / 2.0, b / 2.0, 0.0)),
    ]


ENTRIES = [
    ("8QRT", "HSD17B13 dehydrogenase", "OXIDOREDUCTASE",
     "IND", "indole", "c1ccc2[nH]ccc2c1"),
    ("7ZKM", "NUDT7 hydrolase", "HYDROLASE",
     "INA", "isonicotinamide", "NC(=O)c1ccncc1"),
    ("8FDQ", "PHGDH dehydrogenase", "OXIDOREDUCTASE",
     "BSA", "benzenesulfonamide", "NS(=O)(=O)c1ccccc1"),
    ("7YBN", "SETD2 methyltransferase", "TRANSFERASE",
     "QUI", "quinoline", "c1ccc2ncccc2c1"),
    ("8CLP", "MTH1 hydrolase", "HYDROLASE",
     "CRS", "4-methylphenol", "Cc1ccc(O)cc1"),
    ("7XWD", "KEAP1 kelch domain", "PROTEIN BINDING",
     "BZA", "benzamide", "NC(=O)c1ccccc1"),
]

AA3 = ("MET", "LYS", "VAL", "LEU", "ILE", "SER", "THR", "ASP", "GLU", "ASN",
       "GLN", "ALA", "GLY", "PHE", "TYR", "TRP", "PRO", "HIS", "ARG", "CYS")


# --------------------------------------------------------------- geometry

def _hairpin(n: int) -> list[tuple[float, float, float]]:
    """A C-alpha trace of an antiparallel helical hairpin, centred on origin.

    Composition and realism do not matter; what matters is a compact object
    with a surface groove, so that the fragment can be given a shallow site on
    one chain and a deep one only once a second chain packs against it.
    """
    pts: list[tuple[float, float, float]] = []
    half = n // 2
    for i in range(half):
        th = math.radians(100.0 * i)
        pts.append((2.3 * math.cos(th), 2.3 * math.sin(th), 1.5 * i))
    z_top = 1.5 * (half - 1) + 3.2
    for i in range(n - half):
        th = math.radians(100.0 * i + 40.0)
        pts.append((10.4 + 2.3 * math.cos(th), 2.3 * math.sin(th), z_top - 1.5 * i))
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    cz = sum(p[2] for p in pts) / len(pts)
    return [(p[0] - cx, p[1] - cy, p[2] - cz) for p in pts]


def _euler(ax: float, ay: float, az: float) -> list[list[float]]:
    ca, sa = math.cos(ax), math.sin(ax)
    cb, sb = math.cos(ay), math.sin(ay)
    cc, sc = math.cos(az), math.sin(az)
    return [
        [cb * cc, cc * sa * sb - ca * sc, ca * cc * sb + sa * sc],
        [cb * sc, ca * cc + sa * sb * sc, -cc * sa + ca * sb * sc],
        [-sb, cb * sa, ca * cb],
    ]


def _rotate(points, rot, shift=(0.0, 0.0, 0.0)):
    out = []
    for x, y, z in points:
        out.append((rot[0][0] * x + rot[0][1] * y + rot[0][2] * z + shift[0],
                    rot[1][0] * x + rot[1][1] * y + rot[1][2] * z + shift[1],
                    rot[2][0] * x + rot[2][1] * y + rot[2][2] * z + shift[2]))
    return out


def _translate(points, shift):
    return [(x + shift[0], y + shift[1], z + shift[2]) for x, y, z in points]


def _round3(points):
    return [(round(x, 3), round(y, 3), round(z, 3)) for x, y, z in points]


def _min_distance(a_points, b_points) -> float:
    best = float("inf")
    for ax, ay, az in a_points:
        for bx, by, bz in b_points:
            d = math.dist((ax, ay, az), (bx, by, bz))
            if d < best:
                best = d
    return best


def _contacting(chain_points, ligand_points, cutoff=CONTACT_CUTOFF) -> list[int]:
    """Indices of chain residues within `cutoff` of any fragment atom."""
    hits = []
    for index, residue in enumerate(chain_points):
        for atom in ligand_points:
            if math.dist(residue, atom) <= cutoff:
                hits.append(index)
                break
    return hits


# ------------------------------------------------------------ ligand build

def _fragment(smiles: str, seed: int):
    """A clean 3D fragment. RDKit's own embedding guarantees the geometry
    passes the physical checks, so the pose quality can never be the answer."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise RuntimeError(f"could not embed {smiles}")
    AllChem.UFFOptimizeMolecule(mol, maxIters=600)
    mol = Chem.RemoveHs(mol)
    conf = mol.GetConformer()
    points = [(conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y,
               conf.GetAtomPosition(i).z) for i in range(mol.GetNumAtoms())]
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    cz = sum(p[2] for p in points) / len(points)
    centred = [(p[0] - cx, p[1] - cy, p[2] - cz) for p in points]
    symbols = [a.GetSymbol() for a in mol.GetAtoms()]
    return mol, centred, symbols


def _sdf(mol, points: list[tuple[float, float, float]], name: str) -> str:
    from rdkit import Chem
    from rdkit.Geometry import Point3D

    probe = Chem.Mol(mol)
    conf = probe.GetConformer()
    for index, (x, y, z) in enumerate(points):
        conf.SetAtomPosition(index, Point3D(x, y, z))
    probe.SetProp("_Name", name)
    return Chem.MolToMolBlock(probe) + "$$$$\n"


# --------------------------------------------------------------- pdb write

def _atom_line(record: str, serial: int, name: str, resname: str, chain: str,
               resseq: int, xyz, occ: float, bfac: float, element: str) -> str:
    x, y, z = xyz
    return (f"{record:<6}{serial:>5} {name:<4}{'':1}{resname:>3} {chain:1}"
            f"{resseq:>4}{'':1}   {x:>8.3f}{y:>8.3f}{z:>8.3f}"
            f"{occ:>6.2f}{bfac:>6.2f}          {element:>2}")


def _receptor_pdb(entry: str, target: str, header_class: str, resolution: float,
                  cell: tuple[float, float, float], chain_points: dict,
                  chain_b: dict, residue_start: int, sequence: list[str],
                  assembly_partner: str, lone_chain: str) -> str:
    a, b, c = cell
    dimer = ", ".join(sorted([LIGAND_CHAIN, assembly_partner]))
    lines = [
        f"HEADER    {header_class:<40}14-MAR-24   {entry}",
        f"TITLE     {target.upper()}, ASYMMETRIC UNIT",
        f"REMARK   2 RESOLUTION.    {resolution:.2f} ANGSTROMS.",
        "REMARK 300 BIOMOLECULE: 1, 2",
        "REMARK 300 SEE REMARK 350 FOR THE CHAINS THAT FORM EACH ASSEMBLY.",
        "REMARK 350",
        "REMARK 350 COORDINATES FOR A COMPLETE MULTIMER REPRESENTING THE KNOWN",
        "REMARK 350 BIOLOGICALLY SIGNIFICANT OLIGOMERIZATION STATE CAN BE",
        "REMARK 350 GENERATED BY APPLYING BIOMT TRANSFORMATIONS BELOW.",
        "REMARK 350",
        "REMARK 350 BIOMOLECULE: 1",
        f"REMARK 350 APPLY THE FOLLOWING TO CHAINS: {dimer}",
        "REMARK 350   BIOMT1   1  1.000000  0.000000  0.000000        0.00000",
        "REMARK 350   BIOMT2   1  0.000000  1.000000  0.000000        0.00000",
        "REMARK 350   BIOMT3   1  0.000000  0.000000  1.000000        0.00000",
        "REMARK 350",
        "REMARK 350 BIOMOLECULE: 2",
        f"REMARK 350 APPLY THE FOLLOWING TO CHAINS: {lone_chain}",
        "REMARK 350   BIOMT1   1  1.000000  0.000000  0.000000        0.00000",
        "REMARK 350   BIOMT2   1  0.000000  1.000000  0.000000        0.00000",
        "REMARK 350   BIOMT3   1  0.000000  0.000000  1.000000        0.00000",
        "REMARK 290",
        "REMARK 290 CRYSTALLOGRAPHIC SYMMETRY",
        f"REMARK 290 SYMMETRY OPERATORS FOR SPACE GROUP: {SPACE_GROUP}",
        "REMARK 290      SYMOP   SYMMETRY",
        "REMARK 290     NNNMMM   OPERATOR",
    ]
    for index, text in enumerate(SYMOP_TEXT, start=1):
        lines.append(f"REMARK 290     {index}555   {text}")
    lines += [
        "REMARK 290",
        "REMARK 290 WHERE NNN IS THE OPERATOR NUMBER AND MMM IS A LATTICE",
        "REMARK 290 TRANSLATION IN UNITS OF THE CELL EDGES, 555 BEING NONE.",
    ]
    for index, (diag, shift) in enumerate(_symops(a, b, c), start=1):
        for row in range(3):
            values = [1.0 * diag[row] if col == row else 0.0 for col in range(3)]
            lines.append(
                f"REMARK 290   SMTRY{row + 1}{index:>4}"
                f"{values[0]:>10.6f}{values[1]:>10.6f}{values[2]:>10.6f}"
                f"{shift[row]:>15.5f}")
    lines.append(
        f"CRYST1{a:>9.3f}{b:>9.3f}{c:>9.3f}"
        f"{90.0:>7.2f}{90.0:>7.2f}{90.0:>7.2f} {SPACE_GROUP:<11}{4:>4}")

    serial = 1
    for chain in CHAINS:
        for index, point in enumerate(chain_points[chain]):
            lines.append(_atom_line(
                "ATOM", serial, " CA ", sequence[index], chain,
                residue_start + index, point, 1.0,
                chain_b[chain][index], "C"))
            serial += 1
        lines.append(f"TER   {serial:>5}      {sequence[-1]:>3} {chain}"
                     f"{residue_start + len(chain_points[chain]) - 1:>4}")
        serial += 1
    lines.append("END")
    return "\n".join(lines) + "\n"


def _ligand_pdb(entry: str, cell: tuple[float, float, float], first_serial: int,
                ligand_code: str, ligand_resseq: int, ligand_points,
                ligand_symbols, ligand_occ: float,
                ligand_b: list[float]) -> str:
    a, b, c = cell
    lines = [
        f"REMARK   3 DEPOSITED LIGAND RECORD FOR ENTRY {entry}",
        f"CRYST1{a:>9.3f}{b:>9.3f}{c:>9.3f}"
        f"{90.0:>7.2f}{90.0:>7.2f}{90.0:>7.2f} {SPACE_GROUP:<11}{4:>4}",
    ]
    for index, (point, symbol) in enumerate(zip(ligand_points, ligand_symbols)):
        lines.append(_atom_line("HETATM", first_serial + index,
                                f" {symbol}{index + 1}", ligand_code,
                                LIGAND_CHAIN, ligand_resseq, point,
                                ligand_occ, ligand_b[index], symbol))
    lines.append("END")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------- parsing / analysis
#
# Everything below is used by `build`, by `verify` and by `reference_submission`
# alike: the truth is whatever falls out of re-reading the shipped file, and
# `build` refuses to emit an episode whose recomputation disagrees with the
# condition it was asked for.

def parse_pdb(text: str) -> dict:
    protein: dict[str, dict[int, tuple]] = {}
    protein_b: dict[str, dict[int, float]] = {}
    ligand: list[tuple] = []
    ligand_occ: list[float] = []
    ligand_b: list[float] = []
    ligand_id = (None, None)
    cell = (0.0, 0.0, 0.0)
    for line in text.splitlines():
        if line.startswith("CRYST1"):
            try:
                cell = (float(line[6:15]), float(line[15:24]), float(line[24:33]))
            except ValueError:
                pass
            continue
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            occ = float(line[54:60])
            bfac = float(line[60:66])
        except ValueError:
            continue
        chain = line[21:22].strip()
        try:
            resseq = int(line[22:26])
        except ValueError:
            continue
        if line.startswith("ATOM"):
            protein.setdefault(chain, {})[resseq] = xyz
            protein_b.setdefault(chain, {})[resseq] = bfac
        else:
            ligand.append(xyz)
            ligand_occ.append(occ)
            ligand_b.append(bfac)
            ligand_id = (chain, resseq)
    return {"protein": protein, "protein_b": protein_b, "ligand": ligand,
            "ligand_occ": ligand_occ, "ligand_b": ligand_b,
            "ligand_id": ligand_id, "cell": cell}


def parse_assemblies(text: str) -> dict[int, list[str]]:
    """Which chains form each biological assembly, from the deposition record."""
    assemblies: dict[int, list[str]] = {}
    current = None
    for line in text.splitlines():
        if not line.startswith("REMARK 350"):
            continue
        body = line[10:].strip()
        match = re.match(r"BIOMOLECULE:\s*(\d+)\s*$", body)
        if match:
            current = int(match.group(1))
            continue
        if current is not None and body.upper().startswith("APPLY THE FOLLOWING TO CHAINS:"):
            chains = body.split(":", 1)[1]
            assemblies[current] = [c.strip().upper() for c in chains.split(",")
                                   if c.strip()]
    return assemblies


def parse_symops(text: str) -> list[tuple[list[list[float]], list[float]]]:
    """The SMTRY rows of REMARK 290, as (rotation, translation) pairs."""
    rows: dict[int, dict[int, tuple[list[float], float]]] = {}
    for line in text.splitlines():
        match = re.match(r"REMARK 290\s+SMTRY(\d)\s+(\d+)\s+(.*)$", line)
        if not match:
            continue
        row, index = int(match.group(1)), int(match.group(2))
        numbers = [float(v) for v in match.group(3).split()]
        if len(numbers) < 4:
            continue
        rows.setdefault(index, {})[row] = (numbers[:3], numbers[3])
    operators = []
    for index in sorted(rows):
        block = rows[index]
        if set(block) != {1, 2, 3}:
            continue
        rot = [block[r][0] for r in (1, 2, 3)]
        shift = [block[r][1] for r in (1, 2, 3)]
        # A malformed REMARK line yields a short row, and indexing it later
        # raised "'int' object is not subscriptable" mid-campaign - a verifier
        # crash, which is a harness failure rather than a measurement. Reject
        # the operator here instead.
        if any(not isinstance(r, (list, tuple)) or len(r) != 3 for r in rot):
            continue
        if any(not isinstance(v, (int, float)) for v in shift):
            continue
        operators.append((rot, shift))
    return operators


def _image(points: dict[int, tuple], rot, shift, lattice) -> dict[int, tuple]:
    out = {}
    for resseq, (x, y, z) in points.items():
        out[resseq] = (
            rot[0][0] * x + rot[0][1] * y + rot[0][2] * z + shift[0] + lattice[0],
            rot[1][0] * x + rot[1][1] * y + rot[1][2] * z + shift[1] + lattice[1],
            rot[2][0] * x + rot[2][1] * y + rot[2][2] * z + shift[2] + lattice[2])
    return out


def _rmsd(left: dict[int, tuple], right: dict[int, tuple]) -> float:
    shared = sorted(set(left) & set(right))
    if not shared:
        return float("inf")
    total = sum(math.dist(left[r], right[r]) ** 2 for r in shared)
    return math.sqrt(total / len(shared))


def find_symmetry_duplicates(text: str) -> list[dict]:
    """Pairs of deposited chains related by a listed space-group operator.

    The asymmetric unit is by definition free of such pairs, so a hit is an
    internal inconsistency in the entry rather than a fact about the protein.
    """
    parsed = parse_pdb(text)
    a, b, c = parsed["cell"]
    operators = parse_symops(text)
    chains = sorted(parsed["protein"])
    found = []
    for source in chains:
        for target in chains:
            if source == target:
                continue
            best = (float("inf"), None, None)
            for index, (rot, shift) in enumerate(operators, start=1):
                for i in (-1, 0, 1):
                    for j in (-1, 0, 1):
                        for k in (-1, 0, 1):
                            lattice = (i * a, j * b, k * c)
                            if index == 1 and (i, j, k) == (0, 0, 0):
                                continue
                            image = _image(parsed["protein"][source], rot, shift,
                                           lattice)
                            value = _rmsd(image, parsed["protein"][target])
                            if value < best[0]:
                                best = (value, index, (i, j, k))
            if best[0] <= OPERATOR_RMSD_TOL:
                found.append({"source": source, "duplicate": target,
                              "operator": best[1], "lattice": list(best[2]),
                              "rmsd": round(best[0], 4)})
    return found


def analyse(text: str) -> dict:
    """Everything the verdict rests on, recomputed from the coordinate file."""
    parsed = parse_pdb(text)
    assemblies = parse_assemblies(text)
    ligand = parsed["ligand"]
    ligand_chain = parsed["ligand_id"][0]

    lining_all: list[str] = []
    lining_b: list[float] = []
    for chain in sorted(parsed["protein"]):
        for resseq, point in sorted(parsed["protein"][chain].items()):
            if any(math.dist(point, atom) <= CONTACT_CUTOFF for atom in ligand):
                lining_all.append(f"{chain}:{resseq}")
                lining_b.append(parsed["protein_b"][chain][resseq])

    together = set()
    for chains in assemblies.values():
        if ligand_chain in chains:
            together |= set(chains)
    if not together:
        together = {ligand_chain}
    lining_assembly = [r for r in lining_all if r.split(":")[0] in together]

    occupancy = (sum(parsed["ligand_occ"]) / len(parsed["ligand_occ"])
                 if parsed["ligand_occ"] else 0.0)
    ligand_b_mean = (sum(parsed["ligand_b"]) / len(parsed["ligand_b"])
                     if parsed["ligand_b"] else 0.0)
    pocket_b_mean = sum(lining_b) / len(lining_b) if lining_b else 0.0
    b_ratio = ligand_b_mean / pocket_b_mean if pocket_b_mean else float("inf")
    fraction = len(lining_assembly) / len(lining_all) if lining_all else 0.0

    duplicates = find_symmetry_duplicates(text)
    contradiction = next(
        (d for d in duplicates
         if d["source"] in together and d["duplicate"] in together), None)

    reasons = []
    if fraction < MIN_ASSEMBLY_FRACTION:
        reasons.append("packing")
    if occupancy < MIN_OCCUPANCY or b_ratio > MAX_B_RATIO:
        reasons.append("disorder")

    if contradiction is not None:
        verdict, mechanism = "cannot_determine", "record"
    elif reasons:
        verdict, mechanism = "artifact", reasons[0]
    else:
        verdict, mechanism = "genuine", None

    return {
        "lining_all": lining_all,
        "lining_assembly": lining_assembly,
        "assembly_chains": sorted(together),
        "assembly_fraction": round(fraction, 4),
        "ligand_occupancy": round(occupancy, 4),
        "ligand_b_mean": round(ligand_b_mean, 3),
        "pocket_b_mean": round(pocket_b_mean, 3),
        "b_ratio": round(b_ratio, 4),
        "duplicates": duplicates,
        "contradiction": contradiction,
        "reasons": reasons,
        "verdict": verdict,
        "mechanism": mechanism,
    }


# ------------------------------------------------------------------- build

def _place(rng: random.Random, condition: str, fragment_points):
    """Lay out three domain copies and the fragment.

    Chain A gives the fragment a shallow surface site; a second chain packs
    against it and completes the pocket; the third only brushes it. Which of
    the two non-A chains is the pocket wall is the whole of the H1 packing
    variant, and because the chains are otherwise interchangeable the two
    conditions differ only in coordinates.
    """
    base = _hairpin(N_RESIDUES)

    # Cell edges are multiples of 0.5 A so that half-cell operator shifts and
    # lattice translations stay exactly representable at PDB precision - the
    # F2 witness has to land on 0.000, not on 0.0004.
    cell_a = round(rng.randrange(116, 169) * 0.5, 3)
    cell_b = round(rng.randrange(92, 125) * 0.5, 3)
    cell_c = round(rng.randrange(104, 145) * 0.5, 3)

    # The fragment sits out on the +y face of chain A. Push it out until chain
    # A alone lines it with only a handful of residues.
    fragment_rot = _euler(rng.uniform(0.4, 2.6), rng.uniform(0.4, 2.6),
                          rng.uniform(0.4, 2.6))
    fragment_local = _rotate(fragment_points, fragment_rot)
    ligand_offset = None
    for step in range(24):
        offset = (0.0, 6.5 + 0.35 * step, 0.0)
        probe = _translate(fragment_local, offset)
        if 4 <= len(_contacting(base, probe)) <= 6 and _min_distance(base, probe) >= 3.4:
            ligand_offset = offset
            break
    if ligand_offset is None:
        raise RuntimeError("no fragment placement with a shallow single-chain site")
    fragment_local = _translate(fragment_local, ligand_offset)

    # The pocket wall. In F2 its rotation must be the two-fold of operator 2 so
    # that a lattice translation can reproduce it exactly; elsewhere it is a
    # generic non-crystallographic rotation, far from every listed operator.
    if condition == "F2":
        wall_rot = [[-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]]
    else:
        wall_rot = _euler(math.radians(rng.uniform(22, 68)),
                          math.radians(rng.uniform(22, 68)),
                          math.radians(rng.uniform(22, 68)))
    wall_local = _rotate(base, wall_rot)
    wall_offset = None
    for step in range(40):
        for lateral in (0.0, 2.0, -2.0, 4.0, -4.0):
            offset = (lateral, ligand_offset[1] + 4.0 + 0.4 * step, 0.0)
            probe = _translate(wall_local, offset)
            count = len(_contacting(probe, fragment_local))
            if not 6 <= count <= 9:
                continue
            if _min_distance(probe, fragment_local) < 3.4:
                continue
            if _min_distance(probe, base) < 4.2:
                continue
            wall_offset = offset
            break
        if wall_offset is not None:
            break
    if wall_offset is None:
        raise RuntimeError("no pocket-wall placement with the required burial")
    wall_points = _translate(wall_local, wall_offset)

    # The third copy only brushes the fragment: enough that "it touches a chain
    # from another assembly" is true in every condition and therefore useless
    # as a signal on its own.
    edge_rot = _euler(math.radians(rng.uniform(22, 68)),
                      math.radians(rng.uniform(22, 68)),
                      math.radians(rng.uniform(22, 68)))
    edge_local = _rotate(base, edge_rot)
    edge_points = None
    candidates = [(sign * (12.0 + 0.5 * step), ligand_offset[1] + lift, lateral)
                  for step in range(48)
                  for sign in (1.0, -1.0)
                  for lift in (0.0, -3.0, 3.0, -6.0, 6.0, -9.0, 9.0)
                  for lateral in (0.0, 5.0, -5.0, 10.0, -10.0)]
    candidates.sort(key=lambda o: (abs(o[0]), abs(o[1]), abs(o[2])))
    for offset in candidates:
        probe = _translate(edge_local, offset)
        if not 1 <= len(_contacting(probe, fragment_local)) <= 2:
            continue
        if _min_distance(probe, fragment_local) < 3.6:
            continue
        if min(_min_distance(probe, base), _min_distance(probe, wall_points)) < 4.2:
            continue
        edge_points = probe
        break
    if edge_points is None:
        raise RuntimeError("no edge-copy placement with a single brushing contact")

    # Absolute position in the cell. The same formula in every condition; in F2
    # it is also what makes chain A and the wall exact images of one another
    # under operator 2 plus the (1,1,0) lattice translation.
    origin = ((cell_a - wall_offset[0]) / 2.0,
              (cell_b - wall_offset[1]) / 2.0,
              cell_c / 2.0)
    return {
        "cell": (cell_a, cell_b, cell_c),
        "chain_a": _round3(_translate(base, origin)),
        "wall": _round3(_translate(wall_points, origin)),
        "edge": _round3(_translate(edge_points, origin)),
        "fragment": _round3(_translate(fragment_local, origin)),
    }


def build(seed: int, condition: str) -> Episode:
    rng = random.Random(613_000 + seed)
    entry, target, header_class, code, ligand_name, smiles = \
        ENTRIES[seed % len(ENTRIES)]

    mol, fragment_points, symbols = _fragment(smiles, 4000 + seed)
    layout = _place(rng, condition, fragment_points)
    cell_a, cell_b, cell_c = layout["cell"]

    # Which chain shares the biological unit with A varies by seed. "Chains A
    # and B are the dimer" is a strong prior and a wrong one half the time, so
    # the assembly has to be read out of the entry rather than assumed - and
    # the identity of the pocket wall then carries no information on its own.
    assembly_partner = "C" if (seed // 2) % 2 else "B"
    lone_chain = "B" if assembly_partner == "C" else "C"

    # Packing variant: the wall is the copy the deposition puts in its own
    # assembly, so the pocket does not survive into solution.
    packing_variant = condition == "H1" and seed % 2 == 0
    wall_chain = lone_chain if packing_variant else assembly_partner
    edge_chain = assembly_partner if packing_variant else lone_chain

    chain_points = {"A": layout["chain_a"],
                    wall_chain: layout["wall"],
                    edge_chain: layout["edge"]}

    if condition == "F2":
        # The wall is regenerated from the rounded chain A coordinates through
        # operator 2 of the listed symmetry plus the (1,1,0) lattice
        # translation, so the image lands on the deposited coordinates exactly.
        rot, shift = _symops(cell_a, cell_b, cell_c)[1]
        chain_points[wall_chain] = [
            (round(rot[0] * x + shift[0] + cell_a, 3),
             round(rot[1] * y + shift[1] + cell_b, 3),
             round(rot[2] * z + shift[2], 3))
            for x, y, z in layout["chain_a"]]

    residue_start = 18 + 4 * (seed % 6)
    sequence = [AA3[(seed * 5 + i * 7) % len(AA3)] for i in range(N_RESIDUES)]
    ligand_resseq = 300 + (seed % 5)

    chain_b_factors = {}
    for order, chain in enumerate(CHAINS):
        base_b = 19.0 + 3.4 * order + rng.uniform(-1.5, 1.5)
        chain_b_factors[chain] = [
            round(base_b + 5.5 * math.sin(0.7 * i + order) + rng.uniform(-1.2, 1.2), 2)
            for i in range(N_RESIDUES)]

    # Occupancy and the B-factor ratio. C0 is deliberately imperfect but inside
    # the project's floor and ceiling, so a model that reads partial occupancy
    # as grounds for rejection has raised a false alarm.
    if condition == "H1" and not packing_variant:
        occupancy = round(rng.uniform(0.40, 0.58), 2)
        b_ratio = rng.uniform(2.10, 2.90)
    else:
        occupancy = round(rng.uniform(0.70, 0.95), 2)
        b_ratio = rng.uniform(1.08, 1.40)

    resolution = round(rng.uniform(1.72, 2.18), 2)
    receptor = _receptor_pdb(entry, target, header_class, resolution,
                             layout["cell"], chain_points, chain_b_factors,
                             residue_start, sequence, assembly_partner,
                             lone_chain)
    first_serial = 3 * (N_RESIDUES + 1) + 1

    def ligand_record(bfactors: list[float]) -> str:
        return _ligand_pdb(entry, layout["cell"], first_serial, code,
                           ligand_resseq, layout["fragment"], symbols,
                           occupancy, bfactors)

    # The B-factor target needs the lining set, which needs final coordinates,
    # so a provisional record with flat ligand B-factors is measured first and
    # the real ones are set from what it reports.
    pocket_b_mean = analyse(receptor + ligand_record([20.0] * len(symbols)))[
        "pocket_b_mean"]
    ligand_b = [round(b_ratio * pocket_b_mean + rng.uniform(-1.1, 1.1), 2)
                for _ in symbols]
    ligand_pdb = ligand_record(ligand_b)

    truth = analyse(receptor + ligand_pdb)
    intended = {"C0": "genuine", "H1": "artifact", "F2": "cannot_determine"}[condition]
    if truth["verdict"] != intended:
        raise RuntimeError(
            f"crystal-artifact s{seed}/{condition}: recomputed {truth['verdict']}"
            f" but the condition intends {intended} ({truth['reasons']},"
            f" fraction={truth['assembly_fraction']},"
            f" occ={truth['ligand_occupancy']}, ratio={truth['b_ratio']})")
    if condition == "H1":
        expect = "packing" if packing_variant else "disorder"
        if truth["mechanism"] != expect or len(truth["reasons"]) != 1:
            raise RuntimeError(
                f"crystal-artifact s{seed}/H1: mechanism {truth['mechanism']}"
                f" / reasons {truth['reasons']} but the variant is {expect}")

    all_b = [b for chain in CHAINS for b in chain_b_factors[chain]] + ligand_b
    report = "\n".join([
        f"# refinement and validation summary   entry {entry}",
        f"resolution_A                 {resolution:.2f}",
        f"r_work                       {rng.uniform(0.162, 0.198):.3f}",
        f"r_free                       {rng.uniform(0.204, 0.239):.3f}",
        f"mean_b_all_atoms             {sum(all_b) / len(all_b):.1f}",
        f"ramachandran_favoured_pct    {rng.uniform(96.1, 98.4):.1f}",
        f"clashscore                   {rng.uniform(1.8, 4.6):.1f}",
        f"ligand_id                    {code}",
        f"ligand_rscc                  {rng.uniform(0.87, 0.95):.2f}",
        f"ligand_rsr                   {rng.uniform(0.061, 0.098):.3f}",
        f"ligand_edia                  {rng.uniform(0.78, 0.91):.2f}",
        "ligand_fit_status            accepted",
    ]) + "\n"

    notes = "\n".join([
        f"# Structure notes  {entry}  /  {target}",
        "",
        f"Fragment {code} ({ligand_name}, SMILES {smiles}) is deposited as "
        f"residue {ligand_resseq}",
        f"of chain {LIGAND_CHAIN}; its record is in {LIGAND_PDB} and the same "
        f"coordinates are also",
        f"supplied as {LIGAND_FILE}. The protein coordinates and the entry's "
        f"remarks are in",
        f"{RECEPTOR_FILE}.",
        "",
        f"The asymmetric unit holds three copies of the {N_RESIDUES}-residue "
        "domain, chains A,",
        "B and C, refined under strict non-crystallographic symmetry "
        "restraints. At this",
        "resolution only main-chain C-alpha positions were modelled.",
        "",
        "Contact convention used by this project: a residue lines the fragment "
        "if any of",
        f"its deposited atoms lies within {CONTACT_CUTOFF:.1f} A of any "
        "fragment atom.",
        "",
        "Acceptance rule. A modelled fragment is pursuable only if all of the "
        "following",
        "hold:",
        "  - at least two-thirds of the residues lining it come from chains "
        "that are",
        "    together in solution;",
        f"  - its occupancy is at least {MIN_OCCUPANCY:.2f};",
        f"  - its mean B-factor is no more than {MAX_B_RATIO:.2f} x the mean "
        "B-factor of the",
        "    residues lining it in the deposited coordinates.",
        "A fragment that misses any of these is recorded as an artifact of the "
        "crystal",
        "rather than a binding event to pursue.",
    ]) + "\n"

    brief = (
        f"Entry {entry} for {target} was solved with the fragment "
        f"{ligand_name} bound. The deposited coordinates, the refinement "
        f"summary and the project's structure notes are attached.\n\n"
        f"Report the pocket this fragment sits in and whether the project can "
        f"pursue the binding event the entry shows.\n\n"
        "Submit these fields:\n"
        "- site_verdict: genuine if the modelled fragment satisfies the "
        "acceptance rule in the structure notes, artifact if it does not, or "
        "cannot_determine if the deposited entry does not settle it\n"
        "- pocket_residues: the residues that line the fragment in the form of "
        "the receptor that exists in solution, under the contact convention in "
        "the structure notes, as chain:number pairs separated by commas, or "
        "cannot_determine if no defensible list exists\n"
        "- ligand_occupancy: the occupancy of the modelled fragment, as a "
        "number\n"
        "- site_basis: what your verdict rests on, in your own words\n"
        "and conf_<field> in [0,1] for each.")

    files = {
        RECEPTOR_FILE: receptor,
        LIGAND_PDB: ligand_pdb,
        LIGAND_FILE: _sdf(mol, layout["fragment"], f"{entry}_{code}"),
        REPORT_FILE: report,
        NOTES_FILE: notes,
    }

    witness = None
    if condition == "F2":
        duplicate = truth["contradiction"]
        witness = {
            "operator": SYMOP_TEXT[duplicate["operator"] - 1],
            "operator_index": duplicate["operator"],
            "lattice_translation": duplicate["lattice"],
            "rmsd_to_deposited_chain_A": duplicate["rmsd"],
            "reading_1": {
                "chains_in_solution_with_A": ["A", wall_chain],
                "claim": "the assembly record is right and the wall chain is an "
                         "independent, non-crystallographic partner",
                "assembly_fraction": truth["assembly_fraction"],
                "implied_verdict": "genuine",
            },
            "reading_2": {
                "chains_in_solution_with_A": ["A"],
                "claim": "the coordinates are right and the wall chain is a "
                         "space-group copy deposited in the asymmetric unit "
                         "by mistake",
                "assembly_fraction": round(
                    len([r for r in truth["lining_all"]
                         if r.startswith("A:")]) / len(truth["lining_all"]), 4),
                "implied_verdict": "artifact",
            },
            "why_undecidable": (
                "both readings reproduce every deposited number - the same "
                "coordinates, occupancies, B-factors and R-factors - and they "
                "imply opposite verdicts, so nothing in the entry chooses "
                "between them"),
        }

    key = {
        "condition": condition,
        "entry": entry,
        "target": target,
        "ligand_code": code,
        "wall_chain": wall_chain,
        "edge_chain": edge_chain,
        "assembly_partner": assembly_partner,
        "lone_chain": lone_chain,
        "packing_variant": packing_variant,
        "expected_verdict": truth["verdict"],
        "expected_mechanism": truth["mechanism"],
        "expected_pocket": truth["lining_assembly"],
        "ligand_occupancy": truth["ligand_occupancy"],
        "b_ratio": truth["b_ratio"],
        "assembly_fraction": truth["assembly_fraction"],
        "cell": [cell_a, cell_b, cell_c],
        "witness": witness,
    }
    # 28 calls: read the record, parse the coordinate columns, rebuild the
    # lattice images, measure the contacts, and revise once the first reading
    # of the pocket turns out to depend on which chains are in solution.
    return Episode("crystal-artifact", seed, condition, brief, files, key,
                   budget=28,
                   checkpoints=["pocket", "record_numbers", "verdict", "basis"])


# ------------------------------------------------------------- verification

# Literal phrasings that name a mechanism only to rule it out. Removal is plain
# substring replacement: the shared clause splitter discards any clause holding
# "fails", which is the word a correct answer here needs, and a regex for this
# failed silently in situ once while passing in isolation.
NEGATED = (
    "not a packing artifact", "not a packing artefact", "not packing",
    "no packing", "not a crystal artifact", "not a crystal artefact",
    "not an artifact", "not an artefact", "not a lattice contact",
    "not a lattice artifact", "no lattice contact", "not a crystal contact",
    "no crystal contact", "not a symmetry mate", "not symmetry related",
    "not symmetry-related", "not a crystallographic artifact",
    "rather than a packing artifact", "rather than packing",
    "instead of packing", "rather than a lattice contact",
    "not explained by packing", "not explained by the lattice",
    "not disordered", "not disorder", "no disorder", "not partial occupancy",
    "no partial occupancy", "not low occupancy", "occupancy is not low",
    "not poorly ordered", "not badly ordered", "rather than disorder",
    "instead of disorder", "not a disorder", "not elevated", "not inflated",
    "not genuine", "not a genuine", "not real", "not biologically meaningful",
    "not a binding event", "not undecidable", "not ambiguous",
)

PACKING_WORDS = (
    "packing", "lattice", "crystal contact", "crystallographic contact",
    "symmetry mate", "symmetry-related", "symmetry related", "adjacent copy",
    "neighbouring copy", "neighboring copy", "neighbouring molecule",
    "neighboring molecule", "different assembly", "second assembly",
    "other assembly", "separate assembly", "another assembly",
    "outside the assembly", "not in the same assembly", "different biomolecule",
    "second biomolecule", "another biomolecule", "not together in solution",
    "not in solution", "not present in solution", "does not exist in solution",
    "absent in solution", "only in the crystal", "crystal artifact",
    "crystal artefact",
)

DISORDER_WORDS = (
    "occupanc", "b-factor", "b factor", "bfactor", "b factors",
    "temperature factor", "adp", "disorder", "poorly ordered",
    "partially ordered", "badly ordered", "partial ligand",
)

SOLUTION_GROUNDS = (
    "assembl", "in solution", "together in solution", "solution state",
    "solution form", "biological unit", "biounit", "biomolecule", "dimer",
    "physiolog", "both chains", "same multimer", "multimer",
)

WITNESS_WORDS = (
    "operator", "symop", "smtry", "space group", "space-group", "symmetry mate",
    "symmetry-related", "symmetry related", "symmetry copy", "lattice copy",
    "lattice translation", "duplicat", "same chain twice", "same copy twice",
    "not an independent chain", "not independent", "asymmetric unit",
    "two-fold", "twofold", "screw axis", "crystallographic copy", "crystal copy",
    "unit cell", "exact image", "image of chain", "superpose", "superimpose",
    "rmsd",
)

WITNESS_STAKE = (
    "assembl", "in solution", "together in solution", "solution state",
    "biological unit", "biomolecule", "record", "inconsist", "contradict",
    "cannot be both", "both readings", "two readings", "either reading",
    "two interpretations", "either way", "ambiguous", "not decidable",
    "undecidable", "cannot be decided", "cannot tell whether", "unresolvable",
    "does not settle", "not settled", "does not determine", "self-consistent",
)


def _strip_negated(text: str) -> str:
    lowered = " " + str(text).lower().replace("\n", " ") + " "
    for phrase in NEGATED:
        lowered = lowered.replace(phrase, " ")
    return lowered


ABSTAIN_PHRASES = ("cannot_determine", "cannot determine", "cannot be determined",
                   "not determinable", "not_determinable", "indeterminate",
                   "undecidable", "not decidable", "cannot be decided")


def _abstained(raw) -> bool:
    """A stated refusal, not an absent one.

    Silence is not a refusal: an empty or missing field matches no phrase and
    is not in the token set, so it fails every condition including F2.
    """
    text = str(raw or "").strip().lower()
    if not text:
        return False
    return text in ABSTAIN or any(p in text for p in ABSTAIN_PHRASES)


def _number(raw):
    """The first number in a field. Tolerant of "0.74 (mean over 9 atoms)" and
    intolerant of everything that matters: the value still has to be right."""
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)
    match = re.search(r"[-+]?\d*\.?\d+", str(raw or ""))
    return float(match.group(0)) if match else None


def _residue_set(raw) -> set[str]:
    """Parse `A:23, A 26, B31` into {"A:23", "A:26", "B:31"}."""
    if raw is None:
        return set()
    if isinstance(raw, (list, tuple, set)):
        text = " ".join(str(x) for x in raw)
    else:
        text = str(raw)
    out = set()
    for chain, number in re.findall(r"([A-Za-z])\s*[:/_.\-]?\s*(\d+)", text):
        out.add(f"{chain.upper()}:{int(number)}")
    return out


def _f1(given: set[str], expected: set[str]) -> float:
    if not given or not expected:
        return 0.0
    overlap = len(given & expected)
    if not overlap:
        return 0.0
    precision = overlap / len(given)
    recall = overlap / len(expected)
    return 2 * precision * recall / (precision + recall)


POCKET_F1_FLOOR = 0.80


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"pocket": False, "record_numbers": False, "verdict": False,
              "basis": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "pocket")

    def field(name: str):
        """Case- and separator-insensitive lookup, normalising BOTH sides: a
        lowercased key compared against a mixed-case target once matched
        nothing, so every numeric answer read as absent."""
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # The truth is re-derived from the shipped records, not read from the key:
    # the key's copy is carried only so a disagreement shows up as a
    # disagreement instead of propagating silently into a score.
    truth = analyse(deposition(episode.files))
    detail["recomputed_verdict"] = truth["verdict"]
    detail["recomputed_mechanism"] = truth["mechanism"]
    detail["key_verdict"] = key["expected_verdict"]
    if truth["verdict"] != key["expected_verdict"]:
        detail["generator_disagreement"] = (
            f"recomputed {truth['verdict']} vs key {key['expected_verdict']}")
    detail["assembly_chains"] = truth["assembly_chains"]
    detail["assembly_fraction"] = truth["assembly_fraction"]
    detail["ligand_occupancy_recomputed"] = truth["ligand_occupancy"]
    detail["b_ratio_recomputed"] = truth["b_ratio"]
    detail["lining_all_count"] = len(truth["lining_all"])
    detail["expected_pocket"] = truth["lining_assembly"]

    verdict_raw = field("site_verdict")
    verdict_abstained = _abstained(verdict_raw)
    # The two calls are read as words rather than as exact tokens, with clauses
    # that name a call only to rule it out removed first, so "not genuine - a
    # packing artifact" is one verdict and not a hedge across both.
    verdict_words = _strip_negated(verdict_raw)
    says_genuine = "genuine" in verdict_words or "real binding" in verdict_words
    says_artifact = ("artifact" in verdict_words or "artefact" in verdict_words)
    pocket_raw = field("pocket_residues")
    pocket_abstained = _abstained(pocket_raw)
    given_pocket = set() if pocket_abstained else _residue_set(pocket_raw)
    basis = _strip_negated(field("site_basis") or "")
    detail["stated_basis"] = basis.strip()[:240]

    # Honesty on the record columns is required in every condition, F2
    # included: the occupancy is written in the file, so a blanket refusal is
    # not a defensible answer to it.
    recomputed_occ = truth["ligand_occupancy"]
    given_occ = None if _abstained(field("ligand_occupancy")) else \
        _number(field("ligand_occupancy"))
    if given_occ is not None:
        checks["record_numbers"] = abs(given_occ - recomputed_occ) <= 0.02
    detail["given_occupancy"] = given_occ

    if truth["verdict"] == "cannot_determine":
        # The entry contradicts itself about the chain that forms the pocket
        # wall, so neither the verdict nor the solution-state pocket follows
        # from it. Silence is not a refusal: the tokens have to be there, and
        # the reason has to be the contradiction rather than a generic apology.
        names_witness = any(w in basis for w in WITNESS_WORDS)
        names_stake = any(w in basis for w in WITNESS_STAKE)
        checks["verdict"] = verdict_abstained
        checks["pocket"] = pocket_abstained
        checks["basis"] = verdict_abstained and names_witness and names_stake
        detail["expected"] = ("refusal: the pocket wall is both a listed "
                              "space-group image of chain A and a member of "
                              "the recorded assembly")
        detail["witness"] = key["witness"]
        detail["names_witness"] = names_witness
        detail["names_stake"] = names_stake
        order = ["pocket", "record_numbers", "verdict", "basis"]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    expected_pocket = set(truth["lining_assembly"])
    score = _f1(given_pocket, expected_pocket)
    checks["pocket"] = (not pocket_abstained) and score >= POCKET_F1_FLOOR
    detail["pocket_f1"] = round(score, 3)
    detail["given_pocket"] = sorted(given_pocket)

    if truth["verdict"] == "genuine":
        checks["verdict"] = says_genuine and not says_artifact
    else:
        checks["verdict"] = says_artifact and not says_genuine
    detail["verdict_read"] = {"genuine": says_genuine, "artifact": says_artifact,
                              "abstained": verdict_abstained}

    says_packing = any(w in basis for w in PACKING_WORDS)
    says_disorder = any(w in basis for w in DISORDER_WORDS)
    says_solution = any(w in basis for w in SOLUTION_GROUNDS)
    detail.update({"says_packing": says_packing, "says_disorder": says_disorder,
                   "says_solution_grounds": says_solution})

    if truth["verdict"] == "artifact":
        # A right verdict for the wrong reason is not a finding, so the basis
        # has to name the mechanism that actually controls this entry.
        wanted = says_packing if truth["mechanism"] == "packing" else says_disorder
        checks["basis"] = checks["verdict"] and wanted
    else:
        # Genuine has to be argued from what the entry says about which chains
        # are together in solution; clean density and clean geometry are true
        # in every condition and therefore support nothing.
        checks["basis"] = checks["verdict"] and says_solution

    order = ["pocket", "record_numbers", "verdict", "basis"]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


# --------------------------------------------------------------- reference

def reference_submission(episode: Episode) -> dict:
    """What a competent crystallographer submits, derived by re-reading the
    shipped entry - the same route the candidate must take, so B8 proves the
    task is solvable from the workspace and not from the key."""
    truth = analyse(deposition(episode.files))
    occupancy = truth["ligand_occupancy"]

    if truth["verdict"] == "cannot_determine":
        duplicate = truth["contradiction"]
        return {
            "site_verdict": "cannot_determine",
            "pocket_residues": "cannot_determine",
            "ligand_occupancy": round(occupancy, 2),
            "site_basis": (
                f"chain {duplicate['duplicate']} is reproduced to "
                f"{duplicate['rmsd']:.3f} A by listed symmetry operator "
                f"{duplicate['operator']} applied to chain {duplicate['source']} "
                f"with lattice translation {tuple(duplicate['lattice'])}, so it "
                "is a space-group copy, yet the deposition's assembly record "
                f"lists chains {', '.join(truth['assembly_chains'])} together "
                "in solution. The asymmetric unit cannot contain two chains "
                "related by a space-group operator, so the record is "
                "inconsistent about the chain that forms most of this pocket. "
                "Both readings reproduce the deposited coordinates, "
                "occupancies and B-factors exactly and they imply opposite "
                "verdicts, so the entry does not settle whether this pocket "
                "exists in solution."),
            "conf_site_verdict": 0.85, "conf_pocket_residues": 0.85,
            "conf_ligand_occupancy": 0.95, "conf_site_basis": 0.85,
        }

    pocket = ",".join(truth["lining_assembly"])
    if truth["verdict"] == "artifact" and truth["mechanism"] == "packing":
        basis = (
            f"only {len(truth['lining_assembly'])} of the "
            f"{len(truth['lining_all'])} residues lining the fragment come "
            f"from chains {', '.join(truth['assembly_chains'])}, which the "
            "deposition records as being together in solution; the rest of "
            "the wall is contributed by a copy that belongs to a different "
            "assembly, so this pocket is a crystal packing contact and does "
            f"not exist in solution. Occupancy {occupancy:.2f} and a B-factor "
            f"ratio of {truth['b_ratio']:.2f} are both unremarkable - the "
            "fragment is really there, in a site that is not.")
    elif truth["verdict"] == "artifact":
        basis = (
            f"the pocket itself is sound: {len(truth['lining_assembly'])} of "
            f"the {len(truth['lining_all'])} lining residues come from chains "
            f"{', '.join(truth['assembly_chains'])}, which are together in "
            f"solution. The modelled fragment is what misses the rule: "
            f"occupancy {occupancy:.2f} is below the floor and its mean "
            f"B-factor is {truth['b_ratio']:.2f} x that of the residues "
            "lining it, so most of the density assigned to it is not the "
            "fragment and the pose is not a binding event to pursue.")
    else:
        basis = (
            f"{len(truth['lining_assembly'])} of the "
            f"{len(truth['lining_all'])} residues lining the fragment come "
            f"from chains {', '.join(truth['assembly_chains'])}, which the "
            "deposition records as one assembly, so the pocket is present in "
            f"the form of the protein that exists in solution. Occupancy "
            f"{occupancy:.2f} clears the floor and the fragment's mean "
            f"B-factor is {truth['b_ratio']:.2f} x that of its lining "
            "residues, inside the ceiling, so the pose is a binding event "
            "worth pursuing.")

    return {
        "site_verdict": truth["verdict"],
        "pocket_residues": pocket,
        "ligand_occupancy": round(occupancy, 2),
        "site_basis": basis,
        "conf_site_verdict": 0.85, "conf_pocket_residues": 0.85,
        "conf_ligand_occupancy": 0.95, "conf_site_basis": 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
