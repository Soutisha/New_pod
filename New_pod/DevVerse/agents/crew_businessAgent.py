"""
Business Analyst Agent — RAG-powered (DevVerse).
─────────────────────────────────────────────────────────────────────────
Reads extracted_reqmts.txt, retrieves context from ChromaDB, and generates
Agile user stories via Groq LLM through the LangChain RetrievalQA chain.

All input and output is filtered through the SHAP responsible AI guard.
"""

from pathlib import Path
from core.rag_engine import rag_query, refresh_knowledge_base
from core.responsible_ai import filter_input, filter_output

_PROJECT_ROOT = Path(__file__).parent.parent.absolute()
_OUTPUTS_DIR  = _PROJECT_ROOT / "outputs"

_ROLE = (
    "You are an experienced Business Analyst specialising in Agile software "
    "development. Translate raw business requirements into precise, testable "
    "user stories with clear acceptance criteria."
)


def run_business_analyst() -> str:
    """
    Read extracted_reqmts.txt, enrich with RAG context, generate user stories.
    """
    # Check outputs/ first, then project root
    req_file = _OUTPUTS_DIR / "extracted_reqmts.txt"
    if not req_file.exists():
        req_file = _PROJECT_ROOT / "extracted_reqmts.txt"
    if not req_file.exists():
        raise FileNotFoundError("extracted_reqmts.txt not found.")

    requirements = req_file.read_text(encoding="utf-8").strip()
    if not requirements:
        raise ValueError("Requirements file is empty.")

    # ── Responsible-AI input filter ────────────────────────────────
    safe_req, blocked, score = filter_input(requirements, stage="BA_Input")
    if blocked:
        raise RuntimeError(
            f"Input blocked by Responsible AI filter (score={score:.2f})."
        )

    # ── Refresh KB so the latest requirements are queryable ────────
    refresh_knowledge_base()

    # ── RAG query ─────────────────────────────────────────────────
    question = (
        "Based on the following project requirements, produce 5 to 8 detailed "
        "Agile user stories with acceptance criteria. Format each story as:\n\n"
        "Story N: <short title>\n"
        "As a <role>, I want to <action>, so that <benefit>.\n"
        "Acceptance Criteria:\n- <criterion 1>\n- <criterion 2>\n- <criterion 3>\n\n"
        "Rules: Plain English only. Each story must be specific and testable. "
        "Cover different user roles. No technical implementation details.\n\n"
        f"REQUIREMENTS:\n{safe_req[:3000]}"
    )

    raw_output = rag_query(question=question, system_role=_ROLE)

    # ── Responsible-AI output filter ───────────────────────────────
    safe_output, blocked_out, score_out = filter_output(raw_output, stage="BA_Output")

    # ── Persist ───────────────────────────────────────────────────
    _OUTPUTS_DIR.mkdir(exist_ok=True)
    (_OUTPUTS_DIR / "User_Stories.txt").write_text(safe_output, encoding="utf-8")
    (_PROJECT_ROOT / "User_Stories.txt").write_text(safe_output, encoding="utf-8")

    return safe_output
