function confidenceClass(conf) {
  if (conf >= 0.85) return "chip-high";
  if (conf >= 0.6) return "chip-mid";
  return "chip-low";
}

export default function GlossChips({ gloss, updateWord, removeWord }) {
  if (gloss.length === 0) {
    return <div className="gloss-empty">Sign a word to begin...</div>;
  }

  return (
    <div className="chips">
      {gloss.map((g) => (
        <div key={g.id} className={`chip ${confidenceClass(g.confidence)}`}>
          <input value={g.word} onChange={(e) => updateWord(g.id, e.target.value)} />
          <span className="confidence">{Math.round(g.confidence * 100)}%</span>
          <button className="chip-remove" onClick={() => removeWord(g.id)}>
            ×
          </button>
        </div>
      ))}
    </div>
  );
}