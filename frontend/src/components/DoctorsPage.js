import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DoctorsPage = () => {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [bookingModal, setBookingModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      const response = await axios.get(`${API}/doctors`);
      setDoctors(response.data);
    } catch (error) {
      console.error('Error fetching doctors:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'busy':
        return 'bg-yellow-100 text-yellow-800';
      case 'on_leave':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'available':
        return 'Available';
      case 'busy':
        return 'Busy';
      case 'on_leave':
        return 'On Leave';
      default:
        return 'Unknown';
    }
  };

  const getTodaySlots = (doctor) => {
    const today = new Date().toISOString().split('T')[0];
    return doctor.schedule[today] || [];
  };

  const getAvailableDates = (doctor) => {
    return Object.keys(doctor.schedule).filter(date => 
      new Date(date) >= new Date().setHours(0, 0, 0, 0)
    ).sort();
  };

  const handleBookAppointment = (doctor) => {
    setSelectedDoctor(doctor);
    setBookingModal(true);
    const availableDates = getAvailableDates(doctor);
    if (availableDates.length > 0) {
      setSelectedDate(availableDates[0]);
    }
  };

  const handleBookingSubmit = async () => {
    try {
      await axios.post(`${API}/appointments`, {
        doctor_id: selectedDoctor.id,
        appointment_date: selectedDate,
        appointment_time: selectedTime,
        symptoms: symptoms
      });
      
      alert('Appointment booked successfully!');
      setBookingModal(false);
      setSelectedDoctor(null);
      setSelectedDate('');
      setSelectedTime('');
      setSymptoms('');
    } catch (error) {
      alert('Error booking appointment: ' + (error.response?.data?.detail || 'Something went wrong'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

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
              <h1 className="text-xl font-semibold text-gray-900">Our Doctors</h1>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doctor) => (
            <div key={doctor.id} className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-gray-900">{doctor.name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(doctor.status)}`}>
                    {getStatusText(doctor.status)}
                  </span>
                </div>
                
                <div className="space-y-2 mb-4">
                  <p className="text-gray-600"><strong>Specialty:</strong> {doctor.specialty}</p>
                  <p className="text-gray-600"><strong>Qualification:</strong> {doctor.qualification}</p>
                  <p className="text-gray-600"><strong>Experience:</strong> {doctor.experience_years} years</p>
                  <p className="text-gray-600"><strong>Consultation Fee:</strong> ₹{doctor.consultation_fee}</p>
                </div>

                {doctor.status === 'available' && getTodaySlots(doctor).length > 0 ? (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Today's Available Slots:</p>
                    <div className="flex flex-wrap gap-1">
                      {getTodaySlots(doctor).slice(0, 4).map((slot) => (
                        <span key={slot} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                          {slot}
                        </span>
                      ))}
                      {getTodaySlots(doctor).length > 4 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                          +{getTodaySlots(doctor).length - 4} more
                        </span>
                      )}
                    </div>
                  </div>
                ) : doctor.status === 'on_leave' ? (
                  <div className="mb-4">
                    <p className="text-sm text-red-600">Currently on leave</p>
                  </div>
                ) : (
                  <div className="mb-4">
                    <p className="text-sm text-yellow-600">No slots available today</p>
                  </div>
                )}

                <button
                  onClick={() => handleBookAppointment(doctor)}
                  disabled={doctor.status === 'on_leave'}
                  className={`w-full py-2 px-4 rounded-lg font-medium ${
                    doctor.status === 'on_leave'
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {doctor.status === 'on_leave' ? 'Not Available' : 'Book Appointment'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Booking Modal */}
      {bookingModal && selectedDoctor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">Book Appointment with {selectedDoctor.name}</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Date</label>
                <select
                  value={selectedDate}
                  onChange={(e) => {
                    setSelectedDate(e.target.value);
                    setSelectedTime(''); // Reset time when date changes
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {getAvailableDates(selectedDoctor).map((date) => (
                    <option key={date} value={date}>{date}</option>
                  ))}
                </select>
              </div>

              {selectedDate && selectedDoctor.schedule[selectedDate] && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select Time</label>
                  <div className="grid grid-cols-3 gap-2">
                    {selectedDoctor.schedule[selectedDate].map((slot) => (
                      <button
                        key={slot}
                        onClick={() => setSelectedTime(slot)}
                        className={`px-3 py-2 text-sm rounded border ${
                          selectedTime === slot
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-50'
                        }`}
                      >
                        {slot}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Symptoms (Optional)</label>
                <textarea
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Describe your symptoms..."
                />
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setBookingModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleBookingSubmit}
                  disabled={!selectedDate || !selectedTime}
                  className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Book Appointment
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DoctorsPage;