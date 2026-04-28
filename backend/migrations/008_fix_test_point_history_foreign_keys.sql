-- 修复测试点历史表外键，删除需求或测试点时自动清理历史记录
-- 执行日期: 2026-04-28

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'test_point_histories'
    ) THEN
        ALTER TABLE test_point_histories
        DROP CONSTRAINT IF EXISTS test_point_histories_test_point_id_fkey;

        ALTER TABLE test_point_histories
        ADD CONSTRAINT test_point_histories_test_point_id_fkey
        FOREIGN KEY (test_point_id)
        REFERENCES test_points(id)
        ON DELETE CASCADE;

        ALTER TABLE test_point_histories
        DROP CONSTRAINT IF EXISTS test_point_histories_requirement_id_fkey;

        ALTER TABLE test_point_histories
        ADD CONSTRAINT test_point_histories_requirement_id_fkey
        FOREIGN KEY (requirement_id)
        REFERENCES requirements(id)
        ON DELETE CASCADE;
    END IF;
END $$;

SELECT 'test_point_histories 外键已设置为 ON DELETE CASCADE' AS status;
