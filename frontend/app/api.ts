const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface FileUploadResponse {
  success: boolean
  message: string
  file_id: string
  file_name: string
  file_size: number
  file_type: string
  upload_timestamp: string
}

export interface FileInfoResponse {
  file_id: string
  file_name: string
  file_size: number
  file_type: string
  upload_timestamp: string
  status: string
}

export interface AnalysisIssue {
  severity: "critical" | "high" | "medium" | "low"
  title: string
  description: string
  line_number?: number
  code_snippet?: string
  recommendation: string
  category?: string
}

export interface CategoryScoreBreakdown {
  score: number
  weight: number
  weighted_score: number
  issue_count: number
  severity_breakdown: Record<string, number>
}

export interface AnalysisResult {
  file_path: string
  file_name: string
  file_size: number
  analysis_timestamp: string
  analysis_duration: number
  overall_score: number
  score_breakdown: Record<string, CategoryScoreBreakdown>
  total_issues: number
  critical_issues: number
  high_issues: number
  issues: AnalysisIssue[]
  recommendations: string[]
  summary: string
}

export interface AnalysisResponse {
  success: boolean
  message: string
  analysis_result?: AnalysisResult
  error?: string
}

export interface AnalysisStatusResponse {
  file_id: string
  status: "pending" | "running" | "completed" | "failed"
  progress?: number
  estimated_completion?: string
  message: string
}

export interface APIStatusResponse {
  message: string
  version: string
  upload_endpoint: string
  analysis_endpoint: string
  supported_file_types: string[]
  max_file_size: string
}

export interface ErrorResponse {
  success: boolean
  error: string
  details?: string
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
    throw new ApiError(
      errorData.error || errorData.detail || `HTTP ${response.status}`,
      response.status,
      errorData
    )
  }
  return response.json()
}

export const api = {
  // Health check
  async health(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${API_BASE_URL}/health`)
    return handleResponse(response)
  },

  // API status
  async status(): Promise<APIStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/status`)
    return handleResponse(response)
  },

  // Upload file
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/api/v1/`, {
      method: 'POST',
      body: formData,
    })
    return handleResponse(response)
  },

  // Get file info
  async getFileInfo(fileId: string): Promise<FileInfoResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/${fileId}/info`)
    return handleResponse(response)
  },

  // Delete file
  async deleteFile(fileId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/${fileId}`, {
      method: 'DELETE',
    })
    return handleResponse(response)
  },

  // Analysis endpoints

  // Start analysis
  async startAnalysis(fileId: string): Promise<AnalysisResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze/${fileId}`, {
      method: 'POST',
    })
    return handleResponse(response)
  },

  // Get analysis status
  async getAnalysisStatus(fileId: string): Promise<AnalysisStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze/${fileId}/status`)
    return handleResponse(response)
  },

  // Get analysis result
  async getAnalysisResult(fileId: string): Promise<AnalysisResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze/${fileId}/result`)
    return handleResponse(response)
  },

  // Cancel analysis
  async cancelAnalysis(fileId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze/${fileId}`, {
      method: 'DELETE',
    })
    return handleResponse(response)
  },
} 