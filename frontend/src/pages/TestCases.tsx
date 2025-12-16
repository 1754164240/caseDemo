import { useEffect, useState } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm, Tabs, Tag, Drawer, Descriptions, Card, Tooltip } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, ThunderboltOutlined, EyeOutlined, MinusCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, DownloadOutlined, RobotOutlined } from '@ant-design/icons'
import { testPointsAPI, testCasesAPI, requirementsAPI, systemConfigAPI } from '../services/api'
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

  // 审批相关
  const [approvalModalVisible, setApprovalModalVisible] = useState(false)
  const [approvalType, setApprovalType] = useState<'testPoint' | 'testCase'>('testPoint')
  const [approvalItem, setApprovalItem] = useState<any>(null)
  const [approvalForm] = Form.useForm()
  
  // 自动化平台配置
  const [defaultModuleId, setDefaultModuleId] = useState<string>('')

  useEffect(() => {
    loadRequirements()
    loadAllTestPoints()
    loadTestPoints()
    loadTestCases()
    loadAutomationConfig()

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
  
  const loadAutomationConfig = async () => {
    try {
      const response = await systemConfigAPI.getAutomationPlatformConfig()
      if (response.data?.module_id) {
        setDefaultModuleId(response.data.module_id)
      }
    } catch (error) {
      console.error('加载自动化平台配置失败:', error)
    }
  }

  const loadRequirements = async () => {
    try {
      const response = await requirementsAPI.list()
      setRequirements(response.data?.items || response.data || [])
    } catch (error) {
      console.error('Failed to load requirements:', error)
    }
  }

  // 加载所有测试点（用于测试用例页面的筛选下拉框）
  const loadAllTestPoints = async () => {
    try {
      const response = await testPointsAPI.list()
      setAllTestPoints(response.data?.items || response.data || [])
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
      setTestPoints(response.data?.items || response.data || [])
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
      setTestCases(response.data?.items || response.data || [])
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
      setTestPointCases(response.data?.items || response.data || [])
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
      // 如果是对象数组，清理数据
      testStepsValue = testStepsValue.map((item: any) => {
        if (typeof item === 'object' && item !== null) {
          let action = item.action || ''
          let expected = item.expected || ''

          // 去掉 action 中可能已经存在的序号
          action = action.replace(/^\d+\.\s*/, '')
          // 去掉 action 中可能已经存在的预期部分
          action = action.replace(/\s*-\s*预期:.*$/, '')
          action = action.trim()

          return {
            action: action,
            expected: expected
          }
        }
        return item
      })
    } else {
      // 如果没有测试步骤，初始化一个空步骤
      testStepsValue = [{ action: '', expected: '' }]
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

      // 处理 test_steps：添加 step 序号
      const processedValues = { ...values }
      if (values.test_steps && Array.isArray(values.test_steps)) {
        processedValues.test_steps = values.test_steps.map((item: any, index: number) => ({
          step: index + 1,
          action: item.action || '',
          expected: item.expected || ''
        }))
      }

      await testCasesAPI.update(editingTestCase.id, processedValues)
      message.success('更新成功')
      setEditTestCaseModalVisible(false)
      setEditingTestCase(null)
      editTestCaseForm.resetFields()
      loadTestCases()
    } catch (error: any) {
      console.error('更新失败:', error)
      message.error(error.response?.data?.detail || '更新失败')
    }
  }

  // 审批相关函数
  const handleOpenApproval = (item: any, type: 'testPoint' | 'testCase') => {
    setApprovalItem(item)
    setApprovalType(type)
    approvalForm.resetFields()
    setApprovalModalVisible(true)
  }

  const handleApprove = async () => {
    try {
      const values = await approvalForm.validateFields()
      const data = {
        approval_status: values.approval_status,
        approval_comment: values.approval_comment
      }

      if (approvalType === 'testPoint') {
        await testPointsAPI.approve(approvalItem.id, data)
        message.success('测试点审批成功')
        loadTestPoints()
      } else {
        await testCasesAPI.approve(approvalItem.id, data)
        message.success('测试用例审批成功')
        loadTestCases()
      }

      setApprovalModalVisible(false)
      approvalForm.resetFields()
    } catch (error: any) {
      console.error('审批失败:', error)
      message.error(error.response?.data?.detail || '审批失败')
    }
  }

  const handleResetApproval = async (item: any, type: 'testPoint' | 'testCase') => {
    try {
      if (type === 'testPoint') {
        await testPointsAPI.resetApproval(item.id)
        message.success('测试点审批状态已重置')
        loadTestPoints()
      } else {
        await testCasesAPI.resetApproval(item.id)
        message.success('测试用例审批状态已重置')
        loadTestCases()
      }
    } catch (error: any) {
      console.error('重置失败:', error)
      message.error(error.response?.data?.detail || '重置失败')
    }
  }

  const handleGenerateAutomation = async (testCase: any) => {
    // 弹出对话框让用户输入模块ID
    Modal.confirm({
      title: '生成自动化测试用例',
      width: 500,
      content: (
        <div>
          <p>请输入自动化平台的模块ID{defaultModuleId && '（可选，留空使用系统配置）'}：</p>
          <Input
            id="moduleIdInput"
            placeholder={defaultModuleId || '例如：a7f94755-b7c6-42ba-ba12-9026d9760cf5'}
            defaultValue={defaultModuleId}
          />
          {defaultModuleId && (
            <div style={{ marginTop: 8, color: '#52c41a', fontSize: 12 }}>
              ✓ 系统已配置默认模块ID，可直接生成
            </div>
          )}
          <div style={{ marginTop: 16, color: '#999', fontSize: 12 }}>
            <div>测试用例：{testCase.title}</div>
            <div>系统将自动匹配场景并在自动化平台创建用例</div>
          </div>
        </div>
      ),
      okText: '生成',
      cancelText: '取消',
      onOk: async () => {
        const moduleIdInput = (document.getElementById('moduleIdInput') as HTMLInputElement)?.value
        const moduleId = moduleIdInput?.trim() || defaultModuleId
        
        if (!moduleId) {
          message.error('请输入模块ID或在系统配置中设置默认模块ID')
          return Promise.reject()
        }
        
        try {
          message.loading({ content: '正在生成自动化用例...', key: 'generateAuto', duration: 0 })
          
          const response = await testCasesAPI.generateAutomation(testCase.id, moduleId)
          const result = response.data
          
          if (result.success) {
            message.success({
              content: '自动化用例创建成功！',
              key: 'generateAuto',
              duration: 3
            })
            
            // 显示详细信息
            Modal.success({
              title: '自动化用例创建成功',
              width: 700,
              content: (
                <div>
                  <Descriptions column={1} bordered size="small" style={{ marginBottom: 16 }}>
                    <Descriptions.Item label="测试用例">
                      {result.data.test_case.code} - {result.data.test_case.title}
                    </Descriptions.Item>
                    <Descriptions.Item label="匹配场景">
                      <Tag color="blue">{result.data.matched_scenario.scenario_code}</Tag>
                      {result.data.matched_scenario.name}
                    </Descriptions.Item>
                    <Descriptions.Item label="自动化用例ID">
                      <Tag color="green">{result.data.usercase_id}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="场景ID">
                      {result.data.scene_id}
                    </Descriptions.Item>
                  </Descriptions>
                  
                  {result.data.automation_case && (
                    <div style={{ marginTop: 16 }}>
                      <h4>自动化平台返回信息：</h4>
                      <Descriptions column={1} bordered size="small">
                        <Descriptions.Item label="用例编号">
                          {result.data.automation_case.num}
                        </Descriptions.Item>
                        <Descriptions.Item label="创建人">
                          {result.data.automation_case.createBy}
                        </Descriptions.Item>
                        <Descriptions.Item label="创建时间">
                          {new Date(result.data.automation_case.createTime).toLocaleString('zh-CN')}
                        </Descriptions.Item>
                      </Descriptions>
                    </div>
                  )}
                  
                  {result.data.supported_fields && (
                    <div style={{ marginTop: 16, padding: 12, background: '#f0f0f0', borderRadius: 4 }}>
                      <div style={{ fontWeight: 'bold', marginBottom: 8 }}>支持的字段：</div>
                      <pre style={{ margin: 0, fontSize: 12 }}>
                        {JSON.stringify(result.data.supported_fields, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )
            })
          } else {
            message.error({
              content: result.message || '创建失败',
              key: 'generateAuto'
            })
          }
        } catch (error: any) {
          console.error('生成自动化用例失败:', error)
          message.error({
            content: error.response?.data?.detail || '生成失败',
            key: 'generateAuto'
          })
          return Promise.reject()
        }
      }
    })
  }

  // 导出测试用例到Excel
  const handleExportTestCases = async () => {
    try {
      const params: { requirement_id?: number; test_point_id?: number } = {}

      if (selectedRequirementFilter) {
        params.requirement_id = selectedRequirementFilter
      }
      if (selectedTestPointFilter) {
        params.test_point_id = selectedTestPointFilter
      }

      message.loading({ content: '正在导出...', key: 'export' })

      const response = await testCasesAPI.exportExcel(params)

      if (!response.ok) {
        // 尝试解析错误信息
        let errorMessage = '导出失败'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorMessage
        } catch (e) {
          errorMessage = `导出失败 (${response.status} ${response.statusText})`
        }
        throw new Error(errorMessage)
      }

      // 获取文件名
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = '测试用例.xlsx'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
        if (filenameMatch) {
          filename = decodeURIComponent(filenameMatch[1])
        }
      }

      // 下载文件
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      message.success({ content: '导出成功', key: 'export' })
    } catch (error: any) {
      console.error('导出失败:', error)
      message.error({ content: error.message || '导出失败', key: 'export' })
    }
  }

  // 渲染审批状态标签
  const renderApprovalStatus = (status: string) => {
    const statusConfig: any = {
      pending: { color: 'default', text: '待审批', icon: <SyncOutlined spin /> },
      approved: { color: 'success', text: '已通过', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> }
    }
    const config = statusConfig[status] || statusConfig.pending
    return <Tag color={config.color} icon={config.icon}>{config.text}</Tag>
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
      title: '业务线',
      dataIndex: 'business_line',
      key: 'business_line',
      width: 90,
      align: 'center' as const,
      render: (businessLine: string) => {
        if (!businessLine) return <Tag color="default">未识别</Tag>

        const businessLineMap: Record<string, { label: string; color: string }> = {
          contract: { label: '契约', color: 'blue' },
          preservation: { label: '保全', color: 'green' },
          claim: { label: '理赔', color: 'orange' },
        }

        const config = businessLineMap[businessLine] || { label: businessLine, color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      },
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
      title: '审批状态',
      dataIndex: 'approval_status',
      key: 'approval_status',
      width: 100,
      align: 'center' as const,
      render: (status: string) => renderApprovalStatus(status || 'pending'),
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
      width: 350,
      fixed: 'right' as const,
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
          {record.approval_status === 'pending' && (
            <Button
              type="link"
              icon={<CheckCircleOutlined />}
              size="small"
              onClick={() => handleOpenApproval(record, 'testPoint')}
            >
              审批
            </Button>
          )}
          {record.approval_status !== 'pending' && (
            <Tooltip title="重置审批状态">
              <Button
                type="link"
                icon={<SyncOutlined />}
                size="small"
                onClick={() => handleResetApproval(record, 'testPoint')}
              >
                重置
              </Button>
            </Tooltip>
          )}
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
      title: '审批状态',
      dataIndex: 'approval_status',
      key: 'approval_status',
      width: 100,
      align: 'center' as const,
      render: (status: string) => renderApprovalStatus(status || 'pending'),
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
      width: 350,
      fixed: 'right' as const,
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
          {record.approval_status === 'pending' && (
            <Button
              type="link"
              icon={<CheckCircleOutlined />}
              size="small"
              onClick={() => handleOpenApproval(record, 'testCase')}
            >
              审批
            </Button>
          )}
          {record.approval_status !== 'pending' && (
            <Tooltip title="重置审批状态">
              <Button
                type="link"
                icon={<SyncOutlined />}
                size="small"
                onClick={() => handleResetApproval(record, 'testCase')}
              >
                重置
              </Button>
            </Tooltip>
          )}
          <Tooltip title="生成自动化用例">
            <Button
              type="link"
              icon={<RobotOutlined />}
              size="small"
              onClick={() => handleGenerateAutomation(record)}
            >
              自动化
            </Button>
          </Tooltip>
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
            scroll={{ x: 1500 }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个测试点`,
            }}
          />
        </TabPane>

        <TabPane tab="测试用例" key="testCases">
          <div style={{ marginBottom: 16 }}>
            <Space size="middle" style={{ width: '100%', flexWrap: 'wrap', justifyContent: 'space-between' }}>
              <Space size="middle" style={{ flexWrap: 'wrap' }}>
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
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={handleExportTestCases}
                disabled={testCases.length === 0}
              >
                导出Excel
              </Button>
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
              <Descriptions.Item label="测试点编号">
                {selectedTestPoint.code}
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
              <Descriptions.Item label="业务线">
                {(() => {
                  const businessLine = selectedTestPoint.business_line
                  if (!businessLine) return <Tag color="default">未识别</Tag>

                  const businessLineMap: Record<string, { label: string; color: string }> = {
                    contract: { label: '契约', color: 'blue' },
                    preservation: { label: '保全', color: 'green' },
                    claim: { label: '理赔', color: 'orange' },
                  }

                  const config = businessLineMap[businessLine] || { label: businessLine, color: 'default' }
                  return <Tag color={config.color}>{config.label}</Tag>
                })()}
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
              <Descriptions.Item label="审批状态">
                {renderApprovalStatus(selectedTestPoint.approval_status || 'pending')}
              </Descriptions.Item>
              {selectedTestPoint.approved_at && (
                <Descriptions.Item label="审批时间">
                  {dayjs(selectedTestPoint.approved_at).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
              )}
              {selectedTestPoint.approval_comment && (
                <Descriptions.Item label="审批意见">
                  {selectedTestPoint.approval_comment}
                </Descriptions.Item>
              )}
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
                    title: '测试用例编号',
                    dataIndex: 'code',
                    key: 'code',
                    width: 140,
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
            <Descriptions.Item label="测试用例编号">
              {selectedTestCase.code}
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
            <Descriptions.Item label="审批状态">
              {renderApprovalStatus(selectedTestCase.approval_status || 'pending')}
            </Descriptions.Item>
            {selectedTestCase.approved_at && (
              <Descriptions.Item label="审批时间">
                {dayjs(selectedTestCase.approved_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            )}
            {selectedTestCase.approval_comment && (
              <Descriptions.Item label="审批意见">
                {selectedTestCase.approval_comment}
              </Descriptions.Item>
            )}
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
        width={900}
        okText="保存"
        cancelText="取消"
        style={{ top: 20 }}
        bodyStyle={{ maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' }}
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

          <Form.Item label="测试步骤">
            <Form.List name="test_steps">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }, index) => (
                    <Card
                      key={key}
                      size="small"
                      title={`步骤 ${index + 1}`}
                      extra={
                        fields.length > 1 ? (
                          <MinusCircleOutlined
                            onClick={() => remove(name)}
                            style={{ color: '#ff4d4f' }}
                          />
                        ) : null
                      }
                      style={{ marginBottom: 16 }}
                    >
                      <Form.Item
                        {...restField}
                        name={[name, 'action']}
                        label="操作步骤"
                        rules={[{ required: true, message: '请输入操作步骤' }]}
                      >
                        <Input.TextArea
                          rows={2}
                          placeholder="请输入具体的操作步骤"
                        />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'expected']}
                        label="预期结果"
                      >
                        <Input.TextArea
                          rows={2}
                          placeholder="请输入该步骤的预期结果（可选）"
                        />
                      </Form.Item>
                    </Card>
                  ))}
                  <Form.Item>
                    <Button
                      type="dashed"
                      onClick={() => add()}
                      block
                      icon={<PlusOutlined />}
                    >
                      添加测试步骤
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>
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

      {/* 审批模态框 */}
      <Modal
        title={`审批${approvalType === 'testPoint' ? '测试点' : '测试用例'}`}
        open={approvalModalVisible}
        onOk={handleApprove}
        onCancel={() => {
          setApprovalModalVisible(false)
          approvalForm.resetFields()
        }}
        okText="提交"
        cancelText="取消"
      >
        <Form form={approvalForm} layout="vertical">
          <Form.Item label="审批对象">
            <Input value={approvalItem?.title || approvalItem?.code} disabled />
          </Form.Item>

          <Form.Item
            label="审批结果"
            name="approval_status"
            rules={[{ required: true, message: '请选择审批结果' }]}
          >
            <Select placeholder="请选择审批结果">
              <Select.Option value="approved">
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> 通过
              </Select.Option>
              <Select.Option value="rejected">
                <CloseCircleOutlined style={{ color: '#ff4d4f' }} /> 拒绝
              </Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="审批意见"
            name="approval_comment"
          >
            <Input.TextArea
              rows={4}
              placeholder="请输入审批意见（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

