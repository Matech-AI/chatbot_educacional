// Polyfill process and stdout for googleapis
if (!window.process) {
  window.process = {
    stdout: {
      isTTY: false,
      write: () => {},
      end: () => {}
    },
    stderr: {
      isTTY: false,
      write: () => {},
      end: () => {}
    },
    stdin: {
      isTTY: false
    },
    env: {},
    version: 'v16.0.0',
    platform: 'browser'
  };
} else {
  // Ensure all required properties exist even if process exists
  window.process.stdout = window.process.stdout || {
    isTTY: false,
    write: () => {},
    end: () => {}
  };
  window.process.stderr = window.process.stderr || {
    isTTY: false,
    write: () => {},
    end: () => {}
  };
  window.process.stdin = window.process.stdin || {
    isTTY: false
  };
  window.process.env = window.process.env || {};
  window.process.version = window.process.version || 'v16.0.0';
  window.process.platform = window.process.platform || 'browser';
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