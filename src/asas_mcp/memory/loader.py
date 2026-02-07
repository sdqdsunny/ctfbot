import os
import glob
import hashlib
from .db import ChromaManager

def get_content_hash(content: str) -> str:
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_initial_knowledge(db_manager: ChromaManager, knowledge_dir: str = "data/knowledge_base"):
    if not os.path.exists(knowledge_dir):
        print(f"Knowledge directory not found: {knowledge_dir}")
        return
        
    md_files = glob.glob(os.path.join(knowledge_dir, "*.md"))
    
    count = 0
    for file_path in md_files:
        try:
            filename = os.path.basename(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            doc_id = get_content_hash(content)
            
            # Check exist via collection.get
            try:
                existing = db_manager.collection.get(ids=[doc_id])
                if existing and existing['ids']:
                     # Already exists
                     continue
            except Exception:
                pass

            metadata = {
                "source": filename,
                "type": "initial_knowledge"
            }
            
            db_manager.add(content=content, metadata=metadata, doc_id=doc_id)
            count += 1
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    print(f"Loaded {count} new knowledge documents.")
