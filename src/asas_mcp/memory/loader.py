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
