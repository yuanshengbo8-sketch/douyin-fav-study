"""AI 提炼：调用 OpenAI 兼容的 /chat/completions 接口，把文字稿变成结构化学习笔记。

只把文字稿发给你选的 AI 服务商；视频、音频、你的个人笔记都不会上传。
"""
import json
import re
import time
import urllib.error
import urllib.request

MAX_CHARS = 6000  # 文字稿太长就截断，控制花费

SYSTEM = """你是一位擅长把短视频内容整理成学习笔记的助手。你会收到一条抖音视频的语音转文字稿，或者一条抖音图文笔记的正文和图片里识别出的文字（都可能有错别字或断行，请按上下文理解），需要提炼成结构化笔记。

用户关注的主题：{focus}

请严格只输出一个 JSON 对象，不要输出任何其他文字，格式如下：
{{
  "skip": false,
  "skip_reason": "",
  "relevant": true,
  "title": "一句话说清这条视频讲了什么（20字以内，不要照抄原标题里的话题标签）",
  "category": "从这些分类里选最合适的一个：{categories}；都不合适可以自拟一个简短分类",
  "tags": ["3-5个关键词"],
  "difficulty": "入门 / 进阶 / 高级 选一个",
  "summary": "3-5 句话的详细总结",
  "points": ["核心观点或知识点，每条一句话，3-8 条"],
  "steps": ["如果视频教了可以照着做的方法，按顺序写出具体步骤；没有就给空数组"],
  "tools": [{{"name": "视频提到的工具/网站/产品名", "use": "它是干什么用的"}}],
  "concepts": [{{"term": "关键概念", "explain": "用大白话解释"}}],
  "quiz": [{{"q": "根据视频内容出的一道自测题", "a": "答案"}}]
}}

规则：
- 如果视频是广告带货、短剧剧情、唱歌跳舞、纯娱乐闲聊，或几乎没有实质信息，返回 {{"skip": true, "skip_reason": "简短原因"}}。
- 如果有实质内容，但和用户关注的主题无关，"relevant" 填 false，其他字段照常填写。
- 不要编造视频里没有的信息；转写里明显听错的专有名词（比如工具名）可以按常识纠正。
- 全部使用简体中文。quiz 出 1-3 题。"""

USER = """标题：{title}
作者：{author}
{label}：
{transcript}

请提炼成学习笔记。"""


class LLMError(Exception):
    def __init__(self, msg, retry=False):
        super().__init__(msg)
        self.retry = retry


