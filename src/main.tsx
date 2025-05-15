import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Polyfill process and stdout for googleapis
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

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);