# RailFlow — Train Seat Booking System Using Python Data Structures

> **Chennai ⇄ Bangalore Route (10 Total Seats)**  
> Academic Demonstration for M.Sc. Data Science Viva & Practical Examination  
> Built with **Python (Flask)**, **collections.deque (FIFO Queue)**, **Python List (Array)**, **HTML5/CSS3**, and configured for **Vercel Serverless Deployment**.

---

## 1. Project Overview

**RailFlow** is a complete, full-stack train reservation and waiting-list management system designed specifically for academic demonstration. The train operates between **Chennai and Bangalore** with a strict total capacity of **10 confirmed passenger seats**.

The core system logic, seat allocation algorithm, passenger searching, cancellation routines, and FIFO waiting-list promotion are implemented **entirely in Python**. The client-side JavaScript is strictly restricted to event listening, asynchronous API fetch calls, and DOM rendering.

---

## 2. Theoretical Breakdown: Python Data Structures Used

This project directly demonstrates four fundamental Data Structures & Algorithms concepts required for an M.Sc. Data Science curriculum:

### A. Python List (Fixed-Size Array Representation)
* **Variable:** `self.seats = [None] * 10`
* **Purpose:** Represents the 10 physical coach seats (Seat 1 through Seat 10).
* **Seat Allocation Algorithm:**
  1. Performs a linear scan $O(n)$ across the list (`range(10)`) to locate the first vacant slot (`None`).
  2. If found at index `i`, Seat number `i + 1` is assigned to the passenger.
  3. The passenger object is stored at `self.seats[i]`.
* **Direct Indexing:** $O(1)$ constant time lookup when accessing seat statuses.

### B. FIFO Queue (`collections.deque`)
* **Variable:** `self.waiting_queue = collections.deque()`
* **Purpose:** Manages passengers who book after all 10 seats are occupied.
* **Enqueue Operation ($O(1)$):**
  - When a booking arrives and all 10 seats are full, the passenger is added to the rear of the queue using `self.waiting_queue.append(passenger)`.
* **Dequeue Operation ($O(1)$):**
  - When any confirmed seat is released, the earliest waiting passenger is removed from the front of the queue using `self.waiting_queue.popleft()`.
* **Queue Fairness:** Strict First-In, First-Out (FIFO) discipline guarantees that the passenger who joined earliest is promoted first.

### C. Linear Searching
* **Operation:** Search by unique `Passenger ID` (e.g. `P001`, `P007`, `P011`).
* **Algorithm:**
  1. First searches the confirmed `self.seats` list ($O(10) = O(1)$).
  2. If not found in confirmed seats, searches sequentially through the `self.waiting_queue` ($O(k)$ where $k$ is the queue length).

### D. Deletion & Automatic FIFO Promotion
* **When a Confirmed Passenger Cancels:**
  1. The passenger's seat index is cleared: `self.seats[index] = None`.
  2. The system checks `len(self.waiting_queue) > 0`.
  3. If true, the front passenger is dequeued via `promoted = self.waiting_queue.popleft()`.
  4. The freed seat number is assigned to `promoted.seat`.
  5. The promoted passenger is placed directly into the seat: `self.seats[index] = promoted`.
  6. The dashboard updates immediately, displaying an alert identifying the promoted passenger and newly assigned seat number.
  7. If the queue is empty, the seat remains available (Green).
* **When a Waiting Passenger Cancels:**
  1. The specific passenger is removed from the deque.
  2. All remaining waiting passengers maintain their relative FIFO order and their queue positions advance automatically.

---

## 3. Project Structure

```text
Train reservation waitlist/
│
├── train_system.py          # Core Python Data Structures Engine (List, Deque, Search, Promotion)
├── app.py                   # Flask Web Application & REST API Endpoints
├── requirements.txt         # Production Python dependencies (Flask, Werkzeug)
├── vercel.json              # Vercel Serverless routing configuration
│
├── api/
│   └── index.py             # Serverless WSGI entry point for @vercel/python
│
├── templates/
│   └── index.html           # Responsive HTML5 Railway Dashboard
│
├── static/
│   ├── css/
│   │   └── style.css        # Responsive CSS3 styling (Train coach, green/red seats, badges)
│   └── js/
│       └── main.js          # Minimal event listener and DOM rendering (NO booking/queue logic)
│
├── test_system.py           # Python Data Structures unit test suite
└── test_flask_app.py        # End-to-end HTTP integration test suite
```

---

## 4. Local Installation & Execution

### Prerequisites
* Python 3.9+ (Python 3.10, 3.11, 3.12, 3.13, 3.14, 3.15 supported)
* `pip`

