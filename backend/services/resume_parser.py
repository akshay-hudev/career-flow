import io
import re
import pdfplumber
from typing import Optional
from backend.schemas.schemas import ParsedResume


# Common tech skills to extract (expand as needed)
TECH_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "node.js", "nodejs",
    "flask", "fastapi", "django", "spring", "spring boot", "sql", "postgresql",
    "mysql", "mongodb", "redis", "docker", "kubernetes", "git", "github",
    "aws", "gcp", "azure", "tensorflow", "pytorch", "scikit-learn", "pandas",
    "numpy", "opencv", "langchain", "langgraph", "rest", "graphql", "html",
    "css", "tailwind", "c++", "c", "go", "rust", "linux", "bash",
    "machine learning", "deep learning", "nlp", "computer vision",
}

EDUCATION_KEYWORDS = ["b.e", "b.tech", "m.tech", "bsc", "msc", "mba", "phd",
                      "bachelor", "master", "engineering", "computer science",
                      "information technology", "university", "college", "institute"]

EXPERIENCE_PATTERNS = [
    r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
    r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from PDF bytes using pdfplumber."""
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_skills(text: str) -> list[str]:
    """Extract skills by matching against known tech skills list."""
    text_lower = text.lower()
    found = []
    for skill in TECH_SKILLS:
        # Use word boundary matching
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill.title() if len(skill) > 3 else skill.upper())
    return sorted(set(found))


def extract_experience_years(text: str) -> Optional[float]:
    """Extract years of experience from text."""
    text_lower = text.lower()
    for pattern in EXPERIENCE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            return float(match.group(1))
    return None


def extract_education(text: str) -> list[str]:
    """Extract education details using keyword matching."""
    lines = text.split('\n')
    education = []
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in EDUCATION_KEYWORDS):
            cleaned = line.strip()
            if len(cleaned) > 5:
                education.append(cleaned[:200])  # cap at 200 chars
    return list(set(education))[:5]


def extract_companies(text: str) -> list[str]:
    """Extract likely company names using pattern matching."""
    company_keywords = [
        "technologies", "tech", "systems", "solutions", "software",
        "consulting", "services", "labs", "studio", "ai", "digital",
        "innovations", "ventures", "pvt", "ltd", "inc", "corp"
    ]
    lines = text.split('\n')
    companies = []
    for line in lines:
        line = line.strip()
        line_lower = line.lower()
        if any(kw in line_lower for kw in company_keywords):
            if 3 < len(line) < 60 and not line.startswith('•'):
                companies.append(line[:60])
    return list(set(companies))[:8]


def extract_summary(text: str) -> str:
    """Return first meaningful paragraph as summary."""
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 80]
    return paragraphs[0][:400] if paragraphs else ""


def calculate_ats_score(parsed: ParsedResume, raw_text: str) -> float:
    """
    Simple ATS scoring rubric:
    - Skills found:         40 pts
    - Education mentioned:  20 pts
    - Experience mentioned:  20 pts
    - Companies mentioned:   10 pts
    - Summary/objective:     10 pts
    """
    score = 0.0
    score += min(40, len(parsed.skills) * 3)
    score += 20 if parsed.education else 0
    score += 20 if parsed.experience_years else 10 if "experience" in raw_text.lower() else 0
    score += min(10, len(parsed.companies) * 2)
    score += 10 if parsed.summary else 0
    return round(min(score, 100), 1)


def parse_resume(file_bytes: bytes, filename: str) -> tuple[str, ParsedResume, float]:
    """
    Full resume parsing pipeline.
    Returns: (raw_text, parsed_data, ats_score)
    """
    raw_text = extract_text_from_pdf(file_bytes)

    parsed = ParsedResume(
        skills=extract_skills(raw_text),
        experience_years=extract_experience_years(raw_text),
        education=extract_education(raw_text),
        companies=extract_companies(raw_text),
        summary=extract_summary(raw_text),
    )

    ats_score = calculate_ats_score(parsed, raw_text)
    return raw_text, parsed, ats_score