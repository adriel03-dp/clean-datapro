<div align="center">

# 🧹 CleanDataPro

### Professional Data Cleaning & Analysis Platform

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.24+-FF4B4B.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-Open%20Source-green.svg)](LICENSE)

</div>

---

## 🎯 Overview

**CleanDataPro** is a production-ready data cleaning and analysis platform that automates CSV data preprocessing, generates detailed reports, and provides an intuitive web interface for data quality management. Transform messy, incomplete datasets into pristine, analysis-ready data in seconds.

### Why CleanDataPro?

- ⚡ **90% Time Reduction** - Automate hours of manual data cleaning
- 📊 **100% Transparency** - See exactly what was fixed and how
- 🚀 **Production Ready** - Battle-tested with comprehensive error handling
- 🔒 **Enterprise Features** - Authentication, audit trails, and persistence
- 🎯 **Zero Configuration** - Intelligent defaults that just work

---

## ✨ Key Features

### 🧹 Data Cleaning Engine

**Intelligent Missing Value Imputation** *(Pandas-based)*
- **Numeric columns**: Median imputation using `pandas.Series.median()` - robust to outliers
- **Datetime columns**: Forward-fill with earliest date using `pandas.Series.min()`
- **Categorical columns**: Mode imputation using `pandas.Series.mode()` - most frequent value
- **Placeholder detection**: Identifies and converts common placeholders (N/A, UNKNOWN, ERROR) to `NaN`

**Duplicate Detection & Removal** *(Pandas `drop_duplicates()`)*
- Exact row matching algorithm with configurable strategy
- Keeps first occurrence, removes subsequent duplicates
- Reports duplicate count and percentage for audit trail

**Smart Type Inference** *(Custom algorithm + Pandas `to_numeric()`)*
- Detects numeric columns with >80% valid numeric values
- Safe type conversion with error handling (`errors='coerce'`)
- Handles mixed-type columns and type inconsistencies

**Column-Level Statistics** *(NumPy + Pandas aggregations)*
- Missing value counts and percentages per column
- Unique value counts using `nunique()`
- Sample values for data preview
- Data type detection and reporting

---

### 📊 Advanced Reporting & Visualization

**Data Issues Report** *(Streamlit + Plotly)*
- **3-column before/after/cleaning layout** with color-coded metrics
- **Interactive Plotly charts**: Bar charts for missing values, funnel charts for data flow
- **Quality scoring algorithm**: `(1 - missing_pct) * 100` for before/after comparison
- **4 analysis tabs**: Issues Found, Missing by Column, Cleaning Details, Final Quality

**PDF Generation** *(ReportLab library)*
- Professional reports with tables and formatted text
- Before/after statistics with `TableStyle` formatting
- UTC timestamp and metadata inclusion
- Configurable page layouts and styles

**JSON Summaries** *(Python `json` module)*
- Machine-readable format for automation pipelines
- NumPy type conversion for JSON serialization
- Complete metadata: rows, columns, operations, timestamps
- Nested structure: `missing_summary_before/after` arrays

**Interactive Dashboard** *(Streamlit 1.24+)*
- Real-time file upload with `st.file_uploader()`
- Processing status tracking with session state
- Plotly visualizations: `plotly.express` and `plotly.graph_objects`
- Responsive design with Streamlit's column layout

---

### 🔌 Production API & Integration

**RESTful API** *(FastAPI 0.95+ with Uvicorn ASGI)*
- **Endpoints**:
  - `POST /api/process` - Multipart file upload, CSV processing, returns summary JSON
  - `GET /api/download` - Query params: `kind` (processed/reports), `filename`
  - `GET /api/runs` - Paginated processing history from MongoDB
  - `GET /healthz` - Health check endpoint for monitoring
- **Async operations**: `async def` handlers for concurrent request processing
- **Auto-documentation**: OpenAPI/Swagger at `/docs`, ReDoc at `/redoc`

**Authentication System** *(JWT + bcrypt)*
- **JWT tokens**: Generated using `pyjwt` library with configurable expiration
- **Password hashing**: bcrypt algorithm with automatic salt generation
- **Token validation**: Middleware-based authentication for protected routes
- **User management**: MongoDB-backed user storage with email/password

**MongoDB Integration** *(PyMongo 4.0+ driver)*
- **Connection pooling**: Cached MongoDB client for efficient connections
- **Collections**: `users` (authentication), `clean_runs` (processing history)
- **Document structure**: Timestamps, user ID, file metadata, cleaning summary
- **Automatic indexing**: For efficient queries on timestamps and user IDs

**Cross-Origin Support** *(FastAPI CORSMiddleware)*
- Configurable origins for frontend integration
- Credential support enabled for authenticated requests
- All HTTP methods allowed for API flexibility

---

## 🛠️ Tech Stack

### Backend Technologies
- **FastAPI 0.95+**: Modern async web framework with automatic OpenAPI docs, type validation via Pydantic
- **Python 3.11+**: Latest Python features including improved error messages and performance optimizations
- **Pandas 1.5+**: DataFrame-based data manipulation with vectorized operations for performance
- **NumPy**: Numerical computing foundation for Pandas, efficient array operations
- **ReportLab 4.0+**: PDF generation library with table formatting and custom styling
- **PyMongo 4.0+**: Official MongoDB driver with connection pooling and async support
- **APScheduler 3.8+**: Advanced task scheduling for background jobs and cleanup tasks
- **bcrypt 4.0+**: Secure password hashing with automatic salt generation
- **PyJWT 2.8+**: JSON Web Token implementation for stateless authentication
- **python-dotenv**: Environment variable management from `.env` files

