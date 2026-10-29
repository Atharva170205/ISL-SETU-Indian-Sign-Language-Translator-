"""
services/backend/main.py — ISL Setu FastAPI backend.

Endpoints:
  WS   /ws/recognize   — streams raw hand landmarks in, streams recognized
                          words out (live segmentation + recognition).
  POST /api/translate  — gloss word list -> natural sentence(s) via Groq.
  POST /api/text-to-gloss — free text -> gloss word list (for Text-to-Sign avatar).
  GET  /api/vocab       — current trained vocabulary.
  GET  /api/health       — basic health/status check.

Run from project root:
  python -m uvicorn services.backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
import time
from typing import List, Optional

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make sure core/ is importable regardless of current working directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from core.segmenter import StreamingSegmenter, Frame
from core.recognizer import SignRecognizer
from core.translator import translate_gloss
from core.text_to_gloss import text_to_gloss  # NEW

PAUSE_S = 1.0
MIN_WORD_FRAMES = 5

app = FastAPI(title="ISL Setu Backend")

# Allow any origin on the local network to connect (Vite dev server, phone browser, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading recognizer model...")
recognizer = SignRecognizer()
print(f"Model loaded. Vocab size: {len(recognizer.vocab)}")


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"service": "ISL Setu Backend", "status": "running"}


@app.get("/api/health")
def health():
    return {"status": "ok", "vocab_size": len(recognizer.vocab)}


@app.get("/api/vocab")
def get_vocab():
    return {"vocab": recognizer.vocab}


class TranslateRequest(BaseModel):
    gloss: List[str]
    languages: List[str] = ["English"]


@app.post("/api/translate")
def translate_endpoint(req: TranslateRequest):
    if not req.gloss:
        return {"success": False, "error": "gloss list is empty"}
    try:
        sentences = translate_gloss(req.gloss, languages=tuple(req.languages))
        return {"success": True, "gloss": req.gloss, "sentences": sentences}
    except Exception as e:
        return {"success": False, "error": str(e)}


# NEW: Text -> Gloss endpoint (for Text-to-Sign avatar feature)
class TextToGlossRequest(BaseModel):
    text: str


@app.post("/api/text-to-gloss")
def text_to_gloss_endpoint(req: TextToGlossRequest):
    return text_to_gloss(req.text)


# ---------------------------------------------------------------------------
# WebSocket: live landmark streaming -> word recognition
# ---------------------------------------------------------------------------

def hands_to_raw(hands_data) -> np.ndarray:
    """hands_data: list of up to 2 hands, each a list of 21 [x,y,z] points.
    Returns (2, 21, 3) float32 array, zero-filled for missing hands/slots."""
    raw = np.zeros((2, 21, 3), dtype=np.float32)
    if hands_data:
        for i, hand in enumerate(hands_data[:2]):
            for j, lm in enumerate(hand[:21]):
                raw[i, j] = lm
    return raw


def serialize_result(result: dict) -> dict:
    """Ensure all values are plain JSON-safe Python types."""
    out = {
        "word": result.get("word"),
        "confidence": float(result.get("confidence", 0.0)),
        "unclear": bool(result.get("unclear", False)),
        "alternatives": [
            {"word": a["word"], "confidence": float(a["confidence"])}
            for a in result.get("alternatives", [])
        ],
    }
    if "n_frames" in result:
        out["n_frames"] = int(result["n_frames"])
    return out


class ConnectionSession:
    """Wraps a StreamingSegmenter + SignRecognizer for one WebSocket connection."""

    def __init__(self, recognizer: SignRecognizer):
        self.recognizer = recognizer
        self._pending_events = []
        self.segmenter = StreamingSegmenter(
            on_word=self._on_word, pause_s=PAUSE_S, min_word_frames=MIN_WORD_FRAMES
        )

    def _on_word(self, chunk):
        raw = np.stack([f.landmarks for f in chunk.frames])
        result = self.recognizer.predict(raw, top_k=3)
        result["n_frames"] = raw.shape[0]
        self._pending_events.append(result)

    def push_frame(self, frame: Frame):
        self.segmenter.push(frame)
        events, self._pending_events = self._pending_events, []
        return events

    def flush(self):
        self.segmenter.finish()
        events, self._pending_events = self._pending_events, []
        return events


@app.websocket("/ws/recognize")
async def ws_recognize(websocket: WebSocket):
    await websocket.accept()
    session = ConnectionSession(recognizer)
    start_time = time.time()
    print("[WS] Client connected.")

    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type")

            if msg_type == "frame":
                hands_data = msg.get("hands", [])
                raw = hands_to_raw(hands_data)
                hands_present = len(hands_data) > 0
                t = msg.get("t", time.time() - start_time)

                events = session.push_frame(
                    Frame(t=t, landmarks=raw, hands_present=hands_present)
                )
                for ev in events:
                    await websocket.send_json({"type": "word_result", **serialize_result(ev)})

            elif msg_type == "flush":
                events = session.flush()
                for ev in events:
                    await websocket.send_json({"type": "word_result", **serialize_result(ev)})
                await websocket.send_json({"type": "flush_done"})

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        print("[WS] Client disconnected.")