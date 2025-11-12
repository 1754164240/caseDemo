import { useState, useEffect } from 'react'
import { Layout as AntLayout, Menu, Avatar, Dropdown } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  FileTextOutlined,
  CheckSquareOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BookOutlined,
  ApiOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../stores/authStore'
import { wsService } from '../services/websocket'

const { Header, Sider, Content } = AntLayout

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    // 连接 WebSocket
    if (user?.id) {
      wsService.connect(user.id)
    }

    return () => {
      wsService.disconnect()
    }
  }, [user?.id])

  // 根据用户权限动态生成菜单
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '首页',
    },
    {
      key: '/requirements',
      icon: <FileTextOutlined />,
      label: '需求管理',
    },
    {
      key: '/test-cases',
      icon: <CheckSquareOutlined />,
      label: '用例管理',
    },
    {
      key: '/knowledge-base',
      icon: <BookOutlined />,
      label: '知识问答',
    },
    // 只有管理员才能看到系统管理菜单
    ...(user?.is_superuser ? [
      {
        key: '/settings',
        icon: <SettingOutlined />,
        label: '系统管理',
      }
    ] : []),
  ]

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'profile') {
      navigate('/profile')
    } else if (key === 'logout') {
      logout()
      navigate('/login')
    }
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
    },
  ]

  return (
    <AntLayout style={{ height: '100vh', overflow: 'hidden' }}>
      {/* 左侧菜单 - 固定不滚动 */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: collapsed ? 16 : 18,
            fontWeight: 'bold',
          }}
        >
          {collapsed ? '测试' : '智能测试用例平台'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      {/* 右侧内容区域 - 添加左边距以避免被固定的 Sider 遮挡 */}
      <AntLayout style={{ marginLeft: collapsed ? 80 : 200, height: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* 顶部 Header - 固定 */}
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 1,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: 18, fontWeight: 500 }}>
            保险行业智能测试用例平台
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* 版本号 */}
            <span style={{ color: '#999', fontSize: 12 }}>v0.5.0</span>
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }} placement="bottomRight">
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.username}</span>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区域 - 可滚动 */}
        <Content style={{
          margin: '24px 16px',
          padding: 24,
          background: '#fff',
          overflow: 'auto',
          flex: 1
        }}>
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

