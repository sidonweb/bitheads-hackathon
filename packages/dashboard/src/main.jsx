import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import { applyTheme, readTheme } from './lib/theme.js';
import './styles.css';
import './index.css';

applyTheme(readTheme());

createRoot(document.getElementById('root')).render(<App />);
