#!/usr/bin/env python3
"""一键构建 CTF 知识库：ChromaDB 向量化 + WP SQLite FTS5 索引"""
import argparse
import sys
import os
import time

# 确保项目根目录在 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def build_chroma_kb():
    """Layer 1: 核心知识文章向量化到 ChromaDB"""
    from src.asas_mcp.memory.db import ChromaManager
    from src.asas_mcp.memory.loader import load_initial_knowledge

    print("=" * 60)
    print("Layer 1: 构建 ChromaDB 知识库...")
    print("=" * 60)

    manager = ChromaManager()

    # 清理旧数据
    try:
        manager.client.delete_collection("asas_knowledge_base")
        manager.collection = manager.client.get_or_create_collection(name="asas_knowledge_base")
        manager._initialized = False
        manager.__init__()
        print("已清理旧 ChromaDB 数据")
    except Exception as e:
        print(f"清理旧数据时出错（可忽略）: {e}")

    load_initial_knowledge(manager, "data/knowledge_base")

    count = manager.collection.count()
    print(f"ChromaDB 知识库构建完成: {count} 个文档/切片")


def build_wp_index():
    """Layer 2: WP 全文索引"""
    from src.asas_mcp.memory.wp_search import WPSearchEngine

    print("\n" + "=" * 60)
    print("Layer 2: 构建 WP 全文检索索引...")
    print("=" * 60)

    db_path = "data/writeups/wp_index.db"

    # 清理旧索引
    if os.path.exists(db_path):
        os.remove(db_path)
        print("已清理旧 WP 索引")

    engine = WPSearchEngine(db_path)

    wp_dirs = [
        "data/writeups/articles",
        "data/writeups/ctfshow",
    ]

    for wp_dir in wp_dirs:
        if os.path.exists(wp_dir):
            print(f"  索引目录: {wp_dir}")
            engine.build_index(wp_dir)
        else:
            print(f"  跳过 (不存在): {wp_dir}")

    # 统计
    cursor = engine.conn.execute("SELECT COUNT(*) FROM writeups")
    total = cursor.fetchone()[0]
    print(f"WP 索引构建完成: {total} 篇 WriteUp")

    engine.close()


def verify():
    """验证构建结果"""
    print("\n" + "=" * 60)
    print("验证构建结果...")
    print("=" * 60)

    # 验证 ChromaDB
    from src.asas_mcp.memory.db import ChromaManager
    manager = ChromaManager()
    results = manager.query("SQL注入 联合注入", n_results=3)
    print(f"\nChromaDB 测试查询 'SQL注入 联合注入':")
    for r in results:
        src = r['metadata'].get('source', '?')
        heading = r['metadata'].get('heading', '')
        print(f"  - [{src}] {heading}: {r['content'][:80]}...")

    # 验证 WP 索引
    from src.asas_mcp.memory.wp_search import WPSearchEngine
    engine = WPSearchEngine("data/writeups/wp_index.db")
    results = engine.search("反序列化", category="web", limit=3)
    print(f"\nWP 索引测试查询 '反序列化 (web)':")
    for r in results:
        print(f"  - [{r['competition']} {r['year']}] {r['title']}")
    engine.close()

    # 验证脚本注册
    from src.asas_mcp.memory.script_registry import ScriptRegistry
    registry = ScriptRegistry("data/scripts/ctf_tools")
    scripts = registry.list_scripts()
    print(f"\n脚本注册表: {len(scripts)} 个脚本工具")
    for s in scripts[:5]:
        print(f"  - [{s['category']}] {s['name']} ({s['script_count']} files)")

    print("\n✅ 所有验证通过！")


def main():
    parser = argparse.ArgumentParser(description="CTF 知识库构建工具")
    parser.add_argument("--layer", choices=["1", "2", "all"], default="all",
                       help="构建哪一层 (1=ChromaDB, 2=WP索引, all=全部)")
    parser.add_argument("--verify", action="store_true", help="构建后验证")
    args = parser.parse_args()

    start = time.time()

    if args.layer in ("1", "all"):
        build_chroma_kb()

    if args.layer in ("2", "all"):
        build_wp_index()

    if args.verify:
        verify()

    elapsed = time.time() - start
    print(f"\n总耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
