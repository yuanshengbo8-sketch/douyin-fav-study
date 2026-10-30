/* 收藏学习台 前端（原生 JS，不需要编译） */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const view = $("#view");

/* ---------------------------------------------------------------- 线条图标（Lucide 风格，ISC 开源协议） */
const ICONS = {
  shuffle: '<path d="M2 18h1.4c1.3 0 2.5-.6 3.3-1.7l6.1-8.6c.7-1.1 2-1.7 3.3-1.7H22"/><path d="m18 2 4 4-4 4"/><path d="M2 6h1.9c1.5 0 2.9.9 3.6 2.2"/><path d="M22 18h-5.9c-1.3 0-2.6-.7-3.3-1.8l-.5-.8"/><path d="m18 14 4 4-4 4"/>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  play: '<path d="M6 3.5v17a1 1 0 0 0 1.5.86l14-8.5a1 1 0 0 0 0-1.72l-14-8.5A1 1 0 0 0 6 3.5z" fill="currentColor" stroke="none"/>',
  star: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/>',
  starFill: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" fill="currentColor"/>',
  bulb: '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
  eye: '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
  coffee: '<path d="M10 2v2"/><path d="M14 2v2"/><path d="M6 2v2"/><path d="M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"/>',
  cap: '<path d="M21.42 10.92a1 1 0 0 0-.02-1.84L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.83l8.57 3.91a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
  book: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  retry: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  checkCircle: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  xCircle: '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
  trophy: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
  folder: '<path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"/>',
  sparkles: '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0L14.06 8.5A2 2 0 0 0 15.5 9.94l6.14 1.58a.5.5 0 0 1 0 .96L15.5 14.06a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
};
const ico = (name, cls = "ic") => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;

/* ---------------------------------------------------------------- 分类配色（Radix Colors 色阶） */
const CAT_PALETTE = ["blue", "orange", "violet", "pink", "green", "indigo", "amber", "teal", "cyan", "red"];
const CAT_FIXED = {
  "AI 工具推荐": "blue", "提示词技巧": "orange", "AI 编程": "violet", "AI 绘画与视频": "pink", "AI 办公效率": "green",
  "大模型与行业资讯": "indigo", "AI 副业与变现": "amber", "AI 学习方法": "teal", "其他": "gray", "未分类": "gray",
};
function catColor(name) {
  name = name || "其他";
  if (CAT_FIXED[name]) return CAT_FIXED[name];
  let h = 0; for (const ch of name) h = (h * 31 + ch.codePointAt(0)) >>> 0;
  return CAT_PALETTE[h % CAT_PALETTE.length];
}
const catChip = (name, extra = "") => `<span class="chip cat cat-${catColor(name)} ${extra}">${esc(name || "其他")}</span>`;

const STATUS = {
  queued: ["排队中", "gray"], fetching: ["读取信息", "teal"], downloading: ["下载中", "teal"],
  transcribing: ["转文字中", "teal"], extracting: ["AI 提炼中", "teal"], done: ["已完成", "teal"],
  need_key: ["待提炼", "warn"], irrelevant: ["主题无关", "gray"], skipped: ["已跳过", "gray"], failed: ["失败", "bad"],
};
const ACTIVE = ["queued", "fetching", "downloading", "transcribing", "extracting"];

let STATE = null;
let libFilter = { q: "", learned: "", starred: "", category: "" };
let procTab = "active";
let lastItems = [];

async function api(path, body) {
  const opt = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const r = await fetch(path, opt);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `请求失败 ${r.status}`);
  return j;
}

function toast(msg, ms = 2600) {
  const t = $("#toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast._t); toast._t = setTimeout(() => (t.hidden = true), ms);
}

const fmtDur = (s) => { s = Math.round(s || 0); return s ? `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}` : ""; };
const fmtTime = (t) => new Date(t * 1000).toLocaleTimeString("zh-CN", { hour12: false });

/* ---------------------------------------------------------------- 状态轮询 */
async function refreshState() {
  try { STATE = await api("/api/state"); } catch { return; }
  const st = STATE.stats, w = STATE.worker;
  const queued = ACTIVE.reduce((n, k) => n + (st.by_status[k] || 0), 0);
  const q = $("#navQueue"); q.hidden = !queued; q.textContent = queued;
  const sf = $("#sideStatus");
  const pg = STATE.progress || {}, dp = STATE.deep || {};
  const parts = [];
  if (w.busy) parts.push(pg.item_id ? `${pg.stage_label} ${pg.pct}% · ${fmtEta(pg.eta)}` : (w.stage || "处理中…"));
  if (dp.item_id) parts.push(`精读 ${dp.pct || 0}% · ${fmtEta(dp.eta)}`);
  sf.className = "side-foot" + (parts.length ? " busy" : "");
  sf.textContent = parts.join("\n") || `就绪 · v${STATE.version || ""}`;
  $("#navCats").innerHTML = (st.categories || []).map((c) =>
    `<a href="#/library/cat/${encodeURIComponent(c.category || "其他")}" class="${libFilter.category === c.category ? "on" : ""}">
      <i class="dot cat-${catColor(c.category)}"></i>${esc(c.category || "其他")}<span>${c.n}</span></a>`).join("");
  return STATE;
}

let pollTimer = null;
let wasDeepBusy = false;
let lastInsKey = null;
function startPolling() {
  clearTimeout(pollTimer);
  const tick = async () => {
    const before = JSON.stringify(STATE?.stats);
    await refreshState();
    const r = route();
    if (r.name === "process") renderProcessLive();
    else if (r.name === "library" && JSON.stringify(STATE?.stats) !== before) renderLibrary(true);
    else if (r.name === "item" && curItem) {
      const busy = deepBusy(curItem.id);
      if (busy && itemTab === "deep") renderDeepTab($("#tabBody"));
      if (wasDeepBusy && !busy) {
        await renderItem(curItem.id, "deep");
        const err = curItem?.chat?.deep_error;
        toast(err ? "精读失败：" + err : "精读完成 🎉", err ? 6000 : 2600);
      }
      wasDeepBusy = busy;
    }
    // 共识观点整理完（或失败）时刷新页面
    const insKey = JSON.stringify([STATE?.insights?.pending, STATE?.insights?.errors]);
    if (insKey !== lastInsKey) {
      if (lastInsKey !== null && r.name === "graph" && r.tab === "consensus") renderGraphPage(r.tab, r.category, true);
      lastInsKey = insKey;
    }
    const active = STATE?.worker?.busy || STATE?.deep?.item_id || STATE?.insights?.pending?.length;
    pollTimer = setTimeout(tick, active ? 1000 : 2500);
  };
  pollTimer = setTimeout(tick, 1000);
}

/* ---------------------------------------------------------------- 路由 */
function route() {
  const h = decodeURIComponent(location.hash.slice(1) || "/library");
  const p = h.split("/").filter(Boolean);
  if (p[0] === "item") return { name: "item", id: +p[1], tab: p[2] };
  if (p[0] === "process") return { name: "process" };
  if (p[0] === "settings") return { name: "settings" };
  if (p[0] === "graph") return { name: "graph", tab: p[1] === "consensus" ? "consensus" : "map", category: p.slice(2).join("/") };
  if (p[0] === "weekly") return { name: "weekly", offset: Math.min(0, parseInt(p[1] || "0", 10) || 0) };
  return { name: "library", category: p[1] === "cat" ? p.slice(2).join("/") : "" };
}

async function render() {
  const r = route();
  $$(".nav > a").forEach((a) => a.classList.toggle("on", a.dataset.nav === (r.name === "item" ? "library" : r.name)));
  if (!STATE) await refreshState();
  if (r.name === "library") { libFilter.category = r.category; await refreshState(); return renderLibrary(); }
  if (r.name === "item") return renderItem(r.id, r.tab);
  if (r.name === "process") return renderProcess();
  if (r.name === "settings") return renderSettings();
  if (r.name === "graph") return renderGraphPage(r.tab, r.category);
  if (r.name === "weekly") return renderWeekly(r.offset);
}
window.addEventListener("hashchange", () => {
  window.scrollTo(0, 0);
  view.classList.remove("fade-in"); void view.offsetWidth; view.classList.add("fade-in");
  render();
});

/* ---------------------------------------------------------------- 学习库 */
function depsBanner() {
  const d = STATE.deps; if (!d) return "";
  const miss = [];
  if (!d.playwright) miss.push("读取抖音的组件（playwright）：粘贴链接和同步收藏夹都用不了");
  if (!d.asr) miss.push("语音转文字的组件：没有字幕的视频转不了文字");
  if (!miss.length) return "";
  return `<div class="banner warn"><div><b>安装没有完成，缺少：</b><br>${miss.map(esc).join("<br>")}
    <div class="small" style="margin-top:6px">${d.python_ok ? "" : `你用的是 Python ${esc(d.python)}，太新了，部分组件还不支持。请先安装 Python 3.12，`}关掉这个程序，删掉程序文件夹里的 .venv 文件夹，再重新运行安装脚本，看到「安装完成」后再启动。</div></div></div>`;
}

function bannerHtml() {
  const dep = depsBanner(); if (dep) return dep;
  const s = STATE.settings;
  if (!s.api_key_set) return `<div class="banner info"><div><b>还没配置 AI。</b> 没有它只能把视频转成文字，生成不了学习笔记。
    用「免费方案」两分钟就能配好，不花钱。</div><span class="spacer"></span><a class="btn sm primary" href="#/settings">去配置 →</a></div>`;
  if (weeklyDue?.due) return `<div class="banner info"><div><b>上周的学习周报出来了。</b> 看看上周学了什么，这周从哪条开始。</div>
    <span class="spacer"></span><a class="btn sm primary" href="#/weekly/-1">看周报 →</a></div>`;
  return "";
}

async function renderLibrary(soft = false) {
  const st = STATE.stats;
  const doneN = st.by_status.done || 0;
  const pct = doneN ? Math.round((st.learned / doneN) * 100) : 0;
  const params = new URLSearchParams({ status: "done" });
  if (libFilter.q) params.set("q", libFilter.q);
  if (libFilter.learned) params.set("learned", libFilter.learned);
  if (libFilter.starred) params.set("starred", "1");
  if (libFilter.category) params.set("category", libFilter.category);
  if (!soft && !$("#libGrid")) view.innerHTML = skeletonLibrary();
  const items = await api("/api/items?" + params);
  lastItems = items;

  if (soft && $("#libGrid")) { $("#libGrid").innerHTML = gridHtml(items); updateProgress(st, doneN, pct); return; }

  view.innerHTML = `
    ${bannerHtml()}
    <div class="head">
      <div><h1>${libFilter.category ? `<i class="dot big-dot cat-${catColor(libFilter.category)}"></i>${esc(libFilter.category)}` : "学习库"}</h1>
      <div class="muted">${libFilter.category ? `<a href="#/library">← 全部分类</a>` : "收藏过的干货，在这里真正学会"}</div></div>
      <div class="spacer"></div>
      <button class="btn" id="randBtn" title="随机抽一条还没学的">${ico("shuffle")}随机学一条</button>
      <button class="btn primary" id="addBtn">${ico("plus")}添加</button>
    </div>
    <div class="card progress-card" id="progCard"></div>
    <div class="toolbar">
      <input class="search" id="q" placeholder="搜索标题、观点、文字稿、我的笔记…" value="${esc(libFilter.q)}">
      <div class="seg" id="segLearned">
        <button data-v="" class="${libFilter.learned === "" && !libFilter.starred ? "on" : ""}">全部</button>
        <button data-v="0" class="${libFilter.learned === "0" ? "on" : ""}">待学</button>
        <button data-v="1" class="${libFilter.learned === "1" ? "on" : ""}">已学</button>
        <button data-v="star" class="${libFilter.starred ? "on" : ""}">${ico("star", "ic sm")}星标</button>
      </div>
      <button class="btn" id="pdfAll" title="把当前列表里的笔记合并导出成一个 PDF">导出 PDF</button>
    </div>
    <div class="grid" id="libGrid">${gridHtml(items)}</div>`;
  updateProgress(st, doneN, pct);

  let t; $("#q").addEventListener("input", (e) => { clearTimeout(t); t = setTimeout(() => { libFilter.q = e.target.value.trim(); renderLibrary(true); }, 250); });
  $$("#segLearned button").forEach((b) => b.onclick = () => {
    const v = b.dataset.v; libFilter.starred = v === "star" ? "1" : ""; libFilter.learned = v === "star" ? "" : v;
    $$("#segLearned button").forEach((x) => x.classList.toggle("on", x === b)); renderLibrary(true);
  });
  $("#addBtn").onclick = openAdd;
  $("#pdfAll").onclick = () => {
    if (!lastItems.length) return toast("当前列表是空的");
    window.open(`/print?ids=${lastItems.map((x) => x.id).join(",")}`, "_blank");
  };
  $("#randBtn").onclick = async () => {
    const todo = await api("/api/items?status=done&learned=0");
    if (!todo.length) return toast("全部学完啦 🎉");
    location.hash = "#/item/" + todo[Math.floor(Math.random() * todo.length)].id;
  };
}

function updateProgress(st, doneN, pct) {
  const el = $("#progCard"); if (!el) return;
  const pending = ACTIVE.reduce((n, k) => n + (st.by_status[k] || 0), 0);
  el.innerHTML = `
    <div class="big">${st.learned}<span class="muted" style="font-size:18px"> / ${doneN}</span></div>
    <div><div class="row small"><b>学习进度 ${pct}%</b><span class="spacer"></span>
      <span class="muted">${pending ? `还有 ${pending} 条在处理 · ` : ""}${st.starred ? `${ico("starFill", "ic sm star-ic")} ${st.starred} · ` : ""}共收录 ${doneN} 条笔记</span></div>
      <div class="bar" style="margin-top:8px"><i style="width:${pct}%"></i></div></div>`;
}

function gridHtml(items) {
  if (!items.length) {
    const any = STATE.stats.total;
    if (libFilter.q || libFilter.learned || libFilter.starred)
      return emptyHtml("search", "没有符合条件的笔记", "换个关键词，或者切回「全部」看看。");
    if (any) return emptyHtml("inbox", "笔记还在路上", "视频处理完会自动出现在这里。", `<a class="btn" href="#/process">查看处理进度</a>`);
    return emptyHtml("book", "学习库还是空的", "把抖音收藏里的干货搬进来，这里会变成你的知识库。",
      `<a class="btn primary" href="#/process">${ico("plus")}同步收藏夹</a><button class="btn" onclick="openAdd()">粘贴分享链接</button>`);
  }
  return items.map((it, i) => `
    <a class="vcard" href="#/item/${it.id}" style="--i:${Math.min(i, 14)}">
      <div class="cover">${it.cover ? `<img src="${esc(it.cover)}" referrerpolicy="no-referrer" loading="lazy" onerror="this.remove()">` : ""}
        <div class="ph cat-${catColor(it.category)}" ${it.cover ? 'style="z-index:-1"' : ""}>${ico(it.media_type === "note" ? "file" : "play", "ic ph-ic")}</div>
        ${it.learned ? `<span class="learned-tag">${ico("check", "ic sm")}已学</span>` : ""}
        ${it.duration ? `<span class="dur">${fmtDur(it.duration)}</span>` : ""}</div>
      <div class="body">
        <div class="t">${it.starred ? ico("starFill", "ic star-ic") : ""}${esc(it.note_title || it.title)}</div>
        <div class="s">${esc(it.summary)}</div>
        <div class="foot">${catChip(it.category)}
          ${it.difficulty ? `<span class="chip gray">${esc(it.difficulty)}</span>` : ""}
          ${it.media_type === "note" ? `<span class="chip gray">图文</span>` : ""}
          ${it.has_deep ? `<span class="chip teal">${ico("cap", "ic sm")}已精读</span>` : ""}
          <span class="spacer"></span><span>${esc(it.author || "")}</span></div>
      </div></a>`).join("");
}

/* ---------------------------------------------------------------- 笔记详情 */
function noteBody(it) {
  const n = it.note || {};
  const sec = (title, html) => (html ? `<section><h2>${title}</h2>${html}</section>` : "");
  return `
    ${sec("一句话总结", n.summary ? `<div class="summary">${esc(n.summary)}</div>` : "")}
    ${sec("核心观点", n.points?.length ? `<ol class="points">${n.points.map((p) => `<li>${esc(p)}</li>`).join("")}</ol>` : "")}
    ${sec("照着做", n.steps?.length ? `<ol class="steps">${n.steps.map((p) => `<li><div>${esc(p)}</div></li>`).join("")}</ol>` : "")}
    ${sec("提到的工具", n.tools?.length ? `<div class="kv">${n.tools.map((t) => `<div><b>${esc(t.name)}</b><span>${esc(t.use)}</span></div>`).join("")}</div>` : "")}
    ${sec("关键概念", n.concepts?.length ? `<div class="kv">${n.concepts.map((t) => `<div><b>${esc(t.term)}</b><span>${esc(t.explain)}</span></div>`).join("")}</div>` : "")}
    ${sec("自测一下", n.quiz?.length ? `<div class="quiz">${n.quiz.map((q, i) => `<div class="q"><b>${i + 1}. ${esc(q.q)}</b>
        <div class="row" style="margin-top:6px"><button class="btn sm" data-reveal>看答案</button></div><div class="a">${ico("check", "ic sm")} ${esc(q.a)}</div></div>`).join("")}</div>` : "")}`;
}

let itemTab = "note";
let curItem = null;
let quizState = {};

const fmtEta = (s) => {
  s = Math.max(0, Math.round(s || 0));
  if (s < 10) return "马上就好";
  if (s < 60) return `约 ${s} 秒`;
  const m = Math.floor(s / 60), r = s % 60;
  if (m < 60) return `约 ${m} 分${r >= 30 && m < 10 ? "半" : ""}钟`;
  return `约 ${Math.floor(m / 60)} 小时 ${m % 60} 分`;
};
const fmtTs = (sec) => { sec = Math.round(sec || 0); const h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60), s = sec % 60;
  return (h ? h + ":" + String(m).padStart(2, "0") : String(m).padStart(2, "0")) + ":" + String(s).padStart(2, "0"); };
