# -*- coding: utf-8 -*-
"""精选一批「真实可调用」的免费公开端点并实测验证（README 里存的常是文档页而非端点）。

数据来源：https://github.com/public-apis/public-apis  (MIT License)

用法：  python3 scripts/curated_endpoints.py
输出：  data/curated_results.json
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

OUT = os.environ.get("PAP_CURATED") or os.path.join(DATA, "curated_results.json")

ORIGIN = "http://127.0.0.1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
TIMEOUT = 10
MAX_BYTES = 192 * 1024

# (名称, 分类, URL模板, 说明, 默认请求头, [强制类型], [需用户填写的参数])
# 参数定义: {"k": 参数名, "v": 默认值, "ph": 输入提示, "demo": 探测用示例值}
CURATED = [
    # ---- 趣味 / 内容 ----
    ("Cat Facts", "Animals", "https://catfact.ninja/fact", "随机猫咪冷知识", {}),
    ("Dog CEO", "Animals", "https://dog.ceo/api/breeds/image/random", "随机狗狗图片链接", {}),
    ("RandomDog", "Animals", "https://random.dog/woof.json", "随机狗狗图片 / 视频", {}),
    ("RandomDuck", "Animals", "https://random-d.uk/api/random", "随机鸭子图片", {}),
    ("RandomFox", "Animals", "https://randomfox.ca/floof/", "随机狐狸图片", {}),
    ("Shibe.Online", "Animals", "https://shibe.online/api/shibes?count=3", "随机柴犬图片", {}),
    ("TheCatAPI", "Animals", "https://api.thecatapi.com/v1/images/search", "随机猫咪图片", {}),
    ("Chuck Norris", "Entertainment", "https://api.chucknorris.io/jokes/random", "随机 Chuck Norris 段子", {}),
    ("JokeAPI", "Entertainment", "https://v2.jokeapi.dev/joke/Any?type=single", "多语言笑话", {}),
    ("Official Joke", "Entertainment", "https://official-joke-api.appspot.com/random_joke", "随机美式笑话", {}),
    ("icanhazdadjoke", "Entertainment", "https://icanhazdadjoke.com/", "冷笑话（需 JSON 头）", {"Accept": "application/json"}),
    ("Advice Slip", "Personality", "https://api.adviceslip.com/advice", "随机人生建议", {}),
    ("Quotable", "Books", "https://api.quotable.io/random", "随机名人名言", {}),
    ("Kanye Rest", "Entertainment", "https://api.kanye.rest/", "Kanye 随机语录", {}),
    ("Useless Facts", "Entertainment", "https://uselessfacts.jsph.pl/api/v2/facts/random", "无用但有趣的冷知识", {}),
    ("Bored API", "Entertainment", "https://bored-api.appbrewery.com/random", "无聊时能做什么", {}),
    ("Numbers API", "Science & Math", "http://numbersapi.com/42?json", "数字相关冷知识（HTTP）", {}),
    ("Open Trivia DB", "Games & Comics", "https://opentdb.com/api.php?amount=3", "随机问答题", {}),
    ("PokeAPI", "Games & Comics", "https://pokeapi.co/api/v2/pokemon/pikachu", "宝可梦资料", {}),
    ("Rick and Morty", "Games & Comics", "https://rickandmortyapi.com/api/character/1", "瑞克和莫蒂角色资料", {}),
    ("SWAPI", "Games & Comics", "https://swapi.dev/api/people/1", "星球大战资料", {}),
    ("Jikan (MyAnimeList)", "Anime", "https://api.jikan.moe/v4/anime?q=naruto&limit=2", "动漫资料检索", {}),
    ("TheMealDB", "Food & Drink", "https://www.themealdb.com/api/json/v1/1/random.php", "随机菜谱", {}),
    ("TheCocktailDB", "Food & Drink", "https://www.thecocktaildb.com/api/json/v1/1/random.php", "随机鸡尾酒配方", {}),
    ("Open Food Facts", "Food & Drink", "https://world.openfoodfacts.org/api/v2/product/737628064502.json", "食品营养信息", {}),
    ("Deck of Cards", "Games & Comics", "https://deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1", "洗牌发牌", {}),
    # ---- 地理 / 位置 ----
    ("REST Countries", "Geocoding", "https://restcountries.com/v3.1/name/china", "国家信息（中文支持）", {}),
    ("Universities List", "Open Data", "http://universities.hipolabs.com/search?name=tsinghua", "全球大学名单（HTTP）", {}),
    ("Nominatim (OSM)", "Geocoding", "https://nominatim.openstreetmap.org/search?q=beijing&format=json&limit=2", "地名地理编码", {}),
    ("Zippopotam", "Geocoding", "https://api.zippopotam.us/us/90210", "邮编查地理位置", {}),
    ("IPify", "Development", "https://api.ipify.org?format=json", "获取当前公网 IP", {}),
    ("ipinfo", "Development", "https://ipinfo.io/json", "IP 归属地信息", {}),
    ("IP-API", "Development", "http://ip-api.com/json/8.8.8.8", "IP 归属地（HTTP）", {}),
    ("Agify", "Personality", "https://api.agify.io?name=jack", "根据名字预测年龄", {}),
    ("Genderize", "Personality", "https://api.genderize.io?name=lucy", "根据名字预测性别", {}),
    ("Nationalize", "Personality", "https://api.nationalize.io?name=chen", "根据名字预测国籍", {}),
    # ---- 天气 / 环境 ----
    ("Open-Meteo", "Weather", "https://api.open-meteo.com/v1/forecast?latitude=39.9&longitude=116.4&current=temperature_2m", "免费天气（无需 Key）", {}),
    ("wttr.in", "Weather", "https://wttr.in/Beijing?format=j1", "命令行风格天气", {}),
    ("USGS Earthquake", "Environment", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson", "近一月显著地震", {}),
    ("Sunrise-Sunset", "Environment", "https://api.sunrise-sunset.org/json?lat=39.9&lng=116.4", "日出日落时间", {}),
    # ---- 金融 / 汇率 ----
    ("Frankfurter", "Currency Exchange", "https://api.frankfurter.app/latest?from=CNY", "欧洲央行汇率", {}),
    ("ER-API", "Currency Exchange", "https://open.er-api.com/v6/latest/USD", "全球汇率（免费）", {}),
    ("CoinGecko Ping", "Cryptocurrency", "https://api.coingecko.com/api/v3/ping", "CoinGecko 存活检测", {}),
    ("CoinGecko Price", "Cryptocurrency", "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=cny", "加密货币价格", {}),
    ("CoinCap", "Cryptocurrency", "https://api.coincap.io/v2/assets?limit=3", "加密资产行情", {}),
    ("Binance Ticker", "Cryptocurrency", "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", "币安实时价格", {}),
    # ---- 图书 / 文本 / 知识 ----
    ("Open Library", "Books", "https://openlibrary.org/search.json?q=python&limit=3", "图书检索", {}),
    ("Datamuse", "Dictionaries", "https://api.datamuse.com/words?rel_rhy=code", "英文押韵 / 近义词", {}),
    ("Free Dictionary", "Dictionaries", "https://api.dictionaryapi.dev/api/v2/entries/en/hello", "英文词典释义", {}),
    ("Wikipedia Summary", "Open Data", "https://zh.wikipedia.org/api/rest_v1/page/summary/%E5%8C%97%E4%BA%AC", "维基百科摘要", {}),
    ("Art Institute", "Art & Design", "https://api.artic.edu/api/v1/artworks?limit=2", "芝加哥艺术馆藏品", {}),
    # ---- 政务 / 节假日 ----
    ("UK Bank Holidays", "Government", "https://www.gov.uk/bank-holidays.json", "英国公共假日", {}),
    ("Nager.Date", "Calendar", "https://date.nager.at/api/v3/PublicHolidays/2026/CN", "全球公共假日", {}),
    # ---- 开发 / 测试 ----
    # 末尾可挂: (……, 强制类型, 路径参数, 官方文档页 home)
    ("GitHub Repo", "Development", "https://api.github.com/repos/{owner}/{repo}", "GitHub 仓库信息",
     {}, None, [{"k": "owner", "v": "", "ph": "仓库作者，如 torvalds", "demo": "public-apis"},
                {"k": "repo", "v": "", "ph": "仓库名，如 linux", "demo": "public-apis"}],
     "https://docs.github.com/rest/repos/repos#get-a-repository"),
    ("GitHub User", "Development", "https://api.github.com/users/{username}", "GitHub 用户信息",
     {}, None, [{"k": "username", "v": "", "ph": "你的 GitHub 用户名", "demo": "octocat"}],
     "https://docs.github.com/rest/users/users#get-a-user"),
    ("npm registry", "Development", "https://registry.npmjs.org/react/latest", "npm 包元数据", {}),
    ("PyPI", "Development", "https://pypi.org/pypi/requests/json", "PyPI 包元数据", {}),
    ("crates.io", "Development", "https://crates.io/api/v1/crates/serde", "Rust 包元数据", {}),
    ("CDNJS", "Development", "https://api.cdnjs.com/libraries/jquery", "CDN 库信息", {}),
    ("StackExchange", "Development", "https://api.stackexchange.com/2.3/questions?site=stackoverflow&pagesize=2", "Stack Overflow 热门问题", {}),
    ("JSONPlaceholder", "Test Data", "https://jsonplaceholder.typicode.com/posts/1", "假数据接口", {}),
    ("DummyJSON", "Test Data", "https://dummyjson.com/products/1", "假商品数据", {}),
    ("RandomUser", "Test Data", "https://randomuser.me/api/", "随机假用户", {}),
    ("Fake Store", "Test Data", "https://fakestoreapi.com/products/1", "假电商数据", {}),
    ("httpbin IP", "Test Data", "https://httpbin.org/ip", "回显请求 IP", {}),
    ("httpbin UUID", "Test Data", "https://httpbin.org/uuid", "生成 UUID", {}),
    # ---- 太空 / 科学 ----
    ("SpaceX", "Science & Math", "https://api.spacexdata.com/v4/launches/latest", "SpaceX 最新发射", {}),
    ("ISS Location", "Science & Math", "http://api.open-notify.org/iss-now.json", "国际空间站位置（HTTP）", {}),
    ("NASA APOD", "Science & Math", "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", "NASA 每日天文图（DEMO_KEY）", {}),
    # ---- 购物 / 其他 ----
    ("CheapShark", "Shopping", "https://www.cheapshark.com/api/1.0/deals?pageSize=3", "游戏折扣", {}),
    ("Picsum Photos", "Photography", "https://picsum.photos/v2/list?page=1&limit=3", "随机图片列表", {}),
    # ---- 图片类（非 JSON，以图片形式展示）----
    ("HTTP Cat", "Animals", "https://http.cat/200", "HTTP 状态码猫咪图", {}, "image"),
    ("HTTP Dog", "Animals", "https://http.dog/200.jpg", "HTTP 状态码狗狗图", {}, "image"),
    ("PlaceDog", "Animals", "https://place.dog/300/200", "狗狗占位图", {}, "image"),
    ("PlaceBear", "Animals", "https://placebear.com/300/200", "熊占位图", {}, "image"),
]


def probe(item):
    name, cat, url, desc, headers, *rest = item
    forced = rest[0] if rest else None
    params = rest[1] if len(rest) > 1 and rest[1] else []
    home = rest[2] if len(rest) > 2 and rest[2] else ""
    # 用示例值拼出可探测的真实地址（模板里带 {占位符}）
    real_url = url
    for p in params:
        real_url = real_url.replace("{%s}" % p["k"], p.get("demo") or "")
    out = {"name": name, "category": cat, "url": url, "desc": desc, "params": params,
           "home": home,
           "headers": headers, "type": forced or "json",
           "status": None, "ms": None, "ok": False, "acao": "", "ctype": "", "note": ""}
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
         "Origin": ORIGIN, "Accept-Encoding": "identity"}
    h.update(headers)
    t0 = time.time()
    try:
        req = urllib.request.Request(real_url, headers=h)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            out["status"] = resp.status
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            out["ctype"] = ctype
            out["acao"] = (resp.headers.get("Access-Control-Allow-Origin") or "").strip()
            raw = resp.read(MAX_BYTES)
        out["ms"] = int((time.time() - t0) * 1000)
        cors_ok = out["acao"] == "*" or ORIGIN in out["acao"]
        if ctype.startswith("image/"):
            out["type"] = "image"
            out["ok"] = True                       # <img> 不受 CORS 限制
        else:
            txt = raw.decode("utf-8", "replace").lstrip()
            is_json = False
            try:
                json.loads(raw.decode("utf-8", "replace")); is_json = True
            except Exception:
                is_json = txt[:1] in "[{"
            out["type"] = "json"
            out["ok"] = bool(is_json and cors_ok)
            if is_json and not cors_ok:
                out["note"] = "无 CORS"
            elif not is_json:
                out["note"] = "非 JSON"
    except urllib.error.HTTPError as e:
        out["status"] = e.code
        out["ms"] = int((time.time() - t0) * 1000)
        out["note"] = "HTTP %s" % e.code
    except Exception as e:
        out["ms"] = int((time.time() - t0) * 1000)
        out["note"] = type(e).__name__
    return out


def main():
    print("curated=%d" % len(CURATED), flush=True)
    with cf.ThreadPoolExecutor(20) as ex:
        results = list(ex.map(probe, CURATED))
    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ok = [r for r in results if r["ok"]]
    bad = [r for r in results if not r["ok"]]
    print("可用=%d  不可用=%d" % (len(ok), len(bad)))
    print("--- 可用 ---")
    for r in ok:
        print("  %-22s %-5s %s" % (r["name"], r["type"], r["url"][:66]))
    if bad:
        print("--- 不可用 ---")
        for r in bad:
            print("  %-22s %-16s %s" % (r["name"], r["note"] or ("HTTP %s" % r["status"]), r["url"][:56]))


if __name__ == "__main__":
    main()
