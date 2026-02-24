"""函数信息查询工具 - 供 Agent 查询系统函数/自定义函数的详细信息"""

import json
import requests
from urllib.parse import quote
from langchain.tools import tool


# 模块级变量，由调用方在创建 Agent 前注入
_base_url: str = ""


def set_base_url(base_url: str):
    """注入自动化平台 API 基础地址"""
    global _base_url
    _base_url = (base_url or "").rstrip("/")


@tool("query_function_info")
def query_function_info_tool(function_id: str) -> str:
    """查询系统函数或自定义函数的详细信息。当字段的取值类型为"系统函数"或"自定义函数"时，
    可通过此工具查询该函数的名称、描述、参数等信息，了解该函数的作用。

    Args:
        function_id: 函数ID（来自字段定义中 getdatatype 为 2 或 4 的字段的 data 值）

    Returns:
        函数详细信息（JSON格式），包含函数名称、描述、参数等。
        如果查询失败，返回提示信息。
    """
    if not function_id:
        return "未提供函数ID，无法查询函数信息。"

    if not _base_url:
        return "未配置平台地址，无法查询函数信息。"

    try:
        url = f"{_base_url}/ai/case/function/{function_id}"
        print(f"[TOOL] 查询函数信息: GET {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and result.get("data"):
            data = result["data"]
            print(f"[TOOL] 函数 '{function_id}' 查询成功")
            return json.dumps(data, ensure_ascii=False)
        else:
            msg = result.get("message", "未知错误")
            return f"查询函数信息失败: {msg}"

    except requests.exceptions.RequestException as e:
        print(f"[TOOL] 查询函数信息 API 失败: {e}")
        return f"查询函数信息接口异常: {e}"
    except Exception as e:
        print(f"[TOOL] 查询函数信息异常: {e}")
        return f"查询函数信息异常: {e}"


@tool("query_risk_config")
def query_risk_config_tool(query: str) -> str:
    """查询险种配置信息。当你需要根据险种编码或险种名称生成相关测试数据时，请调用此工具。

    Args:
        query: 险种编码或险种名称（支持模糊输入）

    Returns:
        险种配置列表（JSON格式）。
        如果查询失败，返回提示信息。
    """
    if not query:
        return "未提供 query，无法查询险种配置。"

    if not _base_url:
        return "未配置平台地址，无法查询险种配置。"

    try:
        safe_query = quote(str(query), safe="")
        url = f"{_base_url}/ai/case/risk/config/{safe_query}"
        print(f"[TOOL] 查询险种配置: GET {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and isinstance(result.get("data"), list):
            data = result.get("data", [])
            print(f"[TOOL] 险种查询成功，返回 {len(data)} 条配置")
            return json.dumps(data, ensure_ascii=False)

        if isinstance(result.get("data"), list):
            data = result.get("data", [])
            print(f"[TOOL] 险种查询返回 {len(data)} 条配置（未显式 success）")
            return json.dumps(data, ensure_ascii=False)

        msg = result.get("message", "未知错误")
        return f"查询险种配置失败: {msg}"
    except requests.exceptions.RequestException as e:
        print(f"[TOOL] 查询险种配置 API 失败: {e}")
        return f"查询险种配置接口异常: {e}"
    except Exception as e:
        print(f"[TOOL] 查询险种配置异常: {e}")
        return f"查询险种配置异常: {e}"
