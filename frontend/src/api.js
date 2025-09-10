// frontend/src/api.js
import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

let token = null;
export function setToken(t) { token = t; }

const client = axios.create({
  baseURL: BASE,
});

client.interceptors.request.use(config => {
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

export default {
  login: (username, password) => client.post("/auth/login", { username, password }),
  ingestStix: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return client.post("/ingest/stix", fd, { headers: { "Content-Type": "multipart/form-data" }});
  },
  ingestMisp: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return client.post("/ingest/misp", fd, { headers: { "Content-Type": "multipart/form-data" }});
  },
  search: (q) => client.get("/search", { params: { q }}),
  graph: (uid, depth=1) => client.get(`/graph/${encodeURIComponent(uid)}?depth=${depth}`),
  mlAnomaly: (uid, depth=2) => client.get(`/ml/anomaly/${encodeURIComponent(uid)}?depth=${depth}`),
  mlCluster: (uid, depth=2) => client.get(`/ml/cluster/${encodeURIComponent(uid)}?depth=${depth}`)
};
