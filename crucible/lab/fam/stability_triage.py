"""Family: stability triage - which designed candidate is fit to progress?

A protein-engineering group ends every design round with the same artifact: a
shortlist of short sequences and a table of numbers a sequence-only model
produced for them. The number is cheap, the wet-lab slot is not, and the
failure this family is built around is the one PoseBusters made famous in the
docking literature - the metric everyone reports can be excellent for an
artifact that is not physically credible. A sequence-only stability model
scores amino-acid composition and local context; it cannot see whether the
chain has a fold at all, so its best-scoring entry can be a sequence that
folds into nothing.

The project rule is therefore a conjunction: the highest predicted stability
AMONG the candidates whose predicted structure is credible. Neither single
ranking is a path to it. The layout guarantees that the top-scoring candidate
is never the most confidently folded one, so "fold everything and take the
most confident" is wrong in C0; and the shipped table is what fails in H1, so
"trust the spec" is wrong there.

Constructed truth. The generator owns two things: which slot carries a folded
domain and which carries a composition-preserving scramble of that same
domain, and which stability number is attached to each slot. It does not own
the fold confidence, so the confidence is MEASURED, not asserted:

  * every POOL string carries the mean per-residue confidence ESMFold actually
    returned for that exact sequence (runs/_pool_build.py against the NVIDIA
    ESMFold NIM), under four averaging conventions. Those numbers arrange the
    trap and are a fallback of last resort - they are never the graded answer.
  * verify() re-derives the answer end to end: it re-parses the shipped FASTA
    and spec, re-obtains each structure from the tool record (or re-calls
    ESMFold), re-parses the confidence column of the returned PDB, re-reads the
    eligibility line out of the shipped criteria, and applies the rule to the
    numbers it just computed. A generator bug shows up as a disagreement in
    detail["design_agrees"] instead of propagating into a score.

Conventions. A candidate can average that column four defensible ways: over CA
atoms or over all atoms, and over the whole chain or over the part of the PDB
that survives the harness's 6000-character truncation of a tool result. Those
four readings of one structure differ by up to 12.1 points, which is larger
than any honesty tolerance worth having, so the reported number is graded
against the band the four conventions span rather than against the verifier's
own favourite - and the verifier reconstructs all four from the same PDB, so
the band is measurement, not allowance. Every pool member was then screened so
the band never crosses the project's line: the lowest number any folded member
produces under any convention is 79.2 and the highest any scramble produces is
50.8, a 28.4-point separation, so the 70.0 line classifies identically under
all four and a value inside one class's band cannot have come from the other.
Tool choice does not move the call either: co-folding the same pair with Boltz-2
returns 0.92 for the folded member and 0.58 for its scramble, the same side of
the line as ESMFold puts them on. The claimed property is quoted in kcal/mol
and is always negative, so it can never be mistaken for a measurement of the
structure - copying it into the reported confidence fails rather than passing
by a coincidence of range.

Conditions
  C0  the spec is sound: the top-scoring candidate does fold, so it is the one
      that progresses, and a candidate that reports a problem is wrong. The
      other two graded fields still require every candidate to be measured.
  H1  byte-identical brief and byte-identical spec; the FASTA differs in
      exactly one line, where the top-scoring candidate's sequence is replaced
      by a scramble of itself (same length, same composition, same spec row).
      The answer moves to a lower-scoring candidate.
  F2  every candidate is a scramble. Nothing clears the structural line, no
      expression slot can be filled, and a documented refusal - stated, with
      the numbers that support it - is the only correct outcome.
"""
from __future__ import annotations

import json
import random
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

from ..families import Episode, Verdict

# The project's eligibility line, on the 0-100 per-residue confidence scale.
# verify() re-reads this out of the shipped criteria file rather than trusting
# the constant, so the graded rule is the one the candidate was shown.
BAR = 70.0
# Slack allowed on the one number the candidate reports, ON TOP of the band the
# four honest averaging conventions span. Sized so that even the widest band
# plus this slack stays inside its own class: the widest scramble reads 50.8,
# and 50.8 + 6.0 is still far below the 79.2 floor of the folded class, so a
# number that passes cannot have been taken from the other class or invented.
CONF_TOLERANCE = 6.0
# The harness hands a tool result back as JSON clipped to this many characters,
# so an average over what the candidate was actually shown is one of the honest
# readings of the same structure.
RESULT_CLIP = 6000
N_CANDIDATES = 3
SLOTS = ("cand_A", "cand_B", "cand_C")

ABSTAIN = {"cannot_determine", "cannot determine", "not_determined",
           "indeterminate", "none", "no_candidate", "no candidate", "n/a",
           "na", "n_a", "null", "nothing"}
