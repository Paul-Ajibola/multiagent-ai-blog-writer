from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from web.schemas import AgentRunRequest
from web.streaming import stream_workflow

router = APIRouter()


@router.post("/api/run")
def run_agent(request_data: AgentRunRequest):
    topic = request_data.topic.strip()

    if len(topic) < 3:
        raise HTTPException(status_code=422, detail="Please provide a valid topic.")

    run_id = uuid.uuid4().hex

    return StreamingResponse(
        stream_workflow(topic=topic, run_id=run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

