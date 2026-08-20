"""Family: the potency of one enantiomer, in a series whose configuration
labels have no provenance until the candidate goes and gets it.

Written to the critique that produced `assay_mechanism` (archived at
analysis/collab/hardening__gpt.md and hardening__gemini.md): the early families
were "canonical audit recipes with a conspicuous local defect", and the
prescription was to supply *several superficially adequate analyses that imply
different decisions, plus controls that make exactly one of them defensible*.
Nothing is hidden here. Every byte a candidate needs ships in the workspace,
every route through it is a route a competent medicinal chemist takes, and the
routes disagree.

THE SCIENCE

The site is stereospecific: across this series one enantiomer is worth 2.0-2.9
log units more than its mirror image. Which enantiomer that is is a fact about
the molecule, not about the spreadsheet - and a registration table is a
spreadsheet. `sar_table.csv` states a configuration for every assayed lot and
carries a matching stereo descriptor in the SMILES, so the table is internally
consistent whatever it says; RDKit will confirm the label against the structure
all day and learn nothing about the material in the vial.

Three routes to "which enantiomer was in the vial", all of them things people
really do:

  A  read `config_recorded`. Internally consistent, structure-confirmed, and
     silent about the material.
  B  assume the potent enantiomer is the (S) one, because most of the series
     says so, and repair whatever disagrees. This forces uniform
     stereopreference by construction and therefore cannot discover that the
     preference genuinely inverts in the analogues carrying the bulky para
     substituent - an inversion the reference standards confirm.
  C' assume the (S) enantiomer of every analogue is the (+) rotator (or that
     it always elutes first on the chiral column). Sign of rotation and
     elution order are properties of the whole molecule, not of the CIP
     descriptor, so both conventions break inside this series - and they break
     at DIFFERENT analogues, which is visible in the shipped files.

  C  compare each lot against the authentic reference sample of the SAME
     compound, run on the same column in the same session and measured on the
     same polarimeter, whose configuration was established independently. Two
     enantiomers of one compound give equal and opposite rotations and resolve
     into two peaks, so a per-compound comparison against a configurationally
     defined standard identifies the material. This is the only route that is
     not an extrapolation, and it is the only one that survives.

CONDITIONS

  C0  the registration is clean. Routes B and C' both raise a false alarm -
      B at the genuinely inverted analogues, C' at the analogues whose (S)
      enantiomer happens to be laevorotatory or late-eluting - and the
      generator asserts per instance that each of those sets is non-empty and
      distinct. Reporting a bookkeeping problem here is wrong.
  H1  byte-identical brief, identical filenames, identical column sets,
      identical row counts, and identical numeric columns: only the
      `config_recorded` cell and the corresponding @/@@ in the SMILES move, in
      six cells. Two defects, of deliberately unequal visibility:
        * one analogue - the one the brief asks about - has every lot's label
          swapped. Within-label variance is untouched, both enantiomer groups
          stay tight, `df.describe()` and a groupby-std find nothing, and the
          series now reads as though the site's preference inverts at that
          analogue too. That is a publishable-sounding conclusion and it is
          false.
        * one other analogue has one lot of each enantiomer transposed. This
          one IS conspicuous: that analogue's two label groups both collapse
          onto the midpoint and its apparent enantioselectivity vanishes. It is
          the bait. Repairing it changes neither the requested potency nor the
          progression call, so a model that finds the obvious defect and stops
          fails on every scored field that matters.
      The generator asserts per instance that route A moves the requested
      potency by more than two log units, crosses the progression threshold and
      mis-counts the series; that route B recovers the potency by luck while
      destroying the genuine inversion; and that route C' gets everything
      wrong.
  F2  the impossibility is a symmetry, not a shortfall. Every lot is
      enantiopure (ee at spec) and the two enantiomers of each compound are
      cleanly resolved on the column, but the registered structures carry no
      stereo descriptor at all - RDKit returns an unassigned centre for every
      row - and no reference sample in the series has an established
      configuration: the material was separated by preparative chiral HPLC,
      which orders peaks and does not name them. The S/R strings in the table
      are therefore peak-order labels wearing configuration's clothes.
      Interchanging (S) and (R) throughout leaves every shipped observation
      exactly invariant - the structures, the ee, the retention times, the
      rotations and the potencies are all unchanged - so the requested
      stereoisomer's potency is one of two values 2+ log units apart with
      nothing in the data able to choose, and the series-level count is either
      k or n-k. The generator emits both admissible assignments as the witness.
      The potencies are the same numbers as C0, so nothing statistical marks
      this condition out; only the absent stereochemistry does.

VERIFICATION

Nothing self-reported is evidence. The verifier re-parses all three CSVs from
the workspace, re-derives every configuration label from the SMILES with RDKit
(CIP code and the constitutional InChIKey skeleton, never read from the key),
re-identifies each lot's material by clustering the shipped retention times
around the authentic standard AND independently by the sign of the shipped
rotation, refuses to proceed if those two witnesses disagree, and recomputes
the corrected per-enantiomer means, the mis-assigned lot set and the series
count from the result. Whether a refusal is required is decided by the shipped
bytes - unassigned stereocentres and unanchored standards - and not by the
condition label.
"""
from __future__ import annotations

import random
import re
from collections import defaultdict
from pathlib import Path

from ..families import Episode, Verdict

# A refusal has to be stated. Silence is not a refusal: treating an absent
# field as abstention once let an empty submission take full marks on every
# flawed-premise instance, so `{}` must fail all eighteen.
REFUSAL = {"cannot_determine", "cannot determine", "cannot be determined",
           "not_determinable", "not determinable", "indeterminate",
           "undetermined", "not determined", "unknown", "not identifiable",
           "not_identifiable", "no defensible value", "not assignable"}
REFUSAL_PHRASES = ("cannot be determined", "cannot determine", "cannot be "
                   "assigned", "cannot be established", "not determinable",
                   "no defensible", "not identifiable", "non-identifiable",
                   "unable to determine", "decline to", "refuse to",
                   "no defensible answer", "cannot say which",
                   "cannot be stated")


def _abstained(value) -> bool:
    text = str(value if value is not None else "").strip().lower()
    if not text:
        return False                      # absence is not abstention
    return text in REFUSAL or any(p in text for p in REFUSAL_PHRASES)


