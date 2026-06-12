import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { getPatientDashboard } from '../../services/patientService';
import { Link } from 'react-router-dom';
import { Pill, CalendarClock, Receipt, ArrowRight, BrainCircuit, ShieldAlert } from 'lucide-react';

export default function PatientDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const res = await getPatientDashboard();
      if (res.success) {
        setData(res.data);
      } else {
        setError('Failed to fetch patient records');
      }
    } catch (err) {
      console.error(err);
      setError('Could not connect to the backend server');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="main-content">
        <Navbar title="My Medicine Cabinet" subtitle="Loading..." />
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
        <Navbar title="My Medicine Cabinet" subtitle="Error loading data" />
        <div className="glass-card" style={{ borderLeft: '4px solid var(--status-critical)', marginTop: '2rem' }}>
          <p style={{ color: 'var(--text-bright)' }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <Navbar title="Patient Companion" subtitle="Track your medicine schedule, scan QR receipts, and get AI guidance" />

      {/* KPI Stats */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-info">
            <h4>Active Medicines</h4>
            <div className="value">{data.active_medicines_count}</div>
          </div>
          <div className="metric-icon">
            <Pill />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-info">
            <h4>Reminders (Today)</h4>
            <div className="value">{data.reminders_today.total}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              {data.reminders_today.taken} taken | {data.reminders_today.pending} pending
            </div>
          </div>
          <div className="metric-icon">
            <CalendarClock />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-info">
            <h4>Saved Receipts</h4>
            <div className="value">{data.recent_bills.length}</div>
          </div>
          <div className="metric-icon">
            <Receipt />
          </div>
        </div>
      </div>

      {/* Main Grid: Medicine Cabinet and Reminders */}
      <div className="dashboard-grid">
        {/* Cabinet Medicines */}
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BrainCircuit style={{ color: 'var(--primary)' }} /> My Prescribed Medicines
          </h3>
          
          {data.active_medicines.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              <p>No medicines linked to your account yet.</p>
              <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
                Scan a MEDIQR receipt QR code using your phone camera to instantly load prescriptions.
              </p>
              <Link to="/patient/scan" className="btn btn-secondary btn-sm" style={{ marginTop: '1rem' }}>
                Scan Receipt QR Code
              </Link>
            </div>
          ) : (
            <div className="cabinet-grid">
              {data.active_medicines.map((medName, idx) => (
                <div key={idx} className="cabinet-card">
                  <div className="cabinet-card-header">
                    <span className="cabinet-card-name">{medName}</span>
                    <Pill size={16} style={{ color: 'var(--primary)' }} />
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Prescribed from recent purchase
                  </div>
                  <div style={{ marginTop: 'auto', paddingTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                    {/* We link explanation page. We can search by medicine id, but to make it simple let's pass state or link to explanation */}
                    <Link 
                      to={`/patient/scan`} // redirects to scan/cabinet details
                      style={{ 
                        display: 'inline-flex', 
                        alignItems: 'center', 
                        gap: '0.25rem', 
                        color: 'var(--primary)', 
                        textDecoration: 'none', 
                        fontSize: '0.8rem',
                        fontWeight: 600
                      }}
                    >
                      AI Explainer <ArrowRight size={12} />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick links & Recent bills */}
        <div>
          {/* Quick Schedule links */}
          <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1rem' }}>Pill Reminders</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
              Stay on track with customizable pill schedule alerts for morning, afternoon, and night dosages.
            </p>
            <Link to="/patient/reminders" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
              Open Pill Reminders
            </Link>
          </div>

          {/* Recent Bills scan list */}
          <div className="glass-card">
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1rem' }}>Recent Scan Invoices</h3>
            {data.recent_bills.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No invoice history found.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {data.recent_bills.map((bill, idx) => (
                  <div key={idx} style={{
                    padding: '0.75rem',
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: 'var(--radius-sm)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-bright)' }}>{bill.invoice_number}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{new Date(bill.created_at).toLocaleDateString()}</div>
                    </div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                      ₹{bill.final_amount}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
