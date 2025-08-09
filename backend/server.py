from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import hashlib
import jwt
import random
# Email imports removed for simplicity - using console logging for OTP
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'unicare-secret-key-2025')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="Unicare Polyclinic API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Pydantic Models
class UserRole(str):
    PATIENT = "patient"
    ADMIN = "admin"
    DOCTOR = "doctor"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: str
    role: str = UserRole.PATIENT
    is_verified: bool = False
    is_approved: bool = False  # For patient access to medical records
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: str
    password: str
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    emergency_contact: Optional[str] = None

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str

class OTPRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class OTPVerify(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp: str

class Doctor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    specialty: str
    qualification: str
    experience_years: int
    consultation_fee: float
    is_available: bool = True
    status: str = "available"  # available, busy, on_leave
    schedule: Dict[str, List[str]] = {}  # {"2025-03-20": ["09:00", "09:30", "10:00"]}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Medicine(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    generic_name: Optional[str] = None
    manufacturer: str
    category: str
    price: float
    stock_quantity: int
    description: Optional[str] = None
    dosage_form: str  # tablet, capsule, syrup, etc.
    strength: str  # 500mg, 10ml, etc.
    prescription_required: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LabTest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str
    category: str
    price: float
    estimated_duration: str  # "2-4 hours", "1 day", etc.
    sample_type: str  # blood, urine, etc.
    preparation_required: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LabPackage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    test_ids: List[str]
    original_price: float
    package_price: float
    discount_percentage: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    appointment_date: str
    appointment_time: str
    status: str = "scheduled"  # scheduled, completed, cancelled
    consultation_type: str = "regular"  # regular, follow_up, emergency
    symptoms: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MedicineOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    items: List[Dict[str, Any]]  # [{"medicine_id": "...", "quantity": 2, "price": 100}]
    total_amount: float
    status: str = "pending"  # pending, ready_for_pickup, completed, cancelled
    order_date: datetime = Field(default_factory=datetime.utcnow)
    pickup_date: Optional[datetime] = None

class LabOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    test_ids: List[str] = []
    package_ids: List[str] = []
    total_amount: float
    status: str = "scheduled"  # scheduled, sample_collected, in_progress, completed
    order_date: datetime = Field(default_factory=datetime.utcnow)
    sample_collection_date: Optional[datetime] = None

class MedicalRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    record_type: str  # consultation, lab_report, prescription
    doctor_id: Optional[str] = None
    title: str
    content: str
    attachments: List[str] = []  # file URLs
    date: datetime = Field(default_factory=datetime.utcnow)
    is_confidential: bool = True

# Utility Functions
def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                continue  # Skip MongoDB _id field
            result[key] = serialize_doc(value)
        return result
    return doc

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

async def send_email_otp(email: str, otp: str) -> bool:
    """Mock email OTP sending - replace with actual email service"""
    try:
        # For development, just log the OTP
        print(f"EMAIL OTP for {email}: {otp}")
        # Store OTP in database for verification
        await db.otps.insert_one({
            "email": email,
            "otp": otp,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        })
        return True
    except Exception as e:
        print(f"Email OTP error: {e}")
        return False

async def send_phone_otp(phone: str, otp: str) -> bool:
    """Mock phone OTP sending - replace with Twilio or similar service"""
    try:
        # For development, just log the OTP
        print(f"PHONE OTP for {phone}: {otp}")
        # Store OTP in database for verification
        await db.otps.insert_one({
            "phone": phone,
            "otp": otp,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        })
        return True
    except Exception as e:
        print(f"Phone OTP error: {e}")
        return False

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {"id": user_id, "role": role, "user": user}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Authentication Routes
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": user_data.email} if user_data.email else {},
            {"phone": user_data.phone} if user_data.phone else {}
        ]
    })
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        full_name=user_data.full_name,
        address=user_data.address,
        date_of_birth=user_data.date_of_birth,
        emergency_contact=user_data.emergency_contact
    )
    
    # Store password hash separately
    await db.users.insert_one(user.dict())
    await db.user_passwords.insert_one({
        "user_id": user.id,
        "password_hash": hash_password(user_data.password)
    })
    
    return {"message": "Registration successful", "user_id": user.id}

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    # Find user
    query = {}
    if login_data.email:
        query["email"] = login_data.email
    elif login_data.phone:
        query["phone"] = login_data.phone
    else:
        raise HTTPException(status_code=400, detail="Email or phone required")
    
    user = await db.users.find_one(query)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    password_doc = await db.user_passwords.find_one({"user_id": user["id"]})
    if not password_doc or not verify_password(login_data.password, password_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    token = create_access_token(user["id"], user["role"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_verified": user.get("is_verified", False),
            "is_approved": user.get("is_approved", False)
        }
    }

@api_router.post("/auth/request-otp")
async def request_otp(otp_request: OTPRequest):
    otp = generate_otp()
    
    if otp_request.email:
        success = await send_email_otp(otp_request.email, otp)
        if success:
            return {"message": "OTP sent to email"}
    elif otp_request.phone:
        success = await send_phone_otp(otp_request.phone, otp)
        if success:
            return {"message": "OTP sent to phone"}
    else:
        raise HTTPException(status_code=400, detail="Email or phone required")
    
    raise HTTPException(status_code=500, detail="Failed to send OTP")

@api_router.post("/auth/verify-otp")
async def verify_otp(otp_verify: OTPVerify):
    query = {"otp": otp_verify.otp, "expires_at": {"$gt": datetime.utcnow()}}
    
    if otp_verify.email:
        query["email"] = otp_verify.email
    elif otp_verify.phone:
        query["phone"] = otp_verify.phone
    else:
        raise HTTPException(status_code=400, detail="Email or phone required")
    
    otp_doc = await db.otps.find_one(query)
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Mark user as verified
    user_query = {}
    if otp_verify.email:
        user_query["email"] = otp_verify.email
    else:
        user_query["phone"] = otp_verify.phone
    
    await db.users.update_one(user_query, {"$set": {"is_verified": True}})
    
    # Delete used OTP
    await db.otps.delete_one({"_id": otp_doc["_id"]})
    
    return {"message": "OTP verified successfully"}

# User Routes
@api_router.get("/users/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user["user"]

# Doctor Routes
@api_router.get("/doctors")
async def get_doctors():
    doctors = await db.doctors.find().to_list(1000)
    return doctors

@api_router.get("/doctors/{doctor_id}")
async def get_doctor(doctor_id: str):
    doctor = await db.doctors.find_one({"id": doctor_id})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@api_router.put("/doctors/{doctor_id}/status")
async def update_doctor_status(doctor_id: str, status_data: dict, admin_user: dict = Depends(require_admin)):
    await db.doctors.update_one(
        {"id": doctor_id},
        {"$set": {"status": status_data["status"], "is_available": status_data.get("is_available", True)}}
    )
    return {"message": "Doctor status updated"}

# Medicine Routes
@api_router.get("/medicines")
async def get_medicines():
    medicines = await db.medicines.find().to_list(1000)
    return medicines

@api_router.post("/medicines/order")
async def create_medicine_order(order_data: dict, current_user: dict = Depends(get_current_user)):
    order = MedicineOrder(
        patient_id=current_user["id"],
        items=order_data["items"],
        total_amount=order_data["total_amount"]
    )
    await db.medicine_orders.insert_one(order.dict())
    return {"message": "Medicine order created", "order_id": order.id}

# Lab Test Routes
@api_router.get("/lab-tests")
async def get_lab_tests():
    tests = await db.lab_tests.find().to_list(1000)
    return tests

@api_router.get("/lab-packages")
async def get_lab_packages():
    packages = await db.lab_packages.find().to_list(1000)
    return packages

@api_router.post("/lab-tests/order")
async def create_lab_order(order_data: dict, current_user: dict = Depends(get_current_user)):
    order = LabOrder(
        patient_id=current_user["id"],
        test_ids=order_data.get("test_ids", []),
        package_ids=order_data.get("package_ids", []),
        total_amount=order_data["total_amount"]
    )
    await db.lab_orders.insert_one(order.dict())
    return {"message": "Lab order created", "order_id": order.id}

# Appointment Routes
@api_router.post("/appointments")
async def create_appointment(appointment_data: dict, current_user: dict = Depends(get_current_user)):
    appointment = Appointment(
        patient_id=current_user["id"],
        doctor_id=appointment_data["doctor_id"],
        appointment_date=appointment_data["appointment_date"],
        appointment_time=appointment_data["appointment_time"],
        symptoms=appointment_data.get("symptoms")
    )
    await db.appointments.insert_one(appointment.dict())
    return {"message": "Appointment scheduled", "appointment_id": appointment.id}

@api_router.get("/appointments/my")
async def get_my_appointments(current_user: dict = Depends(get_current_user)):
    appointments = await db.appointments.find({"patient_id": current_user["id"]}).to_list(1000)
    return appointments

# Medical Records Routes
@api_router.get("/medical-records/my")
async def get_my_medical_records(current_user: dict = Depends(get_current_user)):
    user = current_user["user"]
    if not user.get("is_approved", False):
        raise HTTPException(status_code=403, detail="Medical record access not approved by admin")
    
    records = await db.medical_records.find({"patient_id": current_user["id"]}).to_list(1000)
    return records

# Admin Routes
@api_router.get("/admin/patients")
async def get_patients(admin_user: dict = Depends(require_admin)):
    patients = await db.users.find({"role": "patient"}).to_list(1000)
    return patients

@api_router.put("/admin/patients/{patient_id}/approve")
async def approve_patient(patient_id: str, admin_user: dict = Depends(require_admin)):
    await db.users.update_one({"id": patient_id}, {"$set": {"is_approved": True}})
    return {"message": "Patient approved for medical record access"}

@api_router.post("/admin/lab-packages")
async def create_lab_package(package_data: dict, admin_user: dict = Depends(require_admin)):
    package = LabPackage(**package_data)
    await db.lab_packages.insert_one(package.dict())
    return {"message": "Lab package created", "package_id": package.id}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Create admin user if not exists
    admin_user = await db.users.find_one({"email": "admin@unicarepolyclinic.com"})
    if not admin_user:
        admin = User(
            email="admin@unicarepolyclinic.com",
            full_name="Administrator",
            role=UserRole.ADMIN,
            is_verified=True,
            is_approved=True
        )
        await db.users.insert_one(admin.dict())
        await db.user_passwords.insert_one({
            "user_id": admin.id,
            "password_hash": hash_password("admin-007")
        })
        logger.info("Admin user created with email: admin@unicarepolyclinic.com")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()