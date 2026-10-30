"""本地网页服务：只监听 127.0.0.1，只有你自己的电脑能打开。"""
import json
import mimetypes
import shutil
import tempfile
import traceback
import os
import platform
import subprocess
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__, backup, config, db, deep, douyin, insights, llm, notes, ocr, transcribe, weekly
from .worker import Worker, scan_inbox

_DEPS = None


def deps_status():
    """检查关键组件有没有装上（结果缓存，装好后重启程序即可刷新）。"""
    global _DEPS
    if _DEPS is None:
        import importlib.util as u
        import sys
        has = lambda m: u.find_spec(m) is not None
        _DEPS = {
            "python": platform.python_version(),
            "python_ok": (3, 10) <= sys.version_info[:2] <= (3, 12),
            "playwright": has("playwright"),
            "asr": has("faster_whisper") or has("mlx_whisper"),
        }
    return _DEPS

STATIC = Path(__file__).resolve().parent / "static"
worker: Worker = None
deep_runner: deep.DeepRunner = None
insight_runner: insights.InsightRunner = None


def open_path(p):
    p = str(p)
    sysname = platform.system()
    if sysname == "Windows":
        os.startfile(p)  # noqa
    elif sysname == "Darwin":
        subprocess.Popen(["open", p])
    else:
        subprocess.Popen(["xdg-open", p])


def reveal(p):
    p = str(p)
    sysname = platform.system()
    if sysname == "Windows":
        subprocess.Popen(["explorer", "/select,", p])
    elif sysname == "Darwin":
        subprocess.Popen(["open", "-R", p])
    else:
        subprocess.Popen(["xdg-open", str(Path(p).parent)])


