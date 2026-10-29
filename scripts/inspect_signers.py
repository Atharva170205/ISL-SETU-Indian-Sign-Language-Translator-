import h5py, numpy as np, glob, os

files = glob.glob(r"D:\ISL_Setu\data\raw_landmarks\Landmarks\MediaPipe\*\*.h5")
print(f"Total files found: {len(files)}")

# --- signer IDs ---
signers = sorted(set(os.path.basename(os.path.dirname(f)) for f in files))
print(f"\nSigners found: {len(signers)}")
for s in signers:
    print("  ", s)

# --- one-hand vs two-hand distribution ---
two_hand, one_hand, zero_hand = 0, 0, 0
for p in files[::5]:
    with h5py.File(p, "r") as f:
        arr = f["intermediate"][()]
    p0 = np.any(arr[:, 0] != 0, axis=(1, 2))
    p1 = np.any(arr[:, 1] != 0, axis=(1, 2))
    both = (p0 & p1).sum()
    only0 = (p0 & ~p1).sum()
    only1 = (~p0 & p1).sum()
    if both > 5:
        two_hand += 1
    elif only0 + only1 > 5:
        one_hand += 1
    else:
        zero_hand += 1

n_sampled = len(files[::5])
print(f"\nSampled {n_sampled} files:")
print(f"  two_hand-dominant:  {two_hand}")
print(f"  one_hand-dominant:  {one_hand}")
print(f"  mostly_empty:       {zero_hand}")