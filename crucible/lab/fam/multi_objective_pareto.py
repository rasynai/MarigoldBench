"""Family: a four-objective progression decision where the recorded structures
are not the ligands.

Written against the collaborator critique that sank the first batch of families
(analysis/collab/hardening__gpt.md): "canonical audit recipes with a conspicuous
local defect", and the warning that we had "confused using a complex tool with
solving a complex scientific problem". The prescription was several
superficially adequate analyses that imply DIFFERENT decisions, plus data that
make exactly one of them defensible. So this family ships one candidate table
that four competent-looking pipelines read four different ways:

  A. rank on the headline objective (potency) and take the leader;
  B. build a Pareto front from the properties as they are recorded in the
     table (or, equivalently, recomputed from the recorded structures);
  C. build a Pareto front from the ligands but compare potency as a bare
     float, ignoring what the assay can actually resolve;
  D. build it from the ligands, at the resolution the assay states.

Only D is defensible, and A, B and C each nominate a different compound. The
table is internally consistent throughout - the `heavy_atoms`,
`ligand_efficiency` and `alert_count` columns agree exactly with what RDKit
returns for the SMILES as written - so there is no local inconsistency to find.
The single fact that separates the worlds is in the record: structures are
stored as received from the compound bank, salt or co-former included, while
every objective is a property of the ligand. One insight, three consequences:

  * heavy-atom count, hence ligand efficiency, is inflated for a salt;
  * a fumarate or maleate co-former is itself a Michael acceptor, so the alert
    count picks up a liability the ligand does not have;
  * the progression tie-break counts heavy atoms in the ligand, so the
    co-former can hand the decision to the wrong compound.

C0 and H1 differ only in three numeric columns of the same twelve-row table.
In C0 the potency leader is genuinely non-dominated - its potency lead over the
efficient small compound is larger than the assay resolves - and calling it
dominated is a false alarm. In H1 that lead shrinks inside the resolution, so
the leader is dominated and the decision moves; a pipeline that keeps the
recorded alert count never sees the domination, because on the recorded
structure the dominator carries a co-former alert.

F2 carries an explicit impossibility witness rather than thin data. Two
candidates sit on the front with objective vectors that are equal in every
component - same potency, same solubility, same ligand efficiency, same alert
count - so the rules' tie-break chain runs out, and its last clause names a
measurement (unbound fraction in the assay buffer) that appears in no supplied
file. The identity is only visible after the co-former is taken off: on the
recorded structures the two look clearly different and every naive pipeline
picks one of them with confidence. The rules file is byte-identical in all
three conditions, so that final clause is also a standing false-alarm bait: it
is unusable in C0 and H1 too, and refusing there is wrong.

One honest limitation, recorded rather than hidden: in F2 the two tied
candidates carry the same ligand efficiency by construction and only one of
them is co-formed, so the reported efficiency is reachable there without
noticing the co-former at all. That is forced - if any front member had a
higher efficiency it would dominate the pair and there would be no tie - so in
F2 the efficiency checkpoint carries no weight and the front, the refusal and
the named tie carry all of it. Measured, not assumed: runs/_naive_pareto.py
builds six wrong-but-competent pipelines and checks all of them fail every
condition.
"""
from __future__ import annotations

import math
import random
import re
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = ("cannot_determine", "cannot determine", "cannot be determined",
           "not_determinable", "not determinable", "indeterminate", "none",
           "n_a", "na", "null", "no unique selection", "not_selectable",
           "not selectable", "no compound", "no single compound",
           "do not single out", "does not single out", "no defensible choice",
           "cannot choose", "no selection", "not identifiable")

# --------------------------------------------------------------- project rules
LE_CONSTANT = 1.37                # kcal/mol per log unit, the usual convention
POT_FOLD = 2.0                    # IC50 differences below this are unresolved
SOL_TOL_UM = 5.0                  # solubility differences below this likewise
IC50_GATE_NM = 100.0
SOL_GATE_UM = 10.0
N_CANDIDATES = 12

# A liability list a medicinal chemist would sign: each pattern is a genuine
# reactive or redox risk. The alkyl-halide pattern is deliberately restricted to
# primary and secondary Cl/Br/I, because a version that also matched
# trifluoromethyl flagged half the pool for a liability CF3 does not carry, and
# a task built on an indefensible alert is not measuring judgment.
ALERTS: tuple[tuple[str, str], ...] = (
    ("michael_acceptor", "[CX3]=[CX3][CX3]=[OX1]"),
    ("nitroaromatic", "[c][NX3+](=O)[O-]"),
    ("primary_aromatic_amine", "[NX3;H2][c]"),
    ("aliphatic_aldehyde", "[CX3H1](=O)[CX4]"),
    ("alkyl_halide", "[CX4;H1,H2][Cl,Br,I]"),
    ("free_thiol", "[SX2H]"),
    ("hydrazine", "[NX3][NX3]"),
    ("catechol", "[OX2H]c1ccccc1[OX2H]"),
    ("azo_linkage", "[#6][NX2]=[NX2][#6]"),
)

TARGETS = [
    ("CRU-31", "MTH1 hydrolase", "8-oxo-dGTPase"),
    ("CRU-32", "NUDT5 hydrolase", "ADP-ribose pyrophosphatase"),
    ("CRU-33", "PIN1 isomerase", "peptidyl-prolyl isomerase"),
    ("CRU-34", "NNMT transferase", "nicotinamide N-methyltransferase"),
    ("CRU-35", "DCLK1 kinase", "doublecortin-like kinase"),
    ("CRU-36", "SETD7 transferase", "protein lysine methyltransferase"),
]

