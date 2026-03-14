#!/usr/bin/env python3
"""
Load testing script for AccessibleAI API.

Uses locust to simulate concurrent users and test API performance.
Run with: locust -f load_test.py --host=http://localhost:8000
"""

import os
import random
import uuid
from locust import HttpUser, task, between
from datetime import datetime


class AccessibleAIUser(HttpUser):
    """Simulated user for load testing."""

    wait_time = between(1, 3)

    def on_start(self):
        """Setup when user starts."""
        self.email = f"loadtest_{uuid.uuid4()}@example.com"
        self.password = "TestPass123!"
        self.access_token = None

    @task(3)
    def health_check(self):
        """Check API health (most common operation)."""
        self.client.get("/health")

    @task(2)
    def get_websites(self):
        """Get user's websites."""
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            self.client.get("/api/v1/websites", headers=headers)

    @task(1)
    def register_and_login(self):
        """Register a new user and login."""
        # Register
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "name": "Load Test User",
            },
            catch_response=True,
        )

        if response.status_code == 201:
            data = response.json()
            self.access_token = data.get("access_token")
        elif response.status_code == 400:
            # User already exists, try login
            self.login()

    def login(self):
        """Login with credentials."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.email,
                "password": self.password,
            },
            catch_response=True,
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")


class WebsiteOwnerUser(HttpUser):
    """Simulated user who owns websites and runs scans."""

    wait_time = between(5, 10)

    def on_start(self):
        """Setup when user starts."""
        self.email = f"website_owner_{uuid.uuid4()}@example.com"
        self.password = "TestPass123!"
        self.access_token = None
        self.website_id = None
        self.login()

    def login(self):
        """Login or register."""
        # Try to register first
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "name": "Website Owner",
            },
        )

        if response.status_code in [200, 201]:
            if response.status_code == 200:
                # Already registered, this is login response
                data = response.json()
                self.access_token = data.get("access_token")
            else:
                # Just registered
                data = response.json()
                self.access_token = data.get("access_token")

            # Create a website
            self.create_website()

    def create_website(self):
        """Create a test website."""
        if not self.access_token:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post(
            "/api/v1/websites",
            json={
                "url": "https://example.com",
                "name": f"Test Site {uuid.uuid4()}",
                "platform": "generic",
            },
            headers=headers,
        )

        if response.status_code == 201:
            data = response.json()
            self.website_id = data.get("id")

    @task
    def get_scan_history(self):
        """Get scan history."""
        if not self.access_token:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.get("/api/v1/scans", headers=headers)

    @task(2)
    def trigger_scan(self):
        """Trigger a new scan."""
        if not self.access_token or not self.website_id:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.post(
            f"/api/v1/websites/{self.website_id}/scan",
            json={"full_scan": False},
            headers=headers,
        )


if __name__ == "__main__":
    # Run with locust CLI
    # locust -f load_test.py --host=http://localhost:8000
    # Or headless mode:
    # locust -f load_test.py --headless --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 1m
    print("Run with: locust -f load_test.py --host=http://localhost:8000")
