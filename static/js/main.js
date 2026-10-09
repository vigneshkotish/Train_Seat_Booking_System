/**
 * RailFlow — Train Seat Booking System Client Interaction Controller
 *
 * NOTE: As per academic requirements, all core business logic (Seat allocation,
 * FIFO queue management, collections.deque operations, searching, deletion,
 * and waitlist promotion) is executed EXCLUSIVELY on the Python Flask backend.
 * This script only handles UI events, asynchronous API calls, and DOM rendering.
 */

// Helper selector
const $ = (id) => document.getElementById(id);

// Notification banner management
let alertTimer = null;
function showAlert(message, type = "success") {
  const banner = $("alertBanner");
  const icon = $("alertIcon");
  const text = $("alertText");

  banner.className = `alert-banner ${type}`;
  text.textContent = message;

  if (type === "success") icon.textContent = "✓";
  else if (type === "warning") icon.textContent = "⏱";
  else icon.textContent = "✕";

  clearTimeout(alertTimer);
  alertTimer = setTimeout(() => {
    banner.className = "alert-banner hidden";
  }, 5000);
}

$("alertCloseBtn").addEventListener("click", () => {
  $("alertBanner").className = "alert-banner hidden";
  clearTimeout(alertTimer);
});

// HTML escaping to prevent XSS
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str).replace(/[&<>"']/g, (match) => {
    return {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[match];
  });
}

