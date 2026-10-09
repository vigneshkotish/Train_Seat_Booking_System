"""
End-to-End integration test suite for RailFlow Flask Web Application.
Tests HTTP routes, REST API endpoints, HTML rendering, and full user journeys.
"""

import unittest
import json
import os
from app import app, system


class TestRailFlowFlaskApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True
        system.reset_system()

    def tearDown(self):
        system.reset_system()

    def test_01_index_html_rendering(self):
        """Verify root route renders HTML with Chennai -> Bangalore and 10 seats."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("RailFlow", html)
        self.assertIn("Chennai", html)
        self.assertIn("Bangalore", html)
        self.assertIn("10 Total Seats", html)
        self.assertIn("collections.deque", html)

    def test_02_status_api(self):
        """Verify /api/status returns accurate initial data."""
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["total_seats"], 10)
        self.assertEqual(data["available_count"], 10)
        self.assertEqual(data["confirmed_count"], 0)
        self.assertEqual(data["waiting_count"], 0)
        self.assertEqual(len(data["seats"]), 10)

    def test_03_booking_api(self):
        """Verify /api/book assigns seats 1-10 and waitlists 11."""
        # Book 10 seats
        for i in range(1, 11):
            res = self.client.post(
                "/api/book",
                data=json.dumps({"name": f"User {i}", "age": 20 + i}),
                content_type="application/json",
            )
            self.assertEqual(res.status_code, 200)
            json_res = res.get_json()
            self.assertTrue(json_res["success"])
            self.assertEqual(json_res["status"], "CONFIRMED")
            self.assertEqual(json_res["passenger"]["seat"], i)

        # 11th passenger enters waitlist
        res11 = self.client.post(
            "/api/book",
            data=json.dumps({"name": "User Eleven", "age": 35}),
            content_type="application/json",
        )
        self.assertEqual(res11.status_code, 200)
        json_11 = res11.get_json()
        self.assertTrue(json_11["success"])
        self.assertEqual(json_11["status"], "WAITING")
        self.assertEqual(json_11["queue_position"], 1)

    def test_04_cancellation_and_promotion_api(self):
        """Verify /api/cancel releases seat and promotes earliest waiting passenger."""
        # Book 10 confirmed + 1 waitlisted
        for i in range(1, 11):
            self.client.post(
                "/api/book",
                data=json.dumps({"name": f"Passenger {i}", "age": 25}),
                content_type="application/json",
            )
        self.client.post(
            "/api/book",
            data=json.dumps({"name": "Waitlisted Hope", "age": 30}),
            content_type="application/json",
        )

        # Cancel P004 (Seat 4)
        res_cancel = self.client.post(
            "/api/cancel",
            data=json.dumps({"passenger_id": "P004"}),
            content_type="application/json",
        )
        self.assertEqual(res_cancel.status_code, 200)
        data = res_cancel.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["type"], "CONFIRMED_WITH_PROMOTION")
        self.assertEqual(data["seat_number"], 4)
        self.assertEqual(data["promoted"]["id"], "P011")

        # Verify status endpoint reflects Seat 4 occupied by P011
        status_res = self.client.get("/api/status")
        status = status_res.get_json()
        self.assertEqual(status["seats"][3]["passenger"]["id"], "P011")
        self.assertEqual(status["waiting_count"], 0)

    def test_05_reset_api(self):
        """Verify /api/reset restores clean initial state."""
        self.client.post(
            "/api/book",
            data=json.dumps({"name": "Tester", "age": 22}),
            content_type="application/json",
        )
        res = self.client.post("/api/reset")
        self.assertEqual(res.status_code, 200)

        status_res = self.client.get("/api/status")
        status = status_res.get_json()
        self.assertEqual(status["available_count"], 10)
        self.assertEqual(status["confirmed_count"], 0)
        self.assertEqual(status["next_id"], "P001")


if __name__ == "__main__":
    unittest.main()
