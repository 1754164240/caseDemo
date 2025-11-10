import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  Row,
  Col,
  Input,
  Button,
  List,
  Typography,
  Space,
  Tag,
  Modal,
  Form,
  message,
  Spin,
  Empty,
  Divider,
  Tooltip,
  Avatar,
  Collapse,
} from 'antd'
import {
  SendOutlined,
  FileTextOutlined,
  PlusOutlined,
  DeleteOutlined,
  LikeOutlined,
  DislikeOutlined,
  CopyOutlined,
  UserOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'

const { TextArea } = Input
const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

interface Source {
  index: number
  content: string
  metadata: {
    document_id?: number
    title?: string
    category?: string
    chunk_index?: number
  }
}

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  sources?: Source[]
  qa_record_id?: number
  timestamp: Date
  is_helpful?: boolean
}

interface QARecord {
  id: number
  question: string
  answer: string
  sources?: Source[]
  is_helpful?: boolean
  created_at: string
}

interface KnowledgeDocument {
  id: number
  title: string
  content: string
  category?: string
  tags?: string
  chunk_count: number
  is_vectorized: boolean
  created_at: string
}

const KnowledgeBase: React.FC = () => {
  const { token } = useAuthStore()
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [uploadForm] = Form.useForm()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 加载文档列表
  const loadDocuments = async () => {
    try {
      const response = await api.get('/knowledge-base/documents', {
        params: { limit: 100 }
      })
      setDocuments(response.data.items)
    } catch (error) {
      console.error('加载文档列表失败:', error)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  // 提交问题 (流式)
  const handleAsk = async () => {
    if (!question.trim()) {
      message.warning('请输入问题')
      return
    }

    const userQuestion = question.trim()
    setQuestion('')

    // 添加用户消息
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: userQuestion,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])

    // 创建 AI 消息占位符
    const assistantMessageId = `assistant-${Date.now()}`
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, assistantMessage])

    setLoading(true)
    setStreaming(true)
    try {
      // 构建对话历史 (只发送最近的消息,不包括当前问题)
      const chatHistory = messages.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
      }))

      // 使用流式 API
      const response = await fetch('/api/v1/knowledge-base/query/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: userQuestion,
          collection_name: 'knowledge_base',
          top_k: 5,
          return_source: true,
          chat_history: chatHistory,  // 发送对话历史
        }),
      })

      if (!response.ok) {
        throw new Error('查询失败')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应')
      }

      let buffer = ''
      let fullAnswer = ''
      let sources: Source[] = []
      let qaRecordId: number | undefined

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            if (dataStr.trim()) {
              try {
                const data = JSON.parse(dataStr)

                if (data.type === 'sources') {
                  // 接收来源信息
                  sources = data.sources
                } else if (data.type === 'token') {
                  // 接收文本块,逐字显示
                  fullAnswer += data.content
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: fullAnswer, sources }
                      : msg
                  ))
                } else if (data.type === 'done') {
                  // 完成
                  fullAnswer = data.answer
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: fullAnswer, sources }
                      : msg
                  ))
                } else if (data.type === 'qa_record_id') {
                  // 接收 QA 记录 ID
                  qaRecordId = data.qa_record_id
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, qa_record_id: qaRecordId }
                      : msg
                  ))
                } else if (data.type === 'error') {
                  // 错误
                  message.error(data.error || '查询失败')
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: '抱歉,查询失败了。请稍后重试。' }
                      : msg
                  ))
                }
              } catch (e) {
                console.error('解析 SSE 数据失败:', e)
              }
            }
          }
        }
      }
    } catch (error: any) {
      message.error(error.message || '查询失败')
      // 更新错误消息
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: '抱歉,查询失败了。请稍后重试。' }
          : msg
      ))
    } finally {
      setLoading(false)
      setStreaming(false)
    }
  }

  // 提交反馈
  const handleFeedback = async (messageId: string, qaRecordId: number, isHelpful: boolean) => {
    try {
      await api.post('/knowledge-base/feedback', {
        qa_record_id: qaRecordId,
        is_helpful: isHelpful,
      })

      // 更新消息的反馈状态
      setMessages(prev => prev.map(msg =>
        msg.id === messageId ? { ...msg, is_helpful: isHelpful } : msg
      ))

      message.success('感谢您的反馈!')
    } catch (error) {
      message.error('提交反馈失败')
    }
  }

  // 清空对话
  const handleClearChat = () => {
    Modal.confirm({
      title: '确认清空对话',
      content: '确定要清空当前对话记录吗?',
      onOk: () => {
        setMessages([])
        message.success('对话已清空')
      },
    })
  }

  // 上传文档
  const handleUploadDocument = async (values: any) => {
    try {
      const formData = new FormData()
      formData.append('title', values.title)
      formData.append('content', values.content)
      if (values.category) formData.append('category', values.category)
      if (values.tags) formData.append('tags', values.tags)
      formData.append('collection_name', 'knowledge_base')

      const response = await api.post('/knowledge-base/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (response.data.success) {
        message.success(`文档上传成功! 已分割为 ${response.data.total_chunks} 个文本块`)
        setUploadModalVisible(false)
        uploadForm.resetFields()
        loadDocuments()
      } else {
        message.error(response.data.error || '上传失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '上传失败')
    }
  }

  // 复制消息
  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
    message.success('内容已复制到剪贴板')
  }

  return (
    <>
      {/* CSS 动画 */}
      <style>
        {`
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
        `}
      </style>

      <div style={{
        height: 'calc(100vh - 112px)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'  // 防止整体页面滚动
      }}>
        <Row gutter={24} style={{ flex: 1, overflow: 'hidden', height: '100%' }}>
        {/* 左侧: 聊天区域 */}
        <Col span={17} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Card
            title={
              <Space>
                <RobotOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                <span>知识问答助手</span>
                <Tag color="blue">RAG</Tag>
              </Space>
            }
            extra={
              <Space>
                <Button
                  icon={<DeleteOutlined />}
                  onClick={handleClearChat}
                  disabled={messages.length === 0}
                >
                  清空对话
                </Button>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setUploadModalVisible(true)}
                >
                  上传文档
                </Button>
              </Space>
            }
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              padding: 0,
              overflow: 'hidden'  // 防止 Card body 滚动
            }}
          >
            {/* 消息列表区域 - 只有这里可以滚动 */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                overflowX: 'hidden',
                padding: '24px',
                backgroundColor: '#f5f5f5',
              }}
            >
              {messages.length === 0 ? (
                <Empty
                  description={
                    <Space direction="vertical" size="large">
                      <Text type="secondary" style={{ fontSize: 16 }}>
                        👋 您好! 我是知识问答助手
                      </Text>
                      <Text type="secondary">
                        基于 RAG 技术,我可以根据知识库内容回答您的问题
                      </Text>
                      <Text type="secondary">
                        请在下方输入您的问题开始对话
                      </Text>
                    </Space>
                  }
                  style={{ marginTop: 100 }}
                />
              ) : (
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  {messages.map((msg, idx) => (
                    <div
                      key={msg.id}
                      style={{
                        display: 'flex',
                        justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start',
                      }}
                    >
                      <div
                        style={{
                          maxWidth: '80%',
                          display: 'flex',
                          gap: 12,
                          flexDirection: msg.type === 'user' ? 'row-reverse' : 'row',
                        }}
                      >
                        {/* 头像 */}
                        <Avatar
                          icon={msg.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
                          style={{
                            backgroundColor: msg.type === 'user' ? '#1890ff' : '#52c41a',
                            flexShrink: 0,
                          }}
                        />

                        {/* 消息内容 */}
                        <div style={{ flex: 1 }}>
                          <Card
                            size="small"
                            style={{
                              backgroundColor: msg.type === 'user' ? '#e6f7ff' : '#fff',
                              borderColor: msg.type === 'user' ? '#91d5ff' : '#d9d9d9',
                            }}
                          >
                            <Paragraph
                              style={{
                                marginBottom: 0,
                                fontSize: 15,
                                lineHeight: 1.8,
                                whiteSpace: 'pre-wrap',
                              }}
                            >
                              {msg.content}
                              {/* 流式输出时显示光标 */}
                              {msg.type === 'assistant' && streaming && idx === messages.length - 1 && (
                                <span
                                  style={{
                                    display: 'inline-block',
                                    width: 8,
                                    height: 18,
                                    backgroundColor: '#52c41a',
                                    marginLeft: 4,
                                    animation: 'blink 1s infinite',
                                  }}
                                />
                              )}
                            </Paragraph>

                            {/* AI 消息的操作按钮和来源 */}
                            {msg.type === 'assistant' && (
                              <>
                                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #f0f0f0' }}>
                                  <Space>
                                    {msg.qa_record_id && (
                                      <>
                                        <Tooltip title="这个回答有帮助">
                                          <Button
                                            size="small"
                                            type={msg.is_helpful === true ? 'primary' : 'default'}
                                            icon={<LikeOutlined />}
                                            onClick={() => handleFeedback(msg.id, msg.qa_record_id!, true)}
                                          />
                                        </Tooltip>
                                        <Tooltip title="这个回答没有帮助">
                                          <Button
                                            size="small"
                                            type={msg.is_helpful === false ? 'primary' : 'default'}
                                            danger={msg.is_helpful === false}
                                            icon={<DislikeOutlined />}
                                            onClick={() => handleFeedback(msg.id, msg.qa_record_id!, false)}
                                          />
                                        </Tooltip>
                                      </>
                                    )}
                                    <Button
                                      size="small"
                                      icon={<CopyOutlined />}
                                      onClick={() => handleCopyMessage(msg.content)}
                                    >
                                      复制
                                    </Button>
                                  </Space>
                                </div>

                                {/* 参考来源 */}
                                {msg.sources && msg.sources.length > 0 && (
                                  <div style={{ marginTop: 12 }}>
                                    <Collapse
                                      size="small"
                                      items={[
                                        {
                                          key: '1',
                                          label: `📚 参考来源 (${msg.sources.length})`,
                                          children: (
                                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                              {msg.sources.map((source) => (
                                                <Card key={source.index} size="small">
                                                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                    <Space>
                                                      <Tag color="blue">来源 {source.index}</Tag>
                                                      {source.metadata.title && (
                                                        <Text strong>{source.metadata.title}</Text>
                                                      )}
                                                      {source.metadata.category && (
                                                        <Tag>{source.metadata.category}</Tag>
                                                      )}
                                                    </Space>
                                                    <Paragraph
                                                      ellipsis={{ rows: 2, expandable: true }}
                                                      style={{ marginBottom: 0, fontSize: 13 }}
                                                    >
                                                      {source.content}
                                                    </Paragraph>
                                                  </Space>
                                                </Card>
                                              ))}
                                            </Space>
                                          ),
                                        },
                                      ]}
                                    />
                                  </div>
                                )}
                              </>
                            )}
                          </Card>

                          {/* 时间戳 */}
                          <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                            {msg.timestamp.toLocaleTimeString()}
                          </Text>
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* 加载中指示器 */}
                  {loading && (
                    <div style={{ display: 'flex', gap: 12 }}>
                      <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
                      <Card size="small" style={{ flex: 1 }}>
                        <Spin size="small" /> <Text type="secondary">AI 正在思考...</Text>
                      </Card>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </Space>
              )}
            </div>

            {/* 输入区域 */}
            <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0', backgroundColor: '#fff' }}>
              <Space.Compact style={{ width: '100%' }}>
                <TextArea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="请输入您的问题... (Enter 发送, Shift + Enter 换行)"
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  onPressEnter={(e) => {
                    // Enter 发送, Shift + Enter 换行
                    if (!e.shiftKey) {
                      e.preventDefault()
                      handleAsk()
                    }
                  }}
                  disabled={loading}
                  style={{ resize: 'none' }}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleAsk}
                  loading={loading}
                  disabled={!question.trim()}
                  style={{ height: 'auto' }}
                >
                  发送
                </Button>
              </Space.Compact>
            </div>
          </Card>
        </Col>

        {/* 右侧: 知识库文档列表 */}
        <Col span={7} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Card
            title={
              <Space>
                <FileTextOutlined />
                <span>知识库文档</span>
                <Tag color="green">{documents.length}</Tag>
              </Space>
            }
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{
              flex: 1,
              overflowY: 'auto',
              overflowX: 'hidden',
              padding: '16px'
            }}
          >
            {documents.length === 0 ? (
              <Empty
                description="暂无文档"
                style={{ marginTop: 60 }}
              >
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setUploadModalVisible(true)}
                >
                  上传第一个文档
                </Button>
              </Empty>
            ) : (
              <List
                dataSource={documents}
                renderItem={(doc) => (
                  <List.Item style={{ padding: '12px 0' }}>
                    <Card
                      size="small"
                      hoverable
                      style={{ width: '100%' }}
                    >
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <Space>
                          <FileTextOutlined style={{ fontSize: 18, color: '#1890ff' }} />
                          <Text strong ellipsis style={{ flex: 1 }}>
                            {doc.title}
                          </Text>
                        </Space>

                        {doc.category && (
                          <Tag color="blue">{doc.category}</Tag>
                        )}

                        <Space size="small">
                          <Tag color={doc.is_vectorized ? 'green' : 'orange'}>
                            {doc.is_vectorized ? '✓ 已向量化' : '⏳ 处理中'}
                          </Tag>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {doc.chunk_count} 块
                          </Text>
                        </Space>

                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {new Date(doc.created_at).toLocaleDateString()}
                        </Text>
                      </Space>
                    </Card>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 上传文档模态框 */}
      <Modal
        title="上传文档到知识库"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false)
          uploadForm.resetFields()
        }}
        onOk={() => uploadForm.submit()}
        width={600}
      >
        <Form
          form={uploadForm}
          layout="vertical"
          onFinish={handleUploadDocument}
        >
          <Form.Item
            name="title"
            label="文档标题"
            rules={[{ required: true, message: '请输入文档标题' }]}
          >
            <Input placeholder="请输入文档标题" />
          </Form.Item>

          <Form.Item
            name="content"
            label="文档内容"
            rules={[{ required: true, message: '请输入文档内容' }]}
          >
            <TextArea
              placeholder="请输入文档内容"
              rows={10}
            />
          </Form.Item>

          <Form.Item name="category" label="分类">
            <Input placeholder="例如: 契约、保全、理赔" />
          </Form.Item>

          <Form.Item name="tags" label="标签">
            <Input placeholder="多个标签用逗号分隔" />
          </Form.Item>
        </Form>
      </Modal>

      </div>
    </>
  )
}

export default KnowledgeBase

