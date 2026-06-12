import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  LayoutDashboard, 
  BarChart3, 
  Pill, 
  Receipt, 
  CalendarClock, 
  QrCode, 
  ShieldAlert, 
  LogOut, 
  Settings,
  Users,
  Activity
} from 'lucide-react';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  const getNavItems = () => {
    switch (user.role) {
      case 'admin':
        return [
          { to: '/admin/dashboard', label: 'Admin Dashboard', icon: LayoutDashboard },
          { to: '/admin/inventory', label: 'Inventory Management', icon: Pill },
          { to: '/admin/expiry', label: 'Expiry & Risks', icon: ShieldAlert },
          { to: '/admin/analytics', label: 'Analytics', icon: BarChart3 },
          { to: '/admin/monitoring', label: 'ML Monitoring', icon: Activity },
        ];
      case 'pharmacist':
        return [
          { to: '/pharmacist/dashboard', label: 'Pharmacy Dashboard', icon: LayoutDashboard },
          { to: '/pharmacist/billing', label: 'Smart Billing', icon: Receipt },
        ];
      case 'patient':
        return [
          { to: '/patient/dashboard', label: 'Cabinet Overview', icon: LayoutDashboard },
          { to: '/patient/reminders', label: 'Pill Reminders', icon: CalendarClock },
          { to: '/patient/scan', label: 'Scan Receipt', icon: QrCode },
        ];
      default:
        return [];
    }
  };

  const navItems = getNavItems();

  return (
    <div className="sidebar">
      <div className="logo-container">
        <div className="logo-icon">
          <svg viewBox="0 0 24 24" style={{ width: '22px', height: '22px', fill: '#070919' }}>
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z" />
          </svg>
        </div>
        <span className="logo-text">MEDIQR MLOPS</span>
      </div>

      <ul className="nav-links">
        {navItems.map((item) => (
          <li key={item.to} className="nav-item">
            <NavLink 
              to={item.to} 
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <item.icon />
              <span>{item.label}</span>
            </NavLink>
          </li>
        ))}
        
        <li className="nav-item" style={{ marginTop: '2rem' }}>
          <button onClick={handleLogout} className="btn-logout" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            padding: '0.85rem 1rem',
            color: '#ff5252',
            background: 'transparent',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer',
            width: '100%',
            textAlign: 'left',
            fontWeight: 500,
            fontSize: '0.95rem'
          }}>
            <LogOut size={20} />
            <span>Sign Out</span>
          </button>
        </li>
      </ul>

      <div className="sidebar-footer">
        <p>Logged in as</p>
        <h4 style={{ textTransform: 'capitalize', color: 'var(--text-bright)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
          {user.full_name || user.username}
        </h4>
        <div className="status">
          <span className="status-dot"></span>
          <span style={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary)' }}>
            {user.role} mode
          </span>
        </div>
      </div>
    </div>
  );
}
