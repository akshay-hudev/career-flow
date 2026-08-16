import google.generativeai as genai
from backend.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = genai.GenerativeModel(settings.GEMINI_MODEL)

QUESTION_TYPES = {
    "behavioral":  "Behavioral (STAR-format) questions about past experience",
    "technical":   "Technical questions specific to the role and tech stack",
    "situational": "Situational 'what would you do if...' questions",
    "hr":          "HR questions about motivation, salary, culture fit",
}


async def generate_interview_questions(
    job_title: str,
    job_description: str,
    skills: list[str],
    question_type: str = "technical",
    count: int = 5,
) -> list[dict]:
    """Generate interview questions for a specific role."""

    prompt = f"""
You are a senior technical interviewer at a top Indian tech company.

Role: {job_title}
Job Description: {job_description[:800]}
Candidate Skills: {', '.join(skills[:10])}
Question Type: {QUESTION_TYPES.get(question_type, question_type)}

Generate exactly {count} interview questions. For each question also provide:
- The ideal answer framework (2-3 sentences)
- Difficulty: easy / medium / hard

Respond ONLY in this JSON format (no markdown, no backticks):
[
  {{
    "question": "...",
    "ideal_answer_framework": "...",
    "difficulty": "medium"
  }}
]
"""
    try:
        response = _model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        import json
        data = json.loads(text.strip())
        # Guard against valid-JSON-but-wrong-shape LLM output: a malformed
        # payload should fall back to canned questions, not 500 on response
        # validation. Require a non-empty list of items with the expected keys.
        if not isinstance(data, list) or not data:
            raise ValueError("LLM did not return a question list")
        for item in data:
            if not isinstance(item, dict) or not all(
                k in item for k in ("question", "ideal_answer_framework", "difficulty")
            ):
                raise ValueError("LLM question item missing required fields")
        return data[:count]
    except Exception as e:
        print(f"[Interview] Question generation error: {e}")
        return _fallback_questions(job_title, question_type, count)


async def evaluate_answer(
    question: str,
    user_answer: str,
    job_title: str,
    ideal_framework: str,
) -> dict:
    """Evaluate a candidate's answer and provide structured feedback."""

    prompt = f"""
You are evaluating a mock interview answer for a {job_title} role.

Question: {question}
Ideal Answer Framework: {ideal_framework}
Candidate's Answer: {user_answer}

Evaluate the answer and respond ONLY in this JSON format (no markdown, no backticks):
{{
  "score": 7,
  "score_out_of": 10,
  "strengths": ["strength 1", "strength 2"],
  "improvements": ["improvement 1", "improvement 2"],
  "sample_better_answer": "A stronger answer would be...",
  "verdict": "Good answer with room for improvement."
}}
"""
    try:
        response = _model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        import json
        data = json.loads(text.strip())
        # Coerce/validate so a valid-JSON-but-wrong-shape payload falls back
        # instead of 500ing on response validation. Gemini often returns the
        # score as a string or a decimal ("8.5") — normalize it to a number.
        required = (
            "score", "score_out_of", "strengths",
            "improvements", "sample_better_answer", "verdict",
        )
        if not isinstance(data, dict) or not all(k in data for k in required):
            raise ValueError("LLM evaluation missing required fields")
        data["score"] = float(data["score"])
        data["score_out_of"] = int(data["score_out_of"])
        return data
    except Exception as e:
        print(f"[Interview] Evaluation error: {e}")
        return {
            "score": 6,
            "score_out_of": 10,
            "strengths": ["You attempted to answer the question."],
            "improvements": ["Add more specific examples.", "Use the STAR format."],
            "sample_better_answer": "Focus on concrete results and metrics.",
            "verdict": "Decent attempt — add more specifics.",
        }


def _fallback_questions(job_title: str, q_type: str, count: int) -> list[dict]:
    base = [
        {"question": f"Tell me about a challenging project you worked on as a {job_title}.",
         "ideal_answer_framework": "Use STAR: Situation, Task, Action, Result. Quantify impact.",
         "difficulty": "medium"},
        {"question": "How do you handle tight deadlines and competing priorities?",
         "ideal_answer_framework": "Describe a prioritization framework you use with a real example.",
         "difficulty": "easy"},
        {"question": "Describe a time you disagreed with a technical decision. What did you do?",
         "ideal_answer_framework": "Show maturity: raised concerns professionally, backed with data.",
         "difficulty": "medium"},
        {"question": "What is your biggest technical weakness and how are you addressing it?",
         "ideal_answer_framework": "Be honest. Mention active steps: courses, projects, mentorship.",
         "difficulty": "easy"},
        {"question": "Where do you see yourself in 3 years?",
         "ideal_answer_framework": "Align growth with the company's trajectory. Show ambition.",
         "difficulty": "easy"},
    ]
    return base[:count]
