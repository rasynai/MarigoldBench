"""Family: pose rescoring against two orthogonal gates.

PoseBusters' arithmetic is the whole point of this family. DiffDock reaches
38% at RMSD <= 2 A on the 308-complex benchmark and 12% once physical
validity is ANDed on, and the single largest sink in that waterfall is not an
internal defect at all - 72 of the 117 poses that survived the RMSD cut died
on the protein-ligand distance test. A pose can be a flawless small molecule
and still be sitting inside the receptor.

So the model is handed several docked poses plus the receptor site they came
from, and the answer is the INTERSECTION of two checks that live in different
files: an internal-geometry check that needs only the SDF, and a clash check
that needs the SDF and the PDB together. Running one gate well and skipping
the other produces a confident, wrong, plausible answer, which is exactly the
failure mode the paper documents in the field.

Three conditions, briefs byte-identical across all of them:

C0  one pose clears both gates; the program's own top-ranked pose does not.
H1  the pose that is internally flawless is the one buried in the receptor,
    and a different pose is the survivor. The per-gate COUNTS are identical
    to C0 - only the intersection moves - so a model that reports counts
    without intersecting them cannot tell the two conditions apart.
F2  every pose fails at least one gate, so there is nothing to carry forward
    and a documented refusal is the only correct outcome. The counts are
    still graded, so blanket abstention does not pass.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from ..families import Episode, Verdict

# Small aromatic ligands: every one has a ring (so the planarity defect is
# available) and <= 20 atoms with hydrogens, which keeps each pose file under
# 2 KB. Workspace bytes are re-read by the candidate and cost real money.
GATE_LIGANDS = [
    ("CC(=O)Nc1ccc(O)cc1", "paracetamol"),
    ("OC(=O)c1ccccc1O", "salicylic acid"),
    ("Nc1ccc(cc1)C(=O)O", "4-aminobenzoic acid"),
    ("NC(=O)c1cccnc1", "nicotinamide"),
    ("COc1ccccc1O", "guaiacol"),
    ("O=Cc1cccc(O)c1", "3-hydroxybenzaldehyde"),
    ("Nc1ccccc1C(=O)O", "anthranilic acid"),
    ("Cc1ccc(O)cc1C", "3,4-dimethylphenol"),
]

# Residues lining the fabricated site. Non-contiguous numbering, because a
# real pocket extract is not a contiguous stretch of sequence.
POCKET_RESIDUES = [
    ("LEU", 24), ("VAL", 31), ("PHE", 45), ("TYR", 58), ("ASP", 62),
    ("SER", 79), ("THR", 88), ("ILE", 104), ("TRP", 117),
]

CORRUPTIONS = ("stretched_bond", "broken_planarity", "overlapped_atoms")

# Role of each of the four poses.
#   clean     - passes internal geometry AND sits clear of the receptor
#   bad_geom  - internally defective, but clear of the receptor
#   clash     - internally flawless, buried in the receptor wall
#   both_bad  - fails both
LAYOUTS_SOUND = [
    ["clean", "bad_geom", "clash", "both_bad"],     # 2 geometry, 2 receptor
    ["clean", "clash", "clash", "bad_geom"],        # 3 geometry, 2 receptor
    ["clean", "bad_geom", "bad_geom", "clash"],     # 2 geometry, 3 receptor
]
LAYOUTS_FLAWED = [
    ["clash", "clash", "bad_geom", "both_bad"],     # 2 geometry, 1 receptor
    ["clash", "clash", "clash", "bad_geom"],        # 3 geometry, 1 receptor
    ["bad_geom", "bad_geom", "clash", "clash"],     # 2 geometry, 2 receptor
]

POSE_IDS = ("pose_A", "pose_B", "pose_C", "pose_D")

# Geometric constants of the fabricated site. The shell sits far enough out
# that a centred pose clears every receptor atom by >= CLEARANCE angstrom,
# which is comfortably above any published protein-ligand contact criterion
# (0.75 x vdW sum peaks at 2.55 A for carbon), and a shoved pose puts one
# ligand atom OVERLAP angstrom from a receptor side-chain carbon, which is
# below every one of them. Neither verdict is threshold-sensitive.
CLEARANCE = 4.3
OVERLAP = 0.55
MIN_SAFE_DISTANCE = 2.9


# --------------------------------------------------------------- vector maths

def _unit(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _axpy(a, b, s):
    return (a[0] + s * b[0], a[1] + s * b[1], a[2] + s * b[2])


def _scale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)


def _directions(n: int, phase: float):
    """Near-uniform directions on the sphere (Fibonacci lattice)."""
    golden = math.pi * (3.0 - math.sqrt(5.0))
    out = []
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1.0 - z * z))
        theta = golden * i + phase
        out.append((r * math.cos(theta), r * math.sin(theta), z))
    return out


def _frame(u):
    ref = (0.0, 0.0, 1.0) if abs(u[2]) < 0.9 else (1.0, 0.0, 0.0)
    v = _unit(_cross(u, ref))
    return v, _unit(_cross(u, v))


# --------------------------------------------------------------- the receptor

def _atom_line(serial: int, name: str, resname: str, resnum: int,
               pos, element: str) -> str:
    return (f"ATOM  {serial:5d}  {name:<3s} {resname:>3s} A{resnum:4d}    "
            f"{pos[0]:8.3f}{pos[1]:8.3f}{pos[2]:8.3f}  1.00 20.00"
            f"          {element:>2s}")


def _receptor_pdb(radius: float, phase: float) -> str:
    """A site extract: the CB of every residue lines a cavity of `radius`."""
    lines = ["REMARK   1 SITE EXTRACT, HEAVY ATOMS, CHAIN A"]
    serial = 1
    for (resname, resnum), u in zip(POCKET_RESIDUES,
                                    _directions(len(POCKET_RESIDUES), phase)):
        v, w = _frame(u)
        cb = _scale(u, radius)
        ca = _scale(u, radius + 1.53)
        n_atom = _axpy(ca, _unit(_axpy(_scale(u, 0.80), v, 0.60)), 1.46)
        c_atom = _axpy(ca, _unit(_axpy(_scale(u, 0.75), v, -0.45)), 1.52)
        o_atom = _axpy(c_atom, _unit(_axpy(_scale(u, 0.85), w, 0.35)), 1.23)
        for name, pos, element in (("N", n_atom, "N"), ("CA", ca, "C"),
                                   ("C", c_atom, "C"), ("O", o_atom, "O"),
                                   ("CB", cb, "C")):
            lines.append(_atom_line(serial, name, resname, resnum, pos, element))
            serial += 1
    lines.append("END")
    return "\n".join(lines) + "\n"


def _receptor_heavy_atoms(pdb_text: str):
    out = []
    for line in pdb_text.splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
        except ValueError:
            continue
        element = (line[76:78].strip() or line[12:16].strip()[:1]).capitalize()
        if element == "H":
            continue
        out.append(xyz)
    return out


# ---------------------------------------------------------------- the ligands

def _embed(smiles: str, seed: int):
    """A relaxed conformer, written out as heavy atoms only.

    Hydrogens are added for the embedding and the force-field relaxation, then
    dropped: docking output is routinely heavy-atom-only, every check in this
    family is a heavy-atom check, and the shipped pose files are a third
    smaller for it - workspace bytes are candidate tokens.
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    if AllChem.EmbedMolecule(mol, params) != 0:
        return None
    AllChem.UFFOptimizeMolecule(mol, maxIters=600)
    return Chem.RemoveHs(mol)


