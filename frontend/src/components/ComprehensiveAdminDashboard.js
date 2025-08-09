import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ComprehensiveAdminDashboard = () => {
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [dailyBookings, setDailyBookings] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientDocuments, setPatientDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Form states
  const [newDoctor, setNewDoctor] = useState({
    name: '',
    specialty: '',
    qualification: '',
    experience_years: 0,
    consultation_fee: 0,
    user_id: ''
  });
  
  const [newScheduleTemplate, setNewScheduleTemplate] = useState({
    doctor_id: '',
    template_name: '',
    schedule_type: 'weekly',
    days_of_week: [],
    start_time: '09:00',
    end_time: '17:00',
    slot_duration: 30,
    break_times: []
  });
  
  const [newInventoryItem, setNewInventoryItem] = useState({
    name: '',
    category: 'medicine',
    current_stock: 0,
    minimum_stock: 0,
    unit: 'pieces',
    cost_per_unit: 0,
    supplier: '',
    location: 'pharmacy'
  });
  
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    description: '',
    campaign_type: 'discount',
    discount_percentage: 10,
    applicable_to: 'medicines',
    start_date: '',
    end_date: '',
    is_active: true
  });
  
  const [newPackage, setNewPackage] = useState({
    name: '',
    description: '',
    test_ids: [],
    package_price: 0
  });
  
  const [documentUpload, setDocumentUpload] = useState({
    patient_id: '',
    document_type: 'opcard',
    description: '',
    file: null
  });
  
  const [tests, setTests] = useState([]);
  const [doctorModal, setDoctorModal] = useState(false);
  const [scheduleModal, setScheduleModal] = useState(false);
  const [inventoryModal, setInventoryModal] = useState(false);
  const [campaignModal, setCampaignModal] = useState(false);
  const [packageModal, setPackageModal] = useState(false);
  const [documentModal, setDocumentModal] = useState(false);
  const [patientDocModal, setPatientDocModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, [user, navigate]);

  const fetchData = async () => {
    try {
      const [
        patientsResponse, 
        doctorsResponse, 
        testsResponse, 
        inventoryResponse,
        campaignsResponse,
        feedbackResponse,
        dailyBookingsResponse
      ] = await Promise.all([
        axios.get(`${API}/admin/patients`),
        axios.get(`${API}/doctors`),
        axios.get(`${API}/lab-tests`),
        axios.get(`${API}/admin/inventory`),
        axios.get(`${API}/admin/campaigns`),
        axios.get(`${API}/admin/feedback`),
        axios.get(`${API}/admin/daily-bookings?date=${selectedDate}`)
      ]);
      
      setPatients(patientsResponse.data);
      setDoctors(doctorsResponse.data);
      setTests(testsResponse.data);
      setInventory(inventoryResponse.data);
      setCampaigns(campaignsResponse.data);
      setFeedback(feedbackResponse.data);
      setDailyBookings(dailyBookingsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const createDoctor = async () => {
    try {
      await axios.post(`${API}/admin/doctors`, newDoctor);
      alert('Doctor created successfully!');
      setDoctorModal(false);
      fetchData();
      setNewDoctor({
        name: '',
        specialty: '',
        qualification: '',
        experience_years: 0,
        consultation_fee: 0,
        user_id: ''
      });
    } catch (error) {
      alert('Error creating doctor: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const updateDoctor = async (doctorId, doctorData) => {
    try {
      await axios.put(`${API}/admin/doctors/${doctorId}`, doctorData);
      alert('Doctor updated successfully!');
      fetchData();
    } catch (error) {
      alert('Error updating doctor: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const deleteDoctor = async (doctorId) => {
    if (window.confirm('Are you sure you want to delete this doctor?')) {
      try {
        await axios.delete(`${API}/admin/doctors/${doctorId}`);
        alert('Doctor deleted successfully!');
        fetchData();
      } catch (error) {
        alert('Error deleting doctor: ' + (error.response?.data?.detail || 'Something went wrong'));
      }
    }
  };

  const createScheduleTemplate = async () => {
    try {
      const response = await axios.post(`${API}/admin/doctor-schedule-template`, newScheduleTemplate);
      const templateId = response.data.template_id;
      
      alert('Schedule template created successfully!');
      
      // Automatically generate schedule for the next 30 days
      if (newScheduleTemplate.doctor_id && templateId) {
        try {
          const startDate = new Date();
          const endDate = new Date();
          endDate.setDate(startDate.getDate() + 30);
          
          await axios.post(`${API}/admin/generate-doctor-schedule`, {
            doctor_id: newScheduleTemplate.doctor_id,
            template_id: templateId,
            start_date: startDate.toISOString().split('T')[0],
            end_date: endDate.toISOString().split('T')[0]
          });
          
          alert('Doctor schedule generated for next 30 days! Patients can now book appointments.');
          
          // Refresh data to show updated schedules
          fetchData();
        } catch (scheduleError) {
          console.error('Schedule generation error:', scheduleError);
          alert('Template created but automatic schedule generation failed. Please try again.');
        }
      }
      
      setScheduleModal(false);
      setNewScheduleTemplate({
        doctor_id: '',
        template_name: '',
        schedule_type: 'weekly',
        days_of_week: [],
        start_time: '09:00',
        end_time: '17:00',
        slot_duration: 30,
        break_times: []
      });
    } catch (error) {
      alert('Error creating schedule template: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const generateScheduleForDoctor = async (doctorId) => {
    try {
      // Get templates for this doctor
      const templatesResponse = await axios.get(`${API}/admin/doctor-schedule-templates/${doctorId}`);
      const templates = templatesResponse.data;
      
      if (templates.length === 0) {
        alert('Please create a schedule template first for this doctor.');
        return;
      }
      
      // Use the first active template
      const activeTemplate = templates.find(t => t.is_active) || templates[0];
      
      const startDate = new Date();
      const endDate = new Date();
      endDate.setDate(startDate.getDate() + 30);
      
      await axios.post(`${API}/admin/generate-doctor-schedule`, {
        doctor_id: doctorId,
        template_id: activeTemplate.id,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0]
      });
      
      alert('Schedule generated successfully for next 30 days!');
      fetchData(); // Refresh to show updated data
      
    } catch (error) {
      alert('Error generating schedule: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const createInventoryItem = async () => {
    try {
      await axios.post(`${API}/admin/inventory`, newInventoryItem);
      alert('Inventory item created successfully!');
      setInventoryModal(false);
      fetchData();
      setNewInventoryItem({
        name: '',
        category: 'medicine',
        current_stock: 0,
        minimum_stock: 0,
        unit: 'pieces',
        cost_per_unit: 0,
        supplier: '',
        location: 'pharmacy'
      });
    } catch (error) {
      alert('Error creating inventory item: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const createCampaign = async () => {
    try {
      await axios.post(`${API}/admin/campaigns`, newCampaign);
      alert('Campaign created successfully!');
      setCampaignModal(false);
      fetchData();
      setNewCampaign({
        name: '',
        description: '',
        campaign_type: 'discount',
        discount_percentage: 10,
        applicable_to: 'medicines',
        start_date: '',
        end_date: '',
        is_active: true
      });
    } catch (error) {
      alert('Error creating campaign: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const createPackage = async () => {
    try {
      const selectedTests = tests.filter(test => newPackage.test_ids.includes(test.id));
      const originalPrice = selectedTests.reduce((total, test) => total + test.price, 0);
      const discountAmount = originalPrice - newPackage.package_price;
      const discountPercentage = originalPrice > 0 ? ((discountAmount / originalPrice) * 100).toFixed(2) : 0;
      
      const packageData = {
        ...newPackage,
        original_price: originalPrice,
        discount_percentage: parseFloat(discountPercentage)
      };
      
      await axios.post(`${API}/admin/lab-packages`, packageData);
      alert('Lab package created successfully!');
      setPackageModal(false);
      setNewPackage({
        name: '',
        description: '',
        test_ids: [],
        package_price: 0
      });
    } catch (error) {
      alert('Error creating package: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const uploadPatientDocument = async () => {
    if (!documentUpload.file || !documentUpload.patient_id) {
      alert('Please select a patient and a file to upload');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', documentUpload.file);
      formData.append('document_type', documentUpload.document_type);
      formData.append('description', documentUpload.description);

      await axios.post(
        `${API}/admin/patients/${documentUpload.patient_id}/upload-document`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      alert('Document uploaded successfully!');
      setDocumentModal(false);
      setDocumentUpload({
        patient_id: '',
        document_type: 'opcard',
        description: '',
        file: null
      });
      
      // Refresh patient documents if viewing a patient
      if (selectedPatient) {
        fetchPatientDocuments(selectedPatient.id);
      }
    } catch (error) {
      alert('Error uploading document: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const fetchPatientDocuments = async (patientId) => {
    try {
      const response = await axios.get(`${API}/admin/patients/${patientId}/documents`);
      setPatientDocuments(response.data);
    } catch (error) {
      console.error('Error fetching patient documents:', error);
    }
  };

  const viewPatientDocuments = (patient) => {
    setSelectedPatient(patient);
    fetchPatientDocuments(patient.id);
    setPatientDocModal(true);
  };

  const deletePatientDocument = async (documentId) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await axios.delete(`${API}/admin/patients/${selectedPatient.id}/documents/${documentId}`);
        alert('Document deleted successfully!');
        fetchPatientDocuments(selectedPatient.id);
      } catch (error) {
        alert('Error deleting document: ' + (error.response?.data?.detail || 'Something went wrong'));
      }
    }
  };

  const handleDayToggle = (day) => {
    const days = [...newScheduleTemplate.days_of_week];
    if (days.includes(day)) {
      days.splice(days.indexOf(day), 1);
    } else {
      days.push(day);
    }
    setNewScheduleTemplate({...newScheduleTemplate, days_of_week: days});
  };

  if (user?.role !== 'admin') {
    return <div>Access denied. Admin only.</div>;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const lowStockItems = inventory.filter(item => item.current_stock <= item.minimum_stock);
  const pendingApprovals = patients.filter(patient => !patient.is_approved);
  const activeCampaigns = campaigns.filter(campaign => campaign.is_active);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-blue-600 hover:text-blue-700 mr-4"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Comprehensive Admin Panel</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Admin: {user?.full_name}</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Overview Cards */}
        {activeTab === 'dashboard' && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex items-center">
                  <div className="bg-blue-100 p-3 rounded-full">
                    <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{dailyBookings.length}</p>
                    <p className="text-gray-600">Today's Appointments</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex items-center">
                  <div className="bg-yellow-100 p-3 rounded-full">
                    <svg className="w-6 h-6 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{pendingApprovals.length}</p>
                    <p className="text-gray-600">Pending Approvals</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex items-center">
                  <div className="bg-red-100 p-3 rounded-full">
                    <svg className="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{lowStockItems.length}</p>
                    <p className="text-gray-600">Low Stock Items</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex items-center">
                  <div className="bg-green-100 p-3 rounded-full">
                    <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 010 2H4a1 1 0 01-1-1zM14 9a1 1 0 100 2h2a1 1 0 100-2h-2z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-2xl font-semibold text-gray-900">{activeCampaigns.length}</p>
                    <p className="text-gray-600">Active Campaigns</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex flex-wrap space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
          {[
            { key: 'dashboard', label: '📊 Dashboard' },
            { key: 'doctors', label: '👨‍⚕️ Doctor Management' },
            { key: 'scheduling', label: '📅 Advanced Scheduling' },
            { key: 'inventory', label: '📦 Inventory & Medicine' },
            { key: 'packages', label: '🧪 Health Packages' },
            { key: 'campaigns', label: '🎯 Festive Offers' },
            { key: 'patients', label: '👥 Patient Documents' },
            { key: 'feedback', label: '⭐ Feedback Review' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 min-w-max py-2 px-4 rounded-md font-medium text-sm ${
                activeTab === tab.key
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Today's Appointments */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="px-6 py-4 border-b flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Today's Appointments</h3>
                  <p className="text-gray-600">Date: {selectedDate}</p>
                </div>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="p-6">
                {dailyBookings.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No appointments for this date</p>
                ) : (
                  <div className="space-y-4">
                    {dailyBookings.map((appointment) => (
                      <div key={appointment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">{appointment.patient_name}</p>
                          <p className="text-sm text-gray-600">Dr. {appointment.doctor_name}</p>
                          <p className="text-sm text-gray-500">{appointment.appointment_time}</p>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            appointment.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                            appointment.status === 'completed' ? 'bg-green-100 text-green-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {appointment.status}
                          </span>
                          {appointment.patient_phone && (
                            <p className="text-sm text-gray-500 mt-1">{appointment.patient_phone}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Low Stock Alert */}
            {lowStockItems.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-red-900 mb-4">⚠️ Low Stock Alert</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {lowStockItems.map((item) => (
                    <div key={item.id} className="bg-white p-4 rounded-lg border border-red-200">
                      <p className="font-medium text-gray-900">{item.name}</p>
                      <p className="text-sm text-gray-600">Current: {item.current_stock} {item.unit}</p>
                      <p className="text-sm text-red-600">Minimum: {item.minimum_stock} {item.unit}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Doctor Management Tab */}
        {activeTab === 'doctors' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">👨‍⚕️ Doctor Management</h2>
                <p className="text-gray-600">Add, edit, and manage doctor profiles</p>
              </div>
              <button
                onClick={() => setDoctorModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                ➕ Add New Doctor
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {doctors.map((doctor) => (
                  <div key={doctor.id} className="border rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{doctor.name}</h3>
                    <div className="space-y-1 text-sm text-gray-600">
                      <p><span className="font-medium">Specialty:</span> {doctor.specialty}</p>
                      <p><span className="font-medium">Qualification:</span> {doctor.qualification}</p>
                      <p><span className="font-medium">Experience:</span> {doctor.experience_years} years</p>
                      <p><span className="font-medium">Fee:</span> ₹{doctor.consultation_fee}</p>
                    </div>
                    
                    <div className="mt-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        doctor.status === 'available' ? 'bg-green-100 text-green-800' :
                        doctor.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {doctor.status === 'available' ? 'Available' :
                         doctor.status === 'busy' ? 'Busy' : 'On Leave'}
                      </span>
                    </div>

                    <div className="mt-4 space-y-2">
                      <button
                        onClick={() => {
                          setNewDoctor({
                            name: doctor.name,
                            specialty: doctor.specialty,
                            qualification: doctor.qualification,
                            experience_years: doctor.experience_years,
                            consultation_fee: doctor.consultation_fee,
                            user_id: doctor.user_id
                          });
                          setDoctorModal(true);
                        }}
                        className="w-full bg-blue-600 text-white py-1 px-3 rounded text-sm hover:bg-blue-700"
                      >
                        ✏️ Edit Doctor
                      </button>
                      <button
                        onClick={() => deleteDoctor(doctor.id)}
                        className="w-full bg-red-600 text-white py-1 px-3 rounded text-sm hover:bg-red-700"
                      >
                        🗑️ Delete Doctor
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Advanced Scheduling Tab */}
        {activeTab === 'scheduling' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md">
              <div className="px-6 py-4 border-b flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">📅 Advanced Doctor Scheduling</h2>
                  <p className="text-gray-600">Create automated schedules visible to patients</p>
                </div>
                <button
                  onClick={() => setScheduleModal(true)}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                >
                  🕒 Create Schedule Template
                </button>
              </div>
              <div className="p-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <h3 className="font-medium text-blue-900 mb-2">💡 How Doctor Scheduling Works:</h3>
                  <ul className="text-blue-800 text-sm space-y-1">
                    <li>• Create a schedule template with working days, hours, and breaks</li>
                    <li>• System automatically generates 30 days of available slots</li>
                    <li>• Patients can see and book available time slots</li>
                    <li>• Slots respect holidays and doctor leave automatically</li>
                    <li>• System removes booked slots from availability</li>
                  </ul>
                </div>
                
                {/* Current Doctor Schedules */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">Current Doctor Schedules</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {doctors.map((doctor) => {
                      const availableDates = doctor.schedule ? Object.keys(doctor.schedule).length : 0;
                      const todaySlots = doctor.schedule && doctor.schedule[selectedDate] ? doctor.schedule[selectedDate].length : 0;
                      
                      return (
                        <div key={doctor.id} className="border rounded-lg p-4">
                          <h4 className="font-semibold text-gray-900 mb-2">{doctor.name}</h4>
                          <div className="space-y-1 text-sm text-gray-600">
                            <p><span className="font-medium">Specialty:</span> {doctor.specialty}</p>
                            <p><span className="font-medium">Available Dates:</span> {availableDates} days</p>
                            <p><span className="font-medium">Today's Slots:</span> {todaySlots} slots</p>
                            <p><span className="font-medium">Status:</span> 
                              <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
                                doctor.status === 'available' ? 'bg-green-100 text-green-800' :
                                doctor.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {doctor.status}
                              </span>
                            </p>
                          </div>
                          
                          <div className="mt-3 space-y-2">
                            <button
                              onClick={() => {
                                setNewScheduleTemplate({...newScheduleTemplate, doctor_id: doctor.id});
                                setScheduleModal(true);
                              }}
                              className="w-full bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700"
                            >
                              🕒 Create/Update Schedule
                            </button>
                            
                            {availableDates === 0 && (
                              <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
                                <p className="text-yellow-800 text-xs">⚠️ No schedule set. Patients cannot book.</p>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Inventory & Medicine Tab */}
        {activeTab === 'inventory' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">📦 Inventory & Medicine Management</h2>
                <p className="text-gray-600">Manage pharmacy and laboratory inventory</p>
              </div>
              <button
                onClick={() => setInventoryModal(true)}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
              >
                ➕ Add Medicine/Lab Item
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {inventory.map((item) => (
                  <div key={item.id} className={`border rounded-lg p-4 ${
                    item.current_stock <= item.minimum_stock ? 'border-red-300 bg-red-50' : 'border-gray-200'
                  }`}>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.name}</h3>
                    <div className="space-y-1 text-sm text-gray-600">
                      <p><span className="font-medium">Category:</span> {item.category}</p>
                      <p><span className="font-medium">Stock:</span> {item.current_stock} {item.unit}</p>
                      <p><span className="font-medium">Min Stock:</span> {item.minimum_stock} {item.unit}</p>
                      <p><span className="font-medium">Cost/Unit:</span> ₹{item.cost_per_unit}</p>
                      <p><span className="font-medium">Location:</span> {item.location}</p>
                      {item.supplier && <p><span className="font-medium">Supplier:</span> {item.supplier}</p>}
                    </div>
                    {item.current_stock <= item.minimum_stock && (
                      <div className="mt-2">
                        <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                          ⚠️ Low Stock
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Health Packages Tab */}
        {activeTab === 'packages' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">🧪 Health Package Management</h2>
                <p className="text-gray-600">Create comprehensive health checkup packages</p>
              </div>
              <button
                onClick={() => setPackageModal(true)}
                className="bg-teal-600 text-white px-4 py-2 rounded-lg hover:bg-teal-700"
              >
                📦 Create Health Package
              </button>
            </div>
            <div className="p-6">
              <div className="bg-teal-50 border border-teal-200 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-teal-900 mb-2">💡 Package Benefits:</h3>
                <ul className="text-teal-800 text-sm space-y-1">
                  <li>• Combine multiple lab tests at discounted prices</li>
                  <li>• Create targeted packages (diabetes, heart health, etc.)</li>
                  <li>• Set custom pricing with automatic discount calculation</li>
                  <li>• Encourage comprehensive health checkups</li>
                </ul>
              </div>
              <p className="text-gray-600">Create attractive health packages that bundle multiple tests at discounted rates.</p>
            </div>
          </div>
        )}

        {/* Festive Offers/Campaigns Tab */}
        {activeTab === 'campaigns' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">🎯 Festive Offers & Campaigns</h2>
                <p className="text-gray-600">Create seasonal discounts and promotional campaigns</p>
              </div>
              <button
                onClick={() => setCampaignModal(true)}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
              >
                🎉 Create Festive Offer
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {campaigns.map((campaign) => (
                  <div key={campaign.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{campaign.name}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        campaign.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {campaign.is_active ? '✅ Active' : '❌ Inactive'}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-2">{campaign.description}</p>
                    <div className="space-y-1 text-sm text-gray-600">
                      <p><span className="font-medium">Type:</span> {campaign.campaign_type}</p>
                      <p><span className="font-medium">Discount:</span> {campaign.discount_percentage}%</p>
                      <p><span className="font-medium">Applies to:</span> {campaign.applicable_to}</p>
                      <p><span className="font-medium">Period:</span> {campaign.start_date} to {campaign.end_date}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Patient Documents Tab */}
        {activeTab === 'patients' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">👥 Patient Document Management</h2>
                <p className="text-gray-600">Upload and manage patient documents (OP cards, lab results, ECG)</p>
              </div>
              <button
                onClick={() => setDocumentModal(true)}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
              >
                📄 Upload Patient Document
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {patients.map((patient) => (
                  <div key={patient.id} className="border rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{patient.full_name}</h3>
                    <div className="space-y-1 text-sm text-gray-600 mb-4">
                      {patient.email && <p><span className="font-medium">Email:</span> {patient.email}</p>}
                      {patient.phone && <p><span className="font-medium">Phone:</span> {patient.phone}</p>}
                      {patient.date_of_birth && <p><span className="font-medium">DOB:</span> {patient.date_of_birth}</p>}
                    </div>
                    
                    <div className="space-y-2">
                      <button
                        onClick={() => {
                          setDocumentUpload({...documentUpload, patient_id: patient.id});
                          setDocumentModal(true);
                        }}
                        className="w-full bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700"
                      >
                        📤 Upload Documents
                      </button>
                      <button
                        onClick={() => viewPatientDocuments(patient)}
                        className="w-full bg-green-600 text-white py-2 px-3 rounded text-sm hover:bg-green-700"
                      >
                        👁️ View Documents
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Feedback Review Tab */}
        {activeTab === 'feedback' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">⭐ Patient Feedback Review</h2>
              <p className="text-gray-600">Monitor patient satisfaction and doctor performance</p>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {feedback.map((item) => (
                  <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-medium text-gray-900">Patient Feedback</p>
                        <div className="flex items-center mt-1">
                          {[...Array(5)].map((_, i) => (
                            <svg
                              key={i}
                              className={`w-4 h-4 ${
                                i < item.rating ? 'text-yellow-400' : 'text-gray-300'
                              }`}
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ))}
                          <span className="ml-2 text-sm text-gray-600">{item.rating}/5</span>
                        </div>
                      </div>
                      <span className="text-sm text-gray-500">
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {item.comment && (
                      <p className="text-gray-700 mt-2">{item.comment}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Doctor Modal */}
      {doctorModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">👨‍⚕️ Add New Doctor</h2>
              <button
                onClick={() => setDoctorModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Doctor Name *</label>
                <input
                  type="text"
                  value={newDoctor.name}
                  onChange={(e) => setNewDoctor({...newDoctor, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Dr. John Smith"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Specialty *</label>
                <input
                  type="text"
                  value={newDoctor.specialty}
                  onChange={(e) => setNewDoctor({...newDoctor, specialty: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Cardiology"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Qualification *</label>
                <input
                  type="text"
                  value={newDoctor.qualification}
                  onChange={(e) => setNewDoctor({...newDoctor, qualification: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="MD, DM Cardiology"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Experience (years) *</label>
                  <input
                    type="number"
                    value={newDoctor.experience_years}
                    onChange={(e) => setNewDoctor({...newDoctor, experience_years: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Consultation Fee (₹) *</label>
                  <input
                    type="number"
                    value={newDoctor.consultation_fee}
                    onChange={(e) => setNewDoctor({...newDoctor, consultation_fee: parseFloat(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setDoctorModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createDoctor}
                  className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  ➕ Add Doctor
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Template Modal */}
      {scheduleModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">🕒 Create Schedule Template</h2>
              <button
                onClick={() => setScheduleModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Doctor</label>
                <select
                  value={newScheduleTemplate.doctor_id}
                  onChange={(e) => setNewScheduleTemplate({...newScheduleTemplate, doctor_id: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Doctor</option>
                  {doctors.map(doctor => (
                    <option key={doctor.id} value={doctor.id}>{doctor.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Template Name</label>
                <input
                  type="text"
                  value={newScheduleTemplate.template_name}
                  onChange={(e) => setNewScheduleTemplate({...newScheduleTemplate, template_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Weekday Morning Schedule"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Working Days</label>
                <div className="flex flex-wrap gap-2">
                  {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, index) => (
                    <label key={day} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newScheduleTemplate.days_of_week.includes(index)}
                        onChange={() => handleDayToggle(index)}
                        className="mr-2"
                      />
                      {day}
                    </label>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Start Time</label>
                  <input
                    type="time"
                    value={newScheduleTemplate.start_time}
                    onChange={(e) => setNewScheduleTemplate({...newScheduleTemplate, start_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">End Time</label>
                  <input
                    type="time"
                    value={newScheduleTemplate.end_time}
                    onChange={(e) => setNewScheduleTemplate({...newScheduleTemplate, end_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Slot Duration (minutes)</label>
                <input
                  type="number"
                  value={newScheduleTemplate.slot_duration}
                  onChange={(e) => setNewScheduleTemplate({...newScheduleTemplate, slot_duration: parseInt(e.target.value) || 30})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="30"
                />
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setScheduleModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createScheduleTemplate}
                  className="flex-1 py-2 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  🕒 Create Template
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Inventory Modal */}
      {inventoryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">📦 Add Medicine/Lab Item</h2>
              <button
                onClick={() => setInventoryModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Item Name *</label>
                <input
                  type="text"
                  value={newInventoryItem.name}
                  onChange={(e) => setNewInventoryItem({...newInventoryItem, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Paracetamol 500mg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Category *</label>
                <select
                  value={newInventoryItem.category}
                  onChange={(e) => setNewInventoryItem({...newInventoryItem, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="medicine">💊 Medicine</option>
                  <option value="lab_equipment">🔬 Lab Equipment</option>
                  <option value="lab_supply">🧪 Lab Supply</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Current Stock *</label>
                  <input
                    type="number"
                    value={newInventoryItem.current_stock}
                    onChange={(e) => setNewInventoryItem({...newInventoryItem, current_stock: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Minimum Stock *</label>
                  <input
                    type="number"
                    value={newInventoryItem.minimum_stock}
                    onChange={(e) => setNewInventoryItem({...newInventoryItem, minimum_stock: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Unit *</label>
                  <input
                    type="text"
                    value={newInventoryItem.unit}
                    onChange={(e) => setNewInventoryItem({...newInventoryItem, unit: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="tablets, ml, grams"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Cost per Unit (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newInventoryItem.cost_per_unit}
                    onChange={(e) => setNewInventoryItem({...newInventoryItem, cost_per_unit: parseFloat(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Supplier</label>
                <input
                  type="text"
                  value={newInventoryItem.supplier}
                  onChange={(e) => setNewInventoryItem({...newInventoryItem, supplier: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Supplier name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Location *</label>
                <select
                  value={newInventoryItem.location}
                  onChange={(e) => setNewInventoryItem({...newInventoryItem, location: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="pharmacy">🏥 Pharmacy</option>
                  <option value="lab_room_1">🔬 Lab Room 1</option>
                  <option value="lab_room_2">🔬 Lab Room 2</option>
                  <option value="storage">📦 Storage</option>
                </select>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setInventoryModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createInventoryItem}
                  className="flex-1 py-2 px-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  📦 Add Item
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Campaign Modal */}
      {campaignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">🎉 Create Festive Offer</h2>
              <button
                onClick={() => setCampaignModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Campaign Name *</label>
                <input
                  type="text"
                  value={newCampaign.name}
                  onChange={(e) => setNewCampaign({...newCampaign, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Diwali Health Special"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description *</label>
                <textarea
                  value={newCampaign.description}
                  onChange={(e) => setNewCampaign({...newCampaign, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Get 10% off on all medicines this festive season!"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Campaign Type *</label>
                  <select
                    value={newCampaign.campaign_type}
                    onChange={(e) => setNewCampaign({...newCampaign, campaign_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="discount">💰 Discount</option>
                    <option value="buy_one_get_one">🎁 Buy One Get One</option>
                    <option value="festive_offer">🎊 Festive Offer</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Discount % *</label>
                  <input
                    type="number"
                    value={newCampaign.discount_percentage}
                    onChange={(e) => setNewCampaign({...newCampaign, discount_percentage: parseFloat(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Applicable To *</label>
                <select
                  value={newCampaign.applicable_to}
                  onChange={(e) => setNewCampaign({...newCampaign, applicable_to: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="medicines">💊 Medicines</option>
                  <option value="lab_tests">🔬 Lab Tests</option>
                  <option value="all">🏥 All Services</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Start Date *</label>
                  <input
                    type="date"
                    value={newCampaign.start_date}
                    onChange={(e) => setNewCampaign({...newCampaign, start_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">End Date *</label>
                  <input
                    type="date"
                    value={newCampaign.end_date}
                    onChange={(e) => setNewCampaign({...newCampaign, end_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setCampaignModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createCampaign}
                  className="flex-1 py-2 px-4 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
                >
                  🎉 Create Campaign
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Health Package Modal */}
      {packageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">🧪 Create Health Package</h2>
              <button
                onClick={() => setPackageModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Package Name *</label>
                <input
                  type="text"
                  value={newPackage.name}
                  onChange={(e) => setNewPackage({...newPackage, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Complete Health Checkup"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description *</label>
                <textarea
                  value={newPackage.description}
                  onChange={(e) => setNewPackage({...newPackage, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Comprehensive package including essential health tests"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Tests *</label>
                <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-lg p-2">
                  {tests.map((test) => (
                    <label key={test.id} className="flex items-center p-2 hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={newPackage.test_ids.includes(test.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewPackage({
                              ...newPackage,
                              test_ids: [...newPackage.test_ids, test.id]
                            });
                          } else {
                            setNewPackage({
                              ...newPackage,
                              test_ids: newPackage.test_ids.filter(id => id !== test.id)
                            });
                          }
                        }}
                        className="mr-3"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium">{test.name}</div>
                        <div className="text-xs text-gray-500">₹{test.price}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Package Price (₹) *</label>
                <input
                  type="number"
                  value={newPackage.package_price}
                  onChange={(e) => setNewPackage({...newPackage, package_price: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="1500"
                />
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setPackageModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createPackage}
                  className="flex-1 py-2 px-4 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
                >
                  🧪 Create Package
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Document Upload Modal */}
      {documentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">📄 Upload Patient Document</h2>
              <button
                onClick={() => setDocumentModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Patient *</label>
                <select
                  value={documentUpload.patient_id}
                  onChange={(e) => setDocumentUpload({...documentUpload, patient_id: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>{patient.full_name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Document Type *</label>
                <select
                  value={documentUpload.document_type}
                  onChange={(e) => setDocumentUpload({...documentUpload, document_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="opcard">📋 OP Card</option>
                  <option value="lab_result">🧪 Lab Result</option>
                  <option value="ecg_result">❤️ ECG Result</option>
                  <option value="xray">📷 X-Ray</option>
                  <option value="scan">🔍 CT/MRI Scan</option>
                  <option value="prescription">💊 Prescription</option>
                  <option value="medical_report">📄 Medical Report</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={documentUpload.description}
                  onChange={(e) => setDocumentUpload({...documentUpload, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="2"
                  placeholder="Brief description of the document"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Upload File *</label>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                  onChange={(e) => setDocumentUpload({...documentUpload, file: e.target.files[0]})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Accepted: PDF, JPG, PNG, DOC, DOCX (Max 10MB)</p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setDocumentModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={uploadPatientDocument}
                  className="flex-1 py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  📤 Upload Document
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Patient Documents View Modal */}
      {patientDocModal && selectedPatient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">📄 Documents for {selectedPatient.full_name}</h2>
              <button
                onClick={() => setPatientDocModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {patientDocuments.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No documents uploaded for this patient</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {patientDocuments.map((doc) => (
                    <div key={doc.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-semibold text-gray-900">{doc.document_name}</h3>
                        <button
                          onClick={() => deletePatientDocument(doc.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Delete Document"
                        >
                          🗑️
                        </button>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600">
                        <p><span className="font-medium">Type:</span> {doc.document_type}</p>
                        <p><span className="font-medium">Size:</span> {Math.round(doc.file_size / 1024)} KB</p>
                        <p><span className="font-medium">Uploaded:</span> {new Date(doc.created_at).toLocaleDateString()}</p>
                        {doc.description && <p><span className="font-medium">Notes:</span> {doc.description}</p>}
                      </div>
                      <div className="mt-3">
                        <a
                          href={`${BACKEND_URL}${doc.file_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block w-full text-center bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700"
                        >
                          👁️ View Document
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComprehensiveAdminDashboard;