"""Построение графа связей между документами для визуализации."""

import json
import logging
from pathlib import Path

import networkx as nx

from app.database import get_db

logger = logging.getLogger(__name__)

# Цвета узлов по типу документа (см. CLAUDE.md)
_NODE_COLORS: dict[str, str] = {
    "code": "#3b82f6",        # синий — кодекс
    "law": "#22c55e",         # зелёный — закон
    "decree": "#a855f7",      # фиолетовый — указ
    "resolution": "#6b7280",  # серый — постановление
    "order": "#f59e0b",       # оранжевый — приказ
}

# Цвета рёбер по типу связи
_EDGE_COLORS: dict[str, str] = {
    "reference": "#6b7280",      # серый — перекрёстная ссылка
    "contradiction": "#ef4444",  # красный — противоречие
    "duplication": "#f97316",    # оранжевый — дублирование
}


class GraphBuilder:
    """Построение графа связей между документами."""

    def __init__(self) -> None:
        self._graph = nx.Graph()

    async def build_graph(self) -> dict:
        """Построить граф из cross_refs и findings.

        Узлы: документы (с метаданными: type, domain, status, findings_count).
        Рёбра:
            - cross_refs → type=reference
            - findings (contradiction/duplication) → type=contradiction/duplication

        Returns:
            Словарь графа в формате react-force-graph-3d: {nodes: [], links: []}.
        """
        self._graph.clear()

        # Загружаем данные
        documents = await self._load_documents()
        cross_refs = await self._load_cross_refs()
        findings = await self._load_findings()

        # Добавляем узлы (документы)
        for doc in documents:
            self._graph.add_node(
                doc["id"],
                title=doc["title"],
                doc_type=doc["doc_type"],
                domain=doc.get("domain", ""),
                status=doc["status"],
                findings_count=doc.get("findings_count", 0),
                norms_count=doc.get("norms_count", 0),
                color=_NODE_COLORS.get(doc["doc_type"], "#6b7280"),
            )

        # Добавляем рёбра из cross_refs
        for ref in cross_refs:
            from_doc = ref["from_doc"]
            to_doc = ref["to_doc"]

            # Добавляем узлы, если их нет (ссылки на внешние документы)
            if from_doc not in self._graph:
                self._graph.add_node(from_doc, title=from_doc, doc_type="unknown", color="#6b7280")
            if to_doc not in self._graph:
                self._graph.add_node(to_doc, title=to_doc, doc_type="unknown", color="#6b7280")

            self._graph.add_edge(
                from_doc,
                to_doc,
                type="reference",
                color=_EDGE_COLORS["reference"],
                context=ref.get("context_text", ""),
            )

        # Добавляем рёбра из findings (contradiction, duplication)
        for finding in findings:
            if not finding.get("doc_a") or not finding.get("doc_b"):
                continue
            if finding["doc_a"] == finding["doc_b"]:
                continue  # внутридокументные findings не добавляем как рёбра

            finding_type = finding["type"]
            edge_key = f"{finding['type']}_{finding['id']}"

            self._graph.add_edge(
                finding["doc_a"],
                finding["doc_b"],
                key=edge_key,
                type=finding_type,
                color=_EDGE_COLORS.get(finding_type, "#6b7280"),
                severity=finding["severity"],
                finding_id=finding["id"],
            )

        logger.info(
            "Граф построен: %d узлов, %d рёбер",
            self._graph.number_of_nodes(),
            self._graph.number_of_edges(),
        )

        return self.to_json()

    def to_json(self) -> dict:
        """Экспортировать граф в формат react-force-graph-3d.

        Returns:
            Словарь с ключами nodes[] и links[].
        """
        nodes: list[dict] = []
        for node_id, data in self._graph.nodes(data=True):
            nodes.append(
                {
                    "id": node_id,
                    "title": data.get("title", node_id),
                    "doc_type": data.get("doc_type", "unknown"),
                    "domain": data.get("domain", ""),
                    "status": data.get("status", ""),
                    "findings_count": data.get("findings_count", 0),
                    "norms_count": data.get("norms_count", 0),
                    "color": data.get("color", "#6b7280"),
                    "val": max(1, data.get("findings_count", 0) + 1),  # размер узла
                }
            )

        links: list[dict] = []
        for u, v, data in self._graph.edges(data=True):
            links.append(
                {
                    "source": u,
                    "target": v,
                    "type": data.get("type", "reference"),
                    "color": data.get("color", "#6b7280"),
                    "severity": data.get("severity", ""),
                    "finding_id": data.get("finding_id"),
                }
            )

        return {"nodes": nodes, "links": links}

    def save_json(self, path: str) -> None:
        """Сохранить граф в JSON-файл."""
        graph_data = self.to_json()
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        logger.info("Граф сохранён: %s (%d узлов, %d рёбер)", path, len(graph_data["nodes"]), len(graph_data["links"]))

    async def _load_documents(self) -> list[dict]:
        """Загрузить документы с количеством норм и findings."""
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT d.id, d.title, d.doc_type, d.domain, d.status,
                       COUNT(DISTINCT n.id) AS norms_count,
                       COUNT(DISTINCT f.id) AS findings_count
                FROM documents d
                LEFT JOIN norms n ON n.doc_id = d.id
                LEFT JOIN findings f ON f.norm_a_id = n.id OR f.norm_b_id = n.id
                GROUP BY d.id
                """
            )
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def _load_cross_refs(self) -> list[dict]:
        """Загрузить перекрёстные ссылки."""
        async with get_db() as db:
            cursor = await db.execute("SELECT from_doc, to_doc, context_text FROM cross_refs")
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def _load_findings(self) -> list[dict]:
        """Загрузить findings с doc_id для обеих норм."""
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT f.id, f.type, f.severity,
                       na.doc_id AS doc_a,
                       nb.doc_id AS doc_b
                FROM findings f
                JOIN norms na ON f.norm_a_id = na.id
                LEFT JOIN norms nb ON f.norm_b_id = nb.id
                WHERE f.type IN ('contradiction', 'duplication')
                """
            )
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]
