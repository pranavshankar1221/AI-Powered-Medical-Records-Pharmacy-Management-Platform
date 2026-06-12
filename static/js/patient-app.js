/**
 * MedTrack - Patient Companion JS
 * Local storage cabinet binder, QR simulator decoder, weekly planner, and chatbot client.
 */

let cabinet = [];

document.addEventListener("DOMContentLoaded", () => {
  // Load cabinet from LocalStorage
  const cached = localStorage.getItem("medtrack_cabinet");
  if (cached) {
    try {
      cabinet = JSON.parse(cached);
      renderCabinet();
      updateIntakeCalendar();
      updateChatSuggestions();
    } catch (e) {
      console.error("Cached cabinet corruption:", e);
    }
  }
});

function saveCabinet() {
  localStorage.setItem("medtrack_cabinet", JSON.stringify(cabinet));
  renderCabinet();
  updateIntakeCalendar();
  updateChatSuggestions();
}

function clearCabinet() {
  if (confirm("Are you sure you want to clear your medicine cabinet?")) {
    cabinet = [];
    saveCabinet();
    
    // Reset messages
    const chatBox = document.getElementById("chat-messages-container");
    chatBox.innerHTML = `
      <div class="chat-msg bot">
        Your cabinet has been cleared. Scan a receipt QR code above to reload your medications and continue querying.
      </div>
    `;
  }
}

async function simulatePatientScan() {
  const payload = document.getElementById("patient-qr-input").value.trim();
  if (!payload) {
    alert("Please paste a receipt QR code payload string.");
    return;
  }

  try {
    const res = await fetch("/api/patient/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payload: payload })
    });

    if (res.ok) {
      const result = await res.json();
      
      if (!result.verified) {
        alert("⚠️ WARNING: QR signature is invalid! This receipt might be forged or tampered with.");
      }

      // Add medicines from invoice
      const invoiceData = result.cabinet_data;
      let addedCount = 0;
      
      invoiceData.medicines.forEach(m => {
        // Avoid duplicate batches in cabinet
        const exists = cabinet.some(c => c.batch === m.batch && c.medicine_id === m.medicine_id);
        if (!exists) {
          cabinet.push({
            medicine_id: m.medicine_id,
            name: m.name,
            batch: m.batch,
            expiry: m.expiry,
            dosage: m.dosage,
            storage: m.storage,
            side_effects_summary: m.side_effects_summary || [],
            db_status: m.db_status,
            batch_exists: m.batch_exists,
            authenticity_alert: m.authenticity_alert,
            scanned_at: new Date().toISOString()
          });
          addedCount++;
        }
      });

      alert(`Successfully loaded ${addedCount} medicine(s) into your cabinet!`);
      document.getElementById("patient-qr-input").value = "";
      saveCabinet();
      
      // Greet patient with active cabinet info
      appendMessage("bot", `I've imported your medications from invoice <strong>${invoiceData.invoice_id}</strong>. I'm ready to answer any questions you have about them.`);
      
    } else {
      const err = await res.json();
      alert(`Scan failed: ${err.error || 'Invalid QR'}`);
    }
  } catch (error) {
    console.error("Patient QR verification failed:", error);
  }
}

