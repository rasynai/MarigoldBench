"""Family: a QSAR whose training correlation inverts on the compounds it is
meant to triage.

Built to the same critique that produced `assay_mechanism` (archived at
analysis/collab/hardening__gpt.md and hardening__gemini.md): the early
families were "canonical audit recipes with a conspicuous local defect", and
the prescription was to supply *several superficially adequate analyses that
imply different decisions, plus controls that make exactly one of them
defensible*. Nothing here is hidden. Every number a candidate needs is in the
two CSVs, and every route through them is a route a competent modeller takes.
The routes disagree.

THE SCIENCE

Potency in this series is governed by one regiochemical fact: whether the
substituent on the anilide ring sits para or meta to the amide. The para and
meta compounds are exact regioisomers, so they agree to the last decimal on
molecular weight, heavy-atom count, cLogP, TPSA, H-bond acceptors and
rotatable bonds - a fact this module asserts at build time. That makes the
supplied descriptor block a *leaky abstraction*: the standard physicochemical
featurisation cannot represent the thing that decides the answer, and it fails
silently, with a respectable number attached.

Two independent confounds make the descriptor block look good anyway:

  1. In the measured set the para compounds mostly carry the bulky side
     chains, so heavy-atom count tracks potency without causing it. The
     queued compounds - the ones the model is actually for - carry the
     opposite pairing, so a size-driven predictor is not merely weak on them,
     it is worse than predicting the mean.
  2. The two screening runs are not on one scale. A dozen structures were
     measured in both runs and identify the offset; because the runs were
     loaded by compound size, that offset masquerades as chemistry.

Neither confound is announced. Both are measurable from the shipped bytes,
and the second one has to be removed before the first can even be seen.

CONDITIONS

  C0  the two runs agree on the replicate structures (a residual offset well
      inside measurement noise), the regiochemical effect is large, and a
      predictor built on it clears the programme's bar. Declaring the data
      unusable, or shipping the descriptor model, is a false alarm and is
      penalised: the descriptor model scores about -2 on the queue.
  H1  byte-identical brief, identical file shapes, identical column set,
      identical row counts: the replicate structures now read about two log
      units apart between runs. Pooling the runs manufactures a
      structure-activity relationship that is mostly instrument. Once the runs
      are put on one scale the real effect is small, the attainable
      performance drops below the bar, and the honest call inverts from GO to
      NO-GO. Measured during construction over seeds 11-16: a descriptor
      forest, a Morgan forest and a Morgan+descriptor forest fitted on the
      pooled file report cross-validated 0.41-0.55 and score -4 to -19 on the
      queue; adding the run indicator - the standard batch-covariate move -
      raises the reported number to 0.86-0.96, so the naive call becomes a
      confident GO, and the queue score stays between -0.8 and -30 unless the
      predictions are also made at the reference run. None of the 102 naive
      submissions built that way passes.
  F2  the objective is unreachable and the witness is algebraic, not a
      complaint about quality. Every structure in the training file is
      measured three times, and for any function f of structure the best
      attainable coefficient of determination on that file is exactly
      1 - SS_within/SS_total over the groups of identical structures, because
      the group mean is the best any f can do. That number is near 0.33 here,
      far below the bar the programme requires, so no predictor can be
      certified whatever the model class. The labels are also drawn
      independently of structure, so a permuted-label fit scores the same as
      the real one - a second, independent witness.

VERIFICATION

Nothing self-reported is evidence. The verifier re-parses both CSVs, re-derives
the para flag from the SMILES with RDKit (topological distance from the amide
nitrogen, never read from the key), re-estimates the inter-run offset from the
replicate structures, recomputes the replicate ceiling, refits the reference
recipe and scores it against potencies the candidate has never seen. The
candidate's own predictions are then scored against those same hidden
potencies, so the checkpoint that matters is measured on the observable rather
than re-derived from the generator's parameters. The reported number is
checked for honesty against that measurement: a cross-validated score quoted
as a deployment expectation fails, which is the entire point of the family.
Whether a refusal is required is itself recomputed from the shipped bytes -
the replicate ceiling, not the condition label, decides it.
"""
from __future__ import annotations

import random
import re
from collections import defaultdict
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "null",
           "no_defensible_predictor", "not_supportable", "unsupportable"}
# A refusal written as a sentence is still a refusal. Only used where nothing
# numeric could be parsed, so a submission cannot both answer and abstain.
ABSTAIN_PHRASES = ("cannot be determined", "cannot determine", "cannot be "
                   "certified", "cannot be supported", "cannot be quoted",
                   "not determinable", "no defensible", "not supportable",
                   "no predictor", "unable to determine", "not identifiable",
                   "no honest", "cannot certify", "decline to", "refuse")


def _abstained(text: str) -> bool:
    lowered = str(text).strip().lower()
    return (lowered in ABSTAIN
            or any(phrase in lowered for phrase in ABSTAIN_PHRASES))

# ------------------------------------------------------------------ chemistry
# Six carboxamide series. {S} is the side-chain position on the core, {A} the
# anilide ring. Every template was checked to parse under RDKit for every
# side chain and every key substituent below.
CORES = [
    ("SER-A", "{S}c1ccc(C(=O)N{A})cc1"),
    ("SER-B", "{S}c1ccc(C(=O)N{A})s1"),
    ("SER-C", "{S}c1ccc(C(=O)N{A})nc1"),
    ("SER-D", "{S}c1cc(C(=O)N{A})n(C)c1"),
    ("SER-E", "{S}c1nc(C(=O)N{A})cs1"),
    ("SER-F", "{S}c1ccc(C(=O)N{A})o1"),
]
SMALL_SIDE = ["C", "CC", "OC", "F", "CC(C)", "CCC", "OCC", "Cl", "C#C", "CO"]
LARGE_SIDE = ["CCCCCC", "CCCCCCCC", "OCCCCCC", "C1CCCCC1", "CC(C)CCCC",
              "CCCCCCCCC", "OCCCCCCC", "C1CCC(C)CC1", "CCC(CC)CC",
              "CCCCCCCCCC"]
