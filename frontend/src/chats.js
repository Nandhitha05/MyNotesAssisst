import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "mynotesassist.chats";
// Older builds wrote chats under different keys; both are migrated on first load.
const LEGACY_KEYS = ["mynotemaker.chats", "mynotemaker.chat.history"];

const newId = () =>
  Date.now().toString(36) + Math.random().toString(36).slice(2, 7);

function freshChat(messages = []) {
  return {
    id: newId(),
    name: "New chat",
    messages,
    updatedAt: Date.now(),
  };
}

function loadInitial() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && Array.isArray(parsed.chats) && parsed.chats.length) {
        return parsed;
      }
    }
  } catch {}

  for (const key of LEGACY_KEYS) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) continue;
      const parsed = JSON.parse(raw);
      localStorage.removeItem(key);
      if (parsed && Array.isArray(parsed.chats) && parsed.chats.length) {
        return parsed;
      }
      if (Array.isArray(parsed) && parsed.length) {
        const chat = freshChat(parsed);
        const firstUser = parsed.find((m) => m.role === "user");
        if (firstUser?.content) chat.name = nameFromContent(firstUser.content);
        return { chats: [chat], activeId: chat.id };
      }
    } catch {}
  }

  const chat = freshChat();
  return { chats: [chat], activeId: chat.id };
}

function nameFromContent(content) {
  return String(content)
    .slice(0, 40)
    .replace(/\s+/g, " ")
    .trim() || "Untitled";
}

export function useChats() {
  const [state, setState] = useState(loadInitial);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {}
  }, [state]);

  const activeChat =
    state.chats.find((c) => c.id === state.activeId) || state.chats[0];

  const newChat = useCallback(() => {
    setState((s) => {
      const chat = freshChat();
      return { chats: [chat, ...s.chats], activeId: chat.id };
    });
  }, []);

  const selectChat = useCallback((id) => {
    setState((s) => ({ ...s, activeId: id }));
  }, []);

  const renameChat = useCallback((id, name) => {
    const clean = (name || "").trim();
    setState((s) => ({
      ...s,
      chats: s.chats.map((c) =>
        c.id === id ? { ...c, name: clean || "Untitled" } : c
      ),
    }));
  }, []);

  const deleteChat = useCallback((id) => {
    setState((s) => {
      const remaining = s.chats.filter((c) => c.id !== id);
      if (remaining.length === 0) {
        const chat = freshChat();
        return { chats: [chat], activeId: chat.id };
      }
      const activeId = s.activeId === id ? remaining[0].id : s.activeId;
      return { chats: remaining, activeId };
    });
  }, []);

  const updateMessages = useCallback((updater) => {
    setState((s) => ({
      ...s,
      chats: s.chats.map((c) => {
        if (c.id !== s.activeId) return c;
        const next =
          typeof updater === "function" ? updater(c.messages) : updater;
        let name = c.name;
        if ((name === "New chat" || !name) && next.length) {
          const firstUser = next.find((m) => m.role === "user");
          if (firstUser?.content) name = nameFromContent(firstUser.content);
        }
        return { ...c, messages: next, name, updatedAt: Date.now() };
      }),
    }));
  }, []);

  return {
    chats: state.chats,
    activeId: state.activeId,
    activeChat,
    newChat,
    selectChat,
    renameChat,
    deleteChat,
    updateMessages,
  };
}