class Handler(BaseHTTPRequestHandler):
    server_version = "DouyinStudy/1.0"

    def log_message(self, *a):
        pass

    # ---------------------------------------------------------- 工具
    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, msg, code=400):
        self._json({"error": msg}, code)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def _static(self, rel):
        p = (STATIC / rel).resolve()
        if STATIC not in p.parents or not p.is_file():
            return self._err("not found", 404)
        data = p.read_bytes()
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _restore_upload(self, dry):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return self._err("没有收到备份文件")
        if n > 3 * 1024 ** 3:
            return self._err("备份文件太大")
        tmpdir = Path(tempfile.mkdtemp(prefix="dsrs-"))
        f = tmpdir / "upload.zip"
        try:
            with open(f, "wb") as out:
                left = n
                while left > 0:
                    chunk = self.rfile.read(min(left, 1024 * 256))
                    if not chunk:
                        break
                    out.write(chunk)
                    left -= len(chunk)
            if dry:
                return self._json(backup.inspect(f))
            why = self._busy_reason()
            if why:
                return self._err(why)
            res = backup.restore(f)
            backup.prune_auto_backups(keep=5)
            worker.log(f"已从备份恢复：{res['items']} 条，其中 {res['done']} 条笔记；恢复前的数据已自动备份")
            return self._json(res)
        except backup.BackupError as e:
            return self._err(str(e))
        except Exception as e:
            traceback.print_exc()
            return self._err(f"恢复失败：{e}", 500)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _download(self, text, filename, ctype):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        if filename:
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{urllib.parse.quote(filename)}")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, f, ctype):
        size = f.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{urllib.parse.quote(f.name)}")
        self.send_header("Content-Length", str(size))
        self.end_headers()
        with open(f, "rb") as fh:
            shutil.copyfileobj(fh, self.wfile, 1024 * 256)

    def _busy_reason(self):
        if worker.state.get("busy"):
            return "后台正在处理视频，请先等处理完或点「停止」，再恢复备份"
        d = deep_runner.snapshot()
        if d.get("item_id") or d.get("pending"):
            return "正在精读，请等精读完成后再恢复备份"
        if insight_runner.snapshot().get("pending"):
            return "正在整理共识观点，请等整理完成后再恢复备份"
        return None

    def _local_only(self):
        # 防止别的网站在你浏览器里偷偷调用这个本地服务
        origin = self.headers.get("Origin")
        if origin and not origin.startswith(("http://127.0.0.1", "http://localhost")):
            self._err("forbidden", 403)
            return False
        return True

    # ---------------------------------------------------------- GET
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        path, qs = u.path, urllib.parse.parse_qs(u.query)
        q = lambda k, d=None: (qs.get(k) or [d])[0]

        if path in ("/", "/index.html"):
            return self._static("index.html")
        if path == "/print":
            return self._static("print.html")
        if path.startswith("/static/"):
            return self._static(path[len("/static/"):])
        if path.startswith("/files/"):  # 笔记目录里的图片（图文）
            rel = urllib.parse.unquote(path[len("/files/"):])
            lib = config.library_dir().resolve()
            f = (lib / rel).resolve()
            if lib not in f.parents or not f.is_file():
                return self._err("not found", 404)
            ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
            if f.suffix.lower() == ".webp":
                ctype = "image/webp"
            data = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "max-age=86400")
            self.end_headers()
            self.wfile.write(data)
            return

        if path == "/api/state":
            s = config.load()
            return self._json({
                "worker": worker.state, "logs": list(worker.logs)[-80:], "stats": db.stats(),
                "settings": config.public(s), "providers": config.PROVIDERS, "free_plans": config.FREE_PLANS,
                "library_dir": str(config.library_dir()), "inbox_dir": str(config.INBOX_DIR),
                "asr": transcribe.engine_status(),
                "ocr": ocr.status(), "version": __version__, "deps": deps_status(),
                "progress": worker.prog.snapshot(
                    max(0, db.stats()["by_status"].get("queued", 0))),
                "deep": deep_runner.snapshot(),
                "insights": insight_runner.snapshot(),
            })
        if path == "/api/graph":
            return self._json(insights.graph())
        if path == "/api/insights":
            return self._json({"categories": insights.categories(), "runner": insight_runner.snapshot()})
        if path.startswith("/api/insights/"):
            cat = urllib.parse.unquote(path[len("/api/insights/"):])
            ins = db.get_insight(cat)
            if not ins:
                return self._err("这个分类还没整理过共识观点", 404)
            titles = {it["id"]: (it.get("note") or {}).get("title") or it.get("title") or "未命名"
                      for it in db.done_items()}
            ins["titles"] = {i: titles[i] for i in ins["item_ids"] if i in titles}
            return self._json(ins)
        if path == "/api/weekly":
            return self._json(weekly.report(int(q("offset", "0") or 0)))
        if path == "/api/weekly/due":
            # 上一周的周报有内容、而且还没看过 → 学习库里提示一下
            last = weekly.report(-1)
            return self._json({"due": last["has_any"] and config.load().get("weekly_seen") != last["week"],
                               "week": last["week"]})
        if path == "/api/backup":
            try:
                f, m = backup.create(include_keys=q("keys", "1") == "1")
            except Exception as e:
                return self._err(f"备份失败：{e}", 500)
            try:
                return self._send_file(f, "application/zip")
            finally:
                shutil.rmtree(f.parent, ignore_errors=True)
        if path == "/api/backups":
            return self._json({"dir": str(backup.BACKUP_DIR), "files": backup.list_auto_backups()})
        if path == "/api/items":
            learned = q("learned")
            return self._json(db.list_items(
                status=q("status"), category=q("category"), q=(q("q") or "").strip() or None,
                learned=None if learned in (None, "") else learned == "1", starred=q("starred") == "1"))
        if path.startswith("/api/items/"):
            parts = path.split("/")
            try:
                item = db.get(int(parts[3]))
            except (ValueError, IndexError):
                item = None
            if not item:
                return self._err("找不到这条", 404)
            sub = parts[4] if len(parts) > 4 else ""
            name = notes.safe_name((item.get("note") or {}).get("title") or item.get("title"))
            if sub == "anki.txt":
                if not item.get("deep"):
                    return self._err("还没有精读结果")
                return self._download(deep.anki_tsv(item["deep"]), f"{name}-Anki卡片.txt", "text/plain")
            if sub == "mindmap.html":
                d = item.get("deep") or {}
                html = deep.mindmap_html(d.get("title") or name, d.get("mindmap"))
                if q("download") == "1":
                    return self._download(html, f"{name}-思维导图.html", "text/html")
                return self._download(html, None, "text/html")
            if sub == "prompt":
                return self._json({"text": deep.prompt_for_other_ai(item, config.load())})
            if sub == "md":
                body = notes.render(item).encode("utf-8")
                fname = urllib.parse.quote(notes.safe_name((item.get("note") or {}).get("title") or item.get("title")) + ".md")
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{fname}")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            return self._json(item)
        return self._err("not found", 404)

    # ---------------------------------------------------------- POST
    def do_POST(self):
        if not self._local_only():
            return
        u = urllib.parse.urlparse(self.path)
        path = u.path
        if path == "/api/restore":
            return self._restore_upload(urllib.parse.parse_qs(u.query).get("dry", ["0"])[0] == "1")
        b = self._body()

        if path == "/api/links":
            links = douyin.extract_links(b.get("text", ""))
            if not links:
                return self._err("没在内容里找到抖音链接。请粘贴抖音「分享 → 复制链接」得到的内容。")
            added = 0
            for link in links:
                vid, kind = douyin._match_id(link)
                item_id, new = db.add("link", aweme_id=vid, url=link)
                if new and kind == "note":
                    db.update(item_id, media_type="note")
                elif not new:
                    old = db.get(item_id)  # 以前被跳过的图文，现在可以处理了
                    if old and old["status"] == "skipped" and "图文" in (old.get("reason") or ""):
                        db.update(item_id, status="queued", media_type="note", reason=None, attempts=0)
                        new = True
                added += int(new)
            if b.get("process", True) and added:
                worker.submit("process")
            return self._json({"found": len(links), "added": added})

        if path == "/api/process":
            worker.submit("process")
            return self._json({"ok": True})
        if path == "/api/stop":
            worker.stop()
            return self._json({"ok": True})
        if path == "/api/login":
            worker.submit("login")
            return self._json({"ok": True})
        if path == "/api/sync":
            s = config.load()
            limit = int(b.get("limit") or s.get("sync_limit") or 50)
            config.save({"sync_limit": limit})
            worker.submit("sync", kind=b.get("kind", "collection"), limit=limit, then_process=True)
            return self._json({"ok": True})
        if path == "/api/inbox":
            n = scan_inbox()
            if n:
                worker.submit("process")
            return self._json({"added": n})
        if path == "/api/open":
            what = b.get("what")
            try:
                if what == "library":
                    open_path(config.library_dir())
                elif what == "inbox":
                    open_path(config.INBOX_DIR)
                elif what == "item":
                    it = db.get(int(b.get("id")))
                    if it and it.get("md_path") and Path(it["md_path"]).exists():
                        reveal(it["md_path"])
                    else:
                        return self._err("这条还没有生成笔记文件")
                elif what == "insight":
                    ins = db.get_insight(str(b.get("category") or ""))
                    if not ins or not ins.get("md_path") or not Path(ins["md_path"]).exists():
                        return self._err("还没有生成共识观点文件")
                    reveal(ins["md_path"])
                return self._json({"ok": True})
            except Exception as e:
                return self._err(f"打不开：{e}")

        if path == "/api/insights":
            cat = str(b.get("category") or "").strip()
            if not cat:
                return self._err("缺少分类")
            if not (config.llm_cfg(config.load(), "deep").get("api_key") or "").strip():
                return self._err("还没保存 AI Key。请到「设置」填好 Key，点「测试连接」（成功会自动保存）。")
            insight_runner.submit(cat)
            return self._json({"ok": True})
        if path == "/api/weekly/save":
            try:
                f = weekly.save_md(int(b.get("offset") or 0))
                reveal(f)
            except Exception as e:
                return self._err(f"保存失败：{e}")
            return self._json({"path": f})
        if path == "/api/weekly/seen":
            config.save({"weekly_seen": str(b.get("week") or "")})
            return self._json({"ok": True})

        if path == "/api/settings":
            patch = {k: v for k, v in b.items()
                     if k in config.DEFAULTS and k not in ("tokens_used", "tokens_weekly", "weekly_seen")}
            if "api_key" in patch and not str(patch["api_key"]).strip():
                patch.pop("api_key")  # 空着表示不修改
            if "deep_api_key" in patch and not str(patch["deep_api_key"]).strip():
                patch.pop("deep_api_key")
            if b.get("clear_key"):
                patch["api_key"] = ""
            if b.get("clear_deep_key"):
                patch["deep_api_key"] = ""
            if "deep_chunk_chars" in patch:
                patch["deep_chunk_chars"] = max(3000, min(100000, int(patch["deep_chunk_chars"] or 12000)))
            if "deep_prompt" in patch and not str(patch["deep_prompt"]).strip():
                patch["deep_prompt"] = config.DEFAULT_DEEP_PROMPT
            if "max_minutes" in patch:
                patch["max_minutes"] = max(1, min(120, int(patch["max_minutes"] or 15)))
            if isinstance(patch.get("categories"), str):
                patch["categories"] = [c.strip() for c in patch["categories"].replace("，", ",").split(",") if c.strip()]
            s = config.save(patch)
            return self._json(config.public(s))
        if path == "/api/test_llm":
            s = config.load()
            purpose = "deep" if b.get("purpose") == "deep" else "main"
            cfg = config.llm_cfg(s, purpose)
            for k in ("provider", "base_url", "model"):
                if b.get(k):
                    cfg[k] = b[k]
            if (b.get("api_key") or "").strip():
                cfg["api_key"] = b["api_key"].strip()
            cfg["kind"] = config.provider_kind(cfg.get("provider"), cfg.get("base_url"))
            try:
                reply = llm.test(cfg)
            except llm.LLMError as e:
                return self._json({"ok": False, "error": str(e)})
            # 测试成功就直接保存，免得忘了点「保存设置」
            if purpose == "deep":
                patch = {"deep_provider": cfg.get("provider"), "deep_base_url": cfg.get("base_url"),
                         "deep_model": cfg.get("model"), "deep_same": False}
                if (b.get("api_key") or "").strip():
                    patch["deep_api_key"] = cfg["api_key"]
            else:
                patch = {"provider": cfg.get("provider"), "base_url": cfg.get("base_url"), "model": cfg.get("model")}
                if (b.get("api_key") or "").strip():
                    patch["api_key"] = cfg["api_key"]
            config.save({k: v for k, v in patch.items() if v is not None})
            models = []
            try:
                models = llm.list_models(cfg)
            except llm.LLMError:
                pass
            return self._json({"ok": True, "reply": reply, "saved": True, "models": models})
        if path == "/api/free_setup":
            plan = b.get("plan")
            key = str(b.get("api_key") or "").strip()
            if plan not in config.FREE_PLANS:
                return self._err("未知的免费方案")
            if not key:
                return self._err("先把 Key 粘贴进来")
            try:
                model, tried = llm.free_setup(plan, key)
            except llm.LLMError as e:
                return self._err(str(e))
            p = config.FREE_PLANS[plan]
            config.save({"provider": p["provider"], "base_url": p["base_url"], "model": model, "api_key": key,
                         "deep_same": True, "free_plan": plan})
            worker.log(f"已配置免费方案：{p['name']} · {model}")
            return self._json({"ok": True, "plan": plan, "name": p["name"], "model": model, "tried": tried})
        if path == "/api/models":
            s = config.load()
            purpose = "deep" if b.get("purpose") == "deep" else "main"
            cfg = config.llm_cfg(s, purpose)
            for k in ("provider", "base_url"):
                if b.get(k):
                    cfg[k] = b[k]
            if (b.get("api_key") or "").strip():
                cfg["api_key"] = b["api_key"].strip()
            cfg["kind"] = config.provider_kind(cfg.get("provider"), cfg.get("base_url"))
            try:
                return self._json({"models": llm.list_models(cfg)})
            except llm.LLMError as e:
                return self._err(str(e))

        if path == "/api/restore_auto":
            name = Path(str(b.get("name") or "")).name
            f = backup.BACKUP_DIR / name
            if not name.endswith(".zip") or not f.exists():
                return self._err("找不到这个自动备份")
            why = self._busy_reason()
            if why:
                return self._err(why)
            try:
                return self._json(backup.restore(f))
            except backup.BackupError as e:
                return self._err(str(e))

        if path == "/api/paste":
            text = str(b.get("text") or "").strip()
            if len(text) < 50:
                return self._err("文稿太短了，至少要 50 个字")
            title = str(b.get("title") or "").strip() or text[:20].replace("\n", " ") + "…"
            dcfg = config.llm_cfg(config.load(), "deep")
            if not (dcfg.get("api_key") or "").strip():
                return self._err("精读用的 AI Key 还没保存。请到「设置」填好 Key，点「测试连接」（成功会自动保存）。")
            item_id, _ = db.add("paste", title=title, author=str(b.get("author") or "").strip() or None)
            db.update(item_id, transcript=text, status="done")
            deep_runner.submit(item_id)
            return self._json({"id": item_id})

        if path.startswith("/api/items/") and path.split("/")[-1] in ("deep", "check", "ask", "quiz"):
            try:
                item_id = int(path.split("/")[3])
            except ValueError:
                return self._err("bad id")
            act = path.split("/")[-1]
            try:
                if act == "deep":
                    if not (db.get(item_id) or {}).get("transcript"):
                        return self._err("这条还没有文字稿，等处理完再精读")
                    dcfg = config.llm_cfg(config.load(), "deep")
                    if not (dcfg.get("api_key") or "").strip():
                        return self._err("精读用的 AI Key 还没保存。请到「设置」填好 Key，点「测试连接」（成功会自动保存）。")
                    if not (dcfg.get("model") or "").strip():
                        return self._err("精读用的模型名是空的，请到「设置」里选一个模型")
                    deep_runner.submit(item_id)
                    return self._json({"ok": True, "model": dcfg["model"]})
                if act == "check":
                    ans = str(b.get("answer") or "").strip()
                    if not ans:
                        return self._err("先写下你的回答")
                    return self._json(deep.check_answer(item_id, int(b.get("idx", -1)), ans))
                if act == "ask":
                    qtext = str(b.get("q") or "").strip()
                    if not qtext:
                        return self._err("问题不能为空")
                    return self._json(deep.ask(item_id, qtext))
                if act == "quiz":
                    deep.quiz_result(item_id, int(b.get("score", 0)), int(b.get("total", 0)))
                    return self._json({"ok": True})
            except llm.LLMError as e:
                return self._err(str(e))

        if path.startswith("/api/items/") and path.endswith("/action"):
            try:
                item_id = int(path.split("/")[3])
            except ValueError:
                return self._err("bad id")
            it = db.get(item_id)
            if not it:
                return self._err("找不到这条", 404)
            act = b.get("action")
            if act in ("retry", "reextract", "include"):
                if act == "include" and it.get("note"):
                    # 用户认为"无关"的也值得学 → 直接收进学习库，不用再花钱提炼
                    it["note"]["relevant"] = True
                    path_ = notes.write(it)
                    db.update(item_id, status="done", note=it["note"], md_path=path_, reason=None)
                    return self._json(db.get(item_id))
                db.update(item_id, status="queued", attempts=0, reason=None)
                worker.submit("process")
            elif act == "learned":
                v = bool(b.get("value", True))
                db.update(item_id, learned=int(v), learned_at=time.time() if v else None)
            elif act == "star":
                db.update(item_id, starred=int(bool(b.get("value", True))))
            elif act == "note":
                db.update(item_id, my_note=str(b.get("text", ""))[:20000])
                it = db.get(item_id)
                if it["status"] == "done":
                    db.update(item_id, md_path=notes.write(it))
            elif act == "category":
                cat = str(b.get("value") or "").strip()
                if cat and it.get("note"):
                    it["note"]["category"] = cat
                    db.update(item_id, note=it["note"], category=cat)
                    it = db.get(item_id)
                    if it["status"] == "done":
                        db.update(item_id, md_path=notes.write(it))
            elif act == "delete":
                notes.remove(it, with_images=True)
                db.delete(item_id)
                return self._json({"deleted": True})
            else:
                return self._err("未知操作")
            return self._json(db.get(item_id))

        return self._err("not found", 404)


def serve(port=8765, open_browser=True):
    global worker
    db.init()
    worker = Worker()
    global deep_runner
    deep_runner = deep.DeepRunner(worker.log)
    global insight_runner
    insight_runner = insights.InsightRunner(worker.log)
    srv = None
    for p in range(port, port + 20):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if srv is None:
        raise SystemExit("找不到可用端口")
    url = f"http://127.0.0.1:{port}/"
    print("=" * 56)
    print(f"  收藏学习台 v{__version__} 已启动")
    print(f"  在浏览器打开：{url}")
    print("  关闭这个窗口即可退出程序")
    print("=" * 56, flush=True)
    if open_browser:
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
