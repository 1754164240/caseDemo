"""枚举值查询工具 - 供 Agent 在生成测试数据时查询字段的有效值范围"""

import json
import requests
from langchain.tools import tool


# 模块级变量，由调用方在创建 Agent 前注入
_base_url: str = ""


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
    if not dict_name:
        return "未提供字典名，无法查询枚举值。"
    if not _base_url:
        return "未配置平台地址，无法查询枚举值。"

    try:
        url = f"{_base_url}/ai/case/dict/{dict_name}"
        print(f"[TOOL] 查询枚举值: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()

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

        print(f"[TOOL] 字典 '{dict_name}' 无枚举数据")
        return f"字典 '{dict_name}' 无枚举数据。"
    except requests.exceptions.RequestException as e:
        print(f"[TOOL] 查询枚举值 API 失败: {e}")
        return f"查询枚举值接口异常: {e}"
    except Exception as e:
        print(f"[TOOL] 查询枚举值异常: {e}")
        return f"查询枚举值异常: {e}"


@tool("query_linkage_rules")
def query_linkage_rules_tool(flag: str) -> str:
    """查询字段的联动关联选项列表。当你需要了解某个字段关联了哪些可选值时调用。
    传入字段的 flag 标识，工具会实时从平台查询该字段关联的选项（如险种列表、缴费方式等）。

    Args:
        flag: 字段的 flag 标识值（来自字段定义中的 flag 字段，如 'RiskFlag', 'PayFlag' 等）

    Returns:
        关联选项列表（JSON格式），按分组返回，每个选项包含 name（名称）和 code（代码）。
    """
    if not flag:
        return "未提供 flag，无法查询联动规则。"
    if not _base_url:
        return "未配置平台地址，无法查询联动规则。"

    try:
        url = f"{_base_url}/linkage/list/{flag}/API"
        print(f"[TOOL] 查询联动规则: POST {url}")
        response = requests.post(url, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and result.get("data"):
            data = result["data"]
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

        print(f"[TOOL] flag '{flag}' 无联动数据")
        return f"flag '{flag}' 无联动数据。"
    except requests.exceptions.RequestException as e:
        print(f"[TOOL] 查询联动规则 API 失败: {e}")
        return f"查询联动规则接口异常: {e}"
    except Exception as e:
        print(f"[TOOL] 查询联动规则异常: {e}")
        return f"查询联动规则异常: {e}"
