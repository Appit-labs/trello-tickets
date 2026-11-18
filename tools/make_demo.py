#!/usr/bin/env python3
"""Render the README hero GIFs for every Appit skill from real captured output.

    python3 scripts/make_demo.py            # all skills with a captured transcript
    python3 scripts/make_demo.py live-qa    # one

Design rules, from how people actually read a repo (≈5–7 seconds, often as a
thumbnail): three acts — install, run, payoff — never more than ~14 lines of text
on screen, one accent colour, and the payoff line left holding for 2.6s.

Each skill's transcript lives in `demos/<skill>.json` and is captured from a real
run; nothing here invents output. Re-run a capture, regenerate the GIF, commit both.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"
OUT = ROOT / "assets"

W, PAD, LH, FS = 940, 20, 22, 15
BG, CHROME, FG, DIM, ACCENT, WARN = (18, 20, 26), (30, 33, 41), (235, 238, 245), (120, 130, 150), (126, 231, 135), (255, 145, 120)
MONO = next(
    (p for p in [
        Path.home() / ".local/share/fonts/JetBrainsMonoNerdFontMono-Regular.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ] if p.exists()),
    None,
)
SANS = next(
    (p for p in [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ] if p.exists()),
    MONO,
)


def font(size: int, mono: bool = True):
    path = MONO if mono else SANS
    return ImageFont.truetype(str(path), size) if path else ImageFont.load_default()


def frame(lines: list[str], caption: str, phase: str, cursor: int | None = None) -> Image.Image:
    h = 40 + PAD * 2 + LH * max(len(lines), 9)
    img = Image.new("RGB", (W, h), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 34], fill=CHROME)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 20, 11, 28 + i * 20, 23], fill=c)
    d.text((96, 9), caption, font=font(13, False), fill=DIM)
    f = font(FS)
    d.text((W - 12 - d.textlength(phase, font=f), 9), phase, font=f, fill=ACCENT)

    y = 34 + PAD
    for i, ln in enumerate(lines):
        colour = FG
        if ln.startswith("$ "):
            colour = ACCENT
        elif ln.startswith("✗") or "refused" in ln or "FAIL" in ln:
            colour = WARN
        elif ln.startswith("#") or ln.startswith("…"):
            colour = DIM
        d.text((PAD, y), ln[:112], font=f, fill=colour)
        if cursor == i:
            tw = d.textlength(ln[:112], font=f)
            d.rectangle([PAD + tw + 2, y - 1, PAD + tw + 9, y + FS + 3], fill=ACCENT)
        y += LH
    return img


def resolve_asset(rel: str) -> Path:
    """Assets live in assets/<skill>/ in the catalog and in skills/<skill>/assets/ in a single-skill repo."""
    for cand in (ROOT / "assets" / rel, ROOT.parent / "assets" / rel,
                 ROOT / "skills" / rel.split("/")[0] / "assets" / Path(rel).name):
        if cand.exists():
            return cand
    raise FileNotFoundError(f"{rel} (looked in assets/ and skills/*/assets/)")


def build(spec: dict) -> Path:
    frames: list[Image.Image] = []
    lines: list[str] = []
    caption = spec["caption"]
    for step in spec["steps"]:
        lines.append("$ " + step["cmd"])
        frames.append(frame(lines, caption, step.get("phase", "run"), cursor=len(lines) - 1))
        for out_line in step.get("out", []):
            lines.append(out_line)
            frames.append(frame(lines, caption, step.get("phase", "run")))
        if step.get("pause_lines"):
            lines.extend(step["pause_lines"])
        lines.append("")
    for extra in spec.get("images") or []:
        shot = Image.open(resolve_asset(extra["path"])).convert("RGB")
        shot = shot.resize((W, int(W * shot.height / shot.width)))
        canvas = Image.new("RGB", (W, 34 + shot.height), CHROME)
        canvas.paste(shot, (0, 34))
        d = ImageDraw.Draw(canvas)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([16 + i * 20, 11, 28 + i * 20, 23], fill=c)
        d.text((96, 9), extra.get("caption", caption), font=font(13, False), fill=DIM)
        d.text((W - 12 - d.textlength(extra.get("phase", ""), font=font(15)), 9),
               extra.get("phase", ""), font=font(15), fill=ACCENT)
        frames += [canvas, canvas, canvas]
    if spec.get("image"):
        # A real screenshot as the payoff frame, captioned.
        shot = Image.open(resolve_asset(spec["image"])).convert("RGB")
        shot = shot.resize((W, int(W * shot.height / shot.width)))
        canvas = Image.new("RGB", (W, 34 + shot.height), CHROME)
        canvas.paste(shot, (0, 34))
        d = ImageDraw.Draw(canvas)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([16 + i * 20, 11, 28 + i * 20, 23], fill=c)
        d.text((96, 9), spec.get("image_caption", caption), font=font(13, False), fill=DIM)
        frames += [canvas, canvas]

    durations = [420] * (len(frames) - 1) + [2600]
    durations[-3] = 900
    target = OUT / spec["out"]
    target.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(target, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=True, disposal=2)
    kb = target.stat().st_size / 1024
    print(f"{spec['out']:<28} {len(frames):>3} frames  {kb:>6.0f} KB  ({spec['skill']})")
    return target


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
