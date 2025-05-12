// Ensure process.stdout exists for googleapis
window.process = window.process || {};
window.process.stdout = window.process.stdout || {};
window.process.stdout.isTTY = false;

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);