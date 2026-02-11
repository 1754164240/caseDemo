"""枚举值查询工具 - 供 Agent 在生成测试数据时查询字段的有效值范围"""

import json
import requests
from langchain.tools import tool


# 模块级变量，由调用方在创建 Agent 前注入
_field_metadata: dict = {}
_base_url: str = ""


def set_field_metadata(metadata: dict):
    """注入字段元数据（在创建 Agent 前调用）"""
    global _field_metadata
    _field_metadata = metadata or {}


def set_base_url(base_url: str):
    """注入自动化平台 API 基础地址（在创建 Agent 前调用）"""
    global _base_url
    _base_url = (base_url or "").rstrip("/")


@tool("query_enum_values")
def query_enum_values_tool(dict_name: str) -> str:
    """查询指定字典名的所有有效枚举值。当你需要为某个字段生成测试数据、但不确定有效值范围时，请调用此工具。
    传入字段定义中的 dataKey 值（如 'sex', 'payintv', 'relationCode' 等），工具会实时从平台查询对应的字典枚举值。

    Args:
        dict_name: 字段定义中的 dataKey 值（如 'sex', 'payintv', 'occupationCode' 等）

    Returns:
        该字段的枚举值列表（JSON格式），包含 value 和 label。
        如果查询失败或无枚举值，返回提示信息。
    """
    # 优先从实时 API 查询
    if _base_url:
        try:
            url = f"{_base_url}/ai/case/dict/{dict_name}"
            print(f"[TOOL] 查询枚举值: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()

            # 提取枚举值列表
            data = result.get("data", result.get("content", []))
            if isinstance(data, list) and len(data) > 0:
                enum_list = []
                for item in data:
                    enum_list.append({
                        "value": item.get("value", ""),
                        "label": item.get("label", "")
                    })
                print(f"[TOOL] 字典 '{dict_name}' 查询到 {len(enum_list)} 个枚举值")
                return json.dumps(enum_list, ensure_ascii=False)
            else:
                print(f"[TOOL] 字典 '{dict_name}' 无枚举数据")
                # API 返回空，降级到元数据查询
        except requests.exceptions.RequestException as e:
            print(f"[TOOL] 查询枚举值 API 失败: {e}，降级到元数据查询")
        except Exception as e:
            print(f"[TOOL] 查询枚举值异常: {e}，降级到元数据查询")

    # 降级: 从内存中的字段元数据查询
    if _field_metadata:
        for field in _field_metadata.get('fields', []):
            if field.get('row') == dict_name:
                enums = field.get('enums', [])
                if enums:
                    result = [{"value": e.get('value', ''), "label": e.get('label', '')} for e in enums]
                    return json.dumps(result, ensure_ascii=False)
                else:
                    return f"字段 '{dict_name}' 没有枚举值约束，可自由填写。"

    return f"未找到字段 '{dict_name}' 的枚举值信息，请根据业务经验自行填写。"


@tool("query_required_fields")
def query_required_fields_tool() -> str:
    """查询当前场景下哪些字段是必填的。在生成测试数据之前调用此工具，确保不遗漏必填字段。

    Returns:
        必填字段列表（JSON格式），包含字段名和中文名。
    """
    if not _field_metadata:
        return "当前场景没有字段元数据。"

    required = []
    for field in _field_metadata.get('fields', []):
        if field.get('required'):
            required.append({
                "row": field.get('row', ''),
                "rowName": field.get('rowName', ''),
                "type": field.get('type', '')
            })

    if required:
        return json.dumps(required, ensure_ascii=False)
    return "当前场景没有明确标记为必填的字段。"


@tool("query_linkage_rules")
def query_linkage_rules_tool(flag: str) -> str:
    """查询字段的联动关联选项列表。当你需要了解某个字段关联了哪些可选值时调用。
    传入字段的 flag 标识，工具会实时从平台查询该字段关联的选项（如险种列表、缴费方式等）。

    Args:
        flag: 字段的 flag 标识值（来自字段定义中的 flag 字段，如 'RiskFlag', 'PayFlag' 等）

    Returns:
        关联选项列表（JSON格式），按分组返回，每个选项包含 name（名称）和 code（代码）。
    """
    # 优先从实时 API 查询
    if _base_url:
        try:
            url = f"{_base_url}/linkage/list/{flag}/API"
            print(f"[TOOL] 查询联动规则: POST {url}")
            response = requests.post(url, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("success") and result.get("data"):
                data = result["data"]
                # data 是按分组 key 组织的字典，如 {"RiskFlag": [{name, code, property}, ...]}
                linkage_result = {}
                for group_key, items in data.items():
                    if isinstance(items, list):
                        linkage_result[group_key] = [
                            {"name": item.get("name", ""), "code": item.get("code", "")}
                            for item in items
                        ]
                total = sum(len(v) for v in linkage_result.values())
                print(f"[TOOL] flag '{flag}' 查询到 {total} 个关联选项")
                return json.dumps(linkage_result, ensure_ascii=False)
            else:
                print(f"[TOOL] flag '{flag}' 无联动数据")
        except requests.exceptions.RequestException as e:
            print(f"[TOOL] 查询联动规则 API 失败: {e}，降级到元数据查询")
        except Exception as e:
            print(f"[TOOL] 查询联动规则异常: {e}，降级到元数据查询")

    # 降级: 从内存中的字段元数据查询
    if _field_metadata:
        rules = []
        for field in _field_metadata.get('fields', []):
            # 按 flag 匹配或按字段名匹配
            if field.get('flag') != flag and field.get('row') != flag:
                continue

            row = field.get('row', '')
            row_name = field.get('rowName', row)

            for dep in field.get('enumDependencies', []):
                rules.append({
                    "field": row,
                    "fieldName": row_name,
                    "whenValue": dep.get('enumValue', ''),
                    "showFields": dep.get('showFields', []),
                    "hideFields": dep.get('hideFields', []),
                    "requiredFields": dep.get('requiredFields', [])
                })

            for dep in field.get('dependencies', []):
                rules.append({
                    "field": row,
                    "fieldName": row_name,
                    "triggerField": dep.get('triggerField', ''),
                    "triggerValue": dep.get('triggerValue', ''),
                    "action": dep.get('action', 'show')
                })

        if rules:
            return json.dumps(rules[:30], ensure_ascii=False)

    return f"未找到 flag '{flag}' 的联动规则信息。"
