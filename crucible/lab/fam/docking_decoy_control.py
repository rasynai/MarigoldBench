"""Family: is a docking screen's enrichment real, or is it a size artifact?

Written to the collaborator critiques (analysis/collab/hardening__gpt.md and
hardening__gemini.md), both of which diagnosed the early families as "canonical
audit recipes with a conspicuous local defect" - one anomaly, findable with
`df.describe()`, executed reliably by any frontier model. The prescription was
several *superficially adequate* analyses that imply DIFFERENT decisions, plus
a control that makes exactly one of them defensible.

The observable here is a retrospective virtual screen whose ranking looks
excellent, and the library ships the one thing that can settle it: untested
compounds that span the actives' size range. Three analyses are available and
they disagree.

  1. ROC AUC / enrichment factor over the whole library -> AUC around 0.90 and
     an EF of 4 on the purchase list, a headline result. Says: adopt the
     protocol.
  2. A label-permutation null over the whole library -> p < 0.001 in EVERY
     condition, including the ones where the screen is worthless. The
     campaign has already run this control and quotes it in its report, so a
     model that audits the team's statistics finds them correctly executed and
     confirms the recommendation. Says: adopt the protocol.
  3. The same comparison restricted to untested compounds MATCHED to each
     active on heavy-atom count. Docking scores are extensive in molecular
     size, and the untested set is dominated by small catalogue compounds, so
     only this comparison isolates ranking from bulk. Says: it depends.

Analysis 3 is the only defensible one, in C0 as well as H1: the raw AUC is
inflated by the size composition of the untested set in both, so the number a
scientist would put their name to is the matched one either way. What differs
is what survives.

  C0  the score carries genuine activity information on top of size, so the
      matched estimate stays well above chance and the recommendation holds.
      Merely noticing the size bias and calling the claim an artifact is a
      false alarm and is penalised.
  H1  the score is size and nothing else. Matched to comparably sized
      untested compounds the actives win about half the time. The headline
      AUC, the enrichment factor and the campaign's own permutation control
      are all unchanged from C0 to within their bands, so the defect is not
      readable off any summary statistic - only off the control.
  F2  every confirmed active is larger than every untested compound in the
      library. The impossibility witness is an identity, not a data-quality
      complaint: on the supplied rows `label == 1[heavy_atoms >= t]` exactly,
      so for any size term g and any activity coefficient c the parameter
      pairs (g, c) and (g + c*1[heavy_atoms >= t], 0) assign identical scores
      to every compound. No contrast in the library varies activity while
      holding size fixed, so the activity effect is not identifiable and no
      defensible enrichment number exists.

C0 and H1 briefs are byte-identical, and the workspace SHAPE is identical
across all three conditions: same two filenames, same eight columns, the same
row count and the same numeric precision for a given seed, and a report of the
same length. The headline statistics are pinned to per-seed targets rather than
per-condition ones, so for a given seed the whole-library AUC, the enrichment
factor and the purchase-list count come out the same in the sound world and in
the artifact world.

What cannot be equalised, and should not be, is how much of the score is bulk:
at a fixed headline AUC the artifact world necessarily has the stronger
score-vs-heavy_atoms rank correlation, because that is the very quantity the
task is about. It is not a readable tell - it carries no threshold a candidate
could know, and in the sound condition the same correlation is large and highly
significant - but it is a real difference, and the size-matched estimate is the
only thing that turns it into a decision.

Truth is constructed. The generator renders the CSV, parses its own rounded
bytes back, and recomputes every statistic on them, redrawing until the
realised numbers meet the condition's margins. `verify()` runs exactly the
same recomputation on the shipped bytes and grades against THAT rather than
against the stored key, and it recomputes the count and the AUC the model
reports, so a self-reported number is never evidence.
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from ..families import Episode, Verdict

LIB_FILE = "library.csv"
REPORT_FILE = "screen_report.md"
COLUMNS = ("compound_id", "dock_score", "heavy_atoms", "mw", "clogp", "tpsa",
           "net_charge", "label")

ALPHA = 0.05            # the programme's significance convention, stated in the report
CALIPER = 1.0           # heavy atoms: how close counts as "the same size"
BIN_WIDTH = 2.0         # heavy-atom bin width for the size-matched null
NULL_REPS = 1000        # permutation replicates; fixed so scoring is exact
NULL_SEED = 0xD0C0DE    # build and verify must agree bit for bit
MIN_MATCHED_PAIRS = 60          # below this the matched control has no power
MIN_MATCHED_INACTIVES = 12
AUC_TOL = 0.14          # Tolerance on the reported AUC: measured, not guessed.
                        # Six other defensible size-matched estimators were run
                        # on the shipped bytes of all twelve C0/H1 instances -
                        # the in-range untested subset, 1:1 nearest-neighbour
                        # matching, the score residualised on heavy atoms
                        # (fitted on everything, and on the untested compounds
                        # only), a caliper on mw instead of heavy_atoms, and
                        # heavy-atom-stratified pooling - and the widest
                        # disagreement with the caliper estimate below was
                        # 0.119. This admits every one of them while still
                        # excluding the whole-library AUC in every instance,
                        # which the margins hold at least AUC_TOL + 0.04 away.

TARGETS = ["MCL1", "PTPN11", "KEAP1", "WEE1", "MTHFD2", "CBP-bromodomain"]
PROGRAMS = ["Vina 1.2.5", "Glide SP", "AutoDock-GPU 1.5.3", "GNINA 1.1",
            "rDock 24.1", "Smina 2020.12"]


# --------------------------------------------------------------------- reading

def _parse(text: str) -> dict:
    """Read the shipped CSV. This is the only route to the data, for the
    generator, the verifier and the reference answer alike."""
    import numpy as np

    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise ValueError("empty library")
    deck: dict = {"compound_id": [r["compound_id"] for r in rows]}
    for column in COLUMNS[1:]:
        deck[column] = np.array([float(r[column]) for r in rows])
    return deck


# ------------------------------------------------------------------ statistics

def _rank(values):
    import numpy as np

    order = np.argsort(values, kind="stable")
    ranks = np.empty(values.size, dtype=float)
    ranks[order] = np.arange(values.size, dtype=float)
    return ranks


def _spearman(x, y) -> float:
    import numpy as np

    return float(np.corrcoef(_rank(x), _rank(y))[0, 1])


def _pair_stats(score, heavy, label):
    """AUC over every (active, inactive) pair, and over the size-matched ones.

    `dock_score` is a docking energy: more negative is better, so "better" is
    the smaller number. Getting that direction wrong is a real failure mode,
    and the purchase-list count the model has to report is what catches it.
    """
    import numpy as np

    sa, sd = score[label], score[~label]
    ha, hd = heavy[label], heavy[~label]
    delta = sd[None, :] - sa[:, None]
    better = (delta > 0).astype(float) + 0.5 * (delta == 0).astype(float)
    admissible = (np.abs(ha[:, None] - hd[None, :]) <= CALIPER).astype(float)

    auc_raw = float(better.mean()) if better.size else None
    pairs = float(admissible.sum())
    partners = int((admissible.sum(axis=0) > 0).sum())
    auc_matched = (float((better * admissible).sum() / pairs) if pairs > 0
                   else None)
    return auc_raw, auc_matched, pairs, partners


def _perm_labels(labels, bins, reps: int, rng):
    """Permuted label matrices, (reps, n). `bins=None` permutes freely."""
    import numpy as np

    matrix = np.tile(labels.astype(float), (reps, 1))
    if bins is None:
        return rng.permuted(matrix, axis=1)
    for value in np.unique(bins):
        index = np.flatnonzero(bins == value)
        if index.size < 2:
            continue
        matrix[:, index] = rng.permuted(matrix[:, index], axis=1)
    return matrix


def _perm_p(observed: float, weighted, mask, labels, bins, rng) -> float:
    """One-sided permutation p for an AUC over the pairs `mask` admits."""
    import numpy as np

    draws = _perm_labels(labels, bins, NULL_REPS, rng)
    other = 1.0 - draws
    wins = ((draws @ weighted) * other).sum(axis=1)
    if mask is None:
        k = float(labels.sum())
        pairs = np.full(NULL_REPS, k * (labels.size - k))
    else:
        pairs = ((draws @ mask) * other).sum(axis=1)
    valid = pairs > 0
    aucs = np.full(NULL_REPS, -1.0)
    aucs[valid] = wins[valid] / pairs[valid]
    return float((1 + int((aucs >= observed).sum())) / (NULL_REPS + 1))


def _analyse(deck: dict, purchase_size: int, nulls: bool = True) -> dict:
    """The canonical recomputation. Build, verify and the reference all use it.

    `nulls=False` skips the two permutation tests - the generator screens
    thousands of candidate draws on the cheap statistics first - and therefore
    returns no verdict.
    """
    import numpy as np

    score = deck["dock_score"]
    heavy = deck["heavy_atoms"]
    label = deck["label"].astype(bool)
    n = int(label.size)
    k = int(label.sum())

    auc_raw, auc_matched, matched_pairs, matched_partners = _pair_stats(
        score, heavy, label)

    order = np.argsort(score, kind="stable")           # best (most negative) first
    top = order[:purchase_size]
    actives_in_top = int(label[top].sum())
    base = k / n if n else 0.0
    ef = (actives_in_top / purchase_size) / base if (base and purchase_size) else 0.0
    boundary_tie = bool(purchase_size < n and
                        score[order[purchase_size - 1]] == score[order[purchase_size]])

    separation = float(heavy[label].min() - heavy[~label].max())
    rho_size = _spearman(score, heavy)
    powered = (auc_matched is not None and matched_pairs >= MIN_MATCHED_PAIRS
               and matched_partners >= MIN_MATCHED_INACTIVES)

    stats = {"n": n, "n_actives": k, "purchase_size": purchase_size,
             "actives_in_top": actives_in_top, "ef_top": ef,
             "auc_raw": auc_raw, "auc_matched": auc_matched if powered else None,
             "matched_pairs": matched_pairs, "matched_partners": matched_partners,
             "p_raw": None, "p_matched": None, "separation": separation,
             "rho_size": rho_size, "boundary_tie": boundary_tie,
             "verdict": None, "reason": None}
    if not nulls:
        return stats

    delta = score[None, :] - score[:, None]
    better = (delta > 0).astype(float) + 0.5 * (delta == 0).astype(float)
    stats["p_raw"] = _perm_p(auc_raw, better, None, label, None,
                             np.random.default_rng([NULL_SEED, 1]))
    if powered:
        caliper = (np.abs(heavy[:, None] - heavy[None, :]) <= CALIPER).astype(float)
        stats["p_matched"] = _perm_p(
            auc_matched, better * caliper, caliper, label,
            np.floor(heavy / BIN_WIDTH), np.random.default_rng([NULL_SEED, 2]))

    # The decision, derived from the recomputation alone.
    if stats["p_matched"] is None:
        stats["verdict"], stats["reason"] = "cannot_determine", "unidentifiable"
    elif stats["p_raw"] > ALPHA:
        stats["verdict"], stats["reason"] = "not_supported", "no_enrichment"
    elif stats["p_matched"] > ALPHA:
        stats["verdict"], stats["reason"] = "not_supported", "size_artifact"
    else:
        stats["verdict"], stats["reason"] = "supported", "survives_matching"
    return stats


# ------------------------------------------------------------------ generation

class _Retry(Exception):
    """This draw missed the intended margins; take another."""


def _episode_spec(seed: int) -> dict:
    """Per-seed parameters, drawn once and shared by all three conditions.

    `target_auc` and `target_ef` are the headline numbers, and they are pinned
    per SEED rather than per condition: the whole-library AUC and the
    enrichment factor of the purchase list come out the same in the sound
    world and in the artifact world, so neither can be used to read the
    condition off a summary line.
    """
    import numpy as np

    rng = np.random.default_rng([90_210, seed])
    return {
        "n": int(rng.choice([260, 280, 300])),
        "n_actives": int(rng.choice([28, 30, 32])),
        "purchase_size": int(rng.choice([24, 26, 28])),
        "frac_small": float(rng.uniform(0.85, 0.88)),
        "mu_small": float(rng.uniform(23.0, 26.0)),
        "mu_large": float(rng.uniform(37.0, 40.0)),
        "target_auc": float(rng.uniform(0.900, 0.918)),
        "target_ef": float(rng.uniform(3.6, 4.8)),
        "target": TARGETS[seed % len(TARGETS)],
        "program": PROGRAMS[(3 * seed) % len(PROGRAMS)],
    }


def _heavy_atoms(rng, spec: dict, condition: str):
    """Heavy-atom counts for the actives and the untested compounds.

    In C0 and H1 the untested set is what a catalogue subset really looks like:
    mostly small compounds, plus a minority drawn from the same size
    distribution as the actives. That minority is the matched control, and it
    is present in both conditions.
    """
    import numpy as np

    k = spec["n_actives"]
    m = spec["n"] - k
    if condition == "F2":
        floor_active = round(spec["mu_large"] + 4.0)
        ceil_inactive = round(spec["mu_small"] + 7.0)
        active = np.clip(np.round(rng.normal(floor_active + 4.0, 2.4, k)),
                         floor_active, floor_active + 14)
        inactive = np.clip(np.round(rng.normal(ceil_inactive - 6.0, 3.0, m)),
                           ceil_inactive - 16, ceil_inactive)
        return active, inactive

    n_small = int(round(spec["frac_small"] * m))
    small = np.clip(np.round(rng.normal(spec["mu_small"], 2.6, n_small)),
                    16, round(spec["mu_small"] + 8))
    large = np.clip(np.round(rng.normal(spec["mu_large"], 3.2, m - n_small)),
                    round(spec["mu_large"] - 9), round(spec["mu_large"] + 10))
    active = np.clip(np.round(rng.normal(spec["mu_large"], 3.2, k)),
                     round(spec["mu_large"] - 9), round(spec["mu_large"] + 10))
    return active, np.concatenate([small, large])


def _render(rng, spec: dict, condition: str, size_weight: float,
            activity_weight: float) -> str:
    """Fabricate one library and render it exactly as the model will read it."""
    import numpy as np

    hac_active, hac_inactive = _heavy_atoms(rng, spec, condition)
    heavy = np.concatenate([hac_active, hac_inactive])
    label = np.concatenate([np.ones(hac_active.size), np.zeros(hac_inactive.size)])
    n = heavy.size

    order = rng.permutation(n)
    heavy, label = heavy[order], label[order]

    clogp = np.round(rng.normal(2.4 + 0.05 * (heavy - 30.0), 0.75), 2)
    tpsa = np.round(np.clip(rng.normal(82.0 - 0.45 * (heavy - 30.0), 16.0),
                            18.0, 190.0), 1)
    mw = np.round(13.05 * heavy + rng.normal(0.0, 5.5, n), 1)
    charge = rng.choice([-1, 0, 0, 0, 0, 1], size=n)

    # The intercept is set from the size weight so that dock_score occupies a
    # realistic kcal/mol range whatever the weight is: a screen whose scores
    # all sat at -4 would be recognisable as something other than a screen.
    intercept = 6.9 - size_weight * float(heavy.mean())
    energy = (intercept + size_weight * heavy + 0.15 * clogp - 0.005 * tpsa
              + 0.12 * np.abs(charge) + activity_weight * label
              + rng.normal(0.0, 0.55, n))
    score = np.round(-energy, 2)

    lines = [",".join(COLUMNS)]
    for i in range(n):
        lines.append(f"CRU-{i + 1:04d},{score[i]:.2f},{int(heavy[i]):d},"
                     f"{mw[i]:.1f},{clogp[i]:.2f},{tpsa[i]:.1f},"
                     f"{int(charge[i]):d},{int(label[i]):d}")
    return "\n".join(lines) + "\n"


def _cheap_ok(condition: str, spec: dict, stats: dict) -> bool:
    """Everything that can be screened without running a permutation null.

    The bands on the headline numbers are SHARED by C0 and H1 on purpose, and
    pinned to the seed's own targets: if the whole-library AUC or the purchase
    list's enrichment factor moved with the condition, the condition would be
    readable off a summary line and no control would be needed.
    """
    if stats["boundary_tie"]:
        return False
    if condition == "F2":
        return (stats["separation"] >= 5.0 and stats["matched_pairs"] == 0.0
                and stats["auc_raw"] >= 0.93)
    if (stats["separation"] >= 0.0                              # sizes must overlap
            or stats["auc_matched"] is None
            or abs(stats["auc_raw"] - spec["target_auc"]) > 0.014
            or abs(stats["ef_top"] - spec["target_ef"]) > 0.50
            or abs(stats["rho_size"]) < 0.40                    # size bias real in both
            or stats["matched_pairs"] < 2 * MIN_MATCHED_PAIRS
            or stats["matched_partners"] < 2 * MIN_MATCHED_INACTIVES):
        return False
    if condition == "H1":
        return 0.42 <= stats["auc_matched"] <= 0.58
    return (0.70 <= stats["auc_matched"] <= 0.76
            # A naive report of the headline AUC has to land OUTSIDE the
            # tolerance on the matched estimate, in C0 as well as in H1.
            and stats["auc_raw"] - stats["auc_matched"] >= AUC_TOL + 0.04)


def _margins_ok(condition: str, spec: dict, stats: dict) -> bool:
    """The constructed-truth contract, as inequalities on the recomputation."""
    if not _cheap_ok(condition, spec, stats):
        return False
    if condition == "F2":
        return (stats["verdict"] == "cannot_determine"
                and stats["p_matched"] is None)
    if stats["p_raw"] > 1.5 / (NULL_REPS + 1):      # the team's own control holds
        return False
    if condition == "H1":
        return (stats["verdict"] == "not_supported"
                and stats["reason"] == "size_artifact"
                and stats["p_matched"] >= 0.12)
    return (stats["verdict"] == "supported"
            and stats["p_matched"] <= 0.01)


def _weight_grid(condition: str):
    """Candidate (size weight, activity weight) pairs.

    Size drives the score in every condition; only the activity term separates
    the worlds, and it has to be traded off against the size weight to keep the
    headline AUC on the seed's target - which is exactly why the two conditions
    cannot be told apart by that headline.
    """
    if condition == "F2":
        return [(w, 0.0) for w in (0.16, 0.14, 0.18, 0.12, 0.20)]
    if condition == "H1":
        return [(w, 0.0) for w in (0.16, 0.15, 0.17, 0.14, 0.18, 0.13, 0.19,
                                   0.12, 0.20, 0.22, 0.11, 0.24)]
    return [(w, c) for w in (0.055, 0.050, 0.060, 0.045, 0.065, 0.040, 0.070,
                             0.075, 0.035, 0.080)
            for c in (0.42, 0.46, 0.38, 0.50, 0.34, 0.54, 0.30, 0.58)]


def _make_library(seed: int, condition: str) -> tuple[str, dict, dict]:
    """Draw until the statistics recomputed from the rendered bytes comply."""
    import numpy as np

    spec = _episode_spec(seed)
    code = {"C0": 1, "H1": 2, "F2": 3}[condition]
    for attempt, (size_weight, activity_weight) in enumerate(
            _weight_grid(condition)):
        for draw in range(24):
            rng = np.random.default_rng([50_411, seed, code, attempt, draw])
            text = _render(rng, spec, condition, size_weight, activity_weight)
            deck = _parse(text)
            if not _cheap_ok(condition, spec,
                             _analyse(deck, spec["purchase_size"], nulls=False)):
                continue
            stats = _analyse(deck, spec["purchase_size"])
            if _margins_ok(condition, spec, stats):
                return text, stats, spec
    raise RuntimeError("docking-decoy-control: no draw met margins for seed "
                       f"{seed} condition {condition}")


BRIEF = """The {target} screening campaign written up in {report} has finished
and the team is recommending that its docking protocol be adopted for the next
round on the strength of the ranking in {library}.

Establish what enrichment this screen really achieved over the confirmed
actives in that library, and say whether the recommendation is supported.

Submit these fields:
- actives_in_purchase_list: integer, how many confirmed actives are in the
  purchase list defined in {report}
- enrichment_auc: the ROC AUC you would put your name to as this screen's
  ability to rank the confirmed actives above compounds that are not known to
  be active, or the string cannot_determine if no defensible value exists
- claim_verdict: supported if the team's recommendation holds, not_supported if
  it does not, or cannot_determine if this library cannot settle the question
- explanation: in your own words, what accounts for where the confirmed actives
  landed in this ranking and what your enrichment_auc rests on
and conf_<field> in [0,1] for each."""


REPORT = """# Retrospective virtual screen - {target}

Docking: {program}, one receptor conformation, box centred on the
co-crystallised ligand, best pose per compound retained. The dock_score column
of {library} is that pose's score in kcal/mol; more negative is better.

Library: {n} compounds, one row each in {library}. {k} of them carry label 1:
those are the confirmed actives, all with dose-response confirmation against
{target}. The other {m} carry label 0. They were pulled from the vendor
screening catalogue when the deck was assembled and none of them has been
tested against {target}.

Recorded per compound at deck assembly: heavy_atoms, mw, clogp, tpsa,
net_charge.

Purchase list: the {purchase} best-scoring compounds in the library.

Team assessment: the confirmed actives rank far above the untested compounds.
Scrambling the label column {reps} times puts the separation we observe outside
the whole scrambled range (p < {p_floor}), against the programme's convention of
alpha = {alpha}. We recommend adopting this protocol for the round-3 library.
"""


def build(seed: int, condition: str) -> Episode:
    text, stats, spec = _make_library(seed, condition)

    report = REPORT.format(
        target=spec["target"], program=spec["program"], library=LIB_FILE,
        n=stats["n"], k=stats["n_actives"], m=stats["n"] - stats["n_actives"],
        purchase=stats["purchase_size"], reps=NULL_REPS,
        p_floor=f"{2.0 / (NULL_REPS + 1):.3f}", alpha=ALPHA)

    brief = BRIEF.format(target=spec["target"], report=REPORT_FILE,
                         library=LIB_FILE)

    key = {
        "condition": condition,
        "target": spec["target"],
        "purchase_size": stats["purchase_size"],
        "verdict": stats["verdict"],
        "reason": stats["reason"],
        "actives_in_top": stats["actives_in_top"],
        "n_actives": stats["n_actives"],
        "library_size": stats["n"],
        "ef_top": round(stats["ef_top"], 4),
        "auc_raw": round(stats["auc_raw"], 4),
        "auc_matched": (None if stats["auc_matched"] is None
                        else round(stats["auc_matched"], 4)),
        "p_raw": round(stats["p_raw"], 5),
        "p_matched": (None if stats["p_matched"] is None
                      else round(stats["p_matched"], 5)),
        "matched_pairs": int(stats["matched_pairs"]),
        "matched_partners": stats["matched_partners"],
        "rho_size": round(stats["rho_size"], 4),
        "separation_heavy_atoms": stats["separation"],
        # F2's impossibility witness: an identity on the shipped rows, not a
        # complaint about data quality.
        "witness": None if condition != "F2" else {
            "min_heavy_atoms_active": None,      # filled below from the bytes
            "max_heavy_atoms_inactive": None,
            "identity": "label == 1[heavy_atoms >= t] for every row in "
                        f"{LIB_FILE}, so (g, c) and (g + c*1[heavy_atoms >= t], "
                        "0) score every compound identically and the activity "
                        "coefficient c is not identifiable",
        },
    }
    if condition == "F2":
        deck = _parse(text)
        heavy = deck["heavy_atoms"]
        label = deck["label"].astype(bool)
        key["witness"]["min_heavy_atoms_active"] = float(heavy[label].min())
        key["witness"]["max_heavy_atoms_inactive"] = float(heavy[~label].max())

    files = {LIB_FILE: text, REPORT_FILE: report}
    # 24 calls: loading the library, the headline metrics, the campaign's own
    # control and then a matched control that has to be built and defended is
    # several passes of work, and the first pass points the wrong way.
    return Episode("docking-decoy-control", seed, condition, brief, files, key,
                   budget=24,
                   checkpoints=["counts", "estimate", "verdict", "attribution"])


# --------------------------------------------------------------------- scoring

# Abstention vocabulary, split by how it has to be matched. The short tokens
# are matched exactly because they are substrings of ordinary words ("na" sits
# inside "unattainable"); the long markers are matched as substrings so that a
# qualified refusal - "cannot_determine (no size-matched partners)" - is not
# thrown away on formatting.
_ABSTAIN_TOKENS = {"n_a", "n.a.", "na", "nan", "none", "null", "nil", "-", "?"}
_ABSTAIN_MARKERS = ("cannot", "can_not", "cant", "not_determin", "undetermin",
                    "indetermin", "determinab", "identifiab", "insufficient",
                    "unknown", "unavailable", "not_applicable", "inconclusive",
                    "unanswerable", "no_defensible", "not_estimable",
                    "not_computable", "no_value", "refus", "abstain",
                    "not_enough", "underpower", "no_power")


def _abstains(raw, has_number: bool) -> bool:
    """Is this field a STATED refusal?

    A missing or empty field is not one. Treating silence as abstention once
    let an empty submission score full marks on every F2 instance, so a model
    that answered nothing would have beaten one that engaged.
    """
    if raw is None or has_number:
        return False
    token = str(raw).strip().lower().replace("'", "")
    token = token.replace("-", "_").replace(" ", "_").replace("/", "_")
    token = token.strip("_.")
    if not token:
        return False
    if token in _ABSTAIN_TOKENS:
        return True
    return any(marker in token for marker in _ABSTAIN_MARKERS)

_SUPPORTED = {"supported", "support", "yes", "true", "real", "genuine",
              "enriched", "adopt", "holds"}
_NOT_SUPPORTED = {"not_supported", "unsupported", "not_support", "no", "false",
                  "artifact", "artefact", "not_enriched", "not_real",
                  "do_not_adopt", "reject"}


def _normalise_verdict(raw) -> str | None:
    token = str(raw or "").strip().lower()
    token = token.replace("'", "").replace("’", "")
    token = token.replace("-", "_").replace(" ", "_").replace("/", "_")
    token = token.strip("_.")
    if not token:
        # An omitted field is not a documented refusal and never scores as one.
        return None
    if token in _NOT_SUPPORTED:
        return "not_supported"
    if token in _SUPPORTED:
        return "supported"
    if token in _ABSTAIN_TOKENS:
        return "cannot_determine"
    # Free-form phrasing. Abstention is tested FIRST and with a wide
    # vocabulary: "not determinable" starts with "not", and a narrower list
    # sends a stated refusal to `not_supported`, which both fails an F2 that
    # was answered correctly and hands a C0/H1 pass to a candidate who never
    # committed to a verdict.
    if any(word in token for word in
           ("cannot", "can_not", "cant_", "unable", "undetermin", "indetermin",
            "not_determin", "determinab", "unidentifiab", "not_identifiab",
            "non_identifiab", "unanswerable", "not_answerable", "untestable",
            "inconclusive", "unclear", "ambiguous", "insufficient",
            "no_conclusion", "not_enough", "underpower", "no_power",
            "not_established", "cannot_be_settled")):
        return "cannot_determine"
    if (token.startswith("not") or token.startswith("no_")
            or any(word in token for word in
                   ("not_support", "unsupported", "not_enrich", "not_real",
                    "artifact", "artefact", "confound", "spurious",
                    "insignificant", "non_significant", "no_significan",
                    "do_not_adopt", "dont_adopt", "reject"))):
        return "not_supported"
    if any(word in token for word in ("support", "real", "genuine", "enrich",
                                      "adopt", "significan", "holds", "valid")):
        return "supported"
    return None


def _number(value):
    """Parse the number the model meant, so formatting is never what fails a
    correct answer: "0.71", "AUC = 0.71", "~0.71" and "71%" all read the same."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value if value is not None else "").strip().lower()
    percent = "%" in text
    text = text.replace("%", "").replace(",", "").strip()
    try:
        number = float(text)
    except ValueError:
        found = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
        if not found:
            return None
        number = float(found.group())
    # An AUC cannot exceed 1, so a percentage is unambiguous.
    if percent and 1.5 < abs(number) <= 100.0:
        number /= 100.0
    return number


