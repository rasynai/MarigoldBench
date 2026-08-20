"""Structural validation of an authored 2.0 template (pre-review gate)."""
from __future__ import annotations

import re

from .sandbox import run_generator

CONDITIONS = ["C0", "H1", "F2"]


class TemplateInvalid(Exception):
    pass


def _fmt(text: str, truth: dict) -> str:
    out = text
    for key, value in truth.items():
        out = out.replace("{" + key + "}", str(value))
    return out


def render_rubric(rubric: list[dict], truth: dict, condition: str) -> list[dict]:
    rendered = []
    for item in rubric:
        conds = item.get("conditions") or CONDITIONS
        if condition not in conds:
            continue
        text = _fmt(item["text"], truth)
        if re.search(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", text):
            raise TemplateInvalid(
                f"rubric {item.get('id')} has unresolved placeholder after render: {text[:120]}")
        rendered.append({**item, "text": text})
    return rendered


def validate_template(sections: dict, seeds: list[int]) -> dict:
    """Run the generator for seeds x conditions and enforce the invariants.
    Returns {(seed, condition): payload} on success; raises TemplateInvalid."""
    rubric = sections["RUBRIC"]
    schema = sections["ANSWER_SCHEMA"]
    if not isinstance(rubric, list) or not (12 <= len(rubric) <= 26):
        raise TemplateInvalid(f"rubric has {len(rubric) if isinstance(rubric, list) else '?'} items")
    field_names = {f["name"] for f in schema.get("fields", [])}
    if "decision" not in field_names or not (2 <= len(field_names) <= 6):
        raise TemplateInvalid(f"answer schema fields bad: {sorted(field_names)}")
    groups = {i.get("group") for i in rubric}
    for needed in ("anchor", "method", "comm", "notice", "act", "penalty"):
        if needed not in groups:
            raise TemplateInvalid(f"rubric missing group '{needed}'")
    for item in rubric:
        if item.get("group") == "penalty" and item.get("points", 0) >= 0:
            raise TemplateInvalid(f"penalty {item.get('id')} has non-negative points")
        if item.get("group") != "penalty" and item.get("points", 0) <= 0:
            raise TemplateInvalid(f"{item.get('id')} has non-positive points")
        auto = item.get("auto")
        if auto and auto.get("field") not in field_names:
            raise TemplateInvalid(f"auto check on unknown field {auto.get('field')}")

    payloads: dict = {}
    for seed in seeds:
        per_cond = {}
        for condition in CONDITIONS:
            payload = run_generator(sections["GENERATOR"], seed, condition)
            per_cond[condition] = payload
            truth = payload["truth"]
            if not isinstance(truth, dict) or "decision" not in truth:
                raise TemplateInvalid(f"truth lacks 'decision' ({seed},{condition})")
            rendered = render_rubric(rubric, truth, condition)
            pos = sum(i["points"] for i in rendered if i["points"] > 0)
            if not (90 <= pos <= 110):
                raise TemplateInvalid(
                    f"positive points {pos} for ({seed},{condition}) not ~100")
            for item in rendered:
                auto = item.get("auto")
                if auto and auto.get("truth_key") not in truth:
                    raise TemplateInvalid(
                        f"auto truth_key {auto.get('truth_key')} missing from truth")
            for answer_name in ("reference_answer", "weak_answer"):
                if "```json" not in payload[answer_name]:
                    raise TemplateInvalid(f"{answer_name} lacks final json block")
            if len(payload["prompt"]) < 400:
                raise TemplateInvalid(f"prompt too short ({seed},{condition})")
        if per_cond["C0"]["prompt"] != per_cond["H1"]["prompt"]:
            raise TemplateInvalid(f"C0/H1 prompt symmetry violated (seed {seed})")
        payloads[seed] = per_cond
    return payloads
