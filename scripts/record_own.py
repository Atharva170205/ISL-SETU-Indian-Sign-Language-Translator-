"""
record_own.py — Webcam recording tool for ISL Setu's own-signer dataset.

Records isolated-word clips via webcam + MediaPipe, saving raw landmarks in the
exact same (T, 2, 21, 3) .h5 format as ISL500, so build_dataset.py picks them
up automatically with zero pipeline changes.

Output: data/raw_landmarks/Landmarks/MediaPipe/ISL_DATA_OWN001/
Filename pattern: {Word}__ownsession001__clip{NNN}.h5

Controls (shown on screen too):
  SPACE : start recording / stop & save current clip
  R     : discard the last saved clip for this word (retake)
  N     : move to next word
  P     : go back to previous word
  Q/ESC : quit

Run (all words):          python scripts/record_own.py
Run (only specific words): python scripts/record_own.py Eat Doctor Drink Give Why What
"""

import os
import re
import sys
import glob
import h5py
import numpy as np
import cv2
import mediapipe as mp

# ---------------------------------------------------------------------------
# Word list (final, 3 tiers)
# ---------------------------------------------------------------------------
TIER1 = ["Eat", "Food", "Please", "Thankyou"]                 # confused live, fix first
TIER2 = ["College", "Home", "Hospital", "Come", "Stop", "Take",
         "Sleep", "Study", "Learn", "Want", "Need", "Like",
         "Know", "Understand", "Who", "How", "Sorry", "Now"]   # missing entirely
TIER3 = ["Water", "Drink", "Give", "Doctor", "Why", "What", "Student"]  # optional insurance

TARGET_CLIPS = {}
for w in TIER1 + TIER2:
    TARGET_CLIPS[w] = 18
for w in TIER3:
    TARGET_CLIPS[w] = 9

WORDLIST = [(w, "TIER1") for w in TIER1] + \
           [(w, "TIER2") for w in TIER2] + \
           [(w, "TIER3 (optional)") for w in TIER3]

OUT_DIR = os.path.join("data", "raw_landmarks", "Landmarks", "MediaPipe", "ISL_DATA_OWN001")
os.makedirs(OUT_DIR, exist_ok=True)

SESSION_TAG = "ownsession001"

# ---------------------------------------------------------------------------
# MediaPipe setup
# ---------------------------------------------------------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


def extract_frame_landmarks(results):
    """Return (2, 21, 3) float32 array, detection-order slots, zero-filled if missing."""
    arr = np.zeros((2, 21, 3), dtype=np.float32)
    if results.multi_hand_landmarks:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks[:2]):
            for j, lm in enumerate(hand_landmarks.landmark):
                arr[i, j, 0] = lm.x
                arr[i, j, 1] = lm.y
                arr[i, j, 2] = lm.z
    return arr


def existing_clip_indices(word):
    pattern = os.path.join(OUT_DIR, f"{word}__*__clip*.h5")
    indices = []
    for f in glob.glob(pattern):
        m = re.search(r"clip(\d+)\.h5$", f)
        if m:
            indices.append(int(m.group(1)))
    return sorted(indices)


def next_clip_index(word):
    idx = existing_clip_indices(word)
    return (idx[-1] + 1) if idx else 0


def save_clip(word, frames):
    """frames: list of (2,21,3) arrays -> save as (T,2,21,3) h5 file."""
    if len(frames) < 3:
        print("  [!] Clip too short (<3 frames), not saved. Try again.")
        return None
    data = np.stack(frames, axis=0).astype(np.float32)  # (T,2,21,3)
    idx = next_clip_index(word)
    fname = f"{word}__{SESSION_TAG}__clip{idx:03d}.h5"
    fpath = os.path.join(OUT_DIR, fname)
    with h5py.File(fpath, "w") as f:
        f.create_dataset("intermediate", data=data)
        f.attrs["native_fps"] = 30.0
        f.attrs["target_fps"] = 30.0
        f.attrs["num_frames"] = data.shape[0]
        f.attrs["shape"] = data.shape
    print(f"  [OK] Saved {fname}  ({data.shape[0]} frames)")
    return fpath


