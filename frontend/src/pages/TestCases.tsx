import { useEffect, useState } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm, Tabs, Tag, Drawer, Descriptions } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons'
import { testPointsAPI, testCasesAPI, requirementsAPI } from '../services/api'
import dayjs from 'dayjs'

const { TabPane } = Tabs

export default function TestCases() {
  const [testPoints, setTestPoints] = useState([])
  const [allTestPoints, setAllTestPoints] = useState([]) // 所有测试点，用于测试用例页面的筛选下拉框
  const [testCases, setTestCases] = useState([])
  const [requirements, setRequirements] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'testPoint' | 'testCase'>('testPoint')
  const [form] = Form.useForm()

  // 测试点筛选和搜索
  const [selectedRequirement, setSelectedRequirement] = useState<number>()
  const [testPointSearchKeyword, setTestPointSearchKeyword] = useState('')

  // 测试用例筛选和搜索
  const [selectedRequirementFilter, setSelectedRequirementFilter] = useState<number>()
  const [selectedTestPointFilter, setSelectedTestPointFilter] = useState<number>()
  const [testCaseSearchKeyword, setTestCaseSearchKeyword] = useState('')

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
    loadAllTestPoints()
    loadTestPoints()
    loadTestCases()

    // 监听 WebSocket 更新
    const handleTestPointsUpdate = () => {
      loadAllTestPoints()
      loadTestPoints()
    }
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

  // 加载所有测试点（用于测试用例页面的筛选下拉框）
  const loadAllTestPoints = async () => {
    try {
      const response = await testPointsAPI.list()
      setAllTestPoints(response.data)
    } catch (error) {
      console.error('Failed to load all test points:', error)
    }
  }

  const loadTestPoints = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (selectedRequirement) {
        params.requirement_id = selectedRequirement
      }
      if (testPointSearchKeyword) {
        params.search = testPointSearchKeyword
      }
      const response = await testPointsAPI.list(params)
      setTestPoints(response.data)
    } catch (error) {
      message.error('加载测试点失败')
    } finally {
      setLoading(false)
    }
  }

  const loadTestCases = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (selectedRequirementFilter) {
        params.requirement_id = selectedRequirementFilter
      }
      if (selectedTestPointFilter) {
        params.test_point_id = selectedTestPointFilter
      }
      if (testCaseSearchKeyword) {
        params.search = testCaseSearchKeyword
      }
      const response = await testCasesAPI.list(params)
      setTestCases(response.data)
    } catch (error) {
      message.error('加载测试用例失败')
    } finally {
      setLoading(false)
    }
  }

  // 监听测试点筛选条件变化
  useEffect(() => {
    loadTestPoints()
  }, [selectedRequirement, testPointSearchKeyword])

  // 监听测试用例筛选条件变化
  useEffect(() => {
    loadTestCases()
  }, [selectedRequirementFilter, selectedTestPointFilter, testCaseSearchKeyword])

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
      title: '测试点编号',
      dataIndex: 'code',
      key: 'code',
      width: 120,
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
      align: 'center' as const,
      render: (priority: string) => {
        if (!priority) return '-'

        const priorityMap: any = {
          high: { color: 'red', text: '高' },
          medium: { color: 'orange', text: '中' },
          low: { color: 'green', text: '低' },
          '高': { color: 'red', text: '高' },
          '中': { color: 'orange', text: '中' },
          '低': { color: 'green', text: '低' },
        }

        const key = priority.toLowerCase()
        const config = priorityMap[key] || priorityMap[priority] || { color: 'default', text: priority }
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
      title: '测试用例编号',
      dataIndex: 'code',
      key: 'code',
      width: 140,
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
        if (!priority) return '-'

        const priorityMap: any = {
          high: { color: 'red', text: '高' },
          medium: { color: 'orange', text: '中' },
          low: { color: 'green', text: '低' },
          '高': { color: 'red', text: '高' },
          '中': { color: 'orange', text: '中' },
          '低': { color: 'green', text: '低' },
        }

        // 转换为小写进行匹配
        const key = priority.toLowerCase()
        const config = priorityMap[key] || priorityMap[priority] || { color: 'default', text: priority }
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
            <Space size="middle" style={{ width: '100%', flexWrap: 'wrap' }}>
              <Select
                showSearch
                placeholder="筛选需求"
                style={{ width: 300 }}
                allowClear
                filterOption={(input, option) =>
                  (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
                }
                onChange={(value) => {
                  setSelectedRequirement(value)
                }}
                value={selectedRequirement}
              >
                {requirements.map((req: any) => (
                  <Select.Option key={req.id} value={req.id}>
                    {req.title}
                  </Select.Option>
                ))}
              </Select>
              <Input.Search
                placeholder="搜索测试点（标题、描述、分类）"
                style={{ width: 350 }}
                allowClear
                onSearch={(value) => setTestPointSearchKeyword(value)}
                onChange={(e) => {
                  if (!e.target.value) {
                    setTestPointSearchKeyword('')
                  }
                }}
              />
              {(selectedRequirement || testPointSearchKeyword) && (
                <Button
                  onClick={() => {
                    setSelectedRequirement(undefined)
                    setTestPointSearchKeyword('')
                  }}
                >
                  清除筛选
                </Button>
              )}
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
                showSearch
                placeholder="筛选需求"
                style={{ width: 250 }}
                allowClear
                filterOption={(input, option) =>
                  (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
                }
                onChange={(value) => {
                  setSelectedRequirementFilter(value)
                  // 清除测试点筛选
                  setSelectedTestPointFilter(undefined)
                }}
                value={selectedRequirementFilter}
              >
                {requirements.map((req: any) => (
                  <Select.Option key={req.id} value={req.id}>
                    {req.title}
                  </Select.Option>
                ))}
              </Select>
              <Select
                showSearch
                placeholder="筛选测试点"
                style={{ width: 250 }}
                allowClear
                filterOption={(input, option) =>
                  (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
                }
                onChange={(value) => {
                  setSelectedTestPointFilter(value)
                }}
                value={selectedTestPointFilter}
              >
                {allTestPoints
                  .filter((tp: any) => !selectedRequirementFilter || tp.requirement_id === selectedRequirementFilter)
                  .map((tp: any) => (
                    <Select.Option key={tp.id} value={tp.id}>
                      {tp.title}
                    </Select.Option>
                  ))}
              </Select>
              <Input.Search
                placeholder="搜索测试用例（标题、描述、前置条件、预期结果）"
                style={{ width: 350 }}
                allowClear
                onSearch={(value) => setTestCaseSearchKeyword(value)}
                onChange={(e) => {
                  if (!e.target.value) {
                    setTestCaseSearchKeyword('')
                  }
                }}
              />
              {(selectedRequirementFilter || selectedTestPointFilter || testCaseSearchKeyword) && (
                <Button
                  onClick={() => {
                    setSelectedRequirementFilter(undefined)
                    setSelectedTestPointFilter(undefined)
                    setTestCaseSearchKeyword('')
                  }}
                >
                  清除筛选
                </Button>
              )}
              <span style={{ color: '#999' }}>
                共 {testCases.length} 条测试用例
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
                  if (!priority) return '-'

                  const priorityMap: any = {
                    high: { color: 'red', text: '高' },
                    medium: { color: 'orange', text: '中' },
                    low: { color: 'green', text: '低' },
                    '高': { color: 'red', text: '高' },
                    '中': { color: 'orange', text: '中' },
                    '低': { color: 'green', text: '低' },
                  }

                  const key = priority.toLowerCase()
                  const config = priorityMap[key] || priorityMap[priority] || { color: 'default', text: priority }
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
                      if (!priority) return '-'

                      const priorityMap: any = {
                        high: { color: 'red', text: '高' },
                        medium: { color: 'orange', text: '中' },
                        low: { color: 'green', text: '低' },
                        '高': { color: 'red', text: '高' },
                        '中': { color: 'orange', text: '中' },
                        '低': { color: 'green', text: '低' },
                      }

                      const key = priority.toLowerCase()
                      const config = priorityMap[key] || priorityMap[priority] || { color: 'default', text: priority }
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
                if (!priority) return '-'

                const priorityMap: any = {
                  high: { color: 'red', text: '高' },
                  medium: { color: 'orange', text: '中' },
                  low: { color: 'green', text: '低' },
                  '高': { color: 'red', text: '高' },
                  '中': { color: 'orange', text: '中' },
                  '低': { color: 'green', text: '低' },
                }

                const key = priority.toLowerCase()
                const config = priorityMap[key] || priorityMap[priority] || { color: 'default', text: priority }
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

