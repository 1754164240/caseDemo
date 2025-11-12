import { Card, Form, Input, Button, message, Descriptions, Row, Col } from 'antd'
import { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { UserOutlined, MailOutlined } from '@ant-design/icons'

export default function Profile() {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    if (user) {
      form.setFieldsValue({
        username: user.username,
        email: user.email,
      })
    }
  }, [user, form])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      // TODO: 实现更新个人信息的API
      message.success('个人信息更新成功')
    } catch (error: any) {
      console.error('更新失败:', error)
      message.error(error.response?.data?.detail || '更新失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>个人信息</h1>

      <Row gutter={24}>
        <Col span={12}>
          <Card title="基本信息" bordered={false}>
            <Descriptions column={1}>
              <Descriptions.Item label="用户名">
                <UserOutlined style={{ marginRight: 8 }} />
                {user?.username}
              </Descriptions.Item>
              <Descriptions.Item label="邮箱">
                <MailOutlined style={{ marginRight: 8 }} />
                {user?.email || '未设置'}
              </Descriptions.Item>
              <Descriptions.Item label="用户ID">
                {user?.id}
              </Descriptions.Item>
              <Descriptions.Item label="账户状态">
                {user?.is_active ? (
                  <span style={{ color: '#52c41a' }}>✓ 已激活</span>
                ) : (
                  <span style={{ color: '#ff4d4f' }}>✗ 未激活</span>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="管理员权限">
                {user?.is_superuser ? (
                  <span style={{ color: '#1890ff' }}>✓ 是</span>
                ) : (
                  <span>✗ 否</span>
                )}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="修改密码" bordered={false}>
            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
            >
              <Form.Item
                name="old_password"
                label="当前密码"
                rules={[{ required: true, message: '请输入当前密码' }]}
              >
                <Input.Password placeholder="请输入当前密码" />
              </Form.Item>

              <Form.Item
                name="new_password"
                label="新密码"
                rules={[
                  { required: true, message: '请输入新密码' },
                  { min: 6, message: '密码至少6个字符' }
                ]}
              >
                <Input.Password placeholder="请输入新密码" />
              </Form.Item>

              <Form.Item
                name="confirm_password"
                label="确认新密码"
                dependencies={['new_password']}
                rules={[
                  { required: true, message: '请确认新密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('new_password') === value) {
                        return Promise.resolve()
                      }
                      return Promise.reject(new Error('两次输入的密码不一致'))
                    },
                  }),
                ]}
              >
                <Input.Password placeholder="请再次输入新密码" />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  修改密码
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

