from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from typing import List, Dict, Any
from app.core.config import settings


class MilvusService:
    """Milvus 向量数据库服务"""
    
    def __init__(self):
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.collection = None
        
    def connect(self):
        """连接到 Milvus"""
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
    def create_collection(self, dim: int = 1536):
        """创建集合"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            return
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="requirement_id", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        
        schema = CollectionSchema(fields=fields, description="Test case embeddings")
        self.collection = Collection(name=self.collection_name, schema=schema)
        
        # Create index
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        self.collection.create_index(field_name="embedding", index_params=index_params)
        
    def insert(self, requirement_id: int, text: str, embedding: List[float]):
        """插入向量"""
        if not self.collection:
            self.create_collection(len(embedding))
        
        data = [
            [requirement_id],
            [text],
            [embedding]
        ]
        self.collection.insert(data)
        self.collection.flush()
        
    def search(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        if not self.collection:
            return []
        
        self.collection.load()
        
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["requirement_id", "text"]
        )
        
        return [
            {
                "id": hit.id,
                "requirement_id": hit.entity.get("requirement_id"),
                "text": hit.entity.get("text"),
                "distance": hit.distance
            }
            for hit in results[0]
        ]
    
    def delete_by_requirement(self, requirement_id: int):
        """删除指定需求的向量"""
        if not self.collection:
            return
        
        expr = f"requirement_id == {requirement_id}"
        self.collection.delete(expr)


milvus_service = MilvusService()

