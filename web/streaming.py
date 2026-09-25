from __future__ import annotations

from typing import Any, Generator

from backend import app as workflow
from web.logging_config import logger
from web.serialization import (
    create_sse_event,
    get_plan_task_map,
    normalize_stream_chunk,
    save_final_markdown,
)


def stream_workflow(topic: str, run_id: str) -> Generator[str, None, None]:
    """
    Run the LangGraph workflow and stream observable execution updates
    to the browser: node status, routing decision, research queries and
    source count, structured article plan, completed sections,
    image-processing status, and final Markdown.

    Does not expose private model reasoning.
    """
    config = {"configurable": {"thread_id": run_id}}
    workflow_input = {"topic": topic, "sections": []}

    task_map: dict[int, dict[str, Any]] = {}
    completed_task_ids: set[int] = set()

    final_markdown = ""
    workers_completed_event_sent = False
    reducer_started_event_sent = False

    yield create_sse_event({"type": "run_started", "run_id": run_id, "topic": topic})

    yield create_sse_event(
        {
            "type": "stage",
            "id": "router",
            "label": "Analyze the request",
            "status": "running",
            "detail": "Determining whether the topic requires current web research.",
        }
    )

    try:
        stream = workflow.stream(
            workflow_input,
            config=config,
            stream_mode="updates",
            subgraphs=True,
        )

        for raw_chunk in stream:
            namespace, updates = normalize_stream_chunk(raw_chunk)

            if not updates:
                continue

            for node_name, raw_node_update in updates.items():
                node_update = make_serializable_dict(raw_node_update)

                if node_name == "router":
                    yield from _handle_router(node_update)

                elif node_name == "research":
                    yield from _handle_research(node_update)

                elif node_name == "orchestrator":
                    task_map = get_plan_task_map(node_update.get("plan", {}) or {})
                    yield from _handle_orchestrator(node_update, task_map)

                elif node_name == "worker":
                    sections = node_update.get("sections", [])
                    if not isinstance(sections, list):
                        sections = []

                    for section in sections:
                        result = _handle_worker_section(
                            section, task_map, completed_task_ids
                        )
                        if result is not None:
                            yield result

                    if (
                        task_map
                        and len(completed_task_ids) >= len(task_map)
                        and not workers_completed_event_sent
                    ):
                        workers_completed_event_sent = True
                        reducer_started_event_sent = True
                        yield create_sse_event(
                            {
                                "type": "stage",
                                "id": "workers",
                                "label": "Write the planned sections",
                                "status": "completed",
                                "detail": f"Completed all {len(task_map)} sections.",
                            }
                        )
                        yield create_sse_event(
                            {
                                "type": "stage",
                                "id": "reducer",
                                "label": "Assemble the final article",
                                "status": "running",
                                "detail": "Merging the sections and planning useful visuals.",
                            }
                        )

                elif node_name == "merge_content":
                    if not reducer_started_event_sent:
                        reducer_started_event_sent = True
                        yield create_sse_event(
                            {
                                "type": "stage",
                                "id": "reducer",
                                "label": "Assemble the final article",
                                "status": "running",
                                "detail": "Merging the sections and planning useful visuals.",
                            }
                        )

                    yield create_sse_event(
                        {
                            "type": "substage",
                            "id": "merge_content",
                            "label": "Merged all written sections",
                            "status": "completed",
                            "namespace": list(namespace),
                        }
                    )

                elif node_name == "decide_images":
                    yield from _handle_decide_images(node_update, namespace)

                elif node_name == "generate_and_place_images":
                    generated_final = node_update.get("final")
                    if generated_final:
                        final_markdown = str(generated_final)

                    yield create_sse_event(
                        {
                            "type": "substage",
                            "id": "generate_images",
                            "label": "Generated and placed visuals",
                            "status": "completed",
                            "namespace": list(namespace),
                        }
                    )

                elif node_name == "reducer":
                    generated_final = node_update.get("final")
                    if generated_final:
                        final_markdown = str(generated_final)

        if not final_markdown:
            snapshot = workflow.get_state(config)
            state_values = getattr(snapshot, "values", {})
            if isinstance(state_values, dict):
                final_markdown = str(state_values.get("final", ""))

        if not final_markdown:
            raise RuntimeError(
                "The workflow completed but did not return final Markdown."
            )

        save_final_markdown(run_id=run_id, markdown=final_markdown)

        yield create_sse_event(
            {
                "type": "stage",
                "id": "reducer",
                "label": "Assemble the final article",
                "status": "completed",
                "detail": "The final Markdown article is ready.",
            }
        )

        yield create_sse_event(
            {
                "type": "final",
                "run_id": run_id,
                "markdown": final_markdown,
                "download_url": f"/api/runs/{run_id}/download",
            }
        )

        yield create_sse_event({"type": "done", "run_id": run_id})

    except GeneratorExit:
        logger.info("Browser disconnected from run %s", run_id)
        raise

    except Exception as error:
        logger.exception("Workflow run %s failed", run_id)
        yield create_sse_event({"type": "error", "run_id": run_id, "message": str(error)})


