import { Card, Form, Input, Button, message, InputNumber, Spin, Tabs } from 'antd'
import { useState, useEffect } from 'react'
import { systemConfigAPI } from '../services/api'
import { DatabaseOutlined, ApiOutlined, FileTextOutlined, UserOutlined } from '@ant-design/icons'

const { TextArea } = Input
const { TabPane } = Tabs

export default function Settings() {
  const [loading, setLoading] = useState(false)
  const [milvusForm] = Form.useForm()
  const [modelForm] = Form.useForm()
  const [promptForm] = Form.useForm()
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
      milvusForm.setFieldsValue({
        uri: milvusResponse.data.uri,
        user: milvusResponse.data.user,
        password: milvusResponse.data.password_full,
        token: milvusResponse.data.token_full,
        db_name: milvusResponse.data.db_name,
        collection_name: milvusResponse.data.collection_name,
      })

      // 加载模型配置
      const modelResponse = await systemConfigAPI.getModelConfig()
      modelForm.setFieldsValue({
        api_key: modelResponse.data.api_key_full,
        api_base: modelResponse.data.api_base,
        model_name: modelResponse.data.model_name,
      })

      // 加载 Prompt 配置
      const promptResponse = await systemConfigAPI.getPromptConfig()
      promptForm.setFieldsValue({
        test_point_prompt: promptResponse.data.test_point_prompt,
        test_case_prompt: promptResponse.data.test_case_prompt,
        contract_test_case_prompt: promptResponse.data.contract_test_case_prompt,
        preservation_test_case_prompt: promptResponse.data.preservation_test_case_prompt,
        claim_test_case_prompt: promptResponse.data.claim_test_case_prompt,
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
        uri: values.uri,
        user: values.user || '',
        password: values.password || '',
        token: values.token || '',
        db_name: values.db_name,
        collection_name: values.collection_name,
      })
      message.success('Milvus 配置保存成功（建议重启后端以完全生效）')
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

  const onSavePrompt = async (values: any) => {
    setLoading(true)
    try {
      await systemConfigAPI.updatePromptConfig({
        test_point_prompt: values.test_point_prompt,
        test_case_prompt: values.test_case_prompt,
        contract_test_case_prompt: values.contract_test_case_prompt,
        preservation_test_case_prompt: values.preservation_test_case_prompt,
        claim_test_case_prompt: values.claim_test_case_prompt,
      })
      message.success('Prompt 配置保存成功')
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

      <Tabs defaultActiveKey="milvus" type="card">
        <TabPane
          tab={
            <span>
              <DatabaseOutlined />
              Milvus 配置
            </span>
          }
          key="milvus"
        >
          <Card>
            <Form
              form={milvusForm}
              layout="vertical"
              onFinish={onSaveMilvus}
            >
              <Form.Item
                name="uri"
                label="Milvus 地址"
                rules={[{ required: true, message: '请输入 Milvus 地址' }]}
                extra="Milvus 服务器地址，例如：http://localhost:19530"
              >
                <Input placeholder="http://localhost:19530" />
              </Form.Item>
              <Form.Item
                name="user"
                label="用户名"
                extra="Milvus 用户名（可选，留空表示不使用用户名密码认证）"
              >
                <Input placeholder="请输入用户名" />
              </Form.Item>
              <Form.Item
                name="password"
                label="密码"
                extra="Milvus 密码（可选）"
              >
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
              <Form.Item
                name="token"
                label="Token"
                extra="Milvus Token（可选，用于 Token 认证方式）"
              >
                <Input.Password placeholder="请输入 Token" />
              </Form.Item>
              <Form.Item
                name="db_name"
                label="数据库名称"
                rules={[{ required: true, message: '请输入数据库名称' }]}
                extra="Milvus 数据库名称"
              >
                <Input placeholder="default" />
              </Form.Item>
              <Form.Item
                name="collection_name"
                label="Collection 名称"
                rules={[{ required: true, message: '请输入 Collection 名称' }]}
                extra="用于存储向量的 Collection 名称"
              >
                <Input placeholder="test_cases" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  保存配置
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <ApiOutlined />
              模型配置
            </span>
          }
          key="model"
        >
          <Card>
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
        </TabPane>

        <TabPane
          tab={
            <span>
              <FileTextOutlined />
              Prompt 配置
            </span>
          }
          key="prompt"
        >
          <Card>
            <Form
              form={promptForm}
              layout="vertical"
              onFinish={onSavePrompt}
            >
              <Form.Item
                name="test_point_prompt"
                label="测试点生成 Prompt"
                rules={[{ required: true, message: '请输入测试点生成 Prompt' }]}
                extra="用于从需求文档中提取测试点的 AI Prompt，支持使用 {feedback_instruction} 占位符，会自动识别业务线"
              >
                <TextArea
                  placeholder="请输入测试点生成 Prompt"
                  rows={10}
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item
                name="test_case_prompt"
                label="默认测试用例生成 Prompt"
                rules={[{ required: true, message: '请输入默认测试用例生成 Prompt' }]}
                extra="用于生成通用测试用例的 AI Prompt（当业务线未识别时使用）"
              >
                <TextArea
                  placeholder="请输入默认测试用例生成 Prompt"
                  rows={8}
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item
                name="contract_test_case_prompt"
                label="契约业务线测试用例 Prompt"
                rules={[{ required: true, message: '请输入契约业务线测试用例 Prompt' }]}
                extra="专门用于契约业务的测试用例生成，关注投保、核保、保单生成等流程"
              >
                <TextArea
                  placeholder="请输入契约业务线测试用例 Prompt"
                  rows={8}
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item
                name="preservation_test_case_prompt"
                label="保全业务线测试用例 Prompt"
                rules={[{ required: true, message: '请输入保全业务线测试用例 Prompt' }]}
                extra="专门用于保全业务的测试用例生成，关注保单变更、批改、续保等流程"
              >
                <TextArea
                  placeholder="请输入保全业务线测试用例 Prompt"
                  rows={8}
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item
                name="claim_test_case_prompt"
                label="理赔业务线测试用例 Prompt"
                rules={[{ required: true, message: '请输入理赔业务线测试用例 Prompt' }]}
                extra="专门用于理赔业务的测试用例生成，关注理赔申请、审核、支付等流程"
              >
                <TextArea
                  placeholder="请输入理赔业务线测试用例 Prompt"
                  rows={8}
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  保存配置
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <UserOutlined />
              用户管理
            </span>
          }
          key="users"
        >
          <Card>
            <p>用户管理功能开发中...</p>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

