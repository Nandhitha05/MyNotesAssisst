from langchain_community.document_loaders import PyPDFLoader
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


def load_pdf(path: str, filename: str):
    """Load a PDF file, split it into chunks, and tag each chunk with its source filename."""
    loader = PyPDFLoader(path)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    for c in chunks:
        c.metadata["source"] = filename
        # PyPDFLoader sets page (0-indexed); normalise to 1-indexed for humans
        if "page" in c.metadata and isinstance(c.metadata["page"], int):
            c.metadata["page"] = c.metadata["page"] + 1
    return chunks
