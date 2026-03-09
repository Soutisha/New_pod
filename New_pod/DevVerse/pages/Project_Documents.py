"""
DevVerse — Project Documents Page.
Clean document browser with download cards.
"""

import streamlit as st
from pathlib import Path
import sys

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title="DevVerse — Documents", page_icon="📁", layout="wide")

# ── Ensure project root importable ──────────────────────────
_parent = str(Path(__file__).parent.parent.absolute())
if _parent not in sys.path:
    sys.path.insert(0, _parent)

# ── CSS ────────────────────────────────────────────────────
css_path = Path(__file__).parent.parent / "frontend" / "styleDevVerse.css"
if not css_path.exists():
    css_path = Path(__file__).parent.parent / "styleDevVerse.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────
st.markdown("""
<div style="padding:2.5rem 0 1.5rem;">
    <div class="dv-badge">📁 Project Artifacts</div>
    <h1 class="dv-headline" style="font-size:2.2rem !important; text-align:left;">
        Generated <span class="dv-gradient-text">Documents</span>
    </h1>
    <p class="dv-subtitle" style="text-align:left; margin:0 0 1.5rem !important;">
        Browse and download all artifacts produced by the AI development team.
    </p>
</div>
<hr class="dv-divider"/>
""", unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────────
base_dir    = Path(__file__).parent.parent
outputs_dir = base_dir / "outputs"


def _read(fname: str) -> str | None:
    """Read from outputs/ first, fall back to project root."""
    for directory in [outputs_dir, base_dir]:
        p = directory / fname
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception as exc:
                return f"Error reading file: {exc}"
    return None


def render_doc_card(icon: str, title: str, desc: str,
                    content: str | None, filename: str, lang: str = "text") -> None:
    """Render a single document card."""
    exists = content is not None

    badge_cls = "dv-status-done" if exists else "dv-status-error"
    badge_txt = "✓ Generated" if exists else "○ Pending"

    st.markdown(f"""
    <div class="dv-doc-card">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:1rem;">
            <div style="display:flex; align-items:center; gap:14px;">
                <span style="font-size:2rem;">{icon}</span>
                <div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
            </div>
            <span class="dv-status {badge_cls}" style="flex-shrink:0;">{badge_txt}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if exists:
        with st.expander(f"Preview — {title}", expanded=False):
            snippet = content[:3000] + ("…" if len(content) > 3000 else "")
            if lang == "python":
                st.code(snippet, language="python")
            else:
                st.markdown(
                    f'<div class="dv-output-box">{snippet}</div>',
                    unsafe_allow_html=True
                )

        _, btn_col = st.columns([3, 1])
        with btn_col:
            st.download_button(
                label="⬇️  Download",
                data=content,
                file_name=filename,
                mime="text/plain",
                use_container_width=True,
            )
    else:
        st.info("Not generated yet — run the Dev Pod pipeline to create this document.")

    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)


# ── Load all documents ────────────────────────────────────────
ba_content     = _read("User_Stories.txt")
design_content = _read("System_Design.txt")
code_content   = _read("Implementation_Code.txt")
test_content   = _read("Test_Cases.txt")
report_content = _read("Project_Report.txt")

all_docs = [ba_content, design_content, code_content, test_content, report_content]
has_any  = any(x is not None for x in all_docs)

if not has_any:
    st.markdown("""
    <div style="text-align:center; padding:4rem 0;">
        <div style="font-size:4rem; margin-bottom:1rem;">📂</div>
        <h3 style="font-weight:700; color:#e8f4ff;">No Documents Yet</h3>
        <p style="color:#64748B; font-size:0.95rem; max-width:400px; margin:0 auto;">
            Run the Dev Pod from the main page to generate user stories,
            architecture, code, test cases, and the project report.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    count      = sum(1 for x in all_docs if x)
    code_words = len(code_content.split()) if code_content else 0
    test_lines = len(test_content.splitlines()) if test_content else 0

    st.markdown(f"""
    <div style="display:flex; gap:1rem; margin-bottom:2rem; flex-wrap:wrap;">
        <div class="dv-agent-card" style="min-width:130px; text-align:center; padding:1rem 1.5rem;">
            <div style="font-size:1.7rem; font-weight:800; color:#a78bfa;">{count}/5</div>
            <div style="font-size:0.72rem; color:#3d5475; text-transform:uppercase; letter-spacing:.06em;">Ready</div>
        </div>
        <div class="dv-agent-card" style="min-width:130px; text-align:center; padding:1rem 1.5rem;">
            <div style="font-size:1.7rem; font-weight:800; color:#34d399;">{code_words:,}</div>
            <div style="font-size:0.72rem; color:#3d5475; text-transform:uppercase; letter-spacing:.06em;">Code Tokens</div>
        </div>
        <div class="dv-agent-card" style="min-width:130px; text-align:center; padding:1rem 1.5rem;">
            <div style="font-size:1.7rem; font-weight:800; color:#fb923c;">{test_lines:,}</div>
            <div style="font-size:0.72rem; color:#3d5475; text-transform:uppercase; letter-spacing:.06em;">Test Lines</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_doc_card("📋", "User Stories",
                    "Agile stories from the Business Analyst agent",
                    ba_content, "User_Stories.txt")

    render_doc_card("🏗️", "System Architecture",
                    "Technical design & diagrams from the Design agent",
                    design_content, "System_Design.txt")

    render_doc_card("💻", "Implementation Code",
                    "Full-stack codebase from the Developer agent",
                    code_content, "Implementation_Code.txt", lang="python")

    render_doc_card("🧪", "Test Cases (7-Category Suite)",
                    "Ultra-comprehensive pytest suite from the Tester agent",
                    test_content, "Test_Cases.txt", lang="python")

    render_doc_card("📑", "Corporate Project Report",
                    "10-section executive report from the Report agent",
                    report_content, "Project_Report.txt")
