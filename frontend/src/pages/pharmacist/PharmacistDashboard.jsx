import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { getAlerts, getMedicines } from '../../services/inventoryService';
import { Link } from 'react-router-dom';
import { 
  Receipt, 
  Pill, 
  AlertTriangle, 
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function PharmacistDashboard() {
  const [alerts, setAlerts] = useState({ low_stock: [], expiring_30: [], expired: [] });
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [alertsRes, medsRes] = await Promise.all([
        getAlerts(),
        getMedicines({ page: 1, per_page: 5 })
      ]);

      if (alertsRes.success) {
        setAlerts({
          low_stock: alertsRes.data.low_stock || [],
          expiring_30: alertsRes.data.expiring_30_days || [],
          expired: alertsRes.data.expired || []
        });
      }
      if (medsRes.items) {
        setMedicines(medsRes.items);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch dashboard summaries');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="main-content">
        <Navbar title="Pharmacist Dashboard" subtitle="Loading metrics..." />
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '5rem' }}>
          <div className="scanner-animation">
            <div className="scanner-laser"></div>
          </div>
        </div>
      </div>
    );
  }

  const criticalAlertCount = alerts.low_stock.length + alerts.expiring_30.length + alerts.expired.length;

  return (
    <div className="main-content">
      <Navbar title="Pharmacy Operations" subtitle="Smart billing interface, stock management, and alert logs" />

      {/* Quick Action Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div className="glass-card" style={{ 
          background: 'linear-gradient(135deg, rgba(0, 240, 194, 0.05) 0%, rgba(13, 17, 39, 0.7) 100%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ color: 'var(--text-bright)', marginBottom: '0.5rem' }}>Create Bill & Invoice</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem', maxWidth: '600px' }}>
              Add items to checkout, specify custom dosage guidance, and print QR-activated invoices.
            </p>
            <Link to="/pharmacist/billing" className="btn btn-primary">
              Launch Billing Portal <ArrowRight size={16} />
            </Link>
          </div>
          <Receipt size={60} style={{ color: 'var(--primary)', opacity: 0.8 }} />
        </div>
      </div>

      {/* Columns: Alerts & Medicine Summary */}
      <div className="dashboard-grid">
        {/* Active Alert Log */}
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle style={{ color: criticalAlertCount > 0 ? 'var(--status-critical)' : 'var(--status-success)' }} />
            Active Warning Logs ({criticalAlertCount})
          </h3>
          {criticalAlertCount === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              All batch items are healthy and fully stocked!
            </div>
          ) : (
            <div className="alert-list">
              {alerts.expired.map((alt, idx) => (
                <div key={`exp-${idx}`} className="alert-item critical">
                  <div className="alert-body">
                    <h5>Expired: {alt.medicine_name}</h5>
                    <p>Batch {alt.batch_number} expired on {new Date(alt.expiry_date).toLocaleDateString()}</p>
                  </div>
                  <span className="badge expired">Critical</span>
                </div>
              ))}
              
              {alerts.expiring_30.map((alt, idx) => (
                <div key={`exp30-${idx}`} className="alert-item warning">
                  <div className="alert-body">
                    <h5>Expiring Soon: {alt.medicine_name}</h5>
                    <p>Batch {alt.batch_number} expires in {alt.days_remaining} days ({new Date(alt.expiry_date).toLocaleDateString()})</p>
                  </div>
                  <span className="badge warning">Near Expiry</span>
                </div>
              ))}

              {alerts.low_stock.map((alt, idx) => (
                <div key={`low-${idx}`} className="alert-item warning">
                  <div className="alert-body">
                    <h5>Low Stock: {alt.medicine_name}</h5>
                    <p>Batch {alt.batch_number} has only {alt.quantity_remaining} items left</p>
                  </div>
                  <span className="badge warning">Low Stock</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Catalog Highlights */}
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Pill style={{ color: 'var(--primary)' }} /> Medicine Catalog
          </h3>
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Total Stock</th>
                </tr>
              </thead>
              <tbody>
                {medicines.map((med) => (
                  <tr key={med.medicine_id}>
                    <td style={{ color: 'var(--text-bright)' }}>
                      <div style={{ fontWeight: 600 }}>{med.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{med.generic_name}</div>
                    </td>
                    <td>
                      <span className={`badge ${med.total_stock > 10 ? 'active' : med.total_stock > 0 ? 'warning' : 'expired'}`}>
                        {med.total_stock} Units
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
