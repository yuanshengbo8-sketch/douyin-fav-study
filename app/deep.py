"""精读：「有人带着读」。

流程：
1. 文字稿带上时间戳（有分段信息时），方便大纲里标出章节时间，点一下就能跳到文字稿对应位置。
2. 文稿太长（超过设置里的分段字数）时，先一段一段做详细笔记，最后把各段笔记合并再精读，
   避免超出模型上下文长度。
3. 按用户的精读提示词，生成：核心结论、章节大纲、关键概念、理解检查题、测验题、Anki 卡片、思维导图。
4. 精读之后还能：回答理解检查题让 AI 点评，或者随时「问老师」。
"""
import json
import queue
import threading
import time
import traceback

from . import config, db, llm, notes, progress

# ---------------------------------------------------------------- 提示词

FORMAT = """请严格只输出一个 JSON 对象，不要输出任何其他文字或 Markdown 代码块标记，格式如下：
{
  "title": "给这份内容起一个简洁的中文标题（20字以内）",
  "category": "从这些分类里选一个最合适的：%(categories)s；都不合适可以自拟",
  "conclusions": ["核心结论，每条一句话"],
  "outline": [{"time": "章节开始时间，如 03:12；文稿里没有时间就留空", "title": "章节标题", "points": ["本章要点"]}],
  "concepts": [{"term": "关键概念或术语", "explain": "用大白话解释，必要时举例"}],
  "check_questions": [{"q": "用来检查我是否真正理解的启发式问题（不要直接给答案）", "hint": "如果我卡住了，给一点提示", "key": "参考答案要点（先对我隐藏）"}],
  "quiz": [{"q": "测验题", "options": ["选项A", "选项B", "选项C", "选项D"], "answer": 0, "explain": "为什么选这个"}],
  "anki": [{"q": "问题", "a": "答案"}],
  "mindmap": "用 Markdown 标题和列表写的思维导图（Markmap 格式）：# 主题\\n## 分支\\n- 要点\\n  - 细节"
}
要求：
- quiz 的 answer 是正确选项的下标（0 表示第一个选项）。
- 如果学习要求里没提到某一项，就给空数组或空字符串。
- 不要编造文稿里没有的信息；转写里明显听错的专有名词可以按常识纠正。
- 全部使用简体中文。"""

SYSTEM = """你是一位耐心、善于启发的学习教练，正在带一位学习者精读一段视频内容。学习者还没读过原文。
你的任务是帮他真正读懂并记住，而不是只给摘要。

学习者的学习要求：
%(prompt)s

""" + FORMAT

USER = """标题：%(title)s
作者：%(author)s
%(kind)s：
%(body)s"""

CHUNK_SYSTEM = """你在帮学习者预读一段很长的视频文字稿。下面是其中的第 %(i)d 段（共 %(n)d 段）。
请为这一段做详细笔记，后面会把所有段落的笔记合并起来再做整体精读，所以要保留关键细节、例子、数字和论证过程。
请严格只输出一个 JSON 对象，不要输出其他文字：
{
  "sections": [{"time": "这一小节开始的时间（文稿里有 [mm:ss] 就照抄，没有就留空）", "title": "小节标题", "notes": ["详细要点"]}],
  "concepts": [{"term": "出现的概念或术语", "explain": "解释"}]
}
全部使用简体中文。"""

CHECK_SYSTEM = """你是一位学习教练，用苏格拉底式提问帮学习者检查是否真正理解了一段视频内容。
下面是视频内容、你之前提的问题、参考答案要点，以及学习者的回答。
请用简体中文、口语化地回复，控制在 200 字以内：
1. 第一行先给结论：「✅ 理解到位」「🟡 理解了一部分」或「❌ 有偏差」之一；
2. 指出他说对了什么、漏了什么或哪里理解偏了（引用原文里的说法）；
3. 如果没完全理解，不要直接把答案全说出来，而是再追问一个更小的问题或给一个提示，引导他自己想到；
   如果理解到位，可以补充一个延伸思考。"""

