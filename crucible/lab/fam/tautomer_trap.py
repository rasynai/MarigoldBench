"""Family: the donor count of the species that is actually in the buffer.

This is the leaky-abstraction mechanism both collaborators asked for (Gemini's
"Mechanism A", archived at analysis/collab/hardening__gemini.md): a default
library call silently destroys the thing the task turns on. `MolFromSmiles`
faithfully preserves whatever tautomer and protonation state the registration
system happened to store, and every descriptor computed from that object
describes a species that does not predominate in the assay buffer. Nothing
errors. Nothing looks anomalous. `df.describe()` finds nothing, because there
is nothing locally wrong with the file - the defect is a mismatch between two
correct files.

The workspace therefore supports three superficially adequate analyses that
imply DIFFERENT decisions, which is the shape the critique prescribed:

  A  descriptors of the registered structure. `descriptor_cache.csv` already
     holds exactly these numbers, so a model that recomputes them in RDKit gets
     independent-looking confirmation of its own error and its confidence goes
     UP. The cache even carries the registration pipeline's own triage flag,
     which in H1 marks the wrong compound clear and the right one for watching.
  B  descriptors of RDKit's canonical tautomer. `TautomerEnumerator` scores
     carbonyls heavily, so it drives every beta-dicarbonyl to the keto form -
     the right answer for one compound in the set and the wrong answer for
     another, whichever way the measured enol/keto ratio actually points.
  C  descriptors of the microspecies the shipped constants imply at the assay
     pH: acids below pH 7.40 deprotonated, bases above it protonated, and the
     beta-dicarbonyl in whichever tautomer its measured ratio favours.

Only C is consistent with the control that ships in every condition:
`reference_pampa.csv`, twenty compounds from the same series measured under the
same protocol. Donor count of the microspecies explains their permeability
(R^2 >= 0.90); donor count of the registered structure explains it only
partly (R^2 held inside 0.30-0.65 by construction - mediocre enough to use,
good enough to believe). The generator asserts that separation per instance,
so the discrimination is a property of the shipped data and not of the key.

  C0  the registered structures happen to rank the same way the microspecies
      do, so the naive selection is right and calling a problem is a false
      alarm. The reported donor counts and the reported permeability are still
      wrong under A and under B, so C0 is not a free pass.
  H1  the compound the cache flags clear and the naive count ranks best has the
      HIGHEST microspecies donor count in the set, and the compound that
      actually clears the cut is the one the cache flags for watching. Route A
      progresses the worst candidate. Route B reports a different donor vector
      again. And a model that applies the pKa rows but ignores the enol/keto row
      never lands on the winner alone - it finds no candidate clearing the cut,
      or several, or a different one. Each of those is asserted per instance, so
      "three confident different wrong answers" is measured rather than hoped
      for.
  F2  one pKa is recorded as not measured, and it is the one the decision turns
      on: below pH 7.40 that candidate clears the cut and is the only candidate
      that does, above it nothing clears. The generator proves this by
      recomputing the whole pipeline under both values and emitting the two
      admissible parameter vectors with their different outcomes. The series
      cannot supply the value either - two reference compounds carry the same
      site with measured constants on OPPOSITE sides of the assay pH - so
      "estimate it from the analogues" is refuted by the shipped data rather
      than merely discouraged.

Every number the candidate reports is recomputed here from the shipped SMILES
and the shipped constants by SMARTS-locating each named site and editing the
molecule (charge, H count, and for the tautomer the two bond orders), then
counting hydrogens on N and O. The permeability check is anchored on the
measured reference set - the verifier refits the line itself - rather than on
the coefficients the generator used, so a generator and verifier sharing one
wrong assumption cannot agree their way past it.
"""
from __future__ import annotations

import itertools
import math
import random
import re
from pathlib import Path

from ..families import Episode, Verdict

# A stated refusal. "none" is deliberately NOT here: in F2 "no candidate
# clears the cut" is one of the two admissible worlds the missing constant
# leaves open, so accepting it as a refusal would pass a model that guessed the
# high branch, and as a donor count "none" reads as zero. A candidate that wants
# to refuse has the token the brief names.
REFUSAL = {"cannot_determine", "cannot determine", "cannot be determined",
           "not_determinable", "not determinable", "indeterminate",
           "undetermined", "not determined", "not_measured", "not measured",
           "unknown", "insufficient data", "no defensible value"}

ASSAY_PH = 7.40
CUT_LOG_PAPP = -5.50
N_CANDIDATES = 5
N_REFERENCE = 20
SITES_PER_COMPOUND = 3
PREDICTION_TOL = 0.20

TAGS = ["QND", "TZL", "MBX", "RKA", "VDS", "HPE"]
SERIES = ["macrocycle-free amide", "biaryl amide", "para-linked benzamide",
          "anilide hinge", "benzamide core", "meta-substituted amide"]

# ---------------------------------------------------------------- chemistry

# One assembly template per instance-level filler; the aniline ring carries two
# substituent slots and the benzoyl ring one, and the amide nitrogen is either
# secondary (one donor) or methylated (none).
TEMPLATES = [
    "O=C(N{nh}c1ccc({a})c({b})c1)c1ccc({c})cc1",
    "O=C(N{nh}c1ccc({a})c({b})c1)c1cc(F)c({c})cc1",
    "O=C(N{nh}c1ccc({a})c({b})c1)c1cc(OC)c({c})cc1",
    "O=C(N{nh}c1ccc({a})c({b})c1)c1cc(C)c({c})cc1",
]

# Each ionisable or tautomerisable site appears at most once per molecule and
# has a SMARTS that matches nothing else in the template (asserted per instance
# in `_audit_structures`). `atom` indexes the match tuple to the atom whose
# charge and hydrogen count move: the acidic O or N, or the basic N.
SITE_CHEMISTRY = {
    "carboxylic acid": {
        "frag": "C(=O)O", "smarts": "[CX3](=[OX1])[OX2H1]",
        "kind": "acid", "atom": 2},
    "phenol": {
        "frag": "O", "smarts": "[c][OX2H1]",
        "kind": "acid", "atom": 1},
    "methanesulfonamide": {
        "frag": "NS(C)(=O)=O", "smarts": "[SX4](=[OX1])(=[OX1])[NX3H1]",
        "kind": "acid", "atom": 3},
    "primary alkylamine": {
        "frag": "CCN", "smarts": "[CX4][NX3H2]",
        "kind": "base", "atom": 1},
    "dimethylamino": {
        "frag": "CCN(C)C", "smarts": "[NX3H0]([CH3])([CH3])[CX4]",
        "kind": "base", "atom": 0},
    "diethylamino": {
        "frag": "CCN(CC)CC",
        "smarts": "[NX3H0]([CH2][CH3])([CH2][CH3])[CX4]",
        "kind": "base", "atom": 0},
    "morpholine": {
        "frag": "CCN3CCOCC3",
        "smarts": "[NX3H0]1[CH2][CH2][OX2][CH2][CH2]1",
        "kind": "base", "atom": 0},
    # One site label, two registerable drawings. Which one a file happens to
    # hold is discovered by SMARTS, never assumed.
    "beta-dicarbonyl": {
        "kind": "tautomer",
        "keto_frag": "C(=O)CC(C)=O",
        "enol_frag": "C(=O)C=C(C)O",
        "keto_smarts": "[CX3](=[OX1])[CX4H2][CX3](=[OX1])",
        "enol_smarts": "[CX3](=[OX1])[CX3H1]=[CX3][OX2H1]"},
}

