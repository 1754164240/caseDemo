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

  const testPointColumns = [
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
      width: 200,
    },
    {
      title: '所属需求',
      dataIndex: 'requirement_id',
      key: 'requirement_id',
      width: 200,
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
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (text: string) => text ? <Tag>{text}</Tag> : '-',
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => {
        const colorMap: any = { high: 'red', medium: 'orange', low: 'blue' }
        return <Tag color={colorMap[priority]}>{priority}</Tag>
      },
    },
    {
      title: '用例数',
      dataIndex: 'test_cases_count',
      key: 'test_cases_count',
      width: 80,
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
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 180,
    },
    {
      title: '所属需求',
      dataIndex: 'test_point_id',
      key: 'requirement',
      width: 150,
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
      width: 150,
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
      width: 200,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => {
        const colorMap: any = { high: 'red', medium: 'orange', low: 'blue' }
        return <Tag color={colorMap[priority]}>{priority}</Tag>
      },
    },
    {
      title: '测试类型',
      dataIndex: 'test_type',
      key: 'test_type',
      width: 120,
      render: (text: string) => <Tag color="cyan">{text}</Tag>,
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
          <Button type="link" icon={<EditOutlined />} size="small">
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
                  const colorMap: any = { high: 'red', medium: 'orange', low: 'blue' }
                  return <Tag color={colorMap[priority]}>{priority}</Tag>
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
                      const colorMap: any = { high: 'red', medium: 'orange', low: 'blue' }
                      return <Tag color={colorMap[priority]}>{priority}</Tag>
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
                const colorMap: any = { high: 'red', medium: 'orange', low: 'blue' }
                return <Tag color={colorMap[priority]}>{priority}</Tag>
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="测试类型">
              <Tag color="cyan">{selectedTestCase.test_type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="前置条件">
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {selectedTestCase.preconditions || '无'}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="测试步骤">
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {selectedTestCase.test_steps || '无'}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="预期结果">
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {selectedTestCase.expected_result || '无'}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {dayjs(selectedTestCase.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  )
}

