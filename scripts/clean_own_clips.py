"""
clean_own_clips.py — Deletes clips with low hand-detection or bad shape,
then reports exactly how many more clips each word needs.

Run:  python scripts\clean_own_clips.py          (dry run, lists what WOULD be deleted)
Run:  python scripts\clean_own_clips.py --apply   (actually deletes)
"""

import os
import re
import sys
import glob
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
LOW_DETECTION_THRESHOLD = 0.15


def hand_detection_fraction(data):
    frame_has_hand = np.any(np.abs(data) > 1e-6, axis=(1, 2, 3))
    return frame_has_hand.mean() if len(frame_has_hand) > 0 else 0.0


def main():
    apply = "--apply" in sys.argv

    all_files = glob.glob(os.path.join(OWN_DIR, "*.h5"))
    by_word = {}
    for f in all_files:
        base = os.path.basename(f)
        m = re.match(r"^(.+?)__.+?__clip\d+\.h5$", base)
        if m:
            by_word.setdefault(m.group(1), []).append(f)

    to_delete = []

    for word, files in by_word.items():
        for f in files:
            try:
                with h5py.File(f, "r") as h5f:
                    data = h5f["intermediate"][:]
            except Exception:
                to_delete.append(f)
                continue
            if data.ndim != 4 or data.shape[1:] != (2, 21, 3) or data.shape[0] < MIN_FRAMES:
                to_delete.append(f)
                continue
            if hand_detection_fraction(data) < LOW_DETECTION_THRESHOLD:
                to_delete.append(f)

    print(f"{'ACTION':8s} {os.path.basename(OWN_DIR)}")
    for f in to_delete:
        print(f"  {'DELETE' if apply else '[DRY]':8s} {os.path.basename(f)}")

    if apply:
        for f in to_delete:
            os.remove(f)
        print(f"\nDeleted {len(to_delete)} bad clip(s).")
    else:
        print(f"\n{len(to_delete)} clip(s) would be deleted. Re-run with --apply to actually delete.")

    # Recompute gaps after (simulated) deletion
    deleted_set = set(to_delete) if apply else set(to_delete)
    print("\n" + "=" * 60)
    print("REMAINING GAP PER WORD (after cleanup):")
    print("-" * 60)
    needed = {}
    for word, target in TARGET_CLIPS.items():
        files = by_word.get(word, [])
        good_count = len([f for f in files if f not in deleted_set])
        gap = max(0, target - good_count)
        if gap > 0:
            needed[word] = gap
            print(f"  {word:15s} good={good_count:2d}  target={target:2d}  NEED {gap} MORE")
    print("=" * 60)
    if needed:
        print("\nSuggested re-record command:")
        print("  python scripts\\record_own.py " + " ".join(needed.keys()))
    else:
        print("\nAll words at target. Ready for build_dataset.py.")


if __name__ == "__main__":
    main()