from __future__ import annotations


from typing import List
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import model
from agent.prompts import RESEARCH_SYSTEM
from agent.schemas import EvidencePack, State



def tavily_search(query: str, max_results: int = 5) -> List[dict]:
    tool = TavilySearchResults(max_results=max_results)
    results = tool.invoke({"query": query})

    normalized: List[dict] = []
    for r in results or []:
        normalized.append(
            {
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "snippet": r.get("content") or r.get("snippet") or "",
                "published_at": r.get("published_date") or rget("published_at"),
                "source": r.get("source"),

            }
        )
    return normalized



def research_node(state: State) -> dict:
    queries = state.get("queries", []) or []
    max_results = 6

    raw_results: List[dict] = []
    for q in queries:
        raw_results.extend(_tavility_search(q, max_results=max_results))

    if not raw_results:
        return {"evidence": []}

    extractor = model.with_structured_output(EvidencePack)
    pack = extractor.invoke(
            [
                SystemMessage(content=RESEARCH_SYSTEM),
                HumanMessage(content=f"Raw Results:\n{raw_results}"),
            ]
        )

    # deduplicate by URL
    dedup = {}
    for e in pack.evidence:
        if e.url:
                dedup[e.url] = e
    return {"evidence": list(dedup.values())}


