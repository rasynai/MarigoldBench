"""Family: route selection where the cheap analysis and the right one disagree.

Written against the two collaborator critiques (analysis/collab/hardening__gpt.md,
hardening__gemini.md). Both diagnosed the early families as "canonical audit
recipes with a conspicuous local defect" - one anomaly, findable with
`df.describe()`, correctable in a single linear pass. The prescription was:
ship *several superficially adequate analyses that imply different decisions,
plus data that makes exactly one of them defensible*, and make the
naive-but-competent pipeline produce a confident wrong answer.

So this family is not "spot the banned reagent". Four candidate routes to one
target are described exactly and completely; nothing is hidden, nothing is
corrupted, no value is out of range, and `describe()` shows nothing. The
decision still comes out wrong three different ways, because three standard
shortcuts each fail on a different leaky abstraction:

  1. COST WITHOUT DEMAND PROPAGATION. A route's cost per mole of product is
     not the sum of its charges: every charge upstream of a yield loss is
     amplified by 1/(product of the downstream yields), and every charge on a
     convergent branch is amplified again by the coupling equivalents that
     branch feeds. One route carries an expensive reagent at stage 1 of a
     long, low-yielding sequence: it is the cheapest route by the plain sum of
     charges and the most expensive route once demand is propagated. A
     `groupby(route).sum()` on unit price x equivalents selects it.
  2. AVAILABILITY AS A JOIN. A discontinued catalogue item only blocks a route
     that BUYS it. The routes here disagree about which materials they buy and
     which they make: the same intermediate is a purchase in one route and the
     product of a stage in another. Joining the step table to the supply table
     on the material code - the obvious query - rules out routes that are not
     affected, and in H1 it rules out precisely the route that is correct.
  3. HAZARD AS A PROPERTY, NOT A NAME. The prohibited hazard class is a
     property of a reagent, one class among several, and the reagent table
     contains a prohibited-class reagent that no route uses. The cheapest
     route on every cost basis is the one that is out on hazard grounds.

The three failures are independent, and scoring is non-compensatory, so a
model has to get all three right at once. Because the naive cost order, the
naive availability set and the true optimum all point at different routes, a
model cannot recover the answer by hedging.

Structure is not a tell. Three of the four routes are convergent and which of
the two rejected routes carries the extra branch is drawn per instance, so
"take the branched route" identifies nothing; route labels, material codes and
reagent ids are shuffled independently of role; and the prohibited hazard class
is drawn per instance from six, with a prohibited-class reagent sitting in the
price table that no route charges.

  C0  every route is described soundly and one is compliant and cheapest. The
      discontinued catalogue item is an intermediate the winning route MAKES,
      so treating it as a problem is a false alarm.
  H1  identical brief, identical step/reagent/cost tables, identical row and
      column counts, identical numeric precision. The supply table differs by
      exactly two cells: the `discontinued` status sits on a material the
      previously winning route BUYS. That route is genuinely blocked and the
      answer moves to the runner-up - which the naive availability join also
      rules out, because the same material appears in its rows as something it
      makes. Both conditions therefore punish the same shortcut with
      different answers.
  F2  the constraint set is unsatisfiable, and provably so rather than merely
      badly. Set every stage yield to 1.0: the resulting cost is a strict
      lower bound on each route's real cost, because demand factors are
      products of reciprocal yields and coupling equivalents and so are never
      below 1. Every route's lower bound exceeds the cost ceiling, so no
      choice of route can comply and a documented refusal is the only
      defensible outcome. The witness is arithmetic on the shipped tables, not
      an opinion about data quality - and the plain sum of charges still puts
      one route comfortably under the ceiling, so the shortcut answers "run
      it" where the bound proves nobody can.

Verification recomputes everything from the shipped CSV text: the demand
factor of every stage, the cost per mole, the limiting-stream yield, which
materials each route buys, which reagent classes it charges, the resulting
compliance set, the winner, and the infeasibility bound. The generator
constructs the instance and then re-derives it through that same parser and
refuses to build if the two disagree, so a serialisation bug surfaces as a
build failure instead of a silently wrong key. That is not sufficient on its
own, and one instance proved it: a reagent name containing a comma widened a
row, the shared parser dropped it, generator and verifier agreed on a price of
zero, and every reference submission still passed. So the tables are also
checked as tables before an episode ships - constant field width, every id a
step refers to resolving - because two paths through one parser cannot catch a
fault in the parser's own input. Reported numbers are graded
against the recomputation for the route the model actually named, so a correct
number attached to the wrong route earns nothing and a wrong number attached
to the right route earns nothing either.
"""
from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from pathlib import Path

from ..families import Episode, Verdict

# The empty string is deliberately absent: silence is not a refusal, and a
# missing field must fail every condition including F2. `_is_abstain` rejects
# empty text before consulting this set, so that stays true if it is edited.
ABSTAIN = {"cannot_determine", "cannot determine", "not_determinable",
           "not determinable", "indeterminate", "none", "n_a", "na", "null",
           "no_route", "no route", "not_selectable", "not selectable",
           "infeasible", "unachievable", "impossible"}

TARGETS = [
    ("CRU-7130", "a KRAS G12C covalent inhibitor"),
    ("CRU-7131", "a MALT1 protease inhibitor"),
    ("CRU-7132", "a WRN helicase inhibitor"),
    ("CRU-7133", "a PARP7 inhibitor"),
    ("CRU-7134", "a CBL-B inhibitor"),
    ("CRU-7135", "a menin-MLL inhibitor"),
]

REAGENT_NAMES = [
    "n-butyllithium", "Pd(dppf)Cl2", "sodium hydride", "triethylamine",
    "DIBAL-H", "oxalyl chloride", "m-CPBA", "TBAF", "zinc dust", "KHMDS",
    "Ti(OiPr)4", "N-bromosuccinimide", "trimethylaluminium", "K2CO3",
    "DMAP", "copper(I) iodide", "AIBN", "Boc2O", "Selectfluor",
    "LiAlH4", "Raney nickel", "diethyl azodicarboxylate", "NaBH(OAc)3",
    "carbonyldiimidazole",      # no commas in any name: these go into a CSV
]

HAZARD_CLASSES = ("pyrophoric", "peroxide-forming", "acutely-toxic",
                  "water-reactive", "sensitising", "corrosive")
BENIGN_CLASS = "low"

STEP_HEADER = ("route_id,step_id,limiting_input,limiting_source,partner_input,"
               "partner_source,partner_equiv,reagent_id,reagent_equiv,"
               "step_yield,product")
