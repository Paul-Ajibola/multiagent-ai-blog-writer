from __future__ import annotations

from langchain.core.messages import HumanMessage, SystemMessage
from langgraph.types import Send

from agent.llm import model
from agent.prompts import ORCH_SYSTEM
from agent.schemas import Plan, State


def orchestrator_node(state: State) -> dict:
    planner = model.with_structured_output(Plan)
    evidence = state.get("evidence", [])
    mode = state.get("mode", "closed_book")

    plan = planner.invoke(
        [
            SystemMessage(content=ORCH_SYSTEM),
            HumanMessage(content=(
                f"Topic: {state['topic']}\n"
                f"Mode: {mode}\n\n"
                f"Evidence (ONLY use for fresh claims: may be empty):\n"
                f"{[e.model_dump() for e in evidence][:16]}"
            ),)
        ]
    )

    return {
        "plan": plan.plan,
    }



def fanout(state: State):
    return [
        Send(
            "worker",
            {
                "task": task.model_dump(),
                "topic": state["topic"],
                "mode": state["mode"],
                "plan": state["plan"].model_dump(),
                "evidence": [e.model_dump() for e in state.get("evidence", [])]
            }
        )
        for task in state["plan"].tasks
    ]

