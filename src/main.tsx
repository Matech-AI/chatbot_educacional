// Polyfill process and stdout for googleapis
window.process = window.process || {};
window.process.stdout = window.process.stdout || {};
window.process.stderr = window.process.stderr || {};
window.process.stdin = window.process.stdin || {};

if (window.process) {
  window.process.stdout.isTTY = false;
  window.process.stderr.isTTY = false;
  window.process.stdin.isTTY = false;
  window.process.env = window.process.env || {};
  window.process.version = 'v16.0.0';
  window.process.platform = 'browser';
}

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);