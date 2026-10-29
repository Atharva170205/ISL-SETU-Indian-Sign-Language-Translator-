import h5py, numpy as np, glob, os
from collections import defaultdict

RAW = r"D:\ISL_Setu\data\raw_landmarks\Landmarks\MediaPipe"
WRIST, MIDDLE_MCP = 0, 9

stats = defaultdict(lambda: {"n_clips": 0, "frame_counts": [], "spans": [], "two_hand_frac": []})

files = glob.glob(os.path.join(RAW, "*", "*.h5"))
for path in files:
    signer = os.path.basename(os.path.dirname(path))
    with h5py.File(path, "r") as f:
        raw = f["intermediate"][()]
    T = raw.shape[0]
    p0 = np.any(raw[:, 0] != 0, axis=(1, 2))
    p1 = np.any(raw[:, 1] != 0, axis=(1, 2))
    both_frac = (p0 & p1).sum() / max(T, 1)

    spans = []
    for h in range(2):
        for t in range(T):
            hand = raw[t, h]
            if np.any(hand != 0):
                span = np.linalg.norm(hand[MIDDLE_MCP, :2] - hand[WRIST, :2])
                spans.append(span)

    s = stats[signer]
    s["n_clips"] += 1
    s["frame_counts"].append(T)
    s["spans"].extend(spans)
    s["two_hand_frac"].append(both_frac)

print(f"{'Signer':20s} {'n_clips':8s} {'avg_frames':11s} {'avg_hand_span':14s} {'two_hand_frac'}")
for signer in sorted(stats):
    s = stats[signer]
    print(f"{signer:20s} {s['n_clips']:<8d} "
          f"{np.mean(s['frame_counts']):<11.1f} "
          f"{np.mean(s['spans']):<14.4f} "
          f"{np.mean(s['two_hand_frac']):.3f}")