# ------------------------------------------------------------------
# Small per-node helpers (kept private to this module for cohesion)
# ------------------------------------------------------------------
def make_serializable_dict(raw_node_update: Any) -> dict[str, Any]:
    from web.serialization import make_serializable

    node_update = make_serializable(raw_node_update)
    return node_update if isinstance(node_update, dict) else {}


def _handle_router(node_update: dict[str, Any]):
    mode = str(node_update.get("mode", "closed_book"))
    needs_research = bool(node_update.get("needs_research", False))
    queries = node_update.get("queries", [])

    yield create_sse_event(
        {"type": "routing", "mode": mode, "needs_research": needs_research, "queries": queries}
    )

    yield create_sse_event(
        {
            "type": "stage",
            "id": "router",
            "label": "Analyze the request",
            "status": "completed",
            "detail": f"Selected {mode.replace('_', ' ')} mode.",
        }
    )

    if needs_research:
        yield create_sse_event(
            {
                "type": "stage",
                "id": "research",
                "label": "Research authoritative sources",
                "status": "running",
                "detail": "Searching the web and preparing a deduplicated evidence pack.",
            }
        )
    else:
        yield create_sse_event(
            {
                "type": "stage",
                "id": "orchestrator",
                "label": "Create the article plan",
                "status": "running",
                "detail": "Creating the article structure, goals and writing tasks.",
            }
        )


def _handle_research(node_update: dict[str, Any]):
    evidence = node_update.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []

    yield create_sse_event(
        {"type": "research_complete", "count": len(evidence), "evidence": evidence[:12]}
    )

    yield create_sse_event(
        {
            "type": "stage",
            "id": "research",
            "label": "Research authoritative sources",
            "status": "completed",
            "detail": f"Prepared {len(evidence)} deduplicated sources.",
        }
    )

    yield create_sse_event(
        {
            "type": "stage",
            "id": "orchestrator",
            "label": "Create the article plan",
            "status": "running",
            "detail": "Creating sections, goals, bullets and target word counts.",
        }
    )


def _handle_orchestrator(node_update: dict[str, Any], task_map: dict[int, dict[str, Any]]):
    plan = node_update.get("plan", {})
    if not isinstance(plan, dict):
        plan = {}

    yield create_sse_event({"type": "plan", "plan": plan})

    yield create_sse_event(
        {
            "type": "stage",
            "id": "orchestrator",
            "label": "Create the article plan",
            "status": "completed",
            "detail": f"Created {len(task_map)} article sections.",
        }
    )

    yield create_sse_event(
        {
            "type": "stage",
            "id": "workers",
            "label": "Write the planned sections",
            "status": "running",
            "detail": "Section workers are writing the article in parallel.",
        }
    )


def _handle_worker_section(section, task_map, completed_task_ids):
    if not isinstance(section, (list, tuple)) or len(section) != 2:
        return None

    raw_task_id, section_markdown = section
    try:
        task_id = int(raw_task_id)
    except (TypeError, ValueError):
        return None

    if task_id in completed_task_ids:
        return None

    completed_task_ids.add(task_id)
    task_information = task_map.get(task_id, {})
    title = task_information.get("title", f"Section {task_id}")

    return create_sse_event(
        {
            "type": "section_complete",
            "task_id": task_id,
            "title": title,
            "markdown": str(section_markdown),
            "completed": len(completed_task_ids),
            "total": len(task_map),
        }
    )


def _handle_decide_images(node_update: dict[str, Any], namespace: tuple[str, ...]):
    image_specs = node_update.get("image_specs", [])
    if not isinstance(image_specs, list):
        image_specs = []

    yield create_sse_event(
        {"type": "images_planned", "count": len(image_specs), "images": image_specs}
    )

    yield create_sse_event(
        {
            "type": "substage",
            "id": "decide_images",
            "label": (
                f"Planned {len(image_specs)} technical visual"
                f"{'' if len(image_specs) == 1 else 's'}"
            ),
            "status": "completed",
            "namespace": list(namespace),
        }
    )