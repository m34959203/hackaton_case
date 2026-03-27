"""Эмбеддинг норм и поиск похожих через ChromaDB."""

import logging

from app.config import settings
from app.database import get_chroma_collection, get_db
from app.llm.client import OllamaClient
from app.models.document import Norm

logger = logging.getLogger(__name__)

BATCH_SIZE = 20
MAX_TEXT_LENGTH = 2000  # nomic-embed-text: ограничение по токенам


class NormEmbedder:
    """Создание эмбеддингов для норм и хранение в ChromaDB."""

    def __init__(self) -> None:
        self._client = OllamaClient()
        self._collection = get_chroma_collection("norms")

    async def embed_norms(self, norms: list[Norm]) -> None:
        """Создать эмбеддинги для списка норм и сохранить в ChromaDB.

        Обработка батчами по BATCH_SIZE штук для контроля нагрузки на Ollama.
        """
        total = len(norms)
        if total == 0:
            logger.warning("Нет норм для эмбеддинга")
            return

        logger.info("Начало эмбеддинга %d норм (батчи по %d)", total, BATCH_SIZE)

        for i in range(0, total, BATCH_SIZE):
            batch = norms[i : i + BATCH_SIZE]
            texts = [n.text[:MAX_TEXT_LENGTH] for n in batch]
            ids = [n.id for n in batch]
            metadatas = [
                {
                    "doc_id": n.doc_id,
                    "article": n.article,
                    "paragraph": n.paragraph or 0,
                }
                for n in batch
            ]

            embeddings = await self._client.embed(texts)

            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            done = min(i + BATCH_SIZE, total)
            logger.info("Эмбеддинг: %d/%d норм обработано", done, total)

        logger.info("Эмбеддинг завершён: %d норм в коллекции", self._collection.count())

    async def embed_all(self) -> None:
        """Загрузить все нормы из БД и создать эмбеддинги."""
        async with get_db() as db:
            cursor = await db.execute("SELECT id, doc_id, article, paragraph, text FROM norms")
            rows = await cursor.fetchall()

        norms = [
            Norm(
                id=row["id"],
                doc_id=row["doc_id"],
                article=row["article"],
                paragraph=row["paragraph"],
                text=row["text"],
            )
            for row in rows
        ]

        logger.info("Загружено %d норм из БД для эмбеддинга", len(norms))
        await self.embed_norms(norms)

    def find_similar(
        self,
        norm_id: str,
        threshold: float = 0.85,
        limit: int = 20,
    ) -> list[dict]:
        """Найти нормы, похожие на указанную, по косинусному расстоянию.

        Args:
            norm_id: Идентификатор нормы-эталона.
            threshold: Минимальный порог сходства (cosine similarity).
            limit: Максимальное количество результатов.

        Returns:
            Список словарей с ключами: id, score, doc_id, text.
        """
        # Получаем эмбеддинг исходной нормы
        result = self._collection.get(ids=[norm_id], include=["embeddings"])
        if result["embeddings"] is None or len(result["embeddings"]) == 0:
            logger.warning("Норма %s не найдена в ChromaDB", norm_id)
            return []

        embedding = result["embeddings"][0]

        # Ищем похожие (запрашиваем больше, чтобы отфильтровать по порогу)
        query_result = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(limit + 1, self._collection.count()),
            include=["distances", "documents", "metadatas"],
        )

        similar: list[dict] = []
        if not query_result["ids"] or not query_result["ids"][0]:
            return similar

        for idx, found_id in enumerate(query_result["ids"][0]):
            if found_id == norm_id:
                continue

            # ChromaDB с cosine space возвращает distance = 1 - similarity
            distance = query_result["distances"][0][idx]
            similarity = 1.0 - distance

            if similarity < threshold:
                continue

            metadata = query_result["metadatas"][0][idx]
            similar.append(
                {
                    "id": found_id,
                    "score": round(similarity, 4),
                    "doc_id": metadata.get("doc_id", ""),
                    "text": query_result["documents"][0][idx],
                }
            )

            if len(similar) >= limit:
                break

        return similar

    def get_pairwise_similarity(self, norm_ids: list[str]) -> list[tuple[str, str, float]]:
        """Получить попарное сходство для набора норм.

        Args:
            norm_ids: Список идентификаторов норм.

        Returns:
            Список кортежей (norm_a_id, norm_b_id, similarity).
        """
        if len(norm_ids) < 2:
            return []

        result = self._collection.get(
            ids=norm_ids,
            include=["embeddings"],
        )

        if result["embeddings"] is None or len(result["embeddings"]) == 0:
            return []

        embeddings_map: dict[str, list[float]] = {}
        for idx, nid in enumerate(result["ids"]):
            embeddings_map[nid] = result["embeddings"][idx]

        pairs: list[tuple[str, str, float]] = []
        id_list = list(embeddings_map.keys())

        for i in range(len(id_list)):
            for j in range(i + 1, len(id_list)):
                a_id, b_id = id_list[i], id_list[j]
                vec_a = embeddings_map[a_id]
                vec_b = embeddings_map[b_id]

                # Косинусное сходство
                dot = sum(x * y for x, y in zip(vec_a, vec_b))
                mag_a = sum(x * x for x in vec_a) ** 0.5
                mag_b = sum(x * x for x in vec_b) ** 0.5
                if mag_a == 0 or mag_b == 0:
                    continue
                similarity = dot / (mag_a * mag_b)
                pairs.append((a_id, b_id, round(similarity, 4)))

        return pairs
