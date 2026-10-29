"""
verify_own_clips.py — Sanity check for own-recorded .h5 clips before retraining.

Checks:
  - Per-word clip count vs target
  - Frame count stats (too short / too long clips)
  - Hand-detection fraction (flags clips where hands were barely detected)
  - File integrity (readable, correct shape)

Run:  python scripts\verify_own_clips.py
"""

import os
import glob
import re
import h5py
import numpy as np

OWN_DIR = os.path.join("data", "raw_landmarks", "Landmarks", "MediaPipe", "ISL_DATA_OWN001")

TARGET_CLIPS = {
    "Eat": 18, "Food": 18, "Please": 18, "Thankyou": 18,
    "College": 18, "Home": 18, "Hospital": 18, "Come": 18, "Stop": 18,
    "Take": 18, "Sleep": 18, "Study": 18, "Learn": 18, "Want": 18,
    "Need": 18, "Like": 18, "Know": 18, "Understand": 18, "Who": 18,
    "How": 18, "Sorry": 18, "Now": 18,
    "Water": 9, "Drink": 9, "Give": 9, "Doctor": 9, "Why": 9,
    "What": 9, "Student": 9,
}

MIN_FRAMES = 5
MAX_FRAMES = 300
LOW_DETECTION_WARN = 0.15  # fraction of frames with at least one hand detected


def hand_detection_fraction(data):
    # data: (T, 2, 21, 3)
    frame_has_hand = np.any(np.abs(data) > 1e-6, axis=(1, 2, 3))
    return frame_has_hand.mean() if len(frame_has_hand) > 0 else 0.0


def main():
    if not os.path.isdir(OWN_DIR):
        print(f"ERROR: {OWN_DIR} does not exist. Nothing recorded yet.")
        return

    all_files = glob.glob(os.path.join(OWN_DIR, "*.h5"))
    print(f"Found {len(all_files)} total .h5 files in {OWN_DIR}\n")

    by_word = {}
    for f in all_files:
        base = os.path.basename(f)
        m = re.match(r"^(.+?)__.+?__clip\d+\.h5$", base)
        if not m:
            print(f"  [!] Filename doesn't match pattern: {base}")
            continue
        word = m.group(1)
        by_word.setdefault(word, []).append(f)

    problems = []
    print(f"{'WORD':15s} {'COUNT':>6s} {'TARGET':>7s} {'STATUS':>8s}  NOTES")
    print("-" * 80)

    for word in sorted(set(list(TARGET_CLIPS.keys()) + list(by_word.keys()))):
        files = by_word.get(word, [])
        target = TARGET_CLIPS.get(word, "?")
        count = len(files)

        notes = []
        for f in files:
            try:
                with h5py.File(f, "r") as h5f:
                    data = h5f["intermediate"][:]
            except Exception as e:
                notes.append(f"UNREADABLE({os.path.basename(f)}): {e}")
                problems.append(f)
                continue

            if data.ndim != 4 or data.shape[1:] != (2, 21, 3):
                notes.append(f"BAD SHAPE {data.shape} in {os.path.basename(f)}")
                problems.append(f)
                continue

            T = data.shape[0]
            if T < MIN_FRAMES:
                notes.append(f"TOO SHORT ({T}f) {os.path.basename(f)}")
                problems.append(f)
            elif T > MAX_FRAMES:
                notes.append(f"TOO LONG ({T}f) {os.path.basename(f)}")

            frac = hand_detection_fraction(data)
            if frac < LOW_DETECTION_WARN:
                notes.append(f"LOW DETECTION ({frac:.0%}) {os.path.basename(f)}")
                problems.append(f)

        status = "OK" if (isinstance(target, int) and count >= target) else "SHORT"
        if word not in TARGET_CLIPS:
            status = "EXTRA?"

        note_str = "; ".join(notes[:3]) + (" ..." if len(notes) > 3 else "")
        print(f"{word:15s} {count:>6d} {str(target):>7s} {status:>8s}  {note_str}")

    print("\n" + "=" * 80)
    if problems:
        print(f"{len(set(problems))} clip(s) flagged with issues (see NOTES above). "
              f"Consider re-recording these specific clips with R/retake or manual delete.")
    else:
        print("No flagged clips. Data looks clean and ready for build_dataset.py.")
    print("=" * 80)


if __name__ == "__main__":
    main()