# Ligands drawn as their free forms; `kind` records whether the molecule can
# plausibly be banked as a salt of an acidic co-former.
POOL: tuple[tuple[str, str, str], ...] = (
    ("CC(C)NCC(O)COc1ccc(CC(N)=O)cc1", "base", "atenolol"),
    ("CC(C)NCC(O)COc1cccc2ccccc12", "base", "propranolol"),
    ("CC(C)NCC(O)COc1ccc(CCOC)cc1", "base", "metoprolol"),
    ("CCCN(CCC)CCc1cccc2c1CC(=O)N2", "base", "ropinirole"),
    ("COc1ccc(CN2CCNCC2)c(OC)c1OC", "base", "trimetazidine"),
    ("CN(C)CCC(c1ccccc1)c1ccc(Cl)cc1", "base", "chlorpheniramine"),
    ("CN(C)CCOC(c1ccccc1)c1ccccc1", "base", "diphenhydramine"),
    ("CC(CCCN)Nc1ccnc2cc(OC)ccc12", "base", "primaquine"),
    ("CNC1CCC(c2ccc(Cl)c(Cl)c2)c2ccccc21", "base", "sertraline"),
    ("CN(C)CC(c1ccc(OC)cc1)C1(O)CCCCC1", "base", "venlafaxine"),
    ("CN(C)CCc1c[nH]c2ccc(CN3CCOC3=O)cc12", "base", "zolmitriptan"),
    ("CC(C)N(CCC(c1ccccc1)c1cc(C)ccc1O)C(C)C", "base", "tolterodine"),
    ("Cc1nccn1CC1CCc2c(c3ccccc3n2C)C1=O", "base", "ondansetron"),
    ("CCN(CC)CCCC(C)Nc1ccnc2cc(Cl)ccc12", "base", "chloroquine"),
    ("CN(C)CCC=C1c2ccccc2CCc2ccccc21", "base", "amitriptyline"),
    ("COC(=O)C(c1ccccc1Cl)N1CCc2sccc2C1", "base", "clopidogrel"),
    ("CC(CCc1ccccc1)NCC(O)c1ccc(O)c(C(N)=O)c1", "base", "labetalol"),
    ("CCN(CC)Cc1cc(Nc2ccc3cc(Cl)ccc3n2)ccc1O", "base", "amodiaquine"),
    ("CCOc1ccccc1OCCNC(C)Cc1ccc(OC)c(S(N)(=O)=O)c1", "base", "tamsulosin"),
    ("COc1ccc(C2Sc3ccccc3N(CCN(C)C)C(=O)C2OC(C)=O)cc1", "base", "diltiazem"),
    ("COc1ccccc1OCCNCC(O)COc1cccc2[nH]c3ccccc3c12", "base", "carvedilol"),
    ("COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1", "base", "gefitinib"),
    ("CCCc1nn(C)c2c(=O)[nH]c(-c3cc(S(=O)(=O)N4CCN(C)CC4)ccc3OCC)nc12",
     "base", "sildenafil"),
    ("COc1ccc(CCN(C)CCCC(C#N)(c2ccc(OC)c(OC)c2)C(C)C)cc1OC", "base", "verapamil"),
    ("OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl", "acid", "diclofenac"),
    ("CC(C(=O)O)c1cccc(C(=O)c2ccccc2)c1", "acid", "ketoprofen"),
    ("COc1ccc2cc(C(C)C(=O)O)ccc2c1", "acid", "naproxen"),
    ("CC(C)Cc1ccc(C(C)C(=O)O)cc1", "acid", "ibuprofen"),
    ("CC(C(=O)O)c1ccc(-c2ccccc2)c(F)c1", "acid", "flurbiprofen"),
    ("CC(C)(CCCOc1ccc(C)cc1C)C(=O)O", "acid", "gemfibrozil"),
    ("CCCCNC(=O)NS(=O)(=O)c1ccc(C)cc1", "acid", "tolbutamide"),
    ("CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O", "acid", "warfarin"),
    ("COc1ccc2c(c1)c(CC(=O)O)c(C)n2C(=O)c1ccc(Cl)cc1", "acid", "indomethacin"),
    ("CCCCc1nc(Cl)c(CO)n1Cc1ccc(-c2ccccc2-c2nnn[nH]2)cc1", "acid", "losartan"),
    ("CCN(CC)CC(=O)Nc1c(C)cccc1C", "base", "lidocaine"),
    ("CC(C)(C)NCC(O)c1ccc(O)c(CO)c1", "base", "salbutamol"),
    ("CC(C)NCC(O)c1ccc(NS(C)(=O)=O)cc1", "base", "sotalol"),
    ("NC(=O)N1c2ccccc2C=Cc2ccccc21", "neutral", "carbamazepine"),
    ("CC(NC(C)(C)C)C(=O)c1cccc(Cl)c1", "base", "bupropion"),
    ("Cc1ccnc2c1NC(=O)c1cccnc1N2C1CC1", "neutral", "nevirapine"),
    ("CC(=O)NCC1CN(c2ccc(N3CCOCC3)c(F)c2)C(=O)O1", "neutral", "linezolid"),
    ("COc1ccc2[nH]c(S(=O)Cc3ncc(C)c(OC)c3C)nc2c1", "base", "omeprazole"),
    ("O=C1CN2CCCCC2C(=O)N1CC1CCCCC1", "neutral", "praziquantel"),
    ("CCC(=C(c1ccccc1)c1ccc(OCCN(C)C)cc1)c1ccccc1", "base", "tamoxifen"),
    ("OC(Cn1cncn1)(Cn1cncn1)c1ccc(F)cc1F", "base", "fluconazole"),
    # alert-bearing ligands: real liabilities, not co-former artefacts
    ("CCN(CC)CCOC(=O)c1ccc(N)cc1", "base", "procaine"),
    ("CCN(CC)CCNC(=O)c1ccc(N)cc1", "base", "procainamide"),
    ("Cc1cc(NS(=O)(=O)c2ccc(N)cc2)no1", "acid", "sulfamethoxazole"),
    ("Nc1ccc(S(=O)(=O)c2ccc(N)cc2)cc1", "neutral", "dapsone"),
    ("OC(=O)CCCc1ccc(N(CCCl)CCCl)cc1", "acid", "chlorambucil"),
    ("NC(Cc1ccc(N(CCCl)CCCl)cc1)C(=O)O", "acid", "melphalan"),
    ("CCN(CC)CCNC(=O)c1cc(Cl)c(N)cc1OC", "base", "metoclopramide"),
    ("Cc1ccc(C(=O)c2ccc(O)c(O)c2[N+](=O)[O-])cc1", "acid", "tolcapone"),
    ("CS(=O)(=O)Nc1ccc([N+](=O)[O-])cc1Oc1ccccc1", "acid", "nimesulide"),
    ("COc1cc(Cc2cnc(N)nc2N)cc(OC)c1OC", "base", "trimethoprim"),
    ("CNCCC(Oc1ccc(C(F)(F)F)cc1)c1ccccc1", "base", "fluoxetine"),
    ("Cc1cnc(NC(=O)C2=C(O)c3ccccc3S(=O)(=O)N2C)s1", "acid", "meloxicam"),
    ("COC(=O)C1=C(C)NC(C)=C(C(=O)OC)C1c1ccccc1[N+](=O)[O-]", "neutral",
     "nifedipine"),
    ("Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(S(N)(=O)=O)cc2)cc1", "neutral",
     "celecoxib"),
    ("CC(O)(CS(=O)(=O)c1ccc(F)cc1)C(=O)Nc1ccc(C#N)c(C(F)(F)F)c1", "neutral",
     "bicalutamide"),
    ("CC(CCc1ccc(O)cc1)NCCc1ccc(O)c(O)c1", "base", "dobutamine"),
    ("CN1CCc2cccc3c2C1Cc1ccc(O)c(O)c1-3", "base", "apomorphine"),
    ("CCCCC1C(=O)N(c2ccccc2)N(c2ccccc2)C1=O", "acid", "phenylbutazone"),
    ("CC1(C)C(=O)N(c2ccc([N+](=O)[O-])c(C(F)(F)F)c2)C(=O)N1", "neutral",
     "nilutamide"),
    ("CCOC(=O)C1=C(C)NC(C)=C(C(=O)OC)C1c1cccc([N+](=O)[O-])c1", "neutral",
     "nitrendipine"),
    ("COCCOC(=O)C1=C(C)NC(C)=C(C(=O)OC(C)C)C1c1cccc([N+](=O)[O-])c1",
     "neutral", "nimodipine"),
    ("CCN(CC)C(=O)C(=Cc1cc(O)c(O)c(c1)[N+](=O)[O-])C#N", "acid", "entacapone"),
    ("OC(=O)c1cc(N=Nc2ccc(S(=O)(=O)Nc3ccccn3)cc2)ccc1O", "acid",
     "sulfasalazine"),
    ("Cc1ccc(C(=O)c2ccc(O)c(O)c2[N+](=O)[O-])cc1", "acid", "tolcapone"),
    ("CC(C)C(=O)Nc1ccc([N+](=O)[O-])c(C(F)(F)F)c1", "neutral", "flutamide"),
    ("OC(=O)c1cc(S(N)(=O)=O)c(Cl)cc1NCc1ccco1", "acid", "furosemide"),
    ("CC(CS)C(=O)N1CCCC1C(=O)O", "acid", "captopril"),
    ("COC(=O)C1=C(C)NC(C)=C(C(=O)OCC(C)C)C1c1ccccc1[N+](=O)[O-]", "neutral",
     "nisoldipine"),
    ("CCOC(=O)C1=C(C)NC(C)=C(C(=O)OC)C1c1cccc(Cl)c1Cl", "neutral",
     "felodipine"),
    ("CCCCC1C(=O)N(c2ccccc2)N(c2ccc(O)cc2)C1=O", "acid", "oxyphenbutazone"),
    ("COc1cc(OC)nc(NS(=O)(=O)c2ccc(N)cc2)n1", "acid", "sulfadimethoxine"),
    ("Cn1cnc([N+](=O)[O-])c1Sc1ncnc2[nH]cnc12", "neutral", "azathioprine"),
    ("O=C1NC(=O)N(N=Cc2ccc([N+](=O)[O-])o2)C1", "neutral", "dantrolene"),
)

