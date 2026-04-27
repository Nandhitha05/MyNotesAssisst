# 📚 MyNotesAssist

A full-stack **RAG (Retrieval-Augmented Generation) study assistant** for college notes.
Upload PDFs and ask questions — answers come from your documents first, fall back to trusted study sites (GeeksforGeeks, JavaTPoint, Wikipedia...) when your notes don't cover the topic, and finally to general knowledge so the assistant always replies. Supports exam-style answer modes (1 mark / 2 marks / Long / Seminar / Presentation), multi-chat history, and casual conversation.

---

## 🧱 Stack

| Layer    | Tech                                                    |
|----------|---------------------------------------------------------|
| Backend  | Python · Flask · LangChain · FAISS · OpenAI / Gemini    |
| Frontend | React (CRA) · axios                                     |
| Storage  | Local FAISS index + uploaded PDFs in `backend/uploads/` |

---

## 📁 Project Structure

```
MyNotesAssist/
├── backend/
│   ├── app.py                 # Flask API (login, upload, ask, ...)
│   ├── auth.py                # Single-user login + HMAC token
│   ├── document_loader.py     # PDF → chunks (PyPDF + splitter)
│   ├── embeddings.py          # OpenAI / Gemini embeddings
│   ├── vector_store.py        # FAISS persistence, list, delete
│   ├── rag_chain.py           # Mode-aware RAG pipeline + prompts
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── package.json
│   ├── public/index.html
│   └── src/
│       ├── index.js · index.css · App.js · App.css · api.js
│       └── components/
│           ├── Login.js
│           ├── Sidebar.js
│           ├── ChatBox.js
│           ├── Message.js
│           └── FileUpload.js
└── README.md
```

---

## ⚙️ Setup

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# Copy .env.example → .env, then edit it
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

python app.py
```

Backend runs at **http://localhost:5000**.

#### `.env` keys

| Key             | Notes                                   |
|-----------------|-----------------------------------------|
| `LLM_PROVIDER`  | `openai` (default) or `gemini`          |
| `OPENAI_API_KEY`| Required if using OpenAI                |
| `GOOGLE_API_KEY`| Required if using Gemini                |
| `APP_USERNAME`  | Login username (default: `admin`)       |
| `APP_PASSWORD`  | Login password (default: `admin123`)    |
| `APP_SECRET`    | HMAC signing secret — change for prod   |

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

Frontend runs at **http://localhost:3000** and proxies API calls to the backend.

---

## 🔑 Default Credentials

```
username: admin
password: admin123
```

(Change them in `backend/.env`.)

---

## 🎯 Answer Modes

The chat UI has a mode selector at the top right. Each mode wires up a different prompt, so the same question can produce a 1-mark, 2-marks, long, seminar, or presentation-style answer.

| Mode           | What you get |
|----------------|--------------|
| **Auto**       | Detects mode from your phrasing (default) |
| **1 Mark**     | One-line answer + brief justification. If the question contains options (a/b/c/d), the model picks the correct one. |
| **2 Marks**    | Clear explanation (4–6 sentences) + at least one example |
| **Long Answer**| Headings + sub-topics + working/process + textual flow charts (`A → B → C`) + examples + advantages + limitations + conclusion |
| **Seminar**    | Title, abstract, objectives, detailed content, examples, diagrams, conclusion, references, anticipated Q&A |
| **Presentation** | Slide-by-slide outline (Title, Agenda, content slides with bullets and speaker notes, Thank-You / Q&A) |

> If the answer is not in the uploaded documents, the assistant replies:
> *"This information is not available in the uploaded documents."*

The model also auto-detects mode keywords inside your question — e.g. `"...explain in long answer"`, `"...prepare a seminar on X"`, `"...generate a presentation on Y"`.

---

## 🔌 API Reference

All authenticated endpoints require:

```
Authorization: Bearer <token>
```

The token comes from `POST /login`.

| Method | Endpoint               | Body / Params                              | Description |
|--------|------------------------|--------------------------------------------|-------------|
| POST   | `/login`               | `{username, password}`                     | Returns `{success, token}` |
| POST   | `/upload`              | multipart `file=<pdf>`                     | Loads, chunks, embeds, indexes |
| POST   | `/ask`                 | `{query, mode}`                            | Returns `{answer, sources, mode}` |
| GET    | `/documents`           | —                                          | List indexed documents + chunk counts |
| DELETE | `/document?filename=…` | —                                          | Remove a document from index + disk |
| POST   | `/summarize`           | `{filename}`                               | Document summary |
| POST   | `/notes`               | `{filename}`                               | Structured study notes |
| POST   | `/quiz`                | `{filename}`                               | MCQs + short / long questions |
| GET    | `/health`              | —                                          | Health check |

---

## 🧪 Sample Test Flow

1. **Start the backend**, then the frontend.
2. Open <http://localhost:3000> and sign in with `admin` / `admin123`.
3. Click **+ Upload PDF** in the sidebar and pick a course PDF.
4. Wait for the "Uploaded · N chunks indexed" message.
5. Try these queries (in different modes):

| Mode           | Example question |
|----------------|------------------|
| 1 Mark         | `What is overfitting? 1 mark`                              |
| 1 Mark (MCQ)   | `Which is supervised? a) k-means b) linear regression c) PCA d) DBSCAN` |
| 2 Marks        | `Explain bias-variance tradeoff. 2 marks`                  |
| Long Answer    | `Explain the working of CNN in detail with diagrams`       |
| Seminar        | `Prepare a seminar on transformers`                        |
| Presentation   | `Generate a presentation on reinforcement learning`        |

6. In the sidebar, click **Summarise**, **Notes**, or **Quiz** on any uploaded document — the result streams into the chat.

---

## 🛡️ Constraints (as per spec)

- ✅ Uses **RAG** (retrieval + LLM), not a simple chatbot
- ✅ Uses **LangChain** for loaders, splitter, vector store, LLM wrappers
- ✅ Uses **FAISS** as the vector database (persisted to `backend/faiss_index/`)
- ✅ **Strict context**: refuses to answer outside the uploaded documents
- ✅ **Source attribution**: file name + page number on every grounded answer
- ✅ **Modular**: each backend concern lives in its own file

---

## 🗒️ Notes

- The FAISS index and uploaded PDFs persist between runs in `backend/faiss_index/` and `backend/uploads/`. Delete those folders to wipe state.
- Switch LLM providers any time by changing `LLM_PROVIDER` in `.env`. If you switch *embedding* providers after indexing, delete `backend/faiss_index/` and re-upload — embeddings from different models aren't compatible.
- For production, replace the simple HMAC token with proper JWT + HTTPS and rotate `APP_SECRET`.
