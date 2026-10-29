"""scripts/train_kfold.py — rotate held-out signers, check if the gap is signer-specific."""
import json, os, sys
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

sys.path.insert(0, os.path.abspath("."))
from core.model import SignClassifier

DATA = r"D:\ISL_Setu\data\processed\dataset.npz"
MANIFEST = r"D:\ISL_Setu\data\processed\manifest.json"

ALL_SIGNERS = [f"ISL_DATA_USER{i:03d}" for i in range(1, 16)]
# 5 folds of 3 held-out signers each, covering all 15
FOLDS = [ALL_SIGNERS[i:i+3] for i in range(0, 15, 3)]

EPOCHS = 20
BATCH = 64
LR = 1e-3

d = np.load(DATA, allow_pickle=True)
X, y, lengths, vocab = d["X"], d["y"], d["lengths"], d["vocab"]
vocab = [str(v) for v in vocab]
signers = np.array([r["signer"] for r in json.load(open(MANIFEST))])

device = "cuda" if torch.cuda.is_available() else "cpu"

def make_loader(Xa, ya, la, shuffle):
    ds = TensorDataset(torch.tensor(Xa), torch.tensor(la), torch.tensor(ya))
    return DataLoader(ds, batch_size=BATCH, shuffle=shuffle)

for fold_idx, test_signers in enumerate(FOLDS):
    train_signers = [s for s in ALL_SIGNERS if s not in test_signers]
    train_mask = np.isin(signers, train_signers)
    test_mask = np.isin(signers, test_signers)

    Xtr, ytr, ltr = X[train_mask], y[train_mask], lengths[train_mask]
    Xte, yte, lte = X[test_mask], y[test_mask], lengths[test_mask]
    ste = signers[test_mask]

    model = SignClassifier(num_classes=len(vocab)).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()
    train_loader = make_loader(Xtr, ytr, ltr, True)

    for epoch in range(EPOCHS):
        model.train()
        for xb, lb, yb in train_loader:
            xb, lb, yb = xb.to(device), lb.to(device), yb.to(device)
            opt.zero_grad()
            loss = criterion(model(xb, lb), yb)
            loss.backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        xb = torch.tensor(Xte).to(device)
        lb = torch.tensor(lte).to(device)
        preds = model(xb, lb).argmax(1).cpu().numpy()

    overall_acc = (preds == yte).mean()
    print(f"\n=== Fold {fold_idx+1}: held out {test_signers} ===")
    print(f"Overall: {overall_acc:.3f}")
    for s in test_signers:
        mask = ste == s
        acc = (preds[mask] == yte[mask]).mean()
        print(f"  {s}: {acc:.3f} ({mask.sum()} clips)")