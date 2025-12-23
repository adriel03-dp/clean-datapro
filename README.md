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

### Data Cleaning

- **Automatic Missing Value Imputation**: Intelligent filling of missing values based on data types
  - Numeric columns: Filled with median values
  - Datetime columns: Filled with earliest date
  - Categorical columns: Filled with mode (most frequent value)
- **Duplicate Detection and Removal**: Identifies and removes exact duplicate rows
- **Type Inference and Conversion**: Automatically detects and converts numeric columns
- **Column Analysis**: Detailed per-column statistics including missing percentages, unique counts, and sample values

### Data Issues Reporting (NEW)

- **Before/After Comparison**: See exactly what data quality issues existed and how they were fixed
- **Issues Overview**: Visual summary of all problems found (duplicates, missing values)
- **Column-by-Column Breakdown**: Understand which columns had issues and severity
- **Cleaning Impact Dashboard**: See the complete transformation of your data
- **Data Quality Scoring**: Track quality improvement from start to finish

### 📊 Advanced Reporting

- **Data Issues Report**: Side-by-side before/after comparison
  - Visual 3-column layout showing complete transformation
  - Column-by-column breakdown of issues and fixes
  - Data quality score improvements
- **PDF Reports**: Professional documentation with before/after comparisons
- **JSON Summaries**: Machine-readable metadata for automation
- **Interactive Dashboard**: Streamlit-based interface with real-time Plotly charts

### 🔌 Production API

- **RESTful API**: FastAPI backend with `/api/process`, `/api/download`, `/api/runs`
- **JWT Authentication**: Secure user management with bcrypt password hashing
- **MongoDB Integration**: Persistent storage for processing history and audit trails
- **CORS Support**: Seamless frontend integration
- **Interactive Docs**: Auto-generated API documentation at `/docs`

---

## 🛠️ Tech Stack

**Backend:** FastAPI 0.95+, Python 3.11+, Pandas 1.5+, ReportLab 4.0+, PyMongo 4.0+, APScheduler 3.8+  
**Frontend:** Streamlit 1.24+, Plotly 5.0+  
**Database:** MongoDB 4.0+  
**DevOps:** Docker, pytest, Black, isort

---

## 🎨 Unique Features

1. **Transparency-First** - Complete visibility into every operation performed
2. **Intelligent Type Detection** - Automatic numeric column conversion with placeholder handling
3. **Professional Reporting** - Multi-format outputs (PDF, JSON, CSV) suitable for stakeholders
4. **Enterprise-Grade** - Authentication, audit trails, processing history
5. **Zero-Config Intelligence** - Works out of the box with smart defaults
6. **Modern UX** - Clean Streamlit interface with interactive Plotly visualizations

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
