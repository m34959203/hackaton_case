"use client";

import { useCallback, useState, useMemo, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { getGraph } from "@/lib/api";
import type { GraphNode, GraphLink } from "@/lib/types";
import GraphControls from "./GraphControls";
import GraphNodeInfo from "./GraphNodeInfo";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

/* Динамический импорт (Three.js не работает в SSR) */
const ForceGraph = dynamic(() => import("react-force-graph-3d"), {
  ssr: false,
  loading: () => <Skeleton className="h-full w-full" />,
});

/* Цвета узлов по типу документа */
const NODE_COLORS: Record<string, string> = {
  code: "#4f46e5",
  law: "#16a34a",
  decree: "#9333ea",
  resolution: "#6b7280",
  order: "#f97316",
};

/* Цвета рёбер по типу связи */
const EDGE_COLORS: Record<string, string> = {
  contradiction: "#ef4444",
  duplication: "#f97316",
  reference: "#d1d5db",
};

/** Основной 3D-граф связей между документами. */
export default function ForceGraph3DView() {
  const containerRef = useRef<HTMLDivElement>(null);

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedLink, setSelectedLink] = useState<GraphLink | null>(null);
  const [nodeFilter, setNodeFilter] = useState<string | null>(null);
  const [edgeTypes, setEdgeTypes] = useState<Record<string, boolean>>({
    contradiction: true,
    duplication: true,
    reference: true,
  });
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  const { data: rawGraph, isLoading, error, refetch } = useQuery({
    queryKey: ["graph"],
    queryFn: getGraph,
    retry: false,
  });

  /* Отслеживаем размер контейнера */
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const updateSize = () => {
      setDimensions({
        width: container.clientWidth,
        height: container.clientHeight,
      });
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  /* Фильтрация графа */
  const filteredGraph = useMemo(() => {
    if (!rawGraph) return { nodes: [], links: [] };

    let nodes = rawGraph.nodes;
    if (nodeFilter) {
      nodes = nodes.filter((n) => n.group === nodeFilter);
    }
    const nodeIds = new Set(nodes.map((n) => n.id));

    const links = rawGraph.links.filter((l) => {
      const typeMatch = l.type ? edgeTypes[l.type] !== false : true;
      const nodesMatch =
        nodeIds.has(String(l.source)) && nodeIds.has(String(l.target));
      return typeMatch && nodesMatch;
    });

    return { nodes, links };
  }, [rawGraph, nodeFilter, edgeTypes]);

  const handleNodeClick = useCallback((node: Record<string, unknown>) => {
    setSelectedLink(null);
    setSelectedNode(node as unknown as GraphNode);
  }, []);

  const handleLinkClick = useCallback((link: Record<string, unknown>) => {
    setSelectedNode(null);
    setSelectedLink(link as unknown as GraphLink);
  }, []);

  const handleToggleEdge = useCallback((type: string) => {
    setEdgeTypes((prev) => ({ ...prev, [type]: !prev[type] }));
  }, []);

  const handleCloseInfo = useCallback(() => {
    setSelectedNode(null);
    setSelectedLink(null);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <Skeleton className="h-8 w-48 mx-auto" />
          <p className="text-sm text-muted-foreground">Загрузка графа...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-muted-foreground">
            Ошибка загрузки графа. Убедитесь, что backend запущен.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Повторить
          </Button>
        </div>
      </div>
    );
  }

  if (!rawGraph || rawGraph.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">
          Граф пуст. Запустите анализ для построения связей.
        </p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative h-full w-full">
      <GraphControls
        edgeTypes={edgeTypes}
        onToggleEdge={handleToggleEdge}
        nodeFilter={nodeFilter}
        onSetNodeFilter={setNodeFilter}
      />

      <GraphNodeInfo
        node={selectedNode}
        link={selectedLink}
        onClose={handleCloseInfo}
      />

      <ForceGraph
        width={dimensions.width}
        height={dimensions.height}
        graphData={filteredGraph}
        backgroundColor="#09090b"
        nodeId="id"
        nodeLabel="name"
        nodeVal="val"
        nodeColor={(node: Record<string, unknown>) => {
          const n = node as unknown as GraphNode;
          return n.color ?? NODE_COLORS[n.group ?? ""] ?? "#6b7280";
        }}
        nodeOpacity={0.9}
        nodeRelSize={6}
        linkColor={(link: Record<string, unknown>) => {
          const l = link as unknown as GraphLink;
          return l.color ?? EDGE_COLORS[l.type ?? ""] ?? "#d1d5db";
        }}
        linkOpacity={0.6}
        linkWidth={(link: Record<string, unknown>) => {
          const l = link as unknown as GraphLink;
          return l.type === "contradiction" ? 2 : 1;
        }}
        linkDirectionalParticles={(link: Record<string, unknown>) => {
          const l = link as unknown as GraphLink;
          return l.type === "contradiction" ? 4 : 0;
        }}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleColor={(link: Record<string, unknown>) => {
          const l = link as unknown as GraphLink;
          return EDGE_COLORS[l.type ?? ""] ?? "#d1d5db";
        }}
        onNodeClick={handleNodeClick}
        onLinkClick={handleLinkClick}
        enableNodeDrag
        enableNavigationControls
      />
    </div>
  );
}
