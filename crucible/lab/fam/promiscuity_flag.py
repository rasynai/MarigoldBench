"""Family: is this hit series worth progressing, or is its best hit a frequent
hitter?

Written against the collaborator critique of the first family batch
(analysis/collab/hardening__gpt.md and hardening__gemini.md). Their diagnosis
was that the early families were "canonical audit recipes with a conspicuous
local defect", which frontier models execute reliably, and their prescription
was to ship *several superficially adequate analyses that imply different
decisions, plus data that make exactly one of them defensible*. So this family
deliberately supplies three analyses a competent chemist would recognise, and
they disagree:

  1. POTENCY.  The series' most potent hit is ~10x better than anything else.
     Progressing the best IC50 is the default move and is wrong in a third of
     the instances.
  2. SUBSTRUCTURE ALERTS.  The deck's automated filter flags a catechol on two
     compounds - and it flags them in EVERY condition, because the flag is a
     property of the structures, which are identical across conditions. A model
     that treats a PAINS-style alert as disqualifying rejects the correct
     answer in every condition and lands on a compound that looks clean and is
     not. That inversion is the literature's own finding about alert lists:
     their precision on real frequent hitters is poor in both directions.
  3. THE HISTORICAL ARCHIVE.  The load-bearing evidence. It is the only source
     that can say whether the potency is target-specific.

The archive is where the second trap lives, and it is a trap about
exchangeability rather than about arithmetic. The progression rule is written
in terms of TARGETS ("hit rate against unrelated targets"), but the archive is
a list of ASSAYS, and several of its assays are repeat runs of the same target
at different sites. The obvious pandas move - the fraction of outcome rows that
read ACTIVE - counts one target three times. It is constructed so that the
correct answer's only unrelated-target activity sits on a triplicated target:
its row-level rate is above the 0.20 limit and its target-level rate is below
it. A model that never asks what the denominator is supposed to be rejects the
compound it should progress, in C0 and in H1 alike.

C0 and H1 differ by one intervention with no shape at all: the archive profiles
of the two lead compounds are EXCHANGED. Every file is byte-identical between
the two conditions except for which registry key each outcome column belongs
to, so the multiset of rows, the count of ACTIVE cells, the count of blanks and
every numeric format are identical by construction. The critique was explicit
that byte-identical briefs are not enough - if H1 workspaces are detectably
different objects, the condition is readable without any science.

Two frequent hitters are present in both conditions, so "find the promiscuous
compound" is not the task; whether the MOST POTENT one is promiscuous is.

F2 carries an explicit impossibility witness, not a data-quality complaint. The
archive is keyed by registry parent, and the registry parent is stereo-blind.
In F2 the two lead compounds are enantiomers filed under one key, so the
archive holds a single outcome record for the pair. That record is the union of
the two compounds' behaviour, and union is symmetric: the attribution "the (R)
isomer is the frequent hitter and the (S) isomer is clean" and the attribution
with the isomers exchanged reproduce every shipped outcome exactly, while
implying opposite decisions. The generator emits both witnesses and the
verifier re-derives the collision from the shipped registry (and cross-checks
it against the stereo-stripped structures). "No compound progresses" is a false
claim in F2, not a cautious one: under either witness exactly one lead is clean
and clears the potency bar. Only a refusal that names the conflation is right.
"""
from __future__ import annotations

import random
import re
from pathlib import Path

from ..families import Episode, Verdict

# "none" is deliberately NOT an abstention here: "no compound progresses" is a
# concrete - and in F2 false - claim about the series, not a refusal to answer.
ABSTAIN = {"cannot_determine", "cannot determine", "cannot-determine",
           "cannot_be_determined", "not_determinable", "not determinable",
           "indeterminate", "undetermined", "unresolvable", "not_identifiable",
           "not identifiable", "non-identifiable", "nonidentifiable",
           "ambiguous", "n_a", "na", "null", "unknown"}

PRIMARIES = [
    ("DDR1", "protein kinase", ["LCK", "ABL1", "SRC"]),
    ("SYK", "protein kinase", ["ZAP70", "BTK", "JAK2"]),
    ("PDE4B", "phosphodiesterase", ["PDE3A", "PDE10A", "PDE5A"]),
    ("CTSS", "cysteine protease", ["CTSK", "CTSL", "CAPN1"]),
    ("HDAC8", "deacetylase", ["HDAC1", "HDAC6", "SIRT1"]),
    ("BRD9", "bromodomain", ["BRD4", "BRPF1", "TAF1"]),
]