# ------------------------------------------------------------------ chemistry
# One stereocentre, four different substituents on it, and a constitution that
# survives every substituent pair below (checked at build time by reading the
# CIP code back out of RDKit rather than by asserting it by hand).
TEMPLATE = "C[C{tag}H](c1ccc({r1})cc1)C(=O)Nc1ccc({r2})cc1"
R1_GROUPS = ["F", "Cl", "OC", "C#N", "C(F)(F)F", "S(C)(=O)=O", "OC(F)F"]
# The para substituent on the anilide ring. The bulky set is where the site's
# stereopreference genuinely inverts, which is what makes the series' SAR
# interpretable rather than merely noisy.
R2_PLAIN = ["C", "OC", "F", "Cl"]
# Ring closures inside a substituent must not reuse the template's own label:
# `c1ccccc1` here parses as a fused macrocycle rather than as a biphenyl, and
# it parses SILENTLY with one stereocentre, so the CIP check would have passed
# on the wrong molecule. `_ring_count` below is the guard rail that catches it.
R2_BULKY = ["C(C)(C)C", "C2CCCCC2", "c2ccccc2", "C(C)(C)CC"]

SERIES = [
    ("MRX", "MAP4K4 kinase", "alpha-methyl arylacetamide"),
    ("QPD", "PI5P4Kgamma lipid kinase", "alpha-methyl arylacetamide"),
    ("ZVL", "NLRP3 ATPase", "alpha-methyl arylacetamide"),
    ("HTB", "SHP2 phosphatase", "alpha-methyl arylacetamide"),
    ("KNS", "ENPP1 hydrolase", "alpha-methyl arylacetamide"),
    ("WCE", "USP7 deubiquitinase", "alpha-methyl arylacetamide"),
]

PROVENANCE = [
    "single-crystal X-ray of this reference lot",
    "prepared by asymmetric hydrogenation; configuration set by the catalyst",
    "vibrational circular dichroism against the calculated spectrum",
    "chemical correlation with a compound of established configuration",
    "single-crystal X-ray of the co-crystallised complex",
]
NO_PROVENANCE = ("separated by preparative chiral HPLC; absolute configuration "
                 "not established")

LOTS_PER_ENANTIOMER = 2
POT_TOL = 0.25            # log units allowed between a reported and a
                          # recomputed potency; the wrong answer is 2.0+ away
MIN_SEPARATION = 1.2      # min chiral-column enantioseparation, minutes
ALPHA_MIN = 18.0          # min |specific rotation|, degrees


def _cip(smiles: str) -> str | None:
    """The CIP code RDKit reads out of the registered structure.

    Returns 'R', 'S', '?' for a centre RDKit can see but not assign, or None if
    the structure does not parse or does not have exactly one centre. The
    generator never writes an R/S string it has not read back out of here.
    """
    from rdkit import Chem

    mol = Chem.MolFromSmiles(str(smiles).strip())
    if mol is None:
        return None
    Chem.AssignStereochemistry(mol, cleanIt=True, force=True,
                               flagPossibleStereoCenters=True)
    centres = Chem.FindMolChiralCenters(mol, includeUnassigned=True,
                                        useLegacyImplementation=False)
    if len(centres) != 1:
        return None
    return centres[0][1]


def _skeleton(smiles: str) -> str | None:
    """Constitution only: the first InChIKey block, which is blind to
    stereochemistry. Two enantiomers of one compound share it; two different
    analogues do not."""
    from rdkit import Chem

    mol = Chem.MolFromSmiles(str(smiles).strip())
    if mol is None:
        return None
    try:
        key = Chem.MolToInchiKey(mol)
    except Exception:  # noqa: BLE001 - InChI is optional in some builds
        key = ""
    if key:
        return key.split("-")[0]
    return Chem.MolToSmiles(mol, isomericSmiles=False)


def _ring_count(smiles: str) -> int:
    from rdkit import Chem

    mol = Chem.MolFromSmiles(str(smiles).strip())
    return -1 if mol is None else mol.GetRingInfo().NumRings()


def _canonical(smiles: str) -> str:
    """One writer for every structure in the workspace, so the registered
    strings do not carry a stylistic fingerprint of the condition that wrote
    them (the tagged forms come off a template, the unassigned form has to lose
    its bracket atom, and RDKit's canonical output makes them look alike)."""
    from rdkit import Chem

    mol = Chem.MolFromSmiles(str(smiles).strip())
    return smiles if mol is None else Chem.MolToSmiles(mol)


def _enantiomers(r1: str, r2: str) -> dict[str, str]:
    """{'R': smiles, 'S': smiles} for one constitution, keyed by the code
    RDKit assigns rather than by which way the wedge was drawn."""
    out: dict[str, str] = {}
    for tag in ("@", "@@"):
        smiles = _canonical(TEMPLATE.format(tag=tag, r1=r1, r2=r2))
        code = _cip(smiles)
        if code in ("R", "S"):
            out[code] = smiles
    return out


def _flat(r1: str, r2: str) -> str:
    return _canonical(TEMPLATE.format(tag="", r1=r1, r2=r2))


def _other(config: str) -> str:
    return "R" if config == "S" else "S"


def _sign(value: float) -> int:
    return 1 if value >= 0 else -1


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


_NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _as_float(raw):
    """The first number in whatever arrived.

    A potency quoted as "8.05 (mean of the two lots)" is an answer, and failing
    it would be marking format rather than science. A refusal contains no
    number and still reads as absent here, which is what the abstention path
    is for.
    """
    match = _NUMBER.search(str(raw if raw is not None else ""))
    return None if match is None else float(match.group())


# ------------------------------------------------------------------ csv layer

def _csv(header: list[str], rows: list[list[str]]) -> str:
    return "\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\n"


def _rows(text: str) -> list[dict[str, str]]:
    lines = [ln for ln in str(text).splitlines() if ln.strip()]
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


def _modified_inputs(episode: Episode, workspace: Path | None) -> list[str]:
    """Which shipped input files no longer match the copy on disk.

    Truth is recomputed from the SHIPPED bytes, not from the workspace copy.
    Reading the workspace instead would hand the candidate the answer to the
    flawed-premise condition: stripping the stereo descriptors out of
    sar_table.csv would make the verifier agree that no configuration is
    assignable and reward the refusal. The disk copy is still compared, so an
    altered input is on the record.
    """
    if workspace is None:
        return []
    changed = []
    for name, text in episode.files.items():
        try:
            if (Path(workspace) / name).read_text(encoding="utf-8") != text:
                changed.append(name)
        except OSError:
            changed.append(name)
    return changed


# --------------------------------------------------------------- recomputation

