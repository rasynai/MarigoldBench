"""Deterministic scoring of a chain submission.

Nothing here consults a model: VCC and every stage-level statistic are computed
from the candidate's machine-readable answer block against generated truth. LLM
judges contribute only the advisory reasoning-quality score and the "did it name
the fork" signal, both of which live in judge_chain.py and can never change VCC.
"""
from __future__ import annotations

import json
import math
import re

CONF_RE = re.compile(r"^(?:conf|confidence)_(.+)$", re.I)


def extract_answer_block(submission: str) -> dict | None:
    """Last well-formed ```json object in the response is the answer of record."""
    blocks = re.findall(r"```json\s*(.*?)```", submission, re.S)
    for block in reversed(blocks):
        try:
            parsed = json.loads(block.strip())
        except json.JSONDecodeError:
            # tolerate trailing commas and stray text after the object
            cleaned = re.sub(r",\s*([}\]])", r"\1", block.strip())
            match = re.search(r"\{.*\}", cleaned, re.S)
            if not match:
                continue
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _num(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("%", "")
        cleaned = re.sub(r"[^0-9eE+\-.]", "", cleaned)
        try:
            parsed = float(cleaned)
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None
    return None


def _token(value) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


_FILLER_TOKEN = re.compile(
    r"^\d+$|^nm$|^ng$|^ml$|^ul$|^mm$|^um$|^h$|^hr$|^min$"
    # side-neutral qualifiers: 'below the METHOD LLOQ' must match 'below the
    # lloq'. None of these words can flip which side of a fork is meant.
    r"|^method$|^validated$|^reporting$|^assay$|^stated$|^nominal$|^this$")


def _strip_fillers(token_string: str) -> str:
    """Drop bare numbers, units and side-neutral qualifier tokens so
    interposed words cannot break an alias match: 'above the 1.0 nM LLOQ' and
    'below the method LLOQ' still match their aliases. Negation words are
    kept, so the negation-safety of alias sets survives."""
    kept = [t for t in token_string.split("_") if t and not _FILLER_TOKEN.match(t)]
    return "_".join(kept)


# A clause that REJECTS an alternative must not count as naming it: frontier
# candidates write values like "1/x^2-weighted (unweighted was tried first
# and rejected because ...)" - honest science, not a hedge. Clauses are split
# on parentheses/semicolons/commas; any clause carrying a rejection marker
# contributes no alias hits. A genuine hedge ("either OLS or 1/x^2") has no
# rejection marker and still scores as a hedge.
_REJECTION_MARKERS = ("reject", "ruled out", "rule out", "not used", "not use",
                      "instead of", "rather than", "tried first", "was tried",
                      "discard", "fails", "failed", "does not pass", "did not pass",
                      "not permitted", "excluded as", "was excluded", "were excluded",
                      "not required", "not needed", "over the alternative")
# "so no 1/x^2 fit was required" - negation of need with words in between.
_REJECTION_RE = re.compile(r"\bno\b[^,;()]*\b(required|needed|necessary|used)\b")
_CLAUSE_SPLIT = re.compile(r"[();,.]")


def _decided_clauses(text: str) -> str:
    kept = [c for c in _CLAUSE_SPLIT.split(str(text))
            if not any(m in c.lower() for m in _REJECTION_MARKERS)
            and not _REJECTION_RE.search(c.lower())]
    return " ".join(kept) if kept else str(text)


def _cat_match(given, target, aliases) -> bool:
    """Categorical match without a menu.

    The prompt no longer prints the allowed tokens (that made every judgment
    multiple choice - the campaign-3.0.0 saturation), so a candidate answers in
    its own words: "weighted 1/x^2 regression" must score as
    `weighted_1_over_x2`, and "ordinary least squares" as `unweighted_ols`.
    Each side of the fork therefore carries generator-authored aliases, and a
    phrase matches if the canonical token or any alias appears in it on
    underscore boundaries - so alias "weighted" does NOT fire inside
    "unweighted_ols". Alias sets are gate-checked disjoint at build time,
    under the same filler-stripping used here. Rejected-alternative clauses
    are discounted before matching.
    """
    token = _token(_decided_clauses(given))
    padded = f"_{token}_"
    stripped = f"_{_strip_fillers(token)}_"
    # Any abstention phrasing matches an abstention target: with no menu in
    # the prompt, "cannot be determined", "not quantifiable on the requested
    # basis" and "cannot_determine" are the same verdict. Phrase-level, not
    # exact-token: frontier refusals arrive as sentences.
    if _token(target) in ABSTAIN_TOKENS:
        if _token(given) in ABSTAIN_TOKENS:
            return True
        whole = f"_{_token(given)}_"
        for phrase in _ABSTAIN_PHRASES:
            if f"_{phrase}_" in whole or f"_{phrase}_" in f"_{_strip_fillers(_token(given))}_":
                return True
    for form in [target, *(aliases or [])]:
        needle = f"_{_token(form)}_"
        if needle in padded or f"_{_strip_fillers(_token(form))}_" in stripped:
            return True
    return False


def _set_match(given, target) -> bool:
    """Set-valued stages (hardening spec 3.3): which observations are
    excluded, which levels retained. Accepts a JSON list or a delimited
    string; order-free; the empty set is a legal, meaningful answer."""
    if isinstance(given, str):
        given = [p for p in re.split(r"[;,|\s]+", given) if p]
    if not isinstance(given, (list, tuple, set)):
        return False
    return {_token(x) for x in given if str(x).strip()} == {_token(x) for x in target}


def _match(given, target, tol, aliases=None) -> bool:
    """Dispatch on the TARGET's type, so a stage whose correct answer is
    'cannot_determine' while its decoy is a number is compared correctly on
    both sides."""
    if isinstance(target, (list, tuple, set)):
        return _set_match(given, target)
    if isinstance(target, bool) or not isinstance(target, (int, float)):
        return _cat_match(given, target, aliases)
    given_num = _num(given)
    if given_num is None:
        return False
    width = float(tol) if tol is not None else max(abs(float(target)) * 0.01, 1e-9)
    return abs(given_num - float(target)) <= width


ABSTAIN_TOKENS = {"abstain", "unknown", "cannot_determine", "not_determinable",
                  "insufficient_data", "unidentifiable", "n_a", "na", "none"}

# Natural-language refusal phrasings, matched on token boundaries against a
# value whose TARGET is an abstention. Only consulted in that case, so
# "not quantifiable" here cannot collide with a stage where it is a decoy
# alias for a below-the-limit verdict.
_ABSTAIN_PHRASES = (
    "cannot_determine", "cannot_be_determined", "unable_to_determine",
    "not_determinable", "cannot_be_established", "insufficient_data",
    "insufficient_information", "no_defensible_number", "not_quantifiable",
    "not_possible_to_determine", "cannot_be_quantified", "indeterminate",
)


def score_chain(submission: str, key: dict) -> dict:
    """Deterministic per-run scoring against the generated answer key."""
    answers = extract_answer_block(submission)
    stages_key: dict = key["stages"]
    order = list(stages_key)

    # Field lookup is case- and underscore-insensitive: a candidate that writes
    # "unknown_conc_nm" for "unknown_conc_nM" got the science right, and v1's
    # CORR-004 taught us not to fail those on transcription style.
    lowered = {}
    if answers:
        for field, value in answers.items():
            lowered.setdefault(re.sub(r"[^a-z0-9]", "", str(field).lower()), value)

    def _lookup(name: str):
        if answers is None:
            return None
        if name in answers:
            return answers[name]
        return lowered.get(re.sub(r"[^a-z0-9]", "", name.lower()))

    results = []
    first_failure = None
    tripped = []
    abstained_stages = []
    for index, stage_key in enumerate(order):
        spec = stages_key[stage_key]
        given = _lookup(stage_key)
        present = given is not None
        abstained = present and _token(given) in ABSTAIN_TOKENS
        # Abstention is a diagnostic, never a verdict: on a stage whose correct
        # answer IS "cannot_determine", declining to invent a number is the
        # right science and must score as correct.
        correct = present and _match(given, spec["correct"], spec.get("tol"),
                                     spec.get("correct_aliases"))
        trapped = present and not correct and _match(given, spec["decoy"], spec.get("tol"),
                                                     spec.get("decoy_aliases"))
        # A free-form phrase that matches BOTH sides of the fork is ambiguous,
        # not correct: the build gate keeps alias sets disjoint, so this only
        # happens when the candidate hedged ("weighted or maybe OLS") - and a
        # hedge on a judgment call is not a verdict.
        hedged = bool(correct and _match(given, spec["decoy"], spec.get("tol"),
                                         spec.get("decoy_aliases")))
        if hedged:
            correct = False
        # Which enumerated wrong analysis path was taken, if any. decoys[] is
        # the full wrong-path enumeration (hardening spec M5); knowing WHICH
        # path failures converge on is the primary automated discriminant
        # between genuine difficulty and an ambiguous key (spec D2).
        decoy_id = None
        if present and not correct:
            if trapped:
                decoy_id = "primary"
            else:
                for alt in spec.get("decoys") or []:
                    if _match(given, alt.get("value"), spec.get("tol")):
                        decoy_id = alt.get("id", "enumerated")
                        trapped = True
                        break
        # Free-form categorical that matched neither side: scored incorrect,
        # flagged for the post-campaign cross-family adjudication lane (which
        # can extend aliases and trigger a rescore, never grant credit here).
        unmatched = bool(present and not correct and not trapped and not abstained
                         and not isinstance(spec["correct"], (int, float, list))
                         and not isinstance(spec["correct"], bool)
                         and _num(given) is None)
        if abstained:
            abstained_stages.append(stage_key)
        if trapped:
            tripped.append(stage_key)
        if not correct and first_failure is None:
            first_failure = index
        confidence = None
        if answers:
            for field, value in answers.items():
                match = CONF_RE.match(field)
                if match and match.group(1).lower() == stage_key.lower():
                    confidence = _num(value)
        if confidence is not None and confidence > 1.0:
            confidence = confidence / 100.0
        results.append({
            "stage": stage_key, "index": index, "label": spec.get("label", ""),
            "present": present, "correct": correct, "trapped": trapped,
            "abstained": abstained, "hedged": hedged, "unmatched": unmatched,
            "decoy_id": decoy_id, "given": given,
            "expected": spec["correct"], "decoy": spec["decoy"],
            "confidence": confidence,
        })

    decision_key = key["decision"]
    decision_given = _lookup("decision")
    decision_correct = decision_given is not None and \
        _token(decision_given) == _token(decision_key["correct"])
    decision_trapped = decision_given is not None and \
        _token(decision_given) == _token(decision_key["decoy"])

    n_stages = len(order)
    n_correct = sum(1 for r in results if r["correct"])
    depth = n_stages if first_failure is None else first_failure
    vcc = bool(n_correct == n_stages and decision_correct)

    conf_pairs = [(r["confidence"], r["correct"]) for r in results
                  if r["confidence"] is not None]
    brier = (sum((c - (1.0 if ok else 0.0)) ** 2 for c, ok in conf_pairs) / len(conf_pairs)
             if conf_pairs else None)
    overconfidence = (sum(c - (1.0 if ok else 0.0) for c, ok in conf_pairs) / len(conf_pairs)
                      if conf_pairs else None)

    return {
        "vcc": vcc,
        "answer_block_present": answers is not None,
        "n_stages": n_stages,
        "n_stages_correct": n_correct,
        "stage_accuracy": round(n_correct / n_stages, 4) if n_stages else 0.0,
        "chain_depth": depth,
        "chain_depth_norm": round(depth / n_stages, 4) if n_stages else 0.0,
        "first_failed_stage": None if first_failure is None else order[first_failure],
        "decision_correct": decision_correct,
        "decision_trapped": decision_trapped,
        "decision_given": decision_given,
        "trapped_stages": tripped,
        "trap_rate_within_run": round(len(tripped) / n_stages, 4) if n_stages else 0.0,
        "any_trap": bool(tripped or decision_trapped),
        "abstained_stages": abstained_stages,
        "brier": None if brier is None else round(brier, 4),
        "mean_overconfidence": None if overconfidence is None else round(overconfidence, 4),
        "n_confidences": len(conf_pairs),
        "stages": results,
    }


# --- population statistics -------------------------------------------------

def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def rms_calibration_error(runs: list[dict], bins: int = 10) -> float | None:
    """RMS calibration error over (confidence, correctness) pairs, HLE-style."""
    pairs = [(s["confidence"], s["correct"]) for run in runs for s in run["stages"]
             if s.get("confidence") is not None]
    if not pairs:
        return None
    total = len(pairs)
    error = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        bucket = [(c, ok) for c, ok in pairs if (lo <= c < hi or (b == bins - 1 and c == 1.0))]
        if not bucket:
            continue
        mean_conf = sum(c for c, _ in bucket) / len(bucket)
        mean_acc = sum(1 for _, ok in bucket if ok) / len(bucket)
        error += (len(bucket) / total) * (mean_conf - mean_acc) ** 2
    return round(math.sqrt(error), 4)


def aggregate(runs: list[dict]) -> dict:
    """Aggregate per-run scorings into the reported metric family."""
    if not runs:
        return {"n_runs": 0}
    n = len(runs)
    stage_rows = [s for run in runs for s in run["stages"]]
    return {
        "n_runs": n,
        "vcc_rate": round(sum(1 for r in runs if r["vcc"]) / n, 4),
        "mean_stage_accuracy": round(_mean([r["stage_accuracy"] for r in runs]), 4),
        # NOTE: chain_depth_norm is kept per-run for diagnosing a single
        # instance, but is deliberately NOT averaged across tasks - see
        # hazard_profile() for why that average is not a comparable quantity.
        "mean_chain_depth_norm_DIAGNOSTIC_ONLY": round(
            _mean([r["chain_depth_norm"] for r in runs]), 4),
        "decision_accuracy": round(sum(1 for r in runs if r["decision_correct"]) / n, 4),
        "run_trap_rate": round(sum(1 for r in runs if r["any_trap"]) / n, 4),
        "stage_trap_rate": round(sum(1 for s in stage_rows if s["trapped"]) / len(stage_rows), 4)
        if stage_rows else None,
        "abstention_rate": round(sum(1 for s in stage_rows if s["abstained"]) / len(stage_rows), 4)
        if stage_rows else None,
        "answer_block_rate": round(sum(1 for r in runs if r["answer_block_present"]) / n, 4),
        "mean_brier": (lambda v: None if v is None else round(v, 4))(
            _mean([r["brier"] for r in runs])),
        "rms_calibration_error": rms_calibration_error(runs),
        "mean_overconfidence": (lambda v: None if v is None else round(v, 4))(
            _mean([r["mean_overconfidence"] for r in runs])),
    }


def _comb(n: int, k: int) -> float:
    from math import comb

    return float(comb(n, k)) if 0 <= k <= n else 0.0


def reliability(by_instance: dict[str, list[bool]], k: int = 3) -> dict:
    """The headline family, using the UNBIASED estimators rather than the
    plug-in ones.

    pass^k = E[C(c,k)/C(n,k)]  - all k independent runs succeed (reliability)
    pass@k = E[1 - C(n-c,k)/C(n,k)] - at least one of k succeeds (ceiling)

    The plug-in alternatives p^k and 1-(1-p)^k are both biased; on realistic
    numbers the plug-in pass^3 overstates by ~3x. pass@1 is reported beside
    them because pass^k collapses to a hard zero with a zero-width interval
    once per-run success falls below roughly 8%, and a zero there means the
    benchmark is out of calibration, not that the system scored nothing.
    """
    eligible = {inst: outs for inst, outs in by_instance.items() if len(outs) >= k}
    if not eligible:
        return {"k": k, "n_instances": 0}
    hat_k = at_k = at_1 = 0.0
    flips = 0
    for outs in eligible.values():
        n = len(outs)
        c = sum(1 for o in outs if o)
        hat_k += _comb(c, k) / _comb(n, k)
        at_k += 1.0 - (_comb(n - c, k) / _comb(n, k))
        at_1 += c / n
        if 0 < c < n:
            flips += 1
    m = len(eligible)
    return {
        "k": k, "n_instances": m,
        "pass_hat_k": round(hat_k / m, 4),      # headline: reliable solve rate
        "pass_at_1": round(at_1 / m, 4),        # calibration guard rail
        "pass_at_k": round(at_k / m, 4),        # retry ceiling
        "flip_rate": round(flips / m, 4),
    }


def wilson_interval(successes: int, n: int, z: float = 1.96) -> list[float]:
    """Wilson score interval. The Wald interval is unusable at the rates this
    benchmark targets: 0 of 200 gives a zero-width interval and 1 of 200 gives
    a negative lower bound."""
    if n == 0:
        return [0.0, 0.0]
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def hazard_profile(runs: list[dict]) -> dict:
    """Per-stage hazard h_k = P(fail at k | reached k), and the survival curve
    it implies. This REPLACES normalized chain depth as the progress metric.

    Normalized depth (D/K) is not comparable across tasks with different stage
    counts: at a constant per-stage hazard it falls monotonically with K (0.855
    at K=2 versus 0.090 at K=100 for identical competence), and splitting one
    stage into two equally hard sub-stages moves it by about +2.7% with no
    change in behaviour at all. The hazard is invariant to both.

    E[D] = sum_k S_k is the discrete area under the survival curve and is
    reported unnormalized.
    """
    max_stages = max((r["n_stages"] for r in runs), default=0)
    at_risk = [0] * max_stages
    failed = [0] * max_stages
    for run in runs:
        for index, stage in enumerate(run["stages"]):
            at_risk[index] += 1
            if not stage["correct"]:
                failed[index] += 1
                break                      # the chain stops at its first failure
    hazards, survival = [], []
    running = 1.0
    for index in range(max_stages):
        if at_risk[index] == 0:
            break
        h = failed[index] / at_risk[index]
        hazards.append({"stage_index": index + 1, "n_at_risk": at_risk[index],
                        "n_failed": failed[index], "hazard": round(h, 4),
                        "hazard_ci95": wilson_interval(failed[index], at_risk[index])})
        running *= (1 - h)
        survival.append(round(running, 4))
    return {
        "hazard_by_stage": hazards,
        "survival_curve": survival,
        "expected_depth": round(sum(survival), 4),   # unnormalized, on purpose
        "n_runs": len(runs),
    }


def cluster_bootstrap_ci(rows: list[dict], value_key: str, cluster_key: str = "template_id",
                         iterations: int = 2000, seed: int = 20260816) -> dict:
    """Percentile bootstrap resampling CLUSTERS (templates), because instances
    from one template are correlated - the standard error that treats them as
    independent is the one benchmarks most often get wrong."""
    import random

    if not rows:
        return {"point": None, "ci95": [None, None], "n_clusters": 0}
    clusters: dict = {}
    for row in rows:
        clusters.setdefault(row.get(cluster_key, "_"), []).append(float(row[value_key]))
    names = list(clusters)
    point = sum(sum(v) for v in clusters.values()) / sum(len(v) for v in clusters.values())
    rng = random.Random(seed)
    draws = []
    for _ in range(iterations):
        picked = [clusters[rng.choice(names)] for _ in names]
        flat = [v for group in picked for v in group]
        if flat:
            draws.append(sum(flat) / len(flat))
    draws.sort()
    lo = draws[int(0.025 * len(draws))] if draws else None
    hi = draws[int(0.975 * len(draws)) - 1] if draws else None
    return {"point": round(point, 4), "ci95": [round(lo, 4), round(hi, 4)],
            "n_clusters": len(names)}
