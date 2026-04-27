import React, { useState } from "react";
import Login from "./components/Login";
import Sidebar from "./components/Sidebar";
import ChatBox from "./components/ChatBox";
import { setAuth } from "./api";
import { useChats } from "./chats";
import "./App.css";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [refreshKey, setRefreshKey] = useState(0);

  const {
    chats,
    activeId,
    activeChat,
    newChat,
    selectChat,
    renameChat,
    deleteChat,
    updateMessages,
  } = useChats();

  const handleLogin = (t) => {
    localStorage.setItem("token", t);
    setAuth(t);
    setToken(t);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setAuth(null);
    setToken(null);
  };

  if (!token) return <Login onLogin={handleLogin} />;

  return (
    <div className="app">
      <Sidebar
        token={token}
        refreshKey={refreshKey}
        onRefresh={() => setRefreshKey((k) => k + 1)}
        onLogout={handleLogout}
        chats={chats}
        activeId={activeId}
        onNewChat={newChat}
        onSelectChat={selectChat}
        onRenameChat={renameChat}
        onDeleteChat={deleteChat}
      />
      <ChatBox
        token={token}
        activeChat={activeChat}
        updateMessages={updateMessages}
        onNewChat={newChat}
        onRenameActive={(name) => renameChat(activeId, name)}
      />
    </div>
  );
}
