"""
DevVerse — AI-Powered Virtual Development Pod
Main Streamlit Application (RAG + CrewAI + SHAP Responsible AI edition)
─────────────────────────────────────────────────────────────────────────
Architecture:
  • PDF upload → requirement extraction → SHAP input filter
  • CrewAI Master Agent orchestrates 5 sequential specialist agents
  • Every agent uses RAG (ChromaDB + LangChain + Groq) — no bare LLM calls
  • SHAP responsible-AI filter applied to every agent input AND output
  • SHAP Dashboard shows cumulative safety score across all 12+ filter points

Folder structure (clean code):
  agents/   → all CrewAI agents + master orchestrator
  core/     → RAG engine, responsible AI, PDF extraction
  frontend/ → scifi hero UI component + CSS
  sandbox/  → Docker sandbox manager for generated app preview
  pages/    → Streamlit multi-page app pages
  outputs/  → persisted agent output text files
"""

import streamlit as st
import PyPDF2
import time
import os
import re
import sys
from pathlib import Path

# ── Page config — MUST be first Streamlit call ────────────────────────
st.set_page_config(
    page_title="DevVerse — AI Development Pod",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Environment + sys.path setup ──────────────────────────────────────
project_root = Path(__file__).parent.absolute()

# Ensure the project root is on sys.path so packages resolve
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

env_path = project_root / ".env"

# Disable CrewAI telemetry (prevents signal.signal thread crashes in Streamlit)
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("GROQ_API_KEY="):
                os.environ["GROQ_API_KEY"] = line.split("=", 1)[1]
                break

# ── Module imports (after env + path are loaded) ─────────────────────
from core.extraction import process_pdf_text                          # noqa: E402
from core.responsible_ai import filter_input, explain_with_shap, get_shap_dashboard_data  # noqa: E402
from agents.crew_reportAgent import run_report_agent                  # noqa: E402
from agents.crew_businessAgent import run_business_analyst            # noqa: E402
from agents.crew_designAgent import run_design_agent                  # noqa: E402
from agents.crew_developerAgent import run_developer_agent            # noqa: E402
from agents.crew_testerAgent import run_tester_agent                  # noqa: E402
from agents.master_agent import run_master_crew                       # noqa: E402
from frontend.scifi_hero import log_activity, mark_agent_done, render_hero  # noqa: E402

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet                   # noqa: E402
from io import BytesIO                                                 # noqa: E402

# ── Cache heavy resources — loaded ONCE, reused across all reruns ─────
@st.cache_resource
def _warmup_rag():
    from core.rag_engine import (
        build_vector_store,
        _get_embeddings,
        _get_llm,
        _COLLECTIONS
    )

    os.environ["DEVVERSE_WARMUP"] = "1"   # 👈 add

    _get_embeddings()
    _get_llm()

    for collection in _COLLECTIONS.values():
        build_vector_store(collection_name=collection)

    os.environ.pop("DEVVERSE_WARMUP", None)   # 👈 remove after

    return True

_warmup_rag()   # Runs once; all subsequent reruns return cached result instantly

# ── Ensure outputs directory exists ───────────────────────────────────
(project_root / "outputs").mkdir(exist_ok=True)


# ── PDF → report helper ───────────────────────────────────────────────
def generate_pdf(report_text: str) -> BytesIO:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    story  = []
    for line in report_text.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))
        story.append(Spacer(1, 8))
    SimpleDocTemplate(buffer).build(story)
    buffer.seek(0)
    return buffer


# ── CSS loader ────────────────────────────────────────────────────────
def load_css(css_path: Path) -> None:
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Try frontend/ first, fall back to root
css_file = project_root / "frontend" / "styleDevVerse.css"
if not css_file.exists():
    css_file = project_root / "styleDevVerse.css"
load_css(css_file)


