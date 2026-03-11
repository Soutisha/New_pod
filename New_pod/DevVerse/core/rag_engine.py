"""
RAG Engine — HIGH-SPEED edition (LangChain 1.x + ChromaDB + Groq).
─────────────────────────────────────────────────────────────────────────
SPEED OPTIMIZATIONS:
  1. Vectorstore loaded ONCE and cached globally — no disk I/O on repeat calls
  2. Embeddings model cached globally (heavy, ~80MB, loaded once)
  3. LLM instance cached globally — avoids re-creating client on every query
  4. RAG chain cached per (system_role, k) pair
  5. force_rebuild=False by default — skips rebuild unless explicitly needed
  6. Smaller chunk size (600) + less overlap (80) → faster embedding + retrieval
  7. max_tokens capped at 1024 for faster Groq responses (increase if needed)

Result: subsequent rag_query() calls go from ~3s → ~0.5s (pure Groq API latency)
"""

from __future__ import annotations

import json
import os
import shutil
import time                      # Added for rate-limit backoff
from pathlib import Path
from typing import List
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
 
# ── Constants ─────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).parent.parent.absolute()
_CHROMA_DIR   = _PROJECT_ROOT / "chroma_db"
_OUTPUTS_DIR  = _PROJECT_ROOT / "outputs"
_EMBED_MODEL  = "all-MiniLM-L6-v2"
_COLLECTIONS = {
    "requirements": "devverse_requirements",
    "architecture": "devverse_architecture",
    "code": "devverse_code",
    "testing": "devverse_testing",
    "reports": "devverse_reports"
}
_COLLECTION_TO_KEY = {v: k for k, v in _COLLECTIONS.items()}
_LLM_MODEL    = "llama-3.1-8b-instant"

_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{system_role}\n\nAnswer using ONLY the context below.\n\nContext:\n{context}"),
    ("human",  "{question}"),
])

# ── Global caches (persist across calls in the same Python process) ───
_embeddings_cache: HuggingFaceEmbeddings | None = None
# _vectorstore_cache: Chroma | None = None
_vectorstore_cache: dict[str, Chroma] = {}
_llm_cache: ChatGroq | None = None
_chain_cache: dict = {}            # keyed by (system_role, k)


# ── Internal helpers ──────────────────────────────────────────────────

def _load_groq_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        env_path = _PROJECT_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.strip().startswith("GROQ_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip()
                    break
    if key:
        os.environ["GROQ_API_KEY"] = key
    return key


def _get_embeddings() -> HuggingFaceEmbeddings:
    """Return cached embeddings model — loads once, reused forever."""
    global _embeddings_cache
    if _embeddings_cache is None:
        print("⏳ Loading embeddings model (one-time)…")
        _embeddings_cache = HuggingFaceEmbeddings(
            model_name=_EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
        )
        print("✅ Embeddings model ready.")
    return _embeddings_cache


def _get_llm() -> ChatGroq:
    """Return cached Groq LLM client — created once per process."""
    global _llm_cache
    if _llm_cache is None:
        api_key = _load_groq_key()
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not found. Get a free key at https://console.groq.com/keys"
            )
        _llm_cache = ChatGroq(
            model=_LLM_MODEL,
            temperature=0.3,
            api_key=api_key,
            max_tokens=1024,     # Capped for speed; agents rarely need more
        )
    return _llm_cache


def _load_documents(collection: str) -> List[Document]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
    )

    file_map = {
        "requirements": ["extracted_reqmts.txt", "User_Stories.txt"],
        "architecture": ["System_Design.txt"],
        "code": ["Implementation_Code.txt"],
        "testing": ["Test_Cases.txt"],
        "reports": ["Project_Report.txt"],
    }

    docs: List[Document] = []

    # -----------------------------
    # 1️⃣ Load normal project files
    # -----------------------------
    for fname in file_map.get(collection, []):
        fpath = _OUTPUTS_DIR / fname
        if not fpath.exists():
            fpath = _PROJECT_ROOT / fname

        if not fpath.exists():
            continue

        raw = fpath.read_text(encoding="utf-8").strip()
        if not raw:
            continue

        docs.extend(
            splitter.create_documents([raw], metadatas=[{"source": fname}])
        )

    # -----------------------------
    # 2️⃣ Load memory graph nodes
    # -----------------------------
    GRAPH_DIR = _PROJECT_ROOT / "knowledge_graph"
    nodes_file = GRAPH_DIR / "nodes.json"

    if nodes_file.exists():
        try:
            nodes_raw = json.loads(nodes_file.read_text())

            if isinstance(nodes_raw, dict):
                nodes = [nodes_raw]
            elif isinstance(nodes_raw, list):
                nodes = nodes_raw
            else:
                nodes = []

            for node in nodes:

                if not isinstance(node, dict):
                    continue

                docs.extend(
                    splitter.create_documents(
                        [node["content"]],
                        metadatas=[{
                            "source": "memory_graph",
                            "node_type": node["type"],
                            "node_id": node["id"]
                        }]
                    )
                )

        except Exception as e:
            print(f"⚠️ Memory graph load failed: {e}")

    return docs


