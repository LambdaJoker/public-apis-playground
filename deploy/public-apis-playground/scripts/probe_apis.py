# -*- coding: utf-8 -*-
"""实测 public-apis 中免鉴权 API 的可直连调用能力。

数据来源：https://github.com/public-apis/public-apis  (MIT License)

判定维度：
  1) HTTP 200？
  2) 响应是 JSON？
  3) 是否返回 Access-Control-Allow-Origin（决定浏览器里能否 fetch）

用法：  python3 scripts/probe_apis.py
输出：  data/probe_results.json
"""
import concurrent.futures as cf
import json
import os
import time
import urllib.error
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("PAP_BASE") or os.path.dirname(_HERE)
DATA = os.path.join(BASE, "data")

SRC = os.environ.get("PAP_SRC") or os.path.join(DATA, "public-apis-按用途分类.json")
OUT = os.environ.get("PAP_PROBE") or os.path.join(DATA, "probe_results.json")

ORIGIN = "http://127.0.0.1"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": ORIGIN,
    "Accept-Encoding": "identity",
}
MAX_BYTES = 192 * 1024
TIMEOUT = 9
WORKERS = 30


def probe(rec):
    url = rec["url"]
    out = {"name": rec["name"], "url": url, "category": rec["category"],
           "status": None, "ctype": "", "acao": "", "json": False,
           "ms": None, "kind": "error", "note": ""}
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            out["status"] = resp.status
            out["ctype"] = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            out["acao"] = (resp.headers.get("Access-Control-Allow-Origin") or "").strip()
            raw = resp.read(MAX_BYTES)
        out["ms"] = int((time.time() - t0) * 1000)
        txt = raw.decode("utf-8", "replace").lstrip()
        if out["ctype"].endswith("json") or txt[:1] in "{[":
            try:
                json.loads(raw.decode("utf-8", "replace"))
                out["json"] = True
            except Exception:
                out["json"] = txt[:1] in "[{"          # 截断的大 JSON 也认
        cors_ok = out["acao"] == "*" or ORIGIN in out["acao"]
        if out["json"] and cors_ok:
            out["kind"] = "direct"                      # 浏览器可直接调用
        elif out["json"]:
            out["kind"] = "json_no_cors"                # 有数据但会被 CORS 拦
        elif out["status"] == 200:
            out["kind"] = "page"                        # 文档页 / HTML
        else:
            out["kind"] = "http_error"
        if not out["json"] and out["ctype"] in ("text/html", ""):
            out["note"] = "文档页"
    except urllib.error.HTTPError as e:
        out["status"] = e.code
        out["ms"] = int((time.time() - t0) * 1000)
        out["kind"] = "http_error"
        out["note"] = "HTTP %s" % e.code
    except Exception as e:
        out["ms"] = int((time.time() - t0) * 1000)
        out["kind"] = "error"
        out["note"] = type(e).__name__
    return out


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    targets = []
    for cat, rows in data.items():
        for r in rows:
            if r["auth"].lower() == "no" and r["https"].lower() == "yes":
                targets.append({"name": r["name"], "url": r["url"], "category": cat})
    print("targets=%d workers=%d timeout=%ds" % (len(targets), WORKERS, TIMEOUT), flush=True)

    results, done = [], 0
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        for res in ex.map(probe, targets):
            results.append(res)
            done += 1
            if done % 50 == 0:
                print("progress %d/%d" % (done, len(targets)), flush=True)

    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter
    k = Counter(r["kind"] for r in results)
    print("--- 结果 ---")
    for kind, n in k.most_common():
        print("  %-14s %d" % (kind, n))
    direct = [r for r in results if r["kind"] == "direct"]
    print("可直连调用: %d 条" % len(direct))
    for r in direct[:15]:
        print("   %-22s %s" % (r["name"], r["url"]))
    print("saved -> %s" % OUT)


if __name__ == "__main__":
    main()
