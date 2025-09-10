# backend/ml_utils.py
"""
Simple ML utilities:
- compute centrality-based anomaly score
- cluster nodes using DBSCAN on simple numeric features (degree, centrality)
"""

from db import get_subgraph, search_nodes_by_name
from typing import Dict, Any
import networkx as nx
from sklearn.cluster import DBSCAN
import numpy as np

def compute_anomaly_scores_graph(uid: str, depth: int = 2):
    """
    For the subgraph around uid, compute degree centrality and return nodes with anomaly-like scores
    (nodes with unusually high degree centrality).
    """
    sub = get_subgraph(uid, depth)
    nodes = sub['nodes']
    edges = sub['edges']

    # Build networkx graph
    G = nx.Graph()
    for n in nodes:
        G.add_node(n.get('stix_id') or n.get('_uid') or n.get('uid'), **n)
    for e in edges:
        start = e.get('start')
        end = e.get('end')
        if start and end:
            G.add_edge(start, end)
    if G.number_of_nodes() == 0:
        return []

    centrality = nx.degree_centrality(G)
    # Anomaly score: centrality scaled
    results = []
    for node_id, cent in centrality.items():
        results.append({"node": node_id, "centrality": float(cent)})
    # sort descending
    results = sorted(results, key=lambda x: x['centrality'], reverse=True)
    return results

def cluster_nodes_sample(seed_uid: str, depth: int = 2):
    """
    Build a small numeric feature vector for nodes (degree, centrality) and run DBSCAN.
    Returns cluster labels keyed by node id.
    """
    sub = get_subgraph(seed_uid, depth)
    nodes = sub['nodes']
    edges = sub['edges']
    G = nx.Graph()
    id_map = {}
    for n in nodes:
        nid = n.get('_uid') or n.get('uid') or n.get('stix_id')
        id_map[nid] = n
        G.add_node(nid)
    for e in edges:
        s = e.get('start'); t = e.get('end')
        if s and t:
            G.add_edge(s, t)
    if G.number_of_nodes() == 0:
        return {}

    deg = dict(G.degree())
    cent = nx.degree_centrality(G)
    X = []
    keys = []
    for k in G.nodes():
        X.append([deg.get(k, 0), cent.get(k, 0)])
        keys.append(k)
    X = np.array(X)
    if len(X) <= 1:
        labels = [0]*len(X)
    else:
        model = DBSCAN(eps=0.5, min_samples=1).fit(X)
        labels = model.labels_.tolist()
    out = {k: int(l) for k, l in zip(keys, labels)}
    return out
