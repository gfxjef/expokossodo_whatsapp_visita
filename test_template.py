#!/usr/bin/env python3
"""
Quick Test Template for Attendance Webhook with Photo Support.

This script provides a simple template to test the attendance webhook
with different scenarios including photo attachments.

Usage:
    python test_template.py
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
WEBHOOK_URL = f"{BASE_URL}/attendance-webhook"

def test_basic_notification():
    """Test basic attendance notification without photo."""
    data = {
        "nombre": "María García López",
        "empresa": "Innovación Digital Ltda.",
        "cargo": "Desarrolladora Full Stack",
        "fecha_hora": "2023-12-07 15:45:00"
    }
    
    print("Testing basic notification (no photo)...")
    response = requests.post(WEBHOOK_URL, json=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_notification_with_photo():
    """Test attendance notification with photo."""
    data = {
        "nombre": "Carlos Rodríguez Martín",
        "empresa": "TechSolutions S.A.",
        "cargo": "Arquitecto de Software",
        "fecha_hora": "2023-12-07 16:30:00",
        "photo": "https://iaap.org/wp-content/uploads/2022/11/Image_001-8.jpg"
    }
    
    print("Testing notification with photo...")
    response = requests.post(WEBHOOK_URL, json=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_invalid_photo_url():
    """Test with invalid photo URL."""
    data = {
        "nombre": "Ana Fernández",
        "empresa": "Consultoría Pro",
        "cargo": "Analista de Sistemas",
        "fecha_hora": "2023-12-07 17:00:00",
        "photo": "not-a-valid-url"
    }
    
    print("Testing invalid photo URL...")
    response = requests.post(WEBHOOK_URL, json=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def main():
    """Run all test cases."""
    print("Testing Attendance Webhook with Photo Support")
    print("=" * 60)
    
    try:
        # Test health endpoint first
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("Service is healthy")
            print("-" * 50)
        else:
            print("Service health check failed")
            return
        
        # Run test cases
        test_basic_notification()
        test_notification_with_photo() 
        test_invalid_photo_url()
        
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Cannot connect to service. Is the Flask app running on localhost:5000?")
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    main()