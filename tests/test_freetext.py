"""Every free-text case that has cost this benchmark a correction.

Three corrections came from checkpoints reading model prose by substring. The
cases below are the exact sentences from those corrections, taken from the
recorded episodes, so a regression shows up here rather than in a scorecard.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crucible.lab.freetext import asserts, decided, says  # noqa: E402

INTERFERENCE = ("quench", "interfer", "artifact", "artefact", "optical",
                "absorb", "inner filter", "compound fluorescence")
INHIBITION = ("inhibit", "target engagement", "enzyme activity", "genuine",
              "real inhibition", "on-target")
SOUND = ("transfers", "carries over", "hold", "stands", "reproduc",
         "supported", "genuine", "legitimate", "survive", "confirm")
LEAK = ("leak", "echo", "encodes", "downstream", "inflat", "in-sample")


def test_ruling_an_explanation_out_is_not_claiming_it():
    """CORR-015. These are verbatim from failed episodes that were correct."""
    # Each of these both states the mechanism and rules the other one out,
    # which is what the failed-but-correct episodes actually wrote.
    for sentence in (
        "genuine dose-dependent enzymatic inhibition, confirming the compound "
        "does not interfere with the fluorescence readout",
        "target engagement is real and the no-enzyme control rules out quenching",
        "this is enzyme inhibition; there is no evidence of optical interference",
        "genuine inhibition, not an artifact of compound fluorescence",
        "the signal loss is inhibition rather than quenching",
    ):
        assert not asserts(sentence, INTERFERENCE), sentence
        assert asserts(sentence, INHIBITION), sentence

    # Ruling interference out without naming a mechanism is not an answer, and
    # the matcher must not invent one.
    assert not asserts("the compound does not interfere with the readout",
                       INHIBITION)


def test_claiming_interference_still_registers():
    for sentence in (
        "the compound quenches the assay readout rather than inhibiting the enzyme",
        "an inner filter effect accounts for the apparent potency",
        "this is an optical artefact of compound fluorescence",
    ):
        assert asserts(sentence, INTERFERENCE), sentence
        assert not asserts(sentence, INHIBITION), sentence


def test_the_reports_own_words_are_not_claims_about_it():
    """CORR-015. "hold" inside "holdout" is the report's noun, not a claim."""
    for sentence in (
        "the holdout set shares scaffolds with training",
        "every held-out compound appears in the fit",
        "the reported holdout_auc is 0.82 above the threshold",
        "the 42 genuinely unseen compounds separate cleanly",
    ):
        assert not asserts(sentence, SOUND), sentence


def test_a_soundness_claim_still_registers():
    for sentence in (
        "the relation holds on the unseen compounds",
        "the effect reproduces out of sample",
        "this is a genuine predictor and it transfers",
    ):
        assert asserts(sentence, SOUND), sentence


def test_leakage_claims_and_their_negations():
    assert asserts("stock_conc_uM leaks the label", LEAK)
    assert not asserts("no evidence of label leakage in any column", LEAK)
    assert not asserts("the feature does not leak the outcome", LEAK)


def test_word_boundaries_hold_both_ways():
    # says() is the raw test and knows nothing about the report's vocabulary;
    # asserts() is what a checkpoint calls, and that is where "holdout" stops
    # counting as a claim that something holds.
    assert says("the relation holds", ("hold",))
    assert says("reproducible across batches", ("reproduc",))
    assert not asserts("the holdout is contaminated", ("hold",))
    assert not asserts("shareholder value", ("hold",))
    assert asserts("the relation holds", ("hold",))


def test_decided_leaves_unnegated_text_alone():
    text = "the compound quenches the readout"
    assert "quench" in decided(text, INTERFERENCE)


if __name__ == "__main__":
    import subprocess
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
