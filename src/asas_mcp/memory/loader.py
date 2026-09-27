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
    """按 ## 标题切片 Markdown 文档，保留代码块完整性。

    Args:
        content: Markdown 文本
        max_chunk_size: 每个 chunk 的最大字符数

    Returns:
        list of {"content": str, "heading": str}
    """
    # 按 ## 标题切分（保留 # 一级标题在第一个 section 中）
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
            # 超长章节按双换行（段落）二次切分
            paragraphs = section.split('\n\n')
            current_chunk = ""

            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 > max_chunk_size and current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "heading": heading
                    })
                    current_chunk = para
                else:
                    current_chunk = current_chunk + "\n\n" + para if current_chunk else para

            if current_chunk.strip():
                chunks.append({
                    "content": current_chunk.strip(),
                    "heading": heading
                })

    return chunks


def load_initial_knowledge(db_manager: ChromaManager, knowledge_dir: str = "data/knowledge_base",
                           allow_empty: bool = False):
    """加载知识库文档到 ChromaDB，支持大文件智能切片

    核心知识库缺失或为空时**默认抛错**，而不是静默跳过。
    理由：空知识库会让 agent 在没有依据的情况下作答——对 CTF 场景来说，
    自信的错误答案比明确的失败危险得多。宁可启动就报错。

    Args:
        knowledge_dir: 知识库目录。默认是**相对路径**，依赖当前工作目录。
        allow_empty: 显式接受空知识库（测试或最小化运行时可传 True）。
    """
    if not os.path.exists(knowledge_dir):
        if allow_empty:
            print(f"警告: 知识库目录不存在，按 allow_empty 继续: {knowledge_dir}")
            return
        raise FileNotFoundError(
            f"知识库目录不存在: {knowledge_dir}\n"
            f"  解析为绝对路径: {os.path.abspath(knowledge_dir)}\n"
            f"  当前工作目录: {os.getcwd()}\n"
            f"\n"
            f"  核心知识库 19 篇随仓库交付，不需要下载；此处缺失通常是两类原因：\n"
            f"    1. 工作目录不对 —— 该参数默认是相对路径，请在仓库根目录运行\n"
            f"    2. 克隆不完整 —— 用 git status 确认 data/knowledge_base/ 下的 .md 是否齐全\n"
            f"\n"
            f"  自检: python scripts/fetch_corpus.py --check\n"
            f"  确实需要空知识库运行，请显式传入 allow_empty=True。"
        )

    md_files = glob.glob(os.path.join(knowledge_dir, "*.md"))

    if not md_files:
        if allow_empty:
            print(f"警告: 知识库目录无 .md 文件，按 allow_empty 继续: {knowledge_dir}")
            return
        raise FileNotFoundError(
            f"知识库目录为空（未找到任何 .md 文件）: {knowledge_dir}\n"
            f"  解析为绝对路径: {os.path.abspath(knowledge_dir)}\n"
            f"\n"
            f"  空知识库会让 agent 无依据作答，故默认拒绝。\n"
            f"  自检: python scripts/fetch_corpus.py --check"
        )

    count = 0
    for file_path in md_files:
        try:
            filename = os.path.basename(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 大文件使用切片
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
                # 小文件整体入库
                doc_id = get_content_hash(content)

                try:
                    existing = db_manager.collection.get(ids=[doc_id])
                    if existing and existing['ids']:
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

    print(f"Loaded {count} new knowledge documents/chunks.")