### Step 1: Clone or Extract the Project
```bash
cd "Train reservation waitlist"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Test Suites
Run the core data structure unit tests:
```bash
python test_system.py
```

Run the Flask integration test suite:
```bash
python test_flask_app.py
```

### Step 4: Start the Flask Web Server
```bash
python app.py
```
Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## 5. Test Cases & Verification Results

All 12 mandatory testing scenarios specified in Section 14 have been verified:

| # | Test Scenario Description | Expected Outcome | Result |
|---|---|---|:---:|
| 1 | Initial State | All 10 seats are Available (Green). Confirmed: 0, Waiting: 0. | **PASSED** |
| 2 | First Booking | Assigns Seat 1, marks it Occupied (Red), assigns ID `P001`. | **PASSED** |
| 3 | Book Passengers 2–10 | Assigns remaining Seats 2–10 in order; confirmed count reaches 10. | **PASSED** |
| 4 | Available Count at Capacity | Available seat count drops to exactly 0 when 10 seats are occupied. | **PASSED** |
| 5 | 11th Booking | All seats full; passenger enters Waiting Queue at Position 1 (`P011`). | **PASSED** |
| 6 | Additional Waitlisted Bookings | Passengers enter queue sequentially (Position 2, Position 3, etc.). | **PASSED** |
| 7 | Confirmed Cancellation + Promotion | Cancelling confirmed passenger immediately promotes FIFO Position 1 passenger into released seat. | **PASSED** |
| 8 | Waitlist Passenger Cancellation | Cancelling a waiting passenger removes only that entry; subsequent positions update. | **PASSED** |
| 9 | Unique Sequential IDs | Passenger IDs increment (`P001`, `P002`...) without collisions. | **PASSED** |
| 10 | System Reset | Confirms dialog, clears all seats, empties queue, resets next ID to `P001`. | **PASSED** |
| 11 | Responsive Layout | Form, 10-seat coach grid, tables, and modals adapt to desktop, tablet, and mobile. | **PASSED** |
| 12 | Serverless Compatibility | Functions correctly on serverless / Vercel with JSON state management. | **PASSED** |

---

## 6. Vercel Deployment Guide

### Option A: Deploy via Vercel CLI
1. Open a terminal in the project directory:
   ```bash
   vercel
   ```
2. Log in when prompted (or pass your token with `--token <YOUR_TOKEN>`).
3. Accept the default configuration:
   - **Set up and deploy?** `yes`
   - **Which scope?** `<your-account>`
   - **Link to existing project?** `no`
   - **What's your project's name?** `railflow-train-booking`
   - **In which directory is your code located?** `./`
4. Deploy to production:
   ```bash
   vercel --prod
   ```

### Option B: Deploy via GitHub + Vercel Dashboard (Recommended)
1. Push this directory to a new repository on [GitHub](https://github.com/).
2. Log in to [vercel.com](https://vercel.com/) and click **"Add New Project"**.
3. Select your GitHub repository.
4. Leave **Framework Preset** as **Other**.
5. Click **"Deploy"**. Vercel will automatically detect `api/index.py` and `@vercel/python` via `vercel.json` and deploy a live public URL!

### Serverless Persistence Architecture
On serverless runtimes (like AWS Lambda under Vercel), each request may be handled by different ephemeral container instances. RailFlow implements:
* File-backed atomic synchronization at `/tmp/railflow_train_state.json` (writable in serverless).
* Memory cache synchronization inside `TrainReservationSystem`.
* Optional remote key-value / database integration support via `DATABASE_URL` or Redis if scaling across multi-region serverless clusters.

---

## 7. Viva & Academic Q&A Quick Guide

* **Q: Why use `collections.deque` instead of a Python `list` for the waiting queue?**  
  *A:* In a Python standard list, `list.pop(0)` takes $O(n)$ linear time because all remaining elements must shift one position to the left in memory. In contrast, `collections.deque` is implemented as a doubly linked list of fixed-size blocks, making `popleft()` and `append()` true $O(1)$ constant-time operations. This makes it ideal for a FIFO queue.

* **Q: How does the system guarantee the first passenger is never waitlisted?**  
  *A:* The allocation algorithm first performs a linear check on `self.seats`. Only if `first_free_index == -1` (meaning all indices 0 through 9 contain confirmed passengers) will the system route the passenger into `waiting_queue.append()`.

* **Q: How does automatic FIFO promotion work on cancellation?**  
  *A:* When a confirmed passenger cancels, their seat index `i` is set to `None`. The system checks `if len(self.waiting_queue) > 0`. If true, it calls `promoted = self.waiting_queue.popleft()`, assigns `promoted.seat = i + 1`, and inserts the passenger directly into `self.seats[i]`.