def _centre(mol):
    """Put the heavy-atom centroid at the origin."""
    conf = mol.GetConformer()
    heavy = [i for i in range(mol.GetNumAtoms())
             if mol.GetAtomWithIdx(i).GetSymbol() != "H"]
    cx = sum(conf.GetAtomPosition(i).x for i in heavy) / len(heavy)
    cy = sum(conf.GetAtomPosition(i).y for i in heavy) / len(heavy)
    cz = sum(conf.GetAtomPosition(i).z for i in heavy) / len(heavy)
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, (p.x - cx, p.y - cy, p.z - cz))
    return mol


def _radius(mol) -> float:
    conf = mol.GetConformer()
    return max(math.dist((0.0, 0.0, 0.0),
                         (conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y,
                          conf.GetAtomPosition(i).z))
               for i in range(mol.GetNumAtoms()))


def _corrupt(mol, kind: str, rng: random.Random):
    """Break the pose internally without moving it out of the cavity."""
    from rdkit import Chem
    from ..checks import COVALENT_RADII
    mol = Chem.Mol(mol)
    conf = mol.GetConformer()

    if kind == "stretched_bond":
        candidates = [b for b in mol.GetBonds()
                      if b.GetBeginAtom().GetSymbol() != "H"
                      and b.GetEndAtom().GetSymbol() != "H"
                      and not b.IsInRing()]
        if not candidates:
            candidates = [b for b in mol.GetBonds()
                          if b.GetBeginAtom().GetSymbol() != "H"
                          and b.GetEndAtom().GetSymbol() != "H"]
        if not candidates:
            return None
        bond = candidates[rng.randrange(len(candidates))]
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        ri = COVALENT_RADII.get(mol.GetAtomWithIdx(i).GetSymbol(), 0.76)
        rj = COVALENT_RADII.get(mol.GetAtomWithIdx(j).GetSymbol(), 0.76)
        pi = conf.GetAtomPosition(i)
        pj = conf.GetAtomPosition(j)
        u = _unit((pj.x - pi.x, pj.y - pi.y, pj.z - pi.z))
        target = 1.75 * (ri + rj)
        conf.SetAtomPosition(j, (pi.x + u[0] * target, pi.y + u[1] * target,
                                 pi.z + u[2] * target))
        return mol

    if kind == "broken_planarity":
        rings = [r for r in mol.GetRingInfo().AtomRings()
                 if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in r)]
        if not rings or len(rings[0]) < 6:
            return None
        ring = rings[0]
        pts = [conf.GetAtomPosition(i) for i in ring]
        # The plane the check fits comes from the first three ring atoms, so
        # leave those alone and buckle the far side of the ring.
        normal = _unit(_cross((pts[1].x - pts[0].x, pts[1].y - pts[0].y,
                               pts[1].z - pts[0].z),
                              (pts[2].x - pts[0].x, pts[2].y - pts[0].y,
                               pts[2].z - pts[0].z)))
        # Pucker ALTERNATING atoms by +/-0.40 A. A contiguous buckle is a
        # hinge, and a least-squares plane simply tilts to absorb it, so the
        # defect would be visible to a three-point plane and invisible to a
        # best-fit one - the family would then be grading which planarity
        # implementation the candidate happened to write. An alternating
        # pucker cannot be tilted away: every plane through the ring is
        # 0.40 A from three of its atoms. Ring bonds go 1.39 -> 1.60 A, still
        # inside the 25% bond tolerance, so this pose fails planarity alone.
        for offset, idx in enumerate(ring):
            shift = 0.40 if offset % 2 else -0.40
            p = conf.GetAtomPosition(idx)
            conf.SetAtomPosition(idx, (p.x + shift * normal[0],
                                       p.y + shift * normal[1],
                                       p.z + shift * normal[2]))
        return mol

    if kind == "overlapped_atoms":
        heavy = [i for i in range(mol.GetNumAtoms())
                 if mol.GetAtomWithIdx(i).GetSymbol() != "H"]
        best, pair = -1.0, None
        for a in heavy:
            for b in heavy:
                if a >= b:
                    continue
                d = math.dist(
                    (conf.GetAtomPosition(a).x, conf.GetAtomPosition(a).y,
                     conf.GetAtomPosition(a).z),
                    (conf.GetAtomPosition(b).x, conf.GetAtomPosition(b).y,
                     conf.GetAtomPosition(b).z))
                if d > best:
                    best, pair = d, (a, b)
        if pair is None:
            return None
        a, b = pair
        pa = conf.GetAtomPosition(a)
        # Drop b onto a: 0.45 A apart is far inside any clash criterion, and
        # it moves b INWARD, so the pose stays clear of the receptor wall.
        conf.SetAtomPosition(b, (pa.x + 0.45, pa.y, pa.z))
        return mol
    return None