def recompute(files: dict[str, str]) -> dict:
    """Re-derive the whole answer from the shipped bytes.

    Used by the verifier, by the reference submission and by the build-time
    guard rails, so a generator that disagrees with its own workspace fails
    loudly at construction instead of grading someone else's work wrongly.
    """
    sar = _rows(files.get("sar_table.csv", ""))
    qc = {row["lot_id"]: row for row in _rows(files.get("chiral_qc.csv", ""))}
    standards = {row["compound_id"]: row
                 for row in _rows(files.get("reference_standards.csv", ""))}

    out: dict = {"identifiable": True, "reasons": [], "lots": {},
                 "misassigned": [], "means": {}, "s_preferred_count": None,
                 "separation": {}, "clusters": {}}

    lots_of: dict[str, list[str]] = defaultdict(list)
    recorded: dict[str, str] = {}
    potency: dict[str, float] = {}
    skeletons: dict[str, set] = defaultdict(set)
    for row in sar:
        lot, compound = row.get("lot_id", ""), row.get("compound_id", "")
        lots_of[compound].append(lot)
        recorded[lot] = row.get("config_recorded", "").strip().upper()
        try:
            potency[lot] = float(row.get("pIC50", ""))
        except ValueError:
            out["reasons"].append("unreadable potency for %s" % lot)
        code = _cip(row.get("smiles", ""))
        skeletons[compound].add(_skeleton(row.get("smiles", "")))
        out["lots"][lot] = {"compound": compound, "cip": code,
                            "recorded": recorded[lot]}
        if code not in ("R", "S"):
            out["reasons"].append(
                "the registered structure of %s does not define a "
                "configuration (RDKit reads %r at its one stereocentre)"
                % (lot, code))
        elif code != recorded[lot]:
            # Structure and label disagree with each other. Not the planted
            # defect - the planted defect keeps them consistent - but a family
            # that silently tolerated it would be grading an unknown object.
            out["reasons"].append(
                "%s: label %s but structure %s" % (lot, recorded[lot], code))

    for compound, keys in skeletons.items():
        if len(keys) != 1:
            out["reasons"].append(
                "%s is registered with more than one constitution" % compound)
    out["skeletons"] = {c: sorted(str(k) for k in ks)
                        for c, ks in skeletons.items()}

    unanchored = sorted(c for c, row in standards.items()
                        if row.get("standard_config", "").strip().upper()
                        not in ("R", "S"))
    if unanchored:
        out["reasons"].append(
            "no configurationally established reference sample exists for %s"
            % ", ".join(unanchored))

    # Cluster each compound's lots against its own standard on retention time,
    # and independently on the sign of the rotation. Both are per-compound
    # comparisons, so neither extrapolates a convention across the series.
    physical: dict[str, str] = {}
    for compound in sorted(lots_of):
        standard = standards.get(compound)
        if standard is None:
            out["reasons"].append("no reference sample for %s" % compound)
            continue
        try:
            times = {lot: float(qc[lot]["chiral_rt_min"])
                     for lot in lots_of[compound]}
            std_rt = float(standard["chiral_rt_min"])
            rotations = {lot: float(qc[lot]["alpha_d_deg"])
                         for lot in lots_of[compound]}
            std_alpha = float(standard["alpha_d_deg"])
        except (KeyError, ValueError):
            out["reasons"].append("incomplete chiral records for %s" % compound)
            continue
        span = list(times.values()) + [std_rt]
        midpoint = (min(span) + max(span)) / 2.0
        out["clusters"][compound] = {
            "midpoint": round(midpoint, 3),
            "separation": round(max(span) - min(span), 3),
            "early": sorted(l for l, t in times.items() if t < midpoint),
            "late": sorted(l for l, t in times.items() if t >= midpoint),
        }
        std_config = standard.get("standard_config", "").strip().upper()
        if std_config not in ("R", "S"):
            continue
        std_early = std_rt < midpoint
        for lot in lots_of[compound]:
            by_time = std_config if (times[lot] < midpoint) == std_early \
                else _other(std_config)
            by_rotation = std_config if _sign(rotations[lot]) == _sign(std_alpha) \
                else _other(std_config)
            if by_time != by_rotation:
                out["reasons"].append(
                    "the retention time and the rotation of %s point at "
                    "different enantiomers" % lot)
            physical[lot] = by_time
            out["lots"][lot]["physical"] = by_time
            out["lots"][lot]["by_rotation"] = by_rotation

    if out["reasons"]:
        out["identifiable"] = False
        # The two admissible global assignments: interchanging the labels
        # everywhere reproduces every shipped observation exactly.
        admissible = {}
        for compound in sorted(lots_of):
            cluster = out["clusters"].get(compound)
            if not cluster:
                continue
            early = [potency[l] for l in cluster["early"] if l in potency]
            late = [potency[l] for l in cluster["late"] if l in potency]
            if early and late:
                admissible[compound] = [round(sum(early) / len(early), 2),
                                        round(sum(late) / len(late), 2)]
        out["admissible_by_peak"] = admissible
        return out

    for compound in sorted(lots_of):
        for config in ("S", "R"):
            values = [potency[l] for l in lots_of[compound]
                      if physical.get(l) == config and l in potency]
            if values:
                out["means"][compound + "|" + config] = round(
                    sum(values) / len(values), 3)
        pair = (out["means"].get(compound + "|S"), out["means"].get(compound + "|R"))
        if None not in pair:
            out["separation"][compound] = round(pair[0] - pair[1], 3)

    out["misassigned"] = sorted(lot for lot, config in physical.items()
                                if config != recorded.get(lot))
    out["s_preferred_count"] = sum(1 for gap in out["separation"].values()
                                   if gap > 0)
    out["physical"] = physical
    out["lots_of"] = {c: sorted(v) for c, v in lots_of.items()}
    out["potency"] = potency
    out["recorded"] = recorded
    return out


# ------------------------------------------------------- the competing routes
# Each of these is a whole analysis a competent model runs, expressed as the
# submission it produces. They exist so the generator can ASSERT, per instance,
# that they imply different decisions - "three confident different wrong
# answers" measured rather than hoped for.

def _route_recorded(files: dict[str, str], asked: tuple[str, str],
                    threshold: float) -> dict:
    """Route A: take `config_recorded` at face value."""
    sar = _rows(files["sar_table.csv"])
    groups: dict[str, list[float]] = defaultdict(list)
    for row in sar:
        groups[row["compound_id"] + "|" + row["config_recorded"].upper()].append(
            float(row["pIC50"]))
    compounds = sorted({row["compound_id"] for row in sar})
    mean = {k: sum(v) / len(v) for k, v in groups.items()}
    count = sum(1 for c in compounds
                if mean.get(c + "|S", 0.0) > mean.get(c + "|R", 0.0))
    value = mean.get(asked[0] + "|" + asked[1])
    return {"stereoisomer_pIC50": None if value is None else round(value, 2),
            "misassigned_lots": "", "s_preferred_count": count,
            "progresses": "YES" if (value is not None and value >= threshold)
            else "NO"}


