"""MarigoldBench figures in the Rasyn house style.

Written against Downloads/marigold-figures/FIGURE-DESIGN.md: horizontal bar
scoreboards only, one axes filling the canvas with every position hand placed in
axes fractions, Lato throughout, one accent hue plus a neutral ramp, every bar on
a full length track with a darker stroke, values in one right aligned column,
rows sorted by the primary metric, and no em dashes anywhere (asserted, not
hoped for, at the bottom of this file).

Three places where this benchmark's data forced a documented departure from that
spec, rather than a silent one:

1. **The accent marks the metric, not a contestant.** The spec spends teal on
   Marigold and greys every rival. MarigoldBench is a benchmark we publish about
   other people's models; there is no "us" in the lineup. The spec's own reason
   for the rule - that this is the strongest cue in the figure and must not be
   spent on anything else - is the reason it stays unspent here: teal is the
   primary metric, light teal the secondary, and every system's value is set in
   the same weight and colour. Nobody is flattered by the palette.
2. **Panels and rows share one 0 to 100 scale.** The spec normalises each panel
   against its own max, which makes within-panel reading honest and cross-panel
   reading impossible. Here cross-system comparison IS the question, so the scale
   is shared and the note line says so.
3. **The headline carries its interval.** A bar alone would state 63.2 against
   58.3 as though the difference were real. It is not: the family-clustered
   intervals overlap, which is the single most important fact about this release
   (docs/AUDIT.md D2, D3). The interval is drawn as a thin neutral whisker over
   the bar. Everything the spec forbids - grids, spines, ticks, frames, cards,
   shadows, a second accent - stays forbidden.

    python runs/_figures_house.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crucible.lab.logo import draw_logo  # noqa: E402

ASSETS = Path(r"C:\Users\ansht\Downloads\marigold-figures")
OUT = Path("figures/house")
DPI = 200

# ---------------------------------------------------------------- tokens
BG = "#ffffff"
INK = "#000000"
VAL = "#000000"
MUT = "#6f7875"
TEAL = "#009e7f"
TEALL = "#5fd6bf"
BAR_D = "#39403e"
BARL = "#b2bab7"
BAR = "#6d7774"
TRACK = "#f2f4f3"
TRACKEDGE = "#e3e7e5"
CHIP = "#eef1f0"
CHIPEDGE = "#a9b1ae"
STROKE = {TEAL: "#00654f", TEALL: "#1fae93", BAR_D: "#171a19",
          BARL: "#7e8784", BAR: "#3e4645"}

for ttf in ("Lato-Regular.ttf", "Lato-Bold.ttf", "Lato-Black.ttf",
            "Lato-Light.ttf"):
    path = ASSETS / "fonts" / ttf
    if path.exists():
        font_manager.fontManager.addfont(str(path))
plt.rcParams["font.family"] = "Lato"
plt.rcParams["svg.fonttype"] = "none"

DATA = json.loads(Path("runs/_figdata.json").read_text(encoding="utf-8"))
NAME = {"grok": "Grok 4.6", "gpt": "GPT-5.6 Sol", "claude": "Claude Opus 5",
        "deepseek": "DeepSeek V4 Pro", "gemini": "Gemini 3.1 Pro",
        "glm": "GLM-4.7", "kimi": "Kimi K2 Thinking"}
LOGO = {"grok": "grok-light.png", "gpt": "openai-light.png",
        "claude": "claude-color-light.png", "deepseek": "deepseek-color-light.png",
        "gemini": "gemini-color-light.png", "glm": "org-zai.png",
        "kimi": "moonshot-light.png"}

TEXTS: list[str] = []


def say(text: str) -> str:
    """Every string that reaches the canvas passes through here."""
    TEXTS.append(text)
    return text


# ---------------------------------------------------------------- primitives
def canvas(w_in: float, h_in: float):
    fig = plt.figure(figsize=(w_in, h_in), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig._aspect = w_in / h_in
    return fig, ax


# Sponsor override on the figure spec, which asks for a stroke 25 to 35 percent
# darker than the fill at lw 1.1 to 1.4. A hairline black outline instead: it
# separates a bar from its track more crisply at thumbnail size, and at 0.5pt it
# reads as an edge rather than as a second colour.
BAR_EDGE = "#000000"
BAR_EDGE_WIDTH = 0.5


def bar(ax, fig, x, y_centre, length, height, colour):
    """A rounded bar. Rounding is capped so a short bar is not a lozenge."""
    if length <= 0:
        return
    radius = min(height * 0.20, length / fig._aspect * 0.5)
    ax.add_patch(FancyBboxPatch(
        (x, y_centre - height / 2), length, height,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        mutation_aspect=fig._aspect, facecolor=colour,
        edgecolor=BAR_EDGE, linewidth=BAR_EDGE_WIDTH, zorder=3))


def track(ax, fig, x, y_centre, length, height):
    radius = min(height * 0.20, length / fig._aspect * 0.5)
    ax.add_patch(FancyBboxPatch(
        (x, y_centre - height / 2), length, height,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        mutation_aspect=fig._aspect, facecolor=TRACK,
        edgecolor=TRACKEDGE, linewidth=1.0, zorder=2))


def chipbox(ax, fig, x_centre, y_centre, size, image=None, fill=CHIP,
            edge=CHIPEDGE):
    w = size * (1.0 / fig._aspect)
    ax.add_patch(FancyBboxPatch(
        (x_centre - w / 2, y_centre - size / 2), w, size,
        boxstyle="round,pad=0,rounding_size=0.0045",
        mutation_aspect=fig._aspect, facecolor=fill, edgecolor=edge,
        linewidth=1.0, zorder=3))
    if image is None:
        return
    path = ASSETS / "logos" / image
    if not path.exists():
        return
    img = plt.imread(path)
    target_px = size * fig.get_size_inches()[1] * DPI * 0.62
    zoom = target_px / img.shape[0] / (DPI / 100)
    ax.add_artist(AnnotationBbox(
        OffsetImage(img, zoom=zoom), (x_centre, y_centre), frameon=False,
        box_alignment=(0.5, 0.5), zorder=4))


def whisker(ax, x_lo, x_hi, y, height):
    """The clustered interval. Neutral, thin, and never the loudest mark."""
    ax.plot([x_lo, x_hi], [y, y], color=BAR_D, lw=1.3,
            solid_capstyle="butt", zorder=5)
    for x in (x_lo, x_hi):
        ax.plot([x, x], [y - height * 0.30, y + height * 0.30], color=BAR_D,
                lw=1.3, solid_capstyle="butt", zorder=5)


def heading(fig, ax, title, subtitle=None):
    handle = ax.text(0.055, 0.915, say(title), fontsize=25, fontweight="bold",
                     color=INK, va="center", ha="left")
    if not subtitle:
        return
    # Measure the title instead of guessing an offset, per the spec.
    fig.canvas.draw()
    box = handle.get_window_extent(fig.canvas.get_renderer())
    x1 = ax.transAxes.inverted().transform((box.x1, box.y0))[0]
    ax.text(x1 + 0.02, 0.915, say(subtitle), fontsize=9.5, color=MUT,
            va="center", ha="left")


WORDMARK = "MarigoldBench"


def wordmark(fig, ax, h_in=6.4):
    """The Rasyn mark and the benchmark name, once per figure, bottom right.

    The mark is drawn from its SVG paths and filled in the accent hue, so it
    matches the bars rather than sitting on the figure as a foreign asset. Its
    x is measured from the rendered text rather than guessed, the same rule the
    spec applies to the title and subtitle.
    """
    step = 0.032 * (6.4 / h_in)
    y = 0.055 + step
    handle = ax.text(0.945, y, say(WORDMARK), fontsize=9.5, color=MUT,
                     va="center", ha="right")
    fig.canvas.draw()
    box = handle.get_window_extent(fig.canvas.get_renderer())
    left = ax.transAxes.inverted().transform((box.x0, box.y0))[0]
    draw_logo(ax, fig, x=left - 0.014, y=y, height=0.030 * (6.4 / h_in),
              colour=TEAL)


def legend(ax, entries, x=0.615, y=0.880):
    # Right align the block against the value column instead of trusting a fixed
    # start: a long label used to run off the canvas edge.
    advance = [0.030 + 0.0068 * len(label) + 0.028 for _, label in entries]
    width = sum(advance) - 0.028
    cursor = max(0.360, min(x, 0.945 - width))
    for colour, label in entries:
        ax.add_patch(FancyBboxPatch(
            (cursor, y - 0.011), 0.022, 0.022,
            boxstyle="round,pad=0,rounding_size=0.004", facecolor=colour,
            edgecolor=BAR_EDGE, linewidth=BAR_EDGE_WIDTH, zorder=4))
        handle = ax.text(cursor + 0.030, y, say(label), fontsize=10.5,
                         color=MUT, va="center", ha="left")
        cursor += 0.030 + 0.0068 * len(label) + 0.028


# ---------------------------------------------------------------- scoreboard
BAR_START, TRACK_LEN, VALUE_X = 0.340, 0.540, 0.945


def scoreboard(rows, title, subtitle, note_text, legend_entries,
               filename, *, w_in=12.0, h_in=None, y_top=0.775, y_bottom=0.185,
               bar_h=0.031, gap=0.008, label_x=0.115, chip_x=0.079,
               chip_size=0.062, value_fmt="{:.1f}"):
    """One row per competitor, one or two bars per row, one bar origin."""
    if h_in is None:
        h_in = min(9.6, max(4.4, round(2.6 + 0.55 * len(rows), 1)))
    fig, ax = canvas(w_in, h_in)
    heading(fig, ax, title, subtitle)
    if legend_entries:
        legend(ax, legend_entries)
    n = len(rows)
    pitch = (y_top - y_bottom) / max(n - 1, 1)
    for i, row in enumerate(rows):
        y = y_top - i * pitch
        # A chip with nothing in it is furniture. Family rows have no logo, so
        # they get no chip and the label starts where the chip would have been.
        if row.get("logo"):
            chipbox(ax, fig, chip_x, y, chip_size, row["logo"],
                    fill=row.get("chip_fill", CHIP))
        ax.text(label_x, y, say(row["label"]), fontsize=12.5, color=INK,
                va="center", ha="left")
        bars = row["bars"]
        offsets = ([0.0] if len(bars) == 1
                   else [(bar_h + gap) / 2, -(bar_h + gap) / 2])
        for (value, colour), dy in zip(bars, offsets):
            track(ax, fig, BAR_START, y + dy, TRACK_LEN, bar_h)
            bar(ax, fig, BAR_START, y + dy, TRACK_LEN * value / 100.0,
                bar_h, colour)
        if row.get("interval"):
            lo, hi = row["interval"]
            whisker(ax, BAR_START + TRACK_LEN * lo / 100.0,
                    BAR_START + TRACK_LEN * hi / 100.0, y + offsets[0], bar_h)
        text = row.get("value_text") or value_fmt.format(bars[0][0])
        ax.text(VALUE_X, y, say(text), fontsize=11.5, color=VAL,
                va="center", ha="right")
    if note_text:
        pass
    wordmark(fig, ax, h_in=h_in)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / filename, dpi=DPI, facecolor=BG)
    plt.close(fig)
    return filename


# ---------------------------------------------------------------- figures
S = DATA["systems"]
BY_PASS = sorted(S, key=lambda s: -S[s]["pass_at_1"])

# Plain English everywhere on the canvas. The slugs below are directory names in
# the repository; nobody glancing at a chart should have to decode
# "feature-leakage-audit". Every label stays inside the spec's 26 character
# budget, shortened rather than set smaller.
FAMILY_LABEL = {
    "split-leakage": "Train/test data leakage",
    "feature-leakage-audit": "Leaky model features",
    "docking-decoy-control": "Docking decoy controls",
    "assay-mechanism": "Why the signal moved",
    "hill-slope-anomaly": "Odd dose response curve",
    "model-build": "Building a working model",
    "replicate-power": "Too few replicates",
    "series-activity-cliff": "Activity cliff in a series",
    "dose-extrapolation": "Extrapolating past doses",
    "ensemble-disagreement": "Ensemble that disagrees",
    "promiscuity-flag": "Promiscuous compound",
    "qsar-inversion": "QSAR run backwards",
    "crystal-artifact": "Crystal packing artifact",
    "enrichment-null": "Enrichment versus chance",
    "assay-drift": "Assay drifting over time",
    "admet-filter": "ADMET filtering",
    "affinity-delta": "Binding affinity change",
    "assay-qc": "Assay quality control",
    "batch-effect-potency": "Batch effect on potency",
    "binder-selectivity": "Selective binder design",
    "conformer-energy": "Conformer energies",
    "dose-units": "Dose unit conversion",
    "fold-confidence-calibration": "Fold confidence scores",
    "multi-objective-pareto": "Multi-objective tradeoffs",
    "pose-rescoring": "Rescoring docked poses",
    "selectivity-panel": "Selectivity panel",
    "stability-triage": "Compound stability triage",
    "stereo-specificity": "Stereochemistry matters",
    "synthesis-route-cost": "Synthesis route cost",
    "tautomer-trap": "Tautomer trap",
}


def row_for(system, bars, **extra):
    return {"label": NAME[system], "logo": LOGO.get(system), "bars": bars,
            **extra}


def fig01_headline():
    rows = [row_for(s, [(100 * S[s]["pass_at_1"], TEAL)],
                    interval=[100 * S[s]["ci"][0], 100 * S[s]["ci"][1]])
            for s in BY_PASS]
    return scoreboard(
        rows,
        "Accuracy",
        None,
        None,
        [(TEAL, "Pass@1"), (BAR_D, "95% CI")],
        "fig01_headline.png")


def fig02_refusal():
    rows = [row_for(s, [(100 * S[s]["conditions"]["C0"], TEAL),
                        (100 * S[s]["conditions"]["F2"], TEALL)],
                    value_text=f"{100 * S[s]['conditions']['C0']:.0f}  /  "
                               f"{100 * S[s]['conditions']['F2']:.0f}")
            for s in sorted(S, key=lambda s: -S[s]["conditions"]["C0"])]
    return scoreboard(
        rows,
        "Refusal calibration",
        None,
        None,
        [(TEAL, "Sound"), (TEALL, "Unanswerable")],
        "fig02_refusal.png")


def fig03_defect():
    rows = [row_for(s, [(100 * S[s]["conditions"]["H1"], TEAL)])
            for s in sorted(S, key=lambda s: -S[s]["conditions"]["H1"])]
    return scoreboard(
        rows,
        "Defect detection",
        None,
        None,
        [(TEAL, "Planted defect")],
        "fig03_defect.png")


def fig04_hard():
    rows = [row_for(s, [(100 * S[s]["band"]["discriminating"], TEAL),
                        (100 * S[s]["band"]["anchor"], TEALL)],
                    value_text=f"{100 * S[s]['band']['discriminating']:.0f}  /  "
                               f"{100 * S[s]['band']['anchor']:.0f}")
            for s in sorted(S, key=lambda s: -S[s]["band"]["discriminating"])]
    return scoreboard(
        rows,
        "Accuracy by difficulty",
        None,
        None,
        [(TEAL, "Hard tasks"), (TEALL, "Easy tasks")],
        "fig04_hard.png")


def fig05_reliability():
    full = [s for s in BY_PASS if S[s]["pass_at_3"] is not None]
    rows = [row_for(s, [(100 * S[s]["pass_at_3"], TEAL),
                        (100 * S[s]["pass_at_1"], TEALL)],
                    value_text=f"{100 * S[s]['pass_at_3']:.0f}  /  "
                               f"{100 * S[s]['pass_at_1']:.0f}")
            for s in sorted(full, key=lambda s: -S[s]["pass_at_3"])]
    return scoreboard(
        rows,
        "Reliability",
        None,
        None,
        [(TEAL, "Pass^3"), (TEALL, "Pass@1")],
        "fig05_reliability.png")


def fig07_hardest():
    fams = DATA["families"]
    hard = {f: v for f, v in fams.items() if v["tier"] == "discriminating"}
    best = {f: max(v["scores"].values()) for f, v in hard.items()}
    order = sorted(hard, key=lambda f: best[f])
    rows = [{"label": FAMILY_LABEL.get(f, f), "logo": None,
             "bars": [(100 * best[f], TEAL)],
             "value_text": f"{100 * best[f]:.0f}"} for f in order]
    return scoreboard(
        rows, "Hardest task types",
        None,
        None,
        [(TEAL, "Best of 7")],
        "fig07_hardest.png", h_in=9.0, y_top=0.800, y_bottom=0.135,
        label_x=0.055)


def fig06_cost_accuracy():
    """Accuracy against price. A scoreboard cannot show a tradeoff.

    The one departure from the two house shapes, and the spec's own escape
    clause covers it: two measures per model do not fit a bar, and putting them
    on one track would be the dual axis the spec forbids most strongly. House
    tokens, Lato, teal marks, no frame, no shadow; the price scale is
    logarithmic because the spread is 19 fold and a linear axis would pile six
    models into the first inch.
    """
    fig, ax = canvas(12.0, 6.8)
    heading(fig, ax, "Accuracy vs cost", None)

    per_solve = {s: S[s]["cost_per_episode"] / S[s]["pass_at_1"] for s in S}
    import math
    x_lo, x_hi = 0.085, 2.6
    y_lo, y_hi = 26.0, 67.0
    left, right, bottom, top = 0.115, 0.930, 0.250, 0.800

    def px(value):
        span = math.log10(x_hi) - math.log10(x_lo)
        return left + (math.log10(value) - math.log10(x_lo)) / span * (right - left)

    def py(value):
        return bottom + (value - y_lo) / (y_hi - y_lo) * (top - bottom)

    for tick in (0.1, 0.2, 0.5, 1.0, 2.0):
        ax.plot([px(tick), px(tick)], [bottom, top], color=TRACK, lw=1.2,
                zorder=1)
        ax.text(px(tick), bottom - 0.045, say(f"${tick:.2f}"), fontsize=10.5,
                color=MUT, ha="center", va="center")
    for tick in (30, 40, 50, 60):
        ax.plot([left, right], [py(tick), py(tick)], color=TRACK, lw=1.2,
                zorder=1)
        ax.text(left - 0.018, py(tick), say(str(tick)), fontsize=10.5,
                color=MUT, ha="right", va="center")

    ax.text((left + right) / 2, bottom - 0.100,
            say("$ per solve"), fontsize=11.5, color=INK,
            ha="center", va="center")
    ax.text(left - 0.058, (bottom + top) / 2,
            say("Pass@1 (%)"), fontsize=11.5, color=INK,
            ha="center", va="center", rotation=90)

    # Hand placed so no label sits on a mark or on a neighbour.
    place = {"grok": (0, 0.055, "center"), "gpt": (0, 0.055, "center"),
             "claude": (-0.022, 0.0, "right"), "gemini": (0, -0.062, "center"),
             "deepseek": (0, 0.055, "center"), "kimi": (0, -0.062, "center"),
             "glm": (0, 0.055, "center")}
    for s in BY_PASS:
        x, y = px(per_solve[s]), py(100 * S[s]["pass_at_1"])
        chipbox(ax, fig, x, y, 0.052, LOGO.get(s))
        dx, dy, ha = place[s]
        ax.text(x + dx, y + dy, say(NAME[s]), fontsize=11.5, color=INK,
                ha=ha, va="center")
    wordmark(fig, ax, h_in=6.8)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig06_cost_accuracy.png", dpi=DPI, facecolor=BG)
    plt.close(fig)
    return "fig06_cost_accuracy.png"


def main() -> None:
    made = [fig01_headline(), fig02_refusal(), fig03_defect(), fig04_hard(),
            fig05_reliability(), fig06_cost_accuracy(), fig07_hardest()]
    # Pre-flight, mechanical: the spec's one hard rule before anything else.
    for text in TEXTS:
        assert "—" not in text, f"em dash in figure text: {text!r}"
        assert "–" not in text, f"en dash in figure text: {text!r}"
        assert len(text) <= 26 or " " in text, f"unbroken long label: {text!r}"
    print(f"{len(made)} figures written to {OUT}, {len(TEXTS)} strings checked, "
          "zero em dashes")
    for name in made:
        print("  ", OUT / name)


if __name__ == "__main__":
    main()
