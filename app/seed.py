"""Demo data so a fresh deployment has topics, content and validated questions to explore."""

from sqlalchemy.orm import Session

from app.models import LearningContent, Question, Student, Topic
from app.services.content_processor import heuristic_analysis

DEMO_CURRICULUM = [
    {
        "subject": "Science",
        "name": "Photosynthesis",
        "description": "How plants make food from light, water and carbon dioxide.",
        "content": (
            "Photosynthesis is the process plants use to make their own food. It happens "
            "inside chloroplasts, which contain a green pigment called chlorophyll. "
            "Chlorophyll absorbs sunlight and uses its energy to turn water and carbon "
            "dioxide into glucose. Oxygen is released as a by-product of photosynthesis. "
            "Plants take in carbon dioxide through tiny pores in their leaves called stomata."
        ),
        "questions": [
            ("Which pigment absorbs sunlight during photosynthesis?",
             ["Chlorophyll", "Haemoglobin", "Melanin", "Keratin"], "Chlorophyll", "easy"),
            ("Which gas is released as a by-product of photosynthesis?",
             ["Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"], "Oxygen", "easy"),
            ("Through which structures do leaves take in carbon dioxide?",
             ["Stomata", "Roots", "Xylem", "Petals"], "Stomata", "medium"),
            ("In which organelle does photosynthesis take place?",
             ["Chloroplast", "Mitochondrion", "Nucleus", "Ribosome"], "Chloroplast", "medium"),
        ],
    },
    {
        "subject": "Mathematics",
        "name": "Fractions",
        "description": "Equivalent fractions, simplifying and adding fractions.",
        "content": (
            "A fraction represents part of a whole. The top number is the numerator and the "
            "bottom number is the denominator. Equivalent fractions name the same amount, "
            "for example 1/2 and 2/4. To add fractions with different denominators, first "
            "rewrite them with a common denominator. A fraction is in simplest form when the "
            "numerator and denominator share no common factor other than 1."
        ),
        "questions": [
            ("What is 1/4 + 1/4 in simplest form?", ["1/2", "2/8", "1/8", "2/4"], "1/2", "easy"),
            ("Which fraction is equivalent to 3/6?", ["1/2", "1/3", "3/3", "2/3"], "1/2", "easy"),
            ("What is 1/3 + 1/6?", ["1/2", "2/9", "1/9", "2/6"], "1/2", "medium"),
            ("What is 5/12 expressed with denominator 36?",
             ["15/36", "10/36", "5/36", "12/36"], "15/36", "hard"),
        ],
    },
    {
        "subject": "Mathematics",
        "name": "Linear Equations",
        "description": "Solving one-variable linear equations.",
        "content": (
            "A linear equation in one variable can be written as ax + b = c. To solve it, "
            "isolate the variable by performing the same inverse operation on both sides. "
            "First undo addition or subtraction, then undo multiplication or division. "
            "Always check a solution by substituting it back into the original equation."
        ),
        "questions": [
            ("Solve for x: x + 5 = 12", ["7", "17", "5", "12"], "7", "easy"),
            ("Solve for x: 3x = 21", ["7", "18", "24", "63"], "7", "easy"),
            ("Solve for x: 2x + 3 = 11", ["4", "7", "5", "8"], "4", "medium"),
            ("Solve for x: 5x - 7 = 3x + 9", ["8", "1", "2", "16"], "8", "hard"),
        ],
    },
]


def seed_demo_data(db: Session) -> None:
    for item in DEMO_CURRICULUM:
        topic = Topic(subject=item["subject"], name=item["name"], description=item["description"])
        analysis = heuristic_analysis(item["content"])
        content = LearningContent(
            topic=topic,
            title=f"Introduction to {item['name']}",
            body=item["content"],
            summary=analysis.summary,
            key_concepts=analysis.key_concepts,
            difficulty=analysis.difficulty,
            processed_by="heuristic",
        )
        db.add_all([topic, content])
        db.flush()
        db.add_all(
            Question(
                topic_id=topic.id,
                content_id=content.id,
                text=text,
                options=options,
                correct_answer=answer,
                difficulty=difficulty,
                explanation=f"The correct answer is {answer}.",
                is_validated=True,
                validation_notes=["seed data"],
            )
            for text, options, answer, difficulty in item["questions"]
        )
    db.add(Student(name="Demo Student", email="demo@student.example", grade_level=7))
    db.commit()