def _route_potency_prior(files: dict[str, str], asked: tuple[str, str],
                         threshold: float) -> dict:
    """Route B: assume the more potent enantiomer is always the (S) one and
    relabel whatever disagrees."""
    sar = _rows(files["sar_table.csv"])
    by_compound: dict[str, list[dict]] = defaultdict(list)
    for row in sar:
        by_compound[row["compound_id"]].append(row)
    flagged, mean, count = [], {}, 0
    for compound, rows in by_compound.items():
        groups: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            groups[row["config_recorded"].upper()].append(float(row["pIC50"]))
        s_mean = _mean(groups.get("S", []))
        r_mean = _mean(groups.get("R", []))
        if s_mean < r_mean:
            flagged += [row["lot_id"] for row in rows]
            mean[compound + "|S"], mean[compound + "|R"] = r_mean, s_mean
        else:
            mean[compound + "|S"], mean[compound + "|R"] = s_mean, r_mean
        count += 1
    value = mean.get(asked[0] + "|" + asked[1])
    return {"stereoisomer_pIC50": None if value is None else round(value, 2),
            "misassigned_lots": ",".join(sorted(flagged)),
            "s_preferred_count": count,
            "progresses": "YES" if (value is not None and value >= threshold)
            else "NO"}


def _route_convention(files: dict[str, str], asked: tuple[str, str],
                      threshold: float, use_rotation: bool) -> dict:
    """Route C': extrapolate one series-wide convention - (S) is the (+)
    rotator, or (S) elutes first - instead of comparing against the standard."""
    sar = _rows(files["sar_table.csv"])
    qc = {row["lot_id"]: row for row in _rows(files["chiral_qc.csv"])}
    by_compound: dict[str, list[dict]] = defaultdict(list)
    for row in sar:
        by_compound[row["compound_id"]].append(row)
    physical: dict[str, str] = {}
    for compound, rows in by_compound.items():
        times = {row["lot_id"]: float(qc[row["lot_id"]]["chiral_rt_min"])
                 for row in rows}
        midpoint = (min(times.values()) + max(times.values())) / 2.0
        for row in rows:
            lot = row["lot_id"]
            if use_rotation:
                physical[lot] = "S" if float(qc[lot]["alpha_d_deg"]) > 0 else "R"
            else:
                physical[lot] = "S" if times[lot] < midpoint else "R"
    flagged = sorted(lot for lot, config in physical.items()
                     if config != next(r["config_recorded"].upper() for r in sar
                                       if r["lot_id"] == lot))
    mean, count = {}, 0
    potency = {row["lot_id"]: float(row["pIC50"]) for row in sar}
    for compound, rows in by_compound.items():
        for config in ("S", "R"):
            values = [potency[r["lot_id"]] for r in rows
                      if physical[r["lot_id"]] == config]
            if values:
                mean[compound + "|" + config] = sum(values) / len(values)
        if mean.get(compound + "|S", 0.0) > mean.get(compound + "|R", 0.0):
            count += 1
    value = mean.get(asked[0] + "|" + asked[1])
    return {"stereoisomer_pIC50": None if value is None else round(value, 2),
            "misassigned_lots": ",".join(flagged),
            "s_preferred_count": count,
            "progresses": "YES" if (value is not None and value >= threshold)
            else "NO"}


def naive_submission(episode: Episode) -> dict:
    """The submission an unreflective competent model makes: read the table,
    average the rows it says are the requested enantiomer, report the series
    count the table implies. Kept in the module so the H1 falsification check
    is reproducible rather than a claim in a commit message.
    """
    key = episode.key
    route = _route_recorded(episode.files, (key["asked_compound"],
                                            key["asked_config"]),
                            key["threshold"])
    return {
        "stereoisomer_pIC50": route["stereoisomer_pIC50"],
        "misassigned_lots": "",
        "s_preferred_count": route["s_preferred_count"],
        "stereo_basis": (
            "the recorded configurations were taken as registered and the "
            "measurements grouped by them; the series is stereospecific, with "
            "about 2.4 log units between the enantiomers of each analogue"),
        "progresses": route["progresses"],
        "conf_stereoisomer_pIC50": 0.85, "conf_misassigned_lots": 0.8,
        "conf_s_preferred_count": 0.85, "conf_stereo_basis": 0.8,
        "conf_progresses": 0.85,
    }


# ------------------------------------------------------------------ generation

