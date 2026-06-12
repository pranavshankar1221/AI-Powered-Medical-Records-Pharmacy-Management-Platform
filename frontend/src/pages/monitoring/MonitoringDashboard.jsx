import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { getSystemStatus } from '../../services/mlService';
import { Cpu, HardDrive, HelpCircle, RefreshCw, BarChart2, ShieldCheck, ShieldAlert } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export default function MonitoringDashboard() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchStatus();
    // Set interval to poll system status
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await getSystemStatus();
      if (res.success) {
        setStatus(res.data);
        // Record history for charts
        setHistory(prev => {
          const updated = [...prev, {
            time: new Date().toLocaleTimeString().slice(0, 8),
            cpu: res.data.cpu.usage_percent,
            memory: res.data.memory.usage_percent
          }];
          // Keep last 10 ticks
          return updated.slice(-10);
        });
      } else {
        setError('Failed to fetch monitoring metrics');
      }
    } catch (err) {
      console.error(err);
      setError('Could not connect to FastAPI /metrics server');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !status) {
    return (
      <div className="main-content">
        <Navbar title="MLOps & System Health" subtitle="Contacting monitoring server..." />
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
      <Navbar title="System Health & API Analytics" subtitle="Real-time Prometheus instrumentation telemetry and server hardware loads" />

      {error && (
        <div className="glass-card" style={{ borderLeft: '4px solid var(--status-critical)', marginBottom: '2rem' }}>
          <p style={{ color: 'var(--text-bright)' }}>{error}</p>
        </div>
      )}

      {/* KPI Cards */}
      <div className="metrics-grid" style={{ marginBottom: '2.5rem' }}>
        <div className="metric-card">
          <div className="metric-info">
            <h4>API Requests</h4>
            <div className="value">{status?.requests?.total || 0}</div>
          </div>
          <div className="metric-icon">
            <BarChart2 />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-info">
            <h4>API Errors</h4>
            <div className="value" style={{ color: (status?.requests?.errors || 0) > 0 ? 'var(--status-critical)' : 'var(--text-bright)' }}>
              {status?.requests?.errors || 0}
            </div>
          </div>
          <div className="metric-icon" style={{ color: (status?.requests?.errors || 0) > 0 ? 'var(--status-critical)' : 'inherit' }}>
            <ShieldAlert />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-info">
            <h4>Avg Latency</h4>
            <div className="value">{status?.requests?.avg_latency_ms || 0} ms</div>
          </div>
          <div className="metric-icon">
            <RefreshCw />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-info">
            <h4>Server Status</h4>
            <div className="value" style={{ color: 'var(--status-success)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '1.4rem' }}>
              <ShieldCheck size={24} /> HEALTHY
            </div>
          </div>
          <div className="metric-icon" style={{ color: 'var(--status-success)' }}>
            <ShieldCheck />
          </div>
        </div>
      </div>

      {/* Main Server telemetry specs */}
      <div className="dashboard-grid" style={{ marginBottom: '2.5rem' }}>
        {/* Hardware telemetry status */}
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu style={{ color: 'var(--primary)' }} /> Live Resource Telemetry
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>CPU load (Count: {status?.cpu?.count}):</span>
              <h3 style={{ color: 'var(--primary)', fontSize: '1.8rem', marginTop: '0.25rem' }}>{status?.cpu?.usage_percent}%</h3>
            </div>
            
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Memory (Total: {status?.memory?.total_gb} GB):</span>
              <h3 style={{ color: 'var(--secondary)', fontSize: '1.8rem', marginTop: '0.25rem' }}>{status?.memory?.usage_percent}%</h3>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Used: {status?.memory?.used_gb} GB | Free: {status?.memory?.available_gb} GB</p>
            </div>
          </div>

          {/* Area Chart for CPU and Memory */}
          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--secondary)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--secondary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time" stroke="var(--text-muted)" style={{ fontSize: '0.7rem' }} />
                <YAxis stroke="var(--text-muted)" style={{ fontSize: '0.7rem' }} />
                <Tooltip contentStyle={{ background: '#0d1127', border: '1px solid var(--border-glass)' }} />
                <Area type="monotone" dataKey="cpu" stroke="var(--primary)" fillOpacity={1} fill="url(#colorCpu)" name="CPU Usage %" />
                <Area type="monotone" dataKey="memory" stroke="var(--secondary)" fillOpacity={1} fill="url(#colorMemory)" name="RAM Usage %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Disk & telemetry summaries */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <HardDrive style={{ color: 'var(--primary)' }} /> Storage Allocation
            </h3>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Disk Usage:</span>
              <strong style={{ color: 'var(--text-bright)' }}>{status?.disk?.usage_percent}%</strong>
            </div>
            
            {/* Progress Bar */}
            <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden', marginBottom: '1.5rem' }}>
              <div style={{ width: `${status?.disk?.usage_percent}%`, height: '100%', background: 'var(--primary)', borderRadius: '4px' }}></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
              <span>Total Volume:</span>
              <span>{status?.disk?.total_gb} GB</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
              <span>Used Volume:</span>
              <span>{status?.disk?.used_gb} GB</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>Free Volume:</span>
              <span>{status?.disk?.free_gb} GB</span>
            </div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)', marginTop: '2rem' }}>
            <h4 style={{ color: 'var(--text-bright)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>Endpoint Scraper</h4>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              FastAPI is compiled with Prometheus client endpoints. To scrape raw values, access: <a href="http://localhost:8000/metrics" target="_blank" style={{ color: 'var(--primary)', textDecoration: 'none' }}>/metrics</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
