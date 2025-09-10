// frontend/src/components/NodeDetail.jsx
import React from "react";

export default function NodeDetail({ node }){
  if(!node) return <div>No node selected</div>;
  return (<div>
    <h4>{node.label || node.id}</h4>
    <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(node, null, 2)}</pre>
  </div>);
}
