"""跨视频整理：知识图谱 + 共识观点。

知识图谱在本机算，不花钱：两条笔记的标签、概念、工具有重合，就连一条线，重合越多线越粗。
共识观点要用 AI：把一个分类里的全部笔记交给 AI，找出被两条以上视频互相印证的观点，和说法不一致的地方。
结果存在数据库里，同时写一份 Markdown 到笔记目录的「_共识观点」文件夹（Obsidian 里能点链接跳到原笔记）。
"""
import queue
import re
import threading
import time
import traceback
from collections import defaultdict
from pathlib import Path

from . import config, db, llm, notes

INSIGHT_DIR = "_共识观点"
MAX_INPUT_CHARS = 24000   # 一次交给 AI 的笔记总字数上限
MAX_LINKS_PER_NODE = 6    # 每条笔记最多连几条最相关的线，图才不会乱成一团

SYSTEM = """你是一位帮人整理知识的助手。你会收到同一个主题分类下的多条短视频学习笔记，每条前面有编号 [#数字]。
请找出：
1. 共识观点：被两条或以上视频共同支持、互相印证的观点或方法（不同说法表达同一个意思也算）。
2. 分歧：不同视频对同一件事说法不一致、甚至相反的地方。

请严格只输出一个 JSON 对象，格式如下：
{
  "overview": "2-3 句话概括这个分类的笔记整体在讲什么",
  "consensus": [
    {"view": "一句话写清这个共识观点", "detail": "综合各视频的说法展开解释，2-4 句", "item_ids": [编号, 编号]}
  ],
  "conflicts": [
    {"topic": "在什么问题上有分歧", "sides": [{"view": "一种说法", "item_ids": [编号]}, {"view": "另一种说法", "item_ids": [编号]}],
     "advice": "怎么看待这个分歧，什么情况下该听谁的"}
  ]
}

规则：
- item_ids 只能填上面出现过的编号（只写数字）；共识观点至少要有 2 个编号。
- 按支持的视频数从多到少排序，最多 12 条共识、5 条分歧；没有就给空数组，不要硬凑。
- 不要编造笔记里没有的内容。全部使用简体中文。"""


def _norm(s):
    return re.sub(r"[\s\-_·•.,，。:：/()（）\"'“”]+", "", str(s or "")).lower()


def _keywords(note):
    """一条笔记用来连线的关键词：标签、概念、工具。"""
    out = {}
    for t in note.get("tags") or []:
        out.setdefault(_norm(t), str(t).strip())
    for c in note.get("concepts") or []:
        out.setdefault(_norm(c.get("term")), str(c.get("term") or "").strip())
    for t in note.get("tools") or []:
        out.setdefault(_norm(t.get("name")), str(t.get("name") or "").strip())
    out.pop("", None)
    return out


def graph():
    """返回 {nodes, links, keywords}：节点是笔记，连线是共同的关键词。"""
    items = db.done_items()
    nodes, kw_of, index = [], {}, defaultdict(set)
    for it in items:
        n = it.get("note") or {}
        kws = _keywords(n)
        kw_of[it["id"]] = kws
        for k in kws:
            index[k].add(it["id"])
        nodes.append({"id": it["id"], "title": n.get("title") or it.get("title") or "未命名",
                      "category": it.get("category") or n.get("category") or "其他",
                      "learned": bool(it.get("learned")), "deep": bool(it.get("deep"))})

    # 太常见的词（比如几乎每条都打了「AI」标签）不算关联，否则所有笔记都连在一起
    too_common = max(6, int(len(items) * 0.35))
    pair_shared = defaultdict(list)
    for k, ids in index.items():
        if len(ids) < 2 or len(ids) > too_common:
            continue
        ids = sorted(ids)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                pair_shared[(a, b)].append(k)

    # 每条笔记只保留最相关的几条线
    best = defaultdict(list)
    for (a, b), ks in pair_shared.items():
        best[a].append((len(ks), b))
        best[b].append((len(ks), a))
    keep = set()
    for a, lst in best.items():
        for _, b in sorted(lst, reverse=True)[:MAX_LINKS_PER_NODE]:
            keep.add((min(a, b), max(a, b)))
    links = []
    for a, b in sorted(keep):
        ks = pair_shared[(a, b)]
        links.append({"source": a, "target": b, "w": len(ks), "shared": [kw_of[a].get(k) or k for k in ks][:6]})

    deg = defaultdict(int)
    for l in links:
        deg[l["source"]] += 1
        deg[l["target"]] += 1
    for nd in nodes:
        nd["deg"] = deg[nd["id"]]

    # 共识观点也画进图里：一个观点连着支持它的几条笔记
    views = []
    for ins in db.list_insights():
        for i, c in enumerate(ins["data"].get("consensus") or []):
            ids = [x for x in c.get("item_ids") or [] if x in kw_of]
            if len(ids) >= 2:
                views.append({"id": f"v:{ins['category']}:{i}", "view": c.get("view", ""),
                              "category": ins["category"], "items": ids})
    return {"nodes": nodes, "links": links, "views": views}


