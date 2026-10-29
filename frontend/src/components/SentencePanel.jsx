function speak(text, lang) {
  if (!text) return;
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = lang === "Hindi" ? "hi-IN" : lang === "Marathi" ? "mr-IN" : "en-IN";
  speechSynthesis.speak(utter);
}

export default function SentencePanel({ sentences }) {
  if (!sentences) return null;

  return (
    <div className="sentence-panel">
      {Object.entries(sentences).map(([lang, text]) => (
        <div key={lang} className="sentence-row">
          <strong>{lang}:</strong> <span>{text}</span>
          <button className="btn-speak" onClick={() => speak(text, lang)}>
            🔊
          </button>
        </div>
      ))}
    </div>
  );
}