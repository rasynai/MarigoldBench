"""Family: enrichment-null - is a virtual screen's hit list actually enriched?

The docking-power deep read (`analysis/literature2/deep/docking-power.md`) is
the source: retrospective screening benchmarks are dominated by *decoy
artifacts* - "models separate on simple physicochemical properties, not
binding" - and by enrichment factors quoted with no null model at all. A hit
list with EF 4 looks like a result and is routinely bought. Whether it IS a
result depends on a comparison the raw number cannot supply.

So the episode ships one deck: docking scores, four physicochemical columns,
the compounds the campaign flagged for purchase, and the subset with prior
dose-response confirmation. The enrichment factor is arithmetic and settles
nothing. The judgment lives in what the model compares it against:

  C0  the deck is clean. Two flavours by seed - either the score carries
      genuine activity information (verdict `supported`), or it does not and
      the eye-catching EF is inside the range chance produces at this deck
      size (verdict `not_supported`). Either way nothing in the material is
      broken, so calling a defect is a false alarm.
  H1  the confirmed actives are shifted on one physicochemical column and the
      docking score tracks that column and nothing else. The plain
      label-permutation null is wildly significant; permuting labels only
      among compounds matched on that column is not.
  F2  the deck carries a single confirmed active. The smallest p-value ANY
      ranking could reach against the permutation null is then the hit
      fraction itself, about a tenth - roughly twice the threshold - so no
      statistic computed on this deck can answer the question however good
      the screen is. A documented refusal is the only correct outcome.

C0 and H1 briefs are byte-identical; `screen_notes.txt` is identical too. The
whole difference is in the numbers in `screen_deck.csv`.

Truth is constructed: the generator writes the CSV, parses its own rounded
bytes back, and runs the permutation nulls on them, retrying until the
episode meets its intended margins. `verify()` re-runs exactly the same
recomputation on the shipped bytes and grades against THAT, not against the
stored key, and it recomputes the counts and the enrichment factor the model
reports so a self-reported number is never evidence.
"""
from __future__ import annotations

import csv
import io
import math
import re
from pathlib import Path

from ..families import Episode, Verdict

DECK_FILE = "screen_deck.csv"
NOTES_FILE = "screen_notes.txt"
COLUMNS = ("compound_id", "dock_score", "mw", "clogp", "tpsa", "hba",
           "picked", "confirmed_active")
PROPERTIES = ("mw", "clogp", "tpsa", "hba")

ALPHA = 0.05           # significance level for every null in this family
NULL_REPS = 4000       # permutation replicates; fixed so scoring is exact
NULL_SEED = 0xE7C0DE   # fixed RNG seed: build and verify must agree bit for bit
N_STRATA = 5           # quantile bins used by the property-matched null

TARGETS = ["KAT2A", "ADRB2", "FEN1", "PKM2", "IDH1", "VDR", "MAPK1", "ESR1"]
PROGRAMS = ["AutoDock-GPU 1.5", "Vina 1.2.5", "Glide SP", "GNINA 1.1",
            "rDock 24.1", "Smina"]

# Words that count as naming a physicochemical column, for grading the
# free-text explanation against the recomputed confound.
PROPERTY_WORDS = {
    "mw": ("mw", "molecular weight", "molweight", "mol. weight", "molwt",
           "molecular-weight", "weight", "heavy atom count"),
    "clogp": ("clogp", "logp", "log p", "lipophilic", "lipophilicity",
              "hydrophobic"),
    "tpsa": ("tpsa", "polar surface", "psa"),
    "hba": ("hba", "acceptor", "acceptors"),
}


# --------------------------------------------------------------------- stats

def _parse_deck(text: str) -> dict:
    """Read the shipped CSV into arrays. This is the only route to the data."""
    import numpy as np

    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise ValueError("empty deck")
    deck: dict = {"compound_id": [r["compound_id"] for r in rows]}
    for column in COLUMNS[1:]:
        deck[column] = np.array([float(r[column]) for r in rows])
    return deck


