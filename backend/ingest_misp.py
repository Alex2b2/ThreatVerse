# backend/ingest_misp.py
"""
Ingest a MISP export (JSON) created by MISP 'export' or API (or a saved sample).
We expect a JSON dict with 'Event' and 'Attribute' lists (MISP standard export).
This is a simplified parser: each MISP Event becomes Report node, Attributes become Indicators and link to the report.
"""

import json
from db import merge_node, create_relationship

def ingest_misp_json(misp_json: dict):
    # Accept either {'Event': {...}} single event or {'Event': [ ... ]}
    ingested_nodes = 0
    ingested_rels = 0

    events = []
    if isinstance(misp_json, dict) and 'Event' in misp_json:
        ev = misp_json['Event']
        if isinstance(ev, list):
            events = ev
        else:
            events = [ev]
    elif isinstance(misp_json, dict) and 'response' in misp_json and 'Event' in misp_json['response']:
        events = misp_json['response']['Event']
    else:
        # maybe it's a list of events
        if isinstance(misp_json, list):
            events = misp_json

    for e in events:
        ev_id = str(e.get('id') or e.get('Event', {}).get('id') or e.get('uuid') or e.get('org_id', 'evt'))
        info = e.get('info') or (e.get('Event', {}).get('info') if e.get('Event') else '')
        report_props = {"name": info or f"MISP Event {ev_id}", "misp_id": ev_id, "description": info}
        merge_node("Report", f"misp-event-{ev_id}", report_props)
        ingested_nodes += 1

        attributes = e.get('Attribute') or (e.get('Event', {}).get('Attribute') if e.get('Event') else [])
        for a in attributes:
            val = a.get('value')
            typ = a.get('type', 'unknown')
            uid = f"misp-attr-{ev_id}-{typ}-{val}"
            props = {"value": val, "type": typ, "misp_type": typ}
            merge_node("Indicator", uid, props)
            ingested_nodes += 1
            create_relationship(f"misp-event-{ev_id}", uid, "HAS_INDICATOR")
            ingested_rels += 1

    return ingested_nodes, ingested_rels
