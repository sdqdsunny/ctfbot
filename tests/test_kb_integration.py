"""知识库三层架构集成测试"""
import pytest
import os

KB_DIR = "data/knowledge_base"
WP_DIR = "data/writeups"
SCRIPTS_DIR = "data/scripts/ctf_tools"

# 第 1 层（19 篇核心知识）随仓库交付，任何检出都该在，所以下面不设跳过条件。
#
# 第 2、3 层（WP 全文 31MB + 脚本 4.4MB）是第三方汇编，为体积与授权考虑不随仓库分发，
# 由 scripts/fetch_corpus.py 按需拉取（见 README「拉取知识库语料」）。
# 也就是说"语料在不在"是**环境前置条件**，不是产品不变量：没拉取时应当 skip，
# 而不是把干净检出判成失败——否则 CI 一上来就是一片红，真正的回归反而被淹没。
_HAS_CORPUS = os.path.exists(os.path.join(WP_DIR, "articles")) and os.path.exists(SCRIPTS_DIR)
_CORPUS_REASON = (
    "语料未拉取（31MB 第三方汇编，不随仓库分发），"
    "先运行: python scripts/fetch_corpus.py"
)
needs_corpus = pytest.mark.skipif(not _HAS_CORPUS, reason=_CORPUS_REASON)


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
    @needs_corpus
    def test_symlink_articles_exists(self):
        path = os.path.join(WP_DIR, "articles")
        assert os.path.exists(path), "WP articles symlink missing"

    @needs_corpus
    def test_symlink_ctfshow_exists(self):
        path = os.path.join(WP_DIR, "ctfshow")
        assert os.path.exists(path), "WP ctfshow symlink missing"

    @needs_corpus
    def test_articles_have_content(self):
        articles_dir = os.path.join(WP_DIR, "articles")
        files = [f for f in os.listdir(articles_dir) if f.endswith('.md')]
        assert len(files) >= 100, f"Expected >=100 WP articles, got {len(files)}"

    @pytest.mark.skipif(
        not os.path.exists("data/writeups/wp_index.db"),
        reason="WP 索引未构建（该索引由语料生成），先运行: python scripts/fetch_corpus.py"
    )
    def test_wp_search_works(self):
        from src.asas_mcp.memory.wp_search import WPSearchEngine
        engine = WPSearchEngine("data/writeups/wp_index.db")
        results = engine.search("SQL注入")
        assert len(results) > 0, "WP search returned no results for 'SQL注入'"
        engine.close()

    @pytest.mark.skipif(
        not os.path.exists("data/writeups/wp_index.db"),
        reason="WP 索引未构建，先运行: python scripts/fetch_corpus.py"
    )
    def test_wp_filter_by_category(self):
        from src.asas_mcp.memory.wp_search import WPSearchEngine
        engine = WPSearchEngine("data/writeups/wp_index.db")
        results = engine.search("", category="web", limit=5)
        assert len(results) > 0, "No web category WPs found"
        assert all(r["category"] == "web" for r in results)
        engine.close()


class TestLayer3Scripts:
    @needs_corpus
    def test_scripts_symlink_accessible(self):
        assert os.path.exists(SCRIPTS_DIR), f"Scripts symlink missing: {SCRIPTS_DIR}"

    @needs_corpus
    def test_script_registry_finds_tools(self):
        from src.asas_mcp.memory.script_registry import ScriptRegistry
        registry = ScriptRegistry(SCRIPTS_DIR)
        scripts = registry.list_scripts()
        assert len(scripts) >= 10, f"Expected >=10 script dirs, got {len(scripts)}"

    @needs_corpus
    def test_script_categories_work(self):
        from src.asas_mcp.memory.script_registry import ScriptRegistry
        registry = ScriptRegistry(SCRIPTS_DIR)
        crypto = registry.list_scripts(category="crypto")
        assert len(crypto) >= 1, "No crypto scripts found"

    @needs_corpus
    def test_find_rsa_script(self):
        from src.asas_mcp.memory.script_registry import ScriptRegistry
        registry = ScriptRegistry(SCRIPTS_DIR)
        result = registry.find_script("RSA")
        assert result is not None, "RSA script not found"
        assert result["path"].endswith(".py")
