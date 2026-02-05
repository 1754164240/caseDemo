import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 600000, // 增加到10分钟
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

  // 自动化测试平台配置
  getAutomationPlatformConfig: () => api.get('/system-config/automation-platform'),
  updateAutomationPlatformConfig: (data: { api_base: string; module_id: string }) =>
    api.put('/system-config/automation-platform', data),

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

// 模型配置 API (新的多模型配置)
export const modelConfigAPI = {
  // 获取所有模型配置列表
  list: (includeInactive?: boolean) =>
    api.get('/model-configs/', { params: { include_inactive: includeInactive } }),

  // 获取单个模型配置详情(包含完整 API Key)
  get: (id: number) => api.get(`/model-configs/${id}`),

  // 获取当前默认模型配置
  getDefault: () => api.get('/model-configs/default/current'),

  // 创建新模型配置
  create: (data: {
    name: string;
    display_name: string;
    description?: string;
    api_key: string;
    api_base: string;
    model_name: string;
    temperature?: string;
    max_tokens?: number;
    provider?: string;
    model_type?: string;
    is_active?: boolean;
  }) => api.post('/model-configs/', data),

  // 更新模型配置
  update: (id: number, data: {
    display_name?: string;
    description?: string;
    api_key?: string;
    api_base?: string;
    model_name?: string;
    temperature?: string;
    max_tokens?: number;
    provider?: string;
    model_type?: string;
    is_active?: boolean;
  }) => api.put(`/model-configs/${id}`, data),

  // 删除模型配置
  delete: (id: number) => api.delete(`/model-configs/${id}`),

  // 设置默认模型
  setDefault: (modelId: number) =>
    api.post('/model-configs/set-default', { model_id: modelId }),
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
  regenerate: (
    requirementId: number,
    params?: { feedback?: string; force?: boolean }
  ) => api.post(`/test-points/regenerate/${requirementId}`, null, { params: params || {} }),
  history: (id: number) => api.get(`/test-points/${id}/history`),
  historyVersions: (requirementId: number) =>
    api.get(`/test-points/history/requirements/${requirementId}`),
  historySnapshot: (requirementId: number, version: string) =>
    api.get(`/test-points/history/requirements/${requirementId}/${encodeURIComponent(version)}`),
  bulkUpdate: (data: {
    requirement_id: number
    updates: Array<{
      id: number
      title?: string
      description?: string
      category?: string
      priority?: string
      business_line?: string
    }>
  }) => api.post('/test-points/bulk-update', data),
  // 审批相关
  approve: (id: number, data: { approval_status: string; approval_comment?: string }) =>
    api.post(`/test-points/${id}/approve`, data),
  resetApproval: (id: number) => api.post(`/test-points/${id}/reset-approval`),
  historyVersionsByRequirement: (requirementId: number) =>
    api.get(`/test-points/history/requirements/${requirementId}`),
  historySnapshotByRequirement: (requirementId: number, version: string) =>
    api.get(`/test-points/history/requirements/${requirementId}/${version}`),
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
  generateAutomation: (testCaseId: number, moduleId?: string) =>
    api.post(`/test-cases/${testCaseId}/generate-automation`, moduleId ? { module_id: moduleId } : undefined),
  // 导出Excel
  exportExcel: (params?: { requirement_id?: number; test_point_id?: number }) => {
    const queryParams = new URLSearchParams()
    if (params?.requirement_id) queryParams.append('requirement_id', params.requirement_id.toString())
    if (params?.test_point_id) queryParams.append('test_point_id', params.test_point_id.toString())

    // 从 zustand store 获取 token
    const token = useAuthStore.getState().token

    return fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/test-cases/export/excel?${queryParams}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
  },
}

// 场景管理 API
export const scenariosAPI = {
  // 获取场景列表
  list: (params?: {
    skip?: number
    limit?: number
    search?: string
    business_line?: string
    channel?: string
    module?: string
    is_active?: boolean
  }) => api.get('/scenarios/', { params }),
  
  // 获取单个场景
  get: (id: number) => api.get(`/scenarios/${id}`),
  
  // 通过编号获取场景
  getByCode: (code: string) => api.get(`/scenarios/code/${code}`),
  
  // 创建场景
  create: (data: {
    scenario_code: string
    name: string
    description?: string
    business_line?: string
    channel?: string
    module?: string
    is_active?: boolean
  }) => api.post('/scenarios/', data),
  
  // 更新场景
  update: (id: number, data: {
    scenario_code?: string
    name?: string
    description?: string
    business_line?: string
    channel?: string
    module?: string
    is_active?: boolean
  }) => api.put(`/scenarios/${id}`, data),
  
  // 删除场景
  delete: (id: number) => api.delete(`/scenarios/${id}`),
  
  // 切换场景状态
  toggleStatus: (id: number) => api.post(`/scenarios/${id}/toggle-status`),
}

// 自动化工作流任务 API
export const workflowTasksAPI = {
  // 启动异步工作流
  start: (data: {
    test_case_id: number
    name?: string
    module_id?: string
    scene_id?: string
    scenario_type?: string
    description?: string
  }) => api.post('/automation/workflow/start', data),

  // 查询单个任务状态
  getTask: (taskId: number) => api.get(`/automation/workflow/tasks/${taskId}`),

  // 查询任务列表
  listTasks: (params?: {
    status?: 'pending' | 'processing' | 'reviewing' | 'completed' | 'failed'
    limit?: number
    offset?: number
  }) => api.get('/automation/workflow/tasks', { params }),

  // 提交人工审核
  submitReview: (threadId: string, data: {
    review_status: 'approved' | 'modified' | 'rejected'
    corrected_body?: any[]
    feedback?: string
  }) => api.post(`/automation/workflow/${threadId}/review`, data),

  // 查询工作流状态（LangGraph）
  getState: (threadId: string) => api.get(`/automation/workflow/${threadId}/state`),

  // 查询校验结果
  getValidation: (threadId: string) => api.get(`/automation/workflow/${threadId}/validation`),
}
