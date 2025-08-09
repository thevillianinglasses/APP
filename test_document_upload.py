#!/usr/bin/env python3
"""
Test script specifically for document upload functionality
"""
import requests
import io
import json

def test_document_upload():
    base_url = "https://634fec4b-409c-4c75-b58c-fb21cbd6d0ba.preview.emergentagent.com/api"
    
    # First login as admin
    print("🔐 Logging in as admin...")
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "admin@unicarepolyclinic.com",
        "password": "admin-007"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return False
    
    admin_token = login_response.json()['access_token']
    admin_user_id = login_response.json()['user']['id']
    print("✅ Admin login successful")
    
    # Create a test patient first
    import time
    timestamp = str(int(time.time()))
    test_email = f"test_patient_doc_{timestamp}@test.com"
    
    print("👤 Creating test patient...")
    patient_response = requests.post(f"{base_url}/auth/register", json={
        "email": test_email,
        "phone": f"+123456{timestamp[-4:]}",
        "full_name": f"Test Patient for Documents {timestamp}",
        "password": "TestPass123!",
        "address": "123 Test Street",
        "date_of_birth": "1990-01-01"
    })
    
    if patient_response.status_code != 200:
        print(f"❌ Patient creation failed: {patient_response.status_code}")
        return False
    
    # Login as patient to get patient ID
    patient_login = requests.post(f"{base_url}/auth/login", json={
        "email": "test_patient_doc@test.com",
        "password": "TestPass123!"
    })
    
    if patient_login.status_code != 200:
        print(f"❌ Patient login failed: {patient_login.status_code}")
        return False
    
    patient_id = patient_login.json()['user']['id']
    print(f"✅ Test patient created with ID: {patient_id}")
    
    # Test document upload with multipart form data
    print("📄 Testing document upload...")
    
    # Create a mock PDF file
    mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
    
    files = {
        'file': ('test_opcard.pdf', io.BytesIO(mock_pdf_content), 'application/pdf')
    }
    
    data = {
        'document_type': 'opcard',
        'description': 'Test OP Card upload',
        'appointment_id': 'test-appointment-123'
    }
    
    headers = {
        'Authorization': f'Bearer {admin_token}'
    }
    
    upload_response = requests.post(
        f"{base_url}/admin/patients/{patient_id}/upload-document?document_type=opcard&description=Test OP Card upload&appointment_id=test-appointment-123",
        files=files,
        headers=headers
    )
    
    print(f"Upload response status: {upload_response.status_code}")
    if upload_response.status_code == 200:
        print("✅ Document upload successful!")
        response_data = upload_response.json()
        print(f"Document ID: {response_data.get('document_id')}")
        print(f"File URL: {response_data.get('file_url')}")
        document_id = response_data.get('document_id')
    else:
        print(f"❌ Document upload failed: {upload_response.text}")
        return False
    
    # Test getting patient documents
    print("📋 Testing get patient documents...")
    docs_response = requests.get(
        f"{base_url}/admin/patients/{patient_id}/documents",
        headers=headers
    )
    
    if docs_response.status_code == 200:
        documents = docs_response.json()
        print(f"✅ Retrieved {len(documents)} documents")
        for doc in documents:
            print(f"  - {doc['document_name']} ({doc['document_type']})")
    else:
        print(f"❌ Failed to get documents: {docs_response.status_code}")
    
    # Test patient accessing their own documents
    print("👤 Testing patient access to own documents...")
    patient_token = patient_login.json()['access_token']
    patient_docs_response = requests.get(
        f"{base_url}/patients/{patient_id}/documents",
        headers={'Authorization': f'Bearer {patient_token}'}
    )
    
    if patient_docs_response.status_code == 200:
        patient_documents = patient_docs_response.json()
        print(f"✅ Patient can access {len(patient_documents)} of their documents")
    else:
        print(f"❌ Patient document access failed: {patient_docs_response.status_code}")
    
    # Test document deletion
    if document_id:
        print("🗑️ Testing document deletion...")
        delete_response = requests.delete(
            f"{base_url}/admin/patients/{patient_id}/documents/{document_id}",
            headers=headers
        )
        
        if delete_response.status_code == 200:
            print("✅ Document deletion successful!")
        else:
            print(f"❌ Document deletion failed: {delete_response.status_code}")
    
    return True

if __name__ == "__main__":
    print("🏥 Testing Document Upload System")
    print("=" * 40)
    
    success = test_document_upload()
    
    if success:
        print("\n🎉 Document upload system tests completed successfully!")
    else:
        print("\n❌ Document upload system tests failed!")