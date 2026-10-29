import React, { useState } from "react";

export default function Sidebar({
  role,
  operator,
  personInfo,
  onNewConversation,
  onLogout,
  onDashboard,
}) {
  const [showSettingsHint, setShowSettingsHint] = useState(false);

  return (
    <aside className="app-sidebar">
      <div>
        <div className="sidebar-brand">ISL Setu</div>

        <div className="sidebar-context">
          <div className="sidebar-role">{role || "Guest"}</div>
          {operator && (
            <div className="sidebar-operator">
              Operator: <strong>{operator.fullName}</strong>
            </div>
          )}
          {personInfo && (
            <div className="sidebar-person">
              Person: <strong>{personInfo.name}</strong>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          {role !== "PUBLIC" && (
            <button className="sidebar-link" onClick={onDashboard}>
              📊 Dashboard
            </button>
          )}
          <button
            className="sidebar-link"
            onClick={() => setShowSettingsHint(!showSettingsHint)}
          >
            ⚙️ Settings
          </button>
          {showSettingsHint && (
            <div className="sidebar-hint">
              Use &quot;Connection &amp; Languages&quot; panel to change backend
              IP and spoken languages.
            </div>
          )}
        </nav>
      </div>

      <div className="sidebar-footer">
        {role !== "PUBLIC" && (
          <button className="btn btn-secondary" onClick={onNewConversation}>
            + New person / conversation
          </button>
        )}
        <button className="btn btn-secondary" onClick={onLogout}>
          Logout
        </button>
      </div>
    </aside>
  );
}