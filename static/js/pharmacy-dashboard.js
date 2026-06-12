/**
 * MedTrack - Pharmacy Inventory Dashboard JS
 * Interfaces with B2B inventory APIs for real-time tracking, alerts, and ingestion.
 */

let allMedicines = [];

document.addEventListener("DOMContentLoaded", () => {
  // Load initial data
  loadDashboardData();
  loadMedicinesForManualSelect();
  
  // Set up search and filter event listeners
  document.getElementById("search-input").addEventListener("input", debounce(loadDashboardData, 300));
  document.getElementById("filter-status").addEventListener("change", loadDashboardData);
});

// Helper for debouncing search input
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

async function loadDashboardData() {
  const searchQuery = document.getElementById("search-input").value.trim();
  const filterStatus = document.getElementById("filter-status").value;
  
  try {
    // 1. Load Statistics
    const statsRes = await fetch("/api/inventory/stats");
    if (statsRes.ok) {
      const stats = await statsRes.json();
      renderStats(stats);
    }

    // 2. Load Active Alerts
    const alertsRes = await fetch("/api/inventory/alerts");
    if (alertsRes.ok) {
      const alertsData = await alertsRes.json();
      renderAlerts(alertsData.alerts);
    }

    // 3. Load Inventory batches
    let url = `/api/inventory?page=1&per_page=50`;
    if (filterStatus) url += `&status=${filterStatus}`;
    if (searchQuery) url += `&q=${encodeURIComponent(searchQuery)}`;
    
    // We also fetch medicine listings if status includes active to find matches
    const invRes = await fetch(url);
    if (invRes.ok) {
      const invData = await invRes.json();
      renderInventory(invData.batches);
    }

  } catch (error) {
    console.error("Error loading dashboard data:", error);
  }
}

function renderStats(stats) {
  document.getElementById("stat-medicines").textContent = stats.total_medicines;
  document.getElementById("stat-total-stock").textContent = stats.total_stock_units.toLocaleString();
  document.getElementById("stat-low-stock").textContent = stats.low_stock_batches;
  document.getElementById("stat-expiring").textContent = stats.expiring_soon;

  // Add flashing classes if alerts are active
  const lowStockCard = document.getElementById("metric-low-stock");
  if (stats.low_stock_batches > 0) {
    lowStockCard.classList.add("warning");
  } else {
    lowStockCard.classList.remove("warning");
  }

  const expiringCard = document.getElementById("metric-expiring");
  if (stats.expiring_soon > 0) {
    expiringCard.classList.add("critical");
  } else {
    expiringCard.classList.remove("critical");
  }
}

function renderAlerts(alerts) {
  const container = document.getElementById("alerts-container");
  const countBadge = document.getElementById("alerts-count-badge");
  const alertsCard = document.getElementById("alerts-card");
  
  countBadge.textContent = `${alerts.length} Active Alert${alerts.length !== 1 ? 's' : ''}`;
  
  if (alerts.length === 0) {
    container.innerHTML = `
      <div style="color: var(--text-muted); font-size: 0.9rem; text-align: center; padding: 1.5rem;">
        ✅ All systems nominal. No stock shortages or expired batches found.
      </div>
    `;
    alertsCard.style.borderColor = "var(--border-glass)";
    return;
  }
  
  alertsCard.style.borderColor = "rgba(255, 23, 68, 0.4)";
  
  container.innerHTML = alerts.map(alert => {
    const dateStr = new Date(alert.created_at).toLocaleString();
    let severityClass = "info";
    if (alert.severity === "warning") severityClass = "warning";
    if (alert.severity === "critical") severityClass = "critical";
    
    return `
      <div class="alert-item ${severityClass}">
        <div class="alert-body">
          <h5 style="display:flex; align-items:center; gap:0.5rem;">
            <span style="color: ${getSeverityColor(alert.severity)}">●</span>
            ${alert.message}
          </h5>
          <p>Logged: ${dateStr} | Type: ${alert.alert_type.replace('_', ' ')}</p>
        </div>
        <button class="btn btn-sm btn-secondary" onclick="resolveAlert(${alert.id})">Mark Resolved</button>
      </div>
    `;
  }).join("");
}