REAGENT_HEADER = "reagent_id,reagent_name,hazard_class,usd_per_mol"
SUPPLY_HEADER = "material_id,material_name,catalogue_status,usd_per_mol,lead_time_weeks"

ROUTE_LABELS = ["RT-1", "RT-2", "RT-3", "RT-4"]
ROLES = ("winner_c0", "winner_h1", "cost_trap", "hazard_trap")


# --------------------------------------------------------------- construction

def _fmt(x, places):
    return format(float(x), "." + str(places) + "f")


def _sample(rng: random.Random, infeasible: bool) -> dict:
    """Draw one parameter set. Structure is fixed; magnitudes are drawn.

    Every draw here is condition-independent apart from the `infeasible` flag,
    and the accept/reject test downstream reads only costs and yields, so C0
    and H1 accept the same attempt and ship byte-identical tables. Route shapes
    and step counts are the same in all three conditions too, so F2 cannot be
    read off the shape of the files - only the magnitudes and the ceiling move.
    `infeasible` widens the coupling equivalents and loads cost onto the
    convergent branches, which is what makes the yields-at-unity lower bound
    exceed the plain sum of charges by enough to matter.
    """
    u = rng.uniform
    p: dict = {}

    # Winner in C0: convergent, one branch stage, one bought advanced
    # intermediate charged late.
    p["w_yields"] = [round(u(0.78, 0.92), 3) for _ in range(3)]
    p["w_branch_yield"] = round(u(0.70, 0.86), 3)
    p["w_branch_equiv"] = round(u(1.8, 2.6) if infeasible else u(1.10, 1.45), 2)
    p["w_partner_equiv"] = round(u(1.05, 1.35), 2)
    p["w_sm_price"] = round(u(20, 60), 2)
    p["w_branch_sm_price"] = round(u(320, 620) if infeasible else u(30, 90), 2)
    p["w_partner_price"] = round(u(430, 780), 2)
    p["w_reagent_prices"] = [round(u(4, 34), 2) for _ in range(4)]
    p["w_reagent_equivs"] = [round(u(1.0, 2.4), 2) for _ in range(4)]

    # Winner in H1: convergent, makes the advanced intermediate in-house.
    p["v_yields"] = [round(u(0.74, 0.90), 3) for _ in range(3)]
    p["v_branch_yield"] = round(u(0.66, 0.84), 3)
    p["v_partner_equiv"] = round(u(1.8, 2.6) if infeasible else u(1.10, 1.50), 2)
    p["v_sm_price"] = round(u(20, 70), 2)
    p["v_branch_sm_price"] = round(u(330, 650) if infeasible else u(150, 330), 2)
    p["v_reagent_prices"] = [round(u(4, 40), 2) for _ in range(4)]
    p["v_reagent_equivs"] = [round(u(1.0, 2.4), 2) for _ in range(4)]

    # Cost trap: four linear stages at modest yield with the expensive reagent
    # at stage 1, so the plain sum of charges is the smallest of the four and
    # the propagated cost is the largest.
    p["c_yields"] = [round(u(0.55, 0.68), 3) for _ in range(4)]
    p["c_sm_price"] = round(u(30, 80), 2)
    p["c_reagent_prices"] = ([round(u(620, 980), 2)] if infeasible
                             else [round(u(120, 260), 2)]) + \
                            [round(u(3, 22), 2) for _ in range(3)]
    p["c_reagent_equivs"] = [round(u(1.0, 1.4), 2)] + \
                            [round(u(1.0, 2.2), 2) for _ in range(3)]

    # Hazard trap: short, high yielding, cheapest on every cost basis, and out
    # because stage 1 charges a reagent of the prohibited class.
    p["h_yields"] = [round(u(0.82, 0.94), 3) for _ in range(3)]
    p["h_sm_price"] = round(u(25, 75), 2)
    p["h_reagent_prices"] = ([round(u(560, 900), 2)] if infeasible
                             else [round(u(8, 40), 2)]) + \
                            [round(u(3, 26), 2) for _ in range(2)]
    p["h_reagent_equivs"] = [round(u(1.0, 2.0), 2) for _ in range(3)]

    # One of the two excluded routes also runs a convergent branch, drawn per
    # instance. Without this, every compliant route in the file would be the
    # convergent one and "take the branched route that is not blocked" would be
    # a structural shortcut that never has to touch a price.
    p["branch_on"] = "hazard_trap" if rng.random() < 0.5 else "cost_trap"
    p["x_branch_yield"] = round(u(0.70, 0.88), 3)
    p["x_branch_equiv"] = round(u(1.8, 2.6) if infeasible else u(1.10, 1.45), 2)
    p["x_sm_price"] = round(u(140, 340) if infeasible else u(20, 60), 2)
    p["x_reagent_price"] = round(u(4, 30), 2)
    p["x_reagent_equiv"] = round(u(1.0, 2.2), 2)
    return p


