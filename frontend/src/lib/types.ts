/**
 * TypeScript-интерфейсы для ZanAlytics.
 * Соответствуют Pydantic-моделям backend (snake_case → camelCase).
 */

/* ───────── Документы и нормы ───────── */

export interface Document {
  id: string;
  title: string;
  docType: string;
  dateAdopted: string | null;
  dateAmended: string | null;
  status: string;
  domain: string | null;
  adoptingBody: string | null;
  legalForce: string | null;
  normsCount: number;
  findingsCount: number;
}

export interface Norm {
  id: string;
  docId: string;
  article: number;
  paragraph: number | null;
  text: string;
  clusterId: number | null;
  clusterTopic: string | null;
  findingsCount: number;
}

export interface NormBrief {
  id: string;
  docId: string;
  article: number;
  paragraph: number | null;
  text: string;
}

export interface DocumentDetail extends Document {
  norms: NormBrief[];
}

export interface CrossRef {
  id: number;
  fromDoc: string;
  toDoc: string;
  contextText: string | null;
}

/* ───────── Обнаружения ───────── */

export interface Finding {
  id: number;
  type: "contradiction" | "duplication" | "outdated";
  severity: "high" | "medium" | "low";
  confidence: number;
  normA: NormBrief;
  normB: NormBrief | null;
  explanation: string;
  clusterTopic: string | null;
  createdAt: string | null;
}

export interface FindingDetail {
  id: number;
  type: "contradiction" | "duplication" | "outdated";
  severity: "high" | "medium" | "low";
  confidence: number;
  normA: NormBrief;
  normB: NormBrief | null;
  explanation: string;
  recommendation: string | null;
  clusterId: number | null;
  clusterTopic: string | null;
  createdAt: string | null;
}

/* ───────── Граф ───────── */

export interface GraphNode {
  id: string;
  name: string;
  group: string | null;
  val: number;
  color: string | null;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string | null;
  color: string | null;
  value: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

/* ───────── Статистика и здоровье ───────── */

export interface DomainStat {
  domain: string;
  docsCount: number;
  normsCount: number;
  findingsCount: number;
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
  totalDocuments: number;
  totalNorms: number;
  totalFindings: number;
  findingsByType: FindingTypeStat[];
  findingsBySeverity: FindingSeverityStat[];
  topDomains: DomainStat[];
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
  pages: number;
}

/* ───────── SSE-события анализа ───────── */

export interface AnalysisEvent {
  event: "progress" | "finding" | "complete" | "error";
  data: AnalysisProgressData | Finding | AnalysisCompleteData | AnalysisErrorData;
}

export interface AnalysisProgressData {
  step: string;
  progress: number;
  message: string;
}

export interface AnalysisCompleteData {
  findingsCount: number;
  message: string;
}

export interface AnalysisErrorData {
  message: string;
}
