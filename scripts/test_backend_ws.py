"""
scripts/test_backend_ws.py — sends one real .h5 clip's landmarks through the
backend WebSocket to confirm end-to-end recognition works, without a frontend.
"""
import asyncio
import glob
import json
import h5py
import numpy as np
import websockets

WS_URL = "ws://localhost:8000/ws/recognize"
CLIP_PATH = glob.glob(r"data/raw_landmarks/Landmarks/MediaPipe/ISL_DATA_USER001/School__*.h5")[0]


async def main():
    print(f"Using test clip: {CLIP_PATH}")
    with h5py.File(CLIP_PATH, "r") as f:
        data = f["intermediate"][()]  # (T, 2, 21, 3)

    async with websockets.connect(WS_URL) as ws:
        t = 0.0
        for frame in data:
            # Only send detected hands (non-zero slots), like the browser will
            hands = [hand.tolist() for hand in frame if np.any(hand)]
            await ws.send(json.dumps({"type": "frame", "t": t, "hands": hands}))
            t += 1 / 30

        await ws.send(json.dumps({"type": "flush"}))

        while True:
            resp = json.loads(await ws.recv())
            print(resp)
            if resp.get("type") == "flush_done":
                break


asyncio.run(main())