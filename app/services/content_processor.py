"""Learning-content processing with LangChain: analysis and question generation.

Each operation runs a ``prompt | llm | parser`` chain against Azure OpenAI when one is
configured, and falls back to deterministic text heuristics when it isn't (or when the
model call / output parsing fails).
"""

import logging
import re
from collections import Counter
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.services.question_validator import QuestionDraft

logger = logging.getLogger(__name__)

Difficulty = Literal["easy", "medium", "hard"]

MAX_CONTENT_CHARS = 12_000
SUMMARY_SENTENCES = 2
MAX_SUMMARY_CHARS = 400

STOPWORDS = frozenset(
    """
    a about above after again also an and any are as at be because been before being
    below between both but by can could did do does doing down during each few for from
    further had has have having here how into its itself just more most much must only
    other over same should some such than that their them then there these they this
    those through very was were what when where which while who whom why will with
    within without would your often called known used uses using make makes made
    """.split()
)

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z-]+")


class ContentAnalysis(BaseModel):
    summary: str = Field(description="A 2-3 sentence, student-friendly summary.")
    key_concepts: list[str] = Field(description="3-8 key terms or concepts, most important first.")
    difficulty: Difficulty = Field(description="Reading/conceptual difficulty of the material.")


class GeneratedQuestionSet(BaseModel):
    questions: list[QuestionDraft]


_ANALYSIS_PARSER = PydanticOutputParser(pydantic_object=ContentAnalysis)
_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert curriculum designer. Analyse the learning material and "
            "respond with JSON only.\n{format_instructions}",
        ),
        ("human", "Subject: {subject}\nTopic: {topic}\n\nMaterial:\n{text}"),
    ]
).partial(format_instructions=_ANALYSIS_PARSER.get_format_instructions())

_QUESTIONS_PARSER = PydanticOutputParser(pydantic_object=GeneratedQuestionSet)
_QUESTIONS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You write high-quality multiple-choice questions for school students. Every "
            "question must be answerable from the material, have 4 distinct options, exactly "
            "one correct answer copied verbatim from the options, and a short explanation. "
            "Respond with JSON only.\n{format_instructions}",
        ),
        (
            "human",
            "Topic: {topic}\nTarget difficulty: {difficulty}\nNumber of questions: {count}\n"
            "Key concepts: {key_concepts}\n\nMaterial:\n{text}",
        ),
    ]
).partial(format_instructions=_QUESTIONS_PARSER.get_format_instructions())


# --- Heuristic fallbacks -----------------------------------------------------


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text.strip()) if s.strip()]


def extract_key_concepts(text: str, limit: int = 6) -> list[str]:
    words = (w.lower() for w in _WORD_RE.findall(text))
    counts = Counter(w for w in words if len(w) > 3 and w not in STOPWORDS)
    return [word for word, _ in counts.most_common(limit)]


def estimate_difficulty(text: str) -> Difficulty:
    words = _WORD_RE.findall(text)
    if not words:
        return "easy"
    avg_word_length = sum(map(len, words)) / len(words)
    avg_sentence_length = len(words) / max(len(split_sentences(text)), 1)
    score = avg_word_length * 0.6 + avg_sentence_length * 0.1
    if score < 4.5:
        return "easy"
    if score < 5.5:
        return "medium"
    return "hard"


def heuristic_analysis(text: str) -> ContentAnalysis:
    summary = " ".join(split_sentences(text)[:SUMMARY_SENTENCES])
    if len(summary) > MAX_SUMMARY_CHARS:
        summary = summary[: MAX_SUMMARY_CHARS - 3].rstrip() + "..."
    return ContentAnalysis(
        summary=summary,
        key_concepts=extract_key_concepts(text),
        difficulty=estimate_difficulty(text),
    )


def heuristic_questions(
    text: str, *, key_concepts: list[str], count: int, difficulty: Difficulty
) -> list[QuestionDraft]:
    """Build fill-in-the-blank questions from sentences that mention a key concept."""
    concepts = key_concepts or extract_key_concepts(text)
    questions: list[QuestionDraft] = []
    used_sentences: set[str] = set()

    for concept in concepts:
        if len(questions) >= count:
            break
        pattern = re.compile(rf"\b{re.escape(concept)}\b", re.IGNORECASE)
        sentence = next(
            (s for s in split_sentences(text) if pattern.search(s) and s not in used_sentences),
            None,
        )
        distractors = [c for c in concepts if c != concept][:3]
        if sentence is None or len(distractors) < 2:
            continue
        used_sentences.add(sentence)
        options = [concept, *distractors]
        # Rotate so the answer isn't always the first option.
        shift = len(questions) % len(options)
        options = options[shift:] + options[:shift]
        questions.append(
            QuestionDraft(
                text=f"Fill in the blank: {pattern.sub('_____', sentence, count=1)}",
                options=options,
                correct_answer=concept,
                explanation=f'From the material: "{sentence}"',
                difficulty=difficulty,
            )
        )
    return questions


# --- Public API --------------------------------------------------------------


def analyze_content(
    text: str, *, subject: str, topic: str, llm: BaseChatModel | None
) -> tuple[ContentAnalysis, str]:
    """Return the analysis and which engine produced it ("llm" or "heuristic")."""
    if llm is not None:
        try:
            chain = _ANALYSIS_PROMPT | llm | _ANALYSIS_PARSER
            result = chain.invoke(
                {"subject": subject, "topic": topic, "text": text[:MAX_CONTENT_CHARS]}
            )
            result.key_concepts = [c.strip() for c in result.key_concepts if c.strip()][:8]
            return result, "llm"
        except Exception:
            logger.warning("LLM content analysis failed; using heuristics", exc_info=True)
    return heuristic_analysis(text), "heuristic"


def generate_questions(
    text: str,
    *,
    topic: str,
    count: int,
    difficulty: Difficulty,
    key_concepts: list[str],
    llm: BaseChatModel | None,
) -> tuple[list[QuestionDraft], str]:
    """Return generated question drafts and which engine produced them."""
    if llm is not None:
        try:
            chain = _QUESTIONS_PROMPT | llm | _QUESTIONS_PARSER
            result = chain.invoke(
                {
                    "topic": topic,
                    "difficulty": difficulty,
                    "count": count,
                    "key_concepts": ", ".join(key_concepts) or "(not provided)",
                    "text": text[:MAX_CONTENT_CHARS],
                }
            )
            return result.questions[:count], "llm"
        except Exception:
            logger.warning("LLM question generation failed; using heuristics", exc_info=True)
    drafts = heuristic_questions(text, key_concepts=key_concepts, count=count, difficulty=difficulty)
    return drafts, "heuristic"
