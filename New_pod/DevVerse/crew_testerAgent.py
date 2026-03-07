"""
Tester Agent for DevVerse.
Reads Implementation_Code.txt and generates a clean, executable
pytest test suite covering unit tests, integration tests, and edge cases.
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
        temperature=0.2,
        api_key=GROQ_API_KEY,
        max_tokens=3000,
    )


def run_tester_agent() -> str:
    """
    Generate a complete, executable pytest test suite for the
    generated Flask application. Returns the raw test code string.
    Raises RuntimeError / FileNotFoundError on failure.
    """
    if not llm:
        raise RuntimeError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys"
        )

    code_file = project_root / "Implementation_Code.txt"
    if not code_file.exists():
        raise FileNotFoundError(
            "Implementation_Code.txt not found. Run the Developer Agent first."
        )

    code = code_file.read_text(encoding="utf-8").strip()
    if not code:
        raise ValueError("Implementation_Code.txt is empty.")

    # Truncate to avoid token overflow (LLM context limit)
    code_excerpt = code[:4000]

    prompt = textwrap.dedent(f"""
        You are a senior QA engineer specialising in Python Flask applications.
        Your job is to write a complete, executable pytest test suite.

        Here is the generated Flask application code (possibly truncated):

        {code_excerpt}

        ============================
        STRICT OUTPUT RULES
        ============================

        1. Output ONLY valid Python code — no markdown, no prose, no explanations.
        2. The file must be executable with:  pytest test_app.py -v
        3. Do NOT include any text before the first import statement.
        4. Do NOT use markdown code fences (no ``` anywhere).

        ============================
        REQUIRED TEST STRUCTURE
        ============================

        import pytest
        from app import app   # Flask test client

        @pytest.fixture
        def client():
            app.config["TESTING"] = True
            with app.test_client() as c:
                yield c

        # ── Unit Tests ─────────────────────────────────────
        # Test each route returns HTTP 200 (or expected redirect).
        # Test response Content-Type is text/html.

        # ── Integration Tests ──────────────────────────────
        # Test form submissions with valid data.
        # Test form submissions with invalid/missing data.
        # Test that expected keywords appear in HTML responses.

        # ── Edge Cases ─────────────────────────────────────
        # Test 404 for non-existent routes.
        # Test empty / None inputs where applicable.

        ============================
        GENERATE THE TEST FILE NOW
        ============================
    """)

    response = llm.invoke(prompt)
    test_text = response.content if hasattr(response, "content") else str(response)

    # Strip any accidental markdown fences
    import re
    test_text = re.sub(r"^```[a-zA-Z]*\n?", "", test_text.strip(), flags=re.MULTILINE)
    test_text = re.sub(r"```$", "", test_text.strip(), flags=re.MULTILINE)
    test_text = test_text.strip()

    # Persist
    (project_root / "Test_Cases.txt").write_text(test_text, encoding="utf-8")

    return test_text
