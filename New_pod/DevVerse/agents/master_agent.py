"""
Master Agent — CrewAI Orchestrator for DevVerse.
─────────────────────────────────────────────────────────────────────────
Defines a CrewAI Crew with five specialist agents that execute
sequentially, each agent's output becoming the next agent's input:

  1. Business Analyst  → extracts user stories from requirements (RAG)
  2. Design Architect  → produces system architecture from stories (RAG)
  3. Developer         → generates full-stack code from design (RAG)
  4. QA Tester         → writes pytest test suite from code (RAG)
  5. Report Writer     → compiles corporate project report (RAG)

Every agent uses RAG (ChromaDB + LangChain + Groq) — no bare LLM calls.
All inputs and outputs are passed through the SHAP responsible AI filter.

References:
  CrewAI docs    → https://docs.crewai.com/
  CrewAI tasks   → https://docs.crewai.com/core-concepts/Tasks/
  CrewAI agents  → https://docs.crewai.com/core-concepts/Agents/
  Groq API       → https://console.groq.com/docs/openai
  ChromaDB       → https://docs.trychroma.com/
  LangChain RAG  → https://python.langchain.com/docs/use_cases/question_answering/
  SHAP           → https://shap.readthedocs.io/en/latest/
"""

from __future__ import annotations

import os
import re
import time
import shutil
import textwrap
from pathlib import Path
from typing import Optional

# ── CrewAI / LLM factory ───────────────────────────────────────────────
from crewai import Agent, Task, Crew, Process, LLM

# ── Local modules ─────────────────────────────────────────────────────
from core.rag_engine import rag_query, refresh_knowledge_base, _load_groq_key
from core.responsible_ai import filter_input, filter_output, reset_shap_tracker

# ── Constants ─────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).parent.parent.absolute()
_OUTPUTS_DIR  = _PROJECT_ROOT / "outputs"
_LLM_MODEL    = "llama-3.1-8b-instant"


def _build_llm() -> LLM:
    """Return a Groq LLM instance using CrewAI's native litellm integration."""
    api_key = _load_groq_key()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not found. Get a free key at https://console.groq.com/keys"
        )
    return LLM(
        model=f"groq/{_LLM_MODEL}",
        api_key=api_key,
        temperature=0.3,
    )


# ── RAG-based tool wrapper ─────────────────────────────────────────────

def _rag_tool(prompt: str, role_desc: str, stage: str = "unknown",
              force_rebuild: bool = False) -> str:
    """
    Run a RAG query, applying responsible-AI filters on both sides.
    """
    safe_prompt, blocked_in, score_in = filter_input(prompt, stage=stage)
    if blocked_in:
        return safe_prompt

    raw_answer = rag_query(
        question=safe_prompt,
        system_role=role_desc,
        force_rebuild=force_rebuild,
    )

    safe_answer, blocked_out, score_out = filter_output(raw_answer, stage=stage)
    return safe_answer


# ── Agent definitions ─────────────────────────────────────────────────

