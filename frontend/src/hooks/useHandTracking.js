//useHandTracking.js
import { useRef, useState, useCallback, useEffect } from "react";
import { HandLandmarker, FilesetResolver, DrawingUtils } from "@mediapipe/tasks-vision";

export function useHandTracking(onFrame, enabled = true) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const landmarkerRef = useRef(null);
  const rafRef = useRef(null);
  const streamStartRef = useRef(null);
  const streamRef = useRef(null);

  const [cameraStatus, setCameraStatus] = useState("idle"); // idle | loading | ready | error
  const [cameraError, setCameraError] = useState(null);
  const [handsDetected, setHandsDetected] = useState(false);

  const onFrameRef = useRef(onFrame);
  onFrameRef.current = onFrame;

  useEffect(() => {
    if (!enabled) {
      // Tear down camera/landmarker if currently active, and reset status.
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (landmarkerRef.current) {
        landmarkerRef.current.close();
        landmarkerRef.current = null;
      }
      setCameraStatus("idle");
      return;
    }

    let cancelled = false;

    async function setup() {
      setCameraStatus("loading");
      try {
        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
        );
        const landmarker = await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath:
              "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
            delegate: "GPU",
          },
          runningMode: "VIDEO",
          numHands: 2,
        });
        if (cancelled) return;
        landmarkerRef.current = landmarker;

        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user" },
        });
        if (cancelled) return;
        streamRef.current = stream;

        const video = videoRef.current;
        video.srcObject = stream;
        await video.play();

        streamStartRef.current = performance.now();
        setCameraStatus("ready");
        loop();
      } catch (e) {
        console.error("Camera/MediaPipe setup failed", e);
        setCameraError(String(e.message || e));
        setCameraStatus("error");
      }
    }

    function loop() {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const landmarker = landmarkerRef.current;

      if (video && canvas && landmarker && video.readyState >= 2) {
        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
        }

        const now = performance.now();
        const result = landmarker.detectForVideo(video, now);

        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const present = result.landmarks && result.landmarks.length > 0;
        setHandsDetected(present);

        if (present) {
          const drawingUtils = new DrawingUtils(ctx);
          for (const handLm of result.landmarks) {
            drawingUtils.drawConnectors(handLm, HandLandmarker.HAND_CONNECTIONS, {
              color: "#00e676",
              lineWidth: 3,
            });
            drawingUtils.drawLandmarks(handLm, {
              color: "#ff3d00",
              lineWidth: 1,
              radius: 3,
            });
          }
        }

        const hands = (result.landmarks || [])
          .slice(0, 2)
          .map((hand) => hand.map((lm) => [lm.x, lm.y, lm.z]));
        const t = (now - streamStartRef.current) / 1000;

        if (onFrameRef.current) onFrameRef.current(hands, t);
      }

      rafRef.current = requestAnimationFrame(loop);
    }

    setup();

    return () => {
      cancelled = true;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (landmarkerRef.current) {
        landmarkerRef.current.close();
        landmarkerRef.current = null;
      }
    };
  }, [enabled]);

  return { videoRef, canvasRef, cameraStatus, cameraError, handsDetected };
}