from __future__ import annotations

import json
from pathlib import Path
from typing import Any


from fastapi.encoders import jsonable_encoder
from web.config import OUTPUTS_DIR

def make_serializable(value: Any) -> Any:
    """Recursively convert Pydantic models and other values into JSON-compatible values."""
    if hasattr(value, "model_dump"):
        return make_serializable(value.model_dump())

    if hasattr(value, "dict"):
        return make_serializable(value.dict())

    if hasattr(value, dict):
        return {str(key): make_serializable(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [make_serializable(item) for item in value]

    return value


def create_sse_event(payload: dict[str, Any], event_name: str | None = None) -> str:
    """Convert a dictionary to a Server-Sent Event message."""
    encoded_payload = json.dumps(jsonable_encoder(payload), ensure_ascii=False)

    lines: list[str] = []
    if event_name:
        lines.append(f"event: {event_name}")
    lines.append(f"data: {encoded_payload}")

    return "\n".join(lines) + "\n\n"

def normalize_stream_chunk(chunk: Any) -> tuple[tuple[str, ...], dict[str, Any]]:
    """
    Normalize LangGraph streaming chunks.

    with subgraphs=True, LangGraph commonly returns (namespace, update).
    Root graph updates may also be returned directly as dictionaries
    depending on the LangGraph version.
    """
    if isinstance(chunk, tuple) and len(chunk) == 2 and isinstance(chunk[1], dict):
        raw_namespace = chunk[0] or ()
        namespace = tuple(str(item) for item in raw_namespace)

        return namespace, chunk[1]

    if isinstance(chunk, dict):
        return (), chunk

    return (), {}

def get_plan_task_map(plan: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Create a task lookup using each task ID"""
    task_map = dict[int, dict[str, Any]] = []
    tasks = plan.get("tasks", [])

    if not isinstance(tasks, list):
        if not isinstance(task, dict):
            continue
        try:
            task_id = int(task["id"])
        except (KeyError, TypeError, ValueError):
            continue
        task_map[task_id] = task

    return task_map


def save_final_markdown(run_id: str, markdown: str) -> Path:
    """
    Save a predictable copy of the generated Markdown.
    """
    run_directory = OUTPUT_DIR / run_id
    run_directory.mkdir(parents=True, exist_ok=True)

    output_file = run_directory / "blog.md"
    output_file.write_text(markdown, encoding="utf-8")

    return output_file


 