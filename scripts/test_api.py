#!/usr/bin/env python3
"""
API Test Script for Criminal Network Intelligence Platform
Tests all API endpoints to verify functionality.
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    print(f"  ✓ Health: {data['status']}")
    return True

def test_network():
    """Test network graph endpoint."""
    print("Testing network graph...")
    response = requests.get(f"{BASE_URL}/network")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data and "links" in data
    print(f"  ✓ Network: {len(data['nodes'])} nodes, {len(data['links'])} links")
    return True

def test_risk_scores():
    """Test risk scores endpoint."""
    print("Testing risk scores...")
    response = requests.get(f"{BASE_URL}/analytics/risk-scores")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"  ✓ Risk Scores: {len(data)} entities")
    return True

def test_centrality():
    """Test centrality endpoint."""
    print("Testing centrality...")
    response = requests.get(f"{BASE_URL}/analytics/centrality")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"  ✓ Centrality: {len(data)} entities")
    return True

def test_communities():
    """Test communities endpoint."""
    print("Testing communities...")
    response = requests.get(f"{BASE_URL}/analytics/communities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"  ✓ Communities: {len(data)} communities")
    return True

def test_anomalies():
    """Test anomalies endpoint."""
    print("Testing anomalies...")
    response = requests.get(f"{BASE_URL}/analytics/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"  ✓ Anomalies: {len(data)} anomalies")
    return True

def test_network_stats():
    """Test network stats endpoint."""
    print("Testing network stats...")
    response = requests.get(f"{BASE_URL}/analytics/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_entities" in data
    print(f"  ✓ Stats: {data['total_entities']} entities, {data['total_relationships']} relationships")
    return True

def test_entities():
    """Test entities search endpoint."""
    print("Testing entities search...")
    response = requests.get(f"{BASE_URL}/entities")
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data and "total" in data
    print(f"  ✓ Entities: {len(data['entities'])} returned, {data['total']} total")
    return True

def test_alerts():
    """Test alerts endpoint."""
    print("Testing alerts...")
    response = requests.get(f"{BASE_URL}/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"  ✓ Alerts: {len(data)} alerts")
    return True

def test_ingest_fir():
    """Test FIR ingestion."""
    print("Testing FIR ingestion...")
    test_fir = """
    FIR Number: 2024/TEST/001
    Date: 2024-01-15
    Police Station: Cyber Crime Police Station, Mumbai
    
    Complainant: Rajesh Kumar (Phone: +91-9876543210)
    Accused: Amit Sharma (Phone: +91-9123456789), Priya Singh
    
    Details: The complainant received fraudulent calls from the accused persons
    who claimed to be bank officials. They obtained OTP and transferred Rs. 2,50,000
    from account number 1234567890 (HDFC Bank, IFSC: HDFC0001234) to account
    9876543210 (ICICI Bank). The accused used phone numbers +91-9876543210 and
    +91-9123456789 for coordination. A shell company "Phoenix Solutions Pvt Ltd"
    (PAN: AAACP1234F) was used to layer the funds.
    """
    
    response = requests.post(f"{BASE_URL}/ingest/fir", json={
        "content": test_fir,
        "document_id": "test_fir_001"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"  ✓ FIR Ingested: {data['entities_extracted']} entities extracted")
    return True

def test_ingest_cdr():
    """Test CDR ingestion."""
    print("Testing CDR ingestion...")
    test_cdr = [
        {"caller": "+91-9876543210", "receiver": "+91-9123456789", "duration": 120, "timestamp": "2024-01-15T10:30:00", "source_file": "test_cdr.csv"},
        {"caller": "+91-9123456789", "receiver": "+91-9988776655", "duration": 45, "timestamp": "2024-01-15T10:35:00", "source_file": "test_cdr.csv"},
        {"caller": "+91-9988776655", "receiver": "+91-9876543210", "duration": 300, "timestamp": "2024-01-15T10:40:00", "source_file": "test_cdr.csv"},
    ]
    
    response = requests.post(f"{BASE_URL}/ingest/cdr", json={
        "records": test_cdr,
        "source_file": "test_cdr.csv"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"  ✓ CDR Ingested: {data['relationships_created']} relationships")
    return True

def test_ingest_financial():
    """Test financial ingestion."""
    print("Testing financial ingestion...")
    test_financial = [
        {"sender": "ACC1234567890", "receiver": "ACC9876543210", "amount": 250000, "timestamp": "2024-01-15T11:00:00", "source_file": "test_financial.csv"},
        {"sender": "ACC9876543210", "receiver": "ACC5555555555", "amount": 245000, "timestamp": "2024-01-15T11:05:00", "source_file": "test_financial.csv"},
        {"sender": "ACC5555555555", "receiver": "ACC1111111111", "amount": 240000, "timestamp": "2024-01-15T11:10:00", "source_file": "test_financial.csv"},
    ]
    
    response = requests.post(f"{BASE_URL}/ingest/financial", json={
        "transactions": test_financial,
        "source_file": "test_financial.csv"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"  ✓ Financial Ingested: {data['relationships_created']} relationships")
    return True

def test_full_analysis():
    """Test full analysis trigger."""
    print("Testing full analysis...")
    response = requests.post(f"{BASE_URL}/analysis/run")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"  ✓ Analysis triggered successfully")
    return True

def run_all_tests():
    """Run all API tests."""
    print("=" * 50)
    print("Criminal Network Intelligence Platform - API Tests")
    print("=" * 50)
    
    tests = [
        test_health,
        test_network,
        test_risk_scores,
        test_centrality,
        test_communities,
        test_anomalies,
        test_network_stats,
        test_entities,
        test_alerts,
        test_ingest_fir,
        test_ingest_cdr,
        test_ingest_financial,
        test_full_analysis,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {str(e)}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    # Wait for services to be ready
    print("Waiting for services to be ready...")
    time.sleep(5)
    
    success = run_all_tests()
    sys.exit(0 if success else 1)