"""Regenerate the Totative logos in profile/assets/.

Run: uv run --with fonttools --with uharfbuzz python scripts/build-logos.py [--variant B]

The mark is a capital T cut on a slant, its lower piece in the accent and shifted
right; the wordmark is the name split the same way along one horizontal line.
The social cards carry the site's lattice: dots whose offset from a ringed viewpoint
is coprime, i.e. in line of sight, light up.
"""

import argparse
import io
import subprocess
from math import gcd
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "profile" / "assets"
FAMILY = "Atkinson Hyperlegible Next"
WEIGHT = 800
BODY_WEIGHT = 500

THEMES = {
    "light": {"ink": "#140F1F", "accent": "#7B2FD0", "bg": "#F5F2FA"},
    "dark": {
        "ink": "#F2EEF8",
        "accent": "#B26BFF",
        "bg": "#0D0A14",
        "soft": "#C8BFD6",
        "lit": "#C9B2E6",
        "dim": "#221A30",
    },
}

REPOS = (
    (
        "go-avscan",
        "Asks the machine's antivirus about a folder of files: Windows AMSI, a clamd daemon, or a command you name.",
    ),
    (
        "go-keyring",
        "One credential store for a Go desktop app: the OS keyring, with a sealed-file fallback inside a Flatpak.",
    ),
    (
        "go-codepair",
        "Pair two devices on a LAN with a short human-typed code and an authenticated key exchange.",
    ),
    (
        "repo-template",
        "Starting point for a Totative repository: secret-scanning hooks, CodeQL, dependency review, Scorecard and attested releases",
    ),
    (
        ".github",
        "Totative's organisation profile, security policy, disclosure policy and default community files",
    ),    (
        "totative.dev",
        "Software security research, and the tools we build for it.",
    ),
)


def load_font(weight: int) -> tuple[TTFont, bytes]:
    """Pin the installed variable font at `weight`; returns the static font and its bytes for HarfBuzz."""
    path = subprocess.run(
        ["fc-match", "-f", "%{file}", FAMILY],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    tt = TTFont(path)
    if tt["name"].getBestFamilyName() != FAMILY:
        raise SystemExit(f"{FAMILY} is not installed (fc-match gave {path})")
    static = instancer.instantiateVariableFont(tt, {"wght": weight})
    data = io.BytesIO()
    static.save(data)
    return static, data.getvalue()


HEAVY = load_font(WEIGHT)
BODY = load_font(BODY_WEIGHT)
FONT = HEAVY[0]
UPM = FONT["head"].unitsPerEm


def text_path(
    text: str,
    size: float,
    x: float,
    base: float,
    fill: str,
    font: tuple[TTFont, bytes] = HEAVY,
) -> tuple[str, float, float]:
    """Shaped outlines; returns (svg, advance width, height of the tallest glyph above the baseline)."""
    hb_font = hb.Font(hb.Face(hb.Blob(font[1])))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf, {"kern": True})
    glyphs, order = font[0].getGlyphSet(), font[0].getGlyphOrder()
    scale = size / UPM
    pen_x, top, paths = 0, 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        glyph = glyphs[order[info.codepoint]]
        pen, bounds = SVGPathPen(glyphs), BoundsPen(glyphs)
        glyph.draw(pen)
        glyph.draw(bounds)
        if bounds.bounds:
            top = max(top, bounds.bounds[3] * scale)
            tx = x + (pen_x + pos.x_offset) * scale
            paths.append(
                f'<path transform="translate({tx:.2f} {base:.2f}) scale({scale:.5f} {-scale:.5f})" d="{pen.getCommands()}"/>'
            )
        pen_x += pos.x_advance
    return f'<g fill="{fill}">{"".join(paths)}</g>', pen_x * scale, top