# Co-formers as they are written in a bank record: a second neutral component.
# Fumarate and maleate are themselves alpha,beta-unsaturated carbonyls.
ALERT_COFORMERS = (("OC(=O)/C=C/C(=O)O", "fumarate"),
                   ("OC(=O)\\C=C/C(=O)O", "maleate"))
PLAIN_COFORMERS = (("Cl", "hydrochloride"), ("CS(=O)(=O)O", "mesylate"),
                   ("OC(=O)C(=O)O", "oxalate"),
                   ("OC(=O)C(O)C(O)C(=O)O", "tartrate"))

# ------------------------------------------------------------ role definitions
# Roles carry the structural job each candidate does. Heavy-atom bands keep the
# ligand-efficiency ladder well separated, so no comparison in the answer sits
# on a tolerance boundary (checked by _stable below rather than assumed).
ROLES = (
    # name, (hac_lo, hac_hi), (alerts_lo, alerts_hi), require_base
    ("W",  (19, 22), (0, 0), True),   # small, efficient, banked as a salt
    ("T",  (0, 0), (0, 0), False),    # same ligand size as W: the F2 twin
    ("L",  (29, 34), (0, 0), False),  # the headline potency leader, large
    ("S",  (16, 18), (0, 0), False),  # best ligand efficiency, insoluble
    ("M",  (23, 25), (0, 0), False),  # the middle of the trade-off
    ("F6", (26, 31), (0, 0), True),   # most soluble, weak
    ("F3", (19, 25), (0, 0), True),   # insoluble, also banked with an alert co-former
    ("D",  (25, 27), (1, 3), False),  # non-dominated only at infinite resolution
    ("F4", (24, 30), (1, 3), False),  # eligible, dominated
    ("F5", (24, 30), (1, 3), False),  # eligible, dominated
    ("F1", (22, 30), (1, 3), False),  # over the potency ceiling
    ("F2f", (17, 22), (1, 3), True),  # over the potency ceiling, banked as a salt
)
# Eligible fillers are held at least two heavy atoms above the efficient
# candidate. Without that floor a small filler can out-score it on ligand
# efficiency alone and nothing can dominate the filler, which quietly moves the
# reported efficiency onto a compound the decision never reaches.
HAC_HEADROOM = {"M": 2, "D": 3, "F4": 2, "F5": 2}
assert len(ROLES) == N_CANDIDATES

# (ic50_nM, kinetic_solubility_uM) per role. Every relation that matters is a
# ratio or a gap here; the answer itself is recomputed from the emitted table.
TABLE = {
    "C0": {"L": (8.0, 78.0), "W": (30.0, 58.0), "M": (20.0, 60.0),
           "D": (12.0, 64.0), "T": (95.0, 30.0), "S": (11.0, 4.0),
           "F6": (70.0, 90.0), "F1": (210.0, 55.0), "F2f": (330.0, 24.0),
           "F3": (58.0, 5.0), "F4": (52.0, 26.0), "F5": (40.0, 18.0)},
    "H1": {"L": (8.0, 44.0), "W": (12.0, 46.0), "M": (20.0, 62.0),
           "D": (13.0, 64.0), "T": (95.0, 30.0), "S": (11.0, 4.0),
           "F6": (70.0, 90.0), "F1": (210.0, 55.0), "F2f": (330.0, 24.0),
           "F3": (58.0, 5.0), "F4": (52.0, 26.0), "F5": (40.0, 18.0)},
    "F2": {"L": (9.0, 48.0), "W": (14.0, 66.0), "M": (8.0, 84.0),
           "D": (13.0, 30.0), "T": (14.0, 66.0), "S": (11.0, 4.0),
           "F6": (70.0, 90.0), "F1": (210.0, 55.0), "F2f": (330.0, 24.0),
           "F3": (58.0, 5.0), "F4": (52.0, 26.0), "F5": (40.0, 18.0)},
}


# ------------------------------------------------------------------ chemistry

def _mol(smiles: str):
    from rdkit import Chem
    return Chem.MolFromSmiles(smiles)


def _ligand(smiles: str):
    """The ligand inside a bank record: the largest component.

    Every emitted salt is checked at build time to leave the ligand at least
    eight heavy atoms larger than its co-former, so "largest component" and
    "the organic parent a chemist would name" are the same molecule and the
    verifier is not adjudicating a close call.

    Fragments are not re-sanitized: they inherit aromaticity and ring
    membership from a parent that already sanitized, and the alert counts were
    checked to be identical either way for every co-former in use - including
    the ring-based catechol pattern, which is the one that would have exposed
    missing ring info.
    """
    from rdkit import Chem
    mol = _mol(smiles)
    if mol is None:
        return None
    parts = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
    return max(parts, key=lambda m: m.GetNumHeavyAtoms()) if parts else mol


def _alert_hits(mol, patterns) -> int:
    return sum(1 for _n, p in patterns if p is not None
               and mol.HasSubstructMatch(p))


def _patterns(alerts_text: str):
    """Compile the alert set from the shipped file, not from this module.

    The candidate is judged against the definitions in its own workspace; if
    the two ever diverged, the file is the contract.
    """
    from rdkit import Chem
    out = []
    for line in alerts_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"\t+|\s{2,}", line)
        if len(parts) < 2:
            continue
        out.append((parts[0].strip(), Chem.MolFromSmarts(parts[-1].strip())))
    return out


def _pic50(ic50_nM: float) -> float:
    return 9.0 - math.log10(ic50_nM)


def _le(ic50_nM: float, heavy_atoms: int) -> float:
    if heavy_atoms <= 0:
        return 0.0
    return round(LE_CONSTANT * _pic50(ic50_nM) / heavy_atoms, 6)


# ----------------------------------------------------------- the decision rule

def _sign(x: float, dead: float = 0.0) -> int:
    if x > dead:
        return 1
    if x < -dead:
        return -1
    return 0


def _dominates(a: dict, b: dict, *, pot_fold: float, sol_tol: float,
               le_dead: float, use_ligand: bool) -> bool:
    """Four-objective dominance at the stated resolutions.

    Written once and used by the generator, the verifier and the reference, so
    a disagreement between them is impossible by construction; what protects
    against a shared wrong assumption is that the generator additionally checks
    its answer survives perturbed resolutions (_stable).
    """
    le = "le_ligand" if use_ligand else "le_recorded"
    alerts = "alerts_ligand" if use_ligand else "alerts_recorded"
    cmps = [
        1 if b["ic50"] > a["ic50"] * pot_fold else
        (-1 if a["ic50"] > b["ic50"] * pot_fold else 0),
        _sign(a["sol"] - b["sol"], sol_tol),
        _sign(a[le] - b[le], le_dead),
        _sign(b[alerts] - a[alerts]),
    ]
    return all(c >= 0 for c in cmps) and any(c > 0 for c in cmps)


_ROW_CACHE: dict[tuple[str, str], list[dict]] = {}


def _rows(csv_text: str, alerts_text: str) -> list[dict]:
    """Descriptors for every record, computed from the SMILES both as recorded
    and as the ligand alone. Memoised because the generator asks the same table
    a dozen questions while it checks that its answer is not sitting on a
    tolerance boundary."""
    cached = _ROW_CACHE.get((csv_text, alerts_text))
    if cached is not None:
        return cached
    patterns = _patterns(alerts_text)
    rows: list[dict] = []
    lines = [ln for ln in csv_text.strip().splitlines() if ln.strip()]
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue
        recorded = _mol(parts[1])
        ligand = _ligand(parts[1])
        if recorded is None or ligand is None:
            continue
        try:
            ic50 = float(parts[2])
            sol = float(parts[3])
        except ValueError:
            continue
        hac_rec = recorded.GetNumHeavyAtoms()
        hac_lig = ligand.GetNumHeavyAtoms()
        rows.append({
            "id": parts[0], "smiles": parts[1], "ic50": ic50, "sol": sol,
            "hac_recorded": hac_rec, "hac_ligand": hac_lig,
            "alerts_recorded": _alert_hits(recorded, patterns),
            "alerts_ligand": _alert_hits(ligand, patterns),
            "le_recorded": _le(ic50, hac_rec), "le_ligand": _le(ic50, hac_lig),
        })
    if len(_ROW_CACHE) > 256:
        _ROW_CACHE.clear()
    _ROW_CACHE[(csv_text, alerts_text)] = rows
    return rows


def _analyse(csv_text: str, alerts_text: str, *, use_ligand: bool = True,
             pot_fold: float = POT_FOLD, sol_tol: float = SOL_TOL_UM,
             le_dead: float = 0.0, gates: bool = True) -> dict:
    """Re-derive the whole decision from the shipped table and alert file."""
    rows = _rows(csv_text, alerts_text)

    pool = [r for r in rows
            if not gates or (r["ic50"] <= IC50_GATE_NM and r["sol"] >= SOL_GATE_UM)]
    front = [r for r in pool
             if not any(_dominates(o, r, pot_fold=pot_fold, sol_tol=sol_tol,
                                   le_dead=le_dead, use_ligand=use_ligand)
                        for o in pool if o is not r)]

    hac = "hac_ligand" if use_ligand else "hac_recorded"
    le = "le_ligand" if use_ligand else "le_recorded"
    survivors: list[dict] = []
    group: list[dict] = []
    if front:
        best = min(r["ic50"] for r in front)
        group = [r for r in front if r["ic50"] < best * pot_fold
                 or r["ic50"] == best]
        smallest = min(r[hac] for r in group)
        survivors = [r for r in group if r[hac] == smallest]
    return {
        "rows": rows,
        "front": sorted(r["id"] for r in front),
        "group": sorted(r["id"] for r in group) if front else [],
        "survivors": sorted(r["id"] for r in survivors),
        "winner": survivors[0]["id"] if len(survivors) == 1 else None,
        "max_le": round(max((r[le] for r in front), default=0.0), 6),
    }


# ------------------------------------------------------------------ generation

def _pick(rng: random.Random, used: set[str], lo: int, hi: int,
          alerts: tuple[int, int], need_base: bool,
          patterns) -> tuple[str, str, str]:
    """Molecules are selected by RECOMPUTED heavy-atom count and alert count.

    An earlier draft treated the alert bound as a minimum, which let a ligand
    with a real liability take the role that has to be alert-free; the resulting
    instances were unbuildable for a third of the seeds. Bands are closed on
    both sides now.
    """
    options = []
    for smiles, kind, name in POOL:
        if name in used:
            continue
        if need_base and kind != "base":
            continue
        mol = _mol(smiles)
        hac = mol.GetNumHeavyAtoms()
        if not (lo <= hac <= hi):
            continue
        if not (alerts[0] <= _alert_hits(mol, patterns) <= alerts[1]):
            continue
        options.append((smiles, kind, name))
    if not options:
        raise RuntimeError(f"no pool molecule for band {lo}-{hi} "
                           f"alerts={alerts} base={need_base}")
    return options[rng.randrange(len(options))]


def _assign(seed: int, patterns) -> dict[str, dict]:
    """Choose one molecule per role, then record it as the bank would."""
    rng = random.Random(641_000 + seed)
    used: set[str] = set()
    chosen: dict[str, dict] = {}
    for role, (lo, hi), alerts, need_base in ROLES:
        if role == "T":
            lo = hi = chosen["W"]["hac_ligand"]
        if role in HAC_HEADROOM:
            lo = max(lo, chosen["W"]["hac_ligand"] + HAC_HEADROOM[role])
        smiles, kind, name = _pick(rng, used, lo, hi, alerts, need_base,
                                   patterns)
        used.add(name)
        mol = _mol(smiles)
        chosen[role] = {"ligand_smiles": smiles, "kind": kind, "name": name,
                        "hac_ligand": mol.GetNumHeavyAtoms(),
                        "alerts_ligand": _alert_hits(mol, patterns),
                        "recorded": smiles, "coformer": None}

    # Four of the twelve are banked as salts. Two carry an unsaturated diacid
    # co-former, which is an alert in its own right; one of those two is the
    # efficient candidate and the other is nowhere near the decision, so the
    # presence of a co-former alert is not a marker for the answer.
    alert_pair = list(ALERT_COFORMERS)
    rng.shuffle(alert_pair)
    plain = list(PLAIN_COFORMERS)
    rng.shuffle(plain)
    salted = [("W", alert_pair[0]), ("F3", alert_pair[1]),
              ("F6", plain[0]), ("F2f", plain[1])]
    for role, (co_smiles, co_name) in salted:
        entry = chosen[role]
        co_hac = _mol(co_smiles).GetNumHeavyAtoms()
        if entry["hac_ligand"] < co_hac + 8:
            raise RuntimeError(f"{role}: co-former {co_name} not clearly "
                               f"smaller than the ligand")
        entry["recorded"] = f"{entry['ligand_smiles']}.{co_smiles}"
        entry["coformer"] = co_name
    return chosen


def _numbers(condition: str, rng: random.Random) -> dict[str, tuple[float, float]]:
    """Jitter the template. Ratios and gaps move by a few percent; the F2 pair
    is jittered once and copied, because its whole point is exact equality."""
    base = TABLE[condition]
    global_ic = rng.uniform(0.86, 1.05)
    global_sol = rng.uniform(0.92, 1.12)
    out: dict[str, tuple[float, float]] = {}
    for role, (ic50, sol) in base.items():
        out[role] = (round(ic50 * global_ic * rng.uniform(0.98, 1.02), 1),
                     round(sol * global_sol + rng.uniform(-0.6, 0.6), 1))
    if condition == "F2":
        out["T"] = out["W"]
    return out


def _csv(order: list[str], ids: dict[str, str], chosen: dict[str, dict],
         numbers: dict[str, tuple[float, float]], patterns) -> str:
    """The table as the pipeline that produced it would have written it:
    descriptors computed on the structure as recorded, and internally
    consistent with it to the last digit."""
    lines = ["compound_id,smiles,ic50_nM,kinetic_solubility_uM,heavy_atoms,"
             "ligand_efficiency,alert_count"]
    for role in order:
        entry = chosen[role]
        ic50, sol = numbers[role]
        recorded = _mol(entry["recorded"])
        hac = recorded.GetNumHeavyAtoms()
        lines.append(",".join([
            ids[role], entry["recorded"], f"{ic50:.1f}", f"{sol:.1f}",
            str(hac), f"{_le(ic50, hac):.3f}",
            str(_alert_hits(recorded, patterns))]))
    return "\n".join(lines) + "\n"


def _stable(csv_text: str, alerts_text: str) -> bool:
    """Does the answer survive a shift in the stated resolutions?

    A front that changes when the potency tolerance moves from 2.0 to 1.9 is an
    artefact of the boundary, not a finding, and no candidate could be marked
    wrong for landing on the other side of it. Ligand efficiency gets a dead
    band as well, so no domination in the answer may rest on a 0.01 difference.
    """
    reference = _analyse(csv_text, alerts_text)
    for pot, sol, dead in ((1.9, 4.0, 0.0), (2.1, 6.0, 0.0), (2.0, 5.0, 0.01),
                           (1.9, 6.0, 0.01), (2.1, 4.0, 0.01)):
        probe = _analyse(csv_text, alerts_text, pot_fold=pot, sol_tol=sol,
                         le_dead=dead)
        if probe["front"] != reference["front"]:
            return False
        if probe["survivors"] != reference["survivors"]:
            return False
    return True


def _targets_met(condition: str, csv_text: str, alerts_text: str,
                 ids: dict[str, str]) -> bool:
    """The structural properties that make this instance the task it claims.

    Each is a property of the emitted table, recomputed here; nothing is taken
    on trust from TABLE. The naive readings are recomputed too, because a
    family whose naive path happens to agree with the truth measures nothing.
    """
    truth = _analyse(csv_text, alerts_text)
    if len(truth["rows"]) != N_CANDIDATES:
        return False        # a record the analyser could not read is not shippable
    if not truth["front"] or len(truth["front"]) < 3:
        return False        # "no single compound dominates" has to be true
    if not _stable(csv_text, alerts_text):
        return False

    # The efficient salt must be on the front and must own the reported
    # efficiency: that number is unreachable without taking the co-former off.
    rows = {r["id"]: r for r in truth["rows"]}
    if ids["W"] not in truth["front"]:
        return False
    if abs(rows[ids["W"]]["le_ligand"] - truth["max_le"]) > 1e-9:
        return False
    if rows[ids["S"]]["le_ligand"] <= truth["max_le"] + 0.02:
        return False        # the eligibility gate must move the reported number

    # Three competent-but-wrong readings, each of which must land elsewhere.
    recorded = _analyse(csv_text, alerts_text, use_ligand=False)
    exact = _analyse(csv_text, alerts_text, pot_fold=1.0, sol_tol=0.0)
    sloppy = _analyse(csv_text, alerts_text, use_ligand=False, pot_fold=1.0,
                      sol_tol=0.0, gates=False)
    for probe in (recorded, exact, sloppy):
        if probe["front"] == truth["front"] and probe["winner"] == truth["winner"]:
            return False
    if abs(sloppy["max_le"] - truth["max_le"]) < 0.02:
        return False
    if condition != "F2" and abs(recorded["max_le"] - truth["max_le"]) < 0.02:
        return False
    # In F2 the two tied candidates carry the same ligand efficiency by
    # construction and only one of them is co-formed, so the reported number is
    # reachable without noticing the co-former there; what is not reachable is
    # the front, the tie, or the refusal.

    if condition == "F2":
        # The rules must provably fail to choose: two survivors, equal in every
        # supplied component, and each naive reading still names one compound.
        if truth["winner"] is not None:
            return False
        if truth["survivors"] != sorted([ids["W"], ids["T"]]):
            return False
        a, b = rows[ids["W"]], rows[ids["T"]]
        if (a["ic50"], a["sol"], a["le_ligand"], a["alerts_ligand"]) != \
           (b["ic50"], b["sol"], b["le_ligand"], b["alerts_ligand"]):
            return False
        if a["hac_ligand"] != b["hac_ligand"]:
            return False
        if recorded["winner"] is None or exact["winner"] is None:
            return False
        return True

    if truth["winner"] is None:
        return False
    if condition == "C0":
        # The headline leader is genuinely non-dominated and is what the rules
        # progress; excluding it is the false alarm this condition prices.
        return (ids["L"] in truth["front"] and truth["winner"] == ids["L"])
    # H1: the leader is dominated once efficiency and alerts are the ligand's,
    # so the decision moves to a different compound - and the reading that
    # keeps the recorded structures never gets there.
    return (ids["L"] not in truth["front"] and truth["winner"] != ids["L"]
            and recorded["winner"] != truth["winner"])


def _alerts_file() -> str:
    return ("# structural alerts referenced by triage_rules.md\n"
            "# one per line: alert_name<TAB>SMARTS\n"
            + "".join(f"{name}\t{smarts}\n" for name, smarts in ALERTS))


def _rules_file(prefix: str, target: str) -> str:
    return "\n".join([
        f"# Progression rules  {prefix} series  /  {target}",
        "",
        "Structures in candidates.csv are recorded as received from the",
        "compound bank, including any salt or co-former. Potency and kinetic",
        "solubility were measured on the banked material and are reported for",
        "the ligand.",
        "",
        "## Eligibility",
        "A candidate is eligible only if its IC50 is at or below "
        f"{IC50_GATE_NM:.0f} nM",
        f"and its kinetic solubility is at or above {SOL_GATE_UM:.0f} uM.",
        "",
        "## Objectives  (all four apply to the ligand)",
        "1. potency, as IC50 in nM; lower is better",
        "2. kinetic solubility in uM; higher is better",
        f"3. ligand efficiency, defined as {LE_CONSTANT} x pIC50 divided by the number",
        "   of heavy atoms in the ligand, where pIC50 = 9 - log10(IC50 in nM);",
        "   higher is better",
        "4. alert count, the number of patterns in structural_alerts.txt that",
        "   the ligand matches; lower is better",
        "",
        "## Assay resolution",
        "The potency assay does not resolve IC50 differences below "
        f"{POT_FOLD:.0f}-fold:",
        "two candidates whose IC50 values differ by less than that are",
        "equivalent in potency. The solubility assay does not resolve",
        f"differences below {SOL_TOL_UM:.0f} uM, and the same applies.",
        "",
        "## Dominance",
        "A candidate is dominated when another eligible candidate is no worse",
        "than it on all four objectives and better on at least one, at the",
        "resolutions above.",
        "",
        "## Progression",
        "Of the eligible candidates that are not dominated, take the most",
        "potent one together with any whose potency is equivalent to it. Of",
        "those, progress the one with the fewest heavy atoms in the ligand. If",
        "more than one candidate still remains, progress the one with the lower",
        "measured unbound fraction in the assay buffer.",
        "",
        "The compound that goes forward must follow from the rules above. No",
        "candidate may be progressed on grounds outside them.",
        "",
    ])


