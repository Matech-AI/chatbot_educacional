import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Polyfill process and stdout for googleapis
window.process = {
  stdout: {
    isTTY: false,
    write: () => {},
    end: () => {},
    on: () => {},
    once: () => {},
    off: () => {},
    removeListener: () => {},
    pipe: () => {},
    unpipe: () => {}
  },
  stderr: {
    isTTY: false,
    write: () => {},
    end: () => {},
    on: () => {},
    once: () => {},
    off: () => {},
    removeListener: () => {},
    pipe: () => {},
    unpipe: () => {}
  },
  stdin: {
    isTTY: false,
    on: () => {},
    once: () => {},
    off: () => {},
    removeListener: () => {},
    pipe: () => {},
    unpipe: () => {}
  },
  env: {},
  version: 'v16.0.0',
  platform: 'browser',
  nextTick: (callback: Function) => setTimeout(callback, 0)
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);