# The substituent whose ring position decides potency. Varies with the seed so
# the answer text is not a memorisable constant.
KEY_GROUPS = [("Cl", "chloro"), ("F", "fluoro"), ("OC", "methoxy"),
              ("C", "methyl"), ("C(F)(F)F", "trifluoromethyl"),
              ("S(C)(=O)=O", "methanesulfonyl")]
PROJECTS = [("CRU-PX1", "MAP4K4"), ("CRU-PX2", "TBK1"), ("CRU-PX3", "PLK4"),
            ("CRU-PX4", "HPK1"), ("CRU-PX5", "ITK"), ("CRU-PX6", "SYK")]

N_PRIMARY = 96          # distinct structures measured once
N_BRIDGE = 12           # structures re-measured in the other run
N_QUEUE = 60            # made, not yet assayed
F2_GROUPS = 36          # structures measured three times each -> 108 rows
ALIGN = 0.85            # P(bulky side chain | para) in the measured set

BAR = 0.82              # programme rule: R2 the shipped model must reach
SLACK = 0.20            # how far below the attainable score a shipped model may sit
# A cross-validated estimate and a 60-compound holdout score differ by a few
# hundredths through sampling alone, so honesty is graded at 0.20 - two orders
# of magnitude tighter than the error a confounded model makes here, and loose
# enough that no correct analysis is failed for finite-sample luck.
HONESTY_TOL = 0.20
MARGIN = 0.05           # no instance is allowed nearer than this to the bar
GAP_LIMIT = 0.13        # build-time: cv estimate vs attainable score


def _standardise(rows: list[dict]) -> None:
    """Force the drawn measurement noise to realise its nominal spread exactly.

    Two finite files drawn from the same normal realise different sample
    variances, and a coefficient of determination is a ratio of variances: on
    one seed the measured set landed 9% above its nominal noise and the queued
    set 19% below, which moved the honest estimate 0.14 with no science
    involved. Standardising the draw removes a nuisance the benchmark is not
    trying to measure and leaves the confound it is.
    """
    values = [row["noise"] for row in rows]
    mean = sum(values) / len(values)
    spread = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5 or 1.0
    for row in rows:
        row["noise"] = (row["noise"] - mean) / spread


def _orthogonalise(rows: list[dict], series_names: list[str],
                   with_run: bool) -> None:
    """Draw the measurement noise orthogonal to the terms being fitted.

    Standardising the total spread is not enough: what a coefficient of
    determination on a *different* file depends on is the noise's projection
    onto the fitted directions, and a two-sigma projection onto the
    regiochemical term moved one seed's honest estimate 0.25 while the science
    in the file was unchanged. Residualising the draw against the design makes
    the fitted parameters recover the generating ones exactly in both files, so
    what the candidate is graded on is which analysis it chose rather than how
    the dice fell. Cross-validation still pays its honest out-of-sample
    penalty, because holding a fold out breaks this orthogonality.
    """
    import numpy as np

    matrix = np.asarray(_design(rows, series_names, with_run=with_run), float)
    draw = np.asarray([row["noise"] for row in rows], float)
    residual = draw - matrix @ _solve(matrix, draw)
    spread = float(residual.std()) or 1.0
    for row, value in zip(rows, residual / spread):
        row["noise"] = float(value)


def _smiles(template: str, side: str, key: str, para: bool) -> str:
    # Ring label 2 for the anilide: label 1 is still open in every core
    # template at this point, and reusing it silently builds a different
    # molecule instead of failing to parse.
    aryl = ("c2ccc(%s)cc2" if para else "c2cccc(%s)c2") % key
    return template.format(S=side, A=aryl)


def _descriptors(smiles: str) -> dict:
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors
    mol = Chem.MolFromSmiles(smiles)
    return {
        "heavy_atoms": mol.GetNumHeavyAtoms(),
        "mw": round(Descriptors.MolWt(mol), 2),
        "clogp": round(Crippen.MolLogP(mol), 2),
        "tpsa": round(rdMolDescriptors.CalcTPSA(mol), 2),
        "hba": rdMolDescriptors.CalcNumHBA(mol),
        "rot_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol),
    }


def para_flag(smiles: str) -> int | None:
    """1 if the anilide substituent is para to the amide nitrogen, else 0.

    Derived from the structure, not from the generator: the amide nitrogen is
    located by SMARTS and the ring position is read off the topological
    distance matrix (para is four bonds from the nitrogen, meta three). The
    verifier and the candidate can both compute this; the key never carries it.
    """
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smiles or "")
    if mol is None:
        return None
    matches = mol.GetSubstructMatches(
        Chem.MolFromSmarts("[CX3](=O)[NX3;H1]-[c]"))
    if not matches:
        return None
    _c, _o, n_idx, aryl_idx = matches[0]
    ring = next((r for r in mol.GetRingInfo().AtomRings() if aryl_idx in r), None)
    if ring is None:
        return None
    distances = Chem.GetDistanceMatrix(mol)
    for idx in ring:
        if idx == aryl_idx:
            continue
        atom = mol.GetAtomWithIdx(idx)
        outside = [nb.GetIdx() for nb in atom.GetNeighbors()
                   if nb.GetIdx() not in ring and nb.GetIdx() != n_idx]
        if outside:
            return 1 if int(round(distances[n_idx][idx])) == 4 else 0
    return None


