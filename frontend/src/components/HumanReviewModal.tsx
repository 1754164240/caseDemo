import React, { useState, useEffect } from 'react';
import {
  Modal,
  Table,
  Input,
  Select,
  Alert,
  Tag,
  Space,
  Button,
  Tooltip,
  Badge,
  Typography,
  Switch
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined
} from '@ant-design/icons';

const { Text } = Typography;

interface ValidationError {
  field: string;
  fieldName?: string;
  value?: any;
  type: string;
  message: string;
  suggestion?: string;
  validValues?: string[];
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings?: any[];
  suggestions?: any[];
}

interface BodyItem {
  casezf?: string;
  casedesc: string;
  var: Record<string, any>;
  hoperesult?: string;
  iscaserun?: boolean;
  caseBodySN?: number;
}

interface FieldMetadata {
  fields: Array<{
    row: string;
    rowName: string;
    type: string;
    required?: boolean;
    enums?: Array<{ value: string; label: string }>;
    dependencies?: any[];
  }>;
}

interface WorkflowState {
  generated_body: BodyItem[];
  validation_result: {
    total: number;
    valid_count: number;
    invalid_count: number;
    total_errors: number;
    results: Array<{
      index: number;
      casedesc: string;
      validation: ValidationResult;
    }>;
  };
  field_metadata: FieldMetadata;
}

interface HumanReviewModalProps {
  visible: boolean;
  workflowState: WorkflowState | null;
  onSubmit: (reviewData: {
    review_status: 'approved' | 'modified' | 'rejected';
    corrected_body?: BodyItem[];
    feedback?: string;
  }) => void;
  onCancel: () => void;
  loading?: boolean;
  caseInfo?: {
    name?: string;
    module?: string;
    project?: string;
    sceneType?: string;
    sceneName?: string;
    description?: string;
  };
}

