/**
 * MedTrack - Smart Billing JS
 * Manages medicine inventory lookup, invoice cart builder, and receipt generation.
 */

let cart = [];
let availableBatches = [];

document.addEventListener("DOMContentLoaded", () => {
  loadInvoices();
  
  const searchInput = document.getElementById("med-search");
  searchInput.addEventListener("input", debounce(searchMedicineStock, 250));
  
  // Close search dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (e.target.id !== "med-search" && e.target.id !== "search-dropdown") {
      document.getElementById("search-dropdown").style.display = "none";
    }
  });
});

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

async function searchMedicineStock() {
  const query = document.getElementById("med-search").value.trim();
  const dropdown = document.getElementById("search-dropdown");
  
  if (!query) {
    dropdown.style.display = "none";
    return;
  }

  try {
    const res = await fetch(`/api/billing/available-stock?q=${encodeURIComponent(query)}`);
    if (res.ok) {
      availableBatches = await res.json();
      renderDropdown(availableBatches);
    }
  } catch (error) {
    console.error("Search failed:", error);
  }
}

function renderDropdown(batches) {
  const dropdown = document.getElementById("search-dropdown");
  if (batches.length === 0) {
    dropdown.innerHTML = `<div style="padding: 0.8rem; color: var(--text-muted); font-size: 0.85rem;">No active batches available.</div>`;
    dropdown.style.display = "block";
    return;
  }

  dropdown.innerHTML = batches.map(b => {
    return `
      <div class="dropdown-item" 
           style="padding: 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.03); cursor: pointer; transition: all 0.2s;" 
           onclick="addBatchToCart(${b.id})"
           onmouseover="this.style.background='rgba(255,255,255,0.04)'"
           onmouseout="this.style.background='transparent'">
        <div style="font-weight:600; color: var(--text-bright); font-size: 0.9rem;">
          ${b.medicine_name} (${b.strength})
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-muted); margin-top:0.2rem;">
          <span>Batch: <code>${b.batch_number}</code> | Stock: <strong>${b.quantity_remaining}</strong></span>
          <span style="color: var(--primary);">$${b.unit_price.toFixed(2)}/unit</span>
        </div>
      </div>
    `;
  }).join("");
  dropdown.style.display = "block";
}

function addBatchToCart(batchId) {
  const batch = availableBatches.find(b => b.id === batchId);
  if (!batch) return;

  // Check if already in cart
  const existing = cart.find(item => item.id === batchId);
  if (existing) {
    if (existing.quantity < batch.quantity_remaining) {
      existing.quantity += 1;
    } else {
      alert("Cannot exceed maximum available stock for this batch.");
    }
  } else {
    // Determine default dosage instruction suggestion based on category
    let defaultDosing = "Take 1 tablet daily";
    const cat = (batch.category || "").toLowerCase();
    if (cat.includes("antibiotic")) {
      defaultDosing = "1 capsule 3x daily after meals for 7 days";
    } else if (cat.includes("analgesic") || cat.includes("painkiller")) {
      defaultDosing = "1 tablet twice daily as needed for pain";
    }

    cart.push({
      id: batch.id,
      medicine_name: batch.medicine_name,
      strength: batch.strength,
      batch_number: batch.batch_number,
      unit_price: batch.unit_price,
      quantity: 1,
      max_qty: batch.quantity_remaining,
      dosage: defaultDosing
    });
  }

  document.getElementById("med-search").value = "";
  document.getElementById("search-dropdown").style.display = "none";
  renderCart();
}

function updateCartQty(batchId, val) {
  const item = cart.find(i => i.id === batchId);
  if (!item) return;

  const qty = parseInt(val);
  if (isNaN(qty) || qty <= 0) {
    item.quantity = 1;
  } else if (qty > item.max_qty) {
    alert(`Only ${item.max_qty} units available in this batch.`);
    item.quantity = item.max_qty;
  } else {
    item.quantity = qty;
  }
  renderCart();
}

function updateCartDosage(batchId, text) {
  const item = cart.find(i => i.id === batchId);
  if (item) {
    item.dosage = text;
  }
}

