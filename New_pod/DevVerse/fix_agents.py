"""
Fix script to update agents.py for Ollama
"""
import os
import re

# Read the current agents.py
with open('agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# New content using Ollama
new_content = '''"""
Agent definitions for DevVerse
Uses CrewAI with Ollama (free local LLM)
"""
import os
from pathlib import Path
from crewai import Agent, LLM
from dotenv import load_dotenv

# Load .env file
project_root = Path(__file__).parent.absolute()
env_path = project_root / ".env"
load_dotenv(env_path)

print("✅ DevVerse starting with Ollama...")

# ============================================================
# LLM Setup - Using Ollama (free, local)
# ============================================================
try:
    # Use Ollama with llama3.2 model (free, no API key needed)
    ollama_llm = LLM(
        model="ollama/llama3.2",
        base_url="http://localhost:11434",
        temperature=0.3,
        verbose=True
    )
    print("✅ Ollama LLM initialized successfully")
except Exception as e:
    print(f"⚠️  Error initializing Ollama LLM: {e}")
    ollama_llm = None

# ============================================================
# Agent Definitions - Memory disabled for local LLM
# ============================================================

business_analyst = Agent(
    role="Business Analyst",
    goal=(
        "Analyze requirements and generate user stories in format: "
        "'As a [role], I want to [action], so that [benefit]'. "
        "Do NOT include system design or technical details."
    ),
    backstory=(
        "A skilled business analyst with experience in Agile methodologies. "
        "Your expertise is translating requirements into actionable user stories."
    ),
    verbose=True,
    memory=False,
    tools=[],
    llm=ollama_llm,
    allow_delegation=False
)

design_agent = Agent(
    role="Software Designer",
    goal=(
        "Create software architecture and design based on user stories. "
        "Focus on components, data flow, database, and architecture."
    ),
    backstory=(
        "A software architect specializing in scalable, efficient systems."
    ),
    verbose=True,
    memory=False,
    tools=[],
    llm=ollama_llm,
    allow_delegation=False
)

developer_agent = Agent(
    role="Software Developer",
    goal=(
        "Generate production-ready code. "
        "Ensure modularity, scalability, and best practices."
    ),
    backstory=(
        "A senior software engineer that generates clean, well-structured code."
    ),
    verbose=True,
    memory=False,
    tools=[],
    llm=ollama_llm,
    allow_delegation=False
)

tester_agent = Agent(
    role="Quality Assurance Tester",
    goal=(
        "Generate comprehensive test cases in executable code format. "
        "Include unit tests, integration tests, and edge cases."
    ),
    backstory=(
        "A meticulous QA professional creating thorough test plans."
    ),
    verbose=True,
    memory=False,
    tools=[],
    llm=ollama_llm,
    allow_delegation=False
)

print("✅ All agents created successfully")
'''

# Write the new content
with open('agents.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ agents.py updated to use Ollama!")
print("")
print("Next steps:")
print("1. Run: streamlit run DevVerse.py")

