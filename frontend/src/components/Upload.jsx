import React, { useState } from "react";

export default function Upload({ onIndexed }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const API_URL = import.meta.env.VITE_API_URL;


  // ⭐ Append new files (no overwrite)
  function addFiles(newFiles) {
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name.toLowerCase()));
      const uniqueIncoming = [...newFiles].filter(
        (f) => !existing.has(f.name.toLowerCase())
      );
      return [...prev, ...uniqueIncoming];
    });
  }

  // File picker
  function handleFileSelect(e) {
    addFiles(e.target.files);
  }

  // Drag & drop
  function handleDrop(e) {
    e.preventDefault();
    addFiles(e.dataTransfer.files);
  }

  function handleDragOver(e) {
    e.preventDefault();
  }

  // Upload logic
  async function handleUpload(e) {
    e.preventDefault();
    if (files.length === 0) return setMessage("Please select at least one file.");

    setLoading(true);
    setMessage("");

    const fd = new FormData();
    files.forEach((file) => fd.append("files", file));

    try {
      const res = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: fd,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      setMessage(
        `Uploaded ${data.files_processed} files. Indexed ${data.chunks_indexed} chunks ✔`
      );

      onIndexed();
    } catch (err) {
      setMessage("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="upload-card">
      <div className="upload-header">
        <span className="upload-icon">📁</span>
        <h2>Upload files</h2>
        <p>Select and upload multiple documents</p>
      </div>

      <form onSubmit={handleUpload} style={{ display: "flex", flexDirection: "column", height: "100%" }}>

        {/* DRAG & DROP BOX */}
        <div
          className="drop-zone"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <span className="cloud-icon">☁️</span>
          <p className="dz-title">Choose files or drag & drop here</p>
          <p className="dz-sub">PDF, DOC, TXT formats supported</p>

          <label className="browse-btn">
            Browse Files
            <input type="file" multiple onChange={handleFileSelect} />
          </label>
        </div>

        {/* FILE PREVIEW — SHOW ONLY 1 FILE HEIGHT */}
        {files.length > 0 && (
          <div
            className="file-preview"
            style={{
              maxHeight: "45px",          // show 1 item height
              overflowY: "auto",
              marginTop: "14px",
              paddingRight: "5px",
            }}
          >
            {files.map((file, i) => (
              <div key={i} className="file-item">
                📄 {file.name}
              </div>
            ))}
          </div>
        )}

        {/* BUTTON ALWAYS AT BOTTOM */}
        <button
          disabled={loading}
          className="upload-btn"
          style={{ marginTop: "auto" }}
        >
          {loading ? "Uploading..." : "Upload & Index"}
        </button>
      </form>

      {message && <p className="success-msg">{message}</p>}
    </div>
  );
}
