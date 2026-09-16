# ⚡ API 试炼场 TryAPI · 部署包

> **数据来源：本项目全部 1826 个接口条目均摘自 [public-apis/public-apis](https://github.com/public-apis/public-apis)（MIT License）**
> 原仓库是社区维护的免费 API 合集（⭐ 480k+）。本部署包在其之上增加了「可用性实测数据 + 一键调用调试台」，
> 未对原始数据做任何删改。
>
> 项目名：**API 试炼场（TryAPI）** —— 1826 个公开 API，点一下就看到真实返回。
> 完整项目说明与免责声明见上一级 `README.md`。

技术栈：nginx（静态托管 + 反向代理）+ systemd（进程守护）+ Python 标准库（CORS 代理）。
本项目开源仓库：<https://github.com/LambdaJoker/tryapi>

---

## 一、目录结构

```
/opt/public-apis-playground/
├── site/
│   ├── index.html              # 调试试台单页（内嵌 1826 条数据 + 57 条精选）
│   ├── README.md               # 项目说明副本（nginx 暴露为 /README.md）
│   ├── NOTICE.md               # 来源与许可声明（暴露为 /NOTICE.md）
│   └── LICENSE(-public-apis)   # 协议全文（暴露为 /LICENSE）
├── scripts/                    # 全套 Python 源码（nginx 暴露为 /scripts/ 可下载）
│   ├── serve.py                # 本地/服务端服务：静态页 + /api/proxy 跨域转发
│   ├── parse_public_apis.py    # 解析 README 表格 → public_apis.json
│   ├── export_public_apis.py   # 导出 xlsx / csv / md / json
│   ├── probe_apis.py           # 全量 798 个免鉴权接口的可用性探测
│   ├── curated_endpoints.py    # 75 个精选端点的实测（含 CORS 判定）
│   └── build_html_v2.py        # 生成本页的调试试台 HTML
├── data/                       # 中间产物与导出数据集
├── deploy/                     # install.sh / nginx 模板 / unit / site.env
└── README.md                   # 本文件
```

部署相关文件说明：

| 文件 | 作用 |
|---|---|
| `deploy/install.sh` | 一键安装（探测 Python → systemd → 自测 → nginx → reload） |
| `deploy/nginx-tryapi.conf` | nginx vhost **模板**，占位符由 install.sh 替换 |
| `deploy/public-apis-playground.service` | systemd unit 模板 |
| `deploy/site.env.example` | 部署配置样例，复制为 `site.env` 后填写域名 |
| `deploy/site.env` | 本机实际配置（**不入库**，见 `.gitignore`） |

`site/` 下的 `README.md` / `NOTICE.md` / `LICENSE` 由 install.sh 从包根自动复制，
这样浏览器可以直接访问 `/README.md`、`/NOTICE.md`、`/LICENSE` 看协议原文。

## 二、运行架构

```
浏览器 ──HTTP(S)──> nginx (80/443)
                     ├── /            → site/index.html（静态，gzip）
                     ├── /README.md   → 项目说明（text/plain）
                     ├── /scripts/    → scripts/*.py（可直接下载）
                     ├── /data/       → 数据集（可直接下载）
                     ├── /healthz     → 本机健康检查
                     └── /api/proxy   → 127.0.0.1:8899 (serve.py)
                                          └── 服务端转发上游 API
```

**端口**：Python 进程只监听 `127.0.0.1:8899`（本地回环，不对外暴露）；对外统一走 nginx 的
`80 / 443`。部署前建议先 `ss -lntp` 看一眼 8899 是否被占用，若冲突改 `deploy/*.service`
与 nginx vhost 里的端口号即可（两处保持一致）。

**为什么需要 Python 进程**：浏览器直接调第三方 API 会同时受两道限制 ——
上游没开 CORS + 页面所在地的 CSP `default-src 'self'`。
`serve.py` 在服务端转发请求，**同时绕过这两道限制**，连「未开放跨域」的接口也能调通。

**页面布局 · 贴底页脚**：`body` 是纵向 flex 容器、`.layout` 占 `flex:1 0 auto`、
`footer.src` 用 `margin:auto auto 0` 兜底。效果是——
内容不足一屏时页脚贴在视口最底部（中间留白），内容超一屏时页脚自然跟在内容末尾。
`footer` 是 `body` 的直接子元素，`.mask` / `.toast` / `.drawer` 都是 `position:fixed`，不参与该 flex 流。

## 三、部署步骤

### 1. 打包（本地执行，仓库根目录下）

```bash
bash pack.sh        # 生成 deploy/public-apis-playground.tar.gz
```

### 2. 配置域名

```bash
cp deploy/public-apis-playground/deploy/site.env.example \
   deploy/public-apis-playground/deploy/site.env
# 编辑 site.env：填 DOMAIN（必填）、DOMAIN_ALT / SERVER_IP / PORT（选填）
```

`site.env` 已在 `.gitignore` 里，域名和服务器 IP 不会进仓库。
也可以临时用环境变量覆盖：`DOMAIN=api.example.com bash deploy/install.sh`。

### 3. 上传 + 安装

```bash
# 本地执行，把 <SERVER_IP> 换成你的服务器地址
scp public-apis-playground.tar.gz root@<SERVER_IP>:/tmp/

# 服务器执行
ssh root@<SERVER_IP>
mkdir -p /opt && tar -xzf /tmp/public-apis-playground.tar.gz -C /opt/
cd /opt/public-apis-playground && bash deploy/install.sh
```

`install.sh` 会做五件事：探测 Python（必须 ≥3.7，且把**绝对路径**写进 systemd unit）→ 安装 systemd 服务
→ 自测「页面 / 代理 / SSRF 三项」→ 写入 nginx vhost → `nginx -t` 通过后 reload。

几个安全设计：

- **`nginx -t` 失败会自动回滚**到改动前的配置（首次安装则删除本次写入的 vhost），不会把在线站点改坏
- **证书自动降级**：优先用 `/etc/letsencrypt/live/<域名>/`，找不到就生成一份自签证书
  （SAN 含域名与服务器 IP）先顶上，浏览器提示不安全时点「继续访问」即可
- **幂等**：可重复执行，旧配置会先备份为 `<域名>.conf.bak-<时间戳>`

> ⚠️ 踩坑记录：不能用 `ExecStart=/usr/bin/env python3`。systemd 的默认 PATH 不含
> `/opt/aiext/bin` 这类自定义环境，会落到系统的 python3.6，而 `ThreadingHTTPServer` 需要 3.7+。
> `serve.py` 里已加 3.6 兼容分支，`install.sh` 会自动探测绝对路径并替换 unit 里的 `__PYTHON__` 占位符。

> ⚠️ 端口冲突：本站 Python 进程只监听 `127.0.0.1:8899`。机器上已有服务占用时，
> 改 `site.env` 的 `PORT` 即可（vhost 里的 `proxy_pass` 端口由模板变量带入，无需手工改两处）。
> 部署前建议先 `ss -lntp | grep 8899` 确认。

## 四、验证

```bash
systemctl status public-apis-playground     # 服务应为 active (running)
curl -s http://127.0.0.1:8899/healthz                                  # ok public-apis-playground
curl -s http://127.0.0.1:8899/api/proxy?url=https://catfact.ninja/fact # 代理自测
curl -s http://127.0.0.1/healthz                                       # 本机 nginx 入口
curl -s -H 'Host: <你的域名>' http://127.0.0.1/healthz                  # 按域名路由自测
```

自测覆盖项：

| 项目 | 预期 |
|---|---|
| `/` 首页 | 200，单文件 HTML（约 480 KB） |
| `/api/proxy` → 公开接口 | `ok=true`，返回真实 JSON + 耗时 |
| `/api/proxy` → `169.254.169.254` | 被拦截，提示 `禁止访问本机/内网地址` |
| `/scripts/serve.py` | 200，源码可直接下载 |
| `/README.md`、`/NOTICE.md`、`/LICENSE` | 200，`text/plain`，浏览器内直接可读 |
| `/healthz` | 200，`ok public-apis-playground` |

## 五、HTTPS 证书（可选）

站点默认只监听 80 端口也能跑。要上 HTTPS，先把域名解析到服务器，然后：

```bash
# 1. 签证书（webroot 挑战，nginx 里已留好 /.well-known/acme-challenge/ 的 location）
certbot certonly --webroot -w /var/www/certbot -d <你的域名>

# 2. 改 nginx vhost 的 443 块
#    ssl_certificate     /etc/letsencrypt/live/<你的域名>/fullchain.pem;
#    ssl_certificate_key /etc/letsencrypt/live/<你的域名>/privkey.pem;
nginx -t && systemctl reload nginx
```

> 80 端口被上游服务商拦截、拿不到挑战文件时，可改用 **DNS-01 挑战**
> （`certbot certonly --manual --preferred-challenges dns -d <你的域名>`，在 DNS 服务商加一条 TXT 记录）。

## 六、数据与许可

| 内容 | 归属 | 许可 |
|---|---|---|
| 1826 条接口清单、分类、说明、鉴权/HTTPS/CORS 标记 | [public-apis/public-apis](https://github.com/public-apis/public-apis) | MIT（全文见 `LICENSE-public-apis`） |
| 本项目代码、界面、代理服务、实测结果 | 本项目 | MIT（全文见 `LICENSE`） |
| 各第三方 API 提供的内容与配额 | 各自提供方 | 遵循其各自条款 |

完整声明见仓库根目录 [`NOTICE.md`](../NOTICE.md)。要点：

- 原数据**原样保留**，未做任何删除、修改或重新排序；本项目的补充内容不影响原仓库的 MIT 许可
- 本项目**不代理业务数据**：请求由浏览器或你自己运行的 `serve.py` 直接发往目标 API
- 实测结果（响应码 / 耗时）是**特定时间点的一次性快照**，接口可能随时限流或下线
- 标注需鉴权（`apiKey` / `OAuth` / `X-Mashape-Key`）的接口需自行申请凭据
- 本项目按「现状」提供，不对数据完整性与可用性作任何担保

部署完成后，这几个文件可以直接在浏览器里访问：

```text
https://<你的域名>/README.md              项目说明与数据来源
https://<你的域名>/NOTICE.md              来源与许可声明（要读就读这份）
https://<你的域名>/LICENSE                本项目 MIT 全文
https://<你的域名>/LICENSE-public-apis    上游 MIT 全文
```

## 七、本地也跑得起来

```bash
python3 scripts/serve.py 8899        # 默认 127.0.0.1:8899，会自动开浏览器
python3 scripts/build_html_v2.py     # 重新生成 site/index.html（需先备好 data/）
```

`serve.py` 支持环境变量：`NO_OPEN=1` 不开浏览器，`BIND=0.0.0.0` 改监听地址，`INDEX=` 指定首页。
