"""
Export one canonical landmark clip per vocabulary word for the
Text -> Sign (avatar replay) feature.

Scans all signer folders (ISL_DATA_USER001..015, ISL_DATA_OWN001) for the
FIRST matching .h5 file per word (case-insensitive match on the part of the
filename before the first "__"), and exports it as a JSON file the frontend
can replay on a canvas.

Output: frontend/public/signs/<Word>.json
Format: { "word": "College", "num_frames": 42, "frames": [ [[x,y,z]*21, [x,y,z]*21], ... ] }
  - frames is a list of per-frame entries
  - each frame entry has up to 2 hands, each hand has 21 [x,y,z] landmarks
  - x,y are normalized 0-1 (same convention as MediaPipe tasks-vision output),
    matching the live camera overlay drawing code exactly.
"""

import h5py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIAPIPE_DIR = ROOT / "data" / "raw_landmarks" / "Landmarks" / "MediaPipe"
OUT_DIR = ROOT / "frontend" / "public" / "signs"

VOCAB = [
    "I", "You", "He", "She", "We", "They", "Mother", "Father", "Friend", "Teacher",
    "Student", "School", "College", "Home", "Hospital", "Doctor", "Police", "Water",
    "Food", "Help", "Come", "Go", "Stop", "Give", "Take", "Eat", "Drink", "Sleep",
    "Work", "Study", "Learn", "Want", "Need", "Like", "Know", "Understand", "What",
    "Where", "Who", "Why", "How", "Yes", "No", "Please", "Thankyou", "Sorry",
    "Hello", "Today", "Tomorrow", "Now",
]


def find_clip_for_word(word):
    """Search all signer folders for the first .h5 file matching this word."""
    signer_folders = sorted(MEDIAPIPE_DIR.glob("ISL_DATA_*"))
    for folder in signer_folders:
        for h5_file in sorted(folder.glob("*.h5")):
            fname_word = h5_file.name.split("__")[0]
            if fname_word.lower() == word.lower():
                return h5_file
    return None


def export_word(word, h5_path):
    with h5py.File(h5_path, "r") as f:
        data = f["intermediate"][:]  # shape (num_frames, 2, 21, 3)

    frames = data.tolist()  # nested python lists, JSON-serializable

    out = {
        "word": word,
        "source_file": h5_path.name,
        "num_frames": len(frames),
        "frames": frames,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{word}.json"
    with open(out_path, "w") as f:
        json.dump(out, f)

    return out_path, len(frames)


def main():
    found = []
    missing = []

    for word in VOCAB:
        h5_path = find_clip_for_word(word)
        if h5_path is None:
            missing.append(word)
            continue
        out_path, num_frames = export_word(word, h5_path)
        found.append((word, h5_path.name, num_frames))
        print(f"[OK] {word:12s} <- {h5_path.name:40s} ({num_frames} frames)")

    print()
    print(f"Exported {len(found)}/{len(VOCAB)} words.")
    if missing:
        print(f"MISSING clips for: {missing}")


if __name__ == "__main__":
    main()