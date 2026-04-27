import React, { useRef, useState } from "react";
import { upload } from "../api";

export default function FileUpload({ onUploaded }) {
  const inputRef = useRef();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const handle = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setMsg("Only PDF files are supported.");
      setTimeout(() => setMsg(""), 3000);
      return;
    }
    setBusy(true);
    setMsg(`Uploading ${file.name}...`);
    try {
      const { data } = await upload(file);
      setMsg(`✓ Uploaded · ${data.chunks} chunks indexed`);
      onUploaded?.();
    } catch (err) {
      setMsg(err?.response?.data?.error || "Upload failed.");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
      setTimeout(() => setMsg(""), 4000);
    }
  };

  return (
    <div className="upload">
      <button disabled={busy} onClick={() => inputRef.current?.click()}>
        {busy ? "Uploading..." : "+ Upload PDF"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={handle}
        hidden
      />
      {msg && <div className="upload-msg">{msg}</div>}
    </div>
  );
}
