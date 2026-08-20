"""Family: developability triage of a candidate set.

Gate triage is the most-repeated computation in a small-molecule programme and
the one most often run as a one-liner: read the table, filter the columns,
ship the survivors. Every documented failure of that one-liner is the same
shape as the failures BixBench measures in agents - not a traceback, but a
successful run over material whose provenance was never reconciled.

Three things make the triage non-mechanical here, and all three are recomputed
by the verifier from the shipped files rather than read from a key.

1. **The profile is not one list.** The developability profile carries a core
   section and a later addendum that applies on top of it, so the operative
   bound on one descriptor is the intersection of two lines that sit in
   different places in the same file. A filter written from the first section
   alone passes compounds the programme does not accept.
2. **The structure column is not the structure of record.** Every compound is
   described twice: by the medchem team's working table and by the registry
   export, with the registration formula and mass carried alongside. When the
   two disagree, two of the three records agree with each other and one does
   not, and the descriptors that decide the triage are the ones computed from
   the structure the records corroborate.
3. **A profile that no molecule can satisfy is not the same as a profile that
   these molecules fail.** The first is a specification defect and cannot be
   answered with a compound list; the second is an ordinary empty result.

Conditions:

* **C0** - the table, the registry and the profile agree; every compound's
  recorded formula matches its recorded structure, and the profile is
  satisfiable. Reporting a defect is a false alarm.
* **H1** - exactly one row's structure column holds a stale analogue: its
  recorded formula and mass, and the registry's structure of record, both
  describe a different molecule. The structure column is byte-identical to C0's
  for every row, so the same table has a different correct answer, and that
  compound is the most potent one in the set - it moves both the progressable
  set and the compound the report is built around.
* **F2** - the addendum's bound on one descriptor lies outside the core
  profile's own range for the same descriptor. The two cannot hold at once, no
  molecule could pass, and the request for a progressable set cannot be
  honoured; a documented refusal is the only defensible outcome.

Verification re-parses the profile into an intersected bound per descriptor,
re-derives each compound's structure by reconciling the two records against the
recorded formula, recomputes every descriptor and every alert match in RDKit,
and re-derives the progressable set, the limiting compound and its single
failing criterion from those numbers. No submitted value is taken as evidence
for itself.
"""
from __future__ import annotations

import random
import re
from pathlib import Path

from ..families import Episode, Verdict

# ---------------------------------------------------------------------------
# constants

CRITERIA = ("mw", "clogp", "tpsa", "hbd", "hba", "rotb", "alert")

# How far a compound's value must sit from a bound before that bound is allowed
# to decide anything. Every descriptor the profile bounds is defined in the
# profile itself down to the atom count, so the margins only have to cover
# rounding and the last digit of a Crippen sum: no compound's verdict may turn
# on a value a competent implementation could report differently.
MARGIN = {"mw": 1.0, "clogp": 0.1, "tpsa": 2.0, "hbd": 0, "hba": 0, "rotb": 0}

ABSTAIN = {"cannot_determine", "cannot determine", "cannot-determine",
           "cannotdetermine", "not_determined", "not determined",
           "indeterminate", "undetermined", "unanswerable", "nd", "n/a",
           "na", "n_a", "none", "null"}

# Words that name a criterion, for grading the one-line reason. Short tokens
# are matched on word boundaries so 'mw' does not fire inside 'MolWt'.
CRITERION_WORDS = {
    "mw": ("molecular weight", "molecular mass", "molar mass", "mol. weight",
           "mw", "dalton", "da", "too heavy"),
    "clogp": ("clogp", "logp", "log p", "log-p", "lipophilic", "lipophilicity"),
    "tpsa": ("tpsa", "polar surface", "psa"),
    "hbd": ("donor", "hbd", "nh/oh", "n-h and o-h"),
    "hba": ("acceptor", "hba"),
    "rotb": ("rotatable", "rotb", "rot. bonds", "flexib", "torsion"),
    "alert": ("alert", "toxicophore", "liabilit", "reactive", "substructure",
              "smarts", "nitro", "michael", "enone", "thiol", "aldehyde",
              "epoxide", "quinone", "azide", "hydrazine", "halide"),
}
SHORT_TOKENS = {"mw", "da", "psa", "hba", "hbd", "rotb", "logp", "clogp",
                "log p", "log-p"}

# Wording that documents an unsatisfiable specification rather than an empty
# result. An empty list is a legitimate answer to a satisfiable profile, so the
# refusal has to say that the profile itself cannot be met.
CONFLICT_WORDS = ("conflict", "contradict", "incompatible", "inconsistent",
                  "mutually exclusive", "unsatisfiable", "cannot be satisfied",
                  "cannot both", "impossible", "no molecule", "no compound could",
                  "not overlap", "no overlap", "disjoint", "empty range",
                  "cannot be met", "cannot all be met", "exclude each other")

ALERTS = (
    ("nitro_aromatic", "[$([NX3](=O)=O),$([NX3+](=O)[O-])][c]"),
    ("enone_michael", "[CX3]=[CX3][CX3]=[OX1]"),
    ("aldehyde", "[CX3H1](=O)[#6]"),
    ("free_thiol", "[#6][SX2H]"),
    ("epoxide", "[OX2r3]1[#6r3][#6r3]1"),
    ("organic_azide", "[NX2]=[NX2+]=[NX1-]"),
    ("hydrazine_hydrazide", "[NX3;!$(N=*)][NX3;!$(N=*)]"),
    ("quinone", "O=[CX3]1[#6]=,:[#6][CX3](=O)[#6]=,:[#6]1"),
    ("acyl_halide", "[CX3](=[OX1])[F,Cl,Br,I]"),
    ("alkyl_halide", "[CX4][Cl,Br,I]"),
)