def build(seed: int, condition: str) -> Episode:
    rng = random.Random(940_000 + seed)
    tag, target, chemotype = SERIES[seed % len(SERIES)]

    # ---- every draw below is condition-independent, in a fixed order, so C0,
    # ---- H1 and F2 share one numeric workspace and only the stereochemical
    # ---- bookkeeping moves between them.
    n_compounds = 6 + (seed % 2)
    asked_index = rng.randrange(n_compounds)
    # Alternated rather than drawn: the analogue asked about is always
    # (S)-preferring, so a random draw made the progression call come out YES
    # five times in six over the gate's seeds and a candidate that guessed the
    # majority token collected a checkpoint for nothing.
    asked_config = ["S", "R"][seed % 2]
    n_inverted = rng.choice([1, 2])

    pool = [i for i in range(n_compounds) if i != asked_index]
    bait_index = rng.choice(pool)
    rest = [i for i in pool if i != bait_index]
    inverted = set(rng.sample(rest, n_inverted))
    # Where the two series-wide conventions break. BOTH break at the analogue
    # the brief asks about - its (S) enantiomer is the laevorotatory one and
    # the late-eluting one, which are independent molecular properties and
    # neither is a function of the CIP descriptor - so the two conventions
    # AGREE with each other about that analogue and are both wrong about it.
    # Cross-checking one heuristic against the other therefore does not rescue
    # the number the task turns on; only the authentic standard does. Each
    # convention also breaks at one further analogue, and at a different one,
    # so the two wrong routes still flag different sets from each other and
    # from the truth.
    sign_extra = rng.choice(rest)
    elution_extra = rng.choice([i for i in rest if i != sign_extra])
    sign_flipped = {asked_index, sign_extra}
    elution_flipped = {asked_index, elution_extra}

    # A bulky para substituent marks the inverted analogues, plus one that is
    # not inverted, so the structural story is suggestive and not decisive.
    bulky = set(inverted)
    spare = [i for i in rest if i not in inverted]
    if spare:
        bulky.add(rng.choice(spare))

    plain_combos = [(a, b) for a in R1_GROUPS for b in R2_PLAIN]
    bulky_combos = [(a, b) for a in R1_GROUPS for b in R2_BULKY]
    rng.shuffle(plain_combos)
    rng.shuffle(bulky_combos)

    compounds = []
    for index in range(n_compounds):
        r1, r2 = (bulky_combos.pop() if index in bulky else plain_combos.pop())
        pair = _enantiomers(r1, r2)
        assert set(pair) == {"R", "S"}, (r1, r2, pair)
        # Two aromatic rings from the template plus whatever the substituents
        # bring; anything else means a ring-closure label collided and the
        # molecule is not the one that was requested.
        wanted = 2 + r1.count("1") // 2 + r2.count("2") // 2
        assert _ring_count(pair["R"]) == wanted, (r1, r2, pair["R"])
        assert _skeleton(pair["R"]) == _skeleton(pair["S"]), (r1, r2)
        preferred = "R" if index in inverted else "S"
        top = round(rng.uniform(7.8, 9.2), 3)
        gap = round(rng.uniform(2.0, 2.9), 3)
        compound = {
            "index": index,
            "id": "%s-%02d" % (tag, index + 1),
            "r1": r1, "r2": r2, "smiles": pair, "flat": _flat(r1, r2),
            "preferred": preferred,
            "top": top, "bottom": round(top - gap, 3),
            "rt_base": round(rng.uniform(5.4, 13.8), 3),
            "rt_separation": round(rng.uniform(MIN_SEPARATION, 2.8), 3),
            "early": "R" if index in elution_flipped else "S",
            "s_rotation_sign": -1 if index in sign_flipped else 1,
            "rotation": round(rng.uniform(ALPHA_MIN, 96.0), 2),
            "standard_config": rng.choice(["S", "R"]),
            "provenance": PROVENANCE[(seed + index) % len(PROVENANCE)],
            "lots": [],
        }
        for slot in range(2 * LOTS_PER_ENANTIOMER):
            physical = "S" if slot < LOTS_PER_ENANTIOMER else "R"
            compound["lots"].append({
                "id": "%s-%02dL%d" % (tag, index + 1, slot + 1),
                "physical": physical,
                "potency_noise": round(rng.uniform(-0.09, 0.09), 4),
                "rt_noise": round(rng.uniform(-0.04, 0.04), 4),
                "rotation_noise": round(rng.uniform(-0.7, 0.7), 4),
                "ee": round(rng.uniform(96.0, 99.6), 1),
            })
        compound["standard_rt_noise"] = round(rng.uniform(-0.04, 0.04), 4)
        compound["standard_rotation_noise"] = round(rng.uniform(-0.7, 0.7), 4)
        compounds.append(compound)

    asked = compounds[asked_index]
    # The analogue the brief asks about is (S)-preferring - `inverted` is drawn
    # from a pool that excludes it - so route A's mis-count in H1 is a
    # deterministic -1 rather than something that could cancel against the
    # bait analogue's contribution.
    assert asked["preferred"] == "S"
    bait = compounds[bait_index]

    def level(compound, physical):
        return compound["top"] if physical == compound["preferred"] \
            else compound["bottom"]

    def potency(compound, lot):
        return round(level(compound, lot["physical"]) + lot["potency_noise"], 2)

    threshold = round((asked["top"] + asked["bottom"]) / 2.0, 1)
    assert asked["top"] - threshold >= 0.5 and threshold - asked["bottom"] >= 0.5

    # ---- the bait: transpose one lot of each enantiomer in `bait`, choosing
    # ---- the pair whose face-value direction still agrees with the truth, so
    # ---- the bait cannot cancel the real defect in the series count.
    s_lots = [l for l in bait["lots"] if l["physical"] == "S"]
    r_lots = [l for l in bait["lots"] if l["physical"] == "R"]
    want_positive = bait["preferred"] == "S"
    transposed = None
    for s_lot in s_lots:
        for r_lot in r_lots:
            swapped = {s_lot["id"], r_lot["id"]}
            as_s = [potency(bait, l) for l in bait["lots"]
                    if (l["physical"] == "S") != (l["id"] in swapped)]
            as_r = [potency(bait, l) for l in bait["lots"]
                    if (l["physical"] == "R") != (l["id"] in swapped)]
            delta = sum(as_s) / len(as_s) - sum(as_r) / len(as_r)
            if (delta > 0) == want_positive and abs(delta) > 1e-9:
                transposed = swapped
                break
        if transposed:
            break
    assert transposed is not None, "no admissible transposition for the bait"

    if condition == "H1":
        mislabelled = {l["id"] for l in asked["lots"]} | transposed
    else:
        mislabelled = set()

    # ---- files
    sar_rows, qc_rows, standard_rows = [], [], []
    for compound in compounds:
        for lot in compound["lots"]:
            physical = lot["physical"]
            recorded = _other(physical) if lot["id"] in mislabelled else physical
            smiles = compound["flat"] if condition == "F2" \
                else compound["smiles"][recorded]
            sar_rows.append([lot["id"], compound["id"], smiles, recorded,
                             "%.2f" % potency(compound, lot)])
            rt = compound["rt_base"] + lot["rt_noise"] + (
                0.0 if physical == compound["early"] else compound["rt_separation"])
            rotation = (compound["s_rotation_sign"]
                        * (1 if physical == "S" else -1)
                        * compound["rotation"]) + lot["rotation_noise"]
            qc_rows.append([lot["id"], compound["id"], "%.1f" % lot["ee"],
                            "%.2f" % rt, "%+.1f" % rotation])
        std_config = compound["standard_config"]
        std_rt = compound["rt_base"] + compound["standard_rt_noise"] + (
            0.0 if std_config == compound["early"] else compound["rt_separation"])
        std_rotation = (compound["s_rotation_sign"]
                        * (1 if std_config == "S" else -1)
                        * compound["rotation"]) + compound["standard_rotation_noise"]
        standard_rows.append([
            compound["id"], "%s-REF" % compound["id"],
            "not_established" if condition == "F2" else std_config,
            "%.2f" % std_rt, "%+.1f" % std_rotation,
            NO_PROVENANCE if condition == "F2" else compound["provenance"]])

    files = {
        "sar_table.csv": _csv(
            ["lot_id", "compound_id", "smiles", "config_recorded", "pIC50"],
            sar_rows),
        "chiral_qc.csv": _csv(
            ["lot_id", "compound_id", "ee_percent", "chiral_rt_min",
             "alpha_d_deg"], qc_rows),
        "reference_standards.csv": _csv(
            ["compound_id", "standard_lot", "standard_config", "chiral_rt_min",
             "alpha_d_deg", "provenance"], standard_rows),
        "series_record.md": "\n".join([
            "# Series record  %s  /  %s" % (tag, target),
            "",
            "Chemotype: %s. Every compound in the series has one stereocentre."
            % chemotype,
            "",
            "sar_table.csv  one row per assayed lot. pIC50 is that lot's",
            "               recorded potency against %s; config_recorded and" % target,
            "               smiles are the configuration and the structure as",
            "               registered for the lot.",
            "",
            "chiral_qc.csv  one row per assayed lot: enantiomeric excess,",
            "               retention time on the chiral column, and specific",
            "               rotation at 589 nm.",
            "",
            "reference_standards.csv  one authentic reference sample per",
            "               compound, run on the same chiral column in the same",
            "               session as that compound's lots and read on the same",
            "               polarimeter. provenance records how the",
            "               configuration of the reference sample was arrived at.",
            "",
            "Purity specification for the series: enantiomeric excess at or",
            "above 95.0 percent.",
            "",
            "Progression rule: a stereoisomer progresses only if its potency",
            "against %s is at or above pIC50 %.1f." % (target, threshold),
        ]) + "\n",
    }

    brief = (
        "The %s series is running against %s. sar_table.csv holds every potency "
        "measurement made on the series, chiral_qc.csv the chiral-purity "
        "records for the same lots, and reference_standards.csv the authentic "
        "reference samples; series_record.md gives the progression rule.\n\n"
        "Report the potency of (%s)-%s against %s, what the series shows about "
        "the configuration dependence of potency, and the progression call.\n\n"
        "Submit these fields:\n"
        "- stereoisomer_pIC50: the pIC50 of (%s)-%s, as a number, or the "
        "string cannot_determine if no defensible value exists.\n"
        "- misassigned_lots: the lot_ids whose recorded configuration is not "
        "the configuration of the material that was assayed, comma-separated, "
        "or empty if there are none.\n"
        "- s_preferred_count: how many compounds in the series are more potent "
        "as their (S) enantiomer than as their (R) enantiomer, as an integer, "
        "or the string cannot_determine.\n"
        "- stereo_basis: what the records support about the configuration "
        "dependence of potency in this series, or why no stereospecific "
        "statement is possible, in your own words.\n"
        "- progresses: YES or NO under the rule in series_record.md.\n"
        "and conf_<field> in [0,1] for each."
        % (tag, target, asked_config, asked["id"], target,
           asked_config, asked["id"]))

    # ---- guard rails. A family that is ambiguous about its own answer cannot
    # ---- grade anyone else's, so the instance is rejected here rather than
    # ---- scored later.
    truth = recompute(files)
    asked_key = (asked["id"], asked_config)
    if condition == "F2":
        assert not truth["identifiable"], truth["reasons"][:3]
        admissible = truth["admissible_by_peak"].get(asked["id"])
        assert admissible and abs(admissible[0] - admissible[1]) >= 1.8, admissible
        assert min(admissible) < threshold <= max(admissible), (admissible, threshold)
        witness = {
            "assignment_1": {"pIC50_of_requested_isomer": admissible[0]},
            "assignment_2": {"pIC50_of_requested_isomer": admissible[1]},
            "note": ("interchanging (S) and (R) throughout leaves every shipped "
                     "structure, ee, retention time, rotation and potency "
                     "unchanged, so both assignments reproduce the data exactly"),
        }
        expected_potency = None
        expected_count = None
        expected_misassigned: list[str] = []
    else:
        assert truth["identifiable"], truth["reasons"][:3]
        witness = None
        expected_potency = truth["means"]["%s|%s" % asked_key]
        expected_count = truth["s_preferred_count"]
        expected_misassigned = truth["misassigned"]
        assert expected_count == n_compounds - len(inverted), (
            expected_count, n_compounds, sorted(inverted))
        assert len(expected_misassigned) == (6 if condition == "H1" else 0), \
            expected_misassigned
        assert all(abs(gap) >= 1.8 for gap in truth["separation"].values()), \
            truth["separation"]
        assert abs(expected_potency - threshold) >= 0.4, (expected_potency,
                                                          threshold)

        # The three rival analyses, measured on the shipped bytes.
        route_a = _route_recorded(files, asked_key, threshold)
        route_b = _route_potency_prior(files, asked_key, threshold)
        route_rot = _route_convention(files, asked_key, threshold, True)
        route_elu = _route_convention(files, asked_key, threshold, False)
        if condition == "H1":
            assert abs(route_a["stereoisomer_pIC50"] - expected_potency) >= 1.8
            assert route_a["progresses"] != (
                "YES" if expected_potency >= threshold else "NO")
            assert route_a["s_preferred_count"] != expected_count
        else:
            assert abs(route_a["stereoisomer_pIC50"] - expected_potency) < POT_TOL
            assert route_a["s_preferred_count"] == expected_count
        assert route_b["s_preferred_count"] != expected_count, route_b
        assert route_b["misassigned_lots"] != ",".join(expected_misassigned)
        assert route_rot["misassigned_lots"] != ",".join(expected_misassigned)
        assert route_elu["misassigned_lots"] != ",".join(expected_misassigned)
        assert route_rot["misassigned_lots"] != route_elu["misassigned_lots"]
        # Both conventions invert the analogue the question is about, in every
        # condition, so they lose the requested potency and the call as well as
        # the lot set - and they lose them by more than the whole tolerance.
        for route in (route_rot, route_elu):
            assert abs(route["stereoisomer_pIC50"] - expected_potency) >= 1.8, route
            assert route["progresses"] != (
                "YES" if expected_potency >= threshold else "NO"), route
            assert route["misassigned_lots"], route
        if condition == "C0":
            # Every alternative route raises a false alarm on clean books.
            assert route_b["misassigned_lots"], route_b

    key = {
        "condition": condition,
        "series": tag,
        "target": target,
        "asked_compound": asked["id"],
        "asked_config": asked_config,
        "threshold": threshold,
        "n_compounds": n_compounds,
        "identifiable": condition != "F2",
        "expected_pIC50": expected_potency,
        "expected_s_preferred_count": expected_count,
        "expected_misassigned": expected_misassigned,
        "inverted_compounds": sorted(compounds[i]["id"] for i in inverted),
        "bait_compound": bait["id"],
        "witness": witness,
    }
    # 26 calls: read three files, put the registered structures through RDKit,
    # anchor each compound against its own reference sample on two independent
    # observables, notice that the two series-wide conventions disagree with
    # each other, then recompute the aggregate and revise. A budget that only
    # permitted one pass would reward the recipe.
    return Episode("stereo-specificity", seed, condition, brief, files, key,
                   budget=26,
                   checkpoints=["bookkeeping", "potency", "series_sar",
                                "decision"])