def _make_business_analyst(llm: LLM) -> Agent:
    return Agent(
        role="Business Analyst",
        goal=(
            "Analyse the RFP requirements from the knowledge base and produce "
            "5–8 detailed Agile user stories with acceptance criteria."
        ),
        backstory=(
            "You are an experienced Business Analyst specialising in Agile "
            "software development. You translate raw business requirements into "
            "precise, testable user stories that guide the entire development team."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def _make_design_architect(llm: LLM) -> Agent:
    return Agent(
        role="Design Architect",
        goal=(
            "Convert the user stories into a clear system architecture document "
            "with a valid Mermaid flowchart diagram."
        ),
        backstory=(
            "You are a senior software architect with deep expertise in designing "
            "scalable web applications. You produce concise architecture documents "
            "that guide the development team."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def _make_developer(llm: LLM) -> Agent:
    return Agent(
        role="Senior Full-Stack Developer",
        goal=(
            "Generate a complete, immediately-runnable Flask web application "
            "(app.py + templates + static CSS) based on the system design."
        ),
        backstory=(
            "You are an expert full-stack engineer who writes production-quality "
            "Flask code with premium CSS UI. You follow strict coding standards "
            "and always output clean, structured FILE: blocks."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def _make_tester(llm: LLM) -> Agent:
    return Agent(
        role="QA Engineer",
        goal=(
            "Write a complete, executable pytest test suite covering unit, "
            "integration, and edge-case tests for the generated Flask app."
        ),
        backstory=(
            "You are a senior QA engineer who specialises in Python Flask "
            "testing. You produce clean pytest files that reveal bugs and "
            "guarantee quality."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def _make_report_writer(llm: LLM) -> Agent:
    return Agent(
        role="Senior Technical Report Writer",
        goal=(
            "Compile all agent outputs into a structured corporate project report "
            "suitable for stakeholders and technical leadership."
        ),
        backstory=(
            "You are a senior software consultant with years of experience "
            "writing executive-level project reports. You synthesise complex "
            "technical content into clear, professional documentation."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


# ── Task definitions ──────────────────────────────────────────────────

def _make_ba_task(agent: Agent, requirements: str) -> Task:
    safe_req, blocked, _ = filter_input(requirements, stage="BA")
    description = textwrap.dedent(f"""
        Use the knowledge base (ChromaDB RAG) to understand the project context,
        then produce 5–8 Agile user stories from the following requirements.

        REQUIREMENTS:
        {safe_req[:3000]}

        FORMAT each story exactly as:
        Story N: <short title>
        As a <role>, I want to <action>, so that <benefit>.
        Acceptance Criteria:
        - <criterion 1>
        - <criterion 2>
        - <criterion 3>

        Rules:
        • Plain English only — no markdown headings, no code blocks.
        • Each story must be specific and testable.
        • Do NOT include technical implementation details.
    """)
    return Task(
        description=description,
        expected_output="5–8 Agile user stories with acceptance criteria.",
        agent=agent,
    )


def _make_design_task(agent: Agent, context_task: Task) -> Task:
    description = textwrap.dedent("""
        Using the user stories from the Business Analyst, produce a concise
        system architecture document.

        Output must have THREE sections:
        1. SYSTEM OVERVIEW — 2-3 sentences.
        2. COMPONENTS     — bullet list of key components, one sentence each.
        3. ARCHITECTURE DIAGRAM — a single valid Mermaid flowchart:

        ```mermaid
        flowchart TD
            User["User Browser"] --> Frontend["Frontend / HTML+JS"]
            Frontend --> API["Flask REST API"]
            API --> DB["SQLite / Database"]
            API --> Auth["Auth Module"]
        ```

        DIAGRAM RULES:
        • Start: ```mermaid, first line: flowchart TD
        • Only --> arrows, node labels with spaces MUST be quoted.
        • 6-10 nodes maximum.

        GENERAL RULES:
        • Plain text only. No extra markdown headings, no HTML.
    """)
    return Task(
        description=description,
        expected_output="System architecture doc with Mermaid diagram.",
        agent=agent,
        context=[context_task],
    )


def _make_dev_task(agent: Agent, context_task: Task) -> Task:
    description = textwrap.dedent("""
        Using the system design, generate a complete Flask web application.

        STRICT OUTPUT RULES:
        1. Output ONLY FILE blocks — no explanations, no markdown prose.
        2. Format: FILE: <relative/path>\\n<complete file content>\\n
        3. Always produce: app.py, requirements.txt, static/style.css, and
           ALL needed templates/*.html files.

        BACKEND RULES (app.py):
        • Use Flask + SQLAlchemy (sqlite). Set DATABASE URI before db=SQLAlchemy(app).
        • Init DB: `with app.app_context(): db.create_all()` at the bottom.
        • NO flask-wtf. NO @app.before_first_request.
        • Use request.form.get('field') for form data.
        • Every route function must have a unique name.
        • End with: if __name__ == "__main__": app.run(host="0.0.0.0", port=5000, debug=True)

        FRONTEND RULES:
        • Premium SaaS-style UI. CSS min 400 lines.
        • Separate HTML for every route.
        • Auth pages: split-screen layout.
    """)
    return Task(
        description=description,
        expected_output="Complete Flask app in FILE: blocks (app.py, templates, CSS).",
        agent=agent,
        context=[context_task],
    )


def _make_test_task(agent: Agent, context_task: Task) -> Task:
    description = textwrap.dedent("""
        Write an ULTRA-COMPREHENSIVE, IMMEDIATELY EXECUTABLE pytest test suite.

        OUTPUT RULES:
        1. Output ONLY valid Python code — NO markdown, NO prose, NO ``` fences.
        2. Must run with: pytest test_app.py -v --tb=short
        3. Import: from app import app, db and any models found.

        START WITH EXACTLY THIS BOILERPLATE:
        import pytest, json, time
        from app import app, db

        @pytest.fixture(scope="module")
        def test_app():
            app.config["TESTING"] = True
            app.config["WTF_CSRF_ENABLED"] = False
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
            with app.app_context():
                db.create_all()
                yield app
                db.drop_all()

        @pytest.fixture
        def client(test_app):
            return test_app.test_client()

        THEN GENERATE ALL 7 CATEGORIES:
        1. SMOKE: app creation, 404 check, home page loads
        2. UNIT per route: GET/POST every route found, none return 500
        3. AUTH INTEGRATION: register→login→logout full flow, invalid creds rejected
        4. DATABASE: table creation, model CRUD, uniqueness constraints
        5. EDGE CASES + SECURITY: SQL injection attempt, XSS in input,
           empty fields, very long input (10000 chars), missing fields
        6. PERFORMANCE: home and login load in < 3 seconds
        7. RESPONSE VALIDATION: Content-Type correct, <html> present in body

        Use pytest.mark.parametrize for data-driven tests.
        Use try/except ImportError to skip if models not present.
        Every test must have a clear docstring.
    """)
    return Task(
        description=description,
        expected_output="Executable pytest file covering all routes and edge cases.",
        agent=agent,
        context=[context_task],
    )


def _make_report_task(agent: Agent, context_tasks: list[Task]) -> Task:
    description = textwrap.dedent("""
        Compile all prior agent outputs into a professional corporate project report.

        SECTIONS:
        1. Executive Summary
        2. Project Overview
        3. Functional Requirements
        4. System Architecture
        5. Technology Stack
        6. Implementation Overview
        7. Testing Strategy
        8. Quality Assurance Results
        9. Future Improvements
        10. Conclusion

        Rules: Professional tone. Clear sections. No markdown. No code blocks.
    """)
    return Task(
        description=description,
        expected_output="Full corporate project report with all 10 sections.",
        agent=agent,
        context=context_tasks,
    )


# ── Master Crew ───────────────────────────────────────────────────────

def run_master_crew(requirements: str) -> dict:
    """
    Orchestrate the full DevVerse pipeline via CrewAI.

    Args:
        requirements: Raw text extracted from the RFP PDF.

    Returns:
        A dict with keys: ba_text, design_text, dev_code, test_cases, report_text.

    Flow (sequential — each output feeds the next):
        Business Analyst → Design Architect → Developer → QA Tester → Report Writer
    """
    # --- Reset SHAP tracker for fresh pipeline ---
    reset_shap_tracker()

    # --- Input filter on the raw RFP ---
    safe_req, blocked, score = filter_input(requirements, stage="RFP_Upload")
    if blocked:
        raise ValueError(
            f"RFP content was blocked by the Responsible AI filter "
            f"(toxicity score: {score:.2f}). Please upload cleaner content."
        )

    # --- Ensure outputs directory exists ---
    _OUTPUTS_DIR.mkdir(exist_ok=True)

    # --- Refresh knowledge base with latest docs ---
    refresh_knowledge_base()

    # --- Build LLM ---
    llm = _build_llm()

    # --- Create agents ---
    ba_agent      = _make_business_analyst(llm)
    design_agent  = _make_design_architect(llm)
    dev_agent     = _make_developer(llm)
    test_agent    = _make_tester(llm)
    report_agent  = _make_report_writer(llm)

    # --- Create tasks (sequential chain) ---
    ba_task     = _make_ba_task(ba_agent, safe_req)
    design_task = _make_design_task(design_agent, ba_task)
    dev_task    = _make_dev_task(dev_agent, design_task)
    test_task   = _make_test_task(test_agent, dev_task)
    report_task = _make_report_task(report_agent, [ba_task, design_task, dev_task, test_task])

    # --- Assemble Crew ---
    def _cool_down(*args, **kwargs):
        print(f"\\n⏳ Crew task completed. Cooling down 15s to bypass Groq rate limits...\\n")
        time.sleep(15)

    crew = Crew(
        agents=[ba_agent, design_agent, dev_agent, test_agent, report_agent],
        tasks=[ba_task, design_task, dev_task, test_task, report_task],
        process=Process.sequential,
        task_callback=_cool_down,
        verbose=True,
    )

    # --- Kick off ---
    crew_result = crew.kickoff()

    # --- Extract individual task outputs ---
    task_outputs = crew_result.tasks_output if hasattr(crew_result, "tasks_output") else []

    def _get(idx: int, stage: str) -> str:
        if idx < len(task_outputs):
            raw = str(task_outputs[idx])
            safe, _, _ = filter_output(raw, stage=stage)
            return safe
        return ""

    ba_text     = _get(0, "BA_Output")
    design_text = _get(1, "Design_Output")
    dev_code    = _get(2, "Dev_Output")
    test_cases  = _get(3, "Test_Output")
    report_text = _get(4, "Report_Output")

    # --- Persist to outputs directory ---
    (_OUTPUTS_DIR / "User_Stories.txt").write_text(ba_text, encoding="utf-8")
    (_OUTPUTS_DIR / "System_Design.txt").write_text(design_text, encoding="utf-8")
    (_OUTPUTS_DIR / "Implementation_Code.txt").write_text(dev_code, encoding="utf-8")
    (_OUTPUTS_DIR / "Test_Cases.txt").write_text(test_cases, encoding="utf-8")
    (_OUTPUTS_DIR / "Project_Report.txt").write_text(report_text, encoding="utf-8")

    # --- Also persist to project root for backward compat ---
    (_PROJECT_ROOT / "User_Stories.txt").write_text(ba_text, encoding="utf-8")
    (_PROJECT_ROOT / "System_Design.txt").write_text(design_text, encoding="utf-8")
    (_PROJECT_ROOT / "Implementation_Code.txt").write_text(dev_code, encoding="utf-8")
    (_PROJECT_ROOT / "Test_Cases.txt").write_text(test_cases, encoding="utf-8")
    (_PROJECT_ROOT / "Project_Report.txt").write_text(report_text, encoding="utf-8")

    # --- Extract FILE: blocks to generated_project/ ---
    gen_dir = _PROJECT_ROOT / "generated_project"
    shutil.rmtree(gen_dir, ignore_errors=True)
    gen_dir.mkdir(parents=True, exist_ok=True)

    if dev_code:
        blocks = re.split(r'FILE:\s*([^\n\r]+)', dev_code)
        for i in range(1, len(blocks), 2):
            fname = blocks[i].strip()
            content = blocks[i+1]
            content = re.sub(r'^```[a-zA-Z]*\s*?\n', '', content, flags=re.MULTILINE)
            content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
            content = content.strip() + "\n"
            
            # Write safely inside generated_project
            fpath = (gen_dir / fname).resolve()
            if gen_dir in fpath.parents:
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_text(content, encoding="utf-8")

    # --- Rebuild KB with fresh outputs so chatbot can query them ---
    refresh_knowledge_base()

    return {
        "ba_text":     ba_text,
        "design_text": design_text,
        "dev_code":    dev_code,
        "test_cases":  test_cases,
        "report_text": report_text,
    }
