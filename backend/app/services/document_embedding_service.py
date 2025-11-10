import math
from typing import List

import httpx
from httpx import HTTPStatusError
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.milvus_service import milvus_service


class DocumentEmbeddingService:
    """文档嵌入服务：拆分文本 -> 嵌入 -> 写入 Milvus，并输出详细日志"""

    def __init__(self):
        self.chunk_size = max(settings.DOCUMENT_CHUNK_SIZE, 1)
        self.chunk_overlap = max(settings.DOCUMENT_CHUNK_OVERLAP, 0)
        self.batch_size = max(settings.EMBEDDING_BATCH_SIZE, 1)
        self.model_name = settings.EMBEDDING_MODEL
        self.api_url = settings.EMBEDDING_API_BASE.rstrip("/") + "/embeddings"
        self._config_logged = False

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", ";", "；"],
            length_function=len,
        )

    def _log_configuration(self, total_chunks: int):
        if not self._config_logged:
            print(
                "[EMBED] 当前配置："
                f"chunk_size={self.chunk_size}, overlap={self.chunk_overlap}, "
                f"batch_size={self.batch_size}, model={self.model_name}"
            )
            self._config_logged = True

        estimated_batches = max(1, math.ceil(total_chunks / self.batch_size))
        print(
            f"[EMBED] 分割完成：共 {total_chunks} 段，预计批次数 {estimated_batches}"
        )

    def _split(self, text: str) -> List[str]:
        chunks = [chunk.strip() for chunk in self.splitter.split_text(text) if chunk.strip()]
        return chunks

    def _fetch_embeddings(self, batch: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "input": batch,
        }
        response = httpx.post(self.api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        body = response.json()
        data = body.get("data", [])
        embeddings = [item.get("embedding", []) for item in data]
        if len(embeddings) != len(batch):
            raise ValueError("硅基流动返回的向量数量与输入不一致")
        return embeddings

    def _embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        idx = 0
        batch_id = 1
        current_batch_size = self.batch_size

        while idx < len(chunks):
            end = min(idx + current_batch_size, len(chunks))
            batch = chunks[idx:end]
            print(
                f"[EMBED] 批次 {batch_id}: 处理段 {idx}-{end - 1}（本批 {len(batch)} 段）"
            )
            try:
                batch_embeddings = self._fetch_embeddings(batch)
            except HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 413 and len(batch) > 1:
                    current_batch_size = max(1, len(batch) // 2)
                    print(
                        f"[WARNING] 批次 {batch_id} 收到 413，自动降至 batch_size={current_batch_size} 后重试"
                    )
                    continue  # 不推进 idx，直接重试该批
                raise

            embeddings.extend(batch_embeddings)
            print(
                f"[EMBED] 批次 {batch_id} 完成，累计 {len(embeddings)}/{len(chunks)} 段"
            )
            idx = end
            batch_id += 1
            current_batch_size = self.batch_size  # 成功后恢复配置

        return embeddings

    def process_and_store(self, requirement_id: int, text: str) -> int:
        """处理文档并写入向量数据库，返回写入条数"""
        if not text or not text.strip():
            print("[EMBED] 文本为空，跳过向量化")
            return 0

        if not settings.EMBEDDING_API_KEY:
            print("[WARNING] 未配置硅基流动 API Key，跳过文档向量化流程")
            return 0

        chunks = self._split(text)
        if not chunks:
            print("[EMBED] 分割结果为空，跳过向量化")
            return 0

        self._log_configuration(len(chunks))

        embeddings = self._embed_chunks(chunks)
        if not embeddings:
            print("[EMBED] 嵌入结果为空，跳过写入")
            return 0

        chunk_indices = list(range(len(chunks)))
        print(
            f"[EMBED] 开始写入 Milvus：requirement_id={requirement_id}, 向量数={len(embeddings)}"
        )
        milvus_service.connect()
        milvus_service.insert_batch(requirement_id, chunks, embeddings, chunk_indices)
        print("[EMBED] 写入 Milvus 完成")

        return len(embeddings)


document_embedding_service = DocumentEmbeddingService()
