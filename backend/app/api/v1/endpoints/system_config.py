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
    ModelConfigUpdate,
    EmbeddingConfigUpdate,
    PromptConfigUpdate
)

router = APIRouter()


# 默认 Prompt 模板
DEFAULT_TEST_POINT_PROMPT = """你是一个专业的保险行业测试专家。请从需求文档中识别所有测试点。

测试点应该包括：
1. 功能性测试点
2. 边界条件测试点
3. 异常情况测试点
4. 业务规则验证点

请以JSON格式返回测试点列表，每个测试点包含：
- title: 测试点标题
- description: 详细描述
- category: 分类（功能/边界/异常/业务规则）
- priority: 优先级（high/medium/low）

返回格式示例：
[
  {{"title": "测试点1", "description": "描述1", "category": "功能", "priority": "high"}},
  {{"title": "测试点2", "description": "描述2", "category": "边界", "priority": "medium"}}
]

{feedback_instruction}"""

DEFAULT_TEST_CASE_PROMPT = """你是一个专业的测试用例设计专家。请根据测试点生成详细的测试用例。

测试用例应该包含：
- title: 用例标题
- description: 用例描述
- preconditions: 前置条件
- test_steps: 测试步骤（数组格式，每步包含 step, action, expected）
- expected_result: 预期结果
- priority: 优先级
- test_type: 测试类型

请以JSON格式返回测试用例列表。"""

# 契约业务线测试用例 Prompt
DEFAULT_CONTRACT_TEST_CASE_PROMPT = """你是一个专业的保险契约业务测试专家。请根据测试点生成详细的契约业务测试用例。

契约业务特点：
- 关注投保流程、保单生成、保费计算
- 重点验证保险条款、责任范围、除外责任
- 注意核保规则、风险评估、保单承保

测试用例应该包含：
- title: 用例标题
- description: 用例描述
- preconditions: 前置条件（如：客户信息、产品配置）
- test_steps: 测试步骤（数组格式，每步包含 step, action, expected）
- expected_result: 预期结果
- priority: 优先级
- test_type: 测试类型

请以JSON格式返回测试用例列表。"""

# 保全业务线测试用例 Prompt
DEFAULT_PRESERVATION_TEST_CASE_PROMPT = """你是一个专业的保险保全业务测试专家。请根据测试点生成详细的保全业务测试用例。

保全业务特点：
- 关注保单变更、批改、续保流程
- 重点验证保单信息修改、受益人变更、保额调整
- 注意保全规则、生效时间、费用计算

测试用例应该包含：
- title: 用例标题
- description: 用例描述
- preconditions: 前置条件（如：有效保单、变更申请）
- test_steps: 测试步骤（数组格式，每步包含 step, action, expected）
- expected_result: 预期结果
- priority: 优先级
- test_type: 测试类型

请以JSON格式返回测试用例列表。"""

# 理赔业务线测试用例 Prompt
DEFAULT_CLAIM_TEST_CASE_PROMPT = """你是一个专业的保险理赔业务测试专家。请根据测试点生成详细的理赔业务测试用例。

理赔业务特点：
- 关注理赔申请、审核、支付流程
- 重点验证理赔条件、责任认定、赔付金额计算
- 注意理赔时效、材料审核、反欺诈检查

测试用例应该包含：
- title: 用例标题
- description: 用例描述
- preconditions: 前置条件（如：出险事故、理赔材料）
- test_steps: 测试步骤（数组格式，每步包含 step, action, expected）
- expected_result: 预期结果
- priority: 优先级
- test_type: 测试类型

请以JSON格式返回测试用例列表。"""


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
    uri_config = get_or_create_config(db, "MILVUS_URI", "http://localhost:19530", "Milvus 地址")
    user_config = get_or_create_config(db, "MILVUS_USER", "", "Milvus 用户名")
    password_config = get_or_create_config(db, "MILVUS_PASSWORD", "", "Milvus 密码")
    token_config = get_or_create_config(db, "MILVUS_TOKEN", "", "Milvus Token")
    db_name_config = get_or_create_config(db, "MILVUS_DB_NAME", "default", "Milvus 数据库名称")
    collection_config = get_or_create_config(db, "MILVUS_COLLECTION_NAME", "test_cases", "Milvus Collection 名称")

    # 隐藏密码的部分内容
    password = password_config.config_value
    if password and len(password) > 4:
        masked_password = password[:2] + "*" * (len(password) - 4) + password[-2:]
    else:
        masked_password = password

    # 隐藏 token 的部分内容
    token = token_config.config_value
    if token and len(token) > 8:
        masked_token = token[:4] + "*" * (len(token) - 8) + token[-4:]
    else:
        masked_token = token

    return {
        "uri": uri_config.config_value,
        "user": user_config.config_value,
        "password": masked_password,
        "password_full": password,  # 用于编辑时回显
        "token": masked_token,
        "token_full": token,  # 用于编辑时回显
        "db_name": db_name_config.config_value,
        "collection_name": collection_config.config_value
    }