ASK_SYSTEM = """你是一位耐心的学习教练，正在带学习者精读一段视频内容。请根据下面的视频内容回答学习者的问题。
- 优先依据视频内容回答，引用时可以带上时间点；视频里没讲到的，要明确说「视频里没提到」，再用你的常识补充并注明。
- 用简体中文，讲清楚、举例子，像老师一样；适当反问，帮他自己想明白。
- 回答控制在 400 字以内，除非学习者要求详细展开。

视频内容：
%(context)s"""


# ---------------------------------------------------------------- 文稿整理

def fmt_ts(sec):
    sec = int(sec or 0)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def timed_lines(item):
    """有分段时间戳时，每隔大约 20 秒标一次时间：[03:12] 文字……"""
    segs = item.get("segments") or []
    if not segs:
        return None
    lines, buf, start = [], [], None
    for s in segs:
        if start is None:
            start = s["start"]
        buf.append(s["text"])
        if s["end"] - start >= 20:
            lines.append(f"[{fmt_ts(start)}] " + "".join(buf))
            buf, start = [], None
    if buf:
        lines.append(f"[{fmt_ts(start)}] " + "".join(buf))
    return lines


def body_lines(item):
    lines = timed_lines(item)
    if lines:
        return lines, True
    text = item.get("transcript") or ""
    # 没有时间戳：按句号大致切成行，方便分段
    import re
    parts = [p for p in re.split(r"(?<=[。！？!?])", text) if p.strip()]
    out, buf = [], ""
    for p in parts:
        buf += p
        if len(buf) > 300:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out or [text], False


def split_chunks(lines, limit):
    chunks, cur, n = [], [], 0
    for ln in lines:
        if cur and n + len(ln) > limit:
            chunks.append("\n".join(cur))
            cur, n = [], 0
        cur.append(ln)
        n += len(ln) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks


# ---------------------------------------------------------------- 结果整理

def _strs(v):
    if isinstance(v, str):
        v = [v]
    return [str(x).strip() for x in (v or []) if str(x).strip()]


def _objs(v, keys):
    out = []
    for x in v or []:
        if isinstance(x, dict):
            d = {k: x.get(k, "") for k in keys}
            out.append(d)
    return out


def normalize(d):
    res = {
        "title": str(d.get("title") or "").strip(),
        "category": str(d.get("category") or "").strip(),
        "conclusions": _strs(d.get("conclusions")),
        "outline": [],
        "concepts": [c for c in _objs(d.get("concepts"), ["term", "explain"]) if str(c["term"]).strip()],
        "check_questions": [c for c in _objs(d.get("check_questions"), ["q", "hint", "key"]) if str(c["q"]).strip()],
        "quiz": [],
        "anki": [c for c in _objs(d.get("anki"), ["q", "a"]) if str(c["q"]).strip()],
        "mindmap": str(d.get("mindmap") or "").strip(),
    }
    for o in d.get("outline") or []:
        if isinstance(o, dict) and str(o.get("title", "")).strip():
            res["outline"].append({"time": str(o.get("time") or "").strip(), "title": str(o["title"]).strip(),
                                   "points": _strs(o.get("points"))})
    for q in d.get("quiz") or []:
        if not isinstance(q, dict) or not str(q.get("q", "")).strip():
            continue
        opts = _strs(q.get("options"))
        ans = q.get("answer", 0)
        if isinstance(ans, str):  # 有的模型会写 "B" 或选项原文
            a = ans.strip().upper()
            if len(a) == 1 and "A" <= a <= "Z":
                ans = ord(a) - 65
            else:
                ans = next((i for i, o in enumerate(opts) if o == ans.strip()), 0)
        try:
            ans = int(ans)
        except Exception:
            ans = 0
        if opts:
            res["quiz"].append({"q": str(q["q"]).strip(), "options": opts,
                                "answer": max(0, min(ans, len(opts) - 1)), "explain": str(q.get("explain") or "")})
    if not (res["conclusions"] or res["outline"]):
        raise llm.LLMError("AI 返回的精读内容是空的")
    return res


