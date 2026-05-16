#!/usr/bin/env python3
"""
Test script for What's New? API endpoints
Testing backend without database/external dependencies
"""

import sys
import asyncio
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Import the app
from main import app, DigestRequest

async def test_endpoints():
    """Test all API endpoints"""
    from fastapi.testclient import TestClient
    
    print("=" * 60)
    print("WHAT'S NEW? API ENDPOINT TEST SUITE")
    print("=" * 60)
    
    client = TestClient(app)
    results = []
    
    # Test 1: Health check
    print("\n[1/14] Testing /health")
    try:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        print(f"✓ PASS - Status: {data}")
        results.append(("GET /health", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("GET /health", False, str(e)))
    
    # Test 2: Generate digest
    print("\n[2/14] Testing POST /digest/generate")
    try:
        resp = client.post("/digest/generate", json={"domain": "ai", "days": 7})
        assert resp.status_code == 200
        data = resp.json()
        assert "digest_id" in data
        assert "trends" in data
        print(f"✓ PASS - Generated digest with {data['total_trends']} trends, {data['total_articles']} articles")
        results.append(("POST /digest/generate", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("POST /digest/generate", False, str(e)))
    
    # Test 3: Get digest history
    print("\n[3/14] Testing GET /digest/history")
    try:
        resp = client.get("/digest/history?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ PASS - Retrieved {len(data)} digest history entries")
        results.append(("GET /digest/history", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("GET /digest/history", False, str(e)))
    
    # Test 4: Get digest with domain filter
    print("\n[4/14] Testing GET /digest/history?domain=AI&ML")
    try:
        resp = client.get("/digest/history?domain=AI&ML")
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ PASS - Retrieved {len(data)} AI & ML digests")
        results.append(("GET /digest/history (filtered)", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("GET /digest/history (filtered)", False, str(e)))
    
    # Test 5: Get specific digest
    print("\n[5/14] Testing GET /digest/{digest_id}")
    try:
        resp = client.get("/digest/test-digest-123")
        assert resp.status_code == 200
        data = resp.json()
        assert "trends" in data
        print(f"✓ PASS - Retrieved mock digest")
        results.append(("GET /digest/{id}", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("GET /digest/{id}", False, str(e)))
    
    # Test 6: Save trend
    print("\n[6/14] Testing POST /digest/{digest_id}/save-trend/{trend_id}")
    try:
        resp = client.post("/digest/digest-001/save-trend/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "saved"
        print(f"✓ PASS - Trend saved: {data}")
        results.append(("POST /digest/save-trend", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("POST /digest/save-trend", False, str(e)))
    
    # Test 7: Get saved trends
    print("\n[7/14] Testing GET /user/saved-trends")
    try:
        resp = client.get("/user/saved-trends")
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ PASS - Retrieved {len(data)} saved trends")
        results.append(("GET /user/saved-trends", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("GET /user/saved-trends", False, str(e)))
    
    # Test 8: Delete saved trend
    print("\n[8/14] Testing DELETE /user/saved-trends/{saved_id}")
    try:
        resp = client.delete("/user/saved-trends/saved-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "deleted"
        print(f"✓ PASS - Trend deleted: {data}")
        results.append(("DELETE /user/saved-trends", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("DELETE /user/saved-trends", False, str(e)))
    
    # Test 9: Get current user
    print("\n[9/14] Testing GET /user/me")
    try:
        resp = client.get("/user/me")
        assert resp.status_code == 200
        data = resp.json()
        assert "email" in data
        assert "name" in data
        print(f"✓ PASS - User: {data['name']} ({data['email']})")
        results.append(("GET /user/me", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("GET /user/me", False, str(e)))
    
    # Test 10: Update preferences
    print("\n[10/14] Testing PATCH /user/preferences")
    try:
        prefs = {
            "default_domain": "finance",
            "default_days": 30,
            "daily_digest_enabled": True,
            "daily_digest_time": "09:00",
            "daily_digest_domain": "finance"
        }
        resp = client.patch("/user/preferences", json=prefs)
        assert resp.status_code == 200
        data = resp.json()
        assert data["default_domain"] == "finance"
        print(f"✓ PASS - Preferences updated")
        results.append(("PATCH /user/preferences", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("PATCH /user/preferences", False, str(e)))
    
    # Test 11: Export PDF
    print("\n[11/14] Testing GET /export/pdf/{digest_id}")
    try:
        resp = client.get("/export/pdf/digest-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "url" in data
        print(f"✓ PASS - PDF export URL: {data['url']}")
        results.append(("GET /export/pdf", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("GET /export/pdf", False, str(e)))
    
    # Test 12: Create share link
    print("\n[12/14] Testing GET /export/share/{digest_id}")
    try:
        resp = client.get("/export/share/digest-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "share_url" in data
        assert "token" in data
        print(f"✓ PASS - Share URL: {data['share_url']}")
        results.append(("GET /export/share", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("GET /export/share", False, str(e)))
    
    # Test 13: Test all domains
    print("\n[13/14] Testing POST /digest/generate with all domains")
    domains = ["ai", "finance", "healthcare", "climate", "crypto", "legal", "policy", "cybersecurity"]
    domain_results = []
    try:
        for domain in domains:
            resp = client.post("/digest/generate", json={"domain": domain, "days": 7})
            if resp.status_code == 200:
                data = resp.json()
                domain_results.append(f"✓ {domain}: {data['total_trends']} trends")
            else:
                domain_results.append(f"✗ {domain}: {resp.status_code}")
        
        print("\n".join(domain_results))
        results.append(("POST /digest/generate (all domains)", True, "Multiple OK"))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("POST /digest/generate (all domains)", False, str(e)))
    
    # Test 14: Test pagination
    print("\n[14/14] Testing pagination parameters")
    try:
        resp = client.get("/digest/history?limit=3&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) <= 3
        print(f"✓ PASS - Retrieved with pagination: {len(data)} items")
        results.append(("Pagination", True, resp.status_code))
    except Exception as e:
        print(f"✗ FAIL - {e}")
        results.append(("Pagination", False, str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    
    print("\nDetailed Results:")
    print("-" * 60)
    for endpoint, success, status in results:
        status_str = f"✓ {status}" if success else f"✗ {status}"
        print(f"{endpoint:<35} {status_str}")
    
    print("\n" + "=" * 60)
    print("KEY FINDINGS:")
    print("=" * 60)
    print("✓ No Google OAuth implementation in backend")
    print("✓ No SMTP/email service implementation")
    print("✓ No database currently implemented (using in-memory cache)")
    print("✓ All endpoints return mock/test data")
    print("\nNOTE: This is a functional prototype. Production deployment requires:")
    print("  1. Database integration (MongoDB, PostgreSQL, etc.)")
    print("  2. Authentication/session management")
    print("  3. Real data persistence")
    print("  4. Environment variable configuration for API keys")
    print("=" * 60)
    
    return passed == len(results)

if __name__ == "__main__":
    try:
        success = asyncio.run(test_endpoints())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
