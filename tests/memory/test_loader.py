import pytest
import os
from unittest.mock import MagicMock, call
from asas_mcp.memory.loader import load_initial_knowledge

def test_load_initial_knowledge():
    # Mock ChromaManager
    mock_db = MagicMock()
    mock_db.add = MagicMock()
    # Configure collection.get to return empty result so loader thinks docs are new
    mock_db.collection.get.return_value = {'ids': []}
    
    # Create temp knowledge files
    test_kb_dir = "tests/memory/temp_kb"
    os.makedirs(test_kb_dir, exist_ok=True)
    
    try:
        file1 = os.path.join(test_kb_dir, "test1.md")
        with open(file1, "w") as f:
            f.write("# Test 1\nContent of test 1")
            
        file2 = os.path.join(test_kb_dir, "test2.md")
        with open(file2, "w") as f:
            f.write("# Test 2\nContent of test 2")
            
        # Call loader with custom path override if possible, or we mock scan function.
        # Since loader.py is not implemented, we assume we can pass the dir or mock os.walk.
        # Let's assume load_initial_knowledge takes a directory argument for testing or we mock glob/walk.
        # For this test, let's try to mock the directory path scan if the function hardcodes it, 
        # or better, start implementing loader to accept a path.
        # But per TDD, we write test first. We'll pass the path to the function.
        
        load_initial_knowledge(mock_db, knowledge_dir=test_kb_dir)
        
        # Verify add callss
        assert mock_db.add.call_count == 2
        
        # Verify content
        calls = mock_db.add.call_args_list
        contents = [c.kwargs['content'] for c in calls]
        assert "# Test 1\nContent of test 1" in contents
        assert "# Test 2\nContent of test 2" in contents
        
    finally:
        import shutil
        if os.path.exists(test_kb_dir):
            shutil.rmtree(test_kb_dir)
