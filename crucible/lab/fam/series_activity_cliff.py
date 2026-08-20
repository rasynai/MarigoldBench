"""Family: does the SAR of a congeneric series support the design hypothesis?

Written to the same collaborator critique that produced `assay_mechanism`
(archived at analysis/collab/hardening__gpt.md and hardening__gemini.md): the
first batch of families were "canonical audit recipes with a conspicuous local
defect", and the prescription was to ship *several superficially adequate
analyses that imply different decisions, plus controls that make exactly one of
them defensible*. Nothing here is hidden. Every number a candidate needs is in
the two CSVs and every route through them is a route a competent medicinal
chemist takes. The routes disagree, and which one is licensed is decided by a
file that the summary table gives no reason to open.

THE SCIENCE

A programme has one design vector - grow the lipophilic tail - and one
hypothesis: potency is a smooth function of cLogP across the range made so far,
so the next round should push further along the vector. Two things can kill that
hypothesis and they are not the same thing:

  * the trend is not a trend. It is one measurement with enormous leverage,
    and the leverage point is the hypothesis's own poster child - the newest,
    most lipophilic, apparently most potent compound. Drop it and the slope
    inverts.
  * the trend is real but not smooth. Two analogues that differ by a methyl
    shift, with cLogP equal to three decimal places, are two log units apart.
    A descriptor that cannot separate them cannot be used to predict the next
    analogue, whatever the pooled fit says.

Both of those look identical to the routine pipeline - pool the released
potencies, regress pIC50 on cLogP, report slope, R-squared, p - and the routine
pipeline produces a confident number in every condition. So do three other
defensible-looking routes, and they disagree with each other. Measured over
seeds 11-16 during construction:

  1. Pooled least squares. In H1 shape A this is +0.28 to +0.62 at p < 0.05 with
     the most lipophilic compound as its most potent point, which reads as a
     textbook confirmation of the vector. The truth is a negative slope.
  2. Rank correlation, or any fit that downweights the far point. On the same
     bytes Spearman's rho is about -0.5, because the leverage point is the only
     thing holding the pooled slope up. Two standard summaries of one file,
     opposite signs, and nothing in the file says which to believe.
  3. Screening on the assay software's own goodness-of-fit statistic, or on the
     replicate count. `curve_r2` is carried in the summary table for every
     compound, and a four-parameter fit to a well-behaved curve is excellent
     whether or not the number it produced was transcribed correctly. Both
     screens drop innocent compounds and keep the fatal one: 0/18 instances.
  4. Residual or influence screening. This one does find the compound - its
     residual is the largest in the set - but finding it is not the same as
     being licensed to drop it. The most potent, most lipophilic, newest
     compound is the one the hypothesis is built on, and in C0 the largest
     residual belongs to a compound whose measurement is sound, where dropping
     it is exactly the false alarm the condition is there to catch. The screen
     scores 0/18: it cannot say what the compound's potency actually is.

Exactly one route settles it: every released potency ships with the
dose-response record it was derived from, so a released value can be compared
with the curve underneath it. That comparison costs nothing and decides
everything, and it is not available anywhere else in the workspace - the summary
table alone is consistent with both worlds. So `record_pic50` asks for the
potency each excluded compound's own record supports, and the verifier
recomputes it by interpolating that compound's curve to 50% inhibition. The
value is deliberately NOT what the trend predicts for that compound: every
compound whose released value is wrong also sits 0.5-1.1 log units off the local
trend, so extrapolating the fit produces a number 2-3 times the tolerance away
from the record. The honest number can only be read off the plate.

CONDITIONS

Each instance is one of two shapes, chosen by seed parity, so that no heuristic
about data quality has a stable relationship to the answer.

  shape A - "the long-chain flagship". Eleven analogues packed into a 1.2-unit
      cLogP window plus one much more lipophilic new compound about two units
      beyond them, where a programme that has decided to grow the tail puts its
      next compound.
      C0: the packed set trends up, the new compound sits on that line, every
          released value agrees with its own curve. Answer: supported.
      H1: the packed set trends DOWN, and the new compound's released potency is
          its curve's value plus about three log units - the slip a nM number
          entered in a uM field produces. That one point carries about 70% of
          the leverage in the pooled fit, so pooled least squares reports a
          strong positive slope and the hypothesis looks confirmed. Censor the
          one value its own curve contradicts and the slope is negative.
          Answer: not supported.
  shape B - "the twin pair". Twelve analogues across a 2.7-unit window,
      including a matched pair whose cLogP agrees to three decimals, sitting at
      the CENTRE of the range: a point at the centroid moves the intercept and
      not the slope, so the trend a candidate must report is the same whether
      the odd member is downweighted or not and only the smoothness question
      turns on it.
      C0: one member of the pair is genuinely two log units weaker - a real
          discontinuity, of the kind a tert-butyl for n-butyl swap produces.
          Both curves support their released values. The pooled slope is
          positive and significant and the series is still not smooth where it
          matters, so the descriptor cannot predict the next analogue.
          Answer: not supported.
      H1: series.csv is byte-identical to C0's - the same pair, the same gap,
          the same fit statistics - but the weak member's curve puts it above
          the trend with its partner. The gap is a transcription artifact and
          censoring it removes the discontinuity. Answer: supported.
      The two shapes therefore reward opposite reflexes: in shape A finding a
      broken measurement means the hypothesis dies, in shape B it means the
      hypothesis lives, and in C0 of both shapes there is nothing to find. Both
      answers appear in both conditions across seeds, so neither the verdict nor
      the presence of a data problem is a marker of the condition.
  F2  the file is not one series. Six compounds sit on one Bemis-Murcko
      scaffold and six on another, the two are separated along cLogP, and their
      within-scaffold slopes have OPPOSITE signs with comparable magnitude and
      equal group sizes. The pooled slope is positive and significant and is a
      property of the offset between the two chemotypes rather than of any
      chemistry: no single number is the trend of "the series", because the
      pooled estimate's sign is fixed by how many of each chemotype happen to
      be in the file. The witness is emitted in the key as the two recomputed
      group slopes, so the refusal is a provable statement about the set and not
      a complaint about data quality.

WHY THE CONDITIONS ARE INDISTINGUISHABLE WITHOUT THE SCIENCE

All three conditions ship the same three filenames with the same columns, 12
compound rows, 96 curve rows, the same numeric precision, a byte-identical memo
and a byte-identical brief. C0 and H1 share one random stream and draw in the
same order, so they agree on the compound set, the identifiers, which three
compounds carry a mediocre `curve_r2` and which two were measured in duplicate.
Those decoys never land on the compound the condition turns on, in EITHER
condition, so they cannot be read as a marker. In shape B series.csv is
identical byte for byte between C0 and H1 and the entire difference in the
workspace is the eight percent-inhibition numbers of one compound.

VERIFICATION

verify() re-derives everything from the shipped bytes: cLogP with Crippen from
the SMILES rather than from the supplied column, the potency implied by each
compound's own curve by interpolation at 50% inhibition, which released values
that contradicts, the least-squares slope over what survives, the matched-pair
gaps from Morgan fingerprints, and the Bemis-Murcko partition. Every number the
candidate reports is recomputed and checked against the observable; none of them
is taken as evidence for itself. build(), verify() and reference_submission() all
call the same `_analyse`, so the key cannot drift from the grading and the
reference cannot be right for a reason the candidate has no access to: the
generator writes the CSVs, parses its own rounded bytes back through that
function and asserts the condition's margins before returning, which means a
construction bug fails the build rather than the candidate.

An empty submission fails all 18 instances, and so does every content-free
submission tried during construction: a fixed "supported, slope 0.5, nothing
wrong", a fixed refusal, and a refusal that cites data quality rather than the
two chemotypes. Silence is not a refusal anywhere, including F2, where every
checkpoint is gated on an explicit abstention.
"""
from __future__ import annotations

