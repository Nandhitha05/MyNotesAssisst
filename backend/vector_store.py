import os
from langchain_community.vectorstores import FAISS
from embeddings import get_embeddings

INDEX_DIR = "faiss_index"


class VectorStoreManager:
    def __init__(self):
        self.embeddings = get_embeddings()
        self.store = None
        self._load()

    def _load(self):
        index_file = os.path.join(INDEX_DIR, "index.faiss")
        if os.path.exists(index_file):
            try:
                self.store = FAISS.load_local(
                    INDEX_DIR,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception as e:
                print(f"[vector_store] Failed to load existing index: {e}")
                self.store = None

    def _save(self):
        os.makedirs(INDEX_DIR, exist_ok=True)
        if self.store is not None:
            self.store.save_local(INDEX_DIR)

    def add_documents(self, docs):
        if not docs:
            return
        if self.store is None:
            self.store = FAISS.from_documents(docs, self.embeddings)
        else:
            self.store.add_documents(docs)
        self._save()

    def similarity_search(self, query: str, k: int = 6):
        if self.store is None:
            return []
        return self.store.similarity_search(query, k=k)

    def list_documents(self):
        if self.store is None:
            return []
        counts = {}
        for _, doc in self.store.docstore._dict.items():
            src = doc.metadata.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        return [{"filename": k, "chunks": v} for k, v in sorted(counts.items())]

    def delete_document(self, filename: str):
        if self.store is None:
            return
        ids_to_delete = [
            doc_id
            for doc_id, doc in self.store.docstore._dict.items()
            if doc.metadata.get("source") == filename
        ]
        if ids_to_delete:
            try:
                self.store.delete(ids_to_delete)
                self._save()
            except Exception as e:
                print(f"[vector_store] Delete failed: {e}")

    def get_document_chunks(self, filename: str):
        if self.store is None:
            return []
        return [
            doc
            for _, doc in self.store.docstore._dict.items()
            if doc.metadata.get("source") == filename
        ]
