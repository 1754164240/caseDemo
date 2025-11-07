-- 添加审批相关字段到测试点和测试用例表

-- 1. 为测试点表添加审批字段
ALTER TABLE test_points 
  ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(id),
  ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS approval_comment TEXT;

-- 更新现有数据：将 is_approved=true 的记录设置为 approved 状态
UPDATE test_points 
SET approval_status = CASE 
  WHEN is_approved = true THEN 'approved'
  ELSE 'pending'
END
WHERE approval_status IS NULL OR approval_status = 'pending';

-- 2. 为测试用例表添加审批字段
ALTER TABLE test_cases 
  ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(id),
  ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS approval_comment TEXT;

-- 3. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_test_points_approval_status ON test_points(approval_status);
CREATE INDEX IF NOT EXISTS idx_test_cases_approval_status ON test_cases(approval_status);
CREATE INDEX IF NOT EXISTS idx_test_points_approved_by ON test_points(approved_by);
CREATE INDEX IF NOT EXISTS idx_test_cases_approved_by ON test_cases(approved_by);

-- 4. 添加注释
COMMENT ON COLUMN test_points.approval_status IS '审批状态: pending-待审批, approved-已通过, rejected-已拒绝';
COMMENT ON COLUMN test_points.approved_by IS '审批人ID';
COMMENT ON COLUMN test_points.approved_at IS '审批时间';
COMMENT ON COLUMN test_points.approval_comment IS '审批意见';

COMMENT ON COLUMN test_cases.approval_status IS '审批状态: pending-待审批, approved-已通过, rejected-已拒绝';
COMMENT ON COLUMN test_cases.approved_by IS '审批人ID';
COMMENT ON COLUMN test_cases.approved_at IS '审批时间';
COMMENT ON COLUMN test_cases.approval_comment IS '审批意见';

