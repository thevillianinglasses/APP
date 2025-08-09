import requests
import sys
import json
from datetime import datetime

class UnicareAPITester:
    def __init__(self, base_url="https://2c13db7a-cf26-46fe-aec9-8fa2099ab54a.preview.emergentagent.com"):
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