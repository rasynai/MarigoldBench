"""The Rasyn mark, as matplotlib paths, in whatever colour the figure wants.

The source is an SVG of five subpaths using only relative moveto, lineto and
cubic curveto, with no fill attribute, so the colour is entirely ours to set.
There is no SVG renderer on this machine and installing one on Windows drags in
native cairo, so the path data is parsed here instead. That keeps the mark
vector-accurate, keeps the figures dependency-free, and means recolouring is a
parameter rather than an image edit.

    from crucible.lab.logo import draw_logo
    draw_logo(ax, fig, x=0.9, y=0.06, height=0.05, colour="#009e7f")
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path as FilePath

from matplotlib.patches import PathPatch
from matplotlib.path import Path

# The mark ships with the repository so a clone can regenerate every figure.
# The Downloads copy stays as a fallback for the machine it was drawn on.
_REPO = FilePath(__file__).resolve().parents[2]
_CANDIDATES = (
    _REPO / "figures" / "assets" / "rasyn-mark.svg",
    FilePath(r"C:\Users\ansht\Downloads"
             r"\vectorized_01a0220c-a6c3-7f82-88f6-2fee100530f5.svg"),
)
SOURCE = next((path for path in _CANDIDATES if path.exists()), _CANDIDATES[0])

_NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
_TOKEN = re.compile(r"([MmLlCcZz])|([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)")


def _parse(data: str) -> tuple[list[tuple[float, float]], list[int]]:
    """One SVG subpath string to matplotlib vertices and codes.

    Handles the four commands this mark uses, relative only, including the two
    implicit forms the spec allows: extra coordinate pairs after `m` continue as
    linetos, and extra triples after `c` continue as curvetos.
    """
    tokens = [(letter, number) for letter, number in _TOKEN.findall(data)]
    vertices: list[tuple[float, float]] = []
    codes: list[int] = []
    index = 0
    command = None
    x = y = 0.0
    start = (0.0, 0.0)

    def take(count: int) -> list[float]:
        nonlocal index
        out = []
        while len(out) < count:
            letter, number = tokens[index]
            index += 1
            if letter:
                raise ValueError(f"expected a number, found {letter!r}")
            out.append(float(number))
        return out

    while index < len(tokens):
        letter, _ = tokens[index]
        if letter:
            command = letter
            index += 1
            if command in "Zz":
                codes.append(Path.CLOSEPOLY)
                vertices.append(start)
                x, y = start
                continue
        if command is None:
            raise ValueError("path data began without a command")
        if command == "m":
            dx, dy = take(2)
            x, y = x + dx, y + dy
            start = (x, y)
            vertices.append((x, y))
            codes.append(Path.MOVETO)
            command = "l"          # implicit lineto for further pairs
        elif command == "l":
            dx, dy = take(2)
            x, y = x + dx, y + dy
            vertices.append((x, y))
            codes.append(Path.LINETO)
        elif command == "c":
            a, b, c, d, e, f = take(6)
            first = (x + a, y + b)
            second = (x + c, y + d)
            x, y = x + e, y + f
            vertices.extend([first, second, (x, y)])
            codes.extend([Path.CURVE4] * 3)
        else:
            raise ValueError(f"unsupported command {command!r}")
    return vertices, codes


@lru_cache(maxsize=4)
def _geometry(source: str) -> tuple[tuple[Path, ...], float, float]:
    """Every subpath, plus the viewBox width and height."""
    text = FilePath(source).read_text(encoding="utf-8")
    box = re.search(r'viewBox="([\d.\s-]+)"', text)
    _, _, width, height = (float(v) for v in box.group(1).split())
    paths = []
    for data in re.findall(r'<path[^>]*\sd="([^"]+)"', text):
        vertices, codes = _parse(data)
        paths.append(Path(vertices, codes))
    return tuple(paths), width, height


def draw_logo(ax, fig, x: float, y: float, height: float, colour: str,
              source: FilePath | str = SOURCE) -> float:
    """Draw the mark with its centre at (x, y) in axes fractions.

    `height` is in axes units; the width is corrected by the figure aspect so
    the mark is not stretched, and the drawn width is returned so a caller can
    place text beside it.
    """
    paths, box_w, box_h = _geometry(str(source))
    aspect = getattr(fig, "_aspect", 1.0)
    scale_y = height / box_h
    scale_x = scale_y / aspect
    width = box_w * scale_x
    for path in paths:
        moved = [
            (x - width / 2 + px * scale_x,
             # SVG y grows downward; axes y grows upward
             y + height / 2 - py * scale_y)
            for px, py in path.vertices
        ]
        ax.add_patch(PathPatch(Path(moved, path.codes), facecolor=colour,
                               edgecolor="none", zorder=5))
    return width
