import requests
import sys
import json
from datetime import datetime

class UnicareAPITester:
    def __init__(self, base_url="https://634fec4b-409c-4c75-b58c-fb21cbd6d0ba.preview.emergentagent.com"):
        self.base_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.user_id = None
        self.admin_user_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, use_admin=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use admin token if specified
        token_to_use = self.admin_token if use_admin else self.token
        if token_to_use:
            headers['Authorization'] = f'Bearer {token_to_use}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response text: {response.text}")

            return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n=== HEALTH CHECK TESTS ===")
        self.run_test("Root endpoint", "GET", "", 200)
        self.run_test("Health check", "GET", "health", 200)

    def test_admin_login(self):
        """Test admin login"""
        print("\n=== ADMIN LOGIN TEST ===")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "admin@unicarepolyclinic.com",
                "password": "admin-007"
            }
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            print(f"Admin logged in successfully. Role: {response['user']['role']}")
            return True
        return False

    def test_user_registration_and_login(self):
        """Test user registration and login flow"""
        print("\n=== USER REGISTRATION & LOGIN TESTS ===")
        
        # Generate unique user data
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"test_patient_{timestamp}@test.com"
        test_phone = f"+1234567{timestamp[-3:]}"
        
        # Test registration
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": test_email,
                "phone": test_phone,
                "full_name": f"Test Patient {timestamp}",
                "password": "TestPass123!",
                "address": "123 Test Street, Test City",
                "date_of_birth": "1990-01-01",
                "emergency_contact": "+1234567890"
            }
        )
        
        if not success:
            return False
            
        # Test login with registered user
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": test_email,
                "password": "TestPass123!"
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"User logged in successfully. Role: {response['user']['role']}")
            return True
        return False

    def test_otp_functionality(self):
        """Test OTP request and verification"""
        print("\n=== OTP FUNCTIONALITY TESTS ===")
        
        # Test email OTP request
        success, response = self.run_test(
            "Request Email OTP",
            "POST",
            "auth/request-otp",
            200,
            data={"email": "test@example.com"}
        )
        
        # Test phone OTP request
        success, response = self.run_test(
            "Request Phone OTP",
            "POST",
            "auth/request-otp",
            200,
            data={"phone": "+1234567890"}
        )
        
        # Note: OTP verification would require actual OTP from console logs
        print("Note: OTP verification requires actual OTP codes from backend console logs")

    def test_doctors_endpoints(self):
        """Test doctor-related endpoints"""
        print("\n=== DOCTORS ENDPOINTS TESTS ===")
        
        # Get all doctors
        success, doctors = self.run_test("Get All Doctors", "GET", "doctors", 200)
        
        if success and doctors:
            doctor_id = doctors[0]['id'] if doctors else None
            
            if doctor_id:
                # Get specific doctor
                self.run_test("Get Specific Doctor", "GET", f"doctors/{doctor_id}", 200)
                
                # Test admin updating doctor status
                if self.admin_token:
                    self.run_test(
                        "Update Doctor Status (Admin)",
                        "PUT",
                        f"doctors/{doctor_id}/status",
                        200,
                        data={"status": "busy", "is_available": False},
                        use_admin=True
                    )

    def test_medicines_endpoints(self):
        """Test medicine-related endpoints"""
        print("\n=== MEDICINES ENDPOINTS TESTS ===")
        
        # Get all medicines
        success, medicines = self.run_test("Get All Medicines", "GET", "medicines", 200)
        
        if success and medicines and self.token:
            # Test creating medicine order
            medicine_id = medicines[0]['id'] if medicines else None
            if medicine_id:
                self.run_test(
                    "Create Medicine Order",
                    "POST",
                    "medicines/order",
                    200,
                    data={
                        "items": [{"medicine_id": medicine_id, "quantity": 2, "price": 100}],
                        "total_amount": 200
                    }
                )

    def test_lab_tests_endpoints(self):
        """Test lab test-related endpoints"""
        print("\n=== LAB TESTS ENDPOINTS TESTS ===")
        
        # Get all lab tests
        success, tests = self.run_test("Get All Lab Tests", "GET", "lab-tests", 200)
        
        # Get all lab packages
        success, packages = self.run_test("Get All Lab Packages", "GET", "lab-packages", 200)
        
        if success and tests and self.token:
            # Test creating lab order
            test_id = tests[0]['id'] if tests else None
            if test_id:
                self.run_test(
                    "Create Lab Order",
                    "POST",
                    "lab-tests/order",
                    200,
                    data={
                        "test_ids": [test_id],
                        "package_ids": [],
                        "total_amount": 500
                    }
                )

    def test_appointments_endpoints(self):
        """Test appointment-related endpoints"""
        print("\n=== APPOINTMENTS ENDPOINTS TESTS ===")
        
        if not self.token:
            print("Skipping appointments test - no user token")
            return
            
        # Get doctors first to book appointment
        success, doctors = self.run_test("Get Doctors for Appointment", "GET", "doctors", 200)
        
        if success and doctors:
            doctor_id = doctors[0]['id']
            
            # Create appointment
            self.run_test(
                "Create Appointment",
                "POST",
                "appointments",
                200,
                data={
                    "doctor_id": doctor_id,
                    "appointment_date": "2025-07-20",
                    "appointment_time": "10:00",
                    "symptoms": "Regular checkup"
                }
            )
            
            # Get my appointments
            self.run_test("Get My Appointments", "GET", "appointments/my", 200)

    def test_medical_records_endpoints(self):
        """Test medical records endpoints"""
        print("\n=== MEDICAL RECORDS ENDPOINTS TESTS ===")
        
        if not self.token:
            print("Skipping medical records test - no user token")
            return
            
        # Test accessing medical records (should fail if not approved)
        success, response = self.run_test("Get My Medical Records", "GET", "medical-records/my", 403)
        
        if not success:
            print("Expected 403 for unapproved patient - this is correct behavior")

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        print("\n=== ADMIN ENDPOINTS TESTS ===")
        
        if not self.admin_token:
            print("Skipping admin tests - no admin token")
            return
            
        # Get all patients
        success, patients = self.run_test("Get All Patients (Admin)", "GET", "admin/patients", 200, use_admin=True)
        
        if success and patients and self.user_id:
            # Approve a patient
            self.run_test(
                "Approve Patient (Admin)",
                "PUT",
                f"admin/patients/{self.user_id}/approve",
                200,
                use_admin=True
            )
            
            # Test creating lab package
            self.run_test(
                "Create Lab Package (Admin)",
                "POST",
                "admin/lab-packages",
                200,
                data={
                    "name": "Test Health Package",
                    "description": "Comprehensive health checkup",
                    "test_ids": [],
                    "original_price": 1000,
                    "package_price": 800,
                    "discount_percentage": 20
                },
                use_admin=True
            )

    def test_enhanced_doctor_management(self):
        """Test enhanced doctor CRUD operations"""
        print("\n=== ENHANCED DOCTOR MANAGEMENT TESTS ===")
        
        if not self.admin_token:
            print("Skipping enhanced doctor management tests - no admin token")
            return
        
        # Test creating new doctor
        success, doctor_response = self.run_test(
            "Create New Doctor",
            "POST",
            "admin/doctors",
            200,
            data={
                "user_id": "test-user-id-123",
                "name": "Dr. Sarah Johnson",
                "specialty": "Cardiology",
                "qualification": "MD, FACC",
                "experience_years": 8,
                "consultation_fee": 150.0,
                "is_available": True,
                "status": "available"
            },
            use_admin=True
        )
        
        doctor_id = None
        if success and 'doctor_id' in doctor_response:
            doctor_id = doctor_response['doctor_id']
        
        # Test updating doctor information
        if doctor_id:
            self.run_test(
                "Update Doctor Information",
                "PUT",
                f"admin/doctors/{doctor_id}",
                200,
                data={
                    "consultation_fee": 175.0,
                    "experience_years": 9,
                    "status": "busy"
                },
                use_admin=True
            )
        
        # Test deleting doctor (should fail if has appointments)
        if doctor_id:
            success, response = self.run_test(
                "Delete Doctor",
                "DELETE",
                f"admin/doctors/{doctor_id}",
                200,
                use_admin=True
            )
            if not success:
                print("Note: Doctor deletion may fail if doctor has existing appointments - this is expected behavior")

    def test_patient_document_upload_system(self):
        """Test patient document upload system"""
        print("\n=== PATIENT DOCUMENT UPLOAD SYSTEM TESTS ===")
        
        if not self.admin_token or not self.user_id:
            print("Skipping document upload tests - no admin token or user ID")
            return
        
        # Test getting patient documents (should be empty initially)
        self.run_test(
            "Get Patient Documents",
            "GET",
            f"admin/patients/{self.user_id}/documents",
            200,
            use_admin=True
        )
        
        # Test patient accessing their own documents
        if self.token:
            self.run_test(
                "Get My Documents (Patient)",
                "GET",
                f"patients/{self.user_id}/documents",
                200
            )
        
        # Note: File upload testing requires multipart/form-data which is complex to test
        # In a real scenario, we would test with actual file uploads
        print("Note: File upload endpoints require multipart/form-data testing with actual files")
        print("Document upload endpoints are available at:")
        print(f"- POST /api/admin/patients/{{patient_id}}/upload-document")
        print(f"- GET /api/admin/patients/{{patient_id}}/documents")
        print(f"- DELETE /api/admin/patients/{{patient_id}}/documents/{{document_id}}")

    def test_health_package_creation(self):
        """Test health package creation with discount calculation"""
        print("\n=== HEALTH PACKAGE CREATION TESTS ===")
        
        if not self.admin_token:
            print("Skipping health package tests - no admin token")
            return
        
        # Test creating comprehensive health package
        self.run_test(
            "Create Comprehensive Health Package",
            "POST",
            "admin/lab-packages",
            200,
            data={
                "name": "Executive Health Checkup",
                "description": "Complete health screening for executives including blood work, ECG, and imaging",
                "test_ids": ["test-1", "test-2", "test-3"],
                "original_price": 2500.0,
                "package_price": 1875.0,
                "discount_percentage": 25.0
            },
            use_admin=True
        )
        
        # Test creating basic health package
        self.run_test(
            "Create Basic Health Package",
            "POST",
            "admin/lab-packages",
            200,
            data={
                "name": "Basic Health Screening",
                "description": "Essential health tests for routine checkup",
                "test_ids": ["test-1", "test-2"],
                "original_price": 800.0,
                "package_price": 640.0,
                "discount_percentage": 20.0
            },
            use_admin=True
        )
        
        # Verify packages are available publicly
        self.run_test(
            "Get Lab Packages (Public)",
            "GET",
            "lab-packages",
            200
        )

    def test_doctor_scheduling_system(self):
        """Test comprehensive doctor scheduling system"""
        print("\n=== DOCTOR SCHEDULING SYSTEM TESTS ===")
        
        if not self.admin_token:
            print("Skipping doctor scheduling tests - no admin token")
            return
        
        # First, get doctors to use for scheduling
        success, doctors = self.run_test("Get Doctors for Scheduling", "GET", "doctors", 200)
        if not success or not doctors:
            print("No doctors found, creating test scenario")
            return
            
        doctor_id = doctors[0]['id']
        
        # Test creating doctor schedule template
        success, template_response = self.run_test(
            "Create Doctor Schedule Template",
            "POST",
            "admin/doctor-schedule-template",
            200,
            data={
                "doctor_id": doctor_id,
                "template_name": "Weekday Morning Schedule",
                "schedule_type": "weekly",
                "days_of_week": [1, 2, 3, 4, 5],  # Mon-Fri
                "start_time": "09:00",
                "end_time": "17:00",
                "slot_duration": 30,
                "break_times": [{"start": "13:00", "end": "14:00"}],
                "is_active": True
            },
            use_admin=True
        )
        
        template_id = None
        if success and 'template_id' in template_response:
            template_id = template_response['template_id']
        
        # Test getting doctor schedule templates
        self.run_test(
            "Get Doctor Schedule Templates",
            "GET",
            f"admin/doctor-schedule-templates/{doctor_id}",
            200,
            use_admin=True
        )
        
        # Test updating schedule template
        if template_id:
            self.run_test(
                "Update Schedule Template",
                "PUT",
                f"admin/doctor-schedule-template/{template_id}",
                200,
                data={"slot_duration": 45},
                use_admin=True
            )
        
        # Test generating doctor schedule
        if template_id:
            self.run_test(
                "Generate Doctor Schedule",
                "POST",
                "admin/generate-doctor-schedule",
                200,
                data={
                    "doctor_id": doctor_id,
                    "template_id": template_id,
                    "start_date": "2025-01-20",
                    "end_date": "2025-01-26"
                },
                use_admin=True
            )
        
        # Test creating doctor leave
        success, leave_response = self.run_test(
            "Create Doctor Leave",
            "POST",
            "admin/doctor-leave",
            200,
            data={
                "doctor_id": doctor_id,
                "leave_type": "vacation",
                "start_date": "2025-02-01",
                "end_date": "2025-02-03",
                "reason": "Annual vacation",
                "status": "approved"
            },
            use_admin=True
        )
        
        # Test getting doctor leaves
        self.run_test(
            "Get Doctor Leaves",
            "GET",
            f"admin/doctor-leaves/{doctor_id}",
            200,
            use_admin=True
        )
        
        # Test creating holiday
        self.run_test(
            "Create Holiday",
            "POST",
            "admin/holidays",
            200,
            data={
                "name": "Test Holiday",
                "date": "2025-12-25",
                "is_working_day": False
            },
            use_admin=True
        )
        
        # Test getting holidays
        self.run_test(
            "Get Holidays",
            "GET",
            "admin/holidays",
            200,
            use_admin=True
        )

    def test_inventory_management_system(self):
        """Test comprehensive inventory management system"""
        print("\n=== INVENTORY MANAGEMENT SYSTEM TESTS ===")
        
        if not self.admin_token:
            print("Skipping inventory tests - no admin token")
            return
        
        # Test creating inventory item
        success, item_response = self.run_test(
            "Create Inventory Item",
            "POST",
            "admin/inventory",
            200,
            data={
                "name": "Paracetamol 500mg",
                "category": "medicine",
                "current_stock": 100,
                "minimum_stock": 20,
                "unit": "tablets",
                "cost_per_unit": 2.50,
                "supplier": "MedSupply Co",
                "expiry_date": "2026-12-31",
                "location": "pharmacy"
            },
            use_admin=True
        )
        
        item_id = None
        if success and 'item_id' in item_response:
            item_id = item_response['item_id']
        
        # Test getting all inventory items
        self.run_test(
            "Get All Inventory Items",
            "GET",
            "admin/inventory",
            200,
            use_admin=True
        )
        
        # Test getting inventory items by category
        self.run_test(
            "Get Inventory Items by Category",
            "GET",
            "admin/inventory?category=medicine",
            200,
            use_admin=True
        )
        
        # Test updating inventory item
        if item_id:
            self.run_test(
                "Update Inventory Item",
                "PUT",
                f"admin/inventory/{item_id}",
                200,
                data={"minimum_stock": 25},
                use_admin=True
            )
        
        # Test creating stock transaction
        if item_id:
            self.run_test(
                "Create Stock Transaction - Purchase",
                "POST",
                f"admin/inventory/{item_id}/stock-transaction",
                200,
                data={
                    "transaction_type": "purchase",
                    "quantity": 50,
                    "cost_per_unit": 2.40,
                    "total_cost": 120.00,
                    "notes": "Monthly stock replenishment"
                },
                use_admin=True
            )
            
            self.run_test(
                "Create Stock Transaction - Usage",
                "POST",
                f"admin/inventory/{item_id}/stock-transaction",
                200,
                data={
                    "transaction_type": "usage",
                    "quantity": 10,
                    "notes": "Dispensed to patients"
                },
                use_admin=True
            )
        
        # Test getting low stock items
        self.run_test(
            "Get Low Stock Items",
            "GET",
            "admin/inventory/low-stock",
            200,
            use_admin=True
        )

    def test_campaign_management_system(self):
        """Test comprehensive campaign management system"""
        print("\n=== CAMPAIGN MANAGEMENT SYSTEM TESTS ===")
        
        if not self.admin_token:
            print("Skipping campaign tests - no admin token")
            return
        
        # Test creating campaign
        success, campaign_response = self.run_test(
            "Create Campaign",
            "POST",
            "admin/campaigns",
            200,
            data={
                "name": "New Year Health Checkup",
                "description": "10% off on all lab tests during January",
                "campaign_type": "discount",
                "discount_percentage": 10.0,
                "applicable_to": "lab_tests",
                "applicable_items": [],
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "is_active": True,
                "usage_limit": 100
            },
            use_admin=True
        )
        
        campaign_id = None
        if success and 'campaign_id' in campaign_response:
            campaign_id = campaign_response['campaign_id']
        
        # Test getting all campaigns (admin)
        self.run_test(
            "Get All Campaigns (Admin)",
            "GET",
            "admin/campaigns",
            200,
            use_admin=True
        )
        
        # Test updating campaign
        if campaign_id:
            self.run_test(
                "Update Campaign",
                "PUT",
                f"admin/campaigns/{campaign_id}",
                200,
                data={"discount_percentage": 15.0},
                use_admin=True
            )
        
        # Test getting active campaigns (public endpoint)
        self.run_test(
            "Get Active Campaigns (Public)",
            "GET",
            "campaigns/active",
            200
        )

    def test_notification_system(self):
        """Test comprehensive notification system"""
        print("\n=== NOTIFICATION SYSTEM TESTS ===")
        
        if not self.admin_token:
            print("Skipping notification tests - no admin token")
            return
        
        # Test creating notification
        self.run_test(
            "Create Notification (Admin)",
            "POST",
            "admin/notifications",
            200,
            data={
                "user_id": self.admin_user_id,
                "title": "System Maintenance",
                "message": "Scheduled maintenance tonight from 2-4 AM",
                "notification_type": "system"
            },
            use_admin=True
        )
        
        # Test getting notification statistics
        self.run_test(
            "Get Notification Stats",
            "GET",
            "admin/notifications/stats",
            200,
            use_admin=True
        )
        
        # Test getting daily bookings (admin reminder system)
        self.run_test(
            "Get Daily Bookings",
            "GET",
            "admin/daily-bookings",
            200,
            use_admin=True
        )
        
        # Test getting daily bookings for specific date
        self.run_test(
            "Get Daily Bookings for Date",
            "GET",
            "admin/daily-bookings?date=2025-01-20",
            200,
            use_admin=True
        )
        
        # Test user notifications (if user token available)
        if self.token:
            success, notifications = self.run_test(
                "Get My Notifications",
                "GET",
                "notifications/my",
                200
            )
            
            # Test marking notification as read (if notifications exist)
            if success and notifications:
                notification_id = notifications[0]['id']
                self.run_test(
                    "Mark Notification as Read",
                    "PUT",
                    f"notifications/{notification_id}/mark-read",
                    200
                )

    def test_feedback_system(self):
        """Test comprehensive feedback system"""
        print("\n=== FEEDBACK SYSTEM TESTS ===")
        
        if not self.token:
            print("Skipping feedback tests - no user token")
            return
        
        # Get doctors for feedback
        success, doctors = self.run_test("Get Doctors for Feedback", "GET", "doctors", 200)
        if not success or not doctors:
            print("No doctors found for feedback test")
            return
            
        doctor_id = doctors[0]['id']
        
        # Test submitting feedback
        self.run_test(
            "Submit Feedback",
            "POST",
            "feedback",
            200,
            data={
                "doctor_id": doctor_id,
                "appointment_id": "test-appointment-123",
                "rating": 5,
                "comment": "Excellent service and very professional doctor",
                "feedback_categories": {
                    "professionalism": 5,
                    "waiting_time": 4,
                    "communication": 5,
                    "cleanliness": 5
                },
                "is_anonymous": False
            }
        )
        
        # Test admin feedback endpoints
        if self.admin_token:
            # Test getting all feedback (admin)
            self.run_test(
                "Get All Feedback (Admin)",
                "GET",
                "admin/feedback",
                200,
                use_admin=True
            )
            
            # Test getting feedback statistics
            self.run_test(
                "Get Feedback Stats (Admin)",
                "GET",
                "admin/feedback/stats",
                200,
                use_admin=True
            )

    def test_user_profile(self):
        """Test user profile endpoint"""
        print("\n=== USER PROFILE TESTS ===")
        
        if self.token:
            self.run_test("Get User Profile", "GET", "users/profile", 200)

def main():
    print("🏥 Starting Unicare Polyclinic API Tests")
    print("=" * 50)
    
    tester = UnicareAPITester()
    
    # Run all tests
    tester.test_health_check()
    
    # Test admin login first
    if not tester.test_admin_login():
        print("❌ Admin login failed, some tests will be skipped")
    
    # Test user registration and login
    if not tester.test_user_registration_and_login():
        print("❌ User registration/login failed, some tests will be skipped")
    
    # Test OTP functionality
    tester.test_otp_functionality()
    
    # Test all endpoints
    tester.test_doctors_endpoints()
    tester.test_medicines_endpoints()
    tester.test_lab_tests_endpoints()
    tester.test_appointments_endpoints()
    tester.test_medical_records_endpoints()
    tester.test_admin_endpoints()
    tester.test_user_profile()
    
    # Test comprehensive admin features
    tester.test_doctor_scheduling_system()
    tester.test_inventory_management_system()
    tester.test_campaign_management_system()
    tester.test_notification_system()
    tester.test_feedback_system()
    
    # Test enhanced admin features
    tester.test_enhanced_doctor_management()
    tester.test_patient_document_upload_system()
    tester.test_health_package_creation()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())