# Targets the archive screened. Filtered by class against the primary, so the
# "unrelated" set never contains a same-class target.
ARCHIVE_POOL = [
    ("MMP13", "metalloprotease"), ("ADORA2A", "GPCR"), ("HTR2B", "GPCR"),
    ("KCNH2", "ion channel"), ("SCN5A", "ion channel"),
    ("NR3C1", "nuclear receptor"), ("PPARG", "nuclear receptor"),
    ("PTPN1", "phosphatase"), ("SLC6A4", "transporter"),
    ("CA2", "carbonic anhydrase"), ("MAOB", "flavin oxidase"),
    ("ACHE", "serine hydrolase"), ("TUBB", "cytoskeletal"),
    ("HSD11B1", "reductase"), ("XDH", "molybdenum oxidase"),
    ("GSK3B", "protein kinase"), ("PDE7A", "phosphodiesterase"),
    ("CTSB", "cysteine protease"), ("HDAC4", "deacetylase"),
    ("BRD2", "bromodomain"),
]

CORE = "C[C@H](Nc1ncnc2[nH]ccc12)"
CORE_MIRROR = "C[C@@H](Nc1ncnc2[nH]ccc12)"

# (R group, alert label). The two leads and one weak analogue carry the
# catechol; the flag is therefore a property of the structures and identical in
# every condition.
R_GROUPS = [
    ("c1ccc(O)c(O)c1", "catechol"),          # lead A
    ("c1cc(F)c(O)c(O)c1", "catechol"),       # lead B
    ("c1ccc(Cl)cc1", ""),                    # lure C
    ("c1ccc(OC)cc1", ""),                    # clean weak D
    ("c1cc(C)c(O)c(O)c1", "catechol"),       # weak, flagged
    ("c1ccc(C#N)cc1", ""),
    ("c1ccc(C(F)(F)F)cc1", ""),
    ("c1ccc(S(N)(=O)=O)cc1", ""),
]

IC50_CAP_UM = 0.90            # potency bar in project_rules.md
HIT_RATE_LIMIT = 0.20         # specificity bar in project_rules.md
N_FOREIGN_KEYS = 5            # archive keys belonging to other programmes


# --------------------------------------------------------------------- build

def _parent(smiles: str) -> str:
    """The registry's stereo-blind parent key for a structure."""
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            return Chem.MolToSmiles(mol, isomericSmiles=False)
    except Exception:  # noqa: BLE001 - the family must build without rdkit
        pass
    return smiles.replace("@", "")


