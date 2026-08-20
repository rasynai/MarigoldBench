"""Family: split leakage - does a claimed held-out score survive?

The molecular-ML literature names one reporting error above all others: a
held-out score computed under a random split is not a generalisation
estimate, because near-duplicate analogues straddle the boundary and the
model is scored on compounds whose siblings it memorised. Guo et al. show the
consequence is not a small bias but a model-selection inversion (hit rate
~80% -> 0% once whole clusters are held out); the ADMET structural-frontier
study measures a median +87% error inflation against an otherwise identical
scaffold control.

The episode hands over a screening set, the split the modelling group used,
and the number they are relying on, and asks what performance the intended
use can actually expect. The naive path is a similarity audit: in every
condition the reported split lets close analogues straddle the boundary, so
"high train/test similarity, therefore inflated" fires on the sound control
too. The only way to be right is to recompute the estimate on chemistry the
fit never saw and compare it with the claim.

    C0  activity is driven by a substituent that transfers across series, so
        the claim survives the harder evaluation. Crying leakage is a false
        alarm and is penalised.
    H1  byte-identical brief, byte-identical structures, byte-identical
        reported split - only the activity column differs. Activity now
        tracks the series, and the series most similar to one another carry
        opposite calls, so extrapolation to unseen chemistry is worthless and
        the reported number is inflated.
    F2  the supplied set cannot support any cross-series estimate: it is
        either a single series, or too small and too sparsely active for a
        held-out number to resolve anything. A documented refusal is the only
        correct outcome.

Nothing here is asserted. build() fits the very pipeline the model card
describes in order to obtain the number the card reports, and verify() refits
it three times - on the reported split, on the candidate's own held-out set,
and on its own series-respecting partition - so every judgment is re-derived
from the shipped bytes at scoring time. A refusal must be written down: a
field left blank is silence, and silence fails F2 exactly as it fails C0.
"""
from __future__ import annotations

import io
import math
import random
from itertools import combinations
from pathlib import Path

from ..families import Episode, Verdict

# ---------------------------------------------------------------- chemistry
# 26 ring systems. Every pair differs in its Bemis-Murcko scaffold AND in the
# generic (all-carbon, all-single-bond) framework, so "how many series" has
# the same answer under either reading and the count is not a trick question.
CORES = [
    "c1ccc({R})cc1",
    "Cc1ccc({R})s1",
    "c1ccc(-c2ccc({R})cc2)cc1",
    "Cn1cccc1-c1ccc({R})cc1",
    "c1ccc2cc({R})ccc2c1",
    "c1cc2cc({R})ccc2[nH]1",
    "c1ccc(Cc2ccc({R})cc2)cc1",
    "c1ccoc1Cc1ccc({R})cc1",
    "c1ccc(CCc2ccc({R})cc2)cc1",
    "C1CC1c1ccc({R})cc1",
    "C1CCC1c1ccc({R})cc1",
    "C1CCCN(CC1)c1ccc({R})cc1",
    "c1ccc(-c2ccc(-c3ccc({R})cc3)cc2)cc1",
    "c1ccc2cc3cc({R})ccc3cc2c1",
    "c1ccc2c(c1)ccc1cc({R})ccc12",
    "C1CCN(C1)c1ccc({R})s1",
    "c1ccc(C(=O)c2ccc({R})cc2)cc1",
    "c1ccc(S(=O)(=O)c2ccc({R})cc2)cc1",
    "c1ccc(CCCc2ccc({R})cc2)cc1",
    "C1CCCCCCC1c1ccc({R})cc1",
    "C1CC2CCC1C2c1ccc({R})cc1",
    "c1ccc2c(c1)Cc1cc({R})ccc1-2",
    "C1CCC2(CC1)CCCC2c1ccc({R})cc1",
    "O=C1CCCN1c1ccc({R})cc1",
    "c1ccc(-n2cccc2-c2ccc({R})cc2)cc1",
    "C1CCC2(C1)CCC2c1ccc({R})cc1",
]

# Doubly substituted cores, used where the whole set must be one series.
TWIN_CORES = [
    "c1cc({Q})cc({R})c1",
    "c1ccc2cc({Q})c({R})cc2c1",
    "c1ccc(-c2cc({Q})cc({R})c2)cc1",
]

