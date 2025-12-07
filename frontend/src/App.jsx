import React, { useState } from "react";
import Upload from "./components/Upload";
import Chat from "./components/Chat";
import "./App.css";

export default function App() {
  const [enabled, setEnabled] = useState(false);

  return (
    <div className="app-wrapper">
      <div className="two-column-layout">
        
        {/* LEFT COLUMN — UPLOAD (1/3 width) */}
        <div className="left-panel">
          <Upload onIndexed={() => setEnabled(true)} />
        </div>

        {/* RIGHT COLUMN — CHAT (2/3 width) */}
        <div className="right-panel">
          <Chat enabled={enabled} />
        </div>

      </div>
    </div>
  );
}
