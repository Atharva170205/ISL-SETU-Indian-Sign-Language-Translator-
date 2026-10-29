import React, { useState } from "react";

const ROLE_LABELS = {
  DOCTOR: "Doctor",
  POLICE: "Police Officer",
  TEACHER: "Teacher",
};

const ROLE_INFO = {
  DOCTOR: "Use this account inside hospitals or clinics. Each conversation is linked to the patient details you enter.",
  POLICE: "Use this account at the police station to record clear, traceable conversations with citizens.",
  TEACHER: "Use this account in classrooms, counselling sessions, or parent meetings.",
};

export default function OperatorLogin({ role, authBase, onSuccess, onBack }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const label = ROLE_LABELS[role] || "Institution";
  const info = ROLE_INFO[role] || "";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${authBase}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (data.success) {
        if (data.role !== role) {
          setError(`This account is registered as ${data.role}, not ${role}.`);
        } else {
          onSuccess({ username, fullName: data.fullName, role: data.role });
        }
      } else {
        setError(data.message || "Login failed");
      }
    } catch (err) {
      setError("Could not reach auth server. Check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <button className="link-back" onClick={onBack}>
          ← Back
        </button>
        <div className="auth-header">
          <h2>{label} login</h2>
          <p className="auth-subtitle">
            Secure operator login for institutional use.
          </p>
          <span className="auth-role-pill">{label}</span>
        </div>

        {info && <p className="auth-info">{info}</p>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          {error && <div className="form-error">{error}</div>}

          <div className="auth-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? "Logging in..." : "Login"}
            </button>
          </div>

          <p className="auth-hint">
            Demo accounts: <code>doctor1 / doctor123</code>,{" "}
            <code>police1 / police123</code>, <code>teacher1 / teacher123</code>
          </p>
        </form>
      </div>
    </div>
  );
}