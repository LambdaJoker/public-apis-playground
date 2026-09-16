# -*- coding: utf-8 -*-
"""生成 public-apis 可调用调试台：一键调用 + 智能结果渲染 + 全量清单。

数据来源：https://github.com/public-apis/public-apis  (MIT License)

用法：  python3 scripts/build_html_v2.py
输出：  site/index.html
路径约定（部署包结构，可用环境变量覆盖）：
        <BASE>/data/  输入数据      <BASE>/site/  输出页面
        PAP_BASE 覆盖 BASE
"""
import json
import os

# ---- 路径解析：脚本在 <BASE>/scripts/ 下，数据在 <BASE>/data/，页面输出到 <BASE>/site/ ----
_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("PAP_BASE") or os.path.dirname(_HERE)
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")

SRC = os.environ.get("PAP_SRC") or os.path.join(DATA, "public-apis-按用途分类.json")
PROBE = os.environ.get("PAP_PROBE") or os.path.join(DATA, "probe_results.json")
OUT = os.environ.get("PAP_OUT") or os.path.join(SITE, "index.html")

ZH = {
    "Animals": "动物", "Anime": "动漫", "Anti-Malware": "反恶意软件", "Art & Design": "艺术设计",
    "Authentication & Authorization": "认证授权", "Blockchain": "区块链", "Books": "图书",
    "Business": "商业", "Calendar": "日程日历", "Cloud Storage & File Sharing": "云存储与文件分享",
    "Continuous Integration": "持续集成", "Cryptocurrency": "加密货币", "Currency Exchange": "汇率",
    "Data Validation": "数据校验", "Development": "开发工具", "Dictionaries": "词典",
    "Documents & Productivity": "文档与效率", "Email": "邮件", "Entertainment": "娱乐",
    "Environment": "环境", "Events": "活动事件", "Finance": "金融", "Food & Drink": "餐饮",
    "Games & Comics": "游戏漫画", "Geocoding": "地理编码", "Government": "政务",
    "Health": "健康", "Jobs": "招聘", "Machine Learning": "机器学习", "Music": "音乐",
    "News": "新闻", "Open Data": "开放数据", "Open Source Projects": "开源项目",
    "Patent": "专利", "Personality": "性格分析", "Phone": "电话", "Photography": "摄影",
    "Programming": "编程", "Science & Math": "科学数学", "Security": "安全", "Shopping": "购物",
    "Social": "社交", "Sports & Fitness": "运动健身", "Test Data": "测试数据",
    "Text Analysis": "文本分析", "Tracking": "物流追踪", "Transportation": "交通",
    "URL Shorteners": "短链接", "Vehicle": "车辆", "Video": "视频", "Weather": "天气",
    "APILayer Suite（赞助）": "APILayer 赞助",
}

data = json.load(open(SRC, encoding="utf-8"))
probe = {}
if os.path.exists(PROBE):
    for p in json.load(open(PROBE, encoding="utf-8")):
        probe[p["url"]] = p

# 精选可直连端点（真实 endpoint，已实测通过）
CURATED_FILE = os.environ.get("PAP_CURATED") or os.path.join(DATA, "curated_results.json")
curated = []
if os.path.exists(CURATED_FILE):
    curated = [c for c in json.load(open(CURATED_FILE, encoding="utf-8")) if c.get("ok")]