def _post(url, headers, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _as_cfg(c):
    """兼容传整份设置或已经整理好的模型配置。"""
    if "kind" in c:
        return c
    from .config import llm_cfg
    return llm_cfg(c, "main")


_QUIRKS = {}  # (接口地址, 模型) → 这个模型需要的参数调整，记住后下次直接用


def _apply_quirks(payload, key):
    q = _QUIRKS.get(key, set())
    if "mct" in q and "max_tokens" in payload:
        # 推理模型的输出上限也包含"思考"用的 token，给宽一点
        payload["max_completion_tokens"] = max(payload.pop("max_tokens") * 2, 4000)
    if "no_temp" in q:
        payload.pop("temperature", None)


def chat(cfg, messages, json_mode=True, temperature=0.3, max_tokens=None, timeout=120, retry_429=True):
    """返回 (文本, 消耗的 token 数)。带重试：网络/5xx 重试 2 次，429/529 限速等 5 秒。

    cfg 可以是整份设置，也可以是 config.llm_cfg() 的结果。
    """
    cfg = _as_cfg(cfg)
    key = (cfg.get("api_key") or "").strip()
    base = (cfg.get("base_url") or "").strip().rstrip("/")
    model = (cfg.get("model") or "").strip()
    if not key:
        raise LLMError("还没填 AI 的 API Key")
    if not base or not model:
        raise LLMError("请在设置里填好接口地址和模型名")

    if cfg.get("kind") == "anthropic":
        # Claude 原生接口：system 单独传；没有 JSON 模式，靠提示词约束 + parse_json 兜底
        if base.endswith("/v1"):
            base = base[:-3]
        url = base + "/v1/messages"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        msgs = [m for m in messages if m["role"] != "system"]
        payload = {"model": model, "max_tokens": max_tokens or 4096, "messages": msgs, "temperature": temperature}
        if system:
            payload["system"] = system
    else:
        url = base + "/chat/completions"
        headers = {"Authorization": f"Bearer {key}"}
        payload = {"model": model, "messages": messages, "temperature": temperature, "stream": False}
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        _apply_quirks(payload, (base, model))

    attempt = 0
    while True:
        attempt += 1
        try:
            data = _post(url, headers, payload, timeout=timeout)
            if cfg.get("kind") == "anthropic":
                text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
                u = data.get("usage") or {}
                used = (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)
                if data.get("stop_reason") == "max_tokens" and json_mode:
                    raise LLMError("AI 输出太长被截断了，可以在设置里把精读分段字数调小再试")
            else:
                text = data["choices"][0]["message"]["content"] or ""
                used = (data.get("usage") or {}).get("total_tokens", 0)
            return text, used
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "ignore")[:300]
            except Exception:
                pass
            if e.code == 401:
                raise LLMError("API Key 无效（401），请到设置里检查")
            if e.code in (402, 403):
                raise LLMError(f"账户余额不足或没有权限（{e.code}），请到服务商后台检查：{body}")
            if e.code == 404:
                raise LLMError(f"接口地址或模型名不对（404）：{body}")
            low = body.lower()
            qk = (base, model)
            # OpenAI 新一代（推理）模型：max_tokens 改名 max_completion_tokens
            if e.code == 400 and "max_completion_tokens" in low and "max_tokens" in payload:
                _QUIRKS.setdefault(qk, set()).add("mct")
                _apply_quirks(payload, qk)
                continue
            # 有的模型只允许默认 temperature
            if e.code == 400 and "temperature" in low and "temperature" in payload:
                _QUIRKS.setdefault(qk, set()).add("no_temp")
                payload.pop("temperature", None)
                continue
            if e.code == 400 and (payload.get("max_tokens") or 0) > 4096 and "token" in low:
                payload["max_tokens"] = 4096  # 免费模型通常限制单次最多输出 4096 tokens
                continue
            if e.code == 400 and "response_format" in payload:
                payload.pop("response_format")  # 有的模型不支持 JSON 模式，去掉再试
                continue
            if e.code in (429, 529) and attempt <= 3 and retry_429:
                time.sleep(5 * attempt)
                continue
            if e.code >= 500 and attempt <= 2:
                time.sleep(2)
                continue
            if e.code == 429:
                raise LLMError("请求太频繁或免费额度用完了（429）。免费额度一般按天/按月恢复；"
                               "着急的话可以在设置里换成付费模型。", retry=True)
            raise LLMError(f"AI 接口报错（HTTP {e.code}）：{body}", retry=e.code >= 500)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt <= 2:
                time.sleep(2)
                continue
            raise LLMError(f"连不上 AI 接口：{getattr(e, 'reason', e)}", retry=True)
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(f"AI 接口返回的格式看不懂：{e}")


def parse_json(text: str) -> dict:
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except Exception:
        a, b = t.find("{"), t.rfind("}")
        if a >= 0 and b > a:
            return json.loads(t[a:b + 1])
        raise


def _str_list(v):
    if isinstance(v, str):
        v = [v]
    return [str(x).strip() for x in (v or []) if str(x).strip()]


def _obj_list(v, keys):
    out = []
    for x in v or []:
        if isinstance(x, dict):
            d = {k: str(x.get(k, "")).strip() for k in keys}
            if d[keys[0]]:
                out.append(d)
        elif isinstance(x, str) and x.strip():
            out.append({keys[0]: x.strip(), keys[1]: ""})
    return out


def normalize(d: dict) -> dict:
    """统一字段格式，校验不过就抛错。"""
    if d.get("skip") is True:
        return {"skip": True, "skip_reason": str(d.get("skip_reason") or "没有实质内容")}
    note = {
        "skip": False,
        "relevant": d.get("relevant") is not False,
        "title": str(d.get("title") or "").strip(),
        "category": str(d.get("category") or "其他").strip() or "其他",
        "tags": _str_list(d.get("tags"))[:6],
        "difficulty": str(d.get("difficulty") or "").strip(),
        "summary": str(d.get("summary") or "").strip(),
        "points": _str_list(d.get("points")),
        "steps": _str_list(d.get("steps")),
        "tools": _obj_list(d.get("tools"), ["name", "use"]),
        "concepts": _obj_list(d.get("concepts"), ["term", "explain"]),
        "quiz": _obj_list(d.get("quiz"), ["q", "a"]),
    }
    if not note["points"]:
        raise LLMError("AI 返回的核心观点为空")
    if not note["title"]:
        note["title"] = note["points"][0][:30]
    return note


