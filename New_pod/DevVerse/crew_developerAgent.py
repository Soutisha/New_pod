"""
Developer Agent for DevVerse.
Generates a complete, clean, runnable Flask web application
with a premium modern UI.
"""

from langchain_groq import ChatGroq
from pathlib import Path
import os
import re
import sys
import subprocess
import textwrap
from openai import OpenAI
from dotenv import load_dotenv
import shutil

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
        temperature=0.4,
        api_key=GROQ_API_KEY,
        max_tokens=4096,
    )

# load_dotenv()

# DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# client = OpenAI(
#     api_key=DEEPSEEK_API_KEY,
#     base_url="https://api.deepseek.com"
# )
# ── Public API ──────────────────────────────────────────────

def run_developer_agent() -> str:
    """
    Read System_Design.txt, ask LLM to generate a full-stack
    Flask project with premium UI, parse the FILE blocks, write
    each file to generated_project/, and return the raw LLM output.
    Raises an exception on any unrecoverable error.
    """
    if not llm:
        raise RuntimeError("GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys")
    # if not DEEPSEEK_API_KEY:
    #     raise RuntimeError("DEEPSEEK_API_KEY not set.")

    design_file = project_root / "System_Design.txt"
    if not design_file.exists():
        raise FileNotFoundError("System_Design.txt not found. Run the Design Agent first.")

    design_text = design_file.read_text(encoding="utf-8").strip()
    if not design_text:
        raise ValueError("System_Design.txt is empty.")

    prompt = textwrap.dedent(f"""
        You are a senior full-stack engineer. Your task is to generate a complete,
        immediately-runnable Flask web application based on the system design below.

        SYSTEM DESIGN:
        {design_text}

        ============================
        STRICT OUTPUT RULES
        ============================

        1. Output ONLY the content between FILE blocks. No explanations, no markdown
           prose, no comments outside of code.

        2. Use EXACTLY this format for every file you produce:

           FILE: <relative/path/to/file>
           <complete file content>

           (Leave one blank line between FILE blocks.)

        3. Produce ALWAYS `app.py`, `requirements.txt`, `static/style.css`, and
           AS MANY HTML files as needed in the `templates/` folder to make a FULLY functional app.
           Do NOT just provide an index.html if the app has login, dashboard, or other pages.

        ============================
        BACKEND RULES (app.py)
        ============================

        • Use Flask. If using a database, use SQLAlchemy (sqlite).
        • NEVER use `@app.before_first_request` (it is removed in Flask 2.3+).
        • CRITICAL DATABASE INIT ORDER:
          ```python
          app = Flask(__name__)
          app.secret_key = "supersecret"
          app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
          db = SQLAlchemy(app)
          ```
          You MUST set `SQLALCHEMY_DATABASE_URI` before `db = SQLAlchemy(app)`.
        • MUST INITIALIZE DATABASE using the app context at the bottom:
          ```python
          with app.app_context():
              db.create_all()
          ```
        • ABSOLUTELY NO FLASK-WTF or WTForms! Do NOT import them. DO NOT use `FlaskForm`. You MUST use standard HTML `<form>` tags and `request.form.get('field_name')`.
        • ABSOLUTELY NO THIRD-PARTY APIS: Do NOT import or use external payment gateways, email senders, or SMS APIs (e.g. Stripe, SendGrid, Twilio). You MUST mock any external services using simple standard python code (e.g. `flash("Payment successful!")`).
        • DO NOT import from files you have not generated.
        • EVERY route function MUST have a globally unique name.
        • ACTUALLY BUILD THE APP FLOW: You must implement the full routing logic.
          If the system requires user accounts, implement `/register`, `/login`, and `/dashboard` routes.
        • Forms MUST have end-to-end logic (e.g. POST to /register saves to DB, redirects to /login. POST to /login checks DB and sets session).
        • Use `render_template('filename.html')`. DO NOT use `render_template_string`.
        • Include all necessary imports at the top.
        • End the file with exactly:

          if __name__ == "__main__":
              app.run(host="0.0.0.0", port=5000, debug=True)

        • requirements.txt: one package name per line (e.g. flask, flask-sqlalchemy, flask-login).

        ============================
        FRONTEND RULES (HTML / CSS / JS)
        ============================

        The UI MUST be a fully functional, multi-page application that looks like a high-end,
        premium SaaS product (similar to Stripe or Vercel). Do not generate plain unstyled HTML.

        HTML (templates/*.html):
        • Create a separate HTML file for EVERY route (index, login, register, dashboard/app).
        • **INDUSTRY-STANDARD AUTHENTICITY**: Analyze the task and use the relevant "Original" layout:
          - **eCommerce**: High-density product grid (not just big cards), Sidebar filters (Categories, Price), Shopping Cart drawer/icon, Search Bar in header.
          - **Software/SaaS**: Fixed Sidebar navigation (left-side), Top Breadcrumbs, Contextual Data Tables or Kanban Boards for "Actionable Workspace" rather than summary cards.
          - **Analytics/CRM**: High-density data visualizations and split-screen layouts.
        • Auth pages (login/register) MUST use a professional **Split-Screen or Full-Page Gradient layout** (Left side for Brand Info, Right side for Form) - NO tiny floating cards.
        • **DYNAMIC INTERACTIVITY**:
          - Nav bars must have nested dropdowns or search fields if relevant.
          - Dashboards must feel like a "Daily Workspace" with real data density.
        • Buttons and form actions must point to real routes (e.g. `action="{{{{ url_for('login') }}}}"`).
        • NO WTF-FORMS JINJA TAGS: Use standard HTML tags only.

        CSS (static/style.css):
        • Minimum 400 lines. Write a production-grade UI library.
        • **PHILOSOPHY: "The Real Deal"**. Avoid generic boxy layouts. Use whitespace as a functional tool.
        • LAYOUT: 
          - **SaaS**: Implement a robust `.app-layout` with a fixed sidebar (`nav.sidebar`) and scrollable content area (`main.content`).
          - **Shop**: Implement a responsive `.shop-grid` with multi-column filtering.
        • AESTHETICS:
          - Use **High Information Density** (smaller but crisp fonts like 14px for data, 16px for UI).
          - Pro typography: Variable weights for hierarchy.
          - Minimal use of "Cards": Prefer sectioned dividers, clean tables, and subtle border-bottoms.
          - Professional shadows: Very light (`rgba(0,0,0,0.02)`) but layered.
        • COLORS: Strict professional palettes. No more than 3 colors + Neutrals.
        • REUSABLE COMPONENTS: Define classes for `.badge`, `.status-pill`, `.data-row`, `.input-group`, `.sidebar-item`.
        • SCROLLBARS: Custom thin scrollbars for a premium feel.

        ============================
        NOW GENERATE ALL THE FILES
        ============================
    """)

    response = llm.invoke(prompt)
    dev_text = response.content if hasattr(response, "content") else str(response)

    # response = client.chat.completions.create(
    #     model="deepseek-chat",
    #     messages=[
    #         {"role": "user", "content": prompt}
    #     ],
    #     temperature=0.4,
    #     max_tokens=4096
    # )

    # if not response.choices or not response.choices[0].message.content:
    #     raise RuntimeError("LLM returned empty response")

    # dev_text = response.choices[0].message.content

    # # Save raw output
    (project_root / "Implementation_Code.txt").write_text(dev_text, encoding="utf-8")

    # # Write project files
    # _write_project_files(dev_text)
    proj_dir = project_root / "generated_project"

    if proj_dir.exists():
        shutil.rmtree(proj_dir)

    _write_project_files(dev_text)

    return dev_text


