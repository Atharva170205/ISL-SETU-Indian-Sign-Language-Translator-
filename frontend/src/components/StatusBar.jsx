import React from "react";

function dotClass(status) {
  if (status === "open") return "dot-ok";
  if (status === "connecting") return "dot-warn";
  if (status === "error" || status === "closed") return "dot-bad";
  return "dot-neutral";
}

function cameraLabel(status) {
  if (status === "on") return "Camera on";
  if (status === "off") return "Camera off";
  if (status === "error") return "Camera error";
  return "Camera";
}

export default function StatusBar({ connStatus, cameraStatus, handsDetected, sessionId }) {
  return (
    <div className="status-bar">
      <div className="status-item">
        <span className={`dot ${dotClass(connStatus)}`} />
        <span>
          Backend&nbsp;
          <strong>
            {connStatus === "open"
              ? "Connected"
              : connStatus === "connecting"
              ? "Connecting…"
              : connStatus === "error"
              ? "Error"
              : "Closed"}
          </strong>
        </span>
      </div>

      <div className="status-item">
        <span className={`dot ${dotClass(cameraStatus === "on" ? "open" : cameraStatus)}`} />
        <span>
          {cameraLabel(cameraStatus)}
          {cameraStatus === "on" && handsDetected > 0 && (
            <span>&nbsp;· {handsDetected} hand(s)</span>
          )}
        </span>
      </div>

      {sessionId && (
        <div className="status-item session-id">
          <span className="dot dot-neutral" />
          <span>
            Session&nbsp;
            <code>{sessionId}</code>
          </span>
        </div>
      )}
    </div>
  );
}