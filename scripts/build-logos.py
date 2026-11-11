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
    ),
)


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


def wrap(text: str, size: float, max_width: float, max_lines: int = 2) -> list[str]:
    """Greedy word wrap by shaped advance width; exits if a word or the whole text cannot fit."""
    words = text.split()
    if not words:
        raise SystemExit("empty description")
    lines: list[str] = []
    current = words[0]
    _, width, _ = text_path(current, size, 0, 0, "")
    if width > max_width:
        raise SystemExit(f"{current!r} is {width:.0f}px wide, max {max_width:.0f}px")
    for word in words[1:]:
        candidate = f"{current} {word}"
        _, width, _ = text_path(candidate, size, 0, 0, "")
        if width <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
        _, width, _ = text_path(current, size, 0, 0, "")
        if width > max_width:
            raise SystemExit(
                f"{current!r} is {width:.0f}px wide, max {max_width:.0f}px"
            )
    lines.append(current)
    if len(lines) > max_lines:
        raise SystemExit(
            f"description needs {len(lines)} lines (max {max_lines}): {text}"
        )
    return lines


def social_card(repo: str, description: str, theme: dict[str, str]) -> str:
    """1280x640 Open Graph card: wordmark, name, wrapped description, accent bar."""
    margin, col, title_size, desc_size = 100, 1080, 88, 34
    wm_body, _, wm_h = wordmark(theme)
    wm_scale = 56 / wm_h
    wm = f'<g transform="translate({margin} {margin}) scale({wm_scale:.5f})">{wm_body}</g>'
    title, title_w, _ = text_path(repo, title_size, margin, 320, theme["ink"])
    if title_w > col:
        raise SystemExit(f"{repo}: name is {title_w:.0f}px wide, max {col}px")
    desc_parts = []
    for i, line in enumerate(wrap(description, desc_size, col)):
        g, line_w, _ = text_path(line, desc_size, margin, 376 + i * 46, theme["ink"])
        if line_w > col:
            raise SystemExit(
                f"{repo}: line {i + 1} is {line_w:.0f}px wide, max {col}px"
            )
        desc_parts.append(g)
    desc = f'<g opacity="0.75">{"".join(desc_parts)}</g>'
    bar = f'<rect x="0" y="634" width="1280" height="6" fill="{theme["accent"]}"/>'
    return svg((1280, 640), wm + title + desc + bar, (1280, 640), bg=theme["bg"])


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
    social = OUT / "social"
    social.mkdir(parents=True, exist_ok=True)
    for repo, description in REPOS:
        subprocess.run(
            ["magick", "-density", "96", "svg:-", social / f"{repo}.png"],
            input=social_card(repo, description, dark).encode(),
            check=True,
        )


if __name__ == "__main__":
    build()
