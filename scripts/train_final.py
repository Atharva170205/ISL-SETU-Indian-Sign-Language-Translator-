"""scripts/train_final.py — production model: all 15 signers + own data + mirror augmentation."""
import json, os, sys
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from collections import Counter

sys.path.insert(0, os.path.abspath("."))
from core.model import SignClassifier

DATA = r"D:\ISL_Setu\data\processed\dataset.npz"
MODEL_OUT = r"D:\ISL_Setu\models\production.pt"

EPOCHS = 40
BATCH = 64
LR = 1e-3
VAL_FRACTION = 0.1

torch.manual_seed(42)
np.random.seed(42)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

d = np.load(DATA, allow_pickle=True)
X, y, lengths, vocab = d["X"], d["y"], d["lengths"], d["vocab"]
vocab = [str(v) for v in vocab]

# mirror augmentation: flip x-coordinate (index 0 of each xyz triplet)
X_mirror = X.copy()
X_mirror[..., 0::3] *= -1

X_all = np.concatenate([X, X_mirror], axis=0)
y_all = np.concatenate([y, y], axis=0)
lengths_all = np.concatenate([lengths, lengths], axis=0)

n = len(y_all)
idx = np.random.permutation(n)
n_val = int(n * VAL_FRACTION)
val_idx, train_idx = idx[:n_val], idx[n_val:]

def make_loader(idxs, shuffle):
    ds = TensorDataset(torch.tensor(X_all[idxs]), torch.tensor(lengths_all[idxs]),
                        torch.tensor(y_all[idxs]))
    return DataLoader(ds, batch_size=BATCH, shuffle=shuffle)

train_loader = make_loader(train_idx, True)
val_loader = make_loader(val_idx, False)

print(f"Train: {len(train_idx)} (incl. mirrored) | Val: {len(val_idx)} | Classes: {len(vocab)}")

model = SignClassifier(num_classes=len(vocab)).to(device)
opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-5)
sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=4, factor=0.5)

# Class-weighted loss: compensates for ISL500 words (~130+ clips/signer x15)
# heavily outnumbering own-recorded words (~20-80 clips from 1 signer)
y_train_np = y_all[train_idx]
class_counts = Counter(y_train_np.tolist())
num_classes = len(vocab)
weights = torch.zeros(num_classes)
for cls_idx in range(num_classes):
    count = class_counts.get(cls_idx, 1)
    weights[cls_idx] = 1.0 / count
weights = weights / weights.sum() * num_classes
weights = weights.to(device)

criterion = nn.CrossEntropyLoss(weight=weights)

best_acc, best_epoch, no_improve, PATIENCE = 0.0, -1, 0, 8

for epoch in range(1, EPOCHS + 1):
    model.train()
    correct, total, loss_sum = 0, 0, 0.0
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
        for xb, lb, yb in val_loader:
            xb, lb, yb = xb.to(device), lb.to(device), yb.to(device)
            correct += (model(xb, lb).argmax(1) == yb).sum().item()
            total += len(yb)
    val_acc = correct / total
    sched.step(val_acc)

    print(f"Epoch {epoch:2d} | train {train_acc:.3f} | val {val_acc:.3f} | "
          f"lr {opt.param_groups[0]['lr']:.1e}")

    if val_acc > best_acc:
        best_acc, best_epoch, no_improve = val_acc, epoch, 0
        torch.save({
            "model_state": model.state_dict(),
            "vocab": vocab,
            "config": dict(input_dim=126, hidden_dim=128, num_layers=2,
                           num_classes=len(vocab)),
        }, MODEL_OUT)
    else:
        no_improve += 1
        if no_improve >= PATIENCE:
            print(f"Early stopping at epoch {epoch}")
            break

print(f"\nBest val accuracy: {best_acc:.3f} (epoch {best_epoch})")
print(f"Production model saved to {MODEL_OUT}")
print(f"\nNote: this val split is RANDOM (same-signer leakage possible).")
print(f"True generalization estimate for ISL500 words remains ~82% (5-fold).")
print(f"Own-recorded words (single signer) have NO cross-signer validation yet.")