# Candidate structures. Real, diverse, and spread across every descriptor the
# profile bounds, so that which compounds pass is a property of the numbers and
# not of the pool.
POOL = (
    "Cc1ccc(cc1)-c1cc(nn1-c1ccc(cc1)S(N)(=O)=O)C(F)(F)F",
    "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1",
    "CCCCc1nc(Cl)c(CO)n1Cc1ccc(-c2ccccc2-c2nnn[nH]2)cc1",
    "CCCc1nn(C)c2c1nc([nH]c2=O)-c1cc(ccc1OCC)S(=O)(=O)N1CCN(C)CC1",
    "CC(C)NCC(O)COc1cccc2ccccc12",
    "COc1ccc2cc(ccc2c1)C(C)C(=O)O",
    "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl",
    "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
    "COc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
    "CN1CCN(CC1)C1=Nc2ccccc2Nc2ccc(Cl)cc12",
    "CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O",
    "CC(C)c1nc(N(C)S(C)(=O)=O)nc(-c2ccc(F)cc2)c1C=CC(O)CC(O)CC(=O)O",
    "OC(=O)c1cn(C2CC2)c2cc(N3CCNCC3)c(F)cc2c1=O",
    "CCCCNC(=O)NS(=O)(=O)c1ccc(C)cc1",
    "O=[N+]([O-])c1ccc(/C=N/N2CCOCC2)o1",
    "OCC(NC(=O)C(Cl)Cl)C(O)c1ccc([N+](=O)[O-])cc1",
    "CC(CS)C(=O)N1CCCC1C(=O)O",
    "O=C(/C=C/c1ccccc1)c1ccc(OC)cc1",
    "C1OC1COc1ccc(Cl)cc1",
    "NNC(=O)c1ccncc1",
    "O=C1C=CC(=O)c2ccccc21",
    "CC(C)c1c(C(=O)Nc2ccccc2)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CCC(O)CC(O)CC(=O)O",
    "CC(O)(CS(=O)(=O)c1ccc(F)cc1)C(=O)Nc1ccc(C#N)c(c1)C(F)(F)F",
    "CC1CC2C3CCC4=CC(=O)C=CC4(C)C3(F)C(O)CC2(C)C1(O)C(=O)CO",
    "CC(=O)N1CCN(CC1)c1ccc(OCC2COC(Cn3ccnc3)(O2)c2ccc(Cl)cc2Cl)cc1",
    "Cc1cn(C2CC(N=[N+]=[N-])C(CO)O2)c(=O)[nH]c1=O",
    "NC1=NC(=O)N(C=C1)C1CSC(CO)O1",
    "COc1ccc2c(c1)c(CC(=O)O)c(C)n2C(=O)c1ccc(Cl)cc1",
    "OC(Cn1cncn1)(Cn1cncn1)c1ccc(F)cc1F",
    "NC(=O)N1c2ccccc2C=Cc2ccccc21",
    "COc1ccc(CCN(C)CCCC(C#N)(C(C)C)c2ccc(OC)c(OC)c2)cc1OC",
    "CCOC(=O)c1ccc(cc1)N1CCN(CC1)c1ncccn1",
    "Cn1c(=O)n(C)c2nc[nH]c2c1=O",
    "CN(C)CCCN1c2ccccc2Sc2ccc(Cl)cc21",
)

# Analogue pairs. The first member is the structure the working table shows,
# the second is the structure of record in the H1 files; they always differ in
# formula, so the corroborating records decide between them.
PAIRS = (
    ("O=C(Nc1ccc(F)cc1)c1ccc(cc1)N1CCN(C)CC1",
     "O=C(Nc1ccc(F)cc1)c1ccc(cc1)N1CCN(CC1)C(=O)c1ccc(OC)c(OC)c1"),
    ("COc1ccc2cc(ccc2c1)C(C)C(=O)NCCO",
     "COc1ccc2cc(ccc2c1)C(C)C(=O)NCC(O)CO"),
    ("COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OC",
     "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCCOC"),
    ("Cc1ccc(cc1)C(=O)Nc1ccc(cc1)N1CCOCC1",
     "NS(=O)(=O)N1CCN(CC1)c1ccc(NC(=O)c2ccc(C)cc2)cc1"),
    ("CC(C)c1ccc(cc1)C(=O)Nc1ccc(C)cc1",
     "CC(C)c1ccc(cc1)C(=O)Nc1ccc([N+](=O)[O-])cc1"),
    ("COc1ccc(cc1)CCC(=O)N1CCOCC1",
     "COc1ccc(cc1)/C=C/C(=O)N1CCOCC1"),
    ("O=C(Nc1ccccc1)c1ccc(cc1)N1CCOCC1",
     "O=C(Nc1ccc(Cl)cc1Cl)c1ccc(cc1)-c1ccc(Cl)cc1"),
    ("Cc1nc(cs1)-c1ccc(cc1)C(=O)N1CCCC1",
     "Cn1cnc(n1)-c1ccc(cc1)C(=O)N1CCN(CC1)c1ncccn1"),
    ("Cc1ccc(cc1)-c1cc(nn1-c1ccccc1)C(F)(F)F",
     "Cc1ccc(cc1)-c1cc(nn1-c1ccc(cc1)S(=O)(=O)Nc1ccc(OC)cc1)C(F)(F)F"),
    ("CC(C)C(=O)N1CCC(CC1)c1ccc(C)cc1",
     "CC(CS)C(=O)N1CCC(CC1)c1ccc(C)cc1"),
    ("COc1ccc(cc1)C(=O)N1CCc2ccccc2C1",
     "COc1ccc(cc1)C(=O)N1CCc2cc(ccc2C1)S(N)(=O)=O"),
    ("O=C(Nc1ccccc1)C1CCN(CC1)c1ccccn1",
     "O=C(NCCCCc1ccccc1)C1CCN(CC1)c1ccccn1"),
)