# ── Session state defaults ────────────────────────────────────────────
defaults = {
    "pdf_text":            "",
    "pdf_processed":       False,
    "project_initialized": False,
    "ba_completed":        False,
    "design_completed":    False,
    "dev_completed":       False,
    "test_completed":      False,
    "report_completed":    False,
    "ba_text":             "",
    "design_text":         "",
    "dev_code":            "",
    "test_cases":          "",
    "report_text":         "",
    "report_time":         0.0,
    "ba_time":             0.0,
    "design_time":         0.0,
    "dev_time":            0.0,
    "test_time":           0.0,
    "shap_score":          0.0,
    "use_crew":            True,
    "shap_dashboard":      {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Agent card HTML ───────────────────────────────────────────────────
_ICON_COLORS = {
    "ba":     "rgba(167,139,250,0.15)",
    "des":    "rgba(56,189,248,0.15)",
    "dev":    "rgba(52,211,153,0.15)",
    "test":   "rgba(251,146,60,0.15)",
    "report": "rgba(244,114,182,0.15)",
}


def agent_card(icon: str, kind: str, title: str, subtitle: str,
               status: str, elapsed: float = 0.0) -> str:
    badge_map = {
        "running": ("dv-status-running", "⬤ Running"),
        "done":    ("dv-status-done",    "✓ Done"),
        "error":   ("dv-status-error",   "✗ Error"),
    }
    badge_cls, badge_txt = badge_map.get(status, badge_map["running"])
    time_html = (f'<p class="dv-gen-time">⏱ Completed in {elapsed:.1f}s</p>'
                 if status == "done" else "")
    bg = _ICON_COLORS.get(kind, "rgba(108,99,255,0.12)")
    return f"""
<div class="dv-agent-card">
    <div class="dv-agent-header">
        <div class="dv-agent-icon" style="background:{bg}; border:1px solid {bg.replace('0.15','0.35')}">
            {icon}
        </div>
        <div class="dv-agent-meta">
            <h3>{title}</h3>
            <p>{subtitle}</p>
        </div>
        <span class="dv-status {badge_cls}">{badge_txt}</span>
    </div>
    {time_html}
</div>"""


# ── Hero ──────────────────────────────────────────────────────────────
render_hero()

# ── Pipeline progress bar ─────────────────────────────────────────────
steps = [
    ("ba_completed",     "🧠", "Analyst"),
    ("design_completed", "🎨", "Designer"),
    ("dev_completed",    "💻", "Developer"),
    ("test_completed",   "🧪", "Tester"),
    ("report_completed", "📑", "Report"),
]


def make_pipeline() -> str:
    html = '<div class="dv-pipeline">'
    for i, (flag, icon, label) in enumerate(steps):
        done   = st.session_state.get(flag, False)
        prev   = st.session_state.get(steps[i - 1][0], False) if i > 0 else True
        active = prev and not done and st.session_state.project_initialized

        if done:
            dot_cls, dot_txt = "dv-pipeline-dot-done",    "✓"
        elif active:
            dot_cls, dot_txt = "dv-pipeline-dot-active",  str(i + 1)
        else:
            dot_cls, dot_txt = "dv-pipeline-dot-pending", str(i + 1)

        html += f"""
        <div class="dv-pipeline-step">
            <div class="dv-pipeline-dot {dot_cls}">{dot_txt}</div>
            <span class="dv-pipeline-label">{label}</span>
        </div>"""
        if i < len(steps) - 1:
            conn_cls = "dv-pipeline-connector-done" if done else "dv-pipeline-connector"
            html += f'<div class="{conn_cls}"></div>'

    html += "</div>"
    return html


st.markdown(make_pipeline(), unsafe_allow_html=True)
st.markdown("<hr class='dv-divider'/>", unsafe_allow_html=True)

# ── File upload ───────────────────────────────────────────────────────
uploaded_file = st.file_uploader("📎  Drop your RFP here — PDF format", type=["pdf"])

if uploaded_file:
    try:
        extracted = ""
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted += text + "\n"

        if not extracted.strip():
            st.error("❌  The PDF appears to be empty or unreadable.")
        else:
            safe_text, blocked, score = filter_input(extracted, stage="PDF_Upload")
            st.session_state.shap_score = score

            if blocked:
                st.error(
                    f"🛡️ **Responsible AI Filter** blocked the uploaded PDF "
                    f"(toxicity score: {score:.3f}). Please upload appropriate content."
                )
            else:
                st.session_state.pdf_text      = safe_text
                st.session_state.pdf_processed = True
                
                # Write to disk so RAG engine can ingest it!
                out_dir = Path(__file__).parent / "outputs"
                out_dir.mkdir(exist_ok=True)
                (out_dir / "extracted_reqmts.txt").write_text(safe_text, encoding="utf-8")
                
                if score > 0.15:
                    st.warning(
                        f"⚠️ SHAP Toxicity score: {score:.3f} — content passed but "
                        "flagged for mild concern. (Lower score = safer)"
                    )
                else:
                    st.success(f"✅  PDF uploaded and indexed! (Toxicity Score: {score:.3f} — Lower is better!)")
    except Exception as e:
        st.error(f"❌  Error reading PDF: {e}")
        st.session_state.pdf_processed = False

# ── Mode selector ─────────────────────────────────────────────────────
if st.session_state.pdf_processed and not st.session_state.project_initialized:
    st.markdown("<div style='margin:1rem 0 0.5rem;'><b>🤖 Execution Mode</b></div>",
                unsafe_allow_html=True)
    mode = st.radio(
        "Choose how agents run:",
        ["🏆 CrewAI Master Agent (Recommended)", "⚡ Individual Agents (Step-by-step)"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.use_crew = "CrewAI" in mode

# ── Initialize button ─────────────────────────────────────────────────
if st.session_state.pdf_processed and not st.session_state.project_initialized:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        if st.button("🚀  Initialize Dev Pod", use_container_width=True):
            st.session_state.project_initialized = True
            st.session_state.dv_log     = []
            st.session_state.dv_active  = None
            st.session_state.dv_started = False
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════
# CREW AI MASTER AGENT PATH  (all 5 agents run together)
# ═══════════════════════════════════════════════════════════════════════
if (
    st.session_state.project_initialized
    and st.session_state.use_crew
    and not st.session_state.report_completed
):
    for key in ["ba", "design", "dev", "test"]:
        log_activity(key, f"CrewAI orchestrating {key} agent via RAG…")

    st.markdown(agent_card(
        "🤖", "ba", "CrewAI Master Agent",
        "Orchestrating all 5 specialist agents sequentially via RAG", "running"
    ), unsafe_allow_html=True)

    with st.spinner("CrewAI Master Agent running — BA → Design → Dev → Test → Report…"):
        try:
            pdf_content = st.session_state.get("pdf_text", "")
            reqs, _     = process_pdf_text(pdf_content)
            req_text    = "\n".join(reqs)
            st.session_state["requirements"] = req_text

            # Save to both root and outputs/
            req_file = project_root / "extracted_reqmts.txt"
            req_file.write_text(req_text, encoding="utf-8")
            out_req = project_root / "outputs" / "extracted_reqmts.txt"
            out_req.write_text(req_text, encoding="utf-8")

            t0      = time.time()
            results = run_master_crew(req_text)
            elapsed = round(time.time() - t0, 2)

            st.session_state.ba_text          = results["ba_text"]
            st.session_state.design_text      = results["design_text"]
            st.session_state.dev_code         = results["dev_code"]
            st.session_state.test_cases       = results["test_cases"]
            st.session_state.report_text      = results["report_text"]
            st.session_state.ba_time          = elapsed / 5
            st.session_state.design_time      = elapsed / 5
            st.session_state.dev_time         = elapsed / 5
            st.session_state.test_time        = elapsed / 5
            st.session_state.report_time      = elapsed / 5
            st.session_state.ba_completed     = True
            st.session_state.design_completed = True
            st.session_state.dev_completed    = True
            st.session_state.test_completed   = True
            st.session_state.report_completed = True
            st.session_state.shap_dashboard   = get_shap_dashboard_data()

            for key in ["ba", "design", "dev", "test", "report"]:
                mark_agent_done(key)

        except Exception as e:
            st.error(f"CrewAI Master Agent Error: {e}")
            for flag in ["ba_completed", "design_completed", "dev_completed",
                         "test_completed", "report_completed"]:
                st.session_state[flag] = True

    st.rerun()


# ═══════════════════════════════════════════════════════════════════════
# INDIVIDUAL AGENT PATH  (sequential, step-by-step)
# ═══════════════════════════════════════════════════════════════════════

# ── Step 1: Business Analyst ──────────────────────────────────────────
if (
    st.session_state.project_initialized
    and not st.session_state.use_crew
    and not st.session_state.ba_completed
):
    log_activity("ba", "Extracting requirements from RFP via RAG…")
    log_activity("ba", "Generating user stories…")

    st.markdown(agent_card("🧠", "ba", "Business Analyst",
                           "RAG: Translating RFP into Agile user stories", "running"),
                unsafe_allow_html=True)

    with st.spinner("BA Agent working — generating user stories via RAG…"):
        try:
            pdf_content = st.session_state.get("pdf_text", "")
            reqs, _     = process_pdf_text(pdf_content)
            req_text    = "\n".join(reqs)
            st.session_state["requirements"] = req_text

            req_file = project_root / "extracted_reqmts.txt"
            req_file.write_text(req_text, encoding="utf-8")
            out_req = project_root / "outputs" / "extracted_reqmts.txt"
            out_req.write_text(req_text, encoding="utf-8")

            t0      = time.time()
            ba_out  = run_business_analyst()
            st.session_state.ba_time      = round(time.time() - t0, 2)
            st.session_state.ba_text      = ba_out
            st.session_state.ba_completed = True
            mark_agent_done("ba")
        except Exception as e:
            st.error(f"Business Analyst Error: {e}")
            st.session_state.ba_text      = f"Error: {e}"
            st.session_state.ba_completed = True
            mark_agent_done("ba")
    st.rerun()

if st.session_state.ba_completed:
    st.markdown(agent_card("🧠", "ba", "Business Analyst", "User stories generated (RAG)",
                           "done", st.session_state.ba_time), unsafe_allow_html=True)
    with st.expander("📋  View User Stories", expanded=False):
        if st.session_state.ba_text.startswith("Error:"):
            st.error(st.session_state.ba_text)
        else:
            st.markdown(
                f'<div class="dv-output-box">{st.session_state.ba_text}</div>',
                unsafe_allow_html=True,
            )

# ── Step 2: Design Agent ──────────────────────────────────────────────
if (
    st.session_state.ba_completed
    and not st.session_state.use_crew
    and not st.session_state.design_completed
):
    log_activity("design", "Analysing user stories via RAG…")
    log_activity("design", "Building system architecture + Mermaid diagram…")

    st.markdown(agent_card("🎨", "des", "Design Agent",
                           "RAG: Creating system architecture & diagrams", "running"),
                unsafe_allow_html=True)

    with st.spinner("Design Agent working — building architecture via RAG…"):
        try:
            t0          = time.time()
            design_out  = run_design_agent()
            st.session_state.design_time      = round(time.time() - t0, 2)
            st.session_state.design_text      = design_out
            st.session_state.design_completed = True
            mark_agent_done("design")
        except Exception as e:
            st.error(f"Design Agent Error: {e}")
            st.session_state.design_text      = f"Error: {e}"
            st.session_state.design_completed = True
            mark_agent_done("design")
    st.rerun()

if st.session_state.design_completed:
    st.markdown(agent_card("🎨", "des", "Design Agent", "Architecture & diagrams ready (RAG)",
                           "done", st.session_state.design_time), unsafe_allow_html=True)

    mermaid_blocks = []
    clean_design   = st.session_state.design_text
    if not st.session_state.design_text.startswith("Error:"):
        mermaid_blocks = re.findall(
            r"```mermaid\s*(.*?)```", st.session_state.design_text, re.DOTALL
        )
        clean_design = re.sub(
            r"```mermaid.*?```", "", st.session_state.design_text, flags=re.DOTALL
        ).strip()

    with st.expander("🏗️  View System Architecture", expanded=False):
        if st.session_state.design_text.startswith("Error:"):
            st.error(st.session_state.design_text)
        else:
            st.markdown(
                f'<div class="dv-output-box">{clean_design}</div>',
                unsafe_allow_html=True,
            )

    if mermaid_blocks:
        try:
            from streamlit_mermaid import st_mermaid
            st.markdown("**📊 Architecture Diagram**")
            for i, block in enumerate(mermaid_blocks):
                block_clean = block.strip()
                if block_clean:
                    try:
                        st_mermaid(block_clean, key=f"mermaid_{i}")
                    except Exception as merr:
                        st.warning(f"Could not render diagram: {merr}")
                        st.code(block_clean, language="text")
        except ImportError:
            st.code(mermaid_blocks[0].strip(), language="text")

# ── Step 3: Developer Agent ───────────────────────────────────────────
if (
    st.session_state.design_completed
    and not st.session_state.use_crew
    and not st.session_state.dev_completed
):
    log_activity("dev", "Scaffolding project via RAG…")
    log_activity("dev", "Generating backend logic…")

    st.markdown(agent_card("💻", "dev", "Developer Agent",
                           "RAG: Writing full-stack production code", "running"),
                unsafe_allow_html=True)

    with st.spinner("Developer Agent working — generating codebase via RAG…"):
        try:
            t0       = time.time()
            code_out = run_developer_agent()
            st.session_state.dev_time      = round(time.time() - t0, 2)
            st.session_state.dev_code      = code_out
            st.session_state.dev_completed = True
            mark_agent_done("dev")
        except Exception as e:
            st.error(f"Developer Agent Error: {e}")
            st.session_state.dev_code      = f"Error: {e}"
            st.session_state.dev_completed = False
            mark_agent_done("dev")
    st.rerun()

if st.session_state.dev_completed:
    st.markdown(agent_card("💻", "dev", "Developer Agent", "Full-stack codebase generated (RAG)",
                           "done", st.session_state.dev_time), unsafe_allow_html=True)
    with st.expander("🗂️  View Generated Codebase", expanded=False):
        if st.session_state.dev_code.startswith("Error:"):
            st.error(st.session_state.dev_code)
        else:
            st.code(st.session_state.dev_code, language="python")

# ── Step 4: Tester Agent ──────────────────────────────────────────────
if (
    st.session_state.dev_completed
    and not st.session_state.use_crew
    and not st.session_state.test_completed
):
    log_activity("test", "Analysing codebase via RAG…")
    log_activity("test", "Writing 7-category comprehensive test suite…")

    st.markdown(agent_card("🧪", "test", "Tester Agent",
                           "RAG: Crafting 7-category QA suite (unit, auth, DB, security…)", "running"),
                unsafe_allow_html=True)

    with st.spinner("Tester Agent working — generating ultra-comprehensive test suite via RAG…"):
        try:
            t0        = time.time()
            test_out  = run_tester_agent()
            st.session_state.test_time      = round(time.time() - t0, 2)
            st.session_state.test_cases     = test_out
            st.session_state.test_completed = True
            mark_agent_done("test")
        except Exception as e:
            st.error(f"Tester Agent Error: {e}")
            st.session_state.test_cases     = f"Error: {e}"
            st.session_state.test_completed = True
            mark_agent_done("test")
    st.rerun()

if st.session_state.test_completed:
    st.markdown(agent_card("🧪", "test", "Tester Agent", "7-category test suite complete (RAG)",
                           "done", st.session_state.test_time), unsafe_allow_html=True)
    with st.expander("🧪  View Test Cases", expanded=False):
        if st.session_state.test_cases.startswith("Error:"):
            st.error(st.session_state.test_cases)
        else:
            st.code(st.session_state.test_cases, language="python")

# ── Step 5: Report Agent ──────────────────────────────────────────────
if (
    st.session_state.test_completed
    and not st.session_state.use_crew
    and not st.session_state.report_completed
):
    log_activity("report", "Compiling agent outputs via RAG…")
    log_activity("report", "Generating executive summary…")

    st.markdown(agent_card(
        "📑", "report", "Report Agent",
        "RAG: Generating corporate project report", "running"
    ), unsafe_allow_html=True)

    with st.spinner("Report Agent working — generating corporate documentation via RAG…"):
        try:
            t0      = time.time()
            report  = run_report_agent()
            st.session_state.report_time      = round(time.time() - t0, 2)
            st.session_state.report_text      = report
            st.session_state.report_completed = True
            st.session_state.shap_dashboard   = get_shap_dashboard_data()
            mark_agent_done("report")
        except Exception as e:
            st.error(f"Report Agent Error: {e}")
            st.session_state.report_text      = f"Error: {e}"
            st.session_state.report_completed = True
            mark_agent_done("report")
    st.rerun()


# ── Report output ─────────────────────────────────────────────────────
if st.session_state.report_completed:
    st.markdown(agent_card(
        "📑", "report", "Report Agent",
        "Corporate project documentation generated (RAG)", "done",
        st.session_state.report_time
    ), unsafe_allow_html=True)

    with st.expander("📑 View Corporate Project Report", expanded=False):
        if st.session_state.report_text.startswith("Error:"):
            st.error(st.session_state.report_text)
        else:
            st.markdown(
                f'<div class="dv-output-box">{st.session_state.report_text}</div>',
                unsafe_allow_html=True,
            )
            pdf_file = generate_pdf(st.session_state.report_text)
            st.download_button(
                label="📄 Download Project Report (PDF)",
                data=pdf_file,
                file_name="project_report.pdf",
                mime="application/pdf",
            )

# ── SHAP Dashboard ────────────────────────────────────────────────────
if st.session_state.report_completed and st.session_state.shap_dashboard:
    d = st.session_state.shap_dashboard
    st.markdown("<hr class='dv-divider'/>", unsafe_allow_html=True)
    st.markdown("""
    <div class="dv-badge" style="margin-bottom:1.5rem;">🛡️ SHAP Responsible AI Dashboard</div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    safety_pct = int(d.get("average_safety_score", 1.0) * 100)
    coverage_pct = int(d.get("coverage_score", 0) * 100)

    with c1:
        st.metric("🔬 Total Evaluations", d.get("total_evaluations", 0))
    with c2:
        st.metric("🛡️ Avg Safety Score", f"{safety_pct}%",
                  delta="✅ Safe" if safety_pct >= 85 else "⚠️ Review")
    with c3:
        st.metric("🚫 Blocked Content", d.get("blocked_count", 0))
    with c4:
        st.metric("📊 SHAP Coverage", f"{coverage_pct}%",
                  delta="Full pipeline" if coverage_pct >= 80 else "Partial")

# ── Pipeline complete CTA ─────────────────────────────────────────────
if st.session_state.report_completed:
    st.markdown("<hr class='dv-divider'/>", unsafe_allow_html=True)
    st.markdown("""
    <div class="dv-cta-block">
        <div class="dv-badge">🎯 Pipeline Complete</div>
        <h2 class="dv-cta-heading">Ready to Launch</h2>
        <p class="dv-cta-sub">Your full-stack web application is ready. Click below to preview it live.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🌐  View Generated Project", use_container_width=True):
            st.switch_page("pages/Generated_Project.py")


# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="dv-sidebar-brand">
        <div class="dv-sidebar-logo">DevVerse</div>
        <div class="dv-sidebar-tagline">AI Virtual Development Pod</div>
    </div>
    <hr class="dv-sidebar-divider"/>
    <div class="dv-sidebar-section-title">Pipeline Status</div>
    """, unsafe_allow_html=True)

    def sidebar_item(label: str, icon: str, done: bool) -> str:
        cls  = "dv-sb-done" if done else "dv-sb-pending"
        tick = "✓" if done else "·"
        return f'<div class="dv-sidebar-item {cls}"><span class="dv-sb-icon">{icon}</span> {tick} {label}</div>'

    st.markdown(
        sidebar_item("RFP Uploaded",   "📄", st.session_state.pdf_processed)   +
        sidebar_item("User Stories",   "🧠", st.session_state.ba_completed)     +
        sidebar_item("System Design",  "🎨", st.session_state.design_completed) +
        sidebar_item("Code Generated", "💻", st.session_state.dev_completed)    +
        sidebar_item("Tests Written",  "🧪", st.session_state.test_completed)   +
        sidebar_item("Project Report", "📑", st.session_state.report_completed),
        unsafe_allow_html=True,
    )

    # SHAP score badge
    if st.session_state.shap_score > 0:
        color = "#ef4444" if st.session_state.shap_score > 0.55 else (
            "#f59e0b" if st.session_state.shap_score > 0.15 else "#22c55e"
        )
        st.markdown(
            f'<div style="margin-top:0.75rem; font-size:0.8rem; color:{color};">'
            f'🛡️ SHAP toxicity: {st.session_state.shap_score:.3f}</div>',
            unsafe_allow_html=True,
        )

    # SHAP dashboard mini in sidebar
    if st.session_state.shap_dashboard:
        d = st.session_state.shap_dashboard
        safety_pct = int(d.get("average_safety_score", 1.0) * 100)
        st.markdown(
            f'<div style="margin-top:0.5rem; font-size:0.75rem; color:#a78bfa;">'
            f'📊 SHAP Coverage: {int(d.get("coverage_score",0)*100)}% '
            f'| Safety: {safety_pct}%</div>',
            unsafe_allow_html=True,
        )

    st.markdown("""
    <hr class="dv-sidebar-divider"/>
    <div class="dv-sidebar-footer">
        Powered by<br>
        <span class="dv-tech-pill" style="background:rgba(108,99,255,0.15);color:#a78bfa">CrewAI</span>
        <span class="dv-tech-pill" style="background:rgba(0,212,255,0.1);color:#67e8f9">LangChain RAG</span>
        <span class="dv-tech-pill" style="background:rgba(0,229,160,0.1);color:#6ee7b7">ChromaDB</span>
        <span class="dv-tech-pill" style="background:rgba(239,68,68,0.1);color:#fca5a5">SHAP AI</span>
        <span class="dv-tech-pill" style="background:rgba(251,191,36,0.1);color:#fde68a">Groq LLM</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("↺  Reset Project", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.session_state.dv_log     = []
        st.session_state.dv_active  = None
        st.session_state.dv_started = False
        st.rerun()