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
  users: '<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/></svg>',
  class: '<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/></svg>',
  assign: '<svg viewBox="0 0 24 24"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4z"/></svg>',
  admin: '<svg viewBox="0 0 24 24"><path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/></svg>',
  topics: '<svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg>',
  eye: '<svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
  trash: '<svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>',
};

const STATUS = {
  gap: { label: "Learning gap", cls: "bad" },
  needs_assessment: { label: "Not assessed", cls: "neutral" },
  in_progress: { label: "In progress", cls: "warn" },
  mastered: { label: "Mastered", cls: "good" },
};

const ROLES = {
  student: {
    label: "Student",
    nav: [["dashboard", "Dashboard"], ["practice", "Practice"], ["homework", "Homework"], ["path", "Learning Path"]],
    note: "Practise, take quizzes and follow your learning path.",
  },
  teacher: {
    label: "Teacher",
    nav: [["class", "My Class"], ["assign", "Assign Homework"], ["studio", "Content Studio"], ["validator", "Validator"]],
    hidden: { student: "Student Insights" },
    note: "Track your class, spot gaps and assign work.",
  },
  admin: {
    label: "Admin",
    nav: [["admin", "Overview"], ["users", "Users"], ["topics", "Topics"], ["studio", "Content Studio"], ["validator", "Validator"]],
    hidden: { student: "Student Insights" },
    note: "Manage users, classes and the curriculum.",
  },
};

const state = {
  role: "student",
  personId: null,
  people: { student: [], teacher: [], admin: [] },
  topics: [],
  quiz: null,
  keyHandler: null,
};
const person = () => state.people[state.role].find((p) => p.id === state.personId);
const student = () => (state.role === "student" ? person() : null);
const studentById = (id) => state.people.student.find((s) => s.id === id);
const teacherName = (id) => state.people.teacher.find((t) => t.id === id)?.name ?? "Unassigned";
const topicName = (id) => state.topics.find((t) => t.id === id)?.name ?? `Topic ${id}`;
const initials = (name) => name.replace(/^(Ms|Mr|Mrs|Dr)\.?\s+/, "").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
// Student views read this; it's always the selected student in the student role.
Object.defineProperty(state, "studentId", { get: () => (state.role === "student" ? state.personId : null) });

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

