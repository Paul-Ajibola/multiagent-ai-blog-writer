from __future__ import annotations


from langgraph.graph import END, START, StateGraph

from agent.checkpointer import build_checkpointer
from agent.nodes.orchestrator import fanout, orchestrator_node
from agent.nodes.reducer import build_reducer_subgraph
from agent.nodes.researcher import research_node
from agent.nodes.router import route_next, router_node
from agent.nodes.worker import worker_node
from agent.schemas import State


def build_graph():
    reducer_subgraph = build_reducer_subgraph()

    graph = StateGraph(State)

    graph.add_node("router", router_node)
    graph.add_node("research", research_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("worker", worker_node)
    graph.add_node("reducer", reducer_subgraph)


    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router", route_next, {"research": "research", "orchestrator": "orchestrator"}
    )
    graph.add_edge("research", "orchestrator")

    graph.conditional_edges("orchestrator", fanout, ["worker"])
    graph.add_edge("worker", "reducer")
    graph.add_edge("reducer", END)

    checkpointer = build_checkpointer()

    return graph.compile(checkpointer=checkpointer)


app = build_graph()