def _shove(mol, radius: float, direction) -> "object":
    """Translate the pose so one ligand atom sits inside a receptor side chain."""
    from rdkit import Chem
    mol = Chem.Mol(mol)
    conf = mol.GetConformer()
    heavy = [i for i in range(mol.GetNumAtoms())
             if mol.GetAtomWithIdx(i).GetSymbol() != "H"]
    lead = max(heavy, key=lambda i: (conf.GetAtomPosition(i).x * direction[0]
                                     + conf.GetAtomPosition(i).y * direction[1]
                                     + conf.GetAtomPosition(i).z * direction[2]))
    p = conf.GetAtomPosition(lead)
    target = _scale(direction, radius + OVERLAP)
    shift = (target[0] - p.x, target[1] - p.y, target[2] - p.z)
    for i in range(mol.GetNumAtoms()):
        q = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, (q.x + shift[0], q.y + shift[1], q.z + shift[2]))
    return mol


# ------------------------------------------------------------- recomputation

def _geometry_failures(mol_block: str) -> list[str]:
    from ..checks import check_molecule_geometry
    return [r.name for r in check_molecule_geometry(mol_block) if not r.passed]


def _closest_receptor_contact(mol_block: str, receptor) -> float:
    from rdkit import Chem
    mol = Chem.MolFromMolBlock(mol_block, sanitize=False, removeHs=False)
    if mol is None or mol.GetNumConformers() == 0:
        return 0.0
    conf = mol.GetConformer()
    best = float("inf")
    for i in range(mol.GetNumAtoms()):
        if mol.GetAtomWithIdx(i).GetSymbol() == "H":
            continue
        p = conf.GetAtomPosition(i)
        for q in receptor:
            d = math.dist((p.x, p.y, p.z), q)
            if d < best:
                best = d
    return best


