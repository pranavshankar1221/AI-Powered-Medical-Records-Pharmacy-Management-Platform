import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { 
  getMedicines, 
  createMedicine, 
  getMedicine, 
  createBatch,
  getCategories 
} from '../../services/inventoryService';
import { predictDemand } from '../../services/mlService';
import { useAuth } from '../../context/AuthContext';
import { Plus, Search, Filter, Sparkles, AlertCircle, Info, Calendar } from 'lucide-react';

export default function InventoryPage() {
  const [medicines, setMedicines] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Modals state
  const [showMedModal, setShowMedModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [selectedMedId, setSelectedMedId] = useState('');
  const [medDetails, setMedDetails] = useState(null);

  // ML Demand prediction state
  const [predictionResult, setPredictionResult] = useState(null);
  const [predicting, setPredicting] = useState(false);

  // Forms state
  const [newMed, setNewMed] = useState({
    name: '', generic_name: '', category: '', manufacturer: '',
    dosage_form: '', strength: '', unit_price: 0.0, description: '',
    purpose: '', dosage_schedule: '', 
    initial_stock: 0, expiry_date: '', batch_number: ''
  });
  const [newBatch, setNewBatch] = useState({
    medicine_id: '', batch_number: '', manufacture_date: '',
    expiry_date: '', quantity_received: 100, supplier: ''
  });

  const { user } = useAuth();

  useEffect(() => {
    fetchMedicines();
    fetchCategories();
  }, [search, selectedCategory, page]);

  const fetchMedicines = async () => {
    try {
      setLoading(true);
      const res = await getMedicines({
        page,
        per_page: 10,
        search: search || undefined,
        category: selectedCategory || undefined
      });
      setMedicines(res.data || []);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch medicine listings');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await getCategories();
      if (res.success) {
        setCategories(res.data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleMedClick = async (medId) => {
    if (selectedMedId === medId) {
      // Toggle
      setSelectedMedId('');
      setMedDetails(null);
      setPredictionResult(null);
      return;
    }

    try {
      setSelectedMedId(medId);
      setPredictionResult(null);
      const res = await getMedicine(medId);
      if (res.success) {
        setMedDetails(res.data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Trigger Machine Learning prediction for demand
  const handlePredictDemand = async (med) => {
    try {
      setPredicting(true);
      setPredictionResult(null);
      const currentMonth = new Date().getMonth() + 1;
      
      const payload = {
        medicine_id: med.medicine_id,
        current_stock: med.total_stock,
        month: currentMonth,
        avg_monthly_sales: Math.max(10, Math.round(med.total_stock * 0.4)), // dynamic estimate or historical average
        category: med.category || 'General'
      };

      const res = await predictDemand(payload);
      setPredictionResult(res);
    } catch (err) {
      console.error(err);
      alert('ML model service is currently training or offline. Please train models first.');
    } finally {
      setPredicting(false);
    }
  };

  const handleAddMedicine = async (e) => {
    e.preventDefault();
    try {
      const { initial_stock, expiry_date, batch_number, ...medicineData } = newMed;
      const res = await createMedicine(medicineData);
      if (res.success) {
        if (initial_stock > 0 && expiry_date && batch_number) {
          await createBatch({
            medicine_id: res.data.medicine_id,
            batch_number,
            expiry_date,
            quantity_received: initial_stock,
            supplier: newMed.manufacturer || 'Direct'
          });
        }
        setShowMedModal(false);
        fetchMedicines();
        setNewMed({
          name: '', generic_name: '', category: '', manufacturer: '',
          dosage_form: '', strength: '', unit_price: 0.0, description: '',
          purpose: '', dosage_schedule: '',
          initial_stock: 0, expiry_date: '', batch_number: ''
        });
      }
    } catch (err) {
      console.error(err);
      const errorMsg = Array.isArray(err.response?.data?.detail) 
        ? err.response.data.detail.map(d => d.msg).join(', ') 
        : err.response?.data?.detail;
      alert(errorMsg || 'Failed to add medicine');
    }
  };

  const handleAddBatch = async (e) => {
    e.preventDefault();
    try {
      const res = await createBatch(newBatch);
      if (res.success) {
        setShowBatchModal(false);
        if (selectedMedId === newBatch.medicine_id) {
          // Refresh details
          const detailRes = await getMedicine(selectedMedId);
          if (detailRes.success) setMedDetails(detailRes.data);
        }
        fetchMedicines();
        setNewBatch({
          medicine_id: '', batch_number: '', manufacture_date: '',
          expiry_date: '', quantity_received: 100, supplier: ''
        });
      }
    } catch (err) {
      console.error(err);
      const errorMsg = Array.isArray(err.response?.data?.detail) 
        ? err.response.data.detail.map(d => d.msg).join(', ') 
        : err.response?.data?.detail;
      alert(errorMsg || 'Failed to add batch');
    }
  };

  const openBatchModal = (medId) => {
    setNewBatch({ ...newBatch, medicine_id: medId });
    setShowBatchModal(true);
  };

  return (
    <div className="main-content">
      <Navbar title="Inventory Catalog" subtitle="Query medicine stocks, create batches, and trigger demand predictions" />

      {/* Filter and Action Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem',
        marginBottom: '2rem',
        flexWrap: 'wrap'
      }}>
        <div style={{ display: 'flex', gap: '1rem', flex: 1, minWidth: '300px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="form-control"
              placeholder="Search by name, generic description, or ID..."
              style={{ paddingLeft: '2.5rem' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          
          <div style={{ position: 'relative', width: '200px' }}>
            <Filter size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
            <select
              className="form-control"
              style={{ paddingLeft: '2.5rem', appearance: 'none', background: 'rgba(13, 17, 39, 0.9)' }}
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>

        <button className="btn btn-primary" onClick={() => setShowMedModal(true)}>
          <Plus size={18} /> Add New Medicine
        </button>
      </div>

      {/* Medicines Table */}
      <div className="glass-card">
        {loading && medicines.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>Loading Inventory...</div>
        ) : (
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Med ID</th>
                  <th>Name</th>
                  <th>Generic Descriptor</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th>Stock Levels</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {medicines.map((med) => (
                  <React.Fragment key={med.medicine_id}>
                    <tr 
                      onClick={() => handleMedClick(med.medicine_id)}
                      style={{ cursor: 'pointer', transition: 'var(--transition)' }}
                      className={selectedMedId === med.medicine_id ? 'active' : ''}
                    >
                      <td><span style={{ fontFamily: 'monospace', color: 'var(--primary)' }}>{med.medicine_id}</span></td>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--text-bright)' }}>{med.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{med.dosage_form} | {med.strength}</div>
                      </td>
                      <td>{med.generic_name}</td>
                      <td><span className="badge" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-main)' }}>{med.category}</span></td>
                      <td>₹{med.unit_price}</td>
                      <td>
                        <span className={`badge ${med.total_stock > 15 ? 'active' : med.total_stock > 0 ? 'warning' : 'expired'}`}>
                          {med.total_stock} Available
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                        <button className="btn btn-secondary btn-sm" onClick={() => openBatchModal(med.medicine_id)}>
                          Add Batch
                        </button>
                      </td>
                    </tr>

                    {/* Sub-table Batch Expansion */}
                    {selectedMedId === med.medicine_id && (
                      <tr>
                        <td colSpan="7" style={{ background: 'rgba(255,255,255,0.01)', padding: '1.5rem 2rem' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem' }}>
                            <div>
                              <h4 style={{ color: 'var(--text-bright)', marginBottom: '1rem' }}>Active Batches for {med.name}</h4>
                              {medDetails && medDetails.batches && medDetails.batches.length > 0 ? (
                                <table className="custom-table" style={{ width: '100%' }}>
                                  <thead>
                                    <tr>
                                      <th>Batch Number</th>
                                      <th>Expiry Date</th>
                                      <th>Supplier</th>
                                      <th style={{ textAlign: 'right' }}>Stock Left</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {medDetails.batches.map(batch => (
                                      <tr key={batch.batch_number}>
                                        <td><span style={{ fontFamily: 'monospace' }}>{batch.batch_number}</span></td>
                                        <td>
                                          <span style={{ color: new Date(batch.expiry_date) < new Date() ? 'var(--status-critical)' : 'var(--text-main)' }}>
                                            {new Date(batch.expiry_date).toLocaleDateString()}
                                          </span>
                                        </td>
                                        <td>{batch.supplier}</td>
                                        <td style={{ textAlign: 'right', fontWeight: 600 }}>{batch.quantity_remaining} / {batch.quantity_received}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              ) : (
                                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No batch tracking exists for this item yet. Please add a batch.</div>
                              )}
                            </div>

                            {/* ML Demand Predictor widget */}
                            <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-glass)' }}>
                              <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <Sparkles size={18} /> AI Demand Forecast (30-day)
                              </h4>
                              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                                RandomForest predictive ML model trained on historical sales velocity and seasonal indicators.
                              </p>

                              {predicting ? (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)' }}>
                                  <div className="status-dot"></div> Evaluating models...
                                </div>
                              ) : predictionResult ? (
                                <div>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                    <span style={{ fontSize: '0.85rem' }}>Predicted Demand:</span>
                                    <strong style={{ color: 'var(--text-bright)' }}>{Math.round(predictionResult.predicted_demand_30_days)} units</strong>
                                  </div>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                                    <span style={{ fontSize: '0.85rem' }}>Confidence Score:</span>
                                    <span style={{ color: 'var(--primary)', fontWeight: 600 }}>{(predictionResult.confidence * 100).toFixed(0)}%</span>
                                  </div>
                                  <div style={{ 
                                    background: 'rgba(0, 240, 194, 0.05)', 
                                    border: '1px solid var(--primary-glow)',
                                    padding: '0.75rem', 
                                    borderRadius: '8px', 
                                    fontSize: '0.8rem', 
                                    color: 'var(--text-main)' 
                                  }}>
                                    <strong>Recommendation:</strong> {predictionResult.recommendation}
                                  </div>
                                </div>
                              ) : (
                                <button className="btn btn-primary btn-sm" onClick={() => handlePredictDemand(med)} style={{ width: '100%' }}>
                                  Run Demand Predictor
                                </button>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
            <button className="btn btn-secondary btn-sm" disabled={page === 1} onClick={() => setPage(page - 1)}>Prev</button>
            <span style={{ display: 'flex', alignItems: 'center', padding: '0 1rem', color: 'var(--text-muted)' }}>Page {page} of {totalPages}</span>
            <button className="btn btn-secondary btn-sm" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        )}
      </div>

      {/* Modal: Add Medicine */}
      {showMedModal && (
        <div className="modal-backdrop active">
          <div className="modal-window glass-card">
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem' }}>Add New Medicine</h3>
            <form onSubmit={handleAddMedicine}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Medicine Name *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    value={newMed.name}
                    onChange={(e) => setNewMed({ ...newMed, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Generic Name</label>
                  <input
                    type="text"
                    className="form-control"
                    value={newMed.generic_name}
                    onChange={(e) => setNewMed({ ...newMed, generic_name: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Category *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    placeholder="e.g. Antibiotic"
                    value={newMed.category}
                    onChange={(e) => setNewMed({ ...newMed, category: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Unit Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    className="form-control"
                    value={newMed.unit_price}
                    onChange={(e) => setNewMed({ ...newMed, unit_price: e.target.value === '' ? '' : parseFloat(e.target.value) })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Manufacturer</label>
                  <input
                    type="text"
                    className="form-control"
                    value={newMed.manufacturer}
                    onChange={(e) => setNewMed({ ...newMed, manufacturer: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Dosage Form / Strength</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Capsule, 250mg"
                    value={newMed.dosage_form}
                    onChange={(e) => setNewMed({ ...newMed, dosage_form: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Description & Purpose</label>
                <textarea
                  className="form-control"
                  style={{ height: '60px', resize: 'none' }}
                  value={newMed.description}
                  onChange={(e) => setNewMed({ ...newMed, description: e.target.value, purpose: e.target.value })}
                />
              </div>

              <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-glass)' }}>
                <h4 style={{ color: 'var(--primary)', marginBottom: '1rem', fontSize: '0.9rem' }}>Initial Stock (Optional)</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label>Quantity</label>
                    <input
                      type="number"
                      className="form-control"
                      value={newMed.initial_stock}
                      onChange={(e) => setNewMed({ ...newMed, initial_stock: e.target.value === '' ? '' : parseInt(e.target.value) })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Batch Number</label>
                    <input
                      type="text"
                      className="form-control"
                      value={newMed.batch_number}
                      onChange={(e) => setNewMed({ ...newMed, batch_number: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Expiry Date</label>
                    <input
                      type="date"
                      className="form-control"
                      value={newMed.expiry_date}
                      onChange={(e) => setNewMed({ ...newMed, expiry_date: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '2rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowMedModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Medicine</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Batch */}
      {showBatchModal && (
        <div className="modal-backdrop active">
          <div className="modal-window glass-card">
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem' }}>Add Inventory Batch</h3>
            <form onSubmit={handleAddBatch}>
              <div className="form-group">
                <label>Batch Number *</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  placeholder="e.g. BATCH-12345"
                  value={newBatch.batch_number}
                  onChange={(e) => setNewBatch({ ...newBatch, batch_number: e.target.value })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Quantity *</label>
                  <input
                    type="number"
                    required
                    className="form-control"
                    value={newBatch.quantity_received}
                    onChange={(e) => setNewBatch({ ...newBatch, quantity_received: e.target.value === '' ? '' : parseInt(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>Supplier</label>
                  <input
                    type="text"
                    className="form-control"
                    value={newBatch.supplier}
                    onChange={(e) => setNewBatch({ ...newBatch, supplier: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                <div className="form-group">
                  <label>Manufacture Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={newBatch.manufacture_date}
                    onChange={(e) => setNewBatch({ ...newBatch, manufacture_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Expiry Date *</label>
                  <input
                    type="date"
                    required
                    className="form-control"
                    value={newBatch.expiry_date}
                    onChange={(e) => setNewBatch({ ...newBatch, expiry_date: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowBatchModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Batch</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
