"""The chain-template contract and its structural gates.

A chain template is a Python generator authored by a frontier model. For a
(seed, condition) it emits one instance: a work order, text artifacts, and the
hidden chain of ordered stages. Every stage carries the value a CORRECT analysis
yields and the value the ATTRACTIVE WRONG path yields; the gates below enforce
that those two are separated by a margin (GeneBench-Pro's ablation guarantee,
made mechanical) so "plausible but wrong" can never score.
"""
from __future__ import annotations

import math
import re

CONDITIONS = ("C0", "H1", "F2")
MIN_STAGES, MAX_STAGES = 5, 8
# Kept in sync with score.ABSTAIN_TOKENS; a stage whose correct answer is one of
# these is testing whether the system declines to invent an unavailable number.
ABSTAIN_TOKENS = {"abstain", "unknown", "cannot_determine", "not_determinable",
                  "insufficient_data", "unidentifiable", "n_a", "na", "none"}
TRAP_MARGIN = 3.0          # |decoy - correct| must exceed TRAP_MARGIN * tol
# Scientific field names legitimately carry unit capitalisation (conc_nM, vol_mL).
KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,39}$")

# Words that would leak the benchmark's own machinery into candidate-visible
# text. Deliberately NOT included as bare words: "trap" (ion trap, cold trap,
# trap column), "hazard" (hazard ratio, hazardous waste) and "stage" (stage-1
# reaction) are ordinary vocabulary in these sciences, and banning them
# rejected valid analytical-chemistry and survival-analysis tasks. Only
# benchmark-specific phrasings are forbidden.
META_WORDS = (
    "planted", "decoy", "condition c0", "condition h1", "condition f2",
    "benchmark", "rubric", "grader", "ground truth", "flawed premise",
    "the correct answer", "crucible", "planted hazard", "trap value",
    "distractor value", "clean control", "this evaluation", "the evaluator",
)


class ChainInvalid(Exception):
    """A template violated a structural gate; it never reaches the benchmark."""


def _alias_token(value) -> str:
    """Mirror of score._token: the gate must reason in the same normal form
    the scorer matches in, or the disjointness check proves nothing."""
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(float(value))


