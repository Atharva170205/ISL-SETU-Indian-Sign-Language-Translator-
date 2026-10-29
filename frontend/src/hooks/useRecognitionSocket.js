import { useRef, useState, useCallback, useEffect } from "react";

let nextId = 0;

export function useRecognitionSocket(wsUrl) {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const flushResolveRef = useRef(null);

  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const [gloss, setGloss] = useState([]);
  const sessionIdRef = useRef(Math.random().toString(36).slice(2, 8));

  const connect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.intentionalClose = true;
      wsRef.current.close();
    }

    setStatus("connecting");
    setError(null);

    let ws;
    try {
      ws = new WebSocket(wsUrl);
    } catch (e) {
      setStatus("error");
      setError("Failed to create WebSocket: " + String(e));
      return;
    }
    ws.intentionalClose = false;

    ws.onopen = () => {
      setStatus("open");
      setError(null);
    };

    ws.onclose = (ev) => {
      setStatus("closed");
      if (!ws.intentionalClose) {
        setError(`Disconnected (code ${ev.code}). Reconnecting...`);
        reconnectTimerRef.current = setTimeout(() => connect(), 2000);
      }
    };

    ws.onerror = () => {
      setStatus("error");
      setError("WebSocket error — check backend address and network.");
    };

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "word_result") {
        if (!msg.unclear && msg.word) {
          setGloss((prev) => [
            ...prev,
            { id: nextId++, word: msg.word, confidence: msg.confidence },
          ]);
        }
      } else if (msg.type === "flush_done") {
        if (flushResolveRef.current) {
          flushResolveRef.current();
          flushResolveRef.current = null;
        }
      }
    };

    wsRef.current = ws;
  }, [wsUrl]);

  useEffect(() => {
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.intentionalClose = true;
        wsRef.current.close();
      }
    };
  }, []);

  const sendFrame = useCallback((hands, t) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "frame", t, hands }));
    }
  }, []);

  const flush = useCallback(() => {
    return new Promise((resolve) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        resolve();
        return;
      }
      flushResolveRef.current = resolve;
      ws.send(JSON.stringify({ type: "flush" }));
    });
  }, []);

  const clearGloss = useCallback(() => setGloss([]), []);
  const undoLast = useCallback(() => setGloss((prev) => prev.slice(0, -1)), []);

  const updateWord = useCallback((id, newWord) => {
    setGloss((prev) => prev.map((g) => (g.id === id ? { ...g, word: newWord } : g)));
  }, []);

  const removeWord = useCallback((id) => {
    setGloss((prev) => prev.filter((g) => g.id !== id));
  }, []);

  return {
    status,
    error,
    connect,
    gloss,
    sendFrame,
    flush,
    clearGloss,
    undoLast,
    updateWord,
    removeWord,
    sessionId: sessionIdRef.current,
  };
}