def _quantile_strata(values, n_bins: int):
    """Rank-based equal-count bins. Deterministic, ties broken by row order."""
    import numpy as np

    order = np.argsort(values, kind="stable")
    ranks = np.empty(values.size, dtype=int)
    ranks[order] = np.arange(values.size)
    return (ranks * n_bins) // values.size


def _permutation_counts(labels, picked, rng, reps: int):
    """Null distribution of actives-in-hits when labels are permuted freely."""
    import numpy as np

    keys = rng.random((reps, labels.size))
    order = np.argsort(keys, axis=1, kind="stable")
    return labels[order][:, picked].sum(axis=1)


def _matched_counts(labels, picked, strata, rng, reps: int):
    """Same permutation, but labels only move among compounds in one bin.

    Holding the physicochemical bin fixed is what separates "the score found
    binders" from "the score found a property the actives happen to share".
    """
    import numpy as np

    total = np.zeros(reps, dtype=int)
    for bin_id in np.unique(strata):
        index = np.flatnonzero(strata == bin_id)
        if index.size == 0:
            continue
        labels_bin = labels[index]
        picked_bin = picked[index]
        if not picked_bin.any() or not labels_bin.any():
            continue
        keys = rng.random((reps, index.size))
        order = np.argsort(keys, axis=1, kind="stable")
        total += labels_bin[order][:, picked_bin].sum(axis=1)
    return total


def _min_attainable_p(n: int, k: int, n_hits: int) -> float:
    """Smallest permutation p-value any ranking could reach on this deck.

    Every one of the k actives ranked into the hit list is the best case; if
    even that is not significant, the deck cannot answer the question however
    good the screen is.
    """
    if k <= 0 or n_hits <= 0 or k > n:
        return 1.0
    best = min(k, n_hits)
    return (math.comb(n_hits, best) * math.comb(n - n_hits, k - best)
            / math.comb(n, k))


def _analyse(deck: dict) -> dict:
    """The canonical recomputation. Build and verify both call exactly this."""
    import numpy as np

    labels = deck["confirmed_active"].astype(bool)
    picked = deck["picked"].astype(bool)
    n = int(labels.size)
    k = int(labels.sum())
    n_hits = int(picked.sum())
    a_obs = int((labels & picked).sum())
    base = k / n if n else 0.0
    ef = (a_obs / n_hits) / base if (base > 0 and n_hits) else 0.0

    p_floor = _min_attainable_p(n, k, n_hits)
    plain = _permutation_counts(labels, picked, np.random.default_rng(NULL_SEED),
                                NULL_REPS)
    p_plain = float((1 + int((plain >= a_obs).sum())) / (NULL_REPS + 1))

    p_matched: dict[str, float] = {}
    for i, prop in enumerate(PROPERTIES):
        strata = _quantile_strata(deck[prop], N_STRATA)
        counts = _matched_counts(labels, picked, strata,
                                 np.random.default_rng([NULL_SEED, i]), NULL_REPS)
        p_matched[prop] = float((1 + int((counts >= a_obs).sum())) / (NULL_REPS + 1))

    explained = [p for p in PROPERTIES if p_matched[p] > ALPHA]
    if p_floor > ALPHA:
        verdict, reason, driver = "cannot_determine", "underpowered", None
    elif p_plain > ALPHA:
        verdict, reason, driver = "not_supported", "no_enrichment", None
    elif explained:
        driver = max(explained, key=lambda p: p_matched[p])
        verdict, reason = "not_supported", "confounded"
    else:
        verdict, reason, driver = "supported", "survives_matching", None

    return {"n": n, "n_known_actives": k, "n_hits": n_hits,
            "n_actives_in_hits": a_obs, "ef": ef, "p_floor": p_floor,
            "p_plain": p_plain, "p_matched": p_matched,
            "explained_by": explained, "verdict": verdict, "reason": reason,
            "driver": driver}


# ----------------------------------------------------------------- generation

