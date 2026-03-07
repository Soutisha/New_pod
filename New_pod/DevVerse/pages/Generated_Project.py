"""
DevVerse — Generated Project Page
Live preview + source code viewer for the AI-generated web app.
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

# ── CSS ────────────────────────────────────────────────────
css_path = Path(__file__).parent.parent / "styleDevVerse.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ── Import run function ─────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
from crew_developerAgent import run_generated_project   # type: ignore

# ── File paths ──────────────────────────────────────────────
base_dir = Path(__file__).parent.parent
proj_dir = base_dir / "generated_project"

EXPECTED_FILES = [
    ("app.py",                proj_dir / "app.py"),
    ("templates/index.html",  proj_dir / "templates" / "index.html"),
    ("static/style.css",      proj_dir / "static" / "style.css"),
    ("static/script.js",      proj_dir / "static" / "script.js"),
    ("requirements.txt",      proj_dir / "requirements.txt"),
]

# ── Session state ────────────────────────────────────────────
if "server_running" not in st.session_state:
    st.session_state.server_running = False

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
        <h3 style="font-family:'Inter',sans-serif; font-weight:700; color:#0F172A;">
            No Project Generated Yet
        </h3>
        <p style="color:#64748B; font-size:0.95rem; max-width:420px; margin:0.5rem auto 2rem;">
            Go back to the main page and run the full agent pipeline first.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("← Back to Dev Pod"):
        st.switch_page("DevVerse.py")
    st.stop()

# ── File status chips ────────────────────────────────────────
chips_html = '<div style="display:flex; gap:8px; margin-bottom:1.5rem; flex-wrap:wrap;">'
for name, path in EXPECTED_FILES:
    if path.exists():
        size = path.stat().st_size
        size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
        chips_html += (
            f'<span style="background:#F0FAF7; border:1px solid #6EE7B7; border-radius:999px;'
            f' padding:4px 13px; font-size:0.73rem; font-weight:600; color:#065F46;">'
            f'✓ {name} <span style="opacity:0.65">({size_str})</span></span>'
        )
    else:
        chips_html += (
            f'<span style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:999px;'
            f' padding:4px 13px; font-size:0.73rem; font-weight:600; color:#94A3B8;">'
            f'○ {name}</span>'
        )
chips_html += "</div>"
st.markdown(chips_html, unsafe_allow_html=True)

# ── Launch controls ──────────────────────────────────────────
col_launch, col_open = st.columns([3, 1])

with col_launch:
    if not st.session_state.server_running:
        if st.button("▶  Launch Live Preview", use_container_width=True):
            with st.spinner("Installing requirements & starting Flask server…"):
                try:
                    run_generated_project()
                    time.sleep(2.5)          # give Flask a moment to start
                    st.session_state.server_running = True
                    st.success("✅  Server running at http://localhost:5000")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to start server: {exc}")
    else:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; padding:13px 20px;
                    background:#F0FAF7; border:1px solid #6EE7B7;
                    border-radius:14px; color:#065F46; font-weight:600; font-size:0.9rem;">
            <span style="font-size:1rem;">●</span>
            Flask server running at localhost:5000
        </div>
        """, unsafe_allow_html=True)

with col_open:
    st.link_button("↗  Open in New Tab", "http://127.0.0.1:5000/", use_container_width=True)

st.markdown("<hr class='dv-divider'/>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────
tab_preview, tab_code = st.tabs(["🌐  Live Preview", "📄  Source Code"])

with tab_preview:
    if st.session_state.server_running:
        st.markdown(
            '<div style="border-radius:16px; overflow:hidden; border:1px solid #E2E8F0;'
            ' box-shadow:0 12px 40px rgba(15,23,42,0.12);">',
            unsafe_allow_html=True
        )
        # Append a timestamp to force the iframe to completely reload
        import time
        cache_buster = int(time.time())
        st.components.v1.iframe(f"http://127.0.0.1:5000/?ts={cache_buster}", height=750, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="height:380px; display:flex; flex-direction:column; align-items:center;
                    justify-content:center; background:#F8FAFC; border:2px dashed #E2E8F0;
                    border-radius:16px;">
            <div style="font-size:3rem; margin-bottom:0.75rem;">▶</div>
            <p style="color:#64748B; font-size:0.93rem;">
                Click <strong>Launch Live Preview</strong> to start the Flask server
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
                    f'<code style="font-family:\'JetBrains Mono\',monospace; font-size:0.82rem;'
                    f' color:#64748B;">{name}</code>'
                    f'<span style="font-size:0.75rem; color:#94A3B8;">'
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
