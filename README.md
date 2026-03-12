# 🚀 DevVerse — AI Virtual Development Pod

DevVerse is an **AI-powered software development pipeline** that automatically transforms a **Request for Proposal (RFP)** into a **fully generated web application, test suite, and corporate project report**.

The system orchestrates multiple **AI specialist agents** using **CrewAI**, enhanced with **Retrieval-Augmented Generation (RAG)**, **vector search**, **knowledge graphs**, and **artifact persistence**.

Instead of a single LLM generating everything, DevVerse simulates a **real development team workflow**.

---

# 🧠 Core Idea

A user uploads an **RFP PDF**.

DevVerse automatically executes a **5-agent development pipeline**:

```
RFP Upload
     ↓
Business Analyst
     ↓
System Architect
     ↓
Developer
     ↓
QA Tester
     ↓
Technical Report Writer
```

Each agent specializes in a different stage of software development.

---

# ⚙️ Architecture

```
Streamlit UI
      │
      ▼
CrewAI Master Agent
      │
      ▼
┌──────────────────────────────┐
│ Multi-Agent Pipeline         │
│                              │
│ 1. Business Analyst Agent    │
│ 2. Design Architect Agent    │
│ 3. Developer Agent           │
│ 4. QA Tester Agent           │
│ 5. Report Writer Agent       │
└──────────────────────────────┘
      │
      ▼
RAG Engine (LangChain)
      │
      ▼
ChromaDB Vector Store
      │
      ▼
Knowledge Sources
 • Project artifacts
 • Knowledge base
 • Memory graph
 • AWS S3 storage
```

---

# 🤖 AI Agents

## 1️⃣ Business Analyst Agent

Transforms extracted RFP requirements into **Agile user stories**.

Output:

* 5–8 user stories
* Acceptance criteria

---

## 2️⃣ Design Architect Agent

Converts user stories into **system architecture documentation**.

Output:

* System overview
* Component descriptions
* Mermaid architecture diagram

---

## 3️⃣ Developer Agent

Generates a **complete Flask web application**.

Output includes:

```
app.py
requirements.txt
templates/*.html
static/style.css
```

The generated project is immediately runnable.

---

## 4️⃣ QA Tester Agent

Creates a **full pytest test suite** covering:

* unit tests
* integration tests
* security edge cases
* performance tests

---

## 5️⃣ Report Writer Agent

Generates a **corporate software project report** including:

* executive summary
* architecture overview
* implementation details
* testing strategy
* future improvements

---

# 🧠 Retrieval-Augmented Generation (RAG)

All agents use **RAG instead of pure LLM responses**.

Sources include:

* Generated project artifacts
* Knowledge base documents
* Memory graph nodes
* AWS S3 stored outputs

This improves:

* consistency
* traceability
* contextual awareness

---

# 🗂 Knowledge Graph Memory

DevVerse maintains a **memory graph** linking system components.

Example relationship:

```
Architecture Node
      │
implemented_by
      ▼
Code Node
```

This enables agents to **reference previous development decisions**.

---

# ☁️ AWS S3 Artifact Storage

Generated artifacts are stored in S3 for persistence:

```
artifacts/
 ├── System_Design.txt
 ├── Implementation_Code.txt
 ├── Test_Cases.txt
 └── Project_Report.txt
```

These artifacts are later used as **RAG knowledge sources**.

---

# 🛡 Responsible AI Layer

DevVerse includes a **SHAP-based safety filter** that analyzes:

* uploaded RFP content
* agent inputs
* agent outputs

The dashboard reports:

* toxicity score
* safety coverage
* blocked content events

---

# 🖥 User Interface

The application uses **Streamlit** with a custom UI that includes:

* AI pipeline visualization
* agent progress tracking
* Mermaid architecture rendering
* downloadable project report
* SHAP safety dashboard

---

# 📦 Project Structure

```
DevVerse
│
├── agents/
│   ├── master_agent.py
│   ├── crew_businessAgent.py
│   ├── crew_designAgent.py
│   ├── crew_developerAgent.py
│   ├── crew_testerAgent.py
│   └── crew_reportAgent.py
│
├── core/
│   ├── rag_engine.py
│   ├── responsible_ai.py
│   ├── memory_graph.py
│   ├── artifacts.py
│   ├── extraction.py
│   └── s3_storage.py
│
├── frontend/
│   └── styleDevVerse.css
│
├── pages/
│   └── Generated_Project.py
│
├── knowledge_base/
├── knowledge_graph/
├── chroma_db/
├── outputs/
├── generated_project/
│
└── DevVerse.py
```

---

# 🚀 Installation

### 1️⃣ Clone repository

```
git clone https://github.com/yourusername/devverse.git
cd devverse
```

---

### 2️⃣ Install dependencies

```
pip install -r requirements.txt
```

---

### 3️⃣ Configure environment

Create `.env`

```
GROQ_API_KEY=your_key_here

AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=your_region
S3_BUCKET=your_bucket
```

---

### 4️⃣ Run the application

```
streamlit run DevVerse.py
```

---

# 🧪 Example Workflow

1️⃣ Upload an RFP PDF

2️⃣ Click **Initialize Dev Pod**

3️⃣ DevVerse automatically generates:

* User Stories
* System Architecture
* Full Flask Application
* Test Suite
* Corporate Report

4️⃣ Download the generated report or preview the generated project.

---

# 🔧 Technologies Used

Core AI stack:

* CrewAI
* LangChain
* ChromaDB
* Groq LLM

Infrastructure:

* AWS S3
* Python
* Streamlit

Additional tools:

* Mermaid diagrams
* SHAP explainability
* pytest

---

# 📊 Future Improvements

Planned enhancements:

* multi-user session isolation
* incremental vector updates
* CI/CD integration
* containerized project preview
* agent self-reflection loops

---

👨‍💻 Contributors

**Arka**

🚀 Robotics & AI Developer

📧 arkaghosh0115@gmail.com

Building autonomous systems, AI agents, and intelligent software pipelines.

**Soutisha**

📧 soutisham@gmail.com

AI & Software Development Contributor

---

# ⭐ If you like this project

Consider giving the repository a star.
