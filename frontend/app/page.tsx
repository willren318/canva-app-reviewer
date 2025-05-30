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
  XCircle,
  Info,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { api, ApiError, type UploadResponse, type FileInfo } from "@/lib/api"

type AppState = "upload" | "processing" | "report" | "error"

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
  low: { color: "bg-blue-100 text-blue-800 border-blue-200", icon: CheckCircle, iconColor: "text-blue-500" },
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
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null)
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [apiStatus, setApiStatus] = useState<{
    supported_file_types: string[]
    max_file_size_mb: number
    max_file_size_display: string
  } | null>(null)

  // Check API status on component mount
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const status = await api.status()
        // Parse max_file_size from "10MB" to number
        const maxSizeMB = parseInt(status.max_file_size.replace(/[^\d]/g, '')) || 10
        setApiStatus({
          supported_file_types: status.supported_file_types,
          max_file_size_mb: maxSizeMB,
          max_file_size_display: status.max_file_size
        })
      } catch (error) {
        console.warn('Failed to get API status:', error)
        // Fallback to default values
        setApiStatus({
          supported_file_types: ['.js', '.tsx'],
          max_file_size_mb: 10,
          max_file_size_display: '10MB'
        })
      }
    }
    checkApiStatus()
  }, [])

  const overallScore = Math.round(
    Object.values(categoryScores).reduce((a, b) => a + b, 0) / Object.values(categoryScores).length,
  )

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file)
    setIsUploading(true)
    setError(null)
    setUploadProgress(0)

    try {
      // Validate file before upload
      if (apiStatus) {
        const maxSizeBytes = apiStatus.max_file_size_mb * 1024 * 1024
        if (file.size > maxSizeBytes) {
          throw new Error(`File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds the maximum limit of ${apiStatus.max_file_size_mb}MB`)
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

  const startAnalysis = () => {
    if (!uploadResponse) {
      setError('No file uploaded')
      setCurrentState("error")
      return
    }
    
    setCurrentState("processing")
    // TODO: Phase 3 - Replace with actual analysis API call
    setTimeout(() => {
      setCurrentState("report")
    }, 3000)
  }

  const resetToUpload = () => {
    setCurrentState("upload")
    setUploadedFile(null)
    setUploadResponse(null)
    setFileInfo(null)
    setError(null)
    setUploadProgress(0)
    setIsUploading(false)
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
                            <p>Status: {uploadResponse.status}</p>
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
                          Maximum file size: {apiStatus.max_file_size_display}
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
        <div className="text-center space-y-8">
          <div className="w-24 h-24 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto animate-pulse">
            <Zap className="w-12 h-12 text-white" />
          </div>

          <div className="space-y-4">
            <h2 className="text-3xl font-bold text-gray-800">Analyzing your app...</h2>
            <p className="text-lg text-gray-600">Good things are on their way! ✨</p>
          </div>

          <div className="w-64 mx-auto">
            <Progress value={75} className="h-2" />
          </div>

          <div className="text-sm text-gray-500 space-y-1">
            <p>🔍 Checking code quality...</p>
            <p>♿ Reviewing accessibility...</p>
            <p>🎨 Analyzing design patterns...</p>
          </div>
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
                <p className="text-lg font-semibold text-gray-700">Great work!</p>
                <p className="text-sm text-gray-600">
                  Your app shows strong potential with room for improvement in accessibility.
                </p>
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
                {Object.entries(categoryScores).map(([category, score]) => {
                  // Determine color based on category
                  let barColor = ""
                  if (category === "security") {
                    barColor = "bg-red-500"
                  } else if (category === "code-quality") {
                    barColor = "bg-blue-500"
                  } else if (category === "ui-ux") {
                    barColor = "bg-purple-500"
                  }

                  return (
                    <div key={category} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-lg font-medium text-gray-800 capitalize">
                          {category === "ui-ux" ? "UI & UX" : category.replace("-", " ")}
                        </span>
                        <span className="text-xl font-bold text-blue-600">{score}</span>
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
                  Your Canva app demonstrates solid code quality and performance with a modern, user-friendly interface.
                  The main areas for improvement focus on accessibility compliance and design consistency. Addressing
                  the contrast issues and missing alt text will significantly enhance the user experience for all users.
                </p>
              </div>
            </div>
            <div className="mt-6">
              <Button variant="outline" className="border-blue-300 text-blue-700 hover:bg-blue-50">
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
              <TabsList className="grid w-full grid-cols-4 bg-gray-50 p-1 m-6 mb-0 rounded-lg">
                <TabsTrigger value="all" className="data-[state=active]:bg-white data-[state=active]:text-blue-600">
                  All Issues
                </TabsTrigger>
                <TabsTrigger
                  value="security"
                  className="data-[state=active]:bg-white data-[state=active]:text-blue-600"
                >
                  Security
                </TabsTrigger>
                <TabsTrigger
                  value="code-quality"
                  className="data-[state=active]:bg-white data-[state=active]:text-blue-600"
                >
                  Code Quality
                </TabsTrigger>
                <TabsTrigger value="ui-ux" className="data-[state=active]:bg-white data-[state=active]:text-blue-600">
                  UI & UX
                </TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="p-6 space-y-4">
                {mockIssues.map((issue) => {
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
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                              <p className="text-green-800 font-medium mb-1">💡 Suggestion:</p>
                              <p className="text-green-700">{issue.suggestion}</p>
                            </div>
                            {issue.codeSnippet && (
                              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center gap-2 mb-2">
                                  <Code className="w-4 h-4 text-gray-500" />
                                  <span className="text-sm font-medium text-gray-700">Code Example</span>
                                </div>
                                <code className="text-sm text-gray-800 font-mono">{issue.codeSnippet}</code>
                              </div>
                            )}
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
                <TabsContent key={category} value={category} className="p-6 space-y-4">
                  {mockIssues
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
                                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                  <p className="text-green-800 font-medium mb-1">💡 Suggestion:</p>
                                  <p className="text-green-700">{issue.suggestion}</p>
                                </div>
                                {issue.codeSnippet && (
                                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                    <div className="flex items-center gap-2 mb-2">
                                      <Code className="w-4 h-4 text-gray-500" />
                                      <span className="text-sm font-medium text-gray-700">Code Example</span>
                                    </div>
                                    <code className="text-sm text-gray-800 font-mono">{issue.codeSnippet}</code>
                                  </div>
                                )}
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
