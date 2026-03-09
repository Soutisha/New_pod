"""
Developer Agent — RAG-powered (DevVerse).
─────────────────────────────────────────────────────────────────────────
Reads System_Design.txt, retrieves context from ChromaDB, generates a
complete Flask web application via the LangChain RetrievalQA chain backed
by Groq, parses FILE: blocks, and writes each file to generated_project/.

All input and output is filtered through the SHAP responsible AI guard.
"""

from __future__ import annotations

import os
import re
import sys
import shutil
import subprocess
from pathlib import Path

from core.rag_engine import rag_query, refresh_knowledge_base
from core.responsible_ai import filter_input, filter_output

_PROJECT_ROOT = Path(__file__).parent.parent.absolute()
_OUTPUTS_DIR  = _PROJECT_ROOT / "outputs"

_ROLE = (
    "You are a senior full-stack engineer who writes production-quality "
    "Flask applications with premium UI. Always output FILE: blocks only."
)


# ── Public API ────────────────────────────────────────────────────────

def run_developer_agent() -> str:
    """
    Read System_Design.txt, enrich with RAG, generate full-stack Flask app.
    """
    design_file = _OUTPUTS_DIR / "System_Design.txt"
    if not design_file.exists():
        design_file = _PROJECT_ROOT / "System_Design.txt"
    if not design_file.exists():
        raise FileNotFoundError("System_Design.txt not found. Run Design Agent first.")

    design_text = design_file.read_text(encoding="utf-8").strip()
    if not design_text:
        raise ValueError("System_Design.txt is empty.")

    # ── Responsible-AI input filter ────────────────────────────────
    safe_design, blocked, score = filter_input(design_text, stage="Dev_Input")
    if blocked:
        raise RuntimeError(
            f"Input blocked by Responsible AI filter (score={score:.2f})."
        )

    # ── Refresh KB ────────────────────────────────────────────────
    refresh_knowledge_base()

    # ── RAG query ─────────────────────────────────────────────────
    question = (
        "Generate a complete, immediately-runnable Flask web application based "
        "on the system design below.\n\n"
        "STRICT OUTPUT RULES:\n"
        "1. Output ONLY FILE blocks — no explanations, no markdown prose.\n"
        "2. Format: FILE: <relative/path/to/file>\\n<complete file content>\\n\n"
        "3. Always produce: app.py, requirements.txt, static/style.css, and "
        "ALL needed templates/*.html files.\n\n"
        "BACKEND (app.py):\n"
        "• Flask + SQLAlchemy (sqlite). Set DATABASE URI before db=SQLAlchemy(app).\n"
        "• Init DB: `with app.app_context(): db.create_all()` at the bottom.\n"
        "• NO flask-wtf. NO @app.before_first_request.\n"
        "• Use request.form.get('field') for form data.\n"
        "• Every route function must have a globally unique name.\n"
        "• End file with: if __name__ == '__main__': app.run(host='0.0.0.0', port=5000, debug=True)\n\n"
        "FRONTEND (HTML / CSS):\n"
        "• Premium SaaS-style UI — minimum 400 CSS lines.\n"
        "• Separate HTML file for every route.\n"
        "• Auth pages: professional split-screen layout.\n\n"
        f"SYSTEM DESIGN:\n{safe_design[:3000]}"
    )

    raw_output = rag_query(question=question, system_role=_ROLE)

    # ── Responsible-AI output filter ───────────────────────────────
    safe_output, blocked_out, _ = filter_output(raw_output, stage="Dev_Output")

    # ── Persist raw output ─────────────────────────────────────────
    _OUTPUTS_DIR.mkdir(exist_ok=True)
    (_OUTPUTS_DIR / "Implementation_Code.txt").write_text(safe_output, encoding="utf-8")
    (_PROJECT_ROOT / "Implementation_Code.txt").write_text(safe_output, encoding="utf-8")

    # ── Write project files ────────────────────────────────────────
    proj_dir = _PROJECT_ROOT / "generated_project"
    if proj_dir.exists():
        shutil.rmtree(proj_dir)
    _write_project_files(safe_output)

    return safe_output


