import React from "react";

const ROLES = [
  {
    key: "DOCTOR",
    label: "Doctor",
    description: "Use in hospitals or clinics to talk to deaf/mute patients.",
  },
  {
    key: "POLICE",
    label: "Police",
    description: "Record clear statements and complaints from deaf/mute citizens.",
  },
  {
    key: "TEACHER",
    label: "Teacher",
    description: "Support inclusive classrooms and student counselling.",
  },
  {
    key: "PUBLIC",
    label: "Public",
    description: "Use at home, with friends, or for self-practice.",
  },
];

export default function RoleSelect({ onSelect }) {
  return (
    <div className="landing">
      <div className="landing-inner">
        <div className="landing-left">
          <div className="landing-pill">Indian Sign Language • Assistive AI</div>
          <h1>ISL Setu — a two‑way bridge for real conversations</h1>
          <p className="landing-text">
            ISL Setu helps doctors, police officers, teachers and families
            communicate directly with deaf and mute people. Signs are recognized
            on‑device and turned into natural speech, and typed questions are
            shown back as sign animations.
          </p>

          <div className="landing-metrics">
            <div>
              <strong>50+ core signs</strong>
              <span>Optimised for real-world phrases</span>
            </div>
            <div>
              <strong>On your own laptop</strong>
              <span>No cloud video upload, just landmarks</span>
            </div>
            <div>
              <strong>Two-way</strong>
              <span>Sign → Text & Text → Sign</span>
            </div>
          </div>
        </div>

        <div className="landing-right">
          <h2 className="landing-role-heading">How are you using ISL Setu today?</h2>
          <p className="landing-role-subtitle">
            Choose your context so we can store the right details and logs.
          </p>

          <div className="role-grid">
            {ROLES.map((r) => (
              <button
                key={r.key}
                className="role-card"
                onClick={() => onSelect(r.key)}
              >
                <div className="role-card-label">{r.label}</div>
                <div className="role-card-desc">{r.description}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}