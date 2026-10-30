"""每周知识周报：这一周收了多少笔记、学会了几条、精读和答题情况、AI 花了多少，以及连续学习了几周。

全部在本机统计，不调用 AI，不花钱。一周从周一 0 点算起。
"""
import datetime
import time
from collections import Counter

from . import config, db, notes

REPORT_DIR = "_周报"


def _monday(offset=0):
    """offset=0 是本周，-1 是上周……返回那周周一的 date。"""
    today = datetime.date.today()
    return today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(weeks=offset)


def _ts(d):
    return time.mktime(d.timetuple())


def _activity_times(it):
    """一条笔记上所有「学习动作」的时间：标记学会、精读、测验、回答理解检查题、问老师。"""
    ts = []
    if it.get("learned_at"):
        ts.append(it["learned_at"])
    if (it.get("deep") or {}).get("created_at"):
        ts.append(it["deep"]["created_at"])
    chat = it.get("chat") or {}
    ts += [q.get("t") for q in chat.get("quiz_history") or []]
    ts += [c.get("t") for c in (chat.get("checks") or {}).values()]
    ts += [a.get("t") for a in chat.get("ask") or []]
    return [t for t in ts if t]


def streak(items, this_monday):
    """连续学习周数：从本周（本周还没学就从上周）往前数，每周至少有一次学习动作。"""
    weeks = {config.week_key(t) for it in items for t in _activity_times(it)}
    d = this_monday
    if d.isoformat() not in weeks:
        d -= datetime.timedelta(weeks=1)
    n = 0
    while d.isoformat() in weeks:
        n += 1
        d -= datetime.timedelta(weeks=1)
    return n


def report(offset=0):
    offset = min(0, int(offset))
    mon = _monday(offset)
    start, end = _ts(mon), _ts(mon + datetime.timedelta(weeks=1))
    inside = lambda t: bool(t) and start <= t < end
    items = db.done_items()

    def brief(it):
        n = it.get("note") or {}
        return {"id": it["id"], "title": n.get("title") or it.get("title") or "未命名",
                "category": it.get("category") or "其他", "learned": bool(it.get("learned"))}

    new = [it for it in items if inside(it.get("created_at"))]
    learned = [it for it in items if inside(it.get("learned_at"))]
    deep = [it for it in items if inside((it.get("deep") or {}).get("created_at"))]
    quizzes, checks, asks = [], 0, 0
    for it in items:
        chat = it.get("chat") or {}
        quizzes += [q for q in chat.get("quiz_history") or [] if inside(q.get("t"))]
        checks += sum(1 for c in (chat.get("checks") or {}).values() if inside(c.get("t")))
        asks += sum(1 for a in chat.get("ask") or [] if inside(a.get("t")))
    q_total = sum(q.get("total") or 0 for q in quizzes)
    q_right = sum(q.get("score") or 0 for q in quizzes)

    tags = Counter()
    for it in new:
        tags.update(t for t in (it.get("note") or {}).get("tags") or [] if t)
    cats = Counter(it.get("category") or "其他" for it in new)
    insights = [{"category": i["category"], "consensus": len(i["data"].get("consensus") or [])}
                for i in db.list_insights() if inside(i["created_at"])]
    # 下周建议：收进来最久还没学的几条
    backlog = sorted((it for it in items if not it.get("learned")), key=lambda it: it.get("created_at") or 0)

    wk = mon.isoformat()
    return {
        "week": wk, "offset": offset,
        "label": f"{mon.month}月{mon.day}日 – {(mon + datetime.timedelta(days=6)).month}月{(mon + datetime.timedelta(days=6)).day}日",
        "is_current": offset == 0,
        "new": len(new), "learned": len(learned), "deep": len(deep),
        "quizzes": len(quizzes), "quiz_accuracy": round(q_right / q_total * 100) if q_total else None,
        "checks": checks, "asks": asks,
        "tokens": int((config.load().get("tokens_weekly") or {}).get(wk, 0)),
        "streak": streak(items, _monday(0)),
        "categories": [{"category": c, "n": n} for c, n in cats.most_common()],
        "top_tags": [t for t, _ in tags.most_common(8)],
        "new_items": [brief(it) for it in new][:30],
        "learned_items": [brief(it) for it in learned][:30],
        "insights": insights,
        "suggest": [brief(it) for it in backlog[:3]],
        "unlearned": len(backlog),
        "has_any": bool(new or learned or deep or quizzes or checks or asks),
    }


def render_md(r):
    lines = ["---", f'title: "学习周报 {r["week"]}"', f"date: {r['week']}", "tags: [周报]", "---", "",
             f"# 学习周报 · {r['label']}", "",
             f"- 新增笔记：{r['new']} 条", f"- 学会：{r['learned']} 条", f"- 精读：{r['deep']} 条",
             f"- 测验：{r['quizzes']} 次" + (f"，正确率 {r['quiz_accuracy']}%" if r["quiz_accuracy"] is not None else ""),
             f"- 理解检查题回答：{r['checks']} 次，问老师：{r['asks']} 次",
             f"- AI 消耗：约 {r['tokens']:,} tokens", f"- 连续学习：{r['streak']} 周", ""]
    if r["categories"]:
        lines += ["## 新增笔记的分类", ""] + [f"- {c['category']}：{c['n']} 条" for c in r["categories"]] + [""]
    if r["top_tags"]:
        lines += ["## 本周高频关键词", "", "、".join(r["top_tags"]), ""]
    if r["learned_items"]:
        lines += ["## 本周学会", ""] + [f"- {it['title']}" for it in r["learned_items"]] + [""]
    if r["suggest"]:
        lines += ["## 下周建议先学", ""] + [f"- {it['title']}" for it in r["suggest"]] + [""]
    return "\n".join(lines)


def save_md(offset=0):
    r = report(offset)
    folder = config.library_dir() / REPORT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{notes.safe_name('学习周报-' + r['week'])}.md"
    path.write_text(render_md(r), encoding="utf-8")
    return str(path)
