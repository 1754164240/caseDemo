import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Switch,
  message,
  Space,
  Tag,
  Popconfirm,
  Tooltip,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  StarOutlined,
  StarFilled,
  ApiOutlined,
} from '@ant-design/icons'
import { modelConfigAPI } from '../services/api'

const { TextArea } = Input
const { Option } = Select

interface ModelConfig {
  id: number
  name: string
  display_name: string
  description?: string
  api_key_masked: string
  api_base: string
  model_name: string
  temperature?: string
  max_tokens?: number
  provider?: string
  model_type?: string
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at?: string
}

interface ModelConfigsProps {
  embedded?: boolean
}

export default function ModelConfigs({ embedded = false }: ModelConfigsProps) {
  const [configs, setConfigs] = useState<ModelConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<ModelConfig | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfigs()
  }, [])

  const loadConfigs = async () => {
    setLoading(true)
    try {
      const response = await modelConfigAPI.list(true) // 包含未启用的配置
      setConfigs(response.data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载模型配置失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingConfig(null)
    form.resetFields()
    form.setFieldsValue({
      temperature: '0.7',
      model_type: 'chat',
      is_active: true,
    })
    setModalVisible(true)
  }

  const handleEdit = async (config: ModelConfig) => {
    try {
      // 获取完整配置(不包含 API Key)
      const response = await modelConfigAPI.get(config.id)
      setEditingConfig(response.data)
      form.setFieldsValue({
        name: response.data.name,
        display_name: response.data.display_name,
        description: response.data.description,
        // 不设置 api_key，让用户重新输入
        api_base: response.data.api_base,
        model_name: response.data.model_name,
        temperature: response.data.temperature,
        max_tokens: response.data.max_tokens,
        provider: response.data.provider,
        model_type: response.data.model_type,
        is_active: response.data.is_active,
      })
      setModalVisible(true)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取配置详情失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await modelConfigAPI.delete(id)
      message.success('删除成功')
      loadConfigs()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handleSetDefault = async (id: number) => {
    try {
      await modelConfigAPI.setDefault(id)
      message.success('默认模型已更新')
      loadConfigs()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '设置默认模型失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      // 处理空字符串的 temperature: 如果为空,删除该字段让后端使用默认值
      const submitData = { ...values }
      if (submitData.temperature === '' || submitData.temperature === null || submitData.temperature === undefined) {
        delete submitData.temperature
      }

      if (editingConfig) {
        // 更新
        await modelConfigAPI.update(editingConfig.id, submitData)
        message.success('更新成功')
      } else {
        // 创建
        await modelConfigAPI.create(submitData)
        message.success('创建成功')
      }

      setModalVisible(false)
      loadConfigs()
    } catch (error: any) {
      if (error.errorFields) {
        // 表单验证错误
        return
      }
      message.error(error.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: '默认',
      dataIndex: 'is_default',
      key: 'is_default',
      width: 80,
      render: (isDefault: boolean, record: ModelConfig) => (
        <Tooltip title={isDefault ? '当前默认模型' : '设为默认'}>
          {isDefault ? (
            <StarFilled style={{ color: '#faad14', fontSize: 20 }} />
          ) : (
            <StarOutlined
              style={{ fontSize: 20, cursor: 'pointer', color: '#d9d9d9' }}
              onClick={() => handleSetDefault(record.id)}
            />
          )}
        </Tooltip>
      ),
    },
    {
      title: '配置名称',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 200,
      render: (text: string, record: ModelConfig) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#999' }}>{record.name}</div>
        </div>
      ),
    },
    {
      title: '模型信息',
      key: 'model_info',
      width: 250,
      render: (_: any, record: ModelConfig) => (
        <div>
          <div>
            <Tag color="blue">{record.model_name}</Tag>
            {record.provider && <Tag>{record.provider}</Tag>}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            {record.api_base}
          </div>
        </div>
      ),
    },
    {
      title: 'API Key',
      dataIndex: 'api_key_masked',
      key: 'api_key_masked',
      width: 150,
      render: (text: string) => (
        <code style={{ fontSize: 12, color: '#666' }}>{text}</code>
      ),
    },
    {
      title: '参数',
      key: 'params',
      width: 150,
      render: (_: any, record: ModelConfig) => (
        <div style={{ fontSize: 12 }}>
          {record.temperature && <div>温度: {record.temperature}</div>}
          {record.max_tokens && <div>Max Tokens: {record.max_tokens}</div>}
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: ModelConfig) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个模型配置吗?"
            description={record.is_default ? '不能删除默认模型配置' : undefined}
            onConfirm={() => handleDelete(record.id)}
            disabled={record.is_default}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_default}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: embedded ? 0 : 24 }}>
      <Card
        title={
          embedded ? undefined : (
            <Space>
              <ApiOutlined />
              <span>模型配置管理</span>
            </Space>
          )
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            添加模型配置
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 个配置`,
          }}
        />
      </Card>

      <Modal
        title={editingConfig ? '编辑模型配置' : '添加模型配置'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={700}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item
            name="name"
            label="配置名称(唯一标识)"
            rules={[
              { required: true, message: '请输入配置名称' },
              { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和连字符' },
            ]}
            extra="用于标识配置的唯一名称,只能包含字母、数字、下划线和连字符"
          >
            <Input placeholder="例如: openai-gpt4" disabled={!!editingConfig} />
          </Form.Item>

          <Form.Item
            name="display_name"
            label="显示名称"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="例如: OpenAI GPT-4" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="配置的描述信息" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: !editingConfig, message: '请输入 API Key' }]}
            extra={editingConfig ? '留空则保持原有 API Key 不变' : undefined}
          >
            <Input.Password placeholder={editingConfig ? '留空保持不变' : '请输入 API Key'} />
          </Form.Item>

          <Form.Item
            name="api_base"
            label="API Base URL"
            rules={[{ required: true, message: '请输入 API Base URL' }]}
          >
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>

          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="gpt-4" />
          </Form.Item>

          <Form.Item name="provider" label="提供商">
            <Select placeholder="选择提供商" allowClear>
              <Option value="openai">OpenAI</Option>
              <Option value="modelscope">ModelScope</Option>
              <Option value="azure">Azure OpenAI</Option>
              <Option value="custom">自定义</Option>
            </Select>
          </Form.Item>

          <Form.Item name="temperature" label="温度参数">
            <Input placeholder="0.7" />
          </Form.Item>

          <Form.Item name="max_tokens" label="最大 Token 数">
            <InputNumber placeholder="留空使用默认值" style={{ width: '100%' }} min={1} />
          </Form.Item>

          <Form.Item name="model_type" label="模型类型">
            <Select>
              <Option value="chat">Chat</Option>
              <Option value="completion">Completion</Option>
            </Select>
          </Form.Item>

          <Form.Item name="is_active" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

