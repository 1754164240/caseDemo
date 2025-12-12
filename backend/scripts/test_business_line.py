"""测试业务线功能"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ai_service import AIService
from app.db.session import SessionLocal


def test_business_line_detection():
    """测试业务线识别功能"""
    print("=" * 60)
    print("测试业务线识别功能")
    print("=" * 60)
    
    db = SessionLocal()
    ai_service = AIService(db=db)
    
    # 测试契约业务需求
    contract_text = """
    保险投保系统需求
    
    1. 投保人信息录入
       - 姓名、身份证号、联系方式
       - 职业、收入情况
       - 健康状况告知
    
    2. 保险产品选择
       - 产品类型选择
       - 保额设置
       - 保险期间设置
    
    3. 保费计算
       - 根据年龄、性别、职业计算保费
       - 显示保费明细
    
    4. 核保流程
       - 自动核保规则
       - 人工核保转介
    """
    
    print("\n测试契约业务需求:")
    print("-" * 60)
    try:
        test_points = ai_service.extract_test_points(contract_text)
        print(f"✅ 成功提取 {len(test_points)} 个测试点")
        for i, tp in enumerate(test_points, 1):
            print(f"\n{i}. {tp.get('title', 'N/A')}")
            print(f"   业务线: {tp.get('business_line', 'N/A')}")
            print(f"   分类: {tp.get('category', 'N/A')}")
            print(f"   优先级: {tp.get('priority', 'N/A')}")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    # 测试保全业务需求
    preservation_text = """
    保单保全系统需求
    
    1. 保单信息变更
       - 联系方式变更
       - 地址变更
       - 职业变更
    
    2. 受益人变更
       - 受益人信息修改
       - 受益比例调整
       - 变更生效时间
    
    3. 保额调整
       - 增加保额
       - 减少保额
       - 费用计算
    """
    
    print("\n\n测试保全业务需求:")
    print("-" * 60)
    try:
        test_points = ai_service.extract_test_points(preservation_text)
        print(f"✅ 成功提取 {len(test_points)} 个测试点")
        for i, tp in enumerate(test_points, 1):
            print(f"\n{i}. {tp.get('title', 'N/A')}")
            print(f"   业务线: {tp.get('business_line', 'N/A')}")
            print(f"   分类: {tp.get('category', 'N/A')}")
            print(f"   优先级: {tp.get('priority', 'N/A')}")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    # 测试理赔业务需求
    claim_text = """
    保险理赔系统需求
    
    1. 理赔申请
       - 出险信息录入
       - 理赔材料上传
       - 申请提交
    
    2. 理赔审核
       - 材料完整性检查
       - 责任认定
       - 赔付金额计算
    
    3. 理赔支付
       - 支付方式选择
       - 支付信息确认
       - 支付执行
    """
    
    print("\n\n测试理赔业务需求:")
    print("-" * 60)
    try:
        test_points = ai_service.extract_test_points(claim_text)
        print(f"✅ 成功提取 {len(test_points)} 个测试点")
        for i, tp in enumerate(test_points, 1):
            print(f"\n{i}. {tp.get('title', 'N/A')}")
            print(f"   业务线: {tp.get('business_line', 'N/A')}")
            print(f"   分类: {tp.get('category', 'N/A')}")
            print(f"   优先级: {tp.get('priority', 'N/A')}")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_test_case_generation():
    """测试根据业务线生成测试用例"""
    print("\n\n" + "=" * 60)
    print("测试根据业务线生成测试用例")
    print("=" * 60)
    
    db = SessionLocal()
    ai_service = AIService(db=db)
    
    # 测试契约业务线测试用例生成
    contract_test_point = {
        "title": "投保人信息验证",
        "description": "验证投保人基本信息的完整性和准确性",
        "category": "功能",
        "priority": "high",
        "business_line": "contract"
    }
    
    print("\n测试契约业务线测试用例生成:")
    print("-" * 60)
    try:
        test_cases = ai_service.generate_test_cases(contract_test_point, "投保系统需求")
        print(f"✅ 成功生成 {len(test_cases)} 个测试用例")
        for i, tc in enumerate(test_cases, 1):
            print(f"\n{i}. {tc.get('title', 'N/A')}")
            print(f"   描述: {tc.get('description', 'N/A')}")
            print(f"   测试类型: {tc.get('test_type', 'N/A')}")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    # 测试保全业务线测试用例生成
    preservation_test_point = {
        "title": "受益人变更",
        "description": "验证受益人变更流程",
        "category": "功能",
        "priority": "high",
        "business_line": "preservation"
    }
    
    print("\n\n测试保全业务线测试用例生成:")
    print("-" * 60)
    try:
        test_cases = ai_service.generate_test_cases(preservation_test_point, "保全系统需求")
        print(f"✅ 成功生成 {len(test_cases)} 个测试用例")
        for i, tc in enumerate(test_cases, 1):
            print(f"\n{i}. {tc.get('title', 'N/A')}")
            print(f"   描述: {tc.get('description', 'N/A')}")
            print(f"   测试类型: {tc.get('test_type', 'N/A')}")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    # 测试理赔业务线测试用例生成
    claim_test_point = {
        "title": "理赔审核",
        "description": "验证理赔审核流程",
        "category": "功能",
        "priority": "high",
        "business_line": "claim"
    }
    
    print("\n\n测试理赔业务线测试用例生成:")
    print("-" * 60)
    try:
        test_cases = ai_service.generate_test_cases(claim_test_point, "理赔系统需求")
        print(f"✅ 成功生成 {len(test_cases)} 个测试用例")
        for i, tc in enumerate(test_cases, 1):
            print(f"\n{i}. {tc.get('title', 'N/A')}")
            print(f"   描述: {tc.get('description', 'N/A')}")
            print(f"   测试类型: {tc.get('test_type', 'N/A')}")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    print("\n开始测试业务线功能...\n")
    
    # 测试业务线识别
    test_business_line_detection()
    
    # 测试测试用例生成
    test_test_case_generation()
    
    print("\n所有测试完成!")