def time_to_sec(t):
    try:
        parts = [int(x) for x in str(t).strip().split(":")]
    except Exception:
        return None
    if not parts:
        return None
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


# ---------------------------------------------------------------- 导出

def anki_tsv(deep):
    def clean(s):
        return str(s).replace("\t", " ").replace("\r", "").replace("\n", "<br>")
    return "\n".join(f"{clean(c['q'])}\t{clean(c['a'])}" for c in deep.get("anki", [])) + "\n"


MARKMAP_VERSION = "0.18.12"


def mindmap_html(title, md):
    safe = (md or "# （空）").replace("</script", "<\\/script")
    t = (title or "思维导图").replace("<", "&lt;")
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t} · 思维导图</title>
<style>
html,body{{margin:0;height:100%;background:#fff;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
.markmap{{position:fixed;inset:0}}
.markmap>svg{{width:100%;height:100%}}
.tip{{position:fixed;right:14px;bottom:12px;font-size:12px;color:#86868b}}
</style></head><body>
<div class="markmap"><script type="text/template">
---
markmap:
  initialExpandLevel: 3
  colorFreezeLevel: 2
---
{safe}
</script></div>
<div class="tip">滚轮缩放 · 拖动平移 · 点圆点折叠/展开</div>
<pre id="fallback" style="display:none;margin:24px;white-space:pre-wrap;font:15px/1.8 -apple-system,'PingFang SC',sans-serif;color:#1f1d1a"></pre>
<script>
function showFallback(){{
  var tpl=document.querySelector('.markmap script');
  var md=tpl?tpl.textContent.replace(/^[\\s\\S]*?---[\\s\\S]*?---\\n/,''):'';
  document.querySelector('.markmap').style.display='none';
  var pre=document.getElementById('fallback');
  pre.textContent='（思维导图组件没加载出来，可能是网络连不上 cdn.jsdelivr.net。先用文字版：）\\n\\n'+md;
  pre.style.display='block';
}}
setTimeout(function(){{ if(!document.querySelector('.markmap svg')) showFallback(); }},8000);
</script>
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@{MARKMAP_VERSION}" onerror="showFallback()"></script>
</body></html>"""


def prompt_for_other_ai(item, s):
    """给「复制到豆包 / Kimi / 千问 / Claude 网页版」用的纯文本。"""
    lines, timed = body_lines(item)
    head = (s.get("deep_prompt") or config.DEFAULT_DEEP_PROMPT).strip()
    extra = ("\n另外请用 Markmap 格式（Markdown 标题和列表）画一份思维导图。"
             "如果文稿很长，请先分段总结，最后再合并。")
    if timed:
        extra += "\n文稿里的 [mm:ss] 是时间戳，列大纲时请标出每章开始的时间。"
    title = (item.get("note") or {}).get("title") or item.get("title") or ""
    return f"{head}{extra}\n\n标题：{title}\n\n文字稿：\n" + "\n".join(lines)


# ---------------------------------------------------------------- 后台精读

class DeepRunner:
    """精读在单独的线程里排队跑，不会卡住下载转写。"""

    def __init__(self, log):
        self.log = log
        self.q = queue.Queue()
        self.pending = set()
        self.state = {}
        self._lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True, name="deep").start()

    def submit(self, item_id):
        with self._lock:
            if item_id in self.pending:
                return False
            self.pending.add(item_id)
        self.q.put(item_id)
        return True

    def snapshot(self):
        with self._lock:
            st = dict(self.state)
            pending = sorted(self.pending)
        if st.get("item_id"):
            per = progress.timing().get("deep_call", 45.0)
            elapsed_step = time.time() - st["step_start"]
            frac_step = min(elapsed_step / per, 0.95)
            done = st["step"] - 1 + frac_step
            st["pct"] = round(min(done / st["steps"], 0.99) * 100)
            st["eta"] = round(max(per - elapsed_step, 3) + (st["steps"] - st["step"]) * per)
        st["pending"] = pending
        return st

    def _set(self, **kw):
        with self._lock:
            self.state.update(kw)

    def _run(self):
        while True:
            item_id = self.q.get()
            try:
                self._deep(item_id)
            except llm.LLMError as e:
                self._fail(item_id, str(e))
            except Exception as e:
                traceback.print_exc()
                self._fail(item_id, f"意外错误：{e}")
            finally:
                with self._lock:
                    self.pending.discard(item_id)
                    self.state = {}

    def _fail(self, item_id, msg):
        it = db.get(item_id)
        if it:
            chat = it.get("chat") or {}
            chat["deep_error"] = msg
            db.update(item_id, chat=chat)
        self.log(f"[{item_id}] ✗ 精读失败：{msg}")

    def _call(self, cfg, messages, max_tokens):
        t0 = time.time()
        d, used = llm.chat_json(cfg, messages, json_mode=True, temperature=0.3, max_tokens=max_tokens, timeout=300)
        config.add_tokens(used)
        progress.learn("deep_call", time.time() - t0)
        return d

    def _deep(self, item_id):
        it = db.get(item_id)
        if not it or not it.get("transcript"):
            raise llm.LLMError("这条还没有文字稿，没法精读")
        s = config.load()
        cfg = config.llm_cfg(s, "deep")
        if not (cfg.get("api_key") or "").strip():
            raise llm.LLMError("还没填精读用的 AI Key（设置 → 精读）")
        chat = it.get("chat") or {}
        chat.pop("deep_error", None)
        db.update(item_id, chat=chat)

        title = (it.get("note") or {}).get("title") or it.get("title") or "（无标题）"
        lines, timed = body_lines(it)
        limit = max(3000, int(s.get("deep_chunk_chars") or 12000))
        chunks = split_chunks(lines, limit)
        steps = (len(chunks) + 1) if len(chunks) > 1 else 1
        self._set(item_id=item_id, title=title[:40], step=1, steps=steps, step_start=time.time(),
                  label="精读中" if steps == 1 else f"分段预读 1/{len(chunks)}", started=time.time())
        self.log(f"[{item_id}] 开始精读（{cfg['model']}）" + (f"，文稿较长，分 {len(chunks)} 段预读后合并" if steps > 1 else ""))

        cats = "、".join(s.get("categories") or [])
        system = SYSTEM % {"prompt": (s.get("deep_prompt") or config.DEFAULT_DEEP_PROMPT).strip(),
                           "categories": cats}

        source_notes = None
        if len(chunks) > 1:
            parts = []
            for i, ch in enumerate(chunks, 1):
                self._set(step=i, step_start=time.time(), label=f"分段预读 {i}/{len(chunks)}")
                d = self._call(cfg, [
                    {"role": "system", "content": CHUNK_SYSTEM % {"i": i, "n": len(chunks)}},
                    {"role": "user", "content": f"标题：{title}\n\n第 {i} 段文字稿：\n{ch}"},
                ], max_tokens=4000)
                parts.append(self._chunk_to_text(i, d))
                self.log(f"[{item_id}] 第 {i}/{len(chunks)} 段预读完成")
            source_notes = "\n\n".join(parts)
            self._set(step=steps, step_start=time.time(), label="合并精读")
            body, kind = source_notes, "各段的详细笔记（按时间顺序）"
        else:
            body = "\n".join(lines)
            kind = "文字稿（[mm:ss] 是时间戳）" if timed else "文字稿"

        d = self._call(cfg, [
            {"role": "system", "content": system},
            {"role": "user", "content": USER % {"title": title, "author": it.get("author") or "（未知）",
                                                "kind": kind, "body": body}},
        ], max_tokens=8000)
        deep = normalize(d)
        deep.update(model=cfg["model"], created_at=time.time(), chunks=len(chunks), timed=timed)
        if source_notes:
            deep["source_notes"] = source_notes
        for o in deep["outline"]:
            o["sec"] = time_to_sec(o["time"]) if o["time"] else None

        fields = {"deep": deep}
        if it["source"] == "paste" or not it.get("note"):
            # 粘贴进来的文稿没有走普通提炼，用精读结果补一份笔记，放进学习库
            note = {
                "skip": False, "relevant": True, "title": deep["title"] or title,
                "category": deep["category"] or "精读文稿", "tags": [], "difficulty": "",
                "summary": "；".join(c.rstrip("。；;. ") for c in deep["conclusions"]) + "。", "points": deep["conclusions"], "steps": [],
                "tools": [], "concepts": deep["concepts"],
                "quiz": [{"q": q["q"], "a": q["options"][q["answer"]]} for q in deep["quiz"][:3]],
            }
            fields.update(note=note, category=note["category"], status="done", reason=None)
            it["note"] = note
        it["deep"] = deep
        fields["md_path"] = notes.write(it)
        db.update(item_id, **fields)
        self.log(f"[{item_id}] ✓ 精读完成：{deep['title'] or title}")

    @staticmethod
    def _chunk_to_text(i, d):
        out = [f"=== 第 {i} 段 ==="]
        for sec in d.get("sections") or []:
            if not isinstance(sec, dict):
                continue
            t = str(sec.get("time") or "").strip()
            out.append(f"{'[' + t + '] ' if t else ''}{sec.get('title', '')}")
            out += [f"- {n}" for n in _strs(sec.get("notes"))]
        cs = [c for c in d.get("concepts") or [] if isinstance(c, dict)]
        if cs:
            out.append("概念：" + "；".join(f"{c.get('term')}：{c.get('explain')}" for c in cs))
        return "\n".join(out)


# ---------------------------------------------------------------- 互动：点评 / 问老师

def _context(it, limit=24000):
    deep = it.get("deep") or {}
    if deep.get("source_notes"):
        return deep["source_notes"][:limit]
    lines, _ = body_lines(it)
    text = "\n".join(lines)
    if len(text) > limit:
        text = text[:limit] + "\n……（后面还有，太长省略）"
    return text


def check_answer(item_id, idx, answer):
    it = db.get(item_id)
    deep = (it or {}).get("deep") or {}
    qs = deep.get("check_questions") or []
    if not (0 <= idx < len(qs)):
        raise llm.LLMError("找不到这道题")
    q = qs[idx]
    s = config.load()
    msg = (f"视频内容：\n{_context(it, 16000)}\n\n问题：{q['q']}\n参考答案要点：{q.get('key', '')}\n\n"
           f"学习者的回答：{answer}")
    text, used = llm.chat(config.llm_cfg(s, "deep"), [
        {"role": "system", "content": CHECK_SYSTEM}, {"role": "user", "content": msg}],
        json_mode=False, temperature=0.4, max_tokens=800, timeout=180)
    config.add_tokens(used)
    chat = it.get("chat") or {}
    chat.setdefault("checks", {})[str(idx)] = {"answer": answer, "feedback": text.strip(), "t": time.time()}
    db.update(item_id, chat=chat)
    return chat["checks"][str(idx)]


def ask(item_id, question):
    it = db.get(item_id)
    if not it or not it.get("transcript"):
        raise llm.LLMError("这条还没有文字稿")
    s = config.load()
    chat = it.get("chat") or {}
    hist = chat.get("ask", [])[-8:]
    messages = [{"role": "system", "content": ASK_SYSTEM % {"context": _context(it)}}]
    for h in hist:
        messages += [{"role": "user", "content": h["q"]}, {"role": "assistant", "content": h["a"]}]
    messages.append({"role": "user", "content": question})
    text, used = llm.chat(config.llm_cfg(s, "deep"), messages, json_mode=False, temperature=0.5,
                          max_tokens=1500, timeout=180)
    config.add_tokens(used)
    chat.setdefault("ask", []).append({"q": question, "a": text.strip(), "t": time.time()})
    db.update(item_id, chat=chat)
    return chat["ask"][-1]


def quiz_result(item_id, score, total):
    it = db.get(item_id)
    if not it:
        return
    chat = it.get("chat") or {}
    chat.setdefault("quiz_history", []).append({"score": score, "total": total, "t": time.time()})
    db.update(item_id, chat=chat)