# ------------------------------------------------------------------ statistics
# Hand-rolled so the re-derivation cannot drift with a library release: a
# verifier that changes its mind between versions is not a verifier.

def _solve(matrix, target, lam: float = 1e-6):
    import numpy as np
    matrix = np.asarray(matrix, float)
    target = np.asarray(target, float)
    gram = matrix.T @ matrix + lam * np.eye(matrix.shape[1])
    return np.linalg.solve(gram, matrix.T @ target)


def _r2(observed, predicted) -> float:
    import numpy as np
    observed = np.asarray(observed, float)
    predicted = np.asarray(predicted, float)
    total = float(((observed - observed.mean()) ** 2).sum())
    if total <= 0:
        return 0.0
    return float(1.0 - ((observed - predicted) ** 2).sum() / total)


def _design(rows: list[dict], series_names: list[str],
            with_run: bool = False) -> list[list[float]]:
    out = []
    for row in rows:
        flag = row.get("para")
        columns = ([1.0] + [1.0 * (row["series"] == s) for s in series_names[1:]]
                   + [float(flag if flag is not None else 0)])
        if with_run:
            columns.append(1.0 * (row.get("run") == "RUN-2"))
        out.append(columns)
    return out


def _grouped_cv_r2(rows: list[dict], labels: list[float],
                   series_names: list[str], folds: int = 5) -> float:
    """Cross-validated fit with replicate structures held together.

    Splitting replicates across folds would score a model on a measurement of
    a structure it had already seen, which is the reporting error this whole
    family is about.
    """
    import numpy as np
    matrix = np.asarray(_design(rows, series_names), float)
    labels = np.asarray(labels, float)
    groups = sorted({row["smiles"] for row in rows})
    assignment = {smiles: i % folds for i, smiles in enumerate(groups)}
    fold_of = np.array([assignment[row["smiles"]] for row in rows])
    predicted = np.zeros(len(labels))
    for fold in range(folds):
        test = fold_of == fold
        train = ~test
        if test.sum() == 0 or train.sum() <= matrix.shape[1]:
            predicted[test] = labels[train].mean() if train.sum() else 0.0
            continue
        weights = _solve(matrix[train], labels[train])
        predicted[test] = matrix[test] @ weights
    return _r2(labels, predicted)


def _replicate_groups(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row["smiles"]].append(row)
    return {k: v for k, v in groups.items() if len(v) > 1}


def _paired_offset(rows: list[dict]) -> float | None:
    """Run-to-run difference from the structures measured in both runs alone.

    The crispest statement available - the same molecule, read twice - and the
    one that identifies the run term at all. Reported separately from the
    estimate used for fitting so the two can be compared.
    """
    deltas = []
    for members in _replicate_groups(rows).values():
        by_run: dict[str, list[float]] = defaultdict(list)
        for row in members:
            by_run[row["run"]].append(row["potency"])
        if len(by_run) < 2:
            continue
        first = sum(by_run["RUN-1"]) / len(by_run["RUN-1"])
        second = sum(by_run["RUN-2"]) / len(by_run["RUN-2"])
        deltas.append(second - first)
    if not deltas:
        return None
    return sum(deltas) / len(deltas)


def _run_offset(rows: list[dict], series_names: list[str]) -> float:
    """Run-to-run difference, estimated jointly with the structural terms.

    Differencing the replicate structures on their own identifies the offset
    but throws away every other row: with a dozen pairs its standard error is
    large enough to leave a residual that the confounded design then loads onto
    the structural term, which moves the honest estimate around for reasons
    that have nothing to do with the science. Fitting the run indicator
    alongside the structural terms uses the whole file - the replicates and the
    compounds whose side chain disagrees with their run break the collinearity
    - and is what a careful analyst does anyway. Measured on the observable
    either way: never read from the key.
    """
    if len({row.get("run") for row in rows}) < 2:
        return 0.0
    labels = [row["potency"] for row in rows]
    weights = _solve(_design(rows, series_names, with_run=True), labels)
    return float(weights[-1])


def _corrected(rows: list[dict], offset: float) -> list[float]:
    return [row["potency"] - (offset if row["run"] == "RUN-2" else 0.0)
            for row in rows]


def _replicate_ceiling(rows: list[dict], labels: list[float]) -> float:
    """1 - SS_within/SS_total over groups of identical structures.

    An identity, not an estimate: the best prediction any function of
    structure can make for a group of identical structures is the group mean,
    so this is an exact upper bound on the coefficient of determination
    attainable on this file by any model class whatsoever.
    """
    index = {id(row): i for i, row in enumerate(rows)}
    mean = sum(labels) / len(labels)
    total = sum((value - mean) ** 2 for value in labels)
    if total <= 0:
        return 0.0
    within = 0.0
    for members in _replicate_groups(rows).values():
        values = [labels[index[id(row)]] for row in members]
        group_mean = sum(values) / len(values)
        within += sum((value - group_mean) ** 2 for value in values)
    return 1.0 - within / total


def _reference_analysis(train: list[dict], queue: list[dict]) -> dict:
    """The analysis a competent modeller lands on, from the shipped bytes only.

    Put the two runs on one scale, then fit the regiochemical feature and the
    series term on the normalised measurements. No hidden potency is read here,
    so `reference_submission` can call it without cheating and the verifier can
    call it to obtain the attainable score.
    """
    import numpy as np

    series_names = sorted({row["series"] for row in train})
    offset = _run_offset(train, series_names)
    labels = _corrected(train, offset)
    weights = _solve(_design(train, series_names), labels)
    predictions = [float(v) for v in
                   np.asarray(_design(queue, series_names), float) @ weights]
    return {
        "offset": offset,
        "paired_offset": _paired_offset(train),
        "series_names": series_names,
        "corrected_labels": labels,
        "ceiling": _replicate_ceiling(train, labels),
        "raw_ceiling": _replicate_ceiling(train, [r["potency"] for r in train]),
        "cv_r2": _grouped_cv_r2(train, labels, series_names),
        "queue_predictions": predictions,
    }