function removeFromCart(batchId) {
  cart = cart.filter(i => i.id !== batchId);
  renderCart();
}

function renderCart() {
  const container = document.getElementById("cart-container");
  const grandTotalEl = document.getElementById("grand-total");
  
  if (cart.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 3rem; font-size: 0.95rem;">
        No items added. Use the search bar above to look up medicines and add them to the bill.
      </div>
    `;
    grandTotalEl.textContent = "$0.00";
    return;
  }

  let total = 0;
  
  container.innerHTML = cart.map(item => {
    const lineTotal = item.unit_price * item.quantity;
    total += lineTotal;
    
    return `
      <div class="cart-item">
        <div class="cart-item-header">
          <div>
            <span class="cart-item-title">${item.medicine_name}</span>
            <span style="font-size:0.8rem; color:var(--text-muted); margin-left:0.5rem;">(${item.strength})</span>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">
              Batch: <code>${item.batch_number}</code> | Max Available: ${item.max_qty}
            </div>
          </div>
          <button onclick="removeFromCart(${item.id})" style="background:none; border:none; color:var(--status-critical); cursor:pointer; font-size:1.1rem;">&times;</button>
        </div>
        
        <div style="display:flex; justify-content:space-between; align-items:center; gap:2rem; flex-wrap:wrap; margin-top:0.5rem;">
          <div class="form-group" style="margin-bottom:0; flex:1;">
            <label style="margin-bottom:0.25rem; font-size:0.75rem;">Dispense Quantity</label>
            <input type="number" class="form-control" style="padding:0.4rem 0.75rem;" min="1" max="${item.max_qty}" value="${item.quantity}" onchange="updateCartQty(${item.id}, this.value)">
          </div>
          <div class="form-group" style="margin-bottom:0; flex:2.5;">
            <label style="margin-bottom:0.25rem; font-size:0.75rem;">Patient Dosing Instructions (QR-encoded)</label>
            <input type="text" class="form-control" style="padding:0.4rem 0.75rem;" value="${item.dosage}" oninput="updateCartDosage(${item.id}, this.value)">
          </div>
          <div style="text-align:right; min-width:80px; margin-top:1.25rem;">
            <span style="font-size:0.75rem; color:var(--text-muted); display:block;">$${item.unit_price.toFixed(2)} ea</span>
            <span style="font-weight:600; color:var(--text-bright);">$${lineTotal.toFixed(2)}</span>
          </div>
        </div>
      </div>
    `;
  }).join("");

  grandTotalEl.textContent = `$${total.toFixed(2)}`;
}

async function submitInvoice() {
  const patientName = document.getElementById("bill-patient-name").value.trim();
  const pharmacistName = document.getElementById("bill-pharmacist-name").value.trim();
  
  if (!patientName) {
    alert("Please enter patient name.");
    return;
  }
  if (cart.length === 0) {
    alert("Please add at least one medication to the invoice.");
    return;
  }

  const payload = {
    patient_name: patientName,
    pharmacist_name: pharmacistName,
    items: cart.map(i => ({
      batch_id: i.id,
      quantity: i.quantity,
      dosage_instructions: i.dosage
    }))
  };

  try {
    const res = await fetch("/api/billing/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (res.ok) {
      const data = await res.json();
      
      // Clear cart
      cart = [];
      renderCart();
      document.getElementById("bill-patient-name").value = "";
      
      // Show Receipt Modal
      showReceipt(data);
      loadInvoices();
    } else {
      const err = await res.json();
      alert(`Invoice generation failed: ${err.error}`);
    }
  } catch (error) {
    console.error("Failed to post invoice:", error);
  }
}

function showReceipt(data) {
  document.getElementById("receipt-num").textContent = data.invoice_number;
  document.getElementById("receipt-pat").textContent = data.items[0] ? data.items[0].patient || document.getElementById("bill-patient-name").value : "Patient";
  // Fallback if not returned directly
  document.getElementById("receipt-pat").textContent = data.invoice_number ? document.getElementById("bill-patient-name").value || "Walk-in Patient" : "";
  document.getElementById("receipt-phm").textContent = document.getElementById("bill-pharmacist-name").value;
  document.getElementById("receipt-date").textContent = `Date: ${new Date().toISOString().split('T')[0]}`;
  document.getElementById("receipt-total").textContent = `$${data.total_amount.toFixed(2)}`;
  
  // Set image source
  document.getElementById("receipt-qr-img").src = data.qr_image_url;
  
  // Build items block HTML
  const itemsContainer = document.getElementById("receipt-items-container");
  itemsContainer.innerHTML = data.items.map(item => {
    return `
      <div style="font-size:0.8rem; margin-bottom:0.5rem; color:#222;">
        <div style="display:flex; justify-content:space-between;">
          <span><strong>${item.name}</strong> x${item.quantity}</span>
          <span>$${item.line_total.toFixed(2)}</span>
        </div>
        <div style="font-size:0.7rem; color:#555; margin-left:0.5rem; font-style:italic;">
          Batch: ${item.batch} | Exp: ${item.expiry}
        </div>
        <div style="font-size:0.7rem; color:#555; margin-left:0.5rem;">
          Dir: ${item.dosage}
        </div>
      </div>
    `;
  }).join("");

  // Activate Modal Backdrop
  document.getElementById("receipt-modal").classList.add("active");
}

function closeReceiptModal() {
  document.getElementById("receipt-modal").classList.remove("active");
}

async function loadInvoices() {
  const container = document.getElementById("recent-invoices-container");
  try {
    const res = await fetch("/api/billing/invoices?page=1&per_page=10");
    if (res.ok) {
      const data = await res.json();
      renderInvoicesList(data.invoices);
    }
  } catch (e) {
    console.error("Recent invoices load error:", e);
  }
}

function renderInvoicesList(invoices) {
  const container = document.getElementById("recent-invoices-container");
  if (invoices.length === 0) {
    container.innerHTML = `<div style="color:var(--text-muted); font-size:0.85rem; text-align:center; padding:1.5rem;">No recent invoices logged.</div>`;
    return;
  }

  container.innerHTML = invoices.map(i => {
    const dateStr = new Date(i.created_at).toLocaleDateString();
    return `
      <div class="metric-card" style="padding:1rem; cursor:pointer;" onclick="loadInvoiceDetailsForReceipt(${i.id})">
        <div style="display:flex; flex-direction:column; gap:0.2rem; text-align:left;">
          <code style="color:var(--primary); font-size:0.8rem; font-weight:600;">${i.invoice_number}</code>
          <span style="font-size:0.85rem; color:var(--text-bright);">${i.patient_name}</span>
          <span style="font-size:0.7rem; color:var(--text-muted);">${dateStr}</span>
        </div>
        <div style="text-align:right;">
          <span style="font-family:var(--font-title); font-weight:700; color:var(--text-bright); font-size:1rem;">$${i.total_amount.toFixed(2)}</span>
          <span style="font-size:0.7rem; color:var(--primary); display:block;">View QR</span>
        </div>
      </div>
    `;
  }).join("");
}

async function loadInvoiceDetailsForReceipt(invoiceId) {
  try {
    const res = await fetch(`/api/billing/${invoiceId}`);
    if (res.ok) {
      const data = await res.json();
      
      // The details route includes a payload with medicines, let's decode it
      let qrPayload;
      try {
        qrPayload = JSON.parse(data.qr_payload);
      } catch (e) {
        qrPayload = { medicines: [] };
      }
      
      const receiptData = {
        invoice_number: data.invoice_number,
        total_amount: data.total_amount,
        qr_image_url: `/api/billing/${data.id}/qr`,
        items: qrPayload.medicines.map(m => ({
          name: m.name,
          quantity: m.quantity,
          line_total: m.line_total || (m.unit_price * m.quantity),
          batch: m.batch,
          expiry: m.expiry,
          dosage: m.dosage
        }))
      };
      
      // Update receipt text
      document.getElementById("bill-patient-name").value = data.patient_name;
      showReceipt(receiptData);
    }
  } catch (e) {
    console.error("Failed to load invoice details:", e);
  }
}
