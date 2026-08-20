"""The giveaway gate: a work order must not do the candidate's thinking.

Campaign 3.0.0 measured 94-100% for frontier models against a single-digit
design target. The cause was not that the science was easy; it was that the
prompt handed over the method as an ordered checklist and printed the allowed
answers, so every categorical judgment was multiple choice. `leak_scan` missed
it entirely because it only inspects numeric stages.

Both directions are tested. An over-broad gate is its own failure mode: an
earlier revision of META_WORDS banned "trap" and "hazard" and rejected valid
mass-spectrometry and survival-analysis tasks.
"""
from __future__ import annotations

import pytest

from crucible.chain.spec import ChainInvalid, check_payload, giveaway_scan


def _payload(prompt: str, stages=None, **overrides) -> dict:
    stages = stages or [
        {"key": "n_standards", "label": "eligible standards", "correct": 6,
         "decoy": 7, "tol": 0.2, "wrong_paths": [7, 5], "fork": "which standards are eligible", "fork_keywords": ["standards"]},
        {"key": "slope", "label": "calibration slope", "correct": 1916.17,
         "decoy": 2472.2, "tol": 1.0, "wrong_paths": [2472.2, 1890.0], "fork": "which regression treatment the data require", "fork_keywords": ["regression"]},
        {"key": "conc_nM", "label": "unknown concentration", "correct": 4.6,
         "decoy": 4.74, "tol": 0.03, "wrong_paths": [4.74, 4.41], "fork": "which curve the unknown is read from", "fork_keywords": ["curve"]},
        {"key": "quantifiable", "label": "quantifiability", "correct": "ABOVE_LLOQ",
         "decoy": "BELOW_LLOQ", "tol": 0,
         "correct_aliases": ["above the lloq"], "decoy_aliases": ["below the lloq"],
         "fork": "whether the result clears the validated limit", "fork_keywords": ["the"]},
        {"key": "batch_state", "label": "batch state", "correct": "IN_CONTROL",
         "decoy": "OUT_OF_CONTROL", "tol": 0,
         "correct_aliases": ["within control limits"], "decoy_aliases": ["excursion"],
         "fork": "whether the batch is in statistical control", "fork_keywords": ["the"]},
    ]
    payload = {
        "prompt": prompt,
        "artifacts": {"data.csv": "sample_id,peak_area\nS1,1234\n"},
        "stages": stages,
        "decision": {"correct": "RELEASE", "decoy": "DO_NOT_RELEASE"},
        "reference_answer": "x" * 320 + "\n```json\n{}\n```",
        "weak_answer": "y" * 320 + "\n```json\n{}\n```",
    }
    payload.update(overrides)
    return payload


CLEAN_PROMPT = (
    "You are the bioanalytical reviewer releasing a single clinical PK sample. "
    "The calibration standards, the preparation log for the batch, the method "
    "note extract, and the unknown's peak area are attached. Report the plasma "
    "concentration of the unknown and state whether the result can be issued "
    "as a numeric value. Show the numbers you rely on and state any assumption "
    "you had to make. Finish with a machine-readable JSON block whose field "
    "names are listed below, and give a calibrated confidence in [0,1] for "
    "each field, read as the probability that your value is correct. "
) * 2


# --------------------------------------------------------------- must reject

def test_option_menu_is_rejected():
    prompt = CLEAN_PROMPT + (
        "\nquantifiable: one of ABOVE_LLOQ or BELOW_LLOQ.")
    findings = giveaway_scan(_payload(prompt))
    assert any("multiple choice" in f for f in findings)
    assert any("quantifiable" in f for f in findings)


def test_recipe_sentence_is_rejected():
    prompt = CLEAN_PROMPT + (
        "\nApply the stated single-point test, identify the error structure, "
        "select the permitted calibration treatment, and calculate the slope.")
    findings = giveaway_scan(_payload(prompt))
    assert any("dictates the method" in f for f in findings)


def test_decoy_hint_is_rejected():
    prompt = CLEAN_PROMPT + (
        "\nA good r-squared does not by itself answer the work order.")
    findings = giveaway_scan(_payload(prompt))
    assert any("warns the candidate away" in f for f in findings)


def test_check_payload_raises_on_a_giveaway():
    prompt = CLEAN_PROMPT + "\nquantifiable: ABOVE_LLOQ or BELOW_LLOQ."
    with pytest.raises(ChainInvalid, match="does the candidate's thinking"):
        check_payload(_payload(prompt), "C0")


