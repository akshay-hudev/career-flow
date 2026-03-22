import httpx
from typing import Optional
from backend.config import settings

CACHE_TTL = 3600  # not used anymore (can remove later)
ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/in/search"


def _normalize_job(raw: dict) -> dict:
    """Normalize Adzuna API response to our internal job schema."""
    salary = raw.get("salary_min"), raw.get("salary_max")
    return {
        "external_id": str(raw.get("id", "")),
        "title": raw.get("title", ""),
        "company": raw.get("company", {}).get("display_name", ""),
        "location": raw.get("location", {}).get("display_name", ""),
        "description": raw.get("description", ""),
        "salary_min": float(salary[0]) if salary[0] else None,
        "salary_max": float(salary[1]) if salary[1] else None,
        "job_url": raw.get("redirect_url", ""),
        "match_score": None,
    }


async def search_jobs(
    query: str,
    location: str = "India",
    num_results: int = 20,
) -> list[dict]:
    """
    Search jobs via Adzuna API (no caching).
    Falls back to mock data if API keys are missing.
    """
    page = 1
    results_per_page = min(num_results, 50)

    if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
        return _mock_jobs(query, location, num_results)

    params = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": query,
        "where": location,
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(ADZUNA_BASE + f"/{page}", params=params)
            response.raise_for_status()
            data = response.json()
            jobs = [_normalize_job(j) for j in data.get("results", [])]
            return jobs[:num_results]
    except Exception as e:
        print(f"[JobSearch] Adzuna API error: {e}")
        return _mock_jobs(query, location, num_results)


def _mock_jobs(query: str, location: str, n: int) -> list[dict]:
    """Mock data for development/testing without API keys."""
    mock = []
    companies = ["Infosys", "TCS", "Wipro", "Razorpay", "Zepto", "Swiggy", "PhonePe", "Atlassian India"]
    locations = ["Bengaluru", "Mumbai", "Hyderabad", "Pune", "Chennai", "Delhi NCR"]

    for i in range(min(n, 8)):
        mock.append({
            "external_id": f"mock-{i+1}",
            "title": f"{query} Engineer {'I' * (i % 3 + 1)}",
            "company": companies[i % len(companies)],
            "location": locations[i % len(locations)],
            "description": (
                f"We are looking for a skilled {query} professional to join our team. "
                f"You will work with Python, React, PostgreSQL, Docker, and REST APIs. "
                f"3+ years of experience required. Strong problem-solving skills needed."
            ),
            "salary_min": 800000 + i * 100000,
            "salary_max": 1500000 + i * 100000,
            "job_url": f"https://example.com/jobs/{i+1}",
            "match_score": None,
        })
    return mock