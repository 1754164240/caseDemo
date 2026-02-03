import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Tooltip, Space } from 'antd'
import { FileTextOutlined, CheckSquareOutlined, BulbOutlined, RobotOutlined, CheckCircleOutlined, ApiOutlined } from '@ant-design/icons'
import { dashboardAPI } from '../services/api'
import dayjs from 'dayjs'

export default function Dashboard() {
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await dashboardAPI.getStats()
      setStats(response.data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const requirementColumns = [
    {
      title: '需求标题',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: any = {
          uploaded: 'blue',
          processing: 'orange',
          completed: 'green',
          failed: 'red',
        }
        const textMap: any = {
          uploaded: '已上传',
          processing: '处理中',
          completed: '已完成',
          failed: '失败',
        }
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
  ]

  const testCaseColumns = [
    {
      title: '用例标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '所属需求',
      dataIndex: 'requirement_title',
      key: 'requirement_title',
      ellipsis: true,
      width: 200,
    },
    {
      title: '测试点',
      dataIndex: 'test_point_title',
      key: 'test_point_title',
      ellipsis: true,
      width: 180,
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
      title: '测试类型',
      dataIndex: 'test_type',
      key: 'test_type',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>首页</h1>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="需求数量"
              value={stats.requirements_count || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="测试点数量"
              value={stats.test_points_count || 0}
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="用例数量"
              value={stats.test_cases_count || 0}
              prefix={<CheckSquareOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="当前模型"
              value={(() => {
                // 优先使用 model_config.current_model，否则使用 current_model
                const modelName = stats.model_config?.current_model || stats.current_model || 'N/A'
                // 如果包含 /，只显示最后一部分
                if (modelName.includes('/')) {
                  return modelName.split('/').pop()
                }
                return modelName
              })()}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Card title="最近需求" loading={loading} style={{ marginBottom: 16 }}>
            <Table
              dataSource={stats.recent_requirements || []}
              columns={requirementColumns}
              rowKey="id"
              pagination={false}
            />
          </Card>
        </Col>

        <Col span={24}>
          <Card title="最近测试用例" loading={loading}>
            <Table
              dataSource={stats.recent_test_cases || []}
              columns={testCaseColumns}
              rowKey="id"
              pagination={false}
              scroll={{ x: 1000 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