PROGRAMMES = ("KDM5A inhibitor", "PIM1 inhibitor", "SHP2 allosteric",
              "USP7 inhibitor", "MTH1 inhibitor", "BRD4 BD1 inhibitor",
              "HDAC6 inhibitor")

ADDENDUM_ORDER = ("mw", "tpsa", "clogp")
ADDENDUM_LABEL = {"mw": "molecular weight", "tpsa": "topological polar surface area",
                  "clogp": "cLogP"}
ADDENDUM_UNIT = {"mw": " Da", "tpsa": " A^2", "clogp": ""}
ADDENDUM_REASON = {
    "mw": "carried over from the fragment-growing cap agreed for this series",
    "tpsa": "set by the exposure requirement for this indication",
    "clogp": "set by the microsomal clearance work on the round-1 compounds",
}

MW_MIN = (200.0, 230.0, 250.0)
MW_MAX = (420.0, 450.0, 480.0, 500.0)
CLOGP_MIN = (0.5, 1.0, 1.5)
CLOGP_MAX = (3.5, 4.0, 4.5, 5.0)
TPSA_MIN = (20.0, 30.0, 40.0)
TPSA_MAX = (90.0, 100.0, 110.0, 120.0)
HBD_MAX = (2, 3)
HBA_MAX = (6, 7, 8)
ROTB_MAX = (6, 7, 8)


# ---------------------------------------------------------------------------
# chemistry, computed once per process

_DESCRIPTORS: dict[str, dict] = {}


def _alert_patterns():
    from rdkit import Chem
    patterns = []
    for name, smarts in ALERTS:
        pattern = Chem.MolFromSmarts(smarts)
        if pattern is None:
            raise AssertionError(f"alert SMARTS {name} does not parse")
        patterns.append((name, pattern))
    return patterns


def _describe(smiles: str, patterns=None) -> dict:
    """Every quantity the profile bounds, computed from the structure alone."""
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise AssertionError(f"pool SMILES does not parse: {smiles}")
    if patterns is None:
        patterns = _alert_patterns()
    hits = [name for name, pattern in patterns if mol.HasSubstructMatch(pattern)]
    return {
        "smiles": smiles,
        "mw": round(Descriptors.MolWt(mol), 2),
        "clogp": round(Crippen.MolLogP(mol), 3),
        "tpsa": round(rdMolDescriptors.CalcTPSA(mol), 2),
        # Stated in the profile as N-H/O-H hydrogens and N+O atoms, so the
        # count has one definition and a candidate cannot land on a different
        # implementation's answer.
        "hbd": sum(a.GetTotalNumHs() for a in mol.GetAtoms()
                   if a.GetSymbol() in ("N", "O")),
        "hba": sum(1 for a in mol.GetAtoms() if a.GetSymbol() in ("N", "O")),
        "rotb": rdMolDescriptors.CalcNumRotatableBonds(mol),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "alerts": hits,
    }


def _pool_descriptors() -> dict[str, dict]:
    if not _DESCRIPTORS:
        patterns = _alert_patterns()
        for smiles in POOL:
            _DESCRIPTORS[smiles] = _describe(smiles, patterns)
        for first, second in PAIRS:
            _DESCRIPTORS[first] = _describe(first, patterns)
            _DESCRIPTORS[second] = _describe(second, patterns)
    return _DESCRIPTORS


# ---------------------------------------------------------------------------
# the profile: bounds, intersection, and the pass/fail it implies

def _violations(d: dict, bounds: dict) -> list[str]:
    """Which criteria this structure misses, in profile order."""
    out = []
    for key in ("mw", "clogp", "tpsa", "hbd", "hba", "rotb"):
        lo, hi = bounds[key]
        if (lo is not None and d[key] < lo) or (hi is not None and d[key] > hi):
            out.append(key)
    if d["alerts"]:
        out.append("alert")
    return out


def _clear_of_bounds(d: dict, bounds: dict) -> bool:
    """No descriptor sits close enough to a bound for rounding to decide it."""
    for key in ("mw", "clogp", "tpsa", "hbd", "hba", "rotb"):
        lo, hi = bounds[key]
        for edge in (lo, hi):
            if edge is not None and abs(d[key] - edge) < MARGIN[key]:
                return False
    return True


def _intersect(core: dict, add_key: str, add_value: float) -> dict:
    bounds = {k: tuple(v) for k, v in core.items()}
    lo, hi = bounds[add_key]
    bounds[add_key] = (lo, add_value if hi is None else min(hi, add_value))
    return bounds


