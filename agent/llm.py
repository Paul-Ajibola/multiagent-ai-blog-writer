from __future__ import annotations
from langchain_groq import ChatGroq
from agent.config import GROQ_API_KEY



model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=GROQ_API_KEY
)