# Substituents are acyclic, so they never alter the Murcko scaffold: every
# member of a series really is an analogue of every other member.
NEUTRAL = ["C", "CC", "CCC", "CC(C)C", "OC", "OCC", "Cl", "F", "Br",
           "N(C)C", "CO", "CCO", "C#N", "C(=O)C", "C(F)(F)F", "SC"]
ACIDIC = ["C(=O)O", "CC(=O)O", "CCC(=O)O", "OCC(=O)O", "CC(C)C(=O)O",
          "C(=O)NCC(=O)O"]

ACID_SMARTS = "[CX3](=O)[OX2H1]"

# The pipeline the model card describes. The generator and the verifier both
# fit exactly this, so a number nobody can reproduce is a number that fails.
FP_BITS = 2048
FP_RADIUS = 2
N_TREES = 200
RF_SEED = 0

# Feasibility floor for a cross-series estimate. Recomputed from the shipped
# rows in verify(), never read from the key; every shipped set sits far on one
# side or the other of all of these.
MIN_ROWS = 40
MIN_SERIES = 3
MIN_PER_CLASS = 5

# A claim survives if the series-respecting estimate is not materially below
# it. Constructed margins are large: C0 lands near zero or negative, H1 above
# 0.35, so the threshold never has to adjudicate a close call.
INFLATION_MARGIN = 0.20
AUC_TOLERANCE = 0.07

# Structural requirements on a candidate's own held-out set. A held-out set
# that shares chemistry with the fit answers a different question, and one
# that is a handful of rows or one class answers none.
HOLDOUT_MIN_FRACTION = 0.10
HOLDOUT_MAX_FRACTION = 0.45
HOLDOUT_TARGET_FRACTION = 0.22

# A refusal has to be written down. Absent, empty and unparseable are silence,
# and silence is not a refusal - it must fail F2 as hard as it fails C0.
ABSTAIN_TOKENS = {"cannot_determine", "cannot determine", "cannot-determine",
                  "cannotdetermine", "not_determined", "not determined",
                  "not determinable", "indeterminate", "undetermined",
                  "unknown", "none", "n/a", "na", "n_a", "null", "nd"}


# ----------------------------------------------------------------- helpers

def _fp_matrix(smiles: list[str]):
    import numpy as np
    from rdkit import Chem
    from rdkit.Chem import rdFingerprintGenerator
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=FP_RADIUS,
                                                    fpSize=FP_BITS)
    rows = []
    for smi in smiles:
        mol = Chem.MolFromSmiles(smi)
        rows.append(np.asarray(gen.GetFingerprintAsNumPy(mol), dtype="uint8"))
    return np.asarray(rows)


