import { Card, Form, Input, Button, message, Divider, InputNumber, Spin } from 'antd'
import { useState, useEffect } from 'react'
import { systemConfigAPI } from '../services/api'

export default function Settings() {
  const [loading, setLoading] = useState(false)
  const [milvusForm] = Form.useForm()
  const [modelForm] = Form.useForm()
  const [initialLoading, setInitialLoading] = useState(true)

  // 加载配置
  useEffect(() => {
    loadConfigs()
  }, [])

  const loadConfigs = async () => {
    setInitialLoading(true)
    try {
      // 加载 Milvus 配置
      const milvusResponse = await systemConfigAPI.getMilvusConfig()
      milvusForm.setFieldsValue(milvusResponse.data)

      // 加载模型配置
      const modelResponse = await systemConfigAPI.getModelConfig()
      modelForm.setFieldsValue({
        api_key: modelResponse.data.api_key_full,
        api_base: modelResponse.data.api_base,
        model_name: modelResponse.data.model_name,
      })
    } catch (error: any) {
      console.error('加载配置失败:', error)
      message.error(error.response?.data?.detail || '加载配置失败')
    } finally {
      setInitialLoading(false)
    }
  }

  const onSaveMilvus = async (values: any) => {
    setLoading(true)
    try {
      await systemConfigAPI.updateMilvusConfig({
        host: values.host,
        port: parseInt(values.port),
      })
      message.success('Milvus 配置保存成功')
    } catch (error: any) {
      console.error('保存失败:', error)
      message.error(error.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const onSaveModel = async (values: any) => {
    setLoading(true)
    try {
      await systemConfigAPI.updateModelConfig({
        api_key: values.api_key,
        api_base: values.api_base,
        model_name: values.model_name,
      })
      message.success('模型配置保存成功（部分配置需要重启后端才能完全生效）')
    } catch (error: any) {
      console.error('保存失败:', error)
      message.error(error.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  if (initialLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载配置中..." />
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>系统管理</h1>

      <Card title="Milvus 配置" style={{ marginBottom: 24 }}>
        <Form
          form={milvusForm}
          layout="vertical"
          onFinish={onSaveMilvus}
        >
          <Form.Item
            name="host"
            label="Milvus Host"
            rules={[{ required: true, message: '请输入 Milvus Host' }]}
          >
            <Input placeholder="localhost" />
          </Form.Item>
          <Form.Item
            name="port"
            label="Milvus Port"
            rules={[{ required: true, message: '请输入 Milvus Port' }]}
          >
            <InputNumber
              placeholder="19530"
              style={{ width: '100%' }}
              min={1}
              max={65535}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="模型配置">
        <Form
          form={modelForm}
          layout="vertical"
          onFinish={onSaveModel}
        >
          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: true, message: '请输入 API Key' }]}
            extra="支持 OpenAI、ModelScope 等兼容 OpenAI API 的服务"
          >
            <Input.Password placeholder="请输入 API Key" />
          </Form.Item>
          <Form.Item
            name="api_base"
            label="API Base URL"
            rules={[{ required: true, message: '请输入 API Base URL' }]}
            extra="例如: https://api.openai.com/v1 或 https://api-inference.modelscope.cn/v1/chat/completions"
          >
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
            extra="例如: gpt-4, deepseek-ai/DeepSeek-V3.1 等"
          >
            <Input placeholder="gpt-4" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Divider />

      <Card title="用户管理">
        <p>用户管理功能开发中...</p>
      </Card>
    </div>
  )
}

