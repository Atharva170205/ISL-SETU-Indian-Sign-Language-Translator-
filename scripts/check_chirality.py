"""Checks whether different signers' hands show opposite chirality
(mirrored thumb/pinky layout) after our normalization."""
import h5py, numpy as np, glob, os
from collections import defaultdict
import sys
sys.path.insert(0, os.path.abspath("."))
from core.preprocess import canonicalize_slots, normalize_frame

RAW = r"D:\ISL_Setu\data\raw_landmarks\Landmarks\MediaPipe"
THUMB_TIP, PINKY_TIP = 4, 20

signer_scores = defaultdict(list)

files = glob.glob(os.path.join(RAW, "*", "*.h5"))
for path in files[::3]:          # sample for speed
    signer = os.path.basename(os.path.dirname(path))
    with h5py.File(path, "r") as f:
        raw = f["intermediate"][()]
    for frame in raw:
        norm = normalize_frame(frame)
        hand = norm[0]
        if not np.any(hand != 0):
            continue
        # thumb x minus pinky x, in the wrist-relative frame
        diff = hand[THUMB_TIP, 0] - hand[PINKY_TIP, 0]
        signer_scores[signer].append(diff)

print(f"{'Signer':20s} {'mean(thumb_x - pinky_x)':25s} {'n_frames'}")
for signer in sorted(signer_scores):
    vals = signer_scores[signer]
    print(f"{signer:20s} {np.mean(vals):+.4f}                    {len(vals)}")