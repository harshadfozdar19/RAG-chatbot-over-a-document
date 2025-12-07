import React, { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function Chat({ enabled }) {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);

  async function ask(e) {
    e.preventDefault();
    if (!q) return;

    const userMsg = { role: "user", text: q };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:5000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          history: [...messages, userMsg], // send chat history
          question: q,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      const botMsg = { role: "assistant", text: data.answer };
      setMessages((prev) => [...prev, botMsg]);
      setQ("");

    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Error: " + err.message },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2>🤖 Chat with Your Document</h2>

      {!enabled && <p className="note">Upload a document to enable chat.</p>}

      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <div className="bubble">
              {/* 👇 RENDER MARKDOWN PROPERLY */}
              <ReactMarkdown>{m.text}</ReactMarkdown>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={ask} className="ask-area">
        <input
          placeholder={
            enabled ? "Ask something..." : "Upload a document first"
          }
          disabled={!enabled || loading}
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />

        <button disabled={!enabled || loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>
    </div>
  );
}
