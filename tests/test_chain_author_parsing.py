"""The generator a model writes legitimately contains a nested ```json fence
inside the prompt string it builds. A non-greedy fence regex stops there and
truncates the module mid-string, which surfaces as an unterminated string
literal and silently killed every early template build.
"""
from crucible.chain.author import parse_sections

NESTED_FENCE_DOC = '''===TITLE===
Release decision for a batch
===DESIGN_NOTES===
notes that are hidden from candidates
===GENERATOR===
```python
def gen(seed, condition):
    prompt = "\\n".join([
        "Do the analysis and finish with a block of exactly this shape:",
        "```json",
        '{"value": 0.0, "decision": "RELEASE"}',
        "```",
    ])
    return {"prompt": prompt, "artifacts": {}, "stages": []}
```
===RUBRIC===
[]
===ANSWER_SCHEMA===
{"fields": []}
'''


def test_nested_json_fence_does_not_truncate_the_generator():
    code = parse_sections(NESTED_FENCE_DOC)["GENERATOR"]
    assert "def gen(seed, condition):" in code
    assert "return {" in code, "generator was truncated at the nested fence"
    compile(code, "genmod.py", "exec")


def test_generator_without_a_fence_is_passed_through():
    doc = NESTED_FENCE_DOC.replace("```python\n", "").replace("\n```\n===RUBRIC", "\n===RUBRIC")
    code = parse_sections(doc)["GENERATOR"]
    assert "def gen(seed, condition):" in code