# ---------------------------------------------------------------- 共识观点

def categories():
    """每个分类：多少条笔记、有没有整理过、整理后又新增了几条。"""
    by_cat = defaultdict(list)
    for it in db.done_items():
        by_cat[it.get("category") or "其他"].append(it["id"])
    done = {ins["category"]: ins for ins in db.list_insights()}
    out = []
    for cat, ids in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
        ins = done.get(cat)
        new = len(set(ids) - set(ins["item_ids"])) if ins else len(ids)
        out.append({"category": cat, "n": len(ids), "done": bool(ins), "new": new if ins else 0,
                    "created_at": ins["created_at"] if ins else None,
                    "consensus": len(ins["data"].get("consensus") or []) if ins else 0})
    return out


def _note_text(it, full=True):
    n = it.get("note") or {}
    lines = [f"[#{it['id']}] {n.get('title') or it.get('title') or ''}"]
    if full and n.get("summary"):
        lines.append(f"总结：{n['summary']}")
    lines += [f"- {p}" for p in n.get("points") or []]
    if full and n.get("steps"):
        lines.append("方法：" + "；".join(n["steps"]))
    return "\n".join(lines)


def build_input(items):
    text = "\n\n".join(_note_text(it) for it in items)
    if len(text) > MAX_INPUT_CHARS:  # 太长就只给标题和核心观点
        text = "\n\n".join(_note_text(it, full=False) for it in items)
    return text[:MAX_INPUT_CHARS]


def _ids(v, valid):
    out = []
    for x in v or []:
        try:
            x = int(str(x).lstrip("#"))
        except ValueError:
            continue
        if x in valid and x not in out:
            out.append(x)
    return out


def normalize(d, valid):
    cons = []
    for c in d.get("consensus") or []:
        if not isinstance(c, dict):
            continue
        ids = _ids(c.get("item_ids"), valid)
        view = str(c.get("view") or "").strip()
        if view and len(ids) >= 2:
            cons.append({"view": view, "detail": str(c.get("detail") or "").strip(), "item_ids": ids})
    cons.sort(key=lambda c: -len(c["item_ids"]))
    confs = []
    for c in d.get("conflicts") or []:
        if not isinstance(c, dict):
            continue
        sides = [{"view": str(s.get("view") or "").strip(), "item_ids": _ids(s.get("item_ids"), valid)}
                 for s in c.get("sides") or [] if isinstance(s, dict)]
        sides = [s for s in sides if s["view"] and s["item_ids"]]
        if str(c.get("topic") or "").strip() and len(sides) >= 2:
            confs.append({"topic": str(c["topic"]).strip(), "sides": sides, "advice": str(c.get("advice") or "").strip()})
    return {"overview": str(d.get("overview") or "").strip(), "consensus": cons[:12], "conflicts": confs[:5]}


