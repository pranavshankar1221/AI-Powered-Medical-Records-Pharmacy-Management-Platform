import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { getBatchPredictions } from '../../services/mlService';
import { ShieldAlert, AlertCircle, TrendingDown, HelpCircle } from 'lucide-react';

export default function ExpiryManagementPage() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      const res = await getBatchPredictions();
      if (res.success) {
        setPredictions(res.data);
      } else {
        setError('Failed to load batch expiry predictions');
      }
    } catch (err) {
      console.error(err);
      setError('Could not connect to ML predictions endpoint. Please verify ML models are trained.');
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeClass = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'badge expired'; // red
      case 'medium':
        return 'badge warning'; // orange/yellow
      case 'low':
        return 'badge active'; // green
      default:
        return 'badge';
    }
  };

  if (loading) {
    return (
      <div className="main-content">
        <Navbar title="Expiry Risk Management" subtitle="Evaluating batches..." />
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '5rem' }}>
          <div className="scanner-animation">
            <div className="scanner-laser"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <Navbar title="Expiry & Risk Predictor" subtitle="AI RandomForest classifier evaluating velocity and remaining days" />

      {error && (
        <div className="glass-card" style={{ borderLeft: '4px solid var(--status-critical)', marginBottom: '2rem' }}>
          <p style={{ color: 'var(--text-bright)' }}>{error}</p>
          <button className="btn btn-secondary btn-sm" onClick={fetchPredictions} style={{ marginTop: '1rem' }}>
            Retry
          </button>
        </div>
      )}

      {/* Description Panel */}
      <div className="glass-card" style={{ marginBottom: '2rem', background: 'linear-gradient(135deg, rgba(112, 0, 255, 0.05) 0%, rgba(13, 17, 39, 0.7) 100%)' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-bright)', marginBottom: '0.5rem' }}>
          <ShieldAlert style={{ color: 'var(--secondary)' }} /> How Expiry Risk classification works
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '800px' }}>
          Our Machine Learning classification model evaluates remaining items in stock against the average sales velocity (units/day) and the days remaining until expiry. 
          Batches that are selling slowly and have near-term expiry dates are flagged as **High Risk** to help prevent stock losses and enable early discounts or supplier returns.
        </p>
      </div>

      {/* Predictions Table */}
      <div className="glass-card">
        <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem' }}>Batch Predictions List</h3>
        
        {predictions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            No active stock items detected to analyze.
          </div>
        ) : (
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Batch No.</th>
                  <th>Medicine</th>
                  <th>Remaining stock</th>
                  <th>Expiry Date</th>
                  <th>Days Left</th>
                  <th>Risk Score</th>
                  <th>Risk Level</th>
                  <th>AI Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((pred) => (
                  <tr key={pred.batch_id}>
                    <td><span style={{ fontFamily: 'monospace', color: 'var(--primary)' }}>{pred.batch_number}</span></td>
                    <td style={{ fontWeight: 600, color: 'var(--text-bright)' }}>{pred.medicine_name}</td>
                    <td>{pred.quantity_remaining} Units</td>
                    <td>{new Date(pred.expiry_date).toLocaleDateString()}</td>
                    <td>{pred.days_until_expiry} days</td>
                    <td style={{ fontWeight: 'bold' }}>
                      <span style={{ color: pred.risk_score > 0.7 ? 'var(--status-critical)' : pred.risk_score > 0.4 ? 'var(--status-warning)' : 'var(--status-success)' }}>
                        {(pred.risk_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td>
                      <span className={getRiskBadgeClass(pred.risk_level)}>
                        {pred.risk_level}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-main)', maxWidth: '280px' }}>
                      {pred.recommendation}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