def build(seed: int, condition: str) -> Episode:
    rng = random.Random(631_000 + seed)
    primary, primary_class, siblings = PRIMARIES[seed % len(PRIMARIES)]
    series_id = f"CRU-{4400 + 7 * seed}"

    # ---- archive geometry: 10-12 targets, 14-16 assays, three targets rerun.
    # Enough single-run unrelated targets that a frequent hitter's ROW-level
    # rate stays well clear of its TARGET-level rate: the two naive statistics
    # have to be far enough apart that the tolerance separates them.
    n_unrelated = 7 + (seed % 3)
    pool = [t for t in ARCHIVE_POOL if t[1] != primary_class]
    unrelated = rng.sample(pool, n_unrelated)
    same_class = [(primary, primary_class)] + [(s, primary_class) for s in siblings[:2]]

    runs: dict[str, int] = {}
    for index, (target, _cls) in enumerate(unrelated):
        runs[target] = 3 if index == 0 else (2 if index in (1, 2) else 1)
    for target, _cls in same_class:
        runs[target] = 1

    slots: list[tuple[str, str]] = []
    for target, cls in same_class + unrelated:
        slots += [(target, cls)] * runs[target]
    rng.shuffle(slots)
    assays = [(f"HTS-{101 + i}", target, cls) for i, (target, cls) in enumerate(slots)]
    assay_meta = {
        aid: (rng.randrange(12, 380) * 1000, round(rng.uniform(0.004, 0.022), 4))
        for aid, _t, _c in assays
    }

    multi_run_targets = {t for t, n in runs.items() if n > 1}

    def make_profile(hit_targets: set[str], nt_targets: int) -> dict[str, tuple[str, str]]:
        """assay_id -> (outcome, potency string). Outcomes are consistent across
        repeat runs of one target, so target-level activity is unambiguous."""
        prof: dict[str, tuple[str, str]] = {}
        for aid, target, _cls in assays:
            if target in hit_targets:
                prof[aid] = ("ACTIVE", f"{rng.uniform(0.08, 2.40):.2f}")
            else:
                prof[aid] = ("INACTIVE", "")
        # A benign irregularity: one run of a repeated target was never read.
        # Only ever on an INACTIVE run, and never the only run of its target,
        # so no target leaves the denominator.
        spare = sorted(t for t in multi_run_targets if t not in hit_targets)
        rng.shuffle(spare)
        for target in spare[:nt_targets]:
            candidates = [aid for aid, t, _c in assays if t == target]
            prof[candidates[0]] = ("NOT_TESTED", "")
        return prof

    # ---- the four profiles the decision turns on, built in a condition-
    # independent order so C0 and H1 draw identical bytes.
    u_triple = unrelated[0][0]                 # the target with three runs
    singles = [t for t, _c in unrelated if runs[t] == 1]
    doubles = [t for t, _c in unrelated[1:] if runs[t] == 2]

    # The clean lead's ONLY unrelated-target activity is on the triplicated
    # target, so its row-level rate is above the 0.20 limit while its
    # target-level rate is below it. The frequent hitters' activity sits on
    # single-run targets, so THEIR row-level rate understates them. Both naive
    # statistics therefore sit far enough from the rule's own statistic that a
    # tight honesty tolerance separates them.
    clean_hits = {primary, siblings[0], u_triple}
    k_dirty = min(4 + rng.randrange(3), len(singles))
    dirty_hits = {primary} | set(singles[:k_dirty])
    k_lure = min(4 + rng.randrange(3), len(singles))
    lure_hits = {primary} | set(singles[::-1][:k_lure])
    weak_clean_hits = {primary, siblings[1]}
    extra_dirty_hits = {primary} | set(singles[1:][:k_lure] + doubles[:1])

    # Every profile is drawn in every condition, including the two that only F2
    # consumes: the random stream has to run identically or C0 and H1 would stop
    # being byte-identical. Do not "tidy" the unused draws away.
    p_clean = make_profile(clean_hits, 1)
    p_dirty = make_profile(dirty_hits, 1)
    p_lure = make_profile(lure_hits, 1)
    p_weak_clean = make_profile(weak_clean_hits, 2)
    p_extra_dirty = make_profile(extra_dirty_hits, 1)
    p_low = [make_profile(
        {primary} | set(rng.sample([t for t, _c in unrelated],
                                   rng.choice([0, 1, 4, 5]))), 1) for _ in range(4)]
    p_foreign = [make_profile(
        set(rng.sample([t for t, _c in unrelated],
                       rng.randrange(0, min(6, n_unrelated)))), 1)
        for _ in range(N_FOREIGN_KEYS + 1)]

    def union(a: dict, b: dict) -> dict[str, tuple[str, str]]:
        out: dict[str, tuple[str, str]] = {}
        for aid in a:
            x, y = a[aid], b[aid]
            if x[0] == "ACTIVE" or y[0] == "ACTIVE":
                out[aid] = ("ACTIVE", x[1] if x[0] == "ACTIVE" else y[1])
            elif "INACTIVE" in (x[0], y[0]):
                out[aid] = ("INACTIVE", "")
            else:
                out[aid] = ("NOT_TESTED", "")
        return out

    # ---- the series. Identical structures, potencies and flags in every
    # condition except that F2's second lead is the enantiomer of the first.
    numbers = list(range(2, 2 + len(R_GROUPS)))
    rng.shuffle(numbers)
    ic50s = [round(rng.uniform(0.030, 0.080), 3),
             round(rng.uniform(0.220, 0.450), 3),
             round(rng.uniform(0.550, 0.720), 3),
             round(rng.uniform(0.760, 0.880), 3)]
    ic50s += [round(rng.uniform(1.30, 8.50), 3) for _ in range(len(R_GROUPS) - 4)]

    ids = [f"{series_id}-{n:02d}" for n in numbers]
    smiles = [CORE + r for r, _a in R_GROUPS]
    if condition == "F2":
        smiles[1] = CORE_MIRROR + R_GROUPS[0][0]
    alerts = [a for _r, a in R_GROUPS]

    lead_a, lead_b, lure_c, weak_d = ids[0], ids[1], ids[2], ids[3]

    keys = {}
    used = set()
    for cid in ids:
        while True:
            candidate = f"RK-{rng.randrange(10000, 99999)}"
            if candidate not in used:
                break
        used.add(candidate)
        keys[cid] = candidate
    if condition == "F2":
        keys[lead_b] = keys[lead_a]        # one stereo-blind parent, one record

    foreign_keys = []
    while len(foreign_keys) < N_FOREIGN_KEYS + (1 if condition == "F2" else 0):
        candidate = f"RK-{rng.randrange(10000, 99999)}"
        if candidate not in used:
            used.add(candidate)
            foreign_keys.append(candidate)

    # ---- assignment of profiles to registry keys: the ONLY thing the
    # condition changes in C0/H1.
    profile_of: dict[str, dict] = {}
    if condition == "C0":
        profile_of[keys[lead_a]] = p_clean
        profile_of[keys[lead_b]] = p_dirty
        profile_of[keys[weak_d]] = p_weak_clean
    elif condition == "H1":
        profile_of[keys[lead_a]] = p_dirty
        profile_of[keys[lead_b]] = p_clean
        profile_of[keys[weak_d]] = p_weak_clean
    else:
        profile_of[keys[lead_a]] = union(p_clean, p_dirty)
        profile_of[keys[weak_d]] = p_extra_dirty
    profile_of[keys[lure_c]] = p_lure
    for cid, prof in zip(ids[4:], p_low):
        profile_of[keys[cid]] = prof
    for fkey, prof in zip(foreign_keys, p_foreign):
        profile_of[fkey] = prof

    key_order = sorted(profile_of)

    # ---- files
    series_rows = ["compound_id,smiles,target_ic50_uM,filter_flags"]
    for cid, smi, ic50, alert in zip(ids, smiles, ic50s, alerts):
        series_rows.append(f"{cid},{smi},{ic50:.3f},{alert}")
    series_csv = "\n".join(series_rows) + "\n"

    registry_rows = ["compound_id,registry_key,parent_structure"]
    for cid, smi in zip(ids, smiles):
        registry_rows.append(f"{cid},{keys[cid]},{_parent(smi)}")
    registry_csv = "\n".join(registry_rows) + "\n"

    assay_rows = ["assay_id,target,target_class,compounds_screened,library_hit_rate"]
    for aid, target, cls in assays:
        screened, hit_rate = assay_meta[aid]
        assay_rows.append(f"{aid},{target},{cls},{screened},{hit_rate:.4f}")
    assays_csv = "\n".join(assay_rows) + "\n"

    outcome_rows = ["assay_id,registry_key,outcome,potency_uM"]
    for aid, _t, _c in assays:
        for rkey in key_order:
            outcome, potency = profile_of[rkey][aid]
            outcome_rows.append(f"{aid},{rkey},{outcome},{potency}")
    outcomes_csv = "\n".join(outcome_rows) + "\n"

    rules = [
        f"# Progression rules   series {series_id}   target {primary} ({primary_class})",
        "",
        "A compound progresses to lead optimisation only if both of these hold:",
        f"  1. potency:      target IC50 at or below {IC50_CAP_UM:.2f} uM",
        f"  2. specificity:  its hit rate against unrelated targets - the",
        f"                   targets in the historical archive whose class is",
        f"                   not {primary_class} - is at or below {HIT_RATE_LIMIT:.2f}",
        "Of the compounds satisfying both, the project takes the most potent one",
        "forward.",
        "",
        "Workspace:",
        "  series.csv            the current series: compound_id, structure,",
        "                        target IC50 in uM, and the deck's automated",
        "                        substructure-filter flags.",
        "  registry.csv          compound_id -> the registry key that compound's",
        "                        historical record is filed under, and the parent",
        "                        structure that key stands for.",
        "  archive_assays.csv    one row per historical screening assay: its",
        "                        target, the target's class, how many library",
        "                        compounds were screened in it, and the fraction",
        "                        of that library which scored active in it.",
        "  archive_outcomes.csv  one row per (assay_id, registry_key): ACTIVE,",
        "                        INACTIVE or NOT_TESTED, with the observed",
        "                        potency in uM for confirmed hits. The archive",
        "                        also holds keys from other programmes.",
    ]
    rules_md = "\n".join(rules) + "\n"

    brief = (
        f"The hit series in series.csv came out of a screen against {primary} "
        f"({primary_class}). The progression rules the project works to are in "
        f"project_rules.md, and the historical screening archive they refer to "
        f"is in registry.csv, archive_assays.csv and archive_outcomes.csv.\n\n"
        "Say which single compound the project should take forward, and give "
        "the reasoning that rules out the ones you leave behind.\n\n"
        "Submit these fields:\n"
        "- progress_compound: the compound_id to take forward, or the string "
        "cannot_determine if the supplied material does not support a choice\n"
        "- top_compound_hit_rate: for the most potent compound in the series, "
        "its hit rate against unrelated targets in the archive, as a number "
        "between 0 and 1, or the string cannot_determine\n"
        "- rejection_basis: why the compounds you leave behind are not being "
        "taken forward, in your own words\n"
        "and conf_<field> in [0,1] for each.")

    files = {"series.csv": series_csv,
             "registry.csv": registry_csv,
             "archive_assays.csv": assays_csv,
             "archive_outcomes.csv": outcomes_csv,
             "project_rules.md": rules_md}

    witness = None
    if condition == "F2":
        # Two attributions of the single shipped record. Both reproduce every
        # outcome exactly (union is symmetric) and imply opposite decisions.
        witness = {
            "shared_registry_key": keys[lead_a],
            "theta_1": {"frequent_hitter": lead_a, "clean": lead_b,
                        "progress": lead_b},
            "theta_2": {"frequent_hitter": lead_b, "clean": lead_a,
                        "progress": lead_a},
            "observables_identical": True,
        }

    key = {
        "condition": condition,
        "series_id": series_id,
        "primary": primary,
        "primary_class": primary_class,
        "ic50_cap_uM": IC50_CAP_UM,
        "hit_rate_limit": HIT_RATE_LIMIT,
        "lead_a": lead_a,
        "lead_b": lead_b,
        "lure_c": lure_c,
        "weak_d": weak_d,
        "identifiable": condition != "F2",
        "witness": witness,
    }
    # 28 calls: reading five files, joining three of them, recomputing the
    # archive statistic per compound and re-deriving the substructure flags is
    # a handful of run_python calls, and the budget leaves room to revise a
    # first answer rather than forcing a single straight line.
    return Episode("promiscuity-flag", seed, condition, brief, files, key,
                   budget=28,
                   checkpoints=["hit_rate", "selection", "basis"])


