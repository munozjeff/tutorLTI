"""
RAG Service — Document ingestion and retrieval using ChromaDB.
Stores document chunks with embeddings locally. No data leaves the server.
"""
import os
import json
import logging
import hashlib
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# ChromaDB client — initialized lazily on first use
_chroma_client = None
_collections: Dict[str, object] = {}

CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', '/app/instance/chroma')
CHUNK_SIZE = 600          # characters per chunk
CHUNK_OVERLAP = 80        # overlap between chunks


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            logger.info(f"ChromaDB initialized at {CHROMA_PERSIST_DIR}")
        except ImportError:
            logger.error("chromadb not installed. Run: pip install chromadb")
            raise
    return _chroma_client


def _get_collection(resource_id: str):
    safe_id = 'rag_' + hashlib.md5(resource_id.encode()).hexdigest()[:12]
    if safe_id not in _collections:
        client = _get_client()
        _collections[safe_id] = client.get_or_create_collection(
            name=safe_id,
            metadata={"hnsw:space": "cosine"}
        )
    return _collections[safe_id]


def _chunk_text(text: str) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) > 40]  # skip tiny chunks


def _embed(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings. Tries Ollama first (local), falls back to
    a simple TF-IDF hash embedding for offline environments.
    """
    try:
        import requests as req
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
        resp = req.post(
            f"{base_url}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": texts[0]},
            timeout=30
        )
        if resp.status_code == 200:
            # Batch embed sequentially (simple approach)
            embeddings = []
            for text in texts:
                r = req.post(
                    f"{base_url}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text},
                    timeout=30
                )
                embeddings.append(r.json()['embedding'])
            return embeddings
    except Exception:
        pass

    # Fallback: simple hash-based pseudo-embedding (256 dims)
    import struct
    def hash_embed(text: str) -> List[float]:
        vec = []
        for i in range(256):
            h = hashlib.sha256(f"{i}:{text[:200]}".encode()).digest()
            val = struct.unpack('f', h[:4])[0]
            vec.append(float(val))
        norm = max(abs(v) for v in vec) or 1.0
        return [v / norm for v in vec]

    return [hash_embed(t) for t in texts]


def extract_text(file_path: str, mime_type: str) -> str:
    """Extract plain text from uploaded file."""
    ext = Path(file_path).suffix.lower()
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif ext == '.pdf':
            import PyPDF2
            text = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or '')
            return '\n'.join(text)
        elif ext in ('.docx', '.doc'):
            import docx as python_docx
            doc = python_docx.Document(file_path)
            return '\n'.join(p.text for p in doc.paragraphs)
        else:
            # Last resort: read as text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        logger.error(f"Text extraction failed for {file_path}: {e}")
        return ""


def ingest_document(file_path: str, doc_id: str, resource_id: str, filename: str) -> int:
    """
    Ingest a document into the vector store for a given resource.
    Returns the number of chunks stored.
    """
    text = extract_text(file_path, '')
    if not text.strip():
        raise ValueError("No text could be extracted from the document")

    chunks = _chunk_text(text)
    if not chunks:
        raise ValueError("Document is too short to index")

    embeddings = _embed(chunks)
    collection = _get_collection(resource_id)

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{'doc_id': doc_id, 'filename': filename, 'chunk': i} for i in range(len(chunks))]

    # Delete old chunks for this doc (re-ingest scenario)
    try:
        existing = collection.get(where={"doc_id": doc_id})
        if existing['ids']:
            collection.delete(ids=existing['ids'])
    except Exception:
        pass

    collection.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metadatas)
    logger.info(f"Ingested {len(chunks)} chunks for doc {doc_id} in resource {resource_id}")
    return len(chunks)


def retrieve_context(query: str, resource_id: str, k: int = 3) -> str:
    """
    Find the k most relevant document chunks for a given query.
    Returns a formatted string to inject into the LLM prompt.
    """
    try:
        query_embedding = _embed([query])[0]
        collection = _get_collection(resource_id)

        if collection.count() == 0:
            return ""

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, collection.count()),
            include=['documents', 'metadatas']
        )

        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]

        if not docs:
            return ""

        context_parts = []
        for doc, meta in zip(docs, metas):
            filename = meta.get('filename', 'Documento')
            context_parts.append(f"[{filename}]\n{doc}")

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return ""


def delete_document(doc_id: str, resource_id: str) -> bool:
    """Remove all chunks for a document from the vector store."""
    try:
        collection = _get_collection(resource_id)
        existing = collection.get(where={"doc_id": doc_id})
        if existing['ids']:
            collection.delete(ids=existing['ids'])
            return True
        return False
    except Exception as e:
        logger.error(f"Delete doc error: {e}")
        return False


def list_documents(resource_id: str) -> List[Dict]:
    """List unique documents indexed for a resource."""
    try:
        collection = _get_collection(resource_id)
        all_items = collection.get(include=['metadatas'])
        seen = {}
        for meta in all_items.get('metadatas', []):
            did = meta.get('doc_id')
            if did and did not in seen:
                seen[did] = {'doc_id': did, 'filename': meta.get('filename', did)}
        return list(seen.values())
    except Exception as e:
        logger.warning(f"List docs error: {e}")
        return []
