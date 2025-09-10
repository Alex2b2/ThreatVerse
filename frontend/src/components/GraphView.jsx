// frontend/src/components/GraphView.jsx
import React, { useEffect, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import api from "../api";

export default function GraphView({ uid, depth=1, onNodeClick }){
  const [elements, setElements] = useState([]);

  useEffect(()=>{
    async function fetchGraph(){
      try {
        const res = await api.graph(uid, depth);
        const nodes = res.data.nodes.map(n=>{
          const id = n._uid || n.uid || n.stix_id || n.misp_id || n.name || Math.random().toString(36).slice(2,9);
          return {
            data: { id, label: n.name || n.value || n.misp_id || id },
            classes: (n.stix_type || n.labels || []).join(' ')
          };
        });
        const edges = (res.data.edges || []).map((e,i)=>{
          const start = e.start;
          const end = e.end;
          const id = `e${i}`;
          return { data: { id, source: start, target: end, label: e.type || '' } };
        });
        setElements([...nodes, ...edges]);
      } catch (err) {
        console.error("Graph fetch error", err);
      }
    }
    fetchGraph();
  }, [uid]);

  function handleTap(evt){
    const node = evt.target;
    if(node && node.data) {
      const id = node.data('id');
      const label = node.data('label');
      onNodeClick({ id, label });
    }
  }

  return (<div style={{height:600, border:'1px solid #ddd'}}>
    <CytoscapeComponent elements={elements} style={{width:'100%', height:'100%'}}
      stylesheet={[
        { selector: 'node', style: { 'label': 'data(label)', 'width': 40, 'height':40, 'text-valign':'center', 'text-halign':'center' } },
        { selector: 'edge', style: { 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'label':'data(label)' } }
      ]}
      cy={(cy) => {
        cy.on('tap', 'node', handleTap);
        cy.layout({ name: 'cose' }).run();
      }}
    />
  </div>);
}