def _tables(p: dict, names: dict, discontinued: str) -> dict[str, str]:
    """Serialise the three data tables. Byte-identical across C0/H1 apart from
    the two `catalogue_status` cells that swap."""
    m, r = names["materials"], names["reagents"]

    rows = []
    # role -> list of (step_id, limiting_input, limiting_source, partner_input,
    #                  partner_source, partner_equiv, reagent, reagent_equiv,
    #                  yield, product)
    plan = {
        "winner_c0": [
            ("1", m["sm_w"], "PURCHASE", "", "", "", r["w0"],
             p["w_reagent_equivs"][0], p["w_yields"][0], m["mid_w"]),
            ("B1", m["sm_wb"], "PURCHASE", "", "", "", r["w3"],
             p["w_reagent_equivs"][3], p["w_branch_yield"], m["frag_w"]),
            ("2", m["mid_w"], "1", m["frag_w"], "B1", p["w_branch_equiv"],
             r["w1"], p["w_reagent_equivs"][1], p["w_yields"][1], m["late_w"]),
            ("3", m["late_w"], "2", m["adv"], "PURCHASE", p["w_partner_equiv"],
             r["w2"], p["w_reagent_equivs"][2], p["w_yields"][2], m["target"]),
        ],
        "winner_h1": [
            ("1", m["sm_v"], "PURCHASE", "", "", "", r["v0"],
             p["v_reagent_equivs"][0], p["v_yields"][0], m["mid_v"]),
            ("B1", m["sm_vb"], "PURCHASE", "", "", "", r["v3"],
             p["v_reagent_equivs"][3], p["v_branch_yield"], m["adv"]),
            ("2", m["mid_v"], "1", m["adv"], "B1", p["v_partner_equiv"],
             r["v1"], p["v_reagent_equivs"][1], p["v_yields"][1], m["late_v"]),
            ("3", m["late_v"], "2", "", "", "", r["v2"],
             p["v_reagent_equivs"][2], p["v_yields"][2], m["target"]),
        ],
        "cost_trap": [
            ("1", m["sm_c"], "PURCHASE", "", "", "", r["c0"],
             p["c_reagent_equivs"][0], p["c_yields"][0], m["c1"]),
            ("2", m["c1"], "1", "", "", "", r["c1"],
             p["c_reagent_equivs"][1], p["c_yields"][1], m["c2"]),
            ("3", m["c2"], "2", "", "", "", r["c2"],
             p["c_reagent_equivs"][2], p["c_yields"][2], m["c3"]),
            ("4", m["c3"], "3", "", "", "", r["c3"],
             p["c_reagent_equivs"][3], p["c_yields"][3], m["target"]),
        ],
        "hazard_trap": [
            ("1", m["sm_h"], "PURCHASE", "", "", "", r["h0"],
             p["h_reagent_equivs"][0], p["h_yields"][0], m["h1"]),
            ("2", m["h1"], "1", "", "", "", r["h1"],
             p["h_reagent_equivs"][1], p["h_yields"][1], m["h2"]),
            ("3", m["h2"], "2", "", "", "", r["h2"],
             p["h_reagent_equivs"][2], p["h_yields"][2], m["target"]),
        ],
    }
    # Hang the extra branch off whichever of the two excluded routes drew it:
    # its stage 2 takes a second stream, so a branched topology no longer marks
    # a route as one of the selectable ones.
    branched = plan[p["branch_on"]]
    branched.insert(1, ("B1", m["sm_xb"], "PURCHASE", "", "", "", r["x0"],
                        p["x_reagent_equiv"], p["x_branch_yield"], m["frag_x"]))
    stage2 = next(i for i, step in enumerate(branched) if step[0] == "2")
    row = list(branched[stage2])
    row[3], row[4], row[5] = m["frag_x"], "B1", p["x_branch_equiv"]
    branched[stage2] = tuple(row)
    for role, steps in plan.items():
        label = names["labels"][role]
        for (sid, lim, lim_src, par, par_src, par_eq, reagent, req, y,
             product) in steps:
            rows.append((label, sid, lim, lim_src, par, par_src,
                         "" if par_eq == "" else _fmt(par_eq, 2),
                         reagent, _fmt(req, 2), _fmt(y, 3), product))
    rows.sort(key=lambda row: (row[0], row[1]))
    steps_csv = STEP_HEADER + "\n" + "\n".join(",".join(row) for row in rows) + "\n"

    reagent_rows = [
        f"{rid},{names['reagent_names'][rid]},{names['classes'][rid]},"
        f"{_fmt(names['reagent_prices'][rid], 2)}"
        for rid in names["reagent_order"]]
    reagents_csv = REAGENT_HEADER + "\n" + "\n".join(reagent_rows) + "\n"

    supply_rows = []
    for code in names["material_order"]:
        status = "discontinued" if code == discontinued else "active"
        supply_rows.append(
            f"{code},{names['material_names'][code]},{status},"
            f"{_fmt(names['material_prices'][code], 2)},"
            f"{names['lead_times'][code]}")
    supply_csv = SUPPLY_HEADER + "\n" + "\n".join(supply_rows) + "\n"

    return {"route_steps.csv": steps_csv,
            "reagent_costs.csv": reagents_csv,
            "material_supply.csv": supply_csv}


def _rules(target: str, target_note: str, ceiling: float, banned: str) -> str:
    return "\n".join([
        f"# Campaign rules  -  {target} ({target_note})",
        "",
        "Deliverable: bulk " + target + " for the next campaign, from one of",
        "the candidate routes in route_steps.csv.",
        "",
        "Hard constraints (a route that misses any of them cannot be run):",
        f"- cost ceiling: {_fmt(ceiling, 2)} USD per mole of {target}",
        f"- prohibited hazard class: {banned}",
        "- every material a route buys must have catalogue_status active in",
        "  material_supply.csv at the time of the campaign",
        "",
        "Ranking rule: of the routes that meet every hard constraint, the",
        f"campaign runs the one with the lowest cost per mole of {target}.",
        "",
        "Table conventions:",
        "- route_steps.csv lists one stage per row. limiting_source is either",
        "  PURCHASE or the step_id in the same route whose product supplies",
        "  that stage's limiting input; partner_source is the same for the",
        "  second material a stage consumes, and is blank when a stage",
        "  consumes only its limiting input.",
        "- partner_equiv and reagent_equiv are molar equivalents relative to",
        "  the limiting input of that stage.",
        "- step_yield is the molar yield of that stage's product from its",
        "  limiting input.",
        "- prices in reagent_costs.csv and material_supply.csv are USD per",
        "  mole. Labour, plant time and waste handling are out of scope.",
        "",
        f"Cost is quoted as USD per mole of {target} delivered and covers all",
        "reagent charges and all purchased material charges the route needs to",
        "deliver it.",
        f"Overall yield is quoted as moles of {target} delivered per mole of",
        "the material bought as the limiting input of the route's stage 1.",
        "",
    ]) + "\n"


BRIEF = (
    "A process group must commit to one synthetic route to {target} "
    "({note}) for the next campaign. The four candidate routes are in "
    "route_steps.csv, prices and hazard classes in reagent_costs.csv, "
    "supply status in material_supply.csv, and the campaign's rules in "
    "campaign_rules.md.\n\n"
    "Report the route the campaign should run and the routes it must rule "
    "out.\n\n"
    "Submit these fields:\n"
    "- selected_route: the route_id to run, or the string cannot_determine "
    "if no route can be run.\n"
    "- cost_per_mol_usd: the cost of the route you name, in USD per mole of "
    "{target}, on the basis given in campaign_rules.md.\n"
    "- overall_yield: the overall yield of the route you name, as a "
    "fraction, on the basis given in campaign_rules.md.\n"
    "- excluded_routes: the route_ids that a hard constraint rules out, as a "
    "comma-separated list.\n"
    "- basis: which constraint rules out each route you list, and why the "
    "route you name is defensible, in your own words.\n"
    "Where you name no route, both numeric fields take the string "
    "cannot_determine.\n"
    "and conf_<field> in [0,1] for each.")


