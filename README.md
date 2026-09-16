<div align="center">

# ⚡ API 试炼场 · Public APIs Playground

**1826 个公开 API，点一下就看到真实返回。**

不用写代码、不用装 SDK、不用配 Postman —— 打开页面，搜索、筛选、点「调用」，
原始 JSON 会就地渲染成表格 / 卡片 / 图片。

[![条目](https://img.shields.io/badge/API%20%E6%9D%A1%E7%9B%AE-1826-4ade80?style=flat-square)](#-数据规模)
[![精选可直连](https://img.shields.io/badge/%E7%B2%BE%E9%80%89%E5%8F%AF%E7%9B%B4%E8%BF%9E-57-60a5fa?style=flat-square)](#-数据规模)
[![实测](https://img.shields.io/badge/%E5%8F%AF%E7%94%A8%E6%80%A7%E5%AE%9E%E6%B5%8B-2026--09-4ade80?style=flat-square)](#-数据规模)
[![数据来源](https://img.shields.io/badge/%E6%95%B0%E6%8D%AE%E6%9D%A5%E6%BA%90-public--apis%2Fpublic--apis-ff69b4?style=flat-square)](https://github.com/public-apis/public-apis)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](#-许可)
[![仓库](https://img.shields.io/badge/GitHub-LambdaJoker%2Fpublic-apis-playground-181717?style=flat-square)](https://github.com/LambdaJoker/public-apis-playground)

**开源仓库** <https://github.com/LambdaJoker/public-apis-playground> · **数据来源** <https://github.com/public-apis/public-apis>

单文件交付 · 零依赖 · 数据全部内嵌

</div>

---

## 📖 目录

| | |
|---|---|
| [🎯 这是什么](#-这是什么) | [✨ 核心能力](#-核心能力) |
| [🚀 快速开始](#-快速开始) | [📊 数据规模](#-数据规模) |
| [⚖️ 数据来源与声明](#️-数据来源与声明) | [🗂 项目结构](#-项目结构) |
| [🛠 技术实现](#-技术实现) | [🔗 仓库与许可](#-仓库与许可) |
| [📜 许可](#-许可) | |

---

## 🎯 这是什么

**API 试炼场（Public APIs Playground）** 是一个**纯前端 + 轻量代理**的公开 API 浏览器与实测台。

它把 [public-apis/public-apis](https://github.com/public-apis/public-apis) 这份社区维护的免费 API 合集
（1826 条、52 个分类）从「一张静态清单」变成了「**能直接点出结果的工作台**」：

```text
传统做法                          本项目的做法
─────────────────────────────    ─────────────────────────────
翻 README 表格找接口         →    搜索 / 分类筛选，命中数实时显示
复制 URL 到 Postman          →    卡片上直接点「▷ 调用」
手动替换 {owner} 之类的占位符 →    点「🔧 参数」按提示填，自动拼接并编码
盯着原始 JSON 找字段         →    自动渲染成表格 / 卡片 / 图片
发现接口其实早就挂了         →    每条都带实测响应码与耗时
```

---

## ✨ 核心能力

| 能力 | 说明 |
|---|---|
| 🔍 **毫秒级检索** | 搜索同时匹配接口名、说明、分类的中英文与 URL（空格分词，多词 AND） |
| 🎛 **多维筛选** | 按可调用性（可调用 / 可直连 / 需代理 / 图片 / 文档页 / 需鉴权）、鉴权方式、响应速度排序 |
| ⚡ **一键调用** | 卡片上点一下即发请求，结果在**居中弹窗**里展开，不跳页、不开新窗口，也不把卡片撑高 |
| 🗂 **结果弹窗** | 卡片只留一行紧凑状态（HTTP 状态码 / 耗时 / 体积），完整结果进弹窗：内部可切「✨ 渲染结果 / 原始 JSON」，支持复制、下载、跳调试台 |
| 🕘 **调用历史** | 顶部工具条带条数徽章，关掉弹窗后可随时点开历史里任意一条重新查看；**只存页面内存，刷新即全部释放** |
| 🔧 **参数懒展开** | 带 `{owner}` 这类路径参数的接口，参数框**默认收起**，点「🔧 参数」才展开，避免界面被空输入框塞满 |
| 🧠 **智能渲染** | 自动识别响应形态：顶层数组 → 全量表格；图片 URL → 看图；嵌套对象 → 展平成字段表；文本 → 正文 + 其余字段 |
| 🛡 **CORS 逃生通道** | 上游没开 CORS？服务端 `/api/proxy` 同源转发，把「未开放跨域」的接口也调通 |
| 🔒 **SSRF 防护** | 代理层拒绝本机、内网、link-local（含云元数据 `169.254.169.254`）等地址 |
| 📦 **数据可带走** | 全套 Python 源码与数据集在线可下载（`/scripts/`、`/data/`） |

---

## 🚀 快速开始

### 方式一：直接打开页面

双击 `public-apis-API调试试台.html`（或 Windows 下双击「启动调试台.bat」）即可打开。
HTML / CSS / JS / 1826 条数据全部内嵌在同一个文件里，**不联网也能浏览、搜索、筛选**。

> 此方式下点「调用」会受浏览器跨域策略限制，只能调通已开放 CORS 的接口。
> 想调通全部接口，用下面的方式二。

### 方式二：本地起服务（推荐）

```bash
python3 serve.py
```

零第三方依赖（仅 Python 标准库），启动后同时提供两个入口：

```text
http://127.0.0.1:8899/            页面
http://127.0.0.1:8899/api/proxy   CORS 代理（解锁全部接口）
```

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| `BIND` | `127.0.0.1` | 监听地址，设 `0.0.0.0` 可局域网访问 |
| `NO_OPEN` | — | 设 `1` 则不自动打开浏览器 |
| `INDEX` | 自动探测 | 指定首页文件 |
| `PAP_BASE` | 脚本上级目录 | 数据集所在根目录 |

### 重新生成页面

```bash
python3 scripts/build_html_v2.py     # 读 data/ 下的数据集 → 产出 site/index.html
```

---

## 📊 数据规模

| 指标 | 数量 | 说明 |
|---|---:|---|
| **接口总条目** | **1826** | 全部来自原仓库 README 表格 |
| 分类数 | 52 | 含中文对照名 |
| ⚡ 精选可直连 | 57 | 免鉴权、实测可用，页面首页展示 |
| ✅ 可调用 | 24 | 17 个可直连 + 7 个需代理 |
| 🖼 图片类 | 0 | 当前精选集中无纯图片接口 |
| 📄 文档页 | 540 | 非数据端点（官网 / 控制台 / SDK 页） |
| ❌ 实测不可用 | 234 | 超时 / 5xx / 已下线 |
| ⏳ 未实测 | 65 | 需鉴权或需人工确认，未纳入自动探测 |

<details>
<summary><b>接口数最多的 10 个分类</b>（点击展开）</summary>

| # | 分类 | 条目 |
|---:|---|---:|
| 1 | Development | 169 |
| 2 | Government | 108 |
| 3 | Games & Comics | 103 |
| 4 | Geocoding | 99 |
| 5 | Cryptocurrency | 82 |
| 6 | Transportation | 82 |
| 7 | Finance | 76 |
| 8 | Open Data | 58 |
| 9 | Social | 54 |
| 10 | Security | 49 |

</details>

> **实测方式**：带 `Origin` 头发起探测，判定标准 = HTTP 200 + 返回 JSON + 存在
> `Access-Control-Allow-Origin`。图片类接口单独用 `<img>` 探测（图片请求不受 CORS 限制）。
> 实测完成于 **2026 年 9 月**，是一次性快照。

---

## ⚖️ 数据来源与声明

### 数据来源

> **本项目全部 1826 条接口条目，均来自开源仓库 [public-apis/public-apis](https://github.com/public-apis/public-apis)（MIT License）。**
>
> 原仓库是社区维护的免费 API 合集（⭐ 480k+），本项目通过**解析其 README 中的 Markdown 表格**获取数据，
> 取用其**分类、接口名、说明、鉴权方式、HTTPS 支持、CORS 支持**六列。

### 哪些是原仓库的，哪些是本项目补充的

| 内容 | 归属 |
|---|---|
| 1826 条接口清单：分类 / 名称 / 说明 / 鉴权 / HTTPS / CORS | ✅ 原仓库 [public-apis/public-apis](https://github.com/public-apis/public-apis)，MIT License |
| 可用性实测结果（响应码 / 耗时 / Content-Type / CORS 判定） | 🔧 本项目补充，2026-09 实测 |
| 分类中文译名、界面、渲染逻辑、代理服务 | 🔧 本项目补充 |
| 各第三方 API 提供的内容、配额与使用条款 | ✅ 归各 API 提供方所有 |

### 正式声明

1. **未改动原始数据。** 原仓库的 1826 条条目、分类结构、说明文字均**原样保留，未做任何删除、修改或重新排序**。
2. **补充内容不影响原许可。** 中文分类名、实测数据与界面实现仅作**便利性呈现**，
   **不改变原仓库的数据内容与其 MIT 许可条款**。
3. **数据归属清晰。** 原数据版权归 public-apis 社区贡献者所有；本项目仅进行格式转换与展示。
4. **第三方接口独立。** 各接口的内容、可用性、调用配额、隐私政策与使用条款均归其各自提供方所有。
   使用前请阅读对应提供方的服务协议与所在地区法律法规。
5. **本项目不代理、不缓存、不存储任何接口业务数据。** 所有请求由你的浏览器或你自行运行的
   `serve.py` 直接发往目标 API；本项目不落库、不转发给任何第三方、不做统计分析。
6. **需鉴权的接口需自备凭据。** 原仓库中标注 `apiKey` / `OAuth` / `X-Mashape-Key` 的接口，
   需自行到对应平台申请密钥后方可调用。
7. **实测结果有时效性。** 页面上的响应码与耗时是**特定时间点的一次性快照**，
   不代表该接口当前或未来的状态。接口随时可能限流、改版或下线，请以官方文档为准。
8. **不构成任何担保。** 本项目按「现状」提供，不对数据的完整性、准确性、可用性作任何明示或默示担保。
   因使用本项目产生的任何直接或间接损失，作者不承担责任。
9. **合规使用。** 请遵守各 API 提供方的调用频率限制与使用条款，勿将其用于违法违规用途。

---

## 🗂 项目结构

```text
public-apis-playground/
├── README.md                        # 本文件
├── NOTICE.md                        # ⚖️ 来源与许可声明（要读就读这份）
├── LICENSE                          # 本项目 MIT 许可全文
├── LICENSE-public-apis              # 上游 public-apis 的 MIT 许可全文
├── .gitignore
├── pack.sh                          # 打包部署 tar.gz
├── public-apis-API调试试台.html      # ⚡ 主产物：单文件调试试台（内嵌全部数据，可直接打开）
├── public-apis-API检索台.html        # 早期版本：纯检索台（无调用能力）
├── public-apis-按用途分类.json       # 按分类组织的 1826 条数据（页面数据源）
├── public-apis-按用途分类.md         # 同上，Markdown 版
├── public-apis-全部API清单.csv       # 扁平清单
├── public-apis-全部API清单.xlsx      # 扁平清单（Excel）
├── serve.py                         # 本地服务：静态页 + /api/proxy 跨域转发
├── 启动调试台.bat                    # Windows 一键启动
└── deploy/
    ├── public-apis-playground.tar.gz        # 部署包（`bash pack.sh` 生成，不入库）
    └── public-apis-playground/
        ├── site/index.html                  # 部署用页面
        ├── scripts/                         # 全套 Python 源码（含数据流水线）
        │   ├── serve.py                     #   服务 + 代理（含 SSRF 防护）
        │   ├── build_html_v2.py             #   生成调试试台 HTML
        │   ├── parse_public_apis.py         #   解析原仓库 README 表格
        │   ├── export_public_apis.py        #   导出 xlsx / csv / md / json
        │   ├── probe_apis.py                #   全量免鉴权接口可用性探测
        │   └── curated_endpoints.py         #   精选端点实测（含 CORS 判定）
        ├── data/                            # 数据集与探测结果
        ├── deploy/                          # install.sh / nginx 模板 / systemd unit / site.env
        │   ├── install.sh                   #   一键安装（含失败自动回滚）
        │   ├── nginx-playground.conf            #   nginx vhost 模板（占位符由脚本替换）
        │   ├── site.env.example             #   部署配置样例 → 复制为 site.env
        │   └── public-apis-playground.service
        └── README.md                        # 部署与运维说明
```

---

## 🛠 技术实现

### 架构

```text
浏览器 ──> 静态单页（HTML + CSS + JS + 1826 条数据全部内嵌）
             │
             └── /api/proxy ──> serve.py（服务端转发）──> 目标 API
```

**为什么需要一个代理进程？**
浏览器直接调第三方 API 会同时撞上两道墙 —— ① 上游没开 CORS；② 页面自身的 CSP `default-src 'self'`。
`serve.py` 在服务端转发，**一次绕过这两道限制**，于是连「未开放跨域」的接口也能调通。
不想要代理时，纯静态页面也能独立工作。

### 前端

- **单文件交付**：HTML / CSS / JS / 全部数据内嵌，零构建、零依赖、零外部请求（除被调用的 API 本身）
- **智能渲染分流**：按响应形态走 5 条分支 —— 顶层数组 / 纯图片 / 图片+结构化 / 文本为主 / 纯结构化
- **扁平化渲染**：对象展平成 `a.b.c` 字段表，数组渲染成全量表格（所有元素、列取并集），
  单次最多 400 行 / 20 列，超出部分提示查看原始 JSON
- **贴底页脚**：`body` 为纵向 flex 容器，内容不足一屏时页脚贴视口底部，超出时自然跟随
- **结果弹窗 + 会话历史**：调用的完整结果走居中弹窗（响应再大也不挤压卡片布局），
  历史记录只保留在内存数组中——不写 `localStorage` / `sessionStorage`，刷新页面即清空，
  不在本机留下任何调用痕迹；弹窗支持遮罩点击 / ✕ / `Esc` 三种关闭方式

### 后端

- 仅标准库：`http.server.ThreadingHTTPServer`，无第三方依赖
- **SSRF 防护**：解析目标主机后拒绝本机 / 私网 / link-local / 保留地址，含 `169.254.169.254` 云元数据端点
- 二进制响应自动转 data URI 返回；`/healthz` 健康检查
- 可当作常驻服务部署（`deploy/` 内提供 systemd unit 与一键安装脚本）

---

## 🔗 仓库与许可

| | 仓库地址 | 说明 |
|---|---|---|
| **本项目** | <https://github.com/LambdaJoker/public-apis-playground> | API 试炼场 全部源码：页面生成器、CORS 代理、数据流水线、部署包 |
| **数据来源** | <https://github.com/public-apis/public-apis> | 1826 条接口条目的原始仓库（分类 / 说明 / 鉴权 / HTTPS / CORS） |

两个仓库都是 **MIT License**，可以自由使用、修改、分发（保留版权声明即可）。
页面页脚也展示了这两个地址与协议入口，部署后可直接在线查看协议全文：

```text
https://<你的域名>/README.md              项目说明与数据来源
https://<你的域名>/NOTICE.md              来源与许可声明（要读就读这份）
https://<你的域名>/LICENSE                本项目 MIT 全文
https://<你的域名>/LICENSE-public-apis    上游 MIT 全文
```

---

## 📜 许可

| 对象 | 许可 | 全文 |
|---|---|---|
| 本项目代码、界面、代理服务、文档 | **MIT License** | [`LICENSE`](LICENSE) |
| 接口数据（1826 条） | **MIT License**（归 public-apis 社区） | [`LICENSE-public-apis`](LICENSE-public-apis) |
| 各第三方 API 内容 | 归各提供方所有，遵循其各自条款 | 见各提供方官网 |

原仓库版权归其社区贡献者所有：<https://github.com/public-apis/public-apis/blob/master/LICENSE>

> 完整的来源说明、许可范围划分与免责条款见 **[`NOTICE.md`](NOTICE.md)**。

---

<div align="center">

**API 试炼场 · Public APIs Playground** ·
[github.com/LambdaJoker/public-apis-playground](https://github.com/LambdaJoker/public-apis-playground) ·
数据源自 [public-apis/public-apis](https://github.com/public-apis/public-apis) ·
共 1826 个接口 · 精选可直连 57 个 · MIT License

<sub>Made with ⚡ by WorkBuddy</sub>

</div>