function renderShell() {
  const role = ROLES[state.role];
  $("#nav").innerHTML = role.nav.map(([id, label]) => `<a href="#${id}" data-view="${id}">${ICONS[id]}<span>${label}</span></a>`).join("");
  $("#role-switch").innerHTML = Object.entries(ROLES)
    .map(([id, r]) => `<button role="tab" aria-selected="${id === state.role}" class="${id === state.role ? "on" : ""}" data-role="${id}">${r.label}</button>`)
    .join("");
  $("#role-note").innerHTML = `<span class="pill accent">${role.label} view</span><span>${role.note}</span>`;
  const people = state.people[state.role];
  $("#person-select").innerHTML = people.length
    ? people.map((p) => `<option value="${p.id}" ${p.id === state.personId ? "selected" : ""}>${esc(p.name)}</option>`).join("")
    : `<option>No ${role.label.toLowerCase()}s</option>`;
  const p = person();
  $("#avatar").textContent = p ? initials(p.name) : "?";
  $("#avatar").dataset.role = state.role;
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

async function loadPeople() {
  const [students, staff] = await Promise.all([api("/students?limit=200"), api("/staff")]);
  state.people = { student: students, teacher: staff.filter((s) => s.role === "teacher"), admin: staff.filter((s) => s.role === "admin") };
  pickPerson(Number(store.get(`person:${state.role}`)));
}

function pickPerson(preferredId) {
  const people = state.people[state.role];
  state.personId = people.some((p) => p.id === preferredId) ? preferredId : people[0]?.id ?? null;
  if (state.personId != null) store.set(`person:${state.role}`, String(state.personId));
  renderShell();
}

function selectRole(role, personId) {
  state.role = role;
  store.set("role", role);
  pickPerson(personId ?? Number(store.get(`person:${role}`)));
  const target = `#${ROLES[role].nav[0][0]}`;
  if (location.hash === target) route();
  else location.hash = target;
}

function selectPerson(id) {
  pickPerson(id);
  route();
}

// Lets a teacher or admin see exactly what a student sees.
function viewAsStudent(id) {
  selectRole("student", id);
}

/* ===================== Router ===================== */

const VIEWS = {
  dashboard, practice, homework, path: learningPath, studio, validator,
  class: classView, assign: assignView, student: studentInsights,
  admin: adminView, users: usersView, topics: topicsView,
};

function route() {
  stopQuizKeys();
  closeModal();
  const [name, arg] = location.hash.slice(1).split("/");
  const role = ROLES[state.role];
  const allowed = new Map([...role.nav, ...Object.entries(role.hidden || {})]);
  if (!allowed.has(name)) {
    location.replace(`#${role.nav[0][0]}`);
    if (!name) route(); // replace() on an empty hash doesn't fire hashchange
    return;
  }
  $$("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.view === name || (name === "student" && a.dataset.view === role.nav[0][0])));
  $("#page-title").textContent = allowed.get(name);
  if (state.personId == null) {
    const msg = state.role === "student" ? "No students yet" : `No ${role.label.toLowerCase()}s yet`;
    setView(emptyState("users", msg, "Switch to the Admin view to add people.", `<button class="btn" onclick="selectRole('admin')">Go to Admin</button>`));
    return;
  }
  VIEWS[name](arg).catch(handleViewError);
}

let recovering = false;

function handleViewError(err) {
  if (err.status === 404 && /Student|Staff/.test(err.message) && !recovering) {
    // Serverless storage can reset; reload people and fall back to someone who exists.
    recovering = true;
    loadPeople()
      .then(() => {
        if (location.hash.startsWith("#student/")) location.hash = `#${ROLES[state.role].nav[0][0]}`;
        else route();
      })
      .finally(() => setTimeout(() => (recovering = false), 500));
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
          <div class="stack">${report.gaps.length ? report.gaps.map((g) => gapCard(g)).join("") : emptyState("target", history.length ? "No gaps detected" : "Not assessed yet", history.length ? "Great work! Keep practising to reach mastery." : "Take the diagnostic to discover your gaps.")}</div>
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

// Students get a "practise now" button; teachers and admins assign homework instead.
function gapCard(g, assignTo = null) {
  const button = assignTo
    ? `<button class="btn sm" data-assign-topic="${g.topic_id}" data-assign-student="${assignTo}" data-busy="Assigning…">${ICONS.assign} Assign homework</button>`
    : `<button class="btn sm" data-practice-topic="${g.topic_id}" data-busy="Preparing…">${ICONS.practice} Practise this topic</button>`;
  return `
    <div class="gap-card ${g.severity}">
      <div class="row"><h4>${esc(g.topic_name)}</h4><span class="spacer"></span><span class="pill ${g.severity === "high" ? "bad" : "warn"}">${g.severity} priority</span></div>
      <p class="small muted">${esc(g.reason)}</p>
      <p class="action">💡 ${esc(g.recommended_action)}</p>
      <div>${button}</div>
    </div>`;
}

async function assignHomework(studentId, topicId = null, numQuestions = 5, dueInDays = 7) {
  return api("/homework/generate", {
    method: "POST",
    body: { student_id: studentId, topic_id: topicId, num_questions: numQuestions, due_in_days: dueInDays },
  });
}

function bindAssignButtons(root) {
  $$("[data-assign-topic]", root).forEach((btn) =>
    btn.addEventListener("click", () =>
      withBusy(btn, async () => {
        const hw = await assignHomework(Number(btn.dataset.assignStudent), Number(btn.dataset.assignTopic) || null);
        toast(`Assigned "${hw.title}" to ${studentById(hw.student_id)?.name ?? "student"}`, "success");
      }),
    ),
  );
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

/* ===================== Shared people helpers ===================== */

function avatar(name, size = 34) {
  return `<span class="avatar" style="width:${size}px;height:${size}px;font-size:${Math.round(size / 2.6)}px">${esc(initials(name))}</span>`;
}

function masteryTone(m) {
  return m == null ? "neutral" : m >= 0.85 ? "good" : m >= 0.6 ? "warn" : "bad";
}

function lastActive(iso) {
  return iso ? relativeTime(iso) : "Never";
}

/* ===================== Teacher: class overview ===================== */

async function classView() {
  setView(loading(3));
  const teacher = person();
  const report = await api(`/reports/class?teacher_id=${teacher.id}`);
  const attention = report.students
    .filter((s) => s.gap_topics.length || s.overall_mastery == null)
    .sort((a, b) => b.gap_topics.length - a.gap_topics.length || (a.overall_mastery ?? 2) - (b.overall_mastery ?? 2))
    .slice(0, 5);

  const el = setView(`
    <div class="page-head">
      <div><h1>${esc(teacher.name)}'s class</h1><p>${teacher.subject ? `${esc(teacher.subject)} · ` : ""}${report.student_count} students. Mastery and gaps update as soon as students submit quizzes and homework.</p></div>
      <a class="btn gradient" href="#assign">${ICONS.assign} Assign homework</a>
    </div>
    <section class="grid cols-4" style="margin-bottom:20px">
      ${statCard("accent", "users", report.student_count, "Students")}
      ${statCard("good", "chart", pct(report.average_mastery), "Class mastery")}
      ${statCard("bad", "alert", report.students_with_gaps, "Students with gaps")}
      ${statCard("warn", "practice", report.submissions, "Quizzes & homework done")}
    </section>
    <section class="grid split" style="margin-bottom:20px">
      <div class="card">
        <div class="card-head"><h3>Topic performance</h3><span class="muted small">Class average</span></div>
        <div class="mastery-list">${report.topics.map((t) => `
          <div class="mastery-item">
            <div class="top">
              <div><div class="name">${esc(t.topic_name)}</div><div class="sub">${esc(t.subject)} · ${t.assessed_students} assessed</div></div>
              <div class="row" style="gap:8px">${t.students_with_gap ? `<span class="pill bad">${t.students_with_gap} with gap</span>` : ""}<strong>${pct(t.average_mastery)}</strong></div>
            </div>
            <div class="bar ${masteryTone(t.average_mastery)}"><i data-w="${Math.round((t.average_mastery ?? 0) * 100)}%"></i><span class="target" style="left:60%"></span></div>
          </div>`).join("")}
        </div>
      </div>
      <div class="card">
        <div class="card-head"><h3>Needs attention</h3>${attention.length ? `<span class="pill bad">${attention.length}</span>` : ""}</div>
        <div class="list">${attention.map((s) => `
          <div class="list-item">
            ${avatar(s.name)}
            <div style="flex:1;min-width:0"><a href="#student/${s.id}" style="font-weight:600;color:var(--text)">${esc(s.name)}</a>
              <div class="small muted">${s.gap_topics.length ? `Gaps: ${s.gap_topics.map(esc).join(", ")}` : "Hasn't taken a quiz yet"}</div></div>
            <button class="btn sm soft" data-assign-topic="" data-assign-student="${s.id}" data-busy="…" title="Assign homework on their weakest topic">${ICONS.assign}</button>
          </div>`).join("") || emptyState("trophy", "Everyone is on track", "No student currently has a learning gap.")}
        </div>
      </div>
    </section>
    <div class="card">
      <div class="card-head"><h3>Mastery heatmap</h3><span class="muted small">Click a student for details</span></div>
      <div class="table-wrap">
        <table class="table heatmap">
          <thead><tr><th>Student</th>${report.topics.map((t) => `<th>${esc(t.topic_name)}</th>`).join("")}<th>Overall</th><th>Last active</th></tr></thead>
          <tbody>${report.students.map((s) => `
            <tr data-href="#student/${s.id}">
              <td><div class="row" style="flex-wrap:nowrap">${avatar(s.name, 30)}<span style="font-weight:600">${esc(s.name)}</span></div></td>
              ${s.topics.map((t) => `<td><span class="heat ${STATUS[t.status].cls}" title="${STATUS[t.status].label}">${pct(t.mastery)}</span></td>`).join("")}
              <td><strong class="score-badge ${masteryTone(s.overall_mastery)}">${pct(s.overall_mastery)}</strong></td>
              <td class="muted small">${lastActive(s.last_active)}</td>
            </tr>`).join("") || `<tr><td colspan="${report.topics.length + 3}" class="muted">No students in this class yet. An admin can assign students from the Users page.</td></tr>`}
          </tbody>
        </table>
      </div>
      <div class="row legend">${Object.values(STATUS).map((s) => `<span class="row" style="gap:6px"><span class="heat ${s.cls} dot"></span>${s.label}</span>`).join("")}</div>
    </div>`);

  $$("tr[data-href]", el).forEach((tr) => tr.addEventListener("click", () => (location.hash = tr.dataset.href)));
  bindAssignButtons(el);
  animateBars(el);
}

/* ===================== Teacher/Admin: student insights ===================== */

async function studentInsights(id) {
  setView(loading(3));
  const sid = Number(id);
  const [s, report, history] = await Promise.all([
    api(`/students/${sid}`),
    api(`/students/${sid}/learning-gaps`),
    api(`/students/${sid}/submissions?limit=8`),
  ]);
  const back = state.role === "teacher" ? ["#class", "My class"] : ["#users", "Users"];
  const lastSeen = history[0]?.submitted_at;

  const el = setView(`
    <a class="back-link" href="${back[0]}">${ICONS.arrowL} ${back[1]}</a>
    <div class="profile-head card">
      ${avatar(s.name, 64)}
      <div style="flex:1;min-width:200px">
        <h1 style="font-size:24px">${esc(s.name)}</h1>
        <div class="muted small">${esc(s.email)} · Grade ${s.grade_level} · Teacher: ${esc(teacherName(s.teacher_id))}</div>
      </div>
      <div class="row">
        <button class="btn ghost" id="view-as">${ICONS.eye} View as student</button>
        <button class="btn gradient" data-assign-topic="" data-assign-student="${s.id}" data-busy="Assigning…">${ICONS.assign} Assign homework</button>
      </div>
    </div>
    <section class="grid cols-4" style="margin:20px 0">
      ${statCard("accent", "chart", pct(report.overall_mastery), "Overall mastery")}
      ${statCard("bad", "alert", report.gaps.length, "Learning gaps")}
      ${statCard("warn", "practice", report.progress.reduce((n, p) => n + p.attempts, 0), "Questions answered")}
      ${statCard("good", "clock", lastActive(lastSeen), "Last active")}
    </section>
    <section class="grid split">
      <div class="card">
        <div class="card-head"><h3>Topic mastery</h3><span class="muted small">Target 60%</span></div>
        <div class="mastery-list">${report.progress.map(masteryRow).join("")}</div>
      </div>
      <div class="stack" style="gap:20px">
        <div class="card">
          <div class="card-head"><h3>Learning gaps</h3></div>
          <div class="stack">${report.gaps.map((g) => gapCard(g, s.id)).join("") || emptyState("target", history.length ? "No gaps" : "Not assessed yet", history.length ? "This student is on track." : "They haven't taken a quiz yet.")}</div>
        </div>
        <div class="card">
          <div class="card-head"><h3>Recent activity</h3></div>
          <div class="list">${history.map(activityRow).join("") || '<p class="muted small">No submissions yet.</p>'}</div>
        </div>
      </div>
    </section>`);

  $("#view-as", el).addEventListener("click", () => viewAsStudent(s.id));
  bindAssignButtons(el);
  animateBars(el);
}

/* ===================== Teacher: assign homework ===================== */

async function assignView() {
  setView(loading(2));
  const teacher = person();
  const [roster, topics] = await Promise.all([api(`/students?teacher_id=${teacher.id}&limit=200`), api("/topics")]);
  state.topics = topics;

  const el = setView(`
    <div class="page-head"><div><h1>Assign homework</h1><p>Send adaptive homework to several students at once. "Weakest topic" picks each student's most urgent topic individually.</p></div></div>
    <div class="grid split" style="align-items:start">
      <div class="card">
        <div class="stack" style="gap:20px">
          <div>
            <div class="row" style="margin-bottom:12px"><span class="label">Students</span><span class="spacer"></span><button class="btn sm ghost" id="toggle-all">Select none</button></div>
            <div class="row" id="student-chips">${roster.map((s) => `<button class="chip on" data-student="${s.id}"><span class="check">${ICONS.check}</span>${esc(s.name)}</button>`).join("") || '<p class="muted">No students in your class yet.</p>'}</div>
          </div>
          <div class="grid cols-2" style="gap:14px">
            <div class="field"><label for="as-topic">Topic</label>
              <select class="input" id="as-topic"><option value="">✨ Each student's weakest topic</option>${topics.map((t) => `<option value="${t.id}">${esc(t.name)}</option>`).join("")}</select></div>
            <div class="field"><label for="as-due">Due in</label>
              <select class="input" id="as-due"><option value="3">3 days</option><option value="7" selected>1 week</option><option value="14">2 weeks</option></select></div>
          </div>
          <div class="field"><label for="as-n">Questions per student: <b id="as-n-val">5</b></label><input type="range" id="as-n" min="1" max="10" value="5"></div>
          <div class="row"><span class="muted small" id="as-summary"></span><span class="spacer"></span>
            <button class="btn gradient lg" id="as-go" data-busy="Assigning…">${ICONS.assign} Assign</button></div>
        </div>
      </div>
      <div id="as-result">${emptyState("assign", "Nothing assigned yet", "Results for each student will appear here.")}</div>
    </div>`);

  const selected = () => $$(".chip.on", el).map((c) => Number(c.dataset.student));
  const summary = () => {
    $("#as-n-val").textContent = $("#as-n").value;
    $("#as-summary").textContent = `${selected().length} student${selected().length === 1 ? "" : "s"} selected`;
    $("#as-go").disabled = !selected().length;
    $("#toggle-all").textContent = selected().length ? "Select none" : "Select all";
  };
  $$(".chip", el).forEach((c) => c.addEventListener("click", () => { c.classList.toggle("on"); summary(); }));
  $("#toggle-all").addEventListener("click", () => {
    const on = !selected().length;
    $$(".chip", el).forEach((c) => c.classList.toggle("on", on));
    summary();
  });
  $("#as-n").addEventListener("input", summary);
  $("#as-go").addEventListener("click", (e) =>
    withBusy(e.currentTarget, async () => {
      const topicId = Number($("#as-topic").value) || null;
      const ids = selected();
      const results = await Promise.allSettled(
        ids.map((sid) => assignHomework(sid, topicId, Number($("#as-n").value), Number($("#as-due").value))),
      );
      const ok = results.filter((r) => r.status === "fulfilled").length;
      $("#as-result").innerHTML = `
        <div class="card">
          <div class="card-head"><h3>Assigned</h3><span class="pill good">${ok} of ${ids.length}</span></div>
          <div class="list">${results.map((r, i) => {
            const name = esc(studentById(ids[i])?.name ?? `Student ${ids[i]}`);
            return r.status === "fulfilled"
              ? `<div class="list-item"><div class="list-icon" style="color:var(--good)">${ICONS.check}</div><div><div style="font-weight:600">${name}</div><div class="small muted">${esc(r.value.title)} · ${r.value.questions.length} questions · due ${toDate(r.value.due_at).toLocaleDateString()}</div></div></div>`
              : `<div class="list-item"><div class="list-icon" style="color:var(--bad)">${ICONS.x}</div><div><div style="font-weight:600">${name}</div><div class="small" style="color:var(--bad)">${esc(r.reason.message)}</div></div></div>`;
          }).join("")}</div>
        </div>`;
      toast(`Homework assigned to ${ok} student${ok === 1 ? "" : "s"}`, ok ? "success" : "error");
    }),
  );
  summary();
}

/* ===================== Admin: overview ===================== */

async function adminView() {
  setView(loading(3));
  const [report] = await Promise.all([api("/reports/platform"), loadPeople()]);
  const c = report.counts;
  const unassigned = state.people.student.filter((s) => s.teacher_id == null).length;

  const el = setView(`
    <div class="page-head">
      <div><h1>Platform overview</h1><p>Everything happening across LearnPath AI: people, classes, curriculum and student activity.</p></div>
      <a class="btn gradient" href="#users">${ICONS.users} Manage users</a>
    </div>
    <section class="grid cols-4" style="margin-bottom:20px">
      ${statCard("accent", "users", c.students, `Students · ${c.teachers} teachers`)}
      ${statCard("good", "validator", c.validated_questions, `Validated questions of ${c.questions}`)}
      ${statCard("warn", "practice", c.submissions, `Submissions · ${c.homework} homework`)}
      ${statCard("bad", "chart", report.average_score == null ? "—" : `${Math.round(report.average_score)}%`, "Average score")}
    </section>
    <section class="grid split" style="margin-bottom:20px">
      <div class="card">
        <div class="card-head"><h3>Classes</h3>${unassigned ? `<span class="pill warn">${unassigned} unassigned</span>` : ""}</div>
        <div class="list">${state.people.teacher.map((t) => {
          const n = state.people.student.filter((s) => s.teacher_id === t.id).length;
          return `
            <div class="list-item">${avatar(t.name)}
              <div style="flex:1"><div style="font-weight:600">${esc(t.name)}</div><div class="small muted">${esc(t.subject || "Teacher")} · ${n} student${n === 1 ? "" : "s"}</div></div>
              <button class="btn sm soft" data-open-class="${t.id}">${ICONS.eye} Open class</button>
            </div>`;
        }).join("") || '<p class="muted small">No teachers yet.</p>'}</div>
      </div>
      <div class="card">
        <div class="card-head"><h3>Recent activity</h3></div>
        <div class="list">${report.recent_activity.map((a) => `
          <div class="list-item">
            <div class="list-icon">${ICONS[a.kind === "homework" ? "homework" : "practice"]}</div>
            <div style="flex:1"><a href="#student/${a.student_id}" style="font-weight:600;color:var(--text)">${esc(a.student_name)}</a>
              <div class="small muted">${a.kind === "homework" ? "Homework" : "Assessment"} · ${relativeTime(a.submitted_at)}</div></div>
            <span class="score-badge ${scoreClass(a.score)}">${Math.round(a.score)}%</span>
          </div>`).join("") || '<p class="muted small">No submissions yet.</p>'}</div>
      </div>
    </section>
    <div class="card">
      <div class="card-head"><h3>Curriculum inventory</h3><a class="btn sm ghost" href="#topics">Manage topics</a></div>
      <div class="table-wrap"><table class="table">
        <thead><tr><th>Topic</th><th>Subject</th><th>Materials</th><th>Validated questions</th></tr></thead>
        <tbody>${report.topics.map((t) => `<tr><td style="font-weight:600">${esc(t.topic_name)}</td><td>${esc(t.subject)}</td><td>${t.content_count}</td>
          <td>${t.question_count ? t.question_count : '<span class="pill warn">None yet</span>'}</td></tr>`).join("")}</tbody>
      </table></div>
    </div>`);
  $$("[data-open-class]", el).forEach((b) => b.addEventListener("click", () => selectRole("teacher", Number(b.dataset.openClass))));
}

/* ===================== Admin: users ===================== */

const USER_TABS = { students: "student", teachers: "teacher", admins: "admin" };

async function usersView(tab = "students") {
  if (!USER_TABS[tab]) tab = "students";
  setView(loading(2));
  await loadPeople();
  const rows = state.people[USER_TABS[tab]];
  const teacherOptions = (selected) =>
    `<option value="">Unassigned</option>${state.people.teacher.map((t) => `<option value="${t.id}" ${t.id === selected ? "selected" : ""}>${esc(t.name)}</option>`).join("")}`;

  const table = {
    students: () => `
      <thead><tr><th>Name</th><th>Email</th><th>Grade</th><th>Teacher</th><th></th></tr></thead>
      <tbody>${rows.map((s) => `
        <tr>
          <td><div class="row" style="flex-wrap:nowrap">${avatar(s.name, 30)}<a href="#student/${s.id}" style="font-weight:600;color:var(--text)">${esc(s.name)}</a></div></td>
          <td class="muted">${esc(s.email)}</td><td>${s.grade_level}</td>
          <td><select class="input compact" data-teacher-for="${s.id}">${teacherOptions(s.teacher_id)}</select></td>
          <td class="actions"><button class="btn sm ghost" data-view-as="${s.id}" title="View as this student">${ICONS.eye}</button>
            <button class="btn sm ghost danger" data-delete="students/${s.id}" data-name="${esc(s.name)}" title="Delete">${ICONS.trash}</button></td>
        </tr>`).join("")}</tbody>`,
    teachers: () => `
      <thead><tr><th>Name</th><th>Email</th><th>Subject</th><th>Students</th><th></th></tr></thead>
      <tbody>${rows.map((t) => `
        <tr>
          <td><div class="row" style="flex-wrap:nowrap">${avatar(t.name, 30)}<span style="font-weight:600">${esc(t.name)}</span></div></td>
          <td class="muted">${esc(t.email)}</td><td>${esc(t.subject || "—")}</td>
          <td>${state.people.student.filter((s) => s.teacher_id === t.id).length}</td>
          <td class="actions"><button class="btn sm ghost" data-open-class="${t.id}" title="Open class view">${ICONS.eye}</button>
            <button class="btn sm ghost danger" data-delete="staff/${t.id}" data-name="${esc(t.name)}" title="Delete">${ICONS.trash}</button></td>
        </tr>`).join("")}</tbody>`,
    admins: () => `
      <thead><tr><th>Name</th><th>Email</th><th></th></tr></thead>
      <tbody>${rows.map((a) => `
        <tr>
          <td><div class="row" style="flex-wrap:nowrap">${avatar(a.name, 30)}<span style="font-weight:600">${esc(a.name)}</span></div></td>
          <td class="muted">${esc(a.email)}</td>
          <td class="actions"><button class="btn sm ghost danger" data-delete="staff/${a.id}" data-name="${esc(a.name)}" title="Delete">${ICONS.trash}</button></td>
        </tr>`).join("")}</tbody>`,
  }[tab];

  const el = setView(`
    <div class="page-head">
      <div><h1>Users</h1><p>Add people, assign students to teachers, and remove accounts.</p></div>
      <button class="btn gradient" id="add-user">${ICONS.plus} Add user</button>
    </div>
    <div class="tabs">${Object.entries(USER_TABS).map(([id, role]) => `<a href="#users/${id}" class="${id === tab ? "on" : ""}">${id[0].toUpperCase() + id.slice(1)} <span class="count">${state.people[role].length}</span></a>`).join("")}</div>
    <div class="card" style="padding:8px 8px 4px">
      <div class="table-wrap"><table class="table">${table()}</table></div>
      ${rows.length ? "" : emptyState("users", `No ${tab} yet`, "Use “Add user” to create one.")}
    </div>`);

  $("#add-user").addEventListener("click", () => addUserModal(USER_TABS[tab]));
  $$("[data-teacher-for]", el).forEach((sel) =>
    sel.addEventListener("change", async () => {
      try {
        await api(`/students/${sel.dataset.teacherFor}`, { method: "PATCH", body: { teacher_id: Number(sel.value) || null } });
        toast(sel.value ? `Moved to ${teacherName(Number(sel.value))}'s class` : "Student unassigned", "success");
      } catch (err) {
        toast(err.message, "error");
      }
    }),
  );
  $$("[data-view-as]", el).forEach((b) => b.addEventListener("click", () => viewAsStudent(Number(b.dataset.viewAs))));
  $$("[data-open-class]", el).forEach((b) => b.addEventListener("click", () => selectRole("teacher", Number(b.dataset.openClass))));
  $$("[data-delete]", el).forEach((b) =>
    b.addEventListener("click", async () => {
      const extra = b.dataset.delete.startsWith("students") ? " Their quiz history and homework will be deleted too." : "";
      if (!confirm(`Delete ${b.dataset.name}?${extra}`)) return;
      try {
        await api(`/${b.dataset.delete}`, { method: "DELETE" });
        toast(`${b.dataset.name} deleted`, "success");
        usersView(tab).catch(handleViewError);
      } catch (err) {
        toast(err.message, "error");
      }
    }),
  );
}

function addUserModal(defaultRole = "student") {
  openModal(`
    <h2>Add a user</h2>
    <p class="muted" style="margin-bottom:20px">Students get a mastery profile and learning path. Teachers get a class view.</p>
    <form id="user-form" class="stack">
      <div class="field"><label for="u-role">Role</label>
        <select class="input" id="u-role">${Object.entries(ROLES).map(([id, r]) => `<option value="${id}" ${id === defaultRole ? "selected" : ""}>${r.label}</option>`).join("")}</select></div>
      <div class="field"><label for="u-name">Full name</label><input class="input" id="u-name" required maxlength="120" placeholder="e.g. Meera Iyer"></div>
      <div class="field"><label for="u-email">Email</label><input class="input" id="u-email" type="email" required placeholder="meera@school.edu"></div>
      <div class="grid cols-2" style="gap:12px" data-for="student">
        <div class="field"><label for="u-grade">Grade</label>
          <select class="input" id="u-grade">${Array.from({ length: 12 }, (_, i) => `<option ${i === 6 ? "selected" : ""}>${i + 1}</option>`).join("")}</select></div>
        <div class="field"><label for="u-teacher">Teacher</label>
          <select class="input" id="u-teacher"><option value="">Unassigned</option>${state.people.teacher.map((t) => `<option value="${t.id}">${esc(t.name)}</option>`).join("")}</select></div>
      </div>
      <div class="field" data-for="teacher"><label for="u-subject">Subject</label><input class="input" id="u-subject" maxlength="80" placeholder="e.g. Mathematics"></div>
      <button class="btn gradient lg" data-busy="Creating…">Create user</button>
    </form>`);
  const sync = () => $$("[data-for]").forEach((el) => el.classList.toggle("hidden", el.dataset.for !== $("#u-role").value));
  $("#u-role").addEventListener("change", sync);
  sync();
  $("#user-form").addEventListener("submit", (e) => {
    e.preventDefault();
    withBusy(e.submitter, async () => {
      const role = $("#u-role").value;
      const base = { name: $("#u-name").value.trim(), email: $("#u-email").value.trim() };
      const created = role === "student"
        ? await api("/students", { method: "POST", body: { ...base, grade_level: Number($("#u-grade").value), teacher_id: Number($("#u-teacher").value) || null } })
        : await api("/staff", { method: "POST", body: { ...base, role, subject: $("#u-subject").value.trim() } });
      closeModal();
      toast(`${created.name} added as ${ROLES[role].label.toLowerCase()}`, "success");
      const tab = Object.keys(USER_TABS).find((k) => USER_TABS[k] === role);
      if (location.hash === `#users/${tab}`) route();
      else location.hash = `#users/${tab}`;
    });
  });
}

/* ===================== Admin: topics ===================== */

async function topicsView() {
  setView(loading(2));
  const report = await api("/reports/platform");
  const el = setView(`
    <div class="page-head"><div><h1>Topics</h1><p>The curriculum every quiz, homework and learning path is built on. Add material and questions in the Content Studio.</p></div></div>
    <div class="grid split" style="align-items:start">
      <div class="card" style="padding:8px 8px 4px">
        <div class="table-wrap"><table class="table">
          <thead><tr><th>Topic</th><th>Subject</th><th>Materials</th><th>Questions</th><th></th></tr></thead>
          <tbody>${report.topics.map((t) => `
            <tr><td style="font-weight:600">${esc(t.topic_name)}</td><td>${esc(t.subject)}</td><td>${t.content_count}</td>
              <td>${t.question_count || '<span class="pill warn">0</span>'}</td>
              <td class="actions"><a class="btn sm soft" href="#studio">${ICONS.studio} Add material</a></td></tr>`).join("")}
          </tbody>
        </table></div>
      </div>
      <div class="card">
        <div class="card-head"><h3>New topic</h3></div>
        <form id="topic-form" class="stack" style="gap:14px">
          <div class="field"><label for="tp-subject">Subject</label><input class="input" id="tp-subject" required maxlength="80" placeholder="e.g. Science"></div>
          <div class="field"><label for="tp-name">Topic name</label><input class="input" id="tp-name" required maxlength="120" placeholder="e.g. The Water Cycle"></div>
          <div class="field"><label for="tp-desc">Description</label><textarea class="input" id="tp-desc" rows="3" style="min-height:80px" placeholder="What students will learn"></textarea></div>
          <button class="btn gradient" data-busy="Adding…">${ICONS.plus} Add topic</button>
        </form>
      </div>
    </div>`);
  $("#topic-form", el).addEventListener("submit", (e) => {
    e.preventDefault();
    withBusy(e.submitter, async () => {
      const topic = await api("/topics", {
        method: "POST",
        body: { subject: $("#tp-subject").value.trim(), name: $("#tp-name").value.trim(), description: $("#tp-desc").value.trim() },
      });
      state.topics.push(topic);
      toast(`Topic "${topic.name}" added`, "success");
      topicsView().catch(handleViewError);
    });
  });
}

/* ===================== Boot ===================== */

async function boot() {
  state.role = ROLES[store.get("role")] ? store.get("role") : "student";
  renderShell();
  setTheme(currentTheme());
  $("#theme-toggle").addEventListener("click", () => setTheme(currentTheme() === "dark" ? "light" : "dark"));
  $("#role-switch").addEventListener("click", (e) => e.target.dataset.role && selectRole(e.target.dataset.role));
  $("#person-select").addEventListener("change", (e) => selectPerson(Number(e.target.value)));
  $("#modal-close").addEventListener("click", closeModal);
  $("#modal").addEventListener("click", (e) => e.target.id === "modal" && closeModal());
  document.addEventListener("keydown", (e) => e.key === "Escape" && closeModal());
  window.addEventListener("hashchange", route);

  setView(loading(3));
  loadEngine();
  try {
    const [, topics] = await Promise.all([loadPeople(), api("/topics")]);
    state.topics = topics;
    route();
  } catch (err) {
    handleViewError(err);
  }
}

boot();