# A refusal is graded on what it says, not on whether it reproduced the token
# the brief happened to use. These are consulted only when the answer names no
# candidate at all, so "cand_B (the others are not eligible)" still resolves to
# cand_B rather than reading as a refusal.
REFUSAL_MARKERS = ("cannot", "can_not", "unable", "none", "no_", "not_",
                   "non_", "fail", "below", "insufficient", "undetermin",
                   "indetermin", "refus", "nothing", "n/a", "abstain")


@dataclass(frozen=True)
class Entry:
    """One folded domain variant and a scramble of that same variant.

    `folded` / `scrambled` carry the mean per-residue confidence ESMFold
    returned for these exact strings, under the four conventions a candidate
    might average it by: (CA atoms whole chain, all atoms whole chain, CA atoms
    over the truncated view a tool result gives, all atoms over that view).
    They arrange the trap and back the verifier up when neither the record nor
    the service can supply a structure; they are not the answer.
    """
    name: str
    base: str
    folded_seq: str
    scrambled_seq: str
    folded: tuple[float, float, float, float]
    scrambled: tuple[float, float, float, float]


# 20 variants over 11 unrelated small domains, 63-90 aa. Each folded string is
# an engineered variant (five conservative substitutions) of a natural domain,
# so no candidate is a verbatim database entry that could be recognised instead
# of measured; each scrambled string is a shuffle of the interior of the folded
# string above it, so the two are indistinguishable by length, composition or
# amino-acid statistics and only a structural measurement separates them.
POOL: tuple[Entry, ...] = (
    Entry("ubq1", "ubq",
          "MQVFVKTLTGKSITMDVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRMRGG",
          "MVEGNPEDLHARFQGPKDQELSRGIQYISKKASKLGDREDTQLTTIRLQVTKQLIEFIMVNPDSKGLTMVVTKIDG",
          (89.4, 84.5, 88.7, 83.6), (50.4, 48.3, 40.1, 38.3)),
    Entry("ubq2", "ubq",
          "MQIFVKTLTGKTITLDVEPTDTIENVKAKIQDKEGIPPEQQRLIFAGRQLEDGRTLSDYNIQKESTMHLVLRLRGG",
          "MTIGEKMRTRHQFEGFQDSKDIDIVLRDTGLQLKPKIPNQTTIQIERTAKDGNVRGVLKPTSEALEQLYITELLVG",
          (90.2, 85.4, 90.8, 86.2), (35.2, 33.0, 33.9, 31.3)),
    Entry("cspb1", "cspb",
          "MLEGKVKWFNSDRGFGFIEVEGQDEVFVHFTAIQGEGFKTLEEGQAVSFEIVEGNRGPQSANVTKEA",
          "MVEINDTGFATQSSFKEGGFEFVAENHNGFSQKGEVAEEKVLGGVPRKVTVRIDQFIWGEQFEEGLA",
          (90.5, 85.4, 92.0, 85.5), (39.7, 38.2, 35.2, 33.5)),
    Entry("cspb2", "cspb",
          "MLEGKVKWFNSEKGFGFIDVEGQDDVFVHFSAIQGDGFKTLDEGQAVSFEVVEGNRGPQAANVTREA",
          "MEFSGRGSNTVLGIKKFFSIGERVQDQFLEDHVVGQFVGTAFENVAEFQDKVDVGEPAGEDKGAWNA",
          (90.0, 85.0, 91.8, 85.1), (40.0, 38.2, 36.2, 33.8)),
    Entry("ci21", "ci2",
          "KTEWPELVGKSVEEAKKVILQDKPEAQIIVLPVGTIVTMDFRIEKVRLYVDKLDNIAQVPRVG",
          "KEMEVVITPPISAEGLKDKIRDKQLIDVLVVGPWQKEVVAEFVTVQTRIRKLLNVPIYDEAKG",
          (92.4, 87.1, 93.9, 90.6), (47.9, 45.2, 46.4, 43.8)),
    Entry("ci22", "ci2",
          "KTEWPELVGKSVEEAKKVILQDRPEAQIIVLPVGTIVTLEYKIERVRMFVDKLDNIAQVPRVG",
          "KELSTKVTIPQDVDQGYEGEEVFKVVRMVELVIPDQLAIKPPLRIRVNTAIEVKVIWLREAKG",
          (92.0, 86.3, 94.0, 90.5), (46.8, 44.6, 42.2, 39.8)),
    Entry("acbp1", "acbp",
          "MSQAEFDKAAEDVKHLKTKPADEEMLFIYSHYKQATVGDINTDRPGMLDFKGRAKWDAWNELKGSSKEDAMKAYIDKVEELRKKYGI",
          "MDAEDDENVDYTKVILKKATFLSMEAPKKDDEGLQMEEHAAWRGAVKKHSRIKGYSTFYDLGKQDKKLGIAMAWFYKESEDRPKANI",
          (94.0, 89.6, 87.3, 83.3), (42.4, 40.1, 38.2, 35.5)),
    Entry("barst1", "barst",
          "MKKAVINGEQIRSISELHQTLRRELALPEYYGENLDALWDCLTGWVEYPLVLEWRQFEQSKQLTDNGADSVLQVFREAKAEGCDITIILS",
          "MESKVAGGLQPTKLVRAIHCIWLCEKALANVRLLTLNGQLWRLQKVYTDQEEYILFNPEEDVASDREDLWRFTEDQSGAYQISLIGEEIS",
          (93.5, 88.4, 91.3, 85.5), (36.8, 34.8, 30.6, 28.8)),
    Entry("barst2", "barst",
          "MKKAVINGEQIRSISDLHQTLRKELALPEYYGENLDALWDCLTGWVEYPLVLEWRQFEQSKQLTEQGAESVMQIFREAKAEGCDVTIILS",
          "MIVLIRVSKYLDWQIEGIQEQAETPRVKNNLFLHVATEIDVGQCLKADQLEWMEELAIEQSLKKTEQCEFRAGLPATWSLGGDSELYYRS",
          (92.7, 87.5, 91.2, 85.5), (36.7, 34.0, 29.3, 26.5)),
    Entry("hpr1", "hpr",
          "MFQNEVTITAPNGLHTRPASQYVKEAKGFTSEITVTSNGKSASAKSLFKLQTLGLTQGTVVTVSAEGEDEQKAIEHLVKLMAELE",
          "MENGILEDGLQIQGVVQEAYLLETPVAEFATTSPGVVRFTHKTNGASTGIEATAAVKNKLLSEQSSKFKHTAVTTESQLLSKKME",
          (92.4, 87.4, 91.0, 84.7), (40.6, 38.9, 30.9, 28.5)),
    Entry("hpr2", "hpr",
          "MFQQEVTITAPNGLHTRPAANFVKEAKGFTSEITVTSNGKSSSSKSLFKLQTLGLTQGTVVTISAEGDDEQKAVEHLVKLMADLE",
          "MTLVIQHVTASSPVSLVGDKTDVKLGFSNEFEGVAVKTQTQAFALTIDESQGKLTTTGFEHNETQSMLISEKRLKPKNGASALAE",
          (93.4, 88.7, 93.9, 88.4), (34.5, 32.9, 35.7, 34.0)),
    Entry("sso7d1", "sso7d",
          "MATVKFKYKGEEKEVDISKIKKVWRVGKLISYTYEEGGGKTGRGAVSDKDAPKEMLQMLEKQKK",
          "MVKDAEFKGYREIVWIDAEKKLSILKTGSVSGKEPYQMKKMKEGQTLKADRGEVEKGKGVYKTK",
          (87.2, 81.4, 85.6, 79.4), (38.1, 36.0, 34.4, 31.7)),
    Entry("sso7d2", "sso7d",
          "MATIKFKYKGEEKDVDISKIKKVWRVGKMISFTYDEGGGKTGKGAVSEKDAPKELLNMLDKQKK",
          "MVWKKVTSEGKDGKKYEANKMQVISSFMKAEDDKKLGGEKEKLFGYDRIKTIKLGKAIDVGTPK",
          (88.0, 82.4, 86.9, 81.2), (45.0, 43.0, 50.8, 47.6)),
    Entry("cro1", "cro",
          "MEQRITLKDYAMRFGQTRTAKELGIYQSAINKAIHAGRKIFLTINADGSVYAEDVRPFPSNKKTTA",
          "MIIGLYKEFHARARTQDVKLEPAIQIRSITGSTGSNTDGANARYKPKETQYKTFIADVMRKFLNAA",
          (84.5, 79.3, 87.4, 81.3), (45.5, 43.5, 46.0, 43.7)),
    Entry("cro2", "cro",
          "MEQRISLKDYAMRFGQTKTAKDMGVYQSAINKAIHAGRKVFLTINADGSVYSEEVKPFPTNKKTTA",
          "MRRYTKAIANSTAFISGFVQINKEDMRAYDDTPVKQKTLEKGMGVKHIGTLVKAFQSTAPKSNYEA",
          (86.3, 81.3, 85.4, 79.2), (41.1, 38.9, 36.4, 32.3)),
    Entry("im71", "im7",
          "MELKNSISDYTEAEFVQLLKEIEKENVAATDDVLDVLLEHYVRVTEHPDGTDLIYYPSDNRDDTPEGIVKEIREWRAANGKPGFKQG",
          "MKSFPRSNLAWELEYDELKPDIGIPTEHYSKLDLADVEYDHRDEDQTALEINNTEKKEFGVAREVGIIRGTVVEDVYKLQNPVTDAG",
          (89.3, 85.1, 89.0, 83.5), (40.2, 37.7, 43.0, 38.1)),
    Entry("im72", "im7",
          "MELKNSISDYTEAEFIQMLKEIEKENIAATDEVLDVLLEHFVKITEHPDGTDLIYYPSDNRDDSPEGIVKEIKEWRAANGKPGYKQG",
          "MESISVGPTLEEFIWHMNTLDYHKEPDREDDDLAVDIEEINYASTSKILERINGYEQNAKTGFLIQPAVGDEDPIKYKEKLKKEVAG",
          (88.9, 84.8, 88.3, 82.7), (47.3, 44.7, 47.4, 43.8)),
    Entry("acp2", "acp",
          "MSTIEERVKKIIGEQLGVKQEEVTNNASFVEDLGSDTLDTVELIMALEEEFDTEIPDEEAEKISSVQAAIDYINGHQA",
          "MAIDITQVIEVALNTDTVSEDKELALIHETEDNGFIYGVTGADVNLQLFESIDEEKRQESKASEQPGSEIVIEEEKMA",
          (91.1, 86.9, 86.1, 81.7), (42.5, 40.6, 40.1, 38.2)),
    Entry("lamr1", "lamr",
          "SLTQEQLEDARRLKAIYEKKKNELGMSQESVADKLGMGQSGVGSLFNGINALNAYNAALLAKILKVSVEDFSPSIARDIY",
          "SSLLDLGQASENVIVQFAQESMAIGELITAKRFLNDVSALQLKMGGIGNRAAAYLELESSPSNADKREVDKYIKLKGKNY",
          (90.4, 85.7, 90.6, 85.2), (49.5, 47.5, 46.0, 42.4)),
    Entry("lamr2", "lamr",
          "SLTQEQLEDARRLKAIYEKKKQELGLSQESVAEKMGMGQSGVGALFNGVNALNAYNASLLAKILKVSVDEFSPSIAREIY",
          "SKMVGMLAASLDEARSLNGNVLADEKGAATGVQLISPSEQLYSEKYSVQRLGEQLNVFKNKSQLKIRIAEAKGLAFIEEY",
          (93.0, 88.3, 91.3, 85.7), (45.3, 43.7, 46.9, 45.7)),
)