def render_md(category, data, items, model):
    """写成 Markdown；用 [[笔记文件名]] 链接到原笔记，Obsidian 里能直接点过去、在关系图里连起来。"""
    by_id = {it["id"]: it for it in items}

    def ref(i):
        it = by_id.get(i)
        if not it:
            return f"#{i}"
        title = (it.get("note") or {}).get("title") or it.get("title") or f"#{i}"
        if it.get("md_path"):
            return f"[[{Path(it['md_path']).stem}|{title}]]"
        return title

    lines = ["---", f'title: "{category} · 共识观点"', f"category: {category}",
             f"date: {time.strftime('%Y-%m-%d')}", "tags: [抖音, 共识观点]", "---", "",
             f"# {category} · 共识观点", "",
             f"由 {model} 从 {len(items)} 条笔记中整理 · {time.strftime('%Y-%m-%d %H:%M')}", ""]
    if data["overview"]:
        lines += ["## 概览", "", data["overview"], ""]
    if data["consensus"]:
        lines += ["## 共识观点（多条视频互相印证）", ""]
        for i, c in enumerate(data["consensus"], 1):
            lines += [f"### {i}. {c['view']}", ""]
            if c["detail"]:
                lines += [c["detail"], ""]
            lines += [f"来源（{len(c['item_ids'])} 条）：" + "、".join(ref(x) for x in c["item_ids"]), ""]
    if data["conflicts"]:
        lines += ["## 说法不一致的地方", ""]
        for c in data["conflicts"]:
            lines += [f"### {c['topic']}", ""]
            lines += [f"- {s['view']}（{'、'.join(ref(x) for x in s['item_ids'])}）" for s in c["sides"]]
            if c["advice"]:
                lines += ["", f"> {c['advice']}"]
            lines.append("")
    return "\n".join(lines)


class InsightRunner:
    """共识观点在单独的线程里排队整理，一次一个分类。"""

    def __init__(self, log):
        self.log = log
        self.q = queue.Queue()
        self.pending = []
        self.state = {}
        self.errors = {}
        self._lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True, name="insights").start()

    def submit(self, category):
        with self._lock:
            if category in self.pending:
                return False
            self.pending.append(category)
            self.errors.pop(category, None)
        self.q.put(category)
        return True

    def snapshot(self):
        with self._lock:
            return {**self.state, "pending": list(self.pending), "errors": dict(self.errors)}

    def _run(self):
        while True:
            cat = self.q.get()
            try:
                with self._lock:
                    self.state = {"category": cat, "started": time.time()}
                self._build(cat)
            except llm.LLMError as e:
                self._fail(cat, str(e))
            except Exception as e:
                traceback.print_exc()
                self._fail(cat, f"意外错误：{e}")
            finally:
                with self._lock:
                    if cat in self.pending:
                        self.pending.remove(cat)
                    self.state = {}

    def _fail(self, cat, msg):
        with self._lock:
            self.errors[cat] = msg
        self.log(f"✗ 「{cat}」共识观点整理失败：{msg}")

    def _build(self, cat):
        items = [it for it in db.done_items() if (it.get("category") or "其他") == cat]
        if len(items) < 2:
            raise llm.LLMError("这个分类至少要有 2 条笔记才能找共识")
        s = config.load()
        cfg = config.llm_cfg(s, "deep")
        if not (cfg.get("api_key") or "").strip():
            raise llm.LLMError("还没填 AI Key（设置 → 精读）")
        self.log(f"开始整理「{cat}」的共识观点（{len(items)} 条笔记，{cfg['model']}）")
        text, used = llm.chat(cfg, [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"分类：{cat}\n\n{build_input(items)}"},
        ], json_mode=True, temperature=0.3, max_tokens=6000, timeout=300)
        config.add_tokens(used)
        try:
            d = llm.parse_json(text)
        except Exception:
            raise llm.LLMError("AI 返回的不是有效的 JSON：" + (text or "")[:200])
        data = normalize(d, {it["id"] for it in items})

        folder = config.library_dir() / INSIGHT_DIR
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{notes.safe_name(cat, 30)}.md"
        path.write_text(render_md(cat, data, items, cfg["model"]), encoding="utf-8")
        db.save_insight(cat, data, [it["id"] for it in items], cfg["model"], str(path))
        self.log(f"✓ 「{cat}」整理出 {len(data['consensus'])} 条共识观点、{len(data['conflicts'])} 处分歧")
