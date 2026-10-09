"""
RailFlow - Train Seat Booking System Core Engine
Academic Demonstration for M.Sc. Data Science:
Demonstrating Python Data Structures:
  1. Python List (Fixed-size seat slots, array indexing, linear search, element replacement)
  2. collections.deque (Genuine FIFO Queue for waiting-list passengers)
  3. Searching (Linear search by Passenger ID across confirmed array and waiting deque)
  4. Deletion & FIFO Promotion (Releasing seat and dequeuing earliest waiting passenger)
"""

from collections import deque
import json
import os
import re
from typing import Dict, Any, Optional, List


class Passenger:
    """
    Represents an individual passenger record.
    """
    def __init__(self, passenger_id: str, name: str, age: int, seat: Optional[int] = None):
        self.id = passenger_id
        self.name = name.strip()
        self.age = int(age)
        self.seat = seat  # Integer 1-10 if confirmed, None if on waiting list

    def to_dict(self) -> Dict[str, Any]:
        """Convert passenger object to serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "seat": self.seat,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Passenger":
        """Reconstruct passenger object from dictionary."""
        return cls(
            passenger_id=data["id"],
            name=data["name"],
            age=data["age"],
            seat=data.get("seat"),
        )


class TrainReservationSystem:
    """
    Train Reservation System for Chennai -> Bangalore route with 10 total seats.
    
    Data Structures Used:
      - self.seats: List of length 10.
          * Index 0 to 9 corresponds to Seat 1 to Seat 10.
          * None indicates an available seat.
          * Passenger instance indicates an occupied seat.
          * List operations demonstrated:
              - Fixed-size allocation: [None] * TOTAL_SEATS
              - Linear scan for first empty slot: O(n)
              - Direct index access / replacement: O(1)
      - self.waiting_queue: collections.deque.
          * Genuine FIFO (First-In, First-Out) Queue.
          * Enqueue operation: self.waiting_queue.append(passenger) -> O(1) time
          * Dequeue operation: self.waiting_queue.popleft() -> O(1) time
          * Strict FIFO ordering guarantees that the earliest waiting passenger
            is promoted first when any confirmed passenger cancels.
    """

    TOTAL_SEATS: int = 10
    ROUTE: str = "Chennai → Bangalore"

    def __init__(self, storage_path: Optional[str] = None):
        # Determine persistent storage location
        # On Vercel / serverless, /tmp is writable; locally, use current directory.
        if storage_path:
            self.storage_path = storage_path
        else:
            if os.environ.get("VERCEL"):
                self.storage_path = "/tmp/railflow_train_state.json"
            else:
                self.storage_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "railflow_train_state.json"
                )

        # Core Data Structures
        self.seats: List[Optional[Passenger]] = [None] * self.TOTAL_SEATS
        self.waiting_queue: deque[Passenger] = deque()
        self.next_id_counter: int = 1

        # Attempt to load persistent state if available
        self.load_state()

    # -------------------------------------------------------------------------
    # State Persistence (Handles Serverless Container Lifecycles)
    # -------------------------------------------------------------------------
    def load_state(self) -> None:
        """
        Loads reservation state from JSON file to maintain persistence across
        serverless executions while preserving Python Data Structure operations.
        """
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.next_id_counter = data.get("next_id_counter", 1)

            # Rebuild confirmed seats List
            raw_seats = data.get("seats", [])
            self.seats = [None] * self.TOTAL_SEATS
            for i in range(min(len(raw_seats), self.TOTAL_SEATS)):
                if raw_seats[i] is not None:
                    self.seats[i] = Passenger.from_dict(raw_seats[i])

            # Rebuild FIFO waiting deque
            raw_queue = data.get("waiting_queue", [])
            self.waiting_queue = deque(
                Passenger.from_dict(p) for p in raw_queue
            )
        except Exception as e:
            # If state file is corrupted, initialize fresh state
            self.seats = [None] * self.TOTAL_SEATS
            self.waiting_queue = deque()
            self.next_id_counter = 1

    def save_state(self) -> None:
        """
        Saves current Python data structures state to JSON storage.
        """
        try:
            data = {
                "next_id_counter": self.next_id_counter,
                "seats": [p.to_dict() if p else None for p in self.seats],
                "waiting_queue": [p.to_dict() for p in self.waiting_queue],
            }
            # Ensure target directory exists
            target_dir = os.path.dirname(self.storage_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            # Non-blocking if storage write fails
            pass

    # -------------------------------------------------------------------------
    # Helper & Validation Methods
    # -------------------------------------------------------------------------
    def _generate_passenger_id(self) -> str:
        """Generates sequential ID: P001, P002, etc."""
        pid = f"P{self.next_id_counter:03d}"
        self.next_id_counter += 1
        return pid

    @staticmethod
    def validate_inputs(name: str, age_val: Any) -> tuple[bool, str]:
        """
        Validates passenger name and age.
        Returns (is_valid, error_message).
        """
        if not name or not isinstance(name, str) or not name.strip():
            return False, "Passenger name cannot be blank."

        clean_name = name.strip()
        if len(clean_name) < 2:
            return False, "Passenger name must contain at least 2 characters."
        if len(clean_name) > 40:
            return False, "Passenger name must not exceed 40 characters."
        if not re.match(r"^[A-Za-z0-9\s.'-]+$", clean_name) or not any(c.isalpha() for c in clean_name):
            return False, "Passenger name must contain valid alphabetic characters."

        try:
            age = int(age_val)
        except (ValueError, TypeError):
            return False, "Age must be a valid integer."

        if age < 1 or age > 120:
            return False, "Age must be between 1 and 120 years."

        return True, ""

    # -------------------------------------------------------------------------
    # Core Operation 1: Booking a Passenger
    # -------------------------------------------------------------------------
    def book_passenger(self, name: str, age: int) -> Dict[str, Any]:
        """
        Book a passenger.
        Logic:
          1. Validate inputs.
          2. Generate unique sequential Passenger ID.
          3. Linear search in self.seats (Python List) for the lowest available index.
          4. If an available seat exists (index 0..9):
             - Allocate Seat (index + 1).
             - Update self.seats[index] = passenger.
             - Return Confirmed status.
          5. If all 10 seats are occupied:
             - Enqueue passenger into self.waiting_queue (collections.deque.append).
             - Return Waiting status with FIFO queue position.
        """
        # Reload latest state in case of concurrent serverless instances
        self.load_state()

        is_valid, err_msg = self.validate_inputs(name, age)
        if not is_valid:
            return {
                "success": False,
                "error": err_msg,
            }

        passenger_id = self._generate_passenger_id()
        clean_name = name.strip()
        int_age = int(age)

        # Python List Operation: Linear search for first vacant seat slot
        first_free_index = -1
        for i in range(self.TOTAL_SEATS):
            if self.seats[i] is None:
                first_free_index = i
                break

        if first_free_index != -1:
            # Seat available: Confirm booking
            seat_number = first_free_index + 1
            passenger = Passenger(passenger_id, clean_name, int_age, seat=seat_number)
            self.seats[first_free_index] = passenger
            self.save_state()

            return {
                "success": True,
                "status": "CONFIRMED",
                "passenger": passenger.to_dict(),
                "message": (
                    f"Booking Confirmed! {passenger.name} has been assigned "
                    f"Seat {seat_number}. Passenger ID: {passenger.id}."
                ),
            }
        else:
            # All 10 seats occupied: Enqueue in FIFO Waiting List
            passenger = Passenger(passenger_id, clean_name, int_age, seat=None)
            self.waiting_queue.append(passenger)  # FIFO Enqueue: O(1)
            queue_position = len(self.waiting_queue)
            self.save_state()

            return {
                "success": True,
                "status": "WAITING",
                "passenger": passenger.to_dict(),
                "queue_position": queue_position,
                "message": (
                    f"All 10 seats are occupied. {passenger.name} (ID: {passenger.id}) "
                    f"has been added to the FIFO Waiting List at Position {queue_position}."
                ),
            }

    # -------------------------------------------------------------------------
    # Core Operation 2: Cancellation & Automatic FIFO Promotion
    # -------------------------------------------------------------------------
    def cancel_passenger(self, passenger_id: str) -> Dict[str, Any]:
        """
        Cancel a booking using Passenger ID.
        Supports cancellation for both Confirmed passengers and Waiting passengers.

        Algorithms:
          Case A - Confirmed Passenger Cancellation:
            1. Linear Search through self.seats (Python List):
               Find index where self.seats[i].id == passenger_id.
            2. Deletion:
               Free seat: self.seats[i] = None.
            3. Automatic FIFO Waiting-List Promotion:
               Check if self.waiting_queue is not empty.
               If passengers are waiting:
                 - Dequeue earliest passenger: self.waiting_queue.popleft() (FIFO Dequeue: O(1))
                 - Assign the released seat number to promoted passenger.
                 - Insert promoted passenger into confirmed list: self.seats[i] = promoted.
                 - Return success message with promotion details.
               If queue is empty:
                 - Released seat remains available.
          
          Case B - Waiting-List Passenger Cancellation:
            1. Search inside self.waiting_queue (collections.deque).
            2. Deletion: Remove the matching passenger.
            3. All remaining waiting passengers preserve FIFO relative order and
               their positions are automatically adjusted.
        """
        self.load_state()

        if not passenger_id or not isinstance(passenger_id, str):
            return {"success": False, "error": "Invalid Passenger ID."}

        pid = passenger_id.strip().upper()

        # ---------------------------------------------------------------------
        # Step 1: Search in Confirmed Seats (Python List linear search)
        # ---------------------------------------------------------------------
        confirmed_index = -1
        cancelled_passenger: Optional[Passenger] = None

        for i, p in enumerate(self.seats):
            if p is not None and p.id == pid:
                confirmed_index = i
                cancelled_passenger = p
                break

        if confirmed_index != -1 and cancelled_passenger is not None:
            freed_seat_number = confirmed_index + 1
            self.seats[confirmed_index] = None  # Free the seat slot

            # -----------------------------------------------------------------
            # Step 2: Automatic FIFO Promotion
            # -----------------------------------------------------------------
            if len(self.waiting_queue) > 0:
                # FIFO Dequeue: popleft() retrieves earliest passenger in O(1)
                promoted_passenger = self.waiting_queue.popleft()
                promoted_passenger.seat = freed_seat_number
                self.seats[confirmed_index] = promoted_passenger
                self.save_state()

                return {
                    "success": True,
                    "type": "CONFIRMED_WITH_PROMOTION",
                    "cancelled": cancelled_passenger.to_dict(),
                    "promoted": promoted_passenger.to_dict(),
                    "seat_number": freed_seat_number,
                    "message": (
                        f"Cancellation Successful: Confirmed ticket for {cancelled_passenger.name} "
                        f"({cancelled_passenger.id}) on Seat {freed_seat_number} was cancelled. "
                        f"🎉 FIFO Promotion: {promoted_passenger.name} ({promoted_passenger.id}) "
                        f"from Waiting Position 1 has been automatically promoted to Seat {freed_seat_number}!"
                    ),
                }
            else:
                # Queue empty: seat becomes available
                self.save_state()
                return {
                    "success": True,
                    "type": "CONFIRMED_NO_PROMOTION",
                    "cancelled": cancelled_passenger.to_dict(),
                    "seat_number": freed_seat_number,
                    "message": (
                        f"Cancellation Successful: Confirmed ticket for {cancelled_passenger.name} "
                        f"({cancelled_passenger.id}) was cancelled. Seat {freed_seat_number} is now Available."
                    ),
                }

        # ---------------------------------------------------------------------
        # Step 3: Search in FIFO Waiting Queue (collections.deque search)
        # ---------------------------------------------------------------------
        queue_index = -1
        for idx, p in enumerate(self.waiting_queue):
            if p.id == pid:
                queue_index = idx
                break

        if queue_index != -1:
            # Python Deque Deletion: Rebuild deque without the cancelled passenger
            # preserving strict FIFO arrival order for all remaining passengers
            waiting_list = list(self.waiting_queue)
            removed_passenger = waiting_list.pop(queue_index)
            self.waiting_queue = deque(waiting_list)
            self.save_state()

            return {
                "success": True,
                "type": "WAITING_REMOVED",
                "cancelled": removed_passenger.to_dict(),
                "removed_position": queue_index + 1,
                "message": (
                    f"Waiting list entry for {removed_passenger.name} ({removed_passenger.id}) "
                    f"at Position {queue_index + 1} was successfully cancelled. "
                    f"Subsequent queue positions have been updated."
                ),
            }

        # Step 4: Passenger ID not found in either data structure
        return {
            "success": False,
            "error": f"Passenger ID '{pid}' was not found in confirmed seats or the waiting queue.",
        }

    # -------------------------------------------------------------------------
    # Core Operation 3: Reset System
    # -------------------------------------------------------------------------
    def reset_system(self) -> Dict[str, Any]:
        """
        Resets the entire system to its initial baseline:
          - Clears all confirmed seats in Python List.
          - Clears FIFO waiting queue deque.
          - Resets Passenger ID counter back to P001.
          - Updates persistent storage.
        """
        self.seats = [None] * self.TOTAL_SEATS
        self.waiting_queue.clear()
        self.next_id_counter = 1
        self.save_state()

        return {
            "success": True,
            "message": "System has been reset. All 10 seats are now available, and Passenger IDs reset to P001.",
        }

    # -------------------------------------------------------------------------
    # System Status / Query Method
    # -------------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Returns full state snapshot for dashboard rendering:
          - Route details & total seats (10)
          - Counts: available, confirmed, waiting
          - Visual layout seat list (1 to 10)
          - Confirmed passengers table list
          - Waiting queue list with FIFO positions (1, 2, 3...)
        """
        self.load_state()

        confirmed_list: List[Dict[str, Any]] = []
        seat_display_list: List[Dict[str, Any]] = []

        for i in range(self.TOTAL_SEATS):
            seat_num = i + 1
            passenger = self.seats[i]
            if passenger is not None:
                p_dict = passenger.to_dict()
                confirmed_list.append(p_dict)
                seat_display_list.append({
                    "seat_number": seat_num,
                    "status": "Occupied",
                    "passenger": p_dict,
                })
            else:
                seat_display_list.append({
                    "seat_number": seat_num,
                    "status": "Available",
                    "passenger": None,
                })

        # Process FIFO waiting queue with 1-based positions
        waiting_list: List[Dict[str, Any]] = []
        for idx, p in enumerate(self.waiting_queue):
            item = p.to_dict()
            item["position"] = idx + 1
            waiting_list.append(item)

        confirmed_count = len(confirmed_list)
        available_count = self.TOTAL_SEATS - confirmed_count
        waiting_count = len(waiting_list)

        return {
            "route": self.ROUTE,
            "total_seats": self.TOTAL_SEATS,
            "available_count": available_count,
            "confirmed_count": confirmed_count,
            "waiting_count": waiting_count,
            "seats": seat_display_list,
            "confirmed_passengers": confirmed_list,
            "waiting_passengers": waiting_list,
            "next_id": f"P{self.next_id_counter:03d}",
        }
