#!/usr/bin/env bash
# API 试炼场 TryAPI · 一键安装
# 数据来源：https://github.com/public-apis/public-apis (MIT License)
# 项目仓库：https://github.com/LambdaJoker/tryapi
#
# 用法（在部署包根目录下）：
#     DOMAIN=api.example.com bash deploy/install.sh
#
# 配置优先级：环境变量 > deploy/site.env > 自动探测
#   DOMAIN       必填，主域名
#   DOMAIN_ALT   选填，别名域名（会一起写进 server_name）
#   SERVER_IP    选填，留空则自动探测（用于自签证书的 IP SAN）
#   PORT         选填，Python 进程端口，默认 8899
#
# 做五件事：探测 python3 → 装 systemd 服务 → 自测 → 写 nginx vhost → 校验并 reload
#   其中 nginx 配置若校验失败，会自动回滚到改动前的版本，不会把站点改坏。
# 幂等：可重复执行；已存在的同名 nginx 配置会先备份。
#
# 两个环境坑（已在脚本里处理）：
#   1) systemd 的默认 PATH 不含 /opt/aiext/bin 这类自定义环境，用 `env python3`
#      会落到系统 python3.6，而 ThreadingHTTPServer 需要 3.7+ → 必须写绝对路径
#   2) 本脚本位于 <ROOT>/deploy/，包根目录是它的上一级 → 自动上溯定位

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- 读取 deploy/site.env（若存在）----
if [ -f "$SCRIPT_DIR/site.env" ]; then
  # shellcheck disable=SC1091
  . "$SCRIPT_DIR/site.env"
  echo "已读取配置 $SCRIPT_DIR/site.env"
fi

# ---- 定位包根目录 ----
if [ -f "$SCRIPT_DIR/site/index.html" ]; then
  APP_DIR="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/../site/index.html" ]; then
  APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  printf '\033[31m✗ 找不到 site/index.html，请在部署包内运行本脚本\033[0m\n' >&2
  echo "  脚本位置: $SCRIPT_DIR" >&2
  exit 1
fi

