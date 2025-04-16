from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, String, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
from pydantic import BaseModel
import random
import string
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enum for hash status
class HashStatus(str, enum.Enum):
    ACTIVE = "active"
    ASSIGNED = "assigned"
    USED = "used"
    EXPIRED = "expired"

# Database model
class Hash(Base):
    __tablename__ = "hashes"

    hash = Column(String, primary_key=True, index=True)
    master_promocode = Column(String, index=True)
    status = Column(Enum(HashStatus), default=HashStatus.ACTIVE)
    email = Column(String, nullable=True)
    assigned_date = Column(DateTime, nullable=True)
    used_date = Column(DateTime, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory=".", html=True), name="static")

# Add a root endpoint to serve the index.html
@app.get("/")
async def read_root():
    return FileResponse("index.html")

# Pydantic models for request/response
class GenerateHashesRequest(BaseModel):
    prefix: str
    quantity: int
    masterPromocode: str

class GenerateHashesResponse(BaseModel):
    success: bool
    hashes: list[str]
    masterPromocode: str

class AssignRequest(BaseModel):
    email: str
    prefix: str

class AssignResponse(BaseModel):
    success: bool
    assignedHash: str
    email: str

class ValidateRequest(BaseModel):
    hash: str

class ValidateResponse(BaseModel):
    success: bool

class TranslateRequest(BaseModel):
    hash: str

class TranslateResponse(BaseModel):
    success: bool
    masterPromocode: str

class UseRequest(BaseModel):
    hash: str

class UseResponse(BaseModel):
    success: bool

# Helper function to generate unique hash
def generate_unique_hash(prefix: str, length: int = 6) -> str:
    characters = string.ascii_uppercase + string.digits
    while True:
        hash = prefix + ''.join(random.choices(characters, k=length))
        db = SessionLocal()
        if not db.query(Hash).filter(Hash.hash == hash).first():
            db.close()
            return hash
        db.close()

# Helper function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/generateHashes", response_model=GenerateHashesResponse)
async def generate_hashes(request: GenerateHashesRequest):
    db = SessionLocal()
    hashes = []
    for _ in range(request.quantity):
        hash = generate_unique_hash(request.prefix)
        new_hash = Hash(
            hash=hash,
            master_promocode=request.masterPromocode,
            status=HashStatus.ACTIVE
        )
        db.add(new_hash)
        hashes.append(hash)
    db.commit()
    db.close()
    return GenerateHashesResponse(
        success=True,
        hashes=hashes,
        masterPromocode=request.masterPromocode
    )

@app.post("/assign", response_model=AssignResponse)
async def assign_hash(request: AssignRequest):
    db = SessionLocal()
    
    # Check if email already has an assigned hash
    existing_hash = db.query(Hash).filter(
        Hash.email == request.email,
        Hash.status.in_([HashStatus.ACTIVE, HashStatus.ASSIGNED])
    ).first()
    
    if existing_hash:
        db.close()
        return AssignResponse(
            success=True,
            assignedHash=existing_hash.hash,
            email=request.email
        )
    
    # Find an available hash with the given prefix
    available_hash = db.query(Hash).filter(
        Hash.hash.startswith(request.prefix),
        Hash.status == HashStatus.ACTIVE
    ).first()
    
    if not available_hash:
        db.close()
        raise HTTPException(status_code=404, detail="No available hashes found")
    
    available_hash.status = HashStatus.ASSIGNED
    available_hash.email = request.email
    available_hash.assigned_date = datetime.utcnow()
    
    db.commit()
    db.close()
    
    return AssignResponse(
        success=True,
        assignedHash=available_hash.hash,
        email=request.email
    )

@app.post("/validate", response_model=ValidateResponse)
async def validate_hash(request: ValidateRequest):
    db = SessionLocal()
    hash = db.query(Hash).filter(
        Hash.hash == request.hash,
        Hash.status.in_([HashStatus.ACTIVE, HashStatus.ASSIGNED])
    ).first()
    db.close()
    
    if not hash:
        raise HTTPException(status_code=404, detail="Hash not found or already used")
    
    return ValidateResponse(success=True)

@app.post("/translate", response_model=TranslateResponse)
async def translate_hash(request: TranslateRequest):
    db = SessionLocal()
    hash = db.query(Hash).filter(
        Hash.hash == request.hash,
        Hash.status.in_([HashStatus.ACTIVE, HashStatus.ASSIGNED])
    ).first()
    db.close()
    
    if not hash:
        raise HTTPException(status_code=404, detail="Hash not found or already used")
    
    return TranslateResponse(
        success=True,
        masterPromocode=hash.master_promocode
    )

@app.post("/use", response_model=UseResponse)
async def use_hash(request: UseRequest):
    db = SessionLocal()
    hash = db.query(Hash).filter(
        Hash.hash == request.hash,
        Hash.status.in_([HashStatus.ACTIVE, HashStatus.ASSIGNED])
    ).first()
    
    if not hash:
        db.close()
        raise HTTPException(status_code=404, detail="Hash not found or already used")
    
    hash.status = HashStatus.USED
    hash.used_date = datetime.utcnow()
    
    db.commit()
    db.close()
    
    return UseResponse(success=True) 