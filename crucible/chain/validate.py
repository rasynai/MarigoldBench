"""Validity gates for a chain template (design doc section 6).

A template enters the benchmark only if it is deterministic, trap-separated,
condition-symmetric, solvable by its own reference answer, defeated by its own
weak answer, and not guessable without the artifacts. Everything here is
mechanical; the model-graded hostile review runs afterwards, on top.
"""
from __future__ import annotations

from .sandbox2 import run_chain_generator
from .score import score_chain
from .spec import CONDITIONS, ChainInvalid, answer_key, check_payload


def _stage_signature(payload: dict) -> list:
    return [(s["key"], s["correct"], s["decoy"], s.get("tol")) for s in payload["stages"]]


def validate_chain_template(generator_src: str, seeds: list[int],
                            determinism_reps: int = 2) -> dict:
    """Run every (seed, condition), enforce the gates, return the payloads."""
    payloads: dict = {}
    for seed in seeds:
        per_condition = {}
        for condition in CONDITIONS:
            payload = run_chain_generator(generator_src, seed, condition)
            check_payload(payload, condition)

            # 1. determinism: identical output across repeated executions
            for _ in range(determinism_reps):
                again = run_chain_generator(generator_src, seed, condition)
                if _stage_signature(again) != _stage_signature(payload) \
                        or again["prompt"] != payload["prompt"] \
                        or again["artifacts"] != payload["artifacts"]:
                    raise ChainInvalid(
                        f"generator is non-deterministic at ({seed},{condition})")

            key = answer_key(payload)

            # 2. the reference answer must actually complete the chain
            reference = score_chain(payload["reference_answer"], key)
            if not reference["vcc"]:
                raise ChainInvalid(
                    f"reference answer fails its own chain at ({seed},{condition}):"
                    f" first failure {reference['first_failed_stage']},"
                    f" decision_correct={reference['decision_correct']}")

            # 3. the weak answer must fail AND take at least one baited path,
            #    proving the trap is reachable rather than merely declared
            weak = score_chain(payload["weak_answer"], key)
            if weak["vcc"]:
                raise ChainInvalid(f"weak answer completes the chain at ({seed},{condition})")
            if not weak["any_trap"]:
                raise ChainInvalid(
                    f"weak answer trips no decoy at ({seed},{condition});"
                    " the attractive wrong path is not actually reachable")

            per_condition[condition] = payload

        # 4. condition symmetry: a clean and a defective instance must be
        #    indistinguishable from the work order alone
        if per_condition["C0"]["prompt"] != per_condition["H1"]["prompt"]:
            raise ChainInvalid(f"C0/H1 prompts differ (seed {seed}) - the condition leaks")
        if set(per_condition["C0"]["artifacts"]) != set(per_condition["H1"]["artifacts"]):
            raise ChainInvalid(f"C0/H1 artifact file names differ (seed {seed})")

        # 5. the chain must actually change across conditions, or the three
        #    conditions are cosmetic
        c0_sig = _stage_signature(per_condition["C0"])
        h1_sig = _stage_signature(per_condition["H1"])
        if c0_sig == h1_sig:
            raise ChainInvalid(f"C0 and H1 have identical answer keys (seed {seed})")

        payloads[seed] = per_condition

    # 6. seed variation: different seeds must produce different instances
    first, *rest = list(payloads)
    for other in rest:
        if _stage_signature(payloads[first]["C0"]) == _stage_signature(payloads[other]["C0"]):
            raise ChainInvalid(f"seeds {first} and {other} produce identical answer keys")
    return payloads


def guessability_probe(payload: dict) -> dict:
    """Cheap structural probe for the B0 'answerable without the artifacts'
    failure: how much of the chain is recoverable from round numbers or from
    values printed in the prompt. A model run is the real B0 baseline; this
    catches the obvious cases before spending tokens."""
    key = answer_key(payload)
    prompt = payload["prompt"].lower()
    suspicious = []
    for stage_key, spec in key["stages"].items():
        correct = spec["correct"]
        if isinstance(correct, (int, float)) and not isinstance(correct, bool):
            value = float(correct)
            if value == round(value) and abs(value) < 1000:
                suspicious.append((stage_key, "round integer answer"))
            if f"{value:g}" in prompt:
                suspicious.append((stage_key, "answer appears in prompt"))
        else:
            if str(correct).strip().lower() in prompt:
                suspicious.append((stage_key, "token answer appears in prompt"))
    return {"suspicious_stages": suspicious,
            "n_suspicious": len(suspicious),
            "n_stages": len(key["stages"])}
