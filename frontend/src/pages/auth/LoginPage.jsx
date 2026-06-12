import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const ROLE_ROUTES = {
  admin: '/admin/dashboard',
  pharmacist: '/pharmacist/dashboard',
  patient: '/patient/dashboard',
};

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const doLogin = async (user, pass) => {
    setError('');
    setLoading(true);
    const result = await login(user, pass);
    if (result.success) {
      // Redirect immediately using the role from the login response
      const role = result.user?.role;
      const route = ROLE_ROUTES[role] || '/';
      navigate(route, { replace: true });
    } else {
      setError(result.error);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!username || !password) {
      setError('Please fill in all fields');
      return;
    }
    await doLogin(username, password);
  };

  const handleQuickLogin = (user, pass) => {
    setUsername(user);
    setPassword(pass);
    doLogin(user, pass);
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '2rem',
      background: 'var(--bg-primary)'
    }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '460px', padding: '2.5rem' }}>
        {/* Logo */}
        <div className="logo-container" style={{ justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="logo-icon">
            <svg viewBox="0 0 24 24">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z" />
            </svg>
          </div>
          <span className="logo-text" style={{ fontSize: '1.8rem' }}>MEDIQR MLOPS</span>
        </div>

        <h3 style={{ textAlign: 'center', marginBottom: '0.5rem', color: 'var(--text-bright)' }}>Welcome Back</h3>
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>
          AI-Powered Pharmacy Inventory &amp; Patient Guidance
        </p>

        {/* Error Message */}
        {error && (
          <div style={{
            background: 'rgba(255, 23, 68, 0.1)',
            border: '1px solid var(--status-critical)',
            color: '#ff5252',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '1.5rem',
            fontSize: '0.9rem'
          }}>
            ⚠ {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              id="username-input"
              type="text"
              className="form-control"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="form-group" style={{ marginBottom: '2rem' }}>
            <label>Password</label>
            <input
              id="password-input"
              type="password"
              className="form-control"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button
            id="login-btn"
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.9rem', fontSize: '1rem' }}
            disabled={loading}
          >
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <span className="status-dot" style={{ animation: 'pulse 1s infinite' }}></span>
                Signing in...
              </span>
            ) : 'Sign In →'}
          </button>
        </form>

        {/* Quick Login Demo Accounts */}
        <div style={{ marginTop: '2rem', borderTop: '1px solid var(--border-glass)', paddingTop: '1.5rem' }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            🔑 Quick Demo Login
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.6rem' }}>
            <button
              id="quick-admin-btn"
              onClick={() => handleQuickLogin('admin', 'admin123')}
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'center', fontSize: '0.8rem' }}
              disabled={loading}
            >
              🛡 Admin
            </button>
            <button
              id="quick-pharmacist-btn"
              onClick={() => handleQuickLogin('pharmacist1', 'pharma123')}
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'center', fontSize: '0.8rem' }}
              disabled={loading}
            >
              💊 Pharmacist
            </button>
            <button
              id="quick-patient-btn"
              onClick={() => handleQuickLogin('patient1', 'patient123')}
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'center', fontSize: '0.8rem' }}
              disabled={loading}
            >
              🏥 Patient
            </button>
          </div>
        </div>

        <p style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 600 }}>
            Register Here
          </Link>
        </p>
      </div>
    </div>
  );
}
