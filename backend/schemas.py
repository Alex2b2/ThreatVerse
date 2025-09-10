# backend/schemas.py
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

class IngestResult(BaseModel):
    ingested_nodes: int
    ingested_rels: int
