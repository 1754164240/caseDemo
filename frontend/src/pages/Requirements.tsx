import { useCallback, useEffect, useRef, useState, ChangeEvent } from 'react'
import { Table, Button, Upload, Modal, Form, Input, message, Tag, Space, Popconfirm, Descriptions, Drawer, Select, DatePicker } from 'antd'
import { UploadOutlined, EyeOutlined, DeleteOutlined, DownloadOutlined, ToolOutlined, AlignCenterOutlined } from '@ant-design/icons'
import { requirementsAPI, testPointsAPI } from '../services/api'
import dayjs, { Dayjs } from 'dayjs'
import TestPointsModal from '../components/TestPointsModal'

const { RangePicker } = DatePicker

export default function Requirements() {
  const [requirements, setRequirements] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false)
  const [selectedRequirement, setSelectedRequirement] = useState<any>(null)
  const [testPoints, setTestPoints] = useState([])
  const [form] = Form.useForm()
  const [fileList, setFileList] = useState<any[]>([])
  const [processingRequirementId, setProcessingRequirementId] = useState<number | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [searchKeyword, setSearchKeyword] = useState('')
  const [fileTypeFilter, setFileTypeFilter] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [createdAtRange, setCreatedAtRange] = useState<[Dayjs, Dayjs] | null>(null)
  const [testPointsModalRequirement, setTestPointsModalRequirement] = useState<any | null>(null)

  const hasLoadedRef = useRef(false)
  const processingRequirementIdRef = useRef<number | null>(null)

  const loadRequirements = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = {}
      if (searchKeyword) {
        params.search = searchKeyword
      }
      if (fileTypeFilter.length) {
        params.file_category = fileTypeFilter.join(',')
      }
      if (statusFilter.length) {
        params.statuses = statusFilter.join(',')
      }
      if (createdAtRange) {
        params.start_date = createdAtRange[0].startOf('day').toISOString()
        params.end_date = createdAtRange[1].endOf('day').toISOString()
      }

      const response = await requirementsAPI.list(params)
      const data = response.data || []
      setRequirements(data)

      const currentProcessingId = processingRequirementIdRef.current
      if (currentProcessingId) {
        const currentRequirement = data.find((req: any) => req.id === currentProcessingId)
        if (!currentRequirement || currentRequirement.status !== 'processing') {
          setProcessingRequirementId(null)
        }
      }
    } catch (error) {
      message.error('加载需求列表失败')
    } finally {
      setLoading(false)
    }
  }, [searchKeyword, fileTypeFilter, statusFilter, createdAtRange])

  useEffect(() => {
    if (hasLoadedRef.current) return
    hasLoadedRef.current = true
    loadRequirements()
  }, [loadRequirements])

  useEffect(() => {
    processingRequirementIdRef.current = processingRequirementId
  }, [processingRequirementId])

  useEffect(() => {
    if (!hasLoadedRef.current) return
    loadRequirements()
  }, [searchKeyword, fileTypeFilter, statusFilter, createdAtRange, loadRequirements])

  useEffect(() => {
    const handleUpdate = (event: Event) => {
      const requirementId = (event as CustomEvent<number | undefined>).detail
      if (requirementId && processingRequirementIdRef.current === requirementId) {
        setProcessingRequirementId(null)
      }
      loadRequirements()
    }
    window.addEventListener('test-points-updated', handleUpdate)
    return () => window.removeEventListener('test-points-updated', handleUpdate)
  }, [loadRequirements])

  useEffect(() => {
    const handleReady = (event: Event) => {
      const requirementId = (event as CustomEvent<number | undefined>).detail
      if (!requirementId) return
      const matched = requirements.find((req: any) => req.id === requirementId)
      if (matched) {
        setTestPointsModalRequirement(matched)
      } else {
        requirementsAPI
          .get(requirementId)
          .then((res) => setTestPointsModalRequirement(res.data))
          .catch(() => {})
      }
    }
    window.addEventListener('test-points-ready', handleReady)
    return () => window.removeEventListener('test-points-ready', handleReady)
  }, [requirements])

  const handleUpload = async (values: any) => {
    if (fileList.length === 0) {
      message.error('请选择文件')
      return
    }

    const formData = new FormData()
    formData.append('title', values.title)
    if (values.description) {
      formData.append('description', values.description)
    }
    formData.append('file', fileList[0].originFileObj)

    try {
      const response = await requirementsAPI.create(formData)
      const requirementId = response?.data?.id
      if (requirementId) {
        setProcessingRequirementId(requirementId)
        message.loading({
          content: '需求上传成功，正在处理...',
          key: `requirement-${requirementId}`,
          duration: 0,
        })
      } else {
        message.success('需求上传成功，正在处理...')
      }
      setUploadModalVisible(false)
      form.resetFields()
      setFileList([])
      loadRequirements()
    } catch (error: any) {
      setProcessingRequirementId(null)
      message.error(error.response?.data?.detail || '上传失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await requirementsAPI.delete(id)
      message.success('删除成功')
      loadRequirements()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleViewDetail = async (record: any) => {
    try {
      setSelectedRequirement(record)
      setDetailDrawerVisible(true)

      // 加载该需求的测试点
      const response = await testPointsAPI.list({ requirement_id: record.id })
      setTestPoints(response.data)
    } catch (error) {
      message.error('加载需求详情失败')
    }
  }

  
  const handleDownload = async (requirementId: number, fileName: string) => {
    try {
      message.loading({ content: '正在下载...', key: 'download' })
      await requirementsAPI.download(requirementId, fileName)
      message.success({ content: '下载成功', key: 'download' })
    } catch (error) {
      message.error({ content: '下载失败', key: 'download' })
    }
  }

  const handleSearch = (value: string) => {
    setSearchInput(value)
    setSearchKeyword(value.trim())
  }

  const handleSearchInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target
    setSearchInput(value)
    if (value === '') {
      setSearchKeyword('')
    }
  }

  const handleFileTypeFilterChange = (value: string[]) => {
    setFileTypeFilter(value)
  }

  const handleStatusFilterChange = (value: string[]) => {
    setStatusFilter(value)
  }

  const handleDateRangeChange = (values: null | (Dayjs | null)[], _dateStrings?: [string, string]) => {
    if (values && values[0] && values[1]) {
      setCreatedAtRange([values[0], values[1]] as [Dayjs, Dayjs])
    } else {
      setCreatedAtRange(null)
    }
  }

  const handleResetFilters = () => {
    setSearchInput('')
    setSearchKeyword('')
    setFileTypeFilter([])
    setStatusFilter([])
    setCreatedAtRange(null)
  }

  const fileTypeOptions = [
    { label: 'DOCX', value: 'docx' },
    { label: 'PDF', value: 'pdf' },
    { label: 'TXT', value: 'txt' },
    { label: 'XLS', value: 'xls' },
    { label: 'XLSX', value: 'xlsx' },
  ]

  const statusOptions = [
    { label: '已上传', value: 'uploaded' },
    { label: '处理中', value: 'processing' },
    { label: '已完成', value: 'completed' },
    { label: '失败', value: 'failed' },
  ]

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      align: 'center' as const,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      minWidth: 200,
      align: 'center' as const,
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      minWidth: 200,
      align: 'center' as const,
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type: string) => {
        const typeMap: { [key: string]: { label: string; color: string } } = {
          docx: { label: 'DOCX', color: 'blue' },
          pdf: { label: 'PDF', color: 'red' },
          txt: { label: 'TXT', color: 'green' },
          xls: { label: 'XLS', color: 'orange' },
          xlsx: { label: 'XLSX', color: 'orange' },
          word: { label: 'Word', color: 'blue' },
          excel: { label: 'Excel', color: 'orange' },
        }
        const config = typeMap[type?.toLowerCase()] || { label: type?.toUpperCase() || '未知', color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      },
      minWidth: 100,
      align: 'center' as const,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: any = {
          uploaded: 'blue',
          processing: 'orange',
          completed: 'green',
          failed: 'red',
        }
        const textMap: any = {
          uploaded: '已上传',
          processing: '处理中',
          completed: '已完成',
          failed: '失败',
        }
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
      },
      minWidth: 80,
      align: 'center' as const,
    },
    {
      title: '测试点',
      dataIndex: 'test_points_count',
      key: 'test_points_count',
      minWidth: 80,
      align: 'center' as const,
    },
    {
      title: '用例',
      dataIndex: 'test_cases_count',
      key: 'test_cases_count',
      minWidth: 80,
      align: 'center' as const,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
      minWidth: 150,
      align: 'center' as const,
    },
    {
      title: '操作',
      key: 'action',
      minWidth: 200,
      align: 'center' as const,
      render: (_: any, record: any) => (
        <Space size={2}>
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewDetail(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            icon={<ToolOutlined style={{ color: '#52c41a' }} />}
            size="small"
            onClick={() => setTestPointsModalRequirement(record)}
            style={{ color: '#52c41a' }}
          >
            测试点
          </Button>
            <Popconfirm
            title="确定删除此需求吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />} size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const testPointColumns = [
    {
      title: '测试点编号',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
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
      render: (category: string) => <Tag color="blue">{category}</Tag>,
    },
    {
      title: '业务线',
      dataIndex: 'business_line',
      key: 'business_line',
      width: 90,
      align: 'center' as const,
      render: (businessLine: string) => {
        if (!businessLine) return <Tag color="default">未识别</Tag>

        const businessLineMap: Record<string, { label: string; color: string }> = {
          contract: { label: '契约', color: 'blue' },
          preservation: { label: '保全', color: 'green' },
          claim: { label: '理赔', color: 'orange' },
        }

        const config = businessLineMap[businessLine] || { label: businessLine, color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      },
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      align: 'center' as const,
      render: (priority: string) => {
        const priorityMap: any = {
          high: { color: 'red', text: '高' },
          medium: { color: 'orange', text: '中' },
          low: { color: 'green', text: '低' },
        }
        const config = priorityMap[priority] || { color: 'default', text: priority }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h1>需求管理</h1>
        <Button
          type="primary"
          icon={<UploadOutlined />}
          onClick={() => setUploadModalVisible(true)}
        >
          上传需求
        </Button>
      </div>

      <div style={{ marginBottom: 16, display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
        <Select
          mode="multiple"
          allowClear
          placeholder="文件类型"
          options={fileTypeOptions}
          value={fileTypeFilter}
          onChange={handleFileTypeFilterChange}
          style={{ minWidth: 200 }}
        />
        <Select
          mode="multiple"
          allowClear
          placeholder="状态"
          options={statusOptions}
          value={statusFilter}
          onChange={handleStatusFilterChange}
          style={{ minWidth: 200 }}
        />
        <RangePicker
          value={createdAtRange as [Dayjs, Dayjs] | null}
          onChange={handleDateRangeChange}
          allowClear
          format="YYYY-MM-DD"
        />
        <Input.Search
          placeholder="按标题 / 文件名搜索"
          allowClear
          value={searchInput}
          onChange={handleSearchInputChange}
          onSearch={handleSearch}
          style={{ width: 260 }}
        />
        <Button onClick={handleResetFilters}>重置筛选</Button>
      </div>

      <Table
        dataSource={requirements}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="上传需求文档"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false)
          form.resetFields()
          setFileList([])
        }}
        onOk={() => form.submit()}
        okText="上传"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" onFinish={handleUpload}>
          <Form.Item
            name="title"
            label="需求标题"
            rules={[{ required: true, message: '请输入需求标题' }]}
          >
            <Input placeholder="请输入需求标题" />
          </Form.Item>
          <Form.Item name="description" label="需求描述">
            <Input.TextArea rows={3} placeholder="请输入需求描述（可选）" />
          </Form.Item>
          <Form.Item
            label="需求文档"
            required
          >
            <Upload
              fileList={fileList}
              onChange={({ fileList }) => setFileList(fileList)}
              beforeUpload={() => false}
              maxCount={1}
              accept=".docx,.pdf,.txt,.xls,.xlsx"
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
            <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
              支持格式：DOCX、PDF、TXT、XLS、XLSX
            </div>
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title="需求详情"
        placement="right"
        width={800}
        open={detailDrawerVisible}
        onClose={() => {
          setDetailDrawerVisible(false)
          setSelectedRequirement(null)
          setTestPoints([])
        }}
      >
      {selectedRequirement && (
          <>
            <Descriptions bordered column={1}>
              <Descriptions.Item label="需求标题">
                {selectedRequirement.title}
              </Descriptions.Item>
              <Descriptions.Item label="需求描述">
                {selectedRequirement.description || '无'}
              </Descriptions.Item>
              <Descriptions.Item label="文件名">
                <Button
                  type="link"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(selectedRequirement.id, selectedRequirement.file_name)}
                  style={{ padding: 0 }}
                >
                  {selectedRequirement.file_name}
                </Button>
              </Descriptions.Item>
              <Descriptions.Item label="文件类型">
                {(() => {
                  const type = selectedRequirement.file_type
                  const typeMap: { [key: string]: { label: string; color: string } } = {
                    docx: { label: 'DOCX', color: 'blue' },
                    pdf: { label: 'PDF', color: 'red' },
                    txt: { label: 'TXT', color: 'green' },
                    xls: { label: 'XLS', color: 'orange' },
                    xlsx: { label: 'XLSX', color: 'orange' },
                    word: { label: 'Word', color: 'blue' },
                    excel: { label: 'Excel', color: 'orange' },
                  }
                  const config = typeMap[type?.toLowerCase()] || { label: type?.toUpperCase() || '未知', color: 'default' }
                  return <Tag color={config.color}>{config.label}</Tag>
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="文件大小">
                {selectedRequirement.file_size
                  ? `${(selectedRequirement.file_size / 1024).toFixed(2)} KB`
                  : '未知'}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {(() => {
                  const status = selectedRequirement.status
                  const colorMap: any = {
                    uploaded: 'blue',
                    processing: 'orange',
                    completed: 'green',
                    failed: 'red',
                  }
                  const textMap: any = {
                    uploaded: '已上传',
                    processing: '处理中',
                    completed: '已完成',
                    failed: '失败',
                  }
                  return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(selectedRequirement.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            <div style={{ marginTop: 24 }}>
              <h3>测试点列表 ({testPoints.length})</h3>
              <Table
                dataSource={testPoints}
                columns={testPointColumns}
                rowKey="id"
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </div>
          </>
        )}
      </Drawer>

      {processingRequirementId && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.2)',
            zIndex: 2000,
            pointerEvents: 'auto',
          }}
        />
      )}

      <TestPointsModal
        open={!!testPointsModalRequirement}
        requirement={testPointsModalRequirement}
        onClose={() => setTestPointsModalRequirement(null)}
        onProcessingStart={(requirementId: number) => setProcessingRequirementId(requirementId)}
        onProcessingEnd={() => setProcessingRequirementId(null)}
      />
    </div>
  )
}

