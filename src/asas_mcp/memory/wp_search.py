"""基于 SQLite FTS5 的 WriteUp 全文检索引擎"""
import sqlite3
import os
import re
import glob
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


class WPSearchEngine:
    """CTF WriteUp 全文检索引擎，使用 SQLite FTS5"""

    def __init__(self, db_path: str = "data/writeups/wp_index.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS writeups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                competition TEXT DEFAULT '',
                category TEXT DEFAULT '',
                year INTEGER DEFAULT 0,
                filepath TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS writeups_fts USING fts5(
                title, competition, category, content,
                content='writeups',
                content_rowid='id',
                tokenize='unicode61'
            );

            CREATE TRIGGER IF NOT EXISTS writeups_ai AFTER INSERT ON writeups BEGIN
                INSERT INTO writeups_fts(rowid, title, competition, category, content)
                VALUES (new.id, new.title, new.competition, new.category, new.content);
            END;
        """)
        self.conn.commit()

    def _parse_frontmatter(self, text: str) -> dict:
        """解析 YAML frontmatter"""
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
        if not match:
            return {}

        raw = match.group(1)

        if yaml:
            try:
                return yaml.safe_load(raw) or {}
            except Exception:
                pass

        # 简单正则回退解析
        meta = {}
        for key in ("title", "contest", "year", "difficulty"):
            m = re.search(rf'^{key}:\s*(.+)$', raw, re.MULTILINE)
            if m:
                val = m.group(1).strip()
                if key == "year":
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                meta[key] = val

        # 解析列表字段
        for key in ("vuln_type", "tags"):
            list_match = re.search(rf'^{key}:\s*\n((?:^-\s+.+\n?)+)', raw, re.MULTILINE)
            if list_match:
                items = re.findall(r'^-\s+(.+)$', list_match.group(1), re.MULTILINE)
                if items:
                    meta[key] = [i.strip() for i in items]

        return meta

    def _extract_category(self, meta: dict) -> str:
        """从 vuln_type 推断大类"""
        vuln_types = meta.get("vuln_type", [])
        if isinstance(vuln_types, str):
            vuln_types = [vuln_types]

        category_map = {
            "web": ["web", "sqli", "rce", "xss", "ssrf", "ssti", "lfi", "upload", "deserialize"],
            "crypto": ["crypto", "rsa", "aes", "des"],
            "pwn": ["pwn", "bof", "heap", "rop", "shellcode"],
            "reverse": ["reverse", "re_", "android"],
            "misc": ["misc", "stego", "forensic", "osint"],
        }

        for vt in vuln_types:
            vt_lower = vt.lower()
            for cat, keywords in category_map.items():
                if any(k in vt_lower for k in keywords):
                    return cat
        return "misc"

    def _fallback_parse_filename(self, filename: str) -> dict:
        """从文件名正则提取元数据（YAML 解析失败时的兜底）"""
        name = os.path.splitext(filename)[0]
        name = name.replace(".full", "")

        # 尝试提取年份
        year_match = re.search(r'(20\d{2})', name)
        year = int(year_match.group(1)) if year_match else 0

        # 尝试提取赛事名
        contest_patterns = [
            r'^(.+?)[-_](?:WriteUp|WP|writeup|wp)',
            r'^(.+?)[-_](?:题解|解析|复现)',
            r'^(.+?)$'
        ]
        contest = name
        for pat in contest_patterns:
            m = re.match(pat, name)
            if m:
                contest = m.group(1).strip().replace("_", " ")
                break

        return {
            "title": name.replace("_", " "),
            "contest": contest,
            "year": year,
        }

    def build_index(self, wp_dir: str):
        """从目录构建 WP 索引"""
        md_files = glob.glob(os.path.join(wp_dir, "**/*.md"), recursive=True)

        count = 0
        for filepath in md_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                meta = self._parse_frontmatter(content)

                if not meta.get("title"):
                    fallback = self._fallback_parse_filename(os.path.basename(filepath))
                    meta = {**fallback, **{k: v for k, v in meta.items() if v}}

                title = meta.get("title", os.path.basename(filepath))
                competition = meta.get("contest", "")
                year = meta.get("year", 0)
                if isinstance(year, str):
                    try:
                        year = int(year)
                    except ValueError:
                        year = 0
                category = self._extract_category(meta)

                # 去掉 frontmatter 只存正文
                body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, count=1, flags=re.DOTALL)

                self.conn.execute(
                    "INSERT OR IGNORE INTO writeups (title, competition, category, year, filepath, content) VALUES (?, ?, ?, ?, ?, ?)",
                    (title, competition, category, year, filepath, body)
                )
                count += 1

            except Exception as e:
                print(f"Error indexing {filepath}: {e}")

        self.conn.commit()
        print(f"Indexed {count} writeups.")

    def search(
        self,
        query: str = "",
        competition: str = None,
        category: str = None,
        year: int = None,
        limit: int = 10
    ) -> list[dict]:
        """搜索 WriteUp

        Args:
            query: 搜索关键词（如 "SQL注入 WAF绕过"）
            competition: 过滤赛事名（如 "强网杯"）
            category: 过滤方向（web / crypto / pwn / reverse / misc）
            year: 过滤年份
            limit: 返回结果数量上限

        Returns:
            匹配的 WriteUp 列表
        """
        if query and not competition and not category and not year:
            # 纯全文搜索
            sql = """
                SELECT w.*, rank
                FROM writeups_fts fts
                JOIN writeups w ON w.id = fts.rowid
                WHERE writeups_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            cursor = self.conn.execute(sql, [query, limit])
        elif query:
            # 全文搜索 + 过滤
            conditions = []
            params = [query]
            if competition:
                conditions.append("w.competition LIKE ?")
                params.append(f"%{competition}%")
            if category:
                conditions.append("w.category = ?")
                params.append(category)
            if year:
                conditions.append("w.year = ?")
                params.append(year)
            extra = " AND " + " AND ".join(conditions) if conditions else ""
            sql = f"""
                SELECT w.*, rank
                FROM writeups_fts fts
                JOIN writeups w ON w.id = fts.rowid
                WHERE writeups_fts MATCH ?{extra}
                ORDER BY rank
                LIMIT ?
            """
            params.append(limit)
            cursor = self.conn.execute(sql, params)
        else:
            # 仅过滤（无全文搜索）
            conditions = []
            params = []
            if competition:
                conditions.append("competition LIKE ?")
                params.append(f"%{competition}%")
            if category:
                conditions.append("category = ?")
                params.append(category)
            if year:
                conditions.append("year = ?")
                params.append(year)
            where = " WHERE " + " AND ".join(conditions) if conditions else ""
            sql = f"SELECT * FROM writeups{where} ORDER BY year DESC LIMIT ?"
            params.append(limit)
            cursor = self.conn.execute(sql, params)

        results = []
        for row in cursor:
            content = row["content"]
            results.append({
                "id": row["id"],
                "title": row["title"],
                "competition": row["competition"],
                "category": row["category"],
                "year": row["year"],
                "filepath": row["filepath"],
                "snippet": content[:500] + "..." if len(content) > 500 else content
            })

        return results

    def close(self):
        self.conn.close()
