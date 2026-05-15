import { useEffect, useRef, useState } from 'react';

interface GraphNode {
  id: string;
  label: string;
  type: string;
}

interface GraphEdge {
  from: string;
  to: string;
  label?: string;
}

interface KnowledgeGraphProps {
  data?: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
}

// Fabric.js types
declare global {
  interface Window {
    fabric: any;
  }
}

const typeColors: Record<string, string> = {
  language: '#8b5cf6',
  person: '#10b981',
  year: '#f59e0b',
  company: '#ec4899',
  field: '#06b6d4',
};

export default function KnowledgeGraph({ data }: KnowledgeGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<any>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const nodesRef = useRef<Map<string, any>>(new Map());

  useEffect(() => {
    const initCanvas = async () => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      // Load Fabric.js
      if (!window.fabric) {
        await new Promise<void>((resolve) => {
          const script = document.createElement('script');
          script.src = 'https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js';
          script.onload = () => resolve();
          document.head.appendChild(script);
        });
      }

      const fabric = window.fabric;
      fabricRef.current = new fabric.Canvas(canvas, {
        width: 800,
        height: 500,
        backgroundColor: '#0f172a',
        selection: false,
      });

      // Demo data
      const nodes = data?.nodes || [
        { id: 'python', label: 'Python', type: 'language' },
        { id: 'guido', label: 'Guido van Rossum', type: 'person' },
        { id: '1991', label: '1991', type: 'year' },
        { id: 'google', label: 'Google', type: 'company' },
        { id: 'ai', label: 'AI/ML', type: 'field' },
      ];

      const edges = data?.edges || [
        { from: 'python', to: 'guido', label: 'created_by' },
        { from: 'python', to: '1991', label: 'released_in' },
        { from: 'python', to: 'google', label: 'used_at' },
        { from: 'python', to: 'ai', label: 'used_for' },
      ];

      // Position nodes in a circle
      const centerX = 400;
      const centerY = 250;
      const radius = 180;

      nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / nodes.length;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);

        // Node circle
        const circle = new fabric.Circle({
          radius: 30,
          fill: '#1f2937',
          stroke: '#374151',
          strokeWidth: 2,
          originX: 'center',
          originY: 'center',
        });

        // Node label
        const text = new fabric.Text(node.label, {
          fontSize: 14,
          fill: '#f9fafb',
          fontFamily: 'system-ui',
          originX: 'center',
          originY: 'center',
          top: 45,
        });

        // Type indicator
        const typeColor = typeColors[node.type] || '#6b7280';
        const typeDot = new fabric.Circle({
          radius: 6,
          fill: typeColor,
          originX: 'center',
          originY: 'center',
          left: 20,
          top: -20,
        });

        // Group
        const group = new fabric.Group([circle, typeDot, text], {
          left: x,
          top: y,
          originX: 'center',
          originY: 'center',
          selectable: true,
          hasControls: false,
          hasBorders: false,
          hoverCursor: 'pointer',
          data: { id: node.id, type: node.type },
        });

        nodesRef.current.set(node.id, group);
        fabricRef.current.add(group);
      });

      // Draw edges
      edges.forEach(edge => {
        const from = nodesRef.current.get(edge.from);
        const to = nodesRef.current.get(edge.to);
        if (!from || !to) return;

        const line = new fabric.Line(
          [from.left || 0, from.top || 0, to.left || 0, to.top || 0],
          {
            stroke: '#374151',
            strokeWidth: 2,
            selectable: false,
            evented: false,
          }
        );

        // Edge label
        if (edge.label) {
          const midX = ((from.left || 0) + (to.left || 0)) / 2;
          const midY = ((from.top || 0) + (to.top || 0)) / 2;
          const label = new fabric.Text(edge.label, {
            fontSize: 11,
            fill: '#6b7280',
            fontFamily: 'system-ui',
            backgroundColor: '#0f172a',
            left: midX,
            top: midY - 10,
            originX: 'center',
            originY: 'center',
            selectable: false,
          });
          fabricRef.current.add(label);
        }

        fabricRef.current.add(line);
        fabricRef.current.sendToBack(line);
      });

      // Event handlers
      fabricRef.current.on('selection:created', (e: any) => {
        const selected = e.selected?.[0];
        if (selected?.data?.id) {
          setSelected(selected.data.id);
          selected.set('stroke', '#06b6d4');
          selected.item(0).set('stroke', '#06b6d4');
          fabricRef.current.renderAll();
        }
      });

      fabricRef.current.on('selection:cleared', () => {
        setSelected(null);
      });

      // Make nodes draggable
      fabricRef.current.on('object:moving', (e: any) => {
        const obj = e.target;
        
        // Update connected edges
        edges.forEach(edge => {
          const from = nodesRef.current.get(edge.from);
          const to = nodesRef.current.get(edge.to);
          
          if (from === obj || to === obj) {
            // Find and update the line
            fabricRef.current.getObjects('line').forEach((line: any) => {
              const lineFrom = line.x1 === (from?.left || 0) && line.y1 === (from?.top || 0);
              const lineTo = line.x1 === (to?.left || 0) && line.y1 === (to?.top || 0);
              if (lineFrom || lineTo) {
                if (lineFrom) {
                  line.set({ x1: obj.left, y1: obj.top });
                }
                if (lineTo) {
                  line.set({ x2: obj.left, y2: obj.top });
                }
              }
            });
          }
        });
      });
    };

    initCanvas();

    return () => {
      fabricRef.current?.dispose();
    };
  }, [data]);

  return (
    <div className="relative w-full h-full flex">
      <canvas ref={canvasRef} className="rounded-xl" />
      
      {/* Legend */}
      <div className="absolute top-4 left-4 bg-gray-900/80 backdrop-blur rounded-lg p-3 text-xs space-y-2">
        <div className="font-medium text-gray-300">Node Types</div>
        {Object.entries(typeColors).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></span>
            <span className="text-gray-400 capitalize">{type}</span>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="absolute top-4 right-4 flex gap-2">
        <button 
          onClick={() => {
            const canvas = fabricRef.current;
            if (!canvas) return;
            canvas.getObjects().forEach((obj: any) => {
              if (obj.data?.id) {
                obj.animate('left', Math.random() * 600 + 100, {
                  duration: 500,
                  onChange: () => canvas.renderAll(),
                });
                obj.animate('top', Math.random() * 300 + 100, {
                  duration: 500,
                  onChange: () => canvas.renderAll(),
                });
              }
            });
          }}
          className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          title="Randomize"
        >
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button 
          onClick={() => {
            const canvas = fabricRef.current;
            if (!canvas) return;
            canvas.setViewportTransform([1, 0, 0, 1, 0, 0]);
            canvas.renderAll();
          }}
          className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          title="Reset View"
        >
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        </button>
      </div>

      {/* Selected Info */}
      {selected && (
        <div className="absolute bottom-4 left-4 bg-gray-900/80 backdrop-blur rounded-lg p-4 max-w-xs">
          <div className="font-medium text-white">{selected}</div>
          <div className="text-sm text-gray-400">Click and drag to move</div>
        </div>
      )}
    </div>
  );
}