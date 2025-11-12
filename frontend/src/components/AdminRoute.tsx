import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { Result, Button } from 'antd'
import { LockOutlined } from '@ant-design/icons'

interface AdminRouteProps {
  children: React.ReactNode
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const { user } = useAuthStore()

  // 如果不是管理员，显示无权限页面
  if (!user?.is_superuser) {
    return (
      <Result
        status="403"
        title="403"
        subTitle="抱歉，您没有权限访问此页面。"
        icon={<LockOutlined style={{ fontSize: 72, color: '#ff4d4f' }} />}
        extra={
          <Button type="primary" onClick={() => window.history.back()}>
            返回上一页
          </Button>
        }
      />
    )
  }

  return <>{children}</>
}