def extract(settings, title, author, transcript, kind="video"):
    """返回 (笔记 dict, token 数)。"""
    cats = "、".join(settings.get("categories") or [])
    messages = [
        {"role": "system", "content": SYSTEM.format(focus=settings.get("focus_topic") or "不限", categories=cats)},
        {"role": "user", "content": USER.format(
            title=title or "（无）", author=author or "（未知）",
            label="图文笔记的正文和图片文字（【图N】是第 N 张图里识别出的文字）" if kind == "note" else "语音转文字稿",
            transcript=(transcript or "")[:MAX_CHARS])},
    ]
    text, used = chat(settings, messages)
    try:
        d = parse_json(text)
    except Exception:
        raise LLMError("AI 返回的不是有效的 JSON：" + (text or "")[:200])
    note = normalize(d)
    if not note.get("skip"):
        # AI 有时把「AI 编程」写成「AI编程」，同一个分类就被拆成两个；对上设置里的分类名
        same = {re.sub(r"\s+", "", c): c for c in settings.get("categories") or []}
        note["category"] = same.get(re.sub(r"\s+", "", note["category"]), note["category"])
    return note, used


CHAT_HINT = ("gpt", "o1", "o3", "o4", "chatgpt", "claude", "deepseek", "qwen", "glm", "moonshot", "kimi",
             "yi-", "llama", "mistral", "gemini", "doubao", "ernie", "hunyuan", "minimax", "abab", "step")
SKIP_HINT = ("embed", "whisper", "tts", "dall-e", "image", "audio", "realtime", "moderation", "transcribe",
             "search", "rerank", "vision-preview", "babbage", "davinci", "sora", "speech")


def list_models(cfg):
    """向服务商要可用模型列表，返回模型 ID 列表（尽量只留聊天模型）。"""
    cfg = _as_cfg(cfg)
    key = (cfg.get("api_key") or "").strip()
    base = (cfg.get("base_url") or "").strip().rstrip("/")
    if not key or not base:
        raise LLMError("先填好接口地址和 API Key")
    if cfg.get("kind") == "anthropic":
        if base.endswith("/v1"):
            base = base[:-3]
        url, headers = base + "/v1/models?limit=100", {"x-api-key": key, "anthropic-version": "2023-06-01"}
    else:
        url, headers = base + "/models", {"Authorization": f"Bearer {key}"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise LLMError(f"这个服务商不支持读取模型列表（HTTP {e.code}），请手动填写模型名")
    except Exception as e:
        raise LLMError(f"读取模型列表失败：{e}")
    ids = [str(m.get("id")) for m in (data.get("data") or data.get("models") or []) if isinstance(m, dict) and m.get("id")]
    chat_ids = [i for i in ids if not any(h in i.lower() for h in SKIP_HINT)]
    pref = [i for i in chat_ids if any(h in i.lower() for h in CHAT_HINT)]
    out = pref or chat_ids or ids
    return sorted(set(out), key=lambda x: (x.count("-") > 4, x))


def test(cfg, retry_429=True):
    text, _ = chat(cfg, [{"role": "user", "content": "请只回复两个字：你好"}], json_mode=False, temperature=0,
                   max_tokens=300, retry_429=retry_429)
    return text.strip()[:50] or "（连接正常）"


def free_setup(plan, api_key, log=lambda m: None):
    """免费方案一键配置：读模型列表 → 挑免费模型 → 逐个测试，返回 (能用的模型, 试过的列表)。"""
    from .config import FREE_PLANS
    p = FREE_PLANS[plan]
    cfg = {"provider": p["provider"], "base_url": p["base_url"], "api_key": api_key.strip(), "kind": "openai"}
    listed = []
    try:
        listed = [m.split("/", 1)[1] if m.startswith("models/") else m for m in list_models(cfg)]
    except LLMError:
        pass
    cands = [m for m in p["models"] if not listed or m in listed]
    if listed and p.get("pick"):
        extra = [m for m in listed if all(k in m.lower() for k in p["pick"])
                 and not any(a in m.lower() for a in p["avoid"]) and m not in cands]
        extra.sort(reverse=True)  # 版本号大的通常更新
        cands += extra
    if not cands:
        cands = list(p["models"])
    tried = []
    for m in cands[:5]:
        cfg["model"] = m
        try:
            test(cfg, retry_429=False)
            return m, tried
        except LLMError as e:
            msg = str(e)
            tried.append(f"{m}：{msg[:80]}")
            if "401" in msg or "无效" in msg:
                raise LLMError("这个 Key 无效，请检查有没有复制完整（前后不要有空格）")
            if "429" in msg:
                raise LLMError("Key 是有效的，但现在请求太频繁或免费额度用完了（429）。过一会儿再点一键配置试试。")
    raise LLMError("没有找到能用的免费模型：" + "；".join(tried[:3]))