PKA = "pKa"
LOGK = "log_K_enol_keto"

# (site, drawn form, measurement label, value band, donors as drawn, donors in
# the buffer). The pKa bands never come within 0.30 of the assay pH - asserted
# per instance - so no compound's predominant species is a coin toss.
VARIANTS = [
    ("carboxylic acid", None, PKA, (3.60, 5.00), 1, 0),
    ("phenol", None, PKA, (5.90, 7.00), 1, 0),
    ("phenol", None, PKA, (8.60, 10.40), 1, 1),
    ("methanesulfonamide", None, PKA, (6.00, 7.00), 1, 0),
    ("methanesulfonamide", None, PKA, (8.80, 10.20), 1, 1),
    ("primary alkylamine", None, PKA, (9.60, 10.80), 2, 3),
    ("dimethylamino", None, PKA, (8.60, 9.60), 0, 1),
    ("diethylamino", None, PKA, (9.40, 10.20), 0, 1),
    ("morpholine", None, PKA, (6.20, 7.10), 0, 0),
    ("beta-dicarbonyl", "keto", LOGK, (0.90, 1.60), 0, 1),
    ("beta-dicarbonyl", "keto", LOGK, (-1.60, -0.90), 0, 0),
    ("beta-dicarbonyl", "enol", LOGK, (0.90, 1.60), 1, 1),
    ("beta-dicarbonyl", "enol", LOGK, (-1.60, -0.90), 1, 0),
]

# Candidate (donors as drawn, donors in buffer) targets. The two sound-brief
# conditions draw from the SAME multiset in both columns - {1,2,3,3,4} drawn and
# {2,3,3,4,4} in buffer - so the cache, the descriptor distribution and the row
# counts are statistically identical and only the PAIRING differs. Without that,
# H1 is readable off the workspace without doing any chemistry.
# A design family fixes the multiset of REGISTERED donor counts - the only
# column of this table a candidate can see, since it is what candidates.csv and
# descriptor_cache.csv both encode. The family is chosen from a seed-only rng,
# so C0, H1 and F2 at one seed present the SAME registered-count multiset with a
# unique minimum, and only the pairing of registered count to buffer count
# moves. Without that, "which condition is this" is answerable by sorting a
# column.
FAMILIES = [
    {"drawn": (1, 2, 3, 3, 4), "c0_winner": [(1, 2)], "h1_naive": (1, 4),
     # The H1 winner always registers three donors, so the cache's own triage
     # label says "watch" for the compound that actually clears the cut and
     # "clear" for the one that does not - the decoy is in the shipped file,
     # not only in the model's recomputation of it.
     "h1_winner": [(3, 2), (3, 1)], "f2_drawn": 2},
]
CACHE_CLEAR_AT = 2      # the registration pipeline's own triage threshold
# Every candidate keeps the series' secondary anilide, which contributes one
# donor in both columns; the site-combination index is keyed on the sites alone.
CANDIDATE_BASE = 1


def _site_target(total: tuple[int, int]) -> tuple[int, int]:
    return (total[0] - CANDIDATE_BASE, total[1] - CANDIDATE_BASE)


def _donors(mol) -> int:
    """Hydrogens bonded to nitrogen or oxygen - the definition protocol.md
    states, so the count cannot turn on whether a solver picked the atom-count
    or the hydrogen-count flavour of "H-bond donor"."""
    return sum(a.GetTotalNumHs() for a in mol.GetAtoms()
               if a.GetSymbol() in ("N", "O"))


def _match(mol, smarts: str):
    from rdkit import Chem
    hits = mol.GetSubstructMatches(Chem.MolFromSmarts(smarts), uniquify=True)
    return sorted(hits)[0] if hits else None


def _n_match(mol, smarts: str) -> int:
    from rdkit import Chem
    return len(mol.GetSubstructMatches(Chem.MolFromSmarts(smarts), uniquify=True))


def _assemble(triple, template: str, secondary_amide: bool) -> str:
    frags = []
    for site, form, *_rest in triple:
        chem = SITE_CHEMISTRY[site]
        if chem["kind"] == "tautomer":
            frags.append(chem["keto_frag"] if form == "keto" else chem["enol_frag"])
        else:
            frags.append(chem["frag"])
    return template.format(nh="" if secondary_amide else "(C)",
                           a=frags[0], b=frags[1], c=frags[2])


def _microspecies(smiles: str, rows: list[tuple[str, str, str]],
                  ph: float = ASSAY_PH, skip_tautomer: bool = False):
    """The species the shipped constants imply, built from the shipped SMILES.

    Returns (donors_as_drawn, donors_in_buffer, microspecies_smiles) or
    (drawn, None, None) when any constant needed is not a number - the F2
    indeterminacy, discovered from the file rather than announced.
    """
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None, None
    drawn = _donors(mol)

    deprotonate: list[int] = []
    protonate: list[int] = []
    flip: list[tuple[str, tuple[int, ...]]] = []
    for site, measurement, raw in rows:
        chem = SITE_CHEMISTRY.get(site)
        if chem is None:
            return drawn, None, None
        try:
            value = float(str(raw).strip())
        except (TypeError, ValueError):
            return drawn, None, None
        if chem["kind"] == "tautomer":
            if skip_tautomer:
                continue
            keto = _match(mol, chem["keto_smarts"])
            enol = _match(mol, chem["enol_smarts"])
            enol_favoured = value > 0.0
            if keto is not None and enol_favoured:
                flip.append(("keto_to_enol", keto))
            elif enol is not None and not enol_favoured:
                flip.append(("enol_to_keto", enol))
            continue
        hit = _match(mol, chem["smarts"])
        if hit is None:
            return drawn, None, None
        index = hit[chem["atom"]]
        if chem["kind"] == "acid" and value < ph:
            deprotonate.append(index)
        elif chem["kind"] == "base" and value > ph:
            protonate.append(index)

    edit = Chem.RWMol(mol)
    for index in deprotonate:
        atom = edit.GetAtomWithIdx(index)
        atom.SetFormalCharge(-1)
        atom.SetNumExplicitHs(0)
        atom.SetNoImplicit(True)
    for index in protonate:
        atom = edit.GetAtomWithIdx(index)
        atom.SetNumExplicitHs(atom.GetTotalNumHs() + 1)
        atom.SetFormalCharge(1)
        atom.SetNoImplicit(True)
    for direction, hit in flip:
        if direction == "keto_to_enol":
            _c1, _o1, ch2, c2, o2 = hit
            edit.GetBondBetweenAtoms(ch2, c2).SetBondType(Chem.BondType.DOUBLE)
            edit.GetBondBetweenAtoms(c2, o2).SetBondType(Chem.BondType.SINGLE)
            for index, hs in ((o2, 1), (ch2, 1)):
                atom = edit.GetAtomWithIdx(index)
                atom.SetNumExplicitHs(hs)
                atom.SetNoImplicit(True)
        else:
            _c1, _o1, ch, c2, oh = hit
            edit.GetBondBetweenAtoms(ch, c2).SetBondType(Chem.BondType.SINGLE)
            edit.GetBondBetweenAtoms(c2, oh).SetBondType(Chem.BondType.DOUBLE)
            for index, hs in ((oh, 0), (ch, 2)):
                atom = edit.GetAtomWithIdx(index)
                atom.SetNumExplicitHs(hs)
                atom.SetNoImplicit(True)
    out = edit.GetMol()
    try:
        Chem.SanitizeMol(out)
    except Exception:  # noqa: BLE001 - an unbuildable microspecies is a bug
        return drawn, None, None
    return drawn, _donors(out), Chem.MolToSmiles(out)