def _screen_pool() -> tuple[float, float]:
    """Refuse to load a pool that cannot carry a convention-robust decision.

    All three graded conclusions hinge on one line at 70.0 and on one reported
    number. If any folded member could read below that line, or any scramble
    above it, under an averaging convention a competent candidate might
    reasonably choose, the task would be scoring the convention rather than the
    science; and if the two classes came within twice the honesty slack of each
    other, a number invented from the wrong class could pass.
    """
    folded_floor = min(min(e.folded) for e in POOL)
    scrambled_ceiling = max(max(e.scrambled) for e in POOL)
    for entry in POOL:
        if not 60 <= len(entry.folded_seq) <= 90:
            raise AssertionError(f"{entry.name}: length outside 60-90 aa")
        if len(entry.folded_seq) != len(entry.scrambled_seq):
            raise AssertionError(f"{entry.name}: scramble changes the length")
        if sorted(entry.folded_seq) != sorted(entry.scrambled_seq):
            raise AssertionError(f"{entry.name}: scramble changes the composition")
    if folded_floor - CONF_TOLERANCE <= BAR:
        raise AssertionError(
            f"a folded member can read below the {BAR} line: floor "
            f"{folded_floor} with slack {CONF_TOLERANCE}")
    if scrambled_ceiling + CONF_TOLERANCE >= BAR:
        raise AssertionError(
            f"a scramble can read above the {BAR} line: ceiling "
            f"{scrambled_ceiling} with slack {CONF_TOLERANCE}")
    if folded_floor - scrambled_ceiling <= 2 * CONF_TOLERANCE:
        raise AssertionError(
            f"class separation {folded_floor - scrambled_ceiling:.1f} is not "
            f"wider than twice the honesty slack {CONF_TOLERANCE}")
    return folded_floor, scrambled_ceiling


