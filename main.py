from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
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
        if datetime.utcnow() - active_user.activated_at > timedelta(minutes=3):
            active_user.status = "inactive"
            active_user.activated_at = None
            db.commit()


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.post("/api/login")
def login(req: LoginRequest, db=Depends(get_db)):
    """Log in or register a user by email and username. Returns current user info."""
    check_expiration(db)
    
    # Check if user exists by email
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        # Check if username is already taken
        if not req.username:
             raise HTTPException(status_code=400, detail="Username is required for new users.")
             
        existing_username = db.query(User).filter(User.username == req.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken.")
            
        user = User(email=req.email, username=req.username, status="inactive")
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail="Could not create user.")
    
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