const mdLite = (t) => esc(t).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\n/g, "<br>");

async function copyText(text, msg = "已复制") {
  try { await navigator.clipboard.writeText(text); }
  catch { const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove(); }
  toast(msg);
}

function deepBusy(id) {
  const d = STATE?.deep || {};
  return d.item_id === id || (d.pending || []).includes(id);
}

async function renderItem(id, tab) {
  let it;
  if (curItem?.id !== id) view.innerHTML = skeletonItem();
  try { it = await api(`/api/items/${id}`); } catch (e) { view.innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  if (tab) itemTab = tab;
  if (curItem?.id !== id && !tab) { itemTab = "note"; quizState = {}; }
  if (it.source === "paste" && itemTab === "note" && !tab && curItem?.id !== id) itemTab = "deep";
  curItem = it;
  const n = it.note || {};
  const cats = [...new Set([...(STATE.settings.categories || []), ...(STATE.stats.categories || []).map((c) => c.category)].filter(Boolean))];
  const [stText, stCls] = STATUS[it.status] || [it.status, "gray"];
  const isNote = it.media_type === "note";
  const tabs = [["note", "笔记"], ["deep", "带我精读" + (it.deep ? " ✓" : "")], ["text", isNote ? "原图与文字" : "文字稿"]];
  view.innerHTML = `
    <a class="back" href="javascript:history.length>1?history.back():location.hash='#/library'">← 返回</a>
    <div class="detail">
      <article class="note">
        <h1>${esc(n.title || (it.deep || {}).title || it.title || "未命名")}</h1>
        <div class="meta">
          ${it.status !== "done" ? `<span class="chip ${stCls}">${stText}</span>` : ""}
          ${catChip(n.category || "未分类")}
          ${n.difficulty ? `<span class="chip gray">${esc(n.difficulty)}</span>` : ""}
          ${(n.tags || []).map((t) => `<span class="muted">#${esc(t)}</span>`).join(" ")}
        </div>
        ${it.title && it.title !== n.title && it.source !== "paste" ? `<div class="muted small orig-title" style="margin-top:-8px" title="点击展开 / 收起">原标题：${esc(it.title)}</div>` : ""}
        ${it.reason ? `<div class="banner warn" style="margin-top:14px">${esc(it.reason)}</div>` : ""}
        <div class="tabs itabs" id="itabs">${tabs.map(([k, l]) => `<button data-t="${k}" class="${itemTab === k ? "on" : ""}">${l}</button>`).join("")}</div>
        <div id="tabBody"></div>
      </article>
      <aside class="aside">
        ${it.source === "paste" ? "" : `<div class="cover-lg">${it.cover ? `<img src="${esc(it.cover)}" referrerpolicy="no-referrer" onerror="this.remove()">` : ""}</div>`}
        <div class="small muted">${esc(it.author || "")}${it.duration ? " · " + fmtDur(it.duration) : ""}${it.source === "paste" ? "粘贴的文稿" : ""}</div>
        <div class="actions">
          ${it.status === "done" ? `<button class="btn ${it.learned ? "" : "accent"} full" id="learnBtn">${it.learned ? ico("check") + "已学会（点击取消）" : "标记为已学会"}</button>` : ""}
          ${it.url ? `<a class="btn" href="${esc(it.url)}" target="_blank" rel="noopener" style="text-align:center">${isNote ? ico("external") + "原图文" : ico("play") + "原视频"}</a>` : ""}
          <button class="btn" id="starBtn">${it.starred ? ico("starFill", "ic star-ic") + "已星标" : ico("star") + "星标"}</button>
          <button class="btn" id="pdfBtn">${ico("file")}导出 PDF</button>
          <a class="btn" href="/api/items/${it.id}/md" style="text-align:center">${ico("download")}下载 MD</a>
          ${it.md_path ? `<button class="btn full" id="revealBtn">${ico("folder")}在文件夹中显示笔记</button>` : ""}
          ${it.status === "irrelevant" ? `<button class="btn accent full" id="includeBtn">我觉得有用，收进学习库</button>` : ""}
          ${["failed", "skipped", "need_key", "irrelevant", "done"].includes(it.status) && it.transcript && it.source !== "paste"
            ? `<button class="btn full" id="reBtn">${ico("sparkles")}重新 AI 提炼</button>` : ""}
          ${it.status === "failed" && !it.transcript ? `<button class="btn full" id="retryBtn">重试</button>` : ""}
        </div>
        ${it.status === "done" ? `<div class="field"><label>分类</label><select id="catSel">${cats.map((c) => `<option ${c === n.category ? "selected" : ""}>${esc(c)}</option>`).join("")}${cats.includes(n.category) || !n.category ? "" : `<option selected>${esc(n.category)}</option>`}</select></div>` : ""}
        <div class="mynote"><div class="row"><b>我的笔记</b><span class="spacer"></span><span class="saved" id="saved"></span></div>
          <textarea id="myNote" placeholder="写下自己的理解、实践结果、想法……（自动保存，也会写进 MD 笔记）">${esc(it.my_note)}</textarea></div>
        <button class="btn ghost small" id="delBtn" style="color:var(--bad)">删除这条</button>
      </aside>
    </div>`;

  $$("#itabs button").forEach((b) => b.onclick = () => { itemTab = b.dataset.t; $$("#itabs button").forEach((x) => x.classList.toggle("on", x === b)); renderTab(); });
  renderTab();

  const act = (action, extra = {}) => api(`/api/items/${id}/action`, { action, ...extra });
  $("#learnBtn") && ($("#learnBtn").onclick = async () => { await act("learned", { value: !it.learned }); toast(it.learned ? "已取消" : "太棒了，又学会一条 🎉"); refreshState(); renderItem(id, itemTab); });
  $("#starBtn").onclick = async () => { await act("star", { value: !it.starred }); renderItem(id, itemTab); };
  $("#pdfBtn").onclick = () => window.open(`/print?ids=${id}`, "_blank");
  $("#revealBtn") && ($("#revealBtn").onclick = () => api("/api/open", { what: "item", id }).catch((e) => toast(e.message)));
  $("#includeBtn") && ($("#includeBtn").onclick = async () => { await act("include"); toast("已收进学习库"); refreshState(); renderItem(id, itemTab); });
  $("#reBtn") && ($("#reBtn").onclick = async () => { await act("reextract"); toast("已加入队列，稍等片刻"); location.hash = "#/process"; });
  $("#retryBtn") && ($("#retryBtn").onclick = async () => { await act("retry"); toast("已重新加入队列"); location.hash = "#/process"; });
  $("#catSel") && ($("#catSel").onchange = async (e) => { await act("category", { value: e.target.value }); toast("分类已修改"); refreshState(); });
  $("#delBtn").onclick = async () => {
    if (!confirm("确定删除这条？对应的 MD 笔记文件也会删除。")) return;
    await act("delete"); toast("已删除"); location.hash = "#/library";
  };
  let t; $("#myNote").addEventListener("input", (e) => {
    $("#saved").textContent = "编辑中…"; clearTimeout(t);
    t = setTimeout(async () => { await act("note", { text: e.target.value }); $("#saved").textContent = "已保存"; }, 800);
  });
}

function renderTab() {
  const it = curItem, el = $("#tabBody");
  if (!el) return;
  el.classList.remove("fade-in"); void el.offsetWidth; el.classList.add("fade-in");
  if (itemTab === "note") {
    el.innerHTML = (it.images?.length ? galleryHtml(it.images) : "") +
      (it.note ? noteBody(it) : `<div class="empty" style="padding:30px">这条还没有笔记。${it.transcript ? "可以直接去「带我精读」。" : ""}</div>`);
    bindGallery(el, it.images);
    $$("[data-reveal]", el).forEach((b) => b.onclick = () => { b.closest(".q").classList.add("open"); b.remove(); });
  } else if (itemTab === "text") {
    renderTextTab(el);
  } else {
    renderDeepTab(el);
  }
}

function renderTextTab(el, focusSec) {
  const it = curItem;
  if (!it.transcript) { el.innerHTML = `<div class="empty" style="padding:30px">还没有文字稿</div>`; return; }
  const segs = it.segments || [];
  if (it.images?.length) {
    const parts = {}; let intro = "";
    it.transcript.split(/\n\n(?=【)/).forEach((blk) => {
      const m = blk.match(/^【图(\d+)】\n?([\s\S]*)$/);
      if (m) parts[+m[1]] = m[2]; else intro += blk.replace(/^【正文】\n?/, "") + "\n";
    });
    el.innerHTML = `<div class="row" style="margin:14px 0 10px"><span class="muted small">图文 · ${it.images.length} 张图 · 图片里的文字由本机识别，可能有错字</span>
        <span class="spacer"></span><button class="btn sm" id="cpTr">复制全部文字</button></div>
      ${intro.trim() ? `<div class="summary" style="margin-bottom:14px;white-space:pre-wrap">${esc(intro.trim())}</div>` : ""}
      <div class="ocr-list">${it.images.map((src, i) => `<div class="ocr-row">
        <img src="/files/${encodeURI(src)}" data-g="${i}" loading="lazy">
        <div class="ocr-text"><div class="muted small">图 ${i + 1}</div>${parts[i + 1] ? esc(parts[i + 1]) : '<span class="muted">（这张图没有识别到文字）</span>'}</div></div>`).join("")}</div>`;
    $("#cpTr").onclick = () => copyText(it.transcript, "文字已复制");
    bindGallery(el, it.images);
    return;
  }
  el.innerHTML = `<div class="row" style="margin:14px 0 10px"><span class="muted small">${it.transcript.length} 字${segs.length ? " · 在精读大纲里点时间，会跳到这里对应的位置" : ""}</span>
      <span class="spacer"></span><button class="btn sm" id="cpTr">复制全文</button></div>
    ${segs.length ? `<div class="tsegs">${segs.map((s, i) => `<div class="tseg" id="seg-${i}" data-start="${s.start}"><span class="ts">${fmtTs(s.start)}</span><span>${esc(s.text)}</span></div>`).join("")}</div>`
      : `<div class="transcript" style="max-height:none">${esc(it.transcript)}</div>`}`;
  $("#cpTr").onclick = () => copyText(it.transcript, "文字稿已复制");
  if (focusSec != null && segs.length) {
    let idx = 0;
    segs.forEach((s, i) => { if (s.start <= focusSec + 0.5) idx = i; });
    const row = $(`#seg-${idx}`);
    if (row) { row.classList.add("hl"); row.scrollIntoView({ block: "center", behavior: "smooth" }); setTimeout(() => row.classList.remove("hl"), 2500); }
  }
}

