# CTF 知识库整合 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Des-CTF-Knowledge 知识库（12篇漏洞文章+1156篇WP+50+脚本）整合进 CTFBot，通过三层架构（ChromaDB + SQLite FTS5 + 脚本挂载）让 Agent 在比赛中快速检索。

**Architecture:** Layer 1 将核心漏洞文章切片后存入 ChromaDB 做语义检索；Layer 2 解析 WP 的 YAML frontmatter 建 SQLite FTS5 全文索引；Layer 3 注册脚本工具到 MCP，通过已有 sandbox 执行。三层通过 3 个新 MCP 工具对外暴露。

**Tech Stack:** Python 3.10+, ChromaDB, SQLite FTS5, FastMCP, PyYAML

**设计决策:**
- WP/脚本使用符号链接引用
- ChromaDB 嵌入模型保持默认 all-MiniLM-L6-v2
- WP 元数据从 YAML frontmatter 提取（已发现 WP 自带），正则兜底
- 脚本在 Docker sandbox 中执行

---

### Task 1: 目录结构 + 符号链接 + 核心知识复制

**Files:**
- Create: `data/writeups/` (目录)
- Create: `data/scripts/` (目录)
- Copy: 核心知识文章到 `data/knowledge_base/`
- Create: symlinks

**Step 1: 创建目录结构**

```bash
cd /Users/guoshuguang/my-project/ctfbot
mkdir -p data/writeups data/scripts
```

**Step 2: 创建符号链接**

```bash
# WP 文章链接
ln -s /Users/guoshuguang/my-project/ctf-wp/Des-CTF-Knowledge/CTF大赛WP集合/articles data/writeups/articles
ln -s /Users/guoshuguang/my-project/ctf-wp/Des-CTF-Knowledge/WP汇总 data/writeups/ctfshow

# 脚本工具链接
ln -s /Users/guoshuguang/my-project/ctf-wp/Des-CTF-Knowledge/CTF常用脚本及工具 data/scripts/ctf_tools
```

