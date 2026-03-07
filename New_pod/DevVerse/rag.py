"""
RAG (Retrieval-Augmented Generation) module for DevVerse.
Provides simple text-based context retrieval without heavy ML dependencies.
"""

# === Core Functions (No ML dependencies) ===

def generate_embedding(text: str):
    """
    Placeholder for embedding generation.
    Returns the original text for now - actual embedding would require sentence-transformers.
    """
    return text

def fetch_relevant_data(query: str, n_results: int = 5):
    """
    Simple text-based retrieval (no vector search).
    Returns empty results to use LLM directly without semantic search.
    """
    return [], []

def assemble_context(chunks, tags):
    """
    Format retrieved documents into a readable context block.
    """
    if not chunks:
        return "No relevant context found."
    
    context_parts = []
    for text, tag in zip(chunks, tags):
        project = tag.get('project', 'Unknown')
        section = tag.get('section', 'Unknown')
        context_parts.append(f"🔹 [{project} | {section}] — {text}")
    
    return "\n\n".join(context_parts)

def create_contextual_prompt(query: str, references: str) -> str:
    """
    Generate the final instruction prompt for the AI agent.
    """
    return f"""📘 Prompt Context

You are a domain expert.

User Input:
\"\"\"{query}\"\"\"

Reference Snippets:
{references}

Please use the above information to provide a detailed and refined output.
"""

def contextual_generation(user_input: str, n_results: int = 5) -> str:
    """
    Main RAG function - returns prompt without external context for now.
    """
    # Return prompt without external references (simpler approach)
    return create_contextual_prompt(user_input, "No reference documents available.")

def retrieve_and_generate(user_input: str, n_results: int = 5) -> str:
    """
    Main retrieval and generation function.
    Returns contextual prompt with retrieved information.
    """
    return contextual_generation(user_input, n_results)

def check_database_status() -> dict:
    """
    Check the status of the RAG database.
    """
    status = {
        "model_loaded": False,
        "database_connected": False,
        "document_count": 0,
        "langchain_available": False,
        "langchain_vectorstore": False,
        "note": "RAG running in simple mode without vector embeddings"
    }
    return status

