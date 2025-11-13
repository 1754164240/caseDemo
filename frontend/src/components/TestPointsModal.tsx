import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Modal, Table, message, Form, Input, Tag, Empty, Timeline, Button, Select, Space } from 'antd'
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

const BUSINESS_LINE_OPTIONS = [
  { value: 'contract', label: '合同/单位' },
  { value: 'preservation', label: '保全' },
  { value: 'claim', label: '理赔' },
]

const PRIORITY_OPTIONS = [
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' },
]

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
  const [editedRows, setEditedRows] = useState<Record<number, Partial<TestPointItem>>>({})
  const [savingChanges, setSavingChanges] = useState(false)
  const [awaitingRegenResult, setAwaitingRegenResult] = useState(false)
  const testPointsSnapshotRef = useRef('[]')
  const originalTestPointsRef = useRef<Record<number, TestPointItem>>({})
  const latestSnapshotRef = useRef<TestPointItem[]>([])

  const [promptForm] = Form.useForm()

  const syncSnapshots = (list: TestPointItem[], resetEdits: boolean) => {
    latestSnapshotRef.current = list.map((item) => ({ ...item }))
    const map: Record<number, TestPointItem> = {}
    list.forEach((item) => {
      map[item.id] = { ...item }
    })
    originalTestPointsRef.current = map
    if (resetEdits) {
      setEditedRows({})
    }
  }

  const finalizeOptimization = () => {
    setOptimizing(false)
    setAwaitingRegenResult(false)
    if (requirement?.id) {
      message.destroy(`optimize-${requirement.id}`)
    }
    // 移除重复的成功提示，WebSocket已经处理了提示消息
    onProcessingEnd?.()
  }

  const loadTestPoints = async (options?: { keepOptimizing?: boolean }) => {
    if (!requirement) return
    const shouldShowTableLoading = !options?.keepOptimizing
    if (shouldShowTableLoading) {
      setTableLoading(true)
    }
    let hasChanged = false
    let fetchedData: TestPointItem[] = []
    try {
      const response = await testPointsAPI.list({ requirement_id: requirement.id, limit: 500 })
      fetchedData = response.data || []
      const nextSnapshot = JSON.stringify(fetchedData)
      hasChanged = nextSnapshot !== testPointsSnapshotRef.current
      setTestPoints(fetchedData)
      testPointsSnapshotRef.current = nextSnapshot
      syncSnapshots(fetchedData, !options?.keepOptimizing)
      setActivePoint((prev) => {
        if (!prev) return fetchedData[0] || null
        return fetchedData.find((tp: TestPointItem) => tp.id === prev.id) || fetchedData[0] || null
      })
    } catch (error) {
      message.error('加载测试点失败')
    } finally {
      if (shouldShowTableLoading) {
        setTableLoading(false)
      }
      if (options?.keepOptimizing) {
        if (hasChanged) {
          const shouldFinish = !awaitingRegenResult || (Array.isArray(fetchedData) && fetchedData.length > 0)
          if (shouldFinish) {
            finalizeOptimization()
          }
        }
        return
      }
      setOptimizing(false)
      setAwaitingRegenResult(false)
    }
  }

  useEffect(() => {
    if (open && requirement) {
      loadTestPoints()
    } else {
      setTestPoints([])
      testPointsSnapshotRef.current = '[]'
      setActivePoint(null)
      setHistory([])
      setEditedRows({})
      setAwaitingRegenResult(false)
      originalTestPointsRef.current = {}
      latestSnapshotRef.current = []
      promptForm.resetFields()
    }
  }, [open, requirement])

  useEffect(() => {
    if (!requirement) return
    const handler = (event: Event) => {
      const reqId = (event as CustomEvent<number | undefined>).detail
      if (reqId === requirement.id) {
        loadTestPoints().then(() => finalizeOptimization())
      }
    }
    window.addEventListener('test-points-updated', handler)
    return () => window.removeEventListener('test-points-updated', handler)
  }, [requirement, onProcessingEnd])

  useEffect(() => {
    if (!optimizing || !requirement) return
    const pollTimer = window.setInterval(() => {
      loadTestPoints({ keepOptimizing: true })
    }, 4000)
    const safetyTimer = window.setTimeout(() => {
      finalizeOptimization()
      message.warning('提示词生成结果超时，已停止等待')
    }, 45000)
    // 立即拉取一次，避免等待首个间隔
    loadTestPoints({ keepOptimizing: true })
    return () => {
      window.clearInterval(pollTimer)
      window.clearTimeout(safetyTimer)
    }
  }, [optimizing, requirement])

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

  const submitRegenerate = async (force = false) => {
    if (!requirement) {
      message.info('请选择需求')
      return
    }
    const values = promptForm.getFieldsValue()
    const promptText = (values.prompt || '').trim()
    try {
      await testPointsAPI.regenerate(requirement.id, {
        feedback: promptText || undefined,
        force,
      })
      setAwaitingRegenResult(true)
      setOptimizing(true)
      onProcessingStart?.(requirement.id)
      message.loading({
        content: '提示词已提交，正在重新生成测试点...',
        key: `optimize-${requirement.id}`,
        duration: 0,
      })
    } catch (error: any) {
      const detail = error.response?.data?.detail
      if (!force && detail?.code === 'test_points_in_use') {
        Modal.confirm({
          title: '检测到测试点已被使用',
          content:
            detail?.message ||
            `检测到该需求已有 ${detail?.cases || 0} 条测试用例或 ${detail?.approved || 0} 条已审批测试点，继续将清空这些数据。`,
          okText: '继续并清理',
          cancelText: '取消',
          onOk: () => submitRegenerate(true),
        })
        return
      }
      message.error(detail?.message || detail || '提交重新生成失败')
    }
  }

  const handleOptimize = () => {
    submitRegenerate()
  }

  type EditableField = 'title' | 'description' | 'category' | 'business_line' | 'priority'

  const handleFieldChange = useCallback(
    (id: number, field: EditableField, value: TestPointItem[EditableField]) => {
      setTestPoints((prev) =>
        prev.map((tp) => (tp.id === id ? { ...tp, [field]: value as any } : tp))
      )
      setEditedRows((prev) => {
        const next = { ...prev }
        const original = originalTestPointsRef.current[id]
        const normalize = (val: unknown) => (val ?? '') as string
        if (original && normalize(original[field]) === normalize(value)) {
          if (next[id]) {
            const updatedRow = { ...next[id] }
            delete updatedRow[field]
            if (Object.keys(updatedRow).length) {
              next[id] = updatedRow
            } else {
              delete next[id]
            }
          }
        } else {
          next[id] = { ...(next[id] || {}), [field]: value }
        }
        return next
      })
    },
    []
  )

  const hasPendingEdits = Object.keys(editedRows).length > 0

  const handleResetEdits = () => {
    setTestPoints(latestSnapshotRef.current.map((item) => ({ ...item })))
    setEditedRows({})
  }

  const handleSaveChanges = async () => {
    if (!requirement || !hasPendingEdits) return
    setSavingChanges(true)

    // 保存当前编辑数据，避免清空后无法使用
    const currentEdits = { ...editedRows }

    try {
      const updates = Object.entries(currentEdits).map(([id, payload]) => ({
        id: Number(id),
        ...payload,
      }))
      await testPointsAPI.bulkUpdate({
        requirement_id: requirement.id,
        updates,
      })
      message.success('保存成功')
      setEditedRows({})

      // 保持当前列表顺序，直接更新状态而不重新加载
      setTestPoints(prev => {
        const updated = [...prev]
        Object.entries(currentEdits).forEach(([id, payload]) => {
          const index = updated.findIndex(tp => tp.id === Number(id))
          if (index !== -1) {
            updated[index] = { ...updated[index], ...payload }
          }
        })
        return updated
      })

      // 同步更新快照数据
      syncSnapshots(testPoints.map((item) => ({ ...item })), false)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '保存失败')
    } finally {
      setSavingChanges(false)
    }
  }


  const businessLineOptions = BUSINESS_LINE_OPTIONS
  const priorityOptions = PRIORITY_OPTIONS

  const columns: ColumnsType<TestPointItem> = useMemo(
    () => [
      {
        title: '测试点编号',
        dataIndex: 'code',
        key: 'code',
        width: 110,
        sorter: (a, b) => a.code.localeCompare(b.code),
      },
      {
        title: '标题',
        dataIndex: 'title',
        key: 'title',
        width: 180,
        render: (_: string, record: TestPointItem) => (
          <Input
            size="small"
            value={record.title || ''}
            onChange={(e) => handleFieldChange(record.id, 'title', e.target.value)}
          />
        ),
      },
      {
        title: '描述',
        dataIndex: 'description',
        key: 'description',
        width: 220,
        render: (_: string, record: TestPointItem) => (
          <Input.TextArea
            value={record.description || ''}
            autoSize={{ minRows: 1, maxRows: 2 }}
            style={{ resize: 'none' }}
            onChange={(e) => handleFieldChange(record.id, 'description', e.target.value)}
          />
        ),
      },
      {
        title: '分类',
        dataIndex: 'category',
        key: 'category',
        width: 120,
        render: (_: string, record: TestPointItem) => (
          <Input
            size="small"
            value={record.category || ''}
            onChange={(e) => handleFieldChange(record.id, 'category', e.target.value)}
          />
        ),
      },
      {
        title: '业务线',
        dataIndex: 'business_line',
        key: 'business_line',
        width: 130,
        render: (_: string, record: TestPointItem) => (
          <Select
            allowClear
            size="small"
            options={businessLineOptions}
            placeholder="请选择"
            value={record.business_line || undefined}
            onChange={(value) => handleFieldChange(record.id, 'business_line', value || undefined)}
            style={{ width: '100%' }}
          />
        ),
      },
      {
        title: '优先级',
        dataIndex: 'priority',
        key: 'priority',
        width: 110,
        render: (_: string, record: TestPointItem) => (
          <Select
            size="small"
            options={priorityOptions}
            placeholder="请选择"
            value={record.priority || undefined}
            onChange={(value) => handleFieldChange(record.id, 'priority', value || undefined)}
            style={{ width: '100%' }}
          />
        ),
      },
    ],
    [businessLineOptions, handleFieldChange, priorityOptions]
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
            minHeight: 560,
            position: 'relative',
            height: '70vh',
          }}
        >
          <div style={{ flex: '0 0 75%', maxWidth: '75%', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 8,
              }}
            >
              <div style={{ color: hasPendingEdits ? '#fa8c16' : '#999', fontSize: 12 }}>
                {hasPendingEdits
                  ? `已修改 ${Object.keys(editedRows).length} 条，点击“保存修改”生效`
                  : '点击表格单元格即可行内编辑'}
              </div>
              <Space>
                <Button onClick={handleResetEdits} disabled={!hasPendingEdits}>
                  撤销修改
                </Button>
                <Button
                  type="primary"
                  onClick={handleSaveChanges}
                  disabled={!hasPendingEdits}
                  loading={savingChanges}
                >
                  保存修改
                </Button>
              </Space>
            </div>
            <div style={{ flex: 1, height: '100%', overflow: 'hidden' }}>
              <Table
                rowKey="id"
                dataSource={testPoints}
                columns={columns}
                loading={tableLoading}
                size="small"
                pagination={false}
                scroll={{ x: 'max-content', y: 'calc(70vh - 100px)' }}
                onRow={(record) => ({
                  onClick: () => setActivePoint(record),
                })}
                style={{ height: '100%' }}
                tableLayout="fixed"
              />
            </div>
          </div>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16, minHeight: 0 }}>
            <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16 }}>
              <h4 style={{ marginBottom: 12 }}>业务提示词调优</h4>
              <Form layout="vertical" form={promptForm}>
                <Form.Item name="prompt" label={null}>
                  <Input.TextArea rows={7} placeholder="请输入契合当前业务场景的统一提示词调优说明" />
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
                        <div style={{ color: '#666' }}>{item.prompt_summary || '暂无提示词摘要'}</div>
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
