/**
 * API-клиент для ZanAlytics backend.
 */

import type {
  Document,
  DocumentDetail,
  Finding,
  FindingDetail,
  GraphData,
  HealthResponse,
  ModelsResponse,
  Norm,
  PaginatedResponse,
  StatsResponse,
  AnalysisEvent,
} from "@/lib/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/* ───────── Утилиты ───────── */

/**
 * Универсальный fetch-обёртка. Данные возвращаются как есть (snake_case).
 */
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    ...init,
    redirect: "follow",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(
      `API ${response.status}: ${response.statusText} — ${text}`,
    );
  }

  const json: unknown = await response.json();
  return json as T;
}

/* ───────── Модели / провайдеры ───────── */

export function getModels(): Promise<ModelsResponse> {
  return apiFetch<ModelsResponse>("/api/models");
}

export function setModel(model: string): Promise<{ status: string; model: string }> {
  return apiFetch("/api/models", {
    method: "POST",
    body: JSON.stringify({ model }),
  });
}

/* ───────── Статистика ───────── */

export function getStats(): Promise<StatsResponse> {
  return apiFetch<StatsResponse>("/api/stats");
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health");
}

/* ───────── Документы ───────── */

interface DocumentsParams {
  page?: number;
  limit?: number;
  domain?: string;
  docType?: string;
  status?: string;
}

export function getDocuments(
  params: DocumentsParams = {},
): Promise<PaginatedResponse<Document>> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("limit", String(params.limit ?? 20));
  if (params.domain) query.set("domain", params.domain);
  if (params.docType) query.set("doc_type", params.docType);
  if (params.status) query.set("status", params.status);
  return apiFetch<PaginatedResponse<Document>>(
    `/api/documents?${query.toString()}`,
  );
}

export function getDocument(id: string): Promise<DocumentDetail> {
  return apiFetch<DocumentDetail>(`/api/documents/${encodeURIComponent(id)}`);
}

export function getDocumentNorms(
  docId: string,
): Promise<{ items: Norm[]; total: number }> {
  return apiFetch<{ items: Norm[]; total: number }>(
    `/api/documents/${encodeURIComponent(docId)}/norms`,
  );
}

/* ───────── Обнаружения ───────── */

interface FindingsParams {
  page?: number;
  limit?: number;
  type?: string;
  severity?: string;
  domain?: string;
}

export function getFindings(
  params: FindingsParams = {},
): Promise<PaginatedResponse<Finding>> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("limit", String(params.limit ?? 20));
  if (params.type) query.set("type", params.type);
  if (params.severity) query.set("severity", params.severity);
  if (params.domain) query.set("domain", params.domain);
  return apiFetch<PaginatedResponse<Finding>>(
    `/api/findings?${query.toString()}`,
  );
}

export function getFinding(id: number): Promise<FindingDetail> {
  return apiFetch<FindingDetail>(`/api/findings/${id}`);
}

/* ───────── Граф ───────── */

export function getGraph(): Promise<GraphData> {
  return apiFetch<GraphData>("/api/graph");
}

/* ───────── Поиск ───────── */

interface SearchParams {
  query: string;
  limit?: number;
}

export function search(
  params: SearchParams,
): Promise<PaginatedResponse<Finding>> {
  const query = new URLSearchParams();
  query.set("q", params.query);
  if (params.limit) query.set("limit", String(params.limit));
  return apiFetch<PaginatedResponse<Finding>>(
    `/api/search?${query.toString()}`,
  );
}

/* ───────── Сравнение ───────── */

export function compare(
  normAId: string,
  normBId: string,
): Promise<FindingDetail> {
  return apiFetch<FindingDetail>(
    `/api/compare/${encodeURIComponent(normAId)}/${encodeURIComponent(normBId)}`,
  );
}

/* ───────── SSE анализ ───────── */

/**
 * Подключается к SSE-стриму анализа текста.
 * Вызывает onEvent для каждого полученного события.
 * Возвращает AbortController для отмены.
 */
export function analyzeText(
  text: string,
  onEvent: (event: AnalysisEvent) => void,
): AbortController {
  const controller = new AbortController();

  const url = `${API_BASE}/api/analyze`;

  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok || !response.body) {
        onEvent({
          event: "error",
          data: { message: `Ошибка: ${response.status} ${response.statusText}` },
        });
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";

        for (const block of lines) {
          if (!block.trim()) continue;

          let eventType = "message";
          let eventData = "";

          for (const line of block.split("\n")) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              eventData = line.slice(6);
            }
          }

          if (eventData) {
            try {
              const parsed: unknown = JSON.parse(eventData);
              onEvent({
                event: eventType as AnalysisEvent["event"],
                data: parsed as AnalysisEvent["data"],
              });
            } catch {
              /* пропускаем невалидный JSON */
            }
          }
        }
      }
    })
    .catch((err: unknown) => {
      if (err instanceof Error && err.name !== "AbortError") {
        onEvent({
          event: "error",
          data: { message: err.message },
        });
      }
    });

  return controller;
}
