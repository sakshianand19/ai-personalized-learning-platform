"use strict";

/* ===================== Helpers ===================== */

const API = "/api/v1";
const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const pct = (m) => (m == null ? "—" : `${Math.round(m * 100)}%`);
const LETTERS = "ABCDEF";

const store = {
  get(key) { try { return localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch { /* storage unavailable */ } },
};

async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(API + path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(errorMessage(data) || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return data;
}

function errorMessage(data) {
  const detail = data?.detail;
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg.replace(/^Value error, /, "")).join("; ");
  if (detail.message) return `${detail.message}: ${(detail.issues || []).join(" ")}`;
  return "";
}

const ICONS = {
  dashboard: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>',
  practice: '<svg viewBox="0 0 24 24"><path d="M9 11l3 3 8-8"/><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9"/></svg>',
  homework: '<svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5v14z"/><path d="M20 17v4H6.5A2.5 2.5 0 0 1 4 18.5"/></svg>',
  path: '<svg viewBox="0 0 24 24"><circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h7a3.5 3.5 0 0 0 0-7H9a3.5 3.5 0 0 1 0-7h7"/></svg>',
  studio: '<svg viewBox="0 0 24 24"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg>',
  validator: '<svg viewBox="0 0 24 24"><path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z"/><path d="M9 12l2 2 4-4"/></svg>',
  check: '<svg viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>',
  x: '<svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>',
  target: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg>',
  trophy: '<svg viewBox="0 0 24 24"><path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/></svg>',
  alert: '<svg viewBox="0 0 24 24"><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
  chart: '<svg viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/></svg>',
  clock: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  list: '<svg viewBox="0 0 24 24"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>',
  arrowL: '<svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>',
  arrowR: '<svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"/></svg>',
  book: '<svg viewBox="0 0 24 24"><path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/></svg>',
  info: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg>',
  plus: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  sun: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  moon: '<svg viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
};

const STATUS = {
  gap: { label: "Learning gap", cls: "bad" },
  needs_assessment: { label: "Not assessed", cls: "neutral" },
  in_progress: { label: "In progress", cls: "warn" },
  mastered: { label: "Mastered", cls: "good" },
};

const NAV = [
  ["dashboard", "Dashboard"],
  ["practice", "Practice"],
  ["homework", "Homework"],
  ["path", "Learning Path"],
  ["studio", "Content Studio"],
  ["validator", "Validator"],
];

const state = { students: [], studentId: null, topics: [], quiz: null, keyHandler: null };
const student = () => state.students.find((s) => s.id === state.studentId);
const topicName = (id) => state.topics.find((t) => t.id === id)?.name ?? `Topic ${id}`;

function setView(html, { animate = true } = {}) {
  const el = $("#view");
  if (animate) {
    el.style.animation = "none";
    void el.offsetHeight; // restart the fade-in animation
    el.style.animation = "";
    window.scrollTo({ top: 0 });
  }
  el.innerHTML = html;
  return el;
}

function loading(rows = 3) {
  return `<div class="stack">${'<div class="skeleton" style="height:110px"></div>'.repeat(rows)}</div>`;
}

function toast(message, type = "") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  $("#toasts").append(el);
  setTimeout(() => el.remove(), 3800);
}

function openModal(html) {
  $("#modal-body").innerHTML = html;
  $("#modal").hidden = false;
}
function closeModal() {
  $("#modal").hidden = true;
}