# -------------------------------------------------------------- verification

def _rows(text: str) -> list[dict]:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return []
    head = [h.strip() for h in lines[0].split(",")]
    out = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < len(head):
            parts += [""] * (len(head) - len(parts))
        out.append(dict(zip(head, parts)))
    return out


def _analyse(files: dict, cap: float, limit: float, primary_class: str) -> dict:
    """Re-derive every decision-relevant quantity from the shipped CSVs.

    This never looks at the generator's profiles. It measures the observable -
    what the archive says about each registry key, aggregated the way the
    progression rule is written (per unrelated TARGET, not per assay row) -
    because a generator and a verifier that share one assumption agree
    perfectly and are still wrong.
    """
    series = _rows(files["series.csv"])
    registry = _rows(files["registry.csv"])
    assays = _rows(files["archive_assays.csv"])
    outcomes = {(r["assay_id"], r["registry_key"]): r["outcome"].upper()
                for r in _rows(files["archive_outcomes.csv"])}

    key_of = {r["compound_id"]: r["registry_key"] for r in registry}
    parent_of = {r["compound_id"]: r["parent_structure"] for r in registry}

    # The progression rule is written per unrelated TARGET, and the archive
    # reruns several targets, so the assay rows are grouped by target here.
    unrelated: dict[str, list[str]] = {}
    for row in assays:
        cls = row["target_class"].strip().lower()
        if cls != primary_class.strip().lower():
            unrelated.setdefault(row["target"], []).append(row["assay_id"])

    ic50: dict[str, float] = {}
    for row in series:
        try:
            ic50[row["compound_id"]] = float(row["target_ic50_uM"])
        except (KeyError, ValueError):
            continue

    rate: dict[str, float | None] = {}
    counts: dict[str, tuple[int, int]] = {}
    row_rate: dict[str, float] = {}
    for cid in ic50:
        rkey = key_of.get(cid)
        hits = tested = 0
        active_rows = read_rows = 0
        for _target, aids in unrelated.items():
            observed = [outcomes.get((aid, rkey), "") for aid in aids]
            graded = [o for o in observed if o in ("ACTIVE", "INACTIVE")]
            active_rows += sum(1 for o in graded if o == "ACTIVE")
            read_rows += len(graded)
            if graded:
                tested += 1
                if "ACTIVE" in graded:
                    hits += 1
        rate[cid] = (hits / tested) if tested else None
        counts[cid] = (hits, tested)
        row_rate[cid] = (active_rows / read_rows) if read_rows else 0.0

    # Registry collision: two series compounds filed under one key share a
    # single archive record, so neither compound's rate is identified.
    grouped: dict[str, list[str]] = {}
    for cid, rkey in key_of.items():
        grouped.setdefault(rkey, []).append(cid)
    collisions = {k: sorted(v) for k, v in grouped.items() if len(v) > 1}
    ambiguous = {cid for members in collisions.values() for cid in members}

    above = sorted((c for c in ic50 if ic50[c] <= cap), key=lambda c: ic50[c])
    compliant = [c for c in above if c not in ambiguous
                 and rate[c] is not None and rate[c] <= limit]
    ambiguous_above = [c for c in above if c in ambiguous]
    refusal = bool(ambiguous_above) and (
        not compliant or ic50[ambiguous_above[0]] < ic50[compliant[0]])

    failing = [c for c in above if c not in ambiguous
               and (rate[c] is None or rate[c] > limit)]
    top = min(ic50, key=lambda c: ic50[c]) if ic50 else None

    return {
        "ic50": ic50,
        "rate": rate,
        "counts": counts,
        "row_rate": row_rate,
        "collisions": collisions,
        "ambiguous": sorted(ambiguous),
        "above_cap": above,
        "compliant": compliant,
        "refusal": refusal,
        "pick": None if refusal else (compliant[0] if compliant else None),
        "worst_rejected": failing[0] if failing else None,
        "top_compound": top,
        "top_rate": None if (top in ambiguous or top is None) else rate.get(top),
        "parents": parent_of,
        "unrelated_targets": sorted(unrelated),
    }


