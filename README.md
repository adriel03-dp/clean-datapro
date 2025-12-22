# CleanDataPro

**CleanDataPro** is a comprehensive data cleaning and analysis platform that automates CSV data preprocessing, generates detailed reports, and provides an intuitive web interface for data quality management.

## Features

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

### Reporting & Visualization

- **Data Issues Report**: Side-by-side before/after comparison showing all problems found and how they were fixed
  - Visual 3-column Before/After layout showing the entire transformation
  - Column-by-column breakdown of missing values
  - Complete cleaning operations summary
  - Data quality score improvements
- **PDF Reports**: Comprehensive data quality reports with before/after comparisons
- **JSON Summaries**: Machine-readable summaries of cleaning operations
- **Interactive Dashboard**: Streamlit-based web interface with:
  - Real-time data visualization using Plotly charts
  - Missing value analysis (before vs after)
  - File upload and download capabilities
  - Processing status tracking

### API & Integration

- **RESTful API**: FastAPI-based backend with endpoints for:
  - CSV file processing (`POST /api/process`)
  - File downloads (`GET /api/download`)
  - Processing history (`GET /api/runs`)
  - Health checks (`GET /healthz`)
- **MongoDB Integration**: Persistent storage layer for processing history and data retention
- **CORS Support**: Cross-origin resource sharing enabled for frontend integration

## Tech Stack

### Backend

- **FastAPI** (v0.95.0+): Modern, high-performance web framework
- **Uvicorn**: ASGI server with async support
- **Python 3.11**: Core programming language
- **Pandas** (v1.5.0+): Data manipulation and analysis
- **ReportLab** (v4.0.0+): PDF generation
- **Rich** (v13.0.0+): Terminal output formatting
- **PyMongo** (v4.0.0+): MongoDB driver for data persistence
- **APScheduler** (v3.8.0+): Task scheduling
- **python-dotenv**: Environment variable management

### Frontend

- **Streamlit** (v1.24.0+): Interactive web application framework
- **Plotly** (v5.0.0+): Interactive data visualization
- **Requests** (v2.28.0+): HTTP client for API communication
- **Pandas**: Data display and manipulation

### Data Processing

- **Pandas**: Core data processing engine
- **NumPy**: Numerical computing (via Pandas)

### Development Tools

- **pytest**: Testing framework
- **Black**: Code formatter
- **isort**: Import sorting
- **Docker**: Containerization support

## 📁 Project Structure

```
clean-datapro/
├── backend/               # FastAPI backend service
│   ├── src/
│   │   ├── main.py       # FastAPI application entry point
│   │   ├── cleaner.py    # Data cleaning logic
│   │   ├── report_generator.py  # PDF/JSON report generation
│   │   ├── config.py     # Configuration and MongoDB setup
│   │   ├── routes/       # API route handlers
│   │   │   ├── process.py   # CSV processing endpoint
│   │   │   ├── files.py     # File download endpoint
│   │   │   └── runs.py      # Processing history endpoint
│   │   └── models/       # Data models
│   ├── utils/            # Utility functions (logging, etc.)
│   ├── Dockerfile        # Backend container configuration
│   └── requirements.txt  # Backend dependencies
├── frontend/             # Streamlit web interface
│   ├── streamlit_app.py  # Main Streamlit application
│   └── requirements.txt  # Frontend dependencies
├── src/                  # Core library modules
│   ├── cleaner.py        # Standalone data cleaning utilities
│   └── report_generator.py  # Report generation utilities
├── tests/                # Test suite
│   ├── test_cleaner.py
│   └── test_report_generator.py
├── data/                 # Data directory (gitignored)
│   ├── raw/             # Uploaded raw CSV files
│   └── processed/       # Cleaned CSV files
├── reports/              # Generated reports (gitignored)
├── utils/                # Shared utility functions
├── pyproject.toml        # Project configuration (Black, isort)
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Root-level dependencies
└── README.md            # This file
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- MongoDB (local or MongoDB Atlas) for processing history persistence

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/adriel03-dp/clean-datapro.git
cd clean-datapro
```

#### 2. Set Up Backend

```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

#### 3. Set Up Frontend

```bash
cd ../frontend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### Running the Application

#### Start Backend Server

```bash
cd backend
# From repository root
python -m uvicorn backend.src.main:app --reload --port 8000

# Or from backend directory
python -m uvicorn src.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

#### Start Frontend Interface

```bash
cd frontend
streamlit run streamlit_app.py
```

The web interface will open automatically at `http://localhost:8501`

### Using Docker

#### Backend with Docker

```bash
cd backend
docker build -t cleandatapro-backend .
docker run -p 8000:8000 cleandatapro-backend
```

## Usage

### Web Interface - Data Issues Report

1. Open the Streamlit interface at `http://localhost:8501`
2. Upload a CSV file using the file uploader
3. Click **"Process & Clean"** button
4. **See the Data Issues Report** - A prominent section shows:
   - BEFORE: What problems were found (duplicates, missing values, quality score)
   - CLEANING: What operations were performed
   - AFTER: Final results (all issues fixed, 100% quality)