def _deck_text(rng, n: int, k: int, n_hits: int, confound: str,
               delta: float, w_prop: float, w_act: float,
               single_active_in_hits: bool | None) -> str:
    """Fabricate one deck and render it exactly as the model will read it."""
    import numpy as np

    conf_index = PROPERTIES.index(confound)
    latent = rng.standard_normal((n, 4))
    shared = rng.standard_normal(n)
    latent = 0.92 * latent + 0.33 * shared[:, None]

    active = np.zeros(n, dtype=bool)
    if k > 0:
        active[rng.choice(n, size=k, replace=False)] = True
    latent[:, conf_index] += delta * active

    score = -(6.8 + w_prop * latent[:, conf_index] + w_act * active
              + 0.75 * rng.standard_normal(n))
    score = np.round(score, 2)

    order = np.argsort(score, kind="stable")
    picked = np.zeros(n, dtype=bool)
    picked[order[:n_hits]] = True
    if score[order[n_hits - 1]] == score[order[n_hits]]:
        raise _Retry("hit-list boundary is a tie in the rounded score")

    if single_active_in_hits is not None:
        # F2 decks carry one confirmed active; the seed decides whether the
        # campaign happened to pick it.
        active[:] = False
        pool = np.flatnonzero(picked if single_active_in_hits else ~picked)
        active[pool[rng.integers(pool.size)]] = True

    mw = np.round(340.0 + 45.0 * latent[:, 0], 1)
    clogp = np.round(3.0 + 1.1 * latent[:, 1], 2)
    tpsa = np.round(76.0 + 22.0 * latent[:, 2], 1)
    hba = np.clip(np.round(4.6 + 1.6 * latent[:, 3]), 1, 11).astype(int)

    lines = [",".join(COLUMNS)]
    for i in range(n):
        lines.append(f"C{i + 1:03d},{score[i]:.2f},{mw[i]:.1f},{clogp[i]:.2f},"
                     f"{tpsa[i]:.1f},{hba[i]:d},{int(picked[i])},{int(active[i])}")
    return "\n".join(lines) + "\n"


class _Retry(Exception):
    """This draw did not land inside the intended margins; take another."""


def _margins_ok(condition: str, flavour: str, stats: dict, confound: str) -> bool:
    """The constructed-truth contract, stated as inequalities on recomputation."""
    if condition == "F2":
        return (stats["verdict"] == "cannot_determine"
                and stats["n_known_actives"] == 1
                and stats["p_floor"] >= 1.7 * ALPHA)
    if condition == "H1":
        return (stats["verdict"] == "not_supported"
                and stats["reason"] == "confounded"
                and stats["driver"] == confound
                and stats["p_plain"] <= 0.002
                and stats["p_matched"][confound] >= 0.20
                and stats["ef"] >= 3.0)
    if flavour == "real":
        return (stats["verdict"] == "supported"
                and stats["p_plain"] <= 0.002
                and max(stats["p_matched"].values()) <= 0.01
                and stats["ef"] >= 2.5)
    return (stats["verdict"] == "not_supported"
            and stats["reason"] == "no_enrichment"
            and 0.10 <= stats["p_plain"] <= 0.60
            and stats["ef"] >= 1.5)


def _episode_parameters(seed: int) -> dict:
    import numpy as np

    rng = np.random.default_rng([31_337, seed])
    return {
        "n": int(rng.choice([138, 142, 146, 150])),
        "k": int(rng.integers(11, 18)),
        "n_hits": int(rng.choice([14, 16, 18])),
        "confound": PROPERTIES[seed % len(PROPERTIES)],
        "flavour": "real" if seed % 2 else "absent",
        "target": TARGETS[seed % len(TARGETS)],
        "program": PROGRAMS[seed % len(PROGRAMS)],
        "active_in_hits": bool(seed % 3),
    }