SIZE_WORDS = ("heavy atom", "heavy-atom", "heavy_atom", "atom count",
              "number of atoms", "size", "sized", "bulk", "mass",
              "molecular weight", "molweight", "mol wt", "molwt", "mw",
              "larger", "bigger", "heavier")

ATTRIB_WORDS = ("explain", "account", "proxy", "surrogate", "driven", "drives",
                "track", "reflect", "confound", "artifact", "artefact", "bias",
                "attribut", "because", "purely", "merely", "alone",
                "collinear", "correlat", "monoton", "scales with",
                "function of", "nothing but", "entirely", "rather than")

MATCH_WORDS = ("match", "comparable", "same size", "similar size",
               "similarly sized", "equal size", "stratif", "residual",
               "adjust", "control for", "controlling for", "controlled for",
               "conditional on", "condition on", "conditioning on", "caliper",
               "within bins", "within strata", "partial correlation", "regress",
               "covariate", "propensity", "size-corrected", "size-independent",
               "holding", "accounting for", "restricted to", "subset of the "
               "untested", "like-for-like", "paired with", "held fixed")

IDENT_WORDS = ("identifiab", "identified separately", "no overlap",
               "non-overlapping", "do not overlap", "does not overlap",
               "no common support", "disjoint", "separat", "collinear",
               "confounded with", "cannot be separated", "cannot separate",
               "cannot be distinguished", "cannot distinguish",
               "indistinguishable", "no comparable", "no matched",
               "no size-matched", "outside the range", "outside the size",
               "perfectly predict", "perfectly correlated", "one-to-one",
               "entirely above", "all larger", "every active is larger",
               "no untested compound", "cannot be estimated")