SERVICE=public-apis-playground
CONF_SRC="$SCRIPT_DIR/nginx-tryapi.conf"
PORT="${PORT:-8899}"
DOMAIN="${DOMAIN:-}"
DOMAIN_ALT="${DOMAIN_ALT:-}"
SERVER_IP="${SERVER_IP:-}"
STAMP="$(date +%Y%m%d-%H%M%S)"

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die()  { printf '\n\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" = "0" ] || die "请用 root 执行（当前非 root）"
[ -n "$DOMAIN" ] || die "请指定域名：DOMAIN=你的域名 bash deploy/install.sh
  或新建 deploy/site.env 写入：DOMAIN=你的域名"
[ -f "$APP_DIR/site/index.html" ] || die "缺少 $APP_DIR/site/index.html，请确认部署包已完整解压"
[ -f "$APP_DIR/scripts/serve.py" ] || die "缺少 $APP_DIR/scripts/serve.py"
[ -f "$CONF_SRC" ] || die "缺少 nginx 模板 $CONF_SRC"
echo "部署包根目录: $APP_DIR"
echo "目标域名:     $DOMAIN${DOMAIN_ALT:+（别名 $DOMAIN_ALT）}"

# ---------------------------------------------------------------- 1. python3
say "1/5 探测 Python 解释器（需 >= 3.7）"
detect_python() {
  for p in /opt/aiext/bin/python3 /usr/local/bin/python3 /usr/bin/python3 \
           "$(command -v python3 2>/dev/null || true)"; do
    [ -n "$p" ] && [ -x "$p" ] || continue
    if "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' 2>/dev/null; then
      printf '%s' "$p"; return 0
    fi
  done
  return 1
}

if ! PY="$(detect_python)"; then
  warn "没有 Python >= 3.7，尝试安装…"
  if command -v dnf >/dev/null 2>&1; then dnf install -y -q python3
  elif command -v yum >/dev/null 2>&1; then yum install -y -q python3
  elif command -v apt-get >/dev/null 2>&1; then apt-get update -qq && apt-get install -y -qq python3
  fi
  PY="$(detect_python)" || die "仍找不到 Python >= 3.7，请手动安装后重试"
fi
ok "选用 $PY  ($("$PY" -V 2>&1))"

for p in /opt/aiext/bin/python3 /usr/bin/python3; do
  if [ -x "$p" ] && [ "$p" != "$PY" ]; then
    warn "系统里另有 $p ($("$p" -V 2>&1))，未使用"
  fi
done

"$PY" -c "import http.server, urllib.request, ipaddress, socketserver" || die "python3 标准库不完整"
ok "标准库完整（http.server / urllib / ipaddress / socketserver，无需 pip 依赖）"

# ---------------------------------------------------------------- 2. 目录
say "2/5 整理目录"
mkdir -p "$APP_DIR/data" "$APP_DIR/scripts" "$APP_DIR/site"
chmod +x "$APP_DIR/scripts/serve.py" 2>/dev/null || true

# 把协议与说明文件同步到 site/，供 nginx 的 /README.md、/LICENSE 等路由直接访问
for f in README.md NOTICE.md LICENSE LICENSE-public-apis; do
  [ -f "$APP_DIR/$f" ] && cp -f "$APP_DIR/$f" "$APP_DIR/site/$f"
done
ok "site/ scripts/ data/ 就绪，包大小 $(du -sh "$APP_DIR" 2>/dev/null | cut -f1)"

# ---------------------------------------------------------------- 3. systemd
say "3/5 安装 systemd 服务"
sed -e "s#__PYTHON__#$PY#g" -e "s#/opt/public-apis-playground#$APP_DIR#g" \
    "$SCRIPT_DIR/$SERVICE.service" > "/etc/systemd/system/$SERVICE.service"
grep -q "^ExecStart=$PY " "/etc/systemd/system/$SERVICE.service" \
  || die "unit 里的解释器路径替换失败，请检查 $SCRIPT_DIR/$SERVICE.service"
ok "$(grep '^ExecStart=' "/etc/systemd/system/$SERVICE.service")"
systemctl daemon-reload
systemctl enable "$SERVICE" >/dev/null 2>&1 || true
systemctl restart "$SERVICE"
sleep 2
if systemctl is-active --quiet "$SERVICE"; then
  ok "服务已启动并设为开机自启"
else
  systemctl status "$SERVICE" --no-pager -l | tail -20 || true
  die "服务启动失败，用 journalctl -u $SERVICE -n 50 看日志"
fi

# ---------------------------------------------------------------- 4. 自测
say "4/5 自测（直连 127.0.0.1:$PORT）"
if "$PY" - "$PORT" <<'PYEOF'
import json, sys, urllib.parse, urllib.request
port = sys.argv[1]
r = urllib.request.urlopen("http://127.0.0.1:%s/" % port, timeout=8)
body = r.read()
assert r.status == 200 and len(body) > 10000, "首页异常"
print("    首页 HTTP %s，%.0f KB" % (r.status, len(body) / 1024))
q = "http://127.0.0.1:%s/api/proxy?url=" % port + urllib.parse.quote("https://catfact.ninja/fact", safe="")
j = json.load(urllib.request.urlopen(q, timeout=20))
assert j.get("ok"), "代理失败: %s" % j
print("    代理转发 HTTP %s，%s ms" % (j["status"], j["ms"]))
q2 = "http://127.0.0.1:%s/api/proxy?url=" % port + urllib.parse.quote("http://169.254.169.254/latest/meta-data/", safe="")
j2 = json.load(urllib.request.urlopen(q2, timeout=10))
assert not j2.get("ok"), "SSRF 防护失效！"
print("    SSRF 防护正常（云元数据地址被拒）")
PYEOF
then ok "页面 / 代理 / SSRF 三项自测通过"
else die "自测未通过，请检查 journalctl -u $SERVICE -n 50"; fi

# ---------------------------------------------------------------- 5. nginx
say "5/5 配置 nginx 站点 $DOMAIN"
if ! command -v nginx >/dev/null 2>&1; then
  warn "本机没有 nginx，跳过。可手动访问："
  echo "    curl http://127.0.0.1:$PORT/"
  echo "    systemctl status $SERVICE"
  exit 0
fi

# ---- 5.1 解析证书：优先 Let's Encrypt，找不到就自签一份顶上 ----
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  SSL_CRT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
  SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
  ok "使用 Let's Encrypt 证书：$SSL_CRT"
else
  SSL_CRT="/etc/nginx/ssl/$DOMAIN.crt"
  SSL_KEY="/etc/nginx/ssl/$DOMAIN.key"
  if [ -f "$SSL_CRT" ] && [ -f "$SSL_KEY" ]; then
    ok "复用已有自签证书：$SSL_CRT"
  else
    command -v openssl >/dev/null 2>&1 || die "既没有 Let's Encrypt 证书，也没有 openssl 可生成自签证书"
    mkdir -p /etc/nginx/ssl
    [ -z "$SERVER_IP" ] && SERVER_IP="$(curl -s --max-time 5 https://api64.ipify.org 2>/dev/null \
      || curl -s --max-time 5 http://members.3322.org/dyndns/getip 2>/dev/null || echo '')"
    SAN="DNS:$DOMAIN"
    [ -n "$DOMAIN_ALT" ] && SAN="$SAN,DNS:$DOMAIN_ALT"
    [ -n "$SERVER_IP" ] && SAN="$SAN,IP:$SERVER_IP"
    if openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
         -keyout "$SSL_KEY" -out "$SSL_CRT" -subj "/CN=$DOMAIN" \
         -addext "subjectAltName=$SAN" >/dev/null 2>&1; then
      ok "已生成自签证书（SAN: $SAN）"
    else
      # openssl < 1.1.1 不支持 -addext，退回不带 SAN 的写法
      openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
        -keyout "$SSL_KEY" -out "$SSL_CRT" -subj "/CN=$DOMAIN" >/dev/null 2>&1 \
        || die "自签证书生成失败"
      warn "openssl 版本较旧，证书不含 SAN（浏览器仍会提示不安全）"
    fi
    warn "这是自签证书，浏览器会提示不安全；域名解析可用后建议签 Let's Encrypt（见 deploy/README.md）"
  fi
fi

# ---- 5.2 写入 vhost ----
CONF_DIR=""; LINK_DIR=""
for d in /etc/nginx/conf.d /usr/local/nginx/conf/conf.d; do
  [ -d "$d" ] && CONF_DIR="$d" && break
done
if [ -z "$CONF_DIR" ] && [ -d /etc/nginx/sites-available ]; then
  CONF_DIR="/etc/nginx/sites-available"; LINK_DIR="/etc/nginx/sites-enabled"
fi
[ -n "$CONF_DIR" ] || die "找不到 nginx 配置目录，请手动把 deploy/nginx-tryapi.conf 放进配置目录"

TARGET="$CONF_DIR/$DOMAIN.conf"
ROLLBACK=""
if [ -f "$TARGET" ]; then
  ROLLBACK="$TARGET.bak-$STAMP"
  cp -a "$TARGET" "$ROLLBACK"
  warn "已备份原配置 → $ROLLBACK"
fi

sed -e "s#__DOMAIN__#$DOMAIN#g" \
    -e "s#__DOMAIN_ALT__#$DOMAIN_ALT#g" \
    -e "s#__SSLCERT__#$SSL_CRT#g" \
    -e "s#__SSLKEY__#$SSL_KEY#g" \
    -e "s#/opt/public-apis-playground#$APP_DIR#g" \
    "$CONF_SRC" > "$TARGET"
ok "写入 $TARGET"

if [ -n "$LINK_DIR" ]; then
  mkdir -p "$LINK_DIR"
  ln -sfn "$TARGET" "$LINK_DIR/$DOMAIN.conf"
  ok "已启用软链 $LINK_DIR/$DOMAIN.conf"
fi

# ---- 5.3 校验，失败自动回滚 ----
if nginx -t 2>&1 | tee /tmp/nginx-test.log | grep -q "successful"; then
  ok "nginx -t 通过"
  systemctl reload nginx 2>/dev/null || nginx -s reload
  ok "nginx 已 reload"
else
  echo "--- nginx -t 输出 ---"; cat /tmp/nginx-test.log
  if [ -n "$ROLLBACK" ]; then
    cp -a "$ROLLBACK" "$TARGET"
    warn "已自动回滚到改动前的配置，站点应仍可用"
  else
    rm -f "$TARGET"
    [ -n "$LINK_DIR" ] && rm -f "$LINK_DIR/$DOMAIN.conf"
    warn "已移除本次写入的配置"
  fi
  die "nginx 配置校验失败，站点未变更"
fi

# ---------------------------------------------------------------- 结果
printf '\n\033[1;32m部署完成\033[0m\n'
echo  "  站点       http://$DOMAIN/"
[ -n "$DOMAIN_ALT" ] && echo "  别名       http://$DOMAIN_ALT/（DNS 生效即可用）"
echo  "  HTTPS      https://$DOMAIN/$([ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] || echo '   ← 自签证书，浏览器会提示不安全')"
echo  "  源码下载   http://$DOMAIN/scripts/"
echo  "  数据集     http://$DOMAIN/data/"
echo  "  协议文件   http://$DOMAIN/LICENSE"
echo  "  健康检查   http://$DOMAIN/healthz"
echo
echo  "  服务管理   systemctl {status,restart,stop} $SERVICE"
echo  "  日志       journalctl -u $SERVICE -f"
echo  "  自查       curl -H 'Host: $DOMAIN' http://127.0.0.1/healthz"
echo
echo  "  项目仓库   https://github.com/LambdaJoker/tryapi"
echo  "  数据来源   https://github.com/public-apis/public-apis (MIT License)"
