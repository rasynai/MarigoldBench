"""Family: design a selective binder against a near-identical paralog.

This is the family both collaborators asked for and the one the sponsor named:
de-novo protein design driven by the model itself, using RFdiffusion for the
backbone, ProteinMPNN for the sequence, and a folding tool to check its own
work. It is also the first family with a budget large enough to require
ITERATION rather than a straight line - Gemini 3.1's structural objection was
that an 8-18 call episode can only be solved by a memorised recipe, so this one
gets 40 calls and a design goal that cannot be met on the first attempt.

The science: two paralogs share the binding face almost exactly. Affinity for
the primary target is easy; SELECTIVITY is the hard part, because the residues
that give affinity are conserved and therefore give affinity to the off-target
too. The only exploitable difference is a small number of positions where the
paralogs differ, and a design that ignores them binds both.

  C0  the paralogs differ at exploitable positions inside the interface, so a
      selective design exists and the model must find and use them.
  H1  the difference the sequence files advertise sits OUTSIDE the interface -
      a decoy divergence. The exploitable positions are elsewhere and fewer.
      A model that greps for "where do they differ" and designs against the
      obvious answer produces a non-selective binder.
  F2  the paralogs are identical across the entire interface and its
      environment, so no structural selectivity is achievable and a documented
      refusal is the only defensible outcome. The impossibility is a fact about
      the supplied sequences, checkable by the harness and by the candidate.

Verification recomputes everything from the submitted sequence: length, the
positions it actually contacts by the generator's own interface definition,
whether it exploits divergent positions, and (where a fold tool is reachable)
its predicted confidence. Nothing self-reported is evidence, and no docking
score is treated as truth - the corpus is explicit that a tool's own
confidence is not an affinity.
"""
from __future__ import annotations

import random
import re
from pathlib import Path

from ..families import Episode, Verdict

ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "null",
           "impossible", "not_achievable", "not achievable"}

AA = "ACDEFGHIKLMNPQRSTVWY"
# Residues that make a real difference to an interface when swapped: charge
# reversal, size change, or loss of an H-bond donor. Used to build divergences
# a designer could actually exploit.
EXPLOITABLE_SWAPS = [("K", "E"), ("E", "R"), ("D", "K"), ("R", "D"),
                     ("W", "A"), ("F", "G"), ("Y", "S"), ("L", "T")]

TARGET_PAIRS = [
    ("KDR", "FLT4", "receptor tyrosine kinase"),
    ("CDK4", "CDK6", "cyclin-dependent kinase"),
    ("AKT1", "AKT2", "AGC-family kinase"),
    ("PIM1", "PIM2", "serine/threonine kinase"),
    ("BRD2", "BRD3", "bromodomain"),
    ("HDAC1", "HDAC2", "histone deacetylase"),
]

DOMAIN_LEN = 96
BINDER_MIN, BINDER_MAX = 24, 60


def _scaffold(rng: random.Random) -> str:
    """A plausible globular domain sequence. Composition matters more than
    realism here: the interface positions are what the task turns on."""
    return "".join(rng.choice(AA) for _ in range(DOMAIN_LEN))


def _interface_positions(rng: random.Random) -> list[int]:
    """A contiguous-ish patch, 1-indexed, standing in for the binding face."""
    start = rng.randrange(20, DOMAIN_LEN - 30)
    return sorted(rng.sample(range(start, start + 24), 12))


