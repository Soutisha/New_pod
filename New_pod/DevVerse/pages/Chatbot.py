"""
DevVerse — Chatbot Page
Premium AI chat interface for project status queries.
"""

import streamlit as st
import os
from pathlib import Path

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title="DevVerse Chat", page_icon="💬", layout="wide")

# ── CSS ────────────────────────────────────────────────────
css_path = Path(__file__).parent.parent / "styleDevVerse.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ── Gemini API setup ────────────────────────────────────────
genai = None
USE_NEW = None
try:
    import google.genai as genai
    USE_NEW = True
except ImportError:
    try:
        import google.generativeai as genai   # type: ignore
        USE_NEW = False
    except ImportError:
        pass

from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "")
if genai and api_key:
    genai.configure(api_key=api_key)

# ── Project context ─────────────────────────────────────────
from project_status import project_status   # type: ignore

base_dir = Path(__file__).parent.parent
req_file = base_dir / "extracted_reqmts.txt"
stories_file = base_dir / "User_Stories.txt"
design_file = base_dir / "System_Design.txt"
code_file = base_dir / "Implementation_Code.txt"
test_file = base_dir / "Test_Cases.txt"

def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else "(Not generated yet)"

reqmts_text = _read_file(req_file)
stories_text = _read_file(stories_file)
design_text = _read_file(design_file)
code_text = _read_file(code_file)
test_text = _read_file(test_file)

def _format_status(status: dict) -> str:
    return "\n".join([
        f"- Requirements Extracted: {status.get('requirements_extracted', 0)}",
        f"- User Stories: {status.get('user_stories_generated', 0)}",
        f"- Design Document: {'Yes' if status.get('design_document_generated') else 'No'}",
        f"- Code Generated: {'Yes' if status.get('code_generated') else 'No'}",
        f"- Test Cases: {'Yes' if status.get('test_cases_generated') else 'No'}",
    ])

# ── Session state ────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Hero ─────────────────────────────────────────────────────
st.markdown("""
<div class="dv-hero" style="padding:2.5rem 1rem 1.5rem;">
    <div class="dv-badge">👔 Project Manager Lead</div>
    <h1 class="dv-headline" style="font-size:2.1rem !important;">
        Consult the <span class="dv-gradient-text">PM Lead</span>
    </h1>
    <p class="dv-subtitle" style="font-size:0.95rem !important;">
        Chat with the AI Project Manager to review artifact quality, check status, or validate architecture.
    </p>
</div>
<hr class="dv-divider"/>
""", unsafe_allow_html=True)

# ── Display chat history ────────────────────────────────────
if not st.session_state.chat_history:
    st.markdown("""
    <div style="text-align:center; padding:3rem 0; color:#94A3B8;">
        <div style="font-size:3rem; margin-bottom:0.75rem;">👔</div>
        <p style="font-size:0.93rem; color:#64748B;">
            I am the Project Manager Lead. Ask me to quickly review the generated code, evaluate the user stories, or check on progress.
        </p>
    </div>
    """, unsafe_allow_html=True)

for speaker, msg in st.session_state.chat_history:
    if speaker == "You":
        st.markdown(
            f'<div class="dv-chat-user"><div class="dv-bubble">{msg}</div></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="dv-chat-bot"><div class="dv-bubble">{msg}</div></div>',
            unsafe_allow_html=True
        )

# ── Input ────────────────────────────────────────────────────
user_input = st.chat_input("Ask the Project Manager…")

if user_input:
    st.session_state.chat_history.append(("You", user_input))

    prompt = (
        "You are the Project Manager Lead for this DevVerse AI development pod.\n"
        "You are the overall owner of the development process. Your job is to deeply understand, "
        "analyze, and answer any questions about the project's generated artifacts (requirements, design, code, tests).\n\n"
        "Here is the current state of the project artifacts:\n\n"
        f"--- 1. RAW REQUIREMENTS ---\n{reqmts_text[:500]}...\n\n"
        f"--- 2. USER STORIES ---\n{stories_text[:1000]}...\n\n"
        f"--- 3. SYSTEM DESIGN ---\n{design_text[:1000]}...\n\n"
        f"--- 4. IMPLEMENTATION CODE ---\n{code_text[:2000]}...\n\n"
        f"--- 5. TEST CASES ---\n{test_text[:1000]}...\n\n"
        f"--- OVERALL STATUS ---\n{_format_status(project_status)}\n\n"
        f'User question: "{user_input}"\n\n'
        "Answer confidently, thoroughly, and highly specifically based on the context above. If asked about the code, mention specific routes or models. If asked about user stories, reference them. Act as the ultimate project owner."
    )

    with st.spinner("Thinking..."):
        import requests
        import os
        from langchain_groq import ChatGroq

        OLLAMA_API = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.1",
            "prompt": prompt,
            "stream": False
        }

        bot_response = ""
        try:
            # First, try to query local Ollama
            response = requests.post(OLLAMA_API, json=payload, timeout=5)
            response.raise_for_status()
            bot_response = response.json().get("response", "No response generated.")
            bot_response = "*(Analyzed via Local Ollama)*\n\n" + bot_response

        except requests.exceptions.ConnectionError:
            # Fallback to Groq API if Ollama is offline
            try:
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key or api_key.startswith("your_"):
                    bot_response = (
                        "⚠️ **Could not connect to local Ollama, and no Cloud Fallback found.**\n\n"
                        "Please either run `ollama run llama3.1` in your terminal, OR add a valid `GROQ_API_KEY` to your `.env` file."
                    )
                else:
                    llm = ChatGroq(
                        model="llama-3.1-8b-instant",
                        temperature=0.3,
                        api_key=api_key
                    )
                    cloud_response = llm.invoke(prompt)
                    res_content = cloud_response.content if hasattr(cloud_response, "content") else str(cloud_response)
                    bot_response = "*(Analyzed via Cloud Fallback)*\n\n" + res_content
            except Exception as e:
                bot_response = f"⚠️ Cloud Fallback failed: {e}"

        except Exception as exc:
            err_msg = str(exc).lower()
            if "not found" in err_msg:
                bot_response = "⚠️ **Model Not Found:** Please run `ollama run llama3.1` to download the local model."
            else:
                bot_response = f"Sorry, an unexpected error occurred: {exc}"

    st.session_state.chat_history.append(("Bot", bot_response))
    st.rerun()

# ── Clear button ────────────────────────────────────────────
if st.session_state.chat_history:
    if st.button("🗑️  Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
