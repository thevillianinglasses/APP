import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid

# Load environment variables
load_dotenv('.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def seed_database():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Seeding database with mock data...")
    
    # Clear existing data (except users and passwords)
    collections_to_clear = ['doctors', 'medicines', 'lab_tests', 'lab_packages', 'medical_records']
    for collection_name in collections_to_clear:
        await db[collection_name].delete_many({})
    
    # Seed Doctors
    doctors_data = [
        {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "name": "Dr. Rajesh Kumar",
            "specialty": "General Medicine",
            "qualification": "MBBS, MD",
            "experience_years": 15,
            "consultation_fee": 500.0,
            "is_available": True,
            "status": "available",
            "schedule": {
                "2025-03-20": ["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00"],
                "2025-03-21": ["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00"],
                "2025-03-22": ["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00"]
            },
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "name": "Dr. Priya Sharma",
            "specialty": "Cardiology",
            "qualification": "MBBS, MD (Cardiology)",
            "experience_years": 12,
            "consultation_fee": 800.0,
            "is_available": True,
            "status": "available",
            "schedule": {
                "2025-03-20": ["10:00", "10:30", "11:00", "11:30", "16:00", "16:30", "17:00"],
                "2025-03-21": ["10:00", "10:30", "11:00", "11:30", "16:00", "16:30", "17:00"],
                "2025-03-22": ["10:00", "10:30", "11:00", "11:30", "16:00", "16:30", "17:00"]
            },
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "name": "Dr. Amit Patel",
            "specialty": "Orthopedics",
            "qualification": "MBBS, MS (Orthopedics)",
            "experience_years": 18,
            "consultation_fee": 700.0,
            "is_available": True,
            "status": "available",
            "schedule": {
                "2025-03-20": ["09:30", "10:00", "10:30", "11:00", "15:00", "15:30", "16:00"],
                "2025-03-21": ["09:30", "10:00", "10:30", "11:00", "15:00", "15:30", "16:00"],
                "2025-03-22": ["09:30", "10:00", "10:30", "11:00", "15:00", "15:30", "16:00"]
            },
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "name": "Dr. Sunita Reddy",
            "specialty": "Pediatrics",
            "qualification": "MBBS, MD (Pediatrics)",
            "experience_years": 10,
            "consultation_fee": 600.0,
            "is_available": False,
            "status": "on_leave",
            "schedule": {},
            "created_at": datetime.utcnow()
        }
    ]
    
    await db.doctors.insert_many(doctors_data)
    print(f"Inserted {len(doctors_data)} doctors")
    
    # Seed Medicines
    medicines_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Paracetamol",
            "generic_name": "Acetaminophen",
            "manufacturer": "Sun Pharma",
            "category": "Analgesic",
            "price": 25.0,
            "stock_quantity": 500,
            "description": "Pain reliever and fever reducer",
            "dosage_form": "Tablet",
            "strength": "500mg",
            "prescription_required": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Amoxicillin",
            "generic_name": "Amoxicillin",
            "manufacturer": "Cipla",
            "category": "Antibiotic",
            "price": 120.0,
            "stock_quantity": 200,
            "description": "Broad-spectrum antibiotic",
            "dosage_form": "Capsule",
            "strength": "250mg",
            "prescription_required": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Omeprazole",
            "generic_name": "Omeprazole",
            "manufacturer": "Dr. Reddy's",
            "category": "Antacid",
            "price": 85.0,
            "stock_quantity": 150,
            "description": "Proton pump inhibitor for acid reflux",
            "dosage_form": "Capsule",
            "strength": "20mg",
            "prescription_required": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Cetirizine",
            "generic_name": "Cetirizine HCl",
            "manufacturer": "Ranbaxy",
            "category": "Antihistamine",
            "price": 35.0,
            "stock_quantity": 300,
            "description": "Allergy relief medication",
            "dosage_form": "Tablet",
            "strength": "10mg",
            "prescription_required": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Metformin",
            "generic_name": "Metformin HCl",
            "manufacturer": "USV",
            "category": "Antidiabetic",
            "price": 95.0,
            "stock_quantity": 180,
            "description": "Blood sugar control medication",
            "dosage_form": "Tablet",
            "strength": "500mg",
            "prescription_required": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    await db.medicines.insert_many(medicines_data)
    print(f"Inserted {len(medicines_data)} medicines")
    
    # Seed Lab Tests
    lab_tests_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Complete Blood Count (CBC)",
            "code": "CBC001",
            "category": "Hematology",
            "price": 300.0,
            "estimated_duration": "2-4 hours",
            "sample_type": "Blood",
            "preparation_required": "No fasting required",
            "description": "Comprehensive blood analysis including WBC, RBC, platelets",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Lipid Profile",
            "code": "LIP001",
            "category": "Biochemistry",
            "price": 450.0,
            "estimated_duration": "4-6 hours",
            "sample_type": "Blood",
            "preparation_required": "12-hour fasting required",
            "description": "Cholesterol and triglyceride levels analysis",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Blood Glucose (Fasting)",
            "code": "GLU001",
            "category": "Biochemistry",
            "price": 150.0,
            "estimated_duration": "2 hours",
            "sample_type": "Blood",
            "preparation_required": "8-12 hour fasting required",
            "description": "Fasting blood sugar level test",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Thyroid Function Test (TFT)",
            "code": "THY001",
            "category": "Endocrinology",
            "price": 600.0,
            "estimated_duration": "1 day",
            "sample_type": "Blood",
            "preparation_required": "No special preparation",
            "description": "TSH, T3, T4 hormone levels",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Urine Routine Examination",
            "code": "URE001",
            "category": "Pathology",
            "price": 200.0,
            "estimated_duration": "1-2 hours",
            "sample_type": "Urine",
            "preparation_required": "Morning first sample preferred",
            "description": "Comprehensive urine analysis",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Liver Function Test (LFT)",
            "code": "LFT001",
            "category": "Biochemistry",
            "price": 500.0,
            "estimated_duration": "4-6 hours",
            "sample_type": "Blood",
            "preparation_required": "No fasting required",
            "description": "SGOT, SGPT, Bilirubin, Albumin levels",
            "created_at": datetime.utcnow()
        }
    ]
    
    await db.lab_tests.insert_many(lab_tests_data)
    print(f"Inserted {len(lab_tests_data)} lab tests")
    
    # Get test IDs for packages
    tests = await db.lab_tests.find().to_list(1000)
    test_ids = [test["id"] for test in tests]
    
    # Seed Lab Packages
    lab_packages_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Basic Health Checkup",
            "description": "Essential tests for general health monitoring",
            "test_ids": test_ids[:3],  # CBC, Lipid Profile, Blood Glucose
            "original_price": 900.0,
            "package_price": 750.0,
            "discount_percentage": 16.67,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Comprehensive Health Package",
            "description": "Complete body checkup with all essential tests",
            "test_ids": test_ids[:5],  # All except LFT
            "original_price": 1650.0,
            "package_price": 1300.0,
            "discount_percentage": 21.21,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Diabetes Monitoring Package",
            "description": "Specialized tests for diabetes management",
            "test_ids": [test_ids[2], test_ids[3]],  # Blood Glucose, TFT
            "original_price": 750.0,
            "package_price": 600.0,
            "discount_percentage": 20.0,
            "created_at": datetime.utcnow()
        }
    ]
    
    await db.lab_packages.insert_many(lab_packages_data)
    print(f"Inserted {len(lab_packages_data)} lab packages")
    
    # Seed Sample Medical Records (for demo patients)
    medical_records_data = [
        {
            "id": str(uuid.uuid4()),
            "patient_id": "demo-patient-1",  # This would be replaced with actual patient IDs
            "record_type": "consultation",
            "doctor_id": doctors_data[0]["id"],
            "title": "General Consultation - Fever and Headache",
            "content": "Patient presented with fever (101°F) and headache for 2 days. Physical examination normal. Prescribed paracetamol and rest. Follow-up in 3 days if symptoms persist.",
            "attachments": [],
            "date": datetime.utcnow() - timedelta(days=7),
            "is_confidential": True
        },
        {
            "id": str(uuid.uuid4()),
            "patient_id": "demo-patient-1",
            "record_type": "lab_report",
            "doctor_id": None,
            "title": "Complete Blood Count Report",
            "content": "CBC results within normal limits. Hemoglobin: 13.2 g/dl, WBC: 7200/µl, Platelets: 280000/µl. No abnormalities detected.",
            "attachments": ["cbc_report_demo.pdf"],
            "date": datetime.utcnow() - timedelta(days=5),
            "is_confidential": True
        },
        {
            "id": str(uuid.uuid4()),
            "patient_id": "demo-patient-2",
            "record_type": "prescription",
            "doctor_id": doctors_data[1]["id"],
            "title": "Cardiac Consultation Prescription",
            "content": "Prescribed medication for hypertension management: Amlodipine 5mg once daily, Metoprolol 25mg twice daily. Regular BP monitoring advised.",
            "attachments": ["prescription_cardiac.pdf"],
            "date": datetime.utcnow() - timedelta(days=3),
            "is_confidential": True
        }
    ]
    
    await db.medical_records.insert_many(medical_records_data)
    print(f"Inserted {len(medical_records_data)} medical records")
    
    print("Database seeding completed successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())