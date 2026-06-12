import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { getScanBill, getQrCodeUrl } from '../../services/billingService';
import { getPrescriptionSummary, getMedicineExplanation, autoSetReminders } from '../../services/patientService';
import { QrCode, Search, Pill, Sparkles, MessageSquare, AlertCircle, FileText, Calendar, Camera, X } from 'lucide-react';
import { Html5QrcodeScanner } from 'html5-qrcode';

export default function QRScanPage() {
  const [token, setToken] = useState('');
  const [bill, setBill] = useState(null);
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [scanning, setScanning] = useState(false);

  // AI Explainer State
  const [activeMed, setActiveMed] = useState(null);
  const [medExpl, setMedExpl] = useState('');
  const [fetchingExpl, setFetchingExpl] = useState(false);

  // Tab state: 'bill' | 'ai'
  const [activeTab, setActiveTab] = useState('bill');

  useEffect(() => {
    let scanner = null;
    if (scanning) {
      scanner = new Html5QrcodeScanner(
        "qr-reader",
        { fps: 10, qrbox: {width: 250, height: 250} },
        /* verbose= */ false
      );
      scanner.render((decodedText) => {
        setToken(decodedText);
        setScanning(false);
        scanner.clear();
        handleScanSubmit(null, decodedText);
      }, (err) => {
        // ignore errors
      });
    }

    return () => {
      if (scanner) {
        scanner.clear().catch(e => console.error("Scanner clear error", e));
      }
    };
  }, [scanning]);

  const handleScanSubmit = async (e, directToken = null) => {
    if (e && e.preventDefault) e.preventDefault();
    const rawToken = directToken || token;
    if (!rawToken) return;

    let extractedToken = rawToken.trim();
    try {
      const url = new URL(extractedToken);
      const params = new URLSearchParams(url.search);
      if (params.get('token')) {
        extractedToken = params.get('token');
      }
    } catch (err) {
      const match = extractedToken.match(/(?:token=)?(MQ-[A-F0-9]{16})/i);
      if (match) {
        extractedToken = match[1].toUpperCase();
      }
    }

    setToken(extractedToken);

    try {
      setLoading(true);
      setError('');
      setSuccessMsg('');
      setBill(null);
      setSummary('');
      setActiveMed(null);

      // 1. Fetch public bill details
      const billRes = await getScanBill(extractedToken);
      if (billRes.success) {
        setBill(billRes.data);
        setActiveTab('bill');
        
        // Auto-set reminders & add to cabinet
        try {
          const autoRes = await autoSetReminders(extractedToken);
          if (autoRes.success) {
            setSuccessMsg("Success: Medicine cabinet & pill reminders have been automatically configured for this prescription!");
          }
        } catch (autoErr) {
          console.error('Auto-set reminders error:', autoErr);
        }

        // 2. Fetch AI prescription summary (Gemini/RAG)
        try {
          const summaryRes = await getPrescriptionSummary(extractedToken);
          if (summaryRes.success) {
            setSummary(summaryRes.data.summary);
          }
        } catch (sumErr) {
          console.error('AI summary error:', sumErr);
          setSummary('AI explanation summary service is currently processing, click on individual medicines below for instant guides.');
        }

      } else {
        setError('Invalid Receipt Token. Please check the code.');
      }
    } catch (err) {
      console.error(err);
      setError('Bill token not found. Double check or check backend server logs.');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchMedicineExplanation = async (item) => {
    try {
      setActiveMed(item);
      setMedExpl('');
      setFetchingExpl(true);
      setActiveTab('ai');

      const res = await getMedicineExplanation(item.medicine_id);
      if (res.success) {
        setMedExpl(res.data.explanation);
      } else {
        setMedExpl('Could not generate explanation.');
      }
    } catch (err) {
      console.error(err);
      setMedExpl('Fallback Guidance: This medicine is prescribed for ' + (item.purpose || 'therapeutic indications') + '. Take strictly according to: ' + (item.dosage_instructions || '1 dose daily') + '. Detail details could not be generated from AI engine.');
    } finally {
      setFetchingExpl(false);
    }
  };

  return (
    <div className="main-content">
      <Navbar title="Scan QR Code" subtitle="Read smart receipts and inspect drug indications using the AI Engine" />

      {/* Input token bar */}
      <div className="glass-card" style={{ marginBottom: '2.5rem', maxWidth: '650px', marginLeft: 'auto', marginRight: 'auto' }}>
        <h3 style={{ color: 'var(--text-bright)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
          <QrCode style={{ color: 'var(--primary)' }} /> Enter Receipt QR Token
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', marginBottom: '1.5rem' }}>
          Paste or type the unique bill token printed on the receipt or generated in the pharmacist console. You can also scan the QR code using your device camera.
        </p>

        {scanning ? (
          <div style={{ marginBottom: '1.5rem', border: '2px dashed var(--primary)', borderRadius: 'var(--radius-md)', padding: '1rem', background: 'rgba(0,0,0,0.2)', position: 'relative' }}>
            <button 
              onClick={() => setScanning(false)}
              style={{ position: 'absolute', top: '0.5rem', right: '0.5rem', zIndex: 10, background: 'rgba(0,0,0,0.5)', border: 'none', color: '#fff', borderRadius: '50%', padding: '0.25rem', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
            <div id="qr-reader" style={{ width: '100%', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}></div>
          </div>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <button className="btn btn-secondary" onClick={() => setScanning(true)} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Camera size={18} /> Scan with Camera
            </button>
          </div>
        )}

        <form onSubmit={handleScanSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            className="form-control"
            placeholder="e.g. MQ-A1B2C3D4E5F6G7H8"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Fetching...' : 'Verify'}
          </button>
        </form>

        {error && (
          <div style={{
            background: 'rgba(255, 23, 68, 0.1)',
            border: '1px solid var(--status-critical)',
            color: '#ff5252',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            marginTop: '1.5rem',
            fontSize: '0.85rem',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        {successMsg && (
          <div style={{
            background: 'rgba(0, 240, 194, 0.1)',
            border: '1px solid var(--primary)',
            color: 'var(--primary)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            marginTop: '1.5rem',
            fontSize: '0.85rem',
            textAlign: 'center'
          }}>
            {successMsg}
          </div>
        )}
      </div>

      {/* Details Display (If loaded) */}
      {bill && (
        <div className="patient-layout">
          {/* Left panel: Bill details / tabs */}
          <div>
            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              <button 
                className={`btn ${activeTab === 'bill' ? 'btn-primary' : 'btn-secondary'} btn-sm`} 
                onClick={() => setActiveTab('bill')}
                style={{ flex: 1 }}
              >
                <FileText size={14} /> Receipt Invoice
              </button>
              <button 
                className={`btn ${activeTab === 'ai' ? 'btn-primary' : 'btn-secondary'} btn-sm`} 
                onClick={() => setActiveTab('ai')}
                style={{ flex: 1 }}
                disabled={!activeMed}
              >
                <Sparkles size={14} /> AI Explainer {activeMed && `(${activeMed.medicine_name})`}
              </button>
            </div>

            {activeTab === 'bill' ? (
              <div className="glass-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                  <div>
                    <h2 style={{ color: 'var(--text-bright)' }}>{bill.pharmacy_name || 'MEDIQR PHARMACY'}</h2>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{bill.invoice_number}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Scan Verified</span>
                    <h4 style={{ color: 'var(--primary)', marginTop: '0.25rem' }}>₹{bill.final_amount}</h4>
                  </div>
                </div>

                <h4 style={{ color: 'var(--text-bright)', marginBottom: '1rem' }}>Prescribed Medicine Items</h4>
                <div className="alert-list">
                  {bill.items.map((item, idx) => (
                    <div 
                      key={idx} 
                      className="alert-item" 
                      style={{ 
                        borderLeftColor: 'var(--primary)', 
                        cursor: 'pointer',
                        background: activeMed?.medicine_id === item.medicine_id ? 'rgba(0, 240, 194, 0.05)' : 'rgba(255,255,255,0.02)'
                      }}
                      onClick={() => handleFetchMedicineExplanation(item)}
                    >
                      <div className="alert-body">
                        <h5>{item.medicine_name} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>(x{item.quantity})</span></h5>
                        <p style={{ marginTop: '0.25rem', color: 'var(--primary)', fontSize: '0.8rem', fontWeight: 600 }}>
                          Dosage schedule: {item.dosage_instructions || 'Take as directed'}
                        </p>
                        {item.manufacturer && <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Manufacturer: {item.manufacturer}</p>}
                      </div>
                      <button className="btn btn-secondary btn-sm" style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}>
                        Get AI Guide
                      </button>
                    </div>
                  ))}
                </div>

                <div style={{ marginTop: '1.5rem', background: 'rgba(255, 23, 68, 0.05)', border: '1px solid rgba(255, 23, 68, 0.2)', padding: '0.75rem 1.25rem', borderRadius: 'var(--radius-md)', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                  <AlertCircle size={20} style={{ color: '#ff5252', flexShrink: 0 }} />
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
                    {bill.disclaimer}
                  </p>
                </div>
              </div>
            ) : (
              /* AI Explainer Detail Tab */
              <div className="glass-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                  <Sparkles style={{ color: 'var(--primary)' }} />
                  <h3 style={{ color: 'var(--text-bright)', margin: 0 }}>AI Drug Explainer</h3>
                </div>

                <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>{activeMed.medicine_name}</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1.5rem' }}>
                  Indication: {activeMed.purpose || 'Prescription therapy'}
                </p>

                {fetchingExpl ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '3rem' }}>
                    <div className="scanner-animation">
                      <div className="scanner-laser"></div>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '1.5rem' }}>Consulting LLM knowledge bank...</span>
                  </div>
                ) : (
                  <div style={{ lineHeight: 1.6, fontSize: '0.95rem' }}>
                    <div style={{ 
                      whiteSpace: 'pre-wrap', 
                      background: 'rgba(0,0,0,0.2)', 
                      padding: '1.25rem', 
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-glass)',
                      marginBottom: '1.5rem',
                      color: 'var(--text-main)'
                    }}>
                      {medExpl}
                    </div>

                    <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('bill')}>
                      Back to Invoice
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right panel: AI Summary / Chat */}
          <div className="glass-card">
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <MessageSquare style={{ color: 'var(--primary)' }} /> AI Prescription Brief
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              Synthesized summary of all medicines, key side-effects, interactions, and recommended schedule.
            </p>

            <div style={{
              background: 'rgba(6, 8, 20, 0.4)',
              border: '1px solid var(--border-glass)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
              lineHeight: 1.6,
              fontSize: '0.9rem',
              color: 'var(--text-main)',
              maxHeight: '450px',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap'
            }}>
              {summary || 'Loading AI summary from Gemini model...'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
