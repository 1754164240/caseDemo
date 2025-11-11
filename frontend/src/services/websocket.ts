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
      // 触发数据刷新
      window.dispatchEvent(
        new CustomEvent('test-points-updated', {
          detail: data.requirement_id,
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
      // 触发数据刷新
      window.dispatchEvent(
        new CustomEvent('test-cases-updated', {
          detail: data.test_point_id,
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

