"""字段变量查询工具 - 供 Agent 实时获取用例的字段定义和示例值"""

import json
import requests
from langchain.tools import tool


# 模块级变量，由调用方在创建 Agent 前注入
_base_url: str = ""
_usercase_id: str = ""


def set_base_url(base_url: str):
    """注入自动化平台 API 基础地址"""
    global _base_url
    _base_url = (base_url or "").rstrip("/")


def set_usercase_id(usercase_id: str):
    """注入当前用例 ID"""
    global _usercase_id
    _usercase_id = usercase_id or ""


@tool("query_field_variables")
def query_field_variables_tool(usercase_id: str = "") -> str:
    """查询用例的所有字段变量定义，包括字段名、中文名、示例值、所属分组和关联标识。
    在生成测试数据之前调用此工具，获取完整的字段定义信息。

    Args:
        usercase_id: 用例ID。如果不传，使用当前上下文中的用例ID。

    Returns:
        按分组返回的字段变量列表（JSON格式），每个变量包含：
        - varCode: 字段名（变量代码）
        - varName: 字段中文名
        - vargroup: 所属分组（如 Appnt=投保人, Insured=被保人, Risk=险种）
        - data: 示例值/默认值
        - dataKey: 数据字典名（可用于 query_enum_values 查询枚举值）
        - flag: 联动标识（可用于 query_linkage_rules 查询关联选项）
    """
    case_id = usercase_id or _usercase_id
    if not case_id:
        return "未提供用例ID，无法查询字段变量。"

    if not _base_url:
        return "未配置平台地址，无法查询字段变量。"

    try:
        url = f"{_base_url}/ai/case/variables/{case_id}"
        print(f"[TOOL] 查询字段变量: GET {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and result.get("data"):
            groups = result["data"]
            # 格式化输出：按分组展示字段
            formatted = []
            total_vars = 0
            for group in groups:
                group_info = {
                    "vargroup": group.get("vargroup", ""),
                    "name": group.get("name", ""),
                    "fields": []
                }
                for var in group.get("var", []):
                    field_info = {
                        "varCode": var.get("varCode", ""),
                        "varName": var.get("varName", ""),
                        "data": var.get("data", ""),
                        "dataKey": var.get("dataKey"),
                        "flag": var.get("flag"),
                    }
                    group_info["fields"].append(field_info)
                    total_vars += 1
                formatted.append(group_info)

            print(f"[TOOL] 查询到 {len(groups)} 个分组, {total_vars} 个字段变量")
            return json.dumps(formatted, ensure_ascii=False)
        else:
            msg = result.get("message", "未知错误")
            return f"查询字段变量失败: {msg}"

    except requests.exceptions.RequestException as e:
        print(f"[TOOL] 查询字段变量 API 失败: {e}")
        return f"查询字段变量接口异常: {e}"
    except Exception as e:
        print(f"[TOOL] 查询字段变量异常: {e}")
        return f"查询字段变量异常: {e}"