def _receptor_clash(mol_block: str, pdb_text: str) -> bool:
    """True when the pose interpenetrates the receptor."""
    from ..checks import check_ligand_protein_clash
    return not check_ligand_protein_clash(mol_block, pdb_text).passed


# -------------------------------------------------------------------- builder

BRIEF = (
    "A docking run against the site in receptor_site.pdb left four candidate "
    "poses of one ligand in the rescoring queue: pose_A.sdf, pose_B.sdf, "
    "pose_C.sdf and pose_D.sdf. The program's own score for each is in "
    "docking_run.csv and the run is described in run_notes.txt.\n\n"
    "A pose is only usable if it is sound as a molecular structure in its own "
    "right AND it does not occupy the same space as the receptor. Establish "
    "how the queue stands against each of those two requirements, and which "
    "single pose, if any, the project should carry forward.\n\n"
    "Submit these fields:\n"
    "- surviving_pose: the pose_id that meets both requirements, or the "
    "string cannot_determine if no pose in the queue does\n"
    "- n_pass_geometry: integer, how many of the four poses are sound as "
    "molecular structures\n"
    "- n_pass_receptor: integer, how many of the four poses do not occupy the "
    "same space as the receptor\n"
    "and conf_<field> in [0,1] for each."
)


def build(seed: int, condition: str) -> Episode:
    from rdkit import Chem

    rng = random.Random(310_000 + seed)
    smiles, ligand_name = GATE_LIGANDS[seed % len(GATE_LIGANDS)]

    # Every random draw below happens in a fixed order and does NOT depend on
    # the condition, so C0, H1 and F2 share the same pose layout, the same
    # site geometry and the same score jitter. Only the role assignment moves.
    order = list(range(4))
    rng.shuffle(order)
    kinds = [CORRUPTIONS[rng.randrange(len(CORRUPTIONS))] for _ in range(4)]
    targets = [rng.randrange(len(POCKET_RESIDUES)) for _ in range(4)]
    jitter = [rng.random() for _ in range(4)]
    phase = rng.random() * 2.0 * math.pi
    corrupt_rng = random.Random(910_000 + seed)

    base = LAYOUTS_FLAWED if condition == "F2" else LAYOUTS_SOUND
    roles = [base[seed % 3][i] for i in order]
    if condition == "H1":
        # The planted defect: the internally flawless pose is the one buried
        # in the receptor, and the survivor is somewhere else entirely. Both
        # per-gate counts are unchanged, so only the intersection moves.
        a, b = roles.index("clean"), roles.index("clash")
        roles[a], roles[b] = roles[b], roles[a]

    blocks: dict[str, str] = {}
    pdb = ""
    recomputed: dict[str, dict] = {}
    matched = False

    for attempt in range(6):
        mols = [_embed(smiles, 4_000 + 31 * seed + 7 * i + 101 * attempt)
                for i in range(4)]
        if any(m is None for m in mols):
            continue
        mols = [_centre(m) for m in mols]
        radius = max(_radius(m) for m in mols) + CLEARANCE
        pdb = _receptor_pdb(radius, phase)
        receptor = _receptor_heavy_atoms(pdb)
        site_directions = _directions(len(POCKET_RESIDUES), phase)

        blocks = {}
        attempt_rng = random.Random(corrupt_rng.randrange(1 << 30))
        for i, pose_id in enumerate(POSE_IDS):
            mol = Chem.Mol(mols[i])
            if roles[i] in ("bad_geom", "both_bad"):
                mol = _corrupt(mol, kinds[i], attempt_rng) or mol
            if roles[i] in ("clash", "both_bad"):
                mol = _shove(mol, radius, site_directions[targets[i]])
            blocks[pose_id] = Chem.MolToMolBlock(mol)

        recomputed = {}
        for i, pose_id in enumerate(POSE_IDS):
            block = blocks[pose_id]
            failures = _geometry_failures(block)
            clash = _receptor_clash(block, pdb)
            recomputed[pose_id] = {
                "geometry_failures": failures,
                "geometry_ok": not failures,
                "receptor_ok": not clash,
                "closest_contact": round(
                    _closest_receptor_contact(block, receptor), 2),
            }

        # Constructed truth is only truth once it survives recomputation: the
        # intended role of every pose must be what the shipped bytes actually
        # show, with a margin on the non-clashing poses so the receptor gate
        # is not sensitive to which clash criterion a candidate picks.
        matched = True
        for i, pose_id in enumerate(POSE_IDS):
            want_geometry = roles[i] in ("clean", "clash")
            want_receptor = roles[i] in ("clean", "bad_geom")
            got = recomputed[pose_id]
            if got["geometry_ok"] != want_geometry or got["receptor_ok"] != want_receptor:
                matched = False
            if want_receptor and got["closest_contact"] < MIN_SAFE_DISTANCE:
                matched = False
        if matched:
            break

    # An episode whose bytes do not show the intended roles has a broken
    # premise - F2 could be handed a survivor, H1 could leave the survivor
    # where C0 had it - so it must never ship. Raising here surfaces as a
    # build failure in the family gate instead of a quietly wrong instance.
    if not matched:
        raise RuntimeError(
            f"pose-rescoring s{seed}/{condition}: construction did not match "
            f"intent after 6 attempts; roles={dict(zip(POSE_IDS, roles))} "
            f"recomputed={recomputed}")

    geometry_pass = sorted(p for p in POSE_IDS if recomputed[p]["geometry_ok"])
    receptor_pass = sorted(p for p in POSE_IDS if recomputed[p]["receptor_ok"])
    survivors = sorted(set(geometry_pass) & set(receptor_pass))

    # The program's own ranking puts an internally flawless but receptor-buried
    # pose on top, in every condition. Trusting the score, or stopping after
    # the internal check, therefore lands on the same wrong pose everywhere.
    lead = next((i for i, r in enumerate(roles) if r == "clash"), 0)
    ranking = [lead] + sorted((i for i in range(4) if i != lead),
                              key=lambda i: jitter[i])
    rows = []
    for rank, i in enumerate(ranking):
        score = round(-11.1 + 0.5 * rank + 0.18 * jitter[i], 2)
        rows.append(f"{POSE_IDS[i]},{score:.2f},{rank + 1}")

    files = {f"{pose_id}.sdf": blocks[pose_id] for pose_id in POSE_IDS}
    files["receptor_site.pdb"] = pdb
    files["docking_run.csv"] = ("pose_id,dock_score_kcal_per_mol,rank\n"
                                + "\n".join(rows) + "\n")
    files["run_notes.txt"] = (
        f"Rescoring queue R{seed}\n"
        f"Ligand: {ligand_name}\n"
        f"SMILES: {smiles}\n"
        f"Receptor: site extract in receptor_site.pdb, "
        f"{len(POCKET_RESIDUES)} residues, chain A, heavy atoms only.\n"
        "Poses: pose_A.sdf pose_B.sdf pose_C.sdf pose_D.sdf, one conformer "
        "each, heavy atoms only, coordinates in the receptor frame.\n"
        "Scores: docking_run.csv, more negative is better.\n")

    key = {
        "condition": condition,
        "pose_ids": list(POSE_IDS),
        "roles": dict(zip(POSE_IDS, roles)),
        "geometry_pass": geometry_pass,
        "receptor_pass": receptor_pass,
        "survivors": survivors,
        "n_geometry": len(geometry_pass),
        "n_receptor": len(receptor_pass),
        "top_ranked": POSE_IDS[ranking[0]],
        "ligand": ligand_name,
        "closest_contacts": {p: recomputed[p]["closest_contact"] for p in POSE_IDS},
    }
    return Episode("pose-rescoring", seed, condition, BRIEF, files, key,
                   budget=14,
                   checkpoints=["geometry_gate", "receptor_gate", "conjunction"])


