export default function ControlBar({ onDone, onClear, onUndo, translating, glossEmpty }) {
  return (
    <div className="control-bar">
      <button className="btn btn-secondary" onClick={onUndo} disabled={glossEmpty || translating}>
        Undo
      </button>
      <button className="btn btn-secondary" onClick={onClear} disabled={glossEmpty || translating}>
        Clear
      </button>
      <button className="btn btn-primary" onClick={onDone} disabled={glossEmpty || translating}>
        {translating ? "Translating..." : "Done"}
      </button>
    </div>
  );
}