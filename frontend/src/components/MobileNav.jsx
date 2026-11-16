import React from "react";
import { NAV } from "./Sidebar.jsx";

// Bottom tab bar for narrow screens, where the sidebar is hidden.
// Same destinations as the sidebar. Live system info is also shown in Settings.
export default function MobileNav({ view, onNavigate }) {
  return (
    <nav className="mobilenav" aria-label="Main">
      {NAV.map((n) => (
        <button
          key={n.id}
          type="button"
          aria-current={view === n.id ? "page" : undefined}
          onClick={() => onNavigate(n.id)}
        >
          <span className="mn-icon" aria-hidden="true">{n.icon}</span>
          <span className="mn-label">{n.short || n.label}</span>
        </button>
      ))}
    </nav>
  );
}