@router.put("/milvus")
def update_milvus_config(
    config: MilvusConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新 Milvus 配置"""
    # 更新数据库
    uri_config = get_or_create_config(db, "MILVUS_URI", "http://localhost:19530", "Milvus 地址")
    uri_config.config_value = config.uri

    user_config = get_or_create_config(db, "MILVUS_USER", "", "Milvus 用户名")
    user_config.config_value = config.user

    password_config = get_or_create_config(db, "MILVUS_PASSWORD", "", "Milvus 密码")
    password_config.config_value = config.password

    token_config = get_or_create_config(db, "MILVUS_TOKEN", "", "Milvus Token")
    token_config.config_value = config.token

    db_name_config = get_or_create_config(db, "MILVUS_DB_NAME", "default", "Milvus 数据库名称")
    db_name_config.config_value = config.db_name

    collection_config = get_or_create_config(db, "MILVUS_COLLECTION_NAME", "test_cases", "Milvus Collection 名称")
    collection_config.config_value = config.collection_name

    db.commit()

    # 更新 .env 文件
    update_env_file("MILVUS_URI", config.uri)
    update_env_file("MILVUS_USER", config.user)
    update_env_file("MILVUS_PASSWORD", config.password)
    update_env_file("MILVUS_TOKEN", config.token)
    update_env_file("MILVUS_DB_NAME", config.db_name)
    update_env_file("MILVUS_COLLECTION_NAME", config.collection_name)

    # 更新运行时配置
    from app.core.config import settings
    settings.MILVUS_URI = config.uri
    settings.MILVUS_USER = config.user
    settings.MILVUS_PASSWORD = config.password
    settings.MILVUS_TOKEN = config.token
    settings.MILVUS_DB_NAME = config.db_name
    settings.MILVUS_COLLECTION_NAME = config.collection_name

    return {
        "message": "Milvus 配置更新成功（建议重启后端以完全生效）",
        "uri": config.uri,
        "user": config.user,
        "db_name": config.db_name,
        "collection_name": config.collection_name
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


@router.get("/embedding")
def get_embedding_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """获取 Embedding 模型配置"""
    embedding_model_config = get_or_create_config(db, "EMBEDDING_MODEL", "text-embedding-ada-002", "Embedding 模型名称")
    embedding_api_key_config = get_or_create_config(db, "EMBEDDING_API_KEY", "", "Embedding API Key (为空时使用 LLM 的 API Key)")
    embedding_api_base_config = get_or_create_config(db, "EMBEDDING_API_BASE", "", "Embedding API Base URL (为空时使用 LLM 的 API Base)")

    # 隐藏 API Key 的部分内容
    api_key = embedding_api_key_config.config_value
    if api_key and len(api_key) > 8:
        masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    else:
        masked_key = api_key

    return {
        "embedding_model": embedding_model_config.config_value,
        "embedding_api_key": masked_key,
        "embedding_api_key_full": api_key,  # 用于编辑时回显
        "embedding_api_base": embedding_api_base_config.config_value
    }


@router.put("/embedding")
def update_embedding_config(
    config: EmbeddingConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新 Embedding 模型配置"""
    # 更新数据库
    embedding_model_config = get_or_create_config(db, "EMBEDDING_MODEL", "text-embedding-ada-002", "Embedding 模型名称")
    embedding_model_config.config_value = config.embedding_model

    embedding_api_key_config = get_or_create_config(db, "EMBEDDING_API_KEY", "", "Embedding API Key (为空时使用 LLM 的 API Key)")
    embedding_api_key_config.config_value = config.embedding_api_key

    embedding_api_base_config = get_or_create_config(db, "EMBEDDING_API_BASE", "", "Embedding API Base URL (为空时使用 LLM 的 API Base)")
    embedding_api_base_config.config_value = config.embedding_api_base

    db.commit()

    # 更新 .env 文件
    update_env_file("EMBEDDING_MODEL", config.embedding_model)
    update_env_file("EMBEDDING_API_KEY", config.embedding_api_key)
    update_env_file("EMBEDDING_API_BASE", config.embedding_api_base)

    # 更新运行时配置（需要重启才能完全生效）
    from app.core.config import settings
    settings.EMBEDDING_MODEL = config.embedding_model
    settings.EMBEDDING_API_KEY = config.embedding_api_key
    settings.EMBEDDING_API_BASE = config.embedding_api_base

    return {
        "message": "Embedding 模型配置更新成功（部分配置需要重启后端才能完全生效）",
        "embedding_model": config.embedding_model,
        "embedding_api_base": config.embedding_api_base
    }


@router.get("/prompts")
def get_prompt_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """获取 Prompt 配置"""
    test_point_prompt_config = get_or_create_config(
        db,
        "TEST_POINT_PROMPT",
        DEFAULT_TEST_POINT_PROMPT,
        "测试点生成 Prompt"
    )
    test_case_prompt_config = get_or_create_config(
        db,
        "TEST_CASE_PROMPT",
        DEFAULT_TEST_CASE_PROMPT,
        "测试用例生成 Prompt"
    )
    contract_test_case_prompt_config = get_or_create_config(
        db,
        "CONTRACT_TEST_CASE_PROMPT",
        DEFAULT_CONTRACT_TEST_CASE_PROMPT,
        "契约业务线测试用例生成 Prompt"
    )
    preservation_test_case_prompt_config = get_or_create_config(
        db,
        "PRESERVATION_TEST_CASE_PROMPT",
        DEFAULT_PRESERVATION_TEST_CASE_PROMPT,
        "保全业务线测试用例生成 Prompt"
    )
    claim_test_case_prompt_config = get_or_create_config(
        db,
        "CLAIM_TEST_CASE_PROMPT",
        DEFAULT_CLAIM_TEST_CASE_PROMPT,
        "理赔业务线测试用例生成 Prompt"
    )

    return {
        "test_point_prompt": test_point_prompt_config.config_value,
        "test_case_prompt": test_case_prompt_config.config_value,
        "contract_test_case_prompt": contract_test_case_prompt_config.config_value,
        "preservation_test_case_prompt": preservation_test_case_prompt_config.config_value,
        "claim_test_case_prompt": claim_test_case_prompt_config.config_value
    }


@router.put("/prompts")
def update_prompt_config(
    config: PromptConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新 Prompt 配置"""
    # 更新数据库
    test_point_prompt_config = get_or_create_config(
        db,
        "TEST_POINT_PROMPT",
        DEFAULT_TEST_POINT_PROMPT,
        "测试点生成 Prompt"
    )
    test_point_prompt_config.config_value = config.test_point_prompt

    test_case_prompt_config = get_or_create_config(
        db,
        "TEST_CASE_PROMPT",
        DEFAULT_TEST_CASE_PROMPT,
        "测试用例生成 Prompt"
    )
    test_case_prompt_config.config_value = config.test_case_prompt

    contract_test_case_prompt_config = get_or_create_config(
        db,
        "CONTRACT_TEST_CASE_PROMPT",
        DEFAULT_CONTRACT_TEST_CASE_PROMPT,
        "契约业务线测试用例生成 Prompt"
    )
    contract_test_case_prompt_config.config_value = config.contract_test_case_prompt

    preservation_test_case_prompt_config = get_or_create_config(
        db,
        "PRESERVATION_TEST_CASE_PROMPT",
        DEFAULT_PRESERVATION_TEST_CASE_PROMPT,
        "保全业务线测试用例生成 Prompt"
    )
    preservation_test_case_prompt_config.config_value = config.preservation_test_case_prompt

    claim_test_case_prompt_config = get_or_create_config(
        db,
        "CLAIM_TEST_CASE_PROMPT",
        DEFAULT_CLAIM_TEST_CASE_PROMPT,
        "理赔业务线测试用例生成 Prompt"
    )
    claim_test_case_prompt_config.config_value = config.claim_test_case_prompt

    db.commit()

    return {
        "message": "Prompt 配置更新成功",
        "test_point_prompt": config.test_point_prompt,
        "test_case_prompt": config.test_case_prompt,
        "contract_test_case_prompt": config.contract_test_case_prompt,
        "preservation_test_case_prompt": config.preservation_test_case_prompt,
        "claim_test_case_prompt": config.claim_test_case_prompt
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

