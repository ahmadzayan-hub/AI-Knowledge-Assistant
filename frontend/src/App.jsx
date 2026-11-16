import React, { useCallback, useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import MobileNav from "./components/MobileNav.jsx";
import Home from "./components/Home.jsx";
import Chat from "./components/Chat.jsx";
import Agent from "./components/Agent.jsx";
import KnowledgeBases from "./components/KnowledgeBases.jsx";
import Assistants from "./components/Assistants.jsx";
import Settings from "./components/Settings.jsx";
import { useStatus } from "./useStatus.js";
import { getKey, owuiModels, owuiKnowledge } from "./api.js";

// Set to "true" only by build/build-demo.mjs (the public, sample-data
// deployment). The real build (build/build.mjs) always defines this false —
// see the comment there for why it must be defined in both.
const DEMO = process.env.DEMO === "true";

export default function App() {
  const [view, setView] = useState("home");
  const [chatResetSignal, setChatResetSignal] = useState(0);
  const [models, setModels] = useState(null);
  const [kbs, setKbs] = useState(null);
  const [needKeyNotice, setNeedKeyNotice] = useState(!getKey());

  const status = useStatus(7000);

  const loadData = useCallback(async () => {
    if (!getKey()) {
      setNeedKeyNotice(true);
      throw new Error("API key required");
    }
    const [m, k] = await Promise.all([owuiModels(), owuiKnowledge()]);
    setModels(m);
    setKbs(k);
    setNeedKeyNotice(false);
  }, []);

  useEffect(() => {
    loadData().catch(() => {});
  }, [loadData]);

  function openWebUI() {
    if (DEMO) {
      alert(
        "This is a sample-data demo, not connected to a real AI stack. " +
          "The real app runs entirely on your own machine and opens your local " +
          "Open WebUI here — see the project README to set it up."
      );
      return;
    }
    window.open("http://localhost:8080", "_blank");
  }
  function newChat() {
    setChatResetSignal((s) => s + 1);
    setView("chat");
  }

  return (
    <>
      {DEMO && (
        <div className="demo-banner">
          <b>Demo — sample data only.</b> Not connected to a real AI stack. The
          real app runs 100% on your own machine —{" "}
          <a href="https://github.com/ahmadzayan-hub/AI-Knowledge-Assistant" target="_blank" rel="noreferrer">
            see the README
          </a>{" "}
          to set it up.
        </div>
      )}
      <div className="app">
        <Sidebar view={view} onNavigate={setView} onNewChat={newChat} status={status} />
      <main className="main">
        {needKeyNotice && (
          <div className="notice">
            <b>Setup needed</b> — paste your Open WebUI API key in{" "}
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                setView("set");
              }}
            >
              Settings
            </a>{" "}
            (Open WebUI → Settings → Account → API keys) to load knowledge bases and chat.
          </div>
        )}

        {view === "home" && (
          <Home status={status} kbs={kbs} models={models} onNavigate={setView} onOpenWebUI={openWebUI} onRefresh={loadData} />
        )}
        {view === "chat" && (
          <Chat models={models} kbs={kbs} hasKey={!!getKey()} onNeedKey={() => setView("set")} resetSignal={chatResetSignal} />
        )}
        {view === "agent" && (
          <Agent models={models} kbs={kbs} hasKey={!!getKey()} onNeedKey={() => setView("set")} />
        )}
        {view === "kb" && <KnowledgeBases kbs={kbs} />}
        {view === "as" && <Assistants models={models} />}
        {view === "set" && <Settings status={status} onSaveKey={loadData} />}
      </main>
      </div>
      <MobileNav view={view} onNavigate={setView} />
    </>
  );
}
