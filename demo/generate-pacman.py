#!/usr/bin/env python3
"""Ask the local GLM-5.2 (128K ctx) to write a complete single-file Pac-Man game.
Stream it, timestamp every token (for a real-time generation video), save the HTML.
Personal-info-free: only a localhost call + the model's own output. Usage: generate-pacman.py
"""
from __future__ import annotations
import json, time, re, urllib.request
from pathlib import Path

PORT=8080
SYS=("You are an expert game developer. Output ONLY a single complete HTML file (inline CSS+JS, "
     "HTML5 canvas, no external libraries). No explanation, no markdown fences.")
PROMPT=("Write a complete, playable Pac-Man game as ONE self-contained HTML file. Requirements: "
        "a maze of walls drawn on a canvas; Pac-Man moves with arrow keys and animates its mouth; "
        "pellets to eat that increase a visible score; at least 2 ghosts that chase Pac-Man with "
        "simple AI; collision = lose with a Game Over message; eating all pellets = You Win; a clean "
        "start screen. Keep it under ~400 lines. Output ONLY the HTML, starting with <!DOCTYPE html>.")

def main()->int:
    body=json.dumps({"messages":[{"role":"system","content":SYS},{"role":"user","content":PROMPT}],
                     "max_tokens":7000,"temperature":0.5,"stream":True,"cache_prompt":False}).encode()
    req=urllib.request.Request(f"http://localhost:{PORT}/v1/chat/completions",
                               data=body,headers={"Content-Type":"application/json"})
    events=[]; t0=time.monotonic(); first=None; full=[]
    print("streaming Pac-Man from GLM-5.2 (128K ctx)... (live)")
    with urllib.request.urlopen(req,timeout=900) as r:
        for raw in r:
            s=raw.decode("utf-8","ignore").strip()
            if not s.startswith("data:"): continue
            d=s[5:].strip()
            if d=="[DONE]": break
            try: tok=json.loads(d)["choices"][0]["delta"].get("content","")
            except Exception: tok=""
            if tok:
                now=time.monotonic()-t0
                if first is None: first=now
                events.append((now,tok)); full.append(tok)
                n=len(events)
                if n%50==0:
                    print(f"  {n} tokens  {n/max(1e-3,now-(first or 0)):.1f} tok/s  {now:.1f}s")
    text="".join(full)
    total=events[-1][0] if events else 0; gen=max(1e-3,total-(first or 0)); tps=len(events)/gen
    # extract the HTML (strip any stray fences/prose)
    m=re.search(r"<!DOCTYPE html>.*?</html>", text, re.DOTALL|re.IGNORECASE)
    html=m.group(0) if m else text
    Path("pacman.html").write_text(html)
    Path("pacman-events.json").write_text(json.dumps([[round(t,3),tok] for t,tok in events]))
    print(f"\nDONE: {len(events)} tokens in {gen:.1f}s real -> {tps:.2f} tok/s")
    print(f"  saved pacman.html ({len(html)} chars, ~{html.count(chr(10))+1} lines)")
    print(f"  has <canvas>: {'<canvas' in html.lower()} | has arrow keys: {'arrow' in html.lower() or 'keydown' in html.lower()}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
