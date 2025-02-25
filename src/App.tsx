import React from 'react';
import { Routes, Route } from 'react-router-dom';
import CourseList from './components/CourseList';
import CourseDetails from './components/CourseDetails';

function App() {
  return (
    <Routes>
      <Route path="/" element={<CourseList />} />
      <Route path="/course/:id" element={<CourseDetails />} />
    </Routes>
  );
}

export default App;