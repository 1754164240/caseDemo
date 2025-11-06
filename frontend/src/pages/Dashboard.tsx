import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag } from 'antd'
import { FileTextOutlined, CheckSquareOutlined, BulbOutlined, RobotOutlined } from '@ant-design/icons'
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

  const columns = [
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
              value={stats.current_model || 'N/A'}
              prefix={<RobotOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近需求" loading={loading}>
        <Table
          dataSource={stats.recent_requirements || []}
          columns={columns}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  )
}

