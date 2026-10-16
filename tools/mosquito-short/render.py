"""render — assemble the finished 1080x1920 / 30fps / 25s short.

  python3 render.py                -> out/mosquito-vs-stickman.mp4   (full render + audio)
  python3 render.py --preview      -> out/preview.mp4                (every 4th frame, 540x960)
  python3 render.py --sheet PATH   -> out/contact-sheet-*.png        (keyframe proof sheet)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shots
from sticklib import DUR, FPS, H, W

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
TITLE = "mosquito-vs-stickman"


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run_ffmpeg(args, **kw):
    return subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"] + args, **kw)


def full_render():
    os.makedirs(OUT, exist_ok=True)
    n = int(round(DUR * FPS))
    dst = os.path.join(OUT, f"{TITLE}.mp4")
    audio = os.path.join(HERE, "audio", "mix.wav")
    cmd = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if os.path.exists(audio):
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-level", "4.0", "-movflags", "+faststart", dst]
    p = subprocess.Popen([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"] + cmd,
                         stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(n):
        t = i / FPS
        img = shots.render(t)
        p.stdin.write(img.tobytes())
        if i % 25 == 0:
            el = time.time() - t0
            eta = el / max(1, i + 1) * (n - i - 1)
            print(f"frame {i:4d}/{n}  t={t:5.2f}s  elapsed {el:6.1f}s  eta {eta:6.1f}s", flush=True)
    p.stdin.close()
    p.wait()
    print("wrote", dst, f"{os.path.getsize(dst)/1e6:.1f} MB")
    return dst


def preview(dst=None, step=4, scale=0.5):
    os.makedirs(OUT, exist_ok=True)
    dst = dst or os.path.join(OUT, "preview.mp4")
    n = int(round(DUR * FPS))
    idx = list(range(0, n, step))
    size = (int(W * scale), int(H * scale))
    p = subprocess.Popen([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
                          "-r", str(FPS / step), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "20", "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)
    for i in idx:
        img = shots.render(i / FPS).resize(size, Image.LANCZOS)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    print("wrote", dst)
    return dst


def sheet(times=None, cols=5, tw=280, gap=8, parts=2):
    """storyboard proof sheet(s) straight out of the timeline"""
    times = times or [1.0, 2.6, 3.4, 4.5, 5.6, 7.5, 9.4, 11.2, 12.7, 14.6, 16.4, 17.0,
                      18.0, 19.9, 20.6, 22.0, 23.0, 24.2, 24.7]
    os.makedirs(OUT, exist_ok=True)
    th = int(tw * H / W)
    per = (len(times) + parts - 1) // parts
    paths = []
    for k in range(parts):
        sub = times[k * per:(k + 1) * per]
        if not sub:
            continue
        rows = (len(sub) + cols - 1) // cols
        sh = Image.new("RGB", (cols * (tw + gap) + gap, rows * (th + gap) + gap), (18, 18, 22))
        for j, t in enumerate(sub):
            sh.paste(shots.render(t).resize((tw, th), Image.LANCZOS),
                     (gap + (j % cols) * (tw + gap), gap + (j // cols) * (th + gap)))
        p_ = os.path.join(OUT, f"storyboard-{k + 1}.png")
        sh.save(p_)
        paths.append(p_)
    print("wrote", paths)
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()
    if a.sheet:
        sheet()
    elif a.preview:
        preview()
    else:
        full_render()
