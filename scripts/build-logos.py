"""Regenerate the Totative logos in profile/assets/.

Run: uv run --with fonttools --with uharfbuzz python scripts/build-logos.py

The mark is a capital T cut on a slant, its lower piece in the accent and shifted
right; the wordmark is the name split the same way along one horizontal line.
"""

import io
import subprocess
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

THEMES = {
    "light": {"ink": "#140F1F", "accent": "#7B2FD0", "bg": "#F5F2FA"},
    "dark": {"ink": "#F2EEF8", "accent": "#B26BFF", "bg": "#0D0A14"},
}


def load_font() -> tuple[TTFont, bytes]:
    """Pin the installed variable font at WEIGHT; returns the static font and its bytes for HarfBuzz."""
    path = subprocess.run(
        ["fc-match", "-f", "%{file}", FAMILY],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    tt = TTFont(path)
    if tt["name"].getBestFamilyName() != FAMILY:
        raise SystemExit(f"{FAMILY} is not installed (fc-match gave {path})")
    static = instancer.instantiateVariableFont(tt, {"wght": WEIGHT})
    data = io.BytesIO()
    static.save(data)
    return static, data.getvalue()


FONT, FONT_BYTES = load_font()
UPM = FONT["head"].unitsPerEm


def text_path(
    text: str, size: float, x: float, base: float, fill: str
) -> tuple[str, float, float]:
    """Shaped outlines; returns (svg, advance width, height of the tallest glyph above the baseline)."""
    hb_font = hb.Font(hb.Face(hb.Blob(FONT_BYTES)))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf, {"kern": True})
    glyphs, order = FONT.getGlyphSet(), FONT.getGlyphOrder()
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


def build() -> None:
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
    subprocess.run(
        [
            "magick",
            "-density",
            "96",
            OUT / "totative-avatar.svg",
            OUT / "totative-avatar.png",
        ],
        check=True,
    )


if __name__ == "__main__":
    build()
