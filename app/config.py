"""设置读写与路径。所有数据都放在程序目录下的 data/ 里，删掉程序文件夹就全部清干净。"""
import json
import os
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = DATA / "library.db"
SETTINGS_PATH = DATA / "settings.json"
MEDIA_DIR = DATA / "media"          # 临时视频，转录完即删
INBOX_DIR = DATA / "inbox"          # 手动放进来的本地视频
MODELS_DIR = DATA / "models"        # Whisper 模型缓存
BROWSER_DIR = DATA / "browser"      # 抖音登录态（浏览器配置目录）
DEFAULT_LIBRARY = DATA / "知识库"    # Markdown 笔记（可当 Obsidian 库打开）

for d in (DATA, MEDIA_DIR, INBOX_DIR, MODELS_DIR, BROWSER_DIR):
    d.mkdir(parents=True, exist_ok=True)

# AI 服务商预设。kind=openai 走 OpenAI 兼容的 /chat/completions；kind=anthropic 走 Claude 原生接口。
# 模型名各家会更新，设置页里可以随时改。
PROVIDERS = {
    "anthropic": {"name": "Claude（Anthropic）", "base_url": "https://api.anthropic.com", "model": "claude-sonnet-5-5",
                  "key_url": "https://console.anthropic.com/settings/keys", "kind": "anthropic",
                  "models": ["claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-5-5"]},
    "deepseek": {"name": "DeepSeek", "base_url": "https://api.deepseek.com", "model": "deepseek-chat",
                 "key_url": "https://platform.deepseek.com/api_keys", "models": ["deepseek-chat", "deepseek-reasoner"]},
    "kimi": {"name": "Kimi（月之暗面）", "base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k",
             "key_url": "https://platform.moonshot.cn/console/api-keys"},
    "qwen": {"name": "通义千问", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus",
             "key_url": "https://bailian.console.aliyun.com/"},
    "zhipu": {"name": "智谱 GLM", "base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4.7-flash",
              "models": ["glm-4.7-flash", "glm-4.5-flash"],
              "key_url": "https://open.bigmodel.cn/usercenter/apikeys"},
    "siliconflow": {"name": "硅基流动", "base_url": "https://api.siliconflow.cn/v1", "model": "deepseek-ai/DeepSeek-V3",
                    "key_url": "https://cloud.siliconflow.cn/account/ak"},
    "openai": {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini",
               "key_url": "https://platform.openai.com/api-keys"},
    "custom": {"name": "自定义（任意 OpenAI 兼容接口）", "base_url": "", "model": "", "key_url": ""},
}

# 免费方案：每个用户用自己账号的免费额度（不把谁的 Key 打包进软件）。
# models 是按优先顺序尝试的免费模型；服务商会更新模型，一键配置时会先读服务商的模型列表再挑。
FREE_PLANS = {
    "zhipu": {
        "name": "智谱 GLM", "tag": "国内推荐", "provider": "zhipu",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4.7-flash", "glm-4.5-flash", "glm-4-flash-250414", "glm-4-flash"],
        "pick": ["glm", "flash"], "avoid": ["flashx", "air", "plus", "vision", "4v", "voice", "image", "video"],
        "signup": "https://open.bigmodel.cn/", "key_url": "https://open.bigmodel.cn/usercenter/apikeys",
        "desc": "国内直连，Flash 系列模型免费调用，中文好。手机号注册即可。",
    },
    "siliconflow": {
        "name": "硅基流动", "tag": "国内", "provider": "siliconflow",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["Qwen/Qwen3-8B", "THUDM/GLM-4-9B-0414", "THUDM/glm-4-9b-chat", "Qwen/Qwen2.5-7B-Instruct"],
        "pick": [], "avoid": [],
        "signup": "https://cloud.siliconflow.cn/", "key_url": "https://cloud.siliconflow.cn/account/ak",
        "desc": "国内直连，有一批免费的小模型，注册还送体验额度。",
    },
    "gemini": {
        "name": "Google Gemini", "tag": "海外", "provider": "custom",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-3.8-flash", "gemini-2.5-flash"],
        "pick": ["gemini", "flash"], "avoid": ["image", "tts", "live", "audio", "embedding", "thinking-exp", "lite", "preview-tts"],
        "signup": "https://aistudio.google.com/", "key_url": "https://aistudio.google.com/apikey",
        "desc": "免费额度多、能力强，但国内无法直接访问；免费版的内容可能被 Google 用来改进模型。",
    },
}

DEFAULT_CATEGORIES = [
    "AI 工具推荐", "提示词技巧", "AI 编程", "AI 绘画与视频", "AI 办公效率",
    "大模型与行业资讯", "AI 副业与变现", "AI 学习方法", "其他",
]

DEFAULT_DEEP_PROMPT = (
    "这是一段视频的文字稿，我还没读。请先给我 5 句话的核心结论，再按章节列大纲，标出关键概念和术语解释；"
    "然后不要直接给答案，用提问的方式检查我是否真正理解；最后出 10 道测验题，"
    "并把要点做成「问题<Tab>答案」格式的 Anki 卡片。"
)

