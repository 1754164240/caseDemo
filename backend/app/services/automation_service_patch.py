# 优化后的 select_best_case_by_ai 方法
# 将此代码替换到 automation_service.py 的 220-293 行

def select_best_case_by_ai(
    self,
    test_case_info: Dict[str, Any],
    available_cases: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    使用AI选择最匹配的用例

    Args:
        test_case_info: 测试用例信息（标题、描述等）
        available_cases: 可用的用例列表

    Returns:
        选中的用例（包含完整信息），如果没有合适的返回None
    """
    try:
        from app.services.ai_service import get_ai_service
        import concurrent.futures

        # 传入db以读取数据库配置
        ai_service = get_ai_service(self.db)
        if not ai_service:
            print("[WARNING] AI服务不可用，使用第一个用例")
            return available_cases[0] if available_cases else None

        # 限制用例数量，避免prompt过长
        max_cases = 5
        if len(available_cases) > max_cases:
            print(f"[INFO] 用例数量过多({len(available_cases)}个)，仅使用前{max_cases}个")
            available_cases = available_cases[:max_cases]

        # 构建用例列表，限制描述长度
        cases_for_ai = []
        for idx, c in enumerate(available_cases):
            desc = str(c.get('description', ''))
            # 限制描述长度为100字符
            if len(desc) > 100:
                desc = desc[:100] + "..."

            case_info = {
                'index': idx,
                'usercaseId': str(c.get('usercaseId', '')),
                'name': str(c.get('name', '')),
                'description': desc
            }
            cases_for_ai.append(case_info)

        # 限制测试用例信息的长度
        def truncate(text, max_len=200):
            text = str(text) if text else ''
            return text[:max_len] + "..." if len(text) > max_len else text

        # 准备prompt（简化版本）
        prompt = f"""你是一个自动化测试专家。选择最匹配的用例模板。

测试用例：
标题：{truncate(test_case_info.get('title', ''), 100)}
描述：{truncate(test_case_info.get('description', ''), 200)}

可选模板：
{json.dumps(cases_for_ai, ensure_ascii=False)}

只返回usercaseId，不要其他内容。"""

        print(f"[INFO] 使用AI选择最佳用例...")
        print(f"[DEBUG] 可选用例数量: {len(available_cases)}")
        print(f"[DEBUG] Prompt长度: {len(prompt)} 字符")

        # 使用线程池执行AI调用，设置60秒超时
        def call_ai():
            return ai_service.llm.invoke(prompt)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(call_ai)
            try:
                response = future.result(timeout=60)  # 60秒超时

                selected_id = response.content.strip()
                print(f"[INFO] AI选择的用例ID: {selected_id}")

                # 查找匹配的用例（在原始列表中查找，不是截断的）
                original_cases = self.get_scene_cases(test_case_info.get('scene_id')) if len(available_cases) < 10 else available_cases
                for c in original_cases if len(available_cases) < 10 else available_cases:
                    if str(c.get('usercaseId', '')) == selected_id:
                        print(f"[INFO] 找到匹配的用例: {c.get('name', '')}")
                        return c

                print(f"[WARNING] AI返回的ID无效，使用第一个用例")
                return available_cases[0] if available_cases else None

            except concurrent.futures.TimeoutError:
                print(f"[ERROR] AI调用超时（60秒），使用第一个用例")
                return available_cases[0] if available_cases else None

    except Exception as e:
        print(f"[ERROR] AI选择用例失败: {e}")
        import traceback
        traceback.print_exc()
        return available_cases[0] if available_cases else None
