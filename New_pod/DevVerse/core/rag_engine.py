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
_COLLECTION   = "devverse_knowledge"
_LLM_MODEL    = "llama-3.1-8b-instant"

_KB_FILES: List[str] = [
    "extracted_reqmts.txt",
    "User_Stories.txt",
    "System_Design.txt",
    "Implementation_Code.txt",
    "Test_Cases.txt",
    "Project_Report.txt",
]

_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{system_role}\n\nAnswer using ONLY the context below.\n\nContext:\n{context}"),
    ("human",  "{question}"),
])

# ── Global caches (persist across calls in the same Python process) ───
_embeddings_cache: HuggingFaceEmbeddings | None = None
_vectorstore_cache: Chroma | None = None
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


def _load_documents() -> List[Document]:
    """Load KB text files — smaller chunks for faster retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,      # Smaller = faster embedding
        chunk_overlap=80,
    )
    docs: List[Document] = []
    for fname in _KB_FILES:
        fpath = _OUTPUTS_DIR / fname
        if not fpath.exists():
            fpath = _PROJECT_ROOT / fname
        if not fpath.exists():
            continue
        try:
            raw = fpath.read_text(encoding="utf-8").strip()
            if not raw:
                continue
            docs.extend(splitter.create_documents(
                [raw], metadatas=[{"source": fname}]
            ))
        except Exception as exc:
            print(f"⚠️  Could not load {fname}: {exc}")
    return docs


def _format_docs(docs: List[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


# ── Public API ────────────────────────────────────────────────────────

def build_vector_store(force_rebuild: bool = False) -> Chroma:
    """
    Build or load the ChromaDB store.
    Uses global cache — only hits disk once per process unless force_rebuild=True.
    """
    global _vectorstore_cache, _chain_cache

    if not force_rebuild and _vectorstore_cache is not None:
        return _vectorstore_cache      # ← instant return from RAM cache

    embeddings = _get_embeddings()

    if force_rebuild:
        if _vectorstore_cache is not None:
            try:
                _vectorstore_cache.delete_collection()
            except Exception:
                pass
        _chain_cache.clear()
        _vectorstore_cache = None

    if _CHROMA_DIR.exists() and not force_rebuild:
        _vectorstore_cache = Chroma(
            collection_name=_COLLECTION,
            embedding_function=embeddings,
            persist_directory=str(_CHROMA_DIR),
        )
        return _vectorstore_cache

    docs = _load_documents()
    if not docs:
        docs = [Document(
            page_content="DevVerse knowledge base initialising. No documents yet.",
            metadata={"source": "placeholder"},
        )]

    _vectorstore_cache = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=_COLLECTION,
        persist_directory=str(_CHROMA_DIR),
    )
    return _vectorstore_cache


def get_rag_chain(
    system_role: str = "You are a helpful DevVerse AI assistant.",
    k: int = 4,
    force_rebuild: bool = False,
):
    """
    Return a cached LCEL RAG chain for (system_role, k).
    Building the chain is fast, but we cache it anyway for pure speed.
    """
    cache_key = (system_role[:60], k)
    if not force_rebuild and cache_key in _chain_cache:
        return _chain_cache[cache_key]   # instant return

    llm        = _get_llm()
    vectorstore = build_vector_store(force_rebuild=force_rebuild)
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
    system_role: str = "You are a helpful DevVerse AI assistant.",
    k: int = 4,
    force_rebuild: bool = False,
) -> str:
    """One-shot RAG query — handles Groq rate limits with retry."""
    chain = get_rag_chain(system_role=system_role, k=k, force_rebuild=force_rebuild)
    
    # --- Rate limit retry attempt ---
    for _ in range(2):   # 2 attempts: first try, then retry once
        try:
            return chain.invoke(question)
        except Exception as exc:
            msg = str(exc).lower()
            if "rate limit" in msg or "429" in msg or "tpm" in msg:
                print(f"⚠️ Groq Rate limit hit. Cooling down for 15s…")
                time.sleep(15)
                continue  # next iteration is the retry
            raise exc
    
    # If both attempts failed, return fallback
    return "Error: RAG query could not complete due to rate limits."


def refresh_knowledge_base() -> None:
    """Rebuild ChromaDB from latest agent outputs. Clears all caches."""
    build_vector_store(force_rebuild=True)