def check_stage(stage: dict, index: int) -> None:
    where = f"stage[{index}]"
    for field in ("key", "label", "correct", "decoy", "fork"):
        if field not in stage:
            raise ChainInvalid(f"{where} missing '{field}'")
    key = stage["key"]
    if not isinstance(key, str) or not KEY_RE.match(key):
        raise ChainInvalid(f"{where} key {key!r} must be snake_case [3,40] chars")
    correct, decoy = stage["correct"], stage["decoy"]
    # Mixed types are legal in exactly one situation: the quantity is genuinely
    # not determinable (correct = an abstention token) while the attractive
    # wrong path still produces a number. That IS the flawed-premise test.
    mixed_ok = (not _is_number(correct)) and _is_number(decoy) \
        and str(correct).strip().lower() in ABSTAIN_TOKENS
    if _is_number(correct) != _is_number(decoy) and not mixed_ok:
        raise ChainInvalid(
            f"{where} correct/decoy types differ ({correct!r} vs {decoy!r});"
            " mixed types are allowed only when the correct answer is an"
            f" abstention token from {sorted(ABSTAIN_TOKENS)}")
    if mixed_ok and not _is_number(stage.get("tol")):
        raise ChainInvalid(f"{where} abstention stage needs 'tol' for its numeric decoy")
    if isinstance(correct, (list, tuple)):
        # Set-valued stage (which observations excluded, which levels kept).
        if not isinstance(decoy, (list, tuple)):
            raise ChainInvalid(f"{where} set-valued stage needs a set-valued decoy")
        c_set = {str(x).strip().lower() for x in correct}
        d_set = {str(x).strip().lower() for x in decoy}
        sym = c_set ^ d_set
        if not sym:
            raise ChainInvalid(f"{where} set decoy is identical to the correct set")
        biggest = max(len(c_set), len(d_set), 1)
        if len(sym) > max(3, round(0.5 * biggest)):
            raise ChainInvalid(
                f"{where} set decoy differs by {len(sym)} elements from a"
                f" {biggest}-element answer; a plausible wrong path differs by"
                " a few elements, not wholesale")
        return _finish_stage_checks(stage, where)
    if _is_number(correct):
        tol = stage.get("tol")
        if not _is_number(tol) or float(tol) <= 0:
            raise ChainInvalid(f"{where} numeric stage needs positive 'tol'")
        gap = abs(float(correct) - float(decoy))
        if gap < TRAP_MARGIN * float(tol):
            raise ChainInvalid(
                f"{where} trap separation too small: |{correct}-{decoy}|={gap:.6g}"
                f" < {TRAP_MARGIN}*tol={TRAP_MARGIN * float(tol):.6g}."
                " A careless analysis must fail by a clear margin.")
        # EVERY enumerated wrong analysis path must miss by the same margin,
        # not just the designated decoy. Campaign 3.0.0's exemplar had four
        # analysis paths of which three landed in-band (unweighted OLS passed
        # within 1% on seed 12), so the chain was compensatory and p^K never
        # multiplied. wrong_paths is the generator's own enumeration of the
        # {eligible set} x {weighting} x {rule choice} product.
        paths = stage.get("wrong_paths")
        if not isinstance(paths, list) or len(paths) < 2:
            raise ChainInvalid(
                f"{where} numeric stage needs 'wrong_paths': >=2 enumerated"
                " wrong-analysis values (the decoy is one path; a chain with"
                " a single wrong path is a coin flip, not a judgment)")
        for wrong in paths:
            value = wrong.get("value") if isinstance(wrong, dict) else wrong
            if not _is_number(value):
                raise ChainInvalid(f"{where} wrong_path {wrong!r} is not numeric")
            if abs(float(correct) - float(value)) <= TRAP_MARGIN * float(tol):
                raise ChainInvalid(
                    f"{where} wrong path {wrong!r} lands within"
                    f" {TRAP_MARGIN}*tol of the correct value {correct}: the"
                    " stage scores a careless analysis as correct")
        # The decoy must be ATTRACTIVE, not merely wrong: a value of the wrong
        # sign or off by orders of magnitude is one a competent analyst would
        # reject on sight, so it tests nothing.
        c_val, d_val = float(correct), float(decoy)
        if c_val != 0.0 and d_val != 0.0:
            if (c_val > 0) != (d_val > 0):
                raise ChainInvalid(
                    f"{where} decoy {decoy} has the opposite sign to the correct"
                    f" value {correct}; an implausible trap tests nothing")
            ratio = abs(d_val / c_val)
            if not (0.1 <= ratio <= 10.0):
                raise ChainInvalid(
                    f"{where} decoy/correct ratio {ratio:.3g} is outside [0.1, 10];"
                    " the wrong path must be plausible enough to be taken")
    else:
        if str(correct).strip().lower() == str(decoy).strip().lower():
            raise ChainInvalid(f"{where} token stage has identical correct/decoy")
        # With no menu in the prompt, categorical answers arrive as free-form
        # phrases and are matched against generator-authored aliases. Both
        # sides need aliases (except an abstention, whose vocabulary the
        # prompt may name), and no form on one side may boundary-match any
        # form on the other, or scoring becomes ambiguous.
        if str(correct).strip().lower() not in ABSTAIN_TOKENS:
            for side in ("correct_aliases", "decoy_aliases"):
                forms = stage.get(side)
                if not isinstance(forms, list) or not forms or \
                        not all(isinstance(f, str) and f.strip() for f in forms):
                    raise ChainInvalid(
                        f"{where} categorical stage needs non-empty {side!r}:"
                        " without a menu in the prompt, free-form answers are"
                        " matched via aliases")
            correct_forms = [str(correct)] + list(stage["correct_aliases"])
            decoy_forms = [str(decoy)] + list(stage["decoy_aliases"])
            # Disjointness must hold in the same normal forms the scorer
            # matches in - raw tokens AND with number/unit fillers stripped
            # (the scorer strips them so '1 0 nM' cannot break a phrase).
            from .score import _strip_fillers
            for a in correct_forms:
                for b in decoy_forms:
                    for norm in (_alias_token, lambda s: _strip_fillers(_alias_token(s))):
                        pa, pb = f"_{norm(a)}_", f"_{norm(b)}_"
                        if pa in pb or pb in pa:
                            raise ChainInvalid(
                                f"{where} alias overlap: correct form {a!r} and"
                                f" decoy form {b!r} would match the same answer")
    _finish_stage_checks(stage, where)