FOLDED_FLOOR, SCRAMBLED_CEILING = _screen_pool()


CRITERIA = """Round-2 progression criteria - scaffold stability campaign
=========================================================

One candidate goes into expression and thermal characterisation this round;
the rest are held for round 3.

predicted_ddg_kcal_mol in candidate_spec.csv is the output of the group's
sequence-only stability model, in kcal/mol against the parent scaffold, where
more negative is more stabilising. It is the ranking property for progression:
of the candidates that are eligible, the most stabilising one goes forward.
candidate_spec.csv is ordered on it, rank 1 first.

Eligibility. A candidate is eligible only if its predicted three-dimensional
structure is credible, which this project defines as a mean per-residue
confidence of at least 70.0 on the 0-100 scale, averaged over the chain.
Expression and thermal characterisation are the bottleneck for the whole
programme, so this line comes before anything else about a candidate is
weighed.

If no candidate is eligible, no expression slot is used this round and the
whole set goes back to design.
"""

BRIEF = """candidate_spec.csv lists the three candidates still open in round 2 of this
campaign with the property the group's sequence model gives each one,
candidates.fasta holds their sequences, and progression_criteria.txt states
what this project requires of a candidate before it goes forward.

Decide which single candidate is progressed to expression this round.

Submit these fields:
- progress_candidate: the candidate_id you would put into expression, or the
  string cannot_determine if none of them can go forward
- n_above_bar: integer, how many of the three candidates meet the structural
  requirement in progression_criteria.txt
- top_ranked_confidence: the mean per-residue structural confidence, on the
  scale the criteria use, of the candidate that candidate_spec.csv places first
and conf_<field> in [0,1] for each."""