export const HumanReviewModal: React.FC<HumanReviewModalProps> = ({
  visible,
  workflowState,
  onSubmit,
  onCancel,
  loading = false,
  caseInfo
}) => {
  const [editedBody, setEditedBody] = useState<BodyItem[]>([]);
  const [reviewStatus, setReviewStatus] = useState<'approved' | 'modified' | 'rejected'>('approved');
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (workflowState?.generated_body) {
      setEditedBody(JSON.parse(JSON.stringify(workflowState.generated_body)));
      setReviewStatus('approved');
      setHasChanges(false);
    }
  }, [workflowState]);

  // 修改字段值
  const handleFieldChange = (bodyIndex: number, fieldName: string, value: any) => {
    const newBody = [...editedBody];
    if (!newBody[bodyIndex].var) {
      newBody[bodyIndex].var = {};
    }
    newBody[bodyIndex].var[fieldName] = value;
    setEditedBody(newBody);
    setReviewStatus('modified');
    setHasChanges(true);
  };

  // 修改基础字段
  const handleBasicFieldChange = (bodyIndex: number, field: keyof BodyItem, value: any) => {
    const newBody = [...editedBody];
    (newBody[bodyIndex] as any)[field] = value;
    setEditedBody(newBody);
    setReviewStatus('modified');
    setHasChanges(true);
  };

  // 删除一行数据
  const handleDeleteRow = (bodyIndex: number) => {
    const newBody = editedBody.filter((_, idx) => idx !== bodyIndex);
    setEditedBody(newBody);
    setReviewStatus('modified');
    setHasChanges(true);
  };

  const handleSubmit = () => {
    onSubmit({
      review_status: reviewStatus,
      corrected_body: hasChanges ? editedBody : undefined,
      feedback: hasChanges ? '人工修正完成' : '数据无误，直接通过'
    });
  };

  const handleReject = () => {
    Modal.confirm({
      title: '确认拒绝',
      content: '拒绝后将重新生成测试数据，当前修改将丢失。是否继续？',
      onOk: () => {
        onSubmit({
          review_status: 'rejected',
          feedback: '数据不符合要求，请重新生成'
        });
      }
    });
  };

  const findFieldMetadata = (fieldName: string) => {
    // 优先从 field_metadata 查找
    const fromMetadata = workflowState?.field_metadata?.fields?.find(
      (f: any) => f.row === fieldName
    );
    if (fromMetadata) {
      return fromMetadata;
    }

    // 备用：从 header_fields 查找
    const fromHeader = (workflowState as any)?.header_fields?.find(
      (f: any) => f.row === fieldName
    );
    if (fromHeader) {
      return fromHeader;
    }

    return null;
  };

  // 获取所有字段名（用于动态生成列）
  const getAllFieldKeys = (): string[] => {
    const fieldSet = new Set<string>();
    editedBody.forEach(body => {
      if (body.var) {
        Object.keys(body.var).forEach(key => fieldSet.add(key));
      }
    });
    return Array.from(fieldSet);
  };

  // 渲染单元格编辑器
  const renderCellEditor = (
    field: string,
    value: any,
    bodyIndex: number
  ) => {
    const fieldMeta = findFieldMetadata(field);
    const validation = workflowState?.validation_result?.results[bodyIndex]?.validation;
    const error = validation?.errors?.find((e: ValidationError) => e.field === field);

    // 如果有枚举值，使用下拉选择
    if (fieldMeta?.enums && fieldMeta.enums.length > 0) {
      return (
        <Select
          size="small"
          style={{ width: '100%', minWidth: 100 }}
          value={value || undefined}
          onChange={(v) => handleFieldChange(bodyIndex, field, v)}
          placeholder="请选择"
          status={error ? 'error' : undefined}
          showSearch
          optionFilterProp="children"
        >
          {fieldMeta.enums.map((e: any) => (
            <Select.Option key={e.value} value={e.value}>
              {e.label}
            </Select.Option>
          ))}
        </Select>
      );
    }

    // 普通输入框
    return (
      <Input
        size="small"
        value={value || ''}
        onChange={(e) => handleFieldChange(bodyIndex, field, e.target.value)}
        placeholder="请输入"
        status={error ? 'error' : undefined}
        style={{ minWidth: 80 }}
      />
    );
  };

  if (!workflowState) {
    return null;
  }

  const { validation_result } = workflowState;
  const allFieldKeys = getAllFieldKeys();

  // 构建表格列 - 参考截图样式
  const columns: any[] = [
    {
      title: '序号',
      dataIndex: 'index',
      width: 60,
      fixed: 'left',
      render: (_: any, __: any, index: number) => index + 1
    },
    {
      title: '测试角度',
      dataIndex: 'casedesc',
      width: 150,
      render: (value: string, _: any, index: number) => (
        <Input
          size="small"
          value={value || ''}
          onChange={(e) => handleBasicFieldChange(index, 'casedesc', e.target.value)}
          placeholder="测试角度"
        />
      )
    },
    {
      title: '预期结果',
      dataIndex: 'hoperesult',
      width: 150,
      render: (value: string, _: any, index: number) => (
        <Input
          size="small"
          value={value || ''}
          onChange={(e) => handleBasicFieldChange(index, 'hoperesult', e.target.value)}
          placeholder="预期结果"
        />
      )
    },
    {
      title: '正反案例',
      dataIndex: 'casezf',
      width: 100,
      render: (value: string, _: any, index: number) => (
        <Select
          size="small"
          style={{ width: '100%' }}
          value={value || '正'}
          onChange={(v) => handleBasicFieldChange(index, 'casezf', v)}
        >
          <Select.Option value="正">正</Select.Option>
          <Select.Option value="反">反</Select.Option>
        </Select>
      )
    },
    {
      title: '是否运行',
      dataIndex: 'iscaserun',
      width: 80,
      render: (value: boolean, _: any, index: number) => (
        <Switch
          size="small"
          checked={value !== false}
          onChange={(checked) => handleBasicFieldChange(index, 'iscaserun', checked)}
          checkedChildren="是"
          unCheckedChildren="否"
        />
      )
    }
  ];

  // 动态添加字段列
  allFieldKeys.forEach(fieldKey => {
    const fieldMeta = findFieldMetadata(fieldKey);
    columns.push({
      title: (
        <Tooltip title={fieldKey}>
          <span>{fieldMeta?.rowName || fieldKey}</span>
        </Tooltip>
      ),
      dataIndex: ['var', fieldKey],
      width: 120,
      render: (_: any, record: BodyItem, index: number) => {
        const value = record.var?.[fieldKey];
        return renderCellEditor(fieldKey, value, index);
      }
    });
  });

  // 操作列
  columns.push({
    title: '操作',
    width: 80,
    fixed: 'right',
    render: (_: any, __: any, index: number) => (
      <Space>
        <Tooltip title="删除此行">
          <Button
            type="text"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteRow(index)}
          />
        </Tooltip>
      </Space>
    )
  });

  return (
    <Modal
      title={
        <Space>
          <EditOutlined />
          <span>用例明细 - AI 生成的测试数据</span>
          {hasChanges && <Badge status="processing" text="已修改" />}
          <Tag color="blue">{editedBody.length} 条数据</Tag>
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      width="95%"
      style={{ top: 20 }}
      footer={[
        <Button key="reject" danger onClick={handleReject} disabled={loading}>
          拒绝并重新生成
        </Button>,
        <Button key="cancel" onClick={onCancel} disabled={loading}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          onClick={handleSubmit}
          loading={loading}
        >
          确认提交 {hasChanges && '(含修改)'}
        </Button>
      ]}
    >
      {/* 校验汇总 */}
      {validation_result && (
        <Alert
          message={
            <Space>
              <span>数据校验结果:</span>
              <Text strong>{validation_result.total}</Text> 条数据，
              <Text type="success">{validation_result.valid_count} 条通过</Text>
              {validation_result.invalid_count > 0 && (
                <>
                  ，<Text type="danger">{validation_result.invalid_count} 条存在问题</Text>
                </>
              )}
            </Space>
          }
          type={validation_result.invalid_count > 0 ? 'warning' : 'success'}
          style={{ marginBottom: 16 }}
          showIcon
        />
      )}

      {/* 用例基本信息 - 参考截图样式 */}
      <div style={{
        background: '#fafafa',
        padding: '12px 16px',
        borderRadius: 4,
        marginBottom: 16,
        border: '1px solid #f0f0f0'
      }}>
        <Space size={32} wrap>
          <div>
            <Text type="secondary">名称：</Text>
            <Text strong>{caseInfo?.name || workflowState?.name || '自动化用例'}</Text>
          </div>
          <div>
            <Text type="secondary">模块：</Text>
            <Text>{caseInfo?.module || '-'}</Text>
          </div>
          <div>
            <Text type="secondary">项目：</Text>
            <Text>{caseInfo?.project || '-'}</Text>
          </div>
          <div>
            <Text type="secondary">场景类型：</Text>
            <Tag color="blue">{caseInfo?.sceneType || 'API'}</Tag>
          </div>
          <div>
            <Text type="secondary">所属场景：</Text>
            <Text>{caseInfo?.sceneName || '-'}</Text>
          </div>
        </Space>
        {caseInfo?.description && (
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">描述：</Text>
            <Text>{caseInfo.description}</Text>
          </div>
        )}
      </div>

      {/* 用例明细标题 */}
      <div style={{ marginBottom: 8 }}>
        <Text strong style={{ fontSize: 14 }}>用例明细</Text>
      </div>

      {/* 用例明细表格 - 横向展示 */}
      <Table
        dataSource={editedBody}
        columns={columns}
        rowKey={(_, index) => `row-${index}`}
        pagination={false}
        scroll={{ x: 'max-content', y: 'calc(100vh - 400px)' }}
        size="small"
        bordered
        rowClassName={(_, index) => {
          const validation = validation_result?.results[index]?.validation;
          return validation && !validation.valid ? 'row-with-error' : '';
        }}
      />

      <style>{`
        .row-with-error {
          background-color: #fff2f0 !important;
        }
        .row-with-error:hover > td {
          background-color: #ffccc7 !important;
        }
        .ant-table-cell {
          padding: 4px 8px !important;
        }
      `}</style>
    </Modal>
  );
};