import math
import random
import re
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "undefined", "none", "n_a",
           "na", "null", "no single slope", "not applicable"}

# The dose grid, as text, so every condition writes byte-identical dose columns.
DOSE_TEXT = ("0.0005", "0.0025", "0.0125", "0.0625",
             "0.3125", "1.5625", "7.8125", "39.0625")
DOSES = tuple(float(d) for d in DOSE_TEXT)

N_COMPOUNDS = 12
REPRO_LOG = 0.4          # stated in the memo: agreement of repeat determinations
SUPPORT_TOL = 0.45       # a released value further than this from its own curve
                         # is not supported by the record
CLIFF_MIN = 1.5          # matched-pair gap that counts as a discontinuity
NEAR_TANIMOTO = 0.55     # Morgan r=2 similarity for "near-identical"
NEAR_DLOGP = 0.25        # and the descriptor must not separate them
MIN_SLOPE = 0.20         # pIC50 per cLogP unit worth carrying a vector on
NOISE = 0.12             # measurement scatter, consistent with REPRO_LOG
PIC50_FLOOR, PIC50_CEIL = 4.75, 8.95     # inside the measurable window

PROGRAMMES = [
    ("CRU-41", "MCL1", "TR-FRET displacement of a BID BH3 peptide"),
    ("CRU-42", "KEAP1", "fluorescence polarisation, NRF2 peptide probe"),
    ("CRU-43", "NAMPT", "coupled enzymatic assay, NADH readout"),
    ("CRU-44", "sEH", "fluorogenic substrate hydrolysis"),
    ("CRU-45", "PHGDH", "coupled enzymatic assay, NADH readout"),
    ("CRU-46", "ENPP1", "AMP-Glo luminescent detection"),
]

HEADS = [
    ("O=C({am})c1ccc({ch})cc1", "para-alkoxybenzamide"),
    ("O=S(=O)({am})c1ccc({ch})cc1", "para-alkoxybenzenesulfonamide"),
]
AMINES = ["Nc1ccccc1", "Nc1cccc(F)c1", "Nc1ccc(F)cc1", "Nc1cccc(C)c1",
          "Nc1ccc(C)cc1", "Nc1cccc(Cl)c1", "Nc1ccc(Cl)cc1", "Nc1cccc(OC)c1"]
AMINE_ALT = "Nc1ccc2ccccc2c1"          # a second chemotype: distinct scaffold
CHAINS = ["OC", "OCC", "OCCC", "OCCCC", "OC(C)(C)C", "OCCCCC", "OCCCCCC",
          "OCCCCCCC", "OCCCCCCCC"]

FRONTIER_GAP = 2.1       # cLogP units between the packed set and the new compound
SLIP_LOG = 3.0           # size of the transcription slip: a nM value
                         # entered in a uM field, jittered so the offset itself
                         # is not a round number a candidate could assume


# ------------------------------------------------------------------ chemistry

def _fingerprint(mol):
    try:
        from rdkit.Chem import rdFingerprintGenerator
        gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        return gen.GetFingerprint(mol)
    except Exception:  # noqa: BLE001 - older RDKit
        from rdkit.Chem import AllChem
        return AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)


def _describe(smiles: str) -> dict:
    from rdkit import Chem
    from rdkit.Chem import Crippen
    from rdkit.Chem.Scaffolds import MurckoScaffold

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {}
    return {"smiles": smiles,
            "clogp": Crippen.MolLogP(mol),
            "scaffold": MurckoScaffold.MurckoScaffoldSmiles(mol=mol),
            "fp": _fingerprint(mol)}


def _pool(template: str, amines: list[str], chains: list[str]) -> list[dict]:
    from rdkit import Chem

    seen: set[str] = set()
    out: list[dict] = []
    for amine in amines:
        for chain in chains:
            smiles = template.format(am=amine, ch=chain)
            described = _describe(smiles)
            if not described:
                continue
            canonical = Chem.MolToSmiles(Chem.MolFromSmiles(smiles))
            if canonical in seen:
                continue
            seen.add(canonical)
            out.append(described)
    out.sort(key=lambda c: (c["clogp"], c["smiles"]))
    return out


def _similarity(a: dict, b: dict) -> float:
    from rdkit import DataStructs
    return DataStructs.TanimotoSimilarity(a["fp"], b["fp"])


def _is_near(a: dict, b: dict) -> bool:
    """A matched pair: same scaffold, cLogP cannot separate them, and the
    structures are close. This is the population the smoothness claim is about;
    consecutive chain homologues are excluded by the descriptor criterion."""
    return (a["scaffold"] == b["scaffold"]
            and abs(a["clogp"] - b["clogp"]) <= NEAR_DLOGP
            and _similarity(a, b) >= NEAR_TANIMOTO)


def _pick(pool: list[dict], targets: list[float], used: set[int]) -> list[int]:
    chosen: list[int] = []
    for target in targets:
        best, best_gap = None, None
        for index, candidate in enumerate(pool):
            if index in used:
                continue
            gap = abs(candidate["clogp"] - target)
            if best_gap is None or gap < best_gap:
                best, best_gap = index, gap
        if best is None:
            raise RuntimeError("compound pool exhausted")
        used.add(best)
        chosen.append(best)
    return chosen


def _find_matched_pair(pool: list[dict], target: float) -> tuple[int, int]:
    """The matched pair whose mean cLogP is nearest `target`.

    Restricted to pairs the descriptor genuinely cannot separate (<= 0.05), so
    the constructed discontinuity cannot be explained away as a lipophilicity
    difference.
    """
    best, best_gap = None, None
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            a, b = pool[i], pool[j]
            if abs(a["clogp"] - b["clogp"]) > 0.05:
                continue
            if a["scaffold"] != b["scaffold"] or _similarity(a, b) < NEAR_TANIMOTO:
                continue
            gap = abs((a["clogp"] + b["clogp"]) / 2.0 - target)
            if best_gap is None or gap < best_gap:
                best, best_gap = (i, j), gap
    if best is None:
        raise RuntimeError("no matched pair in pool")
    return best


