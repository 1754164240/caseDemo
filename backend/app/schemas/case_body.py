"""Agent 结构化输出模型 - 测试数据生成"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class CaseBodyItem(BaseModel):
    """单条测试数据"""
    casezf: str = Field(
        description="正反案例标识: '正' 表示正向用例, '反' 表示反向/异常用例"
    )
    casedesc: str = Field(
        description="测试角度/场景描述, 如 '正常投保-月缴', '年龄边界值测试'"
    )
    var: Dict[str, str] = Field(
        description="字段名->测试值 的映射字典, 所有值为字符串类型"
    )
    hoperesult: str = Field(
        description="预期结果描述, 针对该条数据的具体预期"
    )
    iscaserun: bool = Field(
        default=True,
        description="是否执行该条测试数据"
    )


class CaseBodyResponse(BaseModel):
    """Agent 最终输出: 测试数据列表"""
    thinking: Optional[str] = Field(
        default=None,
        description="生成测试数据时的思考过程(可选)"
    )
    body: List[CaseBodyItem] = Field(
        description="生成的测试数据列表, 1-3条"
    )
