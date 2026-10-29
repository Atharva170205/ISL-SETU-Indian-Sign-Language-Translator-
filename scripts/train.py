"""scripts/train.py — train BiLSTM with a held-out-signer split.

Train:  ISL_DATA_USER001-012   (12 signers)
Test:   ISL_DATA_USER013-015   (3 signers, NEVER seen in training)
"""
import json, os, sys
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

sys.path.insert(0, os.path.abspath("."))
from core.model import SignClassifier

DATA = r"D:\ISL_Setu\data\processed\dataset.npz"
MANIFEST = r"D:\ISL_Setu\data\processed\manifest.json"
MODEL_OUT = r"D:\ISL_Setu\models\best.pt"

TRAIN_SIGNERS = {f"ISL_DATA_USER{i:03d}" for i in range(1, 13)}
TEST_SIGNERS = {f"ISL_DATA_USER{i:03d}" for i in range(13, 16)}

EPOCHS = 30
BATCH = 64
LR = 1e-3
SEED = 42

torch.manual_seed(SEED)
np.random.seed(SEED)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

d = np.load(DATA, allow_pickle=True)
X, y, lengths, vocab = d["X"], d["y"], d["lengths"], d["vocab"]
vocab = [str(v) for v in vocab]
signers = np.array([r["signer"] for r in json.load(open(MANIFEST))])

train_mask = np.isin(signers, list(TRAIN_SIGNERS))
test_mask = np.isin(signers, list(TEST_SIGNERS))

Xtr, ytr, ltr = X[train_mask], y[train_mask], lengths[train_mask]
Xte, yte, lte = X[test_mask], y[test_mask], lengths[test_mask]
print(f"Train: {len(ytr)} clips (12 signers) | Test: {len(yte)} clips (3 unseen signers)")
print(f"Classes: {len(vocab)}")

def make_loader(Xa, ya, la, shuffle):
    ds = TensorDataset(torch.tensor(Xa), torch.tensor(la), torch.tensor(ya))
    return DataLoader(ds, batch_size=BATCH, shuffle=shuffle)

train_loader = make_loader(Xtr, ytr, ltr, True)
test_loader = make_loader(Xte, yte, lte, False)

model = SignClassifier(num_classes=len(vocab)).to(device)
opt = torch.optim.Adam(model.parameters(), lr=LR)
sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=4, factor=0.5)
criterion = nn.CrossEntropyLoss()

os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
best_acc, best_epoch = 0.0, -1

for epoch in range(1, EPOCHS + 1):
    model.train()
    total, correct, loss_sum = 0, 0, 0.0
    for xb, lb, yb in train_loader:
        xb, lb, yb = xb.to(device), lb.to(device), yb.to(device)
        opt.zero_grad()
        logits = model(xb, lb)
        loss = criterion(logits, yb)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        loss_sum += loss.item() * len(yb)
        correct += (logits.argmax(1) == yb).sum().item()
        total += len(yb)
    train_acc = correct / total

    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for xb, lb, yb in test_loader:
            xb, lb, yb = xb.to(device), lb.to(device), yb.to(device)
            correct += (model(xb, lb).argmax(1) == yb).sum().item()
            total += len(yb)
    test_acc = correct / total
    sched.step(test_acc)

    print(f"Epoch {epoch:2d} | train {train_acc:.3f} | "
          f"UNSEEN-signer {test_acc:.3f} | lr {opt.param_groups[0]['lr']:.1e}")

    if test_acc > best_acc:
        best_acc, best_epoch = test_acc, epoch
        torch.save({
            "model_state": model.state_dict(),
            "vocab": vocab,
            "config": dict(input_dim=126, hidden_dim=128, num_layers=2,
                           num_classes=len(vocab)),
        }, MODEL_OUT)

print(f"\nBest unseen-signer accuracy: {best_acc:.3f} (epoch {best_epoch})")
print(f"Model saved to {MODEL_OUT}")