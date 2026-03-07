"""
Database module for DevVerse.
Simple ChromaDB wrapper for document storage.
"""
import os
import uuid
from typing import List

# === ChromaDB Client Setup ===
import chromadb
db = chromadb.PersistentClient(path="./chroma_db")
repo = db.get_or_create_collection("project_docs")

print(f"✅ Connected to ChromaDB with {repo.count()} documents")

# === Text Chunking Utility ===
def split_into_chunks(data: str, size: int = 500, step: int = 450) -> List[str]:
    """Split text into overlapping chunks."""
    segments = []
    for i in range(0, len(data), step):
        piece = data[i:i + size]
        if piece.strip():
            segments.append(piece)
    return segments

# === File Ingestion & Embedding Pipeline ===
def ingest_directory(project_id: str, directory_path: str) -> int:
    """Ingest all .txt files from a directory into ChromaDB."""
    # Lazy import sentence_transformers only when needed
    try:
        from sentence_transformers import SentenceTransformer
        vectorizer = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        print(f"⚠️  Could not load SentenceTransformer: {e}")
        return 0
    
    if not os.path.exists(directory_path):
        print(f"⚠️  Directory not found: {directory_path}")
        return 0
    
    indexed_count = 0
    
    for file in os.listdir(directory_path):
        if file.endswith(".txt"):
            category = file.replace(".txt", "")
            full_path = os.path.join(directory_path, file)

            try:
                with open(full_path, 'r', encoding='utf-8') as handle:
                    content = handle.read()
                    blocks = split_into_chunks(content)

                    for index, block in enumerate(blocks):
                        vec = vectorizer.encode(block).tolist()
                        doc_id = str(uuid.uuid4())

                        repo.add(
                            documents=[block],
                            embeddings=[vec],
                            metadatas=[{
                                "project": project_id,
                                "section": category,
                                "filename": file,
                                "block_index": index
                            }],
                            ids=[doc_id]
                        )
                        indexed_count += 1
                        
                print(f"📄 {file} from '{project_id}' indexed ({len(blocks)} blocks)")
                
            except Exception as e:
                print(f"⚠️  Error indexing {file}: {str(e)}")
    
    return indexed_count

def run_indexing() -> None:
    """Run the indexing process for sample projects."""
    print("🔄 Starting database indexing...")
    
    if repo.count() > 0:
        print(f"📊 Database already contains {repo.count()} documents")
        response = input("Re-index? (y/n): ")
        if response.lower() != 'y':
            print("✅ Indexing cancelled")
            return
    
    total_indexed = 0
    total_indexed += ingest_directory("social_media_platform", "./social_media_clone")
    total_indexed += ingest_directory("shop_system", "./ecommerce")
    
    print("✅ Indexing complete.")
    print(f"📊 Total documents in DB: {repo.count()}")

def get_document_count() -> int:
    """Get the total number of documents in the database."""
    return repo.count()

def clear_database() -> None:
    """Clear all documents from the database."""
    global repo
    db.delete_collection("project_docs")
    repo = db.get_or_create_collection("project_docs")
    print("✅ Database cleared")

if __name__ == "__main__":
    run_indexing()
