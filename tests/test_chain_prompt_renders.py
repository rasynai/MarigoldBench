"""The author prompt is assembled with str.format(), so any stray brace in its
own instruction text is read as a placeholder. One added rule containing an
f-string example raised KeyError('value') on every template in a 30-template
build - 28 crashes from one unescaped brace. This test renders the real
prompt so that failure can never reach a build again.
"""
from crucible.chain.author import AUTHOR_TEMPLATE
from crucible.chain.exemplar import EXEMPLAR_GENERATOR
from crucible.chain.spec import MAX_STAGES, MIN_STAGES


def test_author_prompt_renders_with_real_arguments():
    rendered = AUTHOR_TEMPLATE.format(
        area_desc="analytical chemistry",
        workflow_desc="quantitative analysis",
        idea="a seeded scenario",
        exemplar=EXEMPLAR_GENERATOR.strip(),
        min_stages=MIN_STAGES,
        max_stages=MAX_STAGES,
    )
    assert len(rendered) > 5000
    assert "printf-style %-formatting" in rendered
    assert "===GENERATOR===" in rendered


def test_exemplar_avoids_percent_formatting():
    """Authors copy the exemplar's style, and scientific text is full of
    literal percent signs, so the exemplar must not model %-formatting."""
    for line in EXEMPLAR_GENERATOR.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or '"' not in stripped:
            continue
        # A '%' used for string interpolation appears as `" % (` or `" % x`.
        assert '" % ' not in stripped and "' % " not in stripped, line
