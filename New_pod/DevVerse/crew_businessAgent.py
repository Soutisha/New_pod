"""
Business Analyst Agent for DevVerse.
Reads extracted requirements and generates structured Agile user stories.
"""

from langchain_groq import ChatGroq
from pathlib import Path
import os
import textwrap

# ── Environment ────────────────────────────────────────────
project_root = Path(__file__).parent.absolute()
env_path = project_root / ".env"

GROQ_API_KEY = ""
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            if line.strip().startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.strip().split("=", 1)[1]
                break

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# ── LLM ────────────────────────────────────────────────────
llm = None
if GROQ_API_KEY and not GROQ_API_KEY.startswith("your_"):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.3,
        api_key=GROQ_API_KEY,
        max_tokens=2048,
    )


def run_business_analyst() -> str:
    """
    Read extracted_reqmts.txt and generate well-structured Agile
    user stories with acceptance criteria. Returns the story text.
    Raises RuntimeError / FileNotFoundError on failure.
    """
    if not llm:
        raise RuntimeError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys"
        )

    req_file = project_root / "extracted_reqmts.txt"
    if not req_file.exists():
        raise FileNotFoundError("extracted_reqmts.txt not found.")

    requirements = req_file.read_text(encoding="utf-8").strip()
    if not requirements:
        raise ValueError("Requirements file is empty.")

    prompt = textwrap.dedent(f"""
        You are an experienced Business Analyst specialising in Agile software development.

        REQUIREMENTS:
        {requirements}

        ============================
        YOUR TASK
        ============================

        Produce 5 to 8 user stories that fully cover the requirements above.

        Use this exact format for every story:

        Story N: <short title>
        As a <role>, I want to <action>, so that <benefit>.

        Acceptance Criteria:
        - <criterion 1>
        - <criterion 2>
        - <criterion 3>

        ============================
        RULES
        ============================

        • Write in plain, clear English.
        • Each story must be specific and testable.
        • Cover different user roles where appropriate.
        • Do NOT include technical implementation details.
        • Do NOT include markdown headings or code blocks.
    """)

    response = llm.invoke(prompt)
    ba_text = response.content if hasattr(response, "content") else str(response)

    (project_root / "User_Stories.txt").write_text(ba_text, encoding="utf-8")

    return ba_text
