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
  updateMilvusConfig: (data: {
    uri: string;
    user: string;
    password: string;
    token: string;
    db_name: string;
    collection_name: string
  }) => api.put('/system-config/milvus', data),

  // 模型配置
  getModelConfig: () => api.get('/system-config/model'),
  updateModelConfig: (data: { api_key: string; api_base: string; model_name: string }) =>
    api.put('/system-config/model', data),

  // Embedding 模型配置
  getEmbeddingConfig: () => api.get('/system-config/embedding'),
  updateEmbeddingConfig: (data: {
    embedding_model: string;
    embedding_api_key: string;
    embedding_api_base: string;
  }) => api.put('/system-config/embedding', data),

  // Prompt 配置
  getPromptConfig: () => api.get('/system-config/prompts'),
  updatePromptConfig: (data: {
    test_point_prompt: string;
    test_case_prompt: string;
    contract_test_case_prompt: string;
    preservation_test_case_prompt: string;
    claim_test_case_prompt: string;
  }) =>
    api.put('/system-config/prompts', data),

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
  download: (id: number, fileName?: string) => {
    const token = useAuthStore.getState().token
    const url = `/api/v1/requirements/${id}/download`

    return fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }).then(response => {
      if (!response.ok) {
        throw new Error('Download failed')
      }

      // 从响应头获取文件名
      let downloadFileName = fileName || 'document'
      const contentDisposition = response.headers.get('Content-Disposition')

      if (contentDisposition) {
        // 优先解析 RFC 5987 格式的 filename* (支持 UTF-8 编码)
        // 格式: filename*=UTF-8''%E6%96%B0%E4%BA%A7%E5%93%81.xlsx
        const filenameStarMatch = contentDisposition.match(/filename\*=UTF-8''(.+?)(?:;|$)/i)
        if (filenameStarMatch && filenameStarMatch[1]) {
          try {
            // URL 解码
            downloadFileName = decodeURIComponent(filenameStarMatch[1])
          } catch (e) {
            console.error('Failed to decode filename:', e)
          }
        } else {
          // 回退到标准 filename 参数
          const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (filenameMatch && filenameMatch[1]) {
            downloadFileName = filenameMatch[1].replace(/['"]/g, '')
          }
        }
      }

      return response.blob().then(blob => ({ blob, fileName: downloadFileName }))
    }).then(({ blob, fileName: downloadFileName }) => {
      const blobUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = downloadFileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(blobUrl)
    })
  },
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
  // 审批相关
  approve: (id: number, data: { approval_status: string; approval_comment?: string }) =>
    api.post(`/test-points/${id}/approve`, data),
  resetApproval: (id: number) => api.post(`/test-points/${id}/reset-approval`),
}

export const testCasesAPI = {
  list: (params?: any) => api.get('/test-cases/', { params }),
  get: (id: number) => api.get(`/test-cases/${id}`),
  create: (data: any) => api.post('/test-cases/', data),
  update: (id: number, data: any) => api.put(`/test-cases/${id}`, data),
  delete: (id: number) => api.delete(`/test-cases/${id}`),
  generate: (testPointId: number) => api.post(`/test-cases/generate/${testPointId}`),
  // 审批相关
  approve: (id: number, data: { approval_status: string; approval_comment?: string }) =>
    api.post(`/test-cases/${id}/approve`, data),
  resetApproval: (id: number) => api.post(`/test-cases/${id}/reset-approval`),
}

