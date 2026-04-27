import React, { useEffect, useRef, useState } from "react";
import { ask, setAuth } from "../api";
import Message from "./Message";

const MODES = [
  { id: "auto", label: "Auto" },
  { id: "1mark", label: "1 Mark" },
  { id: "2marks", label: "2 Marks" },
  { id: "long", label: "Long Answer" },
  { id: "seminar", label: "Seminar" },
  { id: "presentation", label: "Presentation" },
];

const GREETING = {
  role: "assistant",
  content:
    "Hey! I'm MyNotesAssist — your study companion.\n\n" +
    "Here's what I can do:\n" +
    "- Answer questions from PDFs you upload (1 mark, 2 marks, long answer, seminar, presentation)\n" +
    "- If your notes don't cover something, I'll check trusted study sites (GeeksforGeeks, JavaTPoint, Wikipedia...)\n" +
    "- Generate summaries, structured notes, and quizzes from any document\n" +
    "- Just chat normally if you want — I'm not stuck to documents\n\n" +
    "What would you like to learn about today?",
  mode: "chat",
};

export default function ChatBox({
  token,
  activeChat,
  updateMessages,
  onNewChat,
  onRenameActive,
}) {
  const messages = activeChat?.messages || [];
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("auto");
  const [loading, setLoading] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    setAuth(token);
  }, [token]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Sidebar buttons (Summarise / Notes / Quiz) push results into the active chat.
  useEffect(() => {
    const handler = (e) => {
      updateMessages((m) => [...m, e.detail]);
    };
    window.addEventListener("ai-message", handler);
    return () => window.removeEventListener("ai-message", handler);
  }, [updateMessages]);

  const send = async () => {
    const q = input.trim();
    if (!q || loading) return;
    updateMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    try {
      const { data } = await ask(q, mode);
      updateMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
          mode: data.mode,
          source_kind: data.source_kind,
        },
      ]);
    } catch (err) {
      updateMessages((m) => [
        ...m,
        {
          role: "assistant",
          content:
            err?.response?.data?.error ||
            "Sorry, something went wrong. Please try again.",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const startTitleEdit = () => {
    setTitleDraft(activeChat?.name || "");
    setEditingTitle(true);
  };

  const commitTitle = () => {
    const next = titleDraft.trim();
    if (next && next !== activeChat?.name) onRenameActive?.(next);
    setEditingTitle(false);
  };

  const cancelTitle = () => {
    setEditingTitle(false);
    setTitleDraft("");
  };

  const visibleMessages =
    messages.length === 0 ? [GREETING] : messages;

  return (
    <main className="chatbox">
      <div className="chat-header">
        {editingTitle ? (
          <input
            autoFocus
            className="title-input"
            value={titleDraft}
            onChange={(e) => setTitleDraft(e.target.value)}
            onBlur={commitTitle}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitTitle();
              if (e.key === "Escape") cancelTitle();
            }}
          />
        ) : (
          <div
            className="title"
            title="Double-click to rename"
            onDoubleClick={startTitleEdit}
          >
            {activeChat?.name || "MyNotesAssist"}
            <span className="title-hint"> · double-click to rename</span>
          </div>
        )}
        <div className="mode-selector">
          {MODES.map((m) => (
            <button
              key={m.id}
              className={"mode-btn" + (mode === m.id ? " active" : "")}
              onClick={() => setMode(m.id)}
              title={m.label}
            >
              {m.label}
            </button>
          ))}
          <button
            className="mode-btn new-btn"
            onClick={onNewChat}
            title="Start a new chat"
          >
            + New chat
          </button>
        </div>
      </div>

      <div className="messages">
        {visibleMessages.map((m, i) => (
          <Message key={i} msg={m} />
        ))}
        {loading && (
          <Message msg={{ role: "assistant", content: "Thinking..." }} />
        )}
        <div ref={endRef} />
      </div>

      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask anything — from your notes, the web, or just chat. (Shift+Enter for newline)"
          rows={2}
        />
        <button onClick={send} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </main>
  );
}
