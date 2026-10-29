import { useState, useCallback, useRef, useEffect } from "react";
import { SignAvatarPlayer } from "./SignAvatarPlayer";

export default function TextToSignPanel({ cleanHost, httpProtocol, onConversation }) {
  const [inputText, setInputText] = useState("");
  const [glossWords, setGlossWords] = useState(null); // null = not generated yet
  const [unsupported, setUnsupported] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [currentWord, setCurrentWord] = useState(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    }
  }, [inputText]);

  const handleGenerate = useCallback(async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    setError(null);
    setGlossWords(null);
    setUnsupported([]);

    try {
      const resp = await fetch(`${httpProtocol}://${cleanHost}/api/text-to-gloss`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText }),
      });
      const data = await resp.json();
      if (data.success) {
        setGlossWords(data.gloss);
        setUnsupported(data.unsupported || []);

        if (onConversation) {
          onConversation({
            direction: "TEXT_TO_SIGN",
            speaker: "HEARING",
            glossText: data.gloss.join(" "),
            sentenceText: inputText,
            language: "English",
          });
        }
      } else {
        setError(data.error || "Failed to generate gloss");
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [inputText, cleanHost, httpProtocol, onConversation]);

  const handlePlay = useCallback(() => {
    if (!glossWords || glossWords.length === 0) return;
    setPlaying(true);
  }, [glossWords]);

  const handleDone = useCallback(() => {
    setPlaying(false);
    setCurrentWord(null);
  }, []);

  const handleWordStart = useCallback((word) => {
    setCurrentWord(word);
  }, []);

  const removeGlossWord = useCallback((idx) => {
    setGlossWords((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  return (
    <div className="text-to-sign-panel">
      <header className="panel-header">
        <h2>Type a sentence — we&apos;ll sign it back</h2>
        <p className="panel-subtitle">
          This side is for the hearing person. Type clearly; unsupported words will be
          highlighted.
        </p>
      </header>

      <textarea
        ref={textareaRef}
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        placeholder="Example: Today I will take you to the hospital. How are you feeling now?"
        rows={3}
        disabled={playing}
      />

      <div className="panel-actions">
        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={loading || playing || !inputText.trim()}
        >
          {loading ? "Generating gloss..." : "Generate sign sequence"}
        </button>
      </div>

      {error && <div className="ws-error">{error}</div>}

      {glossWords && (
        <div className="gloss-review">
          <h3>Review before signing</h3>
          <p className="panel-subtitle">
            Remove or adjust any word that does not match what you want to say.
          </p>

          <div className="gloss-chips">
            {glossWords.map((word, idx) => (
              <span key={idx} className="gloss-chip">
                {word}
                {!playing && (
                  <button
                    className="gloss-chip-remove"
                    onClick={() => removeGlossWord(idx)}
                    title="Remove word"
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
            {glossWords.length === 0 && (
              <em className="panel-subtitle">No words left — nothing to sign.</em>
            )}
          </div>

          {unsupported.length > 0 && (
            <div className="unsupported-warning">
              Note: could not express these concepts with available signs:{" "}
              {unsupported.join(", ")}
            </div>
          )}

          <div className="panel-actions">
            <button
              className="btn btn-secondary"
              onClick={handlePlay}
              disabled={playing || glossWords.length === 0}
            >
              {playing ? "Signing..." : "▶ Play signs"}
            </button>
          </div>
        </div>
      )}

      {glossWords && (
        <div className="sign-avatar-player">
          <SignAvatarPlayer
            words={glossWords}
            playing={playing}
            onWordStart={handleWordStart}
            onDone={handleDone}
          />
          {currentWord && (
            <div className="sign-avatar-current-word">
              Signing: <strong>{currentWord}</strong>
            </div>
          )}
        </div>
      )}
    </div>
  );
}