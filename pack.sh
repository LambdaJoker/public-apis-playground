#!/usr/bin/env bash
# 打包部署包：deploy/public-apis-playground/  →  deploy/public-apis-playground.tar.gz
#
# 用法（仓库根目录下）：
#     bash pack.sh
#
# 产物不入库（见 .gitignore），需要时随时重新生成。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/deploy/public-apis-playground"
OUT="$ROOT/deploy/public-apis-playground.tar.gz"

[ -d "$SRC" ] || { echo "✗ 找不到 $SRC"; exit 1; }

# 打包前做一次基本体检，避免把半成品打进去
for f in site/index.html scripts/serve.py deploy/install.sh deploy/nginx-tryapi.conf; do
  [ -f "$SRC/$f" ] || { echo "✗ 部署包缺少 $f，请检查"; exit 1; }
done

# ---- 在临时目录里统一换行为 LF 后再打包 ----
# Windows 上编辑过的文件很可能是 CRLF，直接打进 tar 会让 install.sh / *.service
# 在 Linux 上报 `\r: command not found` 之类的错。这里做一次归一化，源文件不动。
TMP="$(mktemp -d 2>/dev/null || mktemp -d -t tryapi)"
# Windows 上 rm 可能被安全软件/沙箱包一层，清理失败不应影响打包结果
trap 'rm -rf "$TMP" 2>/dev/null || true' EXIT INT TERM
cp -a "$SRC" "$TMP/"

if command -v python3 >/dev/null 2>&1; then PY3=python3
elif command -v python >/dev/null 2>&1; then PY3=python
else PY3=""; fi

if [ -n "$PY3" ]; then
  "$PY3" - "$TMP/public-apis-playground" <<'PYEOF'
import os, sys
ROOT = sys.argv[1]
EXT = {'.sh', '.py', '.conf', '.md', '.service', '.example', '.env',
       '.txt', '.json', '.csv', '.html', '.gitignore'}
NAMES = {'.gitignore', 'LICENSE', 'LICENSE-public-apis', 'site.env'}
fixed = 0
for base, _dirs, files in os.walk(ROOT):
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in EXT and fn not in NAMES:
            continue
        p = os.path.join(base, fn)
        with open(p, 'rb') as f:
            raw = f.read()
        if b'\r\n' in raw:
            with open(p, 'wb') as f:
                f.write(raw.replace(b'\r\n', b'\n'))
            fixed += 1
print("    换行归一化：%d 个文件转为 LF" % fixed)
PYEOF
else
  echo "  ! 未找到 python，跳过换行归一化（Windows 上打包可能带 CRLF）"
fi

rm -f "$OUT"
tar -czf "$OUT" -C "$TMP" public-apis-playground

SIZE="$(du -h "$OUT" | cut -f1)"
if command -v md5sum >/dev/null 2>&1; then
  SUM="$(md5sum "$OUT" | cut -d' ' -f1)"
elif command -v md5 >/dev/null 2>&1; then
  SUM="$(md5 -q "$OUT")"
else
  SUM="(无 md5 工具)"
fi

echo "✓ 已生成 $OUT"
echo "  大小 $SIZE   md5 $SUM"
echo
echo "上传并安装："
echo "  scp \"$OUT\" root@<SERVER_IP>:/tmp/"
echo "  ssh root@<SERVER_IP> 'mkdir -p /opt && tar -xzf /tmp/public-apis-playground.tar.gz -C /opt/ && cd /opt/public-apis-playground && bash deploy/install.sh'"
