import { useState, useEffect, useCallback } from 'react'
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Tag,
  Popconfirm,
  Switch,
  Card,
  Row,
  Col,
  Drawer,
  Descriptions,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  SearchOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { scenariosAPI } from '../services/api'
import type { ColumnsType } from 'antd/es/table'

const { Option } = Select
const { TextArea } = Input

interface Scenario {
  id: number
  scenario_code: string
  name: string
  description?: string
  business_line?: string
  channel?: string
  module?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export default function Scenarios() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false)
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null)
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [form] = Form.useForm()

  // 筛选条件
  const [searchKeyword, setSearchKeyword] = useState('')
  const [businessLineFilter, setBusinessLineFilter] = useState<string | undefined>()
  const [channelFilter, setChannelFilter] = useState<string | undefined>()
  const [moduleFilter, setModuleFilter] = useState<string | undefined>()
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>()

  // 加载场景列表
  const loadScenarios = useCallback(async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (searchKeyword) params.search = searchKeyword
      if (businessLineFilter) params.business_line = businessLineFilter
      if (channelFilter) params.channel = channelFilter
      if (moduleFilter) params.module = moduleFilter
      if (activeFilter !== undefined) params.is_active = activeFilter

      const response = await scenariosAPI.list(params)
      setScenarios(response.data || [])
    } catch (error) {
      message.error('加载场景列表失败')
    } finally {
      setLoading(false)
    }
  }, [searchKeyword, businessLineFilter, channelFilter, moduleFilter, activeFilter])

  useEffect(() => {
    loadScenarios()
  }, [loadScenarios])

  // 打开创建/编辑模态框
  const openModal = (scenario?: Scenario) => {
    setEditingScenario(scenario || null)
    if (scenario) {
      form.setFieldsValue(scenario)
    } else {
      form.resetFields()
      form.setFieldsValue({ is_active: true })
    }
    setModalVisible(true)
  }

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false)
    setEditingScenario(null)
    form.resetFields()
  }

  // 提交表单
  const handleSubmit = async (values: any) => {
    try {
      if (editingScenario) {
        // 更新
        await scenariosAPI.update(editingScenario.id, values)
        message.success('场景更新成功')
      } else {
        // 创建
        await scenariosAPI.create(values)
        message.success('场景创建成功')
      }
      closeModal()
      loadScenarios()
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '操作失败'
      message.error(errorMsg)
    }
  }

  // 删除场景
  const handleDelete = async (id: number) => {
    try {
      await scenariosAPI.delete(id)
      message.success('场景删除成功')
      loadScenarios()
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '删除失败'
      message.error(errorMsg)
    }
  }

  // 切换场景状态
  const handleToggleStatus = async (id: number) => {
    try {
      await scenariosAPI.toggleStatus(id)
      message.success('状态切换成功')
      loadScenarios()
    } catch (error) {
      message.error('状态切换失败')
    }
  }

  // 查看详情
  const viewDetail = (scenario: Scenario) => {
    setSelectedScenario(scenario)
    setDetailDrawerVisible(true)
  }

  // 重置筛选
  const resetFilters = () => {
    setSearchKeyword('')
    setBusinessLineFilter(undefined)
    setChannelFilter(undefined)
    setModuleFilter(undefined)
    setActiveFilter(undefined)
  }

  // 业务线映射
  const businessLineMap: Record<string, { text: string; color: string }> = {
    contract: { text: '契约', color: 'blue' },
    preservation: { text: '保全', color: 'green' },
    claim: { text: '理赔', color: 'orange' },
  }

  // 表格列定义
  const columns: ColumnsType<Scenario> = [
    {
      title: '场景名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      fixed: 'left' as const,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 300,
      ellipsis: true,
    },
    {
      title: '业务线',
      dataIndex: 'business_line',
      key: 'business_line',
      width: 100,
      render: (value) => {
        if (!value) return '-'
        const config = businessLineMap[value] || { text: value, color: 'default' }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '渠道',
      dataIndex: 'channel',
      key: 'channel',
      width: 120,
      render: (value) => value || '-',
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 120,
      render: (value) => value || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (value, record) => (
        <Switch
          checked={value}
          onChange={() => handleToggleStatus(record.id)}
          checkedChildren="启用"
          unCheckedChildren="停用"
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (value) => value ? new Date(value).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => viewDetail(record)}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除该场景吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      {/* 筛选区域 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Input
              placeholder="搜索场景名称、编号、描述"
              prefix={<SearchOutlined />}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Select
              placeholder="业务线"
              value={businessLineFilter}
              onChange={setBusinessLineFilter}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="contract">契约</Option>
              <Option value="preservation">保全</Option>
              <Option value="claim">理赔</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Input
              placeholder="渠道"
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value || undefined)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Input
              placeholder="模块"
              value={moduleFilter}
              onChange={(e) => setModuleFilter(e.target.value || undefined)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Select
              placeholder="状态"
              value={activeFilter}
              onChange={setActiveFilter}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value={true}>启用</Option>
              <Option value={false}>停用</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={resetFilters}>
                重置
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal()}>
                新建场景
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={scenarios}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1350 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* 创建/编辑模态框 */}
      <Modal
        title={editingScenario ? '编辑场景' : '新建场景'}
        open={modalVisible}
        onCancel={closeModal}
        onOk={() => form.submit()}
        width={700}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            label="场景编号"
            name="scenario_code"
            rules={[{ required: true, message: '请输入场景编号' }]}
            extra="建议格式：SC-{业务线缩写}-{序号}，如 SC-CONTRACT-001"
          >
            <Input placeholder="如：SC-CONTRACT-001" />
          </Form.Item>

          <Form.Item
            label="场景名称"
            name="name"
            rules={[{ required: true, message: '请输入场景名称' }]}
          >
            <Input placeholder="请输入场景名称" />
          </Form.Item>

          <Form.Item label="场景描述" name="description">
            <TextArea
              rows={4}
              placeholder="请输入场景描述"
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="业务线" name="business_line">
                <Select placeholder="请选择业务线" allowClear>
                  <Option value="contract">契约</Option>
                  <Option value="preservation">保全</Option>
                  <Option value="claim">理赔</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="渠道" name="channel">
                <Input placeholder="如：移动端、线上、线下" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="模块" name="module">
                <Input placeholder="如：投保模块、保全模块" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="状态" name="is_active" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="停用" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title="场景详情"
        placement="right"
        width={600}
        onClose={() => setDetailDrawerVisible(false)}
        open={detailDrawerVisible}
      >
        {selectedScenario && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="场景编号">
              {selectedScenario.scenario_code}
            </Descriptions.Item>
            <Descriptions.Item label="场景名称">
              {selectedScenario.name}
            </Descriptions.Item>
            <Descriptions.Item label="场景描述">
              {selectedScenario.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="业务线">
              {selectedScenario.business_line ? (
                <Tag color={businessLineMap[selectedScenario.business_line]?.color || 'default'}>
                  {businessLineMap[selectedScenario.business_line]?.text || selectedScenario.business_line}
                </Tag>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="渠道">
              {selectedScenario.channel || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="模块">
              {selectedScenario.module || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedScenario.is_active ? 'green' : 'red'}>
                {selectedScenario.is_active ? '启用' : '停用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(selectedScenario.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
            {selectedScenario.updated_at && (
              <Descriptions.Item label="更新时间">
                {new Date(selectedScenario.updated_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Drawer>
    </div>
  )
}

