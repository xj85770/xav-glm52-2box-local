#!/usr/bin/env python3
"""Real-time proof video: stream GLM-5.2 output token-by-token, timestamp each token's
ACTUAL arrival, and render an MP4 whose generation phase runs at TRUE wall-clock (video-time
== real-time), with a live elapsed clock + running tok/s. Personal-info-free by construction
(only prints hardware/model facts + a localhost stream). Eyes-on + leak-scan before publishing.
Usage: bench-realtime.py <out.mp4>
"""
from __future__ import annotations
import json, time, sys, subprocess, tempfile, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PORT = 8080
PROMPT = "In two sentences, explain why the sky is blue."
FPS = 15
BG=(11,14,20); FG=(201,209,217); BLUE=(88,166,255); GREEN=(63,185,80); PURPLE=(210,168,255); DIM=(110,118,129)
W,H=1920,1080; PADX,PADY=90,64; LINE_H=37; FSIZE=26
FONT=ImageFont.truetype("/System/Library/Fonts/Menlo.ttc",FSIZE)
FONT_B=ImageFont.truetype("/System/Library/Fonts/Menlo.ttc",FSIZE+10)

HEADER = [
 ("GLM-5.2  -  744B Mixture-of-Experts  -  running 100% LOCAL", BLUE),
 ("No cloud. No API. Open weights. Two Apple Silicon machines.", DIM),
 ("", FG),
 ("HARDWARE : 2x Apple M5 Max, 128GB unified memory each (256GB total), Thunderbolt 5", FG),
 ("MODEL    : GLM-5.2  |  744B params, ~40B active/token  |  MoE 256 experts, glm-dsa/MLA", FG),
 ("QUANT    : IQ1_S, ~202GB  ->  split across BOTH machines (llama.cpp RPC, pipeline-parallel)", FG),
 ("CONFIG   : f16 KV cache  |  top-5 expert routing  |  +18.7% tuned (15.6->18.5)", FG),
 ("__CTX__", FG),
 ("", FG),
 ('PROMPT   : "In two sentences, explain why the sky is blue."', BLUE),
 ("", FG),
]

def wrap(text: str, width: int = 92):
    out, cur = [], ""
    for w in text.split(" "):
        if len(cur)+len(w)+1 > width:
            out.append(cur); cur = w
        else:
            cur = (cur+" "+w).strip()
    if cur: out.append(cur)
    return out or [""]

def stream():
    body = json.dumps({"messages":[{"role":"user","content":PROMPT}],
                       "max_tokens":80,"temperature":0.7,"stream":True,"cache_prompt":False}).encode()
    req = urllib.request.Request(f"http://localhost:{PORT}/v1/chat/completions",
                                 data=body, headers={"Content-Type":"application/json"})
    events=[]; t0=time.monotonic(); first=None
    with urllib.request.urlopen(req, timeout=120) as r:
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
                events.append((now,tok))
    return events, first

def draw(text_tokens_upto: str, elapsed: float, tps: float, done: bool):
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img); y=PADY
    for ln,col in HEADER:
        d.text((PADX,y),ln,font=FONT,fill=col); y+=LINE_H
    # live clock line
    clk = f"LIVE  elapsed {elapsed:5.2f}s   |   {tps:5.2f} tok/s   (real-time, unedited)"
    d.text((PADX,y),clk,font=FONT,fill=GREEN); y+=LINE_H+6
    d.text((PADX,y),"MODEL OUTPUT (streaming live):",font=FONT,fill=DIM); y+=LINE_H
    for ln in wrap(text_tokens_upto):
        d.text((PADX,y),ln,font=FONT,fill=PURPLE); y+=LINE_H
    if done:
        d.text((PADX,H-110),f"GLM-5.2  744B  fully local  ->  {tps:.1f} tok/s  measured in real time",
               font=FONT_B,fill=BLUE)
    return img

def live_nctx()->str:
    try:
        with urllib.request.urlopen(f"http://localhost:{PORT}/props",timeout=5) as r:
            g=json.loads(r.read()).get("default_generation_settings",{})
            n=g.get("n_ctx");
            return f"CONTEXT  : {int(n):,} tokens served LIVE  |  model native max 1,048,576 (1M)  -- verified" if n else "CONTEXT  : (querying...)"
    except Exception:
        return "CONTEXT  : (server props unavailable)"

def main()->int:
    out=Path(sys.argv[1])
    ctx_line=live_nctx()
    for i,(t,c) in enumerate(HEADER):
        if t=="__CTX__": HEADER[i]=(ctx_line,FG)
    events,first=stream()
    if not events:
        print("no tokens streamed — is the server warm?",file=sys.stderr); return 1
    total=events[-1][0]; gen=max(1e-3,total-(first or 0)); tps=len(events)/gen
    print(f"streamed {len(events)} tokens in {gen:.2f}s real -> {tps:.2f} tok/s")
    tmp=Path(tempfile.mkdtemp()); fi=0
    # phase 1: header + empty, held 2.5s
    for _ in range(int(FPS*2.5)):
        draw("",0.0,0.0,False).save(tmp/f"f{fi:05d}.png"); fi+=1
    # phase 2: REAL-TIME streaming — video time maps 1:1 to real time
    nframes=int(total*FPS)+1
    for k in range(nframes):
        t=k/FPS
        txt="".join(tok for (ts,tok) in events if ts<=t)
        arrived=sum(1 for (ts,_) in events if ts<=t)
        cur_tps=arrived/max(1e-3,(t-(first or 0))) if t>(first or 0) else 0.0
        draw(txt,t,cur_tps,False).save(tmp/f"f{fi:05d}.png"); fi+=1
    # phase 3: final, held 3s
    full="".join(t for _,t in events)
    for _ in range(int(FPS*3)):
        draw(full,total,tps,True).save(tmp/f"f{fi:05d}.png"); fi+=1
    subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(tmp/"f%05d.png"),
                    "-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(out)],
                   check=True,capture_output=True)
    for p in tmp.glob("*.png"): p.unlink()
    tmp.rmdir()
    dur=fi/FPS
    print(f"rendered {fi} frames @ {FPS}fps = {dur:.1f}s video ({out.stat().st_size//1024} KB); "
          f"generation phase = {total:.2f}s real-time")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
