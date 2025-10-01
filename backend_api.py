"""
Backend API для платформы "Конфорка"
FastAPI + PostgreSQL + SQLAlchemy
"""

from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, DECIMAL, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import bcrypt
import jwt
from enum import Enum
import json

# Конфигурация
DATABASE_URL = "postgresql://user:password@localhost/konforka_db"
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Инициализация
app = FastAPI(title="Конфорка API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Модели SQLAlchemy
class UserType(str, Enum):
    RESEARCHER = "researcher"
    MENTOR = "mentor"
    EQUIPMENT_PROVIDER = "equipment_provider"
    ENTERPRISE = "enterprise"
    STUDENT = "student"

class ProjectStage(str, Enum):
    IDEA = "idea"
    PROTOTYPE = "prototype"
    TESTING = "testing"
    COMMERCIALIZATION = "commercialization"
    COMPLETED = "completed"

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    avatar_url = Column(String(500))
    bio = Column(Text)
    
    education = Column(JSON)
    skills = Column(ARRAY(String))
    experience_years = Column(Integer)
    user_type = Column(String(50))
    
    rating = Column(DECIMAL(3, 2), default=0.0)
    completed_projects = Column(Integer, default=0)
    
    social_links = Column(JSON)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    notification_settings = Column(JSON, default={})
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String(1000))
    
    category = Column(String(100))
    tags = Column(ARRAY(String))
    stage = Column(String(50))
    
    required_skills = Column(ARRAY(String))
    max_team_size = Column(Integer)
    
    required_equipment = Column(JSON)
    budget_estimate = Column(DECIMAL(12, 2))
    # Дополнительные структурированные поля проекта (16 полей) в JSON для гибкости
    details = Column(JSON)  # см. Pydantic ProjectDetails ниже
    
    author_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    status = Column(String(50), default=ProjectStatus.ACTIVE)
    
    images = Column(JSON)
    documents = Column(JSON)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    author = relationship("User")

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    role = Column(String(100))
    responsibilities = Column(Text)
    status = Column(String(50), default='pending')
    contribution_score = Column(Integer, default=0)
    
    joined_at = Column(DateTime, default=func.now())
    left_at = Column(DateTime)
    
    project = relationship("Project")
    user = relationship("User")

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    manufacturer = Column(String(200))
    model = Column(String(200))
    
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    owner_type = Column(String(50))
    
    location = Column(JSON)
    specifications = Column(JSON)
    images = Column(JSON)
    
    rental_price_per_hour = Column(DECIMAL(10, 2))
    rental_price_per_day = Column(DECIMAL(10, 2))
    currency = Column(String(3), default='RUB')
    
    availability_calendar = Column(JSON)
    booking_lead_time_hours = Column(Integer, default=24)
    
    required_certifications = Column(ARRAY(String))
    required_training = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EquipmentBooking(Base):
    __tablename__ = "equipment_bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(50), default='pending')
    
    total_cost = Column(DECIMAL(10, 2))
    payment_status = Column(String(50), default='pending')
    
    purpose = Column(Text)
    special_requirements = Column(Text)
    
    user_rating = Column(Integer)
    user_review = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Mentor(Base):
    __tablename__ = "mentors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    expertise_areas = Column(ARRAY(String))
    industry_experience = Column(Integer)
    companies_founded = Column(Integer, default=0)
    
    achievements = Column(Text)
    education_details = Column(Text)
    
    consultation_price = Column(DECIMAL(10, 2))
    currency = Column(String(3), default='RUB')
    consultation_duration_minutes = Column(Integer, default=60)
    
    availability_schedule = Column(JSON)
    
    total_consultations = Column(Integer, default=0)
    average_rating = Column(DECIMAL(3, 2), default=0.0)
    
    articles = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Consultation(Base):
    __tablename__ = "consultations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey('mentors.id'))
    client_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    
    scheduled_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    format = Column(String(50), default='online')
    
    topics = Column(ARRAY(String))
    client_questions = Column(Text)
    
    price = Column(DECIMAL(10, 2))
    currency = Column(String(3), default='RUB')
    payment_status = Column(String(50), default='pending')
    
    status = Column(String(50), default='scheduled')
    
    client_rating = Column(Integer)
    client_review = Column(Text)
    mentor_notes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class RDOrder(Base):
    __tablename__ = "rd_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    technical_requirements = Column(Text)
    expected_outcomes = Column(Text)
    
    category = Column(String(100))
    tags = Column(ARRAY(String))
    
    prize_fund = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), default='RUB')
    number_of_winners = Column(Integer, default=1)
    
    evaluation_criteria = Column(JSON)
    
    submission_deadline = Column(DateTime, nullable=False)
    announcement_date = Column(DateTime)
    
    status = Column(String(50), default='open')
    
    attachments = Column(JSON)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class RDSubmission(Base):
    __tablename__ = "rd_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rd_order_id = Column(UUID(as_uuid=True), ForeignKey('rd_orders.id'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    team_lead_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    solution_description = Column(Text)
    solution_files = Column(JSON)
    
    status = Column(String(50), default='submitted')
    
    score = Column(DECIMAL(5, 2))
    evaluation_feedback = Column(Text)
    
    prize_amount = Column(DECIMAL(12, 2))
    
    submitted_at = Column(DateTime, default=func.now())
    evaluated_at = Column(DateTime)