# ---------------------------------------------------------------- statistics

def _ols(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    n = len(xs)
    if n < 3:
        return 0.0, 0.0, 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    residual = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    total = sum((y - my) ** 2 for y in ys)
    return intercept, slope, (1.0 - residual / total) if total else 0.0


# ---------------------------------------------------------------- file layout

def _csv(header: list[str], rows: list[list[str]]) -> str:
    return "\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n"


def _read_csv(text: str) -> list[dict[str, str]]:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
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


def _ion_rows(text: str) -> dict[str, list[tuple[str, str, str]]]:
    grouped: dict[str, list[tuple[str, str, str]]] = {}
    for row in _read_csv(text):
        grouped.setdefault(row.get("compound_id", ""), []).append(
            (row.get("site", ""), row.get("measurement", ""), row.get("value", "")))
    return grouped


def recompute(files: dict[str, str], skip_tautomer: bool = False,
              use_drawn: bool = False, override: tuple[str, str, str] | None = None) -> dict:
    """Re-derive the whole decision from the shipped files alone.

    `skip_tautomer` reproduces the analysis that applies the pKa rows and
    ignores the enol/keto row; `use_drawn` reproduces the registered-structure
    analysis. Both are here so the generator can PROVE, per instance, that they
    reach a different decision than the microspecies analysis - the difficulty
    claim is measured, not asserted.
    """
    ions = _ion_rows(files["ionisation.csv"])
    if override is not None:
        cid, site, value = override
        ions[cid] = [(s, m, value if s == site else v) for s, m, v in ions[cid]]

    candidates = [r["compound_id"] for r in _read_csv(files["candidates.csv"])]
    smiles = {r["compound_id"]: r["smiles"]
              for r in _read_csv(files["candidates.csv"])}
    reference = _read_csv(files["reference_pampa.csv"])
    measured = {r["compound_id"]: float(r["log_papp_cm_s"]) for r in reference}
    for row in reference:
        smiles[row["compound_id"]] = row["smiles"]

    drawn: dict[str, int] = {}
    buffered: dict[str, int | None] = {}
    species: dict[str, str | None] = {}
    for cid, smi in smiles.items():
        d, b, s = _microspecies(smi, ions.get(cid, []), skip_tautomer=skip_tautomer)
        drawn[cid] = d
        buffered[cid] = d if use_drawn else b
        species[cid] = s

    ref_ids = [r["compound_id"] for r in reference]
    xs = [buffered[c] for c in ref_ids]
    ys = [measured[c] for c in ref_ids]
    if any(x is None for x in xs):
        intercept, slope, r2 = 0.0, 0.0, 0.0
    else:
        intercept, slope, r2 = _ols(xs, ys)

    predicted: dict[str, float | None] = {}
    for cid in candidates:
        count = buffered[cid]
        predicted[cid] = None if count is None else intercept + slope * count
    passers = sorted(c for c in candidates
                     if predicted[c] is not None and predicted[c] > CUT_LOG_PAPP)
    indeterminate = sorted(c for c in candidates if buffered[c] is None)
    return {
        "candidates": candidates, "reference": ref_ids, "smiles": smiles,
        "drawn": drawn, "buffered": buffered, "species": species,
        "measured": measured, "intercept": intercept, "slope": slope, "r2": r2,
        "predicted": predicted, "passers": passers,
        "indeterminate": indeterminate,
        "decision": (passers[0] if len(passers) == 1 and not indeterminate
                     else ("none" if not passers and not indeterminate else None)),
    }


def _audit_structures(files: dict[str, str]) -> None:
    """Every declared site matches exactly once and nothing undeclared matches.

    A silently non-matching SMARTS would make the verifier and the generator
    agree on a wrong count, so this runs at build time on every instance.
    """
    from rdkit import Chem

    ions = _ion_rows(files["ionisation.csv"])
    rows = _read_csv(files["candidates.csv"]) + _read_csv(files["reference_pampa.csv"])
    seen = set()
    for row in rows:
        cid, smi = row["compound_id"], row["smiles"]
        mol = Chem.MolFromSmiles(smi)
        assert mol is not None, f"{cid} does not parse: {smi}"
        assert smi not in seen, f"duplicate structure {smi}"
        seen.add(smi)
        declared = {site for site, _m, _v in ions.get(cid, [])}
        assert len(ions.get(cid, [])) == SITES_PER_COMPOUND, f"{cid} site count"
        for site, chem in SITE_CHEMISTRY.items():
            if chem["kind"] == "tautomer":
                total = (_n_match(mol, chem["keto_smarts"])
                         + _n_match(mol, chem["enol_smarts"]))
            else:
                total = _n_match(mol, chem["smarts"])
            want = 1 if site in declared else 0
            assert total == want, f"{cid}: {site} matched {total}, want {want}"


# ---------------------------------------------------------------- generation

def _variant_index() -> dict[tuple[int, int], list[tuple]]:
    """Every legal 3-site combination, indexed by the (drawn, buffer) sum it
    produces. Built once so a target is always realised several ways and the
    same target gives a different molecule at a different seed."""
    index: dict[tuple[int, int], list[tuple]] = {}
    for triple in itertools.combinations(VARIANTS, SITES_PER_COMPOUND):
        if len({v[0] for v in triple}) != SITES_PER_COMPOUND:
            continue
        key = (sum(v[4] for v in triple), sum(v[5] for v in triple))
        index.setdefault(key, []).append(triple)
    return index


VARIANT_INDEX = _variant_index()
# The (registered, in-buffer) donor totals three distinct sites can actually
# produce on the series scaffold. Target vectors are drawn from this rather than
# written by hand, so an unreachable pair fails loudly at authoring time.
AVAILABLE_TOTALS = {(k[0] + 1, k[1] + 1) for k in VARIANT_INDEX}


def _variant(site: str, drawn: int, buffered: int, form=None):
    for entry in VARIANTS:
        if (entry[0] == site and entry[4] == drawn and entry[5] == buffered
                and (form is None or entry[1] == form)):
            return entry
    raise KeyError(f"no {site} variant with donors {drawn}->{buffered}")


# The F2 candidate carries a phenol whose pKa is absent plus sites that fix
# everything else, so the two admissible values for that one constant differ by
# exactly one donor and nothing else moves. One recipe per registered-count
# family, so F2 presents the same visible multiset as C0 and H1 do.
F2_RECIPES = {
    2: lambda: (_variant("phenol", 1, 1), _variant("dimethylamino", 0, 1),
                _variant("morpholine", 0, 0)),
}


def _compound(rng: random.Random, triple, secondary_amide: bool | None = None):
    """One registered structure plus the constant rows that describe it.

    `blind` is what the analysis that applies the pKa rows and ignores the
    enol/keto row would count - carried so the generator can prove that route
    reaches a different answer without having to run it.
    """
    triple = list(triple)
    rng.shuffle(triple)
    template = rng.choice(TEMPLATES)
    if secondary_amide is None:
        secondary_amide = rng.random() < 0.6
    smiles = _assemble(triple, template, secondary_amide)
    rows, variants = [], []
    for site, form, measurement, band, drawn_n, _buffer_n in triple:
        low, high = band
        value = rng.uniform(low, high)
        rows.append((site, measurement, f"{value:.2f}"))
        variants.append((site, form, round(value, 2), drawn_n))
    base = 1 if secondary_amide else 0
    return {
        "smiles": smiles, "rows": rows, "variants": variants, "base": base,
        "drawn": base + sum(v[4] for v in triple),
        "buffered": base + sum(v[5] for v in triple),
        "blind": base + sum(v[4] if v[0] == "beta-dicarbonyl" else v[5]
                            for v in triple),
    }


def _pack(files_rng: random.Random, tag: str, series: str,
          candidates: list[dict], reference: list[dict],
          measured: list[float]) -> dict[str, str]:
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors, Lipinski

    cand_ids = [f"{tag}-{1 + i:03d}" for i in range(len(candidates))]
    ref_ids = [f"{tag}-{101 + i:03d}" for i in range(len(reference))]

    cand_csv = _csv(
        ["compound_id", "smiles", "series", "synthesis_steps"],
        [[cid, c["smiles"], series, str(files_rng.randint(4, 9))]
         for cid, c in zip(cand_ids, candidates)])
    ref_csv = _csv(
        ["compound_id", "smiles", "log_papp_cm_s"],
        [[rid, r["smiles"], f"{value:.3f}"]
         for rid, r, value in zip(ref_ids, reference, measured)])
    ion_rows: list[list[str]] = []
    for cid, entry in list(zip(cand_ids, candidates)) + list(zip(ref_ids, reference)):
        for site, measurement, value in entry["rows"]:
            ion_rows.append([cid, site, measurement, value])
    ion_csv = _csv(["compound_id", "site", "measurement", "value"], ion_rows)

    cache_rows = []
    for cid, entry in list(zip(cand_ids, candidates)) + list(zip(ref_ids, reference)):
        mol = Chem.MolFromSmiles(entry["smiles"])
        hbd = _donors(mol)
        cache_rows.append([cid, str(hbd), str(Lipinski.NumHAcceptors(mol)),
                           f"{Descriptors.TPSA(mol):.2f}",
                           f"{Crippen.MolLogP(mol):.3f}",
                           "clear" if hbd <= CACHE_CLEAR_AT else "watch"])
    cache_csv = _csv(["compound_id", "hbd", "hba", "tpsa", "clogp", "flag"],
                     cache_rows)

    protocol = f"""# PAMPA protocol and progression rule - {series} series

Assay: 96-well PAMPA, donor and acceptor compartments both buffered to
pH {ASSAY_PH:.2f}, 25 C, 4 h incubation, LC-MS/MS quantification of the
acceptor well.

Permeability across this series is a straight line in the compound's
hydrogen-bond donor count, counted as the number of hydrogens bonded to
nitrogen or oxygen. The {len(reference)} compounds in reference_pampa.csv were run
under this protocol and set that line for the series.

Progression rule: a candidate is carried forward only if its log Papp in cm/s
is above {CUT_LOG_PAPP:.2f}. At most one candidate is carried forward per round.

## File notes

candidates.csv        compound_id, smiles, series, synthesis_steps
                      smiles is the structure as it stands in the registry.
reference_pampa.csv   compound_id, smiles, log_papp_cm_s
                      log_papp_cm_s is log10 of the measured apparent
                      permeability in cm/s.
ionisation.csv        compound_id, site, measurement, value
                      measurement {PKA}: the acid dissociation constant of the
                      protonated form of the named site, in the assay buffer
                      at 25 C.
                      measurement {LOGK}: log10 of the enol-to-keto
                      ratio of the named beta-dicarbonyl site, in the assay
                      buffer at 25 C.
                      value not_measured: the constant was not determined on
                      this chemotype and no historical value is carried
                      forward for it.
descriptor_cache.csv  compound_id, hbd, hba, tpsa, clogp, flag
                      the descriptor record the registration pipeline stored
                      for each structure; flag is the pipeline's own triage
                      label.
"""
    return {"candidates.csv": cand_csv, "reference_pampa.csv": ref_csv,
            "ionisation.csv": ion_csv, "descriptor_cache.csv": cache_csv,
            "protocol.md": protocol}


def _reference_set(rng: random.Random, intercept: float, slope: float,
                   probe: tuple[int, int], probe_gap: float):
    """Twenty measured compounds whose permeability the microspecies donor count
    explains and the registered donor count only half explains.

    The window on the registered-structure fit is deliberate: a fit that is
    obviously broken sends a model looking for a better descriptor, and a fit
    that is perfect removes the control. 0.30-0.65 is usable-looking and wrong.
    """
    for _attempt in range(4000):
        entries = []
        for _ in range(N_REFERENCE):
            triple = rng.choice(list(itertools.chain.from_iterable(
                VARIANT_INDEX.values())))
            entries.append(_compound(rng, triple))
        if len({e["smiles"] for e in entries}) != N_REFERENCE:
            continue      # a repeated structure would leave no room for candidates
        buffered = [e["buffered"] for e in entries]
        drawn = [e["drawn"] for e in entries]
        if len(set(buffered)) < 4 or len(set(drawn)) < 3:
            continue
        # Both phenol bands must appear, so an unmeasured phenol constant is
        # provably unpinnable from the series rather than merely unmeasured.
        phenol_bands = {v[2] < ASSAY_PH for e in entries for v in e["variants"]
                        if v[0] == "phenol"}
        if phenol_bands != {True, False}:
            continue
        # And both drawings of the beta-dicarbonyl must be measured, so the
        # tautomer row matters to the LINE as well as to the candidates.
        forms = [v[1] for e in entries for v in e["variants"]
                 if v[0] == "beta-dicarbonyl"]
        if len(forms) < 3 or set(forms) != {"keto", "enol"}:
            continue
        measured = [intercept + slope * b + rng.gauss(0.0, 0.04) for b in buffered]
        true_line = _ols([float(b) for b in buffered], measured)
        naive_line = _ols([float(d) for d in drawn], measured)
        r2_buffer, r2_drawn = true_line[2], naive_line[2]
        if r2_buffer < 0.90 or not (0.30 <= r2_drawn <= 0.65):
            continue
        if sum(1 for d, b in zip(drawn, buffered) if d != b) < 8:
            continue
        # The control has to be DECISIVE, not merely better: the line fitted on
        # registered counts must mispredict a compound of the winner's shape by
        # well over the honesty tolerance, or a model that never leaves the
        # registered structures could still report the right permeability.
        if abs((naive_line[0] + naive_line[1] * probe[0])
               - (true_line[0] + true_line[1] * probe[1])) <= probe_gap:
            continue
        return entries, [round(m, 3) for m in measured], r2_buffer, r2_drawn
    raise RuntimeError("could not build a discriminating reference set")


def build(seed: int, condition: str) -> Episode:
    tag = TAGS[seed % len(TAGS)]
    series = SERIES[seed % len(SERIES)]

    # The reference set, the line and the protocol are drawn from a rng that
    # does NOT see the condition, so the control ships byte-identical in all
    # three and only the candidate block differs.
    shared = random.Random(880_000 + seed)
    intercept = -round(shared.uniform(3.68, 3.80), 3)
    slope = -round(shared.uniform(0.68, 0.78), 3)
    reference, measured, r2_buffer, r2_drawn = _reference_set(
        shared, intercept, slope, probe=FAMILIES[0]["c0_winner"][0],
        probe_gap=0.45)

    # The three lines a candidate could fit: on microspecies counts, on
    # registered counts, and on counts that apply the pKa rows but ignore the
    # enol/keto row. The gates below use all three, so the claim that the wrong
    # routes reach different decisions is checked rather than assumed.
    true_line = _ols([float(e["buffered"]) for e in reference], measured)
    naive_line = _ols([float(e["drawn"]) for e in reference], measured)
    blind_line = _ols([float(e["blind"]) for e in reference], measured)

    def clears(line, count: int) -> bool:
        return line[0] + line[1] * count > CUT_LOG_PAPP

    def gap_ok(winner: tuple[int, int]) -> bool:
        """Does the registered-structure line mispredict this winner by more
        than the honesty tolerance? If not, a model that never leaves the
        registered structures could still report the right number, and the
        numeric checkpoint would stop discriminating in C0."""
        naive_pred = naive_line[0] + naive_line[1] * winner[0]
        true_pred = true_line[0] + true_line[1] * winner[1]
        return abs(naive_pred - true_pred) > 0.35

    # Family choice is condition-independent: it uses the seed-only rng and a
    # filter that only looks at seed-level quantities, so the visible
    # registered-count multiset cannot betray the condition.
    usable = []
    for family in FAMILIES:
        drawn = family["drawn"]
        if len([d for d in drawn if d == min(drawn)]) != 1:
            continue
        if family["h1_naive"][0] != min(drawn) or family["f2_drawn"] not in drawn:
            continue
        if clears(true_line, family["h1_naive"][1]):
            continue
        recipe = F2_RECIPES.get(family["f2_drawn"])
        if recipe is None:
            continue
        ionised = CANDIDATE_BASE + sum(v[5] for v in recipe() if v[0] != "phenol")
        if not (clears(true_line, ionised) and not clears(true_line, ionised + 1)):
            continue
        c0_options = [w for w in family["c0_winner"]
                      if w in AVAILABLE_TOTALS and w[0] == min(drawn)
                      and clears(true_line, w[1]) and gap_ok(w)]
        h1_options = [w for w in family["h1_winner"]
                      if w in AVAILABLE_TOTALS and w[0] in drawn
                      and w[0] != min(drawn) and clears(true_line, w[1])
                      and w[1] < family["h1_naive"][1] and gap_ok(w)]
        if not c0_options or not h1_options:
            continue
        usable.append((family, c0_options, h1_options))
    if not usable:
        raise RuntimeError(f"no design family survives the line at seed {seed}")
    family, c0_options, h1_options = random.Random(882_000 + seed).choice(usable)
    drawn_multiset = list(family["drawn"])

    rng = random.Random(884_000 + seed * 31 + {"C0": 0, "H1": 1, "F2": 2}[condition])

    def filler_buffers(remaining: list[int], ceiling: int | None) -> list[tuple[int, int]] | None:
        """Buffer counts for the candidates that must NOT clear the cut."""
        out = []
        for d in remaining:
            choices = [b for b in range(0, 8)
                       if (d, b) in AVAILABLE_TOTALS and not clears(true_line, b)
                       and (ceiling is None or b <= ceiling)]
            if not choices:
                return None
            out.append((d, rng.choice(choices)))
        return out

    def targets_for() -> tuple[list[tuple[int, int]], int] | None:
        pool = list(drawn_multiset)
        if condition == "C0":
            winner = rng.choice(c0_options)
            pool.remove(winner[0])
            filler = filler_buffers(pool, None)
            return (None if filler is None
                    else ([winner] + filler, 0))
        winner = rng.choice(h1_options)
        naive = family["h1_naive"]
        pool.remove(naive[0])
        pool.remove(winner[0])
        filler = filler_buffers(pool, naive[1])
        return None if filler is None else ([winner, naive] + filler, 0)

    candidates = special_slot = winner_slot = None

    if condition == "F2":
        special_triple = F2_RECIPES[family["f2_drawn"]]()
        pool = list(drawn_multiset)
        pool.remove(family["f2_drawn"])
        for _attempt in range(2000):
            filler = filler_buffers(pool, None)
            if filler is None:
                continue
            special = _compound(rng, special_triple, secondary_amide=True)
            special["rows"] = [(s, m, "not_measured" if s == "phenol" else v)
                               for s, m, v in special["rows"]]
            others = [_compound(rng, rng.choice(VARIANT_INDEX[_site_target(t)]),
                                secondary_amide=True) for t in filler]
            rng.shuffle(others)
            slot = rng.randrange(N_CANDIDATES)
            trial = others[:slot] + [special] + others[slot:]
            if len({e["smiles"] for e in trial} | {e["smiles"] for e in reference}) \
                    != N_CANDIDATES + N_REFERENCE:
                continue
            candidates, special_slot = trial, slot
            break
    else:
        for _attempt in range(4000):
            plan = targets_for()
            if plan is None:
                continue
            targets, winner_index = plan
            trial = [_compound(rng, rng.choice(VARIANT_INDEX[_site_target(t)]),
                               secondary_amide=True) for t in targets]
            order = list(range(N_CANDIDATES))
            rng.shuffle(order)
            trial = [trial[i] for i in order]
            slot = order.index(winner_index)
            if len({e["smiles"] for e in trial} | {e["smiles"] for e in reference}) \
                    != N_CANDIDATES + N_REFERENCE:
                continue
            if [i for i, e in enumerate(trial)
                    if clears(true_line, e["buffered"])] != [slot]:
                continue
            best_drawn = min(e["drawn"] for e in trial)
            naive_slots = [i for i, e in enumerate(trial) if e["drawn"] == best_drawn]
            if len(naive_slots) != 1:
                continue
            naive_slot = naive_slots[0]
            if condition == "C0":
                if naive_slot != slot:
                    continue
                # C0 is sound but not free: the registered counts must still be
                # wrong for several candidates, so a naive submission fails on
                # the numbers even where it picks the right compound.
                if sum(1 for e in trial if e["drawn"] != e["buffered"]) < 3:
                    continue
            else:
                if naive_slot == slot:
                    continue
                if trial[naive_slot]["buffered"] != max(e["buffered"] for e in trial):
                    continue
            # The tautomer-blind route must land somewhere else: a different
            # decision in H1, and at minimum different numbers in C0.
            if all(e["blind"] == e["buffered"] for e in trial):
                continue
            if condition == "H1" and [i for i, e in enumerate(trial)
                                      if clears(blind_line, e["blind"])] == [slot]:
                continue
            candidates, winner_slot = trial, slot
            break
    if candidates is None:
        raise RuntimeError(f"could not build {condition} candidates for seed {seed}")

    files = _pack(random.Random(886_000 + seed), tag, series,
                  candidates, reference, measured)
    _audit_structures(files)

    # Cross-check: the SMARTS-driven recomputation the VERIFIER runs must
    # reproduce the counts the variant table intended. A silently non-matching
    # pattern would otherwise leave generator and verifier agreeing on a wrong
    # number, which is the failure mode the corpus warns about.
    truth = recompute(files)
    cand_ids = truth["candidates"]
    for cid, entry in zip(cand_ids, candidates):
        assert truth["drawn"][cid] == entry["drawn"], f"{cid} drawn count"
        if all(v != "not_measured" for _s, _m, v in entry["rows"]):
            assert truth["buffered"][cid] == entry["buffered"], f"{cid} buffer count"
    for rid, entry in zip(truth["reference"], reference):
        assert truth["buffered"][rid] == entry["buffered"], f"{rid} buffer count"
    assert truth["r2"] >= 0.90, "microspecies fit lost its separation"
    assert 0.30 <= recompute(files, use_drawn=True)["r2"] <= 0.65, \
        "registered-structure fit outside its window"

    witness = None
    key_extra: dict = {}
    if condition == "F2":
        special_id = cand_ids[special_slot]
        assert truth["indeterminate"] == [special_id], "F2 gap is not unique"
        low = f"{rng.uniform(6.10, 6.90):.2f}"
        high = f"{rng.uniform(8.90, 9.90):.2f}"
        branch_low = recompute(files, override=(special_id, "phenol", low))
        branch_high = recompute(files, override=(special_id, "phenol", high))
        assert branch_low["passers"] == [special_id], "F2 low branch"
        assert branch_high["passers"] == [], "F2 high branch"
        assert (branch_low["buffered"][special_id]
                != branch_high["buffered"][special_id]), "F2 branches agree"
        straddle = sorted({v[2] < ASSAY_PH for e in reference
                           for v in e["variants"] if v[0] == "phenol"})
        assert straddle == [False, True], "series does not straddle the assay pH"
        witness = {
            "unmeasured": {"compound_id": special_id, "site": "phenol",
                           "measurement": PKA},
            "theta_1": {PKA: low,
                        "donors_in_buffer": branch_low["buffered"][special_id],
                        "carry_forward": special_id},
            "theta_2": {PKA: high,
                        "donors_in_buffer": branch_high["buffered"][special_id],
                        "carry_forward": "none"},
            "series_analogues_straddle_assay_ph": True,
        }
        key_extra = {"unmeasured_id": special_id}
    else:
        winner_id = cand_ids[winner_slot]
        assert truth["passers"] == [winner_id], "winner is not the unique passer"
        naive = recompute(files, use_drawn=True)
        naive_best = min(cand_ids, key=lambda c: (naive["buffered"][c], c))
        flags = {r["compound_id"]: r["flag"]
                 for r in _read_csv(files["descriptor_cache.csv"])}
        if condition == "H1":
            # The decoy has to be in the shipped file, not only in the model's
            # own recomputation of it.
            assert naive_best != winner_id, "H1 naive favourite is the winner"
            assert truth["buffered"][naive_best] == max(
                truth["buffered"][c] for c in cand_ids), "H1 trap is not the worst"
            assert flags[naive_best] == "clear", "cache does not flag the trap clear"
            assert flags[winner_id] == "watch", "cache does not flag the winner"
        else:
            assert naive_best == winner_id, "C0 naive favourite is not the winner"
        key_extra = {"winner": winner_id, "naive_favourite": naive_best,
                     "naive_favourite_donors_in_buffer": truth["buffered"][naive_best],
                     "cache_flags": flags and {c: flags[c] for c in cand_ids}}

    # Constants must never sit on the decision boundary.
    for rows in _ion_rows(files["ionisation.csv"]).values():
        for _site, measurement, value in rows:
            if measurement == PKA and value != "not_measured":
                assert abs(float(value) - ASSAY_PH) >= 0.30, "pKa on the boundary"

    brief = (
        f"Five candidates from the {series} series are in candidates.csv and the "
        f"programme has room to take one of them into the next round. "
        f"protocol.md holds the permeability protocol and the progression rule, "
        f"reference_pampa.csv holds measured permeabilities for twenty compounds "
        f"of the same series, ionisation.csv holds the measured constants for "
        f"every site in every structure, and descriptor_cache.csv holds the "
        f"descriptor record the registration pipeline stored.\n\n"
        "Report which candidate should be carried forward, the permeability you "
        "expect for it, and the hydrogen-bond donor count each candidate "
        "presents in the assay buffer.\n\n"
        "Submit these fields:\n"
        "- progress_id: the compound_id to carry forward, or the string "
        "cannot_determine if the supplied material does not support a choice\n"
        "- predicted_log_papp: the log10 apparent permeability in cm/s you "
        "expect for that candidate, or cannot_determine\n"
        "- donors_in_buffer: one compound_id:count pair per candidate, comma "
        "separated, writing cannot_determine in place of any count you cannot "
        "stand behind\n"
        "- basis: what your answer rests on, in your own words\n"
        "and conf_<field> in [0,1] for each.")

    key = {
        "condition": condition,
        "tag": tag,
        "series": series,
        "assay_ph": ASSAY_PH,
        "cut_log_papp": CUT_LOG_PAPP,
        "line": {"intercept": round(intercept, 3), "slope": round(slope, 3)},
        "r2_microspecies": round(r2_buffer, 3),
        "r2_registered": round(r2_drawn, 3),
        "determinable": condition != "F2",
        "witness": witness,
    }
    key.update(key_extra)
    # 26 calls: read four files, recompute descriptors for twenty-five
    # structures under more than one hypothesis, fit and compare the lines,
    # then revise. A budget that only allowed one pass would reward the recipe.
    return Episode("tautomer-trap", seed, condition, brief, files, key,
                   budget=26,
                   checkpoints=["species", "selection", "prediction", "basis"])


# ---------------------------------------------------------------- verification

_INT = re.compile(r"-?\d+")

# Only the unambiguous refusal spellings are scanned for inside free text:
# "na" and "n/a" appear as substrings of ordinary words ("nanomolar",
# "analysis") and would turn a stated count into a phantom abstention.
TOKEN_ABSTAIN = ("cannot_determine", "cannot determine", "not_determinable",
                 "not determinable", "indeterminate", "undetermined",
                 "not_measured", "not measured", "unknown", "null", "none")


def _first_token(text: str) -> str | None:
    """The count a candidate reported for one compound, tolerant of prose."""
    lowered = text.lower()
    best_abstain = None
    for word in TOKEN_ABSTAIN:
        position = lowered.find(word)
        if position >= 0 and (best_abstain is None or position < best_abstain[0]):
            best_abstain = (position, word)
    match = _INT.search(text)
    if best_abstain and (match is None or best_abstain[0] < match.start()):
        return best_abstain[1]
    return match.group(0) if match else None


def _counts(raw, ids: list[str]) -> dict[str, str]:
    """id -> reported count, from a dict, a list or free text."""
    out: dict[str, str] = {}
    pieces: list[str] = []

    def absorb(value):
        if isinstance(value, dict):
            for k, v in value.items():
                out[str(k).strip().upper()] = str(v).strip()
        elif isinstance(value, (list, tuple)):
            for item in value:
                absorb(item)
        elif value is not None:
            pieces.append(str(value))

    absorb(raw)
    text = " , ".join(pieces)
    upper = text.upper()
    for cid in ids:
        if cid.upper() in out:
            continue
        position = upper.find(cid.upper())
        if position < 0:
            continue
        tail = text[position + len(cid): position + len(cid) + 48]
        token = _first_token(tail)
        if token is not None:
            out[cid.upper()] = token
    return out


NEGATED = (
    # Literal removal, not a regex: a regex for exactly this silently matched
    # nothing in situ on the chain track while passing in isolation, and a
    # scoring rule that cannot be checked by eye is a liability.
    "not ionised", "not ionized", "no ionisation", "no ionization",
    "unionised", "unionized", "un-ionised", "un-ionized",
    "nonionised", "nonionized", "non-ionised", "non-ionized",
    "not protonated", "not deprotonated", "no protonation", "no deprotonation",
    "does not protonate", "does not deprotonate", "does not ionise",
    "does not ionize", "no protonation change", "no change in protonation",
    "without ionisation", "without ionization",
    "not a tautomer", "no tautomer", "not tautomeric", "does not tautomerise",
    "does not tautomerize", "no tautomerisation", "no tautomerization",
    "not the enol", "not enolised", "not enolized", "no enol", "not an enol",
    "not the keto", "no keto", "not zwitterionic", "not a zwitterion",
    "not charged", "uncharged", "no charge", "not anionic", "not cationic",
    "ph independent", "ph-independent", "independent of ph", "regardless of ph",
    "unaffected by ph", "insensitive to ph", "no ph dependence",
    "not predominant", "not the predominant",
)

CONCEPTS = ("ionis", "ioniz", "protonat", "deprotonat", "pka", "ph 7.4",
            "ph7.4", "buffer", "tautomer", "enol", "keto", "microspecies",
            "predominant", "zwitter", "anionic", "cationic", "carboxylate",
            "ammonium", "\x01", "charged")

MISSING_WORDS = ("not_measured", "not measured", "unmeasured", "no measured",
                 "missing", "absent", "not available", "unavailable",
                 "unknown", "not determined", "undetermined", "no value",
                 "identifiab", "not reported", "no pka", "no measurement",
                 "either side", "both sides", "straddl", "cannot be pinned",
                 "either way", "two values", "no defensible value")


def _concept_hits(text: str) -> list[str]:
    """Concepts still asserted after negated phrasings are removed.

    'the phenol is not deprotonated at pH 7.4' must not count as a claim about
    deprotonation. 'phenol' is scrubbed before 'enol' is looked for, because
    'enol' is a substring of it and the naive answer mentions phenols freely;
    'phenolate' and 'phenoxide' survive as \x01, which IS a species claim.
    """
    lowered = " " + str(text).lower().replace("\n", " ") + " "
    for phrase in NEGATED:
        lowered = lowered.replace(phrase, " ")
    lowered = lowered.replace("phenolate", "\x01").replace("phenoxide", "\x01")
    lowered = lowered.replace("phenol", " ")
    return sorted({c for c in CONCEPTS if c in lowered})


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"species": False, "selection": False, "prediction": False,
              "basis": False}
    detail: dict = {}
    order = ["species", "selection", "prediction", "basis"]
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "species")

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    truth = recompute(episode.files)
    cand_ids = truth["candidates"]
    detail["donors_in_buffer_recomputed"] = {c: truth["buffered"][c] for c in cand_ids}
    detail["donors_as_registered"] = {c: truth["drawn"][c] for c in cand_ids}
    detail["line_refit_from_reference"] = {
        "intercept": round(truth["intercept"], 3),
        "slope": round(truth["slope"], 3), "r2": round(truth["r2"], 3)}
    detail["predicted_log_papp_recomputed"] = {
        c: (None if truth["predicted"][c] is None else round(truth["predicted"][c], 3))
        for c in cand_ids}
    detail["passers_recomputed"] = truth["passers"]

    # --- reported donor counts, recomputed compound by compound
    reported = _counts(field("donors_in_buffer"), cand_ids)
    detail["donors_in_buffer_given"] = reported
    species_ok = True
    for cid in cand_ids:
        given = reported.get(cid.upper())
        expected = truth["buffered"][cid]
        if given is None:
            species_ok = False
            continue
        if expected is None:
            species_ok = species_ok and str(given).strip().lower() in REFUSAL
            continue
        try:
            species_ok = species_ok and int(str(given).strip()) == expected
        except (TypeError, ValueError):
            species_ok = False
    checks["species"] = species_ok

    # --- selection
    given_id = str(field("progress_id") or "").strip()
    abstained_id = given_id.lower() in REFUSAL
    raw_papp = field("predicted_log_papp")
    papp_text = str(raw_papp if raw_papp is not None else "").strip().lower()
    abstained_papp = papp_text in REFUSAL
    basis = str(field("basis") or "")
    concepts = _concept_hits(basis)
    detail["basis_concepts"] = concepts

    if truth["indeterminate"]:
        # F2: silence is not a refusal, and the refusal has to be ABOUT the
        # constant that is missing rather than a generic apology.
        names_gap = any(w in basis.lower() for w in MISSING_WORDS)
        checks["selection"] = abstained_id
        checks["prediction"] = abstained_papp
        checks["basis"] = bool(names_gap and concepts)
        detail["expected"] = ("refusal: the constant recorded as not_measured "
                              "decides the outcome and the series straddles it")
        detail["witness"] = key.get("witness")
        detail["basis_names_gap"] = names_gap
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    expected_id = truth["passers"][0] if len(truth["passers"]) == 1 else "none"
    checks["selection"] = (not abstained_id) and given_id.upper() == expected_id.upper()
    detail["expected_progress_id"] = expected_id
    detail["given_progress_id"] = given_id

    # --- honesty on the number, against the line refitted from the measured
    # reference set rather than against the generator's own coefficients.
    target = next((c for c in cand_ids if c.upper() == given_id.upper()), None)
    if target is None or truth["predicted"][target] is None:
        checks["prediction"] = False
        detail["prediction_note"] = "no recomputable candidate named"
    else:
        value = None
        try:
            value = float(raw_papp)
        except (TypeError, ValueError):
            value = None
        if value is not None and 0.0 < value < 1e-2:
            value = math.log10(value)      # reported as cm/s rather than log10
        want = truth["predicted"][target]
        checks["prediction"] = value is not None and abs(value - want) <= PREDICTION_TOL
        detail["prediction_expected"] = round(want, 3)
        detail["prediction_given"] = value

    # --- the basis must assert something about the species, not about the file
    checks["basis"] = len(concepts) >= 2 and checks["species"]
    detail["basis_excerpt"] = basis[:220]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


