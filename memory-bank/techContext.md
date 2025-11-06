# Technical Context: SpendSense

## Technology Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Shadcn/ui** - Component library (LLM-optimized)
- **TailwindCSS** - Styling
- **React Router** - Navigation
- **Axios** - HTTP client for API calls
- **Recharts** - Charting library for metrics visualization

### Backend
- **FastAPI** (Python 3.11+) - Web framework
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation
- **SQLite** - Database (MVP), PostgreSQL (stretch goal)
- **Python-dotenv** - Environment variable management

### AI/ML
- **OpenAI Python SDK** - GPT-4o-mini integration
- **5 separate endpoints** - One per persona with distinct system prompts
- **JSON response format** - Structured output for recommendations

### Infrastructure
- **AWS Lambda** - Serverless compute
- **AWS API Gateway** - REST API
- **AWS SAM** - Infrastructure as Code
- **AWS S3** - Parquet file storage
- **Mangum** - ASGI adapter for Lambda

### Analytics
- **Pandas** - Data processing
- **PyArrow** - Parquet file format
- **Boto3** - AWS SDK for S3 operations

### Development Tools
- **Faker** - Synthetic data generation
- **Pytest** - Testing framework
- **Httpx** - HTTP client for testing FastAPI

## Development Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

### Environment Variables (.env)
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///./spendsense.db
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=spendsense-analytics
```

## Dependencies

### Backend (requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-dotenv==1.0.0
openai==1.3.5
pandas==2.1.3
pyarrow==14.0.1
faker==20.1.0
boto3==1.29.7
pytest==7.4.3
httpx==0.25.2
mangum==0.17.0
```

### Frontend (package.json)
- React 18
- Vite
- React Router DOM
- Axios
- Recharts
- Shadcn/ui components
- TailwindCSS

## Technical Constraints

### Node Version
- **Node.js 20 LTS** (v20.x.x) - Specified for this project
- **Rationale**: 
  - Current LTS version (as of 2024)
  - Full compatibility with React 18 and Vite
  - Supported by all deployment platforms (Vercel, Netlify, AWS)
  - Stable and well-tested
  - Long-term support until April 2026
- **Verification**: All frontend packages must be compatible with Node 20
- **Installation**: Use `nvm install 20` or download from nodejs.org

### Python Version
- **Python 3.11+** required
- FastAPI and SQLAlchemy 2.0 require Python 3.8+
- Python 3.11 recommended for performance

### Package Compatibility
- **Node 20 LTS**: All frontend packages must be compatible
- **Python 3.11+**: All backend packages must be compatible
- **Only install latest STABLE builds** - No beta, alpha, or RC versions
- **Verify compatibility** before installation:
  - Frontend: Check package.json peer dependencies, run `npm install --dry-run`
  - Backend: Check package documentation, run `pip check` after installation
- **Deployment compatibility**: Verify packages work on target platforms (AWS Lambda, Vercel, etc.)

## Deployment Considerations

### AWS Lambda
- Runtime: Python 3.11
- Memory: 512MB (configurable)
- Timeout: 30 seconds
- Handler: `app.main.handler` (via Mangum)

### API Gateway
- REST API
- CORS enabled
- ANY method on `/{proxy+}` path

### S3 Bucket
- Bucket name: `spendsense-analytics-{suffix}`
- Pre-signed URLs with 7-day expiry
- Parquet files stored in `features/` and `eval/` prefixes

### Platform Compatibility
- **AWS Lambda**: Fully compatible (Python 3.11 runtime)
- **Vercel**: Compatible for frontend deployment (React/Vite)
- **Netlify**: Compatible for frontend deployment
- **S3 + CloudFront**: Alternative frontend hosting

## Development Workflow

### Local Development
1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Backend runs on `http://localhost:8000`
4. Frontend runs on `http://localhost:5173`
5. Frontend proxies API calls to backend

### Testing
- Backend: `pytest tests/ -v`
- Frontend: Manual testing via browser
- Integration: Full flow via UI

### Deployment
- Backend: `sam build && sam deploy`
- Frontend: Build with `npm run build`, deploy to Vercel/Netlify/S3

## Cost Estimates (MVP)
- **Lambda**: ~$0.20/day (10-20 invocations)
- **API Gateway**: ~$0.05/day (~1000 requests)
- **S3**: ~$0.05/month (Parquet files)
- **OpenAI API**: ~$0.50-$1.00/day (75 users × 5 personas × 2 windows)
- **Total MVP cost**: ~$5-10 for 2-4 days of development

