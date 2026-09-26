"""知识库三层架构集成测试"""
import pytest
import os

KB_DIR = "data/knowledge_base"
WP_DIR = "data/writeups"
SCRIPTS_DIR = "data/scripts/ctf_tools"


class TestLayer1KnowledgeBase:
    def test_knowledge_files_exist(self):
        assert os.path.exists(KB_DIR), f"知识库目录不存在: {KB_DIR}"
        md_files = [f for f in os.listdir(KB_DIR) if f.endswith('.md')]
        assert len(md_files) >= 12, f"Expected >=12 knowledge files, got {len(md_files)}"

    def test_key_topics_covered(self):
        files = os.listdir(KB_DIR)
        required = [
            "web_sqli", "web_rce", "web_upload", "web_lfi", "web_ssrf",
            "web_ssti", "web_jwt", "web_deserialize", "payload_cheatsheet"
        ]
        for topic in required:
            assert any(topic in f for f in files), f"Missing topic: {topic}"

    def test_files_not_empty(self):
        for f in os.listdir(KB_DIR):
            if f.endswith('.md'):
                path = os.path.join(KB_DIR, f)
                size = os.path.getsize(path)
                assert size > 100, f"File too small (placeholder?): {f} ({size} bytes)"


class TestLayer2WriteUps:
    def test_symlink_articles_exists(self):
        path = os.path.join(WP_DIR, "articles")
        assert os.path.exists(path), "WP articles symlink missing"

    def test_symlink_ctfshow_exists(self):
        path = os.path.join(WP_DIR, "ctfshow")
        assert os.path.exists(path), "WP ctfshow symlink missing"

    def test_articles_have_content(self):
        articles_dir = os.path.join(WP_DIR, "articles")
        if os.path.exists(articles_dir):
            files = [f for f in os.listdir(articles_dir) if f.endswith('.md')]
            assert len(files) >= 100, f"Expected >=100 WP articles, got {len(files)}"

    @pytest.mark.skipif(
        not os.path.exists("data/writeups/wp_index.db"),
        reason="WP index not built yet (run: python scripts/build_kb.py --layer 2)"
    )
    def test_wp_search_works(self):
        from src.asas_mcp.memory.wp_search import WPSearchEngine
        engine = WPSearchEngine("data/writeups/wp_index.db")
        results = engine.search("SQL注入")
        assert len(results) > 0, "WP search returned no results for 'SQL注入'"
        engine.close()

    @pytest.mark.skipif(
        not os.path.exists("data/writeups/wp_index.db"),
        reason="WP index not built yet"
    )
    def test_wp_filter_by_category(self):
        from src.asas_mcp.memory.wp_search import WPSearchEngine
        engine = WPSearchEngine("data/writeups/wp_index.db")
        results = engine.search("", category="web", limit=5)
        assert len(results) > 0, "No web category WPs found"
        assert all(r["category"] == "web" for r in results)
        engine.close()


class TestLayer3Scripts:
    def test_scripts_symlink_accessible(self):
        assert os.path.exists(SCRIPTS_DIR), f"Scripts symlink missing: {SCRIPTS_DIR}"

    def test_script_registry_finds_tools(self):
        from src.asas_mcp.memory.script_registry import ScriptRegistry
        registry = ScriptRegistry(SCRIPTS_DIR)
        scripts = registry.list_scripts()
        assert len(scripts) >= 10, f"Expected >=10 script dirs, got {len(scripts)}"

    def test_script_categories_work(self):
        from src.asas_mcp.memory.script_registry import ScriptRegistry
        registry = ScriptRegistry(SCRIPTS_DIR)
        crypto = registry.list_scripts(category="crypto")
        assert len(crypto) >= 1, "No crypto scripts found"

    def test_find_rsa_script(self):
        from src.asas_mcp.memory.script_registry import ScriptRegistry
        registry = ScriptRegistry(SCRIPTS_DIR)
        result = registry.find_script("RSA")
        assert result is not None, "RSA script not found"
        assert result["path"].endswith(".py")