### Frontend Technologies
- **Streamlit 1.24+**: Reactive web framework with automatic rerun on user interaction
- **Plotly 5.0+**: Interactive JavaScript-based charts with zoom, pan, and hover capabilities
- **Requests 2.28+**: HTTP library for API communication with connection pooling

### Data Processing Pipeline
- **Pandas**: Core engine for CSV parsing, DataFrame operations, and data transformations
- **NumPy**: Underlying numerical computations, statistical functions (median, mode, etc.)

### Development & Testing
- **pytest**: Unit testing framework with fixtures and parametrized tests
- **Black**: Opinionated code formatter (line length: 88) for consistent style
- **isort**: Import statement organizer compatible with Black's style
- **Docker**: Containerization with multi-stage builds for production deployment

### Infrastructure
- **MongoDB 4.0+**: NoSQL document database for flexible schema and horizontal scaling
- **Uvicorn**: Lightning-fast ASGI server with HTTP/1.1 and WebSocket support

---

## 🎨 Unique Features & Technical Implementation

1. **Transparency-First Architecture**
   - Complete audit trail using MongoDB timestamped documents
   - Before/after snapshots with `missing_summary_before/after` arrays
   - Operation logging with structured metadata (duplicates removed, values imputed, types converted)

2. **Intelligent Type Detection Algorithm**
   - Custom heuristic: >80% numeric values → treat as numeric column
   - Placeholder value detection using predefined set: `{N/A, UNKNOWN, ERROR, null, ...}`
   - Safe conversion with Pandas `to_numeric(errors='coerce')` to handle edge cases

3. **Multi-Format Professional Reporting**
   - **PDF**: ReportLab with custom `TableStyle` for stakeholder distribution
   - **JSON**: Full programmatic access with NumPy type serialization
   - **CSV**: Cleaned data ready for downstream analysis
   - **Interactive UI**: Streamlit with real-time Plotly visualizations

4. **Enterprise-Grade Security & Persistence**
   - JWT-based stateless authentication with configurable token expiration
   - bcrypt password hashing with automatic salt (cost factor: 12)
   - MongoDB document-based storage with automatic indexing
   - Processing history with full metadata for compliance and auditing

5. **Zero-Config Intelligence**
   - Automatic data type inference using Pandas dtype detection
   - Smart imputation strategy selection based on column characteristics
   - Sensible defaults: median for numeric, mode for categorical, min for datetime
   - No configuration files required - works out of the box

6. **Modern Tech Stack**
   - Async FastAPI for high-concurrency handling (ASGI server)
   - Reactive Streamlit UI with session state management
   - Interactive Plotly charts with JavaScript-powered zoom/pan
   - Containerized with Docker for consistent deployments

---

## 💎 Use Cases

**Data Scientists** - Automate preprocessing pipelines, focus on analysis  
**Business Analysts** - Professional reports for stakeholders, no coding required  
**Researchers** - Publication-ready data quality reports with reproducible methodology  
**Startups** - Free, open-source, deploy in minutes, scale as you grow

**Industries:** E-commerce, Healthcare, Finance, Education, Research, Marketing

---

## 🚀 Deployment

**Recommended Platforms:**
- **Frontend:** [Streamlit Cloud](https://streamlit.io/cloud) - Free, auto-deploy from GitHub
- **Backend:** [Railway](https://railway.app) or [Render](https://render.com) - Easy Docker deployments
- **Database:** [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - Free tier available

**Deployment Guide:** See [DEPLOYMENT_STEPS.md](DEPLOYMENT_STEPS.md) for step-by-step instructions (~20 minutes total)

---

## 📦 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB (local or Atlas)
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/adriel03-dp/clean-datapro.git
cd clean-datapro

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup (new terminal)
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Create `backend/.env`:
```env
MONGODB_URI=mongodb://localhost:27017/cleandatapro
CLEAN_DATAPRO_BACKEND=http://localhost:8000
```

### Running

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
streamlit run streamlit_app.py
```

Access at: **http://localhost:8501** (Frontend) | **http://localhost:8000/docs** (API)

---

## 📖 Usage

### Web Interface
1. Upload CSV file
2. Click "Process & Clean"
3. Review data issues report with before/after comparison
4. Download cleaned CSV, PDF report, or JSON summary

### API
See interactive documentation at `http://localhost:8000/docs` for:
- `POST /api/process` - Process CSV files
- `GET /api/download` - Download results
- `GET /api/runs` - View processing history
- `POST /api/auth/login` - Authentication

### Python Library
```python
from src.cleaner import clean_csv
summary = clean_csv("input.csv", "output.csv", drop_duplicates=True)
```

---

## 🧪 Testing

```bash
pytest                              # Run all tests
pytest --cov=src --cov=backend/src  # With coverage
pytest tests/test_cleaner.py        # Specific test
```

---

## 🛠️ Development

```bash
black .   # Format code
isort .   # Sort imports
```

**Docker:**
```bash
cd backend
docker build -t cleandatapro-backend .
docker run -p 8000:8000 cleandatapro-backend
```

---

## 📁 Project Structure

```
clean-datapro/
├── backend/          # FastAPI backend (src/, routes/, models/)
├── frontend/         # Streamlit web interface
├── src/              # Core library modules
├── tests/            # Test suite
├── data/             # Raw/processed files (gitignored)
└── reports/          # Generated reports (gitignored)
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow code style (Black, isort)
4. Add tests for new features
5. Submit a pull request

---

## 📄 License

Open source under MIT License. See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Adriel Perera**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/adriel-perera) [![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/adriel03-dp)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

*Transforming messy data into insights* ✨

</div>
