"""Assemble the presentation video from the recorded screen clips, the slides and the narration.

    python make_video.py                       # silent preview, each part at its target length
    python make_video.py --audio audio/        # final video: each part stretched/trimmed to part01..part12 audio

Inputs (all under recording/, which is git-ignored):
    recording/*.webm            screen recordings of each demo part (1920x1080)
    recording/slides/slide-NN.png   slides rendered from HelpDesk-Presentation.pdf at 192 dpi
Output: recording/HelpDesk-Presentation-preview.mp4 or recording/HelpDesk-Presentation.mp4

Each part's footage plays at natural speed when it fits the narration; if the footage is longer it is
sped up evenly, and if it is shorter the last frame is held, so the picture always matches the voice.
"""
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = "ffmpeg"

HERE = Path(__file__).resolve().parent
REC = HERE / "recording"
SLIDES = REC / "slides"

def slide(n, secs):
    return {"img": SLIDES / f"slide-{n:02d}.png", "dur": secs}

def clip(name, start=0.0, end=None, speed=1.0):
    return {"vid": REC / name, "start": start, "end": end, "speed": speed}

# Visuals per script part, plus the target length (seconds) used for the silent preview.
PARTS = [
    (1,  "Introduction",          45,  [slide(1, 15), slide(2, 30)]),
    (2,  "Architecture",          60,  [slide(3, 38), slide(4, 22)]),
    (3,  "The application",       90,  [clip("p03-app.webm", 0.5)]),
    (4,  "Testing",               45,  [slide(6, 6), clip("p04-tests.webm", 0.5)]),
    (5,  "Docker",                45,  [slide(7, 6), clip("p05-docker.webm", 0.5)]),
    (6,  "CI/CD live change",    120,  [clip("p06a-commit.webm", 0.5), clip("p06b-pipeline.webm", 1.0, None, 3.0), slide(8, 6)]),
    (7,  "Trivy and GHCR",        30,  [slide(9, 8), clip("p07-ghcr.webm", 0.5)]),
    (8,  "Terraform",             75,  [clip("p08a-terraform.webm", 0.5), clip("p08b-console.webm", 36.0, None, 1.4)]),
    (9,  "Kubernetes and Helm",   75,  [clip("p09a-kubectl.webm", 0.5), clip("p09b-live-change.webm", 0.5)]),
    (10, "Autoscaling and monitoring", 90, [clip("p10a-hpa.webm", 0.5),
                                       # /metrics, then Prometheus and Grafana with their loading screens cut out
                                       clip("p10b-monitoring.webm", 0.5, 7.5), clip("p10b-monitoring.webm", 13.0, 18.0), clip("p10b-monitoring.webm", 31.0)]),
    (11, "Challenges",            60,  [slide(13, 60)]),
    (12, "Cleanup and thank you", 30,  [slide(14, 30)]),
]

def run(args):
    r = subprocess.run([FFMPEG, "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed: {' '.join(map(str, args))[:300]}\n{r.stderr[-1500:]}")

def duration(path):
    r = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    sys.exit(f"cannot read duration of {path}")

NORM = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0F3B3A,setsar=1,fps=30,format=yuv420p"

def render_piece(p, out):
    """Normalise one slide or clip to 1920x1080/30fps H.264 at its natural (or pre-set) speed."""
    if "img" in p:
        run(["-loop", "1", "-t", str(p["dur"]), "-i", p["img"], "-vf", NORM, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out])
    else:
        trim = ["-ss", str(p["start"])] + (["-to", str(p["end"])] if p["end"] else [])
        vf = f"setpts=PTS/{p['speed']}," + NORM
        run([*trim, "-i", p["vid"], "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out])

def concat(files, out, tmp):
    lst = Path(tmp) / f"{Path(out).stem}.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", help="folder with part01..part12 audio files (any format ffmpeg reads)")
    ap.add_argument("--max-speed", type=float, default=2.5, help="cap on how much a part's footage is sped up")
    a = ap.parse_args()
    final = REC / ("HelpDesk-Presentation.mp4" if a.audio else "HelpDesk-Presentation-preview.mp4")
    report = []
    with tempfile.TemporaryDirectory() as tmp:
        part_files = []
        for n, title, target, pieces in PARTS:
            audio = None
            if a.audio:
                cands = sorted(Path(a.audio).glob(f"part{n:02d}.*"))
                if not cands:
                    sys.exit(f"missing narration for part {n}: expected {a.audio}/part{n:02d}.<m4a|mp3|wav|…>")
                audio = cands[0]
            want = duration(audio) + 0.6 if audio else float(target)
            raw = []
            for i, p in enumerate(pieces):
                f = Path(tmp) / f"p{n:02d}_{i}.mp4"
                render_piece(p, f)
                raw.append(f)
            joined = Path(tmp) / f"p{n:02d}_joined.mp4"
            concat(raw, joined, tmp)
            have = duration(joined)
            speed = min(max(have / want, 1.0), a.max_speed)
            vf = f"setpts=PTS/{speed:.4f},tpad=stop_mode=clone:stop_duration={max(want - have / speed, 0) + 0.5:.2f},trim=duration={want:.2f},fps=30,format=yuv420p"
            out = Path(tmp) / f"part{n:02d}.mp4"
            if audio:
                run(["-i", joined, "-i", audio, "-filter_complex", f"[0:v]{vf}[v];[1:a]aresample=48000,apad=whole_dur={want:.2f}[a]",
                     "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                     "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-t", f"{want:.2f}", out])
            else:
                run(["-i", joined, "-f", "lavfi", "-t", f"{want:.2f}", "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf,
                     "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-t", f"{want:.2f}", out])
            part_files.append(out)
            report.append(f"part {n:2d} {title:<28} footage {have:6.1f}s  narration {want:6.1f}s  speed x{speed:.2f}")
            print(report[-1], flush=True)
        concat(part_files, final, tmp)
    print(f"\n{final}  ({duration(final) / 60:.1f} min)")

if __name__ == "__main__":
    main()