def _make_files(seed: int, condition: str) -> tuple[str, dict, dict]:
    """Draw until the recomputed statistics meet the condition's margins."""
    import numpy as np

    spec = _episode_parameters(seed)
    n, n_hits, confound = spec["n"], spec["n_hits"], spec["confound"]
    flavour = spec["flavour"]

    if condition == "F2":
        k = 1
        delta, w_prop, w_act = 0.0, 0.9, 0.0
        single = spec["active_in_hits"]
    else:
        k = spec["k"]
        single = None
        # The two C0 flavours share a generative structure with H1 as far as
        # anything visible goes: in all three the confirmed actives sit high
        # on one property and the docking score leans on that property. Only
        # the activity term differs, and only a matched null can see it.
        if condition == "H1":
            delta, w_prop, w_act = 1.10, 1.35, 0.0
        elif flavour == "real":
            delta, w_prop, w_act = 0.70, 0.90, 1.55
        else:
            delta, w_prop, w_act = 0.70, 0.90, 0.55

    code = {"C0": 1, "H1": 2, "F2": 3}[condition]
    for attempt in range(400):
        # Anneal the activity weight for the two flavours whose margin is a
        # window rather than a tail: a fixed weight can miss it for a seed.
        step = attempt // 40
        if condition == "C0" and flavour == "absent":
            weight = w_act * (1.0 + 0.10 * ((step % 5) - 2))
        elif condition == "C0":
            weight = w_act * (1.0 + 0.08 * (step % 4))
        else:
            weight = w_act
        rng = np.random.default_rng([50_021, seed, code, attempt])
        try:
            text = _deck_text(rng, n, k, n_hits, confound, delta, w_prop,
                              weight, single)
        except _Retry:
            continue
        stats = _analyse(_parse_deck(text))
        if _margins_ok(condition, flavour, stats, confound):
            return text, stats, spec
    raise RuntimeError(f"enrichment-null: no draw met margins for seed {seed} "
                       f"condition {condition}")


BRIEF = """The docking campaign described in {notes} has finished and the team
is ready to spend its purchase budget on the compounds flagged in the picked
column of {deck}.

Establish whether that hit list is genuinely enriched in the deck's confirmed
actives, and report what you find.

Submit these fields:
- n_known_actives: integer, confirmed actives in the deck
- n_actives_in_hits: integer, confirmed actives among the picked compounds
- ef_hits: number, the enrichment factor of the picked set over the deck as a
  whole
- enrichment_verdict: supported if the enrichment is real, not_supported if it
  is not, or cannot_determine if this deck cannot settle the question
- explanation: in your own words, what accounts for which compounds ended up
  in the picked set
Report the three numbers in every case, whatever your verdict is, and give
conf_<field> in [0,1] for each field."""


def build(seed: int, condition: str) -> Episode:
    text, stats, spec = _make_files(seed, condition)

    notes = (
        f"Target: {spec['target']}\n"
        f"Campaign: retrospective run of the round-2 docking protocol against "
        f"the {spec['target']} orthosteric site.\n"
        f"Deck: {stats['n']} commercially available compounds assembled for "
        f"this target. Compounds with prior dose-response confirmation against "
        f"{spec['target']} are flagged in the confirmed_active column of "
        f"{DECK_FILE}.\n"
        f"Docking: {spec['program']}, one receptor conformation, box centred on "
        f"the co-crystallised ligand; the single best pose per compound was "
        f"retained. dock_score is that pose's score in kcal/mol, more negative "
        f"is better.\n"
        f"Selection: the {stats['n_hits']} best-scoring compounds were flagged "
        f"in the picked column and are the compounds the team proposes to "
        f"purchase.\n"
        f"Also recorded per compound at deck assembly: mw, clogp, tpsa, hba.\n")

    files = {DECK_FILE: text, NOTES_FILE: notes}
    brief = BRIEF.format(notes=NOTES_FILE, deck=DECK_FILE)

    key = {
        "condition": condition,
        "flavour": spec["flavour"] if condition == "C0" else condition,
        "planted_confound": spec["confound"] if condition == "H1" else None,
        "shifted_property": spec["confound"],
        "verdict": stats["verdict"],
        "reason": stats["reason"],
        "driver": stats["driver"],
        "explained_by": stats["explained_by"],
        "n_known_actives": stats["n_known_actives"],
        "n_actives_in_hits": stats["n_actives_in_hits"],
        "n_hits": stats["n_hits"],
        "deck_size": stats["n"],
        "ef": round(stats["ef"], 4),
        "p_plain": round(stats["p_plain"], 5),
        "p_matched": {k: round(v, 5) for k, v in stats["p_matched"].items()},
        "p_floor": stats["p_floor"],
    }
    return Episode("enrichment-null", seed, condition, brief, files, key,
                   budget=12,
                   checkpoints=["counts", "enrichment", "verdict", "attribution"])


