# Canva App Reviewer - Backend

A FastAPI backend for analyzing Canva apps for security, code quality, and UI/UX.

## Features

- **FastAPI Framework**: Modern, fast, and well-documented API
- **Async Support**: Full asynchronous processing for better performance
- **Comprehensive Analysis**: Security, Code Quality, and UI/UX analysis
- **Multiple Format Support**: JavaScript (.js) and TypeScript React (.tsx) file uploads
- **Real-time Progress**: Track analysis progress in real-time
- **Anthropic Claude Integration**: AI-powered insights and recommendations

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for analysis tools)
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone and navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API:**
   - API: http://localhost:8000 (or your configured BACKEND_URL)
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Development

```bash
# Build and run with docker-compose
docker-compose up --build

# Or build and run manually
docker build -t canva-reviewer-backend .
docker run -p 8000:8000 canva-reviewer-backend
```

## API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `GET /` - API information
- `GET /docs` - Interactive API documentation

### API v1 Endpoints

- `GET /api/v1/status` - API status
- `POST /api/v1/upload` - Upload Canva app file (Coming in Phase 2)
- `POST /api/v1/analyze/{file_id}` - Start analysis (Coming in Phase 3)
- `GET /api/v1/analysis/{file_id}/status` - Check analysis status
- `GET /api/v1/analysis/{file_id}/report` - Get analysis results

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest app/tests/test_main.py
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Configuration

The application uses environment variables for configuration. See `.env.example` for all available options.

Key settings:
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude integration
- `MAX_UPLOAD_SIZE`: Maximum file upload size (default: 10MB for individual files)
- `UPLOAD_DIR`: Directory for temporary file storage
- `DEBUG`: Enable debug mode and detailed logging
- `FRONTEND_URL`: Frontend application URL (for CORS and responses)
- `BACKEND_URL`: Backend API URL (for self-reference)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

### Environment-Specific Configuration

**Local Development:**
```bash
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

**AWS/Cloud Deployment:**
```bash
FRONTEND_URL=https://your-app.example.com
BACKEND_URL=https://api.your-app.example.com
ALLOWED_ORIGINS=https://your-app.example.com,https://staging.your-app.example.com
```

## AWS Deployment

### Prerequisites for AWS Deployment

- AWS CLI configured
- Docker installed
- AWS ECS/EKS or App Runner account access
- Domain names configured (optional)

### Deployment Options

1. **AWS App Runner** (Recommended for simplicity)
2. **AWS ECS with Fargate**
3. **AWS EKS (Kubernetes)**
4. **AWS Lambda with Mangum** (for serverless)

### Environment Variables for Production

```bash
# Production settings
DEBUG=false
UPLOAD_DIR=/app/uploads
FRONTEND_URL=https://your-frontend-domain.com
BACKEND_URL=https://your-api-domain.com
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Security
ANTHROPIC_API_KEY=your-production-key
```

### Docker for AWS Deployment

```dockerfile
# Production Dockerfile considerations
ENV UPLOAD_DIR=/app/uploads
VOLUME /app/uploads
EXPOSE 8000
```

## Architecture

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── api/                 # API routes
│   └── v1/             # API version 1
├── models/             # Pydantic models
├── core/               # Business logic (Phase 3+)
├── analyzers/          # Analysis modules (Phase 4+)
├── utils/              # Utilities (Phase 6+)
└── tests/              # Test files
```

## Analysis Categories

The system analyzes Canva apps across three main categories:

1. **Security (30%)** - Code vulnerabilities, unsafe patterns, API security
2. **Code Quality (30%)** - Static analysis, TypeScript compliance, best practices
3. **UI & UX (40%)** - Accessibility, design consistency, performance, user experience

## Next Steps

- **Phase 2**: File upload and processing
- **Phase 3**: Analysis engine core
- **Phase 4**: Individual analyzers (static, accessibility, performance, design, LLM)
- **Phase 5**: Complete API endpoints
- **Phase 6**: Report generation
- **Phase 7**: Docker and deployment
- **Phase 8**: Testing and documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details. 