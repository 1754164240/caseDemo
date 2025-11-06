import { message } from 'antd'

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimer: NodeJS.Timeout | null = null
  private userId: number | null = null

  connect(userId: number) {
    this.userId = userId
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
      this.reconnect()
    }
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'test_points_generated':
        message.success(data.message)
        // 触发数据刷新
        window.dispatchEvent(new CustomEvent('test-points-updated'))
        break
      case 'test_cases_generated':
        message.success(data.message)
        // 触发数据刷新
        window.dispatchEvent(new CustomEvent('test-cases-updated'))
        break
      case 'progress':
        message.info(data.message)
        break
      default:
        console.log('Unknown message type:', data.type)
    }
  }

  private reconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectTimer = setTimeout(() => {
      if (this.userId) {
        console.log('Reconnecting WebSocket...')
        this.connect(this.userId)
      }
    }, 3000)
  }

  disconnect() {
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

