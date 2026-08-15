import google.generativeai as genai
from backend.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")


async def generate_career_advice(
    resume_text: str,
    job_title: str,
    job_description: str,
    matched_skills: list[str],
    skill_gaps: list[str],
    ats_score: float,
) -> dict:
    """
    Use Gemini to generate:
    - Improvement suggestions
    - Tailored cover letter draft
    - Interview preparation tips
    """

    prompt = f"""
You are an expert career coach and HR consultant.

RESUME SUMMARY:
{resume_text[:2000]}

TARGET JOB: {job_title}
JOB DESCRIPTION:
{job_description[:1500]}

ANALYSIS:
- ATS Match Score: {ats_score}/100
- Matched Skills: {', '.join(matched_skills) or 'None identified'}
- Skill Gaps: {', '.join(skill_gaps) or 'None identified'}

Respond ONLY in this exact JSON format (no markdown, no backticks):
{{
  "improvement_suggestions": [
    "suggestion 1",
    "suggestion 2",
    "suggestion 3",
    "suggestion 4"
  ],
  "cover_letter_draft": "Dear Hiring Manager,\\n\\n[full cover letter here]\\n\\nSincerely,\\n[Your Name]",
  "interview_tips": [
    "tip 1",
    "tip 2",
    "tip 3",
    "tip 4"
  ]
}}
"""

    try:
        response = _model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        import json
        return json.loads(text.strip())
    except Exception as e:
        print(f"[LLM] Gemini error: {e}")
        return {
            "improvement_suggestions": [
                f"Add more keywords from the job description to improve ATS score.",
                f"Quantify your achievements with metrics where possible.",
                f"Tailor your summary to align with: {job_title}.",
                f"Address skill gaps: {', '.join(skill_gaps[:3]) if skill_gaps else 'keep upskilling'}.",
            ],
            "cover_letter_draft": (
                f"Dear Hiring Manager,\n\n"
                f"I am writing to express my interest in the {job_title} position. "
                f"With my background in {', '.join(matched_skills[:3])}, I am confident "
                f"I can contribute meaningfully to your team.\n\n"
                f"Sincerely,\n[Your Name]"
            ),
            "interview_tips": [
                "Research the company's products and recent news before the interview.",
                "Prepare STAR-format answers for behavioral questions.",
                f"Be ready to discuss your experience with: {', '.join(matched_skills[:4])}.",
                "Prepare 3 thoughtful questions to ask the interviewer.",
            ],
        }


async def generate_resume_summary(resume_text: str) -> str:
    """Generate a professional summary from resume text."""
    prompt = f"""
Read this resume and write a 3-sentence professional summary for the candidate.
Be specific about their tech stack and level. No fluff.

RESUME:
{resume_text[:3000]}

Return only the summary text, nothing else.
"""
    try:
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Experienced software professional with strong technical background."
