import React, { useState, useEffect } from 'react';
import Navbar from '../../components/ui/Navbar';
import { getReminders, createReminder, updateReminder, deleteReminder, autoSetReminders } from '../../services/patientService';
import { Plus, Bell, Check, Clock, Trash2, Calendar, AlertCircle, Search } from 'lucide-react';

export default function ReminderPage() {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  // Form state
  const [newReminder, setNewReminder] = useState({
    medicine_name: '',
    dosage: '',
    time_of_day: 'morning', // morning | afternoon | night | custom
    custom_time: '',
    scheduled_date: '',
    notes: ''
  });

  const [autoSetId, setAutoSetId] = useState('');
  const [autoSetLoading, setAutoSetLoading] = useState(false);

  useEffect(() => {
    fetchReminders();
    
    // Check if user came from a QR code scan
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    if (tokenFromUrl) {
      setAutoSetId(tokenFromUrl);
      // We run the auto-set logic directly after setting the state
      handleAutoSet(tokenFromUrl);
    }
  }, []);

  const fetchReminders = async () => {
    try {
      setLoading(true);
      const res = await getReminders();
      if (res.success) {
        setReminders(res.data);
      } else {
        setError('Failed to fetch reminders');
      }
    } catch (err) {
      console.error(err);
      setError('Could not connect to reminders service');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusToggle = async (reminder) => {
    const nextStatus = reminder.status === 'taken' ? 'pending' : 'taken';
    try {
      const res = await updateReminder(reminder.id, { status: nextStatus });
      if (res.success) {
        setReminders(reminders.map(r => r.id === reminder.id ? res.data : r));
      }
    } catch (err) {
      console.error(err);
    }
  };


  const handleAutoSet = async (tokenOverride = null) => {
    const tokenToUse = typeof tokenOverride === 'string' ? tokenOverride : autoSetId;
    if (!tokenToUse.trim()) return;
    
    try {
      setAutoSetLoading(true);
      const res = await autoSetReminders(tokenToUse.trim());
      if (res.success) {
        setAutoSetId('');
        fetchReminders();
        alert(res.message);
      } else {
        alert(res.error || 'Failed to auto-set reminders');
      }
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Could not auto-set reminders');
    } finally {
      setAutoSetLoading(false);
    }
  };

  const handleAddReminder = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...newReminder };
      if (payload.time_of_day !== 'custom') {
        payload.custom_time = undefined;
      }
      if (!payload.scheduled_date) {
        // default to today
        payload.scheduled_date = new Date().toISOString().split('T')[0];
      }

      const res = await createReminder(payload);
      if (res.success) {
        setShowAddModal(false);
        fetchReminders();
        setNewReminder({
          medicine_name: '',
          dosage: '',
          time_of_day: 'morning',
          custom_time: '',
          scheduled_date: '',
          notes: ''
        });
      }
    } catch (err) {
      console.error(err);
      alert('Failed to save reminder');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this reminder schedule?')) return;
    try {
      const res = await deleteReminder(id);
      if (res.success) {
        setReminders(reminders.filter(r => r.id !== id));
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Organize reminders by slot
  const filterByTimeOfDay = (slot) => {
    return reminders.filter(r => r.time_of_day === slot);
  };

  if (loading) {
    return (
      <div className="main-content">
        <Navbar title="Pill Reminders" subtitle="Loading schedules..." />
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
      <Navbar title="My Daily Pill Tracker" subtitle="Mark dosages as taken and configure medicine reminders" />

      {error && (
        <div className="glass-card" style={{ borderLeft: '4px solid var(--status-critical)', marginBottom: '2rem' }}>
          <p style={{ color: 'var(--text-bright)' }}>{error}</p>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
        <div className="glass-card" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '1rem', justifyContent: 'space-between', padding: '1rem 1.5rem' }}>
          <div>
            <h4 style={{ color: 'var(--text-bright)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Search size={18} /> Auto-Set from Prescription
            </h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0.25rem 0 0 0' }}>Enter your bill's unique token to instantly generate your pill schedule.</p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flex: 1, minWidth: '250px', maxWidth: '400px' }}>
            <input 
              type="text" 
              className="form-control" 
              placeholder="e.g. 8f9b2a" 
              value={autoSetId}
              onChange={(e) => setAutoSetId(e.target.value)}
              disabled={autoSetLoading}
            />
            <button className="btn btn-primary" onClick={handleAutoSet} disabled={autoSetLoading || !autoSetId.trim()} style={{ whiteSpace: 'nowrap' }}>
              {autoSetLoading ? 'Setting...' : 'Auto-Set'}
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={() => setShowAddModal(true)}>
            <Plus size={18} /> Add Manual Reminder
          </button>
        </div>
      </div>

      {/* Calendar Dailies Grid */}
      <div className="calendar-grid">
        {/* Morning Slot */}
        <div className="calendar-slot">
          <div className="calendar-slot-title">Morning Dosages</div>
          {filterByTimeOfDay('morning').length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>None scheduled</p>
          ) : (
            filterByTimeOfDay('morning').map(rem => (
              <div 
                key={rem.id} 
                onClick={() => handleStatusToggle(rem)}
                className="calendar-item" 
                style={{ 
                  borderLeftColor: rem.status === 'taken' ? 'var(--status-success)' : 'var(--secondary)',
                  cursor: 'pointer',
                  opacity: rem.status === 'taken' ? 0.7 : 1,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, textDecoration: rem.status === 'taken' ? 'line-through' : 'none' }}>{rem.medicine_name}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Dosage: {rem.dosage || '1 unit'}</div>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }} onClick={(e) => e.stopPropagation()}>
                  <button onClick={() => handleDelete(rem.id)} style={{ background: 'transparent', border: 'none', color: '#ff5252', cursor: 'pointer' }}>
                    <Trash2 size={12} />
                  </button>
                  {rem.status === 'taken' && <Check size={14} style={{ color: 'var(--status-success)' }} />}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Afternoon Slot */}
        <div className="calendar-slot">
          <div className="calendar-slot-title">Afternoon Dosages</div>
          {filterByTimeOfDay('afternoon').length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>None scheduled</p>
          ) : (
            filterByTimeOfDay('afternoon').map(rem => (
              <div 
                key={rem.id} 
                onClick={() => handleStatusToggle(rem)}
                className="calendar-item" 
                style={{ 
                  borderLeftColor: rem.status === 'taken' ? 'var(--status-success)' : 'var(--status-warning)',
                  cursor: 'pointer',
                  opacity: rem.status === 'taken' ? 0.7 : 1,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, textDecoration: rem.status === 'taken' ? 'line-through' : 'none' }}>{rem.medicine_name}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Dosage: {rem.dosage || '1 unit'}</div>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }} onClick={(e) => e.stopPropagation()}>
                  <button onClick={() => handleDelete(rem.id)} style={{ background: 'transparent', border: 'none', color: '#ff5252', cursor: 'pointer' }}>
                    <Trash2 size={12} />
                  </button>
                  {rem.status === 'taken' && <Check size={14} style={{ color: 'var(--status-success)' }} />}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Night Slot */}
        <div className="calendar-slot">
          <div className="calendar-slot-title">Night Dosages</div>
          {filterByTimeOfDay('night').length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>None scheduled</p>
          ) : (
            filterByTimeOfDay('night').map(rem => (
              <div 
                key={rem.id} 
                onClick={() => handleStatusToggle(rem)}
                className="calendar-item" 
                style={{ 
                  borderLeftColor: rem.status === 'taken' ? 'var(--status-success)' : 'var(--primary)',
                  cursor: 'pointer',
                  opacity: rem.status === 'taken' ? 0.7 : 1,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, textDecoration: rem.status === 'taken' ? 'line-through' : 'none' }}>{rem.medicine_name}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Dosage: {rem.dosage || '1 unit'}</div>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }} onClick={(e) => e.stopPropagation()}>
                  <button onClick={() => handleDelete(rem.id)} style={{ background: 'transparent', border: 'none', color: '#ff5252', cursor: 'pointer' }}>
                    <Trash2 size={12} />
                  </button>
                  {rem.status === 'taken' && <Check size={14} style={{ color: 'var(--status-success)' }} />}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Custom / Other slot */}
        <div className="calendar-slot">
          <div className="calendar-slot-title">Custom Scheduled</div>
          {filterByTimeOfDay('custom').length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>None scheduled</p>
          ) : (
            filterByTimeOfDay('custom').map(rem => (
              <div 
                key={rem.id} 
                onClick={() => handleStatusToggle(rem)}
                className="calendar-item" 
                style={{ 
                  borderLeftColor: rem.status === 'taken' ? 'var(--status-success)' : 'var(--status-info)',
                  cursor: 'pointer',
                  opacity: rem.status === 'taken' ? 0.7 : 1,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, textDecoration: rem.status === 'taken' ? 'line-through' : 'none' }}>{rem.medicine_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--primary)' }}>🕒 {rem.custom_time ? rem.custom_time.slice(0, 5) : 'Scheduled'}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>Dosage: {rem.dosage || '1 unit'}</div>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }} onClick={(e) => e.stopPropagation()}>
                  <button onClick={() => handleDelete(rem.id)} style={{ background: 'transparent', border: 'none', color: '#ff5252', cursor: 'pointer' }}>
                    <Trash2 size={12} />
                  </button>
                  {rem.status === 'taken' && <Check size={14} style={{ color: 'var(--status-success)' }} />}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Modal: Add Reminder */}
      {showAddModal && (
        <div className="modal-backdrop active">
          <div className="modal-window glass-card">
            <h3 style={{ color: 'var(--text-bright)', marginBottom: '1.5rem' }}>Create Pill Reminder</h3>
            <form onSubmit={handleAddReminder}>
              <div className="form-group">
                <label>Medicine Name *</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  placeholder="e.g. Paracetamol 500mg"
                  value={newReminder.medicine_name}
                  onChange={(e) => setNewReminder({ ...newReminder, medicine_name: e.target.value })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Dosage unit *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    placeholder="e.g. 1 Tablet, 5ml"
                    value={newReminder.dosage}
                    onChange={(e) => setNewReminder({ ...newReminder, dosage: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Schedule Target *</label>
                  <select
                    className="form-control"
                    style={{ background: 'rgba(13, 17, 39, 0.9)' }}
                    value={newReminder.time_of_day}
                    onChange={(e) => setNewReminder({ ...newReminder, time_of_day: e.target.value })}
                  >
                    <option value="morning">Morning</option>
                    <option value="afternoon">Afternoon</option>
                    <option value="night">Night</option>
                    <option value="custom">Custom Time</option>
                  </select>
                </div>
              </div>

              {newReminder.time_of_day === 'custom' && (
                <div className="form-group">
                  <label>Select Time *</label>
                  <input
                    type="time"
                    required
                    className="form-control"
                    value={newReminder.custom_time}
                    onChange={(e) => setNewReminder({ ...newReminder, custom_time: e.target.value })}
                  />
                </div>
              )}

              <div className="form-group">
                <label>Target Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={newReminder.scheduled_date}
                  onChange={(e) => setNewReminder({ ...newReminder, scheduled_date: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Additional Notes / Directives</label>
                <textarea
                  className="form-control"
                  style={{ height: '70px', resize: 'none' }}
                  placeholder="e.g. Take after meals"
                  value={newReminder.notes}
                  onChange={(e) => setNewReminder({ ...newReminder, notes: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '2rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Schedule</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
