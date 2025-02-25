import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, BookOpen, Star, Clock, User, SlidersHorizontal, ChevronDown, X } from 'lucide-react';

function CourseList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);

  const filters = {
    'Course Level': ['100-200', '300-400', '500+'],
    'Time': ['8:30 AM', '10:05 AM', '11:45 AM', '1:25 PM', '3:05 PM', '4:40 PM', '6:15 PM'],
    'Days': ['Monday/Wednesday/Friday', 'Tuesday/Thursday'],
    'Prerequisites': ['None', 'Basic', 'Advanced'],
    'Rating': ['4.5+', '4.0+', '3.5+'],
  };

  const timeSlots = [
    '8:30 AM - 9:45 AM',
    '10:05 AM - 11:20 AM',
    '11:45 AM - 1:00 PM',
    '1:25 PM - 2:40 PM',
    '3:05 PM - 4:20 PM',
    '4:40 PM - 5:55 PM',
    '6:15 PM - 7:30 PM'
  ];

  const toggleFilter = (filter: string) => {
    setSelectedFilters(prev => 
      prev.includes(filter)
        ? prev.filter(f => f !== filter)
        : [...prev, filter]
    );
  };

  return (
    <div className="min-h-screen bg-white">
      <header className="bg-blue-900 sticky top-0 z-50">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-8 h-8 text-blue-200" />
            <span className="text-xl font-bold text-white">Clasi.</span>
          </div>
          <button className="flex items-center space-x-2 bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded-lg transition">
            <User className="w-4 h-4" />
            <span>Sign In</span>
          </button>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Filters Sidebar */}
          <div className="w-full md:w-64 flex-shrink-0">
            <div className="bg-blue-900 rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white">Filters</h2>
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="md:hidden text-white"
                >
                  <SlidersHorizontal className="w-5 h-5" />
                </button>
              </div>
              
              <div className={`space-y-6 ${showFilters ? 'block' : 'hidden md:block'}`}>
                {Object.entries(filters).map(([category, options]) => (
                  <div key={category} className="space-y-3">
                    <h3 className="text-white font-medium">{category}</h3>
                    <div className="space-y-2">
                      {options.map(option => (
                        <label
                          key={option}
                          className="flex items-center space-x-2 text-blue-200 hover:text-white cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedFilters.includes(option)}
                            onChange={() => toggleFilter(option)}
                            className="rounded border-gray-400 text-blue-500 focus:ring-blue-500"
                          />
                          <span>{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {/* Search Bar */}
            <div className="relative mb-6">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search for courses by name, professor, or department"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 bg-white rounded-xl shadow-lg focus:ring-2 focus:ring-blue-500 focus:outline-none border border-gray-200"
              />
            </div>

            {/* Active Filters */}
            {selectedFilters.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {selectedFilters.map(filter => (
                  <button
                    key={filter}
                    onClick={() => toggleFilter(filter)}
                    className="flex items-center space-x-1 bg-blue-100 text-blue-700 px-3 py-1 rounded-full hover:bg-blue-200 transition"
                  >
                    <span>{filter}</span>
                    <X className="w-4 h-4" />
                  </button>
                ))}
              </div>
            )}

            {/* Sort Dropdown */}
            <div className="flex justify-between items-center mb-6">
              <p className="text-gray-600">Showing 24 results</p>
              <div className="relative">
                <select className="appearance-none bg-white border border-gray-200 text-gray-700 px-4 py-2 pr-8 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>Most Relevant</option>
                  <option>Highest Rated</option>
                  <option>Easiest Courses</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
              </div>
            </div>

            {/* Course Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {[...Array(6)].map((_, i) => (
                <div 
                  key={i} 
                  className="bg-blue-900 rounded-xl p-6 hover:transform hover:scale-105 transition cursor-pointer"
                  onClick={() => navigate(`/course/${201 + i}`)}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-xl font-semibold text-white">CS {201 + i}</h3>
                        <div className="flex space-x-2">
                          <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded-lg text-sm">
                            Prof: {4.5} ★
                          </span>
                          <span className="bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded-lg text-sm">
                            Course: {4.2} ★
                          </span>
                        </div>
                      </div>
                      <p className="text-blue-200">Data Structures & Algorithms</p>
                    </div>
                  </div>
                  <div className="space-y-2 text-sm text-blue-200">
                    <p className="flex items-center space-x-1">
                      <User className="w-4 h-4" />
                      <span>Prof. Sarah Johnson</span>
                    </p>
                    <p className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{timeSlots[i % timeSlots.length]}</span>
                    </p>
                    <p className="flex items-center space-x-1">
                      <BookOpen className="w-4 h-4" />
                      <span>Prerequisites: CS 101</span>
                    </p>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full text-sm">
                      Spring 2024
                    </span>
                    <span className="bg-purple-500/20 text-purple-300 px-2 py-1 rounded-full text-sm">
                      Core Course
                    </span>
                    <span className="bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded-full text-sm">
                      3 Credits
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default CourseList;