# ------------------------------------------------------------------ statistics

def _ols(xs: list[float], ys: list[float]) -> tuple[float, float, float, float]:
    """slope, intercept, r-squared, t-statistic on the slope."""
    n = len(xs)
    if n < 3:
        return 0.0, 0.0, 0.0, 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0:
        return 0.0, my, 0.0, 0.0
    slope = sxy / sxx
    intercept = my - slope * mx
    r2 = (slope * sxy / syy) if syy > 0 else 0.0
    r2 = max(0.0, min(1.0, r2))
    if r2 >= 1.0 or n <= 2:
        t = float("inf")
    else:
        t = math.sqrt(r2 * (n - 2) / max(1.0 - r2, 1e-12))
    return slope, intercept, r2, t


def _hill(dose: float, pic50: float, hill: float) -> float:
    ic50_uM = 10.0 ** (6.0 - pic50)
    return 100.0 / (1.0 + (ic50_uM / dose) ** hill)


def _implied_pic50(points: list[tuple[float, float]]) -> float | None:
    """Potency the curve itself supports: interpolate to 50% inhibition.

    Deliberately not the generator's parameter but the observable - the number
    a chemist reads off the plate. Returns None when the curve never crosses
    50%, in which case no released potency is supported by it.
    """
    ordered = sorted(points)
    for (d1, y1), (d2, y2) in zip(ordered, ordered[1:]):
        if (y1 - 50.0) * (y2 - 50.0) <= 0 and y2 != y1:
            frac = (50.0 - y1) / (y2 - y1)
            log_dose = math.log10(d1) + frac * (math.log10(d2) - math.log10(d1))
            return 6.0 - log_dose
    return None


# ------------------------------------------------------------------- analysis

def _parse_series(text: str) -> list[dict]:
    rows: list[dict] = []
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 6:
            continue
        try:
            rows.append({"id": parts[0].strip(), "smiles": parts[1].strip(),
                         "clogp_col": float(parts[2]), "pic50": float(parts[3]),
                         "curve_r2": float(parts[4]),
                         "n_replicates": int(parts[5])})
        except ValueError:
            continue
    return rows


def _parse_curves(text: str) -> dict[str, list[tuple[float, float]]]:
    out: dict[str, list[tuple[float, float]]] = {}
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 3:
            continue
        try:
            out.setdefault(parts[0].strip(), []).append(
                (float(parts[1]), float(parts[2])))
        except ValueError:
            continue
    return out


def _analyse(series_text: str, curves_text: str) -> dict:
    """Everything the answer rests on, re-derived from the shipped bytes.

    build(), verify() and reference_submission() all call this one function, so
    the key cannot drift from the grading and the reference cannot be right for
    a reason the candidate has no access to.
    """
    rows = _parse_series(series_text)
    curves = _parse_curves(curves_text)
    for row in rows:
        described = _describe(row["smiles"])
        row["clogp"] = described.get("clogp", row["clogp_col"])
        row["scaffold"] = described.get("scaffold", "")
        row["fp"] = described.get("fp")
        row["described"] = described
        implied = _implied_pic50(curves.get(row["id"], []))
        row["implied"] = implied
        row["supported"] = (implied is not None
                            and abs(implied - row["pic50"]) <= SUPPORT_TOL)

    unsupported = sorted(r["id"] for r in rows if not r["supported"])
    kept = [r for r in rows if r["supported"]]

    def fit(subset: list[dict]) -> dict:
        slope, intercept, r2, t = _ols([r["clogp"] for r in subset],
                                       [r["pic50"] for r in subset])
        return {"slope": slope, "intercept": intercept, "r2": r2, "t": t,
                "n": len(subset)}

    def cliff(subset: list[dict]) -> dict | None:
        found_pairs = []
        for i in range(len(subset)):
            for j in range(i + 1, len(subset)):
                a, b = subset[i], subset[j]
                if not (a.get("described") and b.get("described")):
                    continue
                if not _is_near(a["described"], b["described"]):
                    continue
                found_pairs.append({"pair": sorted([a["id"], b["id"]]),
                                    "gap": abs(a["pic50"] - b["pic50"]),
                                    "dclogp": abs(a["clogp"] - b["clogp"])})
        if not found_pairs:
            return None
        found_pairs.sort(key=lambda p: -p["gap"])
        best = dict(found_pairs[0])
        best["is_cliff"] = best["gap"] >= CLIFF_MIN
        best["gaps"] = [round(p["gap"], 3) for p in found_pairs]
        return best

    groups: dict[str, list[dict]] = {}
    for row in kept:
        groups.setdefault(row["scaffold"], []).append(row)
    ranked = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    group_report = [{"scaffold": scaffold, "n": len(members),
                     "ids": sorted(r["id"] for r in members),
                     "slope": round(fit(members)["slope"], 4)}
                    for scaffold, members in ranked]

    # Not one series: two comparably sized chemotypes whose own slopes point in
    # opposite directions. Any single pooled slope is then a statement about the
    # composition of the file, not about chemistry.
    not_one_series = False
    if len(ranked) >= 2:
        (_s1, m1), (_s2, m2) = ranked[0], ranked[1]
        if len(m1) >= 4 and len(m2) >= 4:
            a = fit(m1)["slope"]
            b = fit(m2)["slope"]
            if a * b < 0 and min(abs(a), abs(b)) >= MIN_SLOPE:
                not_one_series = True

    kept_fit = fit(kept)
    kept_cliff = cliff(kept)
    pooled_fit = fit(rows)
    pooled_cliff = cliff(rows)

    cliff_pair = kept_cliff["pair"] if (kept_cliff and kept_cliff["is_cliff"]) else None
    supported = (not not_one_series
                 and kept_fit["slope"] >= MIN_SLOPE
                 and cliff_pair is None)
    return {
        "rows": rows, "kept": kept, "unsupported": unsupported,
        "fit": kept_fit, "pooled_fit": pooled_fit,
        "cliff": kept_cliff, "pooled_cliff": pooled_cliff,
        "cliff_pair": cliff_pair,
        "pooled_cliff_pair": (pooled_cliff["pair"] if
                              (pooled_cliff and pooled_cliff["is_cliff"]) else None),
        "groups": group_report, "not_one_series": not_one_series,
        "hypothesis_supported": supported,
        "curve_rows": sum(len(points) for points in curves.values()),
    }


