from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Difficulty = Literal["easy", "medium", "hard"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Students & topics -------------------------------------------------------


EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
Role = Literal["admin", "teacher"]


Password = Field(min_length=8, max_length=128)


class StaffBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    role: Role
    subject: str = Field(default="", max_length=80)


class StaffCreate(StaffBase):
    password: str = Password


class StaffRead(ORMModel, StaffBase):
    id: int
    created_at: datetime


class StudentBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    grade_level: int = Field(ge=1, le=12)
    teacher_id: int | None = None


class StudentCreate(StudentBase):
    password: str = Password


class StudentUpdate(BaseModel):
    """Partial update; send ``teacher_id: null`` to unassign a student from their teacher."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    grade_level: int | None = Field(default=None, ge=1, le=12)
    teacher_id: int | None = None


class StudentRead(ORMModel, StudentBase):
    id: int
    created_at: datetime


# --- Auth ------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """The account's role decides what the user can do; it isn't chosen at sign-in."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    password: str = Password
    role: Literal["admin", "teacher", "student"]
    grade_level: int | None = Field(default=None, ge=1, le=12, description="Required for students.")
    subject: str = Field(default="", max_length=80, description="Optional, for teachers.")

    @model_validator(mode="after")
    def _student_needs_grade(self) -> "SignupRequest":
        if self.role == "student" and self.grade_level is None:
            raise ValueError("Students must choose a grade.")
        return self


class UserInfo(BaseModel):
    id: int
    name: str
    email: str
    role: Literal["admin", "teacher", "student"]
    subject: str = ""


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserInfo


class TopicCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class TopicRead(ORMModel, TopicCreate):
    id: int
    question_count: int = Field(default=0, description="Validated questions available for quizzes.")


# --- Content -----------------------------------------------------------------


class ContentCreate(BaseModel):
    topic_id: int
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=20, description="Raw learning material to process.")


class ContentRead(ORMModel):
    id: int
    topic_id: int
    title: str
    body: str
    summary: str
    key_concepts: list[str]
    difficulty: Difficulty
    processed_by: str
    created_at: datetime


class ContentSummary(ORMModel):
    id: int
    title: str
    difficulty: Difficulty
    summary: str


# --- Questions ---------------------------------------------------------------


class QuestionBase(BaseModel):
    text: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_answer: str = Field(min_length=1, max_length=500)
    explanation: str = ""
    difficulty: Difficulty = "medium"


class QuestionCreate(QuestionBase):
    topic_id: int
    content_id: int | None = None


class QuestionRead(ORMModel, QuestionBase):
    id: int
    topic_id: int
    content_id: int | None
    is_validated: bool
    validation_notes: list[str]


class QuestionPublic(ORMModel):
    """A question as shown to a student: no answer key."""

    id: int
    topic_id: int
    text: str
    options: list[str]
    difficulty: Difficulty


class QuestionValidateRequest(QuestionBase):
    context: str | None = Field(
        default=None, description="Optional source material the question should be grounded in."
    )


class ValidationReport(BaseModel):
    is_valid: bool
    issues: list[str]
    reviewed_by: str
    llm_review: dict[str, Any] | None = None


class GenerateQuestionsRequest(BaseModel):
    count: int = Field(default=3, ge=1, le=10)
    difficulty: Difficulty | None = None


class RejectedQuestion(BaseModel):
    question: QuestionBase
    issues: list[str]


class GenerateQuestionsResponse(BaseModel):
    generated_by: str
    accepted: list[QuestionRead]
    rejected: list[RejectedQuestion]


# --- Submissions -------------------------------------------------------------


class AnswerIn(BaseModel):
    question_id: int
    answer: str = Field(max_length=500)


class AssessmentSubmit(BaseModel):
    student_id: int
    answers: list[AnswerIn] = Field(min_length=1)


class HomeworkSubmit(BaseModel):
    answers: list[AnswerIn] = Field(min_length=1)