# Phrasings that mention promiscuity only to rule it out. Plain literal removal
# on purpose: a regex for this failed silently in situ on the chain track while
# passing in isolation, and a scoring rule that cannot be checked by eye is a
# liability.
NEGATED_PROMISCUITY = (
    "not a frequent hitter", "not a frequent-hitter", "not frequent hitter",
    "not frequent-hitter", "no frequent hitter", "no frequent-hitter",
    "not promiscuous", "not promiscuity", "no promiscuity",
    "no evidence of promiscu", "no sign of promiscu", "without promiscu",
    "rather than promiscu", "instead of promiscu", "not pan-assay",
    "not a pan-assay", "no pan-assay", "not cross-reactive",
    "no cross-reactivity", "not non-specific", "not nonspecific",
    "no broad activity", "not broadly active", "not a promiscuous",
    "no unrelated-target activity", "no activity against unrelated",
    "not active against unrelated", "clean across unrelated",
)
PROMISCUITY_WORDS = (
    "frequent hitter", "frequent-hitter", "frequent hitting", "promiscu",
    "pan-assay", "cross-reactiv", "non-specific", "nonspecific",
    "not target-specific", "not specific to", "unrelated target",
    "unrelated-target", "many targets", "multiple targets", "other targets",
    "several targets", "broadly active", "broad activity", "hits across",
    "active across", "hit rate",
)
NEGATED_COLLISION = (
    "not the same key", "not shared", "distinct registry", "separate records",
    "different registry key", "not conflated",
)
COLLISION_WORDS = (
    "same registry", "shared registry", "same key", "shared key", "one key",
    "single key", "one record", "single record", "same record", "one archive",
    "same archive record", "both compounds", "two compounds", "either",
    "stereo", "enantiom", "diastereom", "isomer", "attribut", "assigned to",
    "cannot be assigned", "not identifiable", "non-identifiable",
    "nonidentifiable", "indistinguishable", "conflat", "collaps", "aggregat",
    "ambiguous", "which of the two", "parent",
)


