import chromadb
from chromadb.config import Settings
import os

class ChromaManager:
    _instance = None
    
    def __new__(cls, persist_directory: str = "./data/chroma_db"):
        if cls._instance is None:
            cls._instance = super(ChromaManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        if self._initialized:
            return
            
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize PersistentClient
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(name="asas_knowledge_base")
        
        self._initialized = True
    
    def add(self, content: str, metadata: dict, doc_id: str):
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
    def query(self, text: str, n_results: int = 5, where: dict = None):
        if where:
             results = self.collection.query(
                query_texts=[text],
                n_results=n_results,
                where=where
            )
        else:
            results = self.collection.query(
                query_texts=[text],
                n_results=n_results
            )
        
        formatted_results = []
        if results['ids']:
            ids = results['ids'][0]
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            dists = results['distances'][0] if 'distances' in results and results['distances'] else [None]*len(ids)
            
            for i in range(len(ids)):
                formatted_results.append({
                    'id': ids[i],
                    'content': docs[i],
                    'metadata': metas[i],
                    'distance': dists[i]
                })
                
        return formatted_results
