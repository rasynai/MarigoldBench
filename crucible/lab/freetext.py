"""One matcher for every checkpoint that reads a model's free text.

Three separate corrections have now come from two families each keeping their
own literal phrase list and their own substring test:

  * CORR-004 replaced a regex that passed in isolation and failed in situ.
  * The CORRECTIONS audit log records "free-text scored as a hedge, our defect,
    twice" for assay-mechanism, pose-triage and lead-opt.
  * CORR-015 found the same class again: "does not interfere" and "rules out
    quenching" were read as claiming interference, and the soundness vocabulary
    fired on "holdout", "held-out", "threshold" and "genuinely unseen", which
    are the report's own words rather than any claim about it.

A literal list cannot be completed by inspection, so this module replaces the
lists with two rules and one place to test them:

  1. Negation is generative. The target stems are compiled INTO the pattern, so
     a negating opener followed by that stem inside the same clause cancels it.
     An earlier draft post-checked a lazily matched span and cancelled nothing,
     which is the same failure mode as CORR-004 and is why the tests below
     assert the negation cases directly.
  2. Vocabulary matches on a word boundary, and phrases the report itself
     supplies are removed before matching, so "hold" cannot fire on "holdout"
     while "holds" still fires.

`tests/test_freetext.py` holds the cases from all three corrections.
"""
from __future__ import annotations

import re
from functools import lru_cache

# Openers that name an explanation only to rule it out.
NEGATORS = (
    "not", "no", "never", "without", "excludes", "exclude", "excluding",
    "excluded", "rules out", "rule out", "ruled out", "ruling out",
    "rather than", "instead of", "as opposed to", "free of", "absence of",
    "no evidence of", "no evidence for", "no sign of", "inconsistent with",
    "cannot be", "is not", "are not", "does not", "do not", "did not",
    "fails to", "failed to", "nothing is",
)

# Words a report supplies that are not claims about the report.
REPORT_VOCAB = (
    "holdout", "hold-out", "held-out", "held out", "threshold", "thresholds",
    "holdout_auc", "genuinely unseen", "genuinely new", "genuinely held",
    "stronghold", "household", "shareholder",
)

_OPENERS = "|".join(re.escape(n) for n in sorted(NEGATORS, key=len, reverse=True))


@lru_cache(maxsize=256)
def _negation(stems: tuple[str, ...]) -> re.Pattern:
    """Negating opener, then within one clause, one of these stems."""
    # Multi-word targets count too: "not an artifact of compound fluorescence"
    # negates both "artifact" and the phrase "compound fluorescence", and
    # leaving the phrase behind was how an earlier draft of this still failed.
    targets = "|".join(
        re.escape(s.lower()).replace(r"\ ", r"\s+")
        for s in sorted(stems, key=len, reverse=True))
    # After the first negated stem, keep consuming FURTHER stems and the short
    # gaps between them, so "no evidence of optical interference" is cancelled
    # whole rather than leaving "interference" behind. The gap is deliberately
    # small: in "no interference but genuine inhibition" the run stops at "but"
    # and the affirmative clause survives.
    return re.compile(r"\b(?:" + _OPENERS + r")\b[^.;:!?]{0,48}?\b(?:"
                      + targets + r")\w*"
                      + r"(?:[^.;:!?]{0,12}?\b(?:" + targets + r")\w*)*", re.I)


def decided(text: str, targets: tuple[str, ...] = ()) -> str:
    """Lowercase text with negated mentions of `targets` and the report's own
    vocabulary removed, so what is left is what the answer asserts."""
    lowered = str(text or "").lower()
    for phrase in sorted(REPORT_VOCAB, key=len, reverse=True):
        lowered = lowered.replace(phrase, " ")
    if not targets:
        return lowered
    stems = tuple(t.lower() for t in targets if t and t.strip())
    if not stems:
        return lowered
    pattern = _negation(stems)
    # Two passes: one clause can carry two negated mentions.
    for _ in range(2):
        lowered = pattern.sub(" ", lowered)
    return lowered


def says(text: str, vocabulary) -> bool:
    """True when the text contains any vocabulary entry on a word boundary.

    Single words match their inflections; multi-word entries match as phrases.
    This is the raw test: it does not know about negation. Use `asserts` for a
    checkpoint.
    """
    lowered = str(text or "").lower()
    for entry in vocabulary:
        entry = entry.strip().lower()
        if not entry:
            continue
        if " " in entry or "-" in entry:
            if entry in lowered:
                return True
            continue
        if re.search(r"\b" + re.escape(entry) + r"\w*", lowered):
            return True
    return False


def asserts(text: str, vocabulary, negate_stems: tuple[str, ...] = ()) -> bool:
    """`says`, after removing negated clauses and the report's own words."""
    return says(decided(text, negate_stems or tuple(vocabulary)), vocabulary)
