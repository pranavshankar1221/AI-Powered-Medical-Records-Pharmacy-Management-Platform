import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/ui/Sidebar';

// Auth Pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminAnalytics from './pages/admin/AdminAnalytics';

// Pharmacist Pages
import PharmacistDashboard from './pages/pharmacist/PharmacistDashboard';
import InventoryPage from './pages/pharmacist/InventoryPage';
import BillingPage from './pages/pharmacist/BillingPage';
import ExpiryManagementPage from './pages/admin/ExpiryManagementPage';

// Patient Pages
import PatientDashboard from './pages/patient/PatientDashboard';
import ReminderPage from './pages/patient/ReminderPage';
import QRScanPage from './pages/patient/QRScanPage';

// System Monitoring
import MonitoringDashboard from './pages/monitoring/MonitoringDashboard';

// Route Guard Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, token, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--text-bright)' }}>
        <div className="status-dot"></div> Loading Session...
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // If not allowed, redirect to role-specific root
    return <Navigate to="/" replace />;
  }

  return children;
};

// Root Dashboard Redirect Handler
const DashboardRedirect = () => {
  const { user, token, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--text-bright)' }}>
        <div className="status-dot"></div> Loading Session...
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  // Redirect to respective dashboard
  switch (user.role) {
    case 'admin':
      return <Navigate to="/admin/dashboard" replace />;
    case 'pharmacist':
      return <Navigate to="/pharmacist/dashboard" replace />;
    case 'patient':
      return <Navigate to="/patient/dashboard" replace />;
    default:
      return <Navigate to="/login" replace />;
  }
};

// Layout wrapper for all logged-in views
const LayoutWrapper = ({ children }) => {
  return (
    <div className="app-container">
      <Sidebar />
      <div style={{ flex: 1 }}>
        {children}
      </div>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Authentication */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Root Entry Redirection */}
          <Route path="/" element={<DashboardRedirect />} />

          {/* Protected System Admin Routes */}
          <Route 
            path="/admin/dashboard" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <LayoutWrapper><AdminDashboard /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/analytics" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <LayoutWrapper><AdminAnalytics /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/monitoring" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <LayoutWrapper><MonitoringDashboard /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/inventory" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <LayoutWrapper><InventoryPage /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/expiry" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <LayoutWrapper><ExpiryManagementPage /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />

          {/* Protected Pharmacist Routes */}
          <Route 
            path="/pharmacist/dashboard" 
            element={
              <ProtectedRoute allowedRoles={['pharmacist']}>
                <LayoutWrapper><PharmacistDashboard /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/pharmacist/billing" 
            element={
              <ProtectedRoute allowedRoles={['admin', 'pharmacist']}>
                <LayoutWrapper><BillingPage /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />

          {/* Protected Patient Companion Routes */}
          <Route 
            path="/patient/dashboard" 
            element={
              <ProtectedRoute allowedRoles={['patient']}>
                <LayoutWrapper><PatientDashboard /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/patient/reminders" 
            element={
              <ProtectedRoute allowedRoles={['patient']}>
                <LayoutWrapper><ReminderPage /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/patient/scan" 
            element={
              <ProtectedRoute allowedRoles={['patient']}>
                <LayoutWrapper><QRScanPage /></LayoutWrapper>
              </ProtectedRoute>
            } 
          />

          {/* Catch-all Redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
