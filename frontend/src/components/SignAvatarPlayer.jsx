import { useRef, useEffect, useState, useCallback } from "react";
import { HandLandmarker, DrawingUtils } from "@mediapipe/tasks-vision";

// Playback speed: frames per second to replay recorded clips at.
// Recorded clips are ~30fps capture; we can slow slightly for clarity.
const PLAYBACK_FPS = 24;
const PAUSE_BETWEEN_WORDS_MS = 600;

function isHandEmpty(hand) {
  // A hand slot is "empty" if every landmark is exactly [0,0,0]
  // (zero-padding from export, meaning no hand was detected that frame).
  return hand.every((pt) => pt[0] === 0 && pt[1] === 0 && pt[2] === 0);
}

export function SignAvatarPlayer({ words, playing, onWordStart, onDone }) {
  const canvasRef = useRef(null);
  const [currentWordIndex, setCurrentWordIndex] = useState(-1);
  const clipCacheRef = useRef({});
  const stopRef = useRef(false);

  const loadClip = useCallback(async (word) => {
    if (clipCacheRef.current[word]) return clipCacheRef.current[word];
    const resp = await fetch(`/signs/${encodeURIComponent(word)}.json`);
    if (!resp.ok) return null;
    const data = await resp.json();
    clipCacheRef.current[word] = data;
    return data;
  }, []);

  const drawFrame = useCallback((frame, canvas) => {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Light background grid/guide (optional, helps show it's a replay, not live camera)
    ctx.fillStyle = "#111";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const drawingUtils = new DrawingUtils(ctx);

    for (const hand of frame) {
      if (isHandEmpty(hand)) continue;
      const landmarks = hand.map(([x, y, z]) => ({ x, y, z }));
      drawingUtils.drawConnectors(landmarks, HandLandmarker.HAND_CONNECTIONS, {
        color: "#00e676",
        lineWidth: 3,
      });
      drawingUtils.drawLandmarks(landmarks, {
        color: "#ff3d00",
        lineWidth: 1,
        radius: 3,
      });
    }
  }, []);

  const playWord = useCallback(
    (data) => {
      return new Promise((resolve) => {
        const canvas = canvasRef.current;
        if (!canvas || !data) {
          resolve();
          return;
        }
        const frames = data.frames;
        let i = 0;
        const intervalMs = 1000 / PLAYBACK_FPS;

        function step() {
          if (stopRef.current) {
            resolve();
            return;
          }
          if (i >= frames.length) {
            resolve();
            return;
          }
          drawFrame(frames[i], canvas);
          i++;
          setTimeout(step, intervalMs);
        }
        step();
      });
    },
    [drawFrame]
  );

  useEffect(() => {
    if (!playing || !words || words.length === 0) return;

    stopRef.current = false;
    let cancelled = false;

    async function playAll() {
      for (let idx = 0; idx < words.length; idx++) {
        if (cancelled || stopRef.current) break;
        const word = words[idx];
        setCurrentWordIndex(idx);
        if (onWordStart) onWordStart(word, idx);

        const data = await loadClip(word);
        await playWord(data);

        if (cancelled || stopRef.current) break;
        await new Promise((r) => setTimeout(r, PAUSE_BETWEEN_WORDS_MS));
      }
      if (!cancelled) {
        setCurrentWordIndex(-1);
        if (onDone) onDone();
      }
    }

    playAll();

    return () => {
      cancelled = true;
      stopRef.current = true;
    };
  }, [playing, words, loadClip, playWord, onWordStart, onDone]);

  return (
    <div className="sign-avatar-player">
      <canvas
        ref={canvasRef}
        width={480}
        height={480}
        style={{ background: "#111", borderRadius: "8px", width: "100%", maxWidth: 480 }}
      />
      {currentWordIndex >= 0 && words && (
        <div className="sign-avatar-current-word">
          Signing: <strong>{words[currentWordIndex]}</strong>
        </div>
      )}
    </div>
  );
}