function deepModelName() {
  const s = STATE.settings;
  return s.deep_same ? s.model : s.deep_model;
}

function renderDeepTab(el) {
  const it = curItem, d = it.deep, chat = it.chat || {};
  const busy = deepBusy(it.id);
  if (busy) {
    const ds = STATE.deep || {};
    const mine = ds.item_id === it.id;
    el.innerHTML = `<div class="card deep-run" id="deepRun" style="margin-top:16px">
        <div class="row"><div class="spinner"></div><b>${mine ? esc(ds.label || "精读中") : "排队等待精读……"}</b><span class="spacer"></span>
        <span class="muted small">${mine ? `第 ${ds.step}/${ds.steps} 步 · ${fmtEta(ds.eta)}` : ""}</span></div>
        <div class="bar" style="margin-top:10px"><i style="width:${mine ? ds.pct : 2}%"></i></div>
        <div class="muted small" style="margin-top:8px">用 ${esc(deepModelName())} 生成核心结论、章节大纲、概念、理解检查题、测验、Anki 卡片和思维导图。可以先去看别的，好了会自动显示。</div></div>`;
    return;
  }
  if (!d) {
    el.innerHTML = `
      ${chat.deep_error ? `<div class="banner warn" style="margin-top:14px">上次精读失败：${esc(chat.deep_error)}</div>` : ""}
      <div class="card" style="margin-top:16px">
        <h2>有人带着读</h2>
        <p class="muted">让 AI 像老师一样带你读这段内容：先给 5 句核心结论，再按章节列大纲（带时间戳，点击跳到原文），解释关键概念；
          然后不直接给答案，用提问检查你是否真懂（你写回答，AI 点评）；最后出 10 道测验题，做成 Anki 卡片，画思维导图。</p>
        <p class="muted small">使用模型：<b>${esc(deepModelName() || "未设置")}</b>（在设置 → 精读 里可以换成 Claude 等）。文稿很长时会自动分段预读再合并。</p>
        <div class="row" style="margin-top:12px">
          <button class="btn primary" id="deepGo" ${it.transcript ? "" : "disabled"}>开始精读</button>
          <button class="btn" id="copyPrompt" ${it.transcript ? "" : "disabled"}>${ico("copy")}复制提示词+文稿（粘贴到豆包 / Kimi / 千问 / Claude）</button>
        </div>
        ${it.transcript ? "" : `<div class="muted small" style="margin-top:8px">这条还没有文字稿，处理完才能精读。</div>`}
      </div>`;
    $("#deepGo") && ($("#deepGo").onclick = startDeep);
    $("#copyPrompt") && ($("#copyPrompt").onclick = copyPrompt);
    return;
  }

  const checks = chat.checks || {};
  const qs = quizState[it.id] || (quizState[it.id] = {});
  el.innerHTML = `
    ${chat.deep_error ? `<div class="banner warn" style="margin-top:14px">上次重新精读失败：${esc(chat.deep_error)}（下面是之前的结果）</div>` : ""}
    <div class="row deep-head"><span class="muted small">由 ${esc(d.model || "")} 生成${d.chunks > 1 ? ` · 分 ${d.chunks} 段预读后合并` : ""}</span><span class="spacer"></span>
      <button class="btn sm" id="copyPrompt">${ico("copy")}复制给其他 AI</button><button class="btn sm ghost" id="deepRedo">重新精读</button></div>

    ${d.conclusions.length ? `<section><h2>核心结论</h2><ol class="points">${d.conclusions.map((c) => `<li>${esc(c)}</li>`).join("")}</ol></section>` : ""}

    ${d.mindmap ? `<section><h2>思维导图</h2>
      <div class="row" style="margin-bottom:10px"><a class="btn sm" href="/api/items/${it.id}/mindmap.html" target="_blank">${ico("external")}新窗口全屏</a>
        <a class="btn sm" href="/api/items/${it.id}/mindmap.html?download=1">${ico("download")}下载网页</a>
        <button class="btn sm" id="cpMind">${ico("copy")}复制 Markmap 文本</button></div>
      <iframe class="mindmap" src="/api/items/${it.id}/mindmap.html"></iframe></section>` : ""}

    ${d.outline.length ? `<section><h2>章节大纲</h2><div class="outline">${d.outline.map((o) => `
      <div class="ol-item"><div class="ol-head">${o.time ? `<button class="ts-btn" data-sec="${o.sec ?? ""}" title="跳到文字稿这里">${esc(o.time)}</button>` : ""}<b>${esc(o.title)}</b></div>
      ${o.points.length ? `<ul>${o.points.map((p) => `<li>${esc(p)}</li>`).join("")}</ul>` : ""}</div>`).join("")}</div></section>` : ""}

    ${d.concepts.length ? `<section><h2>关键概念与术语</h2><div class="kv">${d.concepts.map((c) => `<div><b>${esc(c.term)}</b><span>${esc(c.explain)}</span></div>`).join("")}</div></section>` : ""}

    ${d.check_questions.length ? `<section><h2>你真的懂了吗？</h2>
      <p class="muted small" style="margin-top:-4px">不直接给答案。用自己的话回答，老师会点评并继续追问。</p>
      ${d.check_questions.map((q, i) => { const c = checks[i]; return `
        <div class="cq card" data-i="${i}">
          <div><b>${i + 1}. ${esc(q.q)}</b></div>
          <div class="row" style="margin:8px 0"><button class="btn sm ghost" data-hint>${ico("bulb")}给点提示</button>${c ? `<button class="btn sm ghost" data-key>${ico("eye")}看参考要点</button>` : ""}</div>
          <div class="hint-box" hidden>${ico("bulb")}${esc(q.hint)}</div>
          <div class="key-box" hidden>${ico("eye")}${esc(q.key)}</div>
          <textarea rows="3" placeholder="用自己的话写下你的理解……">${esc(c?.answer || "")}</textarea>
          <div class="row" style="margin-top:8px"><span class="spacer"></span><button class="btn sm" data-submit>${c ? "再答一次" : "提交给老师"}</button></div>
          <div class="feedback" ${c ? "" : "hidden"}>${c ? mdLite(c.feedback) : ""}</div>
        </div>`; }).join("")}</section>` : ""}

    ${d.quiz.length ? `<section><h2>测验（${d.quiz.length} 题）</h2><div id="quizBox"></div></section>` : ""}

    ${d.anki.length ? `<section><h2>Anki 卡片（${d.anki.length} 张）</h2>
      <div class="row" style="margin-bottom:10px"><a class="btn sm" href="/api/items/${it.id}/anki.txt">${ico("download")}下载 .txt</a>
        <button class="btn sm" id="cpAnki">${ico("copy")}复制「问题⇥答案」</button>
        <span class="muted small">Anki 里选「文件 → 导入」，分隔符选 Tab</span></div>
      <table class="anki"><thead><tr><th>问题</th><th>答案</th></tr></thead><tbody>
        ${d.anki.map((c) => `<tr><td>${esc(c.q)}</td><td>${esc(c.a)}</td></tr>`).join("")}</tbody></table></section>` : ""}



    <section><h2>问老师</h2>
      <div class="asklog" id="askLog">${(chat.ask || []).map((a) => `<div class="qa"><div class="q-me">${esc(a.q)}</div><div class="a-ai">${mdLite(a.a)}</div></div>`).join("")}</div>
      <div class="row ask-row"><input id="askIn" class="search" placeholder="哪里没看懂？随便问，比如「第二章那个方法具体怎么做？」"><button class="btn primary" id="askBtn">提问</button></div>
    </section>`;

  $("#copyPrompt").onclick = copyPrompt;
  $("#deepRedo").onclick = () => { if (confirm("重新精读会覆盖现在的结果（答题记录保留），确定？")) startDeep(); };
  $$(".ts-btn", el).forEach((b) => b.onclick = () => {
    const sec = b.dataset.sec === "" ? null : +b.dataset.sec;
    if (!(it.segments || []).length) return toast("这条文字稿没有时间信息");
    itemTab = "text"; $$("#itabs button").forEach((x) => x.classList.toggle("on", x.dataset.t === "text"));
    renderTextTab($("#tabBody"), sec);
  });
  $$(".cq", el).forEach((card) => {
    const i = +card.dataset.i;
    $("[data-hint]", card).onclick = () => { $(".hint-box", card).hidden = false; };
    // 只有写了回答，「提交」才变成主按钮：一页里不会同时有六个蓝按钮
    const ta = $("textarea", card), sb = $("[data-submit]", card);
    const syncBtn = () => sb.classList.toggle("primary", !!ta.value.trim() && !curItem.chat?.checks?.[i]);
    ta.addEventListener("input", syncBtn); syncBtn();
    $("[data-key]", card) && ($("[data-key]", card).onclick = () => { $(".key-box", card).hidden = false; });
    $("[data-submit]", card).onclick = async (e) => {
      const ans = $("textarea", card).value.trim();
      if (!ans) return toast("先写下你的回答");
      const btn = e.target; btn.disabled = true; btn.textContent = "老师在看……";
      const fb = $(".feedback", card); fb.hidden = false; fb.innerHTML = `<span class="muted">思考中……</span>`;
      try {
        const r = await api(`/api/items/${it.id}/check`, { idx: i, answer: ans });
        fb.innerHTML = mdLite(r.feedback);
        (curItem.chat ||= {}).checks ||= {}; curItem.chat.checks[i] = r;
        if (!$("[data-key]", card)) $("[data-hint]", card).insertAdjacentHTML("afterend", `<button class="btn sm ghost" data-key>${ico("eye")}看参考要点</button>`);
        $("[data-key]", card).onclick = () => { $(".key-box", card).hidden = false; };
      } catch (err) { fb.innerHTML = `<span style="color:var(--bad)">${esc(err.message)}</span>`; }
      btn.disabled = false; btn.textContent = "再答一次";
    };
  });
  if (d.quiz.length) renderQuiz(it, d.quiz, qs);
  $("#cpAnki") && ($("#cpAnki").onclick = () => copyText(d.anki.map((c) => `${c.q}\t${c.a}`).join("\n"), "Anki 卡片已复制"));
  $("#cpMind") && ($("#cpMind").onclick = () => copyText(d.mindmap, "Markmap 文本已复制"));
  const ask = async () => {
    const q = $("#askIn").value.trim(); if (!q) return;
    const log = $("#askLog"); $("#askIn").value = "";
    log.insertAdjacentHTML("beforeend", `<div class="qa"><div class="q-me">${esc(q)}</div><div class="a-ai muted" id="pendingA">老师在想……</div></div>`);
    $("#askBtn").disabled = true;
    try { const r = await api(`/api/items/${it.id}/ask`, { q }); $("#pendingA").outerHTML = `<div class="a-ai">${mdLite(r.a)}</div>`;
      ((curItem.chat ||= {}).ask ||= []).push(r);
    } catch (e) { $("#pendingA").outerHTML = `<div class="a-ai" style="color:var(--bad)">${esc(e.message)}</div>`; }
    $("#askBtn").disabled = false;
  };
  $("#askBtn").onclick = ask;
  $("#askIn").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.isComposing) ask(); });
}

