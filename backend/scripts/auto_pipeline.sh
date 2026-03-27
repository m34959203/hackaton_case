#!/bin/bash
# ============================================================
# ZanAlytics — Автономный пайплайн
# Запуск: bash scripts/auto_pipeline.sh
# Логи: logs/pipeline.log
# PID: logs/pipeline.pid
# Статус: tail -f logs/pipeline.log
# Стоп: kill $(cat logs/pipeline.pid)
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

PYTHON="/home/ubuntu/miniconda3/envs/zan/bin/python"
LOG_DIR="$SCRIPT_DIR/logs"
LOG="$LOG_DIR/pipeline.log"
PID_FILE="$LOG_DIR/pipeline.pid"

mkdir -p "$LOG_DIR"

# Загружаем .env если есть
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Записываем PID
echo $$ > "$PID_FILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

log "============================================================"
log "АВТОНОМНЫЙ ПАЙПЛАЙН ZanAlytics"
log "PID: $$, Python: $PYTHON"
log "============================================================"

# --- Шаг 1: Проверка сервисов ---
log "[1/5] Проверка сервисов..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log "  Ollama: OK"
else
    log "  ОШИБКА: Ollama недоступен на localhost:11434"
    exit 1
fi

NORM_COUNT=$($PYTHON -c "
import sqlite3
conn = sqlite3.connect('data/zandb.sqlite')
r = conn.execute('SELECT COUNT(*) FROM norms').fetchone()
print(r[0])
conn.close()
")
log "  SQLite: OK ($NORM_COUNT норм)"

CHROMA_COUNT=$($PYTHON -c "
from app.database import get_chroma_collection
print(get_chroma_collection('norms').count())
")
log "  ChromaDB: OK ($CHROMA_COUNT эмбеддингов)"

# --- Шаг 2: Парсинг (если данных нет) ---
if [ "$NORM_COUNT" -eq 0 ]; then
    log "[2/5] Парсинг документов..."
    $PYTHON -m scripts.scrape >> "$LOG" 2>&1
    log "  Парсинг завершён"
else
    log "[2/5] Парсинг: пропущен ($NORM_COUNT норм уже есть)"
fi

# --- Шаг 3: Эмбеддинги (если нет) ---
if [ "$CHROMA_COUNT" -lt "$NORM_COUNT" ]; then
    log "[3/5] Эмбеддинг норм..."
    $PYTHON -c "
import asyncio
from app.pipeline.embedder import NormEmbedder
from app.database import init_db
async def run():
    await init_db()
    e = NormEmbedder()
    await e.embed_all()
asyncio.run(run())
" >> "$LOG" 2>&1
    log "  Эмбеддинг завершён"
else
    log "[3/5] Эмбеддинг: пропущен ($CHROMA_COUNT эмбеддингов уже есть)"
fi

# --- Шаг 4: Быстрый анализ (если findings мало) ---
FINDINGS_COUNT=$($PYTHON -c "
import sqlite3
conn = sqlite3.connect('data/zandb.sqlite')
r = conn.execute('SELECT COUNT(*) FROM findings').fetchone()
print(r[0])
conn.close()
")
log "  Текущих findings: $FINDINGS_COUNT"

if [ "$FINDINGS_COUNT" -lt 50 ]; then
    log "[4/5] Быстрый анализ (embedding-based dedup + outdated)..."
    $PYTHON -m scripts.quick_analyze >> "$LOG" 2>&1
    log "  Быстрый анализ завершён"
else
    log "[4/5] Быстрый анализ: пропущен ($FINDINGS_COUNT findings)"
fi

# --- Шаг 5: Расширенный поиск противоречий ---
CONTRA_COUNT=$($PYTHON -c "
import sqlite3
conn = sqlite3.connect('data/zandb.sqlite')
r = conn.execute(\"SELECT COUNT(*) FROM findings WHERE type='contradiction'\").fetchone()
print(r[0])
conn.close()
")
log "[5/5] Расширенный поиск противоречий (текущих: $CONTRA_COUNT)..."

$PYTHON -c "
import asyncio, logging, re, sys, time
sys.path.insert(0, '.')
from app.config import settings
from app.database import get_chroma_collection, get_db, init_db
from app.llm.client import LLMClient
from app.llm.prompts import CONTRADICTION_PROMPT

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger('contradictions')

NUMBER_RE = re.compile(r'\d+\s*(?:дн|суток|месяц|год|лет|процент|тенге|МРП|%|час|рабоч|календарн|минут|размер|кратн|раз\b)', re.I)

async def main():
    await init_db()
    client = LLMClient()

    # Загрузить уже проверенные пары
    checked = set()
    async with get_db() as db:
        rows = await (await db.execute(\"SELECT norm_a_id, norm_b_id FROM findings WHERE type='contradiction'\")).fetchall()
        for r in rows:
            checked.add((r[0], r[1]))
            checked.add((r[1], r[0]))

    # Загрузить кластеры с 2+ документами
    async with get_db() as db:
        rows = await (await db.execute('''
            SELECT n.cluster_id, n.id, n.doc_id, n.text, d.title
            FROM norms n JOIN documents d ON n.doc_id = d.id
            WHERE n.cluster_id IS NOT NULL
        ''')).fetchall()

    # Группировка по кластерам
    clusters = {}
    for r in rows:
        cid = r[0]
        clusters.setdefault(cid, []).append({'id': r[1], 'doc_id': r[2], 'text': r[3], 'title': r[4]})

    # Генерация пар: нормы с числами из РАЗНЫХ документов
    pairs = []
    for cid, norms in clusters.items():
        numbered = [n for n in norms if NUMBER_RE.search(n['text'])]
        docs = {}
        for n in numbered:
            docs.setdefault(n['doc_id'], []).append(n)
        doc_ids = list(docs.keys())
        if len(doc_ids) < 2:
            continue
        for i in range(min(3, len(doc_ids))):
            for j in range(i+1, min(3, len(doc_ids))):
                a = docs[doc_ids[i]][0]
                b = docs[doc_ids[j]][0]
                key = (a['id'], b['id'])
                if key not in checked and (b['id'], a['id']) not in checked:
                    pairs.append((a, b, cid))
                    checked.add(key)
                    if len(pairs) >= 300:
                        break
            if len(pairs) >= 300:
                break
        if len(pairs) >= 300:
            break

    logger.info('Пар для проверки: %d', len(pairs))

    found = 0
    errors = 0
    for i, (a, b, cid) in enumerate(pairs):
        try:
            prompt = CONTRADICTION_PROMPT.format(
                doc_a_title=a['title'], norm_a_text=a['text'][:1500],
                doc_b_title=b['title'], norm_b_text=b['text'][:1500],
            )
            result = await client.generate_json(prompt=prompt, temperature=0.1)

            if result.get('is_contradiction') and float(result.get('confidence', 0)) >= 0.5:
                conf = float(result['confidence'])
                sev = result.get('severity', 'medium')
                expl = result.get('explanation', '')
                rec = result.get('legal_principle', '')

                async with get_db() as db:
                    await db.execute(
                        'INSERT INTO findings (type, severity, confidence, norm_a_id, norm_b_id, explanation, cluster_id, recommendation) VALUES (?,?,?,?,?,?,?,?)',
                        ('contradiction', sev, conf, a['id'], b['id'], expl, cid, rec)
                    )
                    await db.commit()
                found += 1
                logger.info('КОЛЛИЗИЯ #%d [%s, %.2f]: %s vs %s — %s', found, sev, conf, a['id'][:30], b['id'][:30], expl[:80])
        except Exception as e:
            errors += 1
            if errors > 20:
                logger.error('Слишком много ошибок (%d), останавливаюсь', errors)
                break

        if (i + 1) % 10 == 0:
            logger.info('Проверено %d/%d, найдено коллизий: %d, ошибок: %d', i+1, len(pairs), found, errors)

    logger.info('ЗАВЕРШЕНО: %d/%d проверено, %d коллизий найдено, %d ошибок', i+1, len(pairs), found, errors)

asyncio.run(main())
" >> "$LOG" 2>&1

# --- Шаг 6: Перегенерация графа ---
log "[+] Перегенерация графа..."
$PYTHON -c "
import asyncio
from app.pipeline.graph_builder import GraphBuilder
from app.database import init_db
from app.config import settings
from pathlib import Path
async def main():
    await init_db()
    gb = GraphBuilder()
    await gb.build_graph()
    path = str(Path(settings.DB_PATH).parent / 'graph.json')
    gb.save_json(path)
    d = gb.to_json()
    print(f'Graph: {len(d[\"nodes\"])} nodes, {len(d[\"links\"])} links')
asyncio.run(main())
" >> "$LOG" 2>&1

# --- Шаг 7: Экспорт демо-данных ---
log "[+] Экспорт демо-данных..."
$PYTHON -m scripts.export_demo >> "$LOG" 2>&1

# --- Итог ---
FINAL_FINDINGS=$($PYTHON -c "
import sqlite3
conn = sqlite3.connect('data/zandb.sqlite')
for r in conn.execute('SELECT type, COUNT(*) FROM findings GROUP BY type').fetchall():
    print(f'  {r[0]}: {r[1]}')
total = conn.execute('SELECT COUNT(*) FROM findings').fetchone()[0]
print(f'  ВСЕГО: {total}')
conn.close()
")

log "============================================================"
log "ПАЙПЛАЙН ЗАВЕРШЁН"
log "$FINAL_FINDINGS"
log "============================================================"

rm -f "$PID_FILE"