def delete_last_clip(word):
    idx = existing_clip_indices(word)
    if not idx:
        print("  [!] No clips to delete for this word yet.")
        return
    last = idx[-1]
    pattern = os.path.join(OUT_DIR, f"{word}__*__clip{last:03d}.h5")
    for f in glob.glob(pattern):
        os.remove(f)
        print(f"  [OK] Deleted {os.path.basename(f)}")


def draw_overlay(frame, word, tier, word_pos, total_words, saved_count, target, recording, no_hand_detected):
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 170), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)

    color = (0, 0, 255) if recording else (0, 255, 0)
    cv2.putText(frame, f"[{word_pos+1}/{total_words}] {tier}", (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(frame, f"WORD: {word.upper()}", (15, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 2)
    cv2.putText(frame, f"Clips saved: {saved_count}/{target}", (15, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1)

    status = "RECORDING..." if recording else "Press SPACE to start"
    cv2.putText(frame, status, (15, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

    if recording and no_hand_detected:
        cv2.putText(frame, "!! NO HAND DETECTED !!", (15, 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

    cv2.putText(frame, "SPACE=start/stop  R=retake  N=next  P=prev  Q=quit",
                (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    return frame


def filter_wordlist_from_args():
    """If specific words are passed as CLI args, only record those (for gap-filling)."""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        return WORDLIST
    args_lower = {a.lower() for a in args}
    filtered = [(w, t) for (w, t) in WORDLIST if w.lower() in args_lower]
    if not filtered:
        print(f"[!] None of the requested words {args} matched the known word list. Exiting.")
        sys.exit(1)
    return filtered


def main():
    active_wordlist = filter_wordlist_from_args()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        return

    print("=" * 60)
    print("ISL Setu — Own Recording Session")
    print(f"Words in this session: {len(active_wordlist)}")
    print(f"Output dir: {OUT_DIR}")
    print("Tip: record in short 5-10 word bursts, take breaks, vary angle/speed a bit.")
    print("If you see '!! NO HAND DETECTED !!' while recording, press R to retake.")
    print("=" * 60)

    word_pos = 0
    recording = False
    current_frames = []

    while 0 <= word_pos < len(active_wordlist):
        word, tier = active_wordlist[word_pos]
        target = TARGET_CLIPS[word]
        saved_count = len(existing_clip_indices(word))

        ret, frame = cap.read()
        if not ret:
            print("ERROR: Failed to read frame from webcam.")
            break

        frame = cv2.flip(frame, 1)  # mirror for natural self-view
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        no_hand_detected = not results.multi_hand_landmarks

        if results.multi_hand_landmarks:
            for hl in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hl, mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )

        if recording:
            lm = extract_frame_landmarks(results)
            current_frames.append(lm)

        display = draw_overlay(frame, word, tier, word_pos, len(active_wordlist),
                                saved_count, target, recording, no_hand_detected)
        cv2.imshow("ISL Setu - Record Own Signs", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):
            if not recording:
                recording = True
                current_frames = []
                print(f"-- Recording '{word}'...")
            else:
                recording = False
                save_clip(word, current_frames)
                current_frames = []

        elif key == ord('r') or key == ord('R'):
            if recording:
                recording = False
                current_frames = []
                print("  [!] Discarded current (unsaved) take.")
            else:
                delete_last_clip(word)

        elif key == ord('n') or key == ord('N'):
            if recording:
                recording = False
                save_clip(word, current_frames)
                current_frames = []
            word_pos += 1
            if word_pos < len(active_wordlist):
                print(f"\n>> Next word: {active_wordlist[word_pos][0]}")

        elif key == ord('p') or key == ord('P'):
            if recording:
                recording = False
                current_frames = []
            word_pos = max(0, word_pos - 1)
            print(f"\n>> Back to word: {active_wordlist[word_pos][0]}")

        elif key == ord('q') or key == 27:  # q or ESC
            print("\nQuitting session.")
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

    print("\n" + "=" * 60)
    print("Session summary:")
    for word, tier in active_wordlist:
        n = len(existing_clip_indices(word))
        target = TARGET_CLIPS[word]
        flag = "OK" if n >= target else f"NEED {target - n} MORE"
        print(f"  {word:15s} [{tier:16s}] {n:2d}/{target:2d}  {flag}")
    print("=" * 60)


if __name__ == "__main__":
    main()