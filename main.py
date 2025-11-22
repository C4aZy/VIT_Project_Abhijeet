# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Code Review and Documentation Assistant",
    version="1.0.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.api import auth, projects, analysis

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(projects.router, prefix=f"{settings.API_V1_PREFIX}/projects", tags=["Projects"])
app.include_router(analysis.router, prefix=f"{settings.API_V1_PREFIX}/analysis", tags=["Analysis"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Code Review Assistant API",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"api/v1/auth/login")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    user = AuthService.create_user(db, user_data)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    access_token = AuthService.create_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current user info"""
    user = AuthService.get_current_user(db, token)
    return user


# backend/app/api/projects.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService
from app.api.auth import oauth2_scheme
from app.services.auth_service import AuthService

router = APIRouter()

async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    return AuthService.get_current_user(db, token)

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    project = ProjectService.create_project(db, project_data, user.id)
    return project

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List all projects for current user"""
    projects = ProjectService.get_user_projects(db, user.id)
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get project details"""
    project = ProjectService.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    success = ProjectService.delete_project(db, project_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None

@router.post("/{project_id}/upload")
async def upload_files(
    project_id: int,
    files: List[UploadFile] = File(...),
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Upload code files to project"""
    result = await ProjectService.upload_files(db, project_id, user.id, files)
    return result


# backend/app/api/analysis.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.analysis import AnalysisResponse, AnalysisRequest
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.api.auth import oauth2_scheme
from app.services.auth_service import AuthService

router = APIRouter()

async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    return AuthService.get_current_user(db, token)

@router.post("/run/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_analysis(
    project_id: int,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Start code analysis for a project (runs in background)"""
    orchestrator = AnalysisOrchestrator(db)
    
    # Verify project ownership
    from app.services.project_service import ProjectService
    project = ProjectService.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Run analysis in background
    background_tasks.add_task(orchestrator.run_full_analysis, project_id)
    
    return {
        "message": "Analysis started",
        "project_id": project_id,
        "status": "processing"
    }

@router.get("/results/{project_id}", response_model=AnalysisResponse)
async def get_analysis_results(
    project_id: int,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get analysis results for a project"""
    from app.models.analysis import Analysis
    from app.services.project_service import ProjectService
    
    # Verify project ownership
    project = ProjectService.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get latest analysis
    analysis = db.query(Analysis).filter(
        Analysis.project_id == project_id
    ).order_by(Analysis.created_at.desc()).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this project")
    
    return analysis

@router.get("/status/{project_id}")
async def get_analysis_status(
    project_id: int,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Check analysis status"""
    from app.models.analysis import Analysis
    from app.services.project_service import ProjectService
    
    # Verify project ownership
    project = ProjectService.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get latest analysis
    analysis = db.query(Analysis).filter(
        Analysis.project_id == project_id
    ).order_by(Analysis.created_at.desc()).first()
    
    if not analysis:
        return {"status": "not_started"}
    
    if analysis.completed:
        return {"status": "completed", "analysis_id": analysis.id}
    else:
        return {"status": "processing", "analysis_id": analysis.id}


# backend/app/schemas/project.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.project import ProjectSource, ProjectLanguage

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    source: ProjectSource
    primary_language: Optional[ProjectLanguage] = None
    repo_url: Optional[str] = None
    branch: str = "main"

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    total_files: int
    total_lines: int
    is_analyzed: bool
    last_analyzed: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# backend/app/schemas/analysis.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class AnalysisRequest(BaseModel):
    project_id: int
    analyze_security: bool = True
    analyze_complexity: bool = True
    detect_bugs: bool = True
    generate_docs: bool = True

class AnalysisResponse(BaseModel):
    id: int
    project_id: int
    overall_quality_score: Optional[float]
    maintainability_index: Optional[float]
    technical_debt_hours: Optional[float]
    total_lines: Optional[int]
    avg_complexity: Optional[float]
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    security_vulnerabilities: int
    bug_probability: Optional[float]
    completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# backend/app/services/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.config import settings

class AuthService:
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User:
        """Authenticate user"""
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
    
    @staticmethod
    def create_token_for_user(user: User) -> str:
        """Create JWT token"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )
        return access_token
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Get current user from token"""
        from app.utils.security import decode_access_token
        
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        username: str = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user


# backend/app/utils/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None