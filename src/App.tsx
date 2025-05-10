import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/auth-store';
import { AppLayout } from './components/layout/app-layout';
import { LoginPage } from './pages/login-page';
import { HomePage } from './pages/home-page';
import { ChatPage } from './pages/chat-page';
import { MaterialsPage } from './pages/materials-page';
import { AssistantPage } from './pages/assistant-page';

// Protected route wrapper
const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles?: string[];
}> = ({ children, allowedRoles }) => {
  const { isAuthenticated, user } = useAuthStore();
  
  // Check if user is authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  // Check if user has required role
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        <Route path="/" element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }>
          <Route index element={<HomePage />} />
          
          <Route path="chat" element={<ChatPage />} />
          
          <Route path="materials" element={
            <ProtectedRoute allowedRoles={['admin', 'instructor']}>
              <MaterialsPage />
            </ProtectedRoute>
          } />
          
          <Route path="assistant" element={
            <ProtectedRoute allowedRoles={['admin', 'instructor']}>
              <AssistantPage />
            </ProtectedRoute>
          } />
          
          <Route path="settings" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <div className="p-6">
                <h1 className="text-2xl font-bold">Configurações</h1>
                <p className="text-gray-600 mt-2">Página em construção</p>
              </div>
            </ProtectedRoute>
          } />
          
          <Route path="debug" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <div className="p-6">
                <h1 className="text-2xl font-bold">Debug</h1>
                <p className="text-gray-600 mt-2">Página em construção</p>
              </div>
            </ProtectedRoute>
          } />
        </Route>
        
        {/* Redirect unknown routes to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;