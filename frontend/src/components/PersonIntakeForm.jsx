import React, { useState } from "react";

export default function PersonIntakeForm({ role, operator, authBase, onDone, onBack }) {
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${authBase}/api/persons`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          age: Number(age),
          phone,
          role,
          operatorUsername: operator?.username || null,
        }),
      });
      if (!res.ok) throw new Error("Save failed");
      const saved = await res.json();
      onDone(saved);
    } catch (err) {
      setError("Could not save details. Check backend connection.");
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
          <h2>Person details</h2>
          <p className="auth-subtitle">
            Enter the deaf/mute person&apos;s information for this conversation.
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Name
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </label>
          <label>
            Age
            <input
              type="number"
              min="0"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              required
            />
          </label>
          <label>
            Phone number
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
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
              {loading ? "Saving..." : "Continue to conversation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}