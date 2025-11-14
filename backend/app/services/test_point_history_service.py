from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.test_point import TestPoint
from app.models.test_point_history import TestPointHistory


def allocate_requirement_version(db: Session, requirement_id: int) -> str:
    """
    计算指定需求的下一版本号，版本格式 v001/v002...
    """
    latest_version = (
        db.query(func.max(TestPointHistory.version))
        .filter(TestPointHistory.requirement_id == requirement_id)
        .scalar()
    )
    if not latest_version:
        return "v001"
    digits = "".join(ch for ch in latest_version if ch.isdigit())
    try:
        next_index = int(digits) + 1
    except (TypeError, ValueError):
        next_index = 1
    return f"v{next_index:03d}"


def record_history_entry(
    db: Session,
    test_point: TestPoint,
    prompt_summary: str,
    operator_id: Optional[int],
    status: str = "pending",
    version_label: Optional[str] = None,
) -> TestPointHistory:
    """
    写入测试点历史记录，缺省自动分配版本号。
    """
    if version_label is None:
        version_label = allocate_requirement_version(db, test_point.requirement_id)

    history = TestPointHistory(
        test_point_id=test_point.id,
        requirement_id=test_point.requirement_id,
        version=version_label,
        code=test_point.code,
        title=test_point.title,
        description=test_point.description,
        category=test_point.category,
        priority=test_point.priority,
        business_line=test_point.business_line,
        prompt_summary=prompt_summary,
        status=status,
        operator_id=operator_id,
    )
    db.add(history)
    return history
