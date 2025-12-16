from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.scenario import Scenario as ScenarioModel
from app.schemas.scenario import Scenario, ScenarioCreate, ScenarioUpdate

router = APIRouter()


@router.get("/", response_model=List[Scenario])
def list_scenarios(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=500, description="返回的最大记录数"),
    search: Optional[str] = Query(None, description="搜索关键字（场景名称、描述、编号）"),
    business_line: Optional[str] = Query(None, description="业务线筛选"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    module: Optional[str] = Query(None, description="模块筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取场景列表
    
    支持分页、搜索和多条件筛选
    """
    query = db.query(ScenarioModel)
    
    # 搜索功能
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                ScenarioModel.scenario_code.ilike(search_pattern),
                ScenarioModel.name.ilike(search_pattern),
                ScenarioModel.description.ilike(search_pattern)
            )
        )
    
    # 业务线筛选
    if business_line:
        query = query.filter(ScenarioModel.business_line == business_line)
    
    # 渠道筛选
    if channel:
        query = query.filter(ScenarioModel.channel == channel)
    
    # 模块筛选
    if module:
        query = query.filter(ScenarioModel.module == module)
    
    # 启用状态筛选
    if is_active is not None:
        query = query.filter(ScenarioModel.is_active == is_active)
    
    # 按创建时间倒序排序
    query = query.order_by(ScenarioModel.created_at.desc())
    
    scenarios = query.offset(skip).limit(limit).all()
    return scenarios


@router.get("/{scenario_id}", response_model=Scenario)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个场景详情
    """
    scenario = db.query(ScenarioModel).filter(ScenarioModel.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    return scenario


@router.post("/", response_model=Scenario)
def create_scenario(
    scenario_in: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新场景
    """
    # 检查场景编号是否已存在
    existing = db.query(ScenarioModel).filter(
        ScenarioModel.scenario_code == scenario_in.scenario_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"场景编号 {scenario_in.scenario_code} 已存在"
        )
    
    # 创建场景
    scenario = ScenarioModel(**scenario_in.model_dump())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    
    print(f"[INFO] 用户 {current_user.username} 创建场景: {scenario.name} ({scenario.scenario_code})")
    
    return scenario


@router.put("/{scenario_id}", response_model=Scenario)
def update_scenario(
    scenario_id: int,
    scenario_in: ScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新场景信息
    """
    scenario = db.query(ScenarioModel).filter(ScenarioModel.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 如果要更新场景编号，检查新编号是否已被其他场景使用
    if scenario_in.scenario_code and scenario_in.scenario_code != scenario.scenario_code:
        existing = db.query(ScenarioModel).filter(
            ScenarioModel.scenario_code == scenario_in.scenario_code,
            ScenarioModel.id != scenario_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"场景编号 {scenario_in.scenario_code} 已被其他场景使用"
            )
    
    # 更新字段
    update_data = scenario_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)
    
    db.commit()
    db.refresh(scenario)
    
    print(f"[INFO] 用户 {current_user.username} 更新场景: {scenario.name} ({scenario.scenario_code})")
    
    return scenario


@router.delete("/{scenario_id}")
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除场景
    """
    scenario = db.query(ScenarioModel).filter(ScenarioModel.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    scenario_info = f"{scenario.name} ({scenario.scenario_code})"
    
    db.delete(scenario)
    db.commit()
    
    print(f"[INFO] 用户 {current_user.username} 删除场景: {scenario_info}")
    
    return {"message": f"场景 {scenario_info} 已成功删除"}


@router.get("/code/{scenario_code}", response_model=Scenario)
def get_scenario_by_code(
    scenario_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    通过场景编号获取场景详情
    """
    scenario = db.query(ScenarioModel).filter(
        ScenarioModel.scenario_code == scenario_code
    ).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail=f"场景编号 {scenario_code} 不存在")
    
    return scenario


@router.post("/{scenario_id}/toggle-status", response_model=Scenario)
def toggle_scenario_status(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    切换场景的启用/停用状态
    """
    scenario = db.query(ScenarioModel).filter(ScenarioModel.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 切换状态
    scenario.is_active = not scenario.is_active
    db.commit()
    db.refresh(scenario)
    
    status_text = "启用" if scenario.is_active else "停用"
    print(f"[INFO] 用户 {current_user.username} {status_text}场景: {scenario.name} ({scenario.scenario_code})")
    
    return scenario