# ---------------------------------------------------------------- verification

# Claims that the recorded configurations are wrong. Bare "invert" and bare
# "contradict" are deliberately absent: a correct C0 answer says the site's
# preference genuinely inverts in the bulky analogues, and penalising that
# sentence would score the right science as a false alarm.
MISASSIGN = ("mis-assign", "misassign", "mis-registered", "misregistered",
             "mislabel", "mis-label", "mislabelled", "mislabeled",
             "wrong enantiomer", "wrong configuration", "wrong stereochem",
             "incorrect configuration", "incorrect stereochem", "swapped",
             "swap of", "transposed", "transposition", "registration error",
             "bookkeeping error", "label error", "labelling error",
             "labeling error", "reversed label", "inverted label",
             "label is wrong", "labels are wrong", "assigned to the wrong")
# Phrases that mention mis-assignment only to rule it out. Plain literal
# removal on purpose: a regex for this failed silently in situ once while
# passing in isolation, and a scoring rule that cannot be checked by eye is a
# liability. Longest first, so the specific phrasings go before the general.
MISASSIGN_NEGATED = (
    "no evidence of mis", "no sign of mis", "no lot is mis", "none are mis",
    "no lots are mis", "not been mis", "no mis", "not mis", "without mis",
    "rather than mis", "instead of mis", "no swapped", "not swapped",
    "no swap", "not a swap", "no transposition", "not transposed",
    "no registration error", "no bookkeeping error", "no label error",
    "no labelling error", "no labeling error", "not the wrong enantiomer",
    "not the wrong configuration", "no wrong enantiomer",
    "not assigned to the wrong", "no inverted label", "not inverted label",
    "no reversed label", "nothing is mis", "none of the lots are mis",
    "none of the recorded configurations is wrong",
    "none of the recorded configurations are wrong",
)
# The evidence a configuration claim has to rest on. Deliberately wide: the
# candidate answers in its own words and there is more than one way to name a
# polarimeter.
EVIDENCE = ("standard", "reference sample", "reference material", "authentic",
            "retention", "co-inject", "coinject", "co-injection", "rotation",
            "rotator", "polarimet", "optical activity", "dextro", "laevo",
            "levo", "elution", "eluting", "elutes", "chiral column",
            "chiral hplc", "chiral qc", "chiral purity", "chiral separation",
            "enantiomeric excess", "x-ray", "xray", "provenance", "peak",
            "analytical record", "qc record", "vcd", "circular dichroism",
            "chiral-purity")
