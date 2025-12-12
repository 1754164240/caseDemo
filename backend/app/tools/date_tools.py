from datetime import datetime, timezone, timedelta
from langchain.tools import tool


# 使用固定东八区时间，避免服务器时区导致日期错误
CN_TZ = timezone(timedelta(hours=8))


@tool("current_date")
def current_date_tool() -> str:
    """返回当前日期（东八区），格式为 YYYY-MM-DD"""
    return datetime.now(CN_TZ).strftime("%Y-%m-%d")


@tool("current_datetime")
def current_datetime_tool() -> str:
    """返回当前日期和时间（东八区），格式为 YYYY-MM-DD HH:MM:SS"""
    return datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")
