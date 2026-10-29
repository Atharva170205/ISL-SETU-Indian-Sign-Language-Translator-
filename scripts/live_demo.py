"""scripts/live_demo.py — webcam test of the full pipeline.
Press 'q' to quit, 'c' to manually force a word-boundary cut,
'd' to end the sentence (translates gloss -> English + Hindi via Groq).
"""
import sys, os, time
import numpy as np
import cv2
import mediapipe as mp

sys.path.insert(0, os.path.abspath("."))
from core.segmenter import StreamingSegmenter, Frame
from core.recognizer import SignRecognizer
from core.translator import translate_gloss

MODEL_PATH = r"D:\ISL_Setu\models\production.pt"
PAUSE_S = 1.0
MIN_WORD_FRAMES = 5

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

recognizer = SignRecognizer(MODEL_PATH)
gloss = []


def landmarks_to_raw(results, frame_shape) -> np.ndarray:
    """MediaPipe result -> (2, 21, 3) raw array, slot-order = detection order
    (canonicalization happens later in core/preprocess, identical to training)."""
    raw = np.zeros((2, 21, 3), dtype=np.float32)
    if results.multi_hand_landmarks:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks[:2]):
            for j, lm in enumerate(hand_landmarks.landmark):
                raw[i, j] = [lm.x, lm.y, lm.z]
    return raw


def on_word_done(chunk):
    raw = np.stack([f.landmarks for f in chunk.frames])
    n_frames = raw.shape[0]
    result = recognizer.predict(raw, top_k=3)

    alt_str = ", ".join(f"{a['word']}={a['confidence']:.2f}" for a in result["alternatives"])

    if result.get("unclear"):
        print(f"\nUNCLEAR  (frames={n_frames})  top3: {alt_str}")
        return

    gloss.append(result["word"])
    print(f"\nWORD: {result['word']}  (frames={n_frames})  top3: {alt_str}")


segmenter = StreamingSegmenter(on_word=on_word_done, pause_s=PAUSE_S,
                                min_word_frames=MIN_WORD_FRAMES)

cap = cv2.VideoCapture(0)
start_time = time.time()

with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5,
                     max_num_hands=2) as hands:
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)   # mirror for natural selfie-view
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        raw = landmarks_to_raw(results, frame.shape)
        hands_present = bool(results.multi_hand_landmarks)
        t = time.time() - start_time

        segmenter.push(Frame(t=t, landmarks=raw, hands_present=hands_present))

        if results.multi_hand_landmarks:
            for hlm in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hlm, mp_hands.HAND_CONNECTIONS)

        status = "HANDS UP" if hands_present else "hands down (pause)"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0) if hands_present else (0, 0, 255), 2)
        cv2.putText(frame, f"Gloss: {' '.join(gloss)}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(frame, "Press D=Done  Q=Quit  C=Clear", (10, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("ISL Setu - Live Demo", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('d'):
            segmenter.finish()
            print(f"\n=== GLOSS: {gloss} ===")
            if gloss:
                try:
                    sentences = translate_gloss(gloss, languages=("English", "Hindi"))
                    print("--- SENTENCE ---")
                    for lang, sentence in sentences.items():
                        print(f"  {lang}: {sentence}")
                except Exception as e:
                    print(f"  [!] Translation failed: {e}")
            else:
                print("  (gloss is empty, nothing to translate)")
            print("================\n")
            gloss.clear()
        elif key == ord('c'):
            gloss.clear()
            print("Gloss cleared.")

cap.release()
cv2.destroyAllWindows()