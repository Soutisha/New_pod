"""
DevVerse — Generated Project Page.
Live preview + source code viewer for the AI-generated web app.
Uses Docker sandbox when available, falls back to direct Flask process.
"""

import streamlit as st
import time
import sys
from pathlib import Path

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="DevVerse — Live Preview",
    page_icon="🌐",
    layout="wide"
)

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

# ── Imports ─────────────────────────────────────────────────
from sandbox.sandbox_manager import SandboxManager       # noqa: E402

# ── File paths ──────────────────────────────────────────────
base_dir = Path(__file__).parent.parent
proj_dir = base_dir / "generated_project"

EXPECTED_FILES = [
    ("app.py",                proj_dir / "app.py"),
    ("templates/index.html",  proj_dir / "templates" / "index.html"),
    ("static/style.css",      proj_dir / "static" / "style.css"),
    ("requirements.txt",      proj_dir / "requirements.txt"),
    ("test_app.py",           proj_dir / "test_app.py"),
]

# ── Session state ────────────────────────────────────────────
if "server_running" not in st.session_state:
    st.session_state.server_running = False
if "sandbox_mgr" not in st.session_state:
    st.session_state.sandbox_mgr = SandboxManager()

# ── Hero ─────────────────────────────────────────────────────
st.markdown("""
<div style="padding:2.5rem 0 1.5rem;">
    <div class="dv-badge">🌐 Live Generated Project</div>
    <h1 class="dv-headline" style="font-size:2.2rem !important; text-align:left;">
        Your <span class="dv-gradient-text">App is Ready</span>
    </h1>
    <p class="dv-subtitle" style="text-align:left; margin:0 0 1.5rem !important; font-size:0.95rem !important;">
        Preview the AI-generated web application live, or explore its source code below.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Guard: project must be generated ───────────────────────
app_file = proj_dir / "app.py"
if not app_file.exists():
    st.markdown("""
    <div style="text-align:center; padding:5rem 0;">
        <div style="font-size:4rem; margin-bottom:1rem;">🚧</div>
        <h3 style="font-weight:700; color:#e8f4ff;">No Project Generated Yet</h3>
        <p style="color:#64748B; font-size:0.95rem; max-width:420px; margin:0.5rem auto 2rem;">
            Go back to the main page and run the full agent pipeline first.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("← Back to Dev Pod"):
        st.switch_page("DevVerse.py")
    st.stop()

# ── Sandbox mode indicator ───────────────────────────────────
sandbox: SandboxManager = st.session_state.sandbox_mgr
mode_label = "🐳 Docker Sandbox" if sandbox.is_docker_available else "🐍 Direct Process"
st.markdown(
    f'<div style="font-size:0.78rem; color:#a78bfa; margin-bottom:1rem;">'
    f'Execution mode: <strong>{mode_label}</strong></div>',
    unsafe_allow_html=True,
)

# ── File status chips ────────────────────────────────────────
chips_html = '<div style="display:flex; gap:8px; margin-bottom:1.5rem; flex-wrap:wrap;">'
for name, path in EXPECTED_FILES:
    if path.exists():
        size = path.stat().st_size
        size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
        chips_html += (
            f'<span style="background:rgba(0,255,136,0.07); border:1px solid rgba(0,255,136,0.25);'
            f' border-radius:999px; padding:4px 13px; font-size:0.73rem; font-weight:600;'
            f' color:#6EE7B7;">✓ {name} <span style="opacity:0.65">({size_str})</span></span>'
        )
    else:
        chips_html += (
            f'<span style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);'
            f' border-radius:999px; padding:4px 13px; font-size:0.73rem; font-weight:600;'
            f' color:#3d5475;">○ {name}</span>'
        )
chips_html += "</div>"
st.markdown(chips_html, unsafe_allow_html=True)

# ── Launch controls ──────────────────────────────────────────
col_launch, col_open = st.columns([3, 1])

with col_launch:
    if not st.session_state.server_running:
        if st.button("▶  Launch Live Preview", use_container_width=True):
            with st.spinner(f"Starting {mode_label}…"):
                try:
                    sandbox.start_sandbox()
                    time.sleep(2.5)
                    st.session_state.server_running = True
                    st.success("✅  Server running at http://localhost:5000")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to start server: {exc}")
    else:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; padding:13px 20px;
                    background:rgba(0,255,136,0.06); border:1px solid rgba(0,255,136,0.2);
                    border-radius:14px; color:#6EE7B7; font-weight:600; font-size:0.9rem;">
            <span style="font-size:1rem;">●</span>
            Server running at localhost:5000
        </div>
        """, unsafe_allow_html=True)

        if st.button("⏹ Stop Server", use_container_width=False):
            sandbox.stop_sandbox()
            st.session_state.server_running = False
            st.rerun()

with col_open:
    st.link_button("↗  Open in New Tab", "http://127.0.0.1:5000/", use_container_width=True)

st.markdown("<hr class='dv-divider'/>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────
tab_preview, tab_code, tab_tests = st.tabs([
    "🌐  Live Preview", "📄  Source Code", "🧪  Run Tests"
])

with tab_preview:
    if st.session_state.server_running:
        st.markdown(
            '<div style="border-radius:16px; overflow:hidden; border:1px solid rgba(0,212,255,0.15);'
            ' box-shadow:0 12px 40px rgba(0,0,0,0.6);">',
            unsafe_allow_html=True
        )
        cache_buster = int(time.time())
        st.components.v1.iframe(f"http://127.0.0.1:5000/?ts={cache_buster}", height=750, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="height:380px; display:flex; flex-direction:column; align-items:center;
                    justify-content:center; background:rgba(255,255,255,0.02);
                    border:2px dashed rgba(0,212,255,0.12); border-radius:16px;">
            <div style="font-size:3rem; margin-bottom:0.75rem;">▶</div>
            <p style="color:#64748B; font-size:0.93rem;">
                Click <strong>Launch Live Preview</strong> to start the server
            </p>
        </div>
        """, unsafe_allow_html=True)

