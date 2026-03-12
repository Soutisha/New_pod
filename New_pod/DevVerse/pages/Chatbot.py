"""
DevVerse — Chatbot Page (RAG-powered).
─────────────────────────────────────────────────────────────────────────
The PM Lead chatbot answers project questions using Retrieval-Augmented
Generation (ChromaDB + LangChain + Groq) — NO direct LLM calls.

Every user message is filtered by SHAP Responsible AI before querying RAG,
and every bot response is filtered before displaying.
"""

import streamlit as st
from pathlib import Path
import sys

# ── Page configuration ────────────────────────────────────────────────
st.set_page_config(page_title="DevVerse Chat", page_icon="💬", layout="wide")

# ── Ensure project root is importable ────────────────────────────────
_parent = str(Path(__file__).parent.parent.absolute())
if _parent not in sys.path:
    sys.path.insert(0, _parent)

# ── Load CSS ──────────────────────────────────────────────────────────
css_path = Path(__file__).parent.parent / "frontend" / "styleDevVerse.css"
if not css_path.exists():
    css_path = Path(__file__).parent.parent / "styleDevVerse.css"
if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

# ── RAG + Responsible AI imports ─────────────────────────────────────
from core.rag_engine import rag_query, refresh_knowledge_base          # noqa: E402
from core.responsible_ai import filter_input, filter_output, explain_with_shap  # noqa: E402

# Reuse the already-warmed RAG stack from the main app (caching is global)
@st.cache_resource(show_spinner=False)
def _ensure_rag_ready():
    from core.rag_engine import build_vector_store, _get_embeddings, _get_llm
    from core.rag_engine import _COLLECTIONS
    _get_embeddings()
    _get_llm()
    for collection_name in _COLLECTIONS.values():
        build_vector_store(collection_name=collection_name)
    return True

_ensure_rag_ready()

# ── Session state ─────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Hero header ───────────────────────────────────────────────────────
st.markdown("""
<div class="dv-hero" style="padding:2.5rem 1rem 1.5rem;">
    <div class="dv-badge">👔 Project Manager Lead — RAG Chatbot</div>
    <h1 class="dv-headline" style="font-size:2.1rem !important;">
        Consult the <span class="dv-gradient-text">PM Lead</span>
    </h1>
    <p class="dv-subtitle" style="font-size:0.95rem !important;">
        All answers are powered by Retrieval-Augmented Generation (ChromaDB + Groq).
        SHAP Responsible AI filters are active on every message.
    </p>
</div>
<hr class="dv-divider"/>
""", unsafe_allow_html=True)

# ── Suggested prompts ─────────────────────────────────────────────────
SUGGESTED = [
    "What are the user stories?",
    "Explain the system architecture",
    "What tests were written?",
    "Summarise the project report",
    "What technology stack is used?",
]

if not st.session_state.chat_history:
    st.markdown("""
    <div style="text-align:center; padding:2rem 0; color:#94A3B8;">
        <div style="font-size:3rem; margin-bottom:0.75rem;">👔</div>
        <p style="font-size:0.93rem; color:#64748B;">
            I am the Project Manager Lead. Ask me about the generated code,
            user stories, architecture, or test coverage.<br/>
            <span style="color:#a78bfa; font-size:0.8rem;">
                🔒 Powered by RAG &nbsp;|&nbsp; 🛡️ SHAP Responsible AI Active
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**💡 Suggested questions:**")
    cols = st.columns(len(SUGGESTED))
    for col, q in zip(cols, SUGGESTED):
        with col:
            if st.button(q, use_container_width=True, key=f"suggest_{q[:20]}"):
                st.session_state._suggested_q = q
                st.rerun()

# Handle suggested question
if hasattr(st.session_state, "_suggested_q"):
    user_input = st.session_state._suggested_q
    del st.session_state._suggested_q
else:
    user_input = None

# ── Display chat history ────────────────────────────────────────────
for speaker, msg, shap_score in st.session_state.chat_history:
    if speaker == "You":
        st.markdown(
            f'<div class="dv-chat-user"><div class="dv-bubble">{msg}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        badge = ""
        if shap_score is not None and shap_score > 0.0:
            badge = (
                f'<span style="font-size:0.7rem; color:#94A3B8; margin-left:8px;">'
                f'🛡️ SHAP: {shap_score:.3f}</span>'
            )
        st.markdown(
            f'<div class="dv-chat-bot"><div class="dv-bubble">{msg}{badge}</div></div>',
            unsafe_allow_html=True,
        )

# ── Chat input ────────────────────────────────────────────────────────
chat_input = st.chat_input("Ask the PM Lead…")
if chat_input:
    user_input = chat_input

if user_input:
    # ── Input SHAP filter ─────────────────────────────────────────
    safe_input, input_blocked, input_score = filter_input(user_input, stage="Chatbot_Input")

    st.session_state.chat_history.append(("You", user_input, None))

    if input_blocked:
        bot_reply    = safe_input
        output_score = 1.0
    else:
        with st.spinner("🔍 Searching knowledge base…"):
            try:
                system_role = (
                    "You are the Project Manager Lead for the DevVerse AI development pod. "
                    "You own the full development process and answer questions about the "
                    "project's requirements, design, code, and tests — using only the "
                    "retrieved context from the knowledge base. Be specific and thorough."
                )
                raw_answer = rag_query(
                    question=safe_input,
                    system_role=system_role,
                    k=5,
                )
                bot_reply, output_blocked, output_score = filter_output(
                    raw_answer, stage="Chatbot_Output"
                )
            except Exception as exc:
                bot_reply    = f"⚠️ RAG error: {exc}"
                output_score = 0.0

    st.session_state.chat_history.append(("Bot", bot_reply, output_score))
    st.rerun()

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛠️ Knowledge Base")
    if st.button("🔄 Refresh KB from latest docs", use_container_width=True):
        with st.spinner("Rebuilding ChromaDB knowledge base…"):
            try:
                refresh_knowledge_base()
                st.success("✅ Knowledge base refreshed!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("**🛡️ Responsible AI**")
    st.caption("SHAP toxicity filters are active on every message.")

    if st.session_state.chat_history:
        st.markdown("---")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()