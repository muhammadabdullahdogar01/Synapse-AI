"""Checks the real AI model understands instructions. Needs Ollama running,
so it is skipped automatically otherwise (e.g. on GitHub Actions).
Run only these with:  pytest -m ai"""
import pytest

from core import ai

pytestmark = [
    pytest.mark.ai,
    pytest.mark.skipif(not ai.status()["chat_model"], reason="Ollama / model not available"),
]

CASES = [
    ("Find all PDF files related to cybersecurity", "search"),
    ("Sort my assignments into folders by subject", "organize"),
    ("Show me copies of the same file", "find_duplicates"),
    ("Summarize this research paper", "summarize"),
    ("What does my networking assignment say about TCP?", "ask"),
    ("My files have names like doc1 and final_final, fix them", "rename"),
    ("Where is my networking presentation?", "search"),
]


@pytest.mark.parametrize("instruction, expected", CASES)
def test_planner_intent(instruction, expected):
    from core.planner import make_plan
    plan = make_plan(instruction)
    assert plan["intent"] == expected, plan
