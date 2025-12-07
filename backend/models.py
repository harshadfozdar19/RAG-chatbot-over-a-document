# models.py
from pydantic import BaseModel

class QueryRequest(BaseModel):
    history: list
    question: str
    top_k: int = 4