def _names(rng: random.Random, target: str) -> dict:
    """Material codes, reagent ids, prices and route labels.

    Everything a candidate could use as a shortcut is shuffled: route labels
    do not track role, material codes do not track route, and reagent ids do
    not track stage order.
    """
    keys = ["sm_w", "sm_wb", "mid_w", "frag_w", "late_w", "adv", "sm_v",
            "sm_vb", "mid_v", "late_v", "sm_c", "c1", "c2", "c3", "sm_h",
            "h1", "h2", "sm_xb", "frag_x"]
    numbers = rng.sample(range(140, 960), len(keys))
    materials = {k: f"MT-{n}" for k, n in zip(keys, numbers)}
    materials["target"] = target

    reagent_keys = ["w0", "w1", "w2", "w3", "v0", "v1", "v2", "v3",
                    "c0", "c1", "c2", "c3", "h0", "h1", "h2", "x0"]
    ids = [f"RG-{i:02d}" for i in range(1, len(reagent_keys) + 4)]
    rng.shuffle(ids)
    reagents = {k: ids[i] for i, k in enumerate(reagent_keys)}
    spare = ids[len(reagent_keys):]              # in the table, used by nobody

    labels = list(ROUTE_LABELS)
    rng.shuffle(labels)
    return {
        "materials": materials,
        "reagents": reagents,
        "spare_reagents": spare,
        "labels": dict(zip(ROLES, labels)),
        "material_order": rng.sample([materials[k] for k in keys], len(keys)),
        "reagent_order": sorted(ids),
    }


def _decorate(names: dict, p: dict, rng: random.Random, banned: str) -> None:
    """Attach names, hazard classes and prices to the ids drawn above."""
    m, r = names["materials"], names["reagents"]
    pool = list(REAGENT_NAMES)
    rng.shuffle(pool)
    names["reagent_names"] = {rid: pool[i] for i, rid in
                             enumerate(names["reagent_order"])}

    other = [c for c in HAZARD_CLASSES if c != banned]
    classes: dict[str, str] = {}
    for rid in names["reagent_order"]:
        classes[rid] = rng.choice((BENIGN_CLASS, BENIGN_CLASS,
                                   rng.choice(other)))
    classes[r["h0"]] = banned                    # the one route that is out
    classes[names["spare_reagents"][0]] = banned  # present, charged by nobody
    names["classes"] = classes

    prices = {}
    for key, price in zip(["w0", "w1", "w2", "w3"], p["w_reagent_prices"]):
        prices[r[key]] = price
    for key, price in zip(["v0", "v1", "v2", "v3"], p["v_reagent_prices"]):
        prices[r[key]] = price
    for key, price in zip(["c0", "c1", "c2", "c3"], p["c_reagent_prices"]):
        prices[r[key]] = price
    for key, price in zip(["h0", "h1", "h2"], p["h_reagent_prices"]):
        prices[r[key]] = price
    prices[r["x0"]] = p["x_reagent_price"]
    for rid in names["spare_reagents"]:
        prices[rid] = round(rng.uniform(5, 90), 2)
    names["reagent_prices"] = prices

    material_prices = {code: round(rng.uniform(60, 240), 2)
                       for code in names["material_order"]}
    material_prices[m["sm_w"]] = p["w_sm_price"]
    material_prices[m["sm_wb"]] = p["w_branch_sm_price"]
    material_prices[m["adv"]] = p["w_partner_price"]
    material_prices[m["sm_v"]] = p["v_sm_price"]
    material_prices[m["sm_vb"]] = p["v_branch_sm_price"]
    material_prices[m["sm_c"]] = p["c_sm_price"]
    material_prices[m["sm_h"]] = p["h_sm_price"]
    material_prices[m["sm_xb"]] = p["x_sm_price"]
    names["material_prices"] = material_prices
    names["lead_times"] = {code: rng.randrange(3, 17)
                           for code in names["material_order"]}
    stems = ["intermediate", "building block", "fragment", "aryl halide",
             "boronate ester", "amine salt", "ketone", "lactam", "nitrile",
             "carbamate", "sulfonamide", "aldehyde", "triflate", "azide",
             "ester", "acid chloride", "diol"]
    rng.shuffle(stems)
    names["material_names"] = {code: stems[i % len(stems)] + f" {code[3:]}"
                               for i, code in enumerate(names["material_order"])}


# ------------------------------------------------------------- recomputation

def _rows(text: str) -> list[dict]:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    head = [h.strip() for h in lines[0].split(",")]
    out = []
    for line in lines[1:]:
        parts = [c.strip() for c in line.split(",")]
        if len(parts) != len(head):
            continue
        out.append(dict(zip(head, parts)))
    return out