# ------------------------------------------------------------------- verifier

ABSTAIN = {"cannot_determine", "cannot determine", "none", "no_pose",
           "no pose", "n_a", "na", "null", "nan"}

# Distinguishes "the candidate did not answer" from "the candidate answered
# with a refusal". The empty string is deliberately NOT in ABSTAIN: silence is
# not a documented refusal, and the F2 rung is only worth anything if the
# refusal has to be stated (families.verify_lead_opt makes the same point -
# treating an absent field as abstention let a submission that engaged with
# nothing score full marks on every flawed-premise instance).
_MISSING = object()


def _field(submitted: dict, name: str, default=None):
    for candidate, value in submitted.items():
        if str(candidate).strip().lower().replace(" ", "_").replace("-", "_") == name:
            return value
    return default


def _as_int(value):
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return int(number) if float(number).is_integer() else None


def _normalise_pose(value, pose_ids: list[str]) -> str:
    # Not `str(value or "")`: a falsy non-string (0, False) would collapse to
    # the empty token and be read as a refusal it never made.
    text = "" if value is None or value is _MISSING else str(value)
    token = text.strip().lower().replace(" ", "_").replace("-", "_")
    if token in ABSTAIN:
        return ""
    for pose_id in pose_ids:
        short = pose_id.split("_")[-1].lower()
        if token in (pose_id.lower(), short, f"pose{short}", f"pose_{short}"):
            return pose_id
    return token


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    checks = {"geometry_gate": False, "receptor_gate": False,
              "conjunction": False}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, "geometry_gate")

    pose_ids = list(episode.key["pose_ids"])

    # Recompute from the bytes the generator shipped, not from the workspace
    # copy: run_python can overwrite anything in the workspace, and a verifier
    # that reads the candidate's own rewrite of the evidence is not a check.
    # The workspace copy is still compared, and any divergence is reported.
    shipped = episode.files
    tampered = []
    for name, text in shipped.items():
        path = workspace / name
        try:
            if path.exists() and path.read_text(encoding="utf-8", errors="replace") != text:
                tampered.append(name)
        except OSError:
            pass
    if tampered:
        detail["workspace_modified"] = sorted(tampered)

    pdb = shipped["receptor_site.pdb"]
    receptor = _receptor_heavy_atoms(pdb)
    per_pose: dict[str, dict] = {}
    for pose_id in pose_ids:
        block = shipped[f"{pose_id}.sdf"]
        failures = _geometry_failures(block)
        clash = _receptor_clash(block, pdb)
        per_pose[pose_id] = {
            "geometry_failures": failures,
            "geometry_ok": not failures,
            "receptor_ok": not clash,
            "closest_contact": round(_closest_receptor_contact(block, receptor), 2),
        }
    geometry_pass = sorted(p for p in pose_ids if per_pose[p]["geometry_ok"])
    receptor_pass = sorted(p for p in pose_ids if per_pose[p]["receptor_ok"])
    survivors = sorted(set(geometry_pass) & set(receptor_pass))
    detail["recomputed"] = per_pose
    detail["geometry_pass"] = geometry_pass
    detail["receptor_pass"] = receptor_pass
    detail["survivors"] = survivors
    detail["key_survivors"] = episode.key["survivors"]
    if survivors != episode.key["survivors"]:
        detail["key_disagreement"] = True

    given_geometry = _as_int(_field(submitted, "n_pass_geometry"))
    given_receptor = _as_int(_field(submitted, "n_pass_receptor"))
    checks["geometry_gate"] = given_geometry == len(geometry_pass)
    checks["receptor_gate"] = given_receptor == len(receptor_pass)
    detail["n_pass_geometry"] = {"given": given_geometry,
                                 "recomputed": len(geometry_pass)}
    detail["n_pass_receptor"] = {"given": given_receptor,
                                 "recomputed": len(receptor_pass)}

    raw = _field(submitted, "surviving_pose", _MISSING)
    # An absent or blank field is no answer at all. It must fail every
    # condition, F2 included, or the correct move on a flawed premise would be
    # to say nothing rather than to say the queue is empty.
    # A JSON null is what a schema-filling harness emits for a field the model
    # left alone, so it is silence too, not a refusal.
    stated = raw is not _MISSING and raw is not None and str(raw).strip() != ""
    chosen = _normalise_pose(raw, pose_ids) if stated else ""
    abstained = stated and chosen == ""
    if survivors:
        checks["conjunction"] = stated and (not abstained) and chosen in survivors
    else:
        checks["conjunction"] = abstained
    detail["surviving_pose"] = {
        "given": "<absent>" if raw is _MISSING else str(raw)[:60],
        "stated": stated, "normalised": chosen,
        "acceptable": survivors or ["cannot_determine"]}

    order = ["geometry_gate", "receptor_gate", "conjunction"]
    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


# ------------------------------------------------------------------ reference

def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make. Derived from
    the episode key, so it doubles as the B8 baseline check.

    Every number here is the one `build` obtained by RECOMPUTING the shipped
    bytes with the same two checks the verifier reruns - `n_geometry` and
    `n_receptor` are `len()` of the recomputed pass lists, and `survivors` is
    their intersection - so nothing is asserted that the verifier will not
    independently arrive at. On F2 the intersection is empty and the only
    correct answer is the documented refusal; the two counts are still
    reported, because blanket abstention is not a pass.
    """
    key = episode.key
    survivors = list(key["survivors"])
    return {
        "surviving_pose": survivors[0] if survivors else "cannot_determine",
        "n_pass_geometry": int(key["n_geometry"]),
        "n_pass_receptor": int(key["n_receptor"]),
        "conf_surviving_pose": 0.9 if survivors else 0.8,
        "conf_n_pass_geometry": 0.9,
        "conf_n_pass_receptor": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