function getSeverityColor(severity) {
  if (severity === "critical") return "var(--status-critical)";
  if (severity === "warning") return "var(--status-warning)";
  return "var(--status-info)";
}

async function resolveAlert(alertId) {
  try {
    const res = await fetch(`/api/inventory/alerts/${alertId}/resolve`, {
      method: "POST"
    });
    if (res.ok) {
      loadDashboardData();
    }
  } catch (error) {
    console.error("Failed to resolve alert:", error);
  }
}

function renderInventory(batches) {
  const tbody = document.getElementById("inventory-table-body");
  
  if (batches.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 3rem;">
          No inventory batches match current filters.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = batches.map(batch => {
    const expiryDate = new Date(batch.expiry_date);
    const dateStr = expiryDate.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    const isExpired = expiryDate < new Date();
    
    let statusClass = "active";
    if (batch.status === "expired" || isExpired) statusClass = "expired";
    if (batch.status === "recalled") statusClass = "recalled";

    // Warn if expiring within 30 days and not flagged as expired
    if (statusClass === "active") {
      const diffTime = expiryDate - new Date();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays <= 30) {
        statusClass = "warning";
      }
    }
    
    // Quick indicator if stock is low
    const isLowStock = batch.quantity_remaining <= 10;

    return `
      <tr>
        <td>
          <div style="font-weight: 600; color: var(--text-bright);">${batch.medicine_name || 'Loading...'}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${batch.medicine_id}</div>
        </td>
        <td><code style="color: var(--primary);">${batch.batch_number}</code></td>
        <td>
          <span style="font-weight: 500; ${isLowStock ? 'color: var(--status-warning)' : ''}">
            ${batch.quantity_remaining}
          </span>
          <span style="color: var(--text-muted); font-size: 0.8rem;"> / ${batch.quantity_received}</span>
          ${isLowStock && batch.status === 'active' ? '<span style="color:var(--status-warning); font-size:0.75rem; margin-left:0.25rem;">(Low)</span>' : ''}
        </td>
        <td>
          <span style="${statusClass === 'expired' ? 'color: var(--status-critical); text-decoration: line-through;' : ''}">
            ${dateStr}
          </span>
        </td>
        <td style="color: var(--text-muted);">${batch.supplier}</td>
        <td>
          <span class="badge ${statusClass}">
            ${statusClass === 'warning' ? 'expiring soon' : batch.status}
          </span>
        </td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="simulateUsage(${batch.id}, ${batch.quantity_remaining})">
            Dispense
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

async function simulateUsage(batchId, currentQty) {
  if (currentQty <= 0) {
    alert("Batch is already out of stock!");
    return;
  }
  const dispenseQty = prompt("Enter quantity to dispense:", "10");
  if (dispenseQty === null) return;
  
  const qty = parseInt(dispenseQty);
  if (isNaN(qty) || qty <= 0) {
    alert("Please enter a valid positive number.");
    return;
  }
  if (qty > currentQty) {
    alert(`Cannot dispense more than available: ${currentQty}`);
    return;
  }

  try {
    const res = await fetch(`/api/inventory/${batchId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quantity_remaining: currentQty - qty })
    });
    if (res.ok) {
      loadDashboardData();
    } else {
      const err = await res.json();
      alert(`Error: ${err.error}`);
    }
  } catch (error) {
    console.error("Failed to update inventory quantity:", error);
  }
}

// ── Modal & Logging Handlers ──────────────────────────────────────────────────

function openScanModal() {
  document.getElementById("scan-modal").classList.add("active");
  setScanMode('qr');
}

function closeScanModal() {
  document.getElementById("scan-modal").classList.remove("active");
}