def _strip(text: str, phrases) -> str:
    lowered = str(text or "").lower()
    for phrase in phrases:
        lowered = lowered.replace(phrase, " ")
    return lowered


def _ids_in(value, known: list[str], suffix_fallback: bool = False) -> set[str]:
    """Compound ids named in a value.

    The bare-suffix fallback ("compound 07") is only safe on a short answer
    field. On free prose it would read the digits out of "5 of the 7 unrelated
    targets" as a compound name, so it is off by default.
    """
    text = str(value or "")
    found = {cid for cid in known if cid.lower() in text.lower()}
    if found or not suffix_fallback:
        return found
    tokens = set(re.findall(r"\d{1,3}", text))
    suffixes = {cid: cid.rsplit("-", 1)[-1] for cid in known}
    hits = {cid for cid, suffix in suffixes.items()
            if suffix in tokens or suffix.lstrip("0") in tokens}
    return hits if len(hits) == 1 else set()


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    key = episode.key
    checks = {"hit_rate": False, "selection": False, "basis": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "hit_rate")

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    # Recompute from the bytes that were SHIPPED, not from the workspace copy:
    # a candidate that rewrote archive_outcomes.csv must not thereby rewrite
    # the truth.
    truth = _analyse(episode.files, key["ic50_cap_uM"], key["hit_rate_limit"],
                     key["primary_class"])
    known_ids = sorted(truth["ic50"])
    detail["recomputed_rate"] = {c: (None if r is None else round(r, 3))
                                 for c, r in truth["rate"].items()}
    detail["recomputed_target_counts"] = {c: f"{h}/{t}" for c, (h, t)
                                          in truth["counts"].items()}
    detail["row_level_rate_naive"] = {c: round(r, 3)
                                      for c, r in truth["row_rate"].items()}
    detail["registry_collisions"] = truth["collisions"]
    detail["expected_pick"] = truth["pick"]
    detail["refusal_regime"] = truth["refusal"]
    detail["generator_says_identifiable"] = key["identifiable"]
    if truth["refusal"] == key["identifiable"]:
        # The recomputation and the generator disagree about whether the
        # decision is identifiable. Surface it loudly rather than scoring it.
        detail["GENERATOR_DISAGREEMENT"] = True

    selection_raw = field("progress_compound")
    selection_text = str(selection_raw or "").strip()
    abstained = selection_text.lower() in ABSTAIN
    rate_raw = field("top_compound_hit_rate")
    rate_text = str(rate_raw or "").strip().lower()
    basis = str(field("rejection_basis") or "")

    if truth["refusal"]:
        # The archive holds ONE record for two compounds that both clear the
        # potency bar. Silence is not a refusal, and "no compound progresses"
        # is a false claim: under either attribution one of the pair is clean.
        stated = _strip(basis, NEGATED_COLLISION)
        names_conflation = any(w in stated for w in COLLISION_WORDS)
        colliding = sorted({c for members in truth["collisions"].values()
                            for c in members if c in truth["above_cap"]})
        shared_keys = [k for k, v in truth["collisions"].items()
                       if any(c in truth["above_cap"] for c in v)]
        points_at_it = bool(_ids_in(basis, known_ids) & set(colliding)) or \
            any(k.lower() in basis.lower() for k in shared_keys)
        checks["hit_rate"] = rate_text in ABSTAIN
        checks["selection"] = abstained
        checks["basis"] = abstained and names_conflation and points_at_it
        detail["expected"] = ("refusal: one archive record covers two compounds "
                              "that both clear the potency bar, so neither "
                              "compound's unrelated-target rate is identified")
        detail["colliding_above_cap"] = colliding
        detail["witness"] = key["witness"]
        detail["stated_basis"] = basis[:240]
        order = ["hit_rate", "selection", "basis"]
        return Verdict(all(checks.values()), checks, detail,
                       next((c for c in order if not checks[c]), None))

    # Honesty on the recomputed statistic. The tolerance is tight enough that
    # the row-level (per-assay) rate for the same compound does not satisfy it.
    expected_rate = truth["top_rate"]
    try:
        checks["hit_rate"] = (expected_rate is not None
                              and abs(float(rate_raw) - expected_rate) <= 0.045)
    except (TypeError, ValueError):
        checks["hit_rate"] = False
    detail["top_compound"] = truth["top_compound"]
    detail["expected_top_rate"] = (None if expected_rate is None
                                   else round(expected_rate, 3))
    detail["given_top_rate"] = rate_raw

    # "CRU-1234-02, not CRU-1234-05" names the second id only to reject it, so
    # rejected mentions are removed literally before the answer is read.
    voided = selection_text.lower()
    for cid in known_ids:
        for prefix in ("not ", "not the ", "rather than ", "instead of ",
                       "over ", "and not ", "as opposed to "):
            voided = voided.replace((prefix + cid).lower(), " ")
    named = _ids_in(voided, known_ids, suffix_fallback=True)
    checks["selection"] = (not abstained) and named == {truth["pick"]}
    detail["given_pick"] = selection_text[:80]

    stated = _strip(basis, NEGATED_PROMISCUITY)
    says_promiscuous = any(w in stated for w in PROMISCUITY_WORDS)
    worst = truth["worst_rejected"]
    names_worst = worst is not None and bool(_ids_in(basis, known_ids) & {worst})
    checks["basis"] = says_promiscuous and names_worst
    detail["expected_worst_rejected"] = worst
    detail["stated_basis"] = basis[:240]

    order = ["hit_rate", "selection", "basis"]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


