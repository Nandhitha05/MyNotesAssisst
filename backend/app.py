import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from auth import verify_credentials, create_token, verify_token
from document_loader import load_pdf
from vector_store import VectorStoreManager
from rag_chain import RAGChain

load_dotenv(override=True)
print(f"[boot] LLM_PROVIDER={os.getenv('LLM_PROVIDER')} GEMINI_MODEL={os.getenv('GEMINI_MODEL')} GEMINI_EMBEDDING_MODEL={os.getenv('GEMINI_EMBEDDING_MODEL')}")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

vector_store = VectorStoreManager()
rag = RAGChain(vector_store)


def _check_auth():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    return verify_token(auth[7:]) is not None


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    if verify_credentials(username, password):
        return jsonify({"success": True, "token": create_token(username)})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route("/upload", methods=["POST"])
def upload():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(save_path)
    try:
        chunks = load_pdf(save_path, file.filename)
        vector_store.add_documents(chunks)
        return jsonify({"success": True, "filename": file.filename, "chunks": len(chunks)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Failed to process PDF: {type(e).__name__}: {e}"}), 500


@app.route("/ask", methods=["POST"])
def ask():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    mode = data.get("mode", "auto")
    if not query:
        return jsonify({"error": "Empty query"}), 400
    try:
        return jsonify(rag.answer(query, mode=mode))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


@app.route("/documents", methods=["GET"])
def documents():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"documents": vector_store.list_documents()})


@app.route("/document", methods=["DELETE"])
def delete_document():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "filename required"}), 400
    vector_store.delete_document(filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
    return jsonify({"success": True})


@app.route("/summarize", methods=["POST"])
def summarize():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename required"}), 400
    try:
        return jsonify(rag.summarize(filename))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


@app.route("/notes", methods=["POST"])
def notes():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename required"}), 400
    try:
        return jsonify(rag.generate_notes(filename))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


@app.route("/quiz", methods=["POST"])
def quiz():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename required"}), 400
    try:
        return jsonify(rag.generate_quiz(filename))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
