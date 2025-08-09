import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LabTestsPage = () => {
  const [tests, setTests] = useState([]);
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTests, setSelectedTests] = useState([]);
  const [selectedPackages, setSelectedPackages] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [activeTab, setActiveTab] = useState('tests');
  const [cartModal, setCartModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [testsResponse, packagesResponse] = await Promise.all([
        axios.get(`${API}/lab-tests`),
        axios.get(`${API}/lab-packages`)
      ]);
      setTests(testsResponse.data);
      setPackages(packagesResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const categories = [...new Set(tests.map(test => test.category))];

  const filteredTests = tests.filter(test => {
    const matchesSearch = test.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         test.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === '' || test.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const filteredPackages = packages.filter(pkg =>
    pkg.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const toggleTestSelection = (test) => {
    setSelectedTests(prev => {
      const exists = prev.find(t => t.id === test.id);
      if (exists) {
        return prev.filter(t => t.id !== test.id);
      } else {
        return [...prev, test];
      }
    });
  };

  const togglePackageSelection = (pkg) => {
    setSelectedPackages(prev => {
      const exists = prev.find(p => p.id === pkg.id);
      if (exists) {
        return prev.filter(p => p.id !== pkg.id);
      } else {
        return [...prev, pkg];
      }
    });
  };

  const getTotalAmount = () => {
    const testsTotal = selectedTests.reduce((total, test) => total + test.price, 0);
    const packagesTotal = selectedPackages.reduce((total, pkg) => total + pkg.package_price, 0);
    return testsTotal + packagesTotal;
  };

  const getTestsFromPackages = () => {
    const testIds = selectedPackages.flatMap(pkg => pkg.test_ids);
    return tests.filter(test => testIds.includes(test.id));
  };

  const handleBookTests = async () => {
    if (selectedTests.length === 0 && selectedPackages.length === 0) {
      alert('Please select at least one test or package');
      return;
    }

    try {
      await axios.post(`${API}/lab-tests/order`, {
        test_ids: selectedTests.map(test => test.id),
        package_ids: selectedPackages.map(pkg => pkg.id),
        total_amount: getTotalAmount()
      });

      alert('Lab tests booked successfully! You will receive collection instructions.');
      setSelectedTests([]);
      setSelectedPackages([]);
      setCartModal(false);
    } catch (error) {
      alert('Error booking tests: ' + (error.response?.data?.detail || 'Something went wrong'));
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
              <h1 className="text-xl font-semibold text-gray-900">Laboratory Services</h1>
            </div>
            <div className="flex items-center">
              <button
                onClick={() => setCartModal(true)}
                className="relative bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Selected ({selectedTests.length + selectedPackages.length})
                {(selectedTests.length + selectedPackages.length) > 0 && (
                  <span className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center">
                    {selectedTests.length + selectedPackages.length}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
          <button
            onClick={() => setActiveTab('tests')}
            className={`flex-1 py-2 px-4 rounded-md font-medium ${
              activeTab === 'tests'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Individual Tests
          </button>
          <button
            onClick={() => setActiveTab('packages')}
            className={`flex-1 py-2 px-4 rounded-md font-medium ${
              activeTab === 'packages'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Health Packages
          </button>
        </div>

        {/* Filters */}
        <div className="mb-6 bg-white p-4 rounded-lg shadow-md">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder={`Search ${activeTab}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            {activeTab === 'tests' && (
              <div>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Categories</option>
                  {categories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        {activeTab === 'tests' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTests.map((test) => (
              <div
                key={test.id}
                className={`bg-white rounded-lg shadow-md overflow-hidden cursor-pointer transition-all ${
                  selectedTests.find(t => t.id === test.id)
                    ? 'ring-2 ring-blue-500 bg-blue-50'
                    : 'hover:shadow-lg'
                }`}
                onClick={() => toggleTestSelection(test)}
              >
                <div className="p-6">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">{test.name}</h3>
                    <div className="flex items-center">
                      <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded-full mr-2">
                        {test.code}
                      </span>
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                        selectedTests.find(t => t.id === test.id)
                          ? 'bg-blue-600 border-blue-600'
                          : 'border-gray-300'
                      }`}>
                        {selectedTests.find(t => t.id === test.id) && (
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2 mb-4">
                    <p className="text-sm text-gray-600"><strong>Category:</strong> {test.category}</p>
                    <p className="text-sm text-gray-600"><strong>Sample:</strong> {test.sample_type}</p>
                    <p className="text-sm text-gray-600"><strong>Duration:</strong> {test.estimated_duration}</p>
                    {test.preparation_required && (
                      <p className="text-sm text-orange-600"><strong>Preparation:</strong> {test.preparation_required}</p>
                    )}
                    {test.description && (
                      <p className="text-sm text-gray-600">{test.description}</p>
                    )}
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-xl font-bold text-blue-600">₹{test.price}</span>
                    <span className="text-sm text-gray-500">{test.estimated_duration}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredPackages.map((pkg) => (
              <div
                key={pkg.id}
                className={`bg-white rounded-lg shadow-md overflow-hidden cursor-pointer transition-all ${
                  selectedPackages.find(p => p.id === pkg.id)
                    ? 'ring-2 ring-blue-500 bg-blue-50'
                    : 'hover:shadow-lg'
                }`}
                onClick={() => togglePackageSelection(pkg)}
              >
                <div className="p-6">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">{pkg.name}</h3>
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                      selectedPackages.find(p => p.id === pkg.id)
                        ? 'bg-blue-600 border-blue-600'
                        : 'border-gray-300'
                    }`}>
                      {selectedPackages.find(p => p.id === pkg.id) && (
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </div>

                  <p className="text-gray-600 mb-4">{pkg.description}</p>

                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">Included Tests:</h4>
                    <div className="space-y-1">
                      {pkg.test_ids.map(testId => {
                        const test = tests.find(t => t.id === testId);
                        return test ? (
                          <div key={testId} className="flex justify-between text-sm">
                            <span className="text-gray-600">{test.name}</span>
                            <span className="text-gray-500">₹{test.price}</span>
                          </div>
                        ) : null;
                      })}
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-lg text-gray-500 line-through">₹{pkg.original_price}</span>
                        <span className="text-xl font-bold text-blue-600">₹{pkg.package_price}</span>
                      </div>
                      <span className="text-sm text-green-600 font-medium">
                        Save {pkg.discount_percentage}% (₹{pkg.original_price - pkg.package_price})
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {((activeTab === 'tests' && filteredTests.length === 0) || 
          (activeTab === 'packages' && filteredPackages.length === 0)) && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No {activeTab} found matching your criteria.</p>
          </div>
        )}
      </div>

      {/* Cart Modal */}
      {cartModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Selected Tests & Packages</h2>
              <button
                onClick={() => setCartModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {selectedTests.length === 0 && selectedPackages.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No tests or packages selected</p>
            ) : (
              <>
                <div className="space-y-4 mb-6">
                  {/* Selected Tests */}
                  {selectedTests.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Individual Tests:</h3>
                      {selectedTests.map((test) => (
                        <div key={test.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2">
                          <div>
                            <h4 className="font-medium">{test.name}</h4>
                            <p className="text-sm text-gray-600">{test.category} • {test.estimated_duration}</p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">₹{test.price}</span>
                            <button
                              onClick={() => toggleTestSelection(test)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Selected Packages */}
                  {selectedPackages.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Health Packages:</h3>
                      {selectedPackages.map((pkg) => (
                        <div key={pkg.id} className="p-3 bg-gray-50 rounded-lg mb-2">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">{pkg.name}</h4>
                            <div className="flex items-center space-x-2">
                              <span className="font-medium">₹{pkg.package_price}</span>
                              <button
                                onClick={() => togglePackageSelection(pkg)}
                                className="text-red-500 hover:text-red-700"
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 mb-1">{pkg.description}</p>
                          <p className="text-xs text-green-600">Save ₹{pkg.original_price - pkg.package_price}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="border-t pt-4">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-lg font-semibold">Total Amount: ₹{getTotalAmount()}</span>
                  </div>
                  <button
                    onClick={handleBookTests}
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 font-medium"
                  >
                    Book Lab Tests
                  </button>
                  <p className="text-sm text-gray-600 text-center mt-2">
                    You will receive sample collection instructions after booking
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LabTestsPage;