def _finish_stage_checks(stage: dict, where: str) -> None:
    """Fork metadata checks shared by every stage type."""
    if not isinstance(stage["fork"], str) or len(stage["fork"]) < 15:
        raise ChainInvalid(f"{where} 'fork' must describe the judgment call (>=15 chars)")
    keywords = stage.get("fork_keywords") or []
    if not isinstance(keywords, list) or not keywords:
        raise ChainInvalid(f"{where} needs non-empty 'fork_keywords' for notice detection")


def _renderings(value: float) -> set[str]:
    """Every plausible way the answer could be written into a shipped file."""
    forms = {f"{value:.6g}", f"{value:g}", repr(value), str(value)}
    for places in range(1, 7):
        forms.add(f"{value:.{places}f}")
    forms.add(f"{value:.3e}")
    if value == int(value):
        forms.add(str(int(value)))
    return {f for f in forms if len(f.replace("-", "").replace(".", "")) >= 4}


def leak_scan(payload: dict) -> list[str]:
    """Is any stage answer already sitting in what the candidate can read?

    The dominant real-world failure: CORE-Bench shipped values that made 20 of
    45 hard tasks answerable without doing the analysis, and nobody noticed
    until the benchmark saturated. Small integers (counts) are exempt - they
    are unavoidable and carry little information on their own.
    """
    visible = payload["prompt"] + "\n" + "\n".join(payload["artifacts"].values())
    visible_lower = visible.lower()
    findings = []
    for stage in payload["stages"]:
        correct = stage["correct"]
        if not _is_number(correct):
            continue
        value = float(correct)
        if abs(value) < 100 and value == int(value):
            continue                      # a bare count: exempt by necessity
        for form in _renderings(value):
            if form.lower() in visible_lower:
                findings.append(
                    f"stage {stage['key']!r} answer renders as {form!r}, which"
                    " already appears in the prompt or artifacts")
                break
    return findings


# A stage is only a judgment call if the candidate could plausibly get it
# wrong. Campaign 3.0.0 proved that is not automatic: frontier models scored
# 94-100% because the work order handed over the method as an ordered
# checklist and the answer schema printed the allowed values, turning every
# categorical judgment into multiple choice. `leak_scan` never caught it
# because it only inspects numeric stages. These gates close that.

# Verbs that name a scientific decision. Three or more in one sentence is a
# recipe: the candidate executes steps instead of deciding what the steps are.
METHOD_VERBS = (
    "apply", "identify", "select", "calculate", "compute", "diagnose",
    "decide", "fit", "quantify", "exclude", "determine", "assess",
    "evaluate", "check", "verify", "test", "estimate", "derive",
)
RECIPE_VERB_THRESHOLD = 3      # per sentence, any surface
RECIPE_VERBS_PER_PROMPT = 5    # total across the work order (spec P5)

# Sentences that steer the candidate away from the attractive wrong path.
# Noticing the trap is the skill being measured; a warning donates it.
DECOY_HINTS = (
    "does not by itself", "is not by itself", "not sufficient on its own",
    "is not enough on its own", "do not assume", "be careful not to",
    "beware", "may be misleading", "can be misleading", "resist the",
    "a good r-squared", "does not on its own", "should not be taken as",
)


