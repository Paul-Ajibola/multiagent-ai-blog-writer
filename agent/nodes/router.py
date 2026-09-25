from __future__ import annotations


from langchain.core import HumanMessage, SystemMessage
from agent.llm import model

from agent.prompts import ROUTER_SYSTEM
from agent.schemas import RouterDecision, State


def router_node(state: State) -> dict:
    """Route decisions based on the topic."""
    topic = state["topic"]
    decider = model.with_structured_output(RouterDecision)
    decision = decider.invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=f"Topic: {topic}")
        ]
    )

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
    }


def route_next(state: State) -> str:
    return "research" if state["needs_research"] else "orchestrator"

    