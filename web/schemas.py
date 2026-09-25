from __future__ import annotations 

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=1000, description="The technical blog topic.")
