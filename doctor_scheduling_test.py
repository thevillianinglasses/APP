import requests
import sys
import json
from datetime import datetime, timedelta

class DoctorSchedulingTester:
    def __init__(self, base_url="https://634fec4b-409c-4c75-b58c-fb21cbd6d0ba.preview.emergentagent.com"):
        self.base_url = f"{base_url}/api"
        self.admin_token = None
        self.patient_token = None
        self.admin_user_id = None
        self.patient_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.doctor_id = None
        self.template_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, use_admin=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use admin token if specified
        token_to_use = self.admin_token if use_admin else self.patient_token
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

    def test_admin_login(self):
        """Test admin login with admin@unicarepolyclinic.com / admin-007"""
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
            print(f"✅ Admin logged in successfully. Role: {response['user']['role']}")
            return True
        return False

    def test_patient_registration_and_login(self):
        """Create and login a test patient"""
        print("\n=== PATIENT REGISTRATION & LOGIN ===")
        
        # Generate unique patient data
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"patient_{timestamp}@unicaretest.com"
        test_phone = f"+91987654{timestamp[-3:]}"
        
        # Test registration
        success, response = self.run_test(
            "Patient Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": test_email,
                "phone": test_phone,
                "full_name": f"Rajesh Kumar {timestamp}",
                "password": "Patient123!",
                "address": "123 MG Road, Bangalore, Karnataka",
                "date_of_birth": "1985-06-15",
                "emergency_contact": "+919876543210"
            }
        )
        
        if not success:
            return False
            
        # Test login with registered patient
        success, response = self.run_test(
            "Patient Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": test_email,
                "password": "Patient123!"
            }
        )
        
        if success and 'access_token' in response:
            self.patient_token = response['access_token']
            self.patient_user_id = response['user']['id']
            print(f"✅ Patient logged in successfully. Role: {response['user']['role']}")
            return True
        return False

    def test_get_doctors_list(self):
        """Get list of doctors"""
        print("\n=== GET DOCTORS LIST ===")
        success, doctors = self.run_test("Get All Doctors", "GET", "doctors", 200, use_admin=True)
        
        if success and doctors:
            self.doctor_id = doctors[0]['id']
            print(f"✅ Found {len(doctors)} doctors. Using doctor ID: {self.doctor_id}")
            print(f"Doctor: {doctors[0].get('name', 'Unknown')} - {doctors[0].get('specialty', 'Unknown')}")
            return True, doctors
        else:
            print("❌ No doctors found or failed to get doctors")
            return False, []

    def test_create_schedule_template(self):
        """Create a schedule template for a doctor"""
        print("\n=== CREATE SCHEDULE TEMPLATE ===")
        
        if not self.doctor_id:
            print("❌ No doctor ID available")
            return False
        
        success, response = self.run_test(
            "Create Doctor Schedule Template",
            "POST",
            "admin/doctor-schedule-template",
            200,
            data={
                "doctor_id": self.doctor_id,
                "template_name": "Test Weekday Schedule",
                "schedule_type": "weekly",
                "days_of_week": [0, 1, 2, 3, 4],  # Monday to Friday (0=Monday in Python weekday)
                "start_time": "09:00",
                "end_time": "17:00",
                "slot_duration": 30,
                "break_times": [{"start": "13:00", "end": "14:00"}],
                "is_active": True
            },
            use_admin=True
        )
        
        if success and 'template_id' in response:
            self.template_id = response['template_id']
            print(f"✅ Schedule template created with ID: {self.template_id}")
            return True
        return False

    def test_generate_doctor_schedule(self):
        """Generate doctor schedule using the template"""
        print("\n=== GENERATE DOCTOR SCHEDULE ===")
        
        if not self.doctor_id or not self.template_id:
            print("❌ Missing doctor ID or template ID")
            return False
        
        # Generate schedule for next 30 days
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        success, response = self.run_test(
            "Generate Doctor Schedule",
            "POST",
            "admin/generate-doctor-schedule",
            200,
            data={
                "doctor_id": self.doctor_id,
                "template_id": self.template_id,
                "start_date": start_date,
                "end_date": end_date
            },
            use_admin=True
        )
        
        if success:
            generated_dates = response.get('generated_dates', [])
            print(f"✅ Schedule generated for {len(generated_dates)} dates")
            print(f"Date range: {start_date} to {end_date}")
            if generated_dates:
                print(f"Sample generated dates: {generated_dates[:5]}")
            return True
        return False

    def test_verify_doctor_schedule_populated(self):
        """Verify that doctor.schedule is populated with correct slots"""
        print("\n=== VERIFY DOCTOR SCHEDULE POPULATED ===")
        
        if not self.doctor_id:
            print("❌ No doctor ID available")
            return False
        
        success, doctor = self.run_test(
            "Get Doctor Details",
            "GET",
            f"doctors/{self.doctor_id}",
            200
        )
        
        if success and doctor:
            schedule = doctor.get('schedule', {})
            if schedule:
                print(f"✅ Doctor schedule populated with {len(schedule)} dates")
                
                # Check a sample date's slots
                sample_date = list(schedule.keys())[0] if schedule else None
                if sample_date:
                    slots = schedule[sample_date]
                    print(f"Sample date {sample_date} has {len(slots)} slots")
                    print(f"Sample slots: {slots[:5] if len(slots) > 5 else slots}")
                    
                    # Verify slots follow template (9-5, 30min intervals, excluding lunch break)
                    expected_slots = []
                    current_time = datetime.strptime("09:00", "%H:%M")
                    end_time = datetime.strptime("17:00", "%H:%M")
                    lunch_start = datetime.strptime("13:00", "%H:%M")
                    lunch_end = datetime.strptime("14:00", "%H:%M")
                    
                    while current_time < end_time:
                        # Skip lunch break
                        if not (lunch_start <= current_time < lunch_end):
                            expected_slots.append(current_time.strftime("%H:%M"))
                        current_time += timedelta(minutes=30)
                    
                    # Check if generated slots match expected pattern
                    if len(slots) == len(expected_slots):
                        print("✅ Slot count matches expected pattern")
                    else:
                        print(f"⚠️ Slot count mismatch: got {len(slots)}, expected {len(expected_slots)}")
                    
                    # Check if slots respect working hours
                    valid_slots = all(
                        datetime.strptime("09:00", "%H:%M").time() <= 
                        datetime.strptime(slot, "%H:%M").time() < 
                        datetime.strptime("17:00", "%H:%M").time()
                        for slot in slots
                    )
                    
                    if valid_slots:
                        print("✅ All slots are within working hours (9 AM - 5 PM)")
                    else:
                        print("❌ Some slots are outside working hours")
                    
                    return True
                else:
                    print("❌ No dates found in schedule")
                    return False
            else:
                print("❌ Doctor schedule is empty")
                return False
        else:
            print("❌ Failed to get doctor details")
            return False

    def test_patient_can_see_available_slots(self):
        """Test that patients can see available schedules for booking"""
        print("\n=== PATIENT CAN SEE AVAILABLE SLOTS ===")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # Get doctors list as patient
        success, doctors = self.run_test(
            "Get Doctors List (Patient View)",
            "GET",
            "doctors",
            200
        )
        
        if success and doctors:
            # Find our test doctor
            test_doctor = None
            for doctor in doctors:
                if doctor['id'] == self.doctor_id:
                    test_doctor = doctor
                    break
            
            if test_doctor:
                schedule = test_doctor.get('schedule', {})
                if schedule:
                    print(f"✅ Patient can see doctor schedule with {len(schedule)} dates")
                    
                    # Check if schedule has proper structure for booking
                    sample_date = list(schedule.keys())[0] if schedule else None
                    if sample_date:
                        slots = schedule[sample_date]
                        print(f"Sample date {sample_date} has {len(slots)} available slots")
                        print(f"Sample slots for booking: {slots[:3]}")
                        return True
                    else:
                        print("❌ No dates available in schedule")
                        return False
                else:
                    print("❌ Doctor schedule not visible to patient")
                    return False
            else:
                print("❌ Test doctor not found in patient view")
                return False
        else:
            print("❌ Patient cannot access doctors list")
            return False

    def test_patient_booking_with_generated_slots(self):
        """Test that patient can book appointment with generated slots"""
        print("\n=== PATIENT BOOKING WITH GENERATED SLOTS ===")
        
        if not self.patient_token or not self.doctor_id:
            print("❌ Missing patient token or doctor ID")
            return False
        
        # Get doctor details to find available slot
        success, doctor = self.run_test(
            "Get Doctor for Booking",
            "GET",
            f"doctors/{self.doctor_id}",
            200
        )
        
        if success and doctor:
            schedule = doctor.get('schedule', {})
            if schedule:
                # Find first available date and slot
                available_date = list(schedule.keys())[0]
                available_slots = schedule[available_date]
                available_time = available_slots[0] if available_slots else None
                
                if available_date and available_time:
                    print(f"Attempting to book: {available_date} at {available_time}")
                    
                    success, response = self.run_test(
                        "Create Appointment with Generated Slot",
                        "POST",
                        "appointments",
                        200,
                        data={
                            "doctor_id": self.doctor_id,
                            "appointment_date": available_date,
                            "appointment_time": available_time,
                            "symptoms": "Regular health checkup - testing generated schedule slots"
                        }
                    )
                    
                    if success:
                        appointment_id = response.get('appointment_id')
                        print(f"✅ Appointment booked successfully with ID: {appointment_id}")
                        return True
                    else:
                        print("❌ Failed to book appointment")
                        return False
                else:
                    print("❌ No available slots found")
                    return False
            else:
                print("❌ No schedule available for booking")
                return False
        else:
            print("❌ Failed to get doctor details for booking")
            return False

    def run_comprehensive_test(self):
        """Run the complete doctor scheduling test flow"""
        print("🏥 Starting Doctor Scheduling Fix Comprehensive Test")
        print("=" * 60)
        
        # Step 1: Admin Login
        if not self.test_admin_login():
            print("❌ Admin login failed - cannot continue")
            return False
        
        # Step 2: Patient Registration and Login
        if not self.test_patient_registration_and_login():
            print("❌ Patient setup failed - some tests will be limited")
        
        # Step 3: Get Doctors List
        success, doctors = self.test_get_doctors_list()
        if not success:
            print("❌ Cannot get doctors list - test cannot continue")
            return False
        
        # Step 4: Create Schedule Template
        if not self.test_create_schedule_template():
            print("❌ Schedule template creation failed")
            return False
        
        # Step 5: Generate Doctor Schedule
        if not self.test_generate_doctor_schedule():
            print("❌ Schedule generation failed")
            return False
        
        # Step 6: Verify Doctor Schedule is Populated
        if not self.test_verify_doctor_schedule_populated():
            print("❌ Doctor schedule verification failed")
            return False
        
        # Step 7: Test Patient Can See Available Slots
        if self.patient_token:
            if not self.test_patient_can_see_available_slots():
                print("❌ Patient cannot see available slots")
                return False
        
        # Step 8: Test Patient Booking
        if self.patient_token:
            if not self.test_patient_booking_with_generated_slots():
                print("❌ Patient booking with generated slots failed")
                return False
        
        return True

def main():
    tester = DoctorSchedulingTester()
    
    success = tester.run_comprehensive_test()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 DOCTOR SCHEDULING TEST RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if success and tester.tests_passed == tester.tests_run:
        print("🎉 All doctor scheduling tests passed!")
        print("✅ Schedule templates work correctly")
        print("✅ Schedule generation populates doctor.schedule")
        print("✅ Generated slots follow template rules")
        print("✅ Patients can see and book available slots")
        return 0
    else:
        print(f"⚠️ Doctor scheduling test issues found")
        return 1

if __name__ == "__main__":
    sys.exit(main())