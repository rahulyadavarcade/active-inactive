from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ── Database Setup ─────────────────────────────────────────────────────────────
DATABASE_URL = "sqlite:///./email_log.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id     = Column(Integer, primary_key=True, index=True)
    email  = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="inactive")


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
class EmailRequest(BaseModel):
    email: str


# ── Helpers ────────────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Endpoints ──────────────────────────────────────────────────────────────────
from fastapi import Depends


@app.post("/api/login")
def login(req: EmailRequest, db=Depends(get_db)):
    """Log in or register a user by email. Returns current user info."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(email=req.email, status="inactive")
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"email": user.email, "status": user.status}


@app.post("/api/activate")
def activate(req: EmailRequest, db=Depends(get_db)):
    """Activate a user. Fails if any other user is already active."""
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
    db.commit()
    db.refresh(user)
    return {"email": user.email, "status": user.status}


@app.get("/api/active_user")
def get_active_user(db=Depends(get_db)):
    """Return the currently active user, or null if none."""
    active_user = db.query(User).filter(User.status == "active").first()
    if active_user:
        return {"email": active_user.email}
    return {"email": None}
