import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { KnowledgeNode, KnowledgeEdge } from '../../types/electron';

interface KnowledgeGraphProps {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  width?: number;
  height?: number;
  onNodeClick?: (node: KnowledgeNode) => void;
}

const MASTERY_COLORS = {
  high: '#22c55e',   // green — mastery >= 0.7
  medium: '#f59e0b', // yellow — mastery >= 0.4
  low: '#ef4444',    // red — mastery < 0.4
  none: '#6b7280',   // gray — not started
};

function getMasteryColor(mastery: number): string {
  if (mastery >= 0.7) return MASTERY_COLORS.high;
  if (mastery >= 0.4) return MASTERY_COLORS.medium;
  if (mastery > 0) return MASTERY_COLORS.low;
  return MASTERY_COLORS.none;
}

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  nodes,
  edges,
  width = 600,
  height = 400,
  onNodeClick,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g');

    // Build D3 simulation data
    const simNodes = nodes.map((n) => ({ ...n, x: 0, y: 0 }));
    const simLinks = edges.map((e) => ({
      source: e.source,
      target: e.target,
      relationship: e.relationship,
    }));

    const simulation = d3
      .forceSimulation(simNodes as any)
      .force(
        'link',
        d3
          .forceLink(simLinks)
          .id((d: any) => d.id)
          .distance(100)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Links
    const link = g
      .append('g')
      .selectAll('line')
      .data(simLinks)
      .enter()
      .append('line')
      .attr('stroke', '#4b5563')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', (d: any) =>
        d.relationship === 'prerequisite' ? 'none' : '4 2'
      );

    // Node groups
    const node = g
      .append('g')
      .selectAll('g')
      .data(simNodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .on('click', (_event: any, d: any) => {
        if (onNodeClick) onNodeClick(d as KnowledgeNode);
      });

    // Node circles
    node
      .append('circle')
      .attr('r', (d: any) => 12 + d.mastery * 12)
      .attr('fill', (d: any) => getMasteryColor(d.mastery))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .attr('opacity', 0.85);

    // Node labels
    node
      .append('text')
      .text((d: any) => d.label)
      .attr('dy', (d: any) => 20 + d.mastery * 12 + 4)
      .attr('text-anchor', 'middle')
      .attr('fill', '#d1d5db')
      .attr('font-size', '11px')
      .attr('font-weight', '500');

    // Mastery percentage inside node
    node
      .append('text')
      .text((d: any) => `${Math.round(d.mastery * 100)}%`)
      .attr('dy', 4)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .attr('font-size', '9px')
      .attr('font-weight', 'bold');

    // Simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Zoom
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.3, 3]).on('zoom', (event) => {
      g.attr('transform', event.transform);
    });
    svg.call(zoom);

    return () => {
      simulation.stop();
    };
  }, [nodes, edges, width, height, onNodeClick]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      className="bg-surface-dark rounded-lg border border-gray-800"
    />
  );
};