# Система рейтингов и отзывов
class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    target_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    target_equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'))
    target_mentor_id = Column(UUID(as_uuid=True), ForeignKey('mentors.id'))
    
    review_type = Column(String(50))  # equipment, mentor, user, landlord
    rating = Column(Integer)  # 1-5 звезд
    review_text = Column(Text)
    tags = Column(ARRAY(String))  # Теги для отзывов
    
    is_anonymous = Column(Boolean, default=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    
    created_at = Column(DateTime, default=func.now())

# Система модерации и жалоб
class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    target_type = Column(String(50))  # user, project, review, equipment
    target_id = Column(UUID(as_uuid=True))
    reason = Column(String(50))  # spam, insult, fraud, plagiarism, violation
    description = Column(Text)
    
    status = Column(String(50), default='pending')  # pending, reviewed, resolved
    admin_notes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)

# Система штрафов и нарушений
class Violation(Base):
    __tablename__ = "violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    violation_type = Column(String(50))
    description = Column(Text)
    penalty_type = Column(String(50))  # warning, week_ban, lifetime_ban
    penalty_duration = Column(Integer)  # дни для временных банов
    
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)

# Система бронирования и оплаты
class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    equipment_id = Column(UUID(as_uuid=True), ForeignKey('equipment.id'))
    mentor_id = Column(UUID(as_uuid=True), ForeignKey('mentors.id'))
    
    booking_type = Column(String(50))  # equipment, mentor
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_hours = Column(DECIMAL(5, 2))
    
    # Финансы
    total_amount = Column(DECIMAL(12, 2))
    platform_commission = Column(DECIMAL(12, 2))
    provider_amount = Column(DECIMAL(12, 2))
    
    # Статус платежа
    payment_status = Column(String(50), default='pending')  # pending, frozen, completed, refunded
    payment_frozen = Column(Boolean, default=True)
    frozen_until = Column(DateTime)
    
    # Статус бронирования
    booking_status = Column(String(50), default='active')  # active, completed, cancelled, disputed
    
    # Проект
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    
    # Техническое задание (для оборудования)
    technical_spec = Column(Text)
    spec_approved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Система споров и возвратов
class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey('bookings.id'))
    reporter_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    dispute_type = Column(String(50))  # service_not_provided, quality_issue, no_show
    description = Column(Text)
    evidence_files = Column(JSON)
    
    status = Column(String(50), default='open')  # open, investigating, resolved
    admin_notes = Column(Text)
    resolution = Column(String(50))  # refund_user, pay_provider, partial_refund
    
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)

