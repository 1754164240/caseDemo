-- 添加业务线字段到测试点表
-- 执行日期: 2025-01-10

-- 1. 添加 business_line 字段到 test_points 表
ALTER TABLE test_points ADD COLUMN IF NOT EXISTS business_line VARCHAR(50);

-- 2. 添加注释
COMMENT ON COLUMN test_points.business_line IS '业务线：contract(契约)/preservation(保全)/claim(理赔)';

-- 验证迁移结果
SELECT '业务线字段已添加' as status;

-- 查看表结构
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'test_points' AND column_name = 'business_line';

