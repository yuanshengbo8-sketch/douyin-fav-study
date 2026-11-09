"""检查有没有新版本。

只向 GitHub 问一句「最新版本号是多少」，不上传任何笔记、设置或个人信息。
抖音改版导致同步失效时，修好的版本会发在 GitHub Releases，这里负责让你知道。
连不上 GitHub（比如网络不好）就安静地跳过，不影响使用。可以在设置里关掉。
"""
import json
import re
import threading
import time
import urllib.error
import urllib.request

from . import __version__, config

REPO = "yuanshengbo8-sketch/douyin-fav-study"
RELEASES_URL = f"https://github.com/{REPO}/releases"
LATEST_API = f"https://api.github.com/repos/{REPO}/releases/latest"
LATEST_PAGE = f"https://github.com/{REPO}/releases/latest"
CACHE_PATH = config.DATA / "update_check.json"
INTERVAL = 12 * 3600          # 每 12 小时最多问一次
RETRY_AFTER_FAIL = 2 * 3600   # 失败后 2 小时再试

_lock = threading.Lock()
_checking = False


def parse_version(v):
    """"v1.0.10" → (1, 0, 10)；认不出就返回 None。"""
    m = re.match(r"^\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(v or ""))
    if not m:
        return None
    return tuple(int(x or 0) for x in m.groups())


def is_newer(latest, current=__version__):
    a, b = parse_version(latest), parse_version(current)
    return bool(a and b and a > b)


def install_kind():
    """installer = Windows 安装包（自带 python 文件夹）；script = 用安装脚本装的。"""
    return "installer" if (config.ROOT / "python" / "python.exe").exists() else "script"


def _load_cache():
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(d):
    try:
        tmp = CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(CACHE_PATH)
    except Exception:
        pass


def _safe_url(u):
    # 只放行本仓库在 GitHub 上的地址，网页上不会出现别的链接
    u = str(u or "")
    return u if u.startswith(f"https://github.com/{REPO}/") else RELEASES_URL


def _notes_preview(body, lines=4, chars=240):
    out = []
    for line in str(body or "").splitlines():
        line = re.sub(r"[*_`#>]+", "", line).strip(" -•\t")
        if line:
            out.append(line)
        if len(out) >= lines:
            break
    text = "\n".join(out)
    return text[:chars] + ("…" if len(text) > chars else "")


def _fetch_api(timeout):
    req = urllib.request.Request(LATEST_API, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"DouyinFavStudy/{__version__}",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.loads(r.read().decode("utf-8"))
    tag = j.get("tag_name") or ""
    if not parse_version(tag):
        raise ValueError("版本号认不出")
    return {"latest": tag.lstrip("v"), "url": _safe_url(j.get("html_url")),
            "notes": _notes_preview(j.get("body")), "published_at": j.get("published_at") or ""}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _fetch_page(timeout):
    # 备用：API 被限流时，releases/latest 页面会 302 跳到 /releases/tag/v1.2.3
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(LATEST_PAGE, method="HEAD",
                                 headers={"User-Agent": f"DouyinFavStudy/{__version__}"})
    loc = ""
    try:
        opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            loc = e.headers.get("Location") or ""
        else:
            raise
    m = re.search(r"/releases/tag/(v?[\d.]+)", loc)
    if not m:
        raise ValueError("没找到最新版本")
    tag = m.group(1)
    return {"latest": tag.lstrip("v"), "url": _safe_url(f"https://github.com/{REPO}/releases/tag/{tag}"),
            "notes": "", "published_at": ""}


def check(force=False, timeout=8):
    """真正去 GitHub 问一次（会联网，放在后台线程里调用）。返回 status()。"""
    global _checking
    with _lock:
        if _checking:
            return status()
        _checking = True
    try:
        c = _load_cache()
        now = time.time()
        wait = RETRY_AFTER_FAIL if c.get("error") else INTERVAL
        if force or now - float(c.get("checked_at") or 0) >= wait:
            res, err = None, ""
            for fn in (_fetch_api, _fetch_page):
                try:
                    res = fn(timeout)
                    break
                except Exception as e:
                    err = str(e)[:200]
            if res:
                c = {**res, "checked_at": now, "error": ""}
            else:
                c = {**c, "checked_at": now, "error": err or "连不上 GitHub"}
            _save_cache(c)
    finally:
        with _lock:
            _checking = False
    return status()


def check_in_background(force=False):
    if not force and not config.load().get("check_update", True):
        return
    threading.Thread(target=check, kwargs={"force": force}, daemon=True).start()


_last_due_check = 0.0


def maybe_check():
    """程序一直开着时，过了间隔就在后台再问一次（每分钟最多判断一次，不会频繁联网）。"""
    global _last_due_check
    now = time.time()
    if _checking or now - _last_due_check < 60:
        return
    _last_due_check = now
    c = _load_cache()
    wait = RETRY_AFTER_FAIL if c.get("error") else INTERVAL
    if now - float(c.get("checked_at") or 0) >= wait:
        check_in_background()


def status():
    """给网页看的结果（不联网，只读缓存）。"""
    c = _load_cache()
    latest = c.get("latest") or ""
    return {
        "enabled": bool(config.load().get("check_update", True)),
        "current": __version__,
        "latest": latest,
        "newer": is_newer(latest),
        "url": _safe_url(c.get("url")),
        "notes": c.get("notes") or "",
        "checked_at": c.get("checked_at") or 0,
        "error": c.get("error") or "",
        "checking": _checking,
        "install_kind": install_kind(),
    }