def _write_project_files(code_output: str) -> None:
    """Parse FILE: blocks and write each to generated_project/."""
    proj_dir = project_root / "generated_project"
    proj_dir.mkdir(exist_ok=True)

    pattern = re.compile(r"FILE:\s*(.+?)\n([\s\S]*?)(?=\nFILE:|\Z)", re.MULTILINE)
    matches = pattern.findall(code_output)

    if not matches:
        print("⚠️  No FILE: blocks detected in LLM output.")
        # Attempt to save the raw output as app.py fallback
        (proj_dir / "app.py").write_text(code_output, encoding="utf-8")
        return

    for raw_name, content in matches:
        filename = raw_name.strip()
        if not filename:
            continue

        filepath = proj_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        clean = content.strip()
        # Strip markdown fences
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", clean, flags=re.MULTILINE)
        clean = re.sub(r"```$", "", clean, flags=re.MULTILINE)
        clean = clean.strip()

        if filename == "requirements.txt":
            clean = _sanitise_requirements(clean)

        filepath.write_text(clean, encoding="utf-8")
        print(f"  ✅  Written: {filepath.relative_to(project_root)}")


def _sanitise_requirements(raw: str) -> str:
    """Clean requirements.txt so it only contains valid package names."""
    seen: set[str] = set()
    valid: list[str] = []

    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Remove version specifiers
        pkg = re.split(r"[<>=!]", line)[0].strip().lower()
        # Drop lines that look like prose
        if " " in pkg or ":" in pkg or len(pkg) < 2:
            continue
        if pkg not in seen:
            seen.add(pkg)
            valid.append(pkg)

    # Flask must always be present
    if "flask" not in seen:
        valid.insert(0, "flask")

    return "\n".join(valid)


