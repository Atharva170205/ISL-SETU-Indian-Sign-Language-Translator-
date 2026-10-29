"""h5 clips -> padded numpy tensors + manifest for training."""
import h5py, numpy as np, glob, os, json, sys
sys.path.insert(0, os.path.abspath("."))
from core.preprocess import sequence_to_features

RAW = r"D:\ISL_Setu\data\raw_landmarks\Landmarks\MediaPipe"
OUT = r"D:\ISL_Setu\data\processed"

VOCAB = [
    "I", "You", "He", "She", "We", "They", "Mother", "Father", "Friend",
    "Teacher", "Student", "School", "College", "Home", "Hospital", "Doctor",
    "Police", "Water", "Food", "Help", "Come", "Go", "Stop", "Give", "Take",
    "Eat", "Drink", "Sleep", "Work", "Study", "Learn", "Want", "Need", "Like",
    "Know", "Understand", "What", "Where", "Who", "Why", "How", "Yes", "No",
    "Please", "Thankyou", "Sorry", "Hello", "Today", "Tomorrow", "Now"
]
word2idx = {w: i for i, w in enumerate(VOCAB)}

AUG_PER_OWN_CLIP = 3  # extra synthetic variants generated per own-recorded clip


def augment_own_clip(seq, num_augments=AUG_PER_OWN_CLIP):
    """seq: (T, 2, 21, 3) raw landmarks. Returns list of augmented variants
    (small coordinate jitter + random time-stretch), to compensate for
    single-signer narrowness in self-recorded clips."""
    augmented = []
    for _ in range(num_augments):
        aug = seq.copy()
        noise = np.random.normal(0, 0.01, aug.shape).astype(np.float32)
        aug = aug + noise
        T = aug.shape[0]
        stretch_factor = np.random.uniform(0.85, 1.15)
        new_T = max(5, int(T * stretch_factor))
        indices = np.linspace(0, T - 1, new_T).astype(int)
        aug = aug[indices]
        augmented.append(aug)
    return augmented


os.makedirs(OUT, exist_ok=True)
records, all_feats, max_len = [], [], 0
own_clip_count, isl500_clip_count, own_aug_count = 0, 0, 0

for path in glob.glob(os.path.join(RAW, "*", "*.h5")):
    fname = os.path.basename(path)
    word = fname.split("__")[0]          # <-- FIXED: robust to any session-tag naming
    if word not in word2idx:
        continue
    signer = path.split(os.sep)[-2]      # ISL_DATA_USER001 or ISL_DATA_OWN001
    is_own = "OWN" in signer.upper()

    with h5py.File(path, "r") as f:
        raw = f["intermediate"][()]      # (T, 2, 21, 3)

    feats = sequence_to_features(raw)    # (T, 126)
    all_feats.append(feats.astype(np.float32))
    max_len = max(max_len, len(feats))
    records.append({
        "word": word, "label": word2idx[word],
        "signer": signer, "n_frames": len(feats), "file": fname,
    })
    if is_own:
        own_clip_count += 1
    else:
        isl500_clip_count += 1

    # Extra synthetic augmentation only for own-recorded clips (single-signer,
    # needs more variation than ISL500's natural 15-signer diversity provides)
    if is_own:
        for k, aug_raw in enumerate(augment_own_clip(raw)):
            aug_feats = sequence_to_features(aug_raw)
            all_feats.append(aug_feats.astype(np.float32))
            max_len = max(max_len, len(aug_feats))
            records.append({
                "word": word, "label": word2idx[word],
                "signer": signer, "n_frames": len(aug_feats),
                "file": f"{fname}__aug{k}",
            })
            own_aug_count += 1

# pad to max_len
X = np.zeros((len(all_feats), max_len, all_feats[0].shape[1]), dtype=np.float32)
lengths = np.zeros(len(all_feats), dtype=np.int64)
for i, f in enumerate(all_feats):
    X[i, :len(f)] = f
    lengths[i] = len(f)

y = np.array([r["label"] for r in records], dtype=np.int64)

np.savez_compressed(
    os.path.join(OUT, "dataset.npz"),
    X=X, y=y, lengths=lengths, vocab=np.array(VOCAB),
)
with open(os.path.join(OUT, "manifest.json"), "w") as f:
    json.dump(records, f, indent=2)

print(f"Saved {len(records)} clips, max_len={max_len}, vocab={len(VOCAB)}")
print(f"X shape: {X.shape}")
print(f"  ISL500 clips: {isl500_clip_count}")
print(f"  Own clips (real): {own_clip_count}")
print(f"  Own clips (augmented): {own_aug_count}")

# Per-word breakdown, sorted ascending by count (spot the thin classes)
from collections import Counter
word_counts = Counter(r["word"] for r in records)
print("\nPer-word clip counts (post-augmentation):")
for w in sorted(VOCAB, key=lambda w: word_counts.get(w, 0)):
    print(f"  {w:15s} {word_counts.get(w, 0)}")