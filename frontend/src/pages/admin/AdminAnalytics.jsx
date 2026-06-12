import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { 
  getSalesTrend, 
  getCategoryAnalysis, 
  getTopMedicines, 
  getInventoryDistribution 
} from '../../services/adminService';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { TrendingUp, BarChart3, PieChart as PieIcon, Award } from 'lucide-react';

export default function AdminAnalytics() {
  const [salesData, setSalesData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [stockData, setStockData] = useState([]);
  const [topMeds, setTopMeds] = useState({ top_selling: [], least_selling: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const COLORS = ['#00f0c2', '#7000ff', '#2979ff', '#00e676', '#ffb300', '#ff1744'];

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const [salesRes, catRes, stockRes, topRes] = await Promise.all([
        getSalesTrend(12),
        getCategoryAnalysis(),
        getInventoryDistribution(),
        getTopMedicines(5)
      ]);

      if (salesRes.success) setSalesData(salesRes.data);
      if (catRes.success) setCategoryData(catRes.data);
      if (stockRes.success) setStockData(stockRes.data);
      if (topRes.success) setTopMeds(topRes.data);

    } catch (err) {
      console.error(err);
      setError('Failed to fetch analytics datasets');
    } finally {
      setLoading(false);
    }
  };

  const formatMonthName = (mNum) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[mNum - 1] || mNum;
  };

  // Process Sales Trend Data for Recharts
  const chartSalesData = salesData.map(d => ({
    name: `${formatMonthName(d.month)} ${d.year}`,
    Revenue: d.revenue,
    Transactions: d.transactions
  }));

  if (loading) {
    return (
      <div className="main-content">
        <Navbar title="Admin Analytics" subtitle="Loading metrics..." />
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
      <Navbar title="Advanced Analytics" subtitle="Deeper insights on revenue trends, categories, and inventory metrics" />

      {error && (
        <div className="glass-card" style={{ borderLeft: '4px solid var(--status-critical)', marginBottom: '2rem' }}>
          <p style={{ color: 'var(--text-bright)' }}>{error}</p>
        </div>
      )}

      {/* Grid: 2 columns for trends */}
      <div className="dashboard-grid" style={{ marginBottom: '2rem' }}>
        {/* Sales & Revenue Trend */}
        <div className="glass-card" style={{ minHeight: '380px' }}>
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingUp size={20} style={{ color: 'var(--primary)' }} /> Sales & Revenue Trend
          </h3>
          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartSalesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                <YAxis stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                <Tooltip 
                  contentStyle={{ background: '#0d1127', border: '1px solid var(--border-glass)', borderRadius: '8px' }}
                  labelStyle={{ color: 'var(--text-bright)', fontWeight: 600 }}
                />
                <Legend />
                <Line type="monotone" dataKey="Revenue" stroke="var(--primary)" strokeWidth={3} activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Transaction Volume Trend */}
        <div className="glass-card" style={{ minHeight: '380px' }}>
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart3 size={20} style={{ color: 'var(--secondary)' }} /> Transaction Counts
          </h3>
          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartSalesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                <YAxis stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                <Tooltip 
                  contentStyle={{ background: '#0d1127', border: '1px solid var(--border-glass)', borderRadius: '8px' }}
                  labelStyle={{ color: 'var(--text-bright)', fontWeight: 600 }}
                />
                <Legend />
                <Bar dataKey="Transactions" fill="var(--secondary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Grid: Category and Stock distribution */}
      <div className="dashboard-grid" style={{ marginBottom: '2rem' }}>
        {/* Category Pie Chart */}
        <div className="glass-card" style={{ minHeight: '350px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <PieIcon size={20} style={{ color: 'var(--primary)' }} /> Medicine Categories
          </h3>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="count"
                  nameKey="category"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: '#0d1127', border: '1px solid var(--border-glass)', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Stock Volume by Category */}
        <div className="glass-card" style={{ minHeight: '350px' }}>
          <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart3 size={20} style={{ color: 'var(--status-success)' }} fill="none" /> Inventory Stock Distribution
          </h3>
          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stockData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                <YAxis dataKey="category" type="category" stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                <Tooltip 
                  contentStyle={{ background: '#0d1127', border: '1px solid var(--border-glass)', borderRadius: '8px' }}
                />
                <Bar dataKey="total_stock" fill="#00e676" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top and Least Selling Details */}
      <div className="glass-card">
        <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Award size={20} style={{ color: 'var(--primary)' }} /> Performance Leaders (Top 5 vs Least 5)
        </h3>
        <div className="dashboard-grid">
          <div>
            <h4 style={{ color: 'var(--status-success)', marginBottom: '1rem' }}>Top Sellers</h4>
            <div className="table-container">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Medicine</th>
                    <th>Category</th>
                    <th style={{ textAlign: 'right' }}>Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {topMeds.top_selling.map((med) => (
                    <tr key={med.medicine_id}>
                      <td style={{ color: 'var(--text-bright)', fontWeight: 600 }}>{med.name}</td>
                      <td>{med.category}</td>
                      <td style={{ textAlign: 'right', color: 'var(--status-success)', fontWeight: 600 }}>₹{med.revenue}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div>
            <h4 style={{ color: 'var(--status-critical)', marginBottom: '1rem' }}>Least Sellers / Expiry Risk</h4>
            <div className="table-container">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Medicine</th>
                    <th>Category</th>
                    <th style={{ textAlign: 'right' }}>Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {topMeds.least_selling.map((med) => (
                    <tr key={med.medicine_id}>
                      <td style={{ color: 'var(--text-bright)', fontWeight: 600 }}>{med.name}</td>
                      <td>{med.category}</td>
                      <td style={{ textAlign: 'right', color: 'var(--status-warning)', fontWeight: 600 }}>₹{med.revenue}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
