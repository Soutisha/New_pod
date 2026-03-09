"""
Design Architect Agent — RAG-powered (DevVerse).
─────────────────────────────────────────────────────────────────────────
Reads User_Stories.txt, retrieves context from ChromaDB, and generates
a system architecture document (including a Mermaid flowchart) via the
LangChain RetrievalQA chain backed by Groq.

All input and output is filtered through the SHAP responsible AI guard.
"""

from pathlib import Path
from core.rag_engine import rag_query, refresh_knowledge_base
from core.responsible_ai import filter_input, filter_output

_PROJECT_ROOT = Path(__file__).parent.parent.absolute()
_OUTPUTS_DIR  = _PROJECT_ROOT / "outputs"

_ROLE = (
    "You are a senior software architect. Produce concise, accurate system "
    "architecture documents with valid Mermaid diagrams."
)


def run_design_agent() -> str:
    """
    Read User_Stories.txt, enrich with RAG context, generate architecture doc.
    """
    stories_file = _OUTPUTS_DIR / "User_Stories.txt"
    if not stories_file.exists():
        stories_file = _PROJECT_ROOT / "User_Stories.txt"
    if not stories_file.exists():
        raise FileNotFoundError("User_Stories.txt not found. Run Business Analyst first.")

    user_stories = stories_file.read_text(encoding="utf-8").strip()
    if not user_stories:
        raise ValueError("User_Stories.txt is empty.")

    # ── Responsible-AI input filter ────────────────────────────────
    safe_stories, blocked, score = filter_input(user_stories, stage="Design_Input")
    if blocked:
        raise RuntimeError(
            f"Input blocked by Responsible AI filter (score={score:.2f})."
        )

    # ── Refresh KB with the stories ──────────────────────────────
    refresh_knowledge_base()

    # ── RAG query ─────────────────────────────────────────────────
    question = (
        "Based on the following user stories, produce a concise system "
        "architecture document with EXACTLY THREE sections:\n\n"
        "1. SYSTEM OVERVIEW — 2-3 sentences.\n"
        "2. COMPONENTS — bullet list of key components (Frontend, Backend API, "
        "Database, Auth Service), one sentence each.\n"
        "3. ARCHITECTURE DIAGRAM — a single valid Mermaid flowchart:\n\n"
        "```mermaid\n"
        "flowchart TD\n"
        '    User["User Browser"] --> Frontend["Frontend / HTML+JS"]\n'
        '    Frontend --> API["Flask REST API"]\n'
        '    API --> DB["SQLite / Database"]\n'
        '    API --> Auth["Auth Module"]\n'
        "```\n\n"
        "DIAGRAM RULES: Only --> arrows. Node labels with spaces MUST be quoted. "
        "6-10 nodes max. No subgraphs unless essential.\n\n"
        "GENERAL RULES: Plain text only. No extra markdown headings. No HTML.\n\n"
        f"USER STORIES:\n{safe_stories[:3000]}"
    )

    raw_output = rag_query(question=question, system_role=_ROLE)

    # ── Responsible-AI output filter ───────────────────────────────
    safe_output, blocked_out, score_out = filter_output(raw_output, stage="Design_Output")

    # ── Persist ───────────────────────────────────────────────────
    _OUTPUTS_DIR.mkdir(exist_ok=True)
    (_OUTPUTS_DIR / "System_Design.txt").write_text(safe_output, encoding="utf-8")
    (_PROJECT_ROOT / "System_Design.txt").write_text(safe_output, encoding="utf-8")

    return safe_output