# Pydantic модели для API
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: UserType
    bio: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_years: Optional[int] = 0
    
    # Дополнительные поля профиля согласно концепции
    education: Optional[List[Dict[str, Any]]] = []  # [{degree, institution, year}]
    achievements: Optional[List[str]] = []  # Достижения
    social_links: Optional[Dict[str, str]] = {}  # {linkedin, github, website}
    location: Optional[str] = None  # Город/регион
    birth_year: Optional[int] = None
    gender: Optional[str] = None
    languages: Optional[List[str]] = []
    certifications: Optional[List[str]] = []
    portfolio_urls: Optional[List[str]] = []
    motivation: Optional[str] = None  # Мотивация участия в проектах

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    user_type: str
    rating: float
    completed_projects: int
    skills: Optional[List[str]]
    bio: Optional[str]
    avatar_url: Optional[str]

class ProjectCreate(BaseModel):
    title: str
    description: str
    short_description: Optional[str] = None
    category: str
    tags: Optional[List[str]] = []
    stage: ProjectStage = ProjectStage.IDEA
    required_skills: Optional[List[str]] = []
    max_team_size: Optional[int] = None
    budget_estimate: Optional[float] = None
    # 16 обязательных полей концепции согласно документу
    problem_statement: str  # 1. Формулировка проблемы
    hypothesis: str  # 2. Гипотеза исследования
    novelty: str  # 3. Научная новизна
    target_market: str  # 4. Целевой рынок
    trl_level: str  # 5. Уровень технологической готовности (TRL)
    goals_milestones: str  # 6. Цели и ключевые вехи
    success_metrics: str  # 7. Метрики успеха
    risks_mitigation: str  # 8. Риски и план их снижения
    required_equipment_details: Optional[List[Dict[str, Any]]] = []  # 9. Требуемое оборудование
    timeline_months: int  # 10. Временной горизонт (месяцы)
    team_roles_required: List[str]  # 11. Требуемые роли в команде
    ip_status: str  # 12. Статус интеллектуальной собственности
    compliance_ethics: Optional[str] = None  # 13. Соответствие нормам и этика
    budget_breakdown: Optional[Dict[str, Any]] = None  # 14. Детализация бюджета
    expected_outcomes: str  # 15. Ожидаемые результаты
    collaboration_needs: Optional[str] = None  # 16. Потребности в коллаборации

class ProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    category: str
    stage: str
    status: str
    author: UserResponse
    created_at: datetime
    required_skills: Optional[List[str]]
    details: Optional[Dict[str, Any]]

