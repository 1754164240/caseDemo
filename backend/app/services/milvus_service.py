from typing import Any, Dict, List, Optional
import time

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from app.core.config import settings


class MilvusService:
    """Milvus 向量数据库服务"""

    def __init__(self):
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.collection: Optional[Collection] = None
        self._manual_pk_counter = int(time.time() * 1e6)

    def connect(self):
        """连接 Milvus，若已连接则跳过"""
        try:
            if connections.has_connection("default"):
                return
        except AttributeError:
            # 旧版本 PyMilvus 无 has_connection 方法
            pass

        params: Dict[str, Any] = {"alias": "default"}
        if settings.MILVUS_URI:
            params["uri"] = settings.MILVUS_URI
        else:
            params["host"] = settings.MILVUS_HOST
            params["port"] = settings.MILVUS_PORT

        if settings.MILVUS_USER:
            params["user"] = settings.MILVUS_USER
        if settings.MILVUS_PASSWORD:
            params["password"] = settings.MILVUS_PASSWORD
        if settings.MILVUS_TOKEN:
            params["token"] = settings.MILVUS_TOKEN
        if settings.MILVUS_DB_NAME:
            params["db_name"] = settings.MILVUS_DB_NAME

        connections.connect(**params)

    def _ensure_loaded_collection(self):
        """保证 self.collection 已经指向现有集合"""
        self.connect()
        if not self.collection and utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)

    def _ensure_collection(self, dim: int):
        """集合不存在时创建；存在则直接加载"""
        self.connect()
        if not utility.has_collection(self.collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="requirement_id", dtype=DataType.INT64),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            ]
            schema = CollectionSchema(fields=fields, description="Test case embeddings")
            self.collection = Collection(name=self.collection_name, schema=schema)

            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            self.collection.create_index(field_name="embedding", index_params=index_params)
        else:
            self.collection = Collection(self.collection_name)

    def _prepare_insert_payload(
        self,
        requirement_id: int,
        texts: List[str],
        embeddings: List[List[float]],
        chunk_indices: Optional[List[int]] = None,
    ) -> List[List[Any]]:
        """根据当前集合 schema 动态生成插入数据，兼容历史 schema"""
        payload: List[List[Any]] = []
        if not self.collection:
            return payload

        trimmed_texts = [text[:65535] for text in texts]
        requirement_ids = [requirement_id] * len(texts)
        primary_manual_ids: Optional[List[int]] = None
        if chunk_indices is None:
            chunk_indices = list(range(len(texts)))

        primary_field = next((field for field in self.collection.schema.fields if field.is_primary), None)
        if primary_field and not getattr(primary_field, "auto_id", False):
            start = max(self._manual_pk_counter + 1, int(time.time() * 1e6))
            primary_manual_ids = list(range(start, start + len(texts)))
            self._manual_pk_counter = primary_manual_ids[-1]

        for field in self.collection.schema.fields:
            if field.is_primary and field.auto_id:
                continue

            if field.is_primary and primary_manual_ids is not None:
                payload.append(primary_manual_ids)
                continue

            if field.name == "requirement_id":
                payload.append(requirement_ids)
            elif field.name == "chunk_index":
                payload.append(chunk_indices)
            elif field.name == "text":
                payload.append(trimmed_texts)
            elif field.name == "embedding":
                payload.append(embeddings)
            else:
                payload.append([None] * len(texts))

        return payload

    def insert(self, requirement_id: int, text: str, embedding: List[float], chunk_index: int = 0):
        """插入单条向量"""
        self.insert_batch(requirement_id, [text], [embedding], [chunk_index])

    def insert_batch(
        self,
        requirement_id: int,
        texts: List[str],
        embeddings: List[List[float]],
        chunk_indices: Optional[List[int]] = None,
    ):
        """批量插入同一需求下的向量"""
        if not texts or not embeddings:
            return
        if len(texts) != len(embeddings):
            raise ValueError("texts 与 embeddings 数量不一致")

        vector_dim = len(embeddings[0])
        self._ensure_collection(vector_dim)
        self._ensure_loaded_collection()

        if not self.collection:
            raise RuntimeError("Milvus collection 初始化失败")

        payload = self._prepare_insert_payload(requirement_id, texts, embeddings, chunk_indices)
        if not payload:
            raise RuntimeError("无法根据当前 schema 生成插入数据，请检查集合定义")

        self.collection.insert(payload)
        self.collection.flush()

    def search(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        self._ensure_loaded_collection()
        if not self.collection:
            return []

        self.collection.load()

        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["requirement_id", "text"],
        )

        if not results:
            return []

        return [
            {
                "id": hit.id,
                "requirement_id": hit.entity.get("requirement_id"),
                "text": hit.entity.get("text"),
                "distance": hit.distance,
            }
            for hit in results[0]
        ]

    def delete_by_requirement(self, requirement_id: int):
        """删除指定需求的向量"""
        self._ensure_loaded_collection()
        if not self.collection:
            return

        expr = f"requirement_id == {requirement_id}"
        self.collection.delete(expr)


milvus_service = MilvusService()
