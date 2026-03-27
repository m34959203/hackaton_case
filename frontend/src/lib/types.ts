/**
 * TypeScript-интерфейсы для ZanAlytics.
 * Поля совпадают с backend API (snake_case).
 */

/* ───────── Документы и нормы ───────── */

export interface Document {
  id: string;
  title: string;
  doc_type: string;
  date_adopted: string | null;
  date_amended: string | null;
  status: string;
  domain: string | null;
  adopting_body: string | null;
  legal_force: string | null;
  norms_count: number;
  findings_count: number;
}

export interface Norm {
  id: string;
  doc_id: string;
  article: number;
  paragraph: number | null;
  text: string;
  cluster_id: number | null;
  cluster_topic: string | null;
  findings_count: number;
}

export interface NormBrief {
  id: string;
  doc_id: string;
  article: number;
  paragraph: number | null;
  text: string;
}

export interface DocumentDetail extends Document {
  norms: NormBrief[];
}

export interface CrossRef {
  id: number;
  from_doc: string;
  to_doc: string;
  context_text: string | null;
}

/* ───────── Обнаружения ───────── */

export interface Finding {
  id: number;
  type: "contradiction" | "duplication" | "outdated";
  severity: "high" | "medium" | "low";
  confidence: number;
  norm_a: NormBrief;
  norm_b: NormBrief | null;
  explanation: string;
  cluster_topic: string | null;
  created_at: string | null;
}

export interface FindingDetail {
  id: number;
  type: "contradiction" | "duplication" | "outdated";
  severity: "high" | "medium" | "low";
  confidence: number;
  norm_a: NormBrief;
  norm_b: NormBrief | null;
  explanation: string;
  recommendation: string | null;
  cluster_id: number | null;
  cluster_topic: string | null;
  created_at: string | null;
}

/* ───────── Граф ───────── */

export interface GraphNode {
  id: string;
  name: string;
  group: string | null;
  val: number;
  color: string | null;
  findingsCount: number;
  domain: string | null;
  status: string | null;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string | null;
  color: string | null;
  value: number;
  label: string | null;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

/* ───────── Статистика и здоровье ───────── */

export interface DomainStat {
  domain: string;
  docs_count: number;
  norms_count: number;
  findings_count: number;
}

export interface FindingTypeStat {
  type: string;
  count: number;
}

export interface FindingSeverityStat {
  severity: string;
  count: number;
}

export interface StatsResponse {
  total_documents: number;
  total_norms: number;
  total_findings: number;
  findings_by_type: FindingTypeStat[];
  findings_by_severity: FindingSeverityStat[];
  top_domains: DomainStat[];
}

export interface ServiceStatus {
  name: string;
  status: string;
  detail: string | null;
}

export interface HealthResponse {
  status: string;
  services: ServiceStatus[];
}

/* ───────── Пагинация ───────── */

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

/* ───────── SSE-события анализа ───────── */

export interface AnalysisEvent {
  event: "embedding" | "searching" | "analyzing" | "result" | "error";
  data: AnalysisStepData | AnalysisResultData | AnalysisErrorData;
}

/** Данные шага анализа (embedding / searching / analyzing). */
export interface AnalysisStepData {
  status: string;
  done?: boolean;
  count?: number;
}

/** Итоговый результат анализа (event: result). */
export interface AnalysisResultData {
  findings: AnalysisResultFinding[];
  summary: string;
  similar_norms: AnalysisSimilarNorm[];
}

export interface AnalysisResultFinding {
  type: string;
  severity: string;
  confidence: number;
  related_norm_id: string | null;
  explanation: string;
}

export interface AnalysisSimilarNorm {
  id: string;
  doc_id: string;
  article: number;
  paragraph: number | null;
  text: string;
  doc_title: string;
  similarity: number;
}

export interface AnalysisErrorData {
  message: string;
}

/* ───────── Модели (Gemini) ───────── */

export interface ModelsResponse {
  current_model: string;
  available: string[];
  provider: string;
}

/** Legacy aliases for backward compatibility. */
export interface AnalysisProgressData {
  step: string;
  progress: number;
  message: string;
}

export interface AnalysisCompleteData {
  findings_count: number;
  message: string;
}
