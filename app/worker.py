"""后台处理线程：一条一条地 读信息 → 下载 → 转文字 → AI 提炼 → 写笔记。

浏览器只能在同一个线程里操作，所以所有抖音相关的事都放在这个线程里排队做。
"""
import collections
import queue
import threading
import time
import traceback
from pathlib import Path

from . import config, db, douyin, llm, notes, ocr, progress, transcribe

MEDIA_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".flv", ".avi", ".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg"}


class Worker:
    def __init__(self):
        self.cmds = queue.Queue()
        self.logs = collections.deque(maxlen=300)
        self.state = {"busy": False, "task": "", "item_id": None, "stage": "", "done": 0, "total": 0,
                      "last_error": None}  # 最近一次登录 / 同步失败的原因，网页上会显示成提示条
        self._stop = threading.Event()
        self.browser = None
        self.retry_later = []
        self.prog = progress.Progress()
        self.thread = threading.Thread(target=self._run, daemon=True, name="worker")
        self.thread.start()

    # ------------------------------------------------------------ 对外接口
    def log(self, msg):
        self.logs.append({"t": time.time(), "msg": str(msg)})
        print(time.strftime("%H:%M:%S"), msg, flush=True)

    def submit(self, cmd, **kw):
        self._stop.clear()
        self.cmds.put((cmd, kw))

    def stop(self):
        self._stop.set()
        self.log("收到停止指令，处理完当前这一步就停。")

    def stopping(self):
        return self._stop.is_set()

    # ------------------------------------------------------------ 主循环
    def _run(self):
        while True:
            cmd, kw = self.cmds.get()
            self.state.update(busy=True, task=cmd, stage="", item_id=None)
            if cmd in ("login", "sync"):
                self.state["last_error"] = None
            try:
                if cmd == "process":
                    self._process_all()
                elif cmd == "login":
                    self._browser().ensure_login(should_stop=self.stopping)
                elif cmd == "sync":
                    self._sync(kw.get("kind", "collection"), kw.get("limit", 50), kw.get("then_process", True))
            except douyin.DouyinError as e:
                self.log(f"⚠ {e}")
                self._set_error(cmd, str(e))
            except Exception as e:
                self.log(f"⚠ 出错了：{e}")
                self._set_error(cmd, f"出错了：{e}")
                traceback.print_exc()
            finally:
                if self.cmds.empty():
                    self._close_browser()
                    self.state.update(busy=False, task="", stage="", item_id=None)

    def _set_error(self, cmd, msg):
        if cmd in ("login", "sync"):
            self.state["last_error"] = {"task": cmd, "msg": msg, "t": time.time()}

    def clear_error(self):
        self.state["last_error"] = None

    def _browser(self):
        if self.browser is None:
            self.browser = douyin.Browser(config.load().get("browser", "auto"), log=self.log)
        self.browser.start()
        return self.browser

    def _close_browser(self):
        if self.browser:
            self.browser.close()
            self.browser = None

    # ------------------------------------------------------------ 收藏夹同步
    def _sync(self, kind, limit, then_process):
        name = "喜欢" if kind == "like" else "收藏"
        self.log(f"开始读取抖音「{name}」列表（最多 {limit} 条）……")
        added, requeued, notes_n = [0], [0], [0]

        def on_item(d):
            item_id, new = db.add("favorite", aweme_id=d["aweme_id"], url=d["url"], title=d["title"],
                                  author=d["author"], duration=d["duration"], cover=d["cover"])
            if new:
                added[0] += 1
                if d.get("is_note"):
                    db.update(item_id, media_type="note")
                    notes_n[0] += 1
            else:
                old = db.get(item_id)
                retry_note = (old and old["status"] == "skipped" and "图文" in (old.get("reason") or ""))
                if old and (old["status"] == "failed" or retry_note):  # 之前失败的 / 以前跳过的图文，这次重新处理
                    db.update(item_id, status="queued", attempts=0, reason=None,
                              media_type="note" if (d.get("is_note") or retry_note) else old.get("media_type"))
                    requeued[0] += 1

        n = self._browser().sync_list(kind, limit, on_item, should_stop=self.stopping)
        msg = f"读到 {n} 条，其中新增 {added[0]} 条" + (f"（含图文 {notes_n[0]} 条）" if notes_n[0] else "")
        if requeued[0]:
            msg += f"，之前失败的 {requeued[0]} 条重新排队"
        self.log(msg + "（已完成或已跳过的不会重复处理）。")
        if then_process and not self.stopping():
            self._process_all()

    # ------------------------------------------------------------ 批量处理
    def _process_all(self):
        self.retry_later = []
        self.state.update(done=0, total=db.stats()["by_status"].get("queued", 0))
        if not self.state["total"]:
            self.log("队列里没有待处理的视频。")
            return
        self.log(f"开始处理，共 {self.state['total']} 条。")
        while not self.stopping():
            it = db.next_queued()
            if it is None:
                if self.retry_later:
                    ids, self.retry_later = self.retry_later, []
                    self.log(f"有 {len(ids)} 条失败了，30 秒后自动重试一次……")
                    for _ in range(30):
                        if self.stopping():
                            return
                        time.sleep(1)
                    for i in ids:
                        db.update(i, status="queued")
                    self.state["total"] += len(ids)
                    continue
                break
            self.state.update(item_id=it["id"])
            self._process_one(it)
            self.state["done"] += 1
        self.log("这一批处理完了。" if not self.stopping() else "已停止。")

    def _stage(self, it, status, msg):
        db.update(it["id"], status=status, reason=None)
        self.prog.stage(status)
        self.state["stage"] = msg
        self.log(f"[{it['id']}] {msg}")

    def _process_one(self, it):
        s = config.load()
        self.prog.begin(it, bool(it.get("transcript")), transcribe.pick_engine(s.get("asr_engine", "auto")))
        try:
            self._process_one_inner(it, s)
        finally:
            cur = db.get(it["id"])
            self.prog.end(ok=bool(cur and cur["status"] == "done"))

    def _process_one_inner(self, it, s):
        label = (it.get("title") or it.get("url") or "")[:30]
        try:
            # 1-2. 拿到视频文件（已经有文字稿的跳过这一步，比如重新提炼）
            if not it.get("transcript"):
                media = self._get_media(it, s)
                if media is None:
                    return
                if isinstance(media, dict) and "note" in media:  # 图文：下载图片 + 识别图片文字
                    if not self._process_note(it, media["note"]):
                        return
                    it = db.get(it["id"])
                    media = None
                elif isinstance(media, dict):  # 拿到了视频自带字幕，不用下载和转写
                    db.update(it["id"], transcript=media["text"], segments=media["segments"] or None)
                    it = db.get(it["id"])
                    media = None
            if not it.get("transcript"):
                self._stage(it, "transcribing", f"转文字：{label}")
                try:
                    tr = transcribe.transcribe(
                        media, engine=s.get("asr_engine", "auto"), mlx_model=s.get("mlx_model"),
                        size=s.get("whisper_model", "small"), use_mirror=s.get("use_hf_mirror", False),
                        max_minutes=s.get("max_minutes", 15), log=self.log, should_stop=self.stopping,
                        on_progress=self.prog.set_frac)
                except transcribe.NoSpeech as e:
                    db.update(it["id"], status="skipped", reason=str(e))
                    self.log(f"[{it['id']}] 跳过：{e}")
                    self._cleanup(it, media, s)
                    return
                self._cleanup(it, media, s)
                if self.stopping():
                    db.update(it["id"], status="queued")
                    return
                db.update(it["id"], transcript=tr["text"], segments=tr["segments"],
                          duration=it.get("duration") or tr["duration"])
                it = db.get(it["id"])

            # 3. AI 提炼
            if not (s.get("api_key") or "").strip():
                db.update(it["id"], status="need_key", reason="已转成文字，填好 AI Key 后点「重新提炼」生成笔记")
                self.log(f"[{it['id']}] 已转成文字；还没填 AI Key，先不提炼。")
                return
            self._stage(it, "extracting", f"AI 提炼：{label}")
            note, used = llm.extract(s, it.get("title"), it.get("author"), it["transcript"],
                                     kind="note" if it.get("media_type") == "note" else "video")
            config.add_tokens(used)
            if note.get("skip"):
                db.update(it["id"], status="skipped", reason=note.get("skip_reason"), note=None)
                self.log(f"[{it['id']}] 跳过：{note.get('skip_reason')}")
                return
            if not note["relevant"] and s.get("only_relevant", True) and it["source"] != "paste":
                notes.remove(it)
                db.update(it["id"], status="irrelevant", note=note, category=note["category"], md_path=None,
                          reason="和你设置的关注主题无关，已收起")
                self.log(f"[{it['id']}] 和关注主题无关，已收起：{note['title']}")
                return
            it["note"] = note
            path = notes.write(it)
            db.update(it["id"], status="done", note=note, category=note["category"], md_path=path, reason=None)
            self.log(f"[{it['id']}] ✓ 完成：{note['title']}")

        except douyin.NotLoggedIn as e:
            self._fail(it, f"{e}。请点「登录抖音」后重试", retry=False)
        except (douyin.DouyinError, llm.LLMError) as e:
            self._fail(it, str(e), retry=getattr(e, "retry", isinstance(e, douyin.DouyinError)))
        except Exception as e:
            traceback.print_exc()
            self._fail(it, f"意外错误：{e}", retry=True)

    def _fail(self, it, msg, retry):
        cur = db.get(it["id"]) or it
        attempts = (cur.get("attempts") or 0) + 1
        db.update(it["id"], status="failed", reason=msg, attempts=attempts)
        self.log(f"[{it['id']}] ✗ 失败：{msg}")
        if retry and attempts < 2:
            self.retry_later.append(it["id"])

    def _get_media(self, it, s):
        """返回本地视频路径；视频自带字幕时返回 {"text", "segments"}；不需要处理时返回 None（已标记跳过）。"""
        if it["source"] == "local":
            p = Path(it["local_path"])
            if not p.exists():
                raise douyin.DouyinError("本地文件不见了")
            return p

        aweme_id = it.get("aweme_id")
        if not aweme_id:
            self._stage(it, "fetching", f"解析链接：{it['url'][:40]}")
            aweme_id, kind = douyin.resolve(it["url"])
            if kind == "note":
                db.update(it["id"], media_type="note")
                it["media_type"] = "note"
            other = db.conn().execute("SELECT id FROM items WHERE aweme_id=? AND id<>?",
                                      (aweme_id, it["id"])).fetchone()
            if other:
                db.delete(it["id"])
                self.log(f"[{it['id']}] 这个视频之前已经加过了（第 {other['id']} 条），不重复处理。")
                return None
            db.update(it["id"], aweme_id=aweme_id)
            it["aweme_id"] = aweme_id

        kind = "note" if it.get("media_type") == "note" else "video"
        self._stage(it, "fetching", f"读取{'图文' if kind == 'note' else '视频'}信息：{aweme_id}")
        b = self._browser()
        try:
            d = b.fetch_detail(aweme_id, kind)
        except douyin.NotLoggedIn:
            b.ensure_login(should_stop=self.stopping)
            d = b.fetch_detail(aweme_id, kind)
        db.update(it["id"], title=d.get("title") or it.get("title"), author=d.get("author") or it.get("author"),
                  duration=d.get("duration") or it.get("duration"), cover=d.get("cover") or it.get("cover"),
                  url=d.get("url") or it.get("url"))
        it.update({k: v for k, v in d.items() if v and k in ("title", "author", "duration", "cover", "url")})
        self.prog.set_title(it.get("title"), d.get("duration"))
        if d.get("is_ad"):
            db.update(it["id"], status="skipped", reason="广告视频")
            self.log(f"[{it['id']}] 跳过：广告")
            return None
        if d.get("is_note"):
            db.update(it["id"], media_type="note")
            it["media_type"] = "note"
            if not d.get("images"):
                db.update(it["id"], status="skipped", reason="这条图文没有读到图片")
                return None
            return {"note": d}

        if s.get("use_subtitles", True) and d.get("subtitle_urls"):
            for su in d["subtitle_urls"]:
                try:
                    raw = b.fetch_text(su)
                    text = transcribe.parse_subtitle(raw)
                except Exception:
                    continue
                if len(text) >= 30:
                    self.log(f"[{it['id']}] 视频自带字幕，直接使用（跳过下载和转写）")
                    return {"text": text, "segments": transcribe.subtitle_segments(raw)}

        self._stage(it, "downloading", f"下载视频：{(it.get('title') or '')[:30]}")
        dest = config.MEDIA_DIR / f"{aweme_id}.mp4"
        b.download(d.get("play_urls") or [], dest)
        time.sleep(1.0)  # 别太快，降低被风控的概率
        return dest

    def _process_note(self, it, d):
        """图文：下载图片到笔记目录，识别图片里的文字，和正文合成文字稿。返回 False 表示已标记跳过。"""
        aweme_id = it.get("aweme_id") or str(it["id"])
        imgs = d.get("images") or []
        self.prog.mark_note(len(imgs))
        self._stage(it, "downloading", f"下载图文图片（{len(imgs)} 张）：{(it.get('title') or '')[:24]}")
        lib = config.library_dir()
        folder = lib / notes.IMAGE_DIR / aweme_id
        files = self._browser().download_images(imgs, folder)
        rels = [f.relative_to(lib).as_posix() for f in files]
        db.update(it["id"], images=rels, cover="/files/" + rels[0])

        self._stage(it, "transcribing", f"识别图片文字（{len(files)} 张）")
        parts = []
        desc = (d.get("desc") or it.get("title") or "").strip()
        if desc:
            parts.append("【正文】\n" + desc)
        if ocr.backend() is None:
            self.log(f"[{it['id']}] ⚠ 没装文字识别组件，只用正文。重新运行一次安装脚本就能识别图片里的字。")
        else:
            for i, f in enumerate(files, 1):
                if self.stopping():
                    break
                try:
                    text = ocr.recognize(f)
                except Exception as e:
                    self.log(f"[{it['id']}] 第 {i} 张图识别失败：{str(e)[:80]}")
                    text = ""
                if text:
                    parts.append(f"【图{i}】\n{text}")
                self.prog.set_frac(i / len(files))
        transcript = "\n\n".join(parts)
        if len(transcript.replace("【正文】", "").replace(" ", "").replace("\n", "")) < 15:
            db.update(it["id"], status="skipped", reason="图文里几乎没有文字（可能是纯图片、表情包或摄影作品）")
            self.log(f"[{it['id']}] 跳过：图文里几乎没有文字")
            return False
        db.update(it["id"], transcript=transcript, segments=None)
        self.log(f"[{it['id']}] 图文文字已提取：{len(files)} 张图，共 {len(transcript)} 字")
        return True

    def _cleanup(self, it, media, s):
        if media is None:
            return
        if it["source"] == "local" or s.get("keep_video"):
            return
        try:
            Path(media).unlink(missing_ok=True)
        except Exception:
            pass


def scan_inbox():
    """把 data/inbox 文件夹里的音视频加入队列。返回新增条数。"""
    n = 0
    for p in sorted(config.INBOX_DIR.rglob("*")):
        if p.is_file() and p.suffix.lower() in MEDIA_EXT:
            _, new = db.add("local", local_path=str(p), title=p.stem)
            n += int(new)
    return n
