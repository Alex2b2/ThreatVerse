# backend/app.py
import uvicorn
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import json
from config import settings
from schemas import Token, LoginRequest, IngestResult
from auth import create_access_token, get_current_user
from ingest_stix import ingest_stix_json
from ingest_misp import ingest_misp_json
from db import merge_node, search_nodes_by_name, get_subgraph
from ml_utils import compute_anomaly_scores_graph, cluster_nodes_sample

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}

@app.post("/auth/login", response_model=Token)
def login(payload: LoginRequest):
    # very simple username/password check
    if payload.username == settings.DEFAULT_ADMIN_USER and payload.password == settings.DEFAULT_ADMIN_PASS:
        token = create_access_token({"sub": payload.username})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/ingest/stix", response_model=IngestResult)
async def ingest_stix(file: UploadFile = File(...), current_user: Dict = Depends(get_current_user)):
    if not file:
        raise HTTPException(status_code=400, detail="Missing file")
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    nodes, rels = ingest_stix_json(data)
    return {"ingested_nodes": nodes, "ingested_rels": rels}

@app.post("/ingest/misp", response_model=IngestResult)
async def ingest_misp(file: UploadFile = File(...), current_user: Dict = Depends(get_current_user)):
    if not file:
        raise HTTPException(status_code=400, detail="Missing file")
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    nodes, rels = ingest_misp_json(data)
    return {"ingested_nodes": nodes, "ingested_rels": rels}

@app.get("/search")
def search(q: str, current_user: Dict = Depends(get_current_user)):
    results = search_nodes_by_name(q)
    return results

@app.get("/graph/{uid}")
def subgraph(uid: str, depth: int = 1, current_user: Dict = Depends(get_current_user)):
    return get_subgraph(uid, depth)

@app.get("/ml/anomaly/{uid}")
def ml_anomaly(uid: str, depth: int = 2, current_user: Dict = Depends(get_current_user)):
    return compute_anomaly_scores_graph(uid, depth)

@app.get("/ml/cluster/{uid}")
def ml_cluster(uid: str, depth: int = 2, current_user: Dict = Depends(get_current_user)):
    return cluster_nodes_sample(uid, depth)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
