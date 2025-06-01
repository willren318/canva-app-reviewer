# Canva App Reviewer - Backend Implementation Plan

## Overview
This document outlines the comprehensive implementation plan for the Canva App Reviewer backend using FastAPI. The backend will analyze uploaded Canva apps for code quality, accessibility, design consistency, performance, and UX.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Configuration and environment variables
│   ├── models/                     # Pydantic models
│   │   ├── __init__.py
│   │   ├── request.py              # Request models
│   │   ├── response.py             # Response models
│   │   └── analysis.py             # Analysis result models
│   ├── api/                        # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # Main router
│   │   │   ├── upload.py           # File upload endpoints
│   │   │   └── analysis.py         # Analysis endpoints
│   ├── core/                       # Core business logic
│   │   ├── __init__.py
│   │   ├── analyzer.py             # Main analysis orchestrator
│   │   ├── file_handler.py         # File processing utilities
│   │   └── scoring.py              # Scoring algorithms
│   ├── analyzers/                  # Analysis modules
│   │   ├── __init__.py
│   │   ├── static_analysis.py      # ESLint, TypeScript analysis
│   │   ├── accessibility.py        # Playwright + axe-core
│   │   ├── performance.py          # Lighthouse analysis
│   │   ├── design.py              # Visual/design heuristics
│   │   ├── security.py            # Security analysis
│   │   └── llm_analysis.py        # GPT-4o integration
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── file_utils.py          # File manipulation utilities
│   │   ├── report_generator.py    # HTML/Markdown report generation
│   │   └── docker_utils.py        # Docker container utilities
│   └── tests/                     # Test files
│       ├── __init__.py
│       ├── test_main.py
│       ├── test_analyzers/
│       └── test_utils/
├── requirements.txt               # Python dependencies
├── Dockerfile                    # Docker configuration
├── docker-compose.yml           # Development environment
├── .env.example                  # Environment variables template
└── README.md                     # Backend-specific documentation
```

## Implementation Phases

### Phase 1: Foundation Setup (Days 1-2)
- [x] Create basic FastAPI application structure
- [x] Setup virtual environment and dependencies
- [x] Configure environment variables and settings
- [x] Create basic health check endpoint
- [x] Setup logging and error handling

**Key Dependencies:**
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
aiofiles==23.2.1
python-dotenv==1.0.0
playwright==1.40.0
anthropic==0.7.8
pillow==10.1.0
opencv-python==4.8.1.78
jinja2==3.1.2
```

### Phase 2: File Upload & Processing (Day 3)
- [x] Implement file upload endpoints
- [x] Create file validation logic
- [x] Add JavaScript/TypeScript file processing
- [x] Validate Canva app file structure
- [x] Detect source file types (.js, .tsx)

**Key Features:**
- JavaScript/TypeScript file support (.js, .tsx)
- File size validation (max 10MB for individual files)
- Canva app code validation
- Syntax and structure analysis

### Phase 3: Analysis Engine Core (Days 4-5)
- [x] Create main analysis orchestrator
- [x] Implement parallel analyzer execution
- [x] Add timeout and error handling
- [x] Create scoring algorithm
- [x] Setup result aggregation

**Scoring Weights:**
- Security: 30%
- Code Quality: 30%
- UI & UX: 40%

### Phase 4: Individual Analyzers (Days 6-8)

#### 4.1 Static Code Analysis
- ESLint integration with custom rules
- TypeScript analysis
- Security vulnerability detection
- Code quality metrics

#### 4.2 Accessibility Analysis
- Playwright + axe-core integration
- WCAG compliance checking
- Color contrast analysis
- Keyboard navigation testing

#### 4.3 Performance Analysis
- Lighthouse integration
- Bundle size analysis
- Load time metrics
- Resource optimization checks

#### 4.4 Design Analysis
- Screenshot-based visual analysis
- Color consistency checking
- Layout crowding detection
- Contrast ratio calculations

#### 4.5 LLM Analysis
- Anthropic Claude integration for insights
- Automated recommendations
- Markdown report generation
- Context-aware suggestions

### Phase 5: API Endpoints (Day 9)
- [x] Upload endpoints (`/api/v1/upload`)
- [x] Analysis endpoints (`/api/v1/analyze/{file_id}`)
- [x] Status checking (`/api/v1/analysis/{file_id}/status`)
- [x] Report retrieval (`/api/v1/analysis/{file_id}/report`)
- [x] Download endpoints (`/api/v1/analysis/{file_id}/download`)

### Phase 6: Report Generation (Day 10)
- [x] HTML report templates
- [x] Markdown report generation
- [x] JSON API responses
- [x] Downloadable report formats
- [x] Interactive charts and metrics

### Phase 7: Docker & Deployment (Day 11)
- [x] Multi-stage Dockerfile
- [x] Docker Compose setup
- [x] Node.js tools integration
- [x] Browser automation setup
- [x] Production deployment config