def _token_present(token: str, text: str) -> bool:
    """Whole-token match, so 'RELEASE' does not fire inside 'released'."""
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])",
                     text, re.I) is not None


def giveaway_scan(payload: dict) -> list[str]:
    """Ways the candidate-visible material does the candidate's thinking.

    Scans the prompt AND every artifact (hardening spec section 0, root cause
    1): the audited recipes did not live in the work order, they lived in
    method_extract.txt and its siblings - the gate was blind to exactly the
    file that contained the answer sheet.
    """
    prompt = payload["prompt"]
    artifacts = payload.get("artifacts") or {}
    surfaces = [("prompt", prompt)] + [(f"artifact {n!r}", c)
                                       for n, c in artifacts.items()]
    findings = []

    # 1. OPTION MENU. If both the correct token and its decoy are printed, the
    #    stage is a multiple-choice question with the answer on the page. The
    #    final `decision` is exempt: its vocabulary is the output contract, and
    #    a candidate cannot emit a token it was never told exists. Intermediate
    #    stages have no such excuse - they are scored by alias, not by menu.
    for stage in payload["stages"]:
        correct, decoy = stage["correct"], stage.get("decoy")
        if _is_number(correct) or decoy is None or _is_number(decoy):
            continue
        if isinstance(correct, (list, tuple, set)):
            continue                      # set-valued: elements are data, not options
        if str(correct).strip().lower() in ABSTAIN_TOKENS:
            continue
        for where, text in surfaces:
            if _token_present(str(correct), text) and _token_present(str(decoy), text):
                findings.append(
                    f"stage {stage['key']!r} is multiple choice: {where} prints"
                    f" both {correct!r} and {decoy!r}, so the answer is on the page")
                break

    # 2. RECIPE. An ordered list of method verbs tells the candidate which
    #    judgments to make and in what order, which is most of the task.
    #    Threshold per hardening spec P5: 2 verbs in one sentence flags it,
    #    and 5 across a whole surface flags the surface even if no single
    #    sentence trips.
    for where, text in surfaces:
        total_hits = 0
        for sentence in re.split(r"(?<=[.!?:;])\s+", text):
            hits = [v for v in METHOD_VERBS
                    if re.search(rf"(?<![A-Za-z]){v}(?![A-Za-z])", sentence, re.I)]
            total_hits += len(hits)
            if len(hits) >= RECIPE_VERB_THRESHOLD:
                findings.append(
                    f"{where} dictates the method ({', '.join(sorted(hits))}):"
                    f" {sentence.strip()[:120]!r}")
        # The whole-surface budget applies to the WORK ORDER only: a prompt
        # can smuggle a recipe two verbs per sentence, but artifacts are
        # records, where scattered method verbs across hundreds of lines are
        # ordinary language, and only a stepwise sentence is a recipe.
        if where == "prompt" and total_hits >= RECIPE_VERBS_PER_PROMPT:
            findings.append(
                f"the prompt reads as a procedure: {total_hits} method verbs"
                f" in total (limit {RECIPE_VERBS_PER_PROMPT - 1}); state the"
                " deliverable, not the steps")

    # 3. DECOY HINT.
    for where, text in surfaces:
        lowered = text.lower()
        for hint in DECOY_HINTS:
            if hint in lowered:
                findings.append(
                    f"{where} warns the candidate away from the trap: {hint!r}")

    return findings