function renderQuiz(it, quiz, qs) {
  const box = $("#quizBox"); if (!box) return;
  const answered = Object.keys(qs).length;
  const score = Object.entries(qs).filter(([i, a]) => quiz[i] && a === quiz[i].answer).length;
  box.innerHTML = quiz.map((q, i) => {
    const pick = qs[i];
    return `<div class="quiz-q card" data-i="${i}"><b>${i + 1}. ${esc(q.q)}</b>
      <div class="opts">${q.options.map((o, j) => {
        let cls = "";
        if (pick !== undefined) cls = j === q.answer ? "right" : (j === pick ? "wrong" : "dim");
        return `<button class="opt ${cls}" data-j="${j}" ${pick !== undefined ? "disabled" : ""}>${"ABCDEFGH"[j]}. ${esc(o)}</button>`; }).join("")}</div>
      ${pick !== undefined ? `<div class="explain">${pick === q.answer ? `<span class="ok-t">${ico("checkCircle")}答对了</span>` : `<span class="bad-t">${ico("xCircle")}正确答案是</span> ${"ABCDEFGH"[q.answer]}`}${q.explain ? "　" + esc(q.explain) : ""}</div>` : ""}</div>`;
  }).join("") + `<div class="row quiz-score"><b>${answered === quiz.length ? `${ico("trophy")} 完成！得分 ${score} / ${quiz.length}` : `已答 ${answered} / ${quiz.length}，答对 ${score} 题`}</b>
      <span class="spacer"></span>${answered ? `<button class="btn sm" id="quizReset">重做</button>` : ""}</div>`;
  $$(".opt", box).forEach((b) => b.onclick = () => {
    const i = +b.closest(".quiz-q").dataset.i; qs[i] = +b.dataset.j;
    const y = window.scrollY; renderQuiz(it, quiz, qs); window.scrollTo(0, y);
    if (Object.keys(qs).length === quiz.length) {
      const sc = Object.entries(qs).filter(([k, a]) => a === quiz[k].answer).length;
      api(`/api/items/${it.id}/quiz`, { score: sc, total: quiz.length }).catch(() => {});
    }
  });
  $("#quizReset") && ($("#quizReset").onclick = () => { for (const k in qs) delete qs[k]; renderQuiz(it, quiz, qs); });
}

async function startDeep() {
  const it = curItem;
  try {
    const r = await api(`/api/items/${it.id}/deep`, {});
    wasDeepBusy = true;
    toast(`开始精读（${r.model || ""}），长文稿需要几分钟`);
    await refreshState(); itemTab = "deep"; renderTab();
  } catch (e) { toast(e.message, 4000); }
}

async function copyPrompt() {
  try { const r = await api(`/api/items/${curItem.id}/prompt`); copyText(r.text, "提示词和文稿已复制，可以粘贴到任意 AI 对话里"); }
  catch (e) { toast(e.message); }
}

/* ---------------------------------------------------------------- 添加与处理 */
function openAdd() { $("#addModal").hidden = false; setTimeout(() => $("#addText").focus(), 30); }
$$("#addModal [data-close]").forEach((b) => b.addEventListener("click", () => ($("#addModal").hidden = true)));
$("#addModal").addEventListener("click", (e) => { if (e.target.id === "addModal") e.target.hidden = true; });
// 原标题点一下展开 / 收起
document.addEventListener("click", (e) => { const o = e.target.closest(".orig-title"); if (o) o.classList.toggle("open"); });
$("#addSubmit").onclick = async () => {
  const text = $("#addText").value;
  try {
    const r = await api("/api/links", { text });
    $("#addText").value = ""; $("#addModal").hidden = true;
    toast(r.added ? `找到 ${r.found} 个链接，新增 ${r.added} 条，开始处理` : `找到 ${r.found} 个链接，都已经添加过了`);
    location.hash = "#/process";
  } catch (e) { toast(e.message, 4000); }
};

async function renderProcess() {
  await refreshState();
  const s = STATE.settings;
  view.innerHTML = `
    <div class="head"><div><h1>添加与处理</h1><div class="muted">视频：读取信息 → 下载 → 本地转文字 → AI 提炼；图文：下载图片 → 识别图片文字 → AI 提炼</div></div></div>
    ${bannerHtml()}
    <div class="card sync-card">
      <div class="sync-intro">
        <h2>同步抖音收藏夹</h2>
        <p class="muted small">会弹出浏览器窗口，第一次需要用抖音 App 扫码登录（只登录一次）。读取时会自动慢慢滚动，请不要关闭那个窗口。之前失败的视频会自动重新排队。</p>
      </div>
      <div class="sync-form">
        <div class="field"><label>读取哪个列表</label><select id="sKind"><option value="collection">我的收藏</option><option value="like">我的喜欢</option></select></div>
        <div class="field"><label>最多读取几条（从最新开始）</label><input id="sLimit" type="number" min="1" max="2000" value="${s.sync_limit || 50}"></div>
        <div class="row sync-btns"><button class="btn" id="loginBtn">只登录抖音</button><button class="btn primary" id="syncBtn">开始同步</button></div>
      </div>
    </div>
    <div class="panels">
      <div class="card col-card">
        <h2>粘贴分享链接</h2>
        <p class="muted small">抖音里点「分享 → 复制链接」，视频和图文都可以，一次能贴很多条。</p>
        <textarea id="pText" rows="5" placeholder="粘贴一条或多条抖音分享内容……"></textarea>
        <div class="row" style="margin-top:12px"><span class="spacer"></span><button class="btn primary" id="pAdd">添加并处理</button></div>
      </div>
      <div class="card col-card">
        <h2>导入本地视频</h2>
        <p class="muted small">链接解析不了时的备用办法：把视频文件（mp4 / mov / mp3 等）放进「收件箱」文件夹，再点扫描。原文件不会被删除。</p>
        <div class="inbox-box"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13h5l1.5 3h5L16 13h5"/><path d="M5.5 5h13L21 13v6H3v-6z"/></svg>
          <span class="muted small">收件箱文件夹</span></div>
        <div class="row" style="margin-top:12px"><span class="spacer"></span><button class="btn" id="inboxOpen">打开收件箱文件夹</button><button class="btn" id="inboxScan">扫描并处理</button></div>
      </div>
    </div>
    <div class="card status-card" id="statusCard" style="margin-bottom:20px"></div>
    <div class="card">
      <div class="tabs" id="tabs"></div>
      <div class="qlist" id="qlist"></div>
    </div>
    <div class="row" style="margin-top:22px;margin-bottom:12px"><h2 style="margin:0">运行日志</h2><span class="spacer"></span>
      <button class="btn sm" id="copyLogs">${ico("copy")}一键复制日志</button></div>
    <div class="logs" id="logs"></div>`;

  $("#pAdd").onclick = async () => {
    try { const r = await api("/api/links", { text: $("#pText").value }); $("#pText").value = "";
      toast(r.added ? `新增 ${r.added} 条，开始处理` : "这些链接都已经添加过了"); renderProcessLive(); } catch (e) { toast(e.message, 4000); }
  };
  $("#syncBtn").onclick = async () => {
    await api("/api/sync", { kind: $("#sKind").value, limit: +$("#sLimit").value || 50 });
    toast("开始同步，请留意弹出的浏览器窗口"); renderProcessLive();
  };
  $("#loginBtn").onclick = async () => { await api("/api/login", {}); toast("请在弹出的浏览器窗口里扫码登录"); };
  $("#copyLogs").onclick = async () => {
    const text = (STATE.logs || []).map((l) => `${fmtTime(l.t)} ${l.msg}`).join("\n");
    if (!text) return toast("还没有日志");
    try { await navigator.clipboard.writeText(text); }
    catch {
      const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta);
      ta.select(); document.execCommand("copy"); ta.remove();
    }
    toast(`已复制 ${STATE.logs.length} 行日志，可以直接粘贴发给我`);
  };
  $(".inbox-box").onclick = () => api("/api/open", { what: "inbox" }).catch((e) => toast(e.message));
  $("#inboxOpen").onclick =() => api("/api/open", { what: "inbox" }).catch((e) => toast(e.message));
  $("#inboxScan").onclick = async () => { const r = await api("/api/inbox", {}); toast(r.added ? `新增 ${r.added} 个文件，开始处理` : "收件箱里没有新文件"); renderProcessLive(); };
  renderProcessLive();
}

const TABS = [
  ["active", "处理中", ACTIVE], ["failed", "失败", ["failed"]], ["need_key", "待提炼", ["need_key"]],
  ["irrelevant", "主题无关", ["irrelevant"]], ["skipped", "已跳过", ["skipped"]], ["done", "已完成", ["done"]],
];

async function renderProcessLive() {
  if (!$("#statusCard")) return;
  const w = STATE.worker, st = STATE.stats.by_status;
  const pg = STATE.progress || {};
  $("#statusCard").innerHTML = w.busy
    ? (pg.item_id ? `<div class="pcard">
        <div class="row"><div class="spinner"></div><b class="ptitle">${esc(pg.title || "处理中")}</b><span class="spacer"></span><button class="btn sm" id="stopBtn">停止</button></div>
        <div class="stepper">${["fetching", "downloading", "transcribing", "extracting"].map((k) => {
            const lbl = (pg.is_note ? { fetching: "读取图文", downloading: "下载图片", transcribing: "识别图片文字", extracting: "AI 提炼" }
              : { fetching: "读取信息", downloading: "下载", transcribing: "转文字", extracting: "AI 提炼" })[k];
            const order = ["fetching", "downloading", "transcribing", "extracting"];
            const cls = k === pg.stage ? "now" : (order.indexOf(k) < order.indexOf(pg.stage) ? "done" : "");
            return `<span class="step ${cls}">${cls === "done" ? "✓ " : ""}${lbl}${k === pg.stage ? ` ${pg.stage_pct}%` : ""}</span>`; }).join('<span class="arrow">›</span>')}</div>
        <div class="bar big-bar"><i style="width:${pg.pct}%"></i></div>
        <div class="row small"><b>${pg.pct}%</b><span class="muted">这一条预计还剩 ${fmtEta(pg.eta)}${pg.real ? "" : "（估算）"}</span><span class="spacer"></span>
          <span class="muted">${w.total ? `本批 ${w.done + 1} / ${w.total}` : ""}${pg.batch_eta > pg.eta + 5 ? ` · 全部预计还剩 ${fmtEta(pg.batch_eta)}` : ""}</span></div>
      </div>`
      : `<div class="spinner"></div><div style="flex:1"><b>${esc(w.stage || "处理中…")}</b>
        <div class="muted small">${w.total ? `本批进度 ${w.done} / ${w.total}` : ""}</div></div>
        <button class="btn" id="stopBtn">停止</button>`)
    : `<div class="idle-ic">${ico("coffee")}</div><div style="flex:1"><b>空闲中</b><div class="muted small">
        ${(st.queued || 0) ? `队列里还有 ${st.queued} 条等待处理` : "添加视频后会自动开始处理"}</div></div>
        ${(st.failed || 0) ? `<button class="btn" id="retryFailed">${ico("retry")}重试失败的 ${st.failed} 条</button>` : ""}
        ${(st.queued || 0) ? `<button class="btn primary" id="goBtn">开始处理</button>` : ""}`;
  $("#retryFailed") && ($("#retryFailed").onclick = async () => {
    const failed = await api("/api/items?status=failed");
    for (const it of failed) await api(`/api/items/${it.id}/action`, { action: "retry" });
    toast(`${failed.length} 条已重新排队，开始处理`); await refreshState(); renderProcessLive();
  });
  $("#stopBtn") && ($("#stopBtn").onclick = () => api("/api/stop", {}));
  $("#goBtn") && ($("#goBtn").onclick = async () => { await api("/api/process", {}); refreshState().then(renderProcessLive); });

  $("#tabs").innerHTML = TABS.map(([k, label, ss]) => {
    const n = ss.reduce((a, s) => a + (st[s] || 0), 0);
    return `<button data-k="${k}" class="${procTab === k ? "on" : ""}">${label} ${n ? `(${n})` : ""}</button>`;
  }).join("");
  $$("#tabs button").forEach((b) => b.onclick = () => { procTab = b.dataset.k; renderProcessLive(); });

  const ss = TABS.find((t) => t[0] === procTab)[2];
  const items = await api("/api/items?status=" + ss.join(","));
  $("#qlist").innerHTML = items.length ? items.slice(0, 300).map((it) => {
    const [label, cls] = STATUS[it.status] || [it.status, "gray"];
    let btns = "";
    if (it.status === "failed") btns = `<button class="btn sm" data-a="retry" data-id="${it.id}">重试</button>`;
    if (it.status === "need_key") btns = `<button class="btn sm" data-a="reextract" data-id="${it.id}">提炼</button>`;
    if (it.status === "irrelevant") btns = `<button class="btn sm" data-a="include" data-id="${it.id}">收进学习库</button>`;
    if (["failed", "skipped", "irrelevant", "need_key", "queued"].includes(it.status)) btns += ` <button class="btn sm ghost" data-a="delete" data-id="${it.id}">删除</button>`;
    return `<div class="qrow"><div style="min-width:0">
        <div class="t"><a href="#/item/${it.id}" style="color:inherit">${esc(it.note_title || it.title || it.url || "（解析中）")}</a></div>
        <div class="r"><span class="chip ${cls}">${label}</span> ${esc(it.reason || "")}</div></div>
        <div class="row">${btns}</div></div>`;
  }).join("") : `<div class="empty" style="padding:30px">这里是空的</div>`;
  $$("#qlist [data-a]").forEach((b) => b.onclick = async () => {
    const a = b.dataset.a;
    if (a === "delete" && !confirm("删除这条？")) return;
    await api(`/api/items/${b.dataset.id}/action`, { action: a });
    await refreshState(); renderProcessLive();
  });
  if (procTab === "need_key" && items.length > 1 && STATE.settings.api_key_set) {
    $("#qlist").insertAdjacentHTML("afterbegin", `<div class="row" style="padding:8px 4px"><span class="muted small">AI Key 已填好，可以一次全部提炼</span><span class="spacer"></span><button class="btn sm primary" id="allRe">全部提炼</button></div>`);
    $("#allRe").onclick = async () => { for (const it of items) await api(`/api/items/${it.id}/action`, { action: "reextract" }); toast("已全部加入队列"); };
  }
  if (procTab === "failed" && items.length >= 1) {
    $("#qlist").insertAdjacentHTML("afterbegin", `<div class="row" style="padding:8px 4px"><span class="spacer"></span><button class="btn sm" id="allRetry">全部重试</button></div>`);
    $("#allRetry").onclick = async () => { for (const it of items) await api(`/api/items/${it.id}/action`, { action: "retry" }); toast("已全部重新排队，开始处理"); await refreshState(); renderProcessLive(); };
  }
  const logs = $("#logs");
  const atBottom = logs.scrollTop + logs.clientHeight >= logs.scrollHeight - 20;
  logs.innerHTML = (STATE.logs || []).map((l) => `<div><span>${fmtTime(l.t)}</span>${esc(l.msg)}</div>`).join("") || `<div class="muted">暂无日志</div>`;
  if (atBottom) logs.scrollTop = logs.scrollHeight;
}

