// frontend/src/App.jsx
import React, { useState } from "react";
import api, { setToken } from "./api";
import GraphView from "./components/GraphView";
import NodeDetail from "./components/NodeDetail";

export default function App(){
  const [logged, setLogged] = useState(false);
  const [query, setQuery] = useState("");
  const [graphUid, setGraphUid] = useState(null);
  const [nodeDetail, setNodeDetail] = useState(null);

  async function doLogin(e){
    e.preventDefault();
    const user = e.target.username.value;
    const pass = e.target.password.value;
    try {
      const res = await api.login(user, pass);
      setToken(res.data.access_token);
      setLogged(true);
      alert("Logged in");
    } catch (err) {
      alert("Login failed: " + (err?.response?.data?.detail || err.message));
    }
  }

  async function doSearch(e){
    e.preventDefault();
    const q = query;
    try {
      const res = await api.search(q);
      if(res.data.length === 0){
        alert("No nodes found");
      } else {
        // pick first match uid - rely on backend _uid or stix_id or uid
        const n = res.data[0];
        const uid = n._uid || n.stix_id || n.uid || n.misp_id;
        setGraphUid(uid);
      }
    } catch (err) {
      alert("Search error: " + err.message);
    }
  }

  async function handleUploadStix(ev){
    const f = ev.target.files[0];
    if(!f) return;
    try {
      const res = await api.ingestStix(f);
      alert(`Stix ingested. nodes: ${res.data.ingested_nodes}, rels: ${res.data.ingested_rels}`);
    } catch (err) {
      alert("Ingest error: " + err.message);
    }
  }

  async function handleUploadMisp(ev){
    const f = ev.target.files[0];
    if(!f) return;
    try {
      const res = await api.ingestMisp(f);
      alert(`MISP ingested. nodes: ${res.data.ingested_nodes}, rels: ${res.data.ingested_rels}`);
    } catch (err) {
      alert("Ingest error: " + err.message);
    }
  }

  return (<div style={{padding:20, fontFamily:'Arial'}}>
    <h1>ThreatVerse (Local)</h1>
    {!logged && (
      <form onSubmit={doLogin}>
        <h3>Login</h3>
        <input name="username" placeholder="username" defaultValue="admin" />
        <input name="password" type="password" placeholder="password" defaultValue="ChangeMe123" />
        <button>Login</button>
      </form>
    )}

    <div style={{marginTop:20}}>
      <h3>Ingest</h3>
      <div>
        <label>Upload STIX bundle (JSON):</label>
        <input type="file" accept=".json" onChange={handleUploadStix} />
      </div>
      <div>
        <label>Upload MISP export (JSON):</label>
        <input type="file" accept=".json" onChange={handleUploadMisp} />
      </div>
    </div>

    <div style={{marginTop:20}}>
      <h3>Search & Explore</h3>
      <form onSubmit={doSearch}>
        <input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Search by name/IP/domain..." />
        <button>Search and open subgraph</button>
      </form>
    </div>

    <div style={{display:'flex', gap:20, marginTop:20}}>
      <div style={{flex:1}}>
        <h3>Graph</h3>
        {graphUid ? <GraphView uid={graphUid} onNodeClick={setNodeDetail} /> : <div>Search or ingest sample data to see graph.</div>}
      </div>
      <div style={{width:350}}>
        <h3>Details</h3>
        <NodeDetail node={nodeDetail} />
      </div>
    </div>
  </div>);
}