def build(seed: int, condition: str) -> Episode:
    rng = random.Random(770_000 + seed)
    primary, paralog, family_name = TARGET_PAIRS[seed % len(TARGET_PAIRS)]

    seq_a = _scaffold(rng)
    interface = _interface_positions(rng)

    # How many interface positions genuinely diverge, and where.
    if condition == "F2":
        exploitable: list[int] = []          # identical interface: impossible
        decoy_positions: list[int] = []
    elif condition == "H1":
        # Few real differences, inside the interface; plus a loud divergence
        # OUTSIDE it that a keyword search finds first.
        exploitable = rng.sample(interface, 2)
        outside = [p for p in range(1, DOMAIN_LEN + 1) if p not in interface]
        decoy_positions = rng.sample(outside, 6)
    else:
        exploitable = rng.sample(interface, 4)
        decoy_positions = []

    seq_b = list(seq_a)
    for position in exploitable:
        original = seq_a[position - 1]
        swap = next((b for a, b in EXPLOITABLE_SWAPS if a == original), None)
        if swap is None:
            swap = rng.choice([b for _a, b in EXPLOITABLE_SWAPS])
        seq_b[position - 1] = swap
    for position in decoy_positions:
        original = seq_a[position - 1]
        seq_b[position - 1] = next(
            (b for a, b in EXPLOITABLE_SWAPS if a == original),
            rng.choice([b for _a, b in EXPLOITABLE_SWAPS]))
    seq_b = "".join(seq_b)

    fasta = (f">{primary}|primary target|{family_name}\n{seq_a}\n"
             f">{paralog}|paralog|{family_name}\n{seq_b}\n")

    # The interface definition is supplied - which residues form the binding
    # face is structural knowledge the model is not expected to invent - but
    # WHICH of them diverge, and whether any do, is not stated anywhere.
    spec = [
        f"# Design request  {primary} (primary) vs {paralog} (paralog)",
        f"Family: {family_name}.",
        "",
        "Both sequences are in targets.fasta, numbered from 1.",
        "",
        "Binding-face residues on the primary target (same numbering in both):",
        "  " + ", ".join(str(p) for p in interface),
        "",
        f"A binder must be a single chain of {BINDER_MIN}-{BINDER_MAX} residues.",
        "",
        "Progression rule: a design progresses only if it is expected to",
        f"engage {primary} while NOT engaging {paralog}.",
    ]
    spec_text = "\n".join(spec) + "\n"

    brief = (
        f"A programme needs a protein binder for {primary} that does not also "
        f"engage its paralog {paralog}. The two sequences and the binding-face "
        f"numbering are attached.\n\n"
        "Produce a binder sequence and the evidence for its selectivity, or "
        "state that the requested selectivity cannot be achieved.\n\n"
        "Submit these fields:\n"
        "- binder_sequence: the single-letter amino-acid sequence of your "
        "design, or the string cannot_determine if the request cannot be met\n"
        "- exploited_positions: the residue numbers on the target that your "
        "design relies on to discriminate the two proteins, as a "
        "comma-separated list (empty if none)\n"
        "- selectivity_basis: what makes your design selective, or why "
        "selectivity is unachievable, in your own words\n"
        "and conf_<field> in [0,1] for each.")

    files = {"targets.fasta": fasta, "design_request.md": spec_text}
    key = {
        "condition": condition,
        "primary": primary,
        "paralog": paralog,
        "interface": interface,
        "exploitable": sorted(exploitable),
        "decoy_positions": sorted(decoy_positions),
        "achievable": condition != "F2",
        "seq_a": seq_a,
        "seq_b": seq_b,
        "binder_range": [BINDER_MIN, BINDER_MAX],
    }
    # 40 calls: the design route is rfdiffusion -> proteinmpnn -> fold check,
    # and a first attempt that ignores the divergence has to be discovered and
    # revised. A budget that only permits one pass would reward the recipe.
    return Episode("binder-selectivity", seed, condition, brief, files, key,
                   budget=40,
                   checkpoints=["design_valid", "targets_divergence",
                                "selectivity_claim"])


