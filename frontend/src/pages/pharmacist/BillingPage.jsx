import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { getMedicines, getMedicine } from '../../services/inventoryService';
import { createBill, getQrCodeUrl } from '../../services/billingService';
import { Trash2, Plus, Minus, Search, CreditCard, Download, QrCode } from 'lucide-react';

export default function BillingPage() {
  const [medicines, setMedicines] = useState([]);
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState([]);
  const [patientName, setPatientName] = useState('');
  const [patientPhone, setPatientPhone] = useState('');
  const [discount, setDiscount] = useState(0);

  // Selected medicine batches for dropdown
  const [activeBatches, setActiveBatches] = useState({});
  
  // Checkout response
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchMedicines();
  }, [search]);

  const fetchMedicines = async () => {
    try {
      const res = await getMedicines({ page: 1, per_page: 100, search: search || undefined });
      setMedicines(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddProduct = async (med) => {
    // Check if medicine already in cart
    const existing = cart.find(item => item.medicine_id === med.medicine_id);
    if (existing) {
      return;
    }

    try {
      // Fetch batches to select which batch to bill
      const res = await getMedicine(med.medicine_id);
      if (res.success && res.data.batches && res.data.batches.length > 0) {
        // Find first active batch with stock
        const validBatch = res.data.batches.find(b => b.status === 'active' && b.quantity_remaining > 0);
        
        if (!validBatch) {
          alert(`No active stock batches found for ${med.name}`);
          return;
        }

        // Save batches in reference map
        setActiveBatches(prev => ({ ...prev, [med.medicine_id]: res.data.batches }));

        // Add to cart
        setCart([
          ...cart,
          {
            medicine_id: med.medicine_id,
            name: med.name,
            unit_price: med.unit_price,
            quantity: 1,
            batch_id: validBatch.id,
            batch_number: validBatch.batch_number,
            max_stock: validBatch.quantity_remaining,
            dosage_instructions: med.dosage_schedule || ''
          }
        ]);
      } else {
        alert(`No batches tracked for ${med.name}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateQty = (medId, delta) => {
    setCart(
      cart.map(item => {
        if (item.medicine_id === medId) {
          const newQty = item.quantity + delta;
          if (newQty > item.max_stock) {
            alert(`Only ${item.max_stock} items remaining in this batch!`);
            return item;
          }
          return { ...item, quantity: Math.max(1, newQty) };
        }
        return item;
      })
    );
  };

  const handleUpdateBatch = (medId, batchId) => {
    const batches = activeBatches[medId];
    const selected = batches.find(b => b.id === parseInt(batchId));
    if (selected) {
      setCart(
        cart.map(item => {
          if (item.medicine_id === medId) {
            return {
              ...item,
              batch_id: selected.id,
              batch_number: selected.batch_number,
              max_stock: selected.quantity_remaining,
              quantity: Math.min(item.quantity, selected.quantity_remaining)
            };
          }
          return item;
        })
      );
    }
  };

  const handleUpdateInstructions = (medId, inst) => {
    setCart(
      cart.map(item => {
        if (item.medicine_id === medId) {
          return { ...item, dosage_instructions: inst };
        }
        return item;
      })
    );
  };

  const handleRemoveItem = (medId) => {
    setCart(cart.filter(item => item.medicine_id !== medId));
  };

  // Financial calculations
  const subtotal = cart.reduce((sum, item) => sum + item.unit_price * item.quantity, 0);
  const tax = subtotal * 0.05; // 5% tax
  const total = subtotal - discount + tax;

  const handleCheckout = async () => {
    if (cart.length === 0) {
      alert('Cart is empty!');
      return;
    }
    if (!patientName) {
      alert('Patient Name is required!');
      return;
    }

    try {
      setLoading(true);
      const payload = {
        patient_name: patientName,
        patient_phone: patientPhone || undefined,
        discount: parseFloat(discount) || 0.0,
        items: cart.map(item => ({
          medicine_id: item.medicine_id,
          batch_id: item.batch_id,
          quantity: item.quantity,
          dosage_instructions: item.dosage_instructions
        }))
      };

      const res = await createBill(payload);
      if (res.success) {
        setInvoice(res.data);
        // Clear cart
        setCart([]);
        setPatientName('');
        setPatientPhone('');
        setDiscount(0);
      }
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to complete transaction');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-content">
      <Navbar title="Smart Billing" subtitle="Compile receipts, register patient reminders, and generate QR invoices" />

      <div className="billing-layout">
        {/* Left Side: Cart & Search */}
        <div>
          {/* Search Box */}
          <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1rem' }}>Search Medicines</h3>
            <div style={{ position: 'relative' }}>
              <Search size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                className="form-control"
                placeholder="Type name to lookup and select..."
                style={{ paddingLeft: '2.5rem' }}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            
            {search && medicines.length > 0 && (
              <div style={{
                background: 'rgba(13, 17, 39, 0.95)',
                border: '1px solid var(--border-glass)',
                borderRadius: 'var(--radius-sm)',
                marginTop: '0.5rem',
                overflow: 'hidden'
              }}>
                {medicines.map(med => (
                  <div 
                    key={med.medicine_id}
                    onClick={() => handleAddProduct(med)}
                    style={{
                      padding: '0.75rem 1rem',
                      cursor: 'pointer',
                      borderBottom: '1px solid var(--border-glass)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      color: 'var(--text-bright)'
                    }}
                    onMouseEnter={(e) => e.target.style.background = 'rgba(0, 240, 194, 0.05)'}
                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                  >
                    <div>
                      <strong>{med.name}</strong>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{med.generic_name}</div>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.85rem', marginRight: '1rem' }}>₹{med.unit_price}</span>
                      <span className={`badge ${med.total_stock > 10 ? 'active' : med.total_stock > 0 ? 'warning' : 'expired'}`}>
                        {med.total_stock > 0 ? `${med.total_stock} stock` : 'out of stock'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Cart List */}
          <div className="glass-card">
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem' }}>Cart Checkout Items</h3>
            {cart.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                Search and select items to add to the invoice.
              </div>
            ) : (
              <div className="billing-cart">
                {cart.map((item) => (
                  <div key={item.medicine_id} className="cart-item">
                    <div className="cart-item-header">
                      <div>
                        <div className="cart-item-title">{item.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: '1rem', marginTop: '0.25rem' }}>
                          <span>Unit Price: ₹{item.unit_price}</span>
                          <span>Max Stock: {item.max_stock}</span>
                        </div>
                      </div>
                      
                      <div className="cart-item-controls">
                        <button className="btn btn-secondary btn-sm" style={{ padding: '0.25rem 0.5rem' }} onClick={() => handleUpdateQty(item.medicine_id, -1)}>
                          <Minus size={12} />
                        </button>
                        <span style={{ fontWeight: 'bold', minWidth: '20px', textAlign: 'center' }}>{item.quantity}</span>
                        <button className="btn btn-secondary btn-sm" style={{ padding: '0.25rem 0.5rem' }} onClick={() => handleUpdateQty(item.medicine_id, 1)}>
                          <Plus size={12} />
                        </button>
                        
                        <button className="btn btn-danger btn-sm" style={{ padding: '0.4rem' }} onClick={() => handleRemoveItem(item.medicine_id)}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
                      {/* Batch Selector */}
                      <div>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Active Batch *</label>
                        <select
                          className="form-control"
                          style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem', background: 'rgba(13, 17, 39, 0.9)' }}
                          value={item.batch_id}
                          onChange={(e) => handleUpdateBatch(item.medicine_id, e.target.value)}
                        >
                          {(activeBatches[item.medicine_id] || []).map(b => (
                            <option key={b.id} value={b.id}>
                              {b.batch_number} (Stock: {b.quantity_remaining}, Exp: {new Date(b.expiry_date).toLocaleDateString()})
                            </option>
                          ))}
                        </select>
                      </div>
                      {/* Dosage Guidance */}
                      <div>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Dosage schedule *</label>
                        <input
                          type="text"
                          className="form-control"
                          style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                          value={item.dosage_instructions}
                          onChange={(e) => handleUpdateInstructions(item.medicine_id, e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Checkout Details / Receipt Preview */}
        <div>
          {/* Invoice Receipt Preview (If generated) */}
          {invoice ? (
            <div className="receipt-preview" style={{ marginBottom: '1.5rem' }}>
              <div className="receipt-header">
                <span className="receipt-title">MEDIQR PHARMACY</span>
                <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>GSTIN: 29AAAAA1111A1Z1</p>
                <p style={{ fontSize: '0.85rem', fontWeight: 600, marginTop: '0.5rem' }}>{invoice.invoice_number}</p>
              </div>

              <div className="receipt-row">
                <span>Date:</span>
                <strong>{new Date(invoice.created_at).toLocaleString()}</strong>
              </div>
              <div className="receipt-row">
                <span>Patient:</span>
                <strong>{invoice.patient_name}</strong>
              </div>
              {invoice.patient_phone && (
                <div className="receipt-row">
                  <span>Phone:</span>
                  <strong>{invoice.patient_phone}</strong>
                </div>
              )}

              <div className="receipt-divider"></div>

              {invoice.items.map((item, idx) => (
                <div key={idx} style={{ marginBottom: '0.75rem' }}>
                  <div className="receipt-row" style={{ fontWeight: 600 }}>
                    <span>{item.medicine_name} (x{item.quantity})</span>
                    <span>₹{item.subtotal}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#666', fontStyle: 'italic' }}>
                    * Dir: {item.dosage_instructions}
                  </div>
                </div>
              ))}

              <div className="receipt-divider"></div>

              <div className="receipt-row">
                <span>Subtotal:</span>
                <span>₹{invoice.total_amount}</span>
              </div>
              {invoice.discount > 0 && (
                <div className="receipt-row" style={{ color: '#d32f2f' }}>
                  <span>Discount:</span>
                  <span>-₹{invoice.discount}</span>
                </div>
              )}
              <div className="receipt-row">
                <span>Tax (5% GST):</span>
                <span>₹{invoice.tax}</span>
              </div>
              <div className="receipt-row" style={{ fontSize: '1.1rem', fontWeight: 'bold', borderTop: '1px dashed #ccc', paddingTop: '0.5rem', marginTop: '0.5rem' }}>
                <span>Total Amount:</span>
                <span>₹{invoice.final_amount}</span>
              </div>

              {/* QR Code Scan section */}
              <div className="receipt-qr-area">
                <img src={getQrCodeUrl(invoice.bill_token)} alt="Receipt QR" />
                <div style={{ textAlign: 'center', marginTop: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', color: '#777', display: 'block' }}>
                    Scan code to access AI explanations & patient dashboard
                  </span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--primary)', display: 'block', marginTop: '0.25rem' }}>
                    Token: {invoice.bill_token}
                  </span>
                </div>
                
                <div style={{ display: 'flex', gap: '0.5rem', width: '100%', marginTop: '1rem' }}>
                  <a 
                    href={getQrCodeUrl(invoice.bill_token)}
                    download={`QR_${invoice.invoice_number}.png`}
                    className="btn btn-secondary btn-sm"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    <Download size={14} /> Download QR
                  </a>
                  <button className="btn btn-primary btn-sm" onClick={() => setInvoice(null)} style={{ flex: 1 }}>
                    New Invoice
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Checkout Form */
            <div className="glass-card">
              <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CreditCard style={{ color: 'var(--primary)' }} /> Billing Invoice
              </h3>

              <div className="form-group">
                <label>Patient Full Name *</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  placeholder="Enter full name"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Phone Number</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Enter phone number"
                  value={patientPhone}
                  onChange={(e) => setPatientPhone(e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '2rem' }}>
                <label>Discount Amount (₹)</label>
                <input
                  type="number"
                  className="form-control"
                  placeholder="0.00"
                  value={discount}
                  onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                />
              </div>

              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '1.5rem', marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Items Subtotal:</span>
                  <span style={{ color: 'var(--text-bright)' }}>₹{subtotal.toFixed(2)}</span>
                </div>
                {discount > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: '#ff5252' }}>
                    <span>Discount:</span>
                    <span>-₹{discount.toFixed(2)}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>GST Tax (5%):</span>
                  <span style={{ color: 'var(--text-bright)' }}>₹{tax.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.25rem', fontWeight: 'bold', marginTop: '1rem', color: 'var(--primary)' }}>
                  <span>Final Total:</span>
                  <span>₹{Math.max(0, total).toFixed(2)}</span>
                </div>
              </div>

              <button
                className="btn btn-primary"
                style={{ width: '100%', padding: '0.9rem' }}
                disabled={loading || cart.length === 0}
                onClick={handleCheckout}
              >
                {loading ? 'Processing Billing...' : 'Generate Invoice Receipt'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
