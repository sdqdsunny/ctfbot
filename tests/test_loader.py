"""Tests for Markdown smart chunking loader."""
import pytest
from src.asas_mcp.memory.loader import chunk_markdown, extract_heading


class TestExtractHeading:
    def test_h1_heading(self):
        assert extract_heading("# SQL注入\n\n内容") == "SQL注入"

    def test_h2_heading(self):
        assert extract_heading("## 联合注入\n\n内容") == "联合注入"

    def test_no_heading(self):
        assert extract_heading("普通文本，没有标题") == ""


class TestChunkMarkdown:
    def test_chunk_by_heading(self):
        """按 ## 标题切片"""
        content = """# SQL注入

## 联合注入

联合注入是最基本的注入方式。

```sql
-1' union select 1,2,3#
```

## 报错注入

利用报错函数获取数据。

```sql
1' and updatexml(1,concat(0x7e,database()),1)#
```
"""
        chunks = chunk_markdown(content, max_chunk_size=500)
        assert len(chunks) >= 2
        # 第一个 chunk 包含 # 一级标题和第一个 ## 小节
        headings = [c["heading"] for c in chunks]
        assert any("联合注入" in h for h in headings)
        assert any("报错注入" in h for h in headings)

    def test_chunk_preserves_code_blocks(self):
        """代码块不被截断"""
        content = """## 方法一

```python
def exploit():
    payload = "' or 1=1--"
    return payload
```

详细说明在这里。
"""
        chunks = chunk_markdown(content, max_chunk_size=500)
        assert len(chunks) >= 1
        assert "```python" in chunks[0]["content"]
        assert 'exploit' in chunks[0]["content"]

    def test_chunk_oversized_section(self):
        """超大章节按段落二次切分"""
        long_para = "A" * 200 + "\n\n"
        content = "## 大章节\n\n" + long_para * 10
        chunks = chunk_markdown(content, max_chunk_size=500)
        assert len(chunks) > 1
        # 所有 chunks 的 heading 都是 "大章节"
        for chunk in chunks:
            assert chunk["heading"] == "大章节"

    def test_small_content_single_chunk(self):
        """小内容不切分"""
        content = "## 简单内容\n\n这是一小段文字。"
        chunks = chunk_markdown(content, max_chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0]["heading"] == "简单内容"

    def test_empty_content(self):
        """空内容返回空列表"""
        chunks = chunk_markdown("", max_chunk_size=500)
        assert chunks == []

    def test_no_headings(self):
        """无标题的纯文本"""
        content = "这是一段没有标题的文字。\n\n另一段文字。"
        chunks = chunk_markdown(content, max_chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0]["heading"] == ""