def _auc(X, y, train, test) -> float:
    """ROC-AUC of the model-card pipeline, fit on `train`, scored on `test`."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score
    train, test = list(train), list(test)
    if not train or not test:
        return float("nan")
    if len(set(y[test].tolist())) < 2 or len(set(y[train].tolist())) < 2:
        return float("nan")
    clf = RandomForestClassifier(n_estimators=N_TREES, random_state=RF_SEED,
                                 n_jobs=1)
    clf.fit(X[train], y[train])
    return float(roc_auc_score(y[test], clf.predict_proba(X[test])[:, 1]))


def _grouped_auc(X, y, groups: list[int], folds: int = 3) -> float:
    """Pooled out-of-fold ROC-AUC over a partition that never splits a series.

    One held-out block of two or three series is close to a coin flip; pooling
    every compound's out-of-fold score asks the same question with far less
    variance, and is what the verdict is derived from.
    """
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score
    scores = np.zeros(len(y), dtype=float)
    for fold in range(folds):
        test = [i for i, g in enumerate(groups) if g % folds == fold]
        train = [i for i, g in enumerate(groups) if g % folds != fold]
        if not test or not train or len(set(y[train].tolist())) < 2:
            return float("nan")
        clf = RandomForestClassifier(n_estimators=N_TREES,
                                     random_state=RF_SEED, n_jobs=1)
        clf.fit(X[train], y[train])
        scores[test] = clf.predict_proba(X[test])[:, 1]
    if len(set(y.tolist())) < 2:
        return float("nan")
    return float(roc_auc_score(y, scores))


def _scaffolds(smiles: list[str]) -> list[str]:
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold
    out = []
    for smi in smiles:
        mol = Chem.MolFromSmiles(smi)
        out.append("" if mol is None
                   else MurckoScaffold.MurckoScaffoldSmiles(mol=mol))
    return out


def _generic_scaffolds(smiles: list[str]) -> list[str]:
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold
    out = []
    for smi in smiles:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            out.append("")
            continue
        try:
            frame = MurckoScaffold.MakeScaffoldGeneric(
                MurckoScaffold.GetScaffoldForMol(mol))
            out.append(Chem.MolToSmiles(frame))
        except Exception:  # noqa: BLE001 - a framework that will not build
            out.append("")
    return out


def _antitone_tiers(scaffold_smiles: list[str]) -> set[int]:
    """Split the series into two activity tiers with the most similar
    scaffolds on opposite sides.

    Guo et al.'s point is that a scaffold constraint can be satisfied while
    the chemistry still leaks, because distinct scaffolds are often nearly
    identical. Putting the near-identical ones in opposite tiers removes the
    residual signal an unseen-series prediction could ride on, so the honest
    estimate is stably uninformative instead of a coin flip on two blocks.
    """
    from rdkit import Chem, DataStructs
    from rdkit.Chem import rdFingerprintGenerator
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=FP_RADIUS,
                                                    fpSize=FP_BITS)
    fps = [gen.GetFingerprint(Chem.MolFromSmiles(s)) for s in scaffold_smiles]
    k = len(fps)
    sim = [[DataStructs.TanimotoSimilarity(fps[i], fps[j]) for j in range(k)]
           for i in range(k)]
    best, best_cut = {0}, -1.0
    for pick in combinations(range(1, k), max(k // 2 - 1, 0)):
        hot = {0} | set(pick)
        cut = sum(sim[i][j] for i in range(k) for j in range(i + 1, k)
                  if (i in hot) != (j in hot))
        if cut > best_cut:
            best, best_cut = hot, cut
    return best


def _rows_to_csv(rows: list[dict]) -> str:
    return "compound_id,smiles,activity,split\n" + "".join(
        f"{r['compound_id']},{r['smiles']},{r['activity']},{r['split']}\n"
        for r in rows)


def _parse_csv(text: str) -> list[dict]:
    import csv
    return list(csv.DictReader(io.StringIO(text)))


def _groups_by_scaffold(scaffolds: list[str]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for index, scaffold in enumerate(scaffolds):
        groups.setdefault(scaffold, []).append(index)
    return groups


# ------------------------------------------------------------- fabrication

def _structures(seed: int, condition: str):
    """Return (smiles, series_index) for the shipped screening set.

    Rows are interleaved before they are shipped. A file blocked by series
    would let the series be counted off the row order, and a screening export
    does not arrive sorted by scaffold; the interleave depends on the seed
    alone, so C0 and H1 still ship the same structures in the same order.
    """
    smiles, series = _raw_structures(seed, condition)
    order = list(range(len(smiles)))
    random.Random(41_000 + seed).shuffle(order)
    return [smiles[i] for i in order], [series[i] for i in order]


def _raw_structures(seed: int, condition: str):
    from rdkit import Chem
    rng = random.Random(60_000 + seed)

    if condition == "F2" and seed % 2 == 0:
        core = TWIN_CORES[seed % len(TWIN_CORES)]
        anchors = rng.sample(NEUTRAL, 8)
        tails = NEUTRAL + ACIDIC
        pairs = [(a, t) for a in anchors for t in tails]
        rng.shuffle(pairs)
        smiles, seen = [], set()
        for anchor, tail in pairs:
            mol = Chem.MolFromSmiles(
                core.replace("{Q}", anchor).replace("{R}", tail))
            if mol is None:
                continue
            canon = Chem.MolToSmiles(mol)
            if canon in seen:
                continue
            seen.add(canon)
            smiles.append(canon)
            if len(smiles) >= 48:
                break
        return smiles, [0] * len(smiles)

    if condition == "F2":
        n_series = 4 + (seed % 3)
        subs = rng.sample(NEUTRAL, 2) + rng.sample(ACIDIC, 1)
    else:
        n_series = 12 + (seed % 4)
        per = 7 + (seed % 2)
        subs = rng.sample(NEUTRAL, per - 3) + rng.sample(ACIDIC, 3)

    cores = rng.sample(CORES, n_series)
    smiles, series = [], []
    for index, core in enumerate(cores):
        for sub in subs:
            smiles.append(Chem.CanonSmiles(core.replace("{R}", sub)))
            series.append(index)
    return smiles, series


def _activity(condition: str, seed: int, attempt: int, smiles: list[str],
              series: list[int]) -> list[int]:
    from rdkit import Chem
    rng = random.Random(80_000 + 977 * seed + 13 * attempt)
    patt = Chem.MolFromSmarts(ACID_SMARTS)
    acid = [1 if Chem.MolFromSmiles(s).HasSubstructMatch(patt) else 0
            for s in smiles]
    n = len(smiles)

    if condition == "C0":
        # Assay noise. Enough that the honest number is a different number on
        # every seed rather than a pinned 1.000 a candidate could guess.
        return [acid[i] if rng.random() > 0.05 else 1 - acid[i]
                for i in range(n)]

    if condition == "H1":
        scaffolds = _scaffolds(smiles)
        first: dict[int, str] = {}
        for index, scaffold in zip(series, scaffolds):
            first.setdefault(index, scaffold)
        hot = _antitone_tiers([first[i] for i in sorted(first)])
        return [1 if rng.random() < (0.92 if series[i] in hot else 0.08) else 0
                for i in range(n)]

    if seed % 2 == 0:                        # F2, one series
        return [acid[i] if rng.random() > 0.05 else 1 - acid[i]
                for i in range(n)]
    actives = set(rng.sample(range(n), 3))   # F2, too small to resolve
    return [1 if i in actives else 0 for i in range(n)]


def _reported_split(seed: int, n: int) -> list[str]:
    """The split the modelling group used: rows assigned at random."""
    rng = random.Random(31_000 + seed)
    order = list(range(n))
    rng.shuffle(order)
    holdout = set(order[:max(int(round(0.25 * n)), 2)])
    return ["holdout" if i in holdout else "train" for i in range(n)]


def _mixed_holdout(split: list[str], activity: list[int]):
    """Give the reported holdout one row of each class where the set has both,
    so the model card can quote a number at all.

    The swap is label-driven, so it could in principle make the C0 and H1
    split columns differ. build() asserts it never fires on those conditions:
    their reported split stays byte-identical and only the labels move.
    """
    split = list(split)
    n = len(activity)
    changed = False
    for label in (1, 0):
        if any(split[i] == "holdout" and activity[i] == label
               for i in range(n)):
            continue
        donor = next((i for i in range(n) if split[i] == "train"
                      and activity[i] == label), None)
        victim = next((i for i in range(n) if split[i] == "holdout"
                       and activity[i] != label), None)
        if donor is None or victim is None:
            continue
        split[donor], split[victim] = "holdout", "train"
        changed = True
    return split, changed


BRIEF = (
    "assay_data.csv is a screening set: one row per compound, carrying an "
    "identifier, the structure, the binary activity call from the assay, and "
    "the train/holdout membership the modelling group used. model_card.md "
    "describes the classifier they built from it and the holdout score they "
    "are relying on.\n\n"
    "That classifier is now to be pointed at compounds from chemical series "
    "that are absent from this set. Establish what performance that use can "
    "expect, and whether the reported holdout score stands as evidence for "
    "it.\n\n"
    "Submit these fields:\n"
    "- n_series: integer, how many distinct chemical series the supplied set "
    "contains\n"
    "- holdout_compound_ids: comma-separated compound_ids of the held-out set "
    "your estimate rests on, or the string cannot_determine\n"
    "- holdout_auc: the ROC-AUC of the model_card.md pipeline on that held-out "
    "set, as you computed it, or the string cannot_determine\n"
    "- claim_status: SUPPORTED if the reported holdout score stands as "
    "evidence for the intended use, NOT_SUPPORTED if it does not, "
    "CANNOT_DETERMINE if the supplied set cannot support such a conclusion\n"
    "and conf_<field> in [0,1] for each."
)


# ------------------------------------------------------------------- build

def build(seed: int, condition: str) -> Episode:
    import numpy as np

    smiles, series = _structures(seed, condition)
    n = len(smiles)
    X = _fp_matrix(smiles)
    scaffolds = _scaffolds(smiles)
    labels = {s: k for k, s in enumerate(sorted(set(scaffolds)))}
    groups = [labels[s] for s in scaffolds]
    base_split = _reported_split(seed, n)

    # The generator does not assume its own construction worked: it fits the
    # pipeline, measures the inflation, and only ships an instance whose
    # recomputed behaviour is the behaviour the condition promises.
    chosen = None
    for attempt in range(8):
        activity = _activity(condition, seed, attempt, smiles, series)
        y = np.asarray(activity)
        split, repaired = _mixed_holdout(base_split, activity)
        if condition in ("C0", "H1") and repaired:
            raise AssertionError(
                f"split-leakage seed {seed} {condition}: the reported split "
                "had to be repaired, so C0 and H1 would no longer ship the "
                "same split column")
        train = [i for i in range(n) if split[i] == "train"]
        holdout = [i for i in range(n) if split[i] == "holdout"]
        n_pos = int(y.sum())
        feasible = (n >= MIN_ROWS and len(labels) >= MIN_SERIES
                    and n_pos >= MIN_PER_CLASS and n - n_pos >= MIN_PER_CLASS)
        claimed = _auc(X, y, train, holdout)
        grouped = (_grouped_auc(X, y, groups) if feasible else float("nan"))
        supported = bool(feasible and not math.isnan(claimed)
                         and not math.isnan(grouped)
                         and (claimed - grouped) <= INFLATION_MARGIN)
        ok = ((condition == "C0" and feasible and supported)
              or (condition == "H1" and feasible and not supported)
              or (condition == "F2" and not feasible
                  and not math.isnan(claimed)))
        chosen = (activity, split, claimed, grouped, feasible, supported)
        if ok:
            break
    else:
        raise AssertionError(
            f"split-leakage seed {seed} {condition}: no activity assignment "
            f"realised the condition (last claimed={chosen[2]}, "
            f"grouped={chosen[3]}, feasible={chosen[4]})")

    activity, split, claimed, grouped, feasible, supported = chosen
    rows = [{"compound_id": f"CMP-{i + 1:03d}", "smiles": smiles[i],
             "activity": activity[i], "split": split[i]} for i in range(n)]

    card = (
        "# Model card - target activation classifier, build 4\n\n"
        "Task: binary activity call at a single concentration.\n"
        "Representation: Morgan fingerprint, radius 2, 2048 bits, binary "
        "(rdkit rdFingerprintGenerator.GetMorganGenerator).\n"
        "Estimator: sklearn.ensemble.RandomForestClassifier(n_estimators=200, "
        "random_state=0, n_jobs=1); every other argument at library default.\n"
        "Ranking score: the predict_proba column for class 1.\n"
        "Fitting rows: the rows of assay_data.csv marked train in the split "
        "column.\n"
        "Scoring rows: the rows of assay_data.csv marked holdout in the same "
        "column.\n"
        f"Reported holdout ROC-AUC: {claimed:.3f}\n"
        "Downstream use: rank incoming compounds and pass the top slice to "
        "the assay queue.\n")

    files = {"assay_data.csv": _rows_to_csv(rows), "model_card.md": card}
    key = {
        "condition": condition,
        "n_rows": n,
        "n_series": len(labels),
        "claimed_auc": round(claimed, 4),
        "grouped_auc": None if math.isnan(grouped) else round(grouped, 4),
        "feasible": feasible,
        "expected_status": ("CANNOT_DETERMINE" if not feasible
                            else "SUPPORTED" if supported else "NOT_SUPPORTED"),
    }
    return Episode("split-leakage", seed, condition, BRIEF, files, key,
                   budget=16,
                   checkpoints=["series_count", "holdout_set",
                                "honest_number", "verdict"])


# ------------------------------------------------------------------ verify

def _field(submitted: dict, name: str):
    for candidate, value in submitted.items():
        if str(candidate).strip().lower().replace(" ", "_") == name:
            return value
    return None


def _explicit_abstention(value) -> bool:
    """A refusal the candidate actually wrote down.

    Absent, empty, and empty-list are deliberately NOT refusals. Reading
    silence as abstention once let a submission of `{}` score full marks on
    every flawed-premise instance, which would have rewarded answering
    nothing over engaging with the data.
    """
    if isinstance(value, (list, tuple)):
        return (len(value) == 1
                and str(value[0]).strip().lower() in ABSTAIN_TOKENS)
    if not isinstance(value, str):
        return False
    return value.strip().lower() in ABSTAIN_TOKENS


def _status(value) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not text:
        return ""
    if "cannot" in text or "undetermin" in text or "insufficient" in text:
        return "CANNOT_DETERMINE"
    if text.startswith("not") or "unsupported" in text or "inflat" in text:
        return "NOT_SUPPORTED"
    if "support" in text:
        return "SUPPORTED"
    return text.upper()


def _ids(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        parts = [str(v) for v in value]
    else:
        parts = str(value).replace("\n", ",").replace(";", ",").split(",")
    return [p.strip().upper() for p in parts if p.strip()]


def _resolve(token: str, position: dict[str, int]) -> int | None:
    """Match a submitted identifier to a row. Zero padding is presentation,
    not chemistry, so CMP-7 and CMP-007 are the same compound."""
    if token in position:
        return position[token]
    digits = "".join(ch for ch in token if ch.isdigit())
    if digits:
        padded = f"CMP-{int(digits):03d}"
        if padded in position:
            return position[padded]
    return None


def verify(episode: Episode, submitted: dict | None,
           workspace: Path) -> Verdict:
    import numpy as np

    order = ["series_count", "holdout_set", "honest_number", "verdict"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, order[0])

    # The shipped bytes are authoritative. run_python can rewrite anything in
    # the workspace, so the truth is re-derived from what the generator
    # emitted and the workspace copy is only compared against it.
    shipped = episode.files["assay_data.csv"]
    local = workspace / "assay_data.csv"
    try:
        detail["workspace_unmodified"] = (
            local.read_text(encoding="utf-8") == shipped
            if local.exists() else None)
    except OSError:
        detail["workspace_unmodified"] = None

    rows = _parse_csv(shipped)
    ids = [r["compound_id"].strip().upper() for r in rows]
    smiles = [r["smiles"].strip() for r in rows]
    y = np.asarray([int(r["activity"]) for r in rows])
    position = {cid: i for i, cid in enumerate(ids)}

    scaffolds = _scaffolds(smiles)
    n_series_murcko = len(set(scaffolds))
    n_series_generic = len(set(_generic_scaffolds(smiles)))
    n_pos, n_neg = int(y.sum()), int(len(y) - y.sum())
    feasible = (len(rows) >= MIN_ROWS and n_series_murcko >= MIN_SERIES
                and n_pos >= MIN_PER_CLASS and n_neg >= MIN_PER_CLASS)
    detail.update({"n_rows": len(rows), "n_series_recomputed": n_series_murcko,
                   "n_series_generic": n_series_generic, "n_active": n_pos,
                   "n_inactive": n_neg, "feasible_recomputed": feasible})

    given_series = _field(submitted, "n_series")
    try:
        checks["series_count"] = int(given_series) in {n_series_murcko,
                                                       n_series_generic}
    except (TypeError, ValueError):
        checks["series_count"] = False
    detail["n_series_given"] = given_series

    given_ids = _field(submitted, "holdout_compound_ids")
    given_auc = _field(submitted, "holdout_auc")
    status = _status(_field(submitted, "claim_status"))
    detail["claim_status_given"] = status

    if not feasible:
        # The refusal has to be written down in each place a number was asked
        # for; a field left blank is silence, and silence fails here too.
        checks["holdout_set"] = _explicit_abstention(given_ids)
        checks["honest_number"] = _explicit_abstention(given_auc)
        checks["verdict"] = status == "CANNOT_DETERMINE"
        detail["expected_status"] = "CANNOT_DETERMINE"
        detail["why"] = (f"rows={len(rows)} series={n_series_murcko} "
                         f"actives={n_pos} inactives={n_neg}: no cross-series "
                         "holdout with any resolution exists")
        first = next((c for c in order if not checks[c]), None)
        return Verdict(all(checks.values()), checks, detail, first)

    X = _fp_matrix(smiles)

    # Is the submitted holdout actually free of the training chemistry?
    picked = _ids(given_ids)
    resolved = {p: _resolve(p, position) for p in picked}
    unknown = [p for p, index in resolved.items() if index is None]
    test_idx = sorted({index for index in resolved.values()
                       if index is not None})
    chosen = set(test_idx)
    train_idx = [i for i in range(len(rows)) if i not in chosen]
    fraction = len(test_idx) / len(rows)
    test_scaf = {scaffolds[i] for i in test_idx}
    train_scaf = {scaffolds[i] for i in train_idx}
    disjoint = not (test_scaf & train_scaf)
    both_classes = (bool(test_idx) and len(set(y[test_idx].tolist())) == 2
                    and bool(train_idx)
                    and len(set(y[train_idx].tolist())) == 2)
    checks["holdout_set"] = bool(
        picked and not unknown
        and HOLDOUT_MIN_FRACTION <= fraction <= HOLDOUT_MAX_FRACTION
        and disjoint and both_classes and len(train_scaf) >= MIN_SERIES)
    detail.update({"holdout_n": len(test_idx),
                   "holdout_fraction": round(fraction, 3),
                   "unknown_ids": unknown[:5], "scaffold_disjoint": disjoint,
                   "holdout_series": len(test_scaf),
                   "train_series": len(train_scaf),
                   "both_classes": both_classes})

    # Is the number the candidate reported the number that pipeline gives?
    if checks["holdout_set"]:
        recomputed = _auc(X, y, train_idx, test_idx)
        detail["holdout_auc_recomputed"] = (None if math.isnan(recomputed)
                                            else round(recomputed, 4))
        try:
            checks["honest_number"] = (
                not math.isnan(recomputed)
                and abs(float(given_auc) - recomputed) <= AUC_TOLERANCE)
        except (TypeError, ValueError):
            checks["honest_number"] = False
    detail["holdout_auc_given"] = given_auc

    # The verdict, re-derived from the shipped rows alone.
    reported_train = [i for i, r in enumerate(rows) if r["split"] == "train"]
    reported_holdout = [i for i, r in enumerate(rows)
                        if r["split"] == "holdout"]
    claimed = _auc(X, y, reported_train, reported_holdout)
    labels = {s: k for k, s in enumerate(sorted(set(scaffolds)))}
    grouped = _grouped_auc(X, y, [labels[s] for s in scaffolds])
    supported = bool(not math.isnan(claimed) and not math.isnan(grouped)
                     and (claimed - grouped) <= INFLATION_MARGIN)
    expected = "SUPPORTED" if supported else "NOT_SUPPORTED"
    checks["verdict"] = status == expected
    detail.update({"claimed_auc_recomputed": round(claimed, 4),
                   "grouped_auc_recomputed": round(grouped, 4),
                   "inflation": round(claimed - grouped, 4),
                   "expected_status": expected,
                   "key_expected_status": episode.key.get("expected_status")})

    first = next((c for c in order if not checks[c]), None)
    return Verdict(all(checks.values()), checks, detail, first)


# --------------------------------------------------------------- reference

def _series_holdout(smiles: list[str], scaffolds: list[str], y) -> list[int]:
    """Hold out whole chemical series, then make the partition answerable.

    The starting point is the repository's own scaffold split, which fills the
    held-out block with whole Bemis-Murcko groups. That block can land on one
    activity class only - in the leaked condition activity tracks the series,
    so a block of two series is often entirely active - and a one-class block
    has no ROC-AUC. Whole further groups are moved across until both sides
    carry both classes, which keeps every series intact on exactly one side.
    """
    from ..checks import scaffold_split

    _train, test = scaffold_split(smiles, test_fraction=HOLDOUT_TARGET_FRACTION,
                                  seed=0)
    by_scaffold = _groups_by_scaffold(scaffolds)
    held = {scaffolds[i] for i in test}
    n = len(smiles)
    cap = HOLDOUT_MAX_FRACTION * n

    def rows(keys) -> list[int]:
        return sorted(i for k in keys for i in by_scaffold[k])

    def carries(keys, label) -> bool:
        return any(y[i] == label for i in rows(keys))

    smallest_first = sorted(by_scaffold, key=lambda k: (len(by_scaffold[k]), k))

    # the held-out block must contain both classes, or it has no ROC-AUC
    for label in (1, 0):
        if carries(held, label):
            continue
        for key in smallest_first:
            if key in held or not carries([key], label):
                continue
            if len(rows(held)) + len(by_scaffold[key]) > cap:
                continue
            held.add(key)
            break

    # and so must what is left, or there is nothing to fit
    for label in (1, 0):
        outside = [k for k in by_scaffold if k not in held]
        if carries(outside, label):
            continue
        for key in sorted(held, key=lambda k: (len(by_scaffold[k]), k)):
            if len(held) > 2 and carries([key], label):
                held.discard(key)
                break

    # give series back until the fit still sees a range of chemistry
    for key in sorted(held, key=lambda k: (-len(by_scaffold[k]), k)):
        if len(by_scaffold) - len(held) >= MIN_SERIES:
            break
        held.discard(key)
    return rows(held)


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make.

    Every graded quantity is re-derived here the way the verifier re-derives
    it - the series are counted from the shipped structures, the held-out set
    is built out of whole scaffold groups, and the score is the model card's
    own pipeline fit on what is left. The key supplies only what the rows
    alone cannot say: whether a cross-series estimate is worth reporting at
    all. If the key and the recomputation ever disagree, B8 fails loudly
    rather than the disagreement being papered over.
    """
    import numpy as np

    key = episode.key
    rows = _parse_csv(episode.files["assay_data.csv"])
    ids = [r["compound_id"].strip().upper() for r in rows]
    smiles = [r["smiles"].strip() for r in rows]
    y = np.asarray([int(r["activity"]) for r in rows])
    scaffolds = _scaffolds(smiles)
    n_series = len(set(scaffolds))

    if not key["feasible"]:
        # One series, or too few rows and actives for any held-out block to
        # resolve anything: the honest report is that this set carries no
        # generalisation estimate. Written down, not left blank.
        return {"n_series": n_series,
                "holdout_compound_ids": "cannot_determine",
                "holdout_auc": "cannot_determine",
                "claim_status": "CANNOT_DETERMINE",
                "conf_n_series": 0.95, "conf_holdout_compound_ids": 0.9,
                "conf_holdout_auc": 0.9, "conf_claim_status": 0.85}

    test_idx = _series_holdout(smiles, scaffolds, y)
    train_idx = [i for i in range(len(rows)) if i not in set(test_idx)]
    fraction = len(test_idx) / len(rows)
    if not (HOLDOUT_MIN_FRACTION <= fraction <= HOLDOUT_MAX_FRACTION
            and len(set(y[test_idx].tolist())) == 2
            and len(set(y[train_idx].tolist())) == 2
            and len({scaffolds[i] for i in train_idx}) >= MIN_SERIES):
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: no series-respecting "
            f"holdout exists (n={len(test_idx)} of {len(rows)}), so this "
            "instance is not solvable as built")

    auc = _auc(_fp_matrix(smiles), y, train_idx, test_idx)
    if math.isnan(auc):
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: the model-card pipeline "
            "yields no score on a series-respecting holdout")

    return {"n_series": n_series,
            "holdout_compound_ids": ",".join(ids[i] for i in test_idx),
            "holdout_auc": round(auc, 4),
            "claim_status": key["expected_status"],
            "conf_n_series": 0.95, "conf_holdout_compound_ids": 0.85,
            "conf_holdout_auc": 0.85, "conf_claim_status": 0.8}


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