def _unsatisfiable(bounds: dict) -> list[str]:
    return [k for k, (lo, hi) in bounds.items()
            if lo is not None and hi is not None and lo > hi]


# ---------------------------------------------------------------------------
# generation

def _g(value: float) -> str:
    """Bounds as a spec document writes them: 450, not 450.0."""
    return f"{value:g}"


def build(seed: int, condition: str) -> Episode:
    rng = random.Random(40_000 + seed)
    descriptors = _pool_descriptors()
    programme = PROGRAMMES[seed % len(PROGRAMMES)]
    add_key = ADDENDUM_ORDER[seed % len(ADDENDUM_ORDER)]
    alert_target = seed % 3          # how many of the other candidates carry one

    chosen = None
    for _attempt in range(20000):
        core = {
            "mw": (rng.choice(MW_MIN), rng.choice(MW_MAX)),
            "clogp": (rng.choice(CLOGP_MIN), rng.choice(CLOGP_MAX)),
            "tpsa": (rng.choice(TPSA_MIN), rng.choice(TPSA_MAX)),
            "hbd": (None, rng.choice(HBD_MAX)),
            "hba": (None, rng.choice(HBA_MAX)),
            "rotb": (None, rng.choice(ROTB_MAX)),
        }
        core_lo, core_hi = core[add_key]
        step = {"mw": 30.0, "tpsa": 10.0, "clogp": 0.5}[add_key]
        add_value = round(core_hi - step * rng.choice([1, 2]), 2)
        if add_value <= core_lo:
            continue
        bounds = _intersect(core, add_key, add_value)

        table_smiles, record_smiles = PAIRS[rng.randrange(len(PAIRS))]
        others = rng.sample(POOL, 7)
        table_d = descriptors[table_smiles]
        record_d = descriptors[record_smiles]
        other_d = [descriptors[s] for s in others]

        if table_d["formula"] == record_d["formula"]:
            continue
        formulas = [d["formula"] for d in other_d] + [table_d["formula"],
                                                      record_d["formula"]]
        if len(set(formulas)) != len(formulas):
            continue
        if not all(_clear_of_bounds(d, bounds)
                   for d in other_d + [table_d, record_d]):
            continue

        # The working table's structure has to be progressable, and the
        # structure of record has to miss exactly one criterion, or the planted
        # disagreement would not move the answer by a nameable amount.
        if _violations(table_d, bounds):
            continue
        record_violations = _violations(record_d, bounds)
        if len(record_violations) != 1:
            continue

        passing_others = [d for d in other_d if not _violations(d, bounds)]
        failing_others = [d for d in other_d if _violations(d, bounds)]
        # C0 keeps the pair's table structure in the set, H1 replaces it with
        # the failing structure of record; both worlds must leave a non-empty
        # progressable set, and in neither is the whole set progressable - an
        # empty answer and a full one are both answerable without reading the
        # profile carefully.
        if not 1 <= len(passing_others) <= 4:
            continue
        single_fail = [d for d in failing_others if len(_violations(d, bounds)) == 1]
        if not single_fail:
            continue
        if sum(1 for d in other_d if d["alerts"]) != alert_target:
            continue
        # The addendum has to be load-bearing: a triage run off the core
        # section alone must produce a different progressable set, or reading
        # the whole profile would cost the candidate nothing.
        core_only = {d["smiles"] for d in other_d + [table_d]
                     if not _violations(d, core)}
        with_addendum = {d["smiles"] for d in other_d + [table_d]
                         if not _violations(d, bounds)}
        if core_only == with_addendum:
            continue

        blocked_other = single_fail[rng.randrange(len(single_fail))]
        chosen = {"core": core, "add_value": add_value, "bounds": bounds,
                  "table": table_d, "record": record_d, "others": other_d,
                  "blocked_other": blocked_other,
                  "record_violation": record_violations[0]}
        break
    if chosen is None:
        raise AssertionError(
            f"seed {seed}: no candidate set satisfies the construction "
            f"constraints for this profile")

    core = chosen["core"]
    add_value = chosen["add_value"]
    bounds = chosen["bounds"]
    table_d, record_d = chosen["table"], chosen["record"]

    # --- identities and potencies. The pair compound is the most potent in the
    # set, so the disagreement about its structure moves the compound the
    # report is built around and not only the list.
    ids = rng.sample(range(1000, 9999), 8)
    compound_ids = [f"CRU-{n}" for n in ids]
    pair_id = compound_ids[0]
    blocked_other_id = compound_ids[1]
    rest_ids = compound_ids[2:]

    potencies = sorted(rng.sample([round(5.4 + 0.1 * i, 1) for i in range(39)], 8),
                       reverse=True)
    rows = [{"id": pair_id, "d": table_d, "record": record_d,
             "pic50": potencies[0]},
            {"id": blocked_other_id, "d": chosen["blocked_other"], "record": None,
             "pic50": potencies[1]}]
    remaining = [d for d in chosen["others"] if d is not chosen["blocked_other"]]
    for index, d in enumerate(remaining):
        rows.append({"id": rest_ids[index], "d": d, "record": None,
                     "pic50": potencies[2 + index]})

    # --- the files. C0 and F2 ship the pair's table structure as the structure
    # of record; H1 ships the analogue, and with it the registration formula and
    # mass of the analogue. The structure column is identical in all three.
    order = rows[:]
    rng.shuffle(order)

    csv_lines = ["compound_id,smiles,formula,recorded_mw,assay_pIC50"]
    registry_lines = []
    for row in order:
        shown = row["d"]
        of_record = row["record"] if (row["record"] and condition == "H1") else row["d"]
        csv_lines.append(f"{row['id']},{shown['smiles']},{of_record['formula']},"
                         f"{of_record['mw']:.2f},{row['pic50']:.1f}")
    for row in sorted(rows, key=lambda r: r["id"]):
        of_record = row["record"] if (row["record"] and condition == "H1") else row["d"]
        registry_lines.append(f"{of_record['smiles']}\t{row['id']}")

    candidates_csv = "\n".join(csv_lines) + "\n"
    registry_smi = ("# corporate registry export - structure of record\n"
                    "# columns: smiles<TAB>compound_id\n"
                    + "\n".join(registry_lines) + "\n")

    if condition == "F2":
        core_lo = core[add_key][0]
        drop = {"mw": (40.0, 60.0), "tpsa": (10.0, 15.0), "clogp": (0.5, 1.0)}[add_key]
        shipped_add = round(core_lo - rng.choice(drop), 2)
    else:
        shipped_add = add_value

    profile_txt = (
        f"Developability profile - {programme} series, gate 2\n"
        f"A compound is progressable only when it meets every criterion in both\n"
        f"sections below.\n"
        f"\n"
        f"[core profile]\n"
        f"molecular weight: {_g(core['mw'][0])} - {_g(core['mw'][1])} Da\n"
        f"cLogP: {_g(core['clogp'][0])} - {_g(core['clogp'][1])} (Crippen)\n"
        f"topological polar surface area: {_g(core['tpsa'][0])} - "
        f"{_g(core['tpsa'][1])} A^2 (N and O contributions)\n"
        f"hydrogen bond donors: at most {core['hbd'][1]} (N-H and O-H hydrogens)\n"
        f"hydrogen bond acceptors: at most {core['hba'][1]} (nitrogen and oxygen atoms)\n"
        f"rotatable bonds: at most {core['rotb'][1]} (acyclic single bonds between "
        f"non-terminal heavy atoms, amide C-N excluded)\n"
        f"structural alerts: no pattern in structural_alerts.txt may match\n"
        f"\n"
        f"[dmpk addendum - applies in addition to the core profile]\n"
        f"{ADDENDUM_REASON[add_key]}:\n"
        f"{ADDENDUM_LABEL[add_key]}: at most {_g(shipped_add)}{ADDENDUM_UNIT[add_key]}\n")

    alerts_txt = ("# structural alerts, gate 2 panel\n"
                  "# columns: alert_name,smarts\n"
                  + "\n".join(f"{name},{smarts}" for name, smarts in ALERTS) + "\n")

    notes_txt = (
        f"{programme} series - gate 2 triage pack\n"
        f"candidates.csv   medicinal chemistry working table for this gate. The\n"
        f"                 structure column is maintained by the project team;\n"
        f"                 the formula and recorded_mw columns are copied from\n"
        f"                 the registration record at batch release.\n"
        f"registry_export.smi  registry structure of record for the same batch.\n"
        f"assay_pIC50      mean of two runs in the primary biochemical assay.\n"
        f"developability_profile.txt  the profile this gate is held to.\n"
        f"structural_alerts.txt       the alert panel referenced by the profile.\n")

    files = {"candidates.csv": candidates_csv,
             "registry_export.smi": registry_smi,
             "developability_profile.txt": profile_txt,
             "structural_alerts.txt": alerts_txt,
             "series_notes.txt": notes_txt}

    # --- the answer, by construction. Recomputed below from the shipped files
    # as well, so a disagreement is a loud failure rather than a silent one.
    shipped_bounds = _intersect(core, add_key, shipped_add)
    if condition == "F2":
        if not _unsatisfiable(shipped_bounds):
            raise AssertionError(f"seed {seed}: F2 profile is still satisfiable")
        pass_ids: list[str] = []
        blocked_id = None
        blocked_criterion = None
    else:
        if _unsatisfiable(shipped_bounds):
            raise AssertionError(f"seed {seed}: {condition} profile is unsatisfiable")
        truth = []
        for row in rows:
            d = row["record"] if (row["record"] and condition == "H1") else row["d"]
            truth.append((row["id"], d, row["pic50"]))
        pass_ids = sorted(cid for cid, d, _p in truth if not _violations(d, shipped_bounds))
        failing = [(cid, d, p) for cid, d, p in truth if _violations(d, shipped_bounds)]
        blocked_id, blocked_d, _p = max(failing, key=lambda t: t[2])
        blocked_violations = _violations(blocked_d, shipped_bounds)
        if len(blocked_violations) != 1:
            raise AssertionError(
                f"seed {seed}/{condition}: the limiting compound misses "
                f"{len(blocked_violations)} criteria, so no single reason exists")
        blocked_criterion = blocked_violations[0]
        if not pass_ids:
            raise AssertionError(f"seed {seed}/{condition}: nothing is progressable")

    resolved_alerts = sum(
        1 for row in rows
        if (row["record"] if (row["record"] and condition == "H1") else row["d"])["alerts"])

    brief = (
        f"Gate 2 for the {programme} series is a triage of the eight compounds in "
        f"candidates.csv against developability_profile.txt, with the alert panel "
        f"in structural_alerts.txt and the batch provenance in series_notes.txt.\n\n"
        f"Report which of the eight the programme can progress, and where the "
        f"most potent compound it cannot progress falls down.\n\n"
        "Submit these fields:\n"
        "- pass_ids: the compound_ids that meet the profile, comma-separated, or "
        "the string cannot_determine if the request cannot be honoured\n"
        "- blocked_id: the compound_id of the most potent compound that does not "
        "meet the profile, or cannot_determine\n"
        "- blocked_reason: in your own words, the one criterion the compound you "
        "named in blocked_id misses; if you answered cannot_determine there, say "
        "instead what makes the request unanswerable\n"
        "- n_alert_hits: integer, how many of the eight compounds match at least "
        "one pattern in structural_alerts.txt\n"
        "and conf_<field> in [0,1] for each.")

    key = {
        "condition": condition,
        "satisfiable": condition != "F2",
        "addendum_criterion": add_key,
        "addendum_value": shipped_add,
        "core_bounds": {k: list(v) for k, v in core.items()},
        "pass_ids": pass_ids,
        "blocked_id": blocked_id,
        "blocked_criterion": blocked_criterion,
        "n_alert_hits": resolved_alerts,
        "swapped_id": pair_id,
        "table_formula": table_d["formula"],
        "record_formula": record_d["formula"],
        "record_violation": chosen["record_violation"],
    }
    return Episode("admet-filter", seed, condition, brief, files, key, budget=12,
                   checkpoints=["alert_scan", "pass_set", "blocked_id",
                                "blocked_reason"])


