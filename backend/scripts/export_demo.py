"""Экспорт данных из SQLite в JSON для offline-демо на хакатоне.

Создаёт два файла:
  - demo/seed_data.json — полный набор данных (stats, documents, findings, graph, clusters)
  - demo/highlights.json — выборка самых интересных обнаружений для презентации
"""

import json
import logging
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "zandb.sqlite"
GRAPH_PATH = BASE_DIR / "data" / "graph.json"
DEMO_DIR = BASE_DIR.parent / "demo"


def get_conn() -> sqlite3.Connection:
    """Подключение к SQLite с row_factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def export_stats(conn: sqlite3.Connection) -> dict:
    """Статистика в формате /api/stats."""
    cur = conn.cursor()

    total_documents = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    total_norms = cur.execute("SELECT COUNT(*) FROM norms").fetchone()[0]
    total_findings = cur.execute("SELECT COUNT(*) FROM findings").fetchone()[0]

    findings_by_type = [
        {"type": r[0], "count": r[1]}
        for r in cur.execute(
            "SELECT type, COUNT(*) as cnt FROM findings GROUP BY type ORDER BY cnt DESC"
        )
    ]

    findings_by_severity = [
        {"severity": r[0], "count": r[1]}
        for r in cur.execute(
            """SELECT severity, COUNT(*) as cnt FROM findings
               GROUP BY severity
               ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END"""
        )
    ]

    top_domains = [
        {"domain": r[0], "docs_count": r[1], "norms_count": r[2], "findings_count": r[3]}
        for r in cur.execute(
            """
            SELECT d.domain,
                   COUNT(DISTINCT d.id) as docs_count,
                   COUNT(DISTINCT n.id) as norms_count,
                   COUNT(DISTINCT f.id) as findings_count
            FROM documents d
            LEFT JOIN norms n ON n.doc_id = d.id
            LEFT JOIN findings f ON f.norm_a_id = n.id OR f.norm_b_id = n.id
            WHERE d.domain IS NOT NULL
            GROUP BY d.domain
            ORDER BY findings_count DESC
            LIMIT 10
            """
        )
    ]

    return {
        "total_documents": total_documents,
        "total_norms": total_norms,
        "total_findings": total_findings,
        "findings_by_type": findings_by_type,
        "findings_by_severity": findings_by_severity,
        "top_domains": top_domains,
    }


def export_documents(conn: sqlite3.Connection) -> list[dict]:
    """Все документы без body (для компактности)."""
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT d.id, d.title, d.doc_type, d.date_adopted, d.date_amended,
               d.status, d.domain, d.adopting_body, d.legal_force,
               COUNT(DISTINCT n.id) as norms_count,
               COUNT(DISTINCT f.id) as findings_count
        FROM documents d
        LEFT JOIN norms n ON n.doc_id = d.id
        LEFT JOIN findings f ON f.norm_a_id = n.id OR f.norm_b_id = n.id
        GROUP BY d.id
        ORDER BY findings_count DESC, d.title
        """
    ).fetchall()

    return [
        {
            "id": r[0],
            "title": r[1],
            "doc_type": r[2],
            "date_adopted": r[3],
            "date_amended": r[4],
            "status": r[5],
            "domain": r[6],
            "adopting_body": r[7],
            "legal_force": r[8],
            "norms_count": r[9],
            "findings_count": r[10],
        }
        for r in rows
    ]


def _build_finding(r) -> dict:
    """Собрать dict обнаружения из строки запроса."""
    finding = {
        "id": r[0],
        "type": r[1],
        "severity": r[2],
        "confidence": r[3],
        "explanation": r[4],
        "recommendation": r[5],
        "cluster_id": r[6],
        "created_at": r[7],
        "norm_a": {
            "id": r[8],
            "doc_id": r[9],
            "article": r[10],
            "paragraph": r[11],
            "text": r[12],
        },
        "cluster_topic": r[18],
    }
    # norm_b (может быть NULL для outdated)
    if r[13]:
        finding["norm_b"] = {
            "id": r[13],
            "doc_id": r[14],
            "article": r[15],
            "paragraph": r[16],
            "text": r[17],
        }
    else:
        finding["norm_b"] = None

    return finding


# Базовый SQL для findings с JOIN на norms
_FINDINGS_SQL = """
    SELECT f.id, f.type, f.severity, f.confidence,
           f.explanation, f.recommendation, f.cluster_id, f.created_at,
           n_a.id, n_a.doc_id, n_a.article, n_a.paragraph, n_a.text,
           n_b.id, n_b.doc_id, n_b.article, n_b.paragraph, n_b.text,
           n_a.cluster_topic
    FROM findings f
    LEFT JOIN norms n_a ON n_a.id = f.norm_a_id
    LEFT JOIN norms n_b ON n_b.id = f.norm_b_id
"""


def export_findings(conn: sqlite3.Connection) -> list[dict]:
    """Все 306 findings с полными данными."""
    cur = conn.cursor()
    rows = cur.execute(
        _FINDINGS_SQL
        + """
        ORDER BY
            CASE f.severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
            f.confidence DESC
        """
    ).fetchall()

    results = []
    for r in rows:
        finding = _build_finding(r)
        # Добавим названия документов
        for key in ("norm_a", "norm_b"):
            norm = finding.get(key)
            if norm and norm.get("doc_id"):
                doc_row = cur.execute(
                    "SELECT title FROM documents WHERE id = ?", (norm["doc_id"],)
                ).fetchone()
                norm["doc_title"] = doc_row[0] if doc_row else None
        results.append(finding)

    return results


