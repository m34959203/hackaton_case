"""Кластеризация норм через UMAP + HDBSCAN."""

import logging

import hdbscan
import numpy as np
import umap

from app.config import settings
from app.database import get_chroma_collection, get_db
from app.llm.client import OllamaClient
from app.llm.prompts import CLUSTER_TOPIC_PROMPT
from app.utils.text import truncate

logger = logging.getLogger(__name__)

# Максимум норм для включения в промпт тематики кластера
_MAX_SAMPLE_NORMS = 5


class NormClusterer:
    """Кластеризация норм по семантической близости."""

    def __init__(self) -> None:
        self._client = OllamaClient()
        self._collection = get_chroma_collection("norms")

    async def cluster_norms(self) -> dict[int, list[str]]:
        """Кластеризовать все нормы из ChromaDB.

        Алгоритм:
            1. Загрузить все эмбеддинги из ChromaDB.
            2. UMAP для снижения размерности (n_components=50).
            3. HDBSCAN для кластеризации (min_cluster_size=5).
            4. Обновить cluster_id в SQLite.
            5. Назвать каждый кластер через LLM.

        Returns:
            Словарь cluster_id -> список norm_id.
        """
        # Загружаем все данные из коллекции
        all_data = self._collection.get(include=["embeddings", "documents"])
        ids = all_data["ids"]
        embeddings = all_data["embeddings"]

        if not ids or embeddings is None or len(embeddings) == 0:
            logger.warning("Нет эмбеддингов для кластеризации")
            return {}

        n_norms = len(ids)
        logger.info("Начало кластеризации %d норм", n_norms)

        embeddings_array = np.array(embeddings, dtype=np.float32)

        # UMAP — снижение размерности
        n_components = min(50, n_norms - 2) if n_norms > 52 else max(2, n_norms - 2)
        n_neighbors = min(15, n_norms - 1)

        logger.info("UMAP: %d -> %d компонент (n_neighbors=%d)", embeddings_array.shape[1], n_components, n_neighbors)
        reducer = umap.UMAP(
            n_components=n_components,
            metric="cosine",
            n_neighbors=n_neighbors,
            random_state=42,
        )
        reduced = reducer.fit_transform(embeddings_array)

        # HDBSCAN — кластеризация
        min_cluster_size = min(5, max(2, n_norms // 10))
        logger.info("HDBSCAN: min_cluster_size=%d", min_cluster_size)
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric="euclidean",
        )
        labels = clusterer.fit_predict(reduced)

        # Собираем кластеры
        clusters: dict[int, list[str]] = {}
        for idx, label in enumerate(labels):
            label_int = int(label)
            if label_int == -1:
                continue  # шум, не включаем
            clusters.setdefault(label_int, []).append(ids[idx])

        n_clustered = sum(len(v) for v in clusters.values())
        n_noise = n_norms - n_clustered
        logger.info(
            "Кластеризация завершена: %d кластеров, %d норм в кластерах, %d шум",
            len(clusters),
            n_clustered,
            n_noise,
        )

        # Обновляем cluster_id в SQLite и называем кластеры
        texts_map: dict[str, str] = {}
        for idx, nid in enumerate(ids):
            texts_map[nid] = all_data["documents"][idx]

        async with get_db() as db:
            for cluster_id, norm_ids in clusters.items():
                # Называем кластер через LLM
                topic = await self._name_cluster(cluster_id, norm_ids, texts_map)

                # Обновляем нормы в БД
                for norm_id in norm_ids:
                    await db.execute(
                        "UPDATE norms SET cluster_id = ?, cluster_topic = ? WHERE id = ?",
                        (cluster_id, topic, norm_id),
                    )

            # Сброс кластера для шумовых норм
            noise_ids = [ids[i] for i, label in enumerate(labels) if int(label) == -1]
            for norm_id in noise_ids:
                await db.execute(
                    "UPDATE norms SET cluster_id = NULL, cluster_topic = NULL WHERE id = ?",
                    (norm_id,),
                )

            await db.commit()

        logger.info("Кластеры сохранены в БД")
        return clusters

    async def _name_cluster(
        self,
        cluster_id: int,
        norm_ids: list[str],
        texts_map: dict[str, str],
    ) -> str:
        """Назвать кластер через LLM на основе выборки норм.

        Returns:
            Краткое название темы кластера.
        """
        sample_ids = norm_ids[:_MAX_SAMPLE_NORMS]
        sample_texts = "\n\n".join(
            f"- {truncate(texts_map.get(nid, ''), 300)}"
            for nid in sample_ids
        )

        prompt = CLUSTER_TOPIC_PROMPT.format(sample_norms=sample_texts)

        try:
            result = await self._client.generate_json(
                prompt=prompt,
                temperature=settings.LLM_TEMPERATURE_ANALYSIS,
            )
            topic = result.get("topic", f"Кластер {cluster_id}")
            logger.info("Кластер %d: %s", cluster_id, topic)
            return topic
        except Exception:
            logger.exception("Ошибка при именовании кластера %d", cluster_id)
            return f"Кластер {cluster_id}"