# ---------------------------------------------------------------- must pass

def test_clean_work_order_passes():
    assert giveaway_scan(_payload(CLEAN_PROMPT)) == []


def test_decision_vocabulary_is_allowed():
    """The candidate cannot emit a decision token it was never told exists, so
    the terminal output contract is exempt - unlike intermediate stages, which
    are judge-scored and need no menu."""
    prompt = CLEAN_PROMPT + (
        "\ndecision: one of RELEASE, DO_NOT_RELEASE, or PUSH_BACK.")
    assert giveaway_scan(_payload(prompt)) == []


def test_two_method_verbs_are_not_a_recipe():
    """Ordinary instructions use these verbs. Only an enumerated procedure -
    three or more in one sentence - donates the method."""
    prompt = CLEAN_PROMPT + (
        "\nDetermine the reportable result and check it against the "
        "specification.")
    assert giveaway_scan(_payload(prompt)) == []


def test_verbs_split_across_sentences_are_not_a_recipe():
    prompt = CLEAN_PROMPT + (
        "\nDetermine the result. Then verify the outcome. Report what you find.")
    assert giveaway_scan(_payload(prompt)) == []


def test_abstention_token_is_not_a_menu():
    """An abstention token must be nameable in the prompt or the candidate
    cannot express 'I cannot determine this'."""
    stages = [
        {"key": "conc_nM", "label": "concentration", "correct": "cannot_determine",
         "decoy": "4.74", "tol": 0, "fork": "which curve the unknown is read from", "fork_keywords": ["curve"]},
        {"key": "n_standards", "label": "standards", "correct": 6, "decoy": 7,
         "tol": 0.2, "wrong_paths": [7, 5], "fork": "which standards are eligible", "fork_keywords": ["standards"]},
        {"key": "slope", "label": "slope", "correct": 1916.17, "decoy": 2472.2, "tol": 1.0, "wrong_paths": [2472.2, 1890.0], "fork": "which regression treatment the data require", "fork_keywords": ["regression"]},
        {"key": "purity", "label": "purity", "correct": 99.4, "decoy": 97.1, "tol": 0.1, "wrong_paths": [97.1, 98.2], "fork": "which impurity peaks are integrated", "fork_keywords": ["impurity"]},
        {"key": "yield_pct", "label": "yield", "correct": 88.2, "decoy": 79.5, "tol": 0.2, "wrong_paths": [79.5, 84.0], "fork": "which fractions are counted as product", "fork_keywords": ["fractions"]},
    ]
    prompt = CLEAN_PROMPT + "\nUse the string cannot_determine if it is not determinable."
    assert giveaway_scan(_payload(prompt, stages=stages)) == []


def test_substring_tokens_do_not_false_positive():
    """'RELEASE' inside 'released' must not count as printing the token."""
    stages = [
        {"key": "batch_state", "label": "state", "correct": "RELEASE",
         "decoy": "HOLD", "tol": 0,
         "correct_aliases": ["issue the certificate"], "decoy_aliases": ["quarantine"],
         "fork": "whether the batch is in statistical control", "fork_keywords": ["the"]},
        {"key": "n_standards", "label": "standards", "correct": 6, "decoy": 7,
         "tol": 0.2, "wrong_paths": [7, 5], "fork": "which standards are eligible", "fork_keywords": ["standards"]},
        {"key": "slope", "label": "slope", "correct": 1916.17, "decoy": 2472.2, "tol": 1.0, "wrong_paths": [2472.2, 1890.0], "fork": "which regression treatment the data require", "fork_keywords": ["regression"]},
        {"key": "purity", "label": "purity", "correct": 99.4, "decoy": 97.1, "tol": 0.1, "wrong_paths": [97.1, 98.2], "fork": "which impurity peaks are integrated", "fork_keywords": ["impurity"]},
        {"key": "yield_pct", "label": "yield", "correct": 88.2, "decoy": 79.5, "tol": 0.2, "wrong_paths": [79.5, 84.0], "fork": "which fractions are counted as product", "fork_keywords": ["fractions"]},
    ]
    prompt = CLEAN_PROMPT + "\nState whether the material may be released or held."
    assert giveaway_scan(_payload(prompt, stages=stages)) == []
