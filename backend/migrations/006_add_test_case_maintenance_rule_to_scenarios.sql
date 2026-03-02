-- 添加场景表用例维护规则字段
-- 执行日期: 2026-02-25

ALTER TABLE scenarios
ADD COLUMN IF NOT EXISTS test_case_maintenance_rule TEXT;

COMMENT ON COLUMN scenarios.test_case_maintenance_rule IS '用例维护规则';

SELECT '场景表已添加 test_case_maintenance_rule 字段' AS status;