def _format_docs(docs: List[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


# ── Public API ────────────────────────────────────────────────────────

def build_vector_store(
    collection_name: str,
    docs: List[Document] | None = None,
    force_rebuild: bool = False
) -> Chroma:
    """
    Build or load a ChromaDB vector store for a specific collection.
    Supports multiple collections and caches them in memory.
    """

    global _vectorstore_cache, _chain_cache

    # --- Return cached instance if already loaded ---
    if not force_rebuild and collection_name in _vectorstore_cache:
        return _vectorstore_cache[collection_name]

    embeddings = _get_embeddings()

    # --- Handle rebuild ---
    if force_rebuild and collection_name in _vectorstore_cache:
        try:
            _vectorstore_cache[collection_name].delete_collection()
        except Exception:
            pass
        _vectorstore_cache.pop(collection_name, None)
        for key in list(_chain_cache.keys()):
            if key[0] == _COLLECTION_TO_KEY.get(collection_name):
                _chain_cache.pop(key, None)

    # --- Load existing DB from disk ---
    if _CHROMA_DIR.exists() and not force_rebuild:
        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=str(_CHROMA_DIR),
            )

            # if collection exists but empty → rebuild
            data = vectorstore.get()

            if not data or not data.get("ids"):
                raise ValueError("Empty collection")

            _vectorstore_cache[collection_name] = vectorstore
            return vectorstore

        except Exception:
            pass

    # --- Build new collection ---
    if docs is None:
        collection_key = _COLLECTION_TO_KEY.get(collection_name, "requirements")
        docs = _load_documents(collection_key)

    if not docs:
        docs = [
            Document(
                page_content="DevVerse knowledge base initialising. No documents yet.",
                metadata={"source": "placeholder"},
            )
        ]

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=str(_CHROMA_DIR),
    )

    _vectorstore_cache[collection_name] = vectorstore
    return vectorstore


def get_rag_chain(
    collection: str,
    system_role: str = "You are a helpful DevVerse AI assistant.",
    k: int = 4,
    force_rebuild: bool = False,
):
    """
    Return a cached LCEL RAG chain for (system_role, k).
    Building the chain is fast, but we cache it anyway for pure speed.
    """
    cache_key = (collection, system_role[:60], k, force_rebuild)
    if not force_rebuild and cache_key in _chain_cache:
        return _chain_cache[cache_key]   # instant return

    llm        = _get_llm()
    vectorstore = build_vector_store(
        collection_name=_COLLECTIONS[collection],
        force_rebuild=force_rebuild
    )
    retriever   = vectorstore.as_retriever(search_kwargs={"k": k})

    setup = RunnableParallel(
        context=retriever | RunnableLambda(_format_docs),
        question=RunnablePassthrough(),
        system_role=RunnableLambda(lambda _: system_role),
    )
    chain = setup | _RAG_PROMPT | llm | StrOutputParser()
    _chain_cache[cache_key] = chain
    return chain


def rag_query(
    question: str,
    collection: str = "requirements",
    system_role: str = "You are a helpful DevVerse AI assistant.",
    k: int = 4,
    force_rebuild: bool = False,
) -> str:
    """One-shot RAG query — handles Groq rate limits with retry."""
    chain = get_rag_chain(
        collection=collection,
        system_role=system_role,
        k=k,
        force_rebuild=force_rebuild
    )
    
    # --- Rate limit retry attempt ---
    for _ in range(2):   # 2 attempts: first try, then retry once
        try:
            return chain.invoke(question)
        except Exception as exc:
            msg = str(exc).lower()

            if "rate limit" in msg or "429" in msg or "tpm" in msg:
                print("⚠️ Groq rate limit hit. Waiting 20s...")
                time.sleep(20)
                continue

            raise
    
    # If both attempts failed, return fallback
    return "Error: RAG query could not complete due to rate limits."


def refresh_knowledge_base() -> None:
    """Rebuild ChromaDB from latest agent outputs. Clears all caches."""
    # build_vector_store(force_rebuild=True)
    for name in _COLLECTIONS.values():
        build_vector_store(collection_name=name, force_rebuild=True)