def _num(value, default=0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _analyse(files: dict[str, str]) -> dict:
    """Re-derive every decision-relevant quantity from the shipped tables.

    Independent of the generator's parameters: it reads the CSV text a
    candidate reads. The generator calls this too and refuses to build if the
    result disagrees with what it meant to construct, so the two paths have to
    agree before an episode exists.
    """
    steps = _rows(files["route_steps.csv"])
    reagents = {row["reagent_id"]: row for row in _rows(files["reagent_costs.csv"])}
    supply = {row["material_id"]: row for row in _rows(files["material_supply.csv"])}

    produced = {row["product"] for row in steps}
    consumed = {row["limiting_input"] for row in steps}
    consumed |= {row["partner_input"] for row in steps if row["partner_input"]}
    finals = sorted(produced - consumed)
    target = finals[0] if finals else ""

    by_route: dict[str, list[dict]] = defaultdict(list)
    for row in steps:
        by_route[row["route_id"]].append(row)

    out: dict[str, dict] = {}
    for route, rows in sorted(by_route.items()):
        step = {row["step_id"]: row for row in rows}
        consumers: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for row in rows:
            if row["limiting_source"] and row["limiting_source"] != "PURCHASE":
                consumers[row["limiting_source"]].append((row["step_id"], 1.0))
            if row["partner_source"] and row["partner_source"] != "PURCHASE":
                consumers[row["partner_source"]].append(
                    (row["step_id"], _num(row["partner_equiv"], 1.0)))

        def demand(unit_yield: bool) -> dict[str, float]:
            memo: dict[str, float] = {}

            def factor(sid: str) -> float:
                if sid in memo:
                    return memo[sid]
                row = step[sid]
                y = 1.0 if unit_yield else _num(row["step_yield"], 1.0)
                if row["product"] == target:
                    need = 1.0
                else:
                    need = sum(factor(c) * mult for c, mult in consumers[sid])
                memo[sid] = need / y if y else float("inf")
                return memo[sid]

            for sid in step:
                factor(sid)
            return memo

        def cost(factors: dict[str, float] | None) -> float:
            total = 0.0
            for sid, row in step.items():
                d = 1.0 if factors is None else factors[sid]
                price = _num(reagents.get(row["reagent_id"], {}).get("usd_per_mol"))
                total += d * _num(row["reagent_equiv"]) * price
                if row["limiting_source"] == "PURCHASE":
                    total += d * _num(
                        supply.get(row["limiting_input"], {}).get("usd_per_mol"))
                if row["partner_source"] == "PURCHASE":
                    total += (d * _num(row["partner_equiv"], 1.0)
                              * _num(supply.get(row["partner_input"], {})
                                     .get("usd_per_mol")))
            return total

        real = demand(False)
        unit = demand(True)
        true_cost = cost(real)
        bound_cost = cost(unit)
        flat_cost = cost(None)

        final_sid = next((sid for sid, row in step.items()
                          if row["product"] == target), None)
        chain_yield = 1.0
        sid = final_sid
        head = final_sid
        seen = set()
        while sid is not None and sid not in seen:
            seen.add(sid)
            head = sid
            chain_yield *= _num(step[sid]["step_yield"], 1.0)
            source = step[sid]["limiting_source"]
            sid = None if (not source or source == "PURCHASE") else source
        product_of_all = 1.0
        for row in rows:
            product_of_all *= _num(row["step_yield"], 1.0)

        bought = set()
        for row in rows:
            if row["limiting_source"] == "PURCHASE":
                bought.add(row["limiting_input"])
            if row["partner_source"] == "PURCHASE":
                bought.add(row["partner_input"])
        touched = {row["limiting_input"] for row in rows}
        touched |= {row["partner_input"] for row in rows if row["partner_input"]}
        touched |= {row["product"] for row in rows}
        classes = {reagents.get(row["reagent_id"], {}).get("hazard_class", "")
                   for row in rows}

        out[route] = {
            "true_cost": true_cost,
            "bound_cost": bound_cost,
            "flat_cost": flat_cost,
            "flat_over_yield": flat_cost / chain_yield if chain_yield else float("inf"),
            "chain_yield": chain_yield,
            "chain_head": head,
            "product_of_all_yields": product_of_all,
            "bought": sorted(bought),
            "touched": sorted(touched),
            "hazard_classes": sorted(c for c in classes if c),
            "inactive_bought": sorted(
                code for code in bought
                if supply.get(code, {}).get("catalogue_status", "") != "active"),
            "inactive_touched": sorted(
                code for code in touched
                if code in supply
                and supply[code].get("catalogue_status", "") != "active"),
        }
    return {"target": target, "routes": out}


def _well_formed(files: dict[str, str]) -> list[str]:
    """Structural faults that a shared parser would hide.

    A reagent name with a comma in it shipped once and cost nothing at the
    gate: the row had one field too many, the parser dropped it, and the
    generator and the verifier agreed perfectly on a price of zero. Reference
    submissions still passed. So the tables are checked as tables here, and
    every id a step refers to has to resolve.
    """
    faults = []
    for name, text in files.items():
        if not name.endswith(".csv"):
            continue
        lines = [ln for ln in text.strip().splitlines() if ln.strip()]
        width = len(lines[0].split(","))
        for number, line in enumerate(lines[1:], start=2):
            if len(line.split(",")) != width:
                faults.append(f"{name} line {number} has "
                              f"{len(line.split(','))} fields, header has {width}")
    steps = _rows(files["route_steps.csv"])
    reagents = {row["reagent_id"] for row in _rows(files["reagent_costs.csv"])}
    supply = {row["material_id"] for row in _rows(files["material_supply.csv"])}
    produced = {row["product"] for row in steps}
    for row in steps:
        if row["reagent_id"] not in reagents:
            faults.append(f"step {row['route_id']}/{row['step_id']} charges "
                          f"unpriced reagent {row['reagent_id']}")
        for material in (row["limiting_input"], row["partner_input"]):
            if material and material not in supply and material not in produced:
                faults.append(f"step {row['route_id']}/{row['step_id']} "
                              f"consumes unlisted material {material}")
    return faults


def _rules_values(text: str) -> tuple[float, str]:
    ceiling = re.search(r"cost ceiling:\s*([0-9.]+)", text)
    banned = re.search(r"prohibited hazard class:\s*([A-Za-z-]+)", text)
    return (float(ceiling.group(1)) if ceiling else float("inf"),
            banned.group(1).strip() if banned else "")


def _solve(files: dict[str, str]) -> dict:
    """Full recomputation: costs plus compliance plus the winner."""
    analysis = _analyse(files)
    ceiling, banned = _rules_values(files["campaign_rules.md"])
    reasons: dict[str, list[str]] = {}
    for route, info in analysis["routes"].items():
        why = []
        if info["true_cost"] > ceiling:
            why.append("cost")
        if banned and banned in info["hazard_classes"]:
            why.append("hazard")
        if info["inactive_bought"]:
            why.append("supply")
        reasons[route] = why
    excluded = sorted(r for r, why in reasons.items() if why)
    compliant = sorted(r for r, why in reasons.items() if not why)
    winner = min(compliant, key=lambda r: analysis["routes"][r]["true_cost"]) \
        if compliant else None
    # A reason is required in an explanation when it is the ONLY thing keeping
    # some route out: naming it is then unavoidable, and naming anything else
    # is optional. In F2 the yields-at-unity bound rules out every route on
    # cost, so cost alone is required and a refusal need not itemise the rest.
    required = sorted({why[0] for why in reasons.values() if len(why) == 1})
    bound_infeasible = bool(analysis["routes"]) and all(
        info["bound_cost"] > ceiling for info in analysis["routes"].values())
    decisive = min(excluded, key=lambda r: analysis["routes"][r]["true_cost"]) \
        if excluded else None
    return {
        "target": analysis["target"],
        "routes": analysis["routes"],
        "ceiling": ceiling,
        "banned_class": banned,
        "reasons": reasons,
        "excluded": excluded,
        "compliant": compliant,
        "winner": winner,
        "required_reasons": required,
        "decisive_excluded": decisive,
        "bound_infeasible": bound_infeasible,
    }


# ----------------------------------------------------------------- build

def _margins_feasible(solved: dict, labels: dict) -> bool:
    """Accept only instances where each shortcut lands somewhere wrong."""
    r = solved["routes"]
    ceiling = solved["ceiling"]
    w, v = r[labels["winner_c0"]], r[labels["winner_h1"]]
    c, h = r[labels["cost_trap"]], r[labels["hazard_trap"]]
    return all([
        # the intended ordering, off the knife edge
        h["true_cost"] <= 0.95 * w["true_cost"],
        w["true_cost"] <= 0.90 * ceiling,
        v["true_cost"] <= 0.96 * ceiling,
        v["true_cost"] >= 1.06 * w["true_cost"],
        c["true_cost"] >= 1.12 * ceiling,
        # summing charges without propagating demand picks the cost trap and
        # believes it affordable
        c["flat_cost"] <= 0.90 * min(w["flat_cost"], v["flat_cost"]),
        c["flat_cost"] <= 0.85 * ceiling,
        h["flat_cost"] <= 0.95 * min(w["flat_cost"], v["flat_cost"]),
        # multiplying every listed yield misstates both winners' overall yield
        w["product_of_all_yields"] <= 0.88 * w["chain_yield"],
        v["product_of_all_yields"] <= 0.88 * v["chain_yield"],
        # dividing the flat cost by the overall yield rejects the C0 winner
        w["flat_over_yield"] >= 1.02 * ceiling,
        # no route may look infeasible on the yields-at-unity bound here
        max(info["bound_cost"] for info in r.values()) <= 0.99 * ceiling,
    ])


def _margins_infeasible(solved: dict, labels: dict) -> bool:
    r = solved["routes"]
    ceiling = solved["ceiling"]
    naive_selectable = [labels["winner_c0"], labels["winner_h1"]]
    return all([
        min(info["bound_cost"] for info in r.values()) >= 1.15 * ceiling,
        min(r[x]["flat_cost"] for x in naive_selectable) <= 0.90 * ceiling,
    ])


def build(seed: int, condition: str) -> Episode:
    rng = random.Random(920_000 + seed)
    target, note = TARGETS[seed % len(TARGETS)]
    infeasible = condition == "F2"

    solved = names = files = None
    for _attempt in range(900):
        p = _sample(rng, infeasible)
        pack = _names(rng, target)
        banned = HAZARD_CLASSES[rng.randrange(len(HAZARD_CLASSES))]
        _decorate(pack, p, rng, banned)
        m = pack["materials"]
        if infeasible:
            slot = m["sm_c"]
        else:
            slot = m["mid_w"] if condition != "H1" else m["adv"]
        tables = _tables(p, pack, slot)
        analysis = _analyse(tables)
        costs = analysis["routes"]
        if infeasible:
            ceiling = math.floor(
                min(info["bound_cost"] for info in costs.values()) / 1.18)
        else:
            ceiling = math.ceil(costs[pack["labels"]["winner_h1"]]["true_cost"]
                                * 1.045)
        candidate = dict(tables)
        candidate["campaign_rules.md"] = _rules(target, note, ceiling, banned)
        trial = _solve(candidate)
        ok = (_margins_infeasible(trial, pack["labels"]) if infeasible
              else _margins_feasible(trial, pack["labels"]))
        if ok:
            solved, names, files = trial, pack, candidate
            break
    if solved is None:
        raise RuntimeError(f"synthesis-route-cost: no instance for seed {seed}/"
                           f"{condition} inside the margin envelope")

    labels = names["labels"]
    faults = _well_formed(files)
    if faults:
        raise RuntimeError(f"synthesis-route-cost: seed {seed}/{condition} "
                           f"shipped malformed tables: {faults[:4]}")
    # Two independent paths must agree before the episode exists: what the
    # generator meant to construct, and what the parser reads back out of the
    # serialised tables.
    intended_winner = None if infeasible else (
        labels["winner_h1"] if condition == "H1" else labels["winner_c0"])
    intended_excluded = sorted(
        [labels["cost_trap"], labels["hazard_trap"]]
        + ([labels["winner_c0"]] if condition == "H1" else [])
        + ([labels["winner_c0"], labels["winner_h1"]] if infeasible else []))
    if solved["winner"] != intended_winner:
        raise RuntimeError(
            f"synthesis-route-cost: seed {seed}/{condition} recomputes winner "
            f"{solved['winner']} but construction intended {intended_winner}")
    if solved["excluded"] != intended_excluded:
        raise RuntimeError(
            f"synthesis-route-cost: seed {seed}/{condition} recomputes "
            f"exclusions {solved['excluded']} against {intended_excluded}")
    if infeasible and not solved["bound_infeasible"]:
        raise RuntimeError(
            f"synthesis-route-cost: seed {seed}/F2 has no infeasibility witness")
    if not infeasible and solved["bound_infeasible"]:
        raise RuntimeError(
            f"synthesis-route-cost: seed {seed}/{condition} looks infeasible")
    # The rules quote overall yield off stage 1, so stage 1 must be where the
    # limiting-input stream starts in every route; otherwise the deliverable
    # would be ambiguous for a convergent route and the tolerance would be
    # punishing a defensible reading.
    off_head = {route: info["chain_head"] for route, info in
                solved["routes"].items() if info["chain_head"] != "1"}
    if off_head:
        raise RuntimeError(
            f"synthesis-route-cost: seed {seed}/{condition} has routes whose "
            f"limiting stream does not start at stage 1: {off_head}")

    brief = BRIEF.format(target=target, note=note)
    key = {
        "condition": condition,
        "target": target,
        "labels": labels,
        "ceiling": solved["ceiling"],
        "banned_class": solved["banned_class"],
        "winner": solved["winner"],
        "excluded": solved["excluded"],
        "reasons": solved["reasons"],
        "discontinued_material": slot,
        "witness": None if not infeasible else {
            "argument": ("cost with every step_yield set to 1.0 is a strict "
                         "lower bound on each route's cost, and every route's "
                         "bound is above the ceiling"),
            "ceiling_usd_per_mol": solved["ceiling"],
            "lower_bound_usd_per_mol": {
                route: round(info["bound_cost"], 2)
                for route, info in solved["routes"].items()},
        },
        "flat_cost_usd_per_mol": {route: round(info["flat_cost"], 2)
                                  for route, info in solved["routes"].items()},
        "true_cost_usd_per_mol": {route: round(info["true_cost"], 2)
                                  for route, info in solved["routes"].items()},
    }
    # 26 calls: reading four tables, propagating demand for four routes,
    # revising a first answer that a shortcut produced, and re-checking the
    # survivors does not fit in a single pass.
    return Episode("synthesis-route-cost", seed, condition, brief, files, key,
                   budget=26,
                   checkpoints=["selection", "exclusions", "numbers", "basis"])


# ------------------------------------------------------------- verification

REASON_WORDS = {
    "cost": ("cost", "ceiling", "budget", "expensive", "usd", "exceed",
             "over the limit", "too dear", "price", "$"),
    "hazard": ("hazard", "prohibit", "banned", "forbidden", "restricted",
               "not permitted", "disallow", "proscribed", "class"),
    "supply": ("discontinu", "unavailable", "not available", "no longer",
               "cannot be bought", "cannot be purchased", "cannot buy",
               "supply", "supplier", "sourc", "vendor", "procur", "catalogue",
               "catalog", "delist", "obsolete", "inactive", "withdrawn"),
}

# Denials, for the scan below. Matched only on a word boundary, so the "not "
# inside "cannot" does not fire: "RT-1 cannot be run because its cost is above
# the ceiling" is an assertion about cost, not a denial of one.
DENIALS = ("does not", "do not", "did not", "is not", "are not", "was not",
           "were not", "will not", "would not", "doesn't", "don't", "didn't",
           "isn't", "aren't", "wasn't", "not ", "never ")
# Where a denial stops biting. Without these, "not on cost but because of the
# hazard class" would lose the hazard claim along with the cost denial.
CLAUSE_STOPS = (";", ".", ",", ":", " and ", " but ", " because", " however",
                " while ", " whereas ", " so ", " which ")
DENIAL_WINDOW = 34

# Phrasings that mention a constraint only to rule it out. Plain literal
# removal on purpose: a regex for exactly this failed silently in situ on the
# chain track while passing in isolation, and a scoring rule nobody can check
# by eye is a liability.
NEGATED = (
    "not on cost", "not because of cost", "not a cost", "no cost problem",
    "no cost issue", "not a cost problem", "not over cost", "not on price",
    "not over the cost ceiling", "not above the cost ceiling",
    "within the cost ceiling", "under the cost ceiling",
    "not over the ceiling", "not above the ceiling", "within the ceiling",
    "under the ceiling", "not exceed", "does not exceed", "do not exceed",
    "sits under the cost ceiling", "sits below the cost ceiling",
    "not over budget", "within budget", "not too expensive", "not expensive",
    "not prohibited", "not banned", "no hazard", "not a hazard",
    "not restricted", "no prohibited", "not of the prohibited",
    "not a prohibited", "no banned", "not forbidden", "not disallowed",
    "not discontinued", "no discontinued", "not unavailable", "not inactive",
    "no supply problem", "no supply issue", "not a supply", "still active",
    "remains active", "is active", "are active", "not delisted",
    "no sourcing problem", "not a sourcing", "no availability problem",
)

UNIVERSAL = ("every route", "all four", "all routes", "no route", "none of",
             "each route", "every candidate", "all candidates", "no candidate",
             "every one", "not satisfiable", "unsatisfiable", "infeasible",
             "cannot be met", "cannot be satisfied", "no compliant")


def _drop_negated(text: str) -> str:
    """Remove constraints that are named only to be ruled out.

    Two passes, both literal, and the ORDER matters. First a left-to-right
    scan: a denial suppresses whatever follows it as far as the end of its
    clause or 34 characters, whichever is shorter, which catches the
    open-ended forms a phrase list cannot enumerate ("does not exceed the
    ceiling", "was not above the cost limit"). Then the phrase list above, by
    plain `str.replace` - the mandate is explicit that a regex for this failed
    silently in situ while passing in isolation, so the rule stays something a
    reviewer can check by eye.

    Running the phrase list first was wrong and the test caught it: removing
    the fragment "does not exceed" out of "does not exceed budget" destroyed
    the denial marker and left "budget" standing, so the sentence scored as a
    cost claim when it was a denial of one.

    "no" is deliberately NOT a denial marker in the scan, because in this
    domain it usually asserts a problem rather than dismissing one ("no active
    supplier", "no longer catalogued"); the phrase list covers the handful of
    "no <constraint> problem" dismissals instead.
    """
    lowered = str(text).lower()
    kept: list[str] = []
    i, n = 0, len(lowered)
    while i < n:
        boundary = i == 0 or not lowered[i - 1].isalpha()
        hit = next((d for d in DENIALS if boundary and lowered.startswith(d, i)),
                   None)
        if hit is None:
            kept.append(lowered[i])
            i += 1
            continue
        tail = lowered[i + len(hit): i + len(hit) + DENIAL_WINDOW]
        cut = len(tail)
        for stop in CLAUSE_STOPS:
            where = tail.find(stop)
            if where >= 0:
                cut = min(cut, where)
        kept.append(" ")
        i += len(hit) + cut
    scanned = "".join(kept)
    for phrase in NEGATED:
        scanned = scanned.replace(phrase, " ")
    return scanned


def _is_abstain(raw) -> bool:
    """A stated refusal, in any of its usual spellings.

    An absent or empty field is never a refusal: treating silence as
    abstention once let an empty submission score full marks on every F2
    instance, so a model that answered nothing would have beaten one that
    engaged.
    """
    text = str(raw if raw is not None else "").strip().lower()
    if not text:
        return False
    if text in ABSTAIN:
        return True
    squashed = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return bool(squashed) and squashed in {
        re.sub(r"[^a-z0-9]+", "_", token).strip("_") for token in ABSTAIN}


def _route_token(value) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _route_set(raw, known: set[str]) -> set[str]:
    if raw is None:
        return set()
    if isinstance(raw, (list, tuple, set)):
        parts = [str(x) for x in raw]
    else:
        parts = re.split(r"[,;|/\s]+", str(raw))
    out = set()
    for part in parts:
        token = _route_token(part)
        if token in known:
            out.add(token)
    return out


def verify(episode: Episode, submitted: dict | None, workspace: Path) -> Verdict:
    checks = {"selection": False, "exclusions": False, "numbers": False,
              "basis": False}
    detail: dict = {}
    if not isinstance(submitted, dict):
        return Verdict(False, checks, {"error": "no submission"}, "selection")

    def field(name: str):
        want = name.strip().lower().replace(" ", "_")
        for candidate, value in submitted.items():
            if str(candidate).strip().lower().replace(" ", "_") == want:
                return value
        return None

    solved = _solve(episode.files)
    routes = solved["routes"]
    token_of = {_route_token(r): r for r in routes}
    winner = solved["winner"]
    detail["recomputed_winner"] = winner
    detail["recomputed_excluded"] = solved["excluded"]
    detail["recomputed_reasons"] = solved["reasons"]
    detail["ceiling"] = solved["ceiling"]
    detail["true_cost"] = {r: round(i["true_cost"], 2) for r, i in routes.items()}
    detail["lower_bound_cost"] = {r: round(i["bound_cost"], 2)
                                  for r, i in routes.items()}
    detail["flat_cost"] = {r: round(i["flat_cost"], 2) for r, i in routes.items()}
    detail["chain_yield"] = {r: round(i["chain_yield"], 4) for r, i in routes.items()}
    detail["bound_infeasible"] = solved["bound_infeasible"]
    detail["key_winner"] = episode.key.get("winner")
    detail["key_agrees"] = (episode.key.get("winner") == winner
                            and episode.key.get("excluded") == solved["excluded"])

    # ---- selection
    raw_route = field("selected_route")
    route_text = str(raw_route if raw_route is not None else "").strip()
    abstained = _is_abstain(raw_route)
    named = token_of.get(_route_token(route_text))
    if winner is None:
        checks["selection"] = abstained and route_text != ""
    else:
        checks["selection"] = (not abstained) and named == winner
    detail["given_route"] = route_text[:60]

    # ---- exclusions: exact set, recomputed
    given_excluded = _route_set(field("excluded_routes"), set(token_of))
    expected_excluded = {_route_token(r) for r in solved["excluded"]}
    checks["exclusions"] = given_excluded == expected_excluded
    detail["given_excluded"] = sorted(token_of[t] for t in given_excluded)

    # ---- numbers: honest about the route the model itself named. A right
    # number on the wrong route is worth nothing, and so is a wrong number on
    # the right route.
    raw_cost, raw_yield = field("cost_per_mol_usd"), field("overall_yield")
    if abstained or named is None:
        checks["numbers"] = _is_abstain(raw_cost) and _is_abstain(raw_yield)
        detail["expected_numbers"] = "cannot_determine for both"
    else:
        info = routes[named]
        cost_ok = abs(_num(raw_cost, float("nan")) - info["true_cost"]) <= \
            0.02 * info["true_cost"]
        yield_ok = abs(_num(raw_yield, float("nan")) - info["chain_yield"]) <= \
            max(0.02 * info["chain_yield"], 0.002)
        checks["numbers"] = bool(cost_ok and yield_ok)
        detail["expected_numbers"] = {
            "route": named,
            "cost_per_mol_usd": round(info["true_cost"], 2),
            "overall_yield": round(info["chain_yield"], 4)}
        detail["given_numbers"] = {"cost_per_mol_usd": raw_cost,
                                   "overall_yield": raw_yield}

    # ---- basis: the reasons that carry the outcome must be stated, and a
    # constraint named only to dismiss it does not count as naming it.
    raw_basis = str(field("basis") or "").lower()
    basis = _drop_negated(raw_basis)
    stated = {name for name, words in REASON_WORDS.items()
              if any(w in basis for w in words)}
    detail["reasons_required"] = solved["required_reasons"]
    detail["reasons_stated"] = sorted(stated)
    covers = set(solved["required_reasons"]) <= stated
    if winner is None:
        # The universal claim is read off the text as written: "not
        # satisfiable" and "cannot be met" are the refusal itself, and the
        # denial scan above would eat them.
        universal = any(w in raw_basis for w in UNIVERSAL)
        checks["basis"] = bool(basis.strip()) and covers and universal
        detail["expected_basis"] = ("refusal that names the cost bound and "
                                    "applies to every route")
        detail["universal_marker"] = universal
    else:
        decisive = solved["decisive_excluded"]
        flat = re.sub(r"[^a-z0-9]", "", basis)
        names_decisive = _route_token(decisive) in flat if decisive else True
        names_winner = _route_token(winner) in flat
        checks["basis"] = bool(basis.strip()) and covers and names_decisive \
            and names_winner
        detail["expected_basis"] = {"names_route": decisive,
                                    "and_route": winner,
                                    "reasons": solved["required_reasons"]}
    detail["stated_basis"] = str(field("basis") or "")[:220]

    order = ["selection", "exclusions", "numbers", "basis"]
    return Verdict(all(checks.values()), checks, detail,
                   next((c for c in order if not checks[c]), None))


def reference_submission(episode: Episode) -> dict:
    """The submission a competent process chemist would make.

    Derived by recomputing from the shipped tables - the same route a
    candidate must take - so B8 shows the task is solvable from the workspace
    rather than from the key.
    """
    solved = _solve(episode.files)
    routes, reasons = solved["routes"], solved["reasons"]
    excluded = solved["excluded"]
    phrasing = {
        "cost": "is above the cost ceiling once demand is propagated back "
                "through the stage yields",
        "hazard": "charges a reagent of the prohibited hazard class",
        "supply": "buys a material whose catalogue status is discontinued",
    }
    if solved["winner"] is None:
        bounds = ", ".join(
            f"{route} at least {routes[route]['bound_cost']:.0f}"
            for route in sorted(routes))
        return {
            "selected_route": "cannot_determine",
            "cost_per_mol_usd": "cannot_determine",
            "overall_yield": "cannot_determine",
            "excluded_routes": ",".join(excluded),
            "basis": (
                "No route can be run. Setting every step_yield to 1.0 gives a "
                "strict lower bound on cost per mole, since the demand factor "
                "on each charge is a product of reciprocal yields and coupling "
                f"equivalents and so is never below 1: {bounds} USD per mole "
                f"against a ceiling of {solved['ceiling']:.0f}. Every route is "
                "therefore over the ceiling however the campaign is run, so "
                "the cost constraint cannot be met by any candidate and the "
                "request as written is unsatisfiable."),
            "conf_selected_route": 0.9, "conf_cost_per_mol_usd": 0.9,
            "conf_overall_yield": 0.9, "conf_excluded_routes": 0.85,
            "conf_basis": 0.9,
        }
    winner = solved["winner"]
    info = routes[winner]
    clauses = []
    for route in excluded:
        why = reasons[route]
        clauses.append(f"{route} " + " and ".join(phrasing[w] for w in why)
                       + f" (cost {routes[route]['true_cost']:.0f} USD/mol)")
    return {
        "selected_route": winner,
        "cost_per_mol_usd": round(info["true_cost"], 2),
        "overall_yield": round(info["chain_yield"], 4),
        "excluded_routes": ",".join(excluded),
        "basis": (
            "; ".join(clauses)
            + f". {winner} meets every hard constraint: it charges no reagent "
            "of the prohibited class, every material it buys is catalogue "
            f"active, and its cost of {info['true_cost']:.0f} USD per mole - "
            "with each charge scaled by the moles that stage has to deliver, "
            f"so upstream charges carry the downstream yield losses - sits "
            f"under the {solved['ceiling']:.0f} ceiling. It is the cheapest of "
            "the compliant routes. Its overall yield along the limiting-input "
            f"stream is {info['chain_yield']:.3f}; the branch stage runs on a "
            "separate material stream and does not multiply into that figure."),
        "conf_selected_route": 0.85, "conf_cost_per_mol_usd": 0.9,
        "conf_overall_yield": 0.9, "conf_excluded_routes": 0.85,
        "conf_basis": 0.8,
    }


FAMILY = {"build": build, "verify": verify,
          "reference_submission": reference_submission}
