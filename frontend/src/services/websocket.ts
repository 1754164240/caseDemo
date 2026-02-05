import { message } from 'antd'

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimer: NodeJS.Timeout | null = null
  private userId: number | null = null
  private shouldReconnect = true

  connect(userId: number) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }
    this.userId = userId
    this.shouldReconnect = true
    const wsUrl = `ws://localhost:8000/api/v1/ws/notifications?token=${userId}`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.handleMessage(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      if (this.shouldReconnect) {
        this.reconnect()
      }
    }
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'test_points_generated': {
        const messageKey = data.requirement_id ? `requirement-${data.requirement_id}` : undefined
        if (messageKey) {
          message.success({ content: data.message, key: messageKey, duration: 3 })
        } else {
          message.success(data.message)
        }
        window.dispatchEvent(
          new CustomEvent('test-points-updated', {
            detail: data.requirement_id,
          })
        )
        window.dispatchEvent(
          new CustomEvent('test-points-ready', {
            detail: data.requirement_id,
          })
        )
        break
      }
      case 'test_points_failed': {
        const errorMessage = data.message || '重新生成测试点失败，请稍后重试'
        const messageKey = data.requirement_id ? `requirement-${data.requirement_id}` : undefined
        if (messageKey) {
          message.error({ content: errorMessage, key: messageKey, duration: 5 })
        } else {
          message.error(errorMessage)
        }
        window.dispatchEvent(
          new CustomEvent('test-points-failed', {
            detail: {
              requirement_id: data.requirement_id,
              error: errorMessage,
            },
          })
        )
        break
      }
      case 'test_cases_generated': {
        const messageKey = data.test_point_id ? `test-point-${data.test_point_id}` : undefined
        if (messageKey) {
          message.success({ content: data.message, key: messageKey, duration: 3 })
        } else {
          message.success(data.message)
        }
        window.dispatchEvent(
          new CustomEvent('test-cases-updated', {
            detail: data.test_point_id,
          })
        )
        break
      }
      // 工作流相关消息处理
      case 'workflow_started': {
        message.info({
          content: data.data?.message || '工作流已启动',
          duration: 3
        })
        window.dispatchEvent(
          new CustomEvent('workflow-started', {
            detail: data.data
          })
        )
        break
      }
      case 'workflow_need_review': {
        message.warning({
          content: data.data?.message || 'AI已生成测试数据，请进行人工审核',
          duration: 5
        })
        // 触发审核通知事件
        window.dispatchEvent(
          new CustomEvent('workflow-need-review', {
            detail: data.data
          })
        )
        break
      }
      case 'workflow_failed': {
        message.error({
          content: data.data?.error || '工作流执行失败',
          duration: 5
        })
        window.dispatchEvent(
          new CustomEvent('workflow-failed', {
            detail: data.data
          })
        )
        break
      }
      case 'workflow_error': {
        message.error({
          content: data.data?.message || '工作流执行异常',
          duration: 5
        })
        window.dispatchEvent(
          new CustomEvent('workflow-error', {
            detail: data.data
          })
        )
        break
      }
      case 'progress':
        message.info(data.message)
        break
      default:
        console.log('Unknown message type:', data.type)
    }
  }

  private reconnect() {
    if (!this.shouldReconnect) {
      return
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectTimer = setTimeout(() => {
      if (this.userId && this.shouldReconnect) {
        console.log('Reconnecting WebSocket...')
        this.connect(this.userId)
      }
    }, 3000)
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

export const wsService = new WebSocketService()