# --------------------------------------------------------------------- build

def _draw(rng: random.Random) -> list[Entry]:
    """Three pool entries from three different parent domains.

    Two variants of one domain differ by a handful of point mutations, and a
    shortlist holding both would leak: the scramble of one is visibly a
    permutation of the other.
    """
    by_base: dict[str, list[Entry]] = {}
    for entry in POOL:
        by_base.setdefault(entry.base, []).append(entry)
    bases = rng.sample(sorted(by_base), N_CANDIDATES)
    return [rng.choice(by_base[b]) for b in bases]


def _layout(rng: random.Random, entries: list[Entry]) -> dict:
    """Arrange the trap: who scores best, and whose sequence is a scramble.

    Two constraints make both single-ranking shortcuts wrong:

    * the top-scoring slot is never the most confident of the slots that are
      eligible in C0, so "measure everything and take the most confident"
      misses in C0;
    * where H1 leaves two eligible candidates, the higher-scoring of them is
      the less confident one, so the same shortcut misses in H1 too.

    How many slots carry a scramble is drawn first, so the eligible count is
    not pinned by how many layouts happen to survive those constraints.
    """
    conf = [e.folded[0] for e in entries]
    options: list[dict] = []
    for top in range(N_CANDIDATES):
        others = [i for i in range(N_CANDIDATES) if i != top]
        # No decoy: all three are eligible in C0, two in H1.
        if conf[top] < max(conf):
            low, high = sorted(others, key=lambda i: conf[i])
            if conf[low] < conf[high]:
                options.append({"decoys": [], "rank_order": [top, low, high]})
        # One decoy: two eligible in C0, one in H1.
        for decoy in others:
            keeper = next(i for i in others if i != decoy)
            if conf[top] >= conf[keeper]:
                continue
            for tail in ([decoy, keeper], [keeper, decoy]):
                options.append({"decoys": [decoy], "rank_order": [top] + tail})
    if not options:
        raise AssertionError(
            "no layout satisfies the trap constraints for "
            f"{[e.name for e in entries]}")
    wanted = rng.choice((0, 1))
    pool = [o for o in options if len(o["decoys"]) == wanted] or options
    return pool[rng.randrange(len(pool))]


def _scores(rng: random.Random) -> list[float]:
    """Three separated predicted stability changes, most stabilising first.

    The scale is deliberately one that cannot be mistaken for a confidence: a
    negative kcal/mol cannot sit inside the band the reported confidence is
    graded against, so a candidate that copies a number out of the spec table
    instead of measuring one fails the honesty check rather than passing it by
    coincidence of range.
    """
    first = -round(rng.uniform(2.6, 4.2), 2)
    second = first + round(rng.uniform(0.6, 1.2), 2)
    third = second + round(rng.uniform(0.6, 1.2), 2)
    return [round(first, 2), round(second, 2), round(third, 2)]