def sliced(
    top: str,
    bottom: str,
    p0: tuple[float, float],
    p1: tuple[float, float],
    shift: float,
    gap: float,
) -> str:
    """Cut along the line p0-p1: top stays, bottom shifts right by `shift`, `gap` apart."""
    far = 1e4

    def y(x: float, off: float) -> float:
        return p0[1] + (p1[1] - p0[1]) * (x - p0[0]) / (p1[0] - p0[0]) + off

    return (
        f'<defs><clipPath id="above"><polygon points="{-far},{-far} {far},{-far} {far},{y(far, -gap / 2):.2f} {-far},{y(-far, -gap / 2):.2f}"/></clipPath>'
        f'<clipPath id="below"><polygon points="{-far},{y(-far, gap / 2):.2f} {far},{y(far, gap / 2):.2f} {far},{far} {-far},{far}"/></clipPath></defs>'
        f'<g clip-path="url(#above)">{top}</g>'
        f'<g clip-path="url(#below)"><g transform="translate({shift} 0)">{bottom}</g></g>'
    )


def mark(theme: dict[str, str]) -> str:
    """The sliced T in a 200x200 box."""
    size, cx, cy = 190, 96, 104
    glyph = FONT.getGlyphSet()[FONT.getBestCmap()[ord("T")]]
    bounds = BoundsPen(FONT.getGlyphSet())
    glyph.draw(bounds)
    x0, y0, x1, y1 = (v * size / UPM for v in bounds.bounds)
    x, base = cx - (x0 + x1) / 2, cy + (y0 + y1) / 2
    top, _, _ = text_path("T", size, x, base, theme["ink"])
    bottom, _, _ = text_path("T", size, x, base, theme["accent"])
    return sliced(top, bottom, (0, 128), (200, 92), 8, 10)


def wordmark(theme: dict[str, str]) -> tuple[str, float, float]:
    size, pad, shift = 64, 8, 6
    _, width, ascent = text_path("totative", size, 0, 0, "")
    base = pad + ascent
    top, _, _ = text_path("totative", size, pad, base, theme["ink"])
    bottom, _, _ = text_path("totative", size, pad, base, theme["accent"])
    cut = base - FONT["OS/2"].sxHeight / UPM * size * 0.36
    body = sliced(top, bottom, (0, cut), (1, cut), shift, 4)
    return body, width + shift + 2 * pad, base + 2 * pad


def wrap(
    text: str,
    size: float,
    max_width: float,
    max_lines: int,
    font: tuple[TTFont, bytes] = BODY,
) -> list[str]:
    """Greedy word wrap by shaped advance width; exits if a word or the whole text cannot fit."""
    words = text.split()
    if not words:
        raise SystemExit("empty description")

    def width(s: str) -> float:
        w = text_path(s, size, 0, 0, "", font)[1]
        if " " not in s and w > max_width:
            raise SystemExit(f"{s!r} is {w:.0f}px wide, max {max_width:.0f}px")
        return w

    lines: list[str] = []
    current = words[0]
    width(current)
    for word in words[1:]:
        if width(f"{current} {word}") <= max_width:
            current = f"{current} {word}"
            continue
        lines.append(current)
        current = word
        width(current)
    lines.append(current)
    if len(lines) > max_lines:
        raise SystemExit(
            f"description needs {len(lines)} lines (max {max_lines}): {text}"
        )
    return lines


CELL = 32
CARD = (1280, 640)

# Both variants share the type and grid; they differ in where the lattice sits and how much of it is lit.
# eye: grid cell of the ringed viewpoint; rows: grid rows that carry dots; falloff: squared cell
# distance at which a lit dot is at 60%; fade_x: x where lit dots start to show (fully lit 240px on);
# col: text column width; title_base and desc_* place the text block.
VARIANTS = {
    "A": {
        "eye": (33, 11),
        "rows": (1, 19),
        "falloff": 40,
        "reach": 6,
        "fade_x": 720,
        "col": 704,
        "title_base": 340,
        "desc_size": 34,
        "desc_lead": 46,
        "desc_lines": 3,
    },
    "B": {
        "eye": (33, 16),
        "rows": (14, 19),
        "falloff": 24,
        "reach": 4,
        "fade_x": 0,
        "col": 1088,
        "title_base": 266,
        "desc_size": 36,
        "desc_lead": 50,
        "desc_lines": 2,
    },
}


