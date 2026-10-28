import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import DEV_SECRET_KEY, get_settings
from app.database import init_db
from app.routers import assessments, auth, content, homework, questions, reports, staff, students, topics
from app.services.llm import llm_provider_name

logging.basicConfig(level=logging.INFO)

API_PREFIX = "/api/v1"
STATIC_DIR = Path(__file__).parent / "static"

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
    if settings.secret_key == DEV_SECRET_KEY:
        logging.getLogger(__name__).warning(
            "SECRET_KEY is not set: session tokens use a public development key. "
            "Set SECRET_KEY to a long random value before real use."
        )
    # Runs at import rather than in a lifespan hook so serverless cold starts are covered too.
    init_db(seed=settings.seed_demo_data)

    app = FastAPI(title=settings.app_name, version=__version__, description=DESCRIPTION)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    for router in (auth.router, students.router, topics.router, content.router, questions.router,
                   assessments.router, homework.router, staff.router, reports.router):
        app.include_router(router, prefix=API_PREFIX)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str | bool]:
        return {
            "status": "ok",
            "version": __version__,
            "llm_provider": llm_provider_name(),
            # Lets the sign-up form show the admin option; never reveals the code itself.
            "admin_signup": get_settings().admin_signup_enabled,
        }

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