# ------------------------------------------------------------------- scoring

_ABSTAIN = {"cannot_determine", "cannot_be_determined", "undetermined",
            "insufficient_data", "insufficient", "indeterminate", "unknown",
            "inconclusive", "unclear", "ambiguous", "unanswerable",
            "n_a", "na", "none"}
_SUPPORTED = {"supported", "real", "genuine", "yes", "true", "enriched",
              "support"}
_NOT_SUPPORTED = {"not_supported", "unsupported", "not_support", "no",
                  "false", "artifact", "artefact", "confounded",
                  "not_enriched", "not_real"}


def _normalise_verdict(raw) -> str | None:
    token = str(raw or "").strip().lower()
    token = token.replace("'", "").replace("’", "")
    token = token.replace("-", "_").replace(" ", "_").replace("/", "_")
    token = token.strip("_.")
    if not token:
        # An omitted field is not a documented refusal, so it never scores as
        # one: the abstention has to be stated to count.
        return None
    if token in _ABSTAIN:
        return "cannot_determine"
    if token in _NOT_SUPPORTED:
        return "not_supported"
    if token in _SUPPORTED:
        return "supported"
    # Free-form phrasing: order matters, "not supported" contains "supported"
    # and "not enriched" contains "enriched". Abstention is tested FIRST and
    # its vocabulary has to be wide: "not determinable" starts with "not", so
    # a narrower list sent a stated refusal to `not_supported`, which fails an
    # F2 that was answered correctly AND hands a C0/H1 pass to a candidate who
    # never committed to a verdict at all.
    if any(word in token for word in
           ("cannot", "can_not", "cant_determin", "cant_tell", "insufficient",
            "underpower", "no_power", "undetermin", "indetermin",
            "not_determin", "determinab", "inconclusive", "unclear",
            "ambiguous", "unable", "untestable", "unanswerable",
            "not_answerable", "no_conclusion", "not_enough_data",
            "not_enough_active", "not_enough_power", "too_few")):
        return "cannot_determine"
    if (token.startswith("not") or token.startswith("no_")
            or any(word in token for word in
                   ("not_support", "unsupported", "not_enrich", "not_real",
                    "insignificant", "non_significant", "no_significan",
                    "artifact", "artefact", "confound", "spurious"))):
        return "not_supported"
    if any(word in token for word in ("support", "real", "genuine", "enrich",
                                      "significan")):
        return "supported"
    return None


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip().lower()
    text = text.replace("x", "").replace("fold", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        pass
    # "~4.7", "EF = 4.72", "13 actives": grade the number the model meant, so
    # that formatting is never what fails a correct answer.
    found = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    return float(found.group()) if found else None


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    order = ["counts", "enrichment", "verdict", "attribution"]
    checks = {name: False for name in order}
    detail: dict = {}

    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "counts")

    def field(name):
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == name:
                return value
        return None

    # Re-derive the truth from the shipped bytes, not from the key. The
    # workspace copy is compared but never trusted: run_python can overwrite
    # anything in there, and a rewritten deck must not move the answer.
    shipped = episode.files[DECK_FILE]
    on_disk = None
    deck_path = Path(workspace) / DECK_FILE
    if deck_path.exists():
        on_disk = deck_path.read_text(encoding="utf-8", errors="replace")
    detail["workspace_deck_matches_shipped"] = (on_disk == shipped)

    stats = _analyse(_parse_deck(shipped))
    detail["recomputed"] = {
        "n_known_actives": stats["n_known_actives"],
        "n_actives_in_hits": stats["n_actives_in_hits"],
        "n_hits": stats["n_hits"], "deck_size": stats["n"],
        "ef": round(stats["ef"], 4), "p_plain": round(stats["p_plain"], 5),
        "p_matched": {k: round(v, 5) for k, v in stats["p_matched"].items()},
        "p_floor": stats["p_floor"], "verdict": stats["verdict"],
        "reason": stats["reason"], "driver": stats["driver"]}
    detail["key_verdict"] = episode.key.get("verdict")
    detail["key_agrees_with_recomputation"] = (
        episode.key.get("verdict") == stats["verdict"]
        and episode.key.get("n_actives_in_hits") == stats["n_actives_in_hits"])

    # 1. counts - both are facts of the file, and the enrichment factor is
    #    meaningless unless the model has them right.
    given_k = _number(field("n_known_actives"))
    given_a = _number(field("n_actives_in_hits"))
    checks["counts"] = (given_k is not None and given_a is not None
                        and int(round(given_k)) == stats["n_known_actives"]
                        and int(round(given_a)) == stats["n_actives_in_hits"])
    detail["given_counts"] = [field("n_known_actives"), field("n_actives_in_hits")]

    # 2. enrichment - recomputed, so a quoted EF that the deck does not have
    #    fails even when the verdict is right.
    given_ef = _number(field("ef_hits"))
    tolerance = max(0.05, 0.03 * stats["ef"])
    checks["enrichment"] = (given_ef is not None
                            and abs(given_ef - stats["ef"]) <= tolerance)
    detail["given_ef"] = field("ef_hits")
    detail["ef_tolerance"] = round(tolerance, 4)

    # 3. verdict - the decision, graded against the recomputed nulls.
    given_verdict = _normalise_verdict(field("enrichment_verdict"))
    checks["verdict"] = given_verdict == stats["verdict"]
    detail["given_verdict"] = field("enrichment_verdict")
    detail["expected_verdict"] = stats["verdict"]

    # 4. attribution - only gradeable when a property really does account for
    #    the hit list; elsewhere there is nothing to name and the check is
    #    carried, exactly as pose-triage carries its diagnosis on a clean pose.
    if stats["reason"] == "confounded":
        stated = str(field("explanation") or "").lower()
        named = [p for p in stats["explained_by"]
                 if any(word in stated for word in PROPERTY_WORDS[p])]
        checks["attribution"] = bool(named)
        detail["acceptable_drivers"] = stats["explained_by"]
        detail["named_drivers"] = named
        detail["stated_explanation"] = stated[:300]
    else:
        checks["attribution"] = True
        detail["acceptable_drivers"] = None

    first = next((name for name in order if not checks[name]), None)
    return Verdict(all(checks.values()), checks, detail, first)


