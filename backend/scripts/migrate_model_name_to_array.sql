"""
数据库迁移脚本：model_name字段支持多模型配置

说明：
将 model_configs 表的 model_name 字段从 VARCHAR(200) 改为 TEXT，
并将现有数据从单个字符串转换为JSON数组格式。

执行方式：
1. 在PostgreSQL中手动执行此脚本
2. 或使用 Python 脚本自动执行
"""

-- Step 1: 修改字段类型为TEXT
ALTER TABLE model_configs ALTER COLUMN model_name TYPE TEXT;

-- Step 2: 更新现有数据为JSON数组格式
UPDATE model_configs
SET model_name = CONCAT('["', model_name, '"]')
WHERE model_name NOT LIKE '[%';

-- Step 3: 更新注释
COMMENT ON COLUMN model_configs.model_name IS '模型名称列表(JSON数组格式,如["gpt-4","gpt-3.5-turbo"])';
