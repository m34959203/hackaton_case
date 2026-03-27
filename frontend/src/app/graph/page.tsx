"use client";

import ForceGraph3DView from "@/components/graph/ForceGraph3D";

export default function GraphPage() {
  return (
    <div className="flex flex-col h-[calc(100vh-5rem)]">
      <div className="mb-3">
        <h1 className="text-2xl font-bold tracking-tight">Граф связей</h1>
        <p className="text-sm text-muted-foreground">
          3D-визуализация связей между нормативно-правовыми актами
        </p>
      </div>
      <div className="flex-1 rounded-xl border border-border/50 overflow-hidden bg-[#020617] shadow-xl shadow-black/20">
        <ForceGraph3DView />
      </div>
    </div>
  );
}
