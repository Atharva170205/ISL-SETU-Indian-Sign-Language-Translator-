import h5py, numpy as np, glob, os

files = sorted(glob.glob(r"D:\ISL_Setu\data\raw_landmarks\Landmarks\MediaPipe\ISL_DATA_USER014\*.h5"))
print(f"USER014 has {len(files)} clips\n")

for path in files[:5]:
    with h5py.File(path, "r") as f:
        arr = f["intermediate"][()]
    p0 = np.any(arr[:, 0] != 0, axis=(1, 2)).sum()
    p1 = np.any(arr[:, 1] != 0, axis=(1, 2)).sum()
    print(f"{os.path.basename(path):40s} T={arr.shape[0]:4d} slot0_frames={p0:3d} slot1_frames={p1:3d}")