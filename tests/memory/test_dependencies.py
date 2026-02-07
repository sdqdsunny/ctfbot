import pytest

def test_imports():
    """Verify that critical dependencies can be imported."""
    try:
        import chromadb
        from chromadb.config import Settings
        assert chromadb is not None
    except ImportError as e:
        pytest.fail(f"Failed to import chromadb: {e}")

    # sentence-transformers is optional if we use onnx or default
    # try:
    #     import sentence_transformers
    #     assert sentence_transformers is not None
    # except ImportError:
    #     pass

def test_chroma_in_memory():
    """Verify that we can initialize a ChromaDB client in memory."""
    import chromadb
    client = chromadb.Client() # Ephemeral client
    assert client is not None
    
    collection = client.create_collection(name="test_collection")
    assert collection.name == "test_collection"
    
    collection.add(
        documents=["This is a test document"],
        metadatas=[{"source": "test"}],
        ids=["id1"]
    )
    
    results = collection.query(
        query_texts=["test"],
        n_results=1
    )
    
    assert len(results["ids"][0]) == 1
    assert results["ids"][0][0] == "id1"
