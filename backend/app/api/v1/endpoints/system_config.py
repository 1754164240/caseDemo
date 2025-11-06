from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
import os

from app.api.deps import get_db, get_current_active_superuser
from app.models.system_config import SystemConfig
from app.models.user import User
from app.schemas.system_config import (
    SystemConfig as SystemConfigSchema,
    SystemConfigCreate,
    SystemConfigUpdate,
    MilvusConfigUpdate,
    ModelConfigUpdate
)

router = APIRouter()


def get_or_create_config(db: Session, key: str, default_value: str, description: str = None) -> SystemConfig:
    """获取或创建配置项"""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if not config:
        config = SystemConfig(
            config_key=key,
            config_value=default_value,
            description=description
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def update_env_file(key: str, value: str):
    """更新 .env 文件"""
    env_file = ".env"
    if not os.path.exists(env_file):
        return
    
    # 读取现有内容
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新或添加配置
    key_found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        new_lines.append(f"{key}={value}\n")
    
    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


@router.get("/milvus")
def get_milvus_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """获取 Milvus 配置"""
    host_config = get_or_create_config(db, "MILVUS_HOST", "localhost", "Milvus 服务器地址")
    port_config = get_or_create_config(db, "MILVUS_PORT", "19530", "Milvus 服务器端口")
    
    return {
        "host": host_config.config_value,
        "port": int(port_config.config_value)
    }


@router.put("/milvus")
def update_milvus_config(
    config: MilvusConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新 Milvus 配置"""
    # 更新数据库
    host_config = get_or_create_config(db, "MILVUS_HOST", "localhost", "Milvus 服务器地址")
    host_config.config_value = config.host
    
    port_config = get_or_create_config(db, "MILVUS_PORT", "19530", "Milvus 服务器端口")
    port_config.config_value = str(config.port)
    
    db.commit()
    
    # 更新 .env 文件
    update_env_file("MILVUS_HOST", config.host)
    update_env_file("MILVUS_PORT", str(config.port))
    
    return {
        "message": "Milvus 配置更新成功",
        "host": config.host,
        "port": config.port
    }


@router.get("/model")
def get_model_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """获取模型配置"""
    api_key_config = get_or_create_config(db, "OPENAI_API_KEY", "", "OpenAI API Key")
    api_base_config = get_or_create_config(db, "OPENAI_API_BASE", "https://api.openai.com/v1", "OpenAI API Base URL")
    model_name_config = get_or_create_config(db, "MODEL_NAME", "gpt-4", "模型名称")
    
    # 隐藏 API Key 的部分内容
    api_key = api_key_config.config_value
    if api_key and len(api_key) > 8:
        masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    else:
        masked_key = api_key
    
    return {
        "api_key": masked_key,
        "api_key_full": api_key,  # 用于编辑时回显
        "api_base": api_base_config.config_value,
        "model_name": model_name_config.config_value
    }


@router.put("/model")
def update_model_config(
    config: ModelConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新模型配置"""
    # 更新数据库
    api_key_config = get_or_create_config(db, "OPENAI_API_KEY", "", "OpenAI API Key")
    api_key_config.config_value = config.api_key
    
    api_base_config = get_or_create_config(db, "OPENAI_API_BASE", "https://api.openai.com/v1", "OpenAI API Base URL")
    api_base_config.config_value = config.api_base
    
    model_name_config = get_or_create_config(db, "MODEL_NAME", "gpt-4", "模型名称")
    model_name_config.config_value = config.model_name
    
    db.commit()
    
    # 更新 .env 文件
    update_env_file("OPENAI_API_KEY", config.api_key)
    update_env_file("OPENAI_API_BASE", config.api_base)
    update_env_file("MODEL_NAME", config.model_name)
    
    # 更新运行时配置（需要重启才能完全生效）
    from app.core.config import settings
    settings.OPENAI_API_KEY = config.api_key
    settings.OPENAI_API_BASE = config.api_base
    settings.MODEL_NAME = config.model_name
    
    return {
        "message": "模型配置更新成功（部分配置需要重启后端才能完全生效）",
        "api_base": config.api_base,
        "model_name": config.model_name
    }


@router.get("/", response_model=List[SystemConfigSchema])
def list_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """获取所有配置"""
    configs = db.query(SystemConfig).all()
    return configs


@router.post("/", response_model=SystemConfigSchema)
def create_config(
    config: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """创建配置"""
    # 检查是否已存在
    existing = db.query(SystemConfig).filter(SystemConfig.config_key == config.config_key).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置项已存在")
    
    db_config = SystemConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    # 更新 .env 文件
    update_env_file(config.config_key, config.config_value)
    
    return db_config


@router.put("/{config_id}", response_model=SystemConfigSchema)
def update_config(
    config_id: int,
    config: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新配置"""
    db_config = db.query(SystemConfig).filter(SystemConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置项不存在")
    
    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    
    # 更新 .env 文件
    update_env_file(db_config.config_key, db_config.config_value)
    
    return db_config


@router.delete("/{config_id}")
def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """删除配置"""
    db_config = db.query(SystemConfig).filter(SystemConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置项不存在")
    
    db.delete(db_config)
    db.commit()
    
    return {"message": "配置删除成功"}

