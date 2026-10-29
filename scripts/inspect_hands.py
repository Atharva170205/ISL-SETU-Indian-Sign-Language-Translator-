import h5py, numpy as np, glob, os

files = glob.glob(r"D:\ISL_Setu\data\raw_landmarks\Landmarks\MediaPipe\*\*.h5")
sample = files[::200]   # ~20 files spread across words/signers

print(f"Checking {len(sample)} files...\n")

for path in sample:
    with h5py.File(path, "r") as f:
        arr = f["intermediate"][()]   # (T, 2, 21, 3)
        T = arr.shape[0]

        hand0_present = np.any(arr[:, 0] != 0, axis=(1, 2))
        hand1_present = np.any(arr[:, 1] != 0, axis=(1, 2))
        both = hand0_present & hand1_present

        # mean x of each slot when present (0=left edge of image, 1=right edge)
        x0 = arr[hand0_present, 0, 0, 0].mean() if hand0_present.any() else float('nan')
        x1 = arr[hand1_present, 1, 0, 0].mean() if hand1_present.any() else float('nan')

        print(f"{os.path.basename(path)[:30]:30s} T={T:3d} | "
              f"slot0:{hand0_present.sum():3d}f x={x0:.2f} | "
              f"slot1:{hand1_present.sum():3d}f x={x1:.2f} | "
              f"both:{both.sum():3d}f")