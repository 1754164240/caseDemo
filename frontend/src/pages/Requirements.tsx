import { useEffect, useState } from 'react'
import { Table, Button, Upload, Modal, Form, Input, message, Tag, Space, Popconfirm, Descriptions, Drawer } from 'antd'
import { UploadOutlined, EyeOutlined, DeleteOutlined, ThunderboltOutlined, DownloadOutlined } from '@ant-design/icons'
import { requirementsAPI, testPointsAPI } from '../services/api'
import dayjs from 'dayjs'

export default function Requirements() {
  const [requirements, setRequirements] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false)
  const [selectedRequirement, setSelectedRequirement] = useState<any>(null)
  const [testPoints, setTestPoints] = useState([])
  const [form] = Form.useForm()
  const [fileList, setFileList] = useState<any[]>([])

  useEffect(() => {
    loadRequirements()
    
    // 监听 WebSocket 更新
    const handleUpdate = () => loadRequirements()
    window.addEventListener('test-points-updated', handleUpdate)
    return () => window.removeEventListener('test-points-updated', handleUpdate)
  }, [])

  const loadRequirements = async () => {
    setLoading(true)
    try {
      const response = await requirementsAPI.list()
      setRequirements(response.data)
    } catch (error) {
      message.error('加载需求列表失败')
    } finally {
      setLoading(false)
    }
  }

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
      await requirementsAPI.create(formData)
      message.success('需求上传成功，正在处理...')
      setUploadModalVisible(false)
      form.resetFields()
      setFileList([])
      loadRequirements()
    } catch (error: any) {
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

  const handleRegenerateTestPoints = async (record: any) => {
    try {
      await testPointsAPI.regenerate(record.id)
      message.success('正在重新生成测试点...')

      // 更新需求状态为处理中
      setTimeout(() => {
        loadRequirements()
      }, 1000)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '生成测试点失败')
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

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
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
    },
    {
      title: '测试点',
      dataIndex: 'test_points_count',
      key: 'test_points_count',
    },
    {
      title: '用例',
      dataIndex: 'test_cases_count',
      key: 'test_cases_count',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 240,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewDetail(record)}
          >
            查看
          </Button>
          <Popconfirm
            title="确定重新生成测试点吗？这将删除现有的测试点。"
            onConfirm={() => handleRegenerateTestPoints(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              icon={<ThunderboltOutlined />}
              size="small"
            >
              生成测试点
            </Button>
          </Popconfirm>
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
                <Tag>{selectedRequirement.file_type?.toUpperCase()}</Tag>
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
    </div>
  )
}

