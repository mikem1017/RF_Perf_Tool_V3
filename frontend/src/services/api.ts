/**
 * API client service for backend communication.
 * 
 * All API calls go through this service to ensure consistent error handling
 * and to keep the frontend free of business logic.
 */
import axios, { AxiosInstance, AxiosError } from 'axios'

// API base URL - use /api since vite proxy forwards /api to backend
const API_BASE_URL = '/api'

/**
 * Create configured axios instance
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
})

/**
 * Error handler for API responses
 */
export function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>
    if (axiosError.response) {
      // Server responded with error status
      return axiosError.response.data?.detail || axiosError.response.statusText || 'Unknown error'
    } else if (axiosError.request) {
      // Request made but no response
      return 'No response from server. Is the backend running?'
    }
  }
  return 'An unexpected error occurred'
}

/**
 * Health check (separate from /api routes)
 */
export const healthCheck = async () => {
  const response = await axios.get('/health')
  return response.data
}

/**
 * API endpoints
 */
export const api = {

  // Devices
  devices: {
    list: () => apiClient.get('/devices').then(res => res.data),
    get: (id: number) => apiClient.get(`/devices/${id}`).then(res => res.data),
    create: (data: any) => apiClient.post('/devices', data).then(res => res.data),
    update: (id: number, data: any) => apiClient.put(`/devices/${id}`, data).then(res => res.data),
    delete: (id: number) => apiClient.delete(`/devices/${id}`).then(res => res.data),
  },

  // Test stages
  testStages: {
    list: () => apiClient.get('/test-stages').then(res => res.data),
    get: (id: number) => apiClient.get(`/test-stages/${id}`).then(res => res.data),
    create: (data: any) => apiClient.post('/test-stages', data).then(res => res.data),
    update: (id: number, data: any) => apiClient.put(`/test-stages/${id}`, data).then(res => res.data),
    delete: (id: number) => apiClient.delete(`/test-stages/${id}`).then(res => res.data),
  },

  // Requirement sets
  requirementSets: {
    list: () => apiClient.get('/requirement-sets').then(res => res.data),
    get: (id: number) => apiClient.get(`/requirement-sets/${id}`).then(res => res.data),
    create: (data: any) => apiClient.post('/requirement-sets', data).then(res => res.data),
    update: (id: number, data: any) => apiClient.put(`/requirement-sets/${id}`, data).then(res => res.data),
    delete: (id: number) => apiClient.delete(`/requirement-sets/${id}`).then(res => res.data),
  },

  // Test runs
  testRuns: {
    list: () => apiClient.get('/test-runs').then(res => res.data),
    get: (id: number) => apiClient.get(`/test-runs/${id}`).then(res => res.data),
    create: (data: any) => apiClient.post('/test-runs', data).then(res => res.data),
    upload: (id: number, files: File[]) => {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))
      return apiClient.post(`/test-runs/${id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(res => res.data)
    },
    process: (id: number) => apiClient.post(`/test-runs/${id}/process`).then(res => res.data),
    compliance: (id: number) => apiClient.get(`/test-runs/${id}/compliance`).then(res => res.data),
    plots: (id: number, plotType: string) => apiClient.get(`/test-runs/${id}/plots/${plotType}`, {
      responseType: 'blob',
    }).then(res => res.data),
    artifacts: (id: number) => apiClient.get(`/test-runs/${id}/artifacts`).then(res => res.data),
  },
}

export default apiClient

