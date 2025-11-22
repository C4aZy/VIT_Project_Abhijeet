# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    github_username = Column(String)
    github_token = Column(String)  # Encrypted
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


# backend/app/models/project.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class ProjectSource(str, enum.Enum):
    UPLOAD = "upload"
    GITHUB = "github"
    GITLAB = "gitlab"

class ProjectLanguage(str, enum.Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    source = Column(Enum(ProjectSource), nullable=False)
    primary_language = Column(Enum(ProjectLanguage))
    
    # Repository info
    repo_url = Column(String)
    branch = Column(String, default="main")
    
    # Storage
    file_path = Column(String)  # Local storage path
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    
    # Status
    is_analyzed = Column(Boolean, default=False)
    last_analyzed = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="projects")
    analyses = relationship("Analysis", back_populates="project", cascade="all, delete-orphan")
    files = relationship("CodeFile", back_populates="project", cascade="all, delete-orphan")


# backend/app/models/code_file.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class CodeFile(Base):
    __tablename__ = "code_files"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_extension = Column(String)
    file_size = Column(Integer)  # in bytes
    lines_of_code = Column(Integer)
    content_hash = Column(String)  # For change detection
    
    # Analysis results
    complexity_score = Column(Integer)
    maintainability_index = Column(Integer)
    has_issues = Column(Boolean, default=False)
    issue_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="files")
    issues = relationship("CodeIssue", back_populates="file", cascade="all, delete-orphan")


# backend/app/models/analysis.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Overall Metrics
    overall_quality_score = Column(Float)  # 0-100
    maintainability_index = Column(Float)
    technical_debt_hours = Column(Float)
    
    # Code Metrics
    total_lines = Column(Integer)
    code_lines = Column(Integer)
    comment_lines = Column(Integer)
    blank_lines = Column(Integer)
    
    # Complexity Metrics
    avg_complexity = Column(Float)
    max_complexity = Column(Integer)
    complex_functions_count = Column(Integer)
    
    # Issue Counts
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Security
    security_vulnerabilities = Column(Integer, default=0)
    
    # ML Predictions
    bug_probability = Column(Float)  # 0-1
    predicted_bugs = Column(Integer)
    
    # Detailed Results (JSON)
    complexity_details = Column(JSON)
    security_details = Column(JSON)
    code_smells = Column(JSON)
    duplicate_code = Column(JSON)
    
    # Documentation
    documentation_coverage = Column(Float)  # percentage
    missing_docstrings = Column(Integer)
    
    # Status
    analysis_duration = Column(Float)  # seconds
    completed = Column(Boolean, default=False)
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="analyses")
    issues = relationship("CodeIssue", back_populates="analysis", cascade="all, delete-orphan")


# backend/app/models/code_issue.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, DateTime, func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class IssueSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IssueCategory(str, enum.Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_SMELL = "code_smell"
    COMPLEXITY = "complexity"
    DOCUMENTATION = "documentation"
    STYLE = "style"
    DUPLICATION = "duplication"

class CodeIssue(Base):
    __tablename__ = "code_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("code_files.id"), nullable=False)
    
    # Issue Details
    severity = Column(Enum(IssueSeverity), nullable=False)
    category = Column(Enum(IssueCategory), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Location
    line_number = Column(Integer)
    column_number = Column(Integer)
    end_line = Column(Integer)
    code_snippet = Column(Text)
    
    # Recommendations
    recommendation = Column(Text)
    fix_suggestion = Column(Text)
    
    # References
    rule_id = Column(String)
    external_link = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("Analysis", back_populates="issues")
    file = relationship("CodeFile", back_populates="issues")


# backend/app/models/documentation.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base

class Documentation(Base):
    __tablename__ = "documentation"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("code_files.id"))
    
    # Documentation Type
    doc_type = Column(String)  # readme, docstring, api_doc, inline_comment
    
    # Content
    title = Column(String)
    content = Column(Text, nullable=False)
    markdown_content = Column(Text)
    
    # Generation Info
    auto_generated = Column(Boolean, default=False)
    confidence_score = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")


# backend/app/models/__init__.py
from app.models.user import User
from app.models.project import Project, ProjectSource, ProjectLanguage
from app.models.code_file import CodeFile
from app.models.analysis import Analysis
from app.models.code_issue import CodeIssue, IssueSeverity, IssueCategory
from app.models.documentation import Documentation

__all__ = [
    "User",
    "Project",
    "ProjectSource",
    "ProjectLanguage",
    "CodeFile",
    "Analysis",
    "CodeIssue",
    "IssueSeverity",
    "IssueCategory",
    "Documentation",
]