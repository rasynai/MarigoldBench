"""Family: audit a performance claim that is defended by a real number.

The collaborator critique of the first batch (analysis/collab/hardening__gpt.md)
named the failure mode this family is built against: a "canonical audit recipe
with a conspicuous local defect" is executed reliably by frontier models,
because the recipe *is* the answer. A leakage audit is the most canonical
recipe in molecular ML - rank the columns by mutual information with the label,
strike the suspicious one, refit - so the family is constructed so that the
recipe fires with full force in EVERY condition and is right in only one of
them.

The engine is a single column (the "carrier") whose behaviour inside
`train_set.csv` is statistically IDENTICAL in the sound and the defective
world. In both worlds it is the top-ranked column by mutual information, it
separates the training labels almost perfectly, and its conditional
distribution given the label is drawn from the same law. Nothing measured
inside the training table can tell the two apart. What differs is whether that
relationship is a property of the compounds or a property of the file:

  * sound world - the carrier is a measurement of the same physical quantity
    that drives the endpoint, so its relation to the outcome reappears in an
    independently run campaign and in the batch awaiting triage;
  * defective world - the carrier was written back from the call, so it is a
    label echo: same law given the label inside the file, no relation to the
    outcome anywhere else.

So four superficially adequate analyses of the same workspace imply three
different decisions:

  A  reproduce the reported random-split number      -> deploy
  B  strike the top mutual-information column, refit -> do not deploy
  C  score the reported model on the whole earlier
     labelled campaign                               -> deploy
  D  score it on the compounds of that campaign that
     were not also in the fit                        -> the truth

A is wrong whenever a leak exists. B is wrong whenever one does not - and it
fires just as hard there, because a genuine surrogate of the causal variable
looks exactly like a leak from inside one table. C is the subtle one: 30 of
the 72 rows of the "earlier campaign" are a verbatim re-export of training
rows in EVERY condition, and the report states they were not used in fitting,
so an evaluation that takes that sentence at face value inherits the leak it
was meant to detect and returns roughly 0.73 where the truth is near 0.60 -
outside the honesty band, and inflated by exactly the quantity under audit.
Only D is defensible, and only D is right in both worlds.

C0 and H1 therefore share the brief, the report, the chemistry columns, the
outcome column and the honest moderate covariate byte for byte; ONE column of
two files differs. The critique was explicit that byte-identical briefs are not
enough - a detectably different H1 workspace is readable without science - so
the row counts, column counts and decimal precision are fixed by construction
and the carrier's marginal and its joint with the label are matched between
conditions by drawing the echo from the sound world's own conditional law.

F2 carries two exact identities rather than a shortfall in data quality:

  1. `prior_call[i] == outcome[i]` for every labelled row, so a column in the
     report's own feature list IS the target under another name; combined with
     the report's deployment requirement - the score must be produced before
     any panel plate is run - the specification is mutually unsatisfiable,
     because the input the model needs does not exist until the value it is
     predicting has been measured.
  2. every compound id in `external_check.csv` also appears in
     `train_set.csv`, so the count of labelled rows that were not fitted is
     zero and no held-out number about this endpoint is estimable from what is
     supplied.

Both are checkable by the candidate and are re-checked by the verifier from
the shipped bytes; neither is an opinion about noise.

Nothing here is asserted. `verify` re-derives mutual information for every
column, re-fits the report's own recipe, scores it on the deduplicated unseen
rows, re-fits again without the column it independently judged
non-transferable, and only then compares those numbers with what was claimed.
`reference_submission` reaches its answer through the same helpers, so B8
proves the task is solvable from the workspace instead of from the key. The
estimator is hand-rolled in plain Python: a verifier whose numbers move with a
library release is not a verifier.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from ..families import Episode, Verdict

# --------------------------------------------------------------------- shape
# Fixed in every condition: filenames, row counts, column counts, precision.
N_TRAIN = 90
N_EXTERNAL = 72
N_EXTERNAL_REEXPORT = 30        # earlier-campaign rows that are training rows
N_PROSPECTIVE = 44

AUC_THRESHOLD = 0.80           # the report's own deployment rule
TOLERANCE = 0.08               # honesty band around a recomputed AUC

FEATURES = ["logp", "tpsa", "mw", "hbd", "rot_bonds", "fsp3", "basic_pka",
            "stock_conc_uM", "prior_call"]
# The two columns that can plausibly carry either role. One of them is the
# carrier for a given seed and the other is an honest moderate covariate, so
# no fixed column name is ever the answer.
CANDIDATES = ["stock_conc_uM", "prior_call"]
DUPLICATED = "prior_call"      # F2: the column that is the label verbatim

PRECISION = {"logp": 3, "tpsa": 1, "mw": 1, "hbd": 0, "rot_bonds": 0,
             "fsp3": 3, "basic_pka": 2, "stock_conc_uM": 2, "prior_call": 0,
             "outcome": 0}

ENDPOINTS = [
    ("CRU-PANEL-A", "hERG patch-clamp block at 10 uM"),
    ("CRU-PANEL-B", "cytochrome CYP3A4 time-dependent inhibition"),
    ("CRU-PANEL-C", "mitochondrial membrane depolarisation at 30 uM"),
    ("CRU-PANEL-D", "nuclear-receptor promiscuity flag"),
    ("CRU-PANEL-E", "aggregation-driven kinase inhibition"),
    ("CRU-PANEL-F", "HepG2 cytotoxicity at 50 uM"),
]

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "null",
           "no defensible value", "undefined"}
NO_COLUMN = ("none", "no column", "no_column", "nothing", "n_a", "n/a", "na",
             "null", "no leakage", "no leaking", "not applicable", "no feature",
             "no such column")


# ------------------------------------------------------------------ numerics

def _auc(scores: list[float], labels: list[int]) -> float:
    """Rank-based ROC-AUC with tie handling. Plain Python on purpose."""
    pairs = sorted(zip(scores, labels), key=lambda p: p[0])
    n = len(pairs)
    positives = sum(1 for _s, y in pairs if y == 1)
    negatives = n - positives
    if positives == 0 or negatives == 0:
        return float("nan")
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = shared
        i = j + 1
    rank_sum = sum(r for r, (_s, y) in zip(ranks, pairs) if y == 1)
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def _mutual_information(values: list[float], labels: list[int],
                        bins: int = 4) -> float:
    """I(feature; label) in nats, on equal-count bins of the feature.

    The canonical first move of a leakage audit, recomputed here so the family
    can show what that move sees: it ranks the carrier first in BOTH worlds.
    """
    n = len(values)
    if n == 0:
        return 0.0
    order = sorted(range(n), key=lambda i: values[i])
    edges = [order[int(round(k * n / bins)):int(round((k + 1) * n / bins))]
             for k in range(bins)]
    joint: dict[tuple[int, int], int] = {}
    for b, idx in enumerate(edges):
        for i in idx:
            joint[(b, labels[i])] = joint.get((b, labels[i]), 0) + 1
    px: dict[int, float] = {}
    py: dict[int, float] = {}
    for (b, y), count in joint.items():
        px[b] = px.get(b, 0.0) + count / n
        py[y] = py.get(y, 0.0) + count / n
    total = 0.0
    for (b, y), count in joint.items():
        pxy = count / n
        total += pxy * math.log(pxy / (px[b] * py[y]))
    return total


def _fit_logistic(rows: list[list[float]], labels: list[int],
                  l2: float = 1.0, iterations: int = 600,
                  lr: float = 0.8) -> tuple:
    """L2 logistic regression on standardised columns, full-batch gradient.

    Deterministic and dependency-free: the same bytes always produce the same
    number, which is the only property a scorer needs from an estimator.
    """
    n = len(rows)
    d = len(rows[0]) if n else 0
    mean = [sum(r[j] for r in rows) / n for j in range(d)]
    sd = []
    for j in range(d):
        var = sum((r[j] - mean[j]) ** 2 for r in rows) / n
        sd.append(math.sqrt(var) if var > 1e-12 else 1.0)
    z = [[(r[j] - mean[j]) / sd[j] for j in range(d)] for r in rows]
    w = [0.0] * d
    b = 0.0
    for _ in range(iterations):
        gw = [0.0] * d
        gb = 0.0
        for zi, yi in zip(z, labels):
            t = b + sum(w[j] * zi[j] for j in range(d))
            p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, t))))
            err = p - yi
            gb += err
            for j in range(d):
                gw[j] += err * zi[j]
        b -= lr * gb / n
        for j in range(d):
            w[j] -= lr * (gw[j] / n + l2 * w[j] / n)
    return mean, sd, w, b


def _score(model: tuple, rows: list[list[float]]) -> list[float]:
    mean, sd, w, b = model
    out = []
    for r in rows:
        out.append(b + sum(w[j] * (r[j] - mean[j]) / sd[j]
                           for j in range(len(w))))
    return out


# ------------------------------------------------------------------ tables

def _format(row: dict) -> str:
    parts = [str(row["compound_id"])]
    for name in FEATURES + ["outcome"]:
        if name not in row:
            continue
        places = PRECISION[name]
        value = row[name]
        parts.append(str(int(round(value))) if places == 0
                     else format(float(value), "." + str(places) + "f"))
    return ",".join(parts)


def _table(rows: list[dict], with_outcome: bool = True) -> str:
    header = ["compound_id"] + FEATURES + (["outcome"] if with_outcome else [])
    body = []
    for row in rows:
        clean = dict(row)
        if not with_outcome:
            clean.pop("outcome", None)
        body.append(_format(clean))
    return ",".join(header) + "\n" + "\n".join(body) + "\n"


def _parse(text: str) -> list[dict]:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return []
    header = [h.strip() for h in lines[0].split(",")]
    rows = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != len(header):
            continue
        row: dict = {}
        for name, raw in zip(header, parts):
            if name == "compound_id":
                row[name] = raw
                continue
            try:
                row[name] = float(raw)
            except ValueError:
                row[name] = float("nan")
        rows.append(row)
    return rows


# ------------------------------------------------------------------ generator

def _chemistry(rng: random.Random) -> dict:
    return {
        "logp": round(rng.gauss(2.9, 1.05), 3),
        "tpsa": round(rng.gauss(80.0, 20.0), 1),
        "mw": round(rng.gauss(392.0, 55.0), 1),
        "hbd": float(rng.randrange(0, 5)),
        "rot_bonds": float(rng.randrange(1, 10)),
        "fsp3": round(rng.uniform(0.10, 0.70), 3),
        "basic_pka": round(rng.gauss(7.6, 1.7), 2),
    }


# Coefficients on standardised descriptors. Deliberately moderate: the
# chemistry alone lands well below the deployment threshold, which is what
# makes the carrier decide the go/no-go in both directions.
_BETA = {"logp": 0.55, "basic_pka": 0.50, "tpsa": -0.35, "fsp3": 0.20}
_CENTRE = {"logp": (2.9, 1.05), "basic_pka": (7.6, 1.7), "tpsa": (80.0, 20.0),
           "fsp3": (0.40, 0.173)}
_LABEL_NOISE = 2.95            # tuned so the honest model sits well under 0.80


def _latent(chem: dict, rng: random.Random) -> tuple[float, int]:
    z = 0.0
    for name, beta in _BETA.items():
        centre, scale = _CENTRE[name]
        z += beta * (chem[name] - centre) / scale
    u = z + rng.gauss(0.0, _LABEL_NOISE)
    return u, (1 if u > 0.0 else 0)


def _u_scale() -> float:
    signal = math.sqrt(sum(b * b for b in _BETA.values()))
    return math.sqrt(signal * signal + _LABEL_NOISE * _LABEL_NOISE)


def _carrier_honest(name: str, u: float, rng: random.Random,
                    strong: bool) -> float:
    """A measurement of the same latent quantity that drives the outcome.

    `strong` is a surrogate good enough to carry the claim; otherwise it is an
    ordinary moderate covariate. Both are legitimate and both reappear in any
    other campaign on the same compounds.
    """
    scaled = u / _u_scale()
    if name == "stock_conc_uM":
        # The strong form is a good read-back of the dissolved state; the
        # moderate form is a poor one. Both are measurements of the compound,
        # so both survive into any other campaign on the same compounds.
        slope, jitter = (2.4, 0.85) if strong else (0.45, 1.6)
        value = 6.0 - slope * scaled + rng.gauss(0.0, jitter)
        return round(min(10.0, max(0.4, value)), 2)
    noise = 0.26 if strong else 3.20
    return float(1 if scaled + rng.gauss(0.0, noise) > 0.0 else 0)


def _carrier_echo(name: str, outcome: int, rng: random.Random) -> float:
    """A value written back from the call.

    Drawn from the sound world's OWN conditional law given the outcome, so the
    column's marginal and its joint with the label match the sound world to
    within sampling noise. What it no longer has is any tie to the compound.
    """
    if name == "stock_conc_uM":
        half = abs(rng.gauss(0.0, 1.0))
        scaled = half if outcome == 1 else -half
        value = 6.0 - 2.4 * scaled + rng.gauss(0.0, 0.85)
        return round(min(10.0, max(0.4, value)), 2)
    return float(outcome if rng.random() > 0.06 else 1 - outcome)


def _force_disagreement(rows: list[dict], name: str, rng: random.Random,
                        minimum: int = 3) -> None:
    """Keep a binary covariate from becoming an exact copy of the label.

    A 7% flip rate leaves a real chance of zero flips in 90 draws, and an
    accidental identity would collide with the F2 witness. The F2 identity has
    to be the only identity in the family.
    """
    if name != "prior_call":
        return
    disagreeing = [i for i, r in enumerate(rows) if r[name] != r["outcome"]]
    pool = [i for i in range(len(rows)) if i not in disagreeing]
    rng.shuffle(pool)
    while len(disagreeing) < minimum and pool:
        i = pool.pop()
        rows[i][name] = 1.0 - rows[i]["outcome"]
        disagreeing.append(i)


def _balance_carrier(rows: list[dict], name: str, rng: random.Random) -> None:
    """Permute a carrier column among rows until it carries no signal.

    Used on the rows of the earlier campaign that were never fitted. A
    permutation leaves the column's marginal untouched, so the file cannot be
    read by its summary statistics; what it removes is the accident that an
    echo drawn independently of the label still separates 24 rows by luck.
    """
    values = [r[name] for r in rows]
    labels = [int(r["outcome"]) for r in rows]
    if len(set(labels)) < 2:
        return
    best = None
    for _ in range(400):
        rng.shuffle(values)
        score = _auc(values, labels)
        gap = abs(score - 0.5)
        if best is None or gap < best[0]:
            best = (gap, list(values))
        if gap <= 0.05:
            break
    for row, value in zip(rows, best[1]):
        row[name] = value


def build(seed: int, condition: str) -> Episode:
    # Anything the candidate can read is drawn from a condition-free stream, so
    # the report and the brief are byte-identical across conditions by
    # construction rather than by inspection.
    rng_visible = random.Random(4_100_000 + seed)
    # Shared world: chemistry, latent state, outcome, honest covariate. C0 and
    # H1 differ ONLY in the carrier column, drawn from its own stream.
    rng_world = random.Random(4_200_000 + seed)
    rng_carrier = random.Random(4_300_000 + seed)

    panel, endpoint = ENDPOINTS[seed % len(ENDPOINTS)]
    claimed_auc = round(rng_visible.uniform(0.92, 0.95), 2)
    carrier = CANDIDATES[seed % len(CANDIDATES)]
    other = [c for c in CANDIDATES if c != carrier][0]

    # One registry namespace for every compound in the programme. Ids that
    # advertised which file a row came from would give the overlap away by
    # eye; a registry id does not know that, so finding the re-exported rows
    # means intersecting the two id sets.
    next_id = [4_0000]

    def make_rows(count: int, labelled: bool) -> list[dict]:
        rows = []
        for _ in range(count):
            chem = _chemistry(rng_world)
            u, outcome = _latent(chem, rng_world)
            row = dict(chem)
            row["compound_id"] = f"CRU-{next_id[0]}"
            next_id[0] += 1
            row["outcome"] = float(outcome)
            row[other] = _carrier_honest(other, u, rng_world, strong=False)
            if condition == "F2":
                # The duplicated column is the label verbatim; the remaining
                # candidate stays an ordinary moderate covariate.
                remaining = [c for c in CANDIDATES if c != DUPLICATED][0]
                row[remaining] = _carrier_honest(remaining, u, rng_world,
                                                 strong=False)
                row[DUPLICATED] = float(outcome)
            elif condition == "H1":
                row[carrier] = _carrier_echo(carrier, outcome, rng_carrier)
            else:
                row[carrier] = _carrier_honest(carrier, u, rng_carrier,
                                               strong=True)
            if not labelled:
                # Nothing has been called yet, so an echo has nothing to echo:
                # the carrier is whatever the pre-panel record actually holds.
                if condition == "H1":
                    row[carrier] = _carrier_echo(
                        carrier, rng_carrier.randrange(2), rng_carrier)
            rows.append(row)
        return rows

    train = make_rows(N_TRAIN, labelled=True)
    if condition != "F2":
        # Only F2 may contain a column identical to the label, so the binary
        # covariates elsewhere are held off that boundary by construction.
        _force_disagreement(train, other, rng_world)
        _force_disagreement(train, carrier, rng_carrier)

    fresh_count = 0 if condition == "F2" else N_EXTERNAL - N_EXTERNAL_REEXPORT
    fresh = make_rows(fresh_count, labelled=True)
    if condition != "F2":
        _force_disagreement(fresh, other, rng_world, minimum=2)
    if condition == "H1" and fresh:
        # The echo has no purchase on compounds this file never called: the
        # column is drawn from the same law but is unrelated to the outcome.
        _balance_carrier(fresh, carrier, rng_carrier)

    reexport_count = (N_EXTERNAL if condition == "F2"
                      else N_EXTERNAL_REEXPORT)
    indices = list(range(N_TRAIN))
    rng_world.shuffle(indices)
    reexport = [dict(train[i]) for i in indices[:reexport_count]]
    external = reexport + fresh
    order = list(range(len(external)))
    rng_world.shuffle(order)
    external = [external[i] for i in order]

    prospective = make_rows(N_PROSPECTIVE, labelled=False)

    report = [
        f"# Model report  {panel}  /  {endpoint}",
        "",
        "## Data",
        f"train_set.csv: {N_TRAIN} compounds with a recorded {endpoint} call in",
        "the `outcome` column (1 = called, 0 = not called).",
        f"external_check.csv: {N_EXTERNAL} compounds with recorded calls for the",
        "same endpoint from an earlier campaign on the same panel. Not used in",
        "fitting.",
        f"prospective_batch.csv: {N_PROSPECTIVE} registered compounds awaiting",
        "triage. These are the compounds the model would be applied to.",
        "",
        "## Model",
        "L2-regularised logistic regression on standardised columns.",
        "Feature list, in order:",
        "  " + ", ".join(FEATURES),
        "",
        "## Reported performance",
        "Split: random 80/20 partition of train_set.csv.",
        f"Held-out ROC-AUC: {claimed_auc:.2f}",
        "",
        "## Deployment",
        "The score must be produced from the compound registration record",
        "before any panel plate is run for that compound.",
        "Decision rule: deploy for prospective triage only if the held-out",
        f"ROC-AUC is at least {AUC_THRESHOLD:.2f}.",
    ]

    files = {
        "train_set.csv": _table(train),
        "external_check.csv": _table(external),
        "prospective_batch.csv": _table(prospective, with_outcome=False),
        "model_report.md": "\n".join(report) + "\n",
    }

    brief = (
        f"A modelling group has asked to deploy the triage model described in "
        f"model_report.md for {endpoint}. The table it was fitted on, an "
        f"earlier labelled campaign on the same panel, and the batch it would "
        f"be applied to are attached.\n\n"
        f"Report the performance you would defend for this model in the use "
        f"the report describes, and whether it clears the report's own rule.\n\n"
        "Submit these fields:\n"
        "- honest_auc: the ROC-AUC you would defend as this model's "
        "performance on compounds it has not been fitted on, as a number, or "
        "the string cannot_determine if no defensible value exists\n"
        "- leaking_feature: the name of the one column whose presence in the "
        "report's feature list makes the reported number unsound, or the "
        "string none if no column does\n"
        "- deploy: YES or NO\n"
        "- evidence: what your number rests on, in your own words\n"
        "and conf_<field> in [0,1] for each.")

    key = {
        "condition": condition,
        "panel": panel,
        "endpoint": endpoint,
        "carrier": carrier,
        "honest_covariate": other,
        "claimed_auc": claimed_auc,
        "threshold": AUC_THRESHOLD,
        "leak_planted": condition == "H1",
        "duplicated_column": DUPLICATED if condition == "F2" else None,
        "determinable": condition != "F2",
        "reexported_rows": reexport_count,
    }
    # 26 calls: read four files, rank the columns, fit the report's recipe,
    # join the two labelled tables on compound id, refit and re-score. Enough
    # room for the audit to be revised once its first answer is checked.
    return Episode("feature-leakage-audit", seed, condition, brief, files, key,
                   budget=26,
                   checkpoints=["leakage_call", "honest_metric", "decision",
                                "evidence"])


# --------------------------------------------------------------- re-derivation

def _matrix(rows: list[dict], columns: list[str]) -> list[list[float]]:
    return [[row[c] for c in columns] for row in rows]


def _analyse(train: list[dict], external: list[dict]) -> dict:
    """Re-derive every judgment the episode turns on from the shipped tables.

    Shared by `verify` and `reference_submission` so the reference cannot
    answer from anything the candidate does not also have.
    """
    out: dict = {}
    labels = [int(r["outcome"]) for r in train]
    out["n_train"] = len(train)
    out["class_balance"] = round(sum(labels) / max(len(labels), 1), 3)

    # 1. The canonical audit move, recomputed so the record shows what it sees.
    out["mutual_information"] = {
        name: round(_mutual_information([r[name] for r in train], labels), 4)
        for name in FEATURES}
    out["mi_rank"] = sorted(FEATURES, key=lambda n: -out["mutual_information"][n])

    # 2. Exact identities. A feature that equals the label on every labelled
    # row is the label under another name, and that is a fact, not a p-value.
    identities = []
    for name in FEATURES:
        if all(int(r[name]) == int(r["outcome"]) and float(r[name]) in (0.0, 1.0)
               for r in train) and all(
                   int(r[name]) == int(r["outcome"]) and float(r[name]) in (0.0, 1.0)
                   for r in external):
            identities.append(name)
    out["label_identities"] = identities

    # 3. How much of the "independent" campaign is a re-export of the fit.
    train_ids = {r["compound_id"] for r in train}
    unseen = [r for r in external if r["compound_id"] not in train_ids]
    out["external_rows"] = len(external)
    out["external_unseen_rows"] = len(unseen)
    out["external_reexported_rows"] = len(external) - len(unseen)

    if identities and not unseen:
        # F2: the target is an input AND nothing labelled was left out of the
        # fit. Both legs are exact; no held-out number exists to be estimated.
        out["determinable"] = False
        out["duplicated_column"] = identities[0]
        out["non_transferable"] = identities[0]
        out["honest_auc_reported_model"] = None
        out["honest_auc_reduced_model"] = None
        out["expected_deploy"] = "NO"
        return out
    out["determinable"] = True
    out["duplicated_column"] = None

    # 4. Does each column's separation of the label survive into compounds the
    # fit never saw? A surrogate of the causal variable does; an echo does not.
    transfer = {}
    for name in FEATURES:
        inside = _auc([r[name] for r in train], labels)
        inside = max(inside, 1.0 - inside)
        outside = _auc([r[name] for r in unseen],
                       [int(r["outcome"]) for r in unseen])
        if outside == outside:                      # not NaN
            outside = max(outside, 1.0 - outside)
        transfer[name] = (round(inside, 3),
                          None if outside != outside else round(outside, 3))
    out["separation_train_vs_unseen"] = transfer
    suspects = [(inside - outside, name) for name, (inside, outside)
                in transfer.items() if outside is not None
                and inside >= 0.78 and inside - outside >= 0.20]
    suspects.sort(reverse=True)
    out["non_transferable"] = suspects[0][1] if suspects else None

    # 5. The two defensible numbers: the report's own model scored on unseen
    # compounds, and the same recipe refitted without the column that does not
    # transfer. Both are recomputed; neither is read from a key.
    model = _fit_logistic(_matrix(train, FEATURES), labels)
    unseen_labels = [int(r["outcome"]) for r in unseen]
    out["honest_auc_reported_model"] = round(
        _auc(_score(model, _matrix(unseen, FEATURES)), unseen_labels), 4)
    out["naive_auc_whole_external"] = round(
        _auc(_score(model, _matrix(external, FEATURES)),
             [int(r["outcome"]) for r in external]), 4)

    reduced = [f for f in FEATURES if f != out["non_transferable"]]
    reduced_model = _fit_logistic(_matrix(train, reduced), labels)
    out["honest_auc_reduced_model"] = round(
        _auc(_score(reduced_model, _matrix(unseen, reduced)), unseen_labels), 4)

    decisive = out["honest_auc_reduced_model"]
    out["expected_deploy"] = "YES" if decisive >= AUC_THRESHOLD else "NO"
    return out


def _tables(episode: Episode, workspace: Path) -> tuple[list[dict], list[dict], dict]:
    """Re-derive from the bytes that were SHIPPED, and note any that moved.

    The workspace is writable by the system under test and nothing in this
    family asks it to produce a file there, so grading against the on-disk copy
    would let a candidate improve its score by editing the evidence. The
    shipped bytes are the evidence; the on-disk copies are compared to them and
    any divergence is recorded rather than scored on.
    """
    edited = {}
    for name in ("train_set.csv", "external_check.csv"):
        try:
            path = Path(workspace) / name
            if path.exists():
                edited[name] = path.read_text(encoding="utf-8") != episode.files[name]
        except OSError:
            edited[name] = None
    return (_parse(episode.files["train_set.csv"]),
            _parse(episode.files["external_check.csv"]),
            edited)


# ---------------------------------------------------------------- text checks

# Phrases that mention a conclusion only to rule it out. Removed by plain
# literal replacement, longest first: a regex for exactly this job passed in
# isolation and matched nothing in situ, and a scoring rule that cannot be
# checked by eye is a liability.
NEGATED = (
    "no evidence of label leakage", "no evidence of leakage",
    "no sign of label leakage", "no sign of leakage", "without any leakage",
    "no label leakage", "not label leakage", "no target leakage",
    "without leakage", "no leakage", "not leakage", "not leaking",
    "no leaking", "not a leak", "no leak", "is not leaked", "not leaked",
    "does not leak", "do not leak", "nothing is leaking",
    "not an echo", "no echo", "is not an echo of", "not a copy of",
    "not inflated", "is not inflated", "no inflation", "not contaminated",
    "no contamination", "not in-sample", "not an artifact", "not an artefact",
    "does not encode", "do not encode", "not encoded", "not encoding",
    "no duplicate", "not duplicated", "no duplication", "not a duplicate",
    "not identical to the outcome", "not identical to the label",
    "not downstream of", "is not downstream",
    "does not hold up", "does not hold", "do not hold", "did not hold",
    "not supported", "is not supported", "not legitimate", "not genuine",
    "does not survive", "did not survive", "does not reproduce",
    "not reproduced", "does not reproduce", "not confirmed",
    "does not stand", "do not stand", "does not carry over",
    "not carry over", "does not transfer to", "does not transfer",
    "do not transfer", "did not transfer", "fails to transfer",
    "not transferable", "no transfer",
)

LEAK_WORDS = ("leak", "echo", "written back", "read back", "encodes",
              "encoding of the outcome", "downstream", "inflat", "in-sample",
              "in sample", "contaminat", "memoris", "memoriz", "tautolog",
              "duplicat", "copy of the outcome", "copy of the label",
              "identical to the outcome", "identical to the label",
              "function of the outcome", "function of the label",
              "same as the outcome", "derived from the outcome",
              "derived from the call", "after the call", "post hoc",
              "does not transfer", "no relation to the outcome",
              "unrelated to the outcome", "no signal on the unseen",
              "artifact of the file", "artefact of the file")

SOUND_WORDS = ("transfers", "carries over", "hold", "stands", "reproduc",
               "supported", "genuine", "legitimate", "survive", "confirm",
               "same relation", "consistent with the earlier",
               "also separates", "separates the unseen", "real predictor",
               "physically", "causal", "surrogate")

# Deliberately narrow. "held-out" and "not used in fitting" are what the
# report itself says, so accepting them would let a submission that never
# looked at the two id sets score for defending the claim it was handed - and
# that submission is the naive path this family exists to reject.
UNSEEN_WORDS = ("unseen", "never fitted", "never in the fit", "not part of the fit",
                "not in the training set", "not in train_set", "not in the fit",
                "outside the training set", "deduplicat", "de-duplicat",
                "duplicate compound", "duplicated compound", "overlap",
                "re-export", "reexport", "appear in both", "appears in both",
                "present in both", "in both files", "also in train",
                "already in train", "already in the training",
                "shared compound", "shared id", "common compound", "disjoint",
                "unique to", "not among the training compounds",
                "excluded the training compounds",
                "after removing the training compounds")

IDENTITY_WORDS = ("identical", "duplicat", "copy of the outcome",
                  "copy of the label", "same as the outcome",
                  "same values as the outcome", "equals the outcome",
                  "equal to the outcome", "is the outcome", "is the label",
                  "relabel", "re-label", "verbatim", "tautolog", "one-to-one")

NO_HOLDOUT_WORDS = ("every row", "all rows", "every compound", "all compounds",
                    "no unseen", "no independent", "not independent",
                    "already in the training", "already in train",
                    "subset of the training", "subset of train",
                    "contained in the training", "appear in the training",
                    "appears in the training", "re-export", "reexport",
                    "verbatim", "zero rows", "no held-out", "no holdout",
                    "nothing was held out", "entirely a", "wholly a")

# A refusal that also asserts the claim is fine is not a refusal, it is a bet
# on both outcomes. Narrow on purpose: these are assertions about the claim,
# not the vocabulary a correct refusal reaches for.
CLAIM_UPHELD = ("claim stands", "claim holds", "claim is supported",
                "claim survives", "claim is sound", "claim is defensible",
                "number stands", "number holds", "number is supported",
                "number is sound", "auc stands", "auc holds", "probably stands",
                "may well be genuine", "is genuine", "relation is genuine",
                "is legitimate", "report is right", "report is correct",
                "should be deployed", "safe to deploy")


def _strip_negated(text: str) -> str:
    """Kept for callers that want the text; the matcher below does the work."""
    from ..freetext import decided
    return decided(text, SOUND_WORDS + LEAK_WORDS)


def _says(text: str, vocabulary) -> bool:
    """CORR-015: the old substring test fired on the report's own nouns, so
    "the holdout set shares scaffolds with training" counted as a claim that
    the result holds. Boundary matching plus generative negation, tested in
    tests/test_freetext.py."""
    from ..freetext import asserts
    return asserts(text, vocabulary)


def _names_column(text: str, column: str) -> bool:
    lowered = str(text or "").lower()
    target = column.lower()
    return target in lowered or target.replace("_", " ") in lowered


def _named_columns(text: str) -> list[str]:
    """Which of the report's own feature names a short answer mentions.

    The field asks for one column, so an answer that hedges across two is not
    an answer; comparing the whole list rather than testing membership is what
    makes that fail.
    """
    return [name for name in FEATURES if _names_column(text, name)]


# ------------------------------------------------------------------ verifier

def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    checks = {"leakage_call": False, "honest_metric": False,
              "decision": False, "evidence": False}
    detail: dict = {}
    order = ["leakage_call", "honest_metric", "decision", "evidence"]
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "leakage_call")

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    train, external, edited = _tables(episode, workspace)
    found = _analyse(train, external)
    detail["workspace_copies_edited"] = edited
    detail["recomputed"] = {k: v for k, v in found.items()
                            if k != "separation_train_vs_unseen"}
    detail["separation_train_vs_unseen"] = found["separation_train_vs_unseen"] \
        if "separation_train_vs_unseen" in found else None
    detail["key_condition"] = episode.key["condition"]

    raw_auc = str(field("honest_auc") or "").strip().lower()
    abstained = raw_auc in ABSTAIN
    column_raw = str(field("leaking_feature") or "").strip()
    column_text = column_raw.lower()
    deploy = str(field("deploy") or "").strip().upper()
    evidence_raw = str(field("evidence") or "")
    evidence = _strip_negated(evidence_raw)
    detail["given"] = {"honest_auc": str(field("honest_auc"))[:40],
                       "leaking_feature": column_raw[:60],
                       "deploy": deploy[:12],
                       "evidence": evidence_raw[:240]}

    if not found["determinable"]:
        # F2. The refusal has to be stated and it has to be ABOUT the two
        # identities: silence scores zero here exactly as it does elsewhere.
        duplicated = found["duplicated_column"]
        checks["leakage_call"] = _named_columns(column_text) == [duplicated]
        checks["honest_metric"] = abstained
        checks["decision"] = abstained and deploy == "NO"
        checks["evidence"] = (abstained
                              and _names_column(evidence, duplicated)
                              and _says(evidence, IDENTITY_WORDS)
                              and _says(evidence, NO_HOLDOUT_WORDS)
                              and not _says(evidence, CLAIM_UPHELD))
        detail["expected"] = {
            "leaking_feature": duplicated,
            "honest_auc": "cannot_determine",
            "deploy": "NO",
            "witness": {
                "identity": f"{duplicated}[i] == outcome[i] on every labelled row",
                "no_holdout": (f"{found['external_unseen_rows']} of "
                               f"{found['external_rows']} external rows were "
                               "not already in train_set.csv"),
            },
        }
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    suspect = found["non_transferable"]
    honest_reported = found["honest_auc_reported_model"]
    honest_reduced = found["honest_auc_reduced_model"]
    expected_deploy = found["expected_deploy"]
    detail["expected"] = {
        "leaking_feature": suspect or "none",
        "honest_auc_reported_model": honest_reported,
        "honest_auc_reduced_model": honest_reduced,
        "deploy": expected_deploy,
        "naive_auc_whole_external": found["naive_auc_whole_external"],
        "claimed_auc": episode.key["claimed_auc"],
    }

    named = _named_columns(column_text)
    detail["named_columns"] = named
    if suspect is None:
        # A false alarm is a failure here: naming any column when none is a
        # label echo is the mutual-information recipe firing on a genuine
        # predictor, which is the trap this condition exists to set.
        checks["leakage_call"] = (not named) and _says(column_text, NO_COLUMN)
    else:
        checks["leakage_call"] = named == [suspect]

    # Honesty. Either defensible route is accepted, but the number has to be
    # one this workspace actually produces - a value that matches neither
    # recomputation is a reported result nobody can reproduce.
    accepted = [v for v in (honest_reported, honest_reduced) if v is not None]
    try:
        given = float(field("honest_auc"))
    except (TypeError, ValueError):
        given = None
    if given is None:
        checks["honest_metric"] = False
    else:
        checks["honest_metric"] = any(abs(given - v) <= TOLERANCE
                                      for v in accepted)
    detail["given_auc"] = given

    checks["decision"] = deploy == expected_deploy

    if suspect is None:
        # A sound claim has to be defended by the transfer it rests on, and
        # must not be hedged into an accusation of leakage at the same time.
        checks["evidence"] = (_says(evidence, SOUND_WORDS)
                              and not _says(evidence, LEAK_WORDS)
                              and _says(evidence, UNSEEN_WORDS))
    else:
        checks["evidence"] = (_names_column(evidence, suspect)
                              and _says(evidence, LEAK_WORDS)
                              and _says(evidence, UNSEEN_WORDS)
                              and not _says(evidence, SOUND_WORDS))
    detail["evidence_normalised"] = evidence[:240]

    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


# ------------------------------------------------------------------ reference

def reference_submission(episode: Episode) -> dict:
    """The submission a competent auditor would make.

    Reached through the same helpers the candidate must reach for - rank the
    columns, join the two labelled tables on compound id, refit, re-score - so
    B8 demonstrates the task is answerable from the shipped bytes rather than
    from the key.
    """
    train = _parse(episode.files["train_set.csv"])
    external = _parse(episode.files["external_check.csv"])
    found = _analyse(train, external)

    if not found["determinable"]:
        duplicated = found["duplicated_column"]
        return {
            "honest_auc": "cannot_determine",
            "leaking_feature": duplicated,
            "deploy": "NO",
            "evidence": (
                f"the column {duplicated} in the report's feature list takes "
                f"identical values to the outcome column on all "
                f"{found['n_train']} training rows and on every row of "
                f"external_check.csv, so it is the target under another name, "
                f"and the report requires the score before any panel plate is "
                f"run, which is the point at which that value does not yet "
                f"exist; every compound in external_check.csv already appears "
                f"verbatim in train_set.csv, so no labelled row was left out "
                f"of the fit and no held-out number about this endpoint is "
                f"estimable from what is supplied"),
            "conf_honest_auc": 0.9, "conf_leaking_feature": 0.95,
            "conf_deploy": 0.9, "conf_evidence": 0.9,
        }

    suspect = found["non_transferable"]
    unseen = found["external_unseen_rows"]
    reexported = found["external_reexported_rows"]
    if suspect is None:
        value = found["honest_auc_reduced_model"]
        best = max(found["separation_train_vs_unseen"].items(),
                   key=lambda item: item[1][0])
        return {
            "honest_auc": value,
            "leaking_feature": "none",
            "deploy": found["expected_deploy"],
            "evidence": (
                f"{reexported} of the {found['external_rows']} rows in "
                f"external_check.csv are re-exports of compounds that are "
                f"already in train_set.csv under the same compound_id, so only "
                f"the {unseen} unseen compounds carry information; scored "
                f"on those the report's model reaches "
                f"{found['honest_auc_reported_model']:.3f}. The column that "
                f"separates the training labels hardest, {best[0]}, also "
                f"separates the unseen compounds at {best[1][1]:.3f} against "
                f"{best[1][0]:.3f} inside the fit, so the same relation "
                f"transfers to compounds the fit never saw and the reported "
                f"number stands"),
            "conf_honest_auc": 0.8, "conf_leaking_feature": 0.85,
            "conf_deploy": 0.85, "conf_evidence": 0.85,
        }

    inside, outside = found["separation_train_vs_unseen"][suspect]
    return {
        "honest_auc": found["honest_auc_reduced_model"],
        "leaking_feature": suspect,
        "deploy": found["expected_deploy"],
        "evidence": (
            f"{suspect} separates the training labels at {inside:.3f} but "
            f"reaches only {outside:.3f} on the {unseen} unseen compounds of "
            f"external_check.csv, the ones whose compound_id is not in "
            f"train_set.csv, and it is "
            f"unrelated to the outcome there, so its apparent contribution is "
            f"a label echo written back into the training file rather than a "
            f"property of the compounds. {reexported} of the "
            f"{found['external_rows']} external rows are re-exports of "
            f"compounds already in the training table, which is why scoring "
            f"the whole file returns "
            f"{found['naive_auc_whole_external']:.3f}; on the unseen "
            f"compounds alone the report's model reaches "
            f"{found['honest_auc_reported_model']:.3f} and the same recipe "
            f"without {suspect} reaches "
            f"{found['honest_auc_reduced_model']:.3f}"),
        "conf_honest_auc": 0.8, "conf_leaking_feature": 0.9,
        "conf_deploy": 0.85, "conf_evidence": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
