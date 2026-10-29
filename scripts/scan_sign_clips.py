"""
Scans all exported sign clips in frontend/public/signs/*.json
and flags words with potential quality issues:
  - one hand completely empty for the entire clip (likely broken two-handed sign)
  - clip has very few total frames with any hand present (too short to be a real sign)
  - both hands completely empty for the entire clip (nothing exported at all)
"""
import json
from pathlib import Path

SIGNS_DIR = Path("frontend/public/signs")

def empty(h):
    return all(p[0] == 0 and p[1] == 0 and p[2] == 0 for p in h)

def analyze(path):
    data = json.loads(path.read_text())
    frames = data["frames"]
    h0_present = sum(1 for f in frames if not empty(f[0]))
    h1_present = sum(1 for f in frames if not empty(f[1]))
    total = len(frames)
    return total, h0_present, h1_present

def main():
    results = []
    for path in sorted(SIGNS_DIR.glob("*.json")):
        word = path.stem
        total, h0, h1 = analyze(path)
        flags = []

        if h0 == 0 and h1 == 0:
            flags.append("NO_HANDS_AT_ALL")
        elif h0 == 0 or h1 == 0:
            # one hand never appears in the whole clip
            flags.append("ONE_HAND_MISSING_ENTIRE_CLIP")

        active_frames = max(h0, h1)
        if active_frames < 8:
            flags.append(f"TOO_SHORT(active_frames={active_frames})")

        results.append((word, total, h0, h1, flags))

    print(f"{'WORD':<15}{'TOTAL':<8}{'H0':<6}{'H1':<6}FLAGS")
    flagged_count = 0
    for word, total, h0, h1, flags in results:
        if flags:
            flagged_count += 1
        flag_str = ", ".join(flags)
        print(f"{word:<15}{total:<8}{h0:<6}{h1:<6}{flag_str}")

    print(f"\n{flagged_count} / {len(results)} words flagged for review.")

if __name__ == "__main__":
    main()