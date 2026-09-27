#!/usr/bin/env python3
"""拉取大件语料（WP 全文 31MB + 脚本工具 4.4MB）

背景：
    本仓库只随附 19 篇核心知识库（data/knowledge_base/，1.0MB，见该目录 LICENSE）。
    大件语料体积达 35MB 且为第三方汇编，故不入库，改由本脚本按需拉取。

用法：
    python scripts/fetch_corpus.py              # 拉取 + 建链
    python scripts/fetch_corpus.py --skip-build # 只拉取，不建索引
    python scripts/fetch_corpus.py --check      # 只检查现状，不下载

拉取后目录结构：
    data/vendor/Des-CTF-Knowledge/        ← 上游克隆（锁定 commit）
    data/writeups/articles    ->  ../vendor/Des-CTF-Knowledge/CTF大赛WP集合/articles
    data/writeups/ctfshow     ->  ../vendor/Des-CTF-Knowledge/WP汇总
    data/scripts/ctf_tools    ->  ../vendor/Des-CTF-Knowledge/CTF常用脚本及工具

    符号链接使用**相对路径**，因此整个仓库目录可以整体移动/拷贝。
"""
import argparse
import os
import shutil
import subprocess
import sys

# 上游仓库与锁定版本。改这里即可换语料来源。
# commit 与 data/knowledge_base/LICENSE 中记录的一致。
UPSTREAM_REPO = "https://github.com/Dest1ny-Sec/Des-CTF-Knowledge.git"
PINNED_COMMIT = "03525c6104c6f9c9a8061f05c2d045ecc31428b2"

VENDOR_DIR = os.path.join("data", "vendor", "Des-CTF-Knowledge")

# (链接路径, 上游内相对路径, 期望最少文件数)
LINKS = [
    (os.path.join("data", "writeups", "articles"),
     os.path.join("CTF大赛WP集合", "articles"), 1000),
    (os.path.join("data", "writeups", "ctfshow"),
     "WP汇总", 60),
    (os.path.join("data", "scripts", "ctf_tools"),
     "CTF常用脚本及工具", 100),
]


def _run(cmd, cwd=None):
    """执行外部命令，失败时抛出带 stderr 的明确错误"""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"命令失败: {' '.join(cmd)}\n"
            f"  stdout: {result.stdout.strip()}\n"
            f"  stderr: {result.stderr.strip()}"
        )
    return result.stdout


def clone_upstream(commit: str, repo: str):
    """克隆上游并切到锁定 commit。已存在且 commit 正确则跳过。"""
    if os.path.exists(os.path.join(VENDOR_DIR, ".git")):
        head = _run(["git", "rev-parse", "HEAD"], cwd=VENDOR_DIR).strip()
        if head == commit:
            print(f"上游已就绪且 commit 正确（{commit[:8]}），跳过克隆")
            return
        print(f"上游 commit 不符（当前 {head[:8]}，需要 {commit[:8]}），重新检出...")
        _run(["git", "fetch", "--all", "--tags"], cwd=VENDOR_DIR)
        _run(["git", "checkout", "--detach", commit], cwd=VENDOR_DIR)
        print("已切换到锁定 commit")
        return

    if os.path.exists(VENDOR_DIR):
        print(f"发现残留目录但非有效 git 仓库，清理后重来: {VENDOR_DIR}")
        shutil.rmtree(VENDOR_DIR)

    os.makedirs(os.path.dirname(VENDOR_DIR), exist_ok=True)
    print(f"克隆上游 {repo} ...")
    print("  （约 70MB，首次需数分钟；此后复用不再下载）")
    try:
        _run(["git", "clone", "--quiet", repo, VENDOR_DIR])
    except RuntimeError as e:
        raise RuntimeError(
            f"克隆失败——请确认网络可达 GitHub。\n原始错误:\n{e}\n\n"
            f"离线环境请手动准备语料，或改 UPSTREAM_REPO 指向内网镜像。"
        )
    _run(["git", "checkout", "--detach", "--quiet", commit], cwd=VENDOR_DIR)
    print(f"已克隆并锁定 commit {commit[:8]}")


def make_links():
    """建立相对符号链接。返回 (成功数, 失败列表)"""
    ok, failed = 0, []
    for link_path, upstream_rel, min_files in LINKS:
        target_abs = os.path.join(VENDOR_DIR, upstream_rel)

        if not os.path.isdir(target_abs):
            failed.append((link_path, f"上游路径不存在: {upstream_rel}"))
            continue

        # 相对链接：相对 link_path 所在目录计算
        link_dir = os.path.dirname(link_path) or "."
        os.makedirs(link_dir, exist_ok=True)
        rel_target = os.path.relpath(target_abs, link_dir)

        # 已存在
        if os.path.islink(link_path):
            if os.readlink(link_path) == rel_target:
                n = _count_files(link_path)
                print(f"  ✓ {link_path} 已就绪（{n} 个文件）")
                ok += 1
                continue
            print(f"  ! {link_path} 指向错误，重建")
            os.unlink(link_path)
        elif os.path.exists(link_path):
            # 真实目录——可能是在此之前就存在的本地语料，不要删除
            n = _count_files(link_path)
            print(f"  ! {link_path} 是真实目录（{n} 个文件），保留不动。")
            print(f"    如需改用上游语料，请先手动移走该目录。")
            if n >= min_files:
                ok += 1
            else:
                failed.append((link_path, f"真实目录但仅 {n} 个文件（期望 ≥{min_files}）"))
            continue

        os.symlink(rel_target, link_path)
        n = _count_files(link_path)
        status = "✓" if n >= min_files else "!"
        print(f"  {status} {link_path} -> {rel_target}（{n} 个文件）")
        if n >= min_files:
            ok += 1
        else:
            failed.append((link_path, f"仅 {n} 个文件，期望 ≥{min_files}"))

    return ok, failed


