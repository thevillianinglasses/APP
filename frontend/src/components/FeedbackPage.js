import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FeedbackPage = () => {
  const [appointment, setAppointment] = useState(null);
  const [doctor, setDoctor] = useState(null);
  const [feedback, setFeedback] = useState({
    rating: 5,
    comment: '',
    feedback_categories: {
      professionalism: 5,
      waiting_time: 5,
      facility_cleanliness: 5,
      overall_experience: 5
    },
    is_anonymous: false
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const { appointmentId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchAppointmentDetails();
  }, [appointmentId]);

  const fetchAppointmentDetails = async () => {
    try {
      // Get user appointments and find the specific one
      const appointmentsResponse = await axios.get(`${API}/appointments/my`);
      const foundAppointment = appointmentsResponse.data.find(apt => apt.id === appointmentId);
      
      if (!foundAppointment) {
        alert('Appointment not found');
        navigate('/appointments');
        return;
      }

      if (foundAppointment.status !== 'completed') {
        alert('Feedback can only be submitted for completed appointments');
        navigate('/appointments');
        return;
      }

      setAppointment(foundAppointment);

      // Get doctor details
      const doctorResponse = await axios.get(`${API}/doctors/${foundAppointment.doctor_id}`);
      setDoctor(doctorResponse.data);

    } catch (error) {
      console.error('Error fetching appointment details:', error);
      alert('Error loading appointment details');
      navigate('/appointments');
    } finally {
      setLoading(false);
    }
  };

  const handleRatingChange = (category, rating) => {
    if (category === 'overall') {
      setFeedback({ ...feedback, rating: rating });
    } else {
      setFeedback({
        ...feedback,
        feedback_categories: {
          ...feedback.feedback_categories,
          [category]: rating
        }
      });
    }
  };

  const submitFeedback = async () => {
    if (!appointment || !doctor) {
      alert('Missing appointment or doctor information');
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/feedback`, {
        doctor_id: doctor.id,
        appointment_id: appointment.id,
        rating: feedback.rating,
        comment: feedback.comment,
        feedback_categories: feedback.feedback_categories,
        is_anonymous: feedback.is_anonymous
      });

      alert('Thank you for your feedback!');
      navigate('/appointments');
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('Error submitting feedback: ' + (error.response?.data?.detail || 'Something went wrong'));
    } finally {
      setSubmitting(false);
    }
  };

  const StarRating = ({ value, onChange, label }) => {
    return (
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
        <div className="flex items-center space-x-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => onChange(star)}
              className={`w-8 h-8 ${
                star <= value ? 'text-yellow-400' : 'text-gray-300'
              } hover:text-yellow-400 transition-colors`}
            >
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </button>
          ))}
          <span className="ml-2 text-sm text-gray-600">{value}/5</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!appointment || !doctor) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Appointment or doctor information not found.</p>
          <button
            onClick={() => navigate('/appointments')}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Back to Appointments
          </button>
        </div>
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
                onClick={() => navigate('/appointments')}
                className="text-blue-600 hover:text-blue-700 mr-4"
              >
                ← Back to Appointments
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Submit Feedback</h1>
            </div>
            <div className="flex items-center">
              <span className="text-gray-700">Consultation Feedback</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">How was your consultation?</h2>
            <p className="text-gray-600">Your feedback helps us improve our services</p>
          </div>

          <div className="p-6">
            {/* Appointment Details */}
            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <h3 className="font-medium text-gray-900 mb-2">Consultation Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <span className="font-medium">Doctor:</span> Dr. {doctor.name}
                </div>
                <div>
                  <span className="font-medium">Specialty:</span> {doctor.specialty}
                </div>
                <div>
                  <span className="font-medium">Date:</span> {appointment.appointment_date}
                </div>
                <div>
                  <span className="font-medium">Time:</span> {appointment.appointment_time}
                </div>
              </div>
            </div>

            {/* Overall Rating */}
            <StarRating
              value={feedback.rating}
              onChange={(rating) => handleRatingChange('overall', rating)}
              label="Overall Experience *"
            />

            {/* Category Ratings */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Rate Different Aspects</h3>
              <div className="space-y-4">
                <StarRating
                  value={feedback.feedback_categories.professionalism}
                  onChange={(rating) => handleRatingChange('professionalism', rating)}
                  label="Doctor's Professionalism"
                />
                <StarRating
                  value={feedback.feedback_categories.waiting_time}
                  onChange={(rating) => handleRatingChange('waiting_time', rating)}
                  label="Waiting Time"
                />
                <StarRating
                  value={feedback.feedback_categories.facility_cleanliness}
                  onChange={(rating) => handleRatingChange('facility_cleanliness', rating)}
                  label="Facility Cleanliness"
                />
                <StarRating
                  value={feedback.feedback_categories.overall_experience}
                  onChange={(rating) => handleRatingChange('overall_experience', rating)}
                  label="Overall Experience"
                />
              </div>
            </div>

            {/* Comment */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Comments (Optional)
              </label>
              <textarea
                value={feedback.comment}
                onChange={(e) => setFeedback({ ...feedback, comment: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="4"
                placeholder="Tell us more about your experience..."
              />
            </div>

            {/* Anonymous Option */}
            <div className="mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={feedback.is_anonymous}
                  onChange={(e) => setFeedback({ ...feedback, is_anonymous: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Submit feedback anonymously</span>
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Anonymous feedback helps us improve while keeping your identity private
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex space-x-4">
              <button
                onClick={() => navigate('/appointments')}
                className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Skip for Now
              </button>
              <button
                onClick={submitFeedback}
                disabled={submitting}
                className="flex-1 py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Submitting...
                  </div>
                ) : (
                  'Submit Feedback'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Thank You Message */}
        <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-green-800 font-medium">
              Thank you for taking the time to provide feedback!
            </span>
          </div>
          <p className="text-green-700 text-sm mt-1">
            Your feedback helps us maintain high-quality healthcare services and improve patient experience.
          </p>
        </div>
      </div>
    </div>
  );
};

export default FeedbackPage;