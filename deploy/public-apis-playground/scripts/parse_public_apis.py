# -*- coding: utf-8 -*-
"""解析 public-apis README.md 的表格，抽取全部 API 条目并按用途分类。

数据来源：https://github.com/public-apis/public-apis  (MIT License)
README 不在本仓库内，需自行从上游获取：
    curl -o data/README-public-apis.md https://raw.githubusercontent.com/public-apis/public-apis/master/README.md

用法：  python3 scripts/parse_public_apis.py
输出：  data/public_apis.json
"""
import json
import os
import re
from collections import Counter, OrderedDict

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("PAP_BASE") or os.path.dirname(_HERE)
DATA = os.path.join(BASE, "data")

def _first(*cands):
    """取第一个存在的路径，都不存在时返回第一个（便于报出预期位置）。"""
    for c in cands:
        if c and os.path.exists(c):
            return c
    return [c for c in cands if c][0]


README = _first(os.environ.get("PAP_README"),
                os.path.join(DATA, "README-public-apis.md"),
                "D:/code/public-apis/README.md")
OUT_JSON = os.environ.get("PAP_OUT_JSON") or os.path.join(DATA, "public_apis.json")

LINK_RE = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)")
SEP_RE = re.compile(r"^:?-{2,}:?$")
# GitHub badge 形式的特性列，如 🔐 / Yes / No / Unknown / `apiKey`
SKIP_SECTIONS = {"apis covered under apilayer suite!"}


def is_separator(cells):
    real = [c for c in cells if c]
    return bool(real) and all(SEP_RE.match(c) for c in real)


def clean(cell):
    """去掉 markdown 行内格式，保留可读文本。"""
    s = cell.strip()
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)   # 链接 -> 文本
    s = s.replace("`", "").replace("**", "").replace("*", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def main():
    text = open(README, encoding="utf-8", errors="replace").read()
    lines = text.split("\n")

    records = []
    section = None
    header = None
    headers_seen = Counter()
    section_order = []
    section_counts = OrderedDict()

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()

        if s.startswith("### "):
            name = s[4:].strip()
            if name.lower() in SKIP_SECTIONS:
                section, header = None, None
                continue
            section = name
            header = None
            if section not in section_counts:
                section_counts[section] = 0
                section_order.append(section)
            continue

        if s.startswith("## "):
            section, header = None, None
            continue

        # 表头行可能不带前导 "|"（例：API | Description | Auth | HTTPS | CORS）
        if "|" not in s:
            continue

        cells = [c.strip() for c in s.strip("|").split("|")]

        if is_separator(cells):
            continue

        lowered = [c.lower() for c in cells]
        if "description" in lowered and (lowered[0] in ("api", "name") or "auth" in lowered):
            header = cells
            headers_seen[tuple(lowered)] += 1
            continue

        if not raw.lstrip().startswith("|"):
            continue

        if header is None or section is None:
            continue

        m = LINK_RE.match(cells[0])
        if not m:
            continue

        name, url = m.group(1).strip(), m.group(2).strip()
        row = {"name": name, "url": url, "category": section}
        for i, col in enumerate(header):
            if i == 0 or i >= len(cells):
                continue
            key = col.lower().strip()
            key = {"auth": "auth", "https": "https", "cors": "cors",
                   "description": "description"}.get(key, key)
            row[key] = clean(cells[i])
        row.setdefault("description", "")
        row.setdefault("auth", "")
        row.setdefault("https", "")
        row.setdefault("cors", "")
        records.append(row)
        section_counts[section] += 1

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)

    print("=== 解析结果 ===")
    print("total_records = %d" % len(records))
    print("unique_names  = %d" % len({r["name"] for r in records}))
    print("sections      = %d" % len(section_order))
    print("headers_seen  = %s" % [list(h) for h in headers_seen])
    print()
    print("=== 各分类条目数 ===")
    for sec in section_order:
        print("%-38s %4d" % (sec, section_counts[sec]))
    print()
    print("=== Auth 值分布 ===")
    print(Counter(r["auth"] or "(空)" for r in records).most_common())
    print("=== HTTPS 分布 ===")
    print(Counter(r["https"] or "(空)" for r in records).most_common())
    print("=== CORS 分布 ===")
    print(Counter(r["cors"] or "(空)" for r in records).most_common())
    print()
    print("=== 样例 3 条 ===")
    for r in records[:3]:
        print(r)


if __name__ == "__main__":
    main()
