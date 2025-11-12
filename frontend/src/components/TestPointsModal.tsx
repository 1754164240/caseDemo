import { useEffect, useMemo, useState } from 'react'
import { Modal, Table, message, Form, Input, Tag, Empty, Timeline, Button } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { testPointsAPI } from '../services/api'

interface TestPointsModalProps {
  open: boolean
  requirement: any | null
  onClose: () => void
  onProcessingStart?: (requirementId: number) => void
  onProcessingEnd?: () => void
}

interface TestPointItem {
  id: number
  code: string
  title: string
  description?: string
  category?: string
  business_line?: string
  priority?: string
  approval_status?: string
}

interface HistoryEntry {
  id: number
  version: string
  prompt_summary?: string
  status: string
  created_at: string
}

export default function TestPointsModal({
  open,
  requirement,
  onClose,
  onProcessingStart,
  onProcessingEnd,
}: TestPointsModalProps) {
  const [tableLoading, setTableLoading] = useState(false)
  const [testPoints, setTestPoints] = useState<TestPointItem[]>([])
  const [activePoint, setActivePoint] = useState<TestPointItem | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [optimizing, setOptimizing] = useState(false)

  const [promptForm] = Form.useForm()

  const loadTestPoints = async () => {
    if (!requirement) return
    setTableLoading(true)
    try {
      const response = await testPointsAPI.list({ requirement_id: requirement.id, limit: 500 })
      const data = response.data || []
      setTestPoints(data)
      setActivePoint((prev) => {
        if (!prev) return data[0] || null
        return data.find((tp: TestPointItem) => tp.id === prev.id) || data[0] || null
      })
    } catch (error) {
      message.error('加载测试点失败')
    } finally {
      setTableLoading(false)
      setOptimizing(false)
    }
  }

  useEffect(() => {
    if (open && requirement) {
      loadTestPoints()
    } else {
      setTestPoints([])
      setActivePoint(null)
      setHistory([])
      promptForm.resetFields()
    }
  }, [open, requirement])

  useEffect(() => {
    if (!requirement) return
    const handler = (event: Event) => {
      const reqId = (event as CustomEvent<number | undefined>).detail
      if (reqId === requirement.id) {
        loadTestPoints()
        onProcessingEnd?.()
      }
    }
    window.addEventListener('test-points-updated', handler)
    return () => window.removeEventListener('test-points-updated', handler)
  }, [requirement, onProcessingEnd])

  useEffect(() => {
    if (!activePoint) {
      setHistory([])
      return
    }
    ;(async () => {
      try {
        const response = await testPointsAPI.history(activePoint.id)
        setHistory(response.data || [])
      } catch {
        setHistory([])
      }
    })()
  }, [activePoint])

  const handleOptimize = async () => {
    if (!requirement || !testPoints.length) {
      message.info('暂无可优化的测试点')
      return
    }
    const values = promptForm.getFieldsValue()
    try {
      await testPointsAPI.optimize({
        requirement_id: requirement.id,
        selected_ids: testPoints.map((tp) => tp.id),
        mode: 'batch',
        batch_prompt: values.prompt || undefined,
        per_point_prompts: {},
      })
      setOptimizing(true)
      onProcessingStart?.(requirement.id)
      message.loading({
        content: '提示词优化已提交，正在重新生成测试点...',
        key: `optimize-${requirement.id}`,
        duration: 0,
      })
    } catch (error: any) {
      message.error(error.response?.data?.detail || '提交优化失败')
    }
  }

  const columns: ColumnsType<TestPointItem> = useMemo(
    () => [
      {
        title: '测试点编号',
        dataIndex: 'code',
        key: 'code',
        width: 120,
        sorter: (a, b) => a.code.localeCompare(b.code),
      },
      {
        title: '标题',
        dataIndex: 'title',
        key: 'title',
        ellipsis: true,
      },
      {
        title: '描述',
        dataIndex: 'description',
        key: 'description',
        ellipsis: true,
      },
      {
        title: '分类',
        dataIndex: 'category',
        key: 'category',
        width: 120,
        render: (value: string) =>
          value ? <Tag color="purple">{value}</Tag> : <Tag color="default">未分类</Tag>,
      },
      {
        title: '业务线',
        dataIndex: 'business_line',
        key: 'business_line',
        width: 120,
        render: (value: string) => {
          const map: Record<string, { color: string; label: string }> = {
            contract: { color: 'blue', label: '契约' },
            preservation: { color: 'green', label: '保全' },
            claim: { color: 'orange', label: '理赔' },
          }
          if (!value) {
            return <Tag color="default">未设置</Tag>
          }
          const cfg = map[value] || { color: 'default', label: value }
          return <Tag color={cfg.color}>{cfg.label}</Tag>
        },
      },
      {
        title: '优先级',
        dataIndex: 'priority',
        key: 'priority',
        width: 100,
        render: (value: string) => {
          const map: Record<string, { color: string; text: string }> = {
            high: { color: 'red', text: '高' },
            medium: { color: 'orange', text: '中' },
            low: { color: 'green', text: '低' },
          }
          const cfg = map[value] || { color: 'default', text: value || '-' }
          return <Tag color={cfg.color}>{cfg.text}</Tag>
        },
      },
    ],
    []
  )

  return (
    <Modal
      open={open}
      title={`测试点管理 - ${requirement?.title || ''}`}
      onCancel={onClose}
      footer={null}
      width={960}
      destroyOnClose
    >
      {!requirement ? (
        <Empty description="请选择需求" />
      ) : (
        <div
          style={{
            display: 'flex',
            gap: 16,
            minHeight: 520,
            position: 'relative',
            height: '60vh',
          }}
        >
          <div style={{ flex: 1.4, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div style={{ flex: 1, height: '100%', overflow: 'hidden' }}>
              <Table
                rowKey="id"
                dataSource={testPoints}
                columns={columns}
                loading={tableLoading}
                size="small"
                pagination={false}
                scroll={{ y: 'calc(60vh - 24px)' }}
                onRow={(record) => ({
                  onClick: () => setActivePoint(record),
                })}
                style={{ height: '100%' }}
              />
            </div>
          </div>

          <div style={{ flex: 0.6, display: 'flex', flexDirection: 'column', gap: 16, minHeight: 0 }}>
            <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16 }}>
              <h4 style={{ marginBottom: 12 }}>人机协同 - 测试点提示词调优</h4>
              <Form layout="vertical" form={promptForm}>
                <Form.Item name="prompt" label="测试点提示词补充">
                  <Input.TextArea rows={3} placeholder="请输入整体优化测试点的业务提示词" />
                </Form.Item>
                <Button type="primary" block onClick={handleOptimize}>
                  重新生成测试点
                </Button>
              </Form>
            </div>


            <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, flex: 1, overflowY: 'auto' }}>
              <h4 style={{ marginBottom: 12 }}>版本历史</h4>
              {activePoint && history.length ? (
                <Timeline
                  items={history.map((item) => ({
                    color: item.status === 'approved' ? 'green' : 'blue',
                    children: (
                      <div>
                        <strong>{item.version}</strong> - {item.status}
                        <div style={{ color: '#666' }}>{item.prompt_summary || '无提示词摘要'}</div>
                        <div style={{ fontSize: 12 }}>{new Date(item.created_at).toLocaleString()}</div>
                      </div>
                    ),
                  }))}
                />
              ) : (
                <Empty description={activePoint ? '暂无历史' : '请选择测试点'} />
              )}
            </div>
          </div>

          {optimizing && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background: 'rgba(255,255,255,0.65)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                pointerEvents: 'auto',
              }}
            >
              模型生成中...
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}
