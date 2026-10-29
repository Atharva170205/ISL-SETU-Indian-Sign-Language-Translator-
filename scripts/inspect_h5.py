import h5py
import numpy as np

PATH = r"D:\ISL_Setu\data\raw_landmarks\Landmarks\MediaPipe\ISL_DATA_USER001\Doctor__session122__clip024.h5"

def explore(name, obj):
    if isinstance(obj, h5py.Dataset):
        print(f"DATASET: {name}")
        print(f"   shape: {obj.shape}")
        print(f"   dtype: {obj.dtype}")
        try:
            arr = obj[()]
            print(f"   min: {np.nanmin(arr):.4f}  max: {np.nanmax(arr):.4f}")
            print(f"   sample values: {np.array(arr).flatten()[:8]}")
        except Exception as e:
            print(f"   (could not read values: {e})")
    else:
        print(f"GROUP: {name}")

with h5py.File(PATH, "r") as f:
    print("=== Top-level keys ===")
    print(list(f.keys()))
    print()
    print("=== Attributes on file ===")
    for k, v in f.attrs.items():
        print(f"   {k}: {v}")
    print()
    print("=== Full structure ===")
    f.visititems(explore)