# --------------------------------------------------------------- reference

# How the reference names each column in prose. The verifier greps the
# explanation for PROPERTY_WORDS, so these strings have to speak the same
# vocabulary a chemist would use, not a code identifier the grader invented.
_PROPERTY_PHRASE = {
    "mw": "mw (molecular weight)",
    "clogp": "clogp (lipophilicity)",
    "tpsa": "tpsa (topological polar surface area)",
    "hba": "hba (hydrogen-bond acceptor count)",
}


def _reference_explanation(key: dict, ef: float) -> str:
    """The prose half of the reference answer, written from the key's own terms."""
    reason = key.get("reason")
    n_hits = key.get("n_hits")
    k = key.get("n_known_actives")
    a_obs = key.get("n_actives_in_hits")
    p_plain = key.get("p_plain")
    p_matched = key.get("p_matched") or {}
    lead = (f"The picked set is simply the {n_hits} best-scoring compounds by "
            f"dock_score, so whatever dock_score tracks is what ended up in it. ")

    if reason == "confounded":
        driver = key.get("driver")
        explained = [p for p in (key.get("explained_by") or []) if p in PROPERTIES]
        if driver in PROPERTIES and driver not in explained:
            explained = [driver] + explained
        named = ", ".join(_PROPERTY_PHRASE[p] for p in explained) or "a recorded property"
        head = _PROPERTY_PHRASE.get(driver, named)
        return (
            lead +
            f"Here it tracks {named}: the confirmed actives are shifted high on "
            f"that column, so selecting on score selects on {head} and picks up "
            f"the actives as a side effect. Permuting the confirmed_active "
            f"labels freely makes the hit list look decisive (p={p_plain}), but "
            f"permuting them only within {N_STRATA} quantile bins of {head} - "
            f"i.e. comparing each active against compounds it matches on that "
            f"property - gives p={p_matched.get(driver)}, far above {ALPHA}. The "
            f"EF of {ef:.2f} is therefore accounted for by the {head} shift, not "
            f"by the score recognising binders, and the hit list is not evidence "
            f"of enrichment.")

    if reason == "no_enrichment":
        return (
            lead +
            f"Only {a_obs} of the {k} confirmed actives landed in the "
            f"{n_hits}-compound hit list. An EF of {ef:.2f} reads like a result, "
            f"but the label-permutation null over the whole deck puts a count "
            f"that high well inside the range chance produces at this deck size "
            f"({NULL_REPS} permutations, p={p_plain}, against alpha={ALPHA}). "
            f"There is no evidence the docking score carries activity "
            f"information for this target.")

    if reason == "survives_matching":
        worst = max(p_matched.values()) if p_matched else None
        return (
            lead +
            f"In this deck it is carrying real activity information: {a_obs} of "
            f"the {k} confirmed actives are in the {n_hits} picked compounds, an "
            f"EF of {ef:.2f}, and the free label permutation gives p={p_plain}. "
            f"The result is not a property artifact either - repeating the "
            f"permutation within {N_STRATA} quantile bins of each of mw, clogp, "
            f"tpsa and hba, so labels only move between compounds matched on "
            f"that column, leaves the worst p at {worst}, still below {ALPHA}. "
            f"The enrichment survives every matched null available in this deck.")

    # reason == "underpowered": the F2 refusal.
    return (
        lead +
        f"The question cannot be settled from this deck at all. It carries "
        f"{k} confirmed active(s), so even the best case - every confirmed "
        f"active ranked into the {n_hits}-compound hit list - reaches a "
        f"permutation p-value of only {key.get('p_floor')}, above alpha="
        f"{ALPHA}. No statistic computed on this deck can demonstrate "
        f"enrichment however good the screen is, so the honest outcome is a "
        f"documented refusal rather than a verdict; the counts and EF above are "
        f"reported as facts of the file, not as evidence. Get more confirmed "
        f"actives onto the deck before asking again.")