curated.append({  # 补测可用项
    "name": "IPify (v6 通道)", "category": "Development",
    "url": "https://api64.ipify.org?format=json", "desc": "获取当前公网 IP（直连可用）",
    "headers": {}, "type": "json", "ok": True, "ms": 320, "acao": "*",
})
curated_payload = json.dumps(curated, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

def type_of(p, auth):
    """把实测结果归成一个前端可用的类型标签。"""
    if p:
        ctype = (p.get("ctype") or "").lower()
        kind = p.get("kind") or ""
        if ctype.startswith("image/"):
            return "image"                  # 直接返回图片，可渲染
        if kind == "direct":
            return "direct"                 # JSON + 开放跨域，浏览器可直连
        if kind == "json_no_cors":
            return "proxy"                  # 返回 JSON 但未开放跨域，需本地代理
        if kind == "page":
            return "doc"                    # 文档页 / HTML，不是数据端点
        if kind in ("http_error", "error"):
            return "bad"
    # 没实测到的：需要鉴权的单独标出来，其余才叫「未实测」
    return "needkey" if (auth or "").lower() != "no" else ""


items = []
for cat, rows in data.items():
    for r in rows:
        p = probe.get(r["url"], {})
        items.append({
            "n": r["name"], "u": r["url"], "d": r["description"],
            "a": r["auth"] or "-", "h": r["https"] or "-", "c": r["cors"] or "-",
            "k": cat,
            "t": type_of(p, r["auth"]),            # direct / proxy / image / doc / bad / needkey / ""
            "sc": p.get("status"),
            "ms": p.get("ms"),
            "ct": p.get("ctype", ""),
        })

payload = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
zh = json.dumps(ZH, ensure_ascii=False)

total = len(items)
cats = len(data)
direct = sum(1 for i in items if i["t"] == "direct")
proxied = sum(1 for i in items if i["t"] == "proxy")
images = sum(1 for i in items if i["t"] == "image")
docs = sum(1 for i in items if i["t"] == "doc")
bad_n = sum(1 for i in items if i["t"] == "bad")
needkey_n = sum(1 for i in items if i["t"] == "needkey")
untested = sum(1 for i in items if not i["t"])
callable_n = direct + proxied + images
free = sum(1 for i in items if i["a"].lower() == "no")

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>API 试炼场 TryAPI · 1826 个公开 API 一键实测</title>
<style>
:root{
  --bg:#080b12; --bg-soft:#0d1220; --panel:#111827; --panel2:#161f31;
  --line:#1e293b; --line2:#2b3a52;
  --txt:#e9eefb; --txt2:#94a3b8; --txt3:#5b6b85;
  --green:#4ade80; --green-d:#0f2a1c; --blue:#60a5fa; --blue-d:#0f2036;
  --amber:#fbbf24; --amber-d:#2e2408; --violet:#a78bfa; --red:#f87171;
  --r:11px; --sh:0 10px 40px rgba(0,0,0,.5);
}
*{box-sizing:border-box;margin:0;padding:0}
/* 贴底页脚：body 作纵向 flex 容器。
   内容不足一屏时由 .layout 撑满剩余空间，footer 落到视口最底部（中间留白）；
   内容超一屏时 footer 自然跟在末尾。 */
body{
  background:var(--bg); color:var(--txt); min-height:100vh;
  display:flex; flex-direction:column;
  font-family:'Segoe UI',system-ui,-apple-system,'Microsoft YaHei',sans-serif;
  -webkit-font-smoothing:antialiased; font-size:14px;
}
a{color:inherit;text-decoration:none}
button,input,select,textarea{font-family:inherit;font-size:inherit}

/* ============ 原仓库署名 ============ */
.srcbadge{display:flex;align-items:center;gap:8px;padding:7px 12px;border-radius:9px;
  background:var(--panel2);border:1px solid var(--line2);text-decoration:none;
  color:var(--txt2);font-size:12px;white-space:nowrap;transition:.16s}
.srcbadge:hover{border-color:var(--green);color:var(--txt);transform:translateY(-1px)}
.srcbadge b{color:var(--txt);font-weight:600}
.srcbadge .gh{width:16px;height:16px;fill:currentColor;opacity:.85;flex:none}

/* ============ 仓库徽章组（本项目 + 数据来源）============ */
.badges{display:flex;gap:8px;align-items:center;flex-shrink:0}
.srcbadge.mine{background:rgba(96,165,250,.11);border-color:rgba(96,165,250,.4);color:#bfdbfe}
.srcbadge.mine:hover{border-color:#60a5fa;color:#eff6ff}
.srcbadge.mine b{color:#dbeafe}
/* 顶栏空间规划：宽屏两个徽章 + 统计数字同框；
   ≤1600 收掉统计数字给徽章让位；≤1200 只留「开源仓库」徽章
   （数据来源在页脚有完整卡片，不会丢信息） */
@media(max-width:1600px){.top .topstats{display:none}}
@media(max-width:1200px){.badges .optional{display:none}}

/* ============ 页脚：仓库地址卡片 ============ */
.repogrid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:6px 0 2px}
@media(max-width:760px){.repogrid{grid-template-columns:1fr}}
footer.src a.repobox{display:flex;flex-direction:column;gap:5px;padding:13px 15px;
  border-radius:10px;background:var(--panel2);border:1px solid var(--line2);border-bottom:1px solid var(--line2);
  transition:.16s;text-decoration:none}
footer.src a.repobox:hover{border-color:#60a5fa;transform:translateY(-1px);color:inherit}
footer.src a.repobox.src:hover{border-color:var(--green)}
.repobox .rbtag{align-self:flex-start;font-size:10.5px;padding:2px 8px;border-radius:5px;
  background:rgba(96,165,250,.16);color:#93c5fd;border:1px solid rgba(96,165,250,.34)}
.repobox.src .rbtag{background:rgba(74,222,128,.14);color:var(--green);border-color:rgba(74,222,128,.34)}
.repobox b{color:var(--txt);font-size:13.5px;font-family:ui-monospace,Consolas,monospace;font-weight:600}
.repobox .rbdesc{color:var(--txt3);font-size:11.5px;line-height:1.65}
.repobox .rburl{color:var(--txt2);font-size:11.5px;margin-top:2px}
.licrow{display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:13px;padding-top:11px;
  border-top:1px dashed var(--line2)}
.licrow span{display:inline-flex;align-items:center;gap:6px}
footer.src{max-width:1520px;margin:auto auto 0;padding:22px 22px 40px;
  border-top:1px solid var(--line);color:var(--txt3);font-size:12.5px;line-height:1.9}
footer.src h3{font-size:13px;color:var(--txt2);margin:0 0 8px;font-weight:600}
footer.src a{color:var(--green);text-decoration:none;border-bottom:1px dotted rgba(74,222,128,.45)}
footer.src a:hover{color:#86efac}
footer.src .frow{display:flex;flex-wrap:wrap;gap:8px 20px;margin:10px 0}
footer.src .frow span{display:inline-flex;align-items:center;gap:6px}
footer.src .fcard{background:var(--panel);border:1px solid var(--line);border-radius:11px;
  padding:14px 16px;margin-top:12px}
footer.src code{font-family:ui-monospace,Consolas,monospace;font-size:11.5px;
  background:var(--bg-soft);border:1px solid var(--line2);border-radius:5px;padding:1px 6px;color:var(--txt2)}
footer.src .fnote{margin-top:14px;font-size:11.5px;color:var(--txt3)}
/* ============ 顶栏 ============ */
.top{
  position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:16px;
  padding:12px 20px;background:rgba(8,11,18,.86);backdrop-filter:blur(18px);
  border-bottom:1px solid var(--line);
}
.brand{display:flex;align-items:center;gap:11px;flex-shrink:0}
.logo{
  width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-size:16px;
  background:linear-gradient(135deg,#4ade80,#60a5fa);color:#04140c;font-weight:800;
}
.brand h1{font-size:15.5px;font-weight:700;letter-spacing:-.01em;white-space:nowrap}
.brand span{display:block;font-size:11px;color:var(--txt3);font-weight:400}
.search{position:relative;flex:1;max-width:560px}
.search svg{position:absolute;left:13px;top:50%;transform:translateY(-50%);opacity:.45}
#q{
  width:100%;padding:10px 40px;border-radius:9px;background:var(--panel);
  border:1px solid var(--line2);color:var(--txt);outline:none;transition:.16s;
}
#q:focus{border-color:var(--green);box-shadow:0 0 0 3px rgba(74,222,128,.12)}
#q::placeholder{color:var(--txt3)}
.kbd{position:absolute;right:11px;top:50%;transform:translateY(-50%);font-size:11px;
  color:var(--txt3);border:1px solid var(--line2);border-radius:5px;padding:1px 6px}
.topstats{display:flex;gap:7px;flex-shrink:0}
.tstat{
  display:flex;align-items:center;gap:6px;padding:6px 11px;border-radius:8px;
  background:var(--panel);border:1px solid var(--line);font-size:12.5px;color:var(--txt2);white-space:nowrap;
}
.tstat b{color:var(--green);font-weight:700}
.tstat.blue b{color:var(--blue)}
.tstat.amber b{color:var(--amber)}

/* ============ 布局 ============ */
.layout{display:grid;grid-template-columns:238px 1fr;align-items:start;flex:1 0 auto}
.side{
  position:sticky;top:59px;height:calc(100vh - 59px);overflow-y:auto;
  border-right:1px solid var(--line);padding:14px 12px 40px;background:var(--bg-soft);
}
.side::-webkit-scrollbar,.list::-webkit-scrollbar{width:7px}
.side::-webkit-scrollbar-thumb,.list::-webkit-scrollbar-thumb{background:var(--line2);border-radius:9px}
.side h3{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--txt3);
  padding:6px 9px 9px;font-weight:600}
.side .item{
  display:flex;align-items:center;gap:9px;padding:7px 10px;border-radius:8px;cursor:pointer;
  font-size:13px;color:var(--txt2);transition:.13s;border:1px solid transparent;
}
.side .item:hover{background:var(--panel);color:var(--txt)}
.side .item.on{background:rgba(74,222,128,.1);border-color:rgba(74,222,128,.35);color:#fff;font-weight:600}
.side .item i{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.side .item .c{margin-left:auto;font-size:11px;color:var(--txt3);background:rgba(255,255,255,.05);
  padding:1px 6px;border-radius:5px}
.side .item.on .c{color:var(--green)}
.side .all{margin-bottom:6px;background:var(--panel);border-color:var(--line2)}
.side .divider{height:1px;background:var(--line);margin:9px 6px}

.main{padding:14px 20px 90px;min-width:0}
.quickbar{
  position:sticky;top:59px;z-index:50;display:flex;flex-wrap:wrap;gap:8px;align-items:center;
  padding:11px 0 13px;background:linear-gradient(var(--bg) 72%,transparent);
}
.seg{display:flex;background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:3px}
.seg button{
  border:0;background:transparent;color:var(--txt2);cursor:pointer;padding:6px 13px;
  border-radius:7px;transition:.14s;font-size:12.5px;white-space:nowrap;
}
.seg button:hover{color:var(--txt)}
.seg button.on{background:linear-gradient(135deg,rgba(74,222,128,.22),rgba(96,165,250,.22));
  color:#fff;font-weight:600;box-shadow:inset 0 0 0 1px rgba(74,222,128,.35)}
.hits{margin-left:auto;font-size:12.5px;color:var(--txt2)}
.hits b{color:var(--green);font-size:15px}

/* ============ 列表 ============ */
.list{display:flex;flex-direction:column;gap:7px}
.card{
  display:grid;grid-template-columns:14px minmax(190px,1.1fr) minmax(200px,2.2fr) auto;
  gap:14px;align-items:center;padding:11px 14px;background:var(--panel);
  border:1px solid var(--line);border-radius:var(--r);transition:.14s;
}
.card:hover{border-color:var(--line2);background:var(--panel2);transform:translateY(-1px);
  box-shadow:0 6px 22px rgba(0,0,0,.28)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--txt3);justify-self:center}
.dot.direct{background:var(--green);box-shadow:0 0 9px rgba(74,222,128,.75)}
.dot.json_no_cors{background:var(--amber);box-shadow:0 0 8px rgba(251,191,36,.5)}
.dot.page{background:#64748b}
.dot.image{background:var(--blue);box-shadow:0 0 8px rgba(96,165,250,.5)}
.dot.needkey{background:#8b5cf6}
.dot.http_error,.dot.error{background:var(--red);opacity:.75}
.nm{font-weight:650;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block}
.nm:hover{color:var(--green)}
.ct{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--txt3);margin-top:4px}
.ct i{width:5px;height:5px;border-radius:50%;font-style:normal}
.dc{font-size:12.5px;color:var(--txt2);line-height:1.55;overflow:hidden;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.tags{display:flex;gap:5px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
.tag{font-size:10.5px;padding:3px 8px;border-radius:6px;border:1px solid var(--line2);
  color:var(--txt2);white-space:nowrap}
.tag.ok{background:var(--green);border-color:var(--green);color:#04140c;font-weight:700}
.tag.mid{background:var(--amber-d);border-color:rgba(251,191,36,.5);color:var(--amber)}
.tag.img{background:var(--blue-d);border-color:rgba(96,165,250,.5);color:var(--blue);font-weight:700}
.tag.no{color:var(--txt3)}
.tag.ms{color:var(--green);border-color:rgba(74,222,128,.3)}
.ops{display:flex;gap:6px;align-items:center}
.btn{
  border:1px solid var(--line2);background:var(--panel2);color:var(--txt2);cursor:pointer;
  padding:6px 12px;border-radius:8px;transition:.14s;font-size:12.5px;display:inline-flex;
  align-items:center;gap:5px;white-space:nowrap;
}
.btn:hover{border-color:var(--green);color:var(--green)}
.btn.primary{background:linear-gradient(135deg,#4ade80,#34d399);border-color:transparent;
  color:#04140c;font-weight:700}
.btn.primary:hover{filter:brightness(1.08);color:#04140c}
.btn.icon{padding:6px 9px}
.empty{text-align:center;padding:80px 20px;color:var(--txt3)}
.empty .e{font-size:40px;margin-bottom:14px;opacity:.6}
.more{display:flex;justify-content:center;padding:26px 0 10px}
.more button{background:var(--panel);border:1px solid var(--line2);color:var(--txt);
  padding:10px 30px;border-radius:10px;cursor:pointer;transition:.14s}
.more button:hover{border-color:var(--green);color:var(--green)}

/* ============ 视图切换 / 精选区 ============ */
.tabs{display:flex;gap:4px;background:var(--panel);border:1px solid var(--line);
  border-radius:10px;padding:3px;flex-shrink:0}
.tabs button{border:0;background:transparent;color:var(--txt2);cursor:pointer;
  padding:7px 14px;border-radius:8px;transition:.15s;font-size:12.5px;white-space:nowrap;
  display:flex;align-items:center;gap:6px}
.tabs button:hover{color:var(--txt)}
.tabs button.on{background:linear-gradient(135deg,rgba(74,222,128,.24),rgba(96,165,250,.24));
  color:#fff;font-weight:650;box-shadow:inset 0 0 0 1px rgba(74,222,128,.3)}
.tabs .num{font-size:11px;background:rgba(255,255,255,.1);padding:1px 6px;border-radius:5px}
.sec-head{display:flex;align-items:center;gap:11px;margin:6px 0 13px}
.sec-head h2{font-size:16px;font-weight:700}
.sec-head p{font-size:12.5px;color:var(--txt3)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(272px,1fr));gap:11px}
.ccard{
  background:linear-gradient(165deg,var(--panel) 0%,var(--panel2) 100%);
  border:1px solid var(--line);border-radius:12px;padding:14px;display:flex;
  flex-direction:column;gap:10px;transition:.16s;position:relative;overflow:hidden;
}
.ccard::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--green),var(--blue));opacity:.55}
.ccard:hover{transform:translateY(-2px);border-color:var(--line2);
  box-shadow:0 10px 28px rgba(0,0,0,.34)}
.ccard:hover::before{opacity:1}
.ccard .ctop{display:flex;align-items:flex-start;gap:9px}
.ccard .cname{font-weight:700;font-size:14.5px;flex:1;min-width:0;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.ccard .cdesc{font-size:12.5px;color:var(--txt2);line-height:1.6;flex:1;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.ccard .cfoot{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.ccard .curl{font-size:11px;color:var(--txt3);overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap;width:100%;font-family:ui-monospace,Consolas,monospace}
.ctype{font-size:10.5px;padding:2px 7px;border-radius:5px;font-weight:700}
.ctype.json{background:var(--green-d);color:var(--green);border:1px solid rgba(74,222,128,.3)}
.ctype.image{background:var(--blue-d);color:var(--blue);border:1px solid rgba(96,165,250,.3)}
.inline-res{margin-top:4px;border-top:1px dashed var(--line2);padding-top:10px}
.inline-res img{max-width:100%;border-radius:8px;display:block;border:1px solid var(--line2)}
.inline-res pre{background:#070a10;border:1px solid var(--line);border-radius:8px;padding:10px;
  font-size:11.5px;line-height:1.6;max-height:220px;overflow:auto;color:#cbd5e1;
  font-family:ui-monospace,Consolas,monospace}
.errline{color:var(--red);font-size:12px;line-height:1.6}
.modebar{margin:0 0 13px}
.mode{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;padding:7px 13px;
  border-radius:9px;line-height:1.4}
.mode.on{background:var(--green-d);color:var(--green);border:1px solid rgba(74,222,128,.35)}
.mode.off{background:var(--amber-d);color:var(--amber);border:1px solid rgba(251,191,36,.3)}
.mode b{color:#fff}

/* ============ 智能结果渲染 ============ */
.rt-big{font-size:17px;line-height:1.8;color:#fff;padding:16px 18px;background:var(--panel);
  border:1px solid var(--line);border-radius:10px;border-left:3px solid var(--green);
  word-break:break-word;white-space:pre-wrap}
.rt-text{font-size:13.5px;line-height:1.85;color:var(--txt2);padding:14px 16px;background:var(--panel);
  border:1px solid var(--line);border-radius:10px;border-left:3px solid var(--line2);
  word-break:break-word;white-space:pre-wrap;max-height:340px;overflow:auto}
.rt-others{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.rt-chip{font-size:11.5px;color:var(--txt2);background:var(--panel2);border:1px solid var(--line2);
  padding:4px 10px;border-radius:7px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rt-chip b{color:var(--txt3);font-weight:400;margin-right:5px}
.rt-note{font-size:11.5px;color:var(--txt3);margin:13px 0 8px;letter-spacing:.03em}
.rt-img{margin-bottom:10px}
.rt-img img{max-width:100%;border-radius:10px;border:1px solid var(--line2);display:block;
  background:#0b1220;min-height:40px}
.rt-err{font-size:11.5px;color:var(--red);padding:10px 12px;background:#2a1013;
  border:1px solid rgba(248,113,113,.3);border-radius:8px;word-break:break-all;line-height:1.6}
.rt-kv{width:100%;border-collapse:collapse;font-size:12.5px;
  background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.rt-kv td{padding:7px 11px;border-bottom:1px solid var(--line);vertical-align:top}
.rt-kv tr:last-child td{border-bottom:0}
.rt-kv td:first-child{color:var(--txt3);width:36%;font-family:ui-monospace,Consolas,monospace;font-size:11.5px}
.rt-kv td:last-child{color:var(--txt);word-break:break-word}
.rt-tip{font-size:11.5px;color:var(--txt3);margin-top:9px}
.rt-list{display:block;overflow:auto;max-height:420px}
.rt-list th{background:var(--panel2);color:var(--txt3);font-size:11px;font-weight:600;
  text-align:left;padding:7px 11px;border-bottom:1px solid var(--line2);white-space:nowrap;
  position:sticky;top:0;z-index:1}
.rt-thumb{width:52px;height:52px;object-fit:cover;border-radius:6px;display:block}
/* 路径参数：默认收起，点「🔧 参数」才展开 —— 避免卡片上常驻一堆空输入框 */
.rt-params{display:none;flex-wrap:wrap;gap:8px;margin-top:9px;padding:10px 11px;
  border:1px dashed var(--line2);border-radius:10px;background:var(--bg-soft)}
.rt-params.open{display:flex;animation:pdrop .18s ease}
@keyframes pdrop{from{opacity:0;transform:translateY(-5px)}to{opacity:1;transform:none}}
.rt-params .phd{flex:1 0 100%;font-size:11.5px;color:var(--txt3);margin-bottom:2px;line-height:1.6}
.rt-params .phd b{color:var(--amber);font-weight:700}
.pdrop{display:inline-flex;align-items:center;gap:5px;padding:6px 11px;border-radius:8px;
  cursor:pointer;font-size:12.5px;transition:.14s;white-space:nowrap;
  background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.4);color:var(--amber)}
.pdrop:hover{background:rgba(251,191,36,.2);border-color:var(--amber)}
.pdrop b{font-weight:700}
.pdrop.on{background:rgba(251,191,36,.22);border-color:var(--amber)}
.pdrop.done{background:rgba(74,222,128,.1);border-color:rgba(74,222,128,.42);color:var(--green)}
.rt-param{display:flex;flex-direction:column;gap:4px;flex:1;min-width:132px}
.rt-param label{font-size:10.5px;color:var(--txt3);font-family:ui-monospace,Consolas,monospace}
.rt-param input{padding:6px 9px;font-size:12px;background:var(--bg-soft);
  border:1px solid var(--line2);border-radius:7px;color:var(--txt);outline:none;width:100%}
.rt-param input:focus{border-color:var(--green);box-shadow:0 0 0 3px rgba(74,222,128,.1)}
.rt-param input.need{border-color:rgba(251,191,36,.6)}
.rt-param .warn{font-size:10px;color:var(--amber)}
.rt-list td{padding:6px 11px;color:var(--txt);white-space:nowrap;max-width:260px;
  overflow:hidden;text-overflow:ellipsis}
.rt-list td.idx{color:var(--txt3);font-size:11px;width:38px;text-align:right}
.rt-list tr:nth-child(even) td{background:rgba(255,255,255,.017)}
.rt-nil{color:var(--txt3);font-style:italic}
.rt-pathhint{font-size:11px;color:var(--txt3);margin-top:7px;line-height:1.6}
.rt-pathhint b{color:var(--amber);font-weight:600}

/* ============ 抽屉：调用面板 ============ */
.mask{position:fixed;inset:0;background:rgba(4,7,12,.62);backdrop-filter:blur(3px);
  opacity:0;pointer-events:none;transition:.22s;z-index:80}
.mask.on{opacity:1;pointer-events:auto}
.drawer{
  position:fixed;top:0;right:0;bottom:0;width:min(620px,100%);background:var(--bg-soft);
  border-left:1px solid var(--line2);z-index:90;transform:translateX(102%);
  transition:transform .28s cubic-bezier(.32,.72,0,1);display:flex;flex-direction:column;
  box-shadow:var(--sh);
}
.drawer.on{transform:translateX(0)}
.dhead{display:flex;align-items:flex-start;gap:12px;padding:16px 18px;border-bottom:1px solid var(--line)}
.dhead .ttl{flex:1;min-width:0}
.dhead h2{font-size:16.5px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dhead .sub{font-size:12px;color:var(--txt3);margin-top:5px;display:flex;gap:9px;align-items:center;flex-wrap:wrap}
.close{background:var(--panel);border:1px solid var(--line2);color:var(--txt2);width:31px;height:31px;
  border-radius:8px;cursor:pointer;display:grid;place-items:center;transition:.14s;flex-shrink:0}
.close:hover{border-color:var(--red);color:var(--red)}
.dbody{flex:1;overflow-y:auto;padding:16px 18px 30px}
.dbody::-webkit-scrollbar{width:7px}
.dbody::-webkit-scrollbar-thumb{background:var(--line2);border-radius:9px}
.fld{margin-bottom:14px}
.fld label{display:block;font-size:11.5px;color:var(--txt3);margin-bottom:6px;
  letter-spacing:.03em;text-transform:uppercase;font-weight:600}
.row-in{display:flex;gap:7px}
input.ti,textarea.ti{
  width:100%;padding:9px 11px;background:var(--panel);border:1px solid var(--line2);
  border-radius:8px;color:var(--txt);outline:none;transition:.15s;font-size:12.5px;
}
input.ti:focus,textarea.ti:focus{border-color:var(--green);box-shadow:0 0 0 3px rgba(74,222,128,.1)}
textarea.ti{resize:vertical;min-height:64px;font-family:ui-monospace,Consolas,monospace;line-height:1.6}
.pill{background:var(--panel);border:1px solid var(--line2);border-radius:8px;padding:9px 12px;
  font-size:12px;color:var(--txt2);font-family:ui-monospace,Consolas,monospace;flex-shrink:0}
.ghost{display:inline-flex;align-items:center;gap:5px;background:transparent;border:1px dashed var(--line2);
  color:var(--txt3);padding:7px 11px;border-radius:8px;cursor:pointer;transition:.14s;font-size:12px}
.ghost:hover{border-color:var(--green);color:var(--green)}
.snip-tabs,.res-tabs{display:flex;gap:5px;margin-bottom:8px}
.snip-tabs button,.res-tabs button{
  background:transparent;border:1px solid var(--line);color:var(--txt2);padding:5px 11px;
  border-radius:7px;cursor:pointer;transition:.14s;font-size:12px;
}
.snip-tabs button.on,.res-tabs button.on{background:var(--panel2);border-color:var(--line2);color:#fff;font-weight:600}
pre.code{
  background:#070a10;border:1px solid var(--line);border-radius:9px;padding:13px;
  overflow:auto;font-size:12px;line-height:1.65;font-family:ui-monospace,Consolas,monospace;
  color:#cbd5e1;max-height:290px;
}
pre.code::-webkit-scrollbar{height:7px;width:7px}
pre.code::-webkit-scrollbar-thumb{background:var(--line2);border-radius:9px}
.res-meta{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:11px;
  padding:10px 12px;background:var(--panel);border:1px solid var(--line);border-radius:9px;font-size:12.5px}
.mtag{padding:3px 9px;border-radius:6px;font-weight:700;font-size:11.5px}
.mtag.s2{background:var(--green-d);color:var(--green);border:1px solid rgba(74,222,128,.35)}
.mtag.s4,.mtag.s5{background:#2a1013;color:var(--red);border:1px solid rgba(248,113,113,.35)}
.mtag.muted{color:var(--txt3);border:1px solid var(--line2)}
.loading{display:flex;align-items:center;gap:11px;padding:26px;justify-content:center;color:var(--txt2)}
.spin{width:19px;height:19px;border:2px solid var(--line2);border-top-color:var(--green);
  border-radius:50%;animation:sp .7s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
.hintbox{padding:13px 14px;border-radius:9px;font-size:12.5px;line-height:1.7;
  background:var(--amber-d);border:1px solid rgba(251,191,36,.32);color:#fde68a;margin-bottom:12px}
.hintbox.err{background:#2a1013;border-color:rgba(248,113,113,.32);color:#fecaca}
.hintbox b{color:#fff}
.j-key{color:#7dd3fc}.j-str{color:#86efac}.j-num{color:#fcd34d}
.j-bool{color:#c4b5fd}.j-null{color:#94a3b8}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(70px);
  background:var(--green);color:#04140c;font-weight:700;font-size:13px;padding:11px 22px;
  border-radius:10px;opacity:0;transition:.24s;z-index:120;pointer-events:none}
.toast.show{transform:translateX(-50%) translateY(0);opacity:1}
.parambox{border:1px solid var(--line);border-radius:9px;padding:10px;background:var(--panel);margin-bottom:8px}
.prow{display:grid;grid-template-columns:1fr 1.3fr 32px;gap:6px;margin-bottom:6px}
.prow input{padding:6px 9px;font-size:12px;background:var(--bg-soft);border:1px solid var(--line2);
  border-radius:6px;color:var(--txt);outline:none;width:100%}
.prow input:focus{border-color:var(--green)}
.del{background:transparent;border:1px solid var(--line2);color:var(--txt3);border-radius:6px;
  cursor:pointer;transition:.14s}
.del:hover{border-color:var(--red);color:var(--red)}
@media(max-width:1080px){
  .layout{grid-template-columns:1fr}
  .side{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);
    display:flex;gap:7px;overflow-x:auto;padding:11px 14px}
  .side h3,.side .divider{display:none}
  .side .item{white-space:nowrap}
  .topstats{display:none}
}
@media(max-width:760px){
  .card{grid-template-columns:14px 1fr;gap:11px}
  .dc,.tags,.ops{grid-column:2}
  .tags,.ops{justify-content:flex-start}
}
</style>
</head>
<body>

<div class="top">
  <div class="brand">
    <div class="logo">⚡</div>
    <div><h1>API 试炼场<span>TryAPI · public-apis 数据集 · __TOTAL__ 个接口</span></h1></div>
  </div>
  <div class="search">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
      <circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg>
    <input id="q" placeholder="搜索接口，例如 weather / 天气 / ip / 汇率 / 图片" autocomplete="off">
    <span class="kbd">/</span>
  </div>
  <div class="tabs" id="viewTabs">
    <button data-view="curated" class="on">⚡ 精选可直连<span class="num">__NCUR__</span></button>
    <button data-view="all">📚 全量清单<span class="num">__TOTAL__</span></button>
  </div>
  <div class="topstats">
    <div class="tstat"><b>__CALLABLE__</b> 可调用</div>
    <div class="tstat blue"><b>__IMAGES__</b> 图片</div>
    <div class="tstat amber"><b>__DOCS__</b> 文档页</div>
    <div class="tstat"><b>__TOTAL__</b> 总数</div>
  </div>
  <div class="badges">
    <a class="srcbadge mine" href="https://github.com/LambdaJoker/tryapi" target="_blank" rel="noopener"
       title="本项目开源仓库：LambdaJoker/tryapi（MIT License）">
      <svg class="gh" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      开源仓库 <b>LambdaJoker/tryapi</b> ↗
    </a>
    <a class="srcbadge optional" href="https://github.com/public-apis/public-apis" target="_blank" rel="noopener"
       title="数据来源：public-apis/public-apis（MIT License）">
      <svg class="gh" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      数据来源 <b>public-apis/public-apis</b> ↗
    </a>
  </div>
</div>

<div class="layout">
  <aside class="side" id="side"></aside>
  <main class="main">
    <div class="modebar"><span class="mode off" id="modeBadge">⏳ 正在检测调用通道…</span></div>
    <section id="viewCurated">
      <div class="sec-head">
        <h2>⚡ 开箱即用 · 点一下直接出结果</h2>
        <p>这 <b>__NCUR__</b> 个接口已逐个实测：真实数据端点 + 支持跨域，在浏览器中可直接调用</p>
      </div>
      <div class="quickbar" style="margin-bottom:8px;padding-bottom:6px">
        <div class="seg" id="segCurCat"></div>
      </div>
      <div class="grid" id="curatedGrid"></div>
    </section>

    <section id="viewAll" style="display:none">
      <div class="quickbar">
        <div class="seg" id="segCall">
          <button data-call="callable" class="on">✅ 可调用</button>
          <button data-call="direct">可直连</button>
          <button data-call="proxy">需代理</button>
          <button data-call="image">🖼 图片</button>
          <button data-call="doc">📄 文档页</button>
          <button data-call="needkey">🔑 需鉴权</button>
          <button data-call="other">其他</button>
          <button data-call="all">全部</button>
        </div>
        <div class="seg" id="segAuth">
          <button data-auth="all" class="on">全部鉴权</button>
          <button data-auth="free">免鉴权</button>
          <button data-auth="key">需 Key</button>
        </div>
        <div class="seg" id="segSort">
          <button data-sort="idx" class="on">默认顺序</button>
          <button data-sort="name">按名称</button>
          <button data-sort="ms">按响应速度</button>
        </div>
        <div class="hits">命中 <b id="hits">0</b> / __TOTAL__</div>
      </div>
      <div class="list" id="list"></div>
      <div class="more" id="moreBox" style="display:none"><button id="moreBtn">加载更多</button></div>
    </section>
  </main>
</div>

<footer class="src">
  <h3>🔗 仓库与许可</h3>
  <div class="repogrid">
    <a class="repobox" href="https://github.com/LambdaJoker/tryapi" target="_blank" rel="noopener"
       title="本项目开源仓库（MIT License）">
      <span class="rbtag">本项目</span>
      <b>LambdaJoker/tryapi</b>
      <span class="rbdesc">API 试炼场 TryAPI 全部源码：页面生成器、CORS 代理、数据流水线、部署包</span>
      <span class="rburl">github.com/LambdaJoker/tryapi ↗</span>
    </a>
    <a class="repobox src" href="https://github.com/public-apis/public-apis" target="_blank" rel="noopener"
       title="数据来源仓库（MIT License）">
      <span class="rbtag">数据来源</span>
      <b>public-apis/public-apis</b>
      <span class="rbdesc">本页 __TOTAL__ 条接口条目的原始仓库：分类 / 说明 / 鉴权 / HTTPS / CORS 六列数据</span>
      <span class="rburl">github.com/public-apis/public-apis ↗</span>
    </a>
  </div>
  <div class="licrow">
    <span>📜 本项目许可：<a href="LICENSE" target="_blank">MIT License</a></span>
    <span>📜 数据许可：<a href="LICENSE-public-apis" target="_blank">MIT License</a>（归 public-apis 社区）</span>
    <span>⚖️ 完整声明：<a href="NOTICE.md" target="_blank">NOTICE.md</a> · <a href="README.md" target="_blank">README.md</a></span>
  </div>

  <h3 style="margin-top:22px">📌 数据来源与致谢</h3>
  <div class="fcard">
    <div class="frow">
      <span>原仓库：<a href="https://github.com/public-apis/public-apis" target="_blank" rel="noopener">github.com/public-apis/public-apis</a></span>
      <span>许可证：<a href="https://github.com/public-apis/public-apis/blob/master/LICENSE" target="_blank" rel="noopener">MIT License</a></span>
      <span>原仓库概况：⭐ 480k+ / Python / 社区维护的免费 API 合集</span>
    </div>
    <div style="color:var(--txt2);line-height:1.85">
      本页 <b>__TOTAL__</b> 个接口条目全部来自上述仓库 README 的表格解析（含分类、说明、鉴权、HTTPS、CORS 五列），
      未做任何删改；分类中文名、可用性实测结果、调试试台界面为本页额外补充，仅作便利性呈现，
      <b>不改变原仓库的数据与其许可条款</b>。
    </div>
    <div class="frow" style="margin-top:12px">
      <span>📄 调试试台与实测数据由 <b>WorkBuddy</b> 生成</span>
      <span>🧪 实测方式：带 <code>Origin</code> 头探测，判定标准 = HTTP 200 + 返回 JSON + 存在 <code>Access-Control-Allow-Origin</code></span>
      <span>🖼 图片类接口用 <code>&lt;img&gt;</code> 渲染（图片请求不受 CORS 限制）</span>
    </div>
    <div class="frow" style="margin-top:12px">
      <span>🔧 附全套 Python 源码：</span>
      <span><a href="scripts/serve.py" download>serve.py</a>（本地服务 + CORS 代理）</span>
      <span><a href="scripts/parse_public_apis.py" download>parse_public_apis.py</a>（README 表格解析）</span>
      <span><a href="scripts/export_public_apis.py" download>export_public_apis.py</a>（导出 xlsx/csv/md/json）</span>
      <span><a href="scripts/probe_apis.py" download>probe_apis.py</a>（全量可用性探测）</span>
      <span><a href="scripts/curated_endpoints.py" download>curated_endpoints.py</a>（精选端点实测）</span>
      <span><a href="scripts/build_html_v2.py" download>build_html_v2.py</a>（本页生成器）</span>
      <span><a href="README.md" target="_blank">📖 项目 README（数据来源与声明）</a></span>
      <span><a href="scripts/" target="_blank">📁 浏览全部文件</a></span>
    </div>
    <div class="fnote">
      免责声明：本页仅为第三方接口的导航与调试便利工具，不代理、不缓存任何接口的业务数据；
      各接口的内容、可用性、调用配额与使用条款均归其各自提供方所有，请遵守对应服务的使用协议与所在地区法律法规。
      原仓库中标注需鉴权（<code>apiKey</code> / <code>OAuth</code> / <code>X-Mashape-Key</code>）的接口，需自行到服务方申请凭据。
    </div>
  </div>
  <div class="fnote" style="text-align:center;margin-top:18px">
    API 试炼场 TryAPI ·
    <a href="https://github.com/LambdaJoker/tryapi" target="_blank" rel="noopener">github.com/LambdaJoker/tryapi</a> ·
    数据源自 <a href="https://github.com/public-apis/public-apis" target="_blank" rel="noopener">public-apis/public-apis</a> ·
    共 __TOTAL__ 个接口 · 精选可直连 __NCUR__ 个 · MIT License
  </div>
</footer>

<div class="mask" id="mask"></div>
<aside class="drawer" id="drawer">
  <div class="dhead">
    <div class="ttl">
      <h2 id="dTitle">—</h2>
      <div class="sub" id="dSub"></div>
    </div>
    <button class="close" id="dClose">✕</button>
  </div>
  <div class="dbody" id="dBody"></div>
</aside>
<div class="toast" id="toast">已复制</div>

<script>
const DATA = __DATA__;
const CURATED = __CURATED__;
const ZH = __ZH__;
const PAGE = 120;

const esc = s => String(s == null ? "" : s)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
  .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
const hueOf = s => { let h=0; for (let i=0;i<s.length;i++) h=(h*31+s.charCodeAt(i))%360; return h; };
const catColor = k => `hsl(${hueOf(k)},62%,64%)`;
const zhName = k => ZH[k] || k;
const $ = id => document.getElementById(id);

const toast = $("toast");
let toastTimer;
function showToast(msg){
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 1500);
}
function copy(text, msg){
  const p = navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject();
  p.then(() => showToast(msg || "已复制")).catch(() => window.prompt("手动复制：", text));
}

const state = { q:"", cat:null, call:"callable", auth:"all", sort:"idx", shown:PAGE };

/* ---------- 侧栏分类 ---------- */
const counts = {};
DATA.forEach(d => counts[d.k] = (counts[d.k]||0)+1);
const stCount = {};
DATA.forEach(d => { if (d.t === "direct" || d.t === "proxy" || d.t === "image") stCount[d.k] = (stCount[d.k]||0)+1; });
const side = $("side");
side.innerHTML = '<h3>用途分类</h3>';
const mkItem = (label, key, num, color) => {
  const el = document.createElement("div");
  el.className = "item" + (state.cat === key ? " on" : "");
  el.innerHTML = `<i style="background:${color}"></i><span>${esc(label)}</span><span class="c">${num}</span>`;
  el.onclick = () => {
    state.cat = (state.cat === key) ? null : key;
    [...side.querySelectorAll(".item")].forEach(x => x.classList.remove("on"));
    if (state.cat) el.classList.add("on");
    else side.querySelector(".all").classList.add("on");
    state.shown = PAGE; render();
  };
  return el;
};
const allItem = mkItem("全部接口", "__all__", DATA.length, "var(--green)");
allItem.classList.add("all", "on");
allItem.onclick = () => {
  state.cat = null;
  [...side.querySelectorAll(".item")].forEach(x => x.classList.remove("on"));
  allItem.classList.add("on");
  state.shown = PAGE; render();
};
side.appendChild(allItem);
const div0 = document.createElement("div"); div0.className = "divider"; side.appendChild(div0);
Object.keys(counts).forEach(k => {
  const el = mkItem(zhName(k), k, counts[k], catColor(k));
  if (stCount[k]) el.title = `其中 ${stCount[k]} 个可直连调用`;
  side.appendChild(el);
});

/* ---------- 筛选 ---------- */
function filtered(){
  const q = state.q.trim().toLowerCase();
  let out = DATA.filter(d => {
    if (state.cat && d.k !== state.cat) return false;
    if (state.auth === "free" && (d.a||"").toLowerCase() !== "no") return false;
    if (state.auth === "key" && !(d.a||"").toLowerCase().includes("key")) return false;
    if (state.call !== "all"){
      const t = d.t || "";
      if (state.call === "callable"){
        if (t !== "direct" && t !== "proxy" && t !== "image") return false;
      } else if (state.call === "other"){
        if (t !== "bad" && t !== "") return false;   // 不可用 + 未实测
      } else if (t !== state.call){
        return false;
      }
    }
    if (q){
      const hay = (d.n+" "+d.d+" "+d.k+" "+zhName(d.k)).toLowerCase();
      if (!q.split(/\s+/).every(t => hay.includes(t))) return false;
    }
    return true;
  });
  if (state.sort === "name") out = out.slice().sort((x,y) => x.n.localeCompare(y.n));
  if (state.sort === "ms") out = out.slice().sort((x,y) => {
    const a = x.ms == null ? 1e9 : x.ms, b = y.ms == null ? 1e9 : y.ms; return a - b;
  });
  return out;
}

/* ---------- 列表渲染 ---------- */
const listEl = $("list"), moreBox = $("moreBox");
const TYPEMETA = {
  direct: { tag:'<span class="tag ok">可直连</span>', dot:"direct" },
  proxy:  { tag:'<span class="tag mid">需代理</span>', dot:"json_no_cors" },
  image:  { tag:'<span class="tag img">🖼 图片</span>', dot:"image" },
  doc:    { tag:'<span class="tag no">📄 文档</span>', dot:"page" },
  bad:    { tag:'<span class="tag no">不可用</span>', dot:"http_error" },
  needkey:{ tag:'<span class="tag no">🔑 需鉴权</span>', dot:"needkey" },
  "":     { tag:'<span class="tag no">未实测</span>', dot:"" },
};

function render(){
  const rows = filtered();
  $("hits").textContent = rows.length;
  const slice = rows.slice(0, state.shown);
  if (!rows.length){
    listEl.innerHTML = '<div class="empty"><div class="e">🔍</div><div>没有匹配的接口，试试换个关键词或清空筛选</div></div>';
    moreBox.style.display = "none"; return;
  }
  const frag = document.createDocumentFragment();
  slice.forEach(d => {
    const col = catColor(d.k);
    const k = TYPEMETA[d.t || ""] || TYPEMETA[""];
    const el = document.createElement("div");
    el.className = "card";
    const msTag = (d.ms != null && (d.t === "direct" || d.t === "image"))
      ? `<span class="tag ms">${d.ms}ms</span>` : "";
    el.innerHTML =
      `<div class="dot ${k.dot}"></div>` +
      `<div><a class="nm" href="${esc(d.u)}" target="_blank" rel="noopener" title="${esc(d.n)}">${esc(d.n)}</a>` +
      `<div class="ct"><i style="background:${col}"></i>${esc(zhName(d.k))}</div></div>` +
      `<div class="dc">${esc(d.d || "（官方未提供说明）")}</div>` +
      `<div class="ops"><div class="tags">${k.tag}${msTag}</div>` +
      `<button class="btn primary">▷ 调用</button>` +
      `<a class="btn icon" title="打开官方页面" href="${esc(d.u)}" target="_blank" rel="noopener">↗</a></div>`;
    el.querySelector(".btn.primary").onclick = e => { e.preventDefault(); openDrawer(d); };
    frag.appendChild(el);
  });
  listEl.innerHTML = "";
  listEl.appendChild(frag);
  moreBox.style.display = rows.length > state.shown ? "flex" : "none";
  $("moreBtn").textContent = `加载更多（剩余 ${rows.length - state.shown} 条）`;
}
$("moreBtn").onclick = () => { state.shown += PAGE*2; render(); };

/* ---------- 代码片段 ---------- */
function snippets(url, headers){
  const hdrs = Object.entries(headers).map(([k,v]) => `${k}: ${v}`).join("\n");
  const curlH = Object.entries(headers).map(([k,v]) => `-H "${k}: ${v}"`).join(" ");
  return {
    curl: `curl -s ${curlH ? curlH + " " : ""}"${url}"`,
    fetch: `const res = await fetch("${url}"${Object.keys(headers).length
      ? ", { headers: " + JSON.stringify(headers, null, 2) + " }" : ""});
const data = await res.json();
console.log(data);`,
    python: `import requests

resp = requests.get("${url}"${Object.keys(headers).length
      ? ", headers=" + JSON.stringify(headers) : ""}, timeout=10)
resp.raise_for_status()
data = resp.json()
print(data)`,
  };
}

/* ---------- 抽屉 ---------- */
const drawer = $("drawer"), mask = $("mask"), dBody = $("dBody");
let cur = null, curHeaders = {}, curParams = [], curPathVals = {}, lastResult = null, snipTab = "curl", resTab = "pretty";

function closeDrawer(){ drawer.classList.remove("on"); mask.classList.remove("on"); }
mask.onclick = closeDrawer;
$("dClose").onclick = closeDrawer;
document.addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); });

function buildUrl(){
  const raw = $("urlInput") ? $("urlInput").value.trim() : (cur ? cur.u : "");
  const base = fillPath(raw, curPathVals);
  const pairs = curParams.filter(p => p.k.trim());
  if (!pairs.length) return base;
  const qs = pairs.map(p => `${encodeURIComponent(p.k.trim())}=${encodeURIComponent(p.v)}`).join("&");
  return base + (base.includes("?") ? "&" : "?") + qs;
}
// 未填的必填占位符
function missingPath(){
  return placeholders($("urlInput") ? $("urlInput").value : "").filter(k => !curPathVals[k]);
}

function openDrawer(d, opts){
  opts = opts || {};
  cur = d;
  curHeaders = Object.assign({ "Accept": "application/json" }, opts.headers || {});
  curParams = [];
  curPathVals = Object.assign({}, opts.pathVals || {});
  placeholders(d.u).forEach(k => { if (curPathVals[k] == null) curPathVals[k] = ""; });
  lastResult = null;
  const phs = placeholders(d.u);
  dBody.innerHTML =
    `<div class="fld"><label>接口名称 / 来源</label>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        <b style="font-size:14px">${esc(d.n)}</b>
        <span class="tag" style="color:${catColor(d.k)};border-color:${catColor(d.k)}">${esc(zhName(d.k))}</span>
        <a class="btn icon" href="${esc(d.home || d.u)}" target="_blank" rel="noopener" title="打开官方页面">↗</a>
      </div>
      <div style="color:var(--txt2);font-size:12.5px;margin-top:8px;line-height:1.6">${esc(d.d || "")}</div>
     </div>
     ${phs.length ? `<div class="fld"><label>路径参数（<span style="color:var(--amber)">必填</span> · 涉及个人信息的请自己填写）</label>
       <div class="rt-params" id="pathBox"></div>
       <div class="rt-pathhint">这些是 URL 里的占位符，系统不会替你预设任何账号或仓库信息。</div>
     </div>` : ""}
     <div class="fld"><label>请求地址（可直接改成你要的端点）</label>
       <div class="row-in"><span class="pill">GET</span><input class="ti" id="urlInput" value="${esc(d.u)}"></div>
     </div>
     <div class="fld"><label>查询参数</label>
       <div class="parambox" id="pbox"></div>
       <button class="ghost" id="addParam">+ 添加参数</button>
     </div>
     <div class="fld"><label>请求头</label>
       <div class="parambox" id="hbox"></div>
       <button class="ghost" id="addHeader">+ 添加请求头</button>
     </div>
     <div class="fld"><button class="btn primary" id="sendBtn" style="width:100%;justify-content:center;padding:11px">▷ 发送请求</button></div>
     <div class="fld"><label>等价代码</label>
       <div class="snip-tabs">
         <button data-snip="curl" class="on">cURL</button>
         <button data-snip="fetch">JavaScript</button>
         <button data-snip="python">Python</button>
       </div>
       <pre class="code" id="snip"></pre>
       <button class="ghost" id="copySnip" style="margin-top:8px">⧉ 复制代码</button>
     </div>
     <div class="fld"><label>调用结果</label><div id="result"></div></div>`;

  renderParams(); renderHeaders(); renderPathParams(); refreshSnip();
  dBody.querySelectorAll("[data-snip]").forEach(b => b.onclick = () => {
    snipTab = b.dataset.snip;
    dBody.querySelectorAll("[data-snip]").forEach(x => x.classList.toggle("on", x === b));
    refreshSnip();
  });
  $("copySnip").onclick = () => copy($("snip").textContent, "代码已复制");
  $("addParam").onclick = () => { curParams.push({k:"",v:""}); renderParams(); refreshSnip(); };
  $("addHeader").onclick = () => { curHeaders[""] = ""; renderHeaders(); refreshSnip(); };
  $("sendBtn").onclick = doCall;
  $("urlInput").oninput = () => {
    const keys = placeholders($("urlInput").value);
    keys.forEach(k => { if (curPathVals[k] == null) curPathVals[k] = ""; });
    if ($("pathBox") && keys.length !== $("pathBox").children.length) renderPathParams();
    refreshSnip();
  };

  const tip =
    d.t === "image"
      ? '<div class="hintbox">🖼 这是一个<b>图片接口</b>，点上方「发送请求」即可直接预览图片。</div>'
    : d.t === "direct"
      ? '<div class="hintbox">✅ 该接口实测支持<b>跨域直连</b>，点上方按钮即可在浏览器中直接拿到结果。</div>'
    : d.t === "proxy"
      ? '<div class="hintbox">⚠️ 该接口能返回 JSON，但<b>未开放跨域</b>：' +
        (PROXY ? "当前已启用本地代理，可直接调用。" : "运行 <b>serve.py</b> 启用本地代理后即可调用。") + '</div>'
    : d.t === "doc"
      ? '<div class="hintbox">📄 这个地址是<b>官方文档页</b>，不是数据端点。' +
        '点右上角 ↗ 查看文档，找到真正的 endpoint 填到上方「请求地址」再发送。</div>'
    : d.t === "bad"
      ? '<div class="hintbox err">❌ 实测该地址无法直接返回数据' +
        (d.sc ? '（HTTP ' + d.sc + '）' : '') + '。建议点 ↗ 打开官方页面，把真实 endpoint 填入上方地址。</div>'
    : '<div class="hintbox">ℹ️ 该接口未做实测（多为需鉴权或非 HTTPS）。填入真实 endpoint 后可随时试调。</div>';
  $("result").innerHTML = curPathMissingTip() + tip;

  drawer.classList.add("on"); mask.classList.add("on");
  if (opts.auto) doCall();
}

function renderParams(){
  $("pbox").innerHTML = curParams.map((p,i) =>
    `<div class="prow"><input placeholder="参数名" value="${esc(p.k)}" data-pk="${i}">
      <input placeholder="值" value="${esc(p.v)}" data-pv="${i}">
      <button class="del" data-pd="${i}">✕</button></div>`).join("");
  $("pbox").querySelectorAll("[data-pk]").forEach(inp => inp.oninput = e => {
    curParams[+inp.dataset.pk].k = e.target.value; refreshSnip();
  });
  $("pbox").querySelectorAll("[data-pv]").forEach(inp => inp.oninput = e => {
    curParams[+inp.dataset.pv].v = e.target.value; refreshSnip();
  });
  $("pbox").querySelectorAll("[data-pd]").forEach(b => b.onclick = () => {
    curParams.splice(+b.dataset.pd, 1); renderParams(); refreshSnip();
  });
}
/* 路径参数：{owner} / {username} 之类，一律留空由用户自己填 */
function markNeed(box){
  box.querySelectorAll("[data-pp2]").forEach(inp => inp.classList.toggle("need", !inp.value.trim()));
}
function curPathMissingTip(){
  const miss = missingPath();
  if (!miss.length) return "";
  return '<div class="hintbox">📝 该接口需要你先填写 ' +
    miss.map(k => '<b>{' + esc(k) + '}</b>').join("、") +
    ' —— 涉及个人账号 / 仓库信息的一律留空，由你自己填。</div>';
}
function renderPathParams(){
  const box = $("pathBox"); if (!box) return;
  const keys = placeholders($("urlInput") ? $("urlInput").value : "");
  box.innerHTML = keys.map(k => {
    const meta = ((cur && cur.params) || []).filter(p => p.k === k)[0] || {};
    return '<div class="rt-param"><label>{' + esc(k) + '}</label>' +
      '<input data-pp2="' + esc(k) + '" autocomplete="off" placeholder="' +
      esc(meta.ph || ("请填写 " + k)) + '" value="' + esc(curPathVals[k] || "") + '"></div>';
  }).join("");
  box.querySelectorAll("[data-pp2]").forEach(inp => {
    inp.oninput = () => { curPathVals[inp.dataset.pp2] = inp.value.trim(); markNeed(box); refreshSnip(); };
  });
  markNeed(box);
}
function renderHeaders(){
  const keys = Object.keys(curHeaders);
  $("hbox").innerHTML = keys.map((k,i) =>
    `<div class="prow"><input placeholder="Header" value="${esc(k)}" data-hk="${i}">
      <input placeholder="值" value="${esc(curHeaders[k])}" data-hv="${i}">
      <button class="del" data-hd="${i}">✕</button></div>`).join("");
  $("hbox").querySelectorAll("[data-hk]").forEach(inp => inp.oninput = e => {
    const old = Object.keys(curHeaders)[+inp.dataset.hk];
    const v = curHeaders[old]; delete curHeaders[old];
    curHeaders[e.target.value] = v; refreshSnip();
  });
  $("hbox").querySelectorAll("[data-hv]").forEach(inp => inp.oninput = e => {
    curHeaders[Object.keys(curHeaders)[+inp.dataset.hv]] = e.target.value; refreshSnip();
  });
  $("hbox").querySelectorAll("[data-hd]").forEach(b => b.onclick = () => {
    delete curHeaders[Object.keys(curHeaders)[+b.dataset.hd]]; renderHeaders(); refreshSnip();
  });
}
function refreshSnip(){
  const s = snippets(buildUrl(), curHeaders);
  $("snip").textContent = s[snipTab];
}

/* ---------- 智能结果渲染：文本出文本、图片出图片 ---------- */
const IMG_EXT = /\.(jpe?g|png|gif|svg|webp|bmp|ico|avif)(\?|#|$)/i;
const IMG_HOST = /(^|\.)(images?|photos?|thumbs?|img|pic|cdn|media|static|assets)\.[^.]+\.[a-z]{2,}$/i;
function isImgUrl(s){
  if (typeof s !== "string") return false;
  const u = s.trim();
  if (!/^https?:\/\//i.test(u)) return false;
  if (IMG_EXT.test(u)) return true;
  try { return IMG_HOST.test(new URL(u).hostname); } catch(e){ return false; }
}
function collectImages(obj, out, depth){
  out = out || []; depth = depth || 0;
  if (depth > 4 || out.length >= 4) return out;
  if (typeof obj === "string"){ if (isImgUrl(obj)) out.push(obj.trim()); return out; }
  if (Array.isArray(obj)){ obj.slice(0, 6).forEach(v => collectImages(v, out, depth + 1)); return out; }
  if (obj && typeof obj === "object") Object.values(obj).forEach(v => collectImages(v, out, depth + 1));
  return out;
}
const TEXT_KEYS = ["fact","joke","setup","punchline","quote","text","activity","advice","slip",
  "definition","meaning","summary","extract","question","answer","trivia","sentence","content",
  "description","word","message","value","data","type","name","title","label","status","result"];
const MAIN_KEYS = ["fact","joke","quote","text","activity","advice","definition","meaning",
  "summary","extract","question","answer","trivia","sentence","content","description","setup","punchline"];
function collectText(obj, out, depth){
  out = out || []; depth = depth || 0;
  if (depth > 3 || out.length >= 6) return out;
  if (Array.isArray(obj)){ obj.slice(0, 3).forEach(v => collectText(v, out, depth + 1)); return out; }
  if (obj && typeof obj === "object"){
    Object.keys(obj).forEach(k => {
      const v = obj[k];
      if (typeof v === "string"){
        const t = v.trim();
        if (t && t.length <= 400 && !isImgUrl(t) && TEXT_KEYS.indexOf(k.toLowerCase()) >= 0) out.push({ k, v: t });
      } else if (v && typeof v === "object"){
        collectText(v, out, depth + 1);
      }
    });
  }
  return out;
}
// 正文类字段优先，其次按长度降序 —— 避免把 type:"single" 当成主内容
function rankText(list){
  return list.slice().sort((a, b) => {
    const ra = MAIN_KEYS.indexOf(a.k.toLowerCase()), rb = MAIN_KEYS.indexOf(b.k.toLowerCase());
    if ((ra >= 0) !== (rb >= 0)) return ra >= 0 ? -1 : 1;
    return b.v.length - a.v.length;
  });
}
/* 结构化数据全量展开：不丢字段（上限只为防止超大响应卡死页面） */
const MAX_ROWS = 400, MAX_DEPTH = 5, MAX_COLS = 14;
function flattenKV(obj, rows, prefix, depth){
  rows = rows || []; prefix = prefix || ""; depth = depth || 0;
  if (rows.length >= MAX_ROWS || depth > MAX_DEPTH) return rows;
  if (Array.isArray(obj)){
    if (!obj.length) rows.push([prefix || "(空数组)", "—"]);
    else obj.forEach((v, i) => {
      if (rows.length >= MAX_ROWS) return;
      flattenKV(v, rows, prefix + "[" + i + "]", depth + 1);
    });
    return rows;
  }
  if (obj && typeof obj === "object"){
    const keys = Object.keys(obj);
    if (!keys.length) rows.push([prefix || "(空对象)", "—"]);
    keys.forEach(k => {
      if (rows.length >= MAX_ROWS) return;
      const v = obj[k], path = prefix ? prefix + "." + k : k;
      if (v && typeof v === "object") flattenKV(v, rows, path, depth + 1);
      else rows.push([path, v === null ? "null" : String(v)]);
    });
    return rows;
  }
  rows.push([prefix, String(obj)]);
  return rows;
}
function flatStr(v){
  if (v === null || v === undefined) return "";
  if (typeof v === "object"){
    try { const s = JSON.stringify(v); return s.length > 140 ? s.slice(0, 140) + "…" : s; }
    catch(e){ return String(v); }
  }
  return String(v);
}
// 单元格：图片地址渲染缩略图，长文本截断并挂 title
function cellHTML(v){
  if (v === null || v === undefined) return '<span class="rt-nil">null</span>';
  if (typeof v === "string" && isImgUrl(v)) return '<img class="rt-thumb" src="' + esc(v) + '" loading="lazy" alt="">';
  const t = flatStr(v);
  if (!t) return '<span class="rt-nil">空</span>';
  return t.length > 90
    ? '<span title="' + esc(t) + '">' + esc(t.slice(0, 90)) + '…</span>'
    : esc(t);
}
function shortVal(v){
  if (v == null) return "—";
  const s = String(v);
  return s.length > 150 ? s.slice(0, 150) + "…" : s;
}
function imgHTML(urls){
  return urls.map(u =>
    '<div class="rt-img"><img src="' + esc(u) + '" alt="接口返回的图片" loading="lazy"></div>').join("");
}
function textHTML(list){
  if (!list.length) return "";
  let h = '<div class="rt-big">' + esc(list[0].v) + '</div>';
  const rest = list.slice(1).filter(x => x.v.length <= 50);
  if (rest.length){
    h += '<div class="rt-others">' + rest.map(x =>
      '<span class="rt-chip"><b>' + esc(x.k) + '</b>' + esc(x.v) + '</span>').join("") + '</div>';
  }
  return h;
}
function kvHTML(rows){
  if (!rows.length) return "";
  return '<table class="rt-kv">' + rows.map(r =>
    '<tr><td>' + esc(r[0]) + '</td><td>' + cellHTML(r[1]) + '</td></tr>').join("") + '</table>';
}
// 数组 → 全量表格（所有元素都渲染，列 = 各元素顶层字段的并集）
function arrTableHTML(arr){
  const rows = arr.slice(0, MAX_ROWS);
  const objs = rows.filter(x => x && typeof x === "object" && !Array.isArray(x));
  if (!objs.length){
    return '<table class="rt-kv rt-list"><thead><tr><th class="idx">#</th><th>值</th></tr></thead><tbody>' +
      rows.map((v, i) => '<tr><td class="idx">' + i + '</td><td>' + cellHTML(v) + '</td></tr>').join("") +
      '</tbody></table>';
  }
  const cols = [];
  rows.forEach(x => {
    if (x && typeof x === "object" && !Array.isArray(x)) {
      Object.keys(x).forEach(k => { if (cols.indexOf(k) < 0) cols.push(k); });
    }
  });
  const use = cols.slice(0, MAX_COLS), hidden = cols.slice(MAX_COLS);
  let h = '<table class="rt-kv rt-list"><thead><tr><th class="idx">#</th>' +
    use.map(c => '<th>' + esc(c) + '</th>').join("") +
    (hidden.length ? '<th>其余</th>' : '') + '</tr></thead><tbody>';
  rows.forEach((x, i) => {
    h += '<tr><td class="idx">' + i + '</td>' +
      use.map(c => '<td>' + cellHTML(x && typeof x === "object" ? x[c] : null) + '</td>').join("");
    if (hidden.length){
      const extra = {};
      hidden.forEach(c => { if (x && x[c] !== undefined) extra[c] = x[c]; });
      const n = Object.keys(extra).length;
      h += '<td>' + (n ? '<span title="' + esc(flatStr(extra)) + '">+' + n + ' 项</span>' : '—') + '</td>';
    }
    h += '</tr>';
  });
  return h + '</tbody></table>';
}
function renderSmart(body, isJSON){
  if (!isJSON){
    const t = String(body == null ? "" : body).trim();
    if (isImgUrl(t)) return { html: imgHTML([t]), kind: "image" };
    return { html: '<div class="rt-text">' + esc(t.slice(0, 4000) || "（响应为空）") + '</div>', kind: "text" };
  }
  const imgs = collectImages(body);
  const texts = rankText(collectText(body));

  // ① 顶层数组 → 全量列表（每一项都渲染，可滚动）
  if (Array.isArray(body)){
    if (!body.length) return { html: '<div class="rt-text">（空数组）</div>', kind: "text" };
    let h = "";
    if (imgs.length) h += imgHTML(imgs);
    h += '<div class="rt-note">列表数据 · 共 ' + body.length + ' 项</div>' + arrTableHTML(body);
    if (body.length > MAX_ROWS) h += '<div class="rt-tip">共 ' + body.length + ' 项，仅显示前 ' + MAX_ROWS + ' 项（完整内容见「原始 JSON」）。</div>';
    return { html: h, kind: "list" };
  }

  const rows = flattenKV(body);

  // ② 纯图片
  if (imgs.length && !rows.length) return { html: imgHTML(imgs), kind: "image" };

  // ③ 图片 + 结构化数据：图片在上，下方补全「全部字段」，不再丢数据
  if (imgs.length){
    let h = imgHTML(imgs);
    if (texts.length) h += '<div class="rt-note">主要内容</div>' + textHTML(texts);
    if (rows.length) h += '<div class="rt-note">全部字段 · ' + rows.length + ' 项</div>' + kvHTML(rows);
    if (rows.length >= MAX_ROWS) h += '<div class="rt-tip">字段较多，仅显示前 ' + MAX_ROWS + ' 项（完整内容见「原始 JSON」）。</div>';
    return { html: h, kind: "mixed" };
  }

  // ④ 文本为主：正文 + 其余未展示字段
  if (texts.length){
    let h = textHTML(texts);
    const shown = {};
    texts.forEach(x => { shown[x.k] = 1; });
    const extra = rows.filter(r => !(r[0] in shown));
    if (extra.length) h += '<div class="rt-note">其他字段 · ' + extra.length + ' 项</div>' + kvHTML(extra);
    return { html: h, kind: "text" };
  }

  // ⑤ 纯结构化 → 全字段表
  if (rows.length){
    let h = kvHTML(rows);
    if (rows.length >= MAX_ROWS) h += '<div class="rt-tip">字段较多，仅显示前 ' + MAX_ROWS + ' 项（完整内容见「原始 JSON」）。</div>';
    return { html: h, kind: "table" };
  }
  return { html: '<div class="rt-text">' + esc(JSON.stringify(body)) + '</div>', kind: "text" };
}
function bindImgErrors(root){
  root.querySelectorAll(".rt-img img").forEach(im => {
    im.onerror = () => {
      const url = im.getAttribute("src") || "";
      im.parentNode.innerHTML = '<div class="rt-err">🖼 图片加载失败<br>' + esc(url) + '</div>';
    };
  });
}

/* ---------- JSON 高亮 ---------- */
function hlJSON(obj){
  let s;
  try { s = JSON.stringify(obj, null, 2); } catch(e){ s = String(obj); }
  if (s == null) s = String(obj);
  s = s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  return s.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    m => {
      let c = "j-num";
      if (/^"/.test(m)) c = /:$/.test(m) ? "j-key" : "j-str";
      else if (/true|false/.test(m)) c = "j-bool";
      else if (/null/.test(m)) c = "j-null";
      return '<span class="' + c + '">' + m + '</span>';
    });
}

/* ================= 调用通道：本地代理优先 ================= */
let PROXY = false;
function isImageApi(url, d){
  if (d && d.t === "image") return true;
  return /\.(jpe?g|png|gif|svg|webp|bmp|ico)(\?|#|$)/i.test(url || "");
}
function b64url(s){
  return btoa(unescape(encodeURIComponent(s)))
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
async function callApi(url, headers){
  if (PROXY){
    let q = "/api/proxy?url=" + encodeURIComponent(url);
    if (headers && Object.keys(headers).length) q += "&h=" + b64url(JSON.stringify(headers));
    const r = await fetch(q, { cache: "no-store" });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || ("HTTP " + (j.status || "?")));
    return { status: j.status, ms: j.ms, bytes: j.bytes,
             text: j.dataUri ? null : j.body, dataUri: j.dataUri || null, via: "proxy" };
  }
  const t0 = performance.now();
  const res = await fetch(url, { headers: headers || {}, mode: "cors" });
  const text = await res.text();
  return { status: res.status, ms: Math.round(performance.now() - t0),
           bytes: new Blob([text]).size, text, dataUri: null, via: "direct" };
}
async function detectProxy(){
  try {
    const r = await fetch("/api/proxy?url=" + encodeURIComponent("https://catfact.ninja/fact"),
                          { cache: "no-store" });
    if (r.ok){ const j = await r.json(); PROXY = !!j.ok; }
  } catch(e){ PROXY = false; }
  const el = $("modeBadge");
  if (el){
    if (PROXY){
      el.className = "mode on";
      el.innerHTML = "🟢 <b>本地代理已连接</b> · 全部接口均可调用（已绕过跨域限制）";
    } else {
      el.className = "mode off";
      el.innerHTML = "🟡 <b>直连模式</b> · 仅跨域开放的接口可用 —— 运行 <b>serve.py</b> 可解锁全部接口";
    }
  }
}

/* ---------- 真正发起调用 ---------- */
async function doCall(){
  const miss = missingPath();
  if (miss.length){
    const box = $("pathBox");
    if (box){
      markNeed(box);
      const first = box.querySelector("[data-pp2]");
      if (first) first.focus();
    }
    showToast("请先填写：" + miss.map(k => "{" + k + "}").join("、"));
    $("result").innerHTML = '<div class="hintbox">📝 这个接口需要你提供 ' +
      miss.map(k => '<b>{' + esc(k) + '}</b>').join("、") +
      ' 才能调用（涉及个人账号/仓库信息，留空由你自己填）。填好后点「发送请求」。</div>';
    return;
  }
  const url = buildUrl();
  const btn = $("sendBtn");
  btn.disabled = true;
  btn.textContent = "请求中…";
  let host = "";
  try { host = new URL(url, location.href).host; } catch(e){ host = url.slice(0, 48); }
  $("result").innerHTML = '<div class="loading"><div class="spin"></div>正在请求 ' + esc(host) + ' …</div>';

  // 图片接口：渲染图片（代理模式取 dataURI，直连模式用 <img> 探测，不受 CORS 限制）
  if (isImageApi(url, cur)){
    const reset = () => { btn.disabled = false; btn.textContent = "▷ 发送请求"; };
    if (PROXY){
      try {
        const r = await callApi(url, curHeaders);
        lastResult = { url, status: r.status, elapsed: r.ms,
                       dataUri: r.dataUri, via: r.via, error: r.dataUri ? null : "该地址返回的不是图片" };
      } catch(err){
        lastResult = { url, error: String(err && err.message || err) };
      }
      renderResult(); reset(); return;
    }
    const t0i = performance.now();
    const im = new Image();
    im.onload = () => {
      lastResult = { url, status: 200, elapsed: Math.round(performance.now() - t0i),
                     dataUri: url, via: "direct" };
      renderResult(); reset();
    };
    im.onerror = () => {
      lastResult = { url, error: "图片加载失败（可能未开放跨域、需鉴权或站点不可达）",
                     elapsed: Math.round(performance.now() - t0i) };
      renderResult(); reset();
    };
    im.src = url;
    return;
  }

  const t0 = performance.now();
  try {
    const r = await callApi(url, curHeaders);
    const text = r.text != null ? r.text : "[二进制内容，已按图片渲染]";
    let body = text, isJSON = false;
    try { body = JSON.parse(text); isJSON = true; } catch(e){}
    lastResult = { url, status: r.status, elapsed: r.ms, isJSON, body, text,
                   dataUri: r.dataUri, via: r.via };
    renderResult();
  } catch (err){
    lastResult = { url, error: String(err && err.message || err),
                   elapsed: Math.round(performance.now() - t0) };
    renderResult();
  } finally {
    btn.disabled = false;
    btn.textContent = "▷ 发送请求";
  }
}

function renderResult(){
  const r = lastResult; if (!r) return;
  if (r.dataUri){
    $("result").innerHTML =
      '<div class="res-meta"><span class="mtag s2">HTTP ' + r.status + '</span>' +
      '<span class="mtag muted">' + r.elapsed + ' ms</span>' +
      '<span class="mtag muted">图片</span>' +
      '<span class="mtag ' + (r.via === "proxy" ? "s2" : "muted") + '">' +
        (r.via === "proxy" ? "代理转发" : "直连") + '</span></div>' +
      '<img src="' + r.dataUri + '" style="max-width:100%;border-radius:9px;border:1px solid var(--line2)">';
    return;
  }
  if (r.error){
    $("result").innerHTML =
      '<div class="res-meta"><span class="mtag s4">请求失败</span>' +
      '<span class="mtag muted">' + r.elapsed + ' ms</span></div>' +
      '<div class="hintbox err">' + esc(r.error) + '</div>' +
      '<div class="hintbox">常见原因：<b>CORS 未开放</b>（服务器不允许浏览器跨域）、网络不可达、或该地址不是数据端点。' +
      '可切换到「等价代码」用 cURL / Python 在本地或服务端调用。</div>' +
      '<div class="res-tabs"><button class="on">原始错误</button></div>' +
      '<pre class="code">' + esc(r.error) + '</pre>';
    return;
  }
  const ok = r.status >= 200 && r.status < 300;
  const cls = r.status >= 400 ? "s4" : ok ? "s2" : "muted";
  const size = (new Blob([r.text]).size / 1024).toFixed(1);
  const smart = renderSmart(r.isJSON ? r.body : r.text, r.isJSON);
  const rawHTML = '<pre class="code" style="max-height:340px">' +
    (r.isJSON ? hlJSON(r.body) : esc(r.text.slice(0, 20000))) + '</pre>';
  $("result").innerHTML =
    '<div class="res-meta">' +
      '<span class="mtag ' + cls + '">HTTP ' + r.status + '</span>' +
      '<span class="mtag muted">' + r.elapsed + ' ms</span>' +
      '<span class="mtag muted">' + size + ' KB</span>' +
      '<span class="mtag ' + (r.via === "proxy" ? "s2" : "muted") + '">' +
        (r.via === "proxy" ? "代理转发" : "直连") + '</span>' +
      '<span class="mtag ' + (r.isJSON ? "s2" : "muted") + '">' + (r.isJSON ? "JSON" : "文本") + '</span>' +
      '<span style="margin-left:auto;display:flex;gap:6px">' +
        '<button class="btn icon" id="dlRes" title="下载结果">⭳</button>' +
        '<button class="btn icon" id="cpRes" title="复制结果">⧉</button>' +
      '</span></div>' +
    '<div class="res-tabs"><button data-rt="smart" class="on">✨ 渲染结果</button>' +
      '<button data-rt="raw">' + (r.isJSON ? "{} 原始 JSON" : "原始文本") + '</button></div>' +
    '<div id="resBox">' + smart.html + '</div>';
  const cp = $("cpRes"); if (cp) cp.onclick = () => copy(r.isJSON ? JSON.stringify(r.body, null, 2) : r.text, "结果已复制");
  const dl = $("dlRes"); if (dl) dl.onclick = () => {
    const blob = new Blob([r.isJSON ? JSON.stringify(r.body, null, 2) : r.text],
                          { type: r.isJSON ? "application/json" : "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = (cur ? cur.n.replace(/[^\w\u4e00-\u9fa5-]/g, "_") : "result") + ".json";
    a.click(); URL.revokeObjectURL(a.href);
  };
  const resBox = $("resBox");
  bindImgErrors(resBox);
  $("result").querySelectorAll("[data-rt]").forEach(b => b.onclick = () => {
    const v = b.dataset.rt;
    $("result").querySelectorAll("[data-rt]").forEach(x => x.classList.toggle("on", x === b));
    resBox.innerHTML = v === "smart" ? smart.html : rawHTML;
    bindImgErrors(resBox);
  });
}

/* ---------- 顶栏筛选绑定 ---------- */
function bindSeg(id, key, cb){
  $(id).querySelectorAll("button").forEach(b => b.onclick = () => {
    $(id).querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
    state[key] = b.dataset[key]; state.shown = PAGE; cb && cb();
  });
}
$("segCall").querySelectorAll("button").forEach(b => b.onclick = () => {
  $("segCall").querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
  state.call = b.dataset.call; state.shown = PAGE; render();
});
$("segAuth").querySelectorAll("button").forEach(b => b.onclick = () => {
  $("segAuth").querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
  state.auth = b.dataset.auth; state.shown = PAGE; render();
});
$("segSort").querySelectorAll("button").forEach(b => b.onclick = () => {
  $("segSort").querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
  state.sort = b.dataset.sort; state.shown = PAGE; render();
});
$("q").oninput = e => {
  state.q = e.target.value; state.shown = PAGE;
  if (view === "curated") renderCurated(); else render();
};
document.addEventListener("keydown", e => {
  if (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA"){
    e.preventDefault(); $("q").focus();
  }
});

/* ================= 精选可直连：卡片内一键出结果 ================= */
const curState = { cat: null };
function curatedFiltered(){
  const q = state.q.trim().toLowerCase();
  return CURATED.filter(c => {
    if (curState.cat && c.category !== curState.cat) return false;
    if (!q) return true;
    const hay = (c.name + " " + (c.desc || "") + " " + c.category + " " +
                 (zhName(c.category) || "") + " " + c.url).toLowerCase();
    return q.split(/\s+/).every(t => hay.includes(t));
  });
}
function renderCuratedCats(){
  const box = $("segCurCat");
  const cats = [...new Set(CURATED.map(c => c.category))];
  box.innerHTML = `<button class="${curState.cat ? "" : "on"}" data-ccat="">全部（${CURATED.length}）</button>` +
    cats.map(k => {
      const n = CURATED.filter(c => c.category === k).length;
      return `<button class="${curState.cat === k ? "on" : ""}" data-ccat="${esc(k)}">${esc(zhName(k) || k)}（${n}）</button>`;
    }).join("");
  box.querySelectorAll("[data-ccat]").forEach(b => b.onclick = () => {
    curState.cat = b.dataset.ccat || null;
    renderCuratedCats(); renderCurated();
  });
}

function curatedAsApi(c){
  return { n: c.name, u: c.url, d: c.desc, k: c.category, st: "direct",
           t: c.type === "image" ? "image" : "direct", params: c.params || [], home: c.home || "" };
}
// URL 里的 {占位符}，例如 /repos/{owner}/{repo}
function placeholders(u){
  const m = String(u || "").match(/\{([\w.-]+)\}/g) || [];
  return [...new Set(m.map(s => s.slice(1, -1)))];
}
function fillPath(u, vals){
  return String(u || "").replace(/\{([\w.-]+)\}/g, (all, k) =>
    vals && vals[k] != null && vals[k] !== "" ? encodeURIComponent(vals[k]) : all);
}
function readPathVals(scope, idPrefix){
  const v = {};
  scope.querySelectorAll('[data-pp]').forEach(inp => { v[inp.dataset.pp] = inp.value.trim(); });
  return v;
}

function cardPathVals(card){
  const v = {};
  card.querySelectorAll("[data-pk2]").forEach(inp => { v[inp.dataset.pk2] = inp.value.trim(); });
  return v;
}
async function runCurated(i, card, vals){
  const c = CURATED[i];
  const url = fillPath(c.url, vals || {});
  const box = card.querySelector(".inline-res");
  box.style.display = "block";
  const loading = t => {
    box.innerHTML = '<div class="loading" style="padding:14px"><div class="spin"></div>' + t + '</div>';
  };
  // 图片类：代理模式走转发（拿到 data URI）；直连模式直接用 <img>（图片不受 CORS 限制）
  if (c.type === "image"){
    if (PROXY){
      loading("加载图片…");
      try {
        const r = await callApi(url, c.headers);
        box.innerHTML =
          '<div style="font-size:11.5px;color:var(--txt2);margin-bottom:7px">HTTP ' + r.status +
          ' · ' + r.ms + ' ms · 代理转发</div>' +
          '<img src="' + r.dataUri + '" alt="' + esc(c.name) + '">';
      } catch(err){
        box.innerHTML = '<div class="errline">✕ 图片加载失败：' + esc(err && err.message || err) + '</div>';
      }
      return;
    }
    loading("加载图片…");
    const t0i = performance.now();
    const im = new Image();
    im.onload = () => {
      box.innerHTML =
        '<div style="font-size:11.5px;color:var(--txt2);margin-bottom:7px">图片已加载 · ' +
        Math.round(performance.now() - t0i) + ' ms · ' + im.naturalWidth + '×' + im.naturalHeight + '</div>' +
        '<img src="' + esc(url) + '" alt="' + esc(c.name) + '">';
    };
    im.onerror = () => {
      box.innerHTML = '<div class="errline">✕ 图片加载失败（可能被网络限制或站点已下线）</div>';
    };
    im.src = url;
    return;
  }

  loading("请求中…");
  try {
    const r = await callApi(url, c.headers);
    const txt = r.text != null ? r.text : "";
    let body, isJSON = false;
    try { body = JSON.parse(txt); isJSON = true; } catch(e){}
    const kb = (r.bytes / 1024).toFixed(1);
    const smart = renderSmart(isJSON ? body : txt, isJSON);
    box.innerHTML =
      '<div style="font-size:11.5px;color:var(--txt2);margin-bottom:8px">HTTP ' + r.status +
      ' · ' + r.ms + ' ms · ' + kb + ' KB' + (isJSON ? ' · JSON' : '') +
      (r.via === "proxy" ? ' · 代理转发' : '') + '</div>' +
      '<div class="rt-box">' + smart.html + '</div>' +
      '<div style="display:flex;gap:6px;margin-top:9px">' +
        '<button class="btn icon" data-cc="' + i + '">⧉ 复制结果</button>' +
        '<button class="btn icon" data-json="' + i + '">{} 原始 JSON</button>' +
        '<button class="btn icon" data-tune2="' + i + '">⚙ 调试</button>' +
      '</div>';
    const cp = box.querySelector("[data-cc]");
    if (cp) cp.onclick = () => copy(isJSON ? JSON.stringify(body, null, 2) : txt, "结果已复制");
    const jb = box.querySelector("[data-json]");
    if (jb) jb.onclick = () => {
      const rbox = box.querySelector(".rt-box");
      const showingRaw = rbox.dataset.raw === "1";
      rbox.dataset.raw = showingRaw ? "0" : "1";
      rbox.innerHTML = showingRaw
        ? smart.html
        : '<pre class="code" style="max-height:320px">' + (isJSON ? hlJSON(body) : esc(txt)) + '</pre>';
      jb.textContent = showingRaw ? "{} 原始 JSON" : "✨ 渲染结果";
      bindImgErrors(rbox);
    };
    bindImgErrors(box);
    const tn = box.querySelector("[data-tune2]");
    if (tn) tn.onclick = () => openDrawer(curatedAsApi(c), { headers: c.headers, auto: true, pathVals: vals });
  } catch (err){
    box.innerHTML =
      '<div class="errline">✕ 请求失败：' + esc(err && err.message || err) + '</div>' +
      (PROXY
        ? '<div style="font-size:11.5px;color:var(--txt3);margin-top:7px;line-height:1.6">代理已连接，说明是上游接口本身的问题（临时故障 / 已下线）。可点下方按钮改写地址重试。</div>'
        : '<div style="font-size:11.5px;color:var(--txt3);margin-top:7px;line-height:1.6">当前是<b>直连模式</b>，受浏览器跨域与页面安全策略限制。运行 <b>serve.py</b> 启动本地服务后即可调用全部接口。</div>') +
      '<div style="margin-top:8px"><button class="btn icon" data-tune2="' + i + '">⚙ 在调试台打开</button></div>';
    const tn = box.querySelector("[data-tune2]");
    if (tn) tn.onclick = () => openDrawer(curatedAsApi(c), { headers: c.headers, auto: false, pathVals: vals });
  }
}

function renderCurated(){
  const grid = $("curatedGrid");
  const rows = curatedFiltered();
  grid.innerHTML = "";
  if (!rows.length){
    grid.innerHTML = '<div class="empty"><div class="e">🔍</div><div>该分类下暂无精选接口</div></div>';
    return;
  }
  rows.forEach(c => {
    const i = CURATED.indexOf(c);
    const link = c.home || c.url;      // 带占位符的接口，外部链接指向官方文档而非 404 模板
    const nPar = (c.params && c.params.length) ? c.params.length : 0;
    const el = document.createElement("div");
    el.className = "ccard";
    el.innerHTML =
      '<div class="ctop"><a class="cname" href="' + esc(link) + '" target="_blank" rel="noopener" title="' + esc(link) + '">' + esc(c.name) + ' <span style="opacity:.5">↗</span></a>' +
      '<span class="tag" style="color:' + catColor(c.category) + ';border-color:' + catColor(c.category) + '">' +
        esc(zhName(c.category) || c.category) + '</span></div>' +
      '<div class="cdesc">' + esc(c.desc || "") + '</div>' +
      '<a class="curl" href="' + esc(c.url) + '" target="_blank" rel="noopener">' + esc(c.url) + '</a>' +
      (nPar
        ? '<div class="rt-params" data-pbox>' +
            '<div class="phd">这个接口需要先填 <b>' + nPar + '</b> 个参数（涉及个人信息 / 仓库名的请自己填写）</div>' +
            c.params.map(p =>
              '<div class="rt-param"><label>{' + esc(p.k) + '}</label>' +
              '<input data-pk2="' + esc(p.k) + '" autocomplete="off" class="need" placeholder="' +
              esc(p.ph || ("请填写 " + p.k)) + '"></div>').join("") +
          '</div>'
        : '') +
      '<div class="cfoot">' +
        '<button class="btn primary" data-run="' + i + '">▷ 调用</button>' +
        (nPar
          ? '<button class="pdrop" data-pdrop title="这个接口需要先填写 ' + nPar + ' 个参数">' +
              '<span class="pd-n">🔧</span> 参数 <b>' + nPar + '</b></button>'
          : '') +
        '<a class="btn icon" href="' + esc(link) + '" target="_blank" rel="noopener" title="打开官方页面">↗</a>' +
        '<button class="btn icon" data-tune="' + i + '" title="高级调试（改参数 / 看代码）">⚙</button>' +
        '<span class="ctype ' + c.type + '">' + (c.type === "image" ? "图片" : "JSON") + '</span>' +
        (c.ms != null ? '<span class="tag ms">' + c.ms + 'ms</span>' : '') +
      '</div>' +
      '<div class="inline-res" style="display:none"></div>';

    // ---- 参数区：默认收起，点「🔧 参数」展开；点「调用」缺参数时自动展开并聚焦 ----
    const pbox = el.querySelector("[data-pbox]");
    const pbtn = el.querySelector("[data-pdrop]");
    const focusFirstEmpty = () => {
      if (!pbox) return;
      const f = [...pbox.querySelectorAll("[data-pk2]")].find(x => !x.value.trim());
      if (f) setTimeout(() => f.focus(), 60);
    };
    const openParams = () => {
      if (!pbox) return;
      pbox.classList.add("open");
      if (pbtn) pbtn.classList.add("on");
      focusFirstEmpty();
    };
    const syncPbtn = () => {
      if (!pbtn || !pbox) return;
      const all = [...pbox.querySelectorAll("[data-pk2]")].every(x => x.value.trim());
      pbtn.classList.toggle("done", all);
      const ic = pbtn.querySelector(".pd-n");
      if (ic) ic.textContent = all ? "✓" : "🔧";
    };
    if (pbox){
      pbox.querySelectorAll("[data-pk2]").forEach(inp => {
        inp.oninput = () => { inp.classList.toggle("need", !inp.value.trim()); syncPbtn(); };
      });
    }
    if (pbtn) pbtn.onclick = () => {
      const opened = pbox.classList.toggle("open");
      pbtn.classList.toggle("on", opened);
      if (opened) focusFirstEmpty();
    };
    el.querySelector("[data-run]").onclick = () => {
      const vals = cardPathVals(el);
      const miss = (c.params || []).filter(p => !vals[p.k]).map(p => p.k);
      if (miss.length){
        if (pbox && !pbox.classList.contains("open")) openParams();
        if (pbox) pbox.querySelectorAll("[data-pk2]").forEach(inp => {
          if (!vals[inp.dataset.pk2]) inp.classList.add("need");
        });
        showToast("请先填写：" + miss.map(k => "{" + k + "}").join("、"));
        return;
      }
      runCurated(i, el, vals);
    };
    el.querySelector("[data-tune]").onclick = () =>
      openDrawer(curatedAsApi(c), { headers: c.headers, auto: false, pathVals: cardPathVals(el) });
    grid.appendChild(el);
  });
}

/* ================= 视图切换 ================= */
let view = "curated";
function setView(v){
  view = v;
  $("viewCurated").style.display = v === "curated" ? "block" : "none";
  $("viewAll").style.display = v === "all" ? "block" : "none";
  document.querySelector(".side").style.display = v === "curated" ? "none" : "";
  document.querySelector(".layout").style.gridTemplateColumns = v === "curated" ? "1fr" : "";
  $("viewTabs").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.view === v));
  if (v === "all") render();
}
$("viewTabs").querySelectorAll("button").forEach(b => b.onclick = () => setView(b.dataset.view));

renderCuratedCats();
renderCurated();
setView("curated");
detectProxy();
</script>
</body>
</html>
"""

html = (HTML.replace("__DATA__", payload)
            .replace("__CURATED__", curated_payload)
            .replace("__ZH__", zh)
            .replace("__NCUR__", str(len(curated)))
            .replace("__TOTAL__", str(total))
            .replace("__CALLABLE__", str(callable_n))
            .replace("__IMAGES__", str(images))
            .replace("__DOCS__", str(docs))
            .replace("__DIRECT__", str(direct))
            .replace("__PROXIED__", str(proxied)))
# newline="\n"：固定用 LF，避免同一份源在 Windows / Linux 上产出不同字节的页面
open(OUT, "w", encoding="utf-8", newline="\n").write(html)
print("out=%s  %.1f KB" % (OUT, len(html.encode()) / 1024))
print("  total=%d 可调用=%d(直连%d/代理%d/图片%d) 文档页=%d 不可用=%d 未实测=%d  curated=%d" %
      (total, callable_n, direct, proxied, images, docs, bad_n, untested, len(curated)))
