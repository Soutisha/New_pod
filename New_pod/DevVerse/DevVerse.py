"""
DevVerse - AI-Powered Virtual Development Pod
Main Streamlit Application — Premium UI (v2 - Fixed)
"""

import streamlit as st
import PyPDF2
import time
import os
import re
from pathlib import Path

# ============================================================
# Page Configuration — MUST be first Streamlit call
# ============================================================
st.set_page_config(
    page_title="DevVerse — AI Development Pod",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Environment Setup
# ============================================================
project_root = Path(__file__).parent.absolute()
env_path = project_root / ".env"

if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("GROQ_API_KEY="):
                os.environ["GROQ_API_KEY"] = line.split("=", 1)[1]
                break

# Import agents AFTER env is loaded
from Extraction import process_pdf_text
from crew_businessAgent import run_business_analyst
from crew_designAgent import run_design_agent
from crew_developerAgent import run_developer_agent, run_generated_project
from crew_testerAgent import run_tester_agent

# ============================================================
# Load Custom CSS
# ============================================================
def load_css(file_name: str) -> None:
    css_path = Path(__file__).parent / file_name
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styleDevVerse.css")

# ============================================================
# Session State Initialization
# ============================================================
defaults = {
    "pdf_text":           "",      # ← Store pdf_text so it survives rerun
    "pdf_processed":      False,
    "project_initialized": False,
    "ba_completed":       False,
    "design_completed":   False,
    "dev_completed":      False,
    "test_completed":     False,
    "ba_text":            "",
    "design_text":        "",
    "dev_code":           "",
    "test_cases":         "",
    "ba_time":            0.0,
    "design_time":        0.0,
    "dev_time":           0.0,
    "test_time":          0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# Helper — Agent Card HTML
# ============================================================
_ICON_COLORS = {
    "ba":   "rgba(167,139,250,0.15)",
    "des":  "rgba(56,189,248,0.15)",
    "dev":  "rgba(52,211,153,0.15)",
    "test": "rgba(251,146,60,0.15)",
}

def agent_card(icon: str, kind: str, title: str, subtitle: str, status: str, elapsed: float = 0.0) -> str:
    badge_map = {
        "running": ('dv-status-running', '⬤ Running'),
        "done":    ('dv-status-done',    '✓ Done'),
        "error":   ('dv-status-error',   '✗ Error'),
    }
    badge_cls, badge_txt = badge_map.get(status, badge_map["running"])
    time_html = f'<p class="dv-gen-time">⏱ Completed in {elapsed:.1f}s</p>' if status == "done" else ""
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

# ============================================================
# Hero Section
# ============================================================
st.markdown("""
<div class="dv-hero">
    <div class="dv-badge">✦ AI-Powered Development</div>
    <h1 class="dv-headline">
        Your <span class="dv-gradient-text">Virtual Dev Pod</span><br>
        Ships Code Autonomously
    </h1>
    <p class="dv-subtitle">
        Upload your RFP and watch as AI agents — Business Analyst, Designer,
        Developer &amp; Tester — collaborate to deliver production-ready software.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Pipeline Progress Bar
# ============================================================
steps = [
    ("ba_completed",      "🧠", "Analyst"),
    ("design_completed",  "🎨", "Designer"),
    ("dev_completed",     "💻", "Developer"),
    ("test_completed",    "🧪", "Tester"),
]

def make_pipeline() -> str:
    html = '<div class="dv-pipeline">'
    for i, (flag, icon, label) in enumerate(steps):
        done   = st.session_state.get(flag, False)
        prev   = st.session_state.get(steps[i-1][0], False) if i > 0 else True
        active = prev and not done and st.session_state.project_initialized

        if done:
            dot_cls = "dv-pipeline-dot-done"
            dot_txt = "✓"
        elif active:
            dot_cls = "dv-pipeline-dot-active"
            dot_txt = str(i + 1)
        else:
            dot_cls = "dv-pipeline-dot-pending"
            dot_txt = str(i + 1)

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

# ============================================================
# File Upload
# ============================================================
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
            st.session_state.pdf_text = extracted          # ← persisted in session
            st.session_state.pdf_processed = True
            st.success("✅  PDF uploaded and parsed successfully")
    except Exception as e:
        st.error(f"❌  Error reading PDF: {e}")
        st.session_state.pdf_processed = False

# ============================================================
# Initialize Button
# ============================================================
if st.session_state.pdf_processed and not st.session_state.project_initialized:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        if st.button("🚀  Initialize Dev Pod", use_container_width=True):
            st.session_state.project_initialized = True
            st.rerun()

# ============================================================
# Agent Pipeline Execution
# ============================================================

# ── Step 1: Business Analyst ────────────────────────────────
if st.session_state.project_initialized and not st.session_state.ba_completed:

    st.markdown(agent_card("🧠", "ba", "Business Analyst",
                           "Translating RFP into actionable user stories", "running"),
                unsafe_allow_html=True)

    with st.spinner("BA Agent working — generating user stories…"):
        try:
            # Extract requirements from stored pdf_text
            pdf_content = st.session_state.get("pdf_text", "")
            reqs, _ = process_pdf_text(pdf_content)
            req_text = "\n".join(reqs)
            st.session_state["requirements"] = req_text

            req_file = project_root / "extracted_reqmts.txt"
            req_file.write_text("\n".join(reqs), encoding="utf-8")

            t0 = time.time()
            ba_out = run_business_analyst()
            st.session_state.ba_time = round(time.time() - t0, 2)
            st.session_state.ba_text = ba_out
            st.session_state.ba_completed = True
        except Exception as e:
            st.error(f"Business Analyst Error: {e}")
            st.session_state.ba_text = f"Error: {e}"
            st.session_state.ba_completed = True   # allow flow to continue

    st.rerun()

# ── BA Output ───────────────────────────────────────────────
if st.session_state.ba_completed:
    st.markdown(agent_card("🧠", "ba", "Business Analyst", "User stories generated",
                           "done", st.session_state.ba_time), unsafe_allow_html=True)

    with st.expander("📋  View User Stories", expanded=False):
        if st.session_state.ba_text.startswith("Error:"):
            st.error(st.session_state.ba_text)
        else:
            st.markdown(
                f'<div class="dv-output-box">{st.session_state.ba_text}</div>',
                unsafe_allow_html=True
            )

# ── Step 2: Design Agent ────────────────────────────────────
if st.session_state.ba_completed and not st.session_state.design_completed:

    st.markdown(agent_card("🎨", "des", "Design Agent",
                           "Creating system architecture & diagrams", "running"),
                unsafe_allow_html=True)

    with st.spinner("Design Agent working — building architecture…"):
        try:
            t0 = time.time()
            design_out = run_design_agent()
            st.session_state.design_time = round(time.time() - t0, 2)
            st.session_state.design_text = design_out
            st.session_state.design_completed = True
        except Exception as e:
            st.error(f"Design Agent Error: {e}")
            st.session_state.design_text = f"Error: {e}"
            st.session_state.design_completed = True

    st.rerun()

# ── Design Output ────────────────────────────────────────────
if st.session_state.design_completed:
    st.markdown(agent_card("🎨", "des", "Design Agent", "Architecture & diagrams ready",
                           "done", st.session_state.design_time), unsafe_allow_html=True)

    # Extract mermaid blocks before rendering
    mermaid_blocks = []
    clean_design = st.session_state.design_text
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
                unsafe_allow_html=True
            )

    # Render Mermaid diagrams OUTSIDE the expander for reliable rendering
    if mermaid_blocks:
        from streamlit_mermaid import st_mermaid
        st.markdown("**📊 Architecture Diagram**")
        for i, block in enumerate(mermaid_blocks):
            block_clean = block.strip()
            if block_clean:
                try:
                    st_mermaid(block_clean, key=f"mermaid_{i}")
                except Exception as mermaid_err:
                    st.warning(f"Could not render diagram: {mermaid_err}")
                    st.code(block_clean, language="text")

# ── Step 3: Developer Agent ─────────────────────────────────
if st.session_state.design_completed and not st.session_state.dev_completed:

    st.markdown(agent_card("💻", "dev", "Developer Agent",
                           "Writing full-stack production code", "running"),
                unsafe_allow_html=True)

    with st.spinner("Developer Agent working — generating codebase…"):
        try:
            t0 = time.time()
            code_out = run_developer_agent()
            st.session_state.dev_time = round(time.time() - t0, 2)
            st.session_state.dev_code = code_out
            st.session_state.dev_completed = True
        except Exception as e:
            st.error(f"Developer Agent Error: {e}")
            st.session_state.dev_code = f"Error: {e}"
            st.session_state.dev_completed = True

    st.rerun()

# ── Dev Output ───────────────────────────────────────────────
if st.session_state.dev_completed:
    st.markdown(agent_card("💻", "dev", "Developer Agent", "Full-stack codebase generated",
                           "done", st.session_state.dev_time), unsafe_allow_html=True)

    with st.expander("🗂️  View Generated Codebase", expanded=False):
        if st.session_state.dev_code.startswith("Error:"):
            st.error(st.session_state.dev_code)
        else:
            st.code(st.session_state.dev_code, language="python")

# ── Step 4: Tester Agent ────────────────────────────────────
if st.session_state.dev_completed and not st.session_state.test_completed:

    st.markdown(agent_card("🧪", "test", "Tester Agent",
                           "Crafting unit tests, integration tests & QA coverage", "running"),
                unsafe_allow_html=True)

    with st.spinner("Tester Agent working — writing test suite…"):
        try:
            t0 = time.time()
            test_out = run_tester_agent()
            st.session_state.test_time = round(time.time() - t0, 2)
            st.session_state.test_cases = test_out
            st.session_state.test_completed = True
        except Exception as e:
            st.error(f"Tester Agent Error: {e}")
            st.session_state.test_cases = f"Error: {e}"
            st.session_state.test_completed = True

    st.rerun()

# ── Test Output ──────────────────────────────────────────────
if st.session_state.test_completed:
    st.markdown(agent_card("🧪", "test", "Tester Agent", "Test suite complete",
                           "done", st.session_state.test_time), unsafe_allow_html=True)

    with st.expander("🧪  View Test Cases", expanded=False):
        if st.session_state.test_cases.startswith("Error:"):
            st.error(st.session_state.test_cases)
        else:
            st.code(st.session_state.test_cases, language="python")

# ============================================================
# View Generated Project CTA
# ============================================================
if st.session_state.dev_completed:
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

# ============================================================
# Sidebar
# ============================================================
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
        sidebar_item("RFP Uploaded",   "📄", st.session_state.pdf_processed)  +
        sidebar_item("User Stories",   "🧠", st.session_state.ba_completed)    +
        sidebar_item("System Design",  "🎨", st.session_state.design_completed)+
        sidebar_item("Code Generated", "💻", st.session_state.dev_completed)   +
        sidebar_item("Tests Written",  "🧪", st.session_state.test_completed),
        unsafe_allow_html=True
    )

    st.markdown("""
    <hr class="dv-sidebar-divider"/>
    <div class="dv-sidebar-footer">
        Powered by<br>
        <span class="dv-tech-pill" style="background:rgba(108,99,255,0.15);color:#a78bfa">CrewAI</span>
        <span class="dv-tech-pill" style="background:rgba(0,212,255,0.1);color:#67e8f9">LangChain</span>
        <span class="dv-tech-pill" style="background:rgba(0,229,160,0.1);color:#6ee7b7">Groq LLM</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("↺  Reset Project", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()