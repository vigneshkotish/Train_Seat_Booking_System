"""
Unit test suite for TrainReservationSystem.
Tests all data structures, FIFO waiting queue, promotion, searching, deletion, and reset.
"""

import unittest
import os
from train_system import TrainReservationSystem


class TestTrainReservationSystem(unittest.TestCase):
    def setUp(self):
        # Use an isolated test storage file
        self.test_storage = os.path.join(os.path.dirname(__file__), "test_state.json")
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)
        self.system = TrainReservationSystem(storage_path=self.test_storage)

    def tearDown(self):
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)

    def test_01_initial_state(self):
        """1. Initially, all 10 seats are available."""
        status = self.system.get_status()
        self.assertEqual(status["total_seats"], 10)
        self.assertEqual(status["available_count"], 10)
        self.assertEqual(status["confirmed_count"], 0)
        self.assertEqual(status["waiting_count"], 0)
        self.assertEqual(len(status["seats"]), 10)
        for s in status["seats"]:
            self.assertEqual(s["status"], "Available")
            self.assertIsNone(s["passenger"])

    def test_02_book_first_passenger(self):
        """2. Booking the first passenger assigns Seat 1."""
        res = self.system.book_passenger("Aravind Kumar", 24)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "CONFIRMED")
        self.assertEqual(res["passenger"]["id"], "P001")
        self.assertEqual(res["passenger"]["seat"], 1)

        status = self.system.get_status()
        self.assertEqual(status["available_count"], 9)
        self.assertEqual(status["confirmed_count"], 1)
        self.assertEqual(status["seats"][0]["status"], "Occupied")
        self.assertEqual(status["seats"][0]["passenger"]["id"], "P001")

    def test_03_book_10_passengers(self):
        """3 & 4. Booking passengers 2-10 assigns remaining seats. Available seats become 0."""
        for i in range(1, 11):
            res = self.system.book_passenger(f"Passenger {i}", 20 + i)
            self.assertTrue(res["success"])
            self.assertEqual(res["status"], "CONFIRMED")
            self.assertEqual(res["passenger"]["seat"], i)

        status = self.system.get_status()
        self.assertEqual(status["available_count"], 0)
        self.assertEqual(status["confirmed_count"], 10)
        self.assertEqual(status["waiting_count"], 0)

    def test_04_11th_and_further_passengers_enter_fifo_queue(self):
        """5 & 6. 11th passenger enters Waiting Position 1; additional passengers join queue in correct order."""
        for i in range(1, 11):
            self.system.book_passenger(f"Passenger {i}", 20 + i)

        # 11th passenger
        res11 = self.system.book_passenger("Waiting User 1", 30)
        self.assertTrue(res11["success"])
        self.assertEqual(res11["status"], "WAITING")
        self.assertEqual(res11["passenger"]["id"], "P011")
        self.assertEqual(res11["queue_position"], 1)

        # 12th passenger
        res12 = self.system.book_passenger("Waiting User 2", 31)
        self.assertTrue(res12["success"])
        self.assertEqual(res12["status"], "WAITING")
        self.assertEqual(res12["passenger"]["id"], "P012")
        self.assertEqual(res12["queue_position"], 2)

        # 13th passenger
        res13 = self.system.book_passenger("Waiting User 3", 32)
        self.assertTrue(res13["success"])
        self.assertEqual(res13["passenger"]["id"], "P013")
        self.assertEqual(res13["queue_position"], 3)

        status = self.system.get_status()
        self.assertEqual(status["waiting_count"], 3)
        self.assertEqual(status["waiting_passengers"][0]["id"], "P011")
        self.assertEqual(status["waiting_passengers"][0]["position"], 1)
        self.assertEqual(status["waiting_passengers"][1]["id"], "P012")
        self.assertEqual(status["waiting_passengers"][1]["position"], 2)
        self.assertEqual(status["waiting_passengers"][2]["id"], "P013")
        self.assertEqual(status["waiting_passengers"][2]["position"], 3)

    def test_05_cancellation_and_automatic_fifo_promotion(self):
        """7. Cancelling a confirmed passenger promotes the first waiting passenger into that seat."""
        for i in range(1, 11):
            self.system.book_passenger(f"Passenger {i}", 20 + i)
        self.system.book_passenger("Waitlist One", 40)  # P011, Pos 1
        self.system.book_passenger("Waitlist Two", 41)  # P012, Pos 2

        # Cancel confirmed passenger P003 (Seat 3)
        res = self.system.cancel_passenger("P003")
        self.assertTrue(res["success"])
        self.assertEqual(res["type"], "CONFIRMED_WITH_PROMOTION")
        self.assertEqual(res["seat_number"], 3)
        self.assertEqual(res["cancelled"]["id"], "P003")
        self.assertEqual(res["promoted"]["id"], "P011")
        self.assertEqual(res["promoted"]["seat"], 3)

        # Verify seat 3 is now occupied by P011
        status = self.system.get_status()
        self.assertEqual(status["seats"][2]["status"], "Occupied")
        self.assertEqual(status["seats"][2]["passenger"]["id"], "P011")
        self.assertEqual(status["confirmed_count"], 10)
        self.assertEqual(status["waiting_count"], 1)

        # P012 should now be at position 1
        self.assertEqual(status["waiting_passengers"][0]["id"], "P012")
        self.assertEqual(status["waiting_passengers"][0]["position"], 1)

    def test_06_cancellation_of_waiting_passenger(self):
        """8. Cancelling a waiting passenger removes only that passenger."""
        for i in range(1, 11):
            self.system.book_passenger(f"Passenger {i}", 20 + i)
        self.system.book_passenger("Waitlist One", 40)  # P011, Pos 1
        self.system.book_passenger("Waitlist Two", 41)  # P012, Pos 2
        self.system.book_passenger("Waitlist Three", 42)  # P013, Pos 3

        # Cancel middle waiting passenger P012
        res = self.system.cancel_passenger("P012")
        self.assertTrue(res["success"])
        self.assertEqual(res["type"], "WAITING_REMOVED")
        self.assertEqual(res["cancelled"]["id"], "P012")

        status = self.system.get_status()
        self.assertEqual(status["waiting_count"], 2)
        # Position 1 is still P011, Position 2 is now P013
        self.assertEqual(status["waiting_passengers"][0]["id"], "P011")
        self.assertEqual(status["waiting_passengers"][0]["position"], 1)
        self.assertEqual(status["waiting_passengers"][1]["id"], "P013")
        self.assertEqual(status["waiting_passengers"][1]["position"], 2)

    def test_07_unique_ids_and_reset(self):
        """9 & 10. Passenger IDs remain unique until system is reset; reset restores initial state."""
        self.system.book_passenger("P One", 25)  # P001
        self.system.book_passenger("P Two", 26)  # P002
        self.system.cancel_passenger("P001")
        # Next booked passenger must be P003, not reusing P001 before reset
        res3 = self.system.book_passenger("P Three", 27)
        self.assertEqual(res3["passenger"]["id"], "P003")

        # Now test reset
        reset_res = self.system.reset_system()
        self.assertTrue(reset_res["success"])

        status = self.system.get_status()
        self.assertEqual(status["available_count"], 10)
        self.assertEqual(status["confirmed_count"], 0)
        self.assertEqual(status["waiting_count"], 0)

        # After reset, next ID should be P001
        res_new = self.system.book_passenger("Fresh Start", 30)
        self.assertEqual(res_new["passenger"]["id"], "P001")
        self.assertEqual(res_new["passenger"]["seat"], 1)

    def test_08_input_validation(self):
        """Validate edge cases for input fields."""
        res_empty = self.system.book_passenger("", 25)
        self.assertFalse(res_empty["success"])

        res_invalid_name = self.system.book_passenger("12345", 25)
        self.assertFalse(res_invalid_name["success"])

        res_invalid_age = self.system.book_passenger("Valid Name", 0)
        self.assertFalse(res_invalid_age["success"])

        res_high_age = self.system.book_passenger("Valid Name", 150)
        self.assertFalse(res_high_age["success"])


if __name__ == "__main__":
    unittest.main()
