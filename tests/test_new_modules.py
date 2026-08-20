"""Offline tests for the modules added in the model-expert build (no API calls)."""
from pathlib import Path

from crucible import simlab
from crucible.shortcuts import artifact_spoof_attack, card_language_audit
from crucible.stats import cluster_bootstrap_rate, wilson_interval
from crucible.tracks.trackG import _score


def test_simlab_is_deterministic():
    a = simlab.simulate(95.0, "Pd-B", "DMF", 1)
    b = simlab.simulate(95.0, "Pd-B", "DMF", 1)
    assert a == b


def test_simlab_threshold_structure():
    # The optimum region must exceed the threshold; disclosed data must not.
    assert simlab.simulate(95.0, "Pd-B", "DMF", 1) >= simlab.SUCCESS_THRESHOLD
    for m in simlab.disclosed_measurements():
        assert m["yield_percent"] < simlab.SUCCESS_THRESHOLD
    # Non-optimal catalyst/solvent must not reach threshold anywhere sampled.
    for temp in range(40, 121, 10):
        assert simlab.simulate(float(temp), "Ni-C", "ethanol", 1) < simlab.SUCCESS_THRESHOLD


def test_simlab_rejects_out_of_space():
    import pytest

    with pytest.raises(ValueError):
        simlab.simulate(200.0, "Pd-B", "DMF", 1)


def test_wilson_interval_sane():
    low, high = wilson_interval(3, 5)
    assert 0.0 <= low < 0.6 < high <= 1.0
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_cluster_bootstrap_counts_clusters():
    outcomes = [
        {"template": "T1", "reliable_completion": True},
        {"template": "T1", "reliable_completion": False},
        {"template": "T2", "reliable_completion": True},
    ]
    result = cluster_bootstrap_rate(outcomes)
    assert result["n_clusters"] == 2
    assert result["denominator"] == 3


def test_trackG_scorer_rewards_good_process():
    checkpoint = {
        "candidate_hypotheses": [
            {"id": "H1", "text": "The unknown is within the calibrated range", "probability": 0.5},
            {"id": "H2", "text": "The unknown is above the calibration range", "probability": 0.3},
            {"id": "H3", "text": "The peak is an artifact", "probability": 0.2},
        ],
        "predictions": [
            {"hypothesis_id": "H1", "expected_observation": "area between 5000 and 100000"},
            {"hypothesis_id": "H2", "expected_observation": "area above 100240"},
        ],
        "decision_rule": "report only if within range",
    }
    update = {
        "updated_hypotheses": [{"id": "H1", "probability": 0.02}, {"id": "H2", "probability": 0.95}],
        "evidence_interpretation": "area 160480 is above the highest standard",
        "chosen_action": "dilute and rerun",
        "decision_token": "not_reportable_dilute",
        "final_claim": "cannot be reported; above the validated range",
    }
    scores = _score(checkpoint, update)
    assert scores["true_explanation_pre_registered"]
    assert scores["prediction_commitment"]
    assert scores["final_decision_correct"]
    assert scores["evidence_uptake_delta"] > 0
    assert scores["failure_codes"] == []


def test_trackG_scorer_flags_bad_process():
    checkpoint = {"candidate_hypotheses": [{"id": "H1", "text": "all fine", "probability": 1.0}],
                  "predictions": [], "decision_rule": ""}
    update = {"updated_hypotheses": [{"id": "H1", "probability": 1.0}],
              "evidence_interpretation": "looks fine",
              "chosen_action": "report", "decision_token": "reportable",
              "final_claim": "reportable"}
    scores = _score(checkpoint, update)
    assert "G-NOALT" in scores["failure_codes"]
    assert "G-NOPRED" in scores["failure_codes"]
    assert not scores["final_decision_correct"]


def test_card_language_audit_resists(repo_root: Path):
    base = repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "instances"
    result = card_language_audit(base / "N0-s101" / "task_card" / "card.md",
                                 base / "N1-s102" / "task_card" / "card.md")
    assert result["verdict"] == "resisted", result


def test_artifact_spoof_fails_verification(repo_root: Path):
    task = repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "instances" / "N0-s101"
    result = artifact_spoof_attack(task)
    assert result["verdict"] == "resisted"
