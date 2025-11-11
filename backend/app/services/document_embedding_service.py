import math
from typing import List, Optional

import httpx
from httpx import HTTPStatusError
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.milvus_service import milvus_service


class DocumentEmbeddingService:
    """文档嵌入服务：切分 -> 嵌入 -> 写入 Milvus，并提供详细日志"""

    def __init__(self):
        self.chunk_size = max(settings.DOCUMENT_CHUNK_SIZE, 1)
        self.chunk_overlap = max(settings.DOCUMENT_CHUNK_OVERLAP, 0)
        self.batch_size = max(settings.EMBEDDING_BATCH_SIZE, 1)
        self.model_name = settings.EMBEDDING_MODEL
        self.api_url = settings.EMBEDDING_API_BASE.rstrip("/") + "/embeddings"
        self._config_logged = False
        self._min_single_chunk = max(self.chunk_size // 2, 128)

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "、", "，", "；", ".", "!", "?", ";", "："],
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
        print(f"[EMBED] 分割完成：共 {total_chunks} 段，预计批次数 {estimated_batches}")

    def _split(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        chunks = [chunk.strip() for chunk in self.splitter.split_text(text) if chunk.strip()]
        return chunks

    def split_text(self, text: str) -> List[str]:
        """对原始文本进行切分，供后续复用"""
        chunks = self._split(text)
        print(f"[EMBED] 文本切分完成，共 {len(chunks)} 段")
        return chunks

    def _select_chunk_indices(self, total: int, max_chunks: int) -> List[int]:
        if total == 0:
            return []
        if total <= max_chunks:
            return list(range(total))
        step = total / max_chunks
        indices = {min(int(round(i * step)), total - 1) for i in range(max_chunks)}
        indices.add(total - 1)
        return sorted(indices)

    def build_ai_context(self, chunks: List[str]) -> str:
        """从所有分段中抽样拼接，生成符合 LLM 限制的上下文"""
        if not chunks:
            return ""

        max_chunks = max(settings.TEST_POINT_CONTEXT_CHUNKS, 1)
        max_chars = max(settings.TEST_POINT_MAX_INPUT_CHARS, 0)
        selected_indices = self._select_chunk_indices(len(chunks), max_chunks)
        parts: List[str] = []
        current_length = 0

        for order, idx in enumerate(selected_indices, start=1):
            chunk_text = chunks[idx].strip()
            if not chunk_text:
                continue
            labeled_chunk = f"[片段 {order}/{len(selected_indices)}]\n{chunk_text}"
            part_length = len(labeled_chunk) + 2
            if max_chars and current_length + part_length > max_chars:
                break
            parts.append(labeled_chunk)
            current_length += part_length

        context = "\n\n".join(parts)
        print(
            f"[INFO] 构建测试点上下文：选取 {len(parts)} 段，总长度 {len(context)} 字符（原始段数 {len(chunks)}）"
        )
        return context

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

    def _split_large_chunk(self, chunk: str) -> List[str]:
        target_size = max(self._min_single_chunk, 100)
        if len(chunk) <= target_size:
            return [chunk]

        pieces: List[str] = []
        start = 0
        while start < len(chunk):
            piece = chunk[start : start + target_size].strip()
            if piece:
                pieces.append(piece)
            start += target_size

        if not pieces:
            return [chunk]

        print(
            f"[WARNING] 单段文本长度 {len(chunk)} 超过提供方限制，自动拆分为 {len(pieces)} 段（每段≈{target_size} 字符）"
        )
        return pieces

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
                if status == 413:
                    if len(batch) > 1:
                        current_batch_size = max(1, len(batch) // 2)
                        print(
                            f"[WARNING] 批次 {batch_id} 收到 413，自动降至 batch_size={current_batch_size} 后重试"
                        )
                        continue

                    chunk_text = batch[0]
                    smaller_chunks = self._split_large_chunk(chunk_text)
                    if len(smaller_chunks) == 1:
                        raise

                    chunks[idx:idx + 1] = smaller_chunks
                    print(
                        f"[WARNING] 批次 {batch_id} 单段触发 413，已拆成 {len(smaller_chunks)} 段后重试"
                    )
                    current_batch_size = min(current_batch_size, len(smaller_chunks))
                    continue
                raise

            embeddings.extend(batch_embeddings)
            print(
                f"[EMBED] 批次 {batch_id} 完成，累计 {len(embeddings)}/{len(chunks)} 段"
            )
            idx = end
            batch_id += 1
            current_batch_size = self.batch_size  # 成功后恢复配置

        return embeddings

    def process_and_store(self, requirement_id: int, chunks: Optional[List[str]]) -> int:
        """处理分段并写入向量数据库，返回写入条数"""
        if not chunks:
            print("[EMBED] 文本为空，跳过向量化")
            return 0

        if not settings.EMBEDDING_API_KEY:
            print("[WARNING] 未配置硅基流动 API Key，跳过文档向量化流程")
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
