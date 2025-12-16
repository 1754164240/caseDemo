"""通用的 Pydantic 模型"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel

# 泛型类型变量
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型
    
    包含数据列表、总数和分页信息
    """
    items: List[T]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True

