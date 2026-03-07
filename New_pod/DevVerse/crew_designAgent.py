"""
Design Agent for DevVerse.
Reads User_Stories.txt and generates a system architecture document
including a valid Mermaid flowchart.
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
        max_tokens=2500,
    )


def run_design_agent() -> str:
    """
    Generate system architecture from user stories.
    Returns the design document text (includes a Mermaid block).
    Raises RuntimeError / FileNotFoundError on failure.
    """
    if not llm:
        raise RuntimeError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys"
        )

    stories_file = project_root / "User_Stories.txt"
    if not stories_file.exists():
        raise FileNotFoundError(
            "User_Stories.txt not found. Run the Business Analyst Agent first."
        )

    user_stories = stories_file.read_text(encoding="utf-8").strip()
    if not user_stories:
        raise ValueError("User_Stories.txt is empty.")

    prompt = textwrap.dedent(f"""
        You are a senior software architect. Based on the user stories below,
        produce a concise system architecture document.

        USER STORIES:
        {user_stories}

        ============================
        OUTPUT FORMAT
        ============================

        Your output must contain THREE sections in this order:

        1. SYSTEM OVERVIEW
           - 2-3 sentences describing the system.

        2. COMPONENTS
           - Bullet list of key components (e.g. Frontend, Backend API, Database, Auth Service).
           - One sentence per component describing its role.

        3. ARCHITECTURE DIAGRAM
           - A single valid Mermaid flowchart in this exact format:

        ```mermaid
        flowchart TD
            User["User Browser"] --> Frontend["Frontend / HTML+JS"]
            Frontend --> API["Flask REST API"]
            API --> DB["SQLite / Database"]
            API --> Auth["Auth Module"]
        ```

        ============================
        DIAGRAM RULES (CRITICAL)
        ============================

        • Start the block with: ```mermaid
        • First line inside the block: flowchart TD
        • Use ONLY --> arrows (no ==>, -.->, etc.)
        • Node labels with spaces MUST be quoted: NodeId["Label with spaces"]
        • Keep it clean: 6-10 nodes, no subgraphs unless essential.
        • Close the block with: ```

        ============================
        GENERAL RULES
        ============================

        • Plain text only (no extra markdown headings).
        • No HTML.
        • Do NOT repeat the user stories verbatim.
    """)

    response = llm.invoke(prompt)
    design_text = response.content if hasattr(response, "content") else str(response)

    (project_root / "System_Design.txt").write_text(design_text, encoding="utf-8")

    return design_text
