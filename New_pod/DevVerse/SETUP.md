# DevVerse Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Required NLP Models
```bash
python -m spacy download en_core_web_sm
```

### 3. Configure API Key
1. Copy the `.env.example` file to `.env`:
   - On Windows: `copy .env.example .env`
   - On Mac/Linux: `cp .env.example .env`

2. Get your free API key from: https://aistudio.google.com/app/apikey

3. Open `.env` in a text editor and add your API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### 4. Run the Application
```bash
python -m streamlit run DevVerse.py
```

## 📋 Tech Stack Summary

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit, streamlit-chat |
| Backend | Python |
| LLM | Gemini-1.5-flash (via LangChain + CrewAI) |
| Vector DB | ChromaDB |
| Embeddings | Sentence Transformers |
| Agent Framework | CrewAI, LangChain |
| NLP | spaCy, scikit-learn |
| PDF | PyPDF2 |

## 🔑 API Key Information

- **Free API Key**: Available at https://aistudio.google.com/app/apikey
- **Note**: Free tier has rate limits. For production use, consider upgrading to a paid plan

## 📁 Project Structure

```
DevVerse/
├── DevVerse.py            # Main Streamlit application
├── agents.py              # CrewAI agent definitions
├── task.py                # Task definitions for agents
├── rag.py                 # RAG (Retrieval-Augmented Generation) logic
├── database.py            # ChromaDB setup and indexing
├── Extraction.py          # PDF text extraction and requirement analysis
├── project_status.py      # Project status tracking
├── styleDevVerse.css      # Custom CSS styling
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your API key (create from .env.example)
├── SETUP.md               # This file
└── README.md             # Project documentation
```

## ⚠️ Important Notes

1. Always keep your API key private - never commit `.env` to version control
2. The `.env` file is already in `.gitignore` (if configured)
3. If you see API key warnings, check that the key is properly set in `.env`

## Troubleshooting

### If streamlit not found:
Use: `python -m streamlit run DevVerse.py`

### If pip install fails:
Try: `pip install --user -r requirements.txt`

### If spacy model not found:
```bash
python -m spacy download en_core_web_sm
```

### If typer error occurs:
```bash
pip install typer
```

### If ChromaDB errors occur:
Make sure the `chroma_db` directory exists and has proper permissions

### If API key errors occur:
1. Verify your `.env` file exists in the project root
2. Check that `GEMINI_API_KEY` is properly set in the `.env` file
3. Ensure there are no extra spaces or quotes around the API key

## 🔧 Optional: Manual Database Indexing

If you need to re-index the sample projects, run:
```bash
python database.py
```

## 📖 Usage Flow

1. **Upload RFP**: Upload a PDF containing your Request for Proposal
2. **Initialize Project**: Click the button to start the analysis
3. **Business Analysis**: View the generated user stories
4. **Design**: Review the system architecture and design
5. **Development**: Get production-ready code
6. **Testing**: Receive comprehensive test cases

