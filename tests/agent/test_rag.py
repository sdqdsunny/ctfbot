import pytest
import os
import shutil
from asas_agent.rag.retriever import SemanticRetriever

@pytest.fixture
def temp_chroma():
    path = "data/chroma_test"
    if os.path.exists(path):
        shutil.rmtree(path)
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)

def test_retriever_sanity(temp_chroma):
    retriever = SemanticRetriever(persist_directory=temp_chroma)
    
    # Add data
    metadata = {"solution": "Use sqlmap --os-shell"}
    retriever.add_knowledge(
        "SQL injection with file write", 
        "Use sqlmap --os-shell", 
        metadata
    )
    
    # Query
    results = retriever.retrieve("How to exploit SQLi to get shell?")
    
    assert len(results) > 0
    assert "SQL injection with file write" in results
