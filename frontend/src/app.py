# ---- DEV-ONLY public endpoints (no auth) to support local development / testing ----
# These are intentionally unauthenticated to make local testing easier.
# Do NOT expose them in production.
from fastapi import HTTPException

@app.get("/public/search")
def public_search(q: str):
    try:
        return search_nodes_by_name(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/public/graph/{uid}")
def public_graph(uid: str, depth: int = 1):
    try:
        return get_subgraph(uid, depth)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# also public ML endpoints for convenience
@app.get("/public/ml/anomaly/{uid}")
def public_ml_anomaly(uid: str, depth: int = 2):
    try:
        return compute_anomaly_scores_graph(uid, depth)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/public/ml/cluster/{uid}")
def public_ml_cluster(uid: str, depth: int = 2):
    try:
        return cluster_nodes_sample(uid, depth)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ---- end dev-only endpoints ----