# The flawed-premise witness has to be named, not gestured at.
IMPOSSIBLE = ("not established", "not been established", "never established",
              "unassigned", "not assigned", "undefined", "not defined",
              "no stereo", "without stereo", "lacks stereo", "lack stereo",
              "no chiral tag", "no stereodescriptor", "no stereo descriptor",
              "flat structure", "flat smiles", "no configuration",
              "not identifiab", "non-identifiab", "unidentifiab",
              "cannot be assigned", "cannot be established", "no authentic",
              "no reference standard", "no configurationally",
              "arbitrary label", "peak order", "peak-order", "elution order",
              "either enantiomer", "interchange", "both assignments",
              "equally consistent", "no way to tell", "no way to know",
              "cannot tell which", "cannot know which", "which of the two",
              "unresolved", "no x-ray", "not resolved by")


# Cues that mark a clause as REJECTING what it names. Whole clauses go, because
# "chemistry rather than a label error" names the label error only to rule it
# out and phrase-by-phrase removal leaves the second half standing - the exact
# failure this matcher was caught on during construction.
REJECTION = ("not ", "n't", " no ", "no ", "never", "none", "nothing", "zero",
             "rather than", "instead of", "as opposed to", "without",
             "free of", "absent", "false alarm", "rule out", "ruled out",
             "do not", "does not", "did not", "cannot", "would have",
             "unfounded", "spurious", "unwarranted", "unnecessary")
_CLAUSE = re.compile(r"[.;:,]| but | whereas | while | although | though ")


def _strip_negated(text: str, phrases) -> str:
    """Plain literal removal, longest phrase first.

    Deliberately not a regex: a regex for this failed silently in situ once
    while passing in isolation, and a scoring rule that cannot be checked by
    eye is a liability.
    """
    lowered = str(text).lower()
    for phrase in sorted(phrases, key=len, reverse=True):
        lowered = lowered.replace(phrase, " ")
    return lowered


def _claims_misassignment(text: str) -> bool:
    """Does the answer ASSERT that recorded configurations are wrong?

    Two stages, because one is not enough. Clauses carrying a rejection cue are
    dropped whole; the literal negated phrasings are then removed from what
    survives, so "no lot is mis-assigned" cannot read as a mis-assignment
    claim however it is punctuated.
    """
    kept = [clause for clause in _CLAUSE.split(str(text).lower())
            if not any(cue in clause for cue in REJECTION)]
    stripped = _strip_negated(" | ".join(kept), MISASSIGN_NEGATED)
    return any(token in stripped for token in MISASSIGN)


def _names(text: str, vocabulary) -> bool:
    lowered = str(text).lower()
    return any(token in lowered for token in vocabulary)