def export_graph() -> dict:
    """Граф из graph.json."""
    if not GRAPH_PATH.exists():
        logger.warning("graph.json не найден, граф будет пустым")
        return {"nodes": [], "links": []}

    with open(GRAPH_PATH, encoding="utf-8") as f:
        return json.load(f)


def export_clusters(conn: sqlite3.Connection) -> list[dict]:
    """Топ-20 кластеров с topic и количеством норм/findings."""
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT n.cluster_id, n.cluster_topic,
               COUNT(DISTINCT n.id) as norms_count,
               COUNT(DISTINCT f.id) as findings_count
        FROM norms n
        LEFT JOIN findings f ON f.norm_a_id = n.id OR f.norm_b_id = n.id
        WHERE n.cluster_id IS NOT NULL AND n.cluster_topic IS NOT NULL
        GROUP BY n.cluster_id
        ORDER BY findings_count DESC, norms_count DESC
        LIMIT 20
        """
    ).fetchall()

    return [
        {
            "cluster_id": r[0],
            "topic": r[1],
            "norms_count": r[2],
            "findings_count": r[3],
        }
        for r in rows
    ]


def export_highlights(conn: sqlite3.Connection) -> dict:
    """Самые интересные обнаружения для презентации."""
    cur = conn.cursor()

    def _query_findings(where: str, limit: int) -> list[dict]:
        rows = cur.execute(
            _FINDINGS_SQL + where, ()
        ).fetchall()
        results = []
        for r in rows[:limit]:
            finding = _build_finding(r)
            for key in ("norm_a", "norm_b"):
                norm = finding.get(key)
                if norm and norm.get("doc_id"):
                    doc_row = cur.execute(
                        "SELECT title FROM documents WHERE id = ?", (norm["doc_id"],)
                    ).fetchone()
                    norm["doc_title"] = doc_row[0] if doc_row else None
            results.append(finding)
        return results

    # Топ-6 противоречий (самые интересные для демо)
    contradictions = _query_findings(
        "WHERE f.type = 'contradiction' ORDER BY f.severity = 'high' DESC, f.confidence DESC LIMIT 6",
        6,
    )

    # Топ-10 дублирований (наивысшая уверенность)
    duplications = _query_findings(
        "WHERE f.type = 'duplication' ORDER BY f.confidence DESC, f.severity = 'high' DESC LIMIT 10",
        10,
    )

    # Топ-10 устаревших норм
    outdated = _query_findings(
        "WHERE f.type = 'outdated' ORDER BY f.severity = 'high' DESC, f.confidence DESC LIMIT 10",
        10,
    )

    return {
        "contradictions": contradictions,
        "duplications": duplications,
        "outdated": outdated,
        "meta": {
            "description": "Выборка самых значимых обнаружений ZanAlytics для презентации",
            "total_contradictions": len(contradictions),
            "total_duplications": len(duplications),
            "total_outdated": len(outdated),
        },
    }


def main() -> None:
    """Главная функция экспорта."""
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Подключение к БД: %s", DB_PATH)
    conn = get_conn()

    # --- seed_data.json ---
    logger.info("Экспорт статистики...")
    stats = export_stats(conn)

    logger.info("Экспорт документов...")
    documents = export_documents(conn)

    logger.info("Экспорт обнаружений...")
    findings = export_findings(conn)

    logger.info("Экспорт графа...")
    graph = export_graph()

    logger.info("Экспорт кластеров...")
    clusters = export_clusters(conn)

    seed_data = {
        "stats": stats,
        "documents": documents,
        "findings": findings,
        "graph": graph,
        "clusters": clusters,
    }

    seed_path = DEMO_DIR / "seed_data.json"
    with open(seed_path, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, ensure_ascii=False, indent=2)
    seed_size = seed_path.stat().st_size

    # --- highlights.json ---
    logger.info("Экспорт highlights...")
    highlights = export_highlights(conn)

    highlights_path = DEMO_DIR / "highlights.json"
    with open(highlights_path, "w", encoding="utf-8") as f:
        json.dump(highlights, f, ensure_ascii=False, indent=2)
    highlights_size = highlights_path.stat().st_size

    conn.close()

    # Отчёт
    logger.info("=" * 50)
    logger.info("Экспорт завершён!")
    logger.info("  seed_data.json:  %s (%s KB)", seed_path, f"{seed_size / 1024:.1f}")
    logger.info("  highlights.json: %s (%s KB)", highlights_path, f"{highlights_size / 1024:.1f}")
    logger.info("  Документов: %d", len(documents))
    logger.info("  Обнаружений: %d", len(findings))
    logger.info("  Узлов графа: %d", len(graph.get("nodes", [])))
    logger.info("  Рёбер графа: %d", len(graph.get("links", [])))
    logger.info("  Кластеров: %d", len(clusters))


if __name__ == "__main__":
    main()
