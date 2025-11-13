from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.model_config import ModelConfig as ModelConfigModel
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    SetDefaultModelRequest
)
from app.api.deps import get_current_active_superuser

router = APIRouter()


def mask_api_key(api_key: str) -> str:
    """脱敏 API Key"""
    if api_key and len(api_key) > 8:
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    return api_key


@router.get("/", response_model=List[ModelConfigResponse])
def list_model_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    include_inactive: bool = False
):
    """获取所有模型配置列表"""
    query = db.query(ModelConfigModel)
    
    if not include_inactive:
        query = query.filter(ModelConfigModel.is_active == True)
    
    configs = query.order_by(
        ModelConfigModel.is_default.desc(),
        ModelConfigModel.created_at.desc()
    ).all()
    
    # 转换为响应格式并脱敏 API Key
    result = []
    for config in configs:
        config_dict = {
            "id": config.id,
            "name": config.name,
            "display_name": config.display_name,
            "description": config.description,
            "api_key_masked": mask_api_key(config.api_key),
            "api_base": config.api_base,
            "model_name": config.model_name,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "provider": config.provider,
            "model_type": config.model_type,
            "is_active": config.is_active,
            "is_default": config.is_default,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
        result.append(ModelConfigResponse(**config_dict))
    
    return result


@router.get("/{config_id}")
def get_model_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """获取单个模型配置详情(不返回 API Key)"""
    config = db.query(ModelConfigModel).filter(ModelConfigModel.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    return {
        "id": config.id,
        "name": config.name,
        "display_name": config.display_name,
        "description": config.description,
        "api_key_masked": mask_api_key(config.api_key),
        "api_base": config.api_base,
        "model_name": config.model_name,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "provider": config.provider,
        "model_type": config.model_type,
        "is_active": config.is_active,
        "is_default": config.is_default,
        "created_at": config.created_at,
        "updated_at": config.updated_at
    }


@router.get("/default/current")
def get_default_model_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """获取当前默认模型配置"""
    config = db.query(ModelConfigModel).filter(
        ModelConfigModel.is_default == True,
        ModelConfigModel.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="未设置默认模型配置")
    
    return {
        "id": config.id,
        "name": config.name,
        "display_name": config.display_name,
        "description": config.description,
        "api_key_masked": mask_api_key(config.api_key),
        "api_base": config.api_base,
        "model_name": config.model_name,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "provider": config.provider,
        "model_type": config.model_type,
        "is_active": config.is_active,
        "is_default": config.is_default
    }


@router.post("/", response_model=ModelConfigResponse)
def create_model_config(
    config: ModelConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """创建新的模型配置"""
    # 检查名称是否已存在
    existing = db.query(ModelConfigModel).filter(
        ModelConfigModel.name == config.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="模型配置名称已存在")
    
    # 如果是第一个配置,自动设为默认
    is_first = db.query(ModelConfigModel).count() == 0

    # 处理 temperature: 如果为空字符串,使用默认值
    temperature = config.temperature
    if not temperature or (isinstance(temperature, str) and not temperature.strip()):
        temperature = "1.0"

    db_config = ModelConfigModel(
        name=config.name,
        display_name=config.display_name,
        description=config.description,
        api_key=config.api_key,
        api_base=config.api_base,
        model_name=config.model_name,
        temperature=temperature,
        max_tokens=config.max_tokens,
        provider=config.provider,
        model_type=config.model_type,
        is_active=config.is_active,
        is_default=is_first
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    # 返回脱敏后的配置
    return ModelConfigResponse(
        id=db_config.id,
        name=db_config.name,
        display_name=db_config.display_name,
        description=db_config.description,
        api_key_masked=mask_api_key(db_config.api_key),
        api_base=db_config.api_base,
        model_name=db_config.model_name,
        temperature=db_config.temperature,
        max_tokens=db_config.max_tokens,
        provider=db_config.provider,
        model_type=db_config.model_type,
        is_active=db_config.is_active,
        is_default=db_config.is_default,
        created_at=db_config.created_at,
        updated_at=db_config.updated_at
    )


@router.put("/{config_id}", response_model=ModelConfigResponse)
def update_model_config(
    config_id: int,
    config: ModelConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新模型配置"""
    db_config = db.query(ModelConfigModel).filter(
        ModelConfigModel.id == config_id
    ).first()

    if not db_config:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    # 更新字段
    update_data = config.model_dump(exclude_unset=True)

    # 处理 api_key: 如果为空或 None,则不更新(保持原有值)
    if 'api_key' in update_data:
        if not update_data['api_key'] or (isinstance(update_data['api_key'], str) and not update_data['api_key'].strip()):
            del update_data['api_key']

    # 处理 temperature: 如果为空字符串,使用默认值
    if 'temperature' in update_data:
        temp = update_data['temperature']
        if not temp or (isinstance(temp, str) and not temp.strip()):
            update_data['temperature'] = "1.0"

    for field, value in update_data.items():
        setattr(db_config, field, value)

    db.commit()
    db.refresh(db_config)
    
    return ModelConfigResponse(
        id=db_config.id,
        name=db_config.name,
        display_name=db_config.display_name,
        description=db_config.description,
        api_key_masked=mask_api_key(db_config.api_key),
        api_base=db_config.api_base,
        model_name=db_config.model_name,
        temperature=db_config.temperature,
        max_tokens=db_config.max_tokens,
        provider=db_config.provider,
        model_type=db_config.model_type,
        is_active=db_config.is_active,
        is_default=db_config.is_default,
        created_at=db_config.created_at,
        updated_at=db_config.updated_at
    )


@router.delete("/{config_id}")
def delete_model_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """删除模型配置"""
    db_config = db.query(ModelConfigModel).filter(
        ModelConfigModel.id == config_id
    ).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    # 不允许删除默认配置
    if db_config.is_default:
        raise HTTPException(
            status_code=400,
            detail="不能删除默认模型配置,请先设置其他模型为默认"
        )
    
    db.delete(db_config)
    db.commit()
    
    return {"message": "模型配置已删除"}


@router.post("/set-default")
def set_default_model(
    request: SetDefaultModelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """设置默认模型"""
    # 检查目标配置是否存在
    target_config = db.query(ModelConfigModel).filter(
        ModelConfigModel.id == request.model_id
    ).first()
    
    if not target_config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    if not target_config.is_active:
        raise HTTPException(status_code=400, detail="不能将未启用的模型设为默认")
    
    # 取消所有其他配置的默认状态
    db.query(ModelConfigModel).update({"is_default": False})
    
    # 设置新的默认配置
    target_config.is_default = True
    
    db.commit()
    
    return {
        "message": "默认模型已更新",
        "model_id": request.model_id,
        "model_name": target_config.model_name
    }