DEFAULTS = {
    "provider": "deepseek",
    "base_url": PROVIDERS["deepseek"]["base_url"],
    "model": PROVIDERS["deepseek"]["model"],
    "api_key": "",
    "focus_topic": "AI / 人工智能相关的干货：AI 工具、提示词、AI 编程、AI 绘画和视频、大模型、用 AI 提升效率或赚钱的方法",
    "only_relevant": True,              # 只保留和关注主题相关的视频
    "categories": DEFAULT_CATEGORIES,
    "asr_engine": "auto",               # auto / mlx / faster —— auto：苹果芯片 Mac 用 mlx，其他用 faster-whisper
    "mlx_model": "mlx-community/whisper-large-v3-turbo",
    "whisper_model": "small",           # faster-whisper 用：tiny / base / small / medium
    "use_subtitles": True,              # 视频自带字幕时直接用字幕，跳过下载和转写
    "use_hf_mirror": False,             # 在中国大陆时勾选：用 hf-mirror.com 下载模型
    "max_minutes": 15,                  # 超长视频只转录前 N 分钟
    "library_dir": "",                  # 留空 = 程序目录下的 data/知识库
    "keep_video": False,                # 转录完是否保留视频文件
    "browser": "auto",                  # auto / msedge / chrome / chromium
    "sync_limit": 50,                   # 每次同步收藏夹最多读多少条
    # ---- 精读（「有人带着读」）：可以和日常提炼用不同的模型
    "deep_same": True,                  # True = 和上面的 AI 提炼用同一个模型
    "deep_provider": "anthropic",
    "deep_base_url": PROVIDERS["anthropic"]["base_url"],
    "deep_model": PROVIDERS["anthropic"]["model"],
    "deep_api_key": "",
    "deep_prompt": DEFAULT_DEEP_PROMPT,
    "deep_chunk_chars": 12000,          # 文稿超过这个字数就分段总结再合并
    "free_plan": "",                    # 正在用的免费方案（空 = 没用）
    "welcome_done": False,
    "tokens_used": 0,
    "tokens_weekly": {},                # 每周消耗：{"本周一的日期": token 数}，周报用，只留最近 12 周
    "weekly_seen": "",                  # 看过的最近一期周报（那周周一的日期）
    "timing": {},                       # 各步骤实际耗时（用来估算剩余时间）
}

_lock = threading.Lock()


def load():
    with _lock:
        s = dict(DEFAULTS)
        if SETTINGS_PATH.exists():
            try:
                s.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
            except Exception:
                pass
        return s


def save(patch: dict):
    with _lock:
        s = dict(DEFAULTS)
        if SETTINGS_PATH.exists():
            try:
                s.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
            except Exception:
                pass
        for k, v in patch.items():
            if k in DEFAULTS:
                s[k] = v
        fp = FREE_PLANS.get(s.get("free_plan") or "")
        if fp and (s.get("base_url") or "").rstrip("/") != fp["base_url"]:
            s["free_plan"] = ""  # 手动换成了别的服务，就不算免费方案了
        tmp = SETTINGS_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, SETTINGS_PATH)
        return s


def week_key(t=None) -> str:
    """t 所在那一周的周一（本地时间），例如 "2026-10-26"。"""
    import datetime
    d = datetime.date.fromtimestamp(t if t is not None else time.time())
    return (d - datetime.timedelta(days=d.weekday())).isoformat()


def add_tokens(n: int):
    if n:
        s = load()
        weekly = dict(s.get("tokens_weekly") or {})
        wk = week_key()
        weekly[wk] = int(weekly.get(wk, 0)) + int(n)
        weekly = dict(sorted(weekly.items())[-12:])
        save({"tokens_used": int(s.get("tokens_used", 0)) + int(n), "tokens_weekly": weekly})


def public(s: dict) -> dict:
    """给网页看的设置：Key 只露出末尾 4 位。"""
    out = dict(s)
    for field in ("api_key", "deep_api_key"):
        k = out.pop(field, "") or ""
        out[field + "_set"] = bool(k)
        out[field + "_hint"] = ("••••" + k[-4:]) if len(k) >= 4 else ""
    out.pop("timing", None)
    out["default_deep_prompt"] = DEFAULT_DEEP_PROMPT
    return out


def provider_kind(provider, base_url=""):
    p = PROVIDERS.get(provider) or {}
    if p.get("kind"):
        return p["kind"]
    return "anthropic" if "anthropic.com" in (base_url or "") else "openai"


def llm_cfg(s, purpose="main"):
    """返回调用大模型需要的配置。purpose = main（日常提炼）或 deep（精读）。"""
    if purpose == "deep" and not s.get("deep_same", True):
        cfg = {"provider": s.get("deep_provider"), "base_url": s.get("deep_base_url"),
               "model": s.get("deep_model"), "api_key": s.get("deep_api_key")}
    else:
        cfg = {"provider": s.get("provider"), "base_url": s.get("base_url"),
               "model": s.get("model"), "api_key": s.get("api_key")}
    cfg["kind"] = provider_kind(cfg["provider"], cfg["base_url"])
    return cfg


def library_dir() -> Path:
    p = Path(load().get("library_dir") or DEFAULT_LIBRARY).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p