# Clauses that name an explanation only to RULE IT OUT. Removed literally
# before any keyword search: "quenching, not inhibition" must not count as
# claiming inhibition, and "not a size artifact" must not count as claiming
# the enrichment is one. Plain substring removal on purpose - a regex for this
# failed silently in situ once while passing in isolation.
NEGATED = (
    "not merely a size artifact", "not merely a size artefact",
    "not simply a size artifact", "not simply a size artefact",
    "not just a size artifact", "not just a size artefact",
    "not a size artifact", "not a size artefact", "not an artifact of size",
    "not an artefact of size", "not an artifact of molecular size",
    "not an artifact of heavy atom count", "no size artifact",
    "not explained by size", "not explained by heavy", "not explained by mw",
    "not explained by molecular weight", "not fully explained by size",
    "not accounted for by size", "not accounted for by heavy",
    "not attributable to size", "not attributable to heavy",
    "cannot be explained by size", "cannot be explained by heavy",
    "not driven by size", "not driven by heavy", "not driven by molecular",
    "not due to size", "not due to heavy", "not due to molecular weight",
    "not purely size", "not purely a size", "not merely size", "not just size",
    "not only size", "not simply size", "not size alone", "not mw alone",
    "not heavy atom count alone", "not a size effect", "not size",
    "more than size", "beyond size", "rather than size", "instead of size",
    "over and above size", "independent of size", "independently of size",
    "not a molecular weight artifact", "not an artifact",
    "not confounded", "not collinear", "not disjoint", "not separated",
    "not indistinguishable", "do overlap", "sizes do overlap",
    "not unidentifiable", "not a data quality",
)


