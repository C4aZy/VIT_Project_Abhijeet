# AI-Powered Code Review & Documentation Assistant

## 🎯 Project Overview

An intelligent code analysis platform that leverages AST parsing, static analysis, and machine learning to provide comprehensive code reviews, security vulnerability detection, complexity analysis, and automated documentation generation.

## ✨ Key Features

### 1. **Code Quality Analysis**
- Cyclomatic complexity measurement
- Maintainability index calculation
- Code smell detection
- Technical debt estimation

### 2. **Security Scanning**
- SQL injection detection
- Hardcoded secrets identification
- Command injection vulnerabilities
- Insecure deserialization warnings
- CWE (Common Weakness Enumeration) mapping

### 3. **Smart Insights**
- Bug probability prediction
- Function complexity scoring
- Code duplication detection
- Missing documentation identification

### 4. **Multi-Language Support**
- Python (fully implemented)
- JavaScript/TypeScript (planned)
- Java, C++, Go, Rust (planned)

### 5. **GitHub Integration**
- Direct repository analysis
- Pull request reviews (planned)
- Continuous monitoring (planned)

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │
│   (Dashboard)   │
└────────┬────────┘
         │
         │ REST API
         ▼
┌─────────────────┐      ┌──────────────────┐
│  FastAPI        │      │   PostgreSQL     │
│  Backend        │◄────►│   Database       │
└────────┬────────┘      └──────────────────┘
         │
         │
    ┌────┴────────────────────┐
    │                         │
    ▼                         ▼
┌─────────────┐      ┌────────────────┐
│  Analyzers  │      │  ML Models     │
│  - AST      │      │  - Bug Pred    │
│  - Security │      │  - CodeBERT    │
│  - Complex  │      │  - Doc Gen     │
└─────────────┘      └────────────────┘
```

## 🚀 Getting Started

### Prerequisites

```bash
- Python 3.9+
- PostgreSQL (or SQLite for development)
- Node.js 16+ (for frontend)
- Git
```

### Backend Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd code-review-assistant/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize database**
```bash
# Database will be created automatically on first run
# Or use Alembic for migrations:
alembic upgrade head
```

6. **Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access API docs**
```
http://localhost:8000/api/v1/docs
```

## 📊 Database Schema

### Core Tables

**users**
- id, email, username, password
- github integration fields

**projects**
- id, user_id, name, description
- source (upload/github), language
- analysis status

**code_files**
- id, project_id, file_path
- complexity_score, maintainability_index
- issue_count

**analyses**
- id, project_id
- quality_score, technical_debt
- complexity metrics, issue counts
- bug probability

**code_issues**
- id, analysis_id, file_id
- severity, category, title, description
- line_number, recommendations

## 🔌 API Endpoints

### Authentication
```
POST /api/v1/auth/register - Register new user
POST /api/v1/auth/login - Login and get token
GET  /api/v1/auth/me - Get current user
```

### Projects
```
POST   /api/v1/projects - Create project
GET    /api/v1/projects - List user projects
GET    /api/v1/projects/{id} - Get project details
DELETE /api/v1/projects/{id} - Delete project
POST   /api/v1/projects/{id}/upload - Upload files
```

### Analysis
```
POST /api/v1/analysis/run/{project_id} - Start analysis
GET  /api/v1/analysis/results/{project_id} - Get results
GET  /api/v1/analysis/status/{project_id} - Check status
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_ast_parser.py -v
```

## 📝 Usage Example

### 1. Register and Login
```python
import requests

# Register
response = requests.post("http://localhost:8000/api/v1/auth/register", json={
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepass123",
    "full_name": "Test User"
})

# Login
response = requests.post("http://localhost:8000/api/v1/auth/login", data={
    "username": "testuser",
    "password": "securepass123"
})
token = response.json()["access_token"]
```

### 2. Create Project and Upload Code
```python
headers = {"Authorization": f"Bearer {token}"}

# Create project
response = requests.post("http://localhost:8000/api/v1/projects", 
    headers=headers,
    json={
        "name": "My Python Project",
        "description": "Test project",
        "source": "upload",
        "primary_language": "python"
    }
)
project_id = response.json()["id"]

# Upload files
files = {"files": open("my_code.py", "rb")}
response = requests.post(
    f"http://localhost:8000/api/v1/projects/{project_id}/upload",
    headers=headers,
    files=files
)
```

### 3. Run Analysis
```python
# Start analysis
response = requests.post(
    f"http://localhost:8000/api/v1/analysis/run/{project_id}",
    headers=headers
)

# Check status
response = requests.get(
    f"http://localhost:8000/api/v1/analysis/status/{project_id}",
    headers=headers
)

# Get results (when completed)
response = requests.get(
    f"http://localhost:8000/api/v1/analysis/results/{project_id}",
    headers=headers
)
results = response.json()
print(f"Quality Score: {results['overall_quality_score']}")
print(f"Issues: {results['critical_issues']} critical, {results['high_issues']} high")
```

## 🎨 Frontend Setup (Coming Soon)

```bash
cd frontend
npm install
npm start
```

## 📈 Analysis Metrics Explained

### Quality Score (0-100)
- Starts at 100
- Deductions for issues and complexity
- 90-100: Excellent
- 70-89: Good
- 50-69: Needs Improvement
- <50: Poor

### Maintainability Index (0-100)
- Based on Halstead complexity
- Higher is better
- >20: Maintainable
- 10-20: Moderate
- <10: Difficult to maintain

### Cyclomatic Complexity
- Measures code branching
- 1-10: Simple
- 11-20: Moderate
- 21-50: Complex
- 50+: Very Complex

### Technical Debt
- Estimated hours to fix issues
- Based on issue severity
- Critical: 4 hours each
- High: 2 hours each
- Medium: 1 hour each

## 🔒 Security Features

- JWT-based authentication
- Password hashing (bcrypt)
- SQL injection prevention
- Input validation
- Rate limiting (planned)
- API key encryption

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- SQLAlchemy (ORM)
- PostgreSQL/SQLite
- Pydantic (validation)

**Analysis Tools:**
- Radon (complexity metrics)
- AST (Python parser)
- Custom security scanner

**Machine Learning:**
- Transformers (CodeBERT)
- scikit-learn
- PyTorch

**Frontend (Planned):**
- React
- TypeScript
- Tailwind CSS
- Chart.js

## 📚 Documentation

- [API Documentation](http://localhost:8000/api/v1/docs)
- [Architecture Guide](docs/architecture.md)
- [ML Models](docs/ml_models.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🎓 For Students

This project demonstrates:
- ✅ Full-stack development
- ✅ RESTful API design
- ✅ Database design & ORM usage
- ✅ Authentication & security
- ✅ Static code analysis
- ✅ Machine learning integration
- ✅ Software architecture patterns
- ✅ Testing & documentation

Perfect for academic portfolios and demonstrating real-world skills!

## 🚀 Future Enhancements

- [ ] ML-powered bug prediction model
- [ ] Automated documentation generation (CodeT5)
- [ ] Real-time collaboration features
- [ ] CI/CD pipeline integration
- [ ] Multi-language support expansion
- [ ] VS Code extension
- [ ] GitHub App integration
- [ ] Team collaboration features
- [ ] Custom rule configuration
- [ ] Historical trend analysis

## 📞 Contact

Your Name - your.email@example.com
Project Link: https://github.com/yourusername/code-review-assistant

---

**Built with ❤️ for better code quality**