#!/usr/bin/env python3
"""Render the README demo GIF for a skill from a real captured run.

    python3 tools/make_demo.py                # all transcripts in demos/
    python3 tools/make_demo.py live-qa        # one

Design, after studying how the demos of ripgrep, fzf, bat, lazygit and the
charmbracelet toolset are built:

  * One scenario, not a command dump. A viewer needs `problem → command → payoff`
    in under ten seconds, with a human prompt and a real working directory.
  * The command types itself; the output appears; the payload line holds.
  * A caption bar says *why* this step exists, in plain words. A GIF without the
    "why" is decoration; with it, it is an argument.
  * Nothing that is not real. The transcript in `demos/<skill>.json` is captured
    from an actual run, so the GIF can be regenerated (`vhs` discipline) and audited.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"

W, PAD, LH = 960, 24, 22
BAR, FOOT = 44, 30
BG, CHROME = (13, 15, 20), (28, 31, 39)
FG, DIM, MUTED = (222, 227, 236), (128, 138, 156), (88, 96, 112)
GREEN, CYAN, AMBER, RED = (126, 231, 135), (110, 200, 230), (230, 190, 120), (255, 130, 120)

MONO = next((p for p in [Path("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf"),
                         Path.home() / ".local/share/fonts/JetBrainsMonoNerdFontMono-Regular.ttf",
                         Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")] if p.exists()), None)
SANS = next((p for p in [Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")] if p.exists()), MONO)
FS = 16


def font(size: int, mono: bool = True):
    path = MONO if mono else SANS
    return ImageFont.truetype(str(path), size) if path else ImageFont.load_default()


WRAP = 92   # characters that fit at 960px with a 16px mono face, minus padding


def wrap(line: str, width: int = WRAP, indent: str = "      ") -> list[str]:
    """Terminal output wraps; a GIF that clips mid-word looks broken."""
    if len(line) <= width:
        return [line]
    out, rest = [], line
    while len(rest) > width:
        cut = rest.rfind(" ", 0, width) or width
        out.append(rest[:cut])
        rest = indent + rest[cut:].lstrip()
    out.append(rest)
    return out


def colour_for(line: str) -> tuple:
    if line.startswith("$ "):
        return GREEN
    if line.startswith("#"):
        return MUTED
    if line.startswith("✗") or "refused" in line or "FAIL" in line or "timeout" in line:
        return RED
    if line.startswith("== ") or line.startswith("# "):
        return CYAN
    return FG


def draw_frame(lines: list[str], caption: str, phase: str, prompt: str,
               cursor: int | None = None, typed: int | None = None) -> Image.Image:
    height = BAR + PAD + LH * max(len(lines), 8) + FOOT
    img = Image.new("RGB", (W, height), BG)
    d = ImageDraw.Draw(img)

    # window chrome
    d.rectangle([0, 0, W, BAR], fill=CHROME)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([18 + i * 21, 16, 31 + i * 21, 29], fill=c)
    d.text((104, 15), prompt, font=font(13), fill=DIM)
    d.text((W - 18 - d.textlength(phase, font=font(13)), 15), phase, font=font(13), fill=CYAN)

    # body
    f = font(FS)
    y = BAR + PAD
    for i, raw in enumerate(lines):
        line = raw[:WRAP]
        if cursor is not None and i == cursor and typed is not None:
            line = line[:typed]
        d.text((PAD, y), line, font=f, fill=colour_for(raw))
        if cursor == i:
            tw = d.textlength(line, font=f)
            d.rectangle([PAD + tw + 3, y - 2, PAD + tw + 11, y + FS + 3], fill=GREEN)
        y += LH

    # caption bar: the "why"
    d.rectangle([0, height - FOOT, W, height], fill=CHROME)
    d.text((PAD, height - FOOT + 7), caption[:120], font=font(13), fill=MUTED)
    return img


def resolve_asset(rel: str) -> Path:
    for cand in (ROOT / "assets" / rel, ROOT / "skills" / rel.split("/")[0] / "assets" / Path(rel).name,
                 ROOT / "assets" / Path(rel).name):
        if cand.exists():
            return cand
    raise FileNotFoundError(rel)


def shot_frame(path: Path, caption: str, phase: str, prompt: str) -> Image.Image:
    im = Image.open(path).convert("RGB")
    im = im.resize((W, int(W * im.height / im.width)), Image.LANCZOS)
    canvas = Image.new("RGB", (W, BAR + im.height + FOOT), BG)
    canvas.paste(im, (0, BAR))
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, BAR], fill=CHROME)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([18 + i * 21, 16, 31 + i * 21, 29], fill=c)
    d.text((104, 15), prompt, font=font(13), fill=DIM)
    d.text((W - 18 - d.textlength(phase, font=font(13)), 15), phase, font=font(13), fill=CYAN)
    d.rectangle([0, canvas.height - FOOT, W, canvas.height], fill=CHROME)
    d.text((PAD, canvas.height - FOOT + 7), caption[:120], font=font(13), fill=MUTED)
    return canvas


def build(spec: dict) -> Path:
    frames: list[Image.Image] = []
    durations: list[int] = []
    lines: list[str] = []
    prompt = spec.get("prompt", "~/demo")

    for step in spec["steps"]:
        cmd = step["cmd"]
        full = ("$ " + cmd) if step.get("shell", True) else cmd
        lines.append(full)
        idx = len(lines) - 1
        # type it out
        for n in range(8, len(full) + 1, max(10, len(full) // 5)):
            frames.append(draw_frame(lines, step.get("note", ""), step.get("phase", ""), prompt, cursor=idx, typed=n))
            durations.append(55)
        frames.append(draw_frame(lines, step.get("note", ""), step.get("phase", ""), prompt, cursor=idx, typed=len(full)))
        durations.append(320)
        wrapped = []
        for one in step.get("out", []):
            wrapped.extend(wrap(one))
        pending = wrapped
        while pending:
            chunk = pending[:2]
            pending = pending[2:]
            lines.extend(chunk)
            frames.append(draw_frame(lines, step.get("note", ""), step.get("phase", ""), prompt))
            durations.append(230)
        lines.append("")
        durations[-1] = 700

    for extra in spec.get("images") or []:
        f = shot_frame(resolve_asset(extra["path"]), extra.get("note", ""), extra.get("phase", ""), prompt)
        frames += [f, f]
        durations += [1600, 2600]

    if spec.get("image"):
        f = shot_frame(resolve_asset(spec["image"]), spec.get("note", ""), "verdict", prompt)
        frames += [f, f]
        durations += [1600, 2400]

    durations[-1] = max(durations[-1], 2600)
    # 64-colour palette: three times smaller files, no visible loss on a terminal screenshot
    frames = [f.quantize(colors=48, method=Image.MEDIANCUT, dither=Image.NONE) for f in frames]
    out = ROOT / "skills" / spec["skill"] / "assets" / "demo.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations[: len(frames)],
                   loop=0, optimize=True, disposal=2)
    print(f"{spec['skill']:<18} {len(frames):>3} frames  {out.stat().st_size/1024:>6.0f} KB  → {out.relative_to(ROOT)}")
    return out


def main(argv: list[str]) -> int:
    wanted = set(argv[1:])
    specs = sorted(DEMOS.glob("*.json"))
    if not specs:
        print(f"no transcripts in {DEMOS}", file=sys.stderr)
        return 1
    for path in specs:
        spec = json.loads(path.read_text())
        if wanted and spec["skill"] not in wanted:
            continue
        build(spec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
