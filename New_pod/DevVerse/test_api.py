"""Quick test to verify Groq API key works"""
from langchain_groq import ChatGroq
from pathlib import Path
import sys

# Load key
env_path = Path(__file__).parent / ".env"
GROQ_API_KEY = ""
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip().startswith('GROQ_API_KEY='):
                GROQ_API_KEY = line.strip().split('=', 1)[1]
                break

print(f"Key loaded: {GROQ_API_KEY[:15]}..." if GROQ_API_KEY else "NO KEY!")

if GROQ_API_KEY:
    try:
        llm = ChatGroq(model="llama-3.1-8b-instant", api_key=GROQ_API_KEY)
        response = llm.invoke("Say hi!")
        print("✅ API WORKS! Response:", response.content[:100])
    except Exception as e:
        print(f"❌ ERROR: {e}")

