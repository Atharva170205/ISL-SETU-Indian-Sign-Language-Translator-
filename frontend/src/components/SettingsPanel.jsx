import { useState } from "react";

export default function SettingsPanel({
  backendHost,
  setBackendHost,
  onReconnect,
  languages,
  setLanguages,
}) {
  const [open, setOpen] = useState(false);

  function toggleLang(lang) {
    setLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  }

  return (
    <div className="settings-panel">
      <button className="settings-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Hide settings ▲" : "Settings ▼"}
      </button>
      {open && (
        <div className="settings-body">
          <label>
            Backend address:
            <input
              value={backendHost}
              onChange={(e) => setBackendHost(e.target.value)}
              placeholder="192.168.x.x:8000"
            />
          </label>
          <button className="btn btn-secondary" onClick={onReconnect}>
            Reconnect
          </button>

          <div className="lang-toggles">
            <label>
              <input type="checkbox" checked disabled /> English
            </label>
            <label>
              <input
                type="checkbox"
                checked={languages.includes("Hindi")}
                onChange={() => toggleLang("Hindi")}
              />
              Hindi
            </label>
            <label>
              <input
                type="checkbox"
                checked={languages.includes("Marathi")}
                onChange={() => toggleLang("Marathi")}
              />
              Marathi
            </label>
          </div>
        </div>
      )}
    </div>
  );
}