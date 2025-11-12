import { useState } from 'react'
import { Form, Input, Button, Card, message, Tabs, Alert } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { authAPI } from '../services/api'
import { useAuthStore } from '../stores/authStore'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('login')
  const [loginError, setLoginError] = useState('')
  const [registerError, setRegisterError] = useState('')
  const { setAuth } = useAuthStore()

  const onLogin = async (values: any) => {
    setLoading(true)
    setLoginError('') // 清除之前的错误
    try {
      const response = await authAPI.login(values.username, values.password)
      const { access_token } = response.data

      // 使用 token 获取用户信息
      const userResponse = await authAPI.getMe(access_token)

      // 保存 token 和用户信息
      setAuth(access_token, userResponse.data)

      message.success('登录成功，正在跳转...')

      // 跳转到首页
      setTimeout(() => {
        window.location.href = '/'
      }, 500)
    } catch (error: any) {
      console.error('登录失败:', error)

      // 详细的错误处理
      let errorMessage = '登录失败，请稍后重试'

      if (error.response) {
        // 服务器返回错误
        const status = error.response.status
        const detail = error.response.data?.detail

        if (status === 401) {
          errorMessage = '用户名或密码错误，请检查后重试'
        } else if (status === 422) {
          errorMessage = '请输入正确的用户名和密码'
        } else if (status === 500) {
          errorMessage = '服务器错误，请稍后重试'
        } else if (detail) {
          errorMessage = detail
        }
      } else if (error.request) {
        // 请求已发送但没有收到响应
        errorMessage = '无法连接到服务器，请检查网络连接'
      }

      setLoginError(errorMessage)
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const onRegister = async (values: any) => {
    setLoading(true)
    setRegisterError('') // 清除之前的错误
    try {
      await authAPI.register(values)
      message.success('注册成功，请登录')
      setActiveTab('login')
      setRegisterError('')
    } catch (error: any) {
      console.error('注册失败:', error)

      // 详细的错误处理
      let errorMessage = '注册失败，请稍后重试'

      if (error.response) {
        const status = error.response.status
        const detail = error.response.data?.detail

        if (status === 400) {
          if (detail?.includes('already exists') || detail?.includes('已存在')) {
            errorMessage = '该用户名或邮箱已被注册'
          } else {
            errorMessage = detail || '注册信息有误，请检查后重试'
          }
        } else if (status === 422) {
          errorMessage = '请填写正确的注册信息'
        } else if (status === 500) {
          errorMessage = '服务器错误，请稍后重试'
        } else if (detail) {
          errorMessage = detail
        }
      } else if (error.request) {
        errorMessage = '无法连接到服务器，请检查网络连接'
      }

      setRegisterError(errorMessage)
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card
        style={{ width: 400 }}
        title={
          <div style={{ textAlign: 'center', fontSize: 24, fontWeight: 'bold' }}>
            智能测试用例平台
          </div>
        }
      >
        <Tabs activeKey={activeTab} onChange={(key) => {
          setActiveTab(key)
          setLoginError('')
          setRegisterError('')
        }} centered>
          <Tabs.TabPane tab="登录" key="login">
            {loginError && (
              <Alert
                message="登录失败"
                description={loginError}
                type="error"
                showIcon
                closable
                onClose={() => setLoginError('')}
                style={{ marginBottom: 16 }}
              />
            )}
            <Form onFinish={onLogin} autoComplete="off">
              <Form.Item
                name="username"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="用户名" size="large" />
              </Form.Item>
              <Form.Item
                name="password"
                rules={[{ required: true, message: '请输入密码' }]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block size="large">
                  登录
                </Button>
              </Form.Item>
              <div style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>
                默认管理员账号: admin / admin123
              </div>
            </Form>
          </Tabs.TabPane>

          <Tabs.TabPane tab="注册" key="register">
            {registerError && (
              <Alert
                message="注册失败"
                description={registerError}
                type="error"
                showIcon
                closable
                onClose={() => setRegisterError('')}
                style={{ marginBottom: 16 }}
              />
            )}
            <Form onFinish={onRegister} autoComplete="off">
              <Form.Item
                name="username"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="用户名" size="large" />
              </Form.Item>
              <Form.Item
                name="email"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱' }
                ]}
              >
                <Input prefix={<MailOutlined />} placeholder="邮箱" size="large" />
              </Form.Item>
              <Form.Item
                name="full_name"
              >
                <Input prefix={<UserOutlined />} placeholder="姓名（可选）" size="large" />
              </Form.Item>
              <Form.Item
                name="password"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6位' }
                ]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block size="large">
                  注册
                </Button>
              </Form.Item>
            </Form>
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