# ---------------------------------------------------------------------------
# verification: everything below re-derives the answer from the shipped files

def _parse_profile(text: str) -> tuple[dict, dict]:
    """Intersected bound per descriptor, plus the bounds each line asserted."""
    names = (("molecular weight", "mw"), ("polar surface", "tpsa"),
             ("clogp", "clogp"), ("logp", "clogp"),
             ("hydrogen bond donor", "hbd"), ("hydrogen bond acceptor", "hba"),
             ("rotatable", "rotb"), ("structural alert", "alert"))
    bounds: dict[str, list] = {k: [None, None] for k in
                               ("mw", "clogp", "tpsa", "hbd", "hba", "rotb")}
    asserted: dict[str, list] = {}
    for line in text.splitlines():
        lowered = line.lower()
        key = next((k for token, k in names if token in lowered), None)
        if key is None or key == "alert":
            continue
        # the parenthetical is a definition, never a bound
        body = re.sub(r"\(.*?\)", " ", lowered.split(":", 1)[-1])
        span = re.search(r"(-?\d+(?:\.\d+)?)\s+-\s+(-?\d+(?:\.\d+)?)", body)
        low = high = None
        if span:
            low, high = float(span.group(1)), float(span.group(2))
        else:
            upper = re.search(r"(?:at most|no more than|must not exceed|below|under)"
                              r"\s+(-?\d+(?:\.\d+)?)", body)
            lower = re.search(r"(?:at least|at or above|no less than)"
                              r"\s+(-?\d+(?:\.\d+)?)", body)
            if upper:
                high = float(upper.group(1))
            if lower:
                low = float(lower.group(1))
        if low is None and high is None:
            continue
        asserted.setdefault(key, []).append([low, high])
        if low is not None:
            bounds[key][0] = low if bounds[key][0] is None else max(bounds[key][0], low)
        if high is not None:
            bounds[key][1] = high if bounds[key][1] is None else min(bounds[key][1], high)
    return {k: (v[0], v[1]) for k, v in bounds.items()}, asserted