def check_payload(payload: dict, condition: str) -> None:
    """Structural gates for one generated instance."""
    for field in ("prompt", "artifacts", "stages", "decision",
                  "reference_answer", "weak_answer"):
        if field not in payload:
            raise ChainInvalid(f"payload missing '{field}'")

    stages = payload["stages"]
    if not isinstance(stages, list) or not (MIN_STAGES <= len(stages) <= MAX_STAGES):
        raise ChainInvalid(
            f"chain has {len(stages) if isinstance(stages, list) else '?'} stages;"
            f" required {MIN_STAGES}-{MAX_STAGES}")
    seen = set()
    for index, stage in enumerate(stages):
        check_stage(stage, index)
        if stage["key"] in seen:
            raise ChainInvalid(f"duplicate stage key {stage['key']!r}")
        seen.add(stage["key"])

    decision = payload["decision"]
    if not isinstance(decision, dict) or "correct" not in decision or "decoy" not in decision:
        raise ChainInvalid("decision must be {'correct': TOKEN, 'decoy': TOKEN}")
    if str(decision["correct"]).strip().lower() == str(decision["decoy"]).strip().lower():
        raise ChainInvalid("decision correct/decoy tokens are identical")

    artifacts = payload["artifacts"]
    if not isinstance(artifacts, dict) or not (1 <= len(artifacts) <= 8):
        raise ChainInvalid("artifacts must be a dict of 1-8 text files")
    for name, content in artifacts.items():
        if not isinstance(content, str) or not content.strip():
            raise ChainInvalid(f"artifact {name!r} is empty or not text")
        if len(content) > 400_000:
            raise ChainInvalid(f"artifact {name!r} exceeds 400k chars")

    prompt = payload["prompt"]
    if not isinstance(prompt, str) or len(prompt) < 500:
        raise ChainInvalid("prompt must be a substantial work order (>=500 chars)")

    # Truth must never be visible: no stage value may be printed verbatim in the
    # prompt, and no meta-vocabulary may appear in anything the candidate reads.
    visible = (prompt + "\n" + "\n".join(artifacts.values())).lower()
    for word in META_WORDS:
        if word in visible:
            raise ChainInvalid(f"meta-vocabulary {word!r} leaked into candidate-visible text")
    leaks = leak_scan(payload)
    if leaks:
        raise ChainInvalid(
            "answer leakage into candidate-visible material: " + "; ".join(leaks[:5]))
    giveaways = giveaway_scan(payload)
    if giveaways:
        raise ChainInvalid(
            "work order does the candidate's thinking for it: "
            + "; ".join(giveaways[:5]))

    # Rule constants (thresholds, critical values, limits the key depends on)
    # must be DERIVABLE from shipped data, never printed: a printed critical
    # value converts the rule-selection judgment into arithmetic. Generators
    # declare them; the scan holds them to the same standard as answers.
    for constant in payload.get("rule_constants") or []:
        if not _is_number(constant):
            continue
        for form in _renderings(float(constant)):
            if form.lower() in visible:
                raise ChainInvalid(
                    f"rule constant {constant} appears verbatim in candidate-"
                    f"visible text (as {form!r}); it must be derivable from"
                    " the data, not printed")

    for name in ("reference_answer", "weak_answer"):
        text = payload[name]
        if not isinstance(text, str) or "```json" not in text:
            raise ChainInvalid(f"{name} must end with a ```json answer block")
        if len(text) < 300:
            raise ChainInvalid(f"{name} is too short to be a real answer")

    if condition == "F2" and not payload.get("premise_flaw"):
        raise ChainInvalid("F2 instances must document 'premise_flaw'")
    if condition == "H1" and not payload.get("defect"):
        raise ChainInvalid("H1 instances must document 'defect'")


def answer_key(payload: dict) -> dict:
    """The machine-checkable key: {stage_key: (correct, decoy, tol)} + decision."""
    key = {"stages": {}, "decision": payload["decision"]}
    for stage in payload["stages"]:
        key["stages"][stage["key"]] = {
            "correct": stage["correct"], "decoy": stage["decoy"],
            "tol": stage.get("tol"), "label": stage["label"],
            "fork": stage["fork"], "fork_keywords": stage["fork_keywords"],
            "correct_aliases": stage.get("correct_aliases"),
            "decoy_aliases": stage.get("decoy_aliases"),
            # Full wrong-path enumeration, so the scorer can report WHICH
            # wrong analysis a failure converges on (discriminant D2).
            "decoys": [
                (w if isinstance(w, dict) else {"id": f"path{i}", "value": w})
                for i, w in enumerate(stage.get("wrong_paths") or [], 1)
            ],
        }
    return key