/* ---------------------------------------------------------------- 设置 */
async function renderSettings() {
  await refreshState();
  const s = STATE.settings, P = STATE.providers;
  view.innerHTML = `
    <div class="head"><div><h1>设置</h1><div class="muted">所有设置和数据都只保存在你自己的电脑上</div></div></div>
    ${freePlanHtml(s)}
    <div class="card form" style="margin-bottom:16px">
      <h2>AI 提炼</h2>
      <div class="grid2">
        <div class="field"><label>AI 服务商</label><select id="provider">${Object.entries(P).map(([k, v]) => `<option value="${k}" ${s.provider === k ? "selected" : ""}>${esc(v.name)}</option>`).join("")}</select>
          <div class="hint" id="keyLink"></div></div>
        <div class="field"><label>API Key ${s.api_key_set ? `<span class="chip teal">已保存 ${esc(s.api_key_hint)}</span>` : ""}</label>
          <input id="apiKey" type="password" placeholder="${s.api_key_set ? "留空表示不修改" : "sk-..."}" autocomplete="off">
          <div class="hint">Key 只存在本机 data/settings.json，不会上传到别处。</div></div>
        <div class="field"><label>接口地址（Base URL）</label><input id="baseUrl" value="${esc(s.base_url)}"></div>
        <div class="field"><label>模型</label><div class="model-pick"><input id="model" value="${esc(s.model)}" placeholder="选择或输入模型名" autocomplete="off">
          <select id="modelPick" title="从列表选择模型"></select></div>
          <div class="hint"><span id="mHint">点右边的箭头从列表选择；也可以直接输入。</span> <a href="javascript:void 0" id="mLoad">刷新模型列表</a></div></div>
      </div>
      <div class="row"><button class="btn" id="testBtn">测试连接</button><span class="small" id="testRes"></span>
        <span class="spacer"></span><span class="muted small">累计消耗约 ${(s.tokens_used || 0).toLocaleString()} tokens</span></div>
    </div>
    <div class="card form" style="margin-bottom:16px">
      <h2>精读（有人带着读）</h2>
      <div class="field"><label class="check"><input type="checkbox" id="deepSame" ${s.deep_same ? "checked" : ""}> 精读和上面的 AI 提炼用同一个模型</label>
        <div class="hint">日常批量提炼用便宜的模型（比如 DeepSeek），精读用更强的模型（比如 Claude）——取消勾选就能单独设置。</div></div>
      <div id="deepCfg" ${s.deep_same ? "hidden" : ""}>
        <div class="grid2">
          <div class="field"><label>精读用的服务商</label><select id="dProvider">${Object.entries(P).map(([k, v]) => `<option value="${k}" ${s.deep_provider === k ? "selected" : ""}>${esc(v.name)}</option>`).join("")}</select>
            <div class="hint" id="dKeyLink"></div></div>
          <div class="field"><label>API Key ${s.deep_api_key_set ? `<span class="chip teal">已保存 ${esc(s.deep_api_key_hint)}</span>` : ""}</label>
            <input id="dKey" type="password" placeholder="${s.deep_api_key_set ? "留空表示不修改" : "sk-ant-... / sk-..."}" autocomplete="off"></div>
          <div class="field"><label>接口地址</label><input id="dBase" value="${esc(s.deep_base_url)}"></div>
          <div class="field"><label>模型</label><div class="model-pick"><input id="dModel" value="${esc(s.deep_model)}" placeholder="选择或输入模型名" autocomplete="off">
            <select id="dModelPick" title="从列表选择模型"></select></div>
            <div class="hint"><span id="dmHint">点右边的箭头从列表选择；也可以直接输入。</span> <a href="javascript:void 0" id="dmLoad">刷新模型列表</a></div></div>
        </div>
        <div class="row" style="margin:12px 0 14px"><button class="btn" id="dTest">测试精读模型</button><span class="small" id="dTestRes"></span></div>
      </div>
      <div class="field"><label>精读提示词</label><textarea id="dPrompt" rows="4">${esc(s.deep_prompt)}</textarea>
        <div class="hint">告诉 AI 你想怎么被带着读。输出格式（结论/大纲/概念/检查题/测验/Anki/思维导图）由程序固定，这里写学习要求就行。
          <a href="javascript:void 0" id="dPromptReset">恢复默认</a></div></div>
      <div class="field" style="max-width:340px"><label>文稿超过多少字就分段预读</label><input id="dChunk" type="number" min="3000" max="100000" step="1000" value="${s.deep_chunk_chars}">
        <div class="hint">模型上下文小就调小。12000 字大约是 40 分钟的口播。</div></div>
    </div>
    <div class="card form" style="margin-bottom:16px">
      <h2>学什么</h2>
      <div class="field"><label>我关注的主题</label><textarea id="focus" rows="2">${esc(s.focus_topic)}</textarea>
        <div class="hint">AI 会按这个判断视频是否相关。想学别的（比如理财、健身）直接改这里。</div></div>
      <div class="field"><label class="check"><input type="checkbox" id="onlyRel" ${s.only_relevant ? "checked" : ""}> 和主题无关的视频自动收起（在「主题无关」里还能找回）</label></div>
      <div class="field"><label>分类（用逗号分隔，AI 会优先从这里选）</label><input id="cats" value="${esc((s.categories || []).join("，"))}"></div>
    </div>
    <div class="card form" style="margin-bottom:16px">
      <h2>语音转文字（在本机运行）</h2>
      <div class="grid2">
        <div class="field"><label>识别引擎</label><select id="engine">
          ${[["auto", "自动（苹果芯片 Mac 用加速版，其他用通用版）"], ["mlx", "Mac 加速版（mlx-whisper large-v3-turbo）"], ["faster", "通用版（faster-whisper）"]]
            .map(([k, l]) => `<option value="${k}" ${s.asr_engine === k ? "selected" : ""}>${l}</option>`).join("")}</select>
          <div class="hint">${STATE.asr.apple_silicon ? (STATE.asr.mlx_available ? "✓ 检测到苹果芯片，Mac 加速版可用（第一次会下载约 1.6GB 模型）" : "检测到苹果芯片，但还没装加速组件：请重新运行一次安装脚本") : "这台电脑用通用版"}</div></div>
        <div class="field"><label class="check" style="margin-top:26px"><input type="checkbox" id="useSubs" ${s.use_subtitles ? "checked" : ""}> 视频自带字幕时直接用字幕（更快，跳过下载和转写）</label></div>
        <div class="field"><label>通用版的模型大小</label><select id="wm">
          ${[["tiny", "tiny：最快，准确率低"], ["base", "base：较快，够用"], ["small", "small：推荐，准确率和速度平衡"], ["medium", "medium：更准，但慢很多"]]
            .map(([k, l]) => `<option value="${k}" ${s.whisper_model === k ? "selected" : ""}>${l}</option>`).join("")}</select>
          <div class="hint">只在用通用版时生效。第一次使用会自动下载（small 约 480MB）。</div></div>
        <div class="field"><label>超长视频只转录前几分钟</label><input id="maxMin" type="number" min="1" max="120" value="${s.max_minutes}"></div>
      </div>
      <div class="field"><label>图片文字识别（图文用）</label>
        <div class="${STATE.ocr?.backend ? "" : "banner warn"}" style="${STATE.ocr?.backend ? "" : "margin:0"}">${STATE.ocr?.backend ? `✓ ${esc(STATE.ocr.label)}（在本机运行，图片不上传）` : "还没安装文字识别组件：请重新运行一次安装脚本。没装的话，图文只会用正文文字。"}</div></div>
      <div class="field"><label class="check"><input type="checkbox" id="mirror" ${s.use_hf_mirror ? "checked" : ""}> 使用国内镜像下载模型（人在中国大陆时勾选；在海外不要勾）</label></div>
      <div class="field"><label class="check"><input type="checkbox" id="keepVideo" ${s.keep_video ? "checked" : ""}> 转录后保留视频文件（默认删除，节省空间）</label></div>
    </div>
    <div class="card form" style="margin-bottom:16px" id="backupCard">
      <h2>备份与恢复</h2>
      <p class="muted" style="margin:-6px 0 0">把全部数据（笔记、文字稿、精读、学习进度、设置）打包成一个文件。换电脑时，在新电脑上装好学习台，导入这个文件就恢复原样。
        抖音登录状态和语音模型不打包：换电脑后重新扫码、模型会自动重新下载。</p>
      <div class="row" style="gap:12px">
        <a class="btn primary" id="bkDown" href="/api/backup?keys=1">${ico("download")}下载完整备份</a>
        <label class="check small"><input type="checkbox" id="bkKeys" checked style="accent-color:var(--accent)"> 备份里包含 AI Key</label>
        <span class="spacer"></span>
        <label class="btn" for="bkFile">恢复备份…</label>
        <input type="file" id="bkFile" accept=".zip,application/zip" hidden>
      </div>
      <div class="hint" id="bkHint">备份文件里如果包含 AI Key，请当作密码一样保管，别发给别人。恢复会覆盖当前数据，恢复前程序会先自动把当前数据备份一份。</div>
      <div id="bkAuto"></div>
    </div>
    <div class="card form" style="margin-bottom:16px">
      <h2>存储与浏览器</h2>
      <div class="field"><label>笔记保存位置（可以直接用 Obsidian 打开这个文件夹；留空 = 默认位置）</label>
        <div class="row"><input id="libDir" value="${esc(s.library_dir)}" placeholder="${esc(STATE.library_dir)}" style="flex:1"><button class="btn" id="openLib">打开文件夹</button></div></div>
      <div class="field"><label>用哪个浏览器登录抖音</label><select id="browser">
        ${[["auto", "自动（先找 Edge，再找 Chrome）"], ["msedge", "Microsoft Edge"], ["chrome", "Google Chrome"], ["chromium", "内置 Chromium（需单独安装）"]]
          .map(([k, l]) => `<option value="${k}" ${s.browser === k ? "selected" : ""}>${l}</option>`).join("")}</select></div>
    </div>
    <div class="row"><span class="spacer"></span>${s.api_key_set ? `<button class="btn ghost" id="clearKey">清除已保存的 Key</button>` : ""}<button class="btn primary" id="saveBtn">保存设置</button></div>`;

  const showKeyLink = () => {
    const p = P[$("#provider").value];
    $("#keyLink").innerHTML = p.key_url ? `<a href="${esc(p.key_url)}" target="_blank" rel="noopener">去 ${esc(p.name)} 申请 Key →</a>` : "填写任意 OpenAI 兼容接口的地址和模型名";
  };
  showKeyLink();
  const showDKeyLink = () => {
    const p = P[$("#dProvider").value];
    $("#dKeyLink").innerHTML = p.key_url ? `<a href="${esc(p.key_url)}" target="_blank" rel="noopener">去 ${esc(p.name)} 申请 Key →</a>` : "";
  };
  showDKeyLink();
  $("#deepSame").onchange = (e) => { $("#deepCfg").hidden = e.target.checked; };
  $("#dProvider").onchange = () => {
    const p = P[$("#dProvider").value];
    if (p.base_url) { $("#dBase").value = p.base_url; $("#dModel").value = p.model; }
    modelCache.deep = null; fillPick("dModelPick", "dModel", p.models || [p.model].filter(Boolean), "dmHint", false);
    showDKeyLink();
  };
  $("#dPromptReset").onclick = () => { $("#dPrompt").value = s.default_deep_prompt; };
  $("#dTest").onclick = async () => {
    $("#dTestRes").textContent = "测试中…";
    const r = await api("/api/test_llm", { purpose: "deep", provider: $("#dProvider").value, base_url: $("#dBase").value, model: $("#dModel").value, api_key: $("#dKey").value });
    if (r.ok) {
      if (r.models?.length) modelCache.deep = r.models;
      toast("连接成功，精读设置已自动保存");
      await renderSettings();
      $("#dTestRes").innerHTML = `<span style="color:var(--ok)">✓ 连接成功，已保存（AI 回复：${esc(r.reply)}）</span>`;
    } else $("#dTestRes").innerHTML = `<span style="color:var(--bad)">✗ ${esc(r.error)}</span>`;
  };
  $("#provider").onchange = () => {
    const p = P[$("#provider").value];
    if (p.base_url) { $("#baseUrl").value = p.base_url; $("#model").value = p.model; }
    modelCache.main = null; fillPick("modelPick", "model", p.models || [p.model].filter(Boolean), "mHint", false);
    showKeyLink();
  };
  $("#testBtn").onclick = async () => {
    $("#testRes").textContent = "测试中…";
    const r = await api("/api/test_llm", { provider: $("#provider").value, base_url: $("#baseUrl").value, model: $("#model").value, api_key: $("#apiKey").value });
    if (r.ok) {
      if (r.models?.length) modelCache.main = r.models;
      toast("连接成功，已自动保存");
      await renderSettings();
      $("#testRes").innerHTML = `<span style="color:var(--ok)">✓ 连接成功，已保存（AI 回复：${esc(r.reply)}）</span>`;
    } else $("#testRes").innerHTML = `<span style="color:var(--bad)">✗ ${esc(r.error)}</span>`;
  };
  // 模型下拉：有缓存用缓存，没有就用预设，并在后台去服务商拉一次真实列表
  const initPick = (purpose, pickId, inputId, hintId, provId) => {
    const p = P[$("#" + provId).value] || {};
    const cached = modelCache[purpose];
    fillPick(pickId, inputId, cached || p.models || [], hintId, !!cached);
    const load = async (quiet) => {
      const body = purpose === "deep"
        ? { purpose, provider: $("#dProvider").value, base_url: $("#dBase").value, api_key: $("#dKey").value }
        : { purpose, provider: $("#provider").value, base_url: $("#baseUrl").value, api_key: $("#apiKey").value };
      try { const r = await api("/api/models", body); modelCache[purpose] = r.models; fillPick(pickId, inputId, r.models, hintId, true);
        if (!quiet) toast(`读取到 ${r.models.length} 个模型`); }
      catch (e) { if (!quiet) toast(e.message, 4000); }
    };
    $("#" + (purpose === "deep" ? "dmLoad" : "mLoad")).onclick = () => load(false);
    const keySet = purpose === "deep" ? s.deep_api_key_set : s.api_key_set;
    if (!cached && keySet && (purpose === "main" || !s.deep_same)) load(true);
  };
  initPick("main", "modelPick", "model", "mHint", "provider");
  initPick("deep", "dModelPick", "dModel", "dmHint", "dProvider");
  setupBackup();
  setupFreePlan();
  $("#openLib").onclick = () => api("/api/open", { what: "library" }).catch((e) => toast(e.message));
  $("#clearKey") && ($("#clearKey").onclick = async () => { if (confirm("清除已保存的 API Key？")) { await api("/api/settings", { clear_key: true }); toast("已清除"); renderSettings(); } });
  $("#saveBtn").onclick = async () => {
    await api("/api/settings", {
      provider: $("#provider").value, base_url: $("#baseUrl").value.trim(), model: $("#model").value.trim(), api_key: $("#apiKey").value.trim(),
      deep_same: $("#deepSame").checked, deep_provider: $("#dProvider").value, deep_base_url: $("#dBase").value.trim(),
      deep_model: $("#dModel").value.trim(), deep_api_key: $("#dKey").value.trim(), deep_prompt: $("#dPrompt").value.trim(),
      deep_chunk_chars: +$("#dChunk").value,
      focus_topic: $("#focus").value.trim(), only_relevant: $("#onlyRel").checked, categories: $("#cats").value,
      whisper_model: $("#wm").value, asr_engine: $("#engine").value, use_subtitles: $("#useSubs").checked, max_minutes: +$("#maxMin").value, use_hf_mirror: $("#mirror").checked,
      keep_video: $("#keepVideo").checked, library_dir: $("#libDir").value.trim(), browser: $("#browser").value, welcome_done: true,
    });
    toast("已保存"); renderSettings();
  };
}