with tab_code:
    available = [(name, path) for name, path in EXPECTED_FILES if path.exists()]

    if not available:
        st.info("No source files found.")
    else:
        names    = [n for n, _ in available]
        selected = st.selectbox("📂  Select file:", names, label_visibility="collapsed")

        for name, path in available:
            if name != selected:
                continue
            try:
                content = path.read_text(encoding="utf-8")
                ext = path.suffix.lstrip(".")
                lang = {"py": "python", "html": "html", "css": "css",
                        "js": "javascript", "txt": "text"}.get(ext, "text")

                st.markdown(
                    f'<div style="display:flex; justify-content:space-between;'
                    f' align-items:center; margin-bottom:0.6rem;">'
                    f'<code style="font-size:0.82rem; color:#64748B;">{name}</code>'
                    f'<span style="font-size:0.75rem; color:#3d5475;">'
                    f'{len(content.splitlines())} lines</span></div>',
                    unsafe_allow_html=True
                )
                st.code(content, language=lang)
                st.download_button(
                    label=f"⬇️  Download {path.name}",
                    data=content,
                    file_name=path.name,
                    mime="text/plain",
                )
            except Exception as exc:
                st.error(f"Error reading {name}: {exc}")

with tab_tests:
    test_file = proj_dir / "test_app.py"
    if not test_file.exists():
        st.info("No test_app.py found. Run the pipeline to generate tests.")
    else:
        st.markdown("**📄 Generated Test Suite**")
        st.code(test_file.read_text(encoding="utf-8"), language="python")
        st.markdown("""
        **▶ To run tests:**
        ```bash
        cd generated_project
        pip install pytest
        pytest test_app.py -v --tb=short
        ```
        """)
