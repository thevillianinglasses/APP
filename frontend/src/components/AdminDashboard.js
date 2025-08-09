import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = () => {
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('patients');
  const [newPackage, setNewPackage] = useState({
    name: '',
    description: '',
    test_ids: [],
    original_price: 0,
    package_price: 0,
    discount_percentage: 0
  });
  const [tests, setTests] = useState([]);
  const [packageModal, setPackageModal] = useState(false);
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
      const [patientsResponse, doctorsResponse, testsResponse] = await Promise.all([
        axios.get(`${API}/admin/patients`),
        axios.get(`${API}/doctors`),
        axios.get(`${API}/lab-tests`)
      ]);
      
      setPatients(patientsResponse.data);
      setDoctors(doctorsResponse.data);
      setTests(testsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const approvePatient = async (patientId) => {
    try {
      await axios.put(`${API}/admin/patients/${patientId}/approve`);
      setPatients(patients.map(patient =>
        patient.id === patientId ? { ...patient, is_approved: true } : patient
      ));
      alert('Patient approved successfully!');
    } catch (error) {
      alert('Error approving patient: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const updateDoctorStatus = async (doctorId, status, isAvailable) => {
    try {
      await axios.put(`${API}/doctors/${doctorId}/status`, {
        status,
        is_available: isAvailable
      });
      
      setDoctors(doctors.map(doctor =>
        doctor.id === doctorId ? { ...doctor, status, is_available: isAvailable } : doctor
      ));
      alert('Doctor status updated successfully!');
    } catch (error) {
      alert('Error updating doctor status: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  const calculatePackageDetails = () => {
    const selectedTests = tests.filter(test => newPackage.test_ids.includes(test.id));
    const originalPrice = selectedTests.reduce((total, test) => total + test.price, 0);
    const discountAmount = originalPrice - newPackage.package_price;
    const discountPercentage = originalPrice > 0 ? ((discountAmount / originalPrice) * 100).toFixed(2) : 0;
    
    return { originalPrice, discountPercentage };
  };

  const createLabPackage = async () => {
    if (!newPackage.name || !newPackage.description || newPackage.test_ids.length === 0) {
      alert('Please fill in all required fields and select at least one test');
      return;
    }

    const { originalPrice, discountPercentage } = calculatePackageDetails();

    try {
      await axios.post(`${API}/admin/lab-packages`, {
        ...newPackage,
        original_price: originalPrice,
        discount_percentage: parseFloat(discountPercentage)
      });
      
      alert('Lab package created successfully!');
      setPackageModal(false);
      setNewPackage({
        name: '',
        description: '',
        test_ids: [],
        original_price: 0,
        package_price: 0,
        discount_percentage: 0
      });
    } catch (error) {
      alert('Error creating package: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
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

  const { originalPrice, discountPercentage } = calculatePackageDetails();

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
              <h1 className="text-xl font-semibold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center">
              <span className="text-gray-700">Admin Panel</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
          <button
            onClick={() => setActiveTab('patients')}
            className={`flex-1 py-2 px-4 rounded-md font-medium ${
              activeTab === 'patients'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Patient Approvals
          </button>
          <button
            onClick={() => setActiveTab('doctors')}
            className={`flex-1 py-2 px-4 rounded-md font-medium ${
              activeTab === 'doctors'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Doctor Management
          </button>
          <button
            onClick={() => setActiveTab('packages')}
            className={`flex-1 py-2 px-4 rounded-md font-medium ${
              activeTab === 'packages'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Lab Packages
          </button>
        </div>

        {/* Patient Approvals Tab */}
        {activeTab === 'patients' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Patient Access Requests</h2>
              <p className="text-gray-600">Approve patients to access their medical records</p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Patient Details
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {patients.map((patient) => (
                    <tr key={patient.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{patient.full_name}</div>
                          {patient.date_of_birth && (
                            <div className="text-sm text-gray-500">DOB: {patient.date_of_birth}</div>
                          )}
                          {patient.address && (
                            <div className="text-sm text-gray-500">{patient.address}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {patient.email && <div>Email: {patient.email}</div>}
                          {patient.phone && <div>Phone: {patient.phone}</div>}
                          {patient.emergency_contact && (
                            <div className="text-red-600">Emergency: {patient.emergency_contact}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          patient.is_approved
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {patient.is_approved ? 'Approved' : 'Pending'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {!patient.is_approved && (
                          <button
                            onClick={() => approvePatient(patient.id)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Approve Access
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {patients.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No patient records found
                </div>
              )}
            </div>
          </div>
        )}

        {/* Doctor Management Tab */}
        {activeTab === 'doctors' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Doctor Status Management</h2>
              <p className="text-gray-600">Update doctor availability and status</p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {doctors.map((doctor) => (
                  <div key={doctor.id} className="border rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{doctor.name}</h3>
                    <p className="text-gray-600 mb-2">{doctor.specialty}</p>
                    <p className="text-gray-600 mb-4">Fee: ₹{doctor.consultation_fee}</p>
                    
                    <div className="mb-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        doctor.status === 'available' ? 'bg-green-100 text-green-800' :
                        doctor.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {doctor.status === 'available' ? 'Available' :
                         doctor.status === 'busy' ? 'Busy' : 'On Leave'}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <button
                        onClick={() => updateDoctorStatus(doctor.id, 'available', true)}
                        className={`w-full py-2 px-3 rounded text-sm ${
                          doctor.status === 'available'
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-green-100'
                        }`}
                      >
                        Set Available
                      </button>
                      <button
                        onClick={() => updateDoctorStatus(doctor.id, 'busy', true)}
                        className={`w-full py-2 px-3 rounded text-sm ${
                          doctor.status === 'busy'
                            ? 'bg-yellow-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-yellow-100'
                        }`}
                      >
                        Set Busy
                      </button>
                      <button
                        onClick={() => updateDoctorStatus(doctor.id, 'on_leave', false)}
                        className={`w-full py-2 px-3 rounded text-sm ${
                          doctor.status === 'on_leave'
                            ? 'bg-red-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-red-100'
                        }`}
                      >
                        Set On Leave
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Lab Packages Tab */}
        {activeTab === 'packages' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Lab Package Management</h2>
                <p className="text-gray-600">Create custom health checkup packages</p>
              </div>
              <button
                onClick={() => setPackageModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Create New Package
              </button>
            </div>
            <div className="p-6">
              <p className="text-gray-600">Lab package management interface will be displayed here.</p>
            </div>
          </div>
        )}
      </div>

      {/* Create Package Modal */}
      {packageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Create Lab Package</h2>
              <button
                onClick={() => setPackageModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
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
                  placeholder="e.g., Complete Health Checkup"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description *</label>
                <textarea
                  value={newPackage.description}
                  onChange={(e) => setNewPackage({...newPackage, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Describe the package and its benefits"
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Package Price *</label>
                <input
                  type="number"
                  value={newPackage.package_price}
                  onChange={(e) => setNewPackage({...newPackage, package_price: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter package price"
                />
              </div>

              {newPackage.test_ids.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Package Summary:</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <div>Selected Tests: {newPackage.test_ids.length}</div>
                    <div>Original Price: ₹{originalPrice}</div>
                    <div>Package Price: ₹{newPackage.package_price}</div>
                    <div className="text-green-600 font-medium">
                      Discount: {discountPercentage}% (₹{originalPrice - newPackage.package_price})
                    </div>
                  </div>
                </div>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={() => setPackageModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createLabPackage}
                  className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Package
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;