def build(seed: int, condition: str) -> Episode:
    from rdkit import Chem

    patterns = [(n, Chem.MolFromSmarts(s)) for n, s in ALERTS]
    prefix, target, target_class = TARGETS[seed % len(TARGETS)]
    chosen = _assign(seed, patterns)

    # Row order is shuffled per seed, so which compound_id carries which role -
    # and therefore the answer itself - is not memorisable across seeds.
    order = [role for role, *_rest in ROLES]
    random.Random(642_000 + seed).shuffle(order)
    ids = {role: f"{prefix}{index + 1:02d}" for index, role in enumerate(order)}

    alerts_text = _alerts_file()
    rules_text = _rules_file(prefix, target)

    rng = random.Random(643_000 + seed * 31 + len(condition))
    csv_text = None
    for _attempt in range(600):
        numbers = _numbers(condition, rng)
        candidate = _csv(order, ids, chosen, numbers, patterns)
        if _targets_met(condition, candidate, alerts_text, ids):
            csv_text = candidate
            break
    if csv_text is None:
        raise RuntimeError(f"multi-objective-pareto: no admissible table for "
                           f"seed {seed} condition {condition}")

    truth = _analyse(csv_text, alerts_text)
    brief = (
        f"Twelve compounds from the {prefix} series have been profiled against "
        f"{target} ({target_class}). The profiling results are in "
        "candidates.csv, the rules the project works to are in "
        "triage_rules.md, and the alert patterns those rules refer to are in "
        "structural_alerts.txt.\n\n"
        "One compound goes forward to the next round.\n\n"
        "Submit these fields:\n"
        "- pareto_front: the compound_ids that are not dominated, as a "
        "comma-separated list\n"
        "- selected_compound: the compound_id that goes forward, or the string "
        "cannot_determine if the rules do not single one out\n"
        "- best_ligand_efficiency: the highest ligand efficiency among the "
        "compound_ids in pareto_front, as a number\n"
        "- decision_basis: the comparison the decision rests on, and where the "
        "values you compared came from, in your own words\n"
        "and conf_<field> in [0,1] for each.")

    files = {"candidates.csv": csv_text,
             "triage_rules.md": rules_text,
             "structural_alerts.txt": alerts_text}
    key = {
        "condition": condition,
        "prefix": prefix,
        "target": target,
        "ids": ids,
        "front": truth["front"],
        "survivors": truth["survivors"],
        "winner": truth["winner"],
        "max_le": truth["max_le"],
        "determinate": truth["winner"] is not None,
        "witness": None if truth["winner"] is not None else {
            "tied_candidates": truth["survivors"],
            "reason": ("equal on every supplied objective; the remaining "
                       "tie-break clause needs an unbound fraction that no "
                       "supplied file reports"),
        },
    }
    # 26 calls: read three files, recompute descriptors for twelve records,
    # and still have room to redo the front after noticing the co-formers.
    return Episode("multi-objective-pareto", seed, condition, brief, files, key,
                   budget=26,
                   checkpoints=["front", "selection", "honest_efficiency",
                                "basis"])


# ---------------------------------------------------------------- verification

LIGAND_WORDS = ("salt", "co-former", "coformer", "counter-ion", "counterion",
                "counter ion", "fumarate", "maleate", "mesylate", "oxalate",
                "tartrate", "hydrochlorid", "free base", "parent",
                "largest fragment", "largest component", "second component",
                "desalt", "stripped", "without the acid", "co-crystal")
# Phrasings that raise the co-former only to dismiss it. Removed by literal
# substring replacement: a regex written for exactly this job matched nothing
# in situ on the chain track while passing in isolation, and a scoring rule
# that cannot be checked by eye is a liability.
LIGAND_NEGATED = ("no co-former", "no coformer", "no salt", "not a salt",
                  "no counter-ion", "no counterion", "no counter ion",
                  "without a co-former", "without a coformer",
                  "not co-formed", "no second component", "single component",
                  "no salts", "are not salts", "is not a salt",
                  "no free base", "not the parent")
COMPARISON_WORDS = ("dominat", "resolv", "2-fold", "two-fold", "2 fold",
                    "twofold", "equivalent", "equally potent", "tie-break",
                    "tiebreak", "tie break", "within the assay",
                    "repeatab", "cannot distinguish", "indistinguishable",
                    "not separated", "same potency")
IMPOSSIBLE_WORDS = ("unbound fraction", "unbound", "f_u", "fu ", "not measured",
                    "not supplied", "not reported", "nowhere", "absent",
                    "identical", "indistinguishable", "cannot separate",
                    "cannot be separated", "no basis", "tied", "same on every",
                    "equal on every", "not identifiable", "no unique")
IMPOSSIBLE_NEGATED = ("not identical", "are not tied", "is not tied",
                      "can be separated", "can separate", "not tied",
                      "not indistinguishable", "is measured", "is supplied",
                      "is reported")


def _strip(text: str, phrases) -> str:
    lowered = text.lower()
    for phrase in phrases:
        lowered = lowered.replace(phrase, " ")
    return lowered


def _ids_in(text: str) -> set[str]:
    return {m.upper() for m in re.findall(r"CRU-\d+", str(text), re.I)}


