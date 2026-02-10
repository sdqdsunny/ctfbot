from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions

class SemanticRetriever:
    """Simple RAG retriever using ChromaDB."""
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Use default embedding function strictly for demo purposes
        # In production, use SentenceTransformer or OpenAI embeddings
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="ctf_writeups", 
            embedding_function=self.ef
        )
        
    def add_knowledge(self, problem_text: str, solution_text: str, metadata: Dict[str, Any]):
        """Index a solved problem."""
        import uuid
        doc_id = str(uuid.uuid4())
        self.collection.add(
            documents=[problem_text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        # Also store the full solution text separately if needed, or in metadata
        # For simplicity, we assume solution_text is part of the document context or metadata
        
    def retrieve(self, query: str, n_results: int = 3) -> List[str]:
        """Search for similar problems."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Flatten results
        documents = results.get("documents", [[]])[0]
        return documents

# Singleton instance
retriever = SemanticRetriever()
