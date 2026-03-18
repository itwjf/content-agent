import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error.response?.data || error)
  }
)

// ==================== API 接口 ====================

// 健康检查
export const healthCheck = () => apiClient.get('/health')

// 测试 LLM
export const testLLM = (prompt) => apiClient.post('/llm/test', { prompt })

// Agent 决策
export const agentDecide = (data) => apiClient.post('/agent/decide', data)

// 合规检查
export const complianceCheck = (text) => apiClient.post('/compliance/check', { text })

// 商品管理
export const getProducts = () => apiClient.get('/products')
export const getProduct = (skuId) => apiClient.get(`/products/${skuId}`)
export const createProduct = (data) => apiClient.post('/products', data)
export const updateProduct = (skuId, data) => apiClient.put(`/products/${skuId}`, data)
export const deleteProduct = (skuId) => apiClient.delete(`/products/${skuId}`)

export default apiClient