// -----------------------------------------------------------------------------
// DOM Rendering (Reflects Python Backend State)
// -----------------------------------------------------------------------------
function renderDashboard(data) {
  if (!data) return;

  // 1. Update Statistics Cards (Always 10 seats total)
  $("statTotal").textContent = data.total_seats || 10;
  $("statAvailable").textContent = data.available_count ?? 10;
  $("statConfirmed").textContent = data.confirmed_count ?? 0;
  $("statWaiting").textContent = data.waiting_count ?? 0;

  // 2. Next Auto-generated Passenger ID Pill
  if (data.next_id) {
    $("nextIdDisplay").textContent = data.next_id;
  }

  // 3. Render 10-Seat Availability Visual Grid
  const seatGrid = $("seatGrid");
  seatGrid.innerHTML = "";

  (data.seats || []).forEach((s) => {
    const isOccupied = s.status === "Occupied";
    const seatEl = document.createElement("div");
    seatEl.className = `seat-box ${isOccupied ? "occupied" : "available"}`;

    let passengerHtml = "";
    if (isOccupied && s.passenger) {
      passengerHtml = `
        <div class="seat-passenger-info">
          <div class="seat-pname" title="${escapeHtml(s.passenger.name)}">${escapeHtml(s.passenger.name)}</div>
          <div class="seat-pid">${escapeHtml(s.passenger.id)} · Age ${escapeHtml(s.passenger.age)}</div>
        </div>
      `;
    }

    seatEl.innerHTML = `
      <div class="seat-number-tag">Seat ${s.seat_number}</div>
      <span class="seat-status-tag">${isOccupied ? "Occupied" : "Available"}</span>
      ${passengerHtml}
    `;

    seatGrid.appendChild(seatEl);
  });

  // 4. Render Confirmed Passengers Table
  const confirmedList = data.confirmed_passengers || [];
  const tbody = $("confirmedTableBody");
  const emptyConfirmed = $("confirmedEmptyState");
  $("confirmedBadge").textContent = `${confirmedList.length} / 10 Confirmed`;

  tbody.innerHTML = "";
  if (confirmedList.length === 0) {
    emptyConfirmed.style.display = "block";
  } else {
    emptyConfirmed.style.display = "none";
    confirmedList.forEach((p) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><span class="seat-badge">Seat ${p.seat}</span></td>
        <td><span class="pid-badge">${escapeHtml(p.id)}</span></td>
        <td><strong>${escapeHtml(p.name)}</strong></td>
        <td>${escapeHtml(p.age)}</td>
        <td><span class="status-confirmed-tag">● Confirmed</span></td>
        <td class="td-action">
          <button type="button" class="btn-action-cancel" data-id="${p.id}" onclick="handleCancel('${p.id}')">
            Cancel
          </button>
        </td>
      `;
      tbody.appendChild(row);
    });
  }

  // 5. Render FIFO Waiting Queue
  const waitingList = data.waiting_passengers || [];
  const queueContainer = $("queueContainer");
  const emptyQueue = $("queueEmptyState");
  $("queueBadge").textContent = `${waitingList.length} in Queue`;

  queueContainer.innerHTML = "";
  if (waitingList.length === 0) {
    emptyQueue.style.display = "block";
  } else {
    emptyQueue.style.display = "none";
    waitingList.forEach((p) => {
      const isFirst = p.position === 1;
      const card = document.createElement("div");
      card.className = "queue-card-item";
      card.innerHTML = `
        <div class="queue-pos-badge" title="FIFO Position ${p.position}">${p.position}</div>
        <div class="queue-info">
          <div class="queue-title-row">
            <span class="queue-pname">${escapeHtml(p.name)}</span>
            ${isFirst ? '<span class="queue-first-pill">Next in line</span>' : ""}
          </div>
          <div class="queue-meta-row">
            <span>ID: <strong class="pid-badge" style="font-size:0.6875rem;">${escapeHtml(p.id)}</strong></span>
            <span>Age: ${escapeHtml(p.age)}</span>
            <span>Status: Waiting List</span>
          </div>
        </div>
        <button type="button" class="btn-action-cancel" onclick="handleCancel('${p.id}')" title="Remove from waiting queue">
          Remove
        </button>
      `;
      queueContainer.appendChild(card);
    });
  }
}

// -----------------------------------------------------------------------------
// Backend API Communication
// -----------------------------------------------------------------------------
async function refreshDashboard() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) throw new Error("Failed to fetch train status.");
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.error("Status fetch error:", err);
  }
}

// 1. Booking submission
$("bookingForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const nameInput = $("passengerName");
  const ageInput = $("passengerAge");
  const submitBtn = $("bookSubmitBtn");

  const name = nameInput.value.trim();
  const age = ageInput.value.trim();

  // Basic client check
  if (!name || !age) {
    showAlert("Please enter both passenger name and age.", "error");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = "<span>Allocating...</span>";

  try {
    const res = await fetch("/api/book", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, age: Number(age) }),
    });

    const data = await res.json();

    if (res.ok && data.success) {
      const alertType = data.status === "CONFIRMED" ? "success" : "warning";
      showAlert(data.message, alertType);
      nameInput.value = "";
      ageInput.value = "";
      nameInput.focus();
      await refreshDashboard();
    } else {
      showAlert(data.error || "Booking failed. Please try again.", "error");
    }
  } catch (err) {
    showAlert("Network error during booking. Please try again.", "error");
    console.error(err);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = "<span>Confirm & Allocate Seat</span><span class=\"btn-arrow\">→</span>";
  }
});

// 2. Cancellation (both confirmed & waiting passengers)
async function handleCancel(passengerId) {
  if (!passengerId) return;

  try {
    const res = await fetch("/api/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passenger_id: passengerId }),
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showAlert(data.message, "success");
      await refreshDashboard();
    } else {
      showAlert(data.error || "Cancellation failed.", "error");
    }
  } catch (err) {
    showAlert("Network error during cancellation.", "error");
    console.error(err);
  }
}
window.handleCancel = handleCancel;

// 3. Cancel by ID Modal
const cancelModal = $("cancelModal");
const openCancelModalBtn = $("openCancelModalBtn");
const closeCancelModalBtn = $("closeCancelModalBtn");
const cancelModalDismissBtn = $("cancelModalDismissBtn");
const cancelModalForm = $("cancelModalForm");
const cancelIdInput = $("cancelPassengerId");

function showCancelModal() {
  cancelIdInput.value = "";
  cancelModal.classList.remove("hidden");
  cancelIdInput.focus();
}

function hideCancelModal() {
  cancelModal.classList.add("hidden");
}

openCancelModalBtn.addEventListener("click", showCancelModal);
closeCancelModalBtn.addEventListener("click", hideCancelModal);
cancelModalDismissBtn.addEventListener("click", hideCancelModal);

cancelModalForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const idToCancel = cancelIdInput.value.trim().toUpperCase();
  if (!idToCancel) {
    showAlert("Please enter a valid Passenger ID.", "error");
    return;
  }
  hideCancelModal();
  await handleCancel(idToCancel);
});

// 4. Reset System Modal
const resetModal = $("resetModal");
const resetBtn = $("resetBtn");
const closeResetModalBtn = $("closeResetModalBtn");
const dismissResetBtn = $("dismissResetBtn");
const confirmResetBtn = $("confirmResetBtn");

function showResetModal() {
  resetModal.classList.remove("hidden");
}

function hideResetModal() {
  resetModal.classList.add("hidden");
}

resetBtn.addEventListener("click", showResetModal);
closeResetModalBtn.addEventListener("click", hideResetModal);
dismissResetBtn.addEventListener("click", hideResetModal);

confirmResetBtn.addEventListener("click", async () => {
  hideResetModal();
  try {
    const res = await fetch("/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showAlert(data.message, "success");
      await refreshDashboard();
    } else {
      showAlert("Failed to reset system.", "error");
    }
  } catch (err) {
    showAlert("Network error during reset.", "error");
    console.error(err);
  }
});

// Close modals when clicking backdrop
window.addEventListener("click", (e) => {
  if (e.target === cancelModal) hideCancelModal();
  if (e.target === resetModal) hideResetModal();
});

// Close modals on Escape key
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    hideCancelModal();
    hideResetModal();
  }
});

// -----------------------------------------------------------------------------
// Initial Boot
// -----------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  if (window.__INITIAL_STATE__) {
    renderDashboard(window.__INITIAL_STATE__);
  } else {
    refreshDashboard();
  }
});
