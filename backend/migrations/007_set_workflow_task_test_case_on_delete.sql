-- 将工作流任务到测试用例的外键改为删除用例时置空
-- 执行日期: 2026-04-28

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'workflow_tasks'
    ) THEN
        ALTER TABLE workflow_tasks
        DROP CONSTRAINT IF EXISTS workflow_tasks_test_case_id_fkey;

        ALTER TABLE workflow_tasks
        ADD CONSTRAINT workflow_tasks_test_case_id_fkey
        FOREIGN KEY (test_case_id)
        REFERENCES test_cases(id)
        ON DELETE SET NULL;
    END IF;
END $$;

SELECT 'workflow_tasks.test_case_id 外键已设置为 ON DELETE SET NULL' AS status;
