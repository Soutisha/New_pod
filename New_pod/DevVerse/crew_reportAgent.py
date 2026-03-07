"""
Report Agent for DevVerse.
Generates a corporate-style project report.
"""

from langchain_groq import ChatGroq
from pathlib import Path
import os
import textwrap

project_root = Path(__file__).parent.absolute()
env_path = project_root / ".env"

GROQ_API_KEY = ""
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.split("=",1)[1].strip()

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
    api_key=GROQ_API_KEY,
    max_tokens=4000
)


def run_report_agent():

    stories = (project_root / "User_Stories.txt").read_text()
    design = (project_root / "System_Design.txt").read_text()
    code = (project_root / "Implementation_Code.txt").read_text()[:3000]
    tests = (project_root / "Test_Cases.txt").read_text()

    prompt = textwrap.dedent(f"""
You are a senior software consultant preparing a **corporate project report**
for stakeholders and technical leadership.

PROJECT DATA:

USER STORIES
{stories}

SYSTEM DESIGN
{design}

IMPLEMENTATION SUMMARY
{code}

TEST CASES
{tests}

================================

Generate a professional project report with these sections:

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

Rules:
• Professional corporate tone
• Clear sections
• No markdown
• No code blocks
""")

    response = llm.invoke(prompt)
    report = response.content

    (project_root / "Project_Report.txt").write_text(report)

    return report