// Polyfill process and stdout for googleapis
if (!window.process) {
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
      unpipe: () => {},
      listeners: () => [],
      addListener: () => {},
      prependListener: () => {},
      eventNames: () => [],
      listenerCount: () => 0,
      emit: () => false
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
      unpipe: () => {},
      listeners: () => [],
      addListener: () => {},
      prependListener: () => {},
      eventNames: () => [],
      listenerCount: () => 0,
      emit: () => false
    },
    stdin: {
      isTTY: false,
      on: () => {},
      once: () => {},
      off: () => {},
      removeListener: () => {},
      pipe: () => {},
      unpipe: () => {},
      listeners: () => [],
      addListener: () => {},
      prependListener: () => {},
      eventNames: () => [],
      listenerCount: () => 0,
      emit: () => false
    },
    env: {},
    version: 'v16.0.0',
    platform: 'browser',
    nextTick: (callback: Function) => setTimeout(callback, 0),
    title: 'browser',
    browser: true,
    argv: [],
    pid: -1,
    arch: 'x64',
    execPath: '/usr/local/bin/node',
    debugPort: 9229,
    execArgv: [],
    ppid: -1,
    connected: false,
    allowedNodeEnvironmentFlags: new Set(),
    _events: {},
    _eventsCount: 0,
    _maxListeners: undefined,
    domain: null,
    emit: () => false,
    prependListener: () => process,
    prependOnceListener: () => process,
    listeners: () => [],
    addListener: () => process,
    on: () => process,
    once: () => process,
    off: () => process,
    removeListener: () => process,
    removeAllListeners: () => process,
    setMaxListeners: () => process,
    getMaxListeners: () => 0,
    listenerCount: () => 0,
    eventNames: () => []
  };
} else {
  // Ensure all required properties exist even if process exists
  window.process.stdout = window.process.stdout || {
    isTTY: false,
    write: () => {},
    end: () => {},
    on: () => {},
    once: () => {},
    off: () => {},
    removeListener: () => {},
    pipe: () => {},
    unpipe: () => {},
    listeners: () => [],
    addListener: () => {},
    prependListener: () => {},
    eventNames: () => [],
    listenerCount: () => 0,
    emit: () => false
  };
  window.process.stderr = window.process.stderr || {
    isTTY: false,
    write: () => {},
    end: () => {},
    on: () => {},
    once: () => {},
    off: () => {},
    removeListener: () => {},
    pipe: () => {},
    unpipe: () => {},
    listeners: () => [],
    addListener: () => {},
    prependListener: () => {},
    eventNames: () => [],
    listenerCount: () => 0,
    emit: () => false
  };
  window.process.stdin = window.process.stdin || {
    isTTY: false,
    on: () => {},
    once: () => {},
    off: () => {},
    removeListener: () => {},
    pipe: () => {},
    unpipe: () => {},
    listeners: () => [],
    addListener: () => {},
    prependListener: () => {},
    eventNames: () => [],
    listenerCount: () => 0,
    emit: () => false
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