/* ---------------------------------------------------------------- 启动 */
let weeklyDue = null;
(async () => {
  await refreshState();
  try { weeklyDue = await api("/api/weekly/due"); $("#navWeekly").hidden = !weeklyDue.due; } catch {}
  if (!location.hash) location.hash = STATE.settings.api_key_set || STATE.stats.total ? "#/library" : "#/settings";
  render();
  startPolling();
})();

/* ---------------------------------------------------------------- 备份与恢复 */
const fmtSize = (n) => n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";

async function setupBackup() {
  const keys = $("#bkKeys"), down = $("#bkDown");
  keys.onchange = () => { down.href = "/api/backup?keys=" + (keys.checked ? "1" : "0"); };
  down.onclick = () => toast("正在打包备份，稍等几秒浏览器就会开始下载");
  $("#bkFile").onchange = async (e) => {
    const file = e.target.files[0]; e.target.value = "";
    if (!file) return;
    try {
      toast("正在检查备份文件……");
      const r1 = await fetch("/api/restore?dry=1", { method: "POST", body: file });
      const m = await r1.json();
      if (!r1.ok) throw new Error(m.error || "检查失败");
      const msg = `要从这个备份恢复吗？\n\n备份时间：${m.created}\n视频：${m.items} 条（笔记 ${m.done} 条，已学 ${m.learned} 条）\nMarkdown 笔记文件：${m.notes_in_zip} 个\n${m.has_keys ? "包含 AI Key" : "不含 AI Key（会保留你现在的 Key）"}\n\n恢复会覆盖当前数据；当前数据会先自动备份一份，选错了还能找回。`;
      if (!confirm(msg)) return;
      toast("正在恢复……", 10000);
      const r2 = await fetch("/api/restore", { method: "POST", body: file });
      const res = await r2.json();
      if (!r2.ok) throw new Error(res.error || "恢复失败");
      toast(`✓ 恢复完成：${res.items} 条视频，${res.done} 条笔记`, 4000);
      await refreshState(); renderSettings();
    } catch (err) { toast(err.message, 5000); }
  };
  try {
    const r = await api("/api/backups");
    if (r.files.length) {
      $("#bkAuto").innerHTML = `<details style="margin-top:4px"><summary class="small">恢复前的自动备份（${r.files.length} 个，可以用来撤销恢复）</summary>
        <div class="qlist" style="margin-top:8px">${r.files.map((f) => `<div class="qrow"><div><div class="t">${esc(f.name)}</div>
          <div class="r">${new Date(f.mtime * 1000).toLocaleString("zh-CN", { hour12: false })} · ${fmtSize(f.size)}</div></div>
          <button class="btn sm" data-auto="${esc(f.name)}">恢复到这个</button></div>`).join("")}</div>
        <div class="hint">保存在 ${esc(r.dir)}，只保留最近 5 个。</div></details>`;
      $$("[data-auto]").forEach((b) => b.onclick = async () => {
        if (!confirm("恢复到这个自动备份？当前数据同样会先自动备份一份。")) return;
        try { const res = await api("/api/restore_auto", { name: b.dataset.auto }); toast(`✓ 已恢复：${res.items} 条视频`); await refreshState(); renderSettings(); }
        catch (e) { toast(e.message, 5000); }
      });
    }
  } catch {}
}

/* ---------------------------------------------------------------- 模型下拉 */
const modelCache = { main: null, deep: null };
function fillPick(pickId, inputId, models, hintId, live) {
  const sel = $("#" + pickId), inp = $("#" + inputId);
  if (!sel) return;
  const cur = inp.value.trim();
  const list = [...new Set([...(models || []), cur].filter(Boolean))];
  sel.innerHTML = `<option value="">${list.length ? "选择…" : "无列表"}</option>` + list.map((m) => `<option value="${esc(m)}" ${m === cur ? "selected" : ""}>${esc(m)}</option>`).join("");
  sel.onchange = () => { if (sel.value) { inp.value = sel.value; toast(`已选择 ${sel.value}，记得点「测试连接」或「保存设置」`); } };
  const h = $("#" + hintId);
  if (h) h.textContent = live ? `已从服务商读取到 ${models.length} 个可用模型，点右边的箭头选择。` : "点右边的箭头从常用模型里选；填好 Key 后会自动读取完整列表。";
}

/* ---------------------------------------------------------------- 图文：画廊与大图 */
function galleryHtml(images) {
  return `<div class="gallery">${images.map((src, i) => `<img src="/files/${encodeURI(src)}" data-g="${i}" loading="lazy" alt="图 ${i + 1}">`).join("")}</div>`;
}
function bindGallery(root, images) {
  if (!images?.length) return;
  $$("[data-g]", root).forEach((img) => img.onclick = () => openLightbox(images, +img.dataset.g));
}
function openLightbox(images, idx) {
  let box = $("#lightbox");
  if (!box) {
    box = document.createElement("div"); box.id = "lightbox"; box.className = "lightbox";
    box.innerHTML = `<button class="lb-btn lb-close" title="关闭 (Esc)">${ico("x")}</button><button class="lb-btn lb-prev" title="上一张 (←)">‹</button>
      <img alt=""><button class="lb-btn lb-next" title="下一张 (→)">›</button><div class="lb-count"></div>`;
    document.body.appendChild(box);
  }
  const show = () => {
    idx = (idx + images.length) % images.length;
    $("img", box).src = "/files/" + encodeURI(images[idx]);
    $(".lb-count", box).textContent = `${idx + 1} / ${images.length}`;
    $(".lb-prev", box).hidden = $(".lb-next", box).hidden = images.length < 2;
  };
  const close = () => { box.hidden = true; document.removeEventListener("keydown", onKey); };
  const onKey = (e) => { if (e.key === "Escape") close(); if (e.key === "ArrowLeft") { idx--; show(); } if (e.key === "ArrowRight") { idx++; show(); } };
  $(".lb-close", box).onclick = close;
  $(".lb-prev", box).onclick = (e) => { e.stopPropagation(); idx--; show(); };
  $(".lb-next", box).onclick = (e) => { e.stopPropagation(); idx++; show(); };
  box.onclick = (e) => { if (e.target === box) close(); };
  document.addEventListener("keydown", onKey);
  box.hidden = false; show();
}

/* ---------------------------------------------------------------- 免费方案 */
let freePick = null;
function freePlanHtml(s) {
  const FP = STATE.free_plans || {};
  const cur = s.free_plan && FP[s.free_plan];
  return `<div class="card form free-card" style="margin-bottom:16px" id="freeCard">
    <div class="row"><h2 style="margin:0">免费方案</h2><span class="chip">推荐新手</span><span class="spacer"></span>
      ${cur ? `<span class="chip teal">✓ 正在使用：${esc(cur.name)} · ${esc(s.model)}</span>` : ""}</div>
    <p class="muted" style="margin:-6px 0 0">用你自己账号的免费额度，不花钱。免费模型够日常提炼用；想要更好的效果（尤其是「带我精读」），可以在下面换成付费模型。</p>
    <div class="plans">${Object.entries(FP).map(([k, p]) => `
      <button class="plan ${freePick === k ? "on" : ""} ${s.free_plan === k ? "using" : ""}" data-plan="${k}">
        <div class="row" style="gap:6px"><b>${esc(p.name)}</b><span class="chip ${p.tag === "海外" ? "gray" : ""}">${esc(p.tag)}</span></div>
        <div class="muted small">${esc(p.desc)}</div></button>`).join("")}</div>
    <div id="freeSteps"></div>
  </div>`;
}
function setupFreePlan() {
  $$("#freeCard [data-plan]").forEach((b) => b.onclick = () => {
    freePick = b.dataset.plan;
    $$("#freeCard .plan").forEach((x) => x.classList.toggle("on", x === b));
    renderFreeSteps();
  });
  if (freePick) renderFreeSteps();
}
function renderFreeSteps() {
  const p = STATE.free_plans[freePick];
  $("#freeSteps").innerHTML = `<ol class="free-steps">
      <li><b>注册 / 登录</b>：<a href="${esc(p.signup)}" target="_blank" rel="noopener">打开 ${esc(p.name)} 官网 →</a></li>
      <li><b>创建 API Key 并复制</b>：<a href="${esc(p.key_url)}" target="_blank" rel="noopener">打开 API Key 页面 →</a>（点「创建」/「新建 API Key」，然后复制）</li>
      <li><b>粘贴到这里，点一键配置</b>
        <div class="row" style="margin-top:8px"><input id="freeKey" class="search" type="password" placeholder="粘贴 ${esc(p.name)} 的 API Key" autocomplete="off" style="flex:1">
          <button class="btn primary" id="freeGo">一键配置</button></div>
        <div class="small" id="freeRes" style="margin-top:8px"></div></li>
    </ol>`;
  $("#freeGo").onclick = async () => {
    const key = $("#freeKey").value.trim();
    if (!key) return toast("先把 Key 粘贴进来");
    $("#freeGo").disabled = true; $("#freeRes").innerHTML = `<span class="muted">正在测试并挑选免费模型……</span>`;
    try {
      const r = await api("/api/free_setup", { plan: freePick, api_key: key });
      toast(`配置好了：${r.name} · ${r.model}`, 3500);
      freePick = null; modelCache.main = null;
      await renderSettings();
    } catch (e) {
      $("#freeRes").innerHTML = `<span style="color:var(--bad)">✗ ${esc(e.message)}</span>`;
      $("#freeGo").disabled = false;
    }
  };
}