5. Review the 4 detailed analysis tabs:
   - Issues Found - Complete breakdown of problems
   - Missing by Column - Which columns had issues
   - Cleaning Details - What was done step-by-step
   - Final Quality - Before/after quality comparison
6. Download cleaned CSV, PDF report, or JSON summary

**See [DATA_ISSUES_VISUALIZATION_GUIDE.md](DATA_ISSUES_VISUALIZATION_GUIDE.md) for detailed examples**

### API Usage

#### Process CSV File

```bash
curl -X POST "http://localhost:8000/api/process" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@yourfile.csv"
```

Response:

```json
{
  "summary": {
    "original_rows": 1000,
    "cleaned_rows": 950,
    "dropped_duplicates": 50,
    "missing_before_total": 150,
    "missing_after_total": 0,
    "missing_summary_before": [...],
    "missing_summary_after": [...]
  },
  "raw_file": "data/raw/yourfile_abc123.csv",
  "cleaned_file": "data/processed/yourfile_abc123_cleaned.csv",
  "report_file": "reports/yourfile_abc123_report.pdf",
  "json_summary": "reports/yourfile_abc123_summary.json"
}
```

#### Download Files

```bash
# Download cleaned CSV
curl "http://localhost:8000/api/download?kind=processed&filename=yourfile_abc123_cleaned.csv" -o cleaned.csv

# Download PDF report
curl "http://localhost:8000/api/download?kind=reports&filename=yourfile_abc123_report.pdf" -o report.pdf

# Download JSON summary
curl "http://localhost:8000/api/download?kind=reports&filename=yourfile_abc123_summary.json" -o summary.json
```

#### View Processing History

```bash
curl "http://localhost:8000/api/runs?limit=10"
```

### Python Library Usage

```python
from src.cleaner import clean_csv, clean_dataframe
from src.report_generator import generate_pdf_report, save_json_summary
import pandas as pd

# Clean a CSV file
summary = clean_csv("input.csv", "output_cleaned.csv", drop_duplicates=True)

# Or work with DataFrames directly
df = pd.read_csv("input.csv")
cleaned_df, summary = clean_dataframe(df, drop_duplicates=True)

# Generate reports
generate_pdf_report(summary, "report.pdf", title="My Data Report")
save_json_summary(summary, "summary.json")
```

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# MongoDB Connection (Required)
MONGODB_URI=mongodb://localhost:27017/cleandatapro
# or for MongoDB Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/cleandatapro

# Backend URL (for frontend)
CLEAN_DATAPRO_BACKEND=http://localhost:8000
```

### MongoDB Setup (Required)

CleanDataPro requires MongoDB for persistent storage of processing history:

1. **Install MongoDB** - Choose one option:
   - **Local Installation**: Download from https://www.mongodb.com/try/download/community
   - **MongoDB Atlas**: Create a free account at https://www.mongodb.com/cloud/atlas
2. **Configure Connection** - Set the `MONGODB_URI` environment variable in `.env`
3. **Database Setup** - The application will automatically create:
   - Database: `cleandatapro`
   - Collection: `clean_runs` (for processing history)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov=backend/src

# Run specific test file
pytest tests/test_cleaner.py
```

## Development

### Code Formatting

```bash
# Format code with Black
black .

# Sort imports with isort
isort .
```

### Project Configuration

- **Black**: Line length 88, configured in `pyproject.toml`
- **isort**: Black-compatible profile

## API Documentation

Once the backend is running, visit:

- **Interactive API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

## Troubleshooting

### Backend Issues

- **"Address already in use"**: Another process is using port 8000. Stop it or use `--port 8001`
- **"uvicorn not found"**: Ensure virtual environment is activated and dependencies are installed
- **Import errors**: Run from repository root or adjust `PYTHONPATH`

### Frontend Issues

- **Cannot connect to backend**: Ensure backend is running on the correct port
- **Download links not working**: Open links directly in browser instead of Streamlit

### MongoDB Issues

- **Connection failures**: Check `MONGODB_URI` format and network connectivity
- **App cannot start**: MongoDB connection is required - ensure MongoDB is running and `MONGODB_URI` is correctly configured
- **Collection not created**: The app will create the `clean_runs` collection automatically on first use

## License

This project is open source. Please check the repository for license details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Links

- **Repository**: https://github.com/adriel03-dp/clean-datapro
- **Issues**: https://github.com/adriel03-dp/clean-datapro/issues

## Support

For questions and support, please open an issue on GitHub.

---

## Author

**Adriel Perera**

- LinkedIn: [www.linkedin.com/in/adriel-perera](https://www.linkedin.com/in/adriel-perera)
- GitHub: [@adriel03-dp](https://github.com/adriel03-dp)

Made with care by Adriel Perera
