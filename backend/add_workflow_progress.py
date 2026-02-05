"""
批量为工作流节点添加 WebSocket 进度推送
"""

import re

# 节点到步骤名称的映射
NODE_TO_STEP = {
    "_match_scenario_by_ai": ("match_scenario", "正在使用 AI 智能匹配场景"),
    "_load_module_config": ("load_module_config", "正在从系统配置读取模块 ID"),
    "_fetch_scene_cases": ("fetch_cases", "正在获取场景用例列表"),
    "_select_template_by_ai": ("select_template", "正在使用 AI 选择最佳模板"),
    "_fetch_case_details": ("fetch_details", "正在获取用例详情和字段元数据"),
    "_generate_test_data": ("generate_data", "正在使用 AI 生成测试数据"),
    "_validate_generated_data": ("validate_data", "正在校验生成的测试数据"),
    "_human_review": ("human_review", "等待人工审核"),
    "_apply_corrections": ("apply_corrections", "正在应用人工审核结果"),
    "_create_automation_case": ("create_case", "正在创建自动化用例"),
    "_regenerate_data": ("regenerate", "正在重新生成测试数据"),
}

def add_progress_to_file():
    file_path = "app/services/automation_workflow_service.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = content

    for method_name, (step_name, message) in NODE_TO_STEP.items():
        # 查找方法定义
        pattern = rf'(def {method_name}\(self, state: AutomationCaseState\) -> AutomationCaseState:\n        """[^"]*""")\n(        \w+)'

        # 添加进度推送代码
        replacement = rf'\1\n        # 发送进度\n        self._send_progress(state, "{step_name}", "running", "{message}")\n\n\2'

        modified = re.sub(pattern, replacement, modified, count=1)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified)

    print("已成功添加进度推送到所有工作流节点")

if __name__ == "__main__":
    add_progress_to_file()
