"""core/preprocess.py — single source of truth for landmark normalization."""
import numpy as np

N_HANDS = 2
N_LANDMARKS = 21
N_COORDS = 3
FEATURE_DIM = N_HANDS * N_LANDMARKS * N_COORDS   # 126

WRIST = 0
MIDDLE_MCP = 9


def _hand_present(hand: np.ndarray) -> bool:
    return np.any(hand != 0)


def canonicalize_slots(frame: np.ndarray) -> np.ndarray:
    """(2, 21, 3) raw -> (2, 21, 3) with slots reassigned by screen position.
    0 hands: both zero. 1 hand: always slot 0. 2 hands: sorted by wrist x
    (smaller x -> slot 0, larger x -> slot 1). Deterministic, camera-direction
    independent as long as the SAME convention is used live."""
    h0, h1 = frame[0], frame[1]
    p0, p1 = _hand_present(h0), _hand_present(h1)

    if not p0 and not p1:
        return np.zeros_like(frame)
    if p0 and not p1:
        return np.stack([h0, np.zeros_like(h1)])
    if p1 and not p0:
        return np.stack([h1, np.zeros_like(h0)])

    # both present -> sort by wrist x
    if h0[WRIST, 0] <= h1[WRIST, 0]:
        return np.stack([h0, h1])
    return np.stack([h1, h0])


def normalize_frame(frame: np.ndarray) -> np.ndarray:
    """(2, 21, 3) -> (2, 21, 3), slot-canonicalized, wrist-relative, scaled."""
    frame = canonicalize_slots(frame)
    out = np.zeros_like(frame)
    for h in range(frame.shape[0]):
        hand = frame[h]
        if not _hand_present(hand):
            continue
        wrist = hand[WRIST, :2].copy()
        centered = hand.copy()
        centered[:, :2] -= wrist
        span = np.linalg.norm(hand[MIDDLE_MCP, :2] - hand[WRIST, :2])
        scale = span if span > 1e-6 else 1.0
        centered /= scale
        out[h] = centered
    return out


def frame_to_feature(frame: np.ndarray) -> np.ndarray:
    return normalize_frame(frame).reshape(-1)


def sequence_to_features(seq: np.ndarray) -> np.ndarray:
    return np.stack([frame_to_feature(f) for f in seq])