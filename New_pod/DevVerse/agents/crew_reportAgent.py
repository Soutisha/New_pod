"""
Report Agent — RAG-powered (DevVerse).
─────────────────────────────────────────────────────────────────────────
Compiles all agent outputs from the ChromaDB knowledge base into a
corporate-style project report via the RAG chain backed by Groq.

All output is filtered through the SHAP responsible AI guard.
"""

from pathlib import Path
from core.rag_engine import rag_query, refresh_knowledge_base
from core.responsible_ai import filter_output

_PROJECT_ROOT = Path(__file__).parent.parent.absolute()
_OUTPUTS_DIR  = _PROJECT_ROOT / "outputs"

_ROLE = (
    "You are a senior software consultant preparing corporate project reports "
    "for stakeholders and technical leadership. Write in a professional, "
    "clear tone with no markdown and no code blocks."
)

_REPORT_SECTIONS = """
1. Executive Summary
2. Project Overview
3. Functional Requirements (from user stories)
4. System Architecture
5. Technology Stack
6. Implementation Overview
7. Testing Strategy
8. Quality Assurance Results
9. Future Improvements
10. Conclusion
"""


def run_report_agent() -> str:
    """
    Read all prior agent outputs from disk, compile a corporate project report
    via RAG, and return the SHAP-filtered report text.
    """
    def _read(fname: str) -> str:
        p = _OUTPUTS_DIR / fname
        if not p.exists():
            p = _PROJECT_ROOT / fname
        return p.read_text(encoding="utf-8")[:2000] if p.exists() else "(Not generated yet)"

    stories = _read("User_Stories.txt")
    design  = _read("System_Design.txt")
    code    = _read("Implementation_Code.txt")
    tests   = _read("Test_Cases.txt")

    # ── Refresh KB so the latest docs are all queryable ──────────
    refresh_knowledge_base()

    # ── RAG query ─────────────────────────────────────────────────
    question = (
        "Using the project knowledge base, generate a professional corporate "
        "project report with the following sections:\n"
        f"{_REPORT_SECTIONS}\n"
        "Rules: Professional corporate tone. Clear section headers. "
        "No markdown. No code blocks.\n\n"
        f"USER STORIES SUMMARY:\n{stories[:800]}\n\n"
        f"SYSTEM DESIGN SUMMARY:\n{design[:800]}\n\n"
        f"IMPLEMENTATION SUMMARY:\n{code[:800]}\n\n"
        f"TEST CASES SUMMARY:\n{tests[:600]}"
    )

    raw_output = rag_query(question=question, system_role=_ROLE)

    # ── Responsible-AI output filter ───────────────────────────────
    safe_output, _, _ = filter_output(raw_output, stage="Report_Output")

    # ── Persist ───────────────────────────────────────────────────
    _OUTPUTS_DIR.mkdir(exist_ok=True)
    (_OUTPUTS_DIR / "Project_Report.txt").write_text(safe_output, encoding="utf-8")
    (_PROJECT_ROOT / "Project_Report.txt").write_text(safe_output, encoding="utf-8")

    return safe_output
