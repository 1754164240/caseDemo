-- 添加测试点和测试用例编号字段
-- 执行日期: 2025-01-07

-- 1. 添加 code 字段到 test_points 表
ALTER TABLE test_points ADD COLUMN IF NOT EXISTS code VARCHAR(20);

-- 2. 添加 code 字段到 test_cases 表
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS code VARCHAR(30);

-- 3. 为现有测试点生成编号
DO $$
DECLARE
    tp_record RECORD;
    counter INTEGER := 1;
BEGIN
    FOR tp_record IN 
        SELECT id FROM test_points WHERE code IS NULL ORDER BY id
    LOOP
        UPDATE test_points 
        SET code = 'TP-' || LPAD(counter::TEXT, 3, '0')
        WHERE id = tp_record.id;
        counter := counter + 1;
    END LOOP;
END $$;

-- 4. 为现有测试用例生成编号
DO $$
DECLARE
    tc_record RECORD;
    tp_code VARCHAR(20);
    tp_counter INTEGER;
BEGIN
    FOR tc_record IN 
        SELECT tc.id, tc.test_point_id, tp.code as test_point_code
        FROM test_cases tc
        JOIN test_points tp ON tc.test_point_id = tp.id
        WHERE tc.code IS NULL
        ORDER BY tc.test_point_id, tc.id
    LOOP
        -- 获取该测试点下已有的测试用例数量（包括已有编号的）
        SELECT COUNT(*) INTO tp_counter
        FROM test_cases
        WHERE test_point_id = tc_record.test_point_id
        AND id <= tc_record.id;
        
        -- 更新编号
        UPDATE test_cases
        SET code = tc_record.test_point_code || '-' || tp_counter
        WHERE id = tc_record.id;
    END LOOP;
END $$;

-- 5. 创建唯一索引（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'ix_test_points_code'
    ) THEN
        CREATE UNIQUE INDEX ix_test_points_code ON test_points(code);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'ix_test_cases_code'
    ) THEN
        CREATE UNIQUE INDEX ix_test_cases_code ON test_cases(code);
    END IF;
END $$;

-- 6. 设置字段为非空（如果所有记录都有值）
DO $$
BEGIN
    -- 检查是否所有测试点都有编号
    IF NOT EXISTS (SELECT 1 FROM test_points WHERE code IS NULL) THEN
        ALTER TABLE test_points ALTER COLUMN code SET NOT NULL;
    END IF;
    
    -- 检查是否所有测试用例都有编号
    IF NOT EXISTS (SELECT 1 FROM test_cases WHERE code IS NULL) THEN
        ALTER TABLE test_cases ALTER COLUMN code SET NOT NULL;
    END IF;
END $$;

-- 验证迁移结果
SELECT '测试点编号示例:' as info;
SELECT id, code, title FROM test_points ORDER BY code LIMIT 5;

SELECT '测试用例编号示例:' as info;
SELECT id, code, title FROM test_cases ORDER BY code LIMIT 5;

SELECT '迁移完成!' as status;

