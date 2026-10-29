import { useState, useCallback, useEffect } from "react";
import RoleSelect from "./components/RoleSelect";
import OperatorLogin from "./components/OperatorLogin";
import PersonIntakeForm from "./components/PersonIntakeForm";
import Sidebar from "./components/Sidebar";
import Dashboard from "./components/Dashboard";
import { useHandTracking } from "./hooks/useHandTracking";
import { useRecognitionSocket } from "./hooks/useRecognitionSocket";
import StatusBar from "./components/StatusBar";
import CameraView from "./components/CameraView";
import GlossChips from "./components/GlossChips";
import ControlBar from "./components/ControlBar";
import SettingsPanel from "./components/SettingsPanel";
import SentencePanel from "./components/SentencePanel";
import TextToSignPanel from "./components/TextToSignPanel";
import "./App.css";

export default function App() {
  // ---------- Role / Auth / Intake stage flow ----------
  const [stage, setStage] = useState("role-select"); // role-select | login | intake | main | dashboard
  const [role, setRole] = useState(null);            // DOCTOR | POLICE | TEACHER | PUBLIC
  const [operator, setOperator] = useState(null);    // { username, fullName, role }
  const [personInfo, setPersonInfo] = useState(null); // saved Person from Spring Boot

  const authBase = `https://${window.location.hostname}:8081`;

  const handleRoleSelect = (selectedRole) => {
    setRole(selectedRole);
    setStage(selectedRole === "PUBLIC" ? "main" : "login");
  };

  const handleLoginSuccess = (op) => {
    setOperator(op);
    setStage("intake");
  };

  const handleIntakeDone = (savedPerson) => {
    setPersonInfo(savedPerson);
    setStage("main");
  };

  const handleNewConversation = () => {
    setPersonInfo(null);
    setStage("intake");
  };

  const handleLogout = () => {
    setRole(null);
    setOperator(null);
    setPersonInfo(null);
    setStage("role-select");
  };

  // ---------- Existing Sign ↔ Text / Text ↔ Sign logic ----------
  const [mode, setMode] = useState("sign-to-text"); // "sign-to-text" | "text-to-sign"

  // Backend host for FastAPI
  const [backendHost, setBackendHost] = useState(() => {
    const saved = localStorage.getItem("islSetuBackend");
    return saved && saved.trim() !== "" ? saved : `${window.location.hostname}:8000`;
  });
  const [languages, setLanguages] = useState(["English", "Hindi"]);
  const [sentences, setSentences] = useState(null);
  const [translating, setTranslating] = useState(false);

  const cleanHost = backendHost.trim().replace(/^https?:\/\//, "").replace(/\/+$/, "");
  const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  const httpProtocol = window.location.protocol === "https:" ? "https" : "http";
  const wsUrl = `${wsProtocol}://${cleanHost}/ws/recognize`;

  const {
    status,
    error: wsError,
    connect,
    gloss,
    sendFrame,
    flush,
    clearGloss,
    undoLast,
    updateWord,
    removeWord,
    sessionId,
  } = useRecognitionSocket(wsUrl);

  useEffect(() => {
    localStorage.setItem("islSetuBackend", backendHost);
  }, [backendHost]);

  useEffect(() => {
    connect();
  }, [connect]);

  const handleFrame = useCallback(
    (hands, t) => {
      sendFrame(hands, t);
    },
    [sendFrame]
  );

  // Only run camera in main stage + Sign→Text mode
  const cameraEnabled = mode === "sign-to-text" && stage === "main";
  const { videoRef, canvasRef, cameraStatus, cameraError, handsDetected } =
    useHandTracking(handleFrame, cameraEnabled);

  // ---------- Save conversation to Spring Boot (for Dashboard) ----------
  const saveConversation = useCallback(
    async ({ direction, speaker, glossText, sentenceText, language }) => {
      if (role === "PUBLIC" || !operator || !personInfo) return; // Public: no permanent storage
      try {
        await fetch(`${authBase}/api/conversations`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            operatorUsername: operator.username,
            operatorFullName: operator.fullName,
            role,
            personId: personInfo.id,
            personName: personInfo.name,
            personAge: personInfo.age,
            personPhone: personInfo.phone,
            direction,
            speaker,
            glossText,
            sentenceText,
            language,
          }),
        });
      } catch (e) {
        console.error("Failed to save conversation:", e);
      }
    },
    [role, operator, personInfo, authBase]
  );

  const handleDone = useCallback(async () => {
    if (gloss.length === 0) return;
    setTranslating(true);
    setSentences(null);
    await flush();

    try {
      const words = gloss.map((g) => g.word);
      const resp = await fetch(`${httpProtocol}://${cleanHost}/api/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gloss: words, languages }),
      });
      const data = await resp.json();
      if (data.success) {
        setSentences(data.sentences);
        const englishText = data.sentences["English"];
        if (englishText) {
          const utter = new SpeechSynthesisUtterance(englishText);
          utter.lang = "en-IN";
          speechSynthesis.speak(utter);
        }

        // log Sign→Text conversation
        saveConversation({
          direction: "SIGN_TO_TEXT",
          speaker: "DEAF_MUTE",
          glossText: words.join(" "),
          sentenceText: Object.values(data.sentences).join(" | "),
          language: languages.join(","),
        });
      } else {
        setSentences({ Error: data.error });
      }
    } catch (e) {
      setSentences({ Error: String(e) });
    } finally {
      setTranslating(false);
    }
  }, [gloss, flush, cleanHost, httpProtocol, languages, saveConversation]);

  const handleClear = useCallback(() => {
    clearGloss();
    setSentences(null);
  }, [clearGloss]);

  // ---------- Stage-gated rendering ----------
  if (stage === "role-select") {
    return <RoleSelect onSelect={handleRoleSelect} />;
  }

  if (stage === "login") {
    return (
      <OperatorLogin
        role={role}
        authBase={authBase}
        onSuccess={handleLoginSuccess}
        onBack={() => setStage("role-select")}
      />
    );
  }

  if (stage === "intake") {
    return (
      <PersonIntakeForm
        role={role}
        operator={operator}
        authBase={authBase}
        onDone={handleIntakeDone}
        onBack={() => setStage(role === "PUBLIC" ? "role-select" : "login")}
      />
    );
  }

  if (stage === "dashboard") {
    return (
      <div className="app-shell">
        <Sidebar
          role={role}
          operator={operator}
          personInfo={personInfo}
          onNewConversation={handleNewConversation}
          onLogout={handleLogout}
          onDashboard={() => setStage("dashboard")}
        />
        <main className="app-main">
          <Dashboard
            authBase={authBase}
            operator={operator}
            onBack={() => setStage("main")}
          />
        </main>
      </div>
    );
  }

  // ---------- Main app (with sidebar) ----------
  return (
    <div className="app-shell">
      <Sidebar
        role={role}
        operator={operator}
        personInfo={personInfo}
        onNewConversation={handleNewConversation}
        onLogout={handleLogout}
        onDashboard={() => setStage("dashboard")}
      />

      <main className="app-main">
        <header className="app-header">
          <div>
            <h1>ISL Setu</h1>
            <p className="app-tagline">
              Real-time two-way bridge between Indian Sign Language and spoken language.
            </p>
          </div>
          <div className="mode-toggle">
            <button
              className={mode === "sign-to-text" ? "active" : ""}
              onClick={() => setMode("sign-to-text")}
            >
              🧏 Sign → Text
            </button>
            <button
              className={mode === "text-to-sign" ? "active" : ""}
              onClick={() => setMode("text-to-sign")}
            >
              ⌨️ Text → Sign
            </button>
          </div>
        </header>

        {mode === "sign-to-text" && (
          <div className="layout-grid">
            <section className="panel panel-left">
              <StatusBar
                connStatus={status}
                cameraStatus={cameraStatus}
                handsDetected={handsDetected}
                sessionId={sessionId}
              />
              {wsError && <div className="ws-error">{wsError}</div>}

              <SettingsPanel
                backendHost={backendHost}
                setBackendHost={setBackendHost}
                onReconnect={connect}
                languages={languages}
                setLanguages={setLanguages}
              />

              <CameraView
                videoRef={videoRef}
                canvasRef={canvasRef}
                cameraStatus={cameraStatus}
                cameraError={cameraError}
              />
            </section>

            <section className="panel panel-right">
              <div className="panel-header">
                <h2>Live gloss</h2>
                <p className="panel-subtitle">
                  Words detected from the deaf/mute signer. Edit any word before speaking.
                </p>
              </div>

              <GlossChips
                gloss={gloss}
                updateWord={updateWord}
                removeWord={removeWord}
              />

              <ControlBar
                onDone={handleDone}
                onClear={handleClear}
                onUndo={undoLast}
                translating={translating}
                glossEmpty={gloss.length === 0}
              />

              <SentencePanel sentences={sentences} />
            </section>
          </div>
        )}

        {mode === "text-to-sign" && (
          <section className="panel single-panel">
            <TextToSignPanel
              cleanHost={cleanHost}
              httpProtocol={httpProtocol}
              onConversation={saveConversation}
            />
          </section>
        )}
      </main>
    </div>
  );
}