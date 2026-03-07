# DevVerse Implementation Plan

## Tasks Completed:

### ✅ 1. Created requirements.txt with all dependencies
- Created requirements.txt with all required packages

### ✅ 2. Fixed agents.py with proper LangChain integration
- Removed unused import issue
- Added proper LangChain integration
- Added .env loading and API key validation

### ✅ 3. Set up .env file for API key configuration
- Created .env.example template

### ✅ 4. Enhanced UI/CSS styling
- Modernized styleDevVerse.css with animations and better design

### ✅ 5. Integrated LangChain properly
- Updated rag.py with LangChain components
- Added prompt templates for each agent

### ✅ 6. Updated all crew agents
- Updated crew_businessAgent.py, crew_designAgent.py, crew_developerAgent.py, crew_testerAgent.py

### ✅ 7. Fixed DevVerse.py issues
- Moved imports to top of file
- Added proper session state handling
- Save extracted requirements to file (extracted_reqmts.txt)
- Added comprehensive error handling
- Added sidebar with project status

### ✅ 8. Fixed SETUP.md corruption
- Completed the incomplete P Model section (now includes spacy download)
- Fixed broken formatting and typos
- Added complete troubleshooting section

### ✅ 9. Fixed database.py indexing on import
- Wrapped indexing in functions to prevent auto-execution on import
- Added functions: run_indexing(), get_document_count(), clear_database()
- Added proper documentation

### ✅ 10. Improved rag.py
- Now imports from database.py to avoid redundant ChromaDB setup
- Added better error handling
- Added check_database_status() function

## Status: ALL FIXES COMPLETED ✅

## Note on API Keys:
- Free API keys can be obtained from: https://aistudio.google.com/app/apikey
- Copy .env.example to .env and add your key there

## Project Information

- Pitch Video link : https://drive.google.com/file/d/1T6nSzjjwp1AXK-OlgaaHHsEqrQY-cINm/view?usp=sharing  
- Demo Video link : https://drive.google.com/file/d/1sg43tgS1IGhGwoqCU2AFYUOTfeLGhXda/view?usp=sharing  

- **DevVerse: AI-Powered Virtual Development Pod**  
  "Bringing intelligence to requirements — and speed to solutions."
  
  **DevVerse** is an AI-powered assistant that automates the transformation of plain English RFPs (Request for Proposals) into structured, implementation-ready development assets — all through an intelligent pipeline of role-based autonomous agents and Retrieval-Augmented Generation (RAG).


- What is DevVerse?  
  DevVerse mimics a real-world project team using intelligent agents like:  
  🔹Business Analyst Agent – Extracts user stories  
  🔹Design Agent – Generates UI/UX components & architecture  
  🔹Developer Agent – Produces backend code & database structure  
  🔹Tester Agent – Builds test cases based on user stories and code  
  These agents collaborate to convert an RFP into project artifacts — automatically, intelligently, and instantly.  

- Problem We Solve:-  
  RFPs are often written in unstructured, plain English.  
  Converting them into usable formats (user stories, UI layouts, test cases, etc.) takes time, manual effort, and domain expertise.  
  Scaling this process across domains like finance, e-commerce, or healthcare becomes inefficient.  

- Our Solution:-  
  DevVerse automates this workflow using a smart, modular pipeline:  
  🔹Embedding : Creation	RFP is encoded into semantic vectors  
  🔹Vector Search (ChromaDB) : Retrieves domain-relevant templates  
  🔹Agent Collaboration : Agents extract and generate structured outputs  
  🔹LLM Response : Final context goes to LLM (Gemini-1.5-flash) to generate artifacts  

- Tech Stack:-  
  Frontend : Streamlit  
  Backend : Python, CrewAI  
  LLM : API	Gemini-1.5-flash  
  Vector DB : ChromaDB  
  Embeddings : Sentence Transformers  
  Agent Framework : CrewAI, Prompt Chaining  

- Agents in Action:-  
  Each agent plays a defined role in the pipeline:  
  🔹Business Analyst Agent : Extracts domain keywords and requirements; Generates user stories based on RFP understanding  
  🔹Design Agent : Selects UI layouts from template pool; Builds hierarchy and architecture diagrams  
  🔹Developer Agent : Suggests database schema and backend module layout (Extendable to generate code skeletons)  
  🔹Tester Agent : Derives test cases from user stories and functions; Suggests automation test structure  

- System Architecture Overview:-  
  [User Input: RFP]  
        ↓  
  [Vectorization: Sentence Embedding]  
        ↓  
  [ChromaDB Search]  
        ↓  
  [Relevant Format Retrieval]  
        ↓  
  [Agent Collaboration]  
        ↓  
  [Final Prompt Assembly]  
        ↓  
  [LLM Generation]  
        ↓  
  [User Stories | Design | Code | Test Cases]  

- Impact:-  
  🔹80%+ reduction in manual effort  
  🔹Rapid transition from RFP to assets  
  🔹Standardized documentation across projects  
  🔹Domain-agnostic: works for fintech, healthcare, e-commerce, etc.  

- Future Scope:-  
  Add agents like UI/UX Designer, Scrum Master, Security Expert  
  Generate backend code skeletons and API specs  
  Integrate with tools like JIRA, GitHub Projects, Figma  

- Team:-  
  Priya Kumari  
  Tideesha Saha  
  Prakriti Mukhopadhyay  
  Debarati Das  

