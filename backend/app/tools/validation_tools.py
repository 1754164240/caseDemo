"""数据校验工具 - 供 Agent 在生成测试数据后自行校验"""

import json
from langchain.tools import tool


# 模块级变量，由调用方在创建 Agent 前注入
_field_metadata: dict = {}


def set_field_metadata(metadata: dict):
    """注入字段元数据"""
    global _field_metadata
    _field_metadata = metadata or {}


@tool("validate_body_data")
def validate_body_data_tool(body_json: str) -> str:
    """校验生成的测试数据是否符合字段约束。在你生成完测试数据后、提交最终结果前，请调用此工具进行校验。
    如果校验发现错误，请根据错误提示修正数据后重新提交。

    Args:
        body_json: 测试数据的JSON字符串，格式为 {"var": {"字段名": "值", ...}}

    Returns:
        校验结果，包含是否通过、错误列表和修改建议。
    """
    if not _field_metadata or not _field_metadata.get('fields'):
        return json.dumps({"valid": True, "message": "无元数据，跳过校验"}, ensure_ascii=False)

    try:
        body_data = json.loads(body_json)
    except json.JSONDecodeError as e:
        return json.dumps({"valid": False, "errors": [f"JSON解析失败: {e}"]}, ensure_ascii=False)

    from app.services.body_validator import BodyValidator
    validator = BodyValidator(_field_metadata)
    result = validator.validate(body_data)
    return json.dumps(result, ensure_ascii=False, default=str)