### Phase 8: Testing & Documentation (Day 12)
- [x] Unit tests for all analyzers
- [x] Integration tests for API endpoints
- [x] End-to-end analysis workflow tests
- [x] API documentation
- [x] Deployment guides

## Key Technical Decisions

### 1. Architecture Pattern
- **Microservice-ready**: Modular analyzer design
- **Async/Await**: Full async support for I/O operations
- **Background Tasks**: Non-blocking analysis execution
- **Error Isolation**: Each analyzer runs independently

### 2. File Processing
- **Individual File Uploads**: Memory-efficient single file handling
- **Temporary Analysis**: Create temporary analysis environments
- **Syntax Validation**: JavaScript/TypeScript syntax checking
- **Cleanup Strategy**: Automatic temporary file removal

### 3. Analysis Pipeline
- **Parallel Execution**: Independent analyzers run concurrently
- **Graceful Degradation**: Continue if individual analyzers fail
- **Timeout Handling**: Prevent hung analysis processes
- **Progress Tracking**: Real-time status updates

### 4. External Tool Integration
- **Docker Containers**: Isolated Node.js environment
- **Subprocess Management**: Safe external tool execution
- **Resource Limits**: CPU and memory constraints
- **Error Recovery**: Fallback mechanisms

## API Endpoints Overview

```
POST   /api/v1/upload                    # Upload Canva app file (.js/.tsx)
POST   /api/v1/analyze/{file_id}         # Start analysis
GET    /api/v1/analysis/{file_id}/status # Check analysis status
GET    /api/v1/analysis/{file_id}/report # Get analysis results
GET    /api/v1/analysis/{file_id}/download?format=html|md|json # Download report
GET    /health                          # Health check
GET    /docs                            # API documentation
```

## Environment Configuration

```bash
# .env.example
APP_NAME=Canva App Reviewer
DEBUG=false
API_V1_PREFIX=/api/v1
MAX_UPLOAD_SIZE=10485760  # 10MB for individual files
UPLOAD_DIR=/tmp/uploads
TIMEOUT_SECONDS=300
ANTHROPIC_API_KEY=sk-ant-your-key-here
NODE_DOCKER_IMAGE=node:18-alpine

# URL Configuration (Environment-specific)
# Local Development:
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# AWS/Cloud Deployment:
# FRONTEND_URL=https://your-app.example.com
# BACKEND_URL=https://api.your-app.example.com
# ALLOWED_ORIGINS=https://your-app.example.com
```

## Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}
      - BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    volumes:
      - /tmp/uploads:/tmp/uploads
  
  frontend:
    build: ../frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=${BACKEND_URL:-http://localhost:8000}
```

## AWS Deployment Strategy

### Phase 7 Extension: AWS Deployment

**Deployment Options:**
1. **AWS App Runner** - Simplest option, direct container deployment
2. **AWS ECS with Fargate** - More control, scalable
3. **AWS EKS** - Kubernetes-based, most flexible
4. **AWS Lambda + Mangum** - Serverless option

**Architecture for AWS:**
```
Internet Gateway
    ↓
Application Load Balancer
    ↓
ECS/App Runner Containers
├── Frontend Container (Next.js)
└── Backend Container (FastAPI)
    ↓
External Services
├── Anthropic Claude API
└── S3 (for file storage)
```

**Environment Variables for Production:**
```bash
# Production Configuration
DEBUG=false
UPLOAD_DIR=/app/uploads
FRONTEND_URL=https://canva-reviewer.example.com
BACKEND_URL=https://api.canva-reviewer.example.com
ALLOWED_ORIGINS=https://canva-reviewer.example.com
ANTHROPIC_API_KEY=sk-ant-production-key
```

**Security Considerations:**
- Use AWS Secrets Manager for sensitive keys
- Enable HTTPS with AWS Certificate Manager
- Configure security groups for container access
- Use IAM roles for service authentication

## Implementation Questions - ANSWERED

1. **~~OpenAI API~~** ✅ **Anthropic Claude**: Using Claude models with provided API key
2. **~~Redis Integration~~** ✅ **In-Memory**: Simpler in-memory approach for prototype
3. **~~Node.js Tools~~** ✅ **Separate Containers**: Backend and frontend in separate containers
4. **~~Frontend Integration~~** ✅ **Yes**: Update existing Next.js app to use FastAPI backend
5. **~~Authentication~~** ✅ **Open Access**: No authentication needed for prototype

## Updated Analysis Categories

The analysis now focuses on **3 core categories**:

1. **Security (30%)** - Code vulnerabilities, unsafe patterns, API security
2. **Code Quality (30%)** - Static analysis, TypeScript compliance, best practices  
3. **UI & UX (40%)** - Accessibility, design consistency, performance, user experience

## Next Steps

1. Answer clarification questions above
2. Create basic FastAPI structure
3. Implement file upload functionality
4. Build analysis pipeline
5. Integrate external tools
6. Create report generation
7. Setup Docker deployment
8. Test complete workflow

This plan provides a comprehensive roadmap for building a production-ready FastAPI backend that matches the specification requirements. 