"""工具包入口 - 统一导出所有 Agent 工具"""

from .date_tools import current_date_tool, current_datetime_tool, current_date_yyyymmdd_tool
from .enum_tools import (
    query_enum_values_tool,
    query_required_fields_tool,
    query_linkage_rules_tool,
    set_field_metadata as set_enum_metadata,
    set_base_url as set_enum_base_url,
)
from .field_variable_tools import (
    query_field_variables_tool,
    set_base_url as set_field_var_base_url,
    set_usercase_id as set_field_var_usercase_id,
)
from .function_tools import (
    query_function_info_tool,
    set_base_url as set_func_base_url,
)
from .validation_tools import (
    validate_body_data_tool,
    set_field_metadata as set_validation_metadata,
)


# 所有工具列表（用于快速注册）
ALL_DATE_TOOLS = [current_date_tool, current_datetime_tool, current_date_yyyymmdd_tool]
ALL_ENUM_TOOLS = [query_enum_values_tool, query_required_fields_tool, query_linkage_rules_tool]
ALL_FIELD_TOOLS = [query_field_variables_tool]
ALL_FUNCTION_TOOLS = [query_function_info_tool]
ALL_VALIDATION_TOOLS = [validate_body_data_tool]
ALL_CASE_BODY_TOOLS = ALL_DATE_TOOLS + ALL_ENUM_TOOLS + ALL_FIELD_TOOLS + ALL_FUNCTION_TOOLS + ALL_VALIDATION_TOOLS


def setup_metadata_for_tools(metadata: dict, base_url: str = "", usercase_id: str = ""):
    """统一设置元数据、平台地址和用例ID到所有需要的工具模块"""
    set_enum_metadata(metadata)
    set_validation_metadata(metadata)
    if base_url:
        set_enum_base_url(base_url)
        set_field_var_base_url(base_url)
        set_func_base_url(base_url)
    if usercase_id:
        set_field_var_usercase_id(usercase_id)
