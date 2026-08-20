# CRUCIBLE program charter (pilot)

**Accountable sponsor:** Ansh Tiwari (project owner). The sponsor set the
program direction ("build this benchmark; use OpenAI and Anthropic models as
a replacement for scientists"), approves budget (API spend), and holds stop
authority.

**Mission:** implement and operate the CRUCIBLE validity-first evaluation
program for scientific agents, at pilot scale, on this repository.

**Non-goals:** no public leaderboard, no capability marketing, no claims about
real scientists or real laboratories (see docs/LIMITATIONS.md).

**Standing substitution decision (sponsor-approved, 2026-08-14):** all expert
and participant roles that the guide assigns to humans are filled by LLM
panels — OpenAI `gpt-5.6-sol` and Anthropic `claude-opus-5` — with the two
families kept independent wherever the guide requires independent review.
Every artifact produced under this substitution is labeled MODEL-SIMULATED or
carries an explicit claim boundary.

**Negative-result commitment:** failed runs, failed audits, and negative
outcomes are retained and published inside this repository; nothing is deleted
to improve appearances. The sponsor signed off on this by adopting the guide.

**Stop authority:** the sponsor, or any release-gate failure classified
release-blocking in guide section 29.14.
