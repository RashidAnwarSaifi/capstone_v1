"""Registry of all selectable agents. The chat UI lets the user pick one or
more of these to run against the same question."""

from agents.base import BaseAgent
from agents.fact_checker_agent import FactCheckerAgent
from agents.qa_agent import QAAgent
from agents.summarizer_agent import SummarizerAgent

_AGENT_CLASSES = [QAAgent, SummarizerAgent, FactCheckerAgent]

AGENTS: dict[str, BaseAgent] = {cls.key: cls() for cls in _AGENT_CLASSES}

DEFAULT_AGENT_KEYS = [QAAgent.key]


def list_agents() -> list[BaseAgent]:
    return list(AGENTS.values())