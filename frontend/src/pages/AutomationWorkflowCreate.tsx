import React, { useState, useEffect } from 'react';
import {
  Button,
  Card,
  message,
  Space,
  Typography,
  Steps,
  Spin,
  Result,
  Table,
  Divider
} from 'antd';
import {
  RocketOutlined,
  CheckCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { HumanReviewModal } from '../components/HumanReviewModal';
import api from '../services/api';
import { testCasesAPI } from '../services/api';

const { Title, Text } = Typography;

interface WorkflowState {
  thread_id: string;
  status: string;
  current_step: string;
  need_human_review: boolean;
  state: any;
}

interface TestCase {
  id: number;
  code: string;
  title: string;
  description: string;
  test_type: string;
  priority: string;
  preconditions: string;
  test_steps: string;
  expected_result: string;
}

export const AutomationWorkflowCreate: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [threadId, setThreadId] = useState<string>('');
  const [currentStatus, setCurrentStatus] = useState<string>('');
  const [finalResult, setFinalResult] = useState<any>(null);

  // 测试用例选择相关状态
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [selectedTestCase, setSelectedTestCase] = useState<TestCase | null>(null);
  const [loadingTestCases, setLoadingTestCases] = useState(false);

  // 加载测试用例列表
  useEffect(() => {
    loadTestCases();
  }, []);

  const loadTestCases = async () => {
    setLoadingTestCases(true);
    try {
      const response = await testCasesAPI.list({ limit: 100 });
      const data = response.data?.items || response.data || [];
      console.log('加载到的测试用例:', data);
      setTestCases(data);
    } catch (error: any) {
      console.error('加载测试用例失败:', error);
      message.error(`加载测试用例列表失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoadingTestCases(false);
    }
  };

  // 选择测试用例
  const handleSelectTestCase = (testCase: TestCase) => {
    console.log('选择的测试用例:', testCase);
    setSelectedTestCase(testCase);
  };

  const handleSubmit = async () => {
    if (!selectedTestCase) {
      message.error('请先选择一个测试用例');
      return;
    }

    setLoading(true);
    setCurrentStatus('processing');

    try {
      // 启动工作流（同步执行，会在 human_review 节点暂停）
      const response = await api.post('/automation/workflow/start', {
        test_case_id: selectedTestCase.id,
        scenario_type: 'API'
      });

      const data = response.data;
      console.log('工作流响应:', data);

      setThreadId(data.thread_id);

      // 检查工作流状态
      if (data.need_human_review || data.status === 'reviewing') {
        // 工作流在人工审核节点暂停
        setCurrentStatus('reviewing');
        setWorkflowState(data);
        setReviewModalVisible(true);
        message.info('AI 已生成测试数据，请进行人工审核');
      } else if (data.status === 'completed') {
        // 直接完成（不需要审核的情况）
        setCurrentStatus('completed');
        setFinalResult(data.state);
        message.success('自动化用例创建成功！');
      } else if (data.status === 'failed') {
        // 执行失败
        setCurrentStatus('failed');
        setFinalResult(data.state);
        message.error(`工作流执行失败: ${data.state?.error || '未知错误'}`);
      }
    } catch (error: any) {
      console.error('启动工作流失败:', error);
      message.error(`启动失败: ${error.response?.data?.detail || error.message || '未知错误'}`);
      setCurrentStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewComplete = async (reviewData: any) => {
    setLoading(true);

    try {
      // 提交审核结果，继续执行工作流
      const response = await api.post(
        `/automation/workflow/${threadId}/review`,
        reviewData
      );

      const data = response.data;
      console.log('审核提交响应:', data);

      if (data.status === 'completed') {
        setCurrentStatus('completed');
        setFinalResult(data);
        setReviewModalVisible(false);
        message.success('自动化用例创建成功！');
      } else if (data.status === 'failed') {
        setCurrentStatus('failed');
        setFinalResult(data);
        message.error(`创建失败: ${data.error || '未知错误'}`);
      } else if (data.status === 'reviewing') {
        // 拒绝后重新生成，再次需要审核
        message.info('AI 已重新生成数据，请再次审核');
        // 重新获取状态
        const stateRes = await api.get(`/automation/workflow/${threadId}/state`);
        setWorkflowState(stateRes.data);
      } else {
        message.info(`工作流状态: ${data.status}`);
      }
    } catch (error: any) {
      console.error('提交审核失败:', error);
      message.error(`提交失败: ${error.response?.data?.detail || error.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setWorkflowState(null);
    setThreadId('');
    setCurrentStatus('');
    setFinalResult(null);
    setReviewModalVisible(false);
    setSelectedTestCase(null);
  };

  const getStepStatus = () => {
    if (currentStatus === 'completed') return 2;
    if (currentStatus === 'reviewing') return 1;
    if (currentStatus === 'failed') return -1;
    if (loading || currentStatus === 'processing') return 0;
    return -1;
  };

  const stepStatus = getStepStatus();

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Title level={3}>
          <RocketOutlined /> 创建自动化用例（LangGraph 智能工作流）
        </Title>
        <Text type="secondary">
          选择测试用例后，AI 将自动匹配场景、智能生成测试数据，支持人工审核和修正
        </Text>

        {/* 操作按钮区域 */}
        {!currentStatus && (
          <div style={{ marginTop: 24, marginBottom: 16 }}>
            <Space size="large">
              <Button
                type="primary"
                onClick={handleSubmit}
                loading={loading}
                icon={<RocketOutlined />}
                size="large"
                disabled={!selectedTestCase}
              >
                启动智能工作流
              </Button>
              <Button
                onClick={handleReset}
                disabled={loading}
                size="large"
              >
                重置
              </Button>
              {selectedTestCase && (
                <Text type="secondary">
                  已选择: <Text strong>{selectedTestCase.title}</Text>
                </Text>
              )}
            </Space>
          </div>
        )}

        {/* 流程步骤 */}
        {currentStatus && (
          <div style={{ margin: '24px 0' }}>
            <Steps
              current={stepStatus >= 0 ? stepStatus : 0}
              status={stepStatus === -1 ? 'error' : undefined}
              items={[
                {
                  title: '启动工作流',
                  description: 'AI 加载用例、匹配场景、生成数据',
                  icon: (loading && stepStatus === 0) ? <LoadingOutlined /> : undefined
                },
                {
                  title: '人工审核',
                  description: '检查并修正数据',
                  icon: currentStatus === 'reviewing' ? <LoadingOutlined /> : undefined
                },
                {
                  title: '创建用例',
                  description: '提交到自动化平台',
                  icon: currentStatus === 'completed' ? <CheckCircleOutlined /> : undefined
                }
              ]}
            />
          </div>
        )}

        {/* 成功结果 */}
        {currentStatus === 'completed' && finalResult && (
          <Result
            status="success"
            title="自动化用例创建成功！"
            subTitle={
              <Space direction="vertical">
                <Text>用例 ID: {finalResult.new_usercase_id}</Text>
                <Text>用例名称: {finalResult.created_case?.name || finalResult.name}</Text>
              </Space>
            }
            extra={[
              <Button type="primary" key="new" onClick={handleReset}>
                创建新用例
              </Button>,
              <Button key="view" onClick={() => {
                message.info('用例已创建在自动化测试平台中');
                console.log('用例详情:', finalResult);
              }}>
                查看详情
              </Button>
            ]}
          />
        )}

        {/* 失败结果 */}
        {currentStatus === 'failed' && (
          <Result
            status="error"
            title="工作流执行失败"
            subTitle={workflowState?.state?.error || '未知错误'}
            extra={[
              <Button type="primary" key="retry" onClick={handleReset}>
                重新创建
              </Button>
            ]}
          />
        )}

        {/* 测试用例选择表格 */}
        {!currentStatus && (
          <>
            <Divider>选择测试用例</Divider>
            <Table
              loading={loadingTestCases}
              dataSource={testCases}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              rowClassName={(record) =>
                selectedTestCase?.id === record.id ? 'selected-row' : ''
              }
              onRow={(record) => ({
                onClick: () => handleSelectTestCase(record),
                style: { cursor: 'pointer' }
              })}
              columns={[
                {
                  title: '用例编号',
                  dataIndex: 'code',
                  width: 150
                },
                {
                  title: '标题',
                  dataIndex: 'title',
                  ellipsis: true
                },
                {
                  title: '描述',
                  dataIndex: 'description',
                  ellipsis: true,
                  width: 200
                },
                {
                  title: '测试类型',
                  dataIndex: 'test_type',
                  width: 120
                },
                {
                  title: '优先级',
                  dataIndex: 'priority',
                  width: 100
                },
                {
                  title: '操作',
                  width: 120,
                  render: (_: any, record: TestCase) => (
                    <Button
                      type={selectedTestCase?.id === record.id ? 'primary' : 'default'}
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectTestCase(record);
                      }}
                    >
                      {selectedTestCase?.id === record.id ? '已选择' : '选择'}
                    </Button>
                  )
                }
              ]}
            />
          </>
        )}
      </Card>

      {/* 人工审核弹窗 */}
      {workflowState && (
        <HumanReviewModal
          visible={reviewModalVisible}
          workflowState={workflowState.state}
          onSubmit={handleReviewComplete}
          onCancel={() => setReviewModalVisible(false)}
          loading={loading}
          caseInfo={{
            name: workflowState.state?.name || selectedTestCase?.title,
            module: workflowState.state?.module_id,
            project: '新一代核心项目',
            sceneType: workflowState.state?.scenario_type || 'API',
            sceneName: workflowState.state?.matched_scenario?.name || workflowState.state?.scene_id,
            description: workflowState.state?.description || selectedTestCase?.description
          }}
        />
      )}
    </div>
  );
};
