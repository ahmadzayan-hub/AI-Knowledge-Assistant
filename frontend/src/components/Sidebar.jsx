import React from "react";

export const NAV = [
  { id: "home", label: "Home", icon: "🏠" },
  { id: "chat", label: "Chat", icon: "💬" },
  { id: "agent", label: "Agent", icon: "🛠️" },
  { id: "kb", label: "Knowledge Bases", short: "Library", icon: "📚" },
  { id: "as", label: "Assistants", short: "Models", icon: "🤖" },
  { id: "set", label: "Settings", icon: "⚙️" },
];

export default function Sidebar({ view, onNavigate, onNewChat, status }) {
  const ram = status.ram.total
    ? `${(status.ram.total - status.ram.free).toFixed(1)} / ${status.ram.total} GB`
    : "—";
  const ramPct = status.ram.total
    ? Math.round(((status.ram.total - status.ram.free) / status.ram.total) * 100)
    : 0;
  const cpuPct = status.cpu ?? 0;

  return (
    <nav className="side" aria-label="Main">
      <div className="brand">
        <div className="logo">AI</div>
        <div>
          <b>Local AI Assistant</b>
          <small>Private AI knowledge hub</small>
        </div>
      </div>

      <button className="newchat" onClick={onNewChat}>
        ＋ New Chat
      </button>

      <div className="nav">
        {NAV.map((n) => (
          <button
            key={n.id}
            aria-current={view === n.id ? "true" : "false"}
            onClick={() => onNavigate(n.id)}
          >
            {n.icon} {n.label}
          </button>
        ))}
      </div>

      <div className="spacer" />

      <div className="statuscard" aria-label="System status">
        <div className="k" style={{ marginBottom: 6 }}>
          System status
        </div>
        <div className="srow">
          <span>
            <span className={"dot" + (status.ollamaUp ? " on" : "")} />
            Ollama
          </span>
          <b>{status.ollamaUp ? "v" + status.ollamaVersion : "down"}</b>
        </div>
        <div className="srow">
          <span>
            <span className={"dot" + (status.owuiUp ? " on" : "")} />
            Open WebUI
          </span>
          <b>{status.owuiUp ? "up" : "down"}</b>
        </div>
        <div className="srow">
          <span>Model</span>
          <b>{status.loadedModels[0]?.name || "none"}</b>
        </div>
        <div className="srow">
          <span>RAM</span>
          <b>{ram}</b>
        </div>
        <div className="bar">
          <i style={{ width: ramPct + "%" }} />
        </div>
        <div className="srow" style={{ marginTop: 4 }}>
          <span>CPU</span>
          <b>{status.cpu != null ? status.cpu + "%" : "—"}</b>
        </div>
        <div className="bar">
          <i style={{ width: cpuPct + "%" }} />
        </div>
      </div>
    </nav>
  );
}