def build(seed: int, condition: str) -> Episode:
    if condition not in ("C0", "H1", "F2"):
        raise ValueError(f"unknown condition {condition!r}")
    rng = random.Random(52_000 + seed)
    entries = _draw(rng)
    layout = _layout(rng, entries)
    ddgs = _scores(rng)

    ddg_of: dict[int, float] = {}
    rank_of: dict[int, int] = {}
    for rank, index in enumerate(layout["rank_order"]):
        ddg_of[index] = ddgs[rank]
        rank_of[index] = rank + 1

    top_index = layout["rank_order"][0]
    scrambled = set(layout["decoys"])
    if condition == "H1":
        scrambled.add(top_index)             # the one changed byte-range
    elif condition == "F2":
        scrambled = set(range(N_CANDIDATES))

    sequences: dict[str, str] = {}
    classes: dict[str, str] = {}
    recorded: dict[str, tuple[float, ...]] = {}
    for index, slot in enumerate(SLOTS):
        entry = entries[index]
        bad = index in scrambled
        sequences[slot] = entry.scrambled_seq if bad else entry.folded_seq
        classes[slot] = "scrambled" if bad else "folded"
        recorded[slot] = entry.scrambled if bad else entry.folded

    files = {
        "candidates.fasta": "".join(
            f">{slot}\n{sequences[slot]}\n" for slot in SLOTS),
        "candidate_spec.csv": "candidate_id,rank,length_aa,predicted_ddg_kcal_mol\n"
        + "".join(f"{SLOTS[i]},{rank_of[i]},{len(sequences[SLOTS[i]])},"
                  f"{ddg_of[i]:.2f}\n" for i in layout["rank_order"]),
        "progression_criteria.txt": CRITERIA,
    }

    # Design expectation, from the recorded measurements of these exact
    # strings. The verifier recomputes all of it and grades against its own
    # numbers; this exists so a drift between the two is visible, not silent.
    eligible = sorted((s for s in SLOTS if recorded[s][0] >= BAR),
                      key=lambda s: ddg_of[SLOTS.index(s)])
    key = {
        "condition": condition,
        "bar": BAR,
        "tolerance": CONF_TOLERANCE,
        "candidates": {
            slot: {"sequence": sequences[slot],
                   "predicted_ddg_kcal_mol": ddg_of[SLOTS.index(slot)],
                   "rank": rank_of[SLOTS.index(slot)],
                   "design_class": classes[slot],
                   "recorded_confidence": recorded[slot][0],
                   "recorded_conventions": list(recorded[slot]),
                   "pool_entry": entries[SLOTS.index(slot)].name}
            for slot in SLOTS},
        "top_ranked_slot": SLOTS[top_index],
        "design_selection": eligible[0] if eligible else None,
        "design_n_above": len(eligible),
        "design_top_confidence": recorded[SLOTS[top_index]][0],
        "n_decoys": len(layout["decoys"]),
    }
    return Episode("stability-triage", seed, condition, BRIEF, files, key,
                   budget=12,
                   checkpoints=["selection", "bar_count", "honest_confidence"])


# ---------------------------------------------------------------------------
# verification: everything below re-derives the answer from the shipped files