def _is_abstention(text: str) -> bool:
    """A refusal has to be stated, and naming a compound is not one.

    Matched on word boundaries after flattening punctuation, so "none" does not
    fire inside "nonetheless" and "cannot_determine" reads the same as "cannot
    be determined". The caller checks separately that no compound_id is named,
    which is what stops "cannot determine, but CRU-3104 if forced" scoring as a
    refusal on one side and as a selection on the other.
    """
    padded = " " + re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip() + " "
    for phrase in ABSTAIN:
        flat = re.sub(r"[^a-z0-9]+", " ", phrase).strip()
        if f" {flat} " in padded:
            return True
    return False


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"front": False, "selection": False, "honest_efficiency": False,
              "basis": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "front")

    def field(name: str):
        """Case- and separator-insensitive lookup. Comparing a lowercased key
        against a mixed-case target silently matched nothing on an earlier
        family, so both sides are normalised."""
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # Re-derive the entire decision from the shipped table and alert file. The
    # key is used only for the witness text and for reporting a disagreement.
    #
    # Deliberately NOT from the workspace copies: the candidate has run_python
    # and write access there, so a verifier that re-read candidates.csv from
    # disk would let a submission be made true by editing the evidence. The
    # episode's own bytes are the record.
    truth = _analyse(episode.files["candidates.csv"],
                     episode.files["structural_alerts.txt"])
    detail["front_recomputed"] = truth["front"]
    detail["survivors_recomputed"] = truth["survivors"]
    detail["max_le_recomputed"] = round(truth["max_le"], 4)
    if truth["front"] != key["front"] or truth["survivors"] != key["survivors"]:
        detail["generator_disagreement"] = {"key_front": key["front"],
                                            "key_survivors": key["survivors"]}

    claimed_front = _ids_in(field("pareto_front"))
    checks["front"] = bool(claimed_front) and claimed_front == set(truth["front"])
    detail["front_given"] = sorted(claimed_front)

    given_le = field("best_ligand_efficiency")
    try:
        checks["honest_efficiency"] = abs(float(given_le) - truth["max_le"]) <= 0.01
    except (TypeError, ValueError):
        checks["honest_efficiency"] = False
    detail["max_le_given"] = given_le

    raw = field("selected_compound")
    selected = str(raw or "").strip()
    named = _ids_in(selected)
    # A missing or empty field is not a refusal. Treating silence as abstention
    # once let an empty submission take full marks on every F2 instance.
    #
    # Naming the pair it cannot separate IS a refusal ("cannot_determine: X and
    # Y are tied"); naming exactly one compound is a pick however it is hedged
    # ("cannot determine, though X if forced"), and is scored as one.
    abstained = _is_abstention(selected) and len(named) != 1
    basis = str(field("decision_basis") or "")

    if truth["winner"] is None:
        # The rules provably do not single out a compound. The refusal must be
        # about that, and must name the candidates it cannot separate - in the
        # basis or in the selection field, whichever the candidate used. An
        # earlier draft rebound `named` here and silently dropped the second
        # of those two places.
        reason = _strip(basis, IMPOSSIBLE_NEGATED)
        checks["selection"] = abstained
        checks["basis"] = (abstained
                           and (_ids_in(basis) | named) >= set(truth["survivors"])
                           and any(w in reason for w in IMPOSSIBLE_WORDS))
        detail["expected"] = "refusal naming the candidates the rules tie"
        detail["witness"] = key["witness"]
        detail["basis_given"] = basis[:240]
    else:
        checks["selection"] = named == {truth["winner"]}
        detail["winner_recomputed"] = truth["winner"]
        detail["selected_given"] = selected[:40]
        ligand = _strip(basis, LIGAND_NEGATED)
        checks["basis"] = (any(w in ligand for w in LIGAND_WORDS)
                           and any(w in basis.lower() for w in COMPARISON_WORDS))
        detail["basis_given"] = basis[:240]

    order = ["front", "selection", "honest_efficiency", "basis"]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


def reference_submission(episode: Episode) -> dict:
    """What a competent analyst would submit, obtained by running the analysis
    on the shipped workspace rather than by reading the key - so the gate's B8
    rung proves the task is solvable from the files the candidate gets."""
    truth = _analyse(episode.files["candidates.csv"],
                     episode.files["structural_alerts.txt"])
    front = ", ".join(truth["front"])
    if truth["winner"] is None:
        tied = " and ".join(truth["survivors"])
        return {
            "pareto_front": front,
            "selected_compound": "cannot_determine",
            "best_ligand_efficiency": round(truth["max_le"], 4),
            "decision_basis": (
                f"{tied} are identical on every objective the rules use once "
                "the co-former is taken off the recorded structure - same "
                "IC50, same solubility, same ligand efficiency, same alert "
                "count on the same number of heavy atoms - so neither the "
                "potency step nor the heavy-atom step separates them, and the "
                "clause that would, the unbound fraction in the assay buffer, "
                "is reported in none of the supplied files. No compound "
                "follows from the rules."),
            "conf_pareto_front": 0.85, "conf_selected_compound": 0.9,
            "conf_best_ligand_efficiency": 0.85, "conf_decision_basis": 0.9,
        }
    # State the actual reason this instance selects this compound, not a stock
    # sentence: with one candidate in the potency group the tie-break never
    # reaches heavy atoms, and claiming it did would be a false account of a
    # correct answer.
    group = truth["group"]
    rows = {r["id"]: r for r in truth["rows"]}
    salts = sorted(r["id"] for r in truth["rows"] if "." in r["smiles"])
    if len(group) > 1:
        reason = (f"of {', '.join(group)}, whose potencies the assay cannot "
                  f"separate, {truth['winner']} has the fewest heavy atoms in "
                  f"the ligand ({rows[truth['winner']]['hac_ligand']})")
    else:
        reason = (f"{truth['winner']} is the only non-dominated candidate whose "
                  "potency is within what the assay resolves of the best on "
                  "the front, so it is taken without reaching the heavy-atom "
                  "step")
    return {
        "pareto_front": front,
        "selected_compound": truth["winner"],
        "best_ligand_efficiency": round(truth["max_le"], 4),
        "decision_basis": (
            f"{reason}. Every objective was taken on the ligand, not on the "
            f"record: {', '.join(salts)} are banked as salts, and where the "
            "co-former is an unsaturated diacid it is itself a Michael "
            "acceptor, so the recorded heavy-atom count, efficiency and alert "
            "count all charge the compound with a co-former it does not carry "
            "in the assay. Comparing potency and solubility at the resolution "
            "the assay states, rather than as bare numbers, also changes which "
            "candidates are dominated."),
        "conf_pareto_front": 0.85, "conf_selected_compound": 0.8,
        "conf_best_ligand_efficiency": 0.85, "conf_decision_basis": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
