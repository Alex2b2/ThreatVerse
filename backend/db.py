# backend/db.py
"""
DB layer: prefer Neo4j if configured, else fallback to NetworkX in-memory graph.
Provides a small API: merge_node, create_rel, get_subgraph, search_nodes.
"""

import os
from typing import Dict, List, Tuple, Any
from config import settings

USE_NEO4J = bool(settings.NEO4J_URI and settings.NEO4J_PASSWORD)

if USE_NEO4J:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))

else:
    import networkx as nx
    NX = nx.Graph()
    # We'll store node metadata in node attributes keyed by unique id

def merge_node(label: str, uid: str, properties: Dict[str, Any]):
    """
    Create or merge a node identified by uid.
    """
    if USE_NEO4J:
        with driver.session() as session:
            props = ", ".join([f"{k}: $props.{k}" for k in properties.keys()])
            query = (
                f"MERGE (n:{label} {{uid: $uid}}) "
                f"SET n += $props "
                f"RETURN n"
            )
            res = session.run(query, uid=uid, props=properties)
            return res.single()[0]
    else:
        # NetworkX
        if NX.has_node(uid):
            NX.nodes[uid].update(properties)
            NX.nodes[uid]['labels'] = list(set(NX.nodes[uid].get('labels', []) + [label]))
        else:
            attrs = properties.copy()
            attrs['labels'] = [label]
            NX.add_node(uid, **attrs)
        return NX.nodes[uid]

def create_relationship(uid_a: str, uid_b: str, rel_type: str, rel_props: Dict[str, Any] = None):
    rel_props = rel_props or {}
    if USE_NEO4J:
        with driver.session() as session:
            query = (
                "MATCH (a {uid:$a_uid}), (b {uid:$b_uid}) "
                "MERGE (a)-[r:" + rel_type + "]->(b) "
                "SET r += $props "
                "RETURN r"
            )
            session.run(query, a_uid=uid_a, b_uid=uid_b, props=rel_props)
    else:
        NX.add_edge(uid_a, uid_b, key=rel_type, **rel_props)
    return True

def search_nodes_by_name(name_query: str, limit: int = 25):
    """
    Search nodes by common text fields. Works for both Neo4j and NetworkX fallback.
    Looks at: name, value (ioc), misp_id, stix_id, description.
    Returns a list of node dicts (keyed properties).
    """
    if not name_query:
        return []

    q_lower = name_query.lower()

    if USE_NEO4J:
        # search across several possible properties (coalesce/OR)
        with driver.session() as session:
            cypher = """
            MATCH (n)
            WHERE (exists(n.name) AND toLower(n.name) CONTAINS toLower($q))
               OR (exists(n.value) AND toLower(n.value) CONTAINS toLower($q))
               OR (exists(n.misp_id) AND toLower(n.misp_id) CONTAINS toLower($q))
               OR (exists(n.stix_id) AND toLower(n.stix_id) CONTAINS toLower($q))
               OR (exists(n.description) AND toLower(n.description) CONTAINS toLower($q))
            RETURN n LIMIT $limit
            """
            res = session.run(cypher, q=name_query, limit=limit)
            nodes = []
            for r in res:
                node = r["n"]
                props = dict(node)
                try:
                    labels = list(node.labels)
                    props['labels'] = labels
                except Exception:
                    pass
                nodes.append(props)
            return nodes
    else:
        matches = []
        # iterate nodes in memory graph
        for uid, data in list(NX.nodes(data=True)):
            # collect candidate textual fields
            fields = []
            for k in ("name", "value", "misp_id", "stix_id", "description"):
                v = data.get(k)
                if v:
                    fields.append(str(v).lower())
            # additionally include labels list if present
            lbls = data.get("labels")
            if lbls:
                try:
                    fields.extend([str(x).lower() for x in lbls])
                except Exception:
                    fields.append(str(lbls).lower())
            hay = " ".join(fields)
            if name_query.lower() in hay:
                d = data.copy()
                d["_uid"] = uid
                matches.append(d)
                if len(matches) >= limit:
                    break
        return matches

def get_subgraph(uid: str, depth: int = 1):
    """
    Return nodes and edges around uid up to given depth.
    For Neo4j, we return comparable JSON.
    """
    if USE_NEO4J:
        with driver.session() as session:
            q = (
                "MATCH (n {uid:$uid})-[*0.." + str(depth) + "]-(m) "
                "WITH collect(distinct n) + collect(distinct m) as nodes "
                "UNWIND nodes as nd "
                "RETURN distinct nd"
            )
            res = session.run(q, uid=uid)
            nodes = []
            for r in res:
                nodes.append(dict(r["nd"]))
            # edges: simple approach - fetch relationships
            q2 = "MATCH (a {uid:$uid})-[r*1.." + str(depth) + "]-(b) RETURN a, r, b"
            res2 = session.run(q2, uid=uid)
            edges = []
            for r in res2:
                # r['r'] is a list of rels; flatten
                rels = r['r']
                for rel in rels:
                    edges.append({
                        'start': dict(rel.start_node).get('uid'),
                        'end': dict(rel.end_node).get('uid'),
                        'type': rel.type
                    })
            return {"nodes": nodes, "edges": edges}
    else:
        import networkx as nx
        if uid not in NX:
            return {"nodes": [], "edges": []}
        nodes = set([uid])
        frontier = {uid}
        for _ in range(depth):
            new_frontier = set()
            for n in frontier:
                new_frontier.update(NX.neighbors(n))
            nodes.update(new_frontier)
            frontier = new_frontier
        node_list = []
        for n in nodes:
            d = NX.nodes[n].copy()
            d['_uid'] = n
            node_list.append(d)
        edges = []
        for a in nodes:
            for b in NX.neighbors(a):
                if b in nodes:
                    edges.append({"start": a, "end": b, "type": NX.get_edge_data(a, b)})
        return {"nodes": node_list, "edges": edges}
