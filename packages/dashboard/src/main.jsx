import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App.jsx';
import EvalDashboard from './pages/EvalDashboard.jsx';
import { applyTheme, readTheme } from './lib/theme.js';
import './styles.css';
import './index.css';

applyTheme(readTheme());

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/evals" element={<EvalDashboard />} />
    </Routes>
  </BrowserRouter>,
);
