from typing import Iterable, List

from sqlalchemy.orm import Session

from app.models.test_case import TestCase
from app.models.workflow_task import WorkflowTask


def _normalize_ids(ids: Iterable[int]) -> List[int]:
    return [item_id for item_id in ids if item_id is not None]


def detach_workflow_tasks_from_test_cases(db: Session, test_case_ids: Iterable[int]) -> int:
    """删除测试用例前，保留工作流历史并解除用例引用。"""
    normalized_ids = _normalize_ids(test_case_ids)
    if not normalized_ids:
        return 0

    return (
        db.query(WorkflowTask)
        .filter(WorkflowTask.test_case_id.in_(normalized_ids))
        .update({WorkflowTask.test_case_id: None}, synchronize_session=False)
    )


def detach_workflow_tasks_for_test_points(db: Session, test_point_ids: Iterable[int]) -> int:
    """删除测试点关联用例前，解除这些用例上的工作流任务引用。"""
    normalized_ids = _normalize_ids(test_point_ids)
    if not normalized_ids:
        return 0

    test_case_ids = [
        row[0]
        for row in (
            db.query(TestCase.id)
            .filter(TestCase.test_point_id.in_(normalized_ids))
            .all()
        )
    ]
    return detach_workflow_tasks_from_test_cases(db, test_case_ids)