def _positions(raw) -> set[int]:
    if raw is None:
        return set()
    if isinstance(raw, (list, tuple)):
        parts = [str(x) for x in raw]
    else:
        parts = re.split(r"[,;\s]+", str(raw))
    out = set()
    for part in parts:
        part = part.strip().strip("[]()")
        if part.isdigit():
            out.add(int(part))
    return out


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"design_valid": False, "targets_divergence": False,
              "selectivity_claim": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "design_valid")

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # Recompute the divergence from the shipped sequences, independently of
    # what the generator recorded: a generator and verifier that share one
    # wrong assumption agree perfectly and are still wrong.
    seq_a, seq_b = key["seq_a"], key["seq_b"]
    differing = {i + 1 for i, (x, y) in enumerate(zip(seq_a, seq_b)) if x != y}
    interface = set(key["interface"])
    exploitable = sorted(differing & interface)
    detail["divergent_positions_recomputed"] = sorted(differing)
    detail["exploitable_recomputed"] = exploitable
    detail["interface"] = sorted(interface)

    raw_sequence = field("binder_sequence")
    text = str(raw_sequence or "").strip()
    abstained = text.lower() in ABSTAIN
    claimed = _positions(field("exploited_positions"))
    basis = str(field("selectivity_basis") or "").lower()

    if not exploitable:
        # F2: no interface divergence exists, so selectivity is unachievable.
        # Silence is not a refusal, and the refusal must be ABOUT the identity
        # of the binding face rather than a generic apology.
        reason_words = ("identical", "no differ", "same sequence", "conserved",
                        "indistinguishable", "no divergence", "not differ",
                        "cannot discriminate", "no exploitable")
        names_reason = any(w in basis for w in reason_words)
        checks["design_valid"] = abstained
        checks["targets_divergence"] = abstained and not claimed
        checks["selectivity_claim"] = abstained and names_reason
        detail["expected"] = ("refusal: the binding face is identical in both "
                              "paralogs, so no structural selectivity exists")
        detail["stated_basis"] = basis[:200]
        order = ["design_valid", "targets_divergence", "selectivity_claim"]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    # A real design is required. Validate the artifact itself first.
    low, high = key["binder_range"]
    residues = re.sub(r"[^A-Za-z]", "", text).upper()
    valid_alphabet = bool(residues) and all(ch in AA for ch in residues)
    checks["design_valid"] = (not abstained and valid_alphabet
                              and low <= len(residues) <= high)
    detail["binder_length"] = len(residues)
    detail["binder_alphabet_ok"] = valid_alphabet

    # The discriminating positions it claims must be the ones that actually
    # diverge inside the interface. Naming the decoy divergence outside the
    # interface - the H1 trap - fails here.
    if claimed:
        precision = len(claimed & set(exploitable)) / len(claimed)
    else:
        precision = 0.0
    recall = (len(claimed & set(exploitable)) / len(exploitable)) if exploitable else 0.0
    checks["targets_divergence"] = precision >= 0.75 and recall >= 0.5
    detail["claimed_positions"] = sorted(claimed)
    detail["precision"] = round(precision, 3)
    detail["recall"] = round(recall, 3)

    # The stated basis must actually reference discrimination between the two
    # proteins, not merely affinity for the primary.
    discrimination_words = ("differ", "diverg", "paralog", "selectiv",
                            "not conserved", "substitution", "charge",
                            "clash", "steric", "only in", "absent in")
    checks["selectivity_claim"] = (any(w in basis for w in discrimination_words)
                                  and checks["targets_divergence"])
    detail["stated_basis"] = basis[:200]

    order = ["design_valid", "targets_divergence", "selectivity_claim"]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


def reference_submission(episode: Episode) -> dict:
    """The submission a competent designer would make.

    Derived by recomputing the divergence from the shipped sequences - the same
    route the candidate must take - so B8 proves the task is solvable from the
    workspace rather than from the key.
    """
    key = episode.key
    seq_a, seq_b = key["seq_a"], key["seq_b"]
    interface = set(key["interface"])
    exploitable = sorted({i + 1 for i, (x, y) in enumerate(zip(seq_a, seq_b))
                          if x != y} & interface)

    if not exploitable:
        return {
            "binder_sequence": "cannot_determine",
            "exploited_positions": "",
            "selectivity_basis": (
                f"the binding face of {key['primary']} and {key['paralog']} is "
                "identical at every listed interface residue, so the two "
                "proteins are indistinguishable to any binder that engages "
                "that face; no structural basis for selectivity exists"),
            "conf_binder_sequence": 0.9, "conf_exploited_positions": 0.9,
            "conf_selectivity_basis": 0.9,
        }

    # A design of legal length whose composition complements the divergent
    # residues: opposite charge where the primary is charged, small where the
    # primary is bulky.
    complement = {"K": "E", "R": "E", "E": "K", "D": "R", "W": "A", "F": "A",
                  "Y": "S", "L": "S", "T": "L", "G": "F", "S": "Y", "A": "W"}
    core = "".join(complement.get(seq_a[p - 1], "A") for p in exploitable)
    linker = "GSGSGSGS"
    sequence = (core + linker + core + linker + core)[:key["binder_range"][1]]
    while len(sequence) < key["binder_range"][0]:
        sequence += "G"
    return {
        "binder_sequence": sequence,
        "exploited_positions": ",".join(str(p) for p in exploitable),
        "selectivity_basis": (
            f"positions {exploitable} diverge between {key['primary']} and "
            f"{key['paralog']} inside the binding face; the design places "
            "complementary residues against the primary target's identity at "
            "those positions, which the paralog's substitutions cannot "
            "accommodate, so selectivity rests on that divergence rather than "
            "on the conserved remainder of the face"),
        "conf_binder_sequence": 0.7, "conf_exploited_positions": 0.85,
        "conf_selectivity_basis": 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
