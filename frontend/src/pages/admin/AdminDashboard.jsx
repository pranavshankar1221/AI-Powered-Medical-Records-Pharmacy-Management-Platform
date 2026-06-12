import React, { useState, useEffect } from 'react';
import { getAdminDashboardStats } from '../../services/adminService';
import { getAlerts } from '../../services/inventoryService';
import Navbar from '../../components/ui/Navbar';
import { 
  TrendingUp, 
  DollarSign, 
  Pill, 
  Receipt, 
  Users, 
  AlertTriangle, 
  Activity,
  Layers,
  FileCheck
} from 'lucide-react';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [alerts, setAlerts] = useState({ expiring_30: [], expired: [] });
  const [showPopup, setShowPopup] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const [statsRes, alertsRes] = await Promise.all([
        getAdminDashboardStats(),
        getAlerts()
      ]);

      if (statsRes.success) {
        setStats(statsRes.data);
      } else {
        setError('Failed to fetch dashboard stats');
        return;
      }

      let hasAlerts = false;
      let expiringItems = [];
      let expiredItems = [];

      if (alertsRes.success && alertsRes.data) {
        expiringItems = alertsRes.data.expiring_30_days || [];
        expiredItems = alertsRes.data.expired || [];
        setAlerts({
          expiring_30: expiringItems,
          expired: expiredItems
        });
        hasAlerts = expiringItems.length > 0 || expiredItems.length > 0;
      }

      // Check if already shown in this session
      const alreadyDismissed = sessionStorage.getItem('expiry_alert_dismissed');
      if (hasAlerts && !alreadyDismissed) {
        setShowPopup(true);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to connect to the backend server');
    } finally {
      setLoading(false);
    }
  };

  const dismissPopup = () => {
    sessionStorage.setItem('expiry_alert_dismissed', 'true');
    setShowPopup(false);
  };

  if (loading) {
    return (
      <div className="main-content">
        <Navbar title="Admin Dashboard" subtitle="Loading metrics..." />
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '5rem' }}>
          <div className="scanner-animation">
            <div className="scanner-laser"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="main-content">
        <Navbar title="Admin Dashboard" subtitle="Error loading data" />
        <div className="glass-card" style={{ borderLeft: '4px solid var(--status-critical)', marginTop: '2rem' }}>
          <p style={{ color: 'var(--text-bright)' }}>{error}</p>
          <button className="btn btn-secondary btn-sm" onClick={fetchStats} style={{ marginTop: '1rem' }}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <Navbar title="Dashboard Overview" subtitle="System metrics, inventory status, and sales velocity" />

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-info">
            <h4>Total Revenue</h4>
            <div className="value">₹{stats.total_revenue}</div>
          </div>
          <div className="metric-icon">
            <DollarSign />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-info">
            <h4>This Month</h4>
            <div className="value">₹{stats.monthly_revenue}</div>
          </div>
          <div className="metric-icon">
            <TrendingUp />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-info">
            <h4>Medicines</h4>
            <div className="value">{stats.total_medicines}</div>
          </div>
          <div className="metric-icon">
            <Pill />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-info">
            <h4>Total Invoices</h4>
            <div className="value">{stats.total_bills}</div>
          </div>
          <div className="metric-icon">
            <Receipt />
          </div>
        </div>
      </div>

      {/* Critical Stock Alerts */}
      {(stats.low_stock_count > 0 || stats.expiring_soon_count > 0 || stats.expired_count > 0) && (
        <div className="glass-card" style={{ marginBottom: '2.5rem', borderLeft: '4px solid var(--status-warning)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-bright)', marginBottom: '1rem' }}>
            <AlertTriangle style={{ color: 'var(--status-warning)' }} /> Attention Required (Inventory Alerts)
          </h3>
          <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
            {stats.low_stock_count > 0 && (
              <div style={{ background: 'rgba(255, 179, 0, 0.05)', padding: '0.75rem 1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,179,0,0.2)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Low Stock Items:</span>
                <h4 style={{ color: 'var(--status-warning)', fontSize: '1.5rem', marginTop: '0.25rem' }}>{stats.low_stock_count}</h4>
              </div>
            )}
            {stats.expiring_soon_count > 0 && (
              <div style={{ background: 'rgba(255, 179, 0, 0.05)', padding: '0.75rem 1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,179,0,0.2)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Expiring in 30 Days:</span>
                <h4 style={{ color: 'var(--status-warning)', fontSize: '1.5rem', marginTop: '0.25rem' }}>{stats.expiring_soon_count}</h4>
              </div>
            )}
            {stats.expired_count > 0 && (
              <div style={{ background: 'rgba(255, 23, 68, 0.05)', padding: '0.75rem 1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,23,68,0.2)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Expired Batches:</span>
                <h4 style={{ color: 'var(--status-critical)', fontSize: '1.5rem', marginTop: '0.25rem' }}>{stats.expired_count}</h4>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Grid: Fast Moving & Slow Moving */}
      <div className="dashboard-grid">
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity style={{ color: 'var(--primary)' }} /> Fast-Moving Medicines (Top Selling)
          </h3>
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Med ID</th>
                  <th>Medicine Name</th>
                  <th style={{ textAlign: 'right' }}>Total Units Sold</th>
                </tr>
              </thead>
              <tbody>
                {stats.fast_moving.length === 0 ? (
                  <tr>
                    <td colSpan="3" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No sales history recorded yet.</td>
                  </tr>
                ) : (
                  stats.fast_moving.map((med) => (
                    <tr key={med.medicine_id}>
                      <td><span style={{ fontFamily: 'monospace', color: 'var(--primary)' }}>{med.medicine_id}</span></td>
                      <td style={{ fontWeight: 600, color: 'var(--text-bright)' }}>{med.name}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--status-success)' }}>{med.total_sold} units</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers style={{ color: 'var(--secondary)' }} /> Slow-Moving Medicines (Risk Items)
          </h3>
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th style={{ textAlign: 'right' }}>Sold</th>
                </tr>
              </thead>
              <tbody>
                {stats.slow_moving.length === 0 ? (
                  <tr>
                    <td colSpan="2" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No records.</td>
                  </tr>
                ) : (
                  stats.slow_moving.map((med) => (
                    <tr key={med.medicine_id}>
                      <td style={{ color: 'var(--text-bright)', fontWeight: 500 }}>{med.name}</td>
                      <td style={{ textAlign: 'right', color: 'var(--status-warning)' }}>{med.total_sold} units</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Expiry Warning Popup */}
      {showPopup && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(7, 9, 25, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1rem'
        }}>
          <div className="glass-card" style={{
            width: '100%',
            maxWidth: '600px',
            padding: '2.5rem',
            position: 'relative',
            border: '1px solid rgba(255, 79, 117, 0.3)',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
            background: 'linear-gradient(135deg, rgba(20, 10, 35, 0.9) 0%, rgba(10, 12, 28, 0.95) 100%)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{
                background: 'rgba(255, 79, 117, 0.15)',
                padding: '0.75rem',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid rgba(255, 79, 117, 0.3)'
              }}>
                <AlertTriangle color="#ff4f75" size={28} />
              </div>
              <div>
                <h3 style={{ color: 'var(--text-bright)', fontSize: '1.4rem', margin: 0 }}>Critical Expiry Alerts</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0.2rem 0 0 0' }}>
                  Action required: Batch items are expiring or already expired
                </p>
              </div>
            </div>

            <div style={{
              maxHeight: '300px',
              overflowY: 'auto',
              marginBottom: '2rem',
              paddingRight: '0.5rem',
            }} className="custom-scrollbar">
              {/* Render Expired List */}
              {alerts.expired.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h5 style={{ color: '#ff4f75', fontSize: '0.9rem', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ❌ Expired Medicines ({alerts.expired.length})
                  </h5>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {alerts.expired.map((item) => (
                      <div key={item.id} style={{
                        background: 'rgba(255, 79, 117, 0.05)',
                        border: '1px solid rgba(255, 79, 117, 0.15)',
                        padding: '0.75rem 1rem',
                        borderRadius: 'var(--radius-sm)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-bright)' }}>{item.medicine_name}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Batch: {item.batch_number} • Qty: {item.quantity_remaining}</div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '0.8rem', color: '#ff4f75', fontWeight: 600 }}>Expired</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{new Date(item.expiry_date).toLocaleDateString()}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Render Near Expiry List */}
              {alerts.expiring_30.length > 0 && (
                <div>
                  <h5 style={{ color: 'var(--status-warning)', fontSize: '0.9rem', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ⚠️ Expiring Soon ({alerts.expiring_30.length})
                  </h5>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {alerts.expiring_30.map((item) => {
                      const daysLeft = Math.max(0, Math.ceil((new Date(item.expiry_date) - new Date()) / (1000 * 60 * 60 * 24)));
                      return (
                        <div key={item.id} style={{
                          background: 'rgba(255, 179, 0, 0.05)',
                          border: '1px solid rgba(255, 179, 0, 0.15)',
                          padding: '0.75rem 1rem',
                          borderRadius: 'var(--radius-sm)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
                          <div>
                            <div style={{ fontWeight: 600, color: 'var(--text-bright)' }}>{item.medicine_name}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Batch: {item.batch_number} • Qty: {item.quantity_remaining}</div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--status-warning)', fontWeight: 600 }}>Expires in {daysLeft} days</div>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{new Date(item.expiry_date).toLocaleDateString()}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                onClick={dismissPopup} 
                className="btn btn-primary"
                style={{ 
                  background: 'linear-gradient(135deg, #ff4f75 0%, #d81b60 100%)',
                  border: 'none',
                  padding: '0.8rem 2rem',
                  fontWeight: 600
                }}
              >
                Acknowledge &amp; Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
