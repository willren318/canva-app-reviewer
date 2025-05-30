# Canva App Reviewer - Frontend

A modern Next.js frontend application for the Canva App Reviewer tool. This frontend provides an intuitive interface for uploading and analyzing Canva app files.

## Features

- 🚀 Modern React with Next.js 14
- 🎨 Beautiful UI with Tailwind CSS and shadcn/ui components
- 📁 Drag & drop file upload with real-time progress
- 🔄 Real-time API integration with the FastAPI backend
- 📱 Responsive design for all devices
- ⚡ TypeScript for type safety
- 🎯 Optimized for `.js` and `.tsx` file analysis

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Icons**: Lucide React
- **API Client**: Native Fetch API

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running (see `../backend/README.md`)

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` and set:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` | Yes |

### Environment Configuration Examples

**Local Development:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Production/AWS Deployment:**
```bash
NEXT_PUBLIC_API_URL=https://api.your-app.example.com
```

## API Integration

The frontend integrates with the FastAPI backend through the `/lib/api.ts` module, which provides:

- **File Upload**: Upload `.js` and `.tsx` files with validation
- **Progress Tracking**: Real-time upload progress indicators
- **Error Handling**: Comprehensive error handling with user feedback
- **File Management**: Get file info and delete uploaded files
- **API Status**: Dynamic configuration from backend API

### Key API Functions

```typescript
import { api } from '@/lib/api'

// Upload a file
const response = await api.uploadFile(file)

// Get file information
const fileInfo = await api.getFileInfo(fileId)

// Check API status
const status = await api.status()
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Main application page
├── components/            # Reusable components
│   └── ui/               # shadcn/ui components
├── lib/                  # Utilities and API client
│   └── api.ts           # API integration
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

### Code Style

This project uses:
- **ESLint** for code linting
- **Prettier** for code formatting
- **TypeScript** for type safety

## Deployment

### Local Development

1. Ensure the backend is running on `http://localhost:8000`
2. Start the frontend development server
3. Access the application at `http://localhost:3000`

### Production Deployment

For AWS or other cloud deployments:

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Set production environment variables:**
   ```bash
   NEXT_PUBLIC_API_URL=https://your-api-domain.com
   ```

3. **Deploy using your preferred method:**
   - AWS Amplify
   - Vercel
   - Docker container
   - Static hosting (after `npm run export`)

### Docker Deployment

Create a `Dockerfile` in the frontend directory:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t canva-app-reviewer-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://backend:8000 canva-app-reviewer-frontend
```

## Features Overview

### File Upload
- Drag & drop interface
- File type validation (`.js`, `.tsx`)
- File size validation (configurable via API)
- Real-time upload progress
- Canva pattern detection feedback

### Error Handling
- Network error handling
- File validation errors
- API error responses
- User-friendly error messages
- Retry functionality

### User Experience
- Loading states and progress indicators
- Responsive design for mobile/desktop
- Smooth animations and transitions
- Clear visual feedback
- Accessible design patterns

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test on both desktop and mobile
4. Ensure API integration works with backend
5. Update documentation as needed

## License

MIT License - see LICENSE file for details.

---

**Note**: This frontend is designed to work with the FastAPI backend. Ensure both services are running for full functionality. 