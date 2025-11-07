import { useEffect, useState } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm, Tabs, Tag, Drawer, Descriptions } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons'
import { testPointsAPI, testCasesAPI, requirementsAPI } from '../services/api'
import dayjs from 'dayjs'

const { TabPane } = Tabs

export default function TestCases() {
  const [testPoints, setTestPoints] = useState([])
  const [testCases, setTestCases] = useState([])
  const [allTestCases, setAllTestCases] = useState([]) // 保存所有测试用例用于筛选
  const [requirements, setRequirements] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'testPoint' | 'testCase'>('testPoint')
  const [form] = Form.useForm()
  const [selectedRequirement, setSelectedRequirement] = useState<number>()

  // 测试用例筛选和搜索
  const [selectedTestPointFilter, setSelectedTestPointFilter] = useState<number>()
  const [searchKeyword, setSearchKeyword] = useState('')

  // 测试点详情抽屉
  const [testPointDrawerVisible, setTestPointDrawerVisible] = useState(false)
  const [selectedTestPoint, setSelectedTestPoint] = useState<any>(null)
  const [testPointCases, setTestPointCases] = useState([])

  // 测试用例详情抽屉
  const [testCaseDrawerVisible, setTestCaseDrawerVisible] = useState(false)
  const [selectedTestCase, setSelectedTestCase] = useState<any>(null)

  // 测试用例编辑
  const [editTestCaseModalVisible, setEditTestCaseModalVisible] = useState(false)
  const [editingTestCase, setEditingTestCase] = useState<any>(null)
  const [editTestCaseForm] = Form.useForm()

  useEffect(() => {
    loadRequirements()
    loadTestPoints()
    loadTestCases()

    // 监听 WebSocket 更新
    const handleTestPointsUpdate = () => loadTestPoints()
    const handleTestCasesUpdate = () => loadTestCases()
    window.addEventListener('test-points-updated', handleTestPointsUpdate)
    window.addEventListener('test-cases-updated', handleTestCasesUpdate)
    return () => {
      window.removeEventListener('test-points-updated', handleTestPointsUpdate)
      window.removeEventListener('test-cases-updated', handleTestCasesUpdate)
    }
  }, [])

  const loadRequirements = async () => {
    try {
      const response = await requirementsAPI.list()
      setRequirements(response.data)
    } catch (error) {
      console.error('Failed to load requirements:', error)
    }
  }

  const loadTestPoints = async (requirementId?: number) => {
    setLoading(true)
    try {
      const params = requirementId ? { requirement_id: requirementId } : {}
      const response = await testPointsAPI.list(params)
      setTestPoints(response.data)
    } catch (error) {
      message.error('加载测试点失败')
    } finally {
      setLoading(false)
    }
  }

  const loadTestCases = async (testPointId?: number) => {
    setLoading(true)
    try {
      const params = testPointId ? { test_point_id: testPointId } : {}
      const response = await testCasesAPI.list(params)
      setAllTestCases(response.data)
      setTestCases(response.data)
    } catch (error) {
      message.error('加载测试用例失败')
    } finally {
      setLoading(false)
    }
  }

  // 筛选和搜索测试用例
  const filterTestCases = () => {
    let filtered = [...allTestCases]

    // 按测试点筛选
    if (selectedTestPointFilter) {
      filtered = filtered.filter((tc: any) => tc.test_point_id === selectedTestPointFilter)
    }

    // 按关键词搜索
    if (searchKeyword) {
      const keyword = searchKeyword.toLowerCase()
      filtered = filtered.filter((tc: any) =>
        tc.title?.toLowerCase().includes(keyword) ||
        tc.description?.toLowerCase().includes(keyword) ||
        tc.preconditions?.toLowerCase().includes(keyword) ||
        tc.expected_result?.toLowerCase().includes(keyword)
      )
    }

    setTestCases(filtered)
  }

  // 监听筛选条件变化
  useEffect(() => {
    filterTestCases()
  }, [selectedTestPointFilter, searchKeyword, allTestCases])

  const handleGenerateTestCases = async (testPointId: number) => {
    try {
      await testCasesAPI.generate(testPointId)
      message.success('正在生成测试用例...')
    } catch (error) {
      message.error('生成失败')
    }
  }

  const handleDeleteTestPoint = async (id: number) => {
    try {
      await testPointsAPI.delete(id)
      message.success('删除成功')
      loadTestPoints()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleDeleteTestCase = async (id: number) => {
    try {
      await testCasesAPI.delete(id)
      message.success('删除成功')
      loadTestCases()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleViewTestPoint = async (record: any) => {
    try {
      setSelectedTestPoint(record)
      setTestPointDrawerVisible(true)

      // 加载该测试点的测试用例
      const response = await testCasesAPI.list({ test_point_id: record.id })
      setTestPointCases(response.data)
    } catch (error) {
      message.error('加载测试点详情失败')
    }
  }

  const handleViewTestCase = (record: any) => {
    setSelectedTestCase(record)
    setTestCaseDrawerVisible(true)
  }

  const handleEditTestCase = (record: any) => {
    setEditingTestCase(record)

    // 处理 test_steps 字段
    let testStepsValue = record.test_steps
    if (Array.isArray(testStepsValue)) {
      // 如果是对象数组，转换为字符串
      testStepsValue = testStepsValue.map((item: any, index: number) => {
        if (typeof item === 'object' && item !== null) {
          return `${index + 1}. ${item.action || ''} - 预期: ${item.expected || ''}`
        }
        return item
      }).join('\n')
    }

    editTestCaseForm.setFieldsValue({
      title: record.title,
      description: record.description,
      preconditions: record.preconditions,
      test_steps: testStepsValue,
      expected_result: record.expected_result,
      priority: record.priority,
      test_type: record.test_type,
    })
    setEditTestCaseModalVisible(true)
  }

  const handleUpdateTestCase = async () => {
    try {
      const values = await editTestCaseForm.validateFields()
      await testCasesAPI.update(editingTestCase.id, values)
      message.success('更新成功')
      setEditTestCaseModalVisible(false)
      setEditingTestCase(null)
      editTestCaseForm.resetFields()
      loadTestCases()
    } catch (error) {
      message.error('更新失败')
    }
  }

  const testPointColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
      fixed: 'left' as const,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 180,
      ellipsis: true,
    },
    {
      title: '所属需求',
      dataIndex: 'requirement_id',
      key: 'requirement_id',
      width: 150,
      ellipsis: true,
      render: (requirementId: number) => {
        const requirement = requirements.find((req: any) => req.id === requirementId)
        return requirement ? (
          <Tag color="green">{requirement.title}</Tag>
        ) : (
          <span>-</span>
        )
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      width: 250,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (text: string) => text ? <Tag color="blue">{text}</Tag> : '-',
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
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
    {
      title: '用例数',
      dataIndex: 'test_cases_count',
      key: 'test_cases_count',
      width: 80,
      align: 'center' as const,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewTestPoint(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            icon={<ThunderboltOutlined />}
            size="small"
            onClick={() => handleGenerateTestCases(record.id)}
          >
            生成用例
          </Button>
          <Popconfirm
            title="确定删除此测试点吗？"
            onConfirm={() => handleDeleteTestPoint(record.id)}
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

  const testCaseColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
      fixed: 'left' as const,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 180,
      ellipsis: true,
    },
    {
      title: '所属需求',
      dataIndex: 'test_point_id',
      key: 'requirement',
      width: 140,
      ellipsis: true,
      render: (testPointId: number) => {
        const testPoint = testPoints.find((tp: any) => tp.id === testPointId)
        if (!testPoint) return <span>-</span>

        const requirement = requirements.find((req: any) => req.id === testPoint.requirement_id)
        return requirement ? (
          <Tag color="green">{requirement.title}</Tag>
        ) : (
          <span>-</span>
        )
      },
    },
    {
      title: '所属测试点',
      dataIndex: 'test_point_id',
      key: 'test_point_id',
      width: 140,
      ellipsis: true,
      render: (testPointId: number) => {
        const testPoint = testPoints.find((tp: any) => tp.id === testPointId)
        return testPoint ? (
          <Tag color="blue">{testPoint.title}</Tag>
        ) : (
          <span>-</span>
        )
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      width: 220,
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
    {
      title: '测试类型',
      dataIndex: 'test_type',
      key: 'test_type',
      width: 100,
      render: (text: string) => text ? <Tag color="cyan">{text}</Tag> : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewTestCase(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEditTestCase(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此测试用例吗？"
            onConfirm={() => handleDeleteTestCase(record.id)}
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

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>用例管理</h1>

      <Tabs defaultActiveKey="testPoints">
        <TabPane tab="测试点" key="testPoints">
          <div style={{ marginBottom: 16 }}>
            <Space size="middle">
              <Select
                placeholder="筛选需求"
                style={{ width: 300 }}
                allowClear
                onChange={(value) => {
                  setSelectedRequirement(value)
                  loadTestPoints(value)
                }}
              >
                {requirements.map((req: any) => (
                  <Select.Option key={req.id} value={req.id}>
                    {req.title}
                  </Select.Option>
                ))}
              </Select>
              <span style={{ color: '#999' }}>
                共 {testPoints.length} 个测试点
              </span>
            </Space>
          </div>
          <Table
            dataSource={testPoints}
            columns={testPointColumns}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1400 }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个测试点`,
            }}
          />
        </TabPane>

        <TabPane tab="测试用例" key="testCases">
          <div style={{ marginBottom: 16 }}>
            <Space size="middle" style={{ width: '100%', flexWrap: 'wrap' }}>
              <Select
                placeholder="筛选测试点"
                style={{ width: 300 }}
                allowClear
                onChange={(value) => {
                  setSelectedTestPointFilter(value)
                }}
                value={selectedTestPointFilter}
              >
                {testPoints.map((tp: any) => (
                  <Select.Option key={tp.id} value={tp.id}>
                    {tp.title}
                  </Select.Option>
                ))}
              </Select>
              <Input.Search
                placeholder="搜索测试用例（标题、描述、前置条件、预期结果）"
                style={{ width: 400 }}
                allowClear
                onSearch={(value) => setSearchKeyword(value)}
                onChange={(e) => {
                  if (!e.target.value) {
                    setSearchKeyword('')
                  }
                }}
              />
              {(selectedTestPointFilter || searchKeyword) && (
                <Button
                  onClick={() => {
                    setSelectedTestPointFilter(undefined)
                    setSearchKeyword('')
                  }}
                >
                  清除筛选
                </Button>
              )}
              <span style={{ color: '#999' }}>
                共 {testCases.length} 条测试用例
                {allTestCases.length !== testCases.length &&
                  ` (从 ${allTestCases.length} 条中筛选)`
                }
              </span>
            </Space>
          </div>
          <Table
            dataSource={testCases}
            columns={testCaseColumns}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1400 }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`,
            }}
          />
        </TabPane>
      </Tabs>

      {/* 测试点详情抽屉 */}
      <Drawer
        title="测试点详情"
        placement="right"
        width={900}
        open={testPointDrawerVisible}
        onClose={() => {
          setTestPointDrawerVisible(false)
          setSelectedTestPoint(null)
          setTestPointCases([])
        }}
      >
        {selectedTestPoint && (
          <>
            <Descriptions bordered column={1} style={{ marginBottom: 24 }}>
              <Descriptions.Item label="ID">
                {selectedTestPoint.id}
              </Descriptions.Item>
              <Descriptions.Item label="标题">
                {selectedTestPoint.title}
              </Descriptions.Item>
              <Descriptions.Item label="描述">
                {selectedTestPoint.description}
              </Descriptions.Item>
              <Descriptions.Item label="分类">
                <Tag>{selectedTestPoint.category}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="优先级">
                {(() => {
                  const priority = selectedTestPoint.priority
                  const priorityMap: any = {
                    high: { color: 'red', text: '高' },
                    medium: { color: 'orange', text: '中' },
                    low: { color: 'green', text: '低' },
                  }
                  const config = priorityMap[priority] || { color: 'default', text: priority }
                  return <Tag color={config.color}>{config.text}</Tag>
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="用例数量">
                {selectedTestPoint.test_cases_count || 0}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(selectedTestPoint.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              {selectedTestPoint.user_feedback && (
                <Descriptions.Item label="用户反馈">
                  {selectedTestPoint.user_feedback}
                </Descriptions.Item>
              )}
            </Descriptions>

            <div>
              <h3 style={{ marginBottom: 16 }}>
                生成的测试用例 ({testPointCases.length})
              </h3>
              <Table
                dataSource={testPointCases}
                columns={[
                  {
                    title: 'ID',
                    dataIndex: 'id',
                    key: 'id',
                    width: 60,
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
                    title: '优先级',
                    dataIndex: 'priority',
                    key: 'priority',
                    width: 80,
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
                  {
                    title: '操作',
                    key: 'action',
                    width: 100,
                    render: (_: any, record: any) => (
                      <Button
                        type="link"
                        size="small"
                        onClick={() => handleViewTestCase(record)}
                      >
                        查看详情
                      </Button>
                    ),
                  },
                ]}
                rowKey="id"
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </div>
          </>
        )}
      </Drawer>

      {/* 测试用例详情抽屉 */}
      <Drawer
        title="测试用例详情"
        placement="right"
        width={800}
        open={testCaseDrawerVisible}
        onClose={() => {
          setTestCaseDrawerVisible(false)
          setSelectedTestCase(null)
        }}
      >
        {selectedTestCase && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="ID">
              {selectedTestCase.id}
            </Descriptions.Item>
            <Descriptions.Item label="标题">
              {selectedTestCase.title}
            </Descriptions.Item>
            <Descriptions.Item label="描述">
              {selectedTestCase.description}
            </Descriptions.Item>
            <Descriptions.Item label="优先级">
              {(() => {
                const priority = selectedTestCase.priority
                const priorityMap: any = {
                  high: { color: 'red', text: '高' },
                  medium: { color: 'orange', text: '中' },
                  low: { color: 'green', text: '低' },
                }
                const config = priorityMap[priority] || { color: 'default', text: priority }
                return <Tag color={config.color}>{config.text}</Tag>
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="测试类型">
              <Tag color="cyan">{selectedTestCase.test_type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="前置条件">
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {(() => {
                  const preconditions = selectedTestCase.preconditions
                  if (!preconditions) return '无'
                  if (typeof preconditions === 'string') return preconditions
                  if (Array.isArray(preconditions)) {
                    return preconditions.map((item: any, index: number) => (
                      <div key={index}>{typeof item === 'string' ? item : JSON.stringify(item)}</div>
                    ))
                  }
                  return JSON.stringify(preconditions)
                })()}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="测试步骤">
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {(() => {
                  const testSteps = selectedTestCase.test_steps
                  if (!testSteps) return '无'
                  if (typeof testSteps === 'string') return testSteps
                  if (Array.isArray(testSteps)) {
                    return testSteps.map((item: any, index: number) => {
                      if (typeof item === 'string') {
                        return <div key={index} style={{ marginBottom: 8 }}>{item}</div>
                      }
                      // 如果是对象，格式化显示
                      if (typeof item === 'object' && item !== null) {
                        return (
                          <div key={index} style={{ marginBottom: 12, paddingLeft: 8, borderLeft: '2px solid #1890ff' }}>
                            {item.step && <div><strong>步骤 {item.step}:</strong></div>}
                            {item.action && <div>操作: {item.action}</div>}
                            {item.expected && <div>预期: {item.expected}</div>}
                          </div>
                        )
                      }
                      return <div key={index}>{JSON.stringify(item)}</div>
                    })
                  }
                  return JSON.stringify(testSteps)
                })()}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="预期结果">
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {(() => {
                  const expectedResult = selectedTestCase.expected_result
                  if (!expectedResult) return '无'
                  if (typeof expectedResult === 'string') return expectedResult
                  if (Array.isArray(expectedResult)) {
                    return expectedResult.map((item: any, index: number) => (
                      <div key={index}>{typeof item === 'string' ? item : JSON.stringify(item)}</div>
                    ))
                  }
                  return JSON.stringify(expectedResult)
                })()}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {dayjs(selectedTestCase.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>

      {/* 编辑测试用例 Modal */}
      <Modal
        title="编辑测试用例"
        open={editTestCaseModalVisible}
        onOk={handleUpdateTestCase}
        onCancel={() => {
          setEditTestCaseModalVisible(false)
          setEditingTestCase(null)
          editTestCaseForm.resetFields()
        }}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form form={editTestCaseForm} layout="vertical">
          <Form.Item
            label="标题"
            name="title"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="请输入测试用例标题" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>

          <Form.Item label="前置条件" name="preconditions">
            <Input.TextArea rows={3} placeholder="请输入前置条件" />
          </Form.Item>

          <Form.Item label="测试步骤" name="test_steps">
            <Input.TextArea
              rows={6}
              placeholder="请输入测试步骤，每行一个步骤"
            />
          </Form.Item>

          <Form.Item label="预期结果" name="expected_result">
            <Input.TextArea rows={3} placeholder="请输入预期结果" />
          </Form.Item>

          <Form.Item label="优先级" name="priority">
            <Select>
              <Select.Option value="high">高</Select.Option>
              <Select.Option value="medium">中</Select.Option>
              <Select.Option value="low">低</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="测试类型" name="test_type">
            <Input placeholder="如：功能测试、性能测试等" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

