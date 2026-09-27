"""Tests for WP full-text search engine."""
import pytest
from src.asas_mcp.memory.wp_search import WPSearchEngine


@pytest.fixture
def engine(tmp_path):
    db_path = str(tmp_path / "test_wp.db")
    return WPSearchEngine(db_path)


@pytest.fixture
def populated_engine(engine, tmp_path):
    """创建带测试数据的引擎"""
    wp_dir = tmp_path / "articles"
    wp_dir.mkdir()

    (wp_dir / "强网杯_SQL注入.full.md").write_text("""---
title: 强网杯 SQL注入 WriteUp
contest: 强网杯 2024
year: 2024
vuln_type:
- web_sqli
tags:
- SQL注入
- 联合注入
---

# 强网杯 SQL注入

## 解题思路

使用联合注入获取flag，通过 union select 获取数据库信息。
""", encoding="utf-8")

    (wp_dir / "HITCON_Crypto.full.md").write_text("""---
title: HITCON Crypto Challenge
contest: HITCON 2023
year: 2023
vuln_type:
- crypto_rsa
tags:
- RSA
---

# HITCON Crypto

## 解题思路

RSA共模攻击，利用扩展欧几里得算法求解。
""", encoding="utf-8")

    (wp_dir / "西湖论剑_Web.full.md").write_text("""---
title: 西湖论剑 Web WriteUp
contest: 西湖论剑 2024
year: 2024
vuln_type:
- web_ssti
tags:
- SSTI
- Jinja2
---

# 西湖论剑 Web

## SSTI 题目

Jinja2模板注入，通过 __mro__ 获取基类执行命令。
""", encoding="utf-8")

    engine.build_index(str(wp_dir))
    return engine


class TestParseFrontmatter:
    def test_parse_yaml_frontmatter(self, engine):
        meta = engine._parse_frontmatter("""---
title: Test WP
contest: CTF 2024
year: 2024
vuln_type:
- web_sqli
tags:
- SQL注入
---
content here
""")
        assert meta["title"] == "Test WP"
        assert meta["contest"] == "CTF 2024"
        assert meta["year"] == 2024

    def test_parse_no_frontmatter(self, engine):
        meta = engine._parse_frontmatter("# Just a title\n\nSome content.")
        assert meta == {}

    def test_parse_vuln_type_list(self, engine):
        meta = engine._parse_frontmatter("""---
title: Test
vuln_type:
- web_sqli
- web_rce
---
content
""")
        assert "web_sqli" in meta.get("vuln_type", [])
        assert "web_rce" in meta.get("vuln_type", [])


class TestExtractCategory:
    def test_web_category(self, engine):
        assert engine._extract_category({"vuln_type": ["web_sqli"]}) == "web"

    def test_crypto_category(self, engine):
        assert engine._extract_category({"vuln_type": ["crypto_rsa"]}) == "crypto"

    def test_pwn_category(self, engine):
        assert engine._extract_category({"vuln_type": ["pwn_heap"]}) == "pwn"

    def test_default_misc(self, engine):
        assert engine._extract_category({}) == "misc"


class TestFallbackFilename:
    def test_extract_from_filename(self, engine):
        meta = engine._fallback_parse_filename("强网杯2024-WriteUp.full.md")
        assert meta["year"] == 2024
        assert "强网杯" in meta["contest"]

    def test_no_year(self, engine):
        meta = engine._fallback_parse_filename("misc_challenge.md")
        assert meta["year"] == 0


class TestSearch:
    def test_search_by_keyword(self, populated_engine):
        results = populated_engine.search("SQL注入")
        assert len(results) >= 1
        assert any("强网杯" in r["title"] for r in results)

    def test_search_returns_snippet(self, populated_engine):
        results = populated_engine.search("Crypto")
        assert len(results) >= 1
        assert "snippet" in results[0]

    def test_filter_by_contest(self, populated_engine):
        results = populated_engine.search("", competition="强网杯")
        assert len(results) >= 1
        assert all("强网杯" in r["competition"] for r in results)

    def test_filter_by_year(self, populated_engine):
        results = populated_engine.search("", year=2023)
        assert len(results) >= 1
        assert all(r["year"] == 2023 for r in results)

    def test_filter_by_category(self, populated_engine):
        results = populated_engine.search("", category="crypto")
        assert len(results) >= 1
        assert all(r["category"] == "crypto" for r in results)

    def test_combined_query_and_filter(self, populated_engine):
        results = populated_engine.search("SSTI", year=2024)
        assert len(results) >= 1
        assert any("西湖论剑" in r["title"] for r in results)

    def test_no_results(self, populated_engine):
        results = populated_engine.search("不存在的关键词xyz")
        assert len(results) == 0

    def test_empty_query_returns_latest(self, populated_engine):
        results = populated_engine.search("")
        assert len(results) >= 1  # 返回所有，按年份排序


class TestBuildIndex:
    def test_build_counts(self, engine, tmp_path):
        wp_dir = tmp_path / "wp"
        wp_dir.mkdir()
        (wp_dir / "test1.md").write_text("---\ntitle: Test1\n---\ncontent1", encoding="utf-8")
        (wp_dir / "test2.md").write_text("---\ntitle: Test2\n---\ncontent2", encoding="utf-8")
        engine.build_index(str(wp_dir))
        results = engine.search("")
        assert len(results) == 2

    def test_no_duplicate_on_rebuild(self, engine, tmp_path):
        wp_dir = tmp_path / "wp"
        wp_dir.mkdir()
        (wp_dir / "test.md").write_text("---\ntitle: Test\n---\ncontent", encoding="utf-8")
        engine.build_index(str(wp_dir))
        engine.build_index(str(wp_dir))  # 第二次应被 IGNORE
        results = engine.search("")
        assert len(results) == 1