# ---------------------------------------------------------------- construction

def _curve_block(compound_id: str, true_pic50: float, hill: float,
                 n_wells: int, rng: random.Random) -> list[str]:
    lines = []
    for dose_text, dose in zip(DOSE_TEXT, DOSES):
        pct = _hill(dose, true_pic50, hill) + rng.uniform(-1.2, 1.2)
        lines.append(f"{compound_id},{dose_text},{pct:.1f},{n_wells}")
    return lines


def _compose(seed: int, condition: str, attempt: int) -> tuple[dict, dict]:
    """One candidate instance: the files plus the construction record."""
    # C0 and H1 share the random stream, and every draw below happens in the
    # same order in both, so the two conditions agree on the compound set, the
    # identifiers and the decoys. In shape B they agree on series.csv byte for
    # byte and the entire difference between the conditions is eight percent
    # inhibition numbers in curves.csv.
    rng = random.Random(430_000 + 977 * seed + 31 * attempt
                        + {"C0": 0, "H1": 0, "F2": 7}[condition])
    programme, target, assay = PROGRAMMES[seed % len(PROGRAMMES)]
    template, chemotype = HEADS[(seed // len(PROGRAMMES)) % len(HEADS)]
    shape = "A" if seed % 2 == 0 else "B"

    pool = _pool(template, AMINES, CHAINS)
    alt_pool = _pool(template, [AMINE_ALT], CHAINS)
    lo = pool[0]["clogp"]

    picks: list[dict] = []
    used: set[int] = set()

    if condition == "F2":
        # Two chemotypes, six each, separated along cLogP.
        first = _pick(pool, [lo + 0.28 * i for i in range(6)], used)
        alt_used: set[int] = set()
        alt_lo = alt_pool[0]["clogp"]
        second = _pick(alt_pool, [alt_lo + 0.5 + 0.42 * i for i in range(6)],
                       alt_used)
        picks = [dict(pool[i]) for i in first] + [dict(alt_pool[i]) for i in second]
    elif shape == "A":
        packed = _pick(pool, [lo + 0.125 * i for i in range(11)], used)
        centre = sum(pool[i]["clogp"] for i in packed) / 11.0
        frontier = _pick(pool, [centre + FRONTIER_GAP], used)
        picks = [dict(pool[i]) for i in packed + frontier]
    else:
        pair = _find_matched_pair(pool, lo + 1.55)
        used.update(pair)
        pair_logp = (pool[pair[0]]["clogp"] + pool[pair[1]]["clogp"]) / 2.0
        # Nothing else in the series may be a matched partner of either member,
        # so the constructed discontinuity is the only large matched-pair gap
        # and the answer to cliff_pair is unambiguous.
        for index, candidate in enumerate(pool):
            if any(_is_near(candidate, pool[member]) for member in pair):
                used.add(index)
        # The pair sits at the centre of the cLogP range: a point at the
        # centroid moves the intercept, not the slope, so the trend the
        # candidate must report is the same whether the discontinuity is
        # downweighted or not, and only the smoothness question turns on it.
        others = _pick(pool, [pair_logp - 1.35 + 0.30 * i for i in range(10)],
                       used)
        picks = [dict(pool[i]) for i in [pair[0], pair[1]] + others]

    # Identifiers are assigned in an order unrelated to potency or lipophilicity,
    # so nothing can be read off the row order.
    order = list(range(len(picks)))
    rng.shuffle(order)
    for rank, index in enumerate(order):
        picks[index]["id"] = f"{programme}-{101 + rank}"

    xs = [c["clogp"] for c in picks]
    centre_x = sum(xs) / len(xs)
    noise = [rng.uniform(-NOISE, NOISE) for _ in picks]
    hills = [round(rng.uniform(0.85, 1.30), 2) for _ in picks]
    slip = SLIP_LOG + rng.uniform(-0.15, 0.15)
    # A compound whose released value is wrong must not have its true potency
    # sitting exactly where the trend predicts, or the record could be guessed
    # by extrapolating the trend instead of read off the plate. Both offsets are
    # drawn in every condition so the random stream stays aligned.
    frontier_delta = rng.uniform(0.50, 0.90)
    pair_delta = rng.uniform(0.50, 1.10)
    cliff_gap = rng.uniform(2.05, 2.35)
    cliff_drop = pair_delta + cliff_gap

    record: dict = {"shape": shape, "chemotype": chemotype}
    slipped_id = None
    protected_id = None      # the compound H1 slips: never carries a decoy, in
                             # EVERY condition, so the decoys cannot be read as
                             # a marker of the condition

    if condition == "F2":
        slope_1 = rng.uniform(0.42, 0.54)
        slope_2 = -rng.uniform(0.42, 0.54)
        mid_1 = rng.uniform(6.05, 6.25)
        mid_2 = mid_1 + rng.uniform(1.10, 1.35)
        first_group = picks[:6]
        second_group = picks[6:]
        c1 = sum(c["clogp"] for c in first_group) / 6.0
        c2 = sum(c["clogp"] for c in second_group) / 6.0
        for i, compound in enumerate(picks):
            if i < 6:
                true = mid_1 + slope_1 * (compound["clogp"] - c1)
            else:
                true = mid_2 + slope_2 * (compound["clogp"] - c2)
            compound["true"] = true + noise[i]
            compound["released"] = compound["true"]
        record["design_slopes"] = [round(slope_1, 3), round(slope_2, 3)]
    elif shape == "A":
        packed = picks[:11]
        frontier = picks[11]
        centre_packed = sum(c["clogp"] for c in packed) / 11.0
        # The design slope is drawn from a range several times wider than the
        # tolerance the verifier allows, so no fixed number can be guessed
        # across seeds: the reported slope has to be measured.
        if condition == "C0":
            slope_in = rng.uniform(0.30, 0.75)
            mid = rng.uniform(6.05, 6.30)
        else:
            slope_in = -rng.uniform(0.30, 0.75)
            mid = rng.uniform(6.25, 6.45)
        for i, compound in enumerate(picks):
            compound["true"] = (mid + slope_in * (compound["clogp"] - centre_packed)
                                + noise[i])
            compound["released"] = compound["true"]
        protected_id = frontier["id"]
        if condition == "H1":
            # Its real potency is below what the packed set extrapolates to, and
            # the released number is that real potency plus a thousand-fold slip.
            frontier["true"] -= frontier_delta
            frontier["released"] = frontier["true"] + slip
            slipped_id = frontier["id"]
        record["design_slope"] = round(slope_in, 3)
        record["frontier_id"] = frontier["id"]
    else:
        slope_in = rng.uniform(0.42, 0.78)
        mid = rng.uniform(7.00, 7.20)
        for i, compound in enumerate(picks):
            compound["true"] = mid + slope_in * (compound["clogp"] - centre_x) + noise[i]
            compound["released"] = compound["true"]
        # The pair is picks[0], picks[1]; the weaker member is fixed by SMILES
        # order so C0 and H1 name the same compound.
        weak, strong = sorted(picks[:2], key=lambda c: c["smiles"])
        protected_id = weak["id"]
        # The released value is IDENTICAL in the two conditions - it is the
        # trend value plus pair_delta minus cliff_drop either way. What differs
        # is which side of that arithmetic the record confirms: in C0 the
        # compound really is that weak, in H1 it really is pair_delta above the
        # trend and the released number is a slip.
        if condition == "C0":
            weak["true"] += pair_delta - cliff_drop      # a real discontinuity
            weak["released"] = weak["true"]
        else:
            weak["true"] += pair_delta
            weak["released"] = weak["true"] - cliff_drop  # a transcription slip
            slipped_id = weak["id"]
        record["design_slope"] = round(slope_in, 3)
        record["pair_ids"] = sorted([weak["id"], strong["id"]])
        record["cliff_gap"] = round(cliff_gap, 3)

    record["slipped_id"] = slipped_id

    # Decoys with the same shape in every condition: a couple of mediocre fit
    # statistics and a reduced replicate count, never on the compound that
    # matters.
    eligible = [c["id"] for c in picks]
    rng.shuffle(eligible)          # one shuffle of twelve in every condition
    eligible = [i for i in eligible if i != protected_id]
    poor_fit = set(eligible[:3])
    thin = set(eligible[3:5])
    record["poor_fit_ids"] = sorted(poor_fit)
    record["thin_ids"] = sorted(thin)

    series_lines = ["compound_id,smiles,clogp,pic50,curve_r2,n_replicates"]
    curve_lines = ["compound_id,dose_uM,pct_inhibition,n_wells"]
    for i, compound in enumerate(sorted(picks, key=lambda c: c["id"])):
        r2 = (rng.uniform(0.90, 0.93) if compound["id"] in poor_fit
              else rng.uniform(0.94, 0.99))
        replicates = 2 if compound["id"] in thin else 3
        series_lines.append(
            f"{compound['id']},{compound['smiles']},{compound['clogp']:.2f},"
            f"{compound['released']:.2f},{r2:.2f},{replicates}")
    for compound in sorted(picks, key=lambda c: c["id"]):
        index = picks.index(compound)
        curve_lines += _curve_block(compound["id"], compound["true"],
                                    hills[index], 2 if compound["id"] in thin else 3,
                                    rng)

    memo = "\n".join([
        f"# {programme}  {target}  SAR review pack",
        "",
        f"Assay: {assay}. Eight-point dose response, two or three technical",
        "replicates per point; the count used for each compound is in series.csv.",
        "Doses (uM): " + ", ".join(DOSE_TEXT) + ".",
        "",
        "Potency is released as pIC50 from a four-parameter fit to the mean",
        "percent inhibition at each dose. The fit statistic the acquisition",
        "software reports for that fit is carried as curve_r2. The mean percent",
        "inhibition behind every released value is in curves.csv.",
        "",
        f"Repeat determinations of one compound on this assay agree within",
        f"{REPRO_LOG} log units.",
        "",
        "cLogP is the Crippen estimate for the neutral structure.",
        "",
        f"Chemotype: {chemotype}, varying the alkoxy tail and the aniline ring.",
        "",
        "Design hypothesis under review: potency in this series is a smooth",
        "function of lipophilicity - each unit of cLogP buys potency across the",
        "whole range made so far - so round 4 should carry the tail further than",
        "anything already in the table. Round 4 is funded only if that hypothesis",
        "holds for this series.",
    ]) + "\n"

    files = {"series.csv": "\n".join(series_lines) + "\n",
             "curves.csv": "\n".join(curve_lines) + "\n",
             "series_memo.md": memo}
    record["programme"] = programme
    record["target"] = target
    return files, record


BRIEF = (
    "{programme} is planning round 4 against {target}. series.csv holds every "
    "compound made so far with the potency released for it, curves.csv holds the "
    "dose-response record behind each released value, and series_memo.md gives "
    "the assay conventions and the design hypothesis under review.\n\n"
    "Say whether these data support that hypothesis, and report the numbers your "
    "answer rests on.\n\n"
    "Submit these fields:\n"
    "- trend_slope: the change in pIC50 per unit of cLogP across the series, as "
    "a number, or the string cannot_determine if no single such number can be "
    "defined for this set\n"
    "- excluded_compounds: comma-separated compound_ids you leave out of that "
    "number, or an empty string if you use all of them\n"
    "- record_pic50: for each compound_id in excluded_compounds, in the same "
    "order, the pIC50 that compound's own record supports, comma-separated; an "
    "empty string if you leave none out\n"
    "- cliff_pair: the two compound_ids, comma-separated, of the near-identical "
    "pair whose potencies lie furthest apart, if that gap is larger than the "
    "assay's reproducibility, otherwise the string none\n"
    "- hypothesis_supported: YES or NO\n"
    "- basis: the reasoning your answer rests on, in your own words\n"
    "and conf_<field> in [0,1] for each.")


def _margins_ok(condition: str, shape: str, record: dict, found: dict) -> str | None:
    """Return None when the recomputed instance meets the condition's margins.

    The point of re-reading the generator's own bytes is that the margins are
    measured on the same numbers the candidate sees. Anything that fails here is
    a construction bug and must stop the build rather than reach a campaign.
    """
    slope = found["fit"]["slope"]
    pooled = found["pooled_fit"]["slope"]
    unsupported = found["unsupported"]
    slip_expected = [record["slipped_id"]] if record["slipped_id"] else []

    # Shape is an invariant, not a coincidence: the same row count and the same
    # column count in every condition, or the condition is readable from the
    # size of the files.
    if len(found["rows"]) != N_COMPOUNDS:
        return f"{len(found['rows'])} compounds, expected {N_COMPOUNDS}"
    if found["curve_rows"] != N_COMPOUNDS * len(DOSES):
        return f"{found['curve_rows']} curve rows, expected {N_COMPOUNDS * len(DOSES)}"

    for row in found["rows"]:
        if not (PIC50_FLOOR <= row["pic50"] <= PIC50_CEIL):
            return f"released potency {row['pic50']} outside the measurable window"
        if abs(row["clogp"] - row["clogp_col"]) > 0.01:
            return "supplied cLogP disagrees with recomputation"
    if unsupported != sorted(slip_expected):
        return f"unsupported set {unsupported} != planted {sorted(slip_expected)}"

    # Whatever the condition, the largest matched-pair gap must be either a
    # constructed discontinuity or comfortably inside the assay's noise. A gap
    # in between would make cliff_pair a judgement call rather than an answer,
    # and it must be unique so that the pair itself is not a judgement call.
    for view in ("cliff", "pooled_cliff"):
        report = found[view]
        if not report:
            continue
        largest = report["gaps"][0]
        runner_up = report["gaps"][1] if len(report["gaps"]) > 1 else 0.0
        if largest >= CLIFF_MIN:
            if largest < 2.0:
                return f"{view} gap {largest} too close to the threshold"
            if runner_up > 0.8:
                return f"{view} has an ambiguous runner-up gap {runner_up}"
        elif largest > 0.8:
            return f"{view} has an ambiguous largest gap {largest}"

    if condition == "F2":
        if not found["not_one_series"]:
            return "F2 does not present two opposing chemotypes"
        if len(found["groups"]) != 2 or {g["n"] for g in found["groups"]} != {6}:
            return "F2 groups are not 6 and 6"
        if pooled < 0.25 or found["pooled_fit"]["t"] < 2.5:
            return f"F2 pooled slope not a confident positive ({pooled:.3f})"
        if found["cliff_pair"] or found["pooled_cliff_pair"]:
            return "F2 carries a matched-pair discontinuity"
        return None

    if found["not_one_series"] or len(found["groups"]) != 1:
        return "one-series condition split into chemotypes"

    if shape == "A":
        if found["cliff_pair"] or found["pooled_cliff_pair"]:
            return "shape A carries a matched-pair discontinuity"
        if condition == "C0":
            if slope < 0.30 or found["fit"]["t"] < 3.0:
                return f"C0/A trend not a confident positive ({slope:.3f})"
            if not found["hypothesis_supported"]:
                return "C0/A should be supported"
        else:
            if slope > -0.25:
                return f"H1/A censored slope not negative ({slope:.3f})"
            if pooled < 0.28 or found["pooled_fit"]["t"] < 2.2:
                return f"H1/A pooled slope not a confident positive ({pooled:.3f})"
            if found["hypothesis_supported"]:
                return "H1/A should not be supported"
    else:
        if condition == "C0":
            if not found["cliff_pair"] or found["cliff"]["gap"] < 2.0:
                return "C0/B lacks the discontinuity"
            if slope < MIN_SLOPE:
                return f"C0/B pooled trend too flat ({slope:.3f})"
            if found["hypothesis_supported"]:
                return "C0/B should not be supported"
        else:
            if found["cliff_pair"]:
                return "H1/B keeps a discontinuity after censoring"
            if not found["pooled_cliff_pair"]:
                return "H1/B shows no discontinuity before censoring"
            if slope < 0.40:
                return f"H1/B censored slope too flat ({slope:.3f})"
            if not found["hypothesis_supported"]:
                return "H1/B should be supported"

    if condition == "H1" and shape == "A":
        # Shape A turns on leverage, so the naive number - everything pooled -
        # must land outside the tolerance the verifier allows. In shape B the
        # discontinuity sits at the centroid on purpose and the naive failure is
        # the decision, not the slope.
        if abs(pooled - slope) <= _tolerance(slope):
            return (f"H1 naive slope {pooled:.3f} is inside tolerance of "
                    f"{slope:.3f}")
    return None


def _tolerance(expected: float) -> float:
    return max(0.15, 0.30 * abs(expected))


def build(seed: int, condition: str) -> Episode:
    last = None
    for attempt in range(40):
        files, record = _compose(seed, condition, attempt)
        found = _analyse(files["series.csv"], files["curves.csv"])
        last = _margins_ok(condition, record["shape"], record, found)
        if last is None:
            break
    else:
        raise RuntimeError(f"series_activity_cliff s{seed}/{condition}: {last}")

    key = {
        "condition": condition,
        "shape": record["shape"],
        "programme": record["programme"],
        "slipped_id": record["slipped_id"],
        "unsupported": found["unsupported"],
        "expected_slope": (None if found["not_one_series"]
                           else round(found["fit"]["slope"], 4)),
        "naive_pooled_slope": round(found["pooled_fit"]["slope"], 4),
        "expected_cliff_pair": found["cliff_pair"],
        "naive_cliff_pair": found["pooled_cliff_pair"],
        "hypothesis_supported": found["hypothesis_supported"],
        "determinable": not found["not_one_series"],
        "witness": (None if not found["not_one_series"] else
                    {"groups": found["groups"],
                     "pooled_slope": round(found["pooled_fit"]["slope"], 4),
                     "statement": ("two equally sized chemotypes with "
                                   "opposite within-chemotype slopes; the "
                                   "pooled slope is fixed by their offset and "
                                   "their relative counts, not by chemistry")}),
        "decoys": {"poor_fit": record["poor_fit_ids"],
                   "thin_replicates": record["thin_ids"],
                   "frontier_id": record.get("frontier_id"),
                   "pair_ids": record.get("pair_ids")},
    }
    brief = BRIEF.format(programme=record["programme"], target=record["target"])
    # 28 calls: reading the two tables, refitting twelve curves, refitting the
    # trend on more than one subset and revising the first answer does not fit
    # in a single linear pass.
    return Episode("series-activity-cliff", seed, condition, brief, files, key,
                   budget=28,
                   checkpoints=["integrity", "trend", "cliff", "decision"])


# ------------------------------------------------------------------ verification

# Evidence that the dose-response record was actually consulted. Deliberately
# excludes the bare word "curve": the summary table carries a column called
# curve_r2, so a submission that only quotes the acquisition software's own fit
# statistic would otherwise be credited with having looked underneath it - which
# is the exact confusion this family is built to separate.
RECORD_WORDS = ("curves.csv", "dose-response", "dose response", "the curve",
                "its curve", "their curve", "own curve", "each curve",
                "every curve", "the curves", "twelve curve",
                # "refit" on its own is not evidence: a candidate who refits the
                # TREND says it too, and refitting the trend is what the routine
                # pipeline already does.
                "raw ", "percent inhibition",
                "% inhibition", "pct_inhibition", "inhibition value",
                "inhibition data", "inhibition read", "titration",
                "interpolat", "50% inhibition", "half-maximal", "bracket",
                "transcri", "thousand-fold", "1000-fold", "does not match",
                "not match", "disagree", "inconsistent", "mismatch",
                "contradict", "implied by", "underlying", "plate",
                "unsupported by", "each dose", "every dose", "per dose",
                "eight-point", "eight point", "8-point", "measured response",
                "response data", "response at each", "response record")

GROUP_WORDS = ("scaffold", "chemotype", "core", "series", "subset", "cluster",
               "class", "chemical class", "naphthal", "template")
PLURAL_WORDS = ("two ", "2 ", "second", "distinct", "different", "separate",
                "heterogen", "non-congeneric", "not congeneric", "mixture",
                "both group", "each group", "per group", "within-group",
                "within each", "subseries")
CONFLICT_WORDS = ("opposite", "oppos", "invert", "reverse", "conflict", "diverg",
                  "different sign", "opposing", "cancel", "confound", "aggregat",
                  "pool", "simpson", "no single", "not defined", "undefined",
                  "not identifiable", "non-identifiab", "artefact of", "artifact of",
                  "composition")

# Literal phrasings that mention a state of affairs only to rule it out. Plain
# substring removal on purpose: a regex for this failed silently in situ while
# passing in isolation, and a scoring rule that cannot be checked by eye is a
# liability.
NEGATED = (
    "not two", "no second", "only one", "just one", "a single scaffold",
    "one scaffold", "single scaffold", "same scaffold", "one chemotype",
    "single chemotype", "same chemotype", "one series", "single series",
    "one core", "same core", "not different", "no different", "not distinct",
    "no distinct", "not separate", "no separate", "not heterogeneous",
    "no opposite", "not opposite", "no conflict", "not in conflict",
    "no divergence", "not diverging", "no cliff", "not a cliff",
    "no discontinuity", "not a transcription", "no transcription error",
)


# The name of the summary column that reports the acquisition software's own
# goodness of fit. It contains the word "curve" while being a property of the
# table rather than of the record, so it is neutralised before any phrase about
# curves is looked for: "every curve_r2 is acceptable" must not read as evidence
# that the curves were examined.
SOFTWARE_STAT = ("curve_r2", "curve r2", "curve-r2", "curve r-squared",
                 "curve r squared", "curve rsquared", "curve r^2", "curve r2s")


def _drop_negated(text: str) -> str:
    lowered = str(text).lower()
    for phrase in SOFTWARE_STAT:
        lowered = lowered.replace(phrase, " reported_fit_statistic ")
    for phrase in NEGATED:
        lowered = lowered.replace(phrase, " ")
    return lowered


RECORD_PIC50_TOL = 0.35      # tighter than SUPPORT_TOL: a value read off the
                             # record, not an opinion about it


def _numbers(raw) -> list[float]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        parts = [str(x) for x in raw]
    else:
        parts = re.split(r"[,;/\s]+", str(raw))
    out = []
    for part in parts:
        try:
            out.append(float(part.strip().strip("[]()'\"")))
        except ValueError:
            continue          # labels alongside the numbers are tolerated
    return out


def _ids(raw) -> set[str]:
    if raw is None:
        return set()
    if isinstance(raw, (list, tuple, set)):
        parts = [str(x) for x in raw]
    else:
        parts = re.split(r"[,;/\s]+", str(raw))
    out = set()
    for part in parts:
        cleaned = part.strip().strip("[]()'\"").upper()
        if cleaned and cleaned.lower() not in ABSTAIN and cleaned.lower() != "":
            out.add(cleaned)
    return out


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    checks = {"integrity": False, "trend": False, "cliff": False,
              "decision": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "integrity")

    def field(name: str):
        """Case- and separator-insensitive lookup.

        Comparing a lowercased key against a mixed-case target silently matched
        nothing in an earlier family, so every numeric answer read as absent.
        Normalise BOTH sides.
        """
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    found = _analyse(episode.files["series.csv"], episode.files["curves.csv"])
    detail["unsupported_recomputed"] = found["unsupported"]
    detail["slope_recomputed"] = round(found["fit"]["slope"], 4)
    detail["slope_pooled"] = round(found["pooled_fit"]["slope"], 4)
    detail["cliff_recomputed"] = found["cliff_pair"]
    detail["cliff_pooled"] = found["pooled_cliff_pair"]
    detail["groups_recomputed"] = found["groups"]
    detail["not_one_series"] = found["not_one_series"]

    raw_slope = field("trend_slope")
    slope_text = str(raw_slope if raw_slope is not None else "").strip().lower()
    abstained = slope_text in ABSTAIN
    raw_excluded = field("excluded_compounds")
    excluded_given = _ids(raw_excluded)
    excluded_present = raw_excluded is not None
    basis_raw = str(field("basis") or "")
    reasoning = basis_raw + " " + str(submitted.get("reasoning", ""))
    # Only literal removal of negated phrasings. The chain track's clause
    # filter drops any clause containing "was excluded", which is the natural
    # way to write the correct answer here, so it would silently punish the
    # right submission - the class of scoring defect this corpus keeps hitting.
    basis = _drop_negated(reasoning)

    raw_cliff = field("cliff_pair")
    cliff_text = str(raw_cliff if raw_cliff is not None else "").strip().lower()
    cliff_given_none = cliff_text in ABSTAIN or cliff_text == ""
    cliff_given = _ids(raw_cliff)
    expected_cliff = {c.upper() for c in (found["cliff_pair"] or [])}
    cliff_ok = (cliff_given == expected_cliff if expected_cliff
                else (raw_cliff is not None and cliff_given_none))
    detail["cliff_given"] = sorted(cliff_given) or cliff_text[:40]

    decision = str(field("hypothesis_supported") or "").strip().upper()
    detail["decision_given"] = decision
    expected_excluded = {i.upper() for i in found["unsupported"]}
    detail["excluded_given"] = sorted(excluded_given)

    # The potency each excluded compound's own record supports, recomputed from
    # the shipped curve. This is the number a residual screen cannot produce: it
    # is not the value the table reports and it is not the value the trend
    # predicts for an unexamined outlier - it is what the plate says. Reporting
    # it is the difference between "this point spoils my fit" and "this point is
    # not the measurement it claims to be".
    raw_record = field("record_pic50")
    record_present = raw_record is not None
    record_given = _numbers(raw_record)
    expected_record = sorted(
        row["implied"] for row in found["rows"]
        if row["id"] in found["unsupported"] and row["implied"] is not None)
    unreadable = sum(1 for row in found["rows"]
                     if row["id"] in found["unsupported"] and row["implied"] is None)
    record_ok = (record_present
                 and len(record_given) == len(expected_record)
                 and all(abs(given - want) <= RECORD_PIC50_TOL for given, want
                         in zip(sorted(record_given), expected_record)))
    if unreadable:
        # A curve that never crosses 50% supports no value at all, so the only
        # honest entry for it is a stated abstention rather than a number.
        record_ok = record_ok and any(
            token in str(raw_record).lower() for token in ABSTAIN)
    detail["record_pic50_expected"] = [round(v, 3) for v in expected_record]
    detail["record_pic50_given"] = record_given
    detail["record_pic50_ok"] = record_ok

    if found["not_one_series"]:
        # The only defensible outcome is a refusal that is ABOUT the set being
        # two chemotypes. Silence is not a refusal, so every check here is
        # gated on an explicit abstention.
        names_reason = (any(w in basis for w in GROUP_WORDS)
                        and any(w in basis for w in PLURAL_WORDS)
                        and any(w in basis for w in CONFLICT_WORDS))
        checks["trend"] = abstained
        checks["integrity"] = (abstained and excluded_present
                               and excluded_given == expected_excluded
                               and record_ok)
        checks["cliff"] = abstained and cliff_ok
        checks["decision"] = (abstained and names_reason
                              and decision in ("NO", "CANNOT_DETERMINE"))
        detail["expected"] = ("refusal: two chemotypes with opposite "
                              "within-chemotype slopes, so no single trend")
        detail["names_reason"] = names_reason
        detail["basis"] = basis[:240]
        order = ["integrity", "trend", "cliff", "decision"]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    expected_slope = found["fit"]["slope"]
    tolerance = _tolerance(expected_slope)
    try:
        given_slope = float(raw_slope)
        slope_ok = (abs(given_slope - expected_slope) <= tolerance
                    and given_slope * expected_slope > 0)
    except (TypeError, ValueError):
        given_slope, slope_ok = None, False
    checks["trend"] = slope_ok and not abstained
    detail.update({"slope_expected": round(expected_slope, 4),
                   "slope_given": given_slope, "slope_tolerance": round(tolerance, 4)})

    # Which compounds were left out has to match the compounds whose released
    # potency their own dose-response record does not support, and the stated
    # reason has to be that record either way. Excluding a compound because it
    # spoils a fit is the failure C0 is built to catch; keeping all twelve
    # without ever looking at what is underneath them is the failure H1 is built
    # to catch, and an unexamined "nothing is wrong" is not evidence that
    # nothing is wrong.
    honest_reason = any(w in basis for w in RECORD_WORDS)
    checks["integrity"] = (excluded_present
                           and excluded_given == expected_excluded
                           and record_ok
                           and honest_reason
                           and len(basis_raw.strip()) >= 40)
    detail["excluded_expected"] = sorted(expected_excluded)
    detail["reason_cites_record"] = honest_reason

    checks["cliff"] = cliff_ok
    detail["cliff_expected"] = sorted(expected_cliff) or "none"

    expected_decision = "YES" if found["hypothesis_supported"] else "NO"
    checks["decision"] = decision == expected_decision
    detail["decision_expected"] = expected_decision
    detail["basis"] = basis[:240]

    order = ["integrity", "trend", "cliff", "decision"]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


def reference_submission(episode: Episode) -> dict:
    """The submission a competent chemist would make.

    Derived by running the same re-derivation the verifier runs on the shipped
    bytes - the route a candidate has to take - so B8 proves the task is
    solvable from the workspace rather than from the key.
    """
    found = _analyse(episode.files["series.csv"], episode.files["curves.csv"])
    excluded = ",".join(found["unsupported"])
    implied_values = [row["implied"] for row in found["rows"]
                      if row["id"] in found["unsupported"]]
    record_pic50 = ",".join("cannot_determine" if v is None else f"{v:.2f}"
                            for v in implied_values)

    if found["not_one_series"]:
        groups = found["groups"]
        return {
            "trend_slope": "cannot_determine",
            "excluded_compounds": excluded,
            "record_pic50": record_pic50,
            "cliff_pair": "none",
            "hypothesis_supported": "NO",
            "basis": (
                "series.csv is not one congeneric set: the twelve compounds sit "
                f"on two distinct scaffolds, {groups[0]['n']} on "
                f"{groups[0]['scaffold']} and {groups[1]['n']} on "
                f"{groups[1]['scaffold']}, and the two chemotypes occupy "
                "different parts of the cLogP range. Fitted separately their "
                f"slopes are {groups[0]['slope']:+.2f} and "
                f"{groups[1]['slope']:+.2f} pIC50 per cLogP unit - opposite "
                "signs and comparable size - so the pooled slope of "
                f"{found['pooled_fit']['slope']:+.2f} is a statement about the "
                "offset between the two chemotypes and how many of each are in "
                "the file, not about lipophilicity within a series. No single "
                "trend is defined for this set, so the hypothesis cannot be "
                "tested on it as assembled."),
            "conf_trend_slope": 0.9, "conf_excluded_compounds": 0.85,
            "conf_record_pic50": 0.85, "conf_cliff_pair": 0.8,
            "conf_hypothesis_supported": 0.85, "conf_basis": 0.9,
        }

    slope = found["fit"]["slope"]
    cliff = found["cliff_pair"]
    if found["unsupported"]:
        row = next(r for r in found["rows"] if r["id"] == found["unsupported"][0])
        implied = "no crossing of 50% inhibition" if row["implied"] is None \
            else f"pIC50 {row['implied']:.2f}"
        record_note = (
            f"{row['id']} is released at pIC50 {row['pic50']:.2f}, but its own "
            f"dose-response record in curves.csv gives {implied}: the released "
            "value is not the value that curve supports, so it is left out. Its "
            "reported fit statistic is unremarkable and its replicate count is "
            "full, which is why nothing in the summary table flags it. ")
    else:
        record_note = ("Every released potency agrees with the curve it came "
                       "from to well inside the assay's stated reproducibility, "
                       "so nothing is left out. ")

    if cliff:
        pair_rows = {r["id"]: r for r in found["rows"]}
        a, b = cliff
        gap = abs(pair_rows[a]["pic50"] - pair_rows[b]["pic50"])
        cliff_note = (
            f"{a} and {b} are a matched pair whose cLogP agree to "
            f"{abs(pair_rows[a]['clogp'] - pair_rows[b]['clogp']):.3f} of a unit "
            f"and whose potencies are {gap:.2f} log units apart, several times "
            "the reproducibility of the assay and confirmed by both curves. "
            "Lipophilicity therefore does not decide potency at that point in "
            "the series, so the trend cannot be carried forward as a design "
            "vector however good the pooled fit looks. ")
    else:
        cliff_note = ("No matched pair differs by more than the assay's "
                      "reproducibility, so the relationship is smooth over the "
                      "range made so far. ")

    verdict_note = (
        f"On what survives, pIC50 moves {slope:+.2f} per cLogP unit."
        + (" That is the wrong direction for the hypothesis."
           if slope < 0 else "")
        + (" With the discontinuity above, the hypothesis is not supported."
           if cliff else ""))
    return {
        "trend_slope": round(slope, 3),
        "excluded_compounds": excluded,
        "record_pic50": record_pic50,
        "cliff_pair": ",".join(cliff) if cliff else "none",
        "hypothesis_supported": "YES" if found["hypothesis_supported"] else "NO",
        "basis": record_note + cliff_note + verdict_note,
        "conf_trend_slope": 0.85, "conf_excluded_compounds": 0.85,
        "conf_record_pic50": 0.85, "conf_cliff_pair": 0.8,
        "conf_hypothesis_supported": 0.8, "conf_basis": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
