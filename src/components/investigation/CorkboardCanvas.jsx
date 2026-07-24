import { useState, useEffect, useRef } from 'react';

/**
 * The "Reconstruction Board" / case-board canvas: suspect photo cards,
 * sticky notes, and dashed red-string connectors on a free-form surface.
 * Renders `nodes` (percentage-positioned) plus dashed connector lines
 * between them, on a subtly textured dark surface.
 *
 * nodes: [{ id, x, y (0-100 %), type: 'suspect' | 'evidence' | 'note', data }]
 * connectors: [{ fromId, toId, label? }]
 * renderNode(node) returns the JSX for a single pinned card.
 */
export default function CorkboardCanvas({ nodes = [], connectors = [], renderNode }) {
  const containerRef = useRef(null);
  const [positions, setPositions] = useState(() => 
    Object.fromEntries(nodes.map((n) => [n.id, { x: n.x, y: n.y }]))
  );
  const [draggingId, setDraggingId] = useState(null);

  // Sync new nodes that might appear
  useEffect(() => {
    setPositions((prev) => {
      const next = { ...prev };
      let changed = false;
      nodes.forEach((n) => {
        if (!next[n.id]) {
          next[n.id] = { x: n.x, y: n.y };
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, [nodes]);

  const handlePointerDown = (e, id) => {
    if (e.button !== 0) return; // Only left click
    e.target.setPointerCapture(e.pointerId);
    setDraggingId(id);
    e.stopPropagation();
  };

  const handlePointerMove = (e) => {
    if (!draggingId || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const dx = (e.movementX / rect.width) * 100;
    const dy = (e.movementY / rect.height) * 100;
    
    setPositions((prev) => {
      const current = prev[draggingId];
      if (!current) return prev;
      return {
        ...prev,
        [draggingId]: {
          x: Math.min(100, Math.max(0, current.x + dx)),
          y: Math.min(100, Math.max(0, current.y + dy)),
        },
      };
    });
  };

  const handlePointerUp = (e) => {
    if (draggingId) {
      e.target.releasePointerCapture(e.pointerId);
      setDraggingId(null);
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[480px] panel overflow-hidden select-none"
      style={{
        backgroundImage: 'radial-gradient(rgba(255,255,255,0.035) 1px, transparent 1px)',
        backgroundSize: '18px 18px',
        touchAction: 'none' // Prevent scrolling while dragging
      }}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
        {connectors.map((conn, i) => {
          const from = positions[conn.fromId];
          const to = positions[conn.toId];
          if (!from || !to) return null;
          return (
            <line
              key={i}
              x1={`${from.x}%`}
              y1={`${from.y}%`}
              x2={`${to.x}%`}
              y2={`${to.y}%`}
              stroke="#C0392B"
              strokeWidth={1}
              strokeDasharray="6 4"
              opacity={0.7}
            />
          );
        })}
      </svg>

      {nodes.map((node) => {
        const pos = positions[node.id] || { x: node.x, y: node.y };
        const isDragging = draggingId === node.id;
        return (
          <div
            key={node.id}
            className={`absolute -translate-x-1/2 -translate-y-1/2 transition-shadow cursor-grab ${isDragging ? 'cursor-grabbing z-50 shadow-2xl scale-[1.02]' : 'z-10 hover:z-20'}`}
            style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
            onPointerDown={(e) => handlePointerDown(e, node.id)}
          >
            <div className="pointer-events-none">
              {renderNode ? renderNode(node) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}