def _count_files(path: str) -> int:
    """统计文件数，跟随符号链接"""
    total = 0
    for _, _, files in os.walk(path, followlinks=True):
        total += len(files)
    return total


def check():
    """只检查现状，不下载。返回退出码：0 = 全部就绪"""
    print("=" * 60)
    print("语料现状检查")
    print("=" * 60)

    # 三类问题分别归因，因为补救动作完全不同
    kb_ok = True
    corpus_ok = True
    artifacts_ok = True

    kb = os.path.join("data", "knowledge_base")
    n_kb = len([f for f in os.listdir(kb) if f.endswith(".md")]) if os.path.isdir(kb) else 0
    kb_ok = n_kb >= 19
    print(f"\n[核心知识库] data/knowledge_base")
    print(f"  {'✓' if kb_ok else '✗'} {n_kb} 篇（随仓库交付，应为 19）")

    print(f"\n[大件语料] 由 fetch_corpus.py 拉取")
    for link_path, upstream_rel, min_files in LINKS:
        if os.path.islink(link_path) and not os.path.exists(link_path):
            print(f"  ✗ {link_path} 是断链（target 缺失）")
            corpus_ok = False
        elif os.path.exists(link_path):
            n = _count_files(link_path)
            good = n >= min_files
            print(f"  {'✓' if good else '✗'} {link_path}: {n} 个文件（期望 ≥{min_files}）")
            corpus_ok = corpus_ok and good
        else:
            print(f"  ✗ {link_path} 不存在")
            corpus_ok = False

    print(f"\n[构建产物]")
    for art, desc in [("data/writeups/wp_index.db", "WP 全文索引"),
                      ("data/chroma_db/chroma.sqlite3", "ChromaDB 向量库")]:
        exists = os.path.exists(art)
        print(f"  {'✓' if exists else '✗'} {art}（{desc}）")
        artifacts_ok = artifacts_ok and exists

    # 分诊：每类问题给出对应的、正确的那条命令
    print()
    if kb_ok and corpus_ok and artifacts_ok:
        print("全部就绪。")
        return 0

    print("待办：")
    if not kb_ok:
        print("  · 核心知识库缺失 —— 它随仓库交付，fetch_corpus.py 不负责拉取。")
        print("    请确认克隆完整（git status / 重新 clone），或核对上游 LICENSE 说明。")
    if not corpus_ok:
        print("  · 大件语料缺失 → python scripts/fetch_corpus.py")
    if not artifacts_ok:
        print("  · 构建产物缺失 → python scripts/build_kb.py --layer 2")
    return 1


def main():
    parser = argparse.ArgumentParser(description="拉取大件语料（WP 全文 + 脚本工具）")
    parser.add_argument("--repo", default=UPSTREAM_REPO, help="上游仓库地址")
    parser.add_argument("--commit", default=PINNED_COMMIT, help="锁定的 commit")
    parser.add_argument("--skip-build", action="store_true",
                        help="只拉取语料，不构建索引")
    parser.add_argument("--check", action="store_true",
                        help="只检查现状，不下载")
    args = parser.parse_args()

    if args.check:
        sys.exit(check())

    # 必须在仓库根目录运行（build_kb.py 与各处路径都基于根目录）
    if not os.path.isdir("src") or not os.path.isdir("scripts"):
        print("错误：请在仓库根目录运行本脚本。", file=sys.stderr)
        sys.exit(2)

    print("=" * 60)
    print("Step 1/3: 拉取上游语料")
    print("=" * 60)
    try:
        clone_upstream(args.commit, args.repo)
    except RuntimeError as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)

    print()
    print("=" * 60)
    print("Step 2/3: 建立语料链接")
    print("=" * 60)
    ok, failed = make_links()
    if failed:
        print(f"\n{len(failed)} 项未就绪：")
        for path, why in failed:
            print(f"  - {path}: {why}")
        print("\n语料不完整，中止。请检查上游目录结构是否已变更。", file=sys.stderr)
        sys.exit(1)
    print(f"\n{ok}/{len(LINKS)} 项语料就绪")

    if args.skip_build:
        print("\n已跳过构建。后续运行: python scripts/build_kb.py --layer 2")
        return

    print()
    print("=" * 60)
    print("Step 3/3: 构建 WP 全文索引")
    print("=" * 60)
    try:
        _run([sys.executable, os.path.join("scripts", "build_kb.py"), "--layer", "2"])
    except RuntimeError as e:
        print(f"\n构建索引失败:\n{e}", file=sys.stderr)
        sys.exit(1)

    print()
    print("完成。验证: python scripts/fetch_corpus.py --check")


if __name__ == "__main__":
    main()
