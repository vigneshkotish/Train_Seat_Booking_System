"""
RailFlow - Train Seat Booking System (Flask Web Application)
Academic Demonstration for M.Sc. Data Science:
Chennai -> Bangalore (10 Seats) with FIFO Waiting Queue.

This Flask application serves the web dashboard and handles REST API endpoints.
All booking, seat allocation, searching, cancellation, FIFO queueing, and
promotion logic is executed strictly on the Python backend via TrainReservationSystem.
"""

import os
from flask import Flask, render_template, request, jsonify
from train_system import TrainReservationSystem

# Initialize Flask application
# Explicitly configure template and static folders
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "railflow-secret-key-msc-ds-2025")

# Initialize the Python core reservation engine
system = TrainReservationSystem()


@app.route("/")
def index():
    """Renders the main RailFlow train seat reservation dashboard."""
    status_data = system.get_status()
    return render_template("index.html", initial_data=status_data)


@app.route("/api/status", methods=["GET"])
def get_status():
    """
    Returns current train status:
      - 10 total seats status
      - Confirmed passenger list
      - FIFO waiting list queue
      - Counts of available, confirmed, and waiting passengers
    """
    return jsonify(system.get_status())


@app.route("/api/book", methods=["POST"])
def book_passenger():
    """
    Books a passenger.
    Receives JSON payload: { "name": string, "age": integer }
    Executes Python seat allocation or FIFO queue enqueue.
    """
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "")
    age = data.get("age", None)

    result = system.book_passenger(name, age)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.route("/api/cancel", methods=["POST"])
def cancel_passenger():
    """
    Cancels a booking by Passenger ID (e.g. 'P003').
    Executes Python seat release and automatic FIFO waiting-list promotion.
    Supports both confirmed and waiting-list passengers.
    """
    data = request.get_json(force=True, silent=True) or {}
    passenger_id = data.get("passenger_id", "")

    result = system.cancel_passenger(passenger_id)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.route("/api/reset", methods=["POST"])
def reset_system():
    """
    Resets the reservation system:
      - Clears all confirmed seats
      - Clears FIFO waiting queue
      - Resets Passenger ID counter to P001
    """
    result = system.reset_system()
    return jsonify(result), 200


if __name__ == "__main__":
    # Local development server
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting RailFlow Train Seat Booking System on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
