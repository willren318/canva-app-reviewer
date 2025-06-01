"use client"

import type React from "react"

import { useState, useEffect } from "react"
import {
  Upload,
  FileText,
  Zap,
  Eye,
  Code,
  Download,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  XCircle,
  Info,
  Play,
  Clock,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { 
  api, 
  ApiError, 
  type FileUploadResponse, 
  type FileInfoResponse, 
  type AnalysisResult,
  type AnalysisIssue,
  type AnalysisStatusResponse,
  type APIStatusResponse
} from "@/lib/api"

type AppState = "upload" | "processing" | "analysis" | "report" | "error"

interface Issue {
  id: string
  title: string
  severity: "critical" | "high" | "medium" | "low"
  description: string
  suggestion: string
  category: string
  guideline?: string
  codeSnippet?: string
}

// Extended interface for display purposes
interface DisplayIssue extends AnalysisIssue {
  id: string
  guideline?: string
}

const mockIssues: Issue[] = [
  {
    id: "1",
    title: "Low Contrast Text",
    severity: "high",
    description: "Text elements have insufficient color contrast ratio (2.1:1), making them difficult to read.",
    suggestion: "Increase contrast ratio to at least 4.5:1 for normal text and 3:1 for large text.",
    category: "ui-ux",
    guideline: "WCAG 2.1 AA",
    codeSnippet: "color: #999; /* Should be darker */",
  },
  {
    id: "2",
    title: "Use of eval()",
    severity: "critical",
    description: "The eval() function poses security risks and should be avoided.",
    suggestion: "Replace eval() with safer alternatives like JSON.parse() or Function constructor.",
    category: "security",
    codeSnippet: "eval(userInput); // Security risk",
  },
  {
    id: "3",
    title: "Missing Alt Text",
    severity: "medium",
    description: "Images are missing alternative text for screen readers.",
    suggestion: "Add descriptive alt attributes to all images.",
    category: "ui-ux",
    guideline: "WCAG 2.1 A",
  },
  {
    id: "4",
    title: "Inconsistent Button Styling",
    severity: "low",
    description: "Button styles vary across the interface, affecting visual consistency.",
    suggestion: "Standardize button styles using a design system or component library.",
    category: "ui-ux",
  },
  {
    id: "5",
    title: "Unused Variables",
    severity: "medium",
    description: "Several variables are declared but never used, affecting code cleanliness.",
    suggestion: "Remove unused variables or implement their intended functionality.",
    category: "code-quality",
    codeSnippet: "let unusedVar = 'example'; // Never used",
  },
  {
    id: "6",
    title: "Hardcoded API Keys",
    severity: "critical",
    description: "API keys are hardcoded in the source code, creating security vulnerabilities.",
    suggestion: "Move API keys to environment variables and use proper secret management.",
    category: "security",
    codeSnippet: "const apiKey = 'sk-1234567890'; // Security risk",
  },
]

const severityConfig = {
  critical: { color: "bg-red-100 text-red-800 border-red-200", icon: XCircle, iconColor: "text-red-500" },
  high: { color: "bg-orange-100 text-orange-800 border-orange-200", icon: AlertTriangle, iconColor: "text-orange-500" },
  medium: { color: "bg-yellow-100 text-yellow-800 border-yellow-200", icon: Info, iconColor: "text-yellow-500" },
  low: { color: "bg-blue-100 text-blue-800 border-blue-200", icon: AlertCircle, iconColor: "text-blue-500" },
}

const categoryScores = {
  security: 65,
  "code-quality": 88,
  "ui-ux": 92,
}

export default function CanvaAppReviewer() {
  const [currentState, setCurrentState] = useState<AppState>("upload")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadResponse, setUploadResponse] = useState<FileUploadResponse | null>(null)
  const [fileInfo, setFileInfo] = useState<FileInfoResponse | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [apiStatus, setApiStatus] = useState<APIStatusResponse | null>(null)
  
  // Analysis state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatusResponse | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)

  // Check API status on component mount
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const status = await api.status()
        setApiStatus(status)
      } catch (error) {
        console.warn('Failed to get API status:', error)
        // Fallback to default values
        setApiStatus({
          message: "API unavailable",
          version: "1.0.0",
          upload_endpoint: "Available - supports .js and .tsx files",
          analysis_endpoint: "Available - comprehensive 3-category analysis",
          supported_file_types: ['.js', '.tsx'],
          max_file_size: '10MB'
        })
      }
    }
    checkApiStatus()
  }, [])

  // Poll analysis status when analyzing
  useEffect(() => {
    let pollInterval: NodeJS.Timeout

    if (isAnalyzing && uploadResponse) {
      pollInterval = setInterval(async () => {
        try {
          const status = await api.getAnalysisStatus(uploadResponse.file_id)
          setAnalysisStatus(status)
          setAnalysisProgress(status.progress || 0)

          if (status.status === 'completed') {
            // Get the analysis result
            const result = await api.getAnalysisResult(uploadResponse.file_id)
            if (result.success && result.analysis_result) {
              setAnalysisResult(result.analysis_result)
              setCurrentState('report')
            } else {
              setError(result.error || 'Analysis completed but no results available')
              setCurrentState('error')
            }
            setIsAnalyzing(false)
          } else if (status.status === 'failed') {
            setError('Analysis failed: ' + status.message)
            setCurrentState('error')
            setIsAnalyzing(false)
          }
        } catch (error) {
          console.error('Failed to poll analysis status:', error)
          if (error instanceof ApiError) {
            setError(error.message)
          } else {
            setError('Failed to check analysis status')
          }
          setCurrentState('error')
          setIsAnalyzing(false)
        }
      }, 2000) // Poll every 2 seconds
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [isAnalyzing, uploadResponse])

  // Calculate overall score from analysis result or fallback to mock data
  const overallScore = analysisResult ? analysisResult.overall_score : Math.round(
    Object.values(categoryScores).reduce((a, b) => a + b, 0) / Object.values(categoryScores).length,
  )

  // Get category scores from analysis result or fallback to mock data
  const getCategoryScores = () => {
    if (analysisResult) {
      return {
        security: analysisResult.score_breakdown.security?.score || 0,
        "code-quality": analysisResult.score_breakdown.code_quality?.score || 0,
        "ui-ux": analysisResult.score_breakdown.ui_ux?.score || 0,
      }
    }
    return categoryScores
  }

  // Get issues from analysis result or fallback to mock data
  const getIssues = (): DisplayIssue[] => {
    if (analysisResult) {
      return analysisResult.issues.map((issue, index) => ({
        ...issue,
        id: `${analysisResult.file_name}-${index}`,
        guideline: undefined, // Analysis results don't include guidelines
        // Map backend category names to frontend format
        category: issue.category === 'code_quality' ? 'code-quality' : 
                 issue.category === 'ui_ux' ? 'ui-ux' : 
                 issue.category || 'general'
      }))
    }
    return mockIssues.map(issue => ({
      severity: issue.severity,
      title: issue.title,
      description: issue.description,
      recommendation: issue.suggestion,
      category: issue.category,
      code_snippet: issue.codeSnippet,
      id: issue.id,
      guideline: issue.guideline,
    }))
  }

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file)
    setIsUploading(true)
    setError(null)
    setUploadProgress(0)

    try {
      // Validate file before upload
      if (apiStatus) {
        const maxSizeMatch = apiStatus.max_file_size.match(/(\d+)/)
        const maxSizeMB = maxSizeMatch ? parseInt(maxSizeMatch[1]) : 10
        const maxSizeBytes = maxSizeMB * 1024 * 1024
        
        if (file.size > maxSizeBytes) {
          throw new Error(`File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds the maximum limit of ${maxSizeMB}MB`)
        }

        const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
        if (!apiStatus.supported_file_types.includes(fileExtension)) {
          throw new Error(`File type ${fileExtension} is not supported. Supported types: ${apiStatus.supported_file_types.join(', ')}`)
        }
      }

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const response = await api.uploadFile(file)
      setUploadResponse(response)
      setUploadProgress(100)
      
      // Get detailed file info
      const info = await api.getFileInfo(response.file_id)
      setFileInfo(info)
      
      clearInterval(progressInterval)
      setCurrentState("processing")
      
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message)
      } else {
        setError(error instanceof Error ? error.message : 'An unknown error occurred')
      }
      setCurrentState("error")
    } finally {
      setIsUploading(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const startAnalysis = async () => {
    if (!uploadResponse) {
      setError('No file uploaded')
      setCurrentState("error")
      return
    }
    
    try {
      setIsAnalyzing(true)
      setAnalysisProgress(0)
      setCurrentState("analysis")
      
      // Start the analysis
      const response = await api.startAnalysis(uploadResponse.file_id)
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to start analysis')
      }
      
      // Analysis will continue in the background with polling
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message)
      } else {
        setError(error instanceof Error ? error.message : 'Failed to start analysis')
      }
      setCurrentState("error")
      setIsAnalyzing(false)
    }
  }

  const resetToUpload = () => {
    setCurrentState("upload")
    setUploadedFile(null)
    setUploadResponse(null)
    setFileInfo(null)
    setAnalysisResult(null)
    setAnalysisStatus(null)
    setError(null)
    setUploadProgress(0)
    setAnalysisProgress(0)
    setIsUploading(false)
    setIsAnalyzing(false)
  }

  const downloadReport = () => {
    const issues = getIssues()
    const categoryScores = getCategoryScores()
    const currentDate = new Date().toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
    
    const fileName = analysisResult?.file_name || uploadedFile?.name || 'canva-app'
    
    // Function to escape HTML content for display as text
    const escapeHtml = (text: string) => {
      const div = document.createElement('div')
      div.textContent = text
      return div.innerHTML
    }
    
    // Generate HTML report content
    const reportHTML = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canva App Analysis Report - ${fileName}</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            color: #374151;
            background: #ffffff;
        }
        .header { 
            text-align: center; 
            border-bottom: 3px solid #3B82F6; 
            padding-bottom: 20px; 
            margin-bottom: 30px;
        }
        .score-circle { 
            display: inline-block; 
            width: 80px; 
            height: 80px; 
            border-radius: 50%; 
            background: linear-gradient(135deg, #3B82F6, #8B5CF6);
            color: white; 
            text-align: center; 
            line-height: 80px; 
            font-size: 24px; 
            font-weight: bold;
            margin: 10px;
        }
        .category-score { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 12px; 
            margin: 8px 0; 
            background: #F3F4F6; 
            border-radius: 8px;
            clear: both;
        }
        .issue { 
            border: 1px solid #E5E7EB; 
            border-radius: 8px; 
            margin: 20px 0; 
            padding: 20px;
            clear: both;
            overflow: hidden;
        }
        .issue-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: flex-start; 
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .issue-title {
            flex: 1;
            min-width: 200px;
        }
        .severity-critical { background: #FEF2F2; border-left: 4px solid #EF4444; }
        .severity-high { background: #FFFBEB; border-left: 4px solid #F59E0B; }
        .severity-medium { background: #FEFCE8; border-left: 4px solid #EAB308; }
        .severity-low { background: #EFF6FF; border-left: 4px solid #3B82F6; }
        .severity-badge { 
            padding: 6px 12px; 
            border-radius: 20px; 
            font-size: 11px; 
            font-weight: bold;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .badge-critical { background: #FEE2E2; color: #991B1B; }
        .badge-high { background: #FED7AA; color: #C2410C; }
        .badge-medium { background: #FEF3C7; color: #A16207; }
        .badge-low { background: #DBEAFE; color: #1D4ED8; }
        .code-block { 
            background: #F9FAFB; 
            border: 1px solid #E5E7EB; 
            border-radius: 6px; 
            padding: 15px; 
            font-family: 'Monaco', 'Courier New', monospace; 
            font-size: 13px;
            margin: 12px 0;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .code-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-weight: 600;
            color: #374151;
        }
        .suggestion { 
            background: #F0FDF4; 
            border: 1px solid #BBF7D0; 
            border-radius: 6px; 
            padding: 15px; 
            margin: 12px 0;
        }
        .suggestion-header {
            font-weight: 600;
            color: #166534;
            margin-bottom: 8px;
        }
        .recommendation-list { 
            background: #F8FAFC; 
            border-radius: 8px; 
            padding: 16px; 
            margin: 16px 0;
        }
        .recommendation-list ul { 
            margin: 8px 0; 
            padding-left: 20px;
        }
        .recommendation-list li { 
            margin: 8px 0;
        }
        .stats-grid {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .stat-item {
            text-align: center;
            padding: 10px;
        }
        .stat-number {
            font-size: 18px;
            font-weight: bold;
        }
        .stat-label {
            font-size: 11px;
            color: #6B7280;
            margin-top: 2px;
        }
        h1, h2, h3, h4 { 
            color: #1F2937; 
            margin-top: 0;
        }
        h3 {
            border-bottom: 1px solid #E5E7EB;
            padding-bottom: 8px;
            margin-top: 30px;
        }
        .section { 
            margin: 40px 0; 
            clear: both;
        }
        .clearfix::after {
            content: "";
            display: table;
            clear: both;
        }
        @media print {
            body { margin: 0; padding: 15px; }
            .issue { break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ Canva App Analysis Report</h1>
        <h2>${fileName}</h2>
        <p><strong>Generated:</strong> ${currentDate}</p>
        ${analysisResult ? `<p><strong>Analysis Duration:</strong> ${analysisResult.analysis_duration}s</p>` : ''}
    </div>

    <div class="section">
        <h2>📊 Overall Assessment</h2>
        <div style="text-align: center;">
            <div class="score-circle">${overallScore}</div>
            <p><strong>Canva-Ready Score: ${overallScore}/100</strong></p>
        </div>
        <p>${analysisResult?.summary || "Your Canva app demonstrates solid code quality and performance with a modern, user-friendly interface. The main areas for improvement focus on accessibility compliance and design consistency."}</p>
        
        ${analysisResult ? `
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-number" style="color: #EF4444;">${analysisResult.critical_issues}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" style="color: #F59E0B;">${analysisResult.high_issues}</div>
                <div class="stat-label">High</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" style="color: #EAB308;">${analysisResult.issues.filter(issue => issue.severity === 'medium').length}</div>
                <div class="stat-label">Medium</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" style="color: #3B82F6;">${analysisResult.issues.filter(issue => issue.severity === 'low').length}</div>
                <div class="stat-label">Low</div>
            </div>
            <div class="stat-item" style="border-left: 2px solid #E5E7EB; padding-left: 20px; margin-left: 10px;">
                <div class="stat-number" style="color: #1F2937;">${analysisResult.total_issues}</div>
                <div class="stat-label">Total Issues</div>
            </div>
        </div>
        ` : ''}
    </div>

    <div class="section">
        <h2>📈 Category Breakdown</h2>
        ${Object.entries(categoryScores).map(([category, score]) => {
          const categoryDisplayName = category === "code-quality" ? "Code Quality" : 
                                    category === "ui-ux" ? "UI & UX" : 
                                    category.charAt(0).toUpperCase() + category.slice(1)
          const backendCategoryName = category === "code-quality" ? "code_quality" : 
                                    category === "ui-ux" ? "ui_ux" : category
          const issueCount = analysisResult?.score_breakdown[backendCategoryName]?.issue_count || 0
          
          return `
            <div class="category-score">
                <div>
                    <strong>${categoryDisplayName}</strong>
                    ${analysisResult ? `<span style="color: #6B7280; font-size: 14px;"> (${issueCount} issues)</span>` : ''}
                </div>
                <div style="font-size: 18px; font-weight: bold; color: #3B82F6;">${score}/100</div>
            </div>
          `
        }).join('')}
    </div>

    ${analysisResult?.recommendations && analysisResult.recommendations.length > 0 ? `
    <div class="section">
        <h2>💡 Key Recommendations</h2>
        <div class="recommendation-list">
            <ul>
                ${analysisResult.recommendations.slice(0, 5).map(rec => {
                  const isIndentedItem = rec.startsWith('   ') && rec.trim().match(/^\d+\./)
                  if (isIndentedItem) {
                    return `<li style="margin-left: 20px; list-style-type: decimal;">${escapeHtml(rec.trim().replace(/^\d+\.\s*/, ''))}</li>`
                  } else {
                    return `<li>${escapeHtml(rec)}</li>`
                  }
                }).join('')}
            </ul>
        </div>
    </div>
    ` : ''}

    <div class="section">
        <h2>🔍 Detailed Findings</h2>
        
        <h3>📋 All Issues Summary</h3>
        <p><strong>Total Issues Found:</strong> ${issues.length}</p>
        
        ${['critical', 'high', 'medium', 'low'].map(severity => {
          const severityIssues = issues.filter(issue => issue.severity === severity)
          if (severityIssues.length === 0) return ''
          
          return `
            <h3>${severity.charAt(0).toUpperCase() + severity.slice(1)} Priority Issues (${severityIssues.length})</h3>
            ${severityIssues.map(issue => `
              <div class="issue severity-${severity} clearfix">
                <div class="issue-header">
                    <h4 class="issue-title">${escapeHtml(issue.title)}</h4>
                    <span class="severity-badge badge-${severity}">${severity}</span>
                </div>
                <p>${escapeHtml(issue.description)}</p>
                ${issue.code_snippet ? `
                    <div>
                        <div class="code-header">
                            🔍 Issue Found Here:
                        </div>
                        <div class="code-block">${escapeHtml(issue.code_snippet)}</div>
                    </div>
                ` : ''}
                <div class="suggestion">
                    <div class="suggestion-header">💡 Suggestion:</div>
                    <div>${escapeHtml(issue.recommendation)}</div>
                </div>
                ${issue.guideline ? `<p><strong>📖 Guideline:</strong> ${escapeHtml(issue.guideline)}</p>` : ''}
              </div>
            `).join('')}
          `
        }).join('')}

        ${['security', 'code-quality', 'ui-ux'].map(category => {
          const categoryIssues = issues.filter(issue => issue.category === category)
          const categoryDisplayName = category === "code-quality" ? "Code Quality" : 
                                    category === "ui-ux" ? "UI & UX" : 
                                    category.charAt(0).toUpperCase() + category.slice(1)
          
          if (categoryIssues.length === 0) return `<h3>${categoryDisplayName} Issues</h3><p>✅ No issues found in this category.</p>`
          
          return `
            <h3>${categoryDisplayName} Issues (${categoryIssues.length})</h3>
            ${categoryIssues.map(issue => `
              <div class="issue severity-${issue.severity} clearfix">
                <div class="issue-header">
                    <h4 class="issue-title">${escapeHtml(issue.title)}</h4>
                    <span class="severity-badge badge-${issue.severity}">${issue.severity}</span>
                </div>
                <p>${escapeHtml(issue.description)}</p>
                ${issue.code_snippet ? `
                    <div>
                        <div class="code-header">
                            🔍 Issue Found Here:
                        </div>
                        <div class="code-block">${escapeHtml(issue.code_snippet)}</div>
                    </div>
                ` : ''}
                <div class="suggestion">
                    <div class="suggestion-header">💡 Suggestion:</div>
                    <div>${escapeHtml(issue.recommendation)}</div>
                </div>
                ${issue.guideline ? `<p><strong>📖 Guideline:</strong> ${escapeHtml(issue.guideline)}</p>` : ''}
              </div>
            `).join('')}
          `
        }).join('')}
    </div>

    <div class="section" style="text-align: center; border-top: 2px solid #E5E7EB; padding-top: 20px; margin-top: 40px;">
        <p style="color: #6B7280; font-size: 14px;">
            Generated by Canva App Reviewer • ${currentDate}<br>
            MIT Licensed • This prototype is not affiliated with Canva
        </p>
    </div>
</body>
</html>`

    // Create and download the HTML file
    const blob = new Blob([reportHTML], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `canva-app-analysis-${fileName.replace(/\.[^/.]+$/, '')}-${new Date().toISOString().split('T')[0]}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const CircularProgress = ({ value, size = 120 }: { value: number; size?: number }) => {
    const radius = (size - 8) / 2
    const circumference = radius * 2 * Math.PI
    const strokeDasharray = circumference
    const strokeDashoffset = circumference - (value / 100) * circumference

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} stroke="#E5E7EB" strokeWidth="8" fill="transparent" />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="url(#gradient)"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0052CC" />
              <stop offset="100%" stopColor="#8270FF" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-3xl font-bold text-gray-800">{value}</span>
        </div>
      </div>
    )
  }

  if (currentState === "error") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center space-y-8 max-w-md mx-auto px-4">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto">
            <XCircle className="w-12 h-12 text-red-600" />
          </div>

          <div className="space-y-4">
            <h2 className="text-3xl font-bold text-gray-800">Upload Failed</h2>
            <p className="text-lg text-gray-600">{error}</p>
          </div>

          <div className="space-y-4">
            <Button
              onClick={resetToUpload}
              size="lg"
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg"
            >
              <RotateCcw className="w-5 h-5 mr-2" />
              Try Again
            </Button>
          </div>

          <div className="text-sm text-gray-500">
            If the problem persists, please check your file format and size.
          </div>
        </div>
      </div>
    )
  }

  if (currentState === "upload") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-800">Canva App Reviewer</h1>
            </div>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Upload your Canva app and get an instant audit report with actionable insights to improve quality,
              accessibility, and user experience.
            </p>
          </div>

          {/* Upload Area */}
          <div className="max-w-2xl mx-auto">
            <Card className="border-2 border-dashed border-gray-300 hover:border-blue-400 transition-colors duration-200">
              <CardContent className="p-12">
                <div
                  className={`text-center ${isDragOver ? "bg-blue-50" : ""} rounded-lg p-8 transition-colors duration-200`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Upload className="w-8 h-8 text-blue-600" />
                  </div>

                  {uploadedFile ? (
                    <div className="space-y-4">
                      {isUploading ? (
                        <div className="space-y-3">
                          <div className="flex items-center justify-center gap-2 text-blue-600">
                            <Upload className="w-5 h-5 animate-pulse" />
                            <span className="font-medium">Uploading {uploadedFile.name}...</span>
                          </div>
                          <Progress value={uploadProgress} className="h-2" />
                          <p className="text-sm text-gray-500">{uploadProgress}% complete</p>
                        </div>
                      ) : uploadResponse ? (
                        <div className="space-y-3">
                          <div className="flex items-center justify-center gap-2 text-green-600">
                            <CheckCircle className="w-5 h-5" />
                            <span className="font-medium">{uploadResponse.file_name}</span>
                          </div>
                          <div className="text-sm text-gray-600 space-y-1">
                            <p>Size: {(uploadResponse.file_size / 1024).toFixed(1)} KB</p>
                            <p>Type: {uploadResponse.file_type}</p>
                          </div>
                          <p className="text-green-600 font-medium">File ready for analysis</p>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center gap-2 text-green-600">
                          <FileText className="w-5 h-5" />
                          <span className="font-medium">{uploadedFile.name}</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <h3 className="text-xl font-semibold text-gray-800">Drop your app here</h3>
                      <p className="text-gray-600">or click to browse files</p>
                      <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
                        <span>Supported formats:</span>
                        {apiStatus ? (
                          apiStatus.supported_file_types.map((type) => (
                            <Badge key={type} variant="outline">{type}</Badge>
                          ))
                        ) : (
                          <>
                            <Badge variant="outline">.js</Badge>
                            <Badge variant="outline">.tsx</Badge>
                          </>
                        )}
                      </div>
                      {apiStatus && (
                        <p className="text-xs text-gray-400">
                          Maximum file size: {apiStatus.max_file_size}
                        </p>
                      )}
                    </div>
                  )}

                  <input
                    type="file"
                    accept={apiStatus ? apiStatus.supported_file_types.join(',') : '.js,.tsx'}
                    onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                    className="hidden"
                    id="file-upload"
                    disabled={isUploading}
                  />
                  <label
                    htmlFor="file-upload"
                    className={`inline-block mt-6 px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg cursor-pointer hover:from-blue-700 hover:to-purple-700 transition-all duration-200 transform hover:scale-105 ${
                      isUploading ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {isUploading ? 'Uploading...' : 'Choose File'}
                  </label>
                </div>
              </CardContent>
            </Card>

            {uploadResponse && !isUploading && (
              <div className="mt-8 text-center">
                <Button
                  onClick={startAnalysis}
                  size="lg"
                  className="px-12 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transform hover:scale-105 transition-all duration-200"
                >
                  <Zap className="w-5 h-5 mr-2" />
                  Analyze App
                </Button>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="text-center mt-16 text-sm text-gray-500">
            MIT Licensed. This prototype is not affiliated with Canva.
          </div>
        </div>
      </div>
    )
  }

  if (currentState === "processing") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center space-y-8 max-w-md mx-auto px-4">
          <div className="w-24 h-24 bg-gradient-to-r from-green-600 to-blue-600 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle className="w-12 h-12 text-white" />
          </div>

          <div className="space-y-4">
            <h2 className="text-3xl font-bold text-gray-800">File Ready!</h2>
            <p className="text-lg text-gray-600">Your file has been successfully processed and validated ✅</p>
          </div>

          {fileInfo && (
            <div className="bg-white rounded-lg p-6 shadow-lg border border-gray-200 text-left">
              <h3 className="font-semibold text-gray-800 mb-3">File Details:</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <p><span className="font-medium">Name:</span> {fileInfo.file_name}</p>
                <p><span className="font-medium">Size:</span> {(fileInfo.file_size / 1024).toFixed(1)} KB</p>
                <p><span className="font-medium">Type:</span> {fileInfo.file_type}</p>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <p className="text-gray-600">Ready to analyze your Canva app!</p>
            <Button
              onClick={startAnalysis}
              size="lg"
              className="w-full px-12 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transform hover:scale-105 transition-all duration-200 shadow-lg"
            >
              <Zap className="w-5 h-5 mr-2" />
              Start Analysis
            </Button>
            <p className="text-sm text-gray-500">This will run a comprehensive analysis of your code</p>
          </div>

          <div className="text-center">
            <Button
              onClick={resetToUpload}
              variant="outline"
              className="border-gray-300 text-gray-600 hover:bg-gray-50"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Upload Different File
            </Button>
          </div>
        </div>
      </div>
    )
  }

  if (currentState === "analysis") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center space-y-8 max-w-lg mx-auto px-4">
          <div className="w-24 h-24 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto animate-pulse">
            <Zap className="w-12 h-12 text-white" />
          </div>

          <div className="space-y-4">
            <h2 className="text-3xl font-bold text-gray-800">Analyzing your app...</h2>
            <p className="text-lg text-gray-600">
              {analysisStatus?.message || "Running comprehensive analysis..."}
            </p>
          </div>

          <div className="w-80 mx-auto space-y-4">
            <Progress value={analysisProgress} className="h-3" />
            <p className="text-sm text-gray-500">{analysisProgress}% complete</p>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-6 shadow-lg border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Analysis Components</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center space-y-2">
                <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center mx-auto">
                  <span className="text-red-600">🔒</span>
                </div>
                <div className="text-gray-700 font-medium">Security</div>
                <div className="text-xs text-gray-500">Vulnerabilities & threats</div>
              </div>
              <div className="text-center space-y-2">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                  <span className="text-blue-600">🎯</span>
                </div>
                <div className="text-gray-700 font-medium">Code Quality</div>
                <div className="text-xs text-gray-500">Best practices & structure</div>
              </div>
              <div className="text-center space-y-2">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mx-auto">
                  <span className="text-purple-600">🎨</span>
                </div>
                <div className="text-gray-700 font-medium">UI/UX</div>
                <div className="text-xs text-gray-500">Design & accessibility</div>
              </div>
            </div>
            <div className="mt-4 text-xs text-gray-500 text-center">
              All components analyzed in parallel • Powered by Claude AI
            </div>
          </div>

          {analysisStatus?.status === 'failed' && (
            <div className="mt-8">
              <Button
                onClick={resetToUpload}
                variant="outline"
                className="border-red-200 text-red-600 hover:bg-red-50"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-800">Canva App Reviewer</h1>
          </div>
          <Button onClick={resetToUpload} variant="outline" className="border-blue-200 text-blue-600 hover:bg-blue-50">
            <RotateCcw className="w-4 h-4 mr-2" />
            New Analysis
          </Button>
        </div>

        {/* Summary Section */}
        <div className="grid lg:grid-cols-3 gap-8 mb-12">
          {/* Main Score */}
          <Card className="lg:col-span-1 text-center p-8 bg-white shadow-lg border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-2xl font-bold text-gray-800">Canva-Ready Score</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex justify-center">
                <CircularProgress value={overallScore} />
              </div>
              <div className="space-y-2">
                <p className="text-lg font-semibold text-gray-700">
                  {overallScore >= 90 ? "Excellent work!" : 
                   overallScore >= 80 ? "Great work!" :
                   overallScore >= 60 ? "Good progress!" :
                   "Needs improvement"}
                </p>
                <p className="text-sm text-gray-600">
                  {analysisResult ? 
                    `Analysis completed in ${analysisResult.analysis_duration}s with ${analysisResult.total_issues} total issues found.` :
                    "Your app shows strong potential with room for improvement in accessibility."
                  }
                </p>
                
                {/* Analysis Statistics */}
                {analysisResult && (
                  <div className="flex justify-center gap-3 mt-4 text-xs flex-wrap">
                    <div className="text-center">
                      <div className="font-bold text-red-600">{analysisResult.critical_issues}</div>
                      <div className="text-gray-500">Critical</div>
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-orange-600">{analysisResult.high_issues}</div>
                      <div className="text-gray-500">High</div>
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-yellow-600">{analysisResult.issues.filter(issue => issue.severity === 'medium').length}</div>
                      <div className="text-gray-500">Medium</div>
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-blue-600">{analysisResult.issues.filter(issue => issue.severity === 'low').length}</div>
                      <div className="text-gray-500">Low</div>
                    </div>
                    <div className="text-center border-l border-gray-300 pl-3 ml-3">
                      <div className="font-bold text-gray-800">{analysisResult.total_issues}</div>
                      <div className="text-gray-500">Total</div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Sub-scores */}
          <Card className="lg:col-span-2 p-8 bg-white shadow-lg border-0">
            <CardHeader className="pb-6">
              <CardTitle className="text-xl font-bold text-gray-800">Category Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Object.entries(getCategoryScores()).map(([category, score]) => {
                  // Determine color based on category
                  let barColor = ""
                  let categoryDisplayName = ""
                  if (category === "security") {
                    barColor = "bg-red-500"
                    categoryDisplayName = "Security"
                  } else if (category === "code-quality") {
                    barColor = "bg-blue-500"
                    categoryDisplayName = "Code Quality"
                  } else if (category === "ui-ux") {
                    barColor = "bg-purple-500"
                    categoryDisplayName = "UI & UX"
                  }

                  // Get issue count for this category from analysis result
                  const backendCategoryName = category === "code-quality" ? "code_quality" : 
                                            category === "ui-ux" ? "ui_ux" : category
                  const issueCount = analysisResult?.score_breakdown[backendCategoryName]?.issue_count || 0
                  const severityBreakdown = analysisResult?.score_breakdown[backendCategoryName]?.severity_breakdown

                  return (
                    <div key={category} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-medium text-gray-800">
                            {categoryDisplayName}
                          </span>
                          {analysisResult && severityBreakdown && (
                            <div className="flex gap-1 text-xs flex-wrap">
                              {(severityBreakdown.critical !== undefined) && (
                                <span className="bg-red-100 text-red-700 px-2 py-1 rounded">
                                  {severityBreakdown.critical} critical
                                </span>
                              )}
                              {(severityBreakdown.high !== undefined) && (
                                <span className="bg-orange-100 text-orange-700 px-2 py-1 rounded">
                                  {severityBreakdown.high} high
                                </span>
                              )}
                              {(severityBreakdown.medium !== undefined) && (
                                <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded">
                                  {severityBreakdown.medium} medium
                                </span>
                              )}
                              {(severityBreakdown.low !== undefined) && (
                                <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                  {severityBreakdown.low} low
                                </span>
                              )}
                              {issueCount === 0 && !severityBreakdown && (
                                <span className="bg-green-100 text-green-700 px-2 py-1 rounded">
                                  No issues
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          <span className="text-xl font-bold text-blue-600">{score}</span>
                          {analysisResult && (
                            <div className="text-xs text-gray-500">{issueCount} issues</div>
                          )}
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-4">
                        <div
                          className={`${barColor} h-4 rounded-full transition-all duration-1000 ease-out`}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Summary Card */}
        <Card className="mb-8 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Eye className="w-6 h-6 text-white" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-gray-800">Overall Assessment</h3>
                <p className="text-gray-700 leading-relaxed">
                  {analysisResult?.summary || 
                   "Your Canva app demonstrates solid code quality and performance with a modern, user-friendly interface. The main areas for improvement focus on accessibility compliance and design consistency."}
                </p>
              </div>
            </div>
            
            {/* Recommendations Section */}
            {analysisResult?.recommendations && analysisResult.recommendations.length > 0 && (
              <div className="mt-6 bg-white/60 rounded-lg p-4">
                <h4 className="text-md font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  💡 Key Recommendations
                </h4>
                <ul className="space-y-2">
                  {analysisResult.recommendations.slice(0, 5).map((recommendation, index) => {
                    // Check if this is a numbered sub-item (starts with whitespace and number)
                    const isNumberedItem = recommendation.trim().match(/^\d+\./)
                    const isIndentedItem = recommendation.startsWith('   ')
                    
                    if (isIndentedItem && isNumberedItem) {
                      // This is a numbered sub-item, display without bullet and with indentation
                      return (
                        <li key={index} className="text-sm text-gray-700 ml-4">
                          <span>{recommendation.trim()}</span>
                        </li>
                      )
                    } else {
                      // Regular recommendation item with bullet
                      return (
                        <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                          <span className="text-blue-600 font-bold">•</span>
                          <span>{recommendation}</span>
                        </li>
                      )
                    }
                  })}
                </ul>
              </div>
            )}
            
            <div className="mt-6">
              <Button variant="outline" className="border-blue-300 text-blue-700 hover:bg-blue-50" onClick={downloadReport}>
                <Download className="w-4 h-4 mr-2" />
                Download Full Report
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Detailed Report */}
        <Card className="bg-white shadow-lg border-0">
          <CardHeader className="border-b border-gray-100 p-6">
            <CardTitle className="text-xl font-bold text-gray-800">Detailed Findings</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Tabs defaultValue="all" className="w-full">
              <TabsList className="flex w-full bg-gray-50 p-1 rounded-lg overflow-hidden">
                <TabsTrigger value="all" className="data-[state=active]:bg-white data-[state=active]:text-blue-600 text-sm flex-1 px-1 py-2 min-w-0 text-center">
                  <span className="truncate">All Issues</span>
                </TabsTrigger>
                <TabsTrigger
                  value="security"
                  className="data-[state=active]:bg-white data-[state=active]:text-blue-600 text-sm flex-1 px-1 py-2 min-w-0 text-center"
                >
                  <span className="truncate">Security</span>
                </TabsTrigger>
                <TabsTrigger
                  value="code-quality"
                  className="data-[state=active]:bg-white data-[state=active]:text-blue-600 text-sm flex-1 px-1 py-2 min-w-0 text-center"
                >
                  <span className="truncate">Code Quality</span>
                </TabsTrigger>
                <TabsTrigger value="ui-ux" className="data-[state=active]:bg-white data-[state=active]:text-blue-600 text-sm flex-1 px-1 py-2 min-w-0 text-center">
                  <span className="truncate">UI & UX</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="mt-6 space-y-4">
                {getIssues().map((issue) => {
                  const SeverityIcon = severityConfig[issue.severity].icon
                  return (
                    <Card
                      key={issue.id}
                      className="border border-gray-200 hover:shadow-md transition-shadow duration-200"
                    >
                      <CardContent className="p-6">
                        <div className="flex items-start gap-4">
                          <div className={`p-2 rounded-lg ${severityConfig[issue.severity].color}`}>
                            <SeverityIcon className={`w-5 h-5 ${severityConfig[issue.severity].iconColor}`} />
                          </div>
                          <div className="flex-1 space-y-3">
                            <div className="flex items-center justify-between">
                              <h4 className="text-lg font-semibold text-gray-800">{issue.title}</h4>
                              <Badge variant="outline" className={severityConfig[issue.severity].color}>
                                {issue.severity}
                              </Badge>
                            </div>
                            <p className="text-gray-600">{issue.description}</p>
                            
                            {issue.code_snippet && (
                              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center gap-2 mb-2">
                                  <Code className="w-4 h-4 text-gray-500" />
                                  <span className="text-sm font-medium text-gray-700">Issue Found Here:</span>
                                </div>
                                <code className="text-sm text-gray-800 font-mono">{issue.code_snippet}</code>
                              </div>
                            )}
                            
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                              <p className="text-green-800 font-medium mb-1">💡 Suggestion:</p>
                              <p className="text-green-700">{issue.recommendation}</p>
                            </div>
                            {issue.guideline && (
                              <div className="flex items-center gap-2 text-sm text-blue-600">
                                <Info className="w-4 h-4" />
                                <span>Guideline: {issue.guideline}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </TabsContent>

              {["security", "code-quality", "ui-ux"].map((category) => (
                <TabsContent key={category} value={category} className="mt-6 space-y-4">
                  {getIssues()
                    .filter((issue) => issue.category === category)
                    .map((issue) => {
                      const SeverityIcon = severityConfig[issue.severity].icon
                      return (
                        <Card
                          key={issue.id}
                          className="border border-gray-200 hover:shadow-md transition-shadow duration-200"
                        >
                          <CardContent className="p-6">
                            <div className="flex items-start gap-4">
                              <div className={`p-2 rounded-lg ${severityConfig[issue.severity].color}`}>
                                <SeverityIcon className={`w-5 h-5 ${severityConfig[issue.severity].iconColor}`} />
                              </div>
                              <div className="flex-1 space-y-3">
                                <div className="flex items-center justify-between">
                                  <h4 className="text-lg font-semibold text-gray-800">{issue.title}</h4>
                                  <Badge variant="outline" className={severityConfig[issue.severity].color}>
                                    {issue.severity}
                                  </Badge>
                                </div>
                                <p className="text-gray-600">{issue.description}</p>
                                
                                {issue.code_snippet && (
                                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                    <div className="flex items-center gap-2 mb-2">
                                      <Code className="w-4 h-4 text-gray-500" />
                                      <span className="text-sm font-medium text-gray-700">Issue Found Here:</span>
                                    </div>
                                    <code className="text-sm text-gray-800 font-mono">{issue.code_snippet}</code>
                                  </div>
                                )}
                                
                                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                  <p className="text-green-800 font-medium mb-1">💡 Suggestion:</p>
                                  <p className="text-green-700">{issue.recommendation}</p>
                                </div>
                                {issue.guideline && (
                                  <div className="flex items-center gap-2 text-sm text-blue-600">
                                    <Info className="w-4 h-4" />
                                    <span>Guideline: {issue.guideline}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )
                    })}
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-12 text-sm text-gray-500">
          MIT Licensed. This prototype is not affiliated with Canva.
        </div>
      </div>
    </div>
  )
}
