import { Card, Form, Input, Button, message, Spin, Tabs } from 'antd'
import { useState, useEffect } from 'react'
import { systemConfigAPI } from '../services/api'
import { DatabaseOutlined, ApiOutlined, FileTextOutlined, UserOutlined, AppstoreOutlined } from '@ant-design/icons'
import ModelConfigs from './ModelConfigs'

const { TextArea } = Input
const { TabPane } = Tabs

export default function Settings() {
  const [loading, setLoading] = useState(false)
  const [milvusForm] = Form.useForm()
  const [embeddingForm] = Form.useForm()
  const [automationForm] = Form.useForm()
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

      // 加载 Embedding 配置
      const embeddingResponse = await systemConfigAPI.getEmbeddingConfig()
      embeddingForm.setFieldsValue({
        embedding_model: embeddingResponse.data.embedding_model,
        embedding_api_key: embeddingResponse.data.embedding_api_key_full,
        embedding_api_base: embeddingResponse.data.embedding_api_base,
      })

      // 加载自动化测试平台配置
      const automationResponse = await systemConfigAPI.getAutomationPlatformConfig()
      automationForm.setFieldsValue({
        api_base: automationResponse.data.api_base,
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

  const onSaveEmbedding = async (values: any) => {
    setLoading(true)
    try {
      await systemConfigAPI.updateEmbeddingConfig({
        embedding_model: values.embedding_model,
        embedding_api_key: values.embedding_api_key,
        embedding_api_base: values.embedding_api_base,
      })
      message.success('Embedding 模型配置保存成功（部分配置需要重启后端才能完全生效）')
    } catch (error: any) {
      console.error('保存失败:', error)
      message.error(error.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const onSaveAutomationPlatform = async (values: any) => {
    setLoading(true)
    try {
      await systemConfigAPI.updateAutomationPlatformConfig({
        api_base: values.api_base || '',
      })
      message.success('自动化测试平台配置保存成功')
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
          key="model-configs"
        >
          <ModelConfigs embedded={true} />
        </TabPane>

        <TabPane
          tab={
            <span>
              <ApiOutlined />
              Embedding 配置
            </span>
          }
          key="embedding"
        >
          <Card>
            <Form
              form={embeddingForm}
              layout="vertical"
              onFinish={onSaveEmbedding}
            >
              <Form.Item
                name="embedding_model"
                label="Embedding 模型名称"
                rules={[{ required: true, message: '请输入 Embedding 模型名称' }]}
                extra="例如: text-embedding-ada-002 (OpenAI), BAAI/bge-small-zh-v1.5 (ModelScope)"
              >
                <Input placeholder="text-embedding-ada-002" />
              </Form.Item>
              <Form.Item
                name="embedding_api_key"
                label="Embedding API Key"
                extra="为空时使用 LLM 的 API Key。如果 Embedding 模型使用不同的服务,请单独配置"
              >
                <Input.Password placeholder="为空时使用 LLM 的 API Key" />
              </Form.Item>
              <Form.Item
                name="embedding_api_base"
                label="Embedding API Base URL"
                extra="为空时使用 LLM 的 API Base。如果 Embedding 模型使用不同的服务,请单独配置"
              >
                <Input placeholder="为空时使用 LLM 的 API Base" />
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
              <AppstoreOutlined />
              第三方接入
            </span>
          }
          key="automation-platform"
        >
          <Card>
            <Form
              form={automationForm}
              layout="vertical"
              onFinish={onSaveAutomationPlatform}
            >
              <Form.Item
                name="api_base"
                label="自动化测试平台 API 地址"
                rules={[{ required: true, message: '请输入自动化测试平台 API 地址' }]}
                extra="用于与第三方自动化测试平台对接的基础 API 地址，例如：https://autotest.example.com/api"
              >
                <Input placeholder="https://autotest.example.com/api" />
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

      {/* 版本号 */}
      <div style={{
        marginTop: 24,
        textAlign: 'center',
        color: '#999',
        fontSize: 12,
        padding: '12px 0',
        borderTop: '1px solid #f0f0f0'
      }}>
        智能测试用例平台 v0.5.0
      </div>
    </div>
  )
}
