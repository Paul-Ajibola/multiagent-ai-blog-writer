from __future__ import annotations


import psycopg
from psycopg.row import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from agent.config import DATABASE_URL



def build_checkpointer() -> PostgresSaver:
    conn = psycopg.connect(
        DATABASE_URL,
        autocommit=True,
        row_factory=dict_row,
    )
    # create an instance of PostgresSaver object
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    return checkpointer