/* ---------------------------------------------------------------- 空状态与骨架屏 */
function emptyHtml(icon, title, desc, actions = "") {
  return `<div class="empty-state" style="grid-column:1/-1">
    <div class="es-art">${ico(icon, "ic es-ic")}</div>
    <h2>${title}</h2><p class="muted">${desc}</p>
    ${actions ? `<div class="row" style="justify-content:center;margin-top:6px">${actions}</div>` : ""}</div>`;
}
function skeletonLibrary() {
  const card = `<div class="sk-card"><div class="sk sk-cover"></div><div class="sk-body"><div class="sk sk-line w80"></div><div class="sk sk-line"></div><div class="sk sk-line w60"></div></div></div>`;
  return `<div class="head"><div><div class="sk sk-h1"></div><div class="sk sk-line w40"></div></div></div>
    <div class="sk sk-block"></div><div class="grid">${card.repeat(6)}</div>`;
}
function skeletonItem() {
  return `<div class="detail"><div><div class="sk sk-line w20" style="margin-bottom:22px"></div><div class="sk sk-h1 w70"></div>
      <div class="sk sk-line w30"></div><div class="sk sk-block" style="height:110px;margin-top:34px"></div>
      <div class="sk sk-block" style="height:220px"></div></div>
    <div><div class="sk sk-block" style="aspect-ratio:16/10;height:auto"></div><div class="sk sk-line"></div><div class="sk sk-line w60"></div></div></div>`;
}

/* ---------------------------------------------------------------- 知识网络：图谱 + 共识观点 */
Object.assign(ICONS, {
  flame: '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  diamond: '<path d="M12 2.7 21.3 12 12 21.3 2.7 12z"/>',
});

let graphData = null, graphShowViews = true, graphSel = null;
let gView = { x: 0, y: 0, k: 1 };

async function renderGraphPage(tab, category, soft = false) {
  const tabs = `<div class="seg" id="gTabs">
      <a href="#/graph" class="${tab === "map" ? "on" : ""}">图谱</a>
      <a href="#/graph/consensus" class="${tab === "consensus" ? "on" : ""}">共识观点</a></div>`;
  const headHtml = `<div class="head"><div><h1>知识网络</h1>
      <div class="muted">${tab === "map" ? "有共同关键词（标签、概念、工具）的笔记连成线，线越粗关联越多" : "让 AI 把一个分类里的多条笔记放在一起看：哪些观点被多条视频互相印证，哪些说法不一致"}</div></div>
      <div class="spacer"></div>${tabs}</div>`;
  if (tab === "consensus") return renderConsensus(headHtml, category, soft);
  view.innerHTML = headHtml + `<div class="card graph-card"><div class="sk sk-block" style="height:420px;margin:0"></div></div>`;
  graphData = await api("/api/graph");
  drawGraph(headHtml);
}

function drawGraph(headHtml) {
  const g = graphData;
  if (g.nodes.length < 2 || (!g.links.length && !g.views.length)) {
    view.innerHTML = headHtml + `<div class="card">${emptyHtml("link", "笔记之间还没有连起来",
      g.nodes.length < 2 ? "学习库里至少要有两条笔记。" : "现在的笔记之间还没有共同的标签、概念或工具。笔记多起来以后，这里会自动连成网。",
      `<a class="btn" href="#/process">${ico("plus")}添加更多笔记</a>`)}</div>`;
    return;
  }
  const cats = [...new Set(g.nodes.map((n) => n.category))];
  view.innerHTML = headHtml + `
    <div class="graph-wrap">
      <div class="card graph-card">
        <div class="row graph-tools">
          <div class="legend">${cats.map((c) => `<span><i class="dot cat-${catColor(c)}"></i>${esc(c)}</span>`).join("")}
            ${g.views.length ? `<span><i class="gdia"></i>共识观点</span>` : ""}</div>
          <span class="spacer"></span>
          ${g.views.length ? `<label class="check small"><input type="checkbox" id="gViews" ${graphShowViews ? "checked" : ""}> 显示共识观点</label>` : ""}
          <button class="btn sm" id="gFit">复位</button>
        </div>
        <svg id="gSvg" class="gsvg" role="img" aria-label="笔记关系图"></svg>
        <div class="muted small graph-hint">滚轮缩放，拖动空白处移动；点一个圆点看它和谁有关，双击打开笔记</div>
      </div>
      <aside class="card graph-side" id="gSide"></aside>
    </div>`;
  $("#gViews") && ($("#gViews").onchange = (e) => { graphShowViews = e.target.checked; layoutAndPaint(); });
  $("#gFit").onclick = () => { gView = { x: 0, y: 0, k: 1 }; applyView(); };
  layoutAndPaint();
}

function applyView() { const z = $("#gZoom"); if (z) z.setAttribute("transform", `translate(${gView.x},${gView.y}) scale(${gView.k})`); }

/* 简单的力导向布局：同步算好再画（几百个点以内很快） */
function forceLayout(nodes, links, W, H) {
  const byCat = {}; nodes.forEach((n) => (byCat[n.cat] ||= []).push(n));
  const cs = Object.keys(byCat);
  cs.forEach((c, ci) => {  // 同一分类先放在一起，布局收敛得快
    const a0 = (2 * Math.PI * ci) / cs.length, r = Math.min(W, H) * 0.28;
    byCat[c].forEach((n, i) => {
      const a = a0 + i * 0.9;
      n.x = W / 2 + Math.cos(a0) * r + Math.cos(a) * 18 * Math.sqrt(i + 1);
      n.y = H / 2 + Math.sin(a0) * r + Math.sin(a) * 18 * Math.sqrt(i + 1);
      n.vx = n.vy = 0;
    });
  });
  // Fruchterman–Reingold：点之间互相排斥、连线把两端拉近，每步移动距离逐渐变小（降温）
  const N = nodes.length, iters = N > 300 ? 150 : 300;
  const k = Math.min(90, Math.sqrt((W * H) / Math.max(N, 1)) * 0.5);
  const mx = 64, my = 28;  // 留出标签的位置
  let temp = W / 8;
  for (let it = 0; it < iters; it++) {
    for (const n of nodes) n.vx = n.vy = 0;
    for (let i = 0; i < N; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < N; j++) {
        const b = nodes[j], dx = a.x - b.x, dy = a.y - b.y, d = Math.sqrt(dx * dx + dy * dy) || 0.1;
        const f = (k * k) / d / d;
        a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
      }
    }
    for (const l of links) {
      const dx = l.t.x - l.s.x, dy = l.t.y - l.s.y, d = Math.sqrt(dx * dx + dy * dy) || 0.1;
      const f = (d / (k * k)) * (l.view ? 6 : 0.7 + Math.min(l.w, 4) * 0.2);  // 共同关键词越多拉得越紧；共识观点贴着它的笔记
      l.s.vx += dx * f; l.s.vy += dy * f; l.t.vx -= dx * f; l.t.vy -= dy * f;
    }
    for (const n of nodes) {
      n.vx += (W / 2 - n.x) * 0.06; n.vy += (H / 2 - n.y) * 0.06;  // 轻轻拉向中间，没连线的点不会飘走
      const len = Math.sqrt(n.vx * n.vx + n.vy * n.vy) || 1, step = Math.min(len, temp);
      n.x = Math.max(mx, Math.min(W - mx, n.x + (n.vx / len) * step));
      n.y = Math.max(my, Math.min(H - my, n.y + (n.vy / len) * step));
    }
    temp = Math.max(0.5, temp * 0.975);
  }
}

function layoutAndPaint() {
  const svg = $("#gSvg"); if (!svg) return;
  // 画布用实际像素大小，文字不会被缩得看不清
  const W = Math.max(300, Math.round(svg.clientWidth || 800));
  const H = W < 600 ? Math.round(W * 1.15) : Math.max(420, Math.min(720, Math.round(W * 0.62)));
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const nodes = graphData.nodes.map((n) => ({ ...n, key: "n" + n.id, cat: n.category }));
  const byKey = new Map(nodes.map((n) => [n.key, n]));
  const links = graphData.links.map((l) => ({ ...l, s: byKey.get("n" + l.source), t: byKey.get("n" + l.target) }));
  if (graphShowViews) for (const v of graphData.views) {
    const vn = { ...v, key: v.id, cat: v.category, isView: true };
    nodes.push(vn); byKey.set(v.id, vn);
    for (const id of v.items) if (byKey.get("n" + id)) links.push({ s: vn, t: byKey.get("n" + id), view: true, w: 1 });
  }
  forceLayout(nodes, links, W, H);
  const nbr = new Map(nodes.map((n) => [n.key, new Set()]));
  links.forEach((l) => { nbr.get(l.s.key).add(l.t.key); nbr.get(l.t.key).add(l.s.key); });
  const rad = (n) => 5 + Math.min(n.deg || 0, 8) * 1.1;
  const pos = (n) => `translate(${n.x.toFixed(1)},${n.y.toFixed(1)})`;
  svg.innerHTML = `<g id="gZoom">
    ${links.map((l) => `<line class="glink${l.view ? " gl-view" : ""}" data-a="${esc(l.s.key)}" data-b="${esc(l.t.key)}" x1="${l.s.x.toFixed(1)}" y1="${l.s.y.toFixed(1)}" x2="${l.t.x.toFixed(1)}" y2="${l.t.y.toFixed(1)}" stroke-width="${l.view ? 1.2 : (0.8 + Math.min(l.w, 5) * 0.7).toFixed(1)}"/>`).join("")}
    ${nodes.map((n) => n.isView
      ? `<g class="gnode gn-view" data-k="${esc(n.key)}" transform="${pos(n)}" tabindex="0" role="button" aria-label="共识观点：${esc(n.view)}">
          <rect x="-7" y="-7" width="14" height="14" rx="2.5" transform="rotate(45)"/><title>${esc(n.view)}</title></g>`
      : `<g class="gnode cat-${catColor(n.cat)}${n.learned ? " learned" : ""}" data-k="${n.key}" transform="${pos(n)}" tabindex="0" role="button" aria-label="${esc(n.title)}">
          <circle r="${rad(n)}"/>${(n.deg || 0) >= 3 ? `<text y="${rad(n) + 13}">${esc(n.title.slice(0, 12))}</text>` : ""}<title>${esc(n.title)}</title></g>`).join("")}
  </g>`;
  applyView();

  const focus = (key) => {
    svg.classList.toggle("focus", !!key);
    const near = key ? nbr.get(key) : new Set();
    $$(".gnode", svg).forEach((el) => el.classList.toggle("hl", !!key && (el.dataset.k === key || near.has(el.dataset.k))));
    $$(".glink", svg).forEach((el) => el.classList.toggle("hl", !!key && (el.dataset.a === key || el.dataset.b === key)));
  };
  const select = (key) => { graphSel = key; focus(key); renderGraphSide(key ? byKey.get(key) : null, byKey, links); };
  $$(".gnode", svg).forEach((el) => {
    el.addEventListener("mouseenter", () => { if (!graphSel) focus(el.dataset.k); });
    el.addEventListener("mouseleave", () => { if (!graphSel) focus(null); });
    el.addEventListener("click", (e) => { e.stopPropagation(); select(graphSel === el.dataset.k ? null : el.dataset.k); });
    el.addEventListener("keydown", (e) => { if (e.key === "Enter") select(el.dataset.k); });
    el.addEventListener("dblclick", () => { const n = byKey.get(el.dataset.k); if (!n.isView) location.hash = "#/item/" + n.id; });
  });
  // 拖动空白处平移，滚轮缩放
  let drag = null;
  svg.onpointerdown = (e) => { if (e.target.closest(".gnode")) return; drag = { x: e.clientX, y: e.clientY, vx: gView.x, vy: gView.y, moved: false }; svg.setPointerCapture(e.pointerId); };
  svg.onpointermove = (e) => {
    if (!drag) return;
    const s = W / svg.clientWidth;
    gView.x = drag.vx + (e.clientX - drag.x) * s; gView.y = drag.vy + (e.clientY - drag.y) * s;
    drag.moved ||= Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 4; applyView();
  };
  svg.onpointerup = () => { if (drag && !drag.moved) select(null); drag = null; };
  svg.onwheel = (e) => {
    e.preventDefault();
    const rect = svg.getBoundingClientRect(), s = W / rect.width;
    const px = (e.clientX - rect.left) * s, py = (e.clientY - rect.top) * s;
    const k2 = Math.max(0.4, Math.min(4, gView.k * (e.deltaY < 0 ? 1.15 : 1 / 1.15)));
    gView.x = px - ((px - gView.x) * k2) / gView.k; gView.y = py - ((py - gView.y) * k2) / gView.k; gView.k = k2; applyView();
  };
  select(graphSel && byKey.has(graphSel) ? graphSel : null);
}