function setScanMode(mode) {
  const tabQr = document.getElementById("tab-qr");
  const tabManual = document.getElementById("tab-manual");
  const viewQr = document.getElementById("qr-scan-view");
  const viewManual = document.getElementById("manual-entry-view");

  if (mode === 'qr') {
    tabQr.className = "btn btn-sm btn-primary";
    tabManual.className = "btn btn-sm btn-secondary";
    viewQr.style.display = "block";
    viewManual.style.display = "none";
  } else {
    tabQr.className = "btn btn-sm btn-secondary";
    tabManual.className = "btn btn-sm btn-primary";
    viewQr.style.display = "none";
    viewManual.style.display = "block";
  }
}

async function loadMedicinesForManualSelect() {
  try {
    const res = await fetch("/api/medicines");
    if (res.ok) {
      allMedicines = await res.json();
      const select = document.getElementById("manual-med-id");
      select.innerHTML = '<option value="">Choose medicine...</option>' + 
        allMedicines.map(m => `<option value="${m.medicine_id}">${m.name} (${m.strength})</option>`).join("");
    }
  } catch (e) {
    console.error("Failed to load medicine list:", e);
  }
}

function loadSampleManufacturerQR() {
  if (allMedicines.length === 0) return;
  const sampleMed = allMedicines[Math.floor(randomBetween(0, allMedicines.length))];
  
  const now = new Date();
  const mfg = new Date(now.getFullYear(), now.getMonth() - 2, now.getDate());
  const exp = new Date(now.getFullYear() + 2, now.getMonth(), now.getDate());
  
  const payload = {
    medicine_id: sampleMed ? sampleMed.medicine_id : "MED_001",
    batch_number: `BATCH-${sampleMed ? sampleMed.name.substring(0,4).toUpperCase() : 'TEST'}-2026-${randomBetween(10,99)}`,
    manufacture_date: mfg.toISOString().split('T')[0],
    expiry_date: exp.toISOString().split('T')[0],
    quantity_received: Math.floor(randomBetween(100, 300)),
    supplier: "PharmaExpress Logistics",
    manufacturer_qr_data: `MFR_SIGNED_CERTIFICATE_KEY:${randomBetween(1000, 9999)}`
  };
  
  document.getElementById("qr-payload-input").value = JSON.stringify(payload, null, 2);
}

function randomBetween(min, max) {
  return Math.random() * (max - min) + min;
}

async function submitQRScan() {
  const text = document.getElementById("qr-payload-input").value.trim();
  if (!text) {
    alert("Please enter a JSON QR payload first.");
    return;
  }
  
  let payload;
  try {
    payload = JSON.parse(text);
  } catch (e) {
    alert("Invalid JSON format. Please verify standard syntax.");
    return;
  }

  try {
    const res = await fetch("/api/inventory/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (res.ok) {
      closeScanModal();
      loadDashboardData();
      // Reset text field
      document.getElementById("qr-payload-input").value = "";
    } else {
      const err = await res.json();
      alert(`Error ingesting QR: ${err.error}`);
    }
  } catch (error) {
    console.error("Ingestion failed:", error);
  }
}

async function submitManualForm(event) {
  event.preventDefault();
  
  const payload = {
    medicine_id: document.getElementById("manual-med-id").value,
    batch_number: document.getElementById("manual-batch-num").value.trim(),
    quantity_received: parseInt(document.getElementById("manual-qty").value),
    manufacture_date: document.getElementById("manual-mfg-date").value,
    expiry_date: document.getElementById("manual-expiry-date").value,
    supplier: document.getElementById("manual-supplier").value.trim() || "Unknown",
    manufacturer_qr_data: "MANUAL_ENTRY"
  };

  try {
    const res = await fetch("/api/inventory/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (res.ok) {
      closeScanModal();
      loadDashboardData();
      document.getElementById("manual-shipment-form").reset();
    } else {
      const err = await res.json();
      alert(`Error logging batch: ${err.error}`);
    }
  } catch (error) {
    console.error("Batch submission failed:", error);
  }
}

function resetFilters() {
  document.getElementById("search-input").value = "";
  document.getElementById("filter-status").value = "active";
  loadDashboardData();
}