def _permutation_null(train: list[dict], labels: list[float], seed: int,
                      draws: int = 40) -> float:
    """Median cross-validated score under shuffled labels: the F2 witness."""
    series_names = sorted({row["series"] for row in train})
    rng = random.Random(seed)
    scores = []
    for _ in range(draws):
        shuffled = list(labels)
        rng.shuffle(shuffled)
        scores.append(_grouped_cv_r2(train, shuffled, series_names))
    scores.sort()
    return scores[len(scores) // 2]


# ------------------------------------------------------------------ csv layer

TRAIN_COLUMNS = ["compound_id", "smiles", "series", "run", "heavy_atoms", "mw",
                 "clogp", "tpsa", "hba", "rot_bonds", "potency_pIC50"]
QUEUE_COLUMNS = ["compound_id", "smiles", "series", "heavy_atoms", "mw",
                 "clogp", "tpsa", "hba", "rot_bonds"]


def _parse_csv(text: str, with_potency: bool) -> list[dict]:
    rows = []
    lines = [line for line in text.strip().splitlines() if line.strip()]
    header = [h.strip() for h in lines[0].split(",")]
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != len(header):
            continue
        record = dict(zip(header, parts))
        row = {
            "compound_id": record["compound_id"],
            "smiles": record["smiles"],
            "series": record["series"],
            "run": record.get("run", "RUN-1"),
            "heavy_atoms": float(record["heavy_atoms"]),
        }
        if with_potency:
            row["potency"] = float(record["potency_pIC50"])
        rows.append(row)
    return rows


def _annotate(rows: list[dict]) -> list[dict]:
    for row in rows:
        row["para"] = para_flag(row["smiles"])
    return rows


# ------------------------------------------------------------------ generation

def build(seed: int, condition: str) -> Episode:
    rng = random.Random(4_100_000 + seed)
    project, target = PROJECTS[seed % len(PROJECTS)]
    key_smarts, key_name = KEY_GROUPS[seed % len(KEY_GROUPS)]

    # Draw every structure without replacement from the four design cells, so
    # a repeated SMILES in the finished file is always a deliberate replicate.
    cells: dict[tuple[bool, bool], list[tuple]] = {}
    for para in (True, False):
        for bulky in (True, False):
            pool = [(name, template, side, para)
                    for name, template in CORES
                    for side in (LARGE_SIDE if bulky else SMALL_SIDE)]
            rng.shuffle(pool)
            cells[(para, bulky)] = pool

    def draw(para: bool, bulky: bool, count: int) -> list[tuple]:
        return [cells[(para, bulky)].pop() for _ in range(count)]

    series_names = sorted(name for name, _t in CORES)
    series_offset = {name: round(rng.uniform(-0.12, 0.12), 3)
                     for name in series_names}
    baseline = rng.uniform(6.0, 6.8)
    noise_sd = rng.uniform(0.22, 0.30)

    if condition == "F2":
        specs = []
        for index in range(F2_GROUPS):
            specs += draw(index % 2 == 0, index % 4 < 2, 1)
        queue_specs = (draw(True, False, N_QUEUE // 4)
                       + draw(True, True, N_QUEUE // 4)
                       + draw(False, True, N_QUEUE // 4)
                       + draw(False, False, N_QUEUE // 4))
    else:
        aligned = int(round(N_PRIMARY / 2 * ALIGN))
        specs = (draw(True, True, aligned)
                 + draw(True, False, N_PRIMARY // 2 - aligned)
                 + draw(False, False, aligned)
                 + draw(False, True, N_PRIMARY // 2 - aligned))
        inverted = int(round(N_QUEUE / 2 * ALIGN))
        queue_specs = (draw(True, False, inverted)
                       + draw(True, True, N_QUEUE // 2 - inverted)
                       + draw(False, True, inverted)
                       + draw(False, False, N_QUEUE // 2 - inverted))
    rng.shuffle(specs)
    rng.shuffle(queue_specs)

    def make(spec, compound_id):
        series, template, side, para = spec
        smiles = _smiles(template, side, key_smarts, para)
        bulky = side in LARGE_SIDE
        row = {"compound_id": compound_id, "smiles": smiles, "series": series,
               "run": "RUN-2" if bulky else "RUN-1", "para": 1 if para else 0,
               "bulky": bulky, "signal": series_offset[series]}
        row.update(_descriptors(smiles))
        return row

    if condition == "F2":
        # Three measurements of every structure, all inside one run so no
        # inter-run correction can rescue them, and labels drawn independently
        # of structure.
        train_rows = []
        spread = rng.uniform(0.75, 1.05)
        for index, spec in enumerate(specs):
            base = make(spec, "TRN-%03d" % (index + 1))
            for _ in range(3):
                row = dict(base)
                row["noise"] = rng.gauss(0.0, 1.0)
                train_rows.append(row)
        queue_rows = [make(spec, "QUE-%03d" % (i + 1))
                      for i, spec in enumerate(queue_specs)]
        for row in queue_rows:
            row["noise"] = rng.gauss(0.0, 1.0)
        _standardise(train_rows)
        _standardise(queue_rows)
        for row in train_rows + queue_rows:
            row["potency"] = round(baseline + 0.9 + spread * row["noise"], 2)
        effect = 0.0
        offset_true = 0.0
    else:
        train_rows = [make(spec, "TRN-%03d" % (index + 1))
                      for index, spec in enumerate(specs)]
        for row in train_rows:
            row["noise"] = rng.gauss(0.0, 1.0)
        # Replicates: the same structure read a second time in the other run.
        bridges = []
        for index in sorted(rng.sample(range(len(train_rows)), N_BRIDGE)):
            source = train_rows[index]
            twin = dict(source)
            twin["run"] = "RUN-1" if source["run"] == "RUN-2" else "RUN-2"
            twin["noise"] = rng.gauss(0.0, 1.0)
            bridges.append(twin)
        train_rows = train_rows + bridges
        queue_rows = [make(spec, "QUE-%03d" % (i + 1))
                      for i, spec in enumerate(queue_specs)]
        for row in queue_rows:
            row["noise"] = rng.gauss(0.0, 1.0)
        _orthogonalise(train_rows, series_names, with_run=True)
        _orthogonalise(queue_rows, series_names, with_run=False)

        offset_true = (rng.uniform(0.0, 0.10) if condition == "C0"
                       else rng.uniform(1.55, 2.05))
        # The attainable score is a property of the finished files, so it is
        # measured rather than assumed: bisect the regiochemical effect until
        # a fit on the shipped bytes lands on the intended target, which is
        # held clear of the programme bar by MARGIN in every instance.
        # Named target_r2, not target: `target` is the protein, and shadowing
        # it put a condition-dependent number into the brief, which the gate
        # caught as a C0/H1 brief mismatch.
        target_r2 = (rng.uniform(0.90, 0.94) if condition == "C0"
                     else rng.uniform(0.56, 0.70))

        def label(effect_size: float) -> None:
            for row in train_rows:
                row["potency"] = round(
                    baseline + effect_size * row["para"] + row["signal"]
                    + noise_sd * row["noise"]
                    + (offset_true if row["run"] == "RUN-2" else 0.0), 2)
            for row in queue_rows:
                row["potency"] = round(
                    baseline + effect_size * row["para"] + row["signal"]
                    + noise_sd * row["noise"], 2)

        def measure(effect_size: float) -> tuple[float, float]:
            label(effect_size)
            analysis = _reference_analysis(train_rows, queue_rows)
            return (_r2([row["potency"] for row in queue_rows],
                        analysis["queue_predictions"]), analysis["cv_r2"])

        # Both the attainable score AND the cross-validated estimate a
        # candidate can compute from the training file must sit on the same
        # side of the bar with room to spare, and must agree with each other,
        # or the instance would grade sampling luck as an error. Search the
        # target until they do; a seed that cannot be made unambiguous fails
        # the assertions below rather than being scored.
        # A bigger regiochemical effect always sharpens both estimates, so the
        # search walks the target UP first and only then down, inside the
        # window that keeps the instance MARGIN clear of the bar on the side
        # this condition requires.
        floor, roof = ((BAR + MARGIN, 0.965) if condition == "C0"
                       else (0.30, BAR - MARGIN))
        effect = 1.0
        for delta in (0.0, 0.03, 0.06, 0.09, 0.12, -0.04, -0.08, -0.14):
            aim = min(roof, max(floor, target_r2 + delta))
            low, high = 0.05, 6.0
            for _ in range(34):
                effect = 0.5 * (low + high)
                if measure(effect)[0] < aim:
                    low = effect
                else:
                    high = effect
            effect = 0.5 * (low + high)
            attainable_now, cv_now = measure(effect)
            clear = min(abs(attainable_now - BAR), abs(cv_now - BAR)) >= MARGIN
            side = (attainable_now > BAR) == (cv_now > BAR) == (condition == "C0")
            if clear and side and abs(cv_now - attainable_now) <= GAP_LIMIT:
                break

    # Scatter the rows and number the compounds by first appearance. Left
    # alone, the repeat measurements sit in a block - all at the foot of the
    # file in C0/H1, adjacent in F2 - and the replicate structure would be
    # readable from row position rather than from the identifiers.
    rng.shuffle(train_rows)
    seen: dict[str, str] = {}
    for row in train_rows:
        if row["smiles"] not in seen:
            seen[row["smiles"]] = "TRN-%03d" % (len(seen) + 1)
        row["compound_id"] = seen[row["smiles"]]

    # Every para/meta pair must be indistinguishable to the descriptor block,
    # or the leaky abstraction is not leaky and the family measures nothing.
    for name, template in CORES:
        for side in SMALL_SIDE[:1] + LARGE_SIDE[:1]:
            left = _descriptors(_smiles(template, side, key_smarts, True))
            right = _descriptors(_smiles(template, side, key_smarts, False))
            assert left == right, (name, side, left, right)
    for row in train_rows + queue_rows:
        assert para_flag(row["smiles"]) == row["para"], row["smiles"]

    def render(rows, columns, with_potency):
        lines = [",".join(columns)]
        for row in rows:
            values = [row["compound_id"], row["smiles"], row["series"]]
            if "run" in columns:
                values.append(row["run"])
            values += [str(row["heavy_atoms"]), "%.2f" % row["mw"],
                       "%.2f" % row["clogp"], "%.2f" % row["tpsa"],
                       str(row["hba"]), str(row["rot_bonds"])]
            if with_potency:
                values.append("%.2f" % row["potency"])
            lines.append(",".join(values))
        return "\n".join(lines) + "\n"

    files = {
        "train.csv": render(train_rows, TRAIN_COLUMNS, True),
        "queue.csv": render(queue_rows, QUEUE_COLUMNS, False),
        "programme_note.md": "\n".join([
            "# Programme note  %s  /  %s" % (project, target),
            "",
            "train.csv  one row per potency measurement made against %s so far."
            % target,
            "           potency_pIC50 is the recorded value and run names the",
            "           screening run the measurement came from.",
            "",
            "queue.csv  compounds already made and waiting for assay time. No",
            "           potency exists for them yet.",
            "",
            "The descriptor columns in both files came from the group's",
            "standard physicochemical block, run on the structure as given.",
            "",
            "Progression rule: the queue is triaged on model prediction rather",
            "than sent through the assay in full only when the shipped model",
            "reaches a coefficient of determination of %.2f or better on the"
            % BAR,
            "queued potencies.",
        ]) + "\n",
    }

    brief = (
        "%s has been running against %s. train.csv holds every potency "
        "measurement made so far; the compounds in queue.csv are made but not "
        "yet assayed. programme_note.md gives the rule for triaging the queue "
        "on prediction instead of assay time.\n\n"
        "Predict the potency of every queued compound, state what those "
        "predictions are worth on that queue, say what governs potency in this "
        "series, and give the progression call.\n\n"
        "Submit these fields:\n"
        "- queue_predictions: your predicted potency_pIC50 for every "
        "compound_id in queue.csv, as compound_id:value pairs, or the string "
        "cannot_determine if no defensible predictor follows from these data\n"
        "- expected_r2: the coefficient of determination your submitted "
        "predictions will reach on the queued compounds, as a number, or "
        "cannot_determine\n"
        "- potency_driver: what governs potency across this series, in your "
        "own words\n"
        "- deployment_recommendation: GO or NO-GO under the rule in "
        "programme_note.md\n"
        "and conf_<field> in [0,1] for each." % (project, target)
    )

    analysis = _reference_analysis(_annotate(_parse_csv(files["train.csv"], True)),
                                  _annotate(_parse_csv(files["queue.csv"], False)))
    hidden = {row["compound_id"]: row["potency"] for row in queue_rows}
    attainable = _r2([hidden[row["compound_id"]] for row in queue_rows],
                     analysis["queue_predictions"])

    # Guard rails. A family that is ambiguous about its own answer cannot
    # grade anyone else's, so the instance is rejected at build time rather
    # than scored later.
    if condition == "F2":
        assert analysis["ceiling"] < BAR - 0.15, analysis["ceiling"]
    else:
        assert analysis["ceiling"] > BAR + 0.07, analysis["ceiling"]
        assert abs(attainable - BAR) >= MARGIN, (condition, attainable)
        assert abs(analysis["cv_r2"] - BAR) >= MARGIN, (condition, analysis["cv_r2"])
        assert (attainable > BAR) == (condition == "C0"), (condition, attainable)
        assert (analysis["cv_r2"] > BAR) == (condition == "C0"), analysis["cv_r2"]
        assert abs(analysis["cv_r2"] - attainable) <= GAP_LIMIT, (
            condition, analysis["cv_r2"], attainable)

    key = {
        "condition": condition,
        "project": project,
        "target": target,
        "key_group": key_name,
        "queue_potency": hidden,
        "queue_order": [row["compound_id"] for row in queue_rows],
        "bar": BAR,
        "run_offset_true": round(offset_true, 3),
        "run_offset_measured": round(analysis["offset"], 3),
        "effect_true": round(effect, 3),
        "noise_sd": round(noise_sd, 3),
        "replicate_ceiling": round(analysis["ceiling"], 3),
        "attainable_r2": round(attainable, 3),
        "honest_cv_r2": round(analysis["cv_r2"], 3),
        "determinable": condition != "F2",
    }
    # 28 calls: read the two files, look at the replicate structures, put the
    # runs on one scale, build and cross-validate more than one featurisation,
    # compare the measured set with the queued set, then predict. A budget
    # that only permits one pass would reward the recipe.
    return Episode("qsar-inversion", seed, condition, brief, files, key,
                   budget=28,
                   checkpoints=["predictor", "honest_estimate", "driver",
                                "decision"])


# ---------------------------------------------------------------- verification

_CLAUSE = re.compile(r"[.;,]| but | whereas | while | rather than "
                     r"| instead of | although | though ")
# Cues that mark a clause as REJECTING what it names. Whole clauses are
# dropped, because "not molecular weight or lipophilicity" negates both terms
# and phrase-by-phrase removal would leave the second one standing.
_DISMISSAL = ("not ", "n't", " no ", "no ", "never", "none of", "independent",
              "unrelated", "irrelevant", "spurious", "confound", "artifact",
              "artefact", "coincid", "merely", "misleading", "illusor",
              "cannot", "fail", "does not", "do not", "without",
              "apparent only", "an artefact", "nothing to do")
# Position claims. Deliberately wide: the candidate answers in its own words.
_POSITION = ("para", "meta", "1,4", "1,3", "4-position", "3-position",
             "regio", "isomer", "substitution pattern", "position",
             "topolog", "connectiv", "substructur", "pharmacophore",
             "placement", "ring position", "orientation", "attachment",
             "where the")
# Bulk claims: the descriptor block the para/meta pair is invisible to.
_BULK = ("molecular weight", "heavy atom", "heavy-atom", "heavy_atom",
         "atom count", "molecular size", "size", "lipophil", "clogp", "logp",
         "tpsa", "rotatable", "chain length", "bulk", "larger compound", "mw",
         "molwt", "mol_wt")
# A bulk word only counts against an answer when the clause it sits in is
# ASSERTING it as the cause. "the two isomers are the same size" is a true
# statement a correct answer makes; "potency tracks size" is the wrong answer.
_ASSERTION = ("driv", "govern", "explain", "determin", "predict", "correlat",
              "dominat", "responsible", "because", "due to", "track",
              "contribut", "accounts for", "top feature", "key feature",
              "important feature", "main ", "primar", "cause", "controls",
              "sets the", "the driver")
# The F2 witness has to be named, not gestured at.
_CEILING_WORDS = ("replicate", "duplicate", "same compound", "same structure",
                  "identical structure", "identical smiles", "repeat measure",
                  "irreproduc", "reproducib", "ceiling", "upper bound",
                  "cannot exceed", "permut", "shuffl", "noise floor",
                  "no signal", "random label", "discordant", "disagree",
                  "three measurements", "within-compound", "measured three")


def _kept_clauses(text: str) -> list[str]:
    return [clause for clause in _CLAUSE.split(text.lower())
            if not any(cue in clause for cue in _DISMISSAL)]


def _asserts_bulk(text: str) -> bool:
    """Does the answer put the cause on the physicochemical block?

    Two conditions, both inside one clause: the clause must name a bulk
    property AND assert that it is doing the work, and it must not be a clause
    that rejects what it names. Scanning for bulk words anywhere failed
    correct answers that (truthfully) said the regioisomers are the same size,
    and scanning only for negations failed on "not molecular weight or
    lipophilicity", where the negation governs two terms and literal removal
    leaves the second standing.
    """
    for clause in _kept_clauses(text):
        if (any(word in clause for word in _BULK)
                and any(cue in clause for cue in _ASSERTION)):
            return True
    return False


def _parse_predictions(raw, ids: list[str], workspace: Path) -> tuple[dict, bool]:
    """Read a prediction per queued compound out of whatever shape arrived."""
    abstained = False
    out: dict[str, float] = {}

    def take(identifier, value):
        name = str(identifier).strip().upper()
        if name in lookup:
            try:
                out[lookup[name]] = float(str(value).strip())
            except (TypeError, ValueError):
                pass

    lookup = {i.upper(): i for i in ids}
    if isinstance(raw, dict):
        for identifier, value in raw.items():
            take(identifier, value)
    elif isinstance(raw, (list, tuple)):
        for entry in raw:
            if isinstance(entry, dict):
                identifier = next((entry[k] for k in entry
                                   if "id" in str(k).lower()), None)
                value = next((entry[k] for k in entry
                              if "id" not in str(k).lower()), None)
                take(identifier, value)
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                take(entry[0], entry[1])
    elif raw is not None:
        text = str(raw).strip()
        for chunk in re.split(r"[\n;]+", text):
            found = re.findall(r"[A-Za-z]{2,}[-_]?\d+", chunk)
            numbers = re.findall(r"-?\d+\.?\d*", chunk)
            if found and numbers:
                take(found[0], numbers[-1])
        if not out:
            abstained = _abstained(text)
    if not out and not abstained:
        candidate = workspace / "predictions.csv"
        try:
            text = candidate.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001 - absent file is the normal case
            text = ""
        # Every line, header included: an unknown identifier or a non-numeric
        # value is dropped by `take`, so a file written without a header does
        # not silently lose its first compound.
        for line in text.splitlines():
            parts = [p.strip() for p in line.replace("\t", ",").split(",")]
            if len(parts) >= 2:
                take(parts[0], parts[-1])
    return out, abstained


def _as_float(text: str):
    """A number, however it was written down.

    Frontier submissions arrive as "0.62 (grouped 5-fold)" as often as 0.62,
    and a formatting quibble is not a scientific error - the campaign log is
    explicit that infrastructure never decides a score.
    """
    try:
        return float(text)
    except (TypeError, ValueError):
        found = re.search(r"-?\d*\.?\d+", str(text))
        return float(found.group()) if found else None


def _as_call(text: str) -> str:
    """GO / NO-GO out of free text, checking the negative first: every spelling
    of NO-GO contains GO."""
    upper = str(text).strip().upper()
    if any(token in upper for token in ("NO-GO", "NO GO", "NOGO", "NO_GO",
                                        "NOT GO", "DO NOT", "DON'T")):
        return "NO-GO"
    if "GO" in upper:
        return "GO"
    return upper


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    order = ["predictor", "honest_estimate", "driver", "decision"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "predictor")

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # Re-derive the whole analysis from the shipped bytes.
    train = _annotate(_parse_csv(episode.files["train.csv"], True))
    queue = _annotate(_parse_csv(episode.files["queue.csv"], False))
    analysis = _reference_analysis(train, queue)
    truth = key["queue_potency"]
    ids = [row["compound_id"] for row in queue]
    observed = [truth[i] for i in ids]
    attainable = _r2(observed, analysis["queue_predictions"])
    detail.update({
        "run_offset_recomputed": round(analysis["offset"], 3),
        "replicate_ceiling_recomputed": round(analysis["ceiling"], 3),
        "replicate_ceiling_uncorrected": round(analysis["raw_ceiling"], 3),
        "attainable_r2_recomputed": round(attainable, 3),
        "honest_cv_r2_recomputed": round(analysis["cv_r2"], 3),
        "bar": BAR,
    })

    reason = " ".join(str(field(name) or "") for name in
                      ("potency_driver", "expected_r2", "reasoning",
                       "queue_predictions"))
    predictions, predictions_abstained = _parse_predictions(
        field("queue_predictions"), ids, workspace)
    raw_expected = field("expected_r2")
    expected_text = str(raw_expected if raw_expected is not None else "").strip()
    expected_abstained = bool(expected_text) and _abstained(expected_text)
    call = _as_call(field("deployment_recommendation") or "")
    driver_text = str(field("potency_driver") or "")

    # Whether a refusal is required is recomputed, not looked up: the identity
    # 1 - SS_within/SS_total over groups of identical structures is an exact
    # upper bound on what any function of structure can score on this file.
    impossible = analysis["ceiling"] < BAR
    detail["refusal_required"] = impossible
    detail["condition"] = key["condition"]

    if impossible:
        null = _permutation_null(train, analysis["corrected_labels"],
                                 seed=episode.seed)
        detail["permutation_null_cv_r2"] = round(null, 3)
        detail["expected"] = ("refusal: the replicate ceiling is %.2f, below "
                              "the %.2f the programme requires"
                              % (analysis["ceiling"], BAR))
        names_witness = any(word in reason.lower() for word in _CEILING_WORDS)
        checks["predictor"] = predictions_abstained and not predictions
        checks["honest_estimate"] = expected_abstained
        checks["driver"] = (predictions_abstained or expected_abstained) and names_witness
        checks["decision"] = ((predictions_abstained or expected_abstained)
                              and call in ("NO-GO", "CANNOT_DETERMINE"))
        detail["stated_driver"] = driver_text[:220]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    missing = [i for i in ids if i not in predictions]
    detail["predictions_missing"] = len(missing)
    if predictions and not missing:
        achieved = _r2(observed, [predictions[i] for i in ids])
    else:
        achieved = None
    detail["achieved_r2"] = None if achieved is None else round(achieved, 3)

    # 1. The shipped predictor has to work on compounds it has never seen, to
    #    within SLACK of what the supplied measurements support.
    checks["predictor"] = achieved is not None and achieved >= attainable - SLACK
    detail["predictor_floor"] = round(attainable - SLACK, 3)

    # 2. The number reported has to be the number the predictions achieve. A
    #    cross-validated score quoted as a deployment expectation fails here,
    #    and that is the whole family.
    claimed = _as_float(expected_text)
    detail["claimed_r2"] = claimed
    checks["honest_estimate"] = (claimed is not None and achieved is not None
                                 and abs(claimed - achieved) <= HONESTY_TOL)

    # 3. What governs potency. The positional claim is read from the whole
    #    answer; the bulk-descriptor claim only from clauses that are not
    #    rejecting it, so "the para substitution, not molecular size" reads as
    #    the position and "the para compounds win because they are larger"
    #    does not.
    positive = driver_text.lower()
    for phrase in ("not para", "not the para", "not meta", "not the meta",
                   "not a regio", "not regio", "not positional",
                   "not the position", "not the substitution pattern"):
        positive = positive.replace(phrase, " ")
    says_position = any(word in positive for word in _POSITION)
    says_bulk = _asserts_bulk(driver_text)
    checks["driver"] = says_position and not says_bulk
    detail["says_position"] = says_position
    detail["says_bulk"] = says_bulk
    detail["stated_driver"] = driver_text[:220]

    # 4. The progression call has to follow from what the predictions actually
    #    do, not from what the training file suggested they would do.
    if achieved is None:
        expected_call = None
    else:
        expected_call = "GO" if achieved >= BAR else "NO-GO"
    checks["decision"] = expected_call is not None and call == expected_call
    detail["expected_call"] = expected_call
    detail["given_call"] = call

    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


def reference_submission(episode: Episode) -> dict:
    """What a competent modeller submits, derived from the workspace alone.

    No hidden potency and no generator parameter is read here: the runs are put
    on one scale using the replicate structures, the regiochemical feature is
    recomputed from the SMILES, and the reported expectation is the
    cross-validated score on the corrected measurements - so B8 proves the
    honest a-priori estimate really does land on the deployment truth, rather
    than proving the key agrees with itself.
    """
    key = episode.key
    train = _annotate(_parse_csv(episode.files["train.csv"], True))
    queue = _annotate(_parse_csv(episode.files["queue.csv"], False))
    analysis = _reference_analysis(train, queue)
    group = key["key_group"]

    if analysis["ceiling"] < BAR:
        return {
            "queue_predictions": "cannot_determine",
            "expected_r2": "cannot_determine",
            "potency_driver": (
                "no predictor can be certified from this file: every structure "
                "appears three times and the repeat measurements of one "
                "structure disagree by more than the spread between different "
                "structures, so the best any function of structure can score "
                "here is 1 - SS_within/SS_total over the groups of identical "
                "structures, which is %.2f - below the %.2f the programme "
                "requires. Shuffled labels reach the same cross-validated "
                "score as the real ones, so there is no structure-activity "
                "signal left to fit." % (analysis["ceiling"], BAR)),
            "deployment_recommendation": "NO-GO",
            "conf_queue_predictions": 0.9, "conf_expected_r2": 0.9,
            "conf_potency_driver": 0.9, "conf_deployment_recommendation": 0.9,
        }

    predictions = ";".join(
        "%s:%.2f" % (row["compound_id"], value)
        for row, value in zip(queue, analysis["queue_predictions"]))
    expected = round(analysis["cv_r2"], 3)
    return {
        "queue_predictions": predictions,
        "expected_r2": expected,
        "potency_driver": (
            "the ring position of the %s substituent on the anilide ring "
            "governs potency: the para isomers are potent and the meta isomers "
            "are weak by about the same amount in every series. The supplied "
            "physicochemical block cannot express that: para and meta are "
            "exact regioisomers which carry identical molecular weight and "
            "heavy-atom count and cLogP and TPSA. The apparent descriptor trend "
            "is spurious on two counts: run 2 reads %.2f log units high on the "
            "structures measured in both runs, and the measured file happens "
            "to pair the long side chains with the para series while the "
            "queued file pairs them the other way round."
            % (group, analysis["offset"])),
        "deployment_recommendation": "GO" if expected >= BAR else "NO-GO",
        "conf_queue_predictions": 0.8, "conf_expected_r2": 0.75,
        "conf_potency_driver": 0.85, "conf_deployment_recommendation": 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
