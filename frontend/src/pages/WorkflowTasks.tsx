import { useState, useEffect } from 'react'
import { Table, Tag, Button, Space, Modal, Progress, message, Tooltip, Select } from 'antd'
import {
  ReloadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  EditOutlined
} from '@ant-design/icons'
import { workflowTasksAPI } from '../services/api'
import { HumanReviewModal } from '../components/HumanReviewModal'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

interface WorkflowTask {
  id: number
  thread_id: string
  task_type: string
  status: string
  current_step: string
  progress: number
  need_review: boolean
  test_case_id: number
  new_usercase_id: string | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  input_params: any
  result_data: any
  interrupt_data: any
}

export default function WorkflowTasks() {
  const [tasks, setTasks] = useState<WorkflowTask[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedTask, setSelectedTask] = useState<WorkflowTask | null>(null)
  const [reviewModalVisible, setReviewModalVisible] = useState(false)
  const [reviewLoading, setReviewLoading] = useState(false)

  // 轮询刷新（每5秒）
  useEffect(() => {
    fetchTasks()
    const timer = setInterval(() => {
      fetchTasks(false) // 静默刷新，不显示 loading
    }, 5000)
    return () => clearInterval(timer)
  }, [currentPage, pageSize, statusFilter])

  const fetchTasks = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true)
      const { data } = await workflowTasksAPI.listTasks({
        status: statusFilter as any,
        limit: pageSize,
        offset: (currentPage - 1) * pageSize
      })
      setTasks(data.items)
      setTotal(data.total)
    } catch (error: any) {
      if (showLoading) {
        message.error('加载任务列表失败: ' + (error.response?.data?.detail || error.message))
      }
    } finally {
      if (showLoading) setLoading(false)
    }
  }

  const handleViewDetail = async (task: WorkflowTask) => {
    try {
      // 获取最新状态
      const { data } = await workflowTasksAPI.getTask(task.id)
      setSelectedTask(data)
      setDetailModalVisible(true)
    } catch (error: any) {
      message.error('获取任务详情失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleReview = (task: WorkflowTask) => {
    // 打开审核模态框
    console.log('[DEBUG] 审核任务数据:', task)
    console.log('[DEBUG] interrupt_data:', task.interrupt_data)
    if (task.interrupt_data) {
      console.log('[DEBUG] generated_body 数量:', task.interrupt_data.generated_body?.length)
      console.log('[DEBUG] field_metadata:', task.interrupt_data.field_metadata)
    }
    setSelectedTask(task)
    setReviewModalVisible(true)
  }

  const handleReviewSubmit = async (reviewData: {
    review_status: 'approved' | 'modified' | 'rejected'
    corrected_body?: any[]
    feedback?: string
  }) => {
    if (!selectedTask) return

    try {
      setReviewLoading(true)
      await workflowTasksAPI.submitReview(selectedTask.thread_id, reviewData)

      message.success('审核提交成功！工作流将继续执行...')
      setReviewModalVisible(false)
      setSelectedTask(null)

      // 刷新任务列表
      fetchTasks()
    } catch (error: any) {
      message.error('提交审核失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setReviewLoading(false)
    }
  }

  const getStatusTag = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: any; text: string }> = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待执行' },
      processing: { color: 'processing', icon: <SyncOutlined spin />, text: '执行中' },
      reviewing: { color: 'warning', icon: <ExclamationCircleOutlined />, text: '等待审核' },
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' }
    }
    const config = statusConfig[status] || statusConfig.pending
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    )
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => getStatusTag(status)
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record: WorkflowTask) => (
        <Progress
          percent={progress}
          size="small"
          status={
            record.status === 'failed' ? 'exception' :
            record.status === 'completed' ? 'success' :
            'active'
          }
        />
      )
    },
    {
      title: '当前步骤',
      dataIndex: 'current_step',
      key: 'current_step',
      width: 150,
      ellipsis: true,
      render: (step: string) => (
        <Tooltip title={step}>
          <span>{step}</span>
        </Tooltip>
      )
    },
    {
      title: '测试用例ID',
      dataIndex: 'test_case_id',
      key: 'test_case_id',
      width: 100
    },
    {
      title: '创建的用例ID',
      dataIndex: 'new_usercase_id',
      key: 'new_usercase_id',
      width: 120,
      render: (id: string | null) => id || '-'
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => (
        <Tooltip title={dayjs(time).format('YYYY-MM-DD HH:mm:ss')}>
          <span>{dayjs(time).fromNow()}</span>
        </Tooltip>
      )
    },
    {
      title: '耗时',
      key: 'duration',
      width: 100,
      render: (record: WorkflowTask) => {
        if (!record.started_at) return '-'
        const end = record.completed_at ? dayjs(record.completed_at) : dayjs()
        const duration = end.diff(dayjs(record.started_at), 'second')
        if (duration < 60) return `${duration}秒`
        if (duration < 3600) return `${Math.floor(duration / 60)}分${duration % 60}秒`
        return `${Math.floor(duration / 3600)}小时${Math.floor((duration % 3600) / 60)}分`
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: WorkflowTask) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {record.need_review && record.status === 'reviewing' && (
            <Button
              type="primary"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleReview(record)}
            >
              审核
            </Button>
          )}
        </Space>
      )
    }
  ]

  return (
    <div className="workflow-tasks-page" style={{ padding: '24px' }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Select
            placeholder="筛选状态"
            allowClear
            style={{ width: 150 }}
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { label: '等待执行', value: 'pending' },
              { label: '执行中', value: 'processing' },
              { label: '等待审核', value: 'reviewing' },
              { label: '已完成', value: 'completed' },
              { label: '失败', value: 'failed' }
            ]}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => fetchTasks()}
          >
            刷新
          </Button>
        </Space>
        <div style={{ color: '#666' }}>
          自动刷新: 每 5 秒
        </div>
      </div>

      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, size) => {
            setCurrentPage(page)
            setPageSize(size)
          }
        }}
      />

      {/* 详情弹窗 */}
      <Modal
        title="任务详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedTask && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <strong>任务ID:</strong> {selectedTask.id}
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>Thread ID:</strong> {selectedTask.thread_id}
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>状态:</strong> {getStatusTag(selectedTask.status)}
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>进度:</strong> <Progress percent={selectedTask.progress} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>当前步骤:</strong> {selectedTask.current_step}
            </div>
            {selectedTask.error_message && (
              <div style={{ marginBottom: 16 }}>
                <strong style={{ color: 'red' }}>错误信息:</strong>
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                  {selectedTask.error_message}
                </pre>
              </div>
            )}
            {selectedTask.new_usercase_id && (
              <div style={{ marginBottom: 16 }}>
                <strong>创建的用例ID:</strong> {selectedTask.new_usercase_id}
              </div>
            )}
            <div style={{ marginBottom: 16 }}>
              <strong>输入参数:</strong>
              <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>
                {JSON.stringify(selectedTask.input_params, null, 2)}
              </pre>
            </div>
            {selectedTask.result_data && (
              <div style={{ marginBottom: 16 }}>
                <strong>执行结果:</strong>
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>
                  {JSON.stringify(selectedTask.result_data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* 人工审核弹窗 */}
      {selectedTask && selectedTask.interrupt_data && (
        <HumanReviewModal
          visible={reviewModalVisible}
          workflowState={selectedTask.interrupt_data as any}
          onSubmit={handleReviewSubmit}
          onCancel={() => {
            setReviewModalVisible(false)
            setSelectedTask(null)
          }}
          loading={reviewLoading}
          caseInfo={{
            name: selectedTask.input_params?.name,
            module: selectedTask.input_params?.module_id,
            sceneType: selectedTask.input_params?.scenario_type
          }}
        />
      )}
    </div>
  )
}
