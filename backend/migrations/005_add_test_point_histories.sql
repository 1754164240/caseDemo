-- 娣诲姞娴嬭瘯鐐圭増鏈敤鍘嗙被琛?
-- 鎵ц鏃ユ湡: 2025-11-13

CREATE TABLE IF NOT EXISTS test_point_histories (
    id SERIAL PRIMARY KEY,
    test_point_id INTEGER NOT NULL REFERENCES test_points(id) ON DELETE CASCADE,
    requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    code VARCHAR(20),
    title VARCHAR(200),
    description TEXT,
    category VARCHAR(100),
    priority VARCHAR(20),
    business_line VARCHAR(50),
    prompt_summary TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    operator_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_test_point_histories_version
    ON test_point_histories(test_point_id, version);

CREATE INDEX IF NOT EXISTS ix_test_point_histories_requirement
    ON test_point_histories(requirement_id);

CREATE INDEX IF NOT EXISTS ix_test_point_histories_status
    ON test_point_histories(status);

CREATE INDEX IF NOT EXISTS ix_test_point_histories_requirement_version
    ON test_point_histories(requirement_id, version);

COMMENT ON TABLE test_point_histories IS 'Version history snapshots for regenerated test points';
COMMENT ON COLUMN test_point_histories.version IS 'Version label per test point (v001, v002, ...)';
COMMENT ON COLUMN test_point_histories.prompt_summary IS 'Prompt/business context summary used for regeneration';
COMMENT ON COLUMN test_point_histories.status IS 'Workflow status (pending/approved/rejected)'
;

SELECT 'test_point_histories 琛ㄥ凡澧炲姞鎴愬姛' AS info;
