/**
 * 直播场次 / 网关 / 指标策略 / 人工控制 API 封装
 */
import apiClient from './index'

// ==================== 直播场次 ====================
export const listSessions = (params) => apiClient.get('/live/sessions', { params })
export const createSession = (data) => apiClient.post('/live/sessions', data)
export const getSession = (sessionId) => apiClient.get(`/live/sessions/${sessionId}`)
export const startSession = (sessionId, data) => apiClient.post(`/live/sessions/${sessionId}/start`, data)
export const endSession = (sessionId) => apiClient.post(`/live/sessions/${sessionId}/end`)
export const updateSession = (sessionId, data) => apiClient.put(`/live/sessions/${sessionId}`, data)

// 历史回放（连接后补齐 / 页面刷新恢复）
export const replayDanmaku = (sessionId, params) => apiClient.get(`/live/sessions/${sessionId}/replay/danmaku`, { params })
export const replayDecisions = (sessionId, params) => apiClient.get(`/live/sessions/${sessionId}/replay/decisions`, { params })
export const sessionMetrics = (sessionId, params) => apiClient.get(`/live/sessions/${sessionId}/metrics`, { params })

// ==================== 接入网关（弹幕源） ====================
export const listAdapters = () => apiClient.get('/gateway/adapters')
export const startAdapter = (sessionId, adapterName, options = {}) =>
  apiClient.post(`/gateway/sessions/${sessionId}/start`, { adapter_name: adapterName, options })
export const stopAdapter = (sessionId) => apiClient.post(`/gateway/sessions/${sessionId}/stop`)

// ==================== 指标与策略 ====================
export const ingestMetrics = (sessionId, items) => apiClient.post(`/live/sessions/${sessionId}/metrics`, { items })
export const getStrategyWeights = (sessionId) => apiClient.get(`/live/sessions/${sessionId}/strategy/weights`)
export const resetStrategyWeights = (sessionId) => apiClient.post(`/live/sessions/${sessionId}/strategy/reset`)
export const listAdjustments = (sessionId) => apiClient.get(`/live/sessions/${sessionId}/strategy/adjustments`)

// ==================== 人工控制 ====================
export const getControlStatus = (sessionId) => apiClient.get(`/live/sessions/${sessionId}/control/status`)
export const takeover = (sessionId) => apiClient.post(`/live/sessions/${sessionId}/takeover`)
export const restoreAuto = (sessionId) => apiClient.post(`/live/sessions/${sessionId}/restore`)
export const sendManualScript = (sessionId, data) => apiClient.post(`/live/sessions/${sessionId}/manual-script`, data)