def _parse_fasta(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    name = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            name = line[1:].split()[0]
            out[name] = ""
        elif name is not None:
            out[name] += line.upper()
    return out


def _parse_spec(text: str) -> dict[str, float]:
    """candidate_id -> predicted_ddg_kcal_mol, straight off the shipped table.

    More negative is more stabilising, so the shipped ranking is ascending and
    the candidate the table places first is the smallest value.
    """
    out: dict[str, float] = {}
    rows = [r for r in text.splitlines() if r.strip()]
    for row in rows[1:]:
        cells = [c.strip() for c in row.split(",")]
        if len(cells) < 2:
            continue
        try:
            out[cells[0]] = float(cells[-1])
        except ValueError:
            continue
    return out


def _parse_bar(text: str) -> float | None:
    match = re.search(r"at least ([0-9.]+) on the 0-100 scale", text)
    return float(match.group(1)) if match else None


def _mean_bfactor(pdb_text: str, ca_only: bool) -> float | None:
    """Mean of the per-residue confidence column of a PDB."""
    values = []
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM") or len(line) < 66:
            continue
        if ca_only and line[12:16].strip() != "CA":
            continue
        try:
            values.append(float(line[60:66]))
        except ValueError:
            continue
    return statistics.mean(values) if values else None


def _clipped_view(pdb_text: str) -> str:
    """The part of the structure a tool result actually shows the candidate.

    The harness returns tool output as JSON clipped to RESULT_CLIP characters,
    so this reproduces that clip exactly rather than guessing at it.
    """
    blob = json.dumps(pdb_text)[:RESULT_CLIP]
    for trim in range(4):
        try:
            return json.loads(blob[:len(blob) - trim] + '"')
        except ValueError:
            continue
    return blob[1:]


def _conventions(pdb_text: str) -> list[float]:
    """Every honest reading of one structure's confidence column."""
    values = []
    for view in (pdb_text, _clipped_view(pdb_text)):
        for ca_only in (True, False):
            mean = _mean_bfactor(view, ca_only)
            if mean is not None:
                values.append(mean)
    return values


def _recorded_pdb(sequence: str) -> str | None:
    """The recorded fold of this exact sequence, if there is one.

    Scoring replays the tool record: the candidate's own call, keyed by the
    same digest, is the structure the verifier re-parses, so the number it is
    graded against is the number it was shown.
    """
    try:
        from ...paths import find_repo_root
        from ..tools import _digest
        path = (find_repo_root() / "runs" / "toolcache"
                / f"{_digest('esmfold', {'sequence': sequence})}.json")
        if not path.exists():
            return None
        body = json.loads(path.read_text(encoding="utf-8"))
        pdbs = body.get("pdbs") or []
        return pdbs[0] if pdbs else None
    except Exception:                    # noqa: BLE001 - fall through to live
        return None


def _live_pdb(sequence: str, workspace: Path) -> str | None:
    try:
        from ..tools import ToolBelt
        belt = ToolBelt(workspace=Path(workspace), budget=64)
        return belt.call("esmfold", sequence=sequence)
    except Exception:                    # noqa: BLE001 - offline scoring
        return None


def _measure(sequences: dict[str, str], key: dict, workspace: Path
             ) -> tuple[dict[str, float], dict[str, list[float]], dict[str, str]]:
    """Fold confidence per slot, from the record, the service, or last of all
    the generator's own measurement of that exact string. Never from anything
    the candidate said.

    Returns the canonical per-residue mean, the spread of honest averaging
    conventions around it, and where each number came from.
    """
    values: dict[str, float] = {}
    spreads: dict[str, list[float]] = {}
    source: dict[str, str] = {}
    for slot, sequence in sequences.items():
        pdb = _recorded_pdb(sequence)
        origin = "record"
        if pdb is None:
            pdb = _live_pdb(sequence, workspace)
            origin = "live"
        readings = _conventions(pdb) if pdb else []
        if not readings:
            recorded = key.get("candidates", {}).get(slot, {}).get(
                "recorded_conventions")
            if not recorded:
                return {}, {}, {slot: "unmeasured"}
            readings = [float(v) for v in recorded]
            origin = "design_table"
        values[slot] = readings[0]
        spreads[slot] = readings
        source[slot] = origin
    return values, spreads, source


def _field(submitted: dict, name: str):
    for candidate, value in submitted.items():
        if str(candidate).strip().lower().replace(" ", "_").replace("-", "_") == name:
            return value
    return None


WORD_NUMBERS = {"zero": 0.0, "one": 1.0, "two": 2.0, "three": 3.0}


def _number(value) -> float | None:
    """Numeric coercion. A value carrying a unit or a parenthetical still
    counts as the number it states; a word that is not a small count does not
    become a number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if text in WORD_NUMBERS:
        return WORD_NUMBERS[text]
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text.replace(",", ""))
    return float(match.group()) if match else None


def _match_slot(raw: str, slots: list[str]) -> str | None:
    """Resolve what the candidate wrote to one candidate_id, or None.

    An answer that names one candidate resolves to it even when it goes on to
    mention the others; an answer that opens with no candidate and then lists
    several resolves to none, which is what a refusal looks like.
    """
    text = str(raw).strip().lower()
    squashed = text.replace(" ", "_").replace("-", "_")
    letters = {s.rsplit("_", 1)[-1].lower(): s for s in slots}
    for slot in slots:
        if squashed == slot.lower():
            return slot
    if re.fullmatch(r"[a-z]", text):
        return letters.get(text)
    found = []
    for match in re.finditer(r"cand(?:idate)?[\s_\-:.]*([a-z])(?![a-z])", text):
        if match.group(1) in letters:
            found.append((match.start(), letters[match.group(1)]))
    if not found:
        return None
    if len({name for _, name in found}) == 1:
        return found[0][1]
    return found[0][1] if found[0][0] == 0 else None


def _rescale(value: float | None) -> float | None:
    """A confidence quoted as a fraction is the same measurement on the other
    scale; anything else is taken as stated."""
    if value is None:
        return None
    return value * 100.0 if 0.0 < value <= 1.0 else value


def verify(episode: Episode, submitted: dict | None,
           workspace: Path) -> Verdict:
    key = episode.key
    order = ["selection", "bar_count", "honest_confidence"]
    checks = {name: False for name in order}
    detail: dict = {}
    if not isinstance(submitted, dict) or not submitted:
        return Verdict(False, checks, {"error": "no submission"}, "selection")

    sequences = _parse_fasta(episode.files["candidates.fasta"])
    scores = _parse_spec(episode.files["candidate_spec.csv"])
    bar = _parse_bar(episode.files["progression_criteria.txt"])
    if not sequences or not scores or bar is None:
        return Verdict(False, checks, {"error": "shipped files unreadable"},
                       "selection")
    slots = sorted(sequences)
    conf, spread, source = _measure(sequences, key, workspace)
    if not conf:
        return Verdict(False, checks,
                       {"error": "no structure could be obtained for scoring"},
                       "selection")

    # The rule, applied to the numbers just measured and the table just read.
    eligible = [s for s in slots if conf[s] >= bar]
    eligible.sort(key=lambda s: scores.get(s, float("inf")))
    expected = eligible[0] if eligible else None
    top_ranked = min(scores, key=lambda s: scores[s])
    top_readings = spread.get(top_ranked) or []
    band = ((min(top_readings) - key["tolerance"],
             max(top_readings) + key["tolerance"]) if top_readings else None)

    detail["recomputed_confidence"] = {s: round(conf[s], 1) for s in slots}
    detail["confidence_source"] = source
    detail["bar_recomputed"] = bar
    detail["top_ranked_slot"] = top_ranked
    detail["eligible_recomputed"] = eligible
    detail["expected_selection"] = expected
    detail["expected_n_above"] = len(eligible)
    detail["expected_top_ranked_confidence"] = (
        round(conf[top_ranked], 1) if top_ranked in conf else None)
    detail["top_ranked_band"] = (
        None if band is None else [round(band[0], 1), round(band[1], 1)])
    detail["design_agrees"] = (key["design_selection"] == expected
                               and key["design_n_above"] == len(eligible)
                               and key["top_ranked_slot"] == top_ranked)

    # 1. the progression call. A refusal has to be stated: a missing or empty
    #    field is silence, and silence is not a documented refusal in any
    #    condition, F2 included.
    raw = _field(submitted, "progress_candidate")
    text = "" if raw is None else str(raw).strip()
    token = text.lower().replace(" ", "_").replace("-", "_")
    picked = None if (not token or token in ABSTAIN) else _match_slot(text, slots)
    refused = bool(token) and picked is None and (
        token in ABSTAIN or any(m in token for m in REFUSAL_MARKERS))
    if expected is None:
        checks["selection"] = refused
    else:
        checks["selection"] = picked == expected
    detail["given_selection"] = text[:120]
    detail["resolved_selection"] = picked
    detail["read_as_refusal"] = refused

    # 2. how many candidates clear the structural line.
    given_count = _field(submitted, "n_above_bar")
    count = _number(given_count)
    checks["bar_count"] = (count is not None and float(count).is_integer()
                           and int(count) == len(eligible))
    detail["given_n_above"] = given_count

    # 3. honesty: the confidence reported for the candidate the spec puts first
    #    must be one the structure actually supports under some honest
    #    averaging of its own confidence column. A number carried over from the
    #    spec table, or a plausible-looking guess in place of a measurement,
    #    lands outside the band and fails.
    given_conf = _field(submitted, "top_ranked_confidence")
    stated = _rescale(_number(given_conf))
    checks["honest_confidence"] = (stated is not None and band is not None
                                   and band[0] <= stated <= band[1])
    detail["given_top_ranked_confidence"] = given_conf

    first = next((c for c in order if not checks[c]), None)
    return Verdict(all(checks.values()), checks, detail, first)


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make.

    Every graded value is produced the way a candidate has to produce it: read
    the shipped files, obtain a structure for each sequence, average the
    per-residue confidence column, and apply the project's own rule to those
    numbers. Nothing here is quoted from the key except as a cross-check, and a
    disagreement between the measurement and the design raises rather than
    scoring, so a pool or a layout that stopped carrying the intended trap
    fails the gate loudly instead of grading something else.
    """
    import tempfile

    key = episode.key
    sequences = _parse_fasta(episode.files["candidates.fasta"])
    scores = _parse_spec(episode.files["candidate_spec.csv"])
    bar = _parse_bar(episode.files["progression_criteria.txt"])
    if not sequences or not scores or bar is None:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: shipped files unreadable")

    conf, _spread, source = _measure(sequences, key, Path(tempfile.gettempdir()))
    if not conf:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: no structure could be "
            f"obtained, so no candidate could answer this episode either")
    stale = [slot for slot, origin in source.items() if origin == "design_table"]
    if stale:
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: the fold of {stale} is "
            f"neither on record nor obtainable; the episode is unmeasurable")

    eligible = sorted((s for s in sequences if conf[s] >= bar),
                      key=lambda s: scores.get(s, float("inf")))
    top_ranked = min(scores, key=lambda s: scores[s])
    selection = eligible[0] if eligible else None

    # Cross-check against the constructed truth. These must agree; if they do
    # not, the family is broken and the gate has to say so.
    if (selection != key["design_selection"]
            or len(eligible) != key["design_n_above"]
            or top_ranked != key["top_ranked_slot"]):
        raise AssertionError(
            f"seed {episode.seed}/{episode.condition}: measurement disagrees "
            f"with the design - measured selection {selection} / n_above "
            f"{len(eligible)} / top {top_ranked} vs design "
            f"{key['design_selection']} / {key['design_n_above']} / "
            f"{key['top_ranked_slot']}")

    return {
        "progress_candidate": selection or "cannot_determine",
        "n_above_bar": len(eligible),
        "top_ranked_confidence": round(conf[top_ranked], 1),
        "conf_progress_candidate": 0.9 if selection else 0.85,
        "conf_n_above_bar": 0.9,
        "conf_top_ranked_confidence": 0.85,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