def reference_submission(episode: Episode) -> dict:
    """The submission a competent scientist would make. Derived from
    the episode key, so it doubles as the B8 baseline check."""
    key = episode.key
    k = int(key["n_known_actives"])
    a_obs = int(key["n_actives_in_hits"])
    n_hits = int(key["n_hits"])
    n = int(key["deck_size"])

    # verify() recomputes the enrichment factor from the shipped bytes and
    # grades the reported number against THAT, so the reference rebuilds it
    # with the same expression _analyse uses, from the key's own exact counts,
    # rather than quoting the rounded copy stored in key["ef"].
    base = k / n if n else 0.0
    ef = (a_obs / n_hits) / base if (base > 0 and n_hits) else 0.0

    # "cannot_determine" is both a verdict and the abstention token, so F2 is
    # handled by the same line as the other two conditions.
    verdict = key["verdict"]
    abstaining = verdict == "cannot_determine"

    return {
        "n_known_actives": k,
        "n_actives_in_hits": a_obs,
        "ef_hits": ef,
        "enrichment_verdict": verdict,
        "explanation": _reference_explanation(key, ef),
        # Counts are facts of the file; the verdict rests on a null with 4000
        # replicates, and the refusal is the most secure call of the three.
        "conf_n_known_actives": 0.99,
        "conf_n_actives_in_hits": 0.99,
        "conf_ef_hits": 0.97,
        "conf_enrichment_verdict": 0.93 if abstaining else 0.85,
        "conf_explanation": 0.75 if key.get("reason") == "confounded" else 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
