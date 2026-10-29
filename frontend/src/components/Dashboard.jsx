import React, { useEffect, useState } from "react";

export default function Dashboard({ authBase, operator, onBack }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!operator) return;
    fetch(
      `${authBase}/api/conversations?operatorUsername=${encodeURIComponent(
        operator.username
      )}`
    )
      .then((res) => res.json())
      .then((data) => setConversations(data))
      .catch(() => setError("Could not load conversation history."))
      .finally(() => setLoading(false));
  }, [authBase, operator]);

  return (
    <div className="dashboard-panel">
      <div className="dashboard-header">
        <div>
          <h2>Conversation history</h2>
          <p className="panel-subtitle">
            Past conversations saved for this operator account.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onBack}>
          ← Back to live translation
        </button>
      </div>

      {loading && <p>Loading conversation history…</p>}
      {error && <div className="form-error">{error}</div>}

      {!loading && conversations.length === 0 && (
        <div className="gloss-empty">No saved conversations yet.</div>
      )}

      {!loading && conversations.length > 0 && (
        <table className="dashboard-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Person</th>
              <th>Direction</th>
              <th>Speaker</th>
              <th>Content</th>
            </tr>
          </thead>
          <tbody>
            {conversations.map((c) => (
              <tr key={c.id}>
                <td>{new Date(c.timestamp).toLocaleString()}</td>
                <td>
                  {c.personName}
                  <div className="dashboard-subtext">
                    Age {c.personAge} · {c.personPhone}
                  </div>
                </td>
                <td>{c.direction === "SIGN_TO_TEXT" ? "Sign → Text" : "Text → Sign"}</td>
                <td>
                  {c.speaker === "DEAF_MUTE" ? "Deaf/mute person" : "Hearing person"}
                </td>
                <td>
                  <div>
                    <strong>Gloss:</strong> {c.glossText}
                  </div>
                  <div>
                    <strong>Sentence:</strong> {c.sentenceText}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}