import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API 方法
export const authAPI = {
  login: (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData)
  },
  register: (data: any) => api.post('/auth/register', data),
  getMe: (token?: string) => {
    // 如果提供了 token，直接在 headers 中使用
    if (token) {
      return api.get('/users/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
    }
    return api.get('/users/me')
  },
}

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
}

// 系统配置 API
export const systemConfigAPI = {
  // Milvus 配置
  getMilvusConfig: () => api.get('/system-config/milvus'),
  updateMilvusConfig: (data: { host: string; port: number }) =>
    api.put('/system-config/milvus', data),

  // 模型配置
  getModelConfig: () => api.get('/system-config/model'),
  updateModelConfig: (data: { api_key: string; api_base: string; model_name: string }) =>
    api.put('/system-config/model', data),

  // 通用配置
  listConfigs: () => api.get('/system-config/'),
  createConfig: (data: any) => api.post('/system-config/', data),
  updateConfig: (id: number, data: any) => api.put(`/system-config/${id}`, data),
  deleteConfig: (id: number) => api.delete(`/system-config/${id}`),
}

export const requirementsAPI = {
  list: (params?: any) => api.get('/requirements/', { params }),
  get: (id: number) => api.get(`/requirements/${id}`),
  create: (formData: FormData) => api.post('/requirements/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  update: (id: number, data: any) => api.put(`/requirements/${id}`, data),
  delete: (id: number) => api.delete(`/requirements/${id}`),
}

export const testPointsAPI = {
  list: (params?: any) => api.get('/test-points/', { params }),
  get: (id: number) => api.get(`/test-points/${id}`),
  create: (data: any) => api.post('/test-points/', data),
  update: (id: number, data: any) => api.put(`/test-points/${id}`, data),
  delete: (id: number) => api.delete(`/test-points/${id}`),
  submitFeedback: (id: number, feedback: string) =>
    api.post(`/test-points/${id}/feedback`, null, { params: { feedback } }),
  regenerate: (requirementId: number, feedback?: string) =>
    api.post(`/test-points/regenerate/${requirementId}`, null, { params: { feedback } }),
}

export const testCasesAPI = {
  list: (params?: any) => api.get('/test-cases/', { params }),
  get: (id: number) => api.get(`/test-cases/${id}`),
  create: (data: any) => api.post('/test-cases/', data),
  update: (id: number, data: any) => api.put(`/test-cases/${id}`, data),
  delete: (id: number) => api.delete(`/test-cases/${id}`),
  generate: (testPointId: number) => api.post(`/test-cases/generate/${testPointId}`),
}

