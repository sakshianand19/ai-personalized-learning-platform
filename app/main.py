import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app import __version__
from app.config import get_settings
from app.database import init_db
from app.routers import assessments, content, homework, questions, students, topics
from app.services.llm import llm_provider_name

logging.basicConfig(level=logging.INFO)

API_PREFIX = "/api/v1"

DESCRIPTION = """
Backend for a personalised learning platform.

* **Content processing** – summaries, key concepts and difficulty via Azure OpenAI + LangChain
* **Question generation & validation** – rule checks plus an LLM reviewer
* **Assessments & homework** – adaptive homework that targets each student's weakest topic
* **Learning-gap identification** – difficulty-weighted, smoothed per-topic mastery
* **Learning paths** – ordered study plans with level-matched content

Without Azure OpenAI credentials, the AI features fall back to deterministic heuristics.
"""


def create_app() -> FastAPI:
    settings = get_settings()
    # Runs at import rather than in a lifespan hook so serverless cold starts are covered too.
    init_db(seed=settings.seed_demo_data)

    app = FastAPI(title=settings.app_name, version=__version__, description=DESCRIPTION)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    for router in (students.router, topics.router, content.router, questions.router,
                   assessments.router, homework.router):
        app.include_router(router, prefix=API_PREFIX)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "llm_provider": llm_provider_name()}

    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    def index() -> str:
        return LANDING_PAGE.replace("{{provider}}", llm_provider_name())

    return app


LANDING_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Personalized Learning API</title>
<style>
  :root { --bg:#f7f7f5; --fg:#1d1d1b; --muted:#6b6b66; --card:#fff; --line:#e4e4df; --accent:#2f6fde; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#141413; --fg:#ecece8; --muted:#a3a39c; --card:#1e1e1c; --line:#33332f; --accent:#7aa5f5; }
  }
  * { box-sizing:border-box }
  body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 system-ui, sans-serif; }
  main { max-width:760px; margin:0 auto; padding:48px 16px; }
  h1 { font-size:1.8rem; margin:0 0 8px } p { color:var(--muted); margin:0 0 24px }
  .badge { display:inline-block; font-size:.8rem; padding:2px 10px; border:1px solid var(--line); border-radius:99px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:20px; margin-bottom:16px; }
  code { font-size:.9rem } ul { margin:0; padding-left:20px } li { margin:4px 0 }
  a.button { display:inline-block; background:var(--accent); color:#fff; padding:10px 18px; border-radius:8px; text-decoration:none; margin-right:8px; }
</style>
</head>
<body><main>
  <span class="badge">AI engine: {{provider}}</span>
  <h1>AI-Powered Personalized Learning Platform</h1>
  <p>FastAPI backend for personalised learning, homework, assessments and learning-gap identification,
     using Azure OpenAI through LangChain.</p>
  <div class="card">
    <a class="button" href="/docs">Open API docs</a><a class="button" href="/redoc">ReDoc</a>
  </div>
  <div class="card"><strong>Try it</strong>
    <ul>
      <li><code>GET /api/v1/topics</code> – seeded demo curriculum</li>
      <li><code>POST /api/v1/assessments</code> – build an assessment from topics</li>
      <li><code>POST /api/v1/assessments/{id}/submit</code> – grade answers, update mastery</li>
      <li><code>GET /api/v1/students/1/learning-gaps</code> – weak topics with recommended actions</li>
      <li><code>POST /api/v1/homework/generate</code> – adaptive homework for the weakest topic</li>
      <li><code>POST /api/v1/content/{id}/questions</code> – generate &amp; validate questions</li>
    </ul>
  </div>
</main></body></html>
"""

app = create_app()
