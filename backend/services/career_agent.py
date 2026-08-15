"""
LangGraph Career Agent
======================
A stateful multi-step agent that orchestrates:
  parse_resume → search_jobs → rank_matches → generate_advice → END

Each node is a discrete, testable function. State flows through the graph
and accumulates results at each step. This is production-grade agentic AI,
not a single LLM call.
"""

from typing import TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import asyncio

from backend.services.resume_parser import parse_resume
from backend.services.semantic_matcher import get_embedding, rank_jobs, compute_match
from backend.services.job_search import search_jobs
from backend.services.llm_service import generate_career_advice, generate_resume_summary


# ── State Definition ──────────────────────────────────────────────────────────

class CareerAgentState(TypedDict):
    # Inputs
    file_bytes: Optional[bytes]
    filename: Optional[str]
    job_query: str
    location: str
    resume_id: Optional[int]

    # Populated by nodes
    raw_text: Optional[str]
    parsed_data: Optional[dict]
    ats_score: Optional[float]
    embedding: Optional[list]
    jobs: Optional[list]
    ranked_jobs: Optional[list]
    top_job: Optional[dict]
    advice: Optional[dict]

    # Errors
    error: Optional[str]
    steps_completed: list


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_parse_resume(state: CareerAgentState) -> CareerAgentState:
    """Node 1: Parse PDF bytes into structured resume data + embedding."""
    print("[Agent] ▶ node_parse_resume")
    try:
        raw_text, parsed, ats_score = parse_resume(
            state["file_bytes"], state["filename"]
        )
        embedding = get_embedding(raw_text[:3000])

        return {
            **state,
            "raw_text": raw_text,
            "parsed_data": parsed.model_dump(),
            "ats_score": ats_score,
            "embedding": embedding,
            "steps_completed": state["steps_completed"] + ["parse_resume"],
        }
    except Exception as e:
        return {**state, "error": f"Resume parsing failed: {e}"}


async def node_search_jobs(state: CareerAgentState) -> CareerAgentState:
    """Node 2: Fetch jobs from Adzuna API (Redis cached)."""
    print("[Agent] ▶ node_search_jobs")
    if state.get("error"):
        return state
    try:
        jobs = await search_jobs(state["job_query"], state["location"], num_results=20)
        return {
            **state,
            "jobs": jobs,
            "steps_completed": state["steps_completed"] + ["search_jobs"],
        }
    except Exception as e:
        return {**state, "error": f"Job search failed: {e}"}


def node_rank_matches(state: CareerAgentState) -> CareerAgentState:
    """Node 3: Rank fetched jobs by semantic similarity to resume."""
    print("[Agent] ▶ node_rank_matches")
    if state.get("error"):
        return state
    try:
        jobs = state.get("jobs", [])
        embedding = state.get("embedding")
        raw_text = state.get("raw_text", "")

        if not jobs or not embedding:
            return {**state, "ranked_jobs": jobs}

        ranked = rank_jobs(raw_text, embedding, jobs)
        top_job = ranked[0] if ranked else None

        return {
            **state,
            "ranked_jobs": ranked,
            "top_job": top_job,
            "steps_completed": state["steps_completed"] + ["rank_matches"],
        }
    except Exception as e:
        return {**state, "error": f"Ranking failed: {e}"}


async def node_generate_advice(state: CareerAgentState) -> CareerAgentState:
    """Node 4: Generate AI career advice for the top-matched job."""
    print("[Agent] ▶ node_generate_advice")
    if state.get("error"):
        return state
    try:
        top_job = state.get("top_job")
        if not top_job:
            return {**state, "advice": None}

        parsed = state.get("parsed_data", {})
        resume_skills = parsed.get("skills", [])
        job_desc = top_job.get("description", "")

        match = compute_match(
            resume_text=state["raw_text"],
            resume_embedding=state["embedding"],
            job_description=job_desc,
        )

        advice = await generate_career_advice(
            resume_text=state["raw_text"],
            job_title=top_job.get("title", ""),
            job_description=job_desc,
            matched_skills=match["matched_skills"],
            skill_gaps=match["skill_gaps"],
            ats_score=match["score"],
        )

        return {
            **state,
            "advice": {
                **advice,
                "ats_score": match["score"],
                "matched_skills": match["matched_skills"],
                "skill_gaps": match["skill_gaps"],
            },
            "steps_completed": state["steps_completed"] + ["generate_advice"],
        }
    except Exception as e:
        return {**state, "error": f"Advice generation failed: {e}"}


# ── Conditional edge: skip advice if no jobs found ────────────────────────────

def should_generate_advice(state: CareerAgentState) -> str:
    if state.get("error"):
        return "end"
    if not state.get("ranked_jobs"):
        return "end"
    return "generate_advice"


# ── Build the Graph ───────────────────────────────────────────────────────────

def build_career_agent():
    workflow = StateGraph(CareerAgentState)

    workflow.add_node("parse_resume", node_parse_resume)
    workflow.add_node("search_jobs", node_search_jobs)
    workflow.add_node("rank_matches", node_rank_matches)
    workflow.add_node("generate_advice", node_generate_advice)

    workflow.set_entry_point("parse_resume")
    workflow.add_edge("parse_resume", "search_jobs")
    workflow.add_edge("search_jobs", "rank_matches")
    workflow.add_conditional_edges(
        "rank_matches",
        should_generate_advice,
        {
            "generate_advice": "generate_advice",
            "end": END,
        }
    )
    workflow.add_edge("generate_advice", END)

    return workflow.compile()


# Compiled agent — import this elsewhere
career_agent = build_career_agent()


async def run_career_agent(
    file_bytes: bytes,
    filename: str,
    job_query: str,
    location: str = "India",
) -> CareerAgentState:
    """
    Run the full career agent pipeline.
    Returns the final state with jobs, rankings, and advice.
    """
    initial_state: CareerAgentState = {
        "file_bytes": file_bytes,
        "filename": filename,
        "job_query": job_query,
        "location": location,
        "resume_id": None,
        "raw_text": None,
        "parsed_data": None,
        "ats_score": None,
        "embedding": None,
        "jobs": None,
        "ranked_jobs": None,
        "top_job": None,
        "advice": None,
        "error": None,
        "steps_completed": [],
    }

    final_state = await career_agent.ainvoke(initial_state)
    return final_state