function renderGraphSide(n, byKey, links) {
  const side = $("#gSide"); if (!side) return;
  const g = graphData;
  if (!n) {
    const top = [...g.nodes].sort((a, b) => b.deg - a.deg).slice(0, 5).filter((x) => x.deg);
    side.innerHTML = `<h2>概况</h2>
      <div class="gstats"><div><b>${g.nodes.length}</b><span>条笔记</span></div><div><b>${g.links.length}</b><span>条关联</span></div><div><b>${g.views.length}</b><span>个共识</span></div></div>
      ${top.length ? `<h3>关联最多的笔记</h3><ol class="glist">${top.map((x) => `<li><a href="#/item/${x.id}">${esc(x.title)}</a><span class="muted small"> · ${x.deg} 条</span></li>`).join("")}</ol>` : ""}
      ${g.views.length ? "" : `<p class="muted small">到「共识观点」里整理一个分类，图里会多出菱形的共识观点，连着支持它的几条笔记。</p>`}`;
    return;
  }
  if (n.isView) {
    side.innerHTML = `<div class="small muted">共识观点 · ${esc(n.category)}</div>
      <h2 class="gside-title">${esc(n.view)}</h2>
      <h3>${n.items.length} 条视频都这么说</h3>
      <ul class="glist">${n.items.map((id) => byKey.get("n" + id)).filter(Boolean).map((x) => `<li><a href="#/item/${x.id}">${esc(x.title)}</a></li>`).join("")}</ul>
      <a class="btn sm" href="#/graph/consensus/${encodeURIComponent(n.category)}">看完整整理 →</a>`;
    return;
  }
  const rel = links.filter((l) => !l.view && (l.s.key === n.key || l.t.key === n.key))
    .map((l) => ({ other: l.s.key === n.key ? l.t : l.s, shared: l.shared || [], w: l.w })).sort((a, b) => b.w - a.w);
  const views = links.filter((l) => l.view && l.t.key === n.key).map((l) => l.s);
  side.innerHTML = `<div class="row" style="gap:6px">${catChip(n.category)}${n.learned ? `<span class="chip teal">${ico("check", "ic sm")}已学</span>` : ""}</div>
    <h2 class="gside-title">${esc(n.title)}</h2>
    <a class="btn sm primary" href="#/item/${n.id}">打开笔记</a>
    ${views.length ? `<h3>支持的共识观点</h3><ul class="glist">${views.map((v) => `<li>${esc(v.view)}</li>`).join("")}</ul>` : ""}
    <h3>${rel.length ? `和 ${rel.length} 条笔记有关` : "暂时没有关联的笔记"}</h3>
    <ul class="glist">${rel.map((x) => `<li><a href="#/item/${x.other.id}">${esc(x.other.title)}</a>
      <div class="muted small">共同：${x.shared.map(esc).join("、")}</div></li>`).join("")}</ul>`;
}

async function renderConsensus(headHtml, category, soft) {
  if (category) return renderConsensusDetail(headHtml, category, soft);
  if (!soft) view.innerHTML = headHtml + `<div class="sk sk-block" style="height:220px"></div>`;
  const r = await api("/api/insights");
  const ins = r.runner || {}, keyOk = STATE.settings.api_key_set;
  view.innerHTML = headHtml + `
    ${keyOk ? "" : `<div class="banner info"><div>整理共识观点要用 AI，先到设置里配好 AI Key。</div><span class="spacer"></span><a class="btn sm primary" href="#/settings">去配置 →</a></div>`}
    ${r.categories.length ? `<div class="cgrid">${r.categories.map((c) => {
      const running = ins.category === c.category, queued = !running && (ins.pending || []).includes(c.category);
      const err = (ins.errors || {})[c.category];
      const status = running ? `<span class="chip teal">整理中…</span>`
        : queued ? `<span class="chip gray">排队中</span>`
        : c.done ? `<span class="chip teal">${c.consensus} 条共识</span>${c.new ? `<span class="chip warn">新增 ${c.new} 条笔记</span>` : ""}`
        : `<span class="chip gray">未整理</span>`;
      const can = c.n >= 2 && keyOk && !running && !queued;
      return `<div class="card ccard">
        <div class="row"><i class="dot cat-${catColor(c.category)}"></i><b>${esc(c.category)}</b><span class="spacer"></span><span class="muted small">${c.n} 条笔记</span></div>
        <div class="row" style="gap:6px;flex-wrap:wrap">${status}</div>
        ${err ? `<div class="small" style="color:var(--bad)">${esc(err)}</div>` : ""}
        <div class="row ccard-foot">
          ${c.done ? `<a class="btn sm primary" href="#/graph/consensus/${encodeURIComponent(c.category)}">查看</a>` : ""}
          <span class="spacer"></span>
          ${c.n < 2 ? `<span class="muted small">至少 2 条笔记才能比较</span>`
            : `<button class="btn sm ${c.done ? "ghost" : ""}" data-build="${esc(c.category)}" ${can ? "" : "disabled"}>${c.done ? "重新整理" : "整理共识"}</button>`}
        </div></div>`; }).join("")}</div>
      <p class="muted small" style="margin-top:14px">每整理一个分类调用一次 AI（用「设置 → 精读」里的模型）。结果也会保存成 Markdown，放在笔记文件夹的「_共识观点」里，在 Obsidian 里能点链接跳回原笔记。</p>`
    : `<div class="card">${emptyHtml("book", "学习库还是空的", "先添加几条笔记，再来这里找它们之间的共识。")}</div>`}`;
  $$("[data-build]").forEach((b) => b.onclick = async () => {
    try { await api("/api/insights", { category: b.dataset.build }); toast("开始整理，一般需要半分钟到两分钟"); await refreshState(); renderConsensus(headHtml, "", true); }
    catch (e) { toast(e.message, 4000); }
  });
}

async function renderConsensusDetail(headHtml, category, soft) {
  if (!soft) view.innerHTML = headHtml + `<div class="sk sk-block" style="height:320px"></div>`;
  let ins;
  try { ins = await api("/api/insights/" + encodeURIComponent(category)); }
  catch (e) { view.innerHTML = headHtml + `<div class="card">${emptyHtml("search", esc(e.message), "", `<a class="btn" href="#/graph/consensus">← 返回分类列表</a>`)}</div>`; return; }
  const d = ins.data, T = ins.titles || {};
  const busy = STATE.insights?.category === category || (STATE.insights?.pending || []).includes(category);
  const src = (ids) => ids.map((id) => T[id] ? `<a class="src" href="#/item/${id}">${esc(T[id])}</a>` : "").join("");
  view.innerHTML = headHtml + `
    <a class="back" href="#/graph/consensus">← 全部分类</a>
    <div class="card cdetail">
      <div class="row"><h2 style="margin:0"><i class="dot big-dot cat-${catColor(category)}"></i>${esc(category)}</h2><span class="spacer"></span>
        <button class="btn sm" id="cReveal">${ico("folder")}在文件夹中显示</button>
        <button class="btn sm ghost" id="cRedo" ${busy ? "disabled" : ""}>${busy ? "整理中…" : "重新整理"}</button></div>
      <div class="muted small">由 ${esc(ins.model || "")} 从 ${ins.item_ids.length} 条笔记中整理 · ${new Date(ins.created_at * 1000).toLocaleString("zh-CN", { hour12: false })}</div>
      ${d.overview ? `<div class="summary" style="margin-top:14px">${esc(d.overview)}</div>` : ""}
    </div>
    <section><h2>共识观点 <span class="muted small">多条视频互相印证</span></h2>
      ${d.consensus.length ? `<ol class="cons-list">${d.consensus.map((c) => `<li class="card">
        <div class="cons-head"><b>${esc(c.view)}</b><span class="chip teal">${c.item_ids.length} 条视频</span></div>
        ${c.detail ? `<p>${esc(c.detail)}</p>` : ""}
        <div class="srcs">${src(c.item_ids)}</div></li>`).join("")}</ol>`
      : `<p class="muted">这个分类的笔记之间没有找到被多条视频共同支持的观点。笔记多起来以后再整理一次试试。</p>`}
    </section>
    ${d.conflicts.length ? `<section><h2>说法不一致的地方</h2>${d.conflicts.map((c) => `<div class="card conflict">
      <b>${esc(c.topic)}</b>
      <div class="sides">${c.sides.map((s) => `<div class="side-v"><div>${esc(s.view)}</div><div class="srcs">${src(s.item_ids)}</div></div>`).join("")}</div>
      ${c.advice ? `<div class="advice">${ico("bulb")}<span>${esc(c.advice)}</span></div>` : ""}</div>`).join("")}</section>` : ""}`;
  $("#cReveal").onclick = () => api("/api/open", { what: "insight", category }).catch((e) => toast(e.message));
  $("#cRedo").onclick = async () => {
    try { await api("/api/insights", { category }); toast("开始重新整理"); await refreshState(); renderConsensusDetail(headHtml, category, true); }
    catch (e) { toast(e.message, 4000); }
  };
}

/* ---------------------------------------------------------------- 每周周报 */
async function renderWeekly(offset) {
  view.innerHTML = `<div class="sk sk-h1"></div><div class="sk sk-block" style="height:140px"></div><div class="sk sk-block" style="height:260px"></div>`;
  const r = await api("/api/weekly?offset=" + offset);
  if (weeklyDue?.due && r.week === weeklyDue.week) {  // 看过了，不再提示
    weeklyDue.due = false; $("#navWeekly").hidden = true;
    api("/api/weekly/seen", { week: r.week }).catch(() => {});
  }
  const tile = (n, label, sub = "") => `<div class="wtile"><b>${n}</b><span>${label}</span>${sub ? `<em>${sub}</em>` : ""}</div>`;
  const maxCat = Math.max(1, ...r.categories.map((c) => c.n));
  const list = (items) => `<ul class="wlist">${items.map((it) => `<li><i class="dot cat-${catColor(it.category)}"></i><a href="#/item/${it.id}">${esc(it.title)}</a></li>`).join("")}</ul>`;
  const cheer = r.streak >= 4 ? "已经养成习惯了，继续保持" : r.streak >= 2 ? "连着好几周了，别断" : r.streak === 1 ? "开了个好头" : "这周学一条，就能开始计数";
  view.innerHTML = `
    <div class="head"><div><h1>学习周报</h1><div class="muted">${esc(r.label)}${r.is_current ? " · 本周（还在进行中）" : ""}</div></div>
      <div class="spacer"></div>
      <div class="row week-nav">
        <a class="btn sm" href="#/weekly/${r.offset - 1}">‹ 上一周</a>
        ${r.is_current ? "" : `<a class="btn sm" href="#/weekly">本周</a>`}
        ${r.is_current ? `<button class="btn sm" disabled>下一周 ›</button>` : `<a class="btn sm" href="#/weekly/${r.offset + 1}">下一周 ›</a>`}
      </div></div>
    <div class="card streak-card">
      <div class="streak-ic">${ico("flame")}</div>
      <div><div class="streak-n">连续学习 <b>${r.streak}</b> 周</div><div class="muted small">${cheer}。标记学会、精读、做测验、回答检查题都算学习。</div></div>
    </div>
    ${r.has_any ? `
    <div class="wtiles">
      ${tile(r.new, "条新笔记")}
      ${tile(r.learned, "条学会")}
      ${tile(r.deep, "条精读")}
      ${tile(r.quizzes, "次测验", r.quiz_accuracy != null ? `正确率 ${r.quiz_accuracy}%` : "")}
      ${tile(r.checks + r.asks, "次答题和提问", r.checks || r.asks ? `检查题 ${r.checks} · 问老师 ${r.asks}` : "")}
      ${tile(r.tokens.toLocaleString(), "AI tokens", r.tokens ? "" : "从这个版本开始统计")}
    </div>
    <div class="wgrid">
      ${r.categories.length ? `<div class="card"><h2>新笔记都在学什么</h2>
        <div class="wbars">${r.categories.map((c) => `<div class="wbar"><span class="wlabel">${esc(c.category)}</span>
          <span class="wtrack"><i class="cat-${catColor(c.category)}" style="width:${Math.round((c.n / maxCat) * 100)}%"></i></span><b>${c.n}</b></div>`).join("")}</div>
        ${r.top_tags.length ? `<h3>高频关键词</h3><div class="row" style="gap:6px;flex-wrap:wrap">${r.top_tags.map((t) => `<span class="chip gray">${esc(t)}</span>`).join("")}</div>` : ""}
      </div>` : ""}
      ${r.learned_items.length ? `<div class="card"><h2>这周学会了</h2>${list(r.learned_items)}</div>` : ""}
      ${r.insights.length ? `<div class="card"><h2>整理了共识观点</h2><ul class="wlist">${r.insights.map((i) => `<li><i class="dot cat-${catColor(i.category)}"></i><a href="#/graph/consensus/${encodeURIComponent(i.category)}">${esc(i.category)}</a><span class="muted small"> · ${i.consensus} 条</span></li>`).join("")}</ul></div>` : ""}
    </div>` : `<div class="card">${emptyHtml("coffee", r.is_current ? "这周还没开始" : "这周没有学习记录", r.is_current ? "随便挑一条笔记学一下，周报就会热闹起来。" : "休息一下也没关系。")}</div>`}
    ${r.suggest.length ? `<div class="card" style="margin-top:16px"><div class="row"><h2 style="margin:0">接下来先学这几条</h2><span class="spacer"></span><span class="muted small">还有 ${r.unlearned} 条没学，这几条收进来最久</span></div>${list(r.suggest)}</div>` : ""}
    <div class="row" style="margin-top:18px"><span class="spacer"></span>
      <button class="btn" id="wSave">${ico("download")}保存为 Markdown 到笔记文件夹</button></div>`;
  $("#wSave").onclick = async () => {
    try { await api("/api/weekly/save", { offset: r.offset }); toast("已保存到「_周报」文件夹"); }
    catch (e) { toast(e.message, 4000); }
  };
}