def _strip_negated(text: str) -> str:
    lowered = str(text or "").lower()
    for phrase in sorted(NEGATED, key=len, reverse=True):
        lowered = lowered.replace(phrase, " ")
    return lowered


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["counts", "estimate", "verdict", "attribution"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "counts")

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # Re-derive the truth from the shipped bytes rather than reading the key.
    # The workspace copy is compared and never trusted: run_python can rewrite
    # anything in there, and a rewritten library must not move the answer.
    shipped = episode.files[LIB_FILE]
    on_disk = None
    path = Path(workspace) / LIB_FILE
    if path.exists():
        on_disk = path.read_text(encoding="utf-8", errors="replace")
    detail["workspace_library_matches_shipped"] = (on_disk == shipped)

    stats = _analyse(_parse(shipped), int(episode.key["purchase_size"]))
    detail["recomputed"] = {
        "actives_in_purchase_list": stats["actives_in_top"],
        "n_actives": stats["n_actives"], "library_size": stats["n"],
        "auc_raw": round(stats["auc_raw"], 4),
        "auc_matched": (None if stats["auc_matched"] is None
                        else round(stats["auc_matched"], 4)),
        "ef_top": round(stats["ef_top"], 3),
        "p_raw": round(stats["p_raw"], 5),
        "p_matched": (None if stats["p_matched"] is None
                      else round(stats["p_matched"], 5)),
        "matched_pairs": int(stats["matched_pairs"]),
        "separation_heavy_atoms": stats["separation"],
        "rho_score_vs_heavy_atoms": round(stats["rho_size"], 4),
        "verdict": stats["verdict"], "reason": stats["reason"]}
    detail["key_agrees_with_recomputation"] = (
        episode.key.get("verdict") == stats["verdict"]
        and episode.key.get("actives_in_top") == stats["actives_in_top"])
    if episode.key["condition"] == "F2":
        detail["witness"] = episode.key.get("witness")

    # 1. counts - a fact of the file, and the check that pins the sign
    #    convention: with the score direction reversed this count collapses,
    #    so a "no enrichment" verdict cannot come from reading the column
    #    backwards.
    given_count = _number(field("actives_in_purchase_list"))
    checks["counts"] = (given_count is not None
                        and int(round(given_count)) == stats["actives_in_top"])
    detail["given_count"] = field("actives_in_purchase_list")

    # 2. estimate - the number the decision rests on, recomputed. Where no
    #    size-matched contrast exists the only honest answer is a stated
    #    refusal; silence is not one.
    raw_auc = field("enrichment_auc")
    given_auc = _number(raw_auc)
    abstained = _abstains(raw_auc, given_auc is not None)
    if stats["auc_matched"] is None:
        checks["estimate"] = abstained and given_auc is None
        detail["expected_auc"] = ("refusal: no size-matched contrast exists in "
                                  "this library")
    else:
        checks["estimate"] = (not abstained and given_auc is not None
                             and abs(given_auc - stats["auc_matched"]) <= AUC_TOL)
        detail["expected_auc"] = round(stats["auc_matched"], 4)
        detail["auc_tolerance"] = AUC_TOL
    detail["given_auc"] = raw_auc

    # 3. verdict - graded against the recomputed controls.
    given_verdict = _normalise_verdict(field("claim_verdict"))
    checks["verdict"] = given_verdict == stats["verdict"]
    detail["given_verdict"] = field("claim_verdict")
    detail["expected_verdict"] = stats["verdict"]

    # 4. attribution - the explanation has to rest on the right thing, and
    #    clauses that name an explanation only to reject it are removed first.
    stated = _strip_negated(field("explanation"))
    names_size = any(word in stated for word in SIZE_WORDS)
    names_attribution = any(word in stated for word in ATTRIB_WORDS)
    names_matching = any(word in stated for word in MATCH_WORDS)
    names_identity = any(word in stated for word in IDENT_WORDS)
    detail["explanation_signals"] = {
        "size": names_size, "attribution": names_attribution,
        "matching": names_matching, "identity": names_identity}
    if stats["reason"] == "unidentifiable":
        checks["attribution"] = names_size and names_identity
    elif stats["reason"] == "size_artifact":
        checks["attribution"] = names_size and names_attribution
    elif stats["reason"] == "survives_matching":
        # The claim is true, but it is only defensible against a like-for-like
        # comparison: the headline number is inflated here too. And a false
        # alarm - calling the enrichment a size artifact - fails even though
        # the verdict says otherwise.
        checks["attribution"] = names_matching and not (
            names_size and any(word in stated for word in
                               ("artifact", "artefact", "purely", "merely",
                                "nothing but", "alone", "spurious")))
    else:
        checks["attribution"] = names_attribution
    detail["stated_explanation"] = str(field("explanation") or "")[:300]

    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


