"""
Test script to verify security middleware is working.
Run this after starting your API server.

Usage:
    python test_security.py
"""

import requests
import time
from typing import Dict, List

API_URL = "http://localhost:8000"


class SecurityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results: List[Dict] = []

    def test_path_blocking(self):
        """Test that malicious paths are blocked."""
        print("\n🛡️  Testing Path Blocking...")

        malicious_paths = [
            "/.git/config",
            "/.env",
            "/wordpress/wp-login.php",
            "/phpmyadmin/",
            "/.htaccess",
            "/config.php",
            "/backup.sql",
        ]

        for path in malicious_paths:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=5)
                status = (
                    "✅ BLOCKED"
                    if response.status_code in [403, 404]
                    else "❌ NOT BLOCKED"
                )
                print(f"  {status} - {path} (Status: {response.status_code})")
                self.results.append(
                    {
                        "test": "path_blocking",
                        "path": path,
                        "status": response.status_code,
                        "blocked": response.status_code in [403, 404],
                    }
                )
            except requests.RequestException as e:
                print(f"  ⚠️  ERROR - {path}: {e}")

    def test_scanner_detection(self):
        """Test that scanner signatures are detected."""
        print("\n🔍 Testing Scanner Detection...")

        scanner_paths = [
            "/js/lkk_ch.js",
            "/js/twint_ch.js",
            "/css/support_parent.css",
        ]

        for path in scanner_paths:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=5)
                status = (
                    "✅ DETECTED"
                    if response.status_code in [403, 404]
                    else "❌ NOT DETECTED"
                )
                print(f"  {status} - {path} (Status: {response.status_code})")
                self.results.append(
                    {
                        "test": "scanner_detection",
                        "path": path,
                        "status": response.status_code,
                        "detected": response.status_code in [403, 404],
                    }
                )
            except requests.RequestException as e:
                print(f"  ⚠️  ERROR - {path}: {e}")

    def test_rate_limiting(self):
        """Test that rate limiting works."""
        print("\n⏱️  Testing Rate Limiting...")
        print("  Making 105 requests quickly...")

        blocked_count = 0
        success_count = 0

        for i in range(105):
            try:
                response = requests.get(f"{self.base_url}/", timeout=5)
                if response.status_code == 429:
                    blocked_count += 1
                    if blocked_count == 1:
                        print(f"  ✅ Rate limit triggered at request #{i + 1}")
                elif response.status_code == 200:
                    success_count += 1
            except requests.RequestException:
                pass

            # Small delay to avoid overwhelming the server
            time.sleep(0.01)

        print(f"  Successful requests: {success_count}")
        print(f"  Rate limited requests: {blocked_count}")

        if blocked_count > 0:
            print("  ✅ PASSED - Rate limiting is working")
        else:
            print("  ⚠️  WARNING - No rate limiting detected (may need more requests)")

        self.results.append(
            {
                "test": "rate_limiting",
                "success_count": success_count,
                "blocked_count": blocked_count,
                "working": blocked_count > 0,
            }
        )

    def test_legitimate_requests(self):
        """Test that legitimate requests still work."""
        print("\n✨ Testing Legitimate Requests...")

        legitimate_paths = [
            "/",
            "/v1/movies",
            "/docs",
        ]

        for path in legitimate_paths:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=5)
                status = (
                    "✅ ALLOWED"
                    if response.status_code in [200, 307]
                    else "⚠️  UNEXPECTED"
                )
                print(f"  {status} - {path} (Status: {response.status_code})")
                self.results.append(
                    {
                        "test": "legitimate_requests",
                        "path": path,
                        "status": response.status_code,
                        "allowed": response.status_code in [200, 307],
                    }
                )
            except requests.RequestException as e:
                print(f"  ❌ ERROR - {path}: {e}")

    def run_all_tests(self):
        """Run all security tests."""
        print("=" * 60)
        print("🔐 Security Middleware Test Suite")
        print("=" * 60)

        self.test_path_blocking()
        self.test_scanner_detection()
        self.test_legitimate_requests()

        # Rate limiting test last (as it might trigger IP blocking)
        print("\n⚠️  WARNING: Rate limiting test may temporarily block your IP")
        print("Press Enter to continue or Ctrl+C to skip...")
        try:
            input()
            self.test_rate_limiting()
        except KeyboardInterrupt:
            print("\n  Skipped rate limiting test")

        print("\n" + "=" * 60)
        print("✅ Security Tests Complete!")
        print("=" * 60)

        # Summary
        blocked_paths = sum(
            1
            for r in self.results
            if r.get("test") == "path_blocking" and r.get("blocked")
        )
        detected_scanners = sum(
            1
            for r in self.results
            if r.get("test") == "scanner_detection" and r.get("detected")
        )
        allowed_legitimate = sum(
            1
            for r in self.results
            if r.get("test") == "legitimate_requests" and r.get("allowed")
        )

        print(f"\n📊 Summary:")
        print(f"  • Malicious paths blocked: {blocked_paths}/7")
        print(f"  • Scanner signatures detected: {detected_scanners}/3")
        print(f"  • Legitimate requests allowed: {allowed_legitimate}/3")
        print(f"\n💡 Check your application logs for detailed security events")


if __name__ == "__main__":
    print("🔧 Make sure your API server is running first!")
    print(f"Testing API at: {API_URL}")
    print("\nPress Enter to start tests or Ctrl+C to cancel...")

    try:
        input()
        tester = SecurityTester(API_URL)
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("Make sure your API server is running!")
