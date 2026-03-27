"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getModels, setModel } from "@/lib/api";
import type { ModelsResponse } from "@/lib/types";

export default function ModelSelector() {
  const [data, setData] = useState<ModelsResponse | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const fetchModels = useCallback(async () => {
    try {
      const resp = await getModels();
      setData(resp);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function handleSelect(model: string) {
    setLoading(true);
    setOpen(false);
    try {
      await setModel(model);
      await fetchModels();
    } finally {
      setLoading(false);
    }
  }

  if (!data) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
        <span className="hidden sm:inline">Загрузка...</span>
      </div>
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        disabled={loading}
        className="flex items-center gap-1.5 rounded-md border border-border bg-background px-2 py-1 text-xs transition-colors hover:bg-muted disabled:opacity-50"
      >
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        <span className="hidden sm:inline font-medium">
          {loading ? "..." : data.current_model}
        </span>
        <svg
          className={`h-3 w-3 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 min-w-56 rounded-lg border border-border bg-popover shadow-md">
          <div className="px-3 py-2 text-xs font-medium text-muted-foreground border-b border-border">
            Google Gemini — модель анализа
          </div>
          {data.available.map((model) => {
            const isActive = data.current_model === model;
            return (
              <button
                key={model}
                type="button"
                onClick={() => handleSelect(model)}
                className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors ${
                  isActive
                    ? "bg-accent font-medium text-accent-foreground"
                    : "text-popover-foreground hover:bg-accent/50"
                }`}
              >
                {isActive && <span className="text-primary text-xs">✓</span>}
                <span className="truncate">{model}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
