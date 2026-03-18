from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ── Database Setup ─────────────────────────────────────────────────────────────
DATABASE_URL = "sqlite:///./email_log.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id           = Column(Integer, primary_key=True, index=True)
    email        = Column(String, unique=True, index=True, nullable=False)
    username     = Column(String, unique=True, index=True, nullable=False)
    status       = Column(String, default="inactive")
    activated_at = Column(DateTime, nullable=True)


Base.metadata.create_all(bind=engine)

# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(title="Email Log API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return FileResponse("static/index.html")


# ── Pydantic Schemas ───────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    username: str = None  # Optional if logging in existing user


class EmailRequest(BaseModel):
    email: str


class UserCreate(BaseModel):
    email: str
    username: str


# ── Constants ───────────────────────────────────────────────────────────────
ADMIN_EMAILS = ["rahulyadavstevesai@gmail.com", "harshjaiswal.linuxbean@gmail.com"]

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_expiration(db):
    """Check if the currently active user (if any) has expired (3 minutes)."""
    active_user = db.query(User).filter(User.status == "active").first()
    if active_user and active_user.activated_at:
        if datetime.utcnow() - active_user.activated_at > timedelta(minutes=2):
            active_user.status = "inactive"
            active_user.activated_at = None
            db.commit()


def verify_admin(admin_email: str = Header(None)):
    if not admin_email or admin_email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access denied.")
    return admin_email


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.post("/api/login")
def login(req: LoginRequest, db=Depends(get_db)):
    """Log in an existing user by email. Returns current user info."""
    check_expiration(db)
    
    # Check if user exists by email
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        raise HTTPException(
            status_code=403, 
            detail="You are not a member. Please contact the admin to have your account added."
        )
    
    return {"email": user.email, "username": user.username, "status": user.status}


@app.post("/api/activate")
def activate(req: EmailRequest, db=Depends(get_db)):
    """Activate a user. Fails if any other user is already active (after checking expiration)."""
    check_expiration(db)
    # Check for any currently active user
    active_user = db.query(User).filter(User.status == "active").first()
    if active_user and active_user.email != req.email:
        raise HTTPException(
            status_code=409,
            detail=f"User '{active_user.email}' is already active. Please wait."
        )

    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please login first.")

    user.status = "active"
    user.activated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return {"email": user.email, "status": user.status}


@app.post("/api/deactivate")
def deactivate(req: EmailRequest, db=Depends(get_db)):
    """Set a user's status to inactive."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please login first.")

    user.status = "inactive"
    user.activated_at = None
    db.commit()
    db.refresh(user)
    return {"email": user.email, "status": user.status}


@app.get("/api/active_user")
def get_active_user(db=Depends(get_db)):
    """Return the currently active user (after checking expiration), or null if none."""
    check_expiration(db)
    active_user = db.query(User).filter(User.status == "active").first()
    if active_user:
        return {"email": active_user.email, "username": active_user.username}
    return {"email": None, "username": None}


# ── Admin Endpoints ───────────────────────────────────────────────────────────
@app.get("/admin")
def serve_admin():
    return FileResponse("static/admin.html")


@app.get("/api/users")
def list_users(db=Depends(get_db), _=Depends(verify_admin)):
    users = db.query(User).all()
    return [{"email": u.email, "username": u.username, "status": u.status} for u in users]


@app.post("/api/users")
def add_user(req: UserCreate, db=Depends(get_db), _=Depends(verify_admin)):
    # Check if email exists
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already exists.")
    # Check if username exists
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists.")
    
    user = User(email=req.email, username=req.username, status="inactive")
    db.add(user)
    db.commit()
    return {"message": "User added successfully"}


@app.delete("/api/users/{email}")
def delete_user(email: str, db=Depends(get_db), _=Depends(verify_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
