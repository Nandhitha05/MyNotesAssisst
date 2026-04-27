import React, { useEffect, useState } from "react";
import FileUpload from "./FileUpload";
import {
  listDocuments,
  deleteDocument,
  setAuth,
  summarize,
  generateNotes,
  generateQuiz,
} from "../api";

export default function Sidebar({
  token,
  refreshKey,
  onRefresh,
  onLogout,
  chats = [],
  activeId,
  onNewChat,
  onSelectChat,
  onRenameChat,
  onDeleteChat,
}) {
  const [docs, setDocs] = useState([]);
  const [busy, setBusy] = useState(null);
  const [editingChatId, setEditingChatId] = useState(null);
  const [editingDraft, setEditingDraft] = useState("");

  useEffect(() => {
    setAuth(token);
    listDocuments()
      .then((r) => setDocs(r.data.documents || []))
      .catch(() => setDocs([]));
  }, [token, refreshKey]);

  const dispatchAi = (payload) => {
    window.dispatchEvent(new CustomEvent("ai-message", { detail: payload }));
  };

  const handleDelete = async (filename) => {
    if (!window.confirm(`Delete "${filename}"?`)) return;
    await deleteDocument(filename);
    onRefresh();
  };

  const runAction = async (filename, key, fn, titlePrefix) => {
    setBusy(`${filename}:${key}`);
    dispatchAi({
      role: "user",
      content: `${titlePrefix}: ${filename}`,
    });
    try {
      const { data } = await fn(filename);
      dispatchAi({
        role: "assistant",
        content: data.answer || "(empty response)",
        sources: data.sources || [],
        mode: data.mode,
      });
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.message ||
        "Failed to run action. Please try again.";
      dispatchAi({
        role: "assistant",
        content: msg,
        error: true,
      });
    } finally {
      setBusy(null);
    }
  };

  const startRename = (chat) => {
    setEditingChatId(chat.id);
    setEditingDraft(chat.name || "");
  };

  const commitRename = () => {
    if (editingChatId) {
      onRenameChat?.(editingChatId, editingDraft);
    }
    setEditingChatId(null);
    setEditingDraft("");
  };

  const cancelRename = () => {
    setEditingChatId(null);
    setEditingDraft("");
  };

  const confirmDeleteChat = (chat) => {
    if (!window.confirm(`Delete chat "${chat.name}"?`)) return;
    onDeleteChat?.(chat.id);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>📚 MyNotesAssist</h2>
        <p className="tagline">RAG knowledge assistant</p>
      </div>

      <div className="chats">
        <div className="chats-header">
          <h3>Chats</h3>
          <button className="new-chat-btn" onClick={onNewChat} title="New chat">
            + New
          </button>
        </div>
        <div className="chat-list">
          {chats.length === 0 && (
            <p className="muted small">No chats yet.</p>
          )}
          {chats.map((c) => {
            const isActive = c.id === activeId;
            const isEditing = editingChatId === c.id;
            return (
              <div
                key={c.id}
                className={"chat-item" + (isActive ? " active" : "")}
                onClick={() => !isEditing && onSelectChat?.(c.id)}
              >
                {isEditing ? (
                  <input
                    autoFocus
                    className="chat-rename-input"
                    value={editingDraft}
                    onChange={(e) => setEditingDraft(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    onBlur={commitRename}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") commitRename();
                      if (e.key === "Escape") cancelRename();
                    }}
                  />
                ) : (
                  <span
                    className="chat-name"
                    title={c.name}
                    onDoubleClick={(e) => {
                      e.stopPropagation();
                      startRename(c);
                    }}
                  >
                    💬 {c.name || "Untitled"}
                  </span>
                )}
                {!isEditing && (
                  <span className="chat-actions">
                    <button
                      className="icon-btn"
                      title="Rename"
                      onClick={(e) => {
                        e.stopPropagation();
                        startRename(c);
                      }}
                    >
                      ✎
                    </button>
                    <button
                      className="icon-btn danger"
                      title="Delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        confirmDeleteChat(c);
                      }}
                    >
                      ✕
                    </button>
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <FileUpload onUploaded={onRefresh} />

      <div className="docs">
        <h3>Your documents</h3>
        {docs.length === 0 && (
          <p className="muted small">No documents yet. Upload a PDF to start.</p>
        )}
        {docs.map((d) => (
          <div key={d.filename} className="doc-item">
            <div className="doc-name" title={d.filename}>
              📄 {d.filename}
            </div>
            <div className="doc-meta">{d.chunks} chunks</div>
            <div className="doc-actions">
              <button
                disabled={!!busy}
                onClick={() =>
                  runAction(d.filename, "summary", summarize, "Summarise")
                }
              >
                {busy === `${d.filename}:summary` ? "..." : "Summarise"}
              </button>
              <button
                disabled={!!busy}
                onClick={() =>
                  runAction(d.filename, "notes", generateNotes, "Notes from")
                }
              >
                {busy === `${d.filename}:notes` ? "..." : "Notes"}
              </button>
              <button
                disabled={!!busy}
                onClick={() =>
                  runAction(d.filename, "quiz", generateQuiz, "Quiz from")
                }
              >
                {busy === `${d.filename}:quiz` ? "..." : "Quiz"}
              </button>
              <button
                className="danger"
                onClick={() => handleDelete(d.filename)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      <button className="logout" onClick={onLogout}>
        Sign out
      </button>
    </aside>
  );
}