class TeamMemberCreate(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    responsibilities: Optional[str] = None

class EquipmentCreate(BaseModel):
    name: str
    description: str
    category: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    rental_price_per_hour: Optional[float] = None
    rental_price_per_day: Optional[float] = None
    location: Dict[str, Any]
    specifications: Optional[Dict[str, Any]] = None

class EquipmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    category: str
    manufacturer: Optional[str]
    rental_price_per_hour: Optional[float]
    rental_price_per_day: Optional[float]
    is_available: bool
    location: Dict[str, Any]

class MentorCreate(BaseModel):
    expertise_areas: List[str]
    industry_experience: int
    consultation_price: float
    consultation_duration_minutes: int = 60
    achievements: Optional[str] = None
    education_details: Optional[str] = None

class MentorResponse(BaseModel):
    id: uuid.UUID
    user: UserResponse
    expertise_areas: List[str]
    industry_experience: int
    consultation_price: float
    average_rating: float
    total_consultations: int

class RDOrderCreate(BaseModel):
    title: str
    description: str
    technical_requirements: Optional[str] = None
    expected_outcomes: Optional[str] = None
    category: str
    tags: Optional[List[str]] = []
    prize_fund: float
    number_of_winners: int = 1
    submission_deadline: datetime
    evaluation_criteria: List[Dict[str, Any]]

class RDOrderResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    category: str
    prize_fund: float
    submission_deadline: datetime
    status: str
    created_at: datetime

# Вспомогательные функции
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# API endpoints
@app.post("/auth/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Проверка существования пользователя
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Создание нового пользователя
    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        user_type=user.user_type,
        bio=user.bio,
        skills=user.skills,
        experience_years=user.experience_years
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/auth/login")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/projects", response_model=List[ProjectResponse])
def get_projects(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    stage: Optional[str] = None,
    sort_by: Optional[str] = Query(None, description="created_at|rating|team_size|stage|category"),
    db: Session = Depends(get_db)
):
    query = db.query(Project).filter(Project.status == ProjectStatus.ACTIVE)
    
    if category:
        query = query.filter(Project.category == category)
    if stage:
        query = query.filter(Project.stage == stage)
    if sort_by == "created_at":
        query = query.order_by(Project.created_at.desc())
    elif sort_by == "team_size":
        query = query.order_by(Project.max_team_size.desc().nullslast())
    elif sort_by == "stage":
        query = query.order_by(Project.stage.asc())
    elif sort_by == "category":
        query = query.order_by(Project.category.asc())
    
    projects = query.offset(skip).limit(limit).all()
    return projects

# API для бронирования
@app.post("/bookings/equipment")
def create_equipment_booking(
    equipment_id: str,
    start_time: str,
    duration_hours: float,
    project_id: str,
    technical_spec: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Создание бронирования оборудования"""
    # Здесь должна быть логика создания бронирования
    # с заморозкой средств на 24 часа
    return {"message": "Бронирование создано", "booking_id": "demo_booking_id"}

@app.post("/bookings/mentor")
def create_mentor_booking(
    mentor_id: str,
    start_time: str,
    duration_hours: float,
    project_id: str,
    consultation_plan: str,
    db: Session = Depends(get_db)
):
    """Создание бронирования консультации с ментором"""
    return {"message": "Консультация забронирована", "booking_id": "demo_booking_id"}

@app.post("/bookings/{booking_id}/dispute")
def create_dispute(
    booking_id: str,
    dispute_type: str,
    description: str,
    db: Session = Depends(get_db)
):
    """Создание спора по бронированию"""
    return {"message": "Спор создан", "dispute_id": "demo_dispute_id"}

@app.get("/bookings/current")
def get_current_bookings(db: Session = Depends(get_db)):
    """Получение текущих бронирований пользователя"""
    return {"bookings": []}

@app.get("/bookings/history")
def get_booking_history(db: Session = Depends(get_db)):
    """Получение истории бронирований"""
    return {"bookings": []}

# API для рейтингов и отзывов
@app.post("/reviews")
def create_review(
    target_type: str,
    target_id: str,
    rating: int,
    review_text: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_anonymous: bool = False,
    db: Session = Depends(get_db)
):
    """Создание отзыва"""
    return {"message": "Отзыв создан", "review_id": "demo_review_id"}

@app.post("/reports")
def create_report(
    target_type: str,
    target_id: str,
    reason: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Создание жалобы"""
    return {"message": "Жалоба создана", "report_id": "demo_report_id"}

@app.post("/projects", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Разделяем стандартные поля и блок details (16 полей)
    project_data = project.dict()
    details_keys = [
        "problem_statement","hypothesis","novelty","target_market","trl_level",
        "goals_milestones","success_metrics","risks_mitigation","required_equipment_details",
        "timeline_months","team_roles_required","ip_status","compliance_ethics",
        "budget_breakdown","expected_outcomes","collaboration_needs"
    ]
    details = {k: project_data.pop(k) for k in details_keys}
    new_project = Project(
        **project_data,
        details=details,
        author_id=current_user.id
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project

@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.post("/projects/{project_id}/join")
def join_project(
    project_id: uuid.UUID,
    role: str,
    responsibilities: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка существования проекта
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Проверка, не является ли пользователь уже участником
    existing_member = db.query(TeamMember).filter(
        TeamMember.project_id == project_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="Already a team member")
    
    # Создание заявки на участие
    team_member = TeamMember(
        project_id=project_id,
        user_id=current_user.id,
        role=role,
        responsibilities=responsibilities,
        status='pending'
    )
    
    db.add(team_member)
    db.commit()
    
    return {"message": "Application submitted successfully"}

@app.get("/equipment", response_model=List[EquipmentResponse])
def get_equipment(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    available_only: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(Equipment)
    
    if available_only:
        query = query.filter(Equipment.is_available == True)
    if category:
        query = query.filter(Equipment.category == category)
    
    equipment = query.offset(skip).limit(limit).all()
    return equipment

@app.post("/equipment", response_model=EquipmentResponse)
def create_equipment(
    equipment: EquipmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_equipment = Equipment(
        **equipment.dict(),
        owner_id=current_user.id,
        owner_type=current_user.user_type
    )
    
    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)
    
    return new_equipment

@app.get("/mentors", response_model=List[MentorResponse])
def get_mentors(
    skip: int = 0,
    limit: int = 10,
    expertise_area: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Mentor).filter(Mentor.is_active == True)
    
    if expertise_area:
        query = query.filter(Mentor.expertise_areas.contains([expertise_area]))
    
    mentors = query.offset(skip).limit(limit).all()
    return mentors

@app.post("/mentors", response_model=MentorResponse)
def create_mentor_profile(
    mentor: MentorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка, не существует ли уже профиль ментора
    existing_mentor = db.query(Mentor).filter(Mentor.user_id == current_user.id).first()
    if existing_mentor:
        raise HTTPException(status_code=400, detail="Mentor profile already exists")
    
    new_mentor = Mentor(
        **mentor.dict(),
        user_id=current_user.id
    )
    
    db.add(new_mentor)
    db.commit()
    db.refresh(new_mentor)
    
    return new_mentor

@app.get("/rd-orders", response_model=List[RDOrderResponse])
def get_rd_orders(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    status: Optional[str] = 'open',
    db: Session = Depends(get_db)
):
    query = db.query(RDOrder)
    
    if status:
        query = query.filter(RDOrder.status == status)
    if category:
        query = query.filter(RDOrder.category == category)
    
    # Фильтрация по дате дедлайна
    query = query.filter(RDOrder.submission_deadline > datetime.utcnow())
    
    orders = query.offset(skip).limit(limit).all()
    return orders

@app.post("/rd-orders", response_model=RDOrderResponse)
def create_rd_order(
    order: RDOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка, что пользователь - предприятие
    if current_user.user_type != 'enterprise':
        raise HTTPException(status_code=403, detail="Only enterprises can create R&D orders")
    
    new_order = RDOrder(
        **order.dict(),
        enterprise_id=current_user.id
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    return new_order

@app.post("/rd-orders/{order_id}/submit")
def submit_rd_solution(
    order_id: uuid.UUID,
    project_id: uuid.UUID,
    solution_description: str,
    solution_files: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка существования заказа
    order = db.query(RDOrder).filter(RDOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="R&D order not found")
    
    # Проверка существования проекта и прав доступа
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Проверка, что пользователь является участником проекта
    team_member = db.query(TeamMember).filter(
        TeamMember.project_id == project_id,
        TeamMember.user_id == current_user.id,
        TeamMember.status == 'active'
    ).first()
    
    if not team_member:
        raise HTTPException(status_code=403, detail="Not a team member of this project")
    
    # Создание заявки
    submission = RDSubmission(
        rd_order_id=order_id,
        project_id=project_id,
        team_lead_id=current_user.id,
        solution_description=solution_description,
        solution_files=solution_files
    )
    
    db.add(submission)
    db.commit()
    
    return {"message": "Solution submitted successfully"}

# Административные endpoints
@app.get("/admin/stats")
def get_platform_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Проверка прав администратора (упрощенная)
    if current_user.email != "admin@konforka.ru":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stats = {
        "total_users": db.query(User).count(),
        "active_projects": db.query(Project).filter(Project.status == ProjectStatus.ACTIVE).count(),
        "total_equipment": db.query(Equipment).count(),
        "active_mentors": db.query(Mentor).filter(Mentor.is_active == True).count(),
        "open_rd_orders": db.query(RDOrder).filter(RDOrder.status == 'open').count(),
        "total_consultations": db.query(Consultation).count(),
        "equipment_bookings": db.query(EquipmentBooking).count()
    }
    
    return stats

# Инициализация базы данных
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)