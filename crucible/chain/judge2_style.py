"""Formatting normalisation shared by every judge in the project.

Markdown styling shifts judge preference far more than answer position does
(measured up to +0.76 for formatting versus <=0.04 for position in modern
judges), so submissions are stripped to their content before any model sees
them. The evidence-quote substring check runs against this same stripped text,
so a quote can never fail merely because a bullet or bold marker moved.
"""
from __future__ import annotations

import re


def strip_style(text: str) -> str:
    out = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)      # headings
    out = re.sub(r"\*\*(.+?)\*\*", r"\1", out)              # bold
    out = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", out)   # italics
    out = re.sub(r"^\s*[-*+]\s+", "- ", out, flags=re.M)    # bullet glyphs
    out = re.sub(r"^\s*>\s?", "", out, flags=re.M)          # block quotes
    out = re.sub(r"`([^`]*)`", r"\1", out)                  # inline code
    out = re.sub(r"\|", " ", out)                            # table pipes
    out = re.sub(r"[ \t]+", " ", out)
    return out.strip()
