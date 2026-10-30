"""SQLite 条目库。每条视频一行，记录处理状态、文字稿、AI 笔记和学习进度。"""
import json
import sqlite3
import threading
import time

from .config import DB_PATH

# 状态：
#   queued       等待处理
#   fetching     读取视频信息
#   downloading  下载中
#   transcribing 转文字中
#   extracting   AI 提炼中
#   done         完成，可以学习
#   need_key     已转成文字，但没配 AI Key，等配好后再提炼
#   irrelevant   和关注主题无关（自动收起，不算失败）
#   skipped      广告 / 图文 / 纯音乐 / 无对白，自动跳过
#   failed       失败，可以重试
ACTIVE = ("fetching", "downloading", "transcribing", "extracting")

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL DEFAULT 'link',      -- link / favorite / local
  aweme_id TEXT UNIQUE,
  url TEXT,
  local_path TEXT,
  title TEXT,
  author TEXT,
  duration REAL,
  cover TEXT,
  status TEXT NOT NULL DEFAULT 'queued',
  reason TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  transcript TEXT,
  note_json TEXT,
  category TEXT,
  md_path TEXT,
  learned INTEGER NOT NULL DEFAULT 0,
  starred INTEGER NOT NULL DEFAULT 0,
  my_note TEXT NOT NULL DEFAULT '',
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  learned_at REAL
);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
-- 共识观点：每个分类一份，AI 从这个分类的多条笔记里找出互相印证 / 有分歧的观点
CREATE TABLE IF NOT EXISTS insights (
  category TEXT PRIMARY KEY,
  data_json TEXT NOT NULL,
  item_ids TEXT NOT NULL,     -- 整理时用到的笔记 id（逗号分隔），用来判断有没有新笔记
  model TEXT,
  md_path TEXT,
  created_at REAL NOT NULL
);
"""

_local = threading.local()
_write_lock = threading.Lock()


def conn():
    c = getattr(_local, "conn", None)
    if c is None:
        c = sqlite3.connect(DB_PATH, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        _local.conn = c
    return c


EXTRA_COLUMNS = {
    "segments_json": "TEXT",   # 带时间戳的文字稿分段
    "deep_json": "TEXT",       # 精读结果
    "chat_json": "TEXT",       # 精读里的答题点评、问老师记录
    "media_type": "TEXT",      # video / note（图文）
    "images_json": "TEXT",     # 图文的图片（相对于笔记目录的路径列表）
}


def init():
    with _write_lock:
        conn().executescript(SCHEMA)
        have = {r["name"] for r in conn().execute("PRAGMA table_info(items)")}
        for col, typ in EXTRA_COLUMNS.items():
            if col not in have:  # 老版本的数据库自动升级
                conn().execute(f"ALTER TABLE items ADD COLUMN {col} {typ}")
        # 程序上次被强制关掉时，卡在中间状态的条目放回队列
        conn().execute(
            f"UPDATE items SET status='queued' WHERE status IN ({','.join('?' * len(ACTIVE))})", ACTIVE)
        conn().commit()


JSON_FIELDS = {"note": "note_json", "segments": "segments_json", "deep": "deep_json", "chat": "chat_json",
               "images": "images_json"}


def _row(r):
    if r is None:
        return None
    d = dict(r)
    for name, col in JSON_FIELDS.items():
        if col in d:
            d[name] = json.loads(d.pop(col) or "null")
    return d


def add(source, *, aweme_id=None, url=None, local_path=None, title=None, author=None,
        duration=None, cover=None):
    """新增一条；同一个视频（aweme_id 相同）不会重复添加。返回 (id, 是否新增)。"""
    now = time.time()
    with _write_lock:
        c = conn()
        if aweme_id:
            r = c.execute("SELECT id FROM items WHERE aweme_id=?", (aweme_id,)).fetchone()
            if r:
                return r["id"], False
        if local_path:
            r = c.execute("SELECT id FROM items WHERE local_path=?", (local_path,)).fetchone()
            if r:
                return r["id"], False
        cur = c.execute(
            "INSERT INTO items(source,aweme_id,url,local_path,title,author,duration,cover,status,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,'queued',?,?)",
            (source, aweme_id, url, local_path, title, author, duration, cover, now, now))
        c.commit()
        return cur.lastrowid, True


def update(item_id, **fields):
    if not fields:
        return
    for name, col in JSON_FIELDS.items():
        if name in fields:
            v = fields.pop(name)
            fields[col] = json.dumps(v, ensure_ascii=False) if v is not None else None
    fields["updated_at"] = time.time()
    keys = list(fields)
    with _write_lock:
        conn().execute(f"UPDATE items SET {','.join(k + '=?' for k in keys)} WHERE id=?",
                       [fields[k] for k in keys] + [item_id])
        conn().commit()


def get(item_id):
    return _row(conn().execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone())


def delete(item_id):
    with _write_lock:
        conn().execute("DELETE FROM items WHERE id=?", (item_id,))
        conn().commit()


def next_queued():
    return _row(conn().execute(
        "SELECT * FROM items WHERE status='queued' ORDER BY id LIMIT 1").fetchone())


def list_items(status=None, category=None, q=None, learned=None, starred=None, limit=1000):
    sql = ("SELECT id,source,aweme_id,url,title,author,duration,cover,status,reason,category,learned,starred,"
           "created_at,updated_at,note_json,media_type,(deep_json IS NOT NULL) AS has_deep FROM items WHERE 1=1")
    args = []
    if status:
        statuses = status.split(",")
        sql += f" AND status IN ({','.join('?' * len(statuses))})"
        args += statuses
    if category:
        sql += " AND category=?"
        args.append(category)
    if learned is not None:
        sql += " AND learned=?"
        args.append(1 if learned else 0)
    if starred:
        sql += " AND starred=1"
    if q:
        like = f"%{q}%"
        sql += " AND (title LIKE ? OR author LIKE ? OR note_json LIKE ? OR transcript LIKE ? OR my_note LIKE ?)"
        args += [like] * 5
    sql += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    out = []
    for r in conn().execute(sql, args).fetchall():
        d = _row(r)
        note = d.pop("note") or {}
        d["summary"] = note.get("summary", "")
        d["note_title"] = note.get("title", "")
        d["tags"] = note.get("tags", [])
        d["difficulty"] = note.get("difficulty", "")
        out.append(d)
    return out


def done_items():
    """学习库里的全部笔记（含 JSON 字段），图谱、共识观点和周报用。"""
    return [_row(r) for r in conn().execute(
        "SELECT id,title,author,category,learned,learned_at,starred,created_at,md_path,media_type,"
        "note_json,deep_json,chat_json FROM items WHERE status='done' ORDER BY id")]


def get_insight(category):
    r = conn().execute("SELECT * FROM insights WHERE category=?", (category,)).fetchone()
    if r is None:
        return None
    d = dict(r)
    d["data"] = json.loads(d.pop("data_json"))
    d["item_ids"] = [int(x) for x in d["item_ids"].split(",") if x]
    return d


def list_insights():
    return [get_insight(r["category"]) for r in conn().execute("SELECT category FROM insights ORDER BY created_at DESC")]


def save_insight(category, data, item_ids, model, md_path):
    with _write_lock:
        conn().execute(
            "INSERT OR REPLACE INTO insights(category,data_json,item_ids,model,md_path,created_at) VALUES(?,?,?,?,?,?)",
            (category, json.dumps(data, ensure_ascii=False), ",".join(map(str, item_ids)), model, md_path, time.time()))
        conn().commit()


def stats():
    c = conn()
    by_status = {r["status"]: r["n"] for r in c.execute("SELECT status, COUNT(*) n FROM items GROUP BY status")}
    cats = [dict(r) for r in c.execute(
        "SELECT category, COUNT(*) n, SUM(learned) learned FROM items WHERE status='done' "
        "GROUP BY category ORDER BY n DESC")]
    learned = c.execute("SELECT COUNT(*) FROM items WHERE status='done' AND learned=1").fetchone()[0]
    starred = c.execute("SELECT COUNT(*) FROM items WHERE status='done' AND starred=1").fetchone()[0]
    return {"by_status": by_status, "categories": cats, "learned": learned, "starred": starred,
            "total": sum(by_status.values())}
