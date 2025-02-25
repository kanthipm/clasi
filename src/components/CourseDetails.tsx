import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { BookOpen, Star, Clock, User, ChevronLeft } from 'lucide-react';

function CourseDetails() {
  const { id } = useParams();
  const [rating, setRating] = useState(0);
  const [review, setReview] = useState('');

  const reviews = [
    {
      id: 1,
      author: "John D.",
      rating: 5,
      date: "March 15, 2024",
      comment: "Excellent course! Professor explains concepts clearly and assignments are challenging but fair.",
    },
    {
      id: 2,
      author: "Sarah M.",
      rating: 4,
      date: "March 10, 2024",
      comment: "Great content but heavy workload. Be prepared to spend a lot of time on assignments.",
    }
  ];

  const handleSubmitReview = (e: React.FormEvent) => {
    e.preventDefault();
    // Here you would typically send the review to your backend
    console.log({ rating, review });
    setRating(0);
    setReview('');
  };

  return (
    <div className="min-h-screen bg-white">
      <header className="bg-blue-900 sticky top-0 z-50">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center">
          <Link to="/" className="flex items-center space-x-2 text-white hover:text-blue-200 transition">
            <ChevronLeft className="w-5 h-5" />
            <span>Back to Courses</span>
          </Link>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-blue-900 rounded-xl p-8 mb-8">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center space-x-4 mb-2">
                <h1 className="text-3xl font-bold text-white">CS {id}</h1>
                <div className="flex space-x-2">
                  <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-lg">
                    Professor: 4.5 ★
                  </span>
                  <span className="bg-yellow-500/20 text-yellow-400 px-3 py-1 rounded-lg">
                    Course: 4.2 ★
                  </span>
                </div>
              </div>
              <h2 className="text-xl text-blue-200 mb-4">Data Structures & Algorithms</h2>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-blue-200">
            <div className="space-y-4">
              <p className="flex items-center space-x-2">
                <User className="w-5 h-5" />
                <span>Prof. Sarah Johnson</span>
              </p>
              <p className="flex items-center space-x-2">
                <Clock className="w-5 h-5" />
                <span>MWF 10:05 AM - 11:20 AM</span>
              </p>
              <p className="flex items-center space-x-2">
                <BookOpen className="w-5 h-5" />
                <span>Prerequisites: CS 101</span>
              </p>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-2">Course Description</h3>
              <p>
                An introduction to fundamental data structures and algorithms, with an emphasis on practical 
                implementation and theoretical analysis. Topics include lists, stacks, queues, trees, hash tables, 
                graphs, sorting, searching, and basic algorithmic analysis.
              </p>
            </div>
          </div>
        </div>

        {/* Review Form */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Write a Review</h3>
          <form onSubmit={handleSubmitReview} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
              <div className="flex space-x-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className={`p-1 ${rating >= star ? 'text-yellow-400' : 'text-gray-300'}`}
                  >
                    <Star className="w-8 h-8 fill-current" />
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Review</label>
              <textarea
                value={review}
                onChange={(e) => setReview(e.target.value)}
                rows={4}
                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="Share your experience with this course..."
              />
            </div>
            <button
              type="submit"
              className="bg-blue-900 text-white px-4 py-2 rounded-lg hover:bg-blue-800 transition"
            >
              Submit Review
            </button>
          </form>
        </div>

        {/* Reviews List */}
        <div className="space-y-6">
          <h3 className="text-xl font-semibold text-gray-900">Student Reviews</h3>
          {reviews.map((review) => (
            <div key={review.id} className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">{review.author}</span>
                    <span className="text-gray-500">•</span>
                    <span className="text-gray-500">{review.date}</span>
                  </div>
                  <div className="flex space-x-1 text-yellow-400 mt-1">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-5 h-5 ${i < review.rating ? 'fill-current' : 'text-gray-300'}`}
                      />
                    ))}
                  </div>
                </div>
              </div>
              <p className="text-gray-700">{review.comment}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default CourseDetails;