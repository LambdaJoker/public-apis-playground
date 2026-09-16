#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public APIs 调试试台 · 服务端 / 本地服务

作用：
  1) 提供静态页面（同源，避开托管环境 CSP 的 `default-src 'self'` 限制）
  2) /api/proxy?url=... 服务端转发 —— 不受浏览器 CORS 约束，
     因此「未开放跨域」的上游接口也能调通

数据来源：https://github.com/public-apis/public-apis  (MIT License)

用法：
  python3 serve.py [port]        默认 8899

环境变量：
  NO_OPEN=1        不自动打开浏览器（服务端部署必设）
  BIND=0.0.0.0     监听地址，默认 127.0.0.1（服务端由 nginx 反代即可，无需对外暴露）
  PAP_SITE=/path   静态根目录，默认自动探测 ../site（部署包结构）或脚本所在目录
  INDEX=xxx        首页文件名，默认自动探测 index.html / public-apis-API调试试台.html

目录约定（部署包）：
  <BASE>/site/index.html      页面
  <BASE>/scripts/serve.py     本脚本
  <BASE>/data/                数据集
"""
import base64
import ipaddress
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler

try:
    from http.server import ThreadingHTTPServer          # Python 3.7+
except ImportError:                                      # Python 3.6 及更早
    from http.server import HTTPServer
    from socketserver import ThreadingMixIn

    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("PAP_BASE") or os.path.dirname(HERE)
BIND = os.environ.get("BIND", "127.0.0.1")
CANDIDATES = ("index.html", "public-apis-API调试试台.html")


def pick_root():
    """静态根目录：优先环境变量，其次部署包的 ../site，最后脚本所在目录。"""
    env = os.environ.get("PAP_SITE")
    if env:
        return env
    for d in (os.path.join(BASE, "site"), HERE):
        if any(os.path.exists(os.path.join(d, n)) for n in CANDIDATES):
            return d
    return HERE


def pick_index(root):
    if os.environ.get("INDEX"):
        return os.environ["INDEX"]
    for n in CANDIDATES:
        if os.path.exists(os.path.join(root, n)):
            return n
    return CANDIDATES[0]


ROOT = pick_root()
INDEX = pick_index(ROOT)

MAX_BYTES = 3 * 1024 * 1024      # 单次响应读取上限
TIMEOUT = 20
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SKIP_HEADERS = {"host", "content-length", "connection", "origin", "referer",
                "accept-encoding", "cookie", "authorization"}


def is_blocked_host(host):
    """阻止代理访问本机/内网地址（SSRF 防护）。"""
    if not host:
        return True
    host = host.split(":")[0].strip("[]")
    if host.lower() in ("localhost", "0.0.0.0"):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        return False          # 域名放行


class Handler(SimpleHTTPRequestHandler):
    server_version = "PublicAPIPlayground/1.0"

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        sys.stdout.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))
        sys.stdout.flush()

    def translate_path(self, path):
        """让本地直跑也能提供 /scripts/ 与 /data/（服务端由 nginx 接管这两条路径）。"""
        p = urllib.parse.urlparse(path).path
        for prefix in ("/scripts/", "/data/"):
            if p.startswith(prefix):
                rel = [urllib.parse.unquote(x) for x in p[len(prefix):].split("/") if x]
                return os.path.join(BASE, prefix.strip("/"), *rel)
        return super().translate_path(path)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/proxy":
            self.handle_proxy(parsed.query)
        elif parsed.path in ("/", "/index.html"):
            self.serve_index()
        elif parsed.path == "/healthz":
            self.send_text("ok public-apis-playground\n")
        else:
            super().do_GET()

    def serve_index(self):
        path = os.path.join(ROOT, INDEX)
        if not os.path.exists(path):
            self.send_error(404, "playground html not found: %s" % path)
            return
        data = open(path, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    # ---------------- 代理 ----------------
    def handle_proxy(self, query):
        qs = urllib.parse.parse_qs(query)
        target = (qs.get("url") or [""])[0]
        if not target:
            return self.send_json({"ok": False, "error": "缺少 url 参数"})

        parsed = urllib.parse.urlparse(target)
        if parsed.scheme not in ("http", "https"):
            return self.send_json({"ok": False, "error": "仅支持 http/https"})
        if is_blocked_host(parsed.hostname):
            return self.send_json({"ok": False, "error": "禁止访问本机/内网地址"})

        headers = {"User-Agent": UA,
                   "Accept": "application/json, text/plain, */*",
                   "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
        raw_h = (qs.get("h") or [""])[0]
        if raw_h:
            try:
                extra = json.loads(base64.urlsafe_b64decode(raw_h + "==").decode("utf-8"))
                for k, v in (extra or {}).items():
                    if k.lower() not in SKIP_HEADERS and isinstance(v, str):
                        headers[k] = v
            except Exception:
                pass

        t0 = time.time()
        try:
            req = urllib.request.Request(target, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read(MAX_BYTES)
                status = resp.status
                ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
        except urllib.error.HTTPError as e:
            try:
                body = e.read(MAX_BYTES)
            except Exception:
                body = b""
            status, ctype = e.code, (e.headers.get("Content-Type") or "").split(";")[0].strip()
        except socket.timeout:
            return self.send_json({"ok": False,
                                   "error": "上游超时（%ds）" % TIMEOUT,
                                   "ms": int((time.time() - t0) * 1000)})
        except Exception as e:
            return self.send_json({"ok": False,
                                   "error": "%s: %s" % (type(e).__name__, e),
                                   "ms": int((time.time() - t0) * 1000)})

        ms = int((time.time() - t0) * 1000)
        text = None
        if ctype.startswith("text") or "json" in ctype or "xml" in ctype or not ctype:
            text = body.decode("utf-8", "replace")

        if text is None:      # 图片等二进制：转 data URI 让前端可直接显示
            b64 = base64.b64encode(body).decode("ascii")
            return self.send_json({"ok": True, "status": status, "ms": ms,
                                   "ctype": ctype, "bytes": len(body),
                                   "dataUri": "data:%s;base64,%s" % (ctype or "image/png", b64)})

        return self.send_json({"ok": True, "status": status, "ms": ms, "ctype": ctype,
                               "bytes": len(body), "body": text})

    def send_json(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, text):
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    ThreadingHTTPServer.allow_reuse_address = True
    httpd = ThreadingHTTPServer((BIND, PORT), Handler)
    url = "http://%s:%d/" % (BIND, PORT)
    print("=" * 60)
    print(" Public APIs 调试试台已启动")
    print("   页面:   %s%s" % (url, INDEX))
    print("   静态根: %s" % ROOT)
    print("   代理:   %sapi/proxy?url=<目标地址>" % url)
    print("   数据源: https://github.com/public-apis/public-apis (MIT)")
    print("   停止:   Ctrl + C")
    print("=" * 60)
    sys.stdout.flush()
    if not os.environ.get("NO_OPEN"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        httpd.shutdown()


if __name__ == "__main__":
    main()