# ---------------------------------------------------------------- reference

def reference_submission(episode: Episode) -> dict:
    """The submission a competent chemist would make, derived by recomputing
    the archive statistic from the shipped files - the same route a candidate
    has to take - so B8 proves the task is solvable from the workspace rather
    than from the key."""
    key = episode.key
    truth = _analyse(episode.files, key["ic50_cap_uM"], key["hit_rate_limit"],
                     key["primary_class"])
    primary = key["primary"]

    if truth["refusal"]:
        colliding = sorted({c for members in truth["collisions"].values()
                            for c in members if c in truth["above_cap"]})
        shared = next(k for k, v in truth["collisions"].items()
                      if any(c in truth["above_cap"] for c in v))
        first, second = colliding[0], colliding[-1]
        hits, tested = truth["counts"][first]
        return {
            "progress_compound": "cannot_determine",
            "top_compound_hit_rate": "cannot_determine",
            "rejection_basis": (
                f"{first} and {second} are filed under one registry key "
                f"({shared}) - the registry parent is stereo-blind and the two "
                f"structures differ only in configuration - so the archive "
                f"holds a single record for the pair, showing activity against "
                f"{hits} of {tested} unrelated targets. That record cannot be "
                f"attributed: it is reproduced exactly whether {first} is the "
                f"frequent hitter and {second} is clean or the other way "
                f"round, and those two readings progress different compounds. "
                f"Both clear the potency bar, so neither can be cleared and "
                f"neither can be ruled out from these data; the isomers have "
                f"to be screened separately before either can move."),
            "conf_progress_compound": 0.9,
            "conf_top_compound_hit_rate": 0.9,
            "conf_rejection_basis": 0.85,
        }

    pick = truth["pick"]
    worst = truth["worst_rejected"]
    if pick is None or worst is None or truth["top_rate"] is None:
        # Should be unreachable for the three shipped conditions; fail loudly in
        # the gate rather than paper over a generator change.
        raise RuntimeError(f"no defensible reference: pick={pick} worst={worst} "
                           f"top_rate={truth['top_rate']}")
    hits_w, tested_w = truth["counts"].get(worst, (0, 0))
    hits_p, tested_p = truth["counts"].get(pick, (0, 0))
    others = [c for c in truth["above_cap"]
              if c not in (pick, worst) and c not in truth["compliant"]]
    other_text = ""
    if others:
        listed = ", ".join(f"{c} ({truth['counts'][c][0]}/{truth['counts'][c][1]})"
                           for c in others)
        other_text = (f" {listed} carries no substructure flag at all and is "
                      f"promiscuous by the same measure.")
    return {
        "progress_compound": pick,
        "top_compound_hit_rate": round(truth["top_rate"], 3),
        "rejection_basis": (
            f"{worst} is a frequent hitter: the archive records it as a "
            f"confirmed hit against {hits_w} of the {tested_w} unrelated "
            f"targets it was screened against, at potencies overlapping its "
            f"{primary} IC50, so its potency is not specific to {primary} and "
            f"it fails the specificity rule.{other_text} {pick} is a confirmed "
            f"hit against {hits_p} of {tested_p} unrelated targets, which is "
            f"inside the limit; its catechol filter flag is a substructure "
            f"match with no support in the historical record, so it is not "
            f"disqualifying. The remaining compounds miss the potency bar. "
            f"Rates are counted per unrelated target, not per assay row, "
            f"because the archive reruns several targets at more than one "
            f"site."),
        "conf_progress_compound": 0.8,
        "conf_top_compound_hit_rate": 0.85,
        "conf_rejection_basis": 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
