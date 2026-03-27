"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getModels, setModel } from "@/lib/api";
import type { ModelsResponse, ModelProvider } from "@/lib/types";

/** Сокращение длинного имени модели для отображения. */
function truncateModel(name: string, maxLen = 28): string {
  if (name.length <= maxLen) return name;
  const parts = name.split("/");
  const last = parts[parts.length - 1];
  if (last.length <= maxLen) return last;
  return last.slice(0, maxLen - 1) + "\u2026";
}

/** Иконка провайдера. */
function providerIcon(id: string): string {
  if (id === "ollama") return "\uD83D\uDDA5\uFE0F";
  if (id === "openai") return "\u2601\uFE0F";
  if (id === "anthropic") return "\uD83E\uDDE0";
  return "\uD83E\uDD16";
}

/** Цвет индикатора провайдера. */
function providerDotColor(id: string): string {
  if (id === "ollama") return "bg-emerald-500";
  if (id === "openai") return "bg-blue-500";
  if (id === "anthropic") return "bg-orange-500";
  return "bg-gray-400";
}

export default function ModelSelector() {
  const [data, setData] = useState<ModelsResponse | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  const fetchModels = useCallback(async () => {
    try {
      const resp = await getModels();
      setData(resp);
      setError(null);
    } catch {
      setError("Не удалось загрузить модели");
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  /* Закрытие по клику вне */
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function handleSelect(provider: ModelProvider, model: string) {
    if (!provider.configured) return;
    setLoading(true);
    setOpen(false);
    try {
      await setModel(provider.id, model);
      await fetchModels();
    } catch {
      setError("Ошибка переключения модели");
    } finally {
      setLoading(false);
    }
  }

  if (!data) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
        <span className="hidden sm:inline">
          {error ?? "Загрузка..."}
        </span>
      </div>
    );
  }

  const currentShort = truncateModel(data.current_model, 22);
  const dotColor = providerDotColor(data.current_provider);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        disabled={loading}
        className="flex items-center gap-1.5 rounded-md border border-border bg-background px-2 py-1 text-xs transition-colors hover:bg-muted disabled:opacity-50"
      >
        <span className={`h-2 w-2 rounded-full ${dotColor}`} />
        <span className="hidden sm:inline font-medium">
          {loading ? "..." : currentShort}
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

      {error && (
        <div className="absolute right-0 top-full z-50 mt-1 rounded-md bg-destructive/10 px-2 py-1 text-xs text-destructive">
          {error}
        </div>
      )}

      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 min-w-64 rounded-lg border border-border bg-popover shadow-md">
          <div className="px-3 py-2 text-xs font-medium text-muted-foreground border-b border-border">
            Модель для анализа
          </div>

          {data.providers.map((provider) => (
            <div key={provider.id}>
              {/* Заголовок провайдера */}
              <div className="flex items-center gap-1.5 bg-muted/50 px-3 py-1.5 text-xs font-semibold text-muted-foreground">
                <span>{providerIcon(provider.id)}</span>
                <span>{provider.name}</span>
                {!provider.configured && (
                  <span className="ml-auto text-destructive font-normal text-[10px]">
                    Требуется API-ключ
                  </span>
                )}
              </div>

              {/* Модели провайдера */}
              {provider.models.map((model) => {
                const isActive =
                  data.current_provider === provider.id &&
                  data.current_model === model;
                return (
                  <button
                    key={`${provider.id}-${model}`}
                    type="button"
                    disabled={!provider.configured}
                    onClick={() => handleSelect(provider, model)}
                    className={`flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm transition-colors ${
                      isActive
                        ? "bg-accent font-medium text-accent-foreground"
                        : provider.configured
                          ? "text-popover-foreground hover:bg-accent/50"
                          : "text-muted-foreground cursor-not-allowed opacity-50"
                    }`}
                  >
                    {isActive && (
                      <span className="text-primary text-xs">{"\u2713"}</span>
                    )}
                    <span className="truncate">
                      {truncateModel(model, 36)}
                    </span>
                  </button>
                );
              })}
            </div>
          ))}

          {data.providers.every((p) => p.models.length === 0) && (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Нет доступных моделей
            </div>
          )}
        </div>
      )}
    </div>
  );
}
