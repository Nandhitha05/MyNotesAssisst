import axios from "axios";

const BASE = process.env.REACT_APP_API_URL || "http://localhost:5000";

const API = axios.create({ baseURL: BASE });

// Re-attach token on page reload
const saved = localStorage.getItem("token");
if (saved) API.defaults.headers.common.Authorization = `Bearer ${saved}`;

export function setAuth(token) {
  if (token) {
    API.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete API.defaults.headers.common.Authorization;
  }
}

export const login = (username, password) =>
  API.post("/login", { username, password });

export const upload = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return API.post("/upload", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const ask = (query, mode) => API.post("/ask", { query, mode });
export const listDocuments = () => API.get("/documents");
export const deleteDocument = (filename) =>
  API.delete("/document", { params: { filename } });
export const summarize = (filename) => API.post("/summarize", { filename });
export const generateNotes = (filename) => API.post("/notes", { filename });
export const generateQuiz = (filename) => API.post("/quiz", { filename });

export default API;
