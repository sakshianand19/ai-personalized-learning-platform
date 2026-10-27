# AI-Powered Personalized Learning Platform

**Python · FastAPI · Azure OpenAI · LangChain · SQLAlchemy · Pytest**

A backend for personalised learning: it processes learning material with Azure OpenAI through
LangChain, generates and validates assessment questions, runs assessments and adaptive homework,
and identifies each student's learning gaps to build a personalised study path.

## Features

| Area | What it does |
| --- | --- |
| **Content processing** | `prompt \| AzureChatOpenAI \| PydanticOutputParser` chain produces a summary, key concepts and a difficulty rating for uploaded material. |
| **Question generation** | LangChain chain generates multiple-choice questions grounded in the material. |
| **Question validation** | Deterministic rules (unique options, answer key present, etc.) plus an LLM reviewer that checks correctness, ambiguity, relevance and clarity. Only questions that pass are stored. |
| **Assessments** | Build from question ids or topics; answer keys are hidden from students; submissions are graded and feed mastery. |
| **Adaptive homework** | Targets the student's weakest topic, picks questions at the right difficulty and skips ones already answered correctly. |
| **Learning-gap identification** | Difficulty-weighted, Beta-smoothed per-topic mastery → `gap` / `needs_assessment` / `in_progress` / `mastered`, with severity and a recommended action. |
| **Learning path** | Orders topics by urgency and recommends level-matched content for each. |

Without Azure OpenAI credentials every AI feature falls back to deterministic heuristics, so the
API (and the live demo) works out of the box. If a model call fails or returns malformed output,
the service logs it and falls back the same way.

## Architecture

```
app/
├── main.py              FastAPI app, routers, landing page, /health
├── config.py            Settings from environment / .env (pydantic-settings)
├── database.py          SQLAlchemy engine/session, table creation, demo seeding
├── models.py            ORM models (students, topics, content, questions, assessments,
│                        homework, submissions, responses, topic mastery)
├── schemas.py           Pydantic request/response models
├── routers/             students · topics · content · questions · assessments · homework
└── services/
    ├── llm.py                 Azure OpenAI chat model (LangChain) as a FastAPI dependency
    ├── content_processor.py   LangChain chains for analysis + question generation
    ├── question_validator.py  Rule checks + LLM review chain
    ├── grading.py             Grading and incremental mastery updates
    ├── gap_analyzer.py        Learning-gap identification
    └── personalization.py     Learning paths and adaptive homework selection
tests/                   Unit + integration tests (LLM replaced by LangChain fake models)
```

**Database efficiency:** composite index on `(topic_id, is_validated)`, `selectinload` for
assessment/homework questions, a single batched query for mastery updates and for learning-path
content (no N+1 queries).

## API overview

All endpoints are under `/api/v1`; interactive docs at `/docs`.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` / `GET` | `/students` | Create / list students |
| `GET` | `/students/{id}/learning-gaps` | Gap report with severity and recommended actions |
| `GET` | `/students/{id}/learning-path` | Personalised ordered study plan |
| `POST` / `GET` | `/topics` | Manage curriculum topics |
| `POST` | `/content` | Upload material → AI summary, key concepts, difficulty |
| `POST` | `/content/{id}/questions` | Generate + validate questions from material |
| `POST` | `/questions/validate` | Validate a question without saving it |
| `POST` / `GET` | `/questions` | Create (validated) / list questions |
| `POST` | `/assessments` | Build an assessment from questions or topics |
| `POST` | `/assessments/{id}/submit` | Grade answers and update mastery |
| `POST` | `/homework/generate` | Adaptive homework for the weakest (or a given) topic |
| `POST` | `/homework/{id}/submit` | Grade homework |

### Example flow

```bash
# 1. Diagnostic assessment across the seeded topics
curl -X POST localhost:8000/api/v1/assessments -H "Content-Type: application/json" \
  -d '{"title": "Diagnostic", "topic_ids": [1, 2, 3]}'

# 2. Submit answers for the demo student
curl -X POST localhost:8000/api/v1/assessments/1/submit -H "Content-Type: application/json" \
  -d '{"student_id": 1, "answers": [{"question_id": 1, "answer": "Chlorophyll"}]}'

# 3. See the learning gaps, then assign adaptive homework
curl localhost:8000/api/v1/students/1/learning-gaps
curl -X POST localhost:8000/api/v1/homework/generate -H "Content-Type: application/json" \
  -d '{"student_id": 1}'
```

## Running locally

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # optional: add Azure OpenAI credentials
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `AZURE_OPENAI_ENDPOINT` | – | e.g. `https://my-resource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | – | Azure OpenAI key |
| `AZURE_OPENAI_DEPLOYMENT` | – | Chat model deployment name |
| `AZURE_OPENAI_API_VERSION` | `2024-10-21` | API version |
| `DATABASE_URL` | SQLite (`/tmp` on Vercel) | Any SQLAlchemy URL; `postgres://` URLs are supported |
| `SEED_DEMO_DATA` | `true` | Seed demo topics, content, questions and a student |
| `MASTERY_THRESHOLD` | `0.6` | Mastery below this is a learning gap |
| `MIN_ATTEMPTS_FOR_GAP` | `2` | Answers needed before a topic can be judged |

## Testing

```bash
pytest
```

47 unit and integration tests cover the validation rules, content heuristics, LangChain chains
(using `FakeListChatModel` with canned JSON, including malformed-output fallbacks), mastery maths,
gap classification and full API flows against an in-memory database. GitHub Actions runs them on
every push.

## Deploying to Vercel

Live demo: https://ai-personalized-learning-platform-nu.vercel.app (API docs at `/docs`).

Vercel detects FastAPI automatically from `app/main.py`; no extra configuration is needed.

1. Import the GitHub repo at [vercel.com/new](https://vercel.com/new) (no build settings needed).
2. Optionally add the Azure OpenAI variables under **Settings → Environment Variables**.
3. For persistent data, set `DATABASE_URL` to a hosted Postgres database. Without it the app uses
   SQLite in `/tmp`, which resets on cold starts (fine for a demo: it re-seeds automatically).
