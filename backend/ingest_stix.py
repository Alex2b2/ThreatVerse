# backend/ingest_stix.py
"""
Ingest a STIX2 bundle (uploaded as JSON) and create/merge nodes + relationships
We use a conservative mapping: AttackPattern -> Technique, Malware -> Malware, IntrusionSet -> ThreatActor, Vulnerability -> Vulnerability, Indicator -> Indicator.
"""

import json
from stix2 import parse as stix_parse
from db import merge_node, create_relationship
from typing import Tuple

def ingest_stix_json(stix_json: dict) -> Tuple[int, int]:
    objects = stix_json.get("objects", [])
    ingested_nodes = 0
    ingested_rels = 0

    # Keep a map stix id -> node uid used in graph
    id_map = {}

    for obj in objects:
        t = obj.get("type")
        stix_id = obj.get("id") or obj.get("uuid") or obj.get("name")
        uid = stix_id  # use stix id as uid to keep uniqueness
        if t in ("attack-pattern", "malware", "intrusion-set", "vulnerability", "indicator", "report"):
            # Simplified property pick:
            props = {
                "name": obj.get("name") or obj.get("description")[:120] if obj.get("description") else obj.get("type"),
                "description": obj.get("description", ""),
                "stix_type": t,
                "stix_id": stix_id
            }
            label = {
                "attack-pattern": "Technique",
                "malware": "Malware",
                "intrusion-set": "ThreatActor",
                "vulnerability": "Vulnerability",
                "indicator": "Indicator",
                "report": "Report"
            }.get(t, "Entity")
            merge_node(label, uid, props)
            id_map[stix_id] = uid
            ingested_nodes += 1

    # Now ingest relationships (simplified: look for 'relationships' or references)
    for obj in objects:
        if obj.get("type") == "relationship":
            src = obj.get("source_ref") or obj.get("relationship_type")
            tgt = obj.get("target_ref")
            rel_type = obj.get("relationship_type", "RELATED_TO").upper()
            if src and tgt and src in id_map and tgt in id_map:
                create_relationship(id_map[src], id_map[tgt], rel_type)
                ingested_rels += 1
        # also look for common STIX properties like 'object_marking_refs' etc. (omitted for brevity)
    return ingested_nodes, ingested_rels