def _find_duplicate_functions(app_file: Path) -> list[str]:
    """Return a list of function names that appear more than once."""
    code = app_file.read_text(encoding="utf-8")
    names = re.findall(r"^\s*def\s+(\w+)\s*\(", code, re.MULTILINE)
    return [n for n in set(names) if names.count(n) > 1]


def run_generated_project() -> None:
    """
    Install requirements and launch the generated Flask app
    in a background subprocess on port 5000.
    """
    proj_dir = project_root / "generated_project"
    app_file  = proj_dir / "app.py"
    req_file  = proj_dir / "requirements.txt"

    if not app_file.exists():
        raise FileNotFoundError("generated_project/app.py not found.")

    # --- ADVANCED AUTO-FIXER: Strip common LLM hallucinations ---
    # 1. Clean app.py
    app_text = app_file.read_text(encoding="utf-8")
    app_text = app_text.replace("@app.before_first_request", "# [Auto-removed @app.before_first_request]")
    # Disable the Flask reloader because it causes infinite restart loops in background subprocesses on Windows
    if "debug=True" in app_text and "use_reloader=" not in app_text:
        app_text = app_text.replace("debug=True", "debug=True, use_reloader=False")
    
    # regex: transform 'form.something.data' -> "request.form.get('something')"
    app_text = re.sub(r"form\.(\w+)\.data", r"request.form.get('\1')", app_text)
    # regex: remove 'from flask_wtf import ...' or similar
    app_text = re.sub(r"from\s+flask_wtf.*import.*", "# [Auto-removed flask_wtf import]", app_text)
    app_file.write_text(app_text, encoding="utf-8")

    # 2. Clean HTML templates
    tmpl_dir = proj_dir / "templates"
    if tmpl_dir.exists():
        for html_file in tmpl_dir.glob("*.html"):
            h_text = html_file.read_text(encoding="utf-8")
            # Strip {{ form.hidden_tag() }}, {{ form.username() }}, etc.
            h_text = re.sub(r"\{\{\s*form\.\w+(\(\))?\s*\}\}", "", h_text)
            # Strip standard WTF-form variable printing
            h_text = re.sub(r"\{\{\s*form\.\w+\.label\s*\}\}", "", h_text)
            html_file.write_text(h_text, encoding="utf-8")

    # 3. Clean requirements.txt (remove flask-wtf if present)
    if req_file.exists():
        r_lines = req_file.read_text(encoding="utf-8").splitlines()
        clean_r = [l for l in r_lines if "flask-wtf" not in l.lower() and "wtforms" not in l.lower()]
        req_file.write_text("\n".join(clean_r), encoding="utf-8")

    # --- NUCLEAR PROCESS & DB CLEANUP ---
    try:
        # 1. Kill any process currently listening on port 5000 (standard Flask port)
        subprocess.run(
            ["powershell", "-Command", "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
            capture_output=True
        )
        # 2. Kill any ghost python app.py processes
        subprocess.run(
            ["powershell", "-Command", "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'app.py' } | Invoke-CimMethod -MethodName Terminate"],
            capture_output=True
        )
        import time
        time.sleep(1.5) # NUCLEAR WAIT for file locks to release
    except Exception:
        pass

    # Now perform a workspace-wide database purge to prevent shadowing
    try:
        workspace_root = project_root.parent.parent # c:\Users\SHYAM\Desktop\prachanda
        for db_file in workspace_root.rglob("*.db"):
            try:
                db_file.unlink()
            except Exception:
                pass
        for db_file in workspace_root.rglob("*.sqlite"):
            try:
                db_file.unlink()
            except Exception:
                pass
        
        # Specifically wipe the 'instance' folder in the generated project
        import shutil
        instance_folder = proj_dir / "instance"
        if instance_folder.exists():
            shutil.rmtree(instance_folder, ignore_errors=True)
    except Exception:
        pass

    # Check for duplicate function names
    dupes = _find_duplicate_functions(app_file)
    if dupes:
        raise RuntimeError(
            f"Duplicate Flask route functions detected: {dupes}. "
            "Please reset and regenerate."
        )

    # Install dependencies
    if req_file.exists():
        print("📦  Installing dependencies…")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            cwd=str(proj_dir),
            check=False,
        )

    # Launch Flask server
    print("🚀  Starting Flask app on port 5000…")
    log_file = open(proj_dir / "flask_error.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(proj_dir),
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    import time
    time.sleep(1) # wait a second to see if it crashes instantly
    if proc.poll() is not None:
        raise RuntimeError(f"Flask server crashed immediately! Check generated_project/flask_error.log")