**Step 3: 复制核心知识文章到 knowledge_base/**

```bash
SRC="/Users/guoshuguang/my-project/ctf-wp/Des-CTF-Knowledge"
DST="/Users/guoshuguang/my-project/ctfbot/data/knowledge_base"

# 删除旧占位文件
rm -f "$DST/web_sqli.md" "$DST/crypto_classical.md" "$DST/linux_privesc.md"

# 复制核心文章（重命名为英文前缀分类）
cp "$SRC/SQL.md" "$DST/web_sqli.md"
cp "$SRC/命令执行.md" "$DST/web_rce.md"
cp "$SRC/文件上传漏洞.md" "$DST/web_upload.md"
cp "$SRC/文件包含.md" "$DST/web_lfi.md"
cp "$SRC/SSRF漏洞.md" "$DST/web_ssrf.md"
cp "$SRC/SSTI.md" "$DST/web_ssti.md"
cp "$SRC/JWT.md" "$DST/web_jwt.md"
cp "$SRC/PHP反序列化漏洞总结.md" "$DST/web_deserialize.md"
cp "$SRC/php代码审计.md" "$DST/web_audit.md"
cp "$SRC/图片隐写.md" "$DST/misc_image_stego.md"
cp "$SRC/音频隐写.md" "$DST/misc_audio_stego.md"
cp "$SRC/压缩包总结.md" "$DST/misc_archive.md"
cp "$SRC/PAYLOAD-CHEATSHEET.md" "$DST/payload_cheatsheet.md"

# 复制工具速查
cp "$SRC/工具使用/sqlmap-Cheat-Sheet.md" "$DST/tools_sqlmap.md"
cp "$SRC/工具使用/Wireshark使用.md" "$DST/tools_wireshark.md"
cp "$SRC/工具使用/tshark使用.md" "$DST/tools_tshark.md"
cp "$SRC/工具使用/ffuf的使用.md" "$DST/tools_ffuf.md"
cp "$SRC/工具使用/Dirsearch.md" "$DST/tools_dirsearch.md"
cp "$SRC/工具使用/内存取证秒杀所有命令.md" "$DST/tools_volatility.md"
```

**Step 4: 验证**

```bash
ls -la data/writeups/articles | head -5  # 确认符号链接可访问
ls -la data/scripts/ctf_tools | head -5
ls data/knowledge_base/ | wc -l  # 应该 ~19 个文件
```

**Step 5: 更新 .gitignore**

在 `.gitignore` 中添加：
```
# 符号链接指向的外部知识库（不需要 git 跟踪）
data/writeups/articles
data/writeups/ctfshow
data/scripts/ctf_tools
# ChromaDB & SQLite index (构建脚本生成)
data/chroma_db/
data/writeups/wp_index.db
```

**Step 6: Commit**

```bash
git add data/knowledge_base/ data/writeups/.gitkeep data/scripts/.gitkeep .gitignore
git commit -m "feat(kb): 导入12篇核心漏洞文章+工具速查+建立WP/脚本符号链接"
```

---

### Task 2: Markdown 智能切片 Loader

**Files:**
- Modify: `src/asas_mcp/memory/loader.py`
- Create: `tests/test_loader.py`

**Step 1: 写失败测试**

```python
# tests/test_loader.py
import pytest
from src.asas_mcp.memory.loader import chunk_markdown

def test_chunk_by_heading():
    """按 ## 标题切片"""
    content = """# SQL注入

## 联合注入

联合注入是最基本的注入方式。

## 报错注入

利用报错函数获取数据。
"""
    chunks = chunk_markdown(content, max_chunk_size=500)
    assert len(chunks) >= 2
    assert "联合注入" in chunks[0]["heading"]
    assert "报错注入" in chunks[1]["heading"]

def test_chunk_preserves_code_blocks():
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
    assert "```python" in chunks[0]["content"]

def test_chunk_oversized_section():
    """超大章节按段落二次切分"""
    long_para = "A" * 200 + "\n\n"
    content = "## 大章节\n\n" + long_para * 10
    chunks = chunk_markdown(content, max_chunk_size=500)
    assert len(chunks) > 1
```

**Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_loader.py -v
```
Expected: FAIL (chunk_markdown 不存在)

**Step 3: 实现 chunk_markdown**

改写 `src/asas_mcp/memory/loader.py`：

```python
import os
import re
import glob
import hashlib
from .db import ChromaManager


def get_content_hash(content: str) -> str:
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def extract_heading(text: str) -> str:
    """从 Markdown 文本块中提取第一个标题"""
    match = re.search(r'^#{1,6}\s+(.+)$', text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def chunk_markdown(content: str, max_chunk_size: int = 1500) -> list[dict]:
    """按 ## 标题切片 Markdown 文档，保留代码块完整性。"""
    sections = re.split(r'\n(?=##\s)', content)
    
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        heading = extract_heading(section)
        
        if len(section) <= max_chunk_size:
            chunks.append({"content": section, "heading": heading})
        else:
            paragraphs = section.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 > max_chunk_size and current_chunk:
                    chunks.append({"content": current_chunk.strip(), "heading": heading})
                    current_chunk = para
                else:
                    current_chunk = current_chunk + "\n\n" + para if current_chunk else para
            
            if current_chunk.strip():
                chunks.append({"content": current_chunk.strip(), "heading": heading})
    
    return chunks


def load_initial_knowledge(db_manager: ChromaManager, knowledge_dir: str = "data/knowledge_base"):
    """加载知识库文档到 ChromaDB，支持大文件智能切片"""
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
            
            if len(content) > 2000:
                chunks = chunk_markdown(content, max_chunk_size=1500)
                for i, chunk in enumerate(chunks):
                    doc_id = get_content_hash(f"{filename}:{i}:{chunk['content'][:100]}")
                    try:
                        existing = db_manager.collection.get(ids=[doc_id])
                        if existing and existing['ids']:
                            continue
                    except Exception:
                        pass
                    metadata = {
                        "source": filename,
                        "type": "knowledge_chunk",
                        "heading": chunk["heading"],
                        "chunk_index": i
                    }
                    db_manager.add(content=chunk["content"], metadata=metadata, doc_id=doc_id)
                    count += 1
            else:
                doc_id = get_content_hash(content)
                try:
                    existing = db_manager.collection.get(ids=[doc_id])
                    if existing and existing['ids']:
                        continue
                except Exception:
                    pass
                metadata = {"source": filename, "type": "initial_knowledge"}
                db_manager.add(content=content, metadata=metadata, doc_id=doc_id)
                count += 1
                
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    print(f"Loaded {count} new knowledge documents/chunks.")
```

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_loader.py -v
```

**Step 5: Commit**

```bash
git add src/asas_mcp/memory/loader.py tests/test_loader.py
git commit -m "feat(kb): Markdown智能切片loader，按标题分段+大文件二次切分"
```

---

### Task 3: WP 全文检索引擎 (SQLite FTS5)

**Files:**
- Create: `src/asas_mcp/memory/wp_search.py`
- Create: `tests/test_wp_search.py`

**Step 1: 写失败测试**

```python
# tests/test_wp_search.py
import pytest
from src.asas_mcp.memory.wp_search import WPSearchEngine

@pytest.fixture
def engine(tmp_path):
    db_path = str(tmp_path / "test_wp.db")
    return WPSearchEngine(db_path)

@pytest.fixture
def populated_engine(engine, tmp_path):
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
---

# 强网杯 SQL注入

使用联合注入获取flag...
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

RSA共模攻击...
""", encoding="utf-8")
    engine.build_index(str(wp_dir))
    return engine

def test_search_by_keyword(populated_engine):
    results = populated_engine.search("SQL注入")
    assert len(results) >= 1
    assert "强网杯" in results[0]["title"]

def test_filter_by_contest(populated_engine):
    results = populated_engine.search("", competition="强网杯")
    assert len(results) >= 1

def test_filter_by_year(populated_engine):
    results = populated_engine.search("", year=2023)
    assert len(results) >= 1
    assert all(r["year"] == 2023 for r in results)

def test_parse_frontmatter(engine):
    meta = engine._parse_frontmatter("""---
title: Test WP
contest: CTF 2024
year: 2024
vuln_type:
- web_sqli
---
content
""")
    assert meta["title"] == "Test WP"
    assert meta["year"] == 2024
```

**Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_wp_search.py -v
```

**Step 3: 实现 WPSearchEngine**

创建 `src/asas_mcp/memory/wp_search.py`（完整代码见方案文档 Task 3 部分，包含 YAML frontmatter 解析 + SQLite FTS5 + 文件名正则兜底）

**Step 4: 运行测试**

```bash
python -m pytest tests/test_wp_search.py -v
```

**Step 5: Commit**

```bash
git add src/asas_mcp/memory/wp_search.py tests/test_wp_search.py
git commit -m "feat(kb): WP全文检索引擎，SQLite FTS5 + YAML frontmatter解析"
```

---

### Task 4: 脚本工具注册表

**Files:**
- Create: `src/asas_mcp/memory/script_registry.py`
- Create: `tests/test_script_registry.py`

**Step 1 ~ Step 4:** 实现 ScriptRegistry（分类映射 + 关键词查找），详见方案文档 Task 4。

**Step 5: Commit**

```bash
git add src/asas_mcp/memory/script_registry.py tests/test_script_registry.py
git commit -m "feat(kb): 脚本工具注册表，按分类索引50+解题脚本"
```

---

### Task 5: 注册 MCP 工具

**Files:**
- Modify: `src/asas_mcp/server.py` (L325 之前插入新工具)

**Step 1:** 在 `memory_query` 之后、`create_app()` 之前插入 `search_writeups` / `list_ctf_scripts` / `run_ctf_script` 三个 MCP 工具

**Step 2:** 更新 `create_app()` 的 tools 列表

**Step 3: Commit**

```bash
git add src/asas_mcp/server.py
git commit -m "feat(mcp): 注册search_writeups/list_ctf_scripts/run_ctf_script三个MCP工具"
```

---

### Task 6: 一键构建脚本

**Files:**
- Create: `scripts/build_kb.py`

实现 `build_kb.py`，支持 `--layer 1|2|all` + `--verify`

**Commit:**
```bash
git add scripts/build_kb.py
git commit -m "feat(kb): 一键构建脚本 build_kb.py"
```

---

### Task 7: 集成测试

**Files:**
- Create: `tests/test_kb_integration.py`

验证三层架构：knowledge_base 文件完整性 + WP symlink + 脚本注册表

**Commit:**
```bash
git add tests/test_kb_integration.py
git commit -m "test(kb): 三层知识库架构集成测试"
```

---

### Task 8: 文档更新

**Files:**
- Modify: `README.md`

追加知识库章节 + 更新路线图

**Commit:**
```bash
git add README.md
git commit -m "docs: 更新README，添加知识库章节和路线图"
```