def lattice(theme: dict[str, str], v: dict) -> str:
    """Dot field on the CELL grid: dots in line of sight from the eye (coprime offsets) are lit,
    dimming with distance; rays join the eye to the nearest of them, as on totative.dev."""
    (ex, ey), (r0, r1) = v["eye"], v["rows"]
    dim, lit, rays = [], {}, []
    for gy in range(r0, r1 + 1):
        for gx in range(1, CARD[0] // CELL):
            x, y = gx * CELL, gy * CELL
            dx, dy = gx - ex, gy - ey
            level = 0.0
            if gcd(abs(dx), abs(dy)) == 1:
                fade = min(1.0, max(0.0, (x - v["fade_x"]) / 240))
                level = (0.2 + 0.8 / (1 + (dx * dx + dy * dy) / v["falloff"])) * fade
                if dx * dx + dy * dy <= v["reach"] ** 2:
                    rays.append(f"M{ex * CELL} {ey * CELL}L{x} {y}")
            bucket = round(level * 8)
            if bucket == 0:
                dim.append(f'<circle cx="{x}" cy="{y}" r="2"/>')
            else:
                lit.setdefault(bucket, []).append(
                    f'<circle cx="{x}" cy="{y}" r="{2 + bucket / 8 * 1.6:.2f}"/>'
                )
    return (
        f'<path d="{"".join(rays)}" stroke="{theme["lit"]}" stroke-width="1.25" opacity="0.12"/>'
        f'<g fill="{theme["dim"]}">{"".join(dim)}</g>'
        + "".join(
            f'<g fill="{theme["lit"]}" opacity="{b / 8:.3f}">{"".join(c)}</g>'
            for b, c in sorted(lit.items())
        )
        + f'<circle cx="{ex * CELL}" cy="{ey * CELL}" r="11" fill="none" stroke="{theme["accent"]}" stroke-width="2.5"/>'
    )


def social_card(
    repo: str, description: str, theme: dict[str, str], variant: str
) -> str:
    """1280x640 Open Graph card: lattice, wordmark, repo name, wrapped description."""
    v = VARIANTS[variant]
    margin, col, title_size = 3 * CELL, v["col"], 100
    wm_body, _, wm_h = wordmark(theme)
    wm_scale = 48 / wm_h
    wm = f'<g transform="translate({margin - 8 * wm_scale:.2f} {2 * CELL}) scale({wm_scale:.5f})">{wm_body}</g>'
    title, title_w, _ = text_path(
        repo, title_size, margin, v["title_base"], theme["ink"]
    )
    if title_w > col:
        raise SystemExit(f"{repo}: name is {title_w:.0f}px wide, max {col}px")
    desc = "".join(
        text_path(
            line,
            v["desc_size"],
            margin,
            v["title_base"] + 64 + i * v["desc_lead"],
            theme["soft"],
            BODY,
        )[0]
        for i, line in enumerate(
            wrap(description, v["desc_size"], col, v["desc_lines"])
        )
    )
    return svg(CARD, lattice(theme, v) + wm + title + desc, CARD, bg=theme["bg"])


def svg(
    view: tuple[float, float],
    body: str,
    size: tuple[float, float] | None = None,
    bg: str | None = None,
) -> str:
    w, h = size or view
    fill = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view[0]:.0f} {view[1]:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="Totative">'
        f"<title>Totative</title>{fill}{body}</svg>\n"
    )


def png(src: Path | str, dest: Path, svg_text: str | None = None) -> None:
    """Rasterise at 96 dpi, without the timestamp chunks that would make every rebuild a diff."""
    subprocess.run(
        [
            "magick",
            "-density",
            "96",
            src,
            "-define",
            "png:exclude-chunks=date,time",
            dest,
        ],
        input=svg_text.encode() if svg_text else None,
        check=True,
    )


def build(variant: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        (OUT / f"totative-mark-{name}.svg").write_text(
            svg((200, 200), mark(theme), (512, 512))
        )
        body, w, h = wordmark(theme)
        (OUT / f"totative-wordmark-{name}.svg").write_text(svg((w, h), body))

    dark = THEMES["dark"]
    (OUT / "totative-avatar.svg").write_text(
        svg((200, 200), mark(dark), (512, 512), bg=dark["bg"])
    )
    png(OUT / "totative-avatar.svg", OUT / "totative-avatar.png")
    social = OUT / "social"
    social.mkdir(parents=True, exist_ok=True)
    for repo, description in REPOS:
        png(
            "svg:-",
            social / f"{repo}.png",
            social_card(repo, description, dark, variant),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--variant", choices=sorted(VARIANTS), default="A", help="social card layout"
    )
    build(parser.parse_args().variant)
