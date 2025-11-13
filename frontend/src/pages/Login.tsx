import { useState, useEffect, useRef } from 'react'
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
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)

  // 鼠标移动效果
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        const x = (e.clientX - rect.left) / rect.width
        const y = (e.clientY - rect.top) / rect.height
        setMousePosition({ x, y })
      }
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

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
    <div
      ref={containerRef}
      style={{
        height: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
      }}>
      {/* 动态背景装饰 */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        overflow: 'hidden',
        zIndex: 0,
      }}>
        {/* 跟随鼠标的渐变光晕 */}
        <div style={{
          position: 'absolute',
          left: `${mousePosition.x * 100}%`,
          top: `${mousePosition.y * 100}%`,
          width: '600px',
          height: '600px',
          transform: 'translate(-50%, -50%)',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, transparent 70%)',
          filter: 'blur(60px)',
          transition: 'left 0.3s ease-out, top 0.3s ease-out',
          pointerEvents: 'none',
        }} />

        {/* 渐变圆形装饰 - 增强效果 */}
        <div style={{
          position: 'absolute',
          top: '-10%',
          right: '-5%',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, rgba(59, 130, 246, 0.2) 50%, transparent 70%)',
          filter: 'blur(40px)',
          animation: 'float 8s ease-in-out infinite',
          transform: `translate(${mousePosition.x * 20}px, ${mousePosition.y * 20}px)`,
          transition: 'transform 0.5s ease-out',
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-10%',
          left: '-5%',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.4) 0%, rgba(236, 72, 153, 0.2) 50%, transparent 70%)',
          filter: 'blur(40px)',
          animation: 'float 10s ease-in-out infinite reverse',
          transform: `translate(${-mousePosition.x * 30}px, ${-mousePosition.y * 30}px)`,
          transition: 'transform 0.5s ease-out',
        }} />
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: `translate(calc(-50% + ${mousePosition.x * 40}px), calc(-50% + ${mousePosition.y * 40}px))`,
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, rgba(139, 92, 246, 0.2) 50%, transparent 70%)',
          filter: 'blur(50px)',
          animation: 'pulse 6s ease-in-out infinite',
          transition: 'transform 0.5s ease-out',
        }} />

        {/* 粒子效果 */}
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${(i * 5) % 100}%`,
              top: `${(i * 7) % 100}%`,
              width: `${2 + (i % 3)}px`,
              height: `${2 + (i % 3)}px`,
              borderRadius: '50%',
              background: `rgba(${139 + i * 5}, ${92 + i * 8}, 246, ${0.3 + (i % 3) * 0.2})`,
              boxShadow: `0 0 ${10 + i * 2}px rgba(139, 92, 246, 0.5)`,
              animation: `particle${i % 3} ${5 + i % 5}s ease-in-out infinite`,
              transform: `translate(${mousePosition.x * (10 + i * 2)}px, ${mousePosition.y * (10 + i * 2)}px)`,
              transition: 'transform 0.3s ease-out',
            }}
          />
        ))}

        {/* 网格背景 - 增强效果 */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: `
            linear-gradient(rgba(139, 92, 246, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(139, 92, 246, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
          opacity: 0.6,
          transform: `perspective(500px) rotateX(${mousePosition.y * 2}deg) rotateY(${mousePosition.x * 2}deg)`,
          transition: 'transform 0.3s ease-out',
        }} />

        {/* 光线效果 */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: '200%',
          height: '2px',
          background: 'linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), transparent)',
          transform: `translate(-50%, -50%) rotate(${mousePosition.x * 180}deg)`,
          transition: 'transform 0.5s ease-out',
          animation: 'rotate 20s linear infinite',
        }} />
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: '200%',
          height: '2px',
          background: 'linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent)',
          transform: `translate(-50%, -50%) rotate(${90 + mousePosition.y * 180}deg)`,
          transition: 'transform 0.5s ease-out',
          animation: 'rotate 15s linear infinite reverse',
        }} />
      </div>

      {/* 添加动画样式 */}
      <style>{`
        @keyframes float {
          0%, 100% {
            transform: translateY(0) translateX(0);
          }
          50% {
            transform: translateY(-30px) translateX(30px);
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 0.3;
          }
          50% {
            opacity: 0.5;
          }
        }

        @keyframes rotate {
          from {
            transform: translate(-50%, -50%) rotate(0deg);
          }
          to {
            transform: translate(-50%, -50%) rotate(360deg);
          }
        }

        @keyframes particle0 {
          0%, 100% {
            transform: translateY(0) scale(1);
            opacity: 0.3;
          }
          50% {
            transform: translateY(-20px) scale(1.5);
            opacity: 0.8;
          }
        }

        @keyframes particle1 {
          0%, 100% {
            transform: translateX(0) scale(1);
            opacity: 0.4;
          }
          50% {
            transform: translateX(20px) scale(1.3);
            opacity: 0.9;
          }
        }

        @keyframes particle2 {
          0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.5;
          }
          50% {
            transform: translate(15px, -15px) scale(1.4);
            opacity: 1;
          }
        }

        .login-card {
          backdrop-filter: blur(20px) saturate(180%);
          background: rgba(255, 255, 255, 0.1) !important;
          box-shadow:
            0 8px 32px 0 rgba(139, 92, 246, 0.3),
            0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
          border: 1px solid rgba(255, 255, 255, 0.2) !important;
          transition: all 0.3s ease;
        }

        .login-card:hover {
          box-shadow:
            0 12px 48px 0 rgba(139, 92, 246, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.2) inset !important;
          transform: translateY(-5px);
        }

        .login-card .ant-card-head {
          background: transparent !important;
          border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important;
        }

        .login-card .ant-card-body {
          background: transparent !important;
        }

        .login-card .ant-tabs-tab {
          color: rgba(255, 255, 255, 0.7) !important;
        }

        .login-card .ant-tabs-tab-active {
          color: rgba(255, 255, 255, 1) !important;
        }

        .login-card .ant-tabs-ink-bar {
          background: linear-gradient(90deg, #667eea, #764ba2) !important;
        }

        .login-card .ant-form-item-label > label {
          color: rgba(255, 255, 255, 0.9) !important;
        }

        .login-card .ant-input,
        .login-card .ant-input-password,
        .login-card .ant-input-password input {
          background: rgba(255, 255, 255, 0.15) !important;
          border: 1px solid rgba(255, 255, 255, 0.3) !important;
          color: white !important;
        }

        .login-card .ant-input::placeholder {
          color: rgba(255, 255, 255, 0.6) !important;
        }

        .login-card .ant-input-password input::placeholder {
          color: rgba(255, 255, 255, 0.6) !important;
        }

        .login-card .ant-input-affix-wrapper {
          background: rgba(255, 255, 255, 0.15) !important;
          border: 1px solid rgba(255, 255, 255, 0.3) !important;
        }

        .login-card .ant-input-affix-wrapper input {
          background: transparent !important;
          color: white !important;
        }

        /* 修复浏览器自动填充的白色背景 */
        .login-card .ant-input:-webkit-autofill,
        .login-card .ant-input:-webkit-autofill:hover,
        .login-card .ant-input:-webkit-autofill:focus,
        .login-card .ant-input:-webkit-autofill:active,
        .login-card .ant-input-password input:-webkit-autofill,
        .login-card .ant-input-password input:-webkit-autofill:hover,
        .login-card .ant-input-password input:-webkit-autofill:focus,
        .login-card .ant-input-password input:-webkit-autofill:active {
          -webkit-box-shadow: 0 0 0 1000px rgba(255, 255, 255, 0.15) inset !important;
          -webkit-text-fill-color: white !important;
          box-shadow: 0 0 0 1000px rgba(255, 255, 255, 0.15) inset !important;
          transition: background-color 5000s ease-in-out 0s;
          caret-color: white !important;
        }

        .login-card .ant-input:hover,
        .login-card .ant-input-password:hover,
        .login-card .ant-input-affix-wrapper:hover {
          border-color: rgba(139, 92, 246, 0.6) !important;
          background: rgba(255, 255, 255, 0.2) !important;
        }

        .login-card .ant-input:focus,
        .login-card .ant-input-password:focus,
        .login-card .ant-input-focused,
        .login-card .ant-input-password-focused,
        .login-card .ant-input-affix-wrapper-focused {
          border-color: rgba(139, 92, 246, 0.8) !important;
          box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important;
          background: rgba(255, 255, 255, 0.2) !important;
        }

        .login-card .ant-btn-primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
          border: none !important;
          box-shadow: 0 4px 15px 0 rgba(139, 92, 246, 0.4) !important;
          transition: all 0.3s ease !important;
        }

        .login-card .ant-btn-primary:hover {
          transform: translateY(-2px) !important;
          box-shadow: 0 6px 20px 0 rgba(139, 92, 246, 0.6) !important;
        }

        .login-card .anticon {
          color: rgba(255, 255, 255, 0.8) !important;
        }

        .login-card .ant-input-prefix {
          color: rgba(255, 255, 255, 0.8) !important;
        }

        .login-card .ant-input-suffix {
          color: rgba(255, 255, 255, 0.8) !important;
        }

        .login-card .ant-alert {
          background: rgba(255, 77, 79, 0.15) !important;
          border: 1px solid rgba(255, 77, 79, 0.3) !important;
        }

        .login-card .ant-alert-message,
        .login-card .ant-alert-description {
          color: rgba(255, 255, 255, 0.95) !important;
        }
      `}</style>

      <Card
        className="login-card"
        style={{
          width: 420,
          position: 'relative',
          zIndex: 1,
        }}
        title={
          <div style={{
            textAlign: 'center',
            fontSize: 26,
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            textShadow: '0 0 30px rgba(168, 237, 234, 0.5)',
            letterSpacing: '2px',
          }}>
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