# ------------------------------------------------------------------- reference

def reference_submission(episode: Episode) -> dict:
    """The submission a competent screener would make.

    Every number is recomputed from the shipped library, by the same route a
    candidate must take, so B8 proves the episode is solvable from the
    workspace rather than proving the key is self-consistent.
    """
    stats = _analyse(_parse(episode.files[LIB_FILE]),
                     int(episode.key["purchase_size"]))
    count = stats["actives_in_top"]
    raw = stats["auc_raw"]
    matched = stats["auc_matched"]

    if matched is None:
        deck = _parse(episode.files[LIB_FILE])
        heavy = deck["heavy_atoms"]
        label = deck["label"].astype(bool)
        lo = float(heavy[label].min())
        hi = float(heavy[~label].max())
        return {
            "actives_in_purchase_list": count,
            "enrichment_auc": "cannot_determine",
            "claim_verdict": "cannot_determine",
            "explanation": (
                f"dock_score in this library is essentially a size variable: "
                f"its rank correlation with heavy_atoms is "
                f"{stats['rho_size']:.2f}, so the {stats['n_actives']} "
                f"confirmed actives sweep the top of the ranking (AUC "
                f"{raw:.2f}, {count} of them inside the purchase list) largely "
                f"because they are the biggest compounds present. That would "
                f"normally be settled by comparing each active against "
                f"untested compounds of the same size, and here no such "
                f"comparison exists: every confirmed active has at least "
                f"{lo:.0f} heavy atoms and no untested compound has more than "
                f"{hi:.0f}, so the two groups are disjoint in size with no "
                f"common support. On these rows label is exactly the indicator "
                f"of heavy_atoms >= {lo:.0f}, which means any size term g and "
                f"activity coefficient c give the identical fit as g plus that "
                f"indicator scaled by c with c set to zero: the activity "
                f"effect is not identifiable from this library, and the "
                f"scrambled-label control quoted in the report cannot rescue "
                f"it because scrambling breaks the size ordering along with "
                f"the labels. No defensible enrichment number follows from "
                f"these data; the library needs untested compounds inside the "
                f"actives' size range before the question can be asked."),
            "conf_actives_in_purchase_list": 0.99,
            "conf_enrichment_auc": 0.92,
            "conf_claim_verdict": 0.9,
            "conf_explanation": 0.88,
        }

    common = (
        f"The purchase list holds {count} of the {stats['n_actives']} confirmed "
        f"actives, an enrichment factor of {stats['ef_top']:.1f} and a "
        f"whole-library AUC of {raw:.2f} with the label-scrambling control the "
        f"report quotes (p={stats['p_raw']:.3f}). That control is correctly run "
        f"and settles nothing here: dock_score rises with molecular bulk (rank "
        f"correlation {stats['rho_size']:.2f} against heavy_atoms) and the "
        f"untested compounds are mostly small catalogue stock, so scrambling "
        f"labels destroys the size ordering too. The comparison that separates "
        f"ranking from bulk uses the {stats['matched_partners']} untested "
        f"compounds that sit inside the actives' size range: scoring each "
        f"active only against untested compounds within {CALIPER:.0f} heavy "
        f"atom of it gives {int(stats['matched_pairs'])} like-for-like pairs "
        f"and an AUC of {matched:.2f}")

    if stats["reason"] == "size_artifact":
        explanation = (
            common + f", with a size-matched permutation null putting that at "
            f"p={stats['p_matched']:.2f}. Matched on size the actives win about "
            f"half their comparisons, so the headline number is accounted for "
            f"by heavy-atom count rather than by the score recognising "
            f"binders, and the ranking carries no usable activity information. "
            f"The recommendation does not hold: what looks like enrichment is "
            f"the size composition of the untested set.")
    elif stats["reason"] == "survives_matching":
        explanation = (
            common + f", and a size-matched permutation null puts that at "
            f"p={stats['p_matched']:.3f}, below alpha={ALPHA}. So part of the "
            f"headline {raw:.2f} is bulk - that inflation is why {matched:.2f} "
            f"and not {raw:.2f} is the number I would report - but a real "
            f"ranking signal remains once each active is compared with "
            f"like-for-like untested compounds, and it holds under "
            f"stratification by heavy-atom count. The recommendation holds on "
            f"the strength of the matched estimate.")
    else:
        explanation = (
            common + ". Neither the whole-library comparison nor the "
            "size-matched one clears the programme's alpha, so the ranking "
            "carries no usable activity information for this target.")

    return {
        "actives_in_purchase_list": count,
        "enrichment_auc": round(matched, 3),
        "claim_verdict": stats["verdict"],
        "explanation": explanation,
        "conf_actives_in_purchase_list": 0.99,
        "conf_enrichment_auc": 0.85,
        "conf_claim_verdict": 0.88,
        "conf_explanation": 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
