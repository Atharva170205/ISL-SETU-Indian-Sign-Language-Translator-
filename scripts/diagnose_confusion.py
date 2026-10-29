"""
scripts/diagnose_confusion.py — Confusion matrix diagnostic for specific
problem words (I, Now, Today, Tomorrow, Come) and overall worst pairs.
"""
import numpy as np
import torch
import sys, os
sys.path.insert(0, os.path.abspath("."))
from core.model import SignClassifier
from collections import defaultdict

DATA = r"D:\ISL_Setu\data\processed\dataset.npz"
MODEL_PATH = r"D:\ISL_Setu\models\production.pt"
VAL_FRACTION = 0.1

torch.manual_seed(42)
np.random.seed(42)
device = "cuda" if torch.cuda.is_available() else "cpu"

d = np.load(DATA, allow_pickle=True)
X, y, lengths, vocab = d["X"], d["y"], d["lengths"], d["vocab"]
vocab = [str(v) for v in vocab]

X_mirror = X.copy()
X_mirror[..., 0::3] *= -1
X_all = np.concatenate([X, X_mirror], axis=0)
y_all = np.concatenate([y, y], axis=0)
lengths_all = np.concatenate([lengths, lengths], axis=0)

n = len(y_all)
idx = np.random.permutation(n)
n_val = int(n * VAL_FRACTION)
val_idx = idx[:n_val]

checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=False)
model = SignClassifier(**checkpoint["config"]).to(device)
model.load_state_dict(checkpoint["model_state"])
model.eval()

Xv = torch.tensor(X_all[val_idx]).to(device)
Lv = torch.tensor(lengths_all[val_idx]).to(device)
yv = y_all[val_idx]

with torch.no_grad():
    preds = model(Xv, Lv).argmax(1).cpu().numpy()

# Confusion matrix (full)
num_classes = len(vocab)
conf = np.zeros((num_classes, num_classes), dtype=int)
for t, p in zip(yv, preds):
    conf[t, p] += 1

# Focus words
focus_words = ["I", "Now", "Today", "Tomorrow", "Come"]
print("=" * 70)
print("FOCUS WORD CONFUSION (rows=true label, cols=predicted)")
print("=" * 70)
idxs = [vocab.index(w) for w in focus_words]
header = "TRUE\\PRED".ljust(12) + "".join(w[:8].ljust(10) for w in focus_words)
print(header)
for i in idxs:
    row = vocab[i].ljust(12)
    for j in idxs:
        row += str(conf[i, j]).ljust(10)
    total = conf[i].sum()
    acc = conf[i, i] / total if total > 0 else 0
    row += f"  (n={total}, acc={acc:.2f})"
    print(row)

print("\n" + "=" * 70)
print("TOP MISPREDICTIONS FOR EACH FOCUS WORD (where it goes wrong)")
print("=" * 70)
for i in idxs:
    total = conf[i].sum()
    if total == 0:
        continue
    wrong = [(vocab[j], conf[i, j]) for j in range(num_classes) if j != i and conf[i, j] > 0]
    wrong.sort(key=lambda x: -x[1])
    print(f"\n{vocab[i]} (n={total}, correct={conf[i,i]}):")
    for w, c in wrong[:5]:
        print(f"    -> predicted as '{w}': {c} times ({c/total:.0%})")

print("\n" + "=" * 70)
print("OVERALL TOP 15 CONFUSED PAIRS (across all 50 classes)")
print("=" * 70)
pairs = []
for i in range(num_classes):
    for j in range(num_classes):
        if i != j and conf[i, j] > 0:
            pairs.append((vocab[i], vocab[j], conf[i, j]))
pairs.sort(key=lambda x: -x[2])
for true_w, pred_w, count in pairs[:15]:
    print(f"  {true_w:15s} -> {pred_w:15s}  ({count} times)")

print("\n" + "=" * 70)
print("WHICH WORDS DO OTHERS GET PREDICTED AS MOST OFTEN (dustbin check)")
print("=" * 70)
pred_counts = defaultdict(int)
for i in range(num_classes):
    for j in range(num_classes):
        if i != j:
            pred_counts[vocab[j]] += conf[i, j]
dustbin_ranked = sorted(pred_counts.items(), key=lambda x: -x[1])
for word, count in dustbin_ranked[:10]:
    print(f"  {word:15s} absorbed {count} wrong predictions from other classes")