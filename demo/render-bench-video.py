#!/usr/bin/env python3
"""Render a scrubbed benchmark transcript into a terminal-style MP4 (line-by-line reveal).
Personal-info-free by construction: it only renders the text you pass in. Re-scan that text
for leaks BEFORE calling this. Usage: render-bench-video.py <input.txt> <output.mp4>
"""
from __future__ import annotations
import re, sys, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG = (11, 14, 20)          # near-black terminal
FG = (201, 209, 217)       # default light grey
BLUE = (88, 166, 255)      # titles / headers
GREEN = (63, 185, 80)      # tok/s numbers, "CLEAN", positives
PURPLE = (210, 168, 255)   # model output
DIM = (110, 118, 129)      # rules / dim
W, H = 1920, 1080
PAD_X, PAD_Y = 90, 70
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
FSIZE = 27
LINE_H = 38
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07|[\x00-\x08\x0b\x0c\x0e-\x1f]")

def colour(line: str) -> tuple:
    s = line.strip()
    if set(s) <= {"=", " "} and "=" in s: return DIM
    if set(s) <= {"-", " "} and "-" in s: return DIM
    if "tok/s" in line or "STEADY DECODE" in line: return GREEN
    if line.startswith("  \"") or "MODEL OUTPUT" in line: return PURPLE
    if "GLM-5.2" in line and ("MoE" in line or "fully local" in line or "Verified" in line): return BLUE
    if any(k in line for k in ("HARDWARE", "MODEL", "QUANT", "CONFIG", "TUNING", "PROMPT")): return BLUE
    return FG

def render(lines: list[str], font: ImageFont.FreeTypeFont) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = PAD_Y
    for ln in lines:
        d.text((PAD_X, y), ln, font=font, fill=colour(ln))
        y += LINE_H
    return img

def main() -> int:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    raw = ANSI.sub("", src.read_text())
    lines = [l.rstrip() for l in raw.splitlines() if l.strip() != "" or True]
    # drop a leading blank/clear artifacts
    while lines and lines[0].strip() == "":
        lines.pop(0)
    font = ImageFont.truetype(FONT_PATH, FSIZE)
    tmp = Path(tempfile.mkdtemp())
    frame = 0
    # progressive reveal: one frame per revealed line
    for i in range(1, len(lines) + 1):
        render(lines[:i], font).save(tmp / f"f{frame:04d}.png"); frame += 1
    # hold the full frame
    full = render(lines, font)
    for _ in range(20):
        full.save(tmp / f"f{frame:04d}.png"); frame += 1
    cmd = ["ffmpeg", "-y", "-framerate", "3", "-i", str(tmp / "f%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    # cleanup frames
    for p in tmp.glob("*.png"): p.unlink()
    tmp.rmdir()
    print(f"rendered {frame} frames -> {out} ({out.stat().st_size//1024} KB)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
