"""scripts/evaluate.py — confusion matrix + per-class accuracy on unseen signers."""
import json, os, sys
import numpy as np
import torch
from collections import defaultdict

sys.path.insert(0, os.path.abspath("."))
from core.model import SignClassifier

DATA = r"D:\ISL_Setu\data\processed\dataset.npz"
MANIFEST = r"D:\ISL_Setu\data\processed\manifest.json"
MODEL_PATH = r"D:\ISL_Setu\models\best.pt"

TEST_SIGNERS = {f"ISL_DATA_USER{i:03d}" for i in range(13, 16)}

device = "cuda" if torch.cuda.is_available() else "cpu"
ckpt = torch.load(MODEL_PATH, map_location=device, weights_only=False)
vocab = ckpt["vocab"]
model = SignClassifier(**ckpt["config"]).to(device)
model.load_state_dict(ckpt["model_state"])
model.eval()

d = np.load(DATA, allow_pickle=True)
X, y, lengths = d["X"], d["y"], d["lengths"]
signers = np.array([r["signer"] for r in json.load(open(MANIFEST))])
test_mask = np.isin(signers, list(TEST_SIGNERS))
Xte, yte, lte, ste = X[test_mask], y[test_mask], lengths[test_mask], signers[test_mask]

with torch.no_grad():
    xb = torch.tensor(Xte).to(device)
    lb = torch.tensor(lte).to(device)
    preds = model(xb, lb).argmax(1).cpu().numpy()

# per-class accuracy
per_class = defaultdict(lambda: [0, 0])
confusions = defaultdict(lambda: defaultdict(int))
for true, pred in zip(yte, preds):
    per_class[true][1] += 1
    if true == pred:
        per_class[true][0] += 1
    else:
        confusions[vocab[true]][vocab[pred]] += 1

print("=== Per-class accuracy (unseen signers) ===")
rows = []
for idx, word in enumerate(vocab):
    correct, total = per_class[idx]
    acc = correct / total if total else 0
    rows.append((acc, word, correct, total))
for acc, word, c, t in sorted(rows):
    print(f"{word:12s} {acc:.2f}  ({c}/{t})")

print("\n=== Top confusions (true -> predicted : count) ===")
flat = []
for true_word, preds_dict in confusions.items():
    for pred_word, cnt in preds_dict.items():
        flat.append((cnt, true_word, pred_word))
for cnt, t, p in sorted(flat, reverse=True)[:20]:
    print(f"{t:12s} -> {p:12s} : {cnt}")

# per-signer accuracy
print("\n=== Per-signer accuracy ===")
for signer in sorted(TEST_SIGNERS):
    mask = ste == signer
    acc = (preds[mask] == yte[mask]).mean()
    print(f"{signer}: {acc:.3f} ({mask.sum()} clips)")