def run_generated_project() -> None:
    """
    Install dependencies and launch the generated Flask app on port 5000.
    """
    proj_dir = _PROJECT_ROOT / "generated_project"
    app_file  = proj_dir / "app.py"
    req_file  = proj_dir / "requirements.txt"

    if not app_file.exists():
        raise FileNotFoundError("generated_project/app.py not found.")

    # ── Auto-fix common LLM hallucinations ────────────────────────
    app_text = app_file.read_text(encoding="utf-8")
    app_text = app_text.replace(
        "@app.before_first_request", "# [Auto-removed @app.before_first_request]"
    )
    if "debug=True" in app_text and "use_reloader=" not in app_text:
        app_text = app_text.replace("debug=True", "debug=True, use_reloader=False")
    app_text = re.sub(r"form\.(\w+)\.data", r"request.form.get('\1')", app_text)
    app_text = re.sub(r"from\s+flask_wtf.*import.*", "# [Auto-removed flask_wtf import]", app_text)
    app_file.write_text(app_text, encoding="utf-8")

    # ── Clean HTML templates ──────────────────────────────────────
    tmpl_dir = proj_dir / "templates"
    if tmpl_dir.exists():
        for html_file in tmpl_dir.glob("*.html"):
            h_text = html_file.read_text(encoding="utf-8")
            h_text = re.sub(r"\{\{\s*form\.\w+(\(\))?\s*\}\}", "", h_text)
            h_text = re.sub(r"\{\{\s*form\.\w+\.label\s*\}\}", "", h_text)
            html_file.write_text(h_text, encoding="utf-8")

    # ── Clean requirements ────────────────────────────────────────
    if req_file.exists():
        r_lines = req_file.read_text(encoding="utf-8").splitlines()
        clean_r = [
            l for l in r_lines
            if "flask-wtf" not in l.lower() and "wtforms" not in l.lower()
        ]
        req_file.write_text("\n".join(clean_r), encoding="utf-8")

    # ── Kill lingering processes on port 5000 ────────────────────
    try:
        subprocess.run(
            ["powershell", "-Command",
             "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue "
             "| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force "
             "-ErrorAction SilentlyContinue }"],
            capture_output=True,
        )
        subprocess.run(
            ["powershell", "-Command",
             "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' "
             "-and $_.CommandLine -match 'app.py' } | Invoke-CimMethod -MethodName Terminate"],
            capture_output=True,
        )
        import time; time.sleep(1.5)
    except Exception:
        pass

    # ── Check for duplicate route functions ──────────────────────
    dupes = _find_duplicate_functions(app_file)
    if dupes:
        raise RuntimeError(
            f"Duplicate Flask route functions: {dupes}. Reset and regenerate."
        )

    # ── Install deps ─────────────────────────────────────────────
    if req_file.exists():
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            cwd=str(proj_dir),
            check=False,
        )

    # ── Launch Flask ──────────────────────────────────────────────
    log_file = open(proj_dir / "flask_error.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(proj_dir),
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    import time; time.sleep(1)
    if proc.poll() is not None:
        raise RuntimeError("Flask server crashed immediately! Check generated_project/flask_error.log")


# ── Internal helpers ───────────────────────────────────────────────────

def _write_project_files(code_output: str) -> None:
    """Parse FILE: blocks and write each to generated_project/."""
    proj_dir = _PROJECT_ROOT / "generated_project"
    proj_dir.mkdir(exist_ok=True)

    pattern = re.compile(r"FILE:\s*(.+?)\n([\s\S]*?)(?=\nFILE:|\Z)", re.MULTILINE)
    matches = pattern.findall(code_output)

    if not matches:
        print("⚠️  No FILE: blocks detected — saving raw output as app.py fallback.")
        (proj_dir / "app.py").write_text(code_output, encoding="utf-8")
        return

    for raw_name, content in matches:
        filename = raw_name.strip()
        if not filename:
            continue

        filepath = proj_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        clean = content.strip()
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", clean, flags=re.MULTILINE)
        clean = re.sub(r"```$", "", clean, flags=re.MULTILINE)
        clean = clean.strip()

        if filename == "requirements.txt":
            clean = _sanitise_requirements(clean)

        filepath.write_text(clean, encoding="utf-8")
        print(f"  ✅  Written: {filepath.relative_to(_PROJECT_ROOT)}")


def _sanitise_requirements(raw: str) -> str:
    """Remove invalid lines from a requirements.txt string."""
    seen: set[str] = set()
    valid: list[str] = []

    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = re.split(r"[<>=!]", line)[0].strip().lower()
        if " " in pkg or ":" in pkg or len(pkg) < 2:
            continue
        if pkg not in seen:
            seen.add(pkg)
            valid.append(pkg)

    if "flask" not in seen:
        valid.insert(0, "flask")

    return "\n".join(valid)


def _find_duplicate_functions(app_file: Path) -> list[str]:
    """Return list of function names that appear more than once."""
    code  = app_file.read_text(encoding="utf-8")
    names = re.findall(r"^\s*def\s+(\w+)\s*\(", code, re.MULTILINE)
    return [n for n in set(names) if names.count(n) > 1]