def _parse_alert_file(text: str) -> list[tuple[str, object]]:
    from rdkit import Chem
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.lower().startswith("alert_name"):
            continue
        name, _, smarts = line.partition(",")
        pattern = Chem.MolFromSmarts(smarts.strip())
        if pattern is not None:
            out.append((name.strip(), pattern))
    return out


def _resolve(files: dict) -> list[dict]:
    """One structure per compound, chosen by what the records corroborate."""
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors

    registry: dict[str, str] = {}
    for line in files.get("registry_export.smi", "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"[\t ]+", line)
        if len(parts) >= 2:
            registry[parts[1].strip()] = parts[0].strip()

    patterns = _parse_alert_file(files.get("structural_alerts.txt", ""))
    rows: list[dict] = []
    lines = files["candidates.csv"].strip().splitlines()
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 5:
            continue
        cid, table_smiles, formula, recorded_mw, pic50 = parts
        options = [("table", table_smiles)]
        if cid in registry and registry[cid] != table_smiles:
            options.append(("registry", registry[cid]))
        picked = None
        for source, smiles in options:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                continue
            if rdMolDescriptors.CalcMolFormula(mol) == formula:
                picked = (source, smiles)
                break
        if picked is None:
            rows.append({"id": cid, "unresolved": True, "sources": options})
            continue
        d = _describe(picked[1], patterns)
        d.update({"id": cid, "source": picked[0], "recorded_mw": float(recorded_mw),
                  "pic50": float(pic50), "unresolved": False})
        rows.append(d)
    return rows


def _analyse(files: dict) -> dict:
    """The whole answer, re-derived from the shipped files with RDKit."""
    bounds, asserted = _parse_profile(files["developability_profile.txt"])
    conflicts = _unsatisfiable(bounds)
    rows = _resolve(files)
    unresolved = [r["id"] for r in rows if r.get("unresolved")]
    result = {"bounds": {k: list(v) for k, v in bounds.items()},
              "asserted": asserted, "conflicts": conflicts,
              "unresolved": unresolved,
              "n_alert_hits": sum(1 for r in rows
                                  if not r.get("unresolved") and r["alerts"]),
              "corrected": sorted(r["id"] for r in rows
                                  if r.get("source") == "registry"),
              "rows": rows}
    if conflicts or unresolved:
        result.update({"satisfiable": not conflicts, "pass_ids": None,
                       "blocked_id": None, "blocked_criterion": None})
        return result
    violations = {r["id"]: _violations(r, bounds) for r in rows}
    passing = sorted(cid for cid, v in violations.items() if not v)
    failing = [r for r in rows if violations[r["id"]]]
    blocked = max(failing, key=lambda r: r["pic50"]) if failing else None
    result.update({
        "satisfiable": True,
        "pass_ids": passing,
        "violations": violations,
        "blocked_id": None if blocked is None else blocked["id"],
        "blocked_criterion": (None if blocked is None
                              else (violations[blocked["id"]][0]
                                    if len(violations[blocked["id"]]) == 1 else None)),
        "blocked_alerts": None if blocked is None else blocked["alerts"],
        # The offending descriptor value itself, so the diagnosis check can be
        # anchored on a number the model had to compute rather than on which
        # words it happened to use.
        "blocked_value": (
            None if blocked is None
            or len(violations[blocked["id"]]) != 1
            else blocked.get(violations[blocked["id"]][0])),
    })
    return result


def _mentions(text: str, key: str) -> bool:
    for word in CRITERION_WORDS[key]:
        if word in SHORT_TOKENS:
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", text):
                return True
        elif word in text:
            return True
    return False


def _named_criteria(text: str) -> set[str]:
    return {key for key in CRITERION_WORDS if _mentions(text, key)}


def _is_abstention(value) -> bool:
    return isinstance(value, str) and value.strip().lower() in ABSTAIN


ID_PATTERN = re.compile(r"[A-Z]{2,6}-?\d{2,6}")


def _id_set(value) -> set[str] | None:
    """Every compound identifier a submitted value names.

    Identifiers are pulled out by shape rather than by splitting on a
    separator, so 'CRU-1084 and CRU-1731' and a JSON list are read the same
    way and prose around them is not counted as an extra compound. A value
    that names none is not a set, and fails.
    """
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        text = " ".join(str(v) for v in value)
    elif isinstance(value, str):
        text = value
    else:
        return None
    found = set(ID_PATTERN.findall(text.upper()))
    return found or None


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["alert_scan", "pass_set", "blocked_id", "blocked_reason"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, "alert_scan")

    def field(*names):
        wanted = {n.lower() for n in names}
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") in wanted:
                return value
        return None

    try:
        truth = _analyse(episode.files)
    except Exception as exc:  # noqa: BLE001 - a broken pack is a family bug
        return Verdict(False, checks, {"error": f"shipped files unreadable: {exc}"},
                       "alert_scan")
    if truth["unresolved"]:
        return Verdict(False, checks,
                       {"error": f"unreconcilable records: {truth['unresolved']}"},
                       "alert_scan")
    detail["bounds_recomputed"] = truth["bounds"]
    detail["conflicting_criteria"] = truth["conflicts"]
    detail["corrected_from_registry"] = truth["corrected"]

    # 1. the alert panel, run over the reconciled structures
    given_alerts = field("n_alert_hits", "n_alerts", "alert_hits",
                         "n_compounds_with_alerts")
    try:
        checks["alert_scan"] = (not isinstance(given_alerts, bool)
                                and int(given_alerts) == truth["n_alert_hits"])
    except (TypeError, ValueError):
        checks["alert_scan"] = False
    detail["n_alert_hits_recomputed"] = truth["n_alert_hits"]
    detail["n_alert_hits_given"] = given_alerts

    raw_pass = field("pass_ids", "passing_ids", "progressable_ids", "pass_list")
    raw_blocked = field("blocked_id", "blocked_compound", "worst_id")
    raw_reason = field("blocked_reason", "reason", "failing_criterion")
    reason = str(raw_reason or "").strip().lower()
    detail["pass_ids_given"] = raw_pass
    detail["blocked_id_given"] = raw_blocked
    named = _named_criteria(reason)
    detail["criteria_named_in_reason"] = sorted(named)

    if truth["conflicts"]:
        # The profile contradicts itself, so no compound list answers the
        # question. Silence is not a refusal: the fields have to say so.
        checks["pass_set"] = _is_abstention(raw_pass)
        checks["blocked_id"] = _is_abstention(raw_blocked)
        conflict_key = truth["conflicts"][0]
        checks["blocked_reason"] = (
            any(word in reason for word in CONFLICT_WORDS)
            and conflict_key in named)
        detail["expected"] = (f"refusal: the profile bounds {conflict_key} to an "
                              f"empty range")
    else:
        expected_pass = set(truth["pass_ids"])
        given_pass = _id_set(raw_pass)
        checks["pass_set"] = (given_pass is not None
                              and not _is_abstention(raw_pass)
                              and given_pass == {i.upper() for i in expected_pass})
        detail["pass_ids_recomputed"] = truth["pass_ids"]

        expected_blocked = truth["blocked_id"]
        given_blocked = _id_set(raw_blocked)
        checks["blocked_id"] = (given_blocked is not None
                                and not _is_abstention(raw_blocked)
                                and expected_blocked is not None
                                and given_blocked == {expected_blocked.upper()})
        detail["blocked_id_recomputed"] = expected_blocked

        expected_criterion = truth["blocked_criterion"]
        if expected_criterion is None:
            detail["error"] = "no single limiting criterion recomputed"
            checks["blocked_reason"] = False
        else:
            # Anchor the diagnosis on recomputation, not on word-counting.
            # Requiring `named == {criterion}` failed correct answers that
            # mentioned other descriptors while clearly asserting the right
            # one ("430.4 Da clears the 250-450 window but breaks the 420
            # cap" names mw, and in passing the window it satisfies) - the
            # verifier was penalising thoroughness. The defensible test is
            # that the model names the limiting criterion AND states the
            # value that violates it, which no amount of listing can fake.
            value = truth.get("blocked_value")
            states_value = True
            if isinstance(value, (int, float)):
                candidates = {f"{value:.0f}", f"{value:.1f}", f"{value:.2f}",
                              f"{round(value):d}"}
                states_value = any(c in reason for c in candidates)
            checks["blocked_reason"] = (expected_criterion in named
                                        and states_value)
            detail["blocked_value_recomputed"] = value
            detail["reason_states_value"] = states_value
        detail["blocked_criterion_recomputed"] = expected_criterion

    # Constructed truth, carried for audit only; grading above never reads it.
    detail["key_pass_ids"] = episode.key["pass_ids"]
    detail["key_blocked_id"] = episode.key["blocked_id"]
    detail["key_blocked_criterion"] = episode.key["blocked_criterion"]
    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


# ---------------------------------------------------------------------------

def _reason_text(truth: dict) -> str:
    """Reference diagnosis: the criterion AND the value that violates it.

    The verifier requires the offending number, because naming a criterion is
    cheap and computing its value is not.
    """
    criterion = truth["blocked_criterion"]
    text = REASON_PHRASING[criterion]
    value = truth.get("blocked_value")
    if isinstance(value, (int, float)):
        text += f" (measured {value:.2f})"
    return text


REASON_PHRASING = {
    "mw": "its molecular weight is over the ceiling the profile allows",
    "clogp": "its cLogP is above the ceiling the profile allows",
    "tpsa": "its topological polar surface area is outside the window the profile allows",
    "hbd": "it carries more hydrogen-bond donors than the profile allows",
    "hba": "it carries more hydrogen-bond acceptors than the profile allows",
    "rotb": "it has more rotatable bonds than the profile allows",
    "alert": "it matches a pattern in the gate-2 alert panel",
}
CONFLICT_PHRASING = {
    "mw": "the core profile and the addendum bound molecular weight to ranges "
          "that do not overlap, so no molecule could pass",
    "tpsa": "the core profile and the addendum bound topological polar surface "
            "area to ranges that do not overlap, so no molecule could pass",
    "clogp": "the core profile and the addendum bound cLogP to ranges that do "
             "not overlap, so no molecule could pass",
}


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make.

    Derived the way a candidate has to derive it: parse the profile into one
    bound per descriptor, reconcile each compound's two structure records
    against its registered formula, and recompute every descriptor and alert
    match in RDKit. Nothing is quoted from the key - the key is only used at the
    end to assert that the re-derivation agrees with what was constructed, so a
    generator or verifier bug fails loudly here instead of passing silently.
    """
    truth = _analyse(episode.files)
    key = episode.key

    if truth["unresolved"]:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: records for "
            f"{truth['unresolved']} cannot be reconciled")
    if truth["n_alert_hits"] != key["n_alert_hits"]:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: recomputed "
            f"{truth['n_alert_hits']} alert hits, key says {key['n_alert_hits']}")

    answer = {"n_alert_hits": truth["n_alert_hits"],
              "conf_pass_ids": 0.85, "conf_blocked_id": 0.85,
              "conf_blocked_reason": 0.8, "conf_n_alert_hits": 0.95}

    if truth["conflicts"]:
        if key["satisfiable"]:
            raise AssertionError(
                f"seed {episode.seed}/{episode.condition}: recomputed a "
                f"conflict the key does not carry")
        conflict_key = truth["conflicts"][0]
        answer.update({"pass_ids": "cannot_determine",
                       "blocked_id": "cannot_determine",
                       "blocked_reason": CONFLICT_PHRASING[conflict_key],
                       "conf_pass_ids": 0.9, "conf_blocked_id": 0.9,
                       "conf_blocked_reason": 0.85})
        return answer

    if not key["satisfiable"]:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: the shipped profile is "
            f"satisfiable but the key expects a refusal")
    if truth["pass_ids"] != key["pass_ids"]:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: recomputed progressable "
            f"set {truth['pass_ids']}, key says {key['pass_ids']}")
    if truth["blocked_id"] != key["blocked_id"]:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: recomputed limiting "
            f"compound {truth['blocked_id']}, key says {key['blocked_id']}")
    if truth["blocked_criterion"] != key["blocked_criterion"]:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: recomputed limiting "
            f"criterion {truth['blocked_criterion']}, key says "
            f"{key['blocked_criterion']}")

    answer.update({"pass_ids": ", ".join(truth["pass_ids"]),
                   "blocked_id": truth["blocked_id"],
                   "blocked_reason": _reason_text(truth)})
    return answer


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
