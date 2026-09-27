import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import concurrent.futures

def dir_scan(url: str, custom_words: list = None) -> dict:
    """轻量级目录扫描"""
    common_words = ["admin", "login", "config", "phpmyadmin", ".git", ".env", "uploads", "flag.php", "flag"]
    words = custom_words if custom_words else common_words
    results = []
    
    def check_path(path):
        target = urljoin(url, path)
        try:
            resp = requests.head(target, timeout=2)
            if resp.status_code < 400:
                return {"path": path, "status": resp.status_code, "url": target}
        except:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_path, w): w for w in words}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
    
    return {"found": results}

def sql_check(url: str, param: str) -> dict:
    """初步 SQL 注入检查 (基于报错)"""
    payloads = ["'", "''", "\"", "\\", ")' or '1'='1"]
    vulnerabilities = []
    
    for p in payloads:
        # 简单 GET 请求注入
        target = f"{url}?{param}={p}"
        try:
            resp = requests.get(target, timeout=3)
            # 常见 SQL 错误关键字
            errors = ["SQL syntax", "mysql_fetch", "ORA-", "PostgreSQL", "SQLite/JDBC"]
            for err in errors:
                if err.lower() in resp.text.lower():
                    vulnerabilities.append({"payload": p, "type": "Error-based SQLi", "evidence": err})
                    break
        except:
            pass
            
    return {"vulnerable": len(vulnerabilities) > 0, "details": vulnerabilities}

def extract_links(url: str) -> list:
    """从页面提取链接和表单"""
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            links.append(urljoin(url, a['href']))
        
        forms = []
        for f in soup.find_all('form'):
            forms.append({
                "action": f.get('action'),
                "method": f.get('method', 'get'),
                "inputs": [i.get('name') for i in f.find_all('input') if i.get('name')]
            })
            
        return {"links": list(set(links)), "forms": forms}
    except Exception as e:
        return {"error": str(e)}