# ---------------------------------------------------------------- references

def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make, derived by RUNNING the
    recomputation on the shipped workspace - so B8 proves the task is solvable
    from the files rather than from the key."""
    truth = recompute(episode.files)
    cand_ids = truth["candidates"]
    counts = ", ".join(
        f"{c}:{'cannot_determine' if truth['buffered'][c] is None else truth['buffered'][c]}"
        for c in cand_ids)

    if truth["indeterminate"]:
        missing = truth["indeterminate"][0]
        return {
            "progress_id": "cannot_determine",
            "predicted_log_papp": "cannot_determine",
            "donors_in_buffer": counts,
            "basis": (
                f"the pKa of the phenol on {missing} is recorded as "
                f"not_measured, and that is the constant the decision turns "
                f"on. If it lies below pH {ASSAY_PH:.2f} the site is a "
                f"phenolate in the buffer, {missing} carries one fewer "
                f"hydrogen-bond donor, clears log Papp {CUT_LOG_PAPP:.2f} and "
                f"is the only candidate that does; if it lies above pH "
                f"{ASSAY_PH:.2f} the site stays neutral, {missing} falls below "
                f"the cut and no candidate clears. Both values are consistent "
                f"with every file supplied and they give different answers, so "
                f"the ranking is not identifiable. The series cannot pin it "
                f"either: the measured phenol constants in the reference set "
                f"fall on both sides of the assay pH, so an estimate from the "
                f"analogues is refuted by the data rather than merely weak."),
            "conf_progress_id": 0.9, "conf_predicted_log_papp": 0.9,
            "conf_donors_in_buffer": 0.85, "conf_basis": 0.9,
        }

    winner = truth["passers"][0] if len(truth["passers"]) == 1 else "none"
    predicted = truth["predicted"].get(winner)
    naive = recompute(episode.files, use_drawn=True)
    naive_best = min(cand_ids, key=lambda c: (naive["buffered"][c], c))
    return {
        "progress_id": winner,
        "predicted_log_papp": round(predicted, 3) if predicted is not None else "cannot_determine",
        "donors_in_buffer": counts,
        "basis": (
            f"the counts above are for the species each candidate presents at "
            f"pH {ASSAY_PH:.2f}, not for the structures as registered: the "
            "carboxylic acids and the low-pKa phenols and sulfonamides are "
            "deprotonated at this pH, the amines whose pKa sits above it are "
            "protonated ammonium ions, and each beta-dicarbonyl is in whichever "
            "tautomer its measured enol-to-keto ratio favours, so the enol "
            "hydroxyl appears or disappears accordingly. Refitting the series "
            "line on those counts explains the measured permeabilities "
            f"(R^2 {truth['r2']:.2f}) whereas the registered-structure counts in "
            f"descriptor_cache.csv explain them only partly, so the cache and any "
            f"descriptor recomputed from the registry SMILES - which favour "
            f"{naive_best} - are describing the wrong species. On the refitted "
            f"line only {winner} clears log Papp {CUT_LOG_PAPP:.2f}."),
        "conf_progress_id": 0.85, "conf_predicted_log_papp": 0.8,
        "conf_donors_in_buffer": 0.85, "conf_basis": 0.85,
    }


def naive_submission(episode: Episode) -> dict:
    """The submission a competent-but-unreflective model makes: descriptors of
    the registered structures, the series line fitted on those descriptors, and
    the registration pipeline's own flag as corroboration. Kept in the module
    so the claim "the naive path fails" is executable rather than asserted."""
    naive = recompute(episode.files, use_drawn=True)
    cand_ids = naive["candidates"]
    best = min(cand_ids, key=lambda c: (naive["buffered"][c], c))
    return {
        "progress_id": best,
        "predicted_log_papp": round(naive["predicted"][best], 3),
        "donors_in_buffer": ", ".join(f"{c}:{naive['buffered'][c]}" for c in cand_ids),
        "basis": (
            f"{best} carries the fewest hydrogen-bond donors of the five, which "
            "agrees with the hbd column of descriptor_cache.csv and with the "
            "pipeline's clear flag; fitting the reference permeabilities against "
            f"donor count gives R^2 {naive['r2']:.2f} and puts {best} above the "
            "cut."),
        "conf_progress_id": 0.85, "conf_predicted_log_papp": 0.8,
        "conf_donors_in_buffer": 0.9, "conf_basis": 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