class ResponseRead(BaseModel):
    question_id: int
    answer: str
    is_correct: bool
    correct_answer: str
    explanation: str


class SubmissionSummary(ORMModel):
    id: int
    assessment_id: int | None
    homework_id: int | None
    correct: int
    total: int
    score: float
    submitted_at: datetime


class SubmissionRead(BaseModel):
    id: int
    student_id: int
    correct: int
    total: int
    score: float
    submitted_at: datetime
    responses: list[ResponseRead]


# --- Assessments & homework --------------------------------------------------


class AssessmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    question_ids: list[int] | None = None
    topic_ids: list[int] | None = None
    questions_per_topic: int = Field(default=3, ge=1, le=20)

    @model_validator(mode="after")
    def _require_source(self) -> "AssessmentCreate":
        if not self.question_ids and not self.topic_ids:
            raise ValueError("Provide question_ids or topic_ids.")
        return self


class AssessmentRead(ORMModel):
    id: int
    title: str
    created_at: datetime
    questions: list[QuestionPublic]


class HomeworkGenerate(BaseModel):
    student_id: int
    topic_id: int | None = Field(
        default=None, description="Leave empty to target the student's weakest topic."
    )
    num_questions: int = Field(default=5, ge=1, le=20)
    due_in_days: int | None = Field(default=7, ge=0, le=60)


class HomeworkRead(ORMModel):
    id: int
    student_id: int
    topic_id: int
    title: str
    status: Literal["assigned", "completed"]
    due_at: datetime | None
    created_at: datetime
    completed_at: datetime | None
    questions: list[QuestionPublic]


# --- Learning insights -------------------------------------------------------

TopicStatus = Literal["gap", "needs_assessment", "in_progress", "mastered"]


class TopicProgress(BaseModel):
    topic_id: int
    topic_name: str
    subject: str
    attempts: int
    correct: int
    mastery: float | None
    status: TopicStatus


class LearningGapRead(TopicProgress):
    severity: Literal["high", "medium"]
    reason: str
    recommended_action: str


class GapReport(BaseModel):
    student_id: int
    overall_mastery: float | None
    gaps: list[LearningGapRead]
    progress: list[TopicProgress]


class StudentTopicMastery(BaseModel):
    topic_id: int
    mastery: float | None
    status: TopicStatus


class ClassStudent(BaseModel):
    id: int
    name: str
    email: str
    grade_level: int
    overall_mastery: float | None
    gap_topics: list[str]
    submissions: int
    last_active: datetime | None
    topics: list[StudentTopicMastery]


class ClassTopic(BaseModel):
    topic_id: int
    topic_name: str
    subject: str
    average_mastery: float | None
    assessed_students: int
    students_with_gap: int


class ClassReport(BaseModel):
    teacher_id: int | None
    student_count: int
    average_mastery: float | None
    students_with_gaps: int
    submissions: int
    topics: list[ClassTopic]
    students: list[ClassStudent]


class PlatformCounts(BaseModel):
    students: int
    teachers: int
    admins: int
    topics: int
    content: int
    questions: int
    validated_questions: int
    assessments: int
    homework: int
    submissions: int


class TopicInventory(BaseModel):
    topic_id: int
    topic_name: str
    subject: str
    content_count: int
    question_count: int


class ActivityItem(BaseModel):
    submission_id: int
    student_id: int
    student_name: str
    kind: Literal["assessment", "homework"]
    score: float
    submitted_at: datetime


class PlatformReport(BaseModel):
    counts: PlatformCounts
    average_score: float | None
    topics: list[TopicInventory]
    recent_activity: list[ActivityItem]


class LearningPathStep(BaseModel):
    order: int
    topic_id: int
    topic_name: str
    subject: str
    status: TopicStatus
    mastery: float | None
    target_difficulty: Difficulty
    recommended_content: list[ContentSummary]


class LearningPath(BaseModel):
    student_id: int
    steps: list[LearningPathStep]
