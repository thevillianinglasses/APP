from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, BackgroundTasks
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
from twilio.rest import Client
import asyncio

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

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')  # Will be set by user
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')    # Will be set by user
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER') # Will be set by user

# Initialize Twilio client if credentials are available
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        print(f"Twilio initialization failed: {e}")

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

class DoctorScheduleTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doctor_id: str
    template_name: str
    schedule_type: str = "weekly"  # daily, weekly, monthly
    days_of_week: List[int] = []  # [1,2,3,4,5] for Mon-Fri, 0=Sunday, 6=Saturday
    start_time: str  # "09:00"
    end_time: str    # "17:00"
    slot_duration: int = 30  # minutes
    break_times: List[Dict[str, str]] = []  # [{"start": "13:00", "end": "14:00"}]
    is_active: bool = True
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DoctorLeave(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doctor_id: str
    leave_type: str = "sick"  # sick, vacation, emergency, holiday
    start_date: str
    end_date: str
    reason: Optional[str] = None
    status: str = "approved"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Holiday(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    date: str
    is_working_day: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # medicine, lab_equipment, lab_supply
    current_stock: int
    minimum_stock: int
    unit: str  # pieces, ml, grams, etc.
    cost_per_unit: float
    supplier: Optional[str] = None
    expiry_date: Optional[str] = None
    location: Optional[str] = None  # pharmacy, lab_room_1, etc.
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StockTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inventory_item_id: str
    transaction_type: str  # purchase, usage, adjustment, expired
    quantity: int
    cost_per_unit: Optional[float] = None
    total_cost: Optional[float] = None
    notes: Optional[str] = None
    performed_by: str  # admin user_id
    transaction_date: datetime = Field(default_factory=datetime.utcnow)

class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    campaign_type: str = "discount"  # discount, buy_one_get_one, festive_offer
    discount_percentage: Optional[float] = None
    applicable_to: str = "medicines"  # medicines, lab_tests, all
    applicable_items: List[str] = []  # specific item IDs, empty means all
    start_date: str
    end_date: str
    is_active: bool = True
    usage_limit: Optional[int] = None  # max uses per campaign
    usage_count: int = 0
    created_by: str  # admin user_id
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    notification_type: str = "appointment"  # appointment, inventory, campaign, system
    is_read: bool = False
    data: Optional[Dict[str, Any]] = {}  # additional data like appointment_id
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    appointment_id: str
    rating: int  # 1-5 stars
    comment: Optional[str] = None
    feedback_categories: Dict[str, int] = {}  # {"professionalism": 5, "waiting_time": 3}
    is_anonymous: bool = False
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

async def send_sms_notification(phone: str, message: str) -> bool:
    """Send SMS notification using Twilio"""
    try:
        if not twilio_client or not TWILIO_PHONE_NUMBER:
            print(f"SMS MOCK - To {phone}: {message}")
            return True
        
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        print(f"SMS sent successfully: {message.sid}")
        return True
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return False

async def schedule_appointment_notifications(appointment_id: str):
    """Schedule notifications for an appointment"""
    try:
        appointment = await db.appointments.find_one({"id": appointment_id})
        if not appointment:
            return
        
        patient = await db.users.find_one({"id": appointment["patient_id"]})
        if not patient:
            return
        
        # Parse appointment datetime
        appointment_datetime = datetime.strptime(
            f"{appointment['appointment_date']} {appointment['appointment_time']}", 
            "%Y-%m-%d %H:%M"
        )
        
        # Schedule 1-hour before SMS notification
        sms_time = appointment_datetime - timedelta(hours=1)
        
        if sms_time > datetime.utcnow():
            # Create notification record
            notification = Notification(
                user_id=patient["id"],
                title="Appointment Reminder",
                message=f"Your appointment is in 1 hour at {appointment['appointment_time']}",
                notification_type="appointment",
                scheduled_for=sms_time,
                data={"appointment_id": appointment_id, "type": "sms_reminder"}
            )
            await db.notifications.insert_one(notification.dict())
        
        # Create in-app notifications for 2 hours and 10 minutes before
        for hours, minutes in [(2, 0), (0, 10)]:
            notification_time = appointment_datetime - timedelta(hours=hours, minutes=minutes)
            if notification_time > datetime.utcnow():
                notification = Notification(
                    user_id=patient["id"],
                    title="Appointment Reminder" if hours > 0 else "Appointment Starting Soon",
                    message=f"Your appointment is {'in 2 hours' if hours > 0 else 'in 10 minutes'}",
                    notification_type="appointment",
                    scheduled_for=notification_time,
                    data={"appointment_id": appointment_id, "type": "in_app_reminder"}
                )
                await db.notifications.insert_one(notification.dict())
        
    except Exception as e:
        print(f"Error scheduling notifications: {e}")

async def process_scheduled_notifications():
    """Background task to process scheduled notifications"""
    try:
        current_time = datetime.utcnow()
        
        # Find notifications that are due
        due_notifications = await db.notifications.find({
            "scheduled_for": {"$lte": current_time},
            "sent_at": None
        }).to_list(100)
        
        for notification in due_notifications:
            try:
                # Send SMS if it's an SMS notification
                if notification.get("data", {}).get("type") == "sms_reminder":
                    patient = await db.users.find_one({"id": notification["user_id"]})
                    if patient and patient.get("phone"):
                        await send_sms_notification(patient["phone"], notification["message"])
                
                # Mark as sent
                await db.notifications.update_one(
                    {"id": notification["id"]},
                    {"$set": {"sent_at": current_time}}
                )
                
            except Exception as e:
                print(f"Error processing notification {notification['id']}: {e}")
                
    except Exception as e:
        print(f"Error in process_scheduled_notifications: {e}")

async def create_admin_daily_reminder():
    """Create daily booking reminder for admin"""
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        appointments = await db.appointments.find({"appointment_date": today}).to_list(1000)
        
        if appointments:
            admin_users = await db.users.find({"role": "admin"}).to_list(10)
            for admin in admin_users:
                notification = Notification(
                    user_id=admin["id"],
                    title="Daily Booking Reminder",
                    message=f"You have {len(appointments)} appointments scheduled for today",
                    notification_type="system",
                    data={"appointment_count": len(appointments), "date": today}
                )
                await db.notifications.insert_one(notification.dict())
                
    except Exception as e:
        print(f"Error creating admin daily reminder: {e}")

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

# Basic Routes
@api_router.get("/")
async def root():
    return {"message": "Unicare Polyclinic API is running", "status": "success"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

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
    return serialize_doc(current_user["user"])

# Doctor Routes
@api_router.get("/doctors")
async def get_doctors():
    doctors = await db.doctors.find().to_list(1000)
    return [serialize_doc(doc) for doc in doctors]

@api_router.get("/doctors/{doctor_id}")
async def get_doctor(doctor_id: str):
    doctor = await db.doctors.find_one({"id": doctor_id})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return serialize_doc(doctor)

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
    return [serialize_doc(doc) for doc in medicines]

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
    return [serialize_doc(doc) for doc in tests]

@api_router.get("/lab-packages")
async def get_lab_packages():
    packages = await db.lab_packages.find().to_list(1000)
    return [serialize_doc(doc) for doc in packages]

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
async def create_appointment(appointment_data: dict, current_user: dict = Depends(get_current_user), background_tasks: BackgroundTasks = BackgroundTasks()):
    appointment = Appointment(
        patient_id=current_user["id"],
        doctor_id=appointment_data["doctor_id"],
        appointment_date=appointment_data["appointment_date"],
        appointment_time=appointment_data["appointment_time"],
        symptoms=appointment_data.get("symptoms")
    )
    await db.appointments.insert_one(appointment.dict())
    
    # Schedule notifications for this appointment
    background_tasks.add_task(schedule_appointment_notifications, appointment.id)
    
    return {"message": "Appointment scheduled", "appointment_id": appointment.id}

@api_router.get("/appointments/my")
async def get_my_appointments(current_user: dict = Depends(get_current_user)):
    appointments = await db.appointments.find({"patient_id": current_user["id"]}).to_list(1000)
    return [serialize_doc(doc) for doc in appointments]

# Medical Records Routes
@api_router.get("/medical-records/my")
async def get_my_medical_records(current_user: dict = Depends(get_current_user)):
    user = current_user["user"]
    if not user.get("is_approved", False):
        raise HTTPException(status_code=403, detail="Medical record access not approved by admin")
    
    records = await db.medical_records.find({"patient_id": current_user["id"]}).to_list(1000)
    return [serialize_doc(doc) for doc in records]

# Admin Routes
@api_router.get("/admin/patients")
async def get_patients(admin_user: dict = Depends(require_admin)):
    patients = await db.users.find({"role": "patient"}).to_list(1000)
    return [serialize_doc(doc) for doc in patients]

@api_router.put("/admin/patients/{patient_id}/approve")
async def approve_patient(patient_id: str, admin_user: dict = Depends(require_admin)):
    await db.users.update_one({"id": patient_id}, {"$set": {"is_approved": True}})
    return {"message": "Patient approved for medical record access"}

@api_router.post("/admin/lab-packages")
async def create_lab_package(package_data: dict, admin_user: dict = Depends(require_admin)):
    package = LabPackage(**package_data)
    await db.lab_packages.insert_one(package.dict())
    return {"message": "Lab package created", "package_id": package.id}

# Advanced Doctor Scheduling Routes
@api_router.post("/admin/doctor-schedule-template")
async def create_schedule_template(template_data: dict, admin_user: dict = Depends(require_admin)):
    template = DoctorScheduleTemplate(**template_data)
    await db.doctor_schedule_templates.insert_one(template.dict())
    return {"message": "Schedule template created", "template_id": template.id}

@api_router.get("/admin/doctor-schedule-templates/{doctor_id}")
async def get_doctor_schedule_templates(doctor_id: str, admin_user: dict = Depends(require_admin)):
    templates = await db.doctor_schedule_templates.find({"doctor_id": doctor_id}).to_list(1000)
    return [serialize_doc(template) for template in templates]

@api_router.put("/admin/doctor-schedule-template/{template_id}")
async def update_schedule_template(template_id: str, template_data: dict, admin_user: dict = Depends(require_admin)):
    await db.doctor_schedule_templates.update_one(
        {"id": template_id},
        {"$set": template_data}
    )
    return {"message": "Schedule template updated"}

@api_router.post("/admin/generate-doctor-schedule")
async def generate_doctor_schedule(generation_data: dict, admin_user: dict = Depends(require_admin)):
    """Generate doctor schedule based on template for a date range"""
    doctor_id = generation_data["doctor_id"]
    template_id = generation_data["template_id"]
    start_date = generation_data["start_date"]
    end_date = generation_data["end_date"]
    
    # Get template
    template = await db.doctor_schedule_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Generate slots based on template
    from datetime import datetime, timedelta
    import calendar
    
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    
    generated_slots = {}
    
    while current_date <= end_date_obj:
        weekday = current_date.weekday()  # 0=Monday, 6=Sunday
        
        # Check if this day is in template
        if weekday in template.get("days_of_week", []):
            # Check for holidays
            holiday = await db.holidays.find_one({"date": current_date.strftime("%Y-%m-%d")})
            if holiday and not holiday.get("is_working_day", False):
                current_date += timedelta(days=1)
                continue
                
            # Check for doctor leave
            leave = await db.doctor_leaves.find_one({
                "doctor_id": doctor_id,
                "start_date": {"$lte": current_date.strftime("%Y-%m-%d")},
                "end_date": {"$gte": current_date.strftime("%Y-%m-%d")},
                "status": "approved"
            })
            if leave:
                current_date += timedelta(days=1)
                continue
            
            # Generate time slots
            start_time = datetime.strptime(template["start_time"], "%H:%M").time()
            end_time = datetime.strptime(template["end_time"], "%H:%M").time()
            slot_duration = template.get("slot_duration", 30)
            
            slots = []
            current_time = datetime.combine(current_date.date(), start_time)
            end_datetime = datetime.combine(current_date.date(), end_time)
            
            while current_time < end_datetime:
                # Check if current time falls in break time
                is_break = False
                for break_time in template.get("break_times", []):
                    break_start = datetime.strptime(break_time["start"], "%H:%M").time()
                    break_end = datetime.strptime(break_time["end"], "%H:%M").time()
                    if break_start <= current_time.time() < break_end:
                        is_break = True
                        break
                
                if not is_break:
                    slots.append(current_time.strftime("%H:%M"))
                
                current_time += timedelta(minutes=slot_duration)
            
            generated_slots[current_date.strftime("%Y-%m-%d")] = slots
        
        current_date += timedelta(days=1)
    
    # Update doctor's schedule
    await db.doctors.update_one(
        {"id": doctor_id},
        {"$set": {"schedule": generated_slots}}
    )
    
    return {"message": "Doctor schedule generated successfully", "generated_dates": list(generated_slots.keys())}

@api_router.post("/admin/doctor-leave")
async def create_doctor_leave(leave_data: dict, admin_user: dict = Depends(require_admin)):
    leave = DoctorLeave(**leave_data)
    await db.doctor_leaves.insert_one(leave.dict())
    return {"message": "Doctor leave created", "leave_id": leave.id}

@api_router.get("/admin/doctor-leaves/{doctor_id}")
async def get_doctor_leaves(doctor_id: str, admin_user: dict = Depends(require_admin)):
    leaves = await db.doctor_leaves.find({"doctor_id": doctor_id}).to_list(1000)
    return [serialize_doc(leave) for leave in leaves]

@api_router.post("/admin/holidays")
async def create_holiday(holiday_data: dict, admin_user: dict = Depends(require_admin)):
    holiday = Holiday(**holiday_data)
    await db.holidays.insert_one(holiday.dict())
    return {"message": "Holiday created", "holiday_id": holiday.id}

@api_router.get("/admin/holidays")
async def get_holidays(admin_user: dict = Depends(require_admin)):
    holidays = await db.holidays.find().to_list(1000)
    return [serialize_doc(holiday) for holiday in holidays]

# Inventory Management Routes
@api_router.post("/admin/inventory")
async def create_inventory_item(item_data: dict, admin_user: dict = Depends(require_admin)):
    item = InventoryItem(**item_data)
    await db.inventory_items.insert_one(item.dict())
    return {"message": "Inventory item created", "item_id": item.id}

@api_router.get("/admin/inventory")
async def get_inventory_items(category: str = None, admin_user: dict = Depends(require_admin)):
    query = {"category": category} if category else {}
    items = await db.inventory_items.find(query).to_list(1000)
    return [serialize_doc(item) for item in items]

@api_router.put("/admin/inventory/{item_id}")
async def update_inventory_item(item_id: str, item_data: dict, admin_user: dict = Depends(require_admin)):
    item_data["last_updated"] = datetime.utcnow()
    await db.inventory_items.update_one({"id": item_id}, {"$set": item_data})
    return {"message": "Inventory item updated"}

@api_router.post("/admin/inventory/{item_id}/stock-transaction")
async def create_stock_transaction(item_id: str, transaction_data: dict, admin_user: dict = Depends(require_admin)):
    # Create transaction record
    transaction = StockTransaction(
        inventory_item_id=item_id,
        performed_by=admin_user["id"],
        **transaction_data
    )
    await db.stock_transactions.insert_one(transaction.dict())
    
    # Update inventory stock
    if transaction.transaction_type in ["purchase", "adjustment"]:
        stock_change = transaction.quantity
    elif transaction.transaction_type in ["usage", "expired"]:
        stock_change = -transaction.quantity
    else:
        stock_change = 0
    
    await db.inventory_items.update_one(
        {"id": item_id},
        {
            "$inc": {"current_stock": stock_change},
            "$set": {"last_updated": datetime.utcnow()}
        }
    )
    
    return {"message": "Stock transaction recorded", "transaction_id": transaction.id}

@api_router.get("/admin/inventory/low-stock")
async def get_low_stock_items(admin_user: dict = Depends(require_admin)):
    # Items where current_stock <= minimum_stock
    pipeline = [
        {"$match": {"$expr": {"$lte": ["$current_stock", "$minimum_stock"]}}},
        {"$sort": {"current_stock": 1}}
    ]
    items = await db.inventory_items.aggregate(pipeline).to_list(1000)
    return [serialize_doc(item) for item in items]

# Campaign Management Routes
@api_router.post("/admin/campaigns")
async def create_campaign(campaign_data: dict, admin_user: dict = Depends(require_admin)):
    campaign = Campaign(
        created_by=admin_user["id"],
        **campaign_data
    )
    await db.campaigns.insert_one(campaign.dict())
    return {"message": "Campaign created", "campaign_id": campaign.id}

@api_router.get("/admin/campaigns")
async def get_campaigns(admin_user: dict = Depends(require_admin)):
    campaigns = await db.campaigns.find().to_list(1000)
    return [serialize_doc(campaign) for campaign in campaigns]

@api_router.put("/admin/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, campaign_data: dict, admin_user: dict = Depends(require_admin)):
    await db.campaigns.update_one({"id": campaign_id}, {"$set": campaign_data})
    return {"message": "Campaign updated"}

@api_router.get("/campaigns/active")
async def get_active_campaigns():
    """Get active campaigns for patients to see"""
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    campaigns = await db.campaigns.find({
        "is_active": True,
        "start_date": {"$lte": today},
        "end_date": {"$gte": today}
    }).to_list(1000)
    
    return [serialize_doc(campaign) for campaign in campaigns]

# Notification Routes
@api_router.post("/admin/notifications")
async def create_notification(notification_data: dict, admin_user: dict = Depends(require_admin)):
    notification = Notification(**notification_data)
    await db.notifications.insert_one(notification.dict())
    return {"message": "Notification created", "notification_id": notification.id}

@api_router.get("/notifications/my")
async def get_my_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find({
        "user_id": current_user["id"]
    }).sort("created_at", -1).to_list(50)
    return [serialize_doc(notification) for notification in notifications]

@api_router.put("/notifications/{notification_id}/mark-read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user["id"]},
        {"$set": {"is_read": True}}
    )
    return {"message": "Notification marked as read"}

@api_router.get("/admin/notifications/stats")
async def get_notification_stats(admin_user: dict = Depends(require_admin)):
    """Get notification statistics for admin dashboard"""
    total_notifications = await db.notifications.count_documents({})
    unread_notifications = await db.notifications.count_documents({"is_read": False})
    pending_sms = await db.notifications.count_documents({
        "notification_type": "appointment",
        "sent_at": None,
        "scheduled_for": {"$lte": datetime.utcnow()}
    })
    
    return {
        "total_notifications": total_notifications,
        "unread_notifications": unread_notifications,
        "pending_sms": pending_sms
    }

# Feedback Routes  
@api_router.post("/feedback")
async def submit_feedback(feedback_data: dict, current_user: dict = Depends(get_current_user)):
    feedback = Feedback(
        patient_id=current_user["id"],
        **feedback_data
    )
    await db.feedback.insert_one(feedback.dict())
    return {"message": "Feedback submitted successfully", "feedback_id": feedback.id}

@api_router.get("/admin/feedback")
async def get_all_feedback(admin_user: dict = Depends(require_admin)):
    feedback_list = await db.feedback.find().sort("created_at", -1).to_list(1000)
    return [serialize_doc(feedback) for feedback in feedback_list]

@api_router.get("/admin/feedback/stats")
async def get_feedback_stats(admin_user: dict = Depends(require_admin)):
    """Get feedback statistics for admin dashboard"""
    pipeline = [
        {"$group": {
            "_id": "$doctor_id",
            "average_rating": {"$avg": "$rating"},
            "total_feedback": {"$sum": 1}
        }},
        {"$lookup": {
            "from": "doctors",
            "localField": "_id", 
            "foreignField": "id",
            "as": "doctor"
        }},
        {"$unwind": "$doctor"},
        {"$project": {
            "doctor_name": "$doctor.name",
            "average_rating": {"$round": ["$average_rating", 2]},
            "total_feedback": 1
        }}
    ]
    
    stats = await db.feedback.aggregate(pipeline).to_list(1000)
    return stats

# Daily Booking Reminders for Admin
@api_router.get("/admin/daily-bookings")
async def get_daily_bookings(date: str = None, admin_user: dict = Depends(require_admin)):
    """Get all bookings for a specific date (default: today)"""
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    
    appointments = await db.appointments.find({"appointment_date": date}).to_list(1000)
    
    # Enrich with patient and doctor details
    enriched_appointments = []
    for appointment in appointments:
        patient = await db.users.find_one({"id": appointment["patient_id"]})
        doctor = await db.doctors.find_one({"id": appointment["doctor_id"]})
        
        enriched_appointments.append({
            **serialize_doc(appointment),
            "patient_name": patient.get("full_name") if patient else "Unknown",
            "patient_phone": patient.get("phone") if patient else None,
            "doctor_name": doctor.get("name") if doctor else "Unknown"
        })
    
    return enriched_appointments

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