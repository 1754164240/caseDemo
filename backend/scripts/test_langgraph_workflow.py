"""
测试 LangGraph 自动化用例工作流

测试流程：
1. 启动工作流
2. 检查是否需要人工审核
3. 模拟人工审核通过
4. 验证用例创建成功
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.automation_workflow_service import AutomationWorkflowService
from app.db.session import SessionLocal


def test_workflow():
    """测试完整的工作流"""

    print("=" * 80)
    print("开始测试 LangGraph 自动化用例工作流")
    print("=" * 80)

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 创建工作流服务
        workflow_svc = AutomationWorkflowService(db)
        print("\n[OK] 工作流服务创建成功")

        # 准备测试数据
        thread_id = "test_workflow_001"
        initial_state = {
            "name": "理赔测试用例_自动化",
            "module_id": "MOD_TEST_001",
            "scene_id": "SCENE_TEST_001",
            "scenario_type": "API",
            "description": "测试 LangGraph 工作流的自动化用例生成",
            "test_case_info": {
                "title": "被保人出险理赔流程测试",
                "description": "测试被保人出险后的完整理赔流程",
                "preconditions": "1. 保单有效\n2. 被保人身份已认证",
                "test_steps": "1. 提交理赔申请\n2. 上传相关证明材料\n3. 等待审核\n4. 审核通过\n5. 结案",
                "expected_result": "成功结案，理赔金额正确",
                "test_type": "功能测试",
                "priority": "P0"
            }
        }

        print(f"\n[INFO] 测试数据准备完成")
        print(f"   线程ID: {thread_id}")
        print(f"   用例名称: {initial_state['name']}")
        print(f"   场景ID: {initial_state['scene_id']}")

        # 步骤 1: 启动工作流
        print("\n" + "=" * 80)
        print("步骤 1: 启动工作流")
        print("=" * 80)

        current_state = workflow_svc.start_workflow(initial_state, thread_id)

        print(f"\n[STATUS] 工作流状态:")
        print(f"   状态: {current_state.get('status')}")
        print(f"   当前步骤: {current_state.get('current_step')}")
        print(f"   重试次数: {current_state.get('retry_count', 0)}")

        # 检查工作流状态
        status = current_state.get("status")

        if status == "failed":
            print(f"\n[ERROR] 工作流执行失败: {current_state.get('error')}")
            return False

        elif status == "completed":
            print(f"\n[OK] 工作流自动完成（无需人工审核）")
            print(f"   新用例ID: {current_state.get('new_usercase_id')}")
            return True

        elif status == "reviewing":
            print(f"\n[PAUSE]  工作流已暂停，等待人工审核")

            # 显示生成的数据
            generated_body = current_state.get("generated_body", [])
            print(f"\n[DATA] AI 生成了 {len(generated_body)} 条测试数据:")
            for idx, body in enumerate(generated_body):
                print(f"   {idx + 1}. {body.get('casedesc', '未命名')}")

            # 显示校验结果
            validation_result = current_state.get("validation_result")
            if validation_result:
                print(f"\n[CHECK] 校验结果:")
                print(f"   总数: {validation_result.get('total')}")
                print(f"   有效: {validation_result.get('valid_count')}")
                print(f"   无效: {validation_result.get('invalid_count')}")
                print(f"   错误数: {validation_result.get('total_errors')}")

                # 显示错误详情
                if validation_result.get('total_errors', 0) > 0:
                    print(f"\n[WARN]  校验错误详情:")
                    for result in validation_result.get('results', []):
                        if not result['validation']['valid']:
                            print(f"   数据 {result['index'] + 1} ({result['casedesc']}):")
                            for error in result['validation']['errors']:
                                print(f"      - {error.get('fieldName', error.get('field'))}: {error.get('message')}")

            # 步骤 2: 模拟人工审核
            print("\n" + "=" * 80)
            print("步骤 2: 模拟人工审核")
            print("=" * 80)

            # 这里可以选择：
            # 1. approved - 直接通过
            # 2. modified - 修改后通过
            # 3. rejected - 拒绝重新生成

            review_status = "approved"  # 测试时直接通过
            print(f"\n[USER] 提交人工审核: {review_status}")

            final_state = workflow_svc.update_human_review(
                thread_id=thread_id,
                review_status=review_status,
                feedback="测试：数据无误，直接通过"
            )

            print(f"\n[STATUS] 最终状态:")
            print(f"   状态: {final_state.get('status')}")
            print(f"   当前步骤: {final_state.get('current_step')}")

            if final_state.get("status") == "completed":
                print(f"\n[OK] 工作流执行成功！")
                print(f"   新用例ID: {final_state.get('new_usercase_id')}")
                return True
            else:
                print(f"\n[ERROR] 工作流执行失败: {final_state.get('error')}")
                return False

        else:
            print(f"\n[WARN]  未知状态: {status}")
            return False

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


def test_workflow_with_rejection():
    """测试拒绝后重新生成的流程"""

    print("\n" + "=" * 80)
    print("测试场景 2: 人工拒绝并重新生成")
    print("=" * 80)

    db = SessionLocal()

    try:
        workflow_svc = AutomationWorkflowService(db)

        thread_id = "test_workflow_002"
        initial_state = {
            "name": "理赔测试用例_重新生成",
            "module_id": "MOD_TEST_002",
            "scene_id": "SCENE_TEST_001",
            "test_case_info": {
                "title": "测试重新生成流程",
                "test_steps": "1. 测试步骤",
                "expected_result": "预期结果"
            }
        }

        # 启动工作流
        current_state = workflow_svc.start_workflow(initial_state, thread_id)

        if current_state.get("status") == "reviewing":
            print(f"\n[PAUSE]  工作流已暂停，模拟拒绝")

            # 拒绝并重新生成
            final_state = workflow_svc.update_human_review(
                thread_id=thread_id,
                review_status="rejected",
                feedback="测试：数据不符合要求，重新生成"
            )

            print(f"\n[STATUS] 拒绝后状态:")
            print(f"   状态: {final_state.get('status')}")
            print(f"   重试次数: {final_state.get('retry_count', 0)}")

            # 注意：拒绝后会重新生成，如果再次需要审核，会再次暂停
            if final_state.get("status") == "reviewing":
                print(f"\n[PAUSE]  重新生成后再次需要审核")
                return True
            elif final_state.get("status") == "completed":
                print(f"\n[OK] 重新生成后自动完成")
                return True
            else:
                print(f"\n[WARN]  状态: {final_state.get('status')}")
                return False

        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        return False

    finally:
        db.close()


if __name__ == "__main__":
    print("\n")
    print("=" + "=" * 78 + "=")
    print("|" + " " * 20 + "LangGraph 工作流测试套件" + " " * 33 + "|")
    print("=" + "=" * 78 + "=")

    # 测试 1: 正常流程
    success1 = test_workflow()

    # 测试 2: 拒绝重新生成流程（可选）
    # success2 = test_workflow_with_rejection()

    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    if success1:
        print("[OK] 测试通过：工作流运行正常")
    else:
        print("[ERROR] 测试失败：请检查错误信息")

    print("\n")