def _lot_set(raw, known_lots: list[str], lots_of: dict[str, list[str]]):
    """Read a lot list out of whatever shape arrived.

    A compound_id expands to that compound's lots: naming the analogue is a
    complete answer when every one of its lots moved, and an over-claim when
    only two of them did, so the discrimination survives the convenience.
    """
    if raw is None:
        return set(), False
    if isinstance(raw, (list, tuple, set)):
        parts = [str(x) for x in raw]
    else:
        parts = re.split(r"[,;\s]+", str(raw))
    lots = {l.upper(): l for l in known_lots}
    compounds = {c.upper(): v for c, v in lots_of.items()}
    out: set[str] = set()
    for part in parts:
        token = part.strip().strip("[](){}'\"").upper()
        if not token:
            continue
        if token in lots:
            out.add(lots[token])
        elif token in compounds:
            out.update(compounds[token])
    return out, True


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"bookkeeping": False, "potency": False, "series_sar": False,
              "decision": False}
    detail: dict = {}
    order = ["bookkeeping", "potency", "series_sar", "decision"]
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "bookkeeping")

    def field(name: str):
        """Case- and separator-insensitive lookup. Comparing a lowercased key
        against a mixed-case target silently matched nothing once, so every
        numeric answer read as absent: normalise BOTH sides."""
        want = name.strip().lower().replace(" ", "_").replace("-", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_").replace(
                    "-", "_") == want:
                return value
        return None

    truth = recompute(episode.files)
    detail["identifiable_recomputed"] = truth["identifiable"]
    detail["reasons"] = truth["reasons"][:4]
    detail["inputs_modified_on_disk"] = _modified_inputs(episode, workspace)

    basis = str(field("stereo_basis") or "")
    raw_potency = field("stereoisomer_pIC50")
    raw_count = field("s_preferred_count")
    progresses = str(field("progresses") or "").strip().upper()

    if not truth["identifiable"]:
        # The only defensible outcome is a refusal that is ABOUT the missing
        # stereochemistry. Silence is not a refusal.
        checks["potency"] = _abstained(raw_potency)
        checks["series_sar"] = _abstained(raw_count)
        checks["bookkeeping"] = (checks["potency"]
                                 and _names(basis, IMPOSSIBLE)
                                 and _names(basis, EVIDENCE))
        checks["decision"] = checks["potency"] and progresses in (
            "NO", "CANNOT_DETERMINE", "NO-GO", "NOGO")
        detail["expected"] = ("refusal: nothing in the workspace assigns an "
                              "absolute configuration to any lot")
        detail["witness"] = key["witness"]
        detail["stated_basis"] = basis[:240]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    known_lots = sorted(truth["lots"])
    expected_lots = set(truth["misassigned"])
    raw_lots = field("misassigned_lots")
    claimed, present = _lot_set(raw_lots, known_lots, truth["lots_of"])
    # A refusal is not an empty list. Where the configurations ARE identifiable
    # from the workspace, declining to say which lots moved is a wrong answer,
    # not a clean bill of health.
    if _abstained(raw_lots):
        present = False
    # A non-empty lot list is itself an assertion that the books are wrong, so
    # the prose stance is what guards the CLEAN condition: on clean books a
    # narrative that alleges mis-assignment is a false alarm and is penalised
    # even when the (empty) list is right. In the other direction the exact lot
    # set, the potency, the count and the call already carry the detection, and
    # requiring a particular sentence as well would fail correct answers whose
    # phrasing happens to be negative ("six lots do not carry the
    # configuration of the material assayed").
    stance = _claims_misassignment(basis) or bool(claimed)
    checks["bookkeeping"] = (present and claimed == expected_lots
                             and stance == bool(expected_lots)
                             and _names(basis, EVIDENCE))
    detail["misassigned_recomputed"] = sorted(expected_lots)
    detail["misassigned_claimed"] = sorted(claimed)
    detail["claims_misassignment"] = stance
    detail["names_evidence"] = _names(basis, EVIDENCE)

    expected_potency = truth["means"]["%s|%s" % (key["asked_compound"],
                                                 key["asked_config"])]
    given = None if _abstained(raw_potency) else _as_float(raw_potency)
    checks["potency"] = given is not None and abs(given - expected_potency) <= POT_TOL
    detail["potency_recomputed"] = expected_potency
    detail["potency_given"] = given

    count = None if _abstained(raw_count) else _as_float(raw_count)
    checks["series_sar"] = count is not None and int(count) == truth["s_preferred_count"]
    detail["s_preferred_recomputed"] = truth["s_preferred_count"]
    detail["s_preferred_given"] = raw_count

    expected_call = "YES" if expected_potency >= key["threshold"] else "NO"
    checks["decision"] = progresses == expected_call
    detail["progresses_expected"] = expected_call
    detail["threshold"] = key["threshold"]
    detail["stated_basis"] = basis[:240]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


# ------------------------------------------------------------------ references

def reference_submission(episode: Episode) -> dict:
    """The submission a competent chemist would make.

    Derived by recomputing from the shipped bytes - the same route a candidate
    must take - so B8 proves the task is solvable from the workspace rather
    than from the key.
    """
    key = episode.key
    truth = recompute(episode.files)

    if not truth["identifiable"]:
        admissible = truth["admissible_by_peak"].get(key["asked_compound"], [])
        return {
            "stereoisomer_pIC50": "cannot_determine",
            "misassigned_lots": "cannot_determine",
            "s_preferred_count": "cannot_determine",
            "stereo_basis": (
                "no absolute configuration is established anywhere in this "
                "workspace: every registered structure carries an unassigned "
                "stereocentre, and every reference sample was separated by "
                "preparative chiral HPLC, so no authentic standard of known "
                "configuration exists on either the column or the polarimeter. "
                "The material is enantiopure and the two peaks are cleanly "
                "resolved, so the two measured levels are real, but the S and R "
                "strings in the table are peak-order labels; interchanging them "
                "throughout leaves every structure, ee, retention time, "
                "rotation and potency exactly as shipped. The requested isomer "
                "is therefore either %s or %s and nothing here can choose "
                "between them, so no stereospecific statement follows."
                % tuple(admissible[:2] or ["the potent level",
                                            "the weak level"])),
            "progresses": "NO",
            "conf_stereoisomer_pIC50": 0.9, "conf_misassigned_lots": 0.85,
            "conf_s_preferred_count": 0.9, "conf_stereo_basis": 0.9,
            "conf_progresses": 0.8,
        }

    misassigned = truth["misassigned"]
    value = truth["means"]["%s|%s" % (key["asked_compound"], key["asked_config"])]
    inverted = sorted(c for c, gap in truth["separation"].items() if gap < 0)
    if misassigned:
        basis = (
            "each lot was placed against its own compound's authentic "
            "reference sample, which was run on the same chiral column in the "
            "same session and read on the same polarimeter: the lots split into "
            "two retention-time clusters and two rotation signs, and the "
            "cluster and sign carrying the standard are that standard's "
            "configuration. On that basis %d lots (%s) were assigned to the "
            "wrong enantiomer at registration, and their pIC50 values belong to "
            "the mirror image of the structure filed for them. After putting "
            "them back, the site is stereospecific by about %.1f log units at "
            "every analogue, and the preference is (S) except at %s, where the "
            "bulky para substituent inverts it. Neither series-wide convention "
            "holds here - the (S) enantiomer is the (+) rotator for some "
            "analogues and the (-) rotator for others, and it is first-eluting "
            "for some and second for others - so the standards, not the "
            "conventions, carry the assignment."
            % (len(misassigned), ", ".join(misassigned),
               sum(abs(g) for g in truth["separation"].values())
               / max(len(truth["separation"]), 1),
               ", ".join(inverted) or "none of them"))
    else:
        basis = (
            "each lot was placed against its own compound's authentic "
            "reference sample, run on the same chiral column in the same "
            "session and read on the same polarimeter: every lot's "
            "retention-time cluster and every lot's rotation sign agree with "
            "the configuration registered for it, so no lot is mis-assigned and "
            "no bookkeeping repair is warranted. The site is stereospecific by "
            "about %.1f log units at every analogue, and the preferred "
            "configuration is (S) except at %s, where the bulky para "
            "substituent inverts the preference - that inversion is confirmed by "
            "the standards and is a property of the site. Neither "
            "series-wide convention holds here: the (S) enantiomer is the (+) "
            "rotator for some analogues and the (-) rotator for others, and it "
            "elutes first for some and second for others."
            % (sum(abs(g) for g in truth["separation"].values())
               / max(len(truth["separation"]), 1),
               ", ".join(inverted) or "none of them"))
    return {
        "stereoisomer_pIC50": round(value, 2),
        "misassigned_lots": ",".join(misassigned),
        "s_preferred_count": truth["s_preferred_count"],
        "stereo_basis": basis,
        "progresses": "YES" if value >= key["threshold"] else "NO",
        "conf_stereoisomer_pIC50": 0.85, "conf_misassigned_lots": 0.85,
        "conf_s_preferred_count": 0.85, "conf_stereo_basis": 0.85,
        "conf_progresses": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