async function withBusy(button, fn) {
  const original = button.innerHTML;
  button.disabled = true;
  button.innerHTML = `<span class="spinner"></span> ${button.dataset.busy || "Working…"}`;
  try {
    return await fn();
  } catch (err) {
    toast(err.message, "error");
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
}

function ring(value, { size = 120, label = "mastery", color } = {}) {
  const p = value == null ? 0 : Math.round(value * 100);
  const c = color || (value == null ? "var(--neutral)" : p >= 85 ? "var(--good)" : p >= 60 ? "var(--warn)" : "var(--bad)");
  return `<div class="ring" style="--p:${p};--c:${c};--size:${size}px"><div><strong>${value == null ? "—" : p + "%"}</strong><span>${esc(label)}</span></div></div>`;
}

function scoreClass(score) {
  return score >= 80 ? "good" : score >= 50 ? "warn" : "bad";
}

function animateBars(root) {
  requestAnimationFrame(() => $$(".bar > i[data-w]", root).forEach((i) => (i.style.width = i.dataset.w)));
}

function emptyState(icon, title, text, action = "") {
  return `<div class="empty"><div class="empty-icon">${ICONS[icon]}</div><h4>${esc(title)}</h4><p>${esc(text)}</p>${action ? `<div style="margin-top:16px">${action}</div>` : ""}</div>`;
}

// SQLite drops timezone info; server timestamps are always UTC.
const toDate = (iso) => new Date(/(Z|[+-]\d\d:\d\d)$/.test(iso) ? iso : `${iso}Z`);

function relativeTime(iso) {
  const diff = (Date.now() - toDate(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`;
  return toDate(iso).toLocaleDateString();
}

/* ===================== Shell ===================== */

function renderNav() {
  $("#nav").innerHTML = NAV.map(([id, label]) => `<a href="#${id}" data-view="${id}">${ICONS[id]}<span>${label}</span></a>`).join("");
}

function renderStudentPicker() {
  $("#student-select").innerHTML = state.students
    .map((s) => `<option value="${s.id}" ${s.id === state.studentId ? "selected" : ""}>${esc(s.name)}</option>`)
    .join("");
  const s = student();
  $("#avatar").textContent = s ? s.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase() : "?";
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  store.set("theme", theme);
  $("#theme-toggle").innerHTML = theme === "dark" ? ICONS.sun : ICONS.moon;
}

function currentTheme() {
  return document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

async function loadEngine() {
  try {
    const health = await fetch("/health").then((r) => r.json());
    const azure = health.llm_provider === "azure_openai";
    $("#engine").className = `engine ${azure ? "azure" : "heuristic"}`;
    $("#engine-label").textContent = azure ? "Azure OpenAI · LangChain" : "Heuristic engine (no Azure key)";
  } catch {
    $("#engine-label").textContent = "Engine unavailable";
  }
}

async function loadStudents() {
  state.students = await api("/students?limit=200");
  const saved = Number(store.get("studentId"));
  state.studentId = state.students.some((s) => s.id === saved) ? saved : state.students[0]?.id ?? null;
  renderStudentPicker();
}

function newStudentModal() {
  openModal(`
    <h2>Add a student</h2>
    <p class="muted" style="margin-bottom:20px">Each student gets their own mastery profile, gaps and learning path.</p>
    <form id="student-form" class="stack">
      <div class="field"><label for="s-name">Full name</label><input class="input" id="s-name" required maxlength="120" placeholder="e.g. Aarav Sharma"></div>
      <div class="field"><label for="s-email">Email</label><input class="input" id="s-email" type="email" required placeholder="aarav@school.edu"></div>
      <div class="field"><label for="s-grade">Grade</label>
        <select class="input" id="s-grade">${Array.from({ length: 12 }, (_, i) => `<option ${i === 6 ? "selected" : ""}>${i + 1}</option>`).join("")}</select></div>
      <button class="btn gradient lg" data-busy="Creating…">Create student</button>
    </form>`);
  $("#student-form").addEventListener("submit", (e) => {
    e.preventDefault();
    withBusy(e.submitter || $("#student-form button"), async () => {
      const created = await api("/students", {
        method: "POST",
        body: { name: $("#s-name").value.trim(), email: $("#s-email").value.trim(), grade_level: Number($("#s-grade").value) },
      });
      state.students.push(created);
      selectStudent(created.id);
      closeModal();
      toast(`Welcome, ${created.name}!`, "success");
    });
  });
}

function selectStudent(id) {
  state.studentId = id;
  store.set("studentId", String(id));
  renderStudentPicker();
  route();
}

/* ===================== Router ===================== */

const VIEWS = { dashboard, practice, homework, path: learningPath, studio, validator };

function route() {
  stopQuizKeys();
  const name = location.hash.slice(1).split("/")[0] || "dashboard";
  const view = VIEWS[name] ? name : "dashboard";
  $$("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.view === view));
  $("#page-title").textContent = NAV.find(([id]) => id === view)[1];
  if (!state.studentId && ["dashboard", "practice", "homework", "path"].includes(view)) {
    setView(emptyState("dashboard", "No students yet", "Add a student to start tracking their learning.", `<button class="btn" onclick="newStudentModal()">Add student</button>`));
    return;
  }
  VIEWS[view]().catch(handleViewError);
}

function handleViewError(err) {
  if (err.status === 404 && /Student/.test(err.message)) {
    // Serverless storage can reset; fall back to an existing student.
    loadStudents().then(route);
    return;
  }
  setView(emptyState("alert", "Something went wrong", err.message, `<button class="btn ghost" onclick="route()">Try again</button>`));
}

/* ===================== Dashboard ===================== */

async function dashboard() {
  setView(loading(3));
  const sid = state.studentId;
  const [report, history] = await Promise.all([api(`/students/${sid}/learning-gaps`), api(`/students/${sid}/submissions?limit=6`)]);
  const s = student();
  const progress = report.progress;
  const count = (status) => progress.filter((p) => p.status === status).length;
  const answered = progress.reduce((n, p) => n + p.attempts, 0);
  const firstName = s.name.split(" ")[0];

  const hero = history.length
    ? `<h1>Welcome back, ${esc(firstName)} 👋</h1><p>${report.gaps.length ? `You have ${report.gaps.length} focus area${report.gaps.length > 1 ? "s" : ""}. A short practice session will help close the gap.` : "No learning gaps right now — keep the streak going with a practice quiz."}</p>`
    : `<h1>Hi ${esc(firstName)}, let's find your starting point</h1><p>Take a quick diagnostic quiz across all topics. We'll measure your mastery and build a personalised learning path.</p>`;

  const el = setView(`
    <section class="hero">
      <div>${hero}</div>
      <div class="row">
        <a class="btn lg" href="#practice">${ICONS.practice} ${history.length ? "Practice now" : "Start diagnostic"}</a>
        <a class="btn lg ghost-light" href="#path">${ICONS.path} My path</a>
      </div>
    </section>

    <section class="grid cols-4" style="margin-bottom:20px">
      ${statCard("accent", "chart", pct(report.overall_mastery), "Overall mastery")}
      ${statCard("good", "trophy", count("mastered"), "Topics mastered")}
      ${statCard("bad", "alert", report.gaps.length, "Learning gaps")}
      ${statCard("warn", "practice", answered, "Questions answered")}
    </section>

    <section class="grid split">
      <div class="card">
        <div class="card-head"><h3>Topic mastery</h3><span class="muted small">Target ${Math.round(0.6 * 100)}%</span></div>
        <div class="mastery-list">${progress.map(masteryRow).join("") || emptyState("book", "No topics yet", "Add topics in the Content Studio.")}</div>
      </div>
      <div class="stack" style="gap:20px">
        <div class="card">
          <div class="card-head"><h3>Focus areas</h3>${report.gaps.length ? `<span class="pill bad">${report.gaps.length} gap${report.gaps.length > 1 ? "s" : ""}</span>` : ""}</div>
          <div class="stack">${report.gaps.length ? report.gaps.map(gapCard).join("") : emptyState("target", history.length ? "No gaps detected" : "Not assessed yet", history.length ? "Great work! Keep practising to reach mastery." : "Take the diagnostic to discover your gaps.")}</div>
        </div>
        <div class="card">
          <div class="card-head"><h3>Recent activity</h3></div>
          <div class="list">${history.length ? history.map(activityRow).join("") : '<p class="muted small">Your completed quizzes and homework will appear here.</p>'}</div>
        </div>
      </div>
    </section>`);

  $$("[data-practice-topic]", el).forEach((btn) =>
    btn.addEventListener("click", () => withBusy(btn, () => startHomework(Number(btn.dataset.practiceTopic)))),
  );
  animateBars(el);
}

function statCard(tone, icon, value, label) {
  return `<div class="card stat"><div class="stat-icon ${tone}">${ICONS[icon]}</div><div><div class="stat-value">${esc(value)}</div><div class="stat-label">${esc(label)}</div></div></div>`;
}

function masteryRow(p) {
  const st = STATUS[p.status];
  const width = p.mastery == null ? 0 : Math.round(p.mastery * 100);
  return `
    <div class="mastery-item">
      <div class="top">
        <div><div class="name">${esc(p.topic_name)}</div><div class="sub">${esc(p.subject)} · ${p.correct}/${p.attempts} correct</div></div>
        <div class="row" style="gap:8px"><span class="pill ${st.cls}">${st.label}</span><strong>${pct(p.mastery)}</strong></div>
      </div>
      <div class="bar ${st.cls}"><i data-w="${width}%"></i><span class="target" style="left:60%"></span></div>
    </div>`;
}

function gapCard(g) {
  return `
    <div class="gap-card ${g.severity}">
      <div class="row"><h4>${esc(g.topic_name)}</h4><span class="spacer"></span><span class="pill ${g.severity === "high" ? "bad" : "warn"}">${g.severity} priority</span></div>
      <p class="small muted">${esc(g.reason)}</p>
      <p class="action">💡 ${esc(g.recommended_action)}</p>
      <div><button class="btn sm" data-practice-topic="${g.topic_id}" data-busy="Preparing…">${ICONS.practice} Practise this topic</button></div>
    </div>`;
}

function activityRow(s) {
  const kind = s.homework_id ? "Homework" : "Assessment";
  return `
    <div class="list-item">
      <div class="list-icon">${ICONS[s.homework_id ? "homework" : "practice"]}</div>
      <div><div style="font-weight:600">${kind} #${s.homework_id ?? s.assessment_id ?? s.id}</div><div class="small muted">${s.correct}/${s.total} correct · ${relativeTime(s.submitted_at)}</div></div>
      <span class="spacer"></span><span class="score-badge ${scoreClass(s.score)}">${Math.round(s.score)}%</span>
    </div>`;
}

/* ===================== Practice (assessments) ===================== */

async function practice() {
  setView(loading(2));
  state.topics = await api("/topics");
  const questions = await api("/questions");
  const perTopic = Object.fromEntries(state.topics.map((t) => [t.id, questions.filter((q) => q.topic_id === t.id).length]));
  const selectable = state.topics.filter((t) => perTopic[t.id] > 0);

  const el = setView(`
    <div class="page-head">
      <div><h1>Practice quiz</h1><p>Pick the topics you want to test. Your answers update your mastery profile and learning gaps instantly.</p></div>
    </div>
    <div class="card" style="max-width:820px">
      <div class="stack" style="gap:22px">
        <div>
          <div class="row" style="margin-bottom:12px"><span class="label">Topics</span><span class="spacer"></span><button class="btn sm ghost" id="toggle-all">Select none</button></div>
          <div class="row" id="topic-chips">
            ${selectable.map((t) => `<button class="chip on" data-topic="${t.id}"><span class="check">${ICONS.check}</span>${esc(t.name)} <span class="muted small">${perTopic[t.id]} Qs</span></button>`).join("") || '<p class="muted">No validated questions yet — generate some in the Content Studio.</p>'}
          </div>
        </div>
        <div class="field">
          <label for="qpt">Questions per topic: <b id="qpt-val">3</b></label>
          <input type="range" id="qpt" min="1" max="${Math.max(1, Math.min(10, ...Object.values(perTopic)))}" value="3">
        </div>
        <div class="row">
          <span class="muted small" id="quiz-summary"></span><span class="spacer"></span>
          <button class="btn gradient lg" id="start-quiz" data-busy="Building quiz…">${ICONS.practice} Start quiz</button>
        </div>
      </div>
    </div>`);

  const selected = () => $$(".chip.on", el).map((c) => Number(c.dataset.topic));
  const summary = () => {
    const n = Number($("#qpt").value);
    const total = selected().reduce((sum, id) => sum + Math.min(n, perTopic[id]), 0);
    $("#qpt-val").textContent = n;
    $("#quiz-summary").textContent = `${total} question${total === 1 ? "" : "s"} · about ${Math.max(1, Math.round(total * 0.5))} min`;
    $("#start-quiz").disabled = total === 0;
    $("#toggle-all").textContent = selected().length ? "Select none" : "Select all";
  };
  $$(".chip", el).forEach((chip) => chip.addEventListener("click", () => { chip.classList.toggle("on"); summary(); }));
  $("#toggle-all").addEventListener("click", () => {
    const on = !selected().length;
    $$(".chip", el).forEach((c) => c.classList.toggle("on", on));
    summary();
  });
  $("#qpt").addEventListener("input", summary);
  $("#start-quiz").addEventListener("click", (e) =>
    withBusy(e.currentTarget, async () => {
      const assessment = await api("/assessments", {
        method: "POST",
        body: { title: `Practice · ${new Date().toLocaleDateString()}`, topic_ids: selected(), questions_per_topic: Number($("#qpt").value) },
      });
      runQuiz({
        title: "Practice quiz",
        subtitle: selected().map(topicName).join(" · "),
        questions: assessment.questions,
        submit: (answers) => api(`/assessments/${assessment.id}/submit`, { method: "POST", body: { student_id: state.studentId, answers } }),
      });
    }),
  );
  summary();
}

/* ===================== Quiz runner (shared by practice & homework) ===================== */

function runQuiz({ title, subtitle, questions, submit }) {
  state.quiz = { title, subtitle, questions, submit, answers: {}, index: 0 };
  renderQuiz(true);
  stopQuizKeys();
  state.keyHandler = (e) => {
    if (!state.quiz || e.target.matches("input, textarea, select") || !$("#modal").hidden) return;
    const q = state.quiz.questions[state.quiz.index];
    const key = e.key.toUpperCase();
    const n = /^[1-6]$/.test(key) ? Number(key) - 1 : LETTERS.indexOf(key);
    if (n >= 0 && n < q.options.length && key.length === 1) choose(n);
    else if (e.key === "ArrowRight" || e.key === "Enter") moveQuiz(1);
    else if (e.key === "ArrowLeft") moveQuiz(-1);
  };
  document.addEventListener("keydown", state.keyHandler);
}

function stopQuizKeys() {
  if (state.keyHandler) document.removeEventListener("keydown", state.keyHandler);
  state.keyHandler = null;
}

function renderQuiz(animate = false) {
  const quiz = state.quiz;
  const q = quiz.questions[quiz.index];
  const total = quiz.questions.length;
  const answeredCount = Object.keys(quiz.answers).length;
  const last = quiz.index === total - 1;
  const el = setView(`
    <div class="quiz">
      <div class="quiz-head">
        <div><h2 style="font-size:20px">${esc(quiz.title)}</h2><div class="muted small">${esc(quiz.subtitle || "")}</div></div>
        <span class="pill accent">${quiz.index + 1} / ${total}</span>
      </div>
      <div class="quiz-progress"><i style="width:${(answeredCount / total) * 100}%"></i></div>
      <div class="card question-card">
        <div class="row"><span class="pill ${q.difficulty}">${q.difficulty}</span><span class="pill neutral">${esc(topicName(q.topic_id))}</span></div>
        <h2>${esc(q.text)}</h2>
        <div class="options">
          ${q.options.map((o, i) => `<button class="option ${quiz.answers[q.id] === o ? "selected" : ""}" data-i="${i}"><span class="letter">${LETTERS[i]}</span><span>${esc(o)}</span></button>`).join("")}
        </div>
      </div>
      <div class="quiz-nav">
        <button class="btn ghost" id="prev" ${quiz.index === 0 ? "disabled" : ""}>${ICONS.arrowL} Back</button>
        <div class="dots">${quiz.questions.map((qq, i) => `<button title="Question ${i + 1}" data-jump="${i}" class="${i === quiz.index ? "current" : ""} ${quiz.answers[qq.id] != null ? "answered" : ""}"></button>`).join("")}</div>
        ${last
          ? `<button class="btn gradient" id="finish" data-busy="Grading…">Submit ${ICONS.check}</button>`
          : `<button class="btn" id="next">Next ${ICONS.arrowR}</button>`}
      </div>
      <p class="kbd-hint">Tip: press <kbd>A</kbd>–<kbd>${LETTERS[q.options.length - 1]}</kbd> to answer, <kbd>←</kbd> <kbd>→</kbd> to move</p>
    </div>`, { animate });

  $$(".option", el).forEach((btn) => btn.addEventListener("click", () => choose(Number(btn.dataset.i))));
  $$("[data-jump]", el).forEach((btn) => btn.addEventListener("click", () => { quiz.index = Number(btn.dataset.jump); renderQuiz(); }));
  $("#prev", el).addEventListener("click", () => moveQuiz(-1));
  $("#next", el)?.addEventListener("click", () => moveQuiz(1));
  $("#finish", el)?.addEventListener("click", (e) => finishQuiz(e.currentTarget));
}

function choose(i) {
  const quiz = state.quiz;
  const q = quiz.questions[quiz.index];
  quiz.answers[q.id] = q.options[i];
  renderQuiz();
  // Auto-advance after a short pause so the selection is visible.
  if (quiz.index < quiz.questions.length - 1) setTimeout(() => state.quiz === quiz && quiz.index === quiz.questions.indexOf(q) && moveQuiz(1), 280);
}

function moveQuiz(delta) {
  const quiz = state.quiz;
  if (!quiz) return;
  const next = quiz.index + delta;
  if (next >= quiz.questions.length) return void finishQuiz($("#finish"));
  if (next < 0) return;
  quiz.index = next;
  renderQuiz();
}

async function finishQuiz(button) {
  const quiz = state.quiz;
  if (!quiz || !button) return;
  const unanswered = quiz.questions.length - Object.keys(quiz.answers).length;
  if (unanswered && !confirm(`${unanswered} question${unanswered > 1 ? "s are" : " is"} unanswered and will count as incorrect. Submit anyway?`)) return;
  const answers = Object.entries(quiz.answers).map(([question_id, answer]) => ({ question_id: Number(question_id), answer }));
  if (!answers.length) return toast("Answer at least one question first.", "error");
  await withBusy(button, async () => {
    const result = await quiz.submit(answers);
    stopQuizKeys();
    state.quiz = null;
    renderResults(result, quiz);
  });
}

function renderResults(result, quiz) {
  const byId = Object.fromEntries(result.responses.map((r) => [r.question_id, r]));
  const message = result.score >= 85 ? "Outstanding! 🎉" : result.score >= 60 ? "Nice work! 💪" : "Good effort — let's close those gaps 📚";
  const el = setView(`
    <div class="quiz">
      <div class="card" style="margin-bottom:20px">
        <div class="result-hero">
          ${ring(result.score / 100, { size: 140, label: "score", color: `var(--${scoreClass(result.score)})` })}
          <div class="stack" style="gap:8px;flex:1;min-width:220px">
            <h2>${message}</h2>
            <p class="muted">You answered <b>${result.correct} of ${result.total}</b> questions correctly. Your mastery profile and learning gaps have been updated.</p>
            <div class="row" style="margin-top:8px">
              <a class="btn gradient" href="#dashboard">${ICONS.dashboard} See my gaps</a>
              <a class="btn ghost" href="#path">${ICONS.path} Learning path</a>
            </div>
          </div>
        </div>
      </div>
      <h3 style="margin:0 0 12px">Review answers</h3>
      <div class="stack">
        ${quiz.questions.map((q, i) => {
          const r = byId[q.id];
          const ok = r?.is_correct;
          return `
            <div class="review-item">
              <div class="mark ${ok ? "ok" : "no"}">${ok ? ICONS.check : ICONS.x}</div>
              <div style="flex:1">
                <div class="q">${i + 1}. ${esc(q.text)}</div>
                <div class="answer-line">Your answer: <b class="${ok ? "ok" : "no"}">${r ? esc(r.answer) : "Not answered"}</b>${ok ? "" : ` · Correct: <b class="ok">${esc(r?.correct_answer ?? "—")}</b>`}</div>
                ${r?.explanation ? `<div class="answer-line" style="margin-top:4px">${esc(r.explanation)}</div>` : ""}
              </div>
            </div>`;
        }).join("")}
      </div>
    </div>`);
  return el;
}

/* ===================== Homework ===================== */

async function startHomework(topicId, numQuestions = 5) {
  const hw = await api("/homework/generate", {
    method: "POST",
    body: { student_id: state.studentId, topic_id: topicId ?? null, num_questions: numQuestions },
  });
  toast(`Homework assigned: ${hw.title}`, "success");
  openHomework(hw);
}

function openHomework(hw) {
  if (!state.topics.length) api("/topics").then((t) => (state.topics = t));
  runQuiz({
    title: hw.title,
    subtitle: hw.due_at ? `Due ${toDate(hw.due_at).toLocaleDateString()}` : "Adaptive homework",
    questions: hw.questions,
    submit: (answers) => api(`/homework/${hw.id}/submit`, { method: "POST", body: { answers } }),
  });
}

async function homework() {
  setView(loading(2));
  const [topics, list] = await Promise.all([api("/topics"), api(`/homework?student_id=${state.studentId}`)]);
  state.topics = topics;
  const assigned = list.filter((h) => h.status === "assigned");
  const done = list.filter((h) => h.status === "completed");

  const el = setView(`
    <div class="page-head"><div><h1>Homework</h1><p>Adaptive homework targets your weakest topic, prefers questions you haven't mastered yet, and matches difficulty to your level.</p></div></div>
    <div class="grid split" style="align-items:start">
      <div class="stack" style="gap:20px">
        <div class="card">
          <div class="card-head"><h3>To do</h3><span class="pill accent">${assigned.length}</span></div>
          <div class="grid cols-2">${assigned.map(hwCard).join("") || `<div style="grid-column:1/-1">${emptyState("homework", "All caught up", "Generate new homework to keep practising.")}</div>`}</div>
        </div>
        <div class="card">
          <div class="card-head"><h3>Completed</h3><span class="pill good">${done.length}</span></div>
          <div class="list">${done.map((h) => `
            <div class="list-item"><div class="list-icon" style="color:var(--good)">${ICONS.check}</div>
              <div><div style="font-weight:600">${esc(h.title)}</div><div class="small muted">${h.questions.length} questions · completed ${relativeTime(h.completed_at)}</div></div></div>`).join("") || '<p class="muted small">Nothing completed yet.</p>'}
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-head"><h3>Generate homework</h3></div>
        <div class="stack" style="gap:16px">
          <div class="field"><label for="hw-topic">Topic</label>
            <select class="input" id="hw-topic"><option value="">✨ Auto — my weakest topic</option>${topics.map((t) => `<option value="${t.id}">${esc(t.name)}</option>`).join("")}</select></div>
          <div class="field"><label for="hw-n">Questions: <b id="hw-n-val">5</b></label><input type="range" id="hw-n" min="1" max="10" value="5"></div>
          <button class="btn gradient lg" id="hw-go" data-busy="Assigning…">${ICONS.plus} Assign homework</button>
          <div class="callout">${ICONS.info}<span>Homework difficulty adapts to your mastery: below 40% gets easy questions, 40–75% medium, and above that hard.</span></div>
        </div>
      </div>
    </div>`);

  $("#hw-n").addEventListener("input", (e) => ($("#hw-n-val").textContent = e.target.value));
  $("#hw-go").addEventListener("click", (e) =>
    withBusy(e.currentTarget, () => startHomework($("#hw-topic").value ? Number($("#hw-topic").value) : null, Number($("#hw-n").value))),
  );
  $$("[data-hw]", el).forEach((btn) =>
    btn.addEventListener("click", () => withBusy(btn, async () => openHomework(await api(`/homework/${btn.dataset.hw}`)))),
  );
}

function hwCard(h) {
  const due = h.due_at ? toDate(h.due_at) : null;
  const overdue = due && due < new Date();
  return `
    <div class="card hw-card" style="box-shadow:none;background:var(--surface-2)">
      <div class="row"><span class="pill accent">${esc(topicName(h.topic_id))}</span><span class="spacer"></span>${overdue ? '<span class="pill bad">Overdue</span>' : ""}</div>
      <h4>${esc(h.title)}</h4>
      <div class="meta"><span>${ICONS.list}${h.questions.length} questions</span>${due ? `<span>${ICONS.clock}Due ${due.toLocaleDateString()}</span>` : ""}</div>
      <button class="btn sm" data-hw="${h.id}" data-busy="Opening…">Start ${ICONS.arrowR}</button>
    </div>`;
}

/* ===================== Learning path ===================== */

async function learningPath() {
  setView(loading(3));
  const data = await api(`/students/${state.studentId}/learning-path`);
  const el = setView(`
    <div class="page-head">
      <div><h1>Your learning path</h1><p>Topics ordered by urgency — gaps first, then untested topics, then reinforcement. Each step recommends material at the right difficulty.</p></div>
      <a class="btn ghost" href="#practice">${ICONS.practice} Take a quiz</a>
    </div>
    <div class="timeline">
      ${data.steps.map((s) => {
        const st = STATUS[s.status];
        return `
          <div class="step ${s.status}">
            <div class="step-num">${s.order}</div>
            <div class="card">
              <div class="row">
                <div><h3 style="font-size:17px">${esc(s.topic_name)}</h3><div class="small muted">${esc(s.subject)}</div></div>
                <span class="spacer"></span>
                <span class="pill ${st.cls}">${st.label}</span>
                <span class="pill ${s.target_difficulty}">Target: ${s.target_difficulty}</span>
                <strong>${pct(s.mastery)}</strong>
              </div>
              <div class="bar ${st.cls}" style="margin-top:14px"><i data-w="${s.mastery == null ? 0 : Math.round(s.mastery * 100)}%"></i></div>
              ${s.recommended_content.length
                ? `<div class="content-tiles">${s.recommended_content.map((c) => `
                    <button class="content-tile" data-content="${c.id}">
                      <div class="row" style="gap:6px">${ICONS.book}<span class="pill ${c.difficulty}">${c.difficulty}</span></div>
                      <div class="t">${esc(c.title)}</div><div class="s">${esc(c.summary)}</div>
                    </button>`).join("")}</div>`
                : '<p class="muted small" style="margin-top:12px">No study material for this topic yet.</p>'}
              <div class="row" style="margin-top:14px"><button class="btn sm soft" data-practice-topic="${s.topic_id}" data-busy="Preparing…">${ICONS.homework} Practise ${esc(s.topic_name)}</button></div>
            </div>
          </div>`;
      }).join("")}
    </div>`);
  $$("[data-content]", el).forEach((b) => b.addEventListener("click", () => showContent(Number(b.dataset.content))));
  $$("[data-practice-topic]", el).forEach((btn) =>
    btn.addEventListener("click", () => withBusy(btn, () => startHomework(Number(btn.dataset.practiceTopic)))),
  );
  animateBars(el);
}

async function showContent(id) {
  openModal(loading(1));
  try {
    const c = await api(`/content/${id}`);
    openModal(`
      <div class="row" style="margin-bottom:10px"><span class="pill accent">${esc(topicName(c.topic_id))}</span><span class="pill ${c.difficulty}">${c.difficulty}</span><span class="pill neutral">Analysed by ${c.processed_by === "llm" ? "Azure OpenAI" : "heuristics"}</span></div>
      <h2>${esc(c.title)}</h2>
      <div class="analysis" style="margin-top:16px">
        <div><div class="label" style="margin-bottom:8px">AI summary</div><div class="summary">${esc(c.summary)}</div></div>
        <div><div class="label" style="margin-bottom:8px">Key concepts</div><div class="row">${c.key_concepts.map((k) => `<span class="tag">${esc(k)}</span>`).join("")}</div></div>
        <div><div class="label" style="margin-bottom:8px">Material</div><div class="body-text">${esc(c.body)}</div></div>
      </div>`);
  } catch (err) {
    openModal(emptyState("alert", "Couldn't load content", err.message));
  }
}

/* ===================== Content studio ===================== */

async function studio() {
  setView(loading(2));
  const [topics, contents] = await Promise.all([api("/topics"), api("/content")]);
  state.topics = topics;

  const el = setView(`
    <div class="page-head"><div><h1>Content Studio</h1><p>Upload learning material. A LangChain pipeline on Azure OpenAI summarises it, extracts key concepts, rates difficulty and generates validated questions.</p></div></div>
    <div class="grid split" style="align-items:start">
      <div class="stack" style="gap:20px">
        <div class="card">
          <div class="card-head"><h3>New material</h3></div>
          <form id="content-form" class="stack" style="gap:14px">
            <div class="grid cols-2" style="gap:12px">
              <div class="field"><label for="c-topic">Topic</label>
                <select class="input" id="c-topic">${topics.map((t) => `<option value="${t.id}">${esc(t.subject)} · ${esc(t.name)}</option>`).join("")}<option value="__new">+ New topic…</option></select></div>
              <div class="field"><label for="c-title">Title</label><input class="input" id="c-title" required maxlength="200" placeholder="e.g. The water cycle"></div>
            </div>
            <div class="grid cols-2 hidden" id="new-topic" style="gap:12px">
              <div class="field"><label for="t-subject">Subject</label><input class="input" id="t-subject" placeholder="Science"></div>
              <div class="field"><label for="t-name">Topic name</label><input class="input" id="t-name" placeholder="Water Cycle"></div>
            </div>
            <div class="field"><label for="c-body">Material</label>
              <textarea class="input" id="c-body" required minlength="20" rows="8" placeholder="Paste a lesson, textbook passage or notes (at least a few sentences)…"></textarea></div>
            <div class="row"><button type="button" class="btn ghost sm" id="sample">Use sample text</button><span class="spacer"></span>
              <button class="btn gradient" data-busy="Analysing…">${ICONS.studio} Analyse with AI</button></div>
          </form>
        </div>
        <div id="studio-result"></div>
      </div>
      <div class="card">
        <div class="card-head"><h3>Library</h3><span class="pill neutral">${contents.length}</span></div>
        <div class="list">${contents.slice().reverse().map((c) => `
          <div class="list-item">
            <div class="list-icon">${ICONS.book}</div>
            <div style="flex:1;min-width:0"><div style="font-weight:600">${esc(c.title)}</div><div class="small muted">${esc(topicName(c.topic_id))} · <span class="pill ${c.difficulty}" style="padding:1px 8px">${c.difficulty}</span></div></div>
            <button class="btn sm ghost" data-view-content="${c.id}">View</button>
            <button class="btn sm soft" data-gen="${c.id}">Questions</button>
          </div>`).join("") || '<p class="muted small">No material yet.</p>'}
        </div>
      </div>
    </div>`);

  $("#c-topic").addEventListener("change", (e) => $("#new-topic").classList.toggle("hidden", e.target.value !== "__new"));
  $("#sample").addEventListener("click", () => {
    $("#c-title").value = "The Water Cycle";
    $("#c-body").value =
      "The water cycle describes how water moves between the Earth's surface and the atmosphere. " +
      "Heat from the sun causes evaporation, turning water from oceans and lakes into water vapour. " +
      "As the vapour rises and cools, condensation forms tiny droplets that gather into clouds. " +
      "When the droplets grow heavy, they fall back to the ground as precipitation such as rain or snow. " +
      "Water then collects in rivers, lakes and oceans, or soaks into the ground as groundwater, and the cycle repeats.";
  });
  $("#content-form").addEventListener("submit", (e) => {
    e.preventDefault();
    withBusy(e.submitter, async () => {
      let topicId = $("#c-topic").value;
      if (topicId === "__new") {
        const topic = await api("/topics", { method: "POST", body: { subject: $("#t-subject").value.trim(), name: $("#t-name").value.trim() } });
        state.topics.push(topic);
        topicId = topic.id;
      }
      const content = await api("/content", { method: "POST", body: { topic_id: Number(topicId), title: $("#c-title").value.trim(), body: $("#c-body").value.trim() } });
      toast("Material analysed and saved", "success");
      showAnalysis(content);
    });
  });
  $$("[data-view-content]", el).forEach((b) => b.addEventListener("click", () => showContent(Number(b.dataset.viewContent))));
  $$("[data-gen]", el).forEach((b) =>
    b.addEventListener("click", () => withBusy(b, async () => showAnalysis(await api(`/content/${b.dataset.gen}`)))),
  );
}

function showAnalysis(c) {
  const box = $("#studio-result");
  box.innerHTML = `
    <div class="card">
      <div class="card-head"><h3>${esc(c.title)}</h3><div class="row" style="gap:6px"><span class="pill ${c.difficulty}">${c.difficulty}</span><span class="pill neutral">${c.processed_by === "llm" ? "Azure OpenAI" : "Heuristic"}</span></div></div>
      <div class="analysis">
        <div><div class="label" style="margin-bottom:8px">Summary</div><div class="summary">${esc(c.summary)}</div></div>
        <div><div class="label" style="margin-bottom:8px">Key concepts</div><div class="row">${c.key_concepts.map((k) => `<span class="tag">${esc(k)}</span>`).join("") || '<span class="muted small">None found</span>'}</div></div>
        <div class="row" style="padding-top:6px;border-top:1px solid var(--line)">
          <span class="label">Generate</span>
          <select class="input" id="gen-n" style="width:auto">${[2, 3, 4, 5].map((n) => `<option ${n === 3 ? "selected" : ""}>${n}</option>`).join("")}</select>
          <span class="label">questions</span><span class="spacer"></span>
          <button class="btn" id="gen-go" data-busy="Generating & validating…">${ICONS.studio} Generate questions</button>
        </div>
        <div id="gen-result"></div>
      </div>
    </div>`;
  box.scrollIntoView({ behavior: "smooth", block: "start" });
  $("#gen-go").addEventListener("click", (e) =>
    withBusy(e.currentTarget, async () => {
      const r = await api(`/content/${c.id}/questions`, { method: "POST", body: { count: Number($("#gen-n").value) } });
      $("#gen-result").innerHTML = `
        <div class="row" style="margin-bottom:12px"><span class="pill good">${r.accepted.length} accepted</span><span class="pill bad">${r.rejected.length} rejected</span><span class="muted small">Generated by ${r.generated_by === "llm" ? "Azure OpenAI" : "heuristics"} · validated by rules${r.generated_by === "llm" ? " + LLM reviewer" : ""}</span></div>
        <div class="stack">
          ${r.accepted.map((q) => questionPreview(q)).join("")}
          ${r.rejected.map((x) => questionPreview(x.question, x.issues)).join("")}
        </div>`;
      toast(`${r.accepted.length} question${r.accepted.length === 1 ? "" : "s"} added to the question bank`, "success");
    }),
  );
}

function questionPreview(q, issues) {
  return `
    <div class="q-preview ${issues ? "rejected" : ""}">
      <div class="row" style="margin-bottom:6px">${issues ? '<span class="pill bad">Rejected</span>' : '<span class="pill good">Validated</span>'}<span class="pill ${q.difficulty}">${q.difficulty}</span></div>
      <div class="q">${esc(q.text)}</div>
      <ul>${q.options.map((o) => `<li class="${o === q.correct_answer ? "correct" : ""}">${esc(o)}</li>`).join("")}</ul>
      ${issues ? `<ul class="issues" style="display:block">${issues.map((i) => `<li style="background:none;padding:2px 0">${esc(i)}</li>`).join("")}</ul>` : ""}
    </div>`;
}

/* ===================== Question validator ===================== */

async function validator() {
  const el = setView(`
    <div class="page-head"><div><h1>Question Validator</h1><p>Check a multiple-choice question before it reaches students. Structural rules run first; with Azure OpenAI connected, an LLM reviewer also checks correctness, ambiguity, relevance and clarity.</p></div></div>
    <div class="grid split" style="align-items:start">
      <div class="card">
        <form id="val-form" class="stack" style="gap:16px">
          <div class="field"><label for="v-text">Question</label><input class="input" id="v-text" required value="Which gas do plants release during photosynthesis?"></div>
          <div class="field"><span class="label">Options — select the correct answer</span>
            <div class="stack" id="v-options" style="gap:8px"></div>
            <div><button type="button" class="btn ghost sm" id="v-add">${ICONS.plus} Add option</button></div></div>
          <div class="field"><label for="v-diff">Difficulty</label>
            <select class="input" id="v-diff"><option>easy</option><option selected>medium</option><option>hard</option></select></div>
          <div class="field"><label for="v-context">Source material (optional)</label>
            <textarea class="input" id="v-context" rows="4" placeholder="Paste the passage the question should be grounded in…"></textarea></div>
          <div class="row"><span class="spacer"></span><button class="btn gradient" data-busy="Validating…">${ICONS.validator} Validate question</button></div>
        </form>
      </div>
      <div id="val-result">${emptyState("validator", "No report yet", "Fill in a question and run the validator. Try duplicating an option or picking an answer that isn't listed to see the rules in action.")}</div>
    </div>`);

  const options = ["Oxygen", "Nitrogen", "Carbon dioxide", "Helium"];
  const addOption = (value = "", checked = false) => {
    const row = document.createElement("div");
    row.className = "option-row";
    const idx = $$(".option-row", el).length;
    row.innerHTML = `<input type="radio" name="correct" ${checked ? "checked" : ""} aria-label="Mark option ${LETTERS[idx]} correct">
      <input class="input" value="${esc(value)}" placeholder="Option ${LETTERS[idx] || ""}">
      <button type="button" class="btn ghost icon-only" aria-label="Remove option">${ICONS.x}</button>`;
    $("button", row).addEventListener("click", () => row.remove());
    $("#v-options").append(row);
  };
  options.forEach((o, i) => addOption(o, i === 0));
  $("#v-add").addEventListener("click", () => ($$(".option-row", el).length < 6 ? addOption() : toast("Maximum of 6 options", "error")));

  $("#val-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const rows = $$(".option-row", el);
    const values = rows.map((r) => $(".input", r).value);
    const correctRow = rows.find((r) => $("input[type=radio]", r).checked);
    if (!correctRow) return toast("Select the correct option", "error");
    withBusy(e.submitter, async () => {
      const report = await api("/questions/validate", {
        method: "POST",
        body: {
          text: $("#v-text").value,
          options: values,
          correct_answer: $(".input", correctRow).value || " ",
          difficulty: $("#v-diff").value,
          context: $("#v-context").value || null,
        },
      });
      renderValidation(report);
    });
  });
}

function renderValidation(r) {
  const review = r.llm_review;
  const checks = review
    ? [["Answer is correct", review.answer_is_correct], ["Unambiguous", review.is_unambiguous], ["Relevant to context", review.is_relevant], [`Clarity ${review.clarity_score}/5`, review.clarity_score >= 3]]
    : [];
  $("#val-result").innerHTML = `
    <div class="card stack" style="gap:16px">
      <div class="verdict ${r.is_valid ? "ok" : "no"}">
        <div class="big">${r.is_valid ? ICONS.check : ICONS.x}</div>
        <div><h3>${r.is_valid ? "Ready for students" : "Needs changes"}</h3><div class="small">Reviewed by ${r.reviewed_by === "rules+llm" ? "rules + Azure OpenAI reviewer" : "structural rules"}</div></div>
      </div>
      ${r.issues.length ? `<div><div class="label" style="margin-bottom:8px">Issues</div><div class="stack" style="gap:8px">${r.issues.map((i) => `<div class="check-item no">${ICONS.x}<span>${esc(i)}</span></div>`).join("")}</div></div>` : ""}
      ${checks.length ? `<div><div class="label" style="margin-bottom:8px">AI review</div><div class="checks">${checks.map(([label, ok]) => `<div class="check-item ${ok ? "ok" : "no"}">${ok ? ICONS.check : ICONS.x}${esc(label)}</div>`).join("")}</div>
        <p class="small muted" style="margin-top:10px">“${esc(review.feedback)}”</p></div>` : ""}
      ${!review && r.is_valid ? `<div class="checks">${["Options unique", "Answer present", "Clear length", "No 'all/none of the above'"].map((l) => `<div class="check-item ok">${ICONS.check}${l}</div>`).join("")}</div>` : ""}
      ${!review ? `<div class="callout">${ICONS.info}<span>Connect Azure OpenAI (set the <b>AZURE_OPENAI_*</b> environment variables) to add an LLM review of factual correctness and ambiguity.</span></div>` : ""}
    </div>`;
}

/* ===================== Boot ===================== */

async function boot() {
  renderNav();
  setTheme(currentTheme());
  $("#theme-toggle").addEventListener("click", () => setTheme(currentTheme() === "dark" ? "light" : "dark"));
  $("#new-student").addEventListener("click", newStudentModal);
  $("#student-select").addEventListener("change", (e) => selectStudent(Number(e.target.value)));
  $("#modal-close").addEventListener("click", closeModal);
  $("#modal").addEventListener("click", (e) => e.target.id === "modal" && closeModal());
  document.addEventListener("keydown", (e) => e.key === "Escape" && closeModal());
  window.addEventListener("hashchange", route);

  setView(loading(3));
  loadEngine();
  try {
    const [, topics] = await Promise.all([loadStudents(), api("/topics")]);
    state.topics = topics;
    route();
  } catch (err) {
    handleViewError(err);
  }
}

boot();