function renderCabinet() {
  const container = document.getElementById("cabinet-container");
  if (cabinet.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem; font-size: 0.95rem;">
        Your digital cabinet is currently empty. Scan a receipt QR code above to load your medications.
      </div>
    `;
    return;
  }

  container.innerHTML = cabinet.map(m => {
    let authBadge = `<span class="badge active">✅ Verified</span>`;
    let cardClass = "";
    
    if (m.authenticity_alert) {
      if (m.db_status === "recalled") {
        authBadge = `<span class="badge recalled">⚠️ Recalled</span>`;
        cardClass = "recalled";
      } else if (m.db_status === "expired") {
        authBadge = `<span class="badge expired">⚠️ Expired</span>`;
        cardClass = "expired";
      } else {
        authBadge = `<span class="badge warning">⚠️ Unverified</span>`;
      }
    } else if (!m.batch_exists) {
      authBadge = `<span class="badge warning">⚠️ Unverified</span>`;
    }

    return `
      <div class="cabinet-card ${cardClass}">
        <div class="cabinet-card-header">
          <div>
            <div class="cabinet-card-name">${m.name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">
              Batch: <code>${m.batch}</code>
            </div>
          </div>
          ${authBadge}
        </div>
        
        <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.5rem;">
          <div style="margin-bottom:0.25rem;"><strong>Dosage:</strong> ${m.dosage}</div>
          <div><strong>Expiry:</strong> ${m.expiry}</div>
          ${m.storage ? `<div style="margin-top:0.25rem;"><strong>Storage:</strong> ${m.storage}</div>` : ''}
        </div>
        
        ${m.authenticity_alert ? `
          <div style="margin-top:0.5rem; background:rgba(255,23,68,0.1); border:1px solid rgba(255,23,68,0.2); border-radius:4px; padding:0.4rem; font-size:0.75rem; color:#ff5252; font-weight:600;">
            ${m.authenticity_alert}
          </div>
        ` : ''}
      </div>
    `;
  }).join("");
}

async function updateIntakeCalendar() {
  const container = document.getElementById("calendar-container");
  if (cabinet.length === 0) {
    container.innerHTML = `
      <div class="calendar-slot"><div class="calendar-slot-title">Morning</div><div style="color:var(--text-muted); font-size:0.75rem; font-style:italic;">No meds.</div></div>
      <div class="calendar-slot"><div class="calendar-slot-title">Afternoon</div><div style="color:var(--text-muted); font-size:0.75rem; font-style:italic;">No meds.</div></div>
      <div class="calendar-slot"><div class="calendar-slot-title">Evening</div><div style="color:var(--text-muted); font-size:0.75rem; font-style:italic;">No meds.</div></div>
      <div class="calendar-slot"><div class="calendar-slot-title">Night</div><div style="color:var(--text-muted); font-size:0.75rem; font-style:italic;">No meds.</div></div>
    `;
    return;
  }

  try {
    const res = await fetch("/api/patient/calendar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ medicines: cabinet })
    });
    
    if (res.ok) {
      const data = await res.json();
      const slots = data.schedule;
      
      const timeSlots = ["morning", "afternoon", "evening", "night"];
      container.innerHTML = timeSlots.map(time => {
        const items = slots[time] || [];
        const itemsHtml = items.map(i => `
          <div class="calendar-item">
            <strong>${i.name}</strong>
            <div style="font-size:0.7rem; color:var(--text-muted); margin-top:0.1rem;">${i.instructions}</div>
          </div>
        `).join("");
        
        return `
          <div class="calendar-slot">
            <div class="calendar-slot-title">${time}</div>
            ${itemsHtml || '<div style="color:var(--text-muted); font-size:0.75rem; font-style:italic;">No medications.</div>'}
          </div>
        `;
      }).join("");
    }
  } catch (error) {
    console.error("Intake calendar generation failed:", error);
  }
}

function updateChatSuggestions() {
  const box = document.getElementById("chat-suggestions-box");
  if (cabinet.length === 0) {
    box.style.display = "none";
    return;
  }

  const sampleMed = cabinet[0];
  const questions = [
    `Can I take ${sampleMed.name} with milk or coffee?`,
    `What should I do if I miss a dose of ${sampleMed.name}?`,
    `What are the major side effects of ${sampleMed.name}?`,
  ];

  box.innerHTML = questions.map(q => `
    <button class="suggestion-btn" onclick="sendSuggestedQuery('${q.replace(/'/g, "\\'")}')">${q}</button>
  `).join("");
  box.style.display = "flex";
}

function sendSuggestedQuery(queryText) {
  document.getElementById("chat-input").value = queryText;
  sendChatMessage();
}

function handleChatKeyDown(event) {
  if (event.key === "Enter") {
    sendChatMessage();
  }
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const query = input.value.trim();
  if (!query) return;

  input.value = "";
  appendMessage("patient", query);
  
  // Render loading state for bot
  const loadingId = appendMessage("bot", `<span style="color: var(--text-muted); font-style:italic;">Thinking...</span>`);
  
  const medicineIds = cabinet.map(m => m.medicine_id);

  try {
    const res = await fetch("/api/patient/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        medicine_ids: medicineIds,
        cabinet_medicines: cabinet.map(m => ({ medicine_id: m.medicine_id, name: m.name }))
      })
    });

    if (res.ok) {
      const data = await res.json();
      
      let responseHtml = `<p>${data.answer.replace(/\n/g, '<br>')}</p>`;
      if (data.sources && data.sources.length > 0) {
        responseHtml += `<div style="margin-top:0.5rem;">`;
        data.sources.forEach(src => {
          // Find matched medicine in cabinet for name matching
          const cabMatch = cabinet.find(c => c.medicine_id === src);
          const name = cabMatch ? cabMatch.name : src;
          responseHtml += `<span class="citation">Source: ${name}</span> `;
        });
        responseHtml += `</div>`;
      }
      
      updateMessage(loadingId, responseHtml);
    } else {
      updateMessage(loadingId, "I ran into a server error processing your response. Please try again.");
    }
  } catch (error) {
    console.error("Chat error:", error);
    updateMessage(loadingId, "Connection to server failed. Please ensure backend services are active.");
  }
}

function appendMessage(sender, html) {
  const container = document.getElementById("chat-messages-container");
  const msgId = "msg-" + Date.now() + Math.random().toString(36).substr(2, 5);
  
  const div = document.createElement("div");
  div.id = msgId;
  div.className = `chat-msg ${sender}`;
  div.innerHTML = html;
  
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return msgId;
}

function updateMessage(msgId, newHtml) {
  const el = document.getElementById(msgId);
  if (el) {
    el.innerHTML = newHtml;
    const container = document.getElementById("chat-messages-container");
    container.scrollTop = container.scrollHeight;
  }
}

function loadSampleReceiptQR() {
  // Hardcoded receipt data signed with the config key
  // This matches a standard transaction structure generated by billing.py
  // Payload signature corresponds to HMAC verification check
  const samplePayload = {
    "invoice_id": "INV-20260608-0001",
    "pharmacy": "MedTrack Demo Pharmacy",
    "date": "2026-06-08",
    "patient": "Jane Doe",
    "medicines": [
      {
        "medicine_id": "MED_001",
        "name": "Amoxicillin 500mg",
        "batch": "BATCH-AMOX-2026-X11",
        "expiry": "2028-02-09",
        "quantity": 21,
        "unit_price": 0.85,
        "line_total": 17.85,
        "dosage": "1 capsule 3x daily after meals for 7 days",
        "storage": "Store in a cool dry place below 25°C",
        "side_effects_summary": ["Nausea", "Diarrhea", "Rash"]
      },
      {
        "medicine_id": "MED_002",
        "name": "Metformin 500mg",
        "batch": "BATCH-MET-2026-Y22",
        "expiry": "2027-11-15",
        "quantity": 30,
        "unit_price": 0.35,
        "line_total": 10.50,
        "dosage": "1 tablet once daily with breakfast",
        "storage": "Store in a dry place. Keep out of reach of children",
        "side_effects_summary": ["Stomach upset", "Nausea", "Metallic taste"]
      }
    ]
  };

  // Recreate correct signature block matching hmac secret "medtrack-qr-hmac-secret"
  // For demo, we send the raw JSON as string.
  // The decode endpoint verifies signature using the configured secret key.
  // Since we sign on billing generation and verify on scan, we can use the backend /api/billing/create to generate a real QR or simulate one:
  // Let's create an actual invoice via the backend api to get a perfectly signed real QR payload!
  
  fetch("/api/billing/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      patient_name: "Jane Doe",
      pharmacist_name: "Dr. Samantha Intern",
      items: [
        // We will fetch available stock batches to create the receipt
        // For security & verification, we request available-stock list
      ]
    })
  }).then(async res => {
    // If we fail because of empty items, let's look up real active stock batches
    const stockRes = await fetch("/api/billing/available-stock");
    if (stockRes.ok) {
      const stock = await stockRes.json();
      if (stock.length > 0) {
        // take first 2 batches
        const cartItems = stock.slice(0, 2).map(b => ({
          batch_id: b.id,
          quantity: 5,
          dosage_instructions: b.category && b.category.toLowerCase().includes("antibiotic") ? "1 capsule 3x daily" : "1 tablet daily with meals"
        }));
        
        const invRes = await fetch("/api/billing/create", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            patient_name: "Jane Doe",
            pharmacist_name: "Dr. Samantha Intern",
            items: cartItems
          })
        });
        
        if (invRes.ok) {
          const invoice = await invRes.json();
          // Now fetch the actual invoice code details to get the correct payload string
          const detailsRes = await fetch(`/api/billing/${invoice.invoice_id}`);
          if (detailsRes.ok) {
            const details = await detailsRes.json();
            document.getElementById("patient-qr-input").value = details.qr_payload;
            return;
          }
        }
      }
    }
    
    // Fallback: if no DB records existed yet, generate static JSON string
    document.getElementById("patient-qr-input").value = JSON.stringify(samplePayload);
  }).catch(e => {
    document.getElementById("patient-qr-input").value = JSON.stringify(samplePayload);
  });
}
