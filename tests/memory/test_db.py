import pytest
import os
import shutil
from asas_mcp.memory.db import ChromaManager

TEST_DB_PATH = "./data/chroma_db_test"

@pytest.fixture
def clean_db():
    # Reset Singleton
    ChromaManager._instance = None
    
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)
        
    yield
    
    ChromaManager._instance = None
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)

def test_chroma_manager_add_and_query(clean_db):
    try:
        manager = ChromaManager(persist_directory=TEST_DB_PATH)
    except Exception as e:
        pytest.fail(f"Could not initialize ChromaManager: {e}")
        
    doc_id = "test_1"
    content = "This is a test document about Python programming."
    metadata = {"source": "test_script", "category": "coding"}
    
    manager.add(content=content, metadata=metadata, doc_id=doc_id)
    
    # Query exact match or semantic match
    results = manager.query(text="Python programming", n_results=1)
    
    assert len(results) > 0
    assert results[0]['id'] == doc_id
    assert results[0]['content'] == content
    assert results[0]['metadata']['source'] == "test_script"

def test_chroma_manager_persistence():
    unique_path = TEST_DB_PATH + "_persistence"
    
    # Ensure fresh start
    ChromaManager._instance = None
    if os.path.exists(unique_path):
        shutil.rmtree(unique_path)
        
    try:
        # Create and add
        manager = ChromaManager(persist_directory=unique_path)
        manager.add(content="Persistent data", metadata={"type": "persistence_check"}, doc_id="p1")
        
        # Force reset of singleton to simulate restart
        ChromaManager._instance = None
        # We deliberately DO NOT delete the directory here, to test persistence
        
        # Re-open
        manager2 = ChromaManager(persist_directory=unique_path)
        results = manager2.query(text="Persistent data", n_results=1)
        
        assert len(results) > 0
        assert results[0]['id'] == "p1"
        
    finally:
        ChromaManager._instance = None
        if os.path.exists(unique_path):
            try:
                shutil.rmtree(unique_path)
            except OSError:
                pass
