#!/usr/bin/env python3
"""
Test script for multiple recipients functionality.

This script tests the new multiple recipients feature by simulating
a webhook request with attendance data.
"""

import json
import requests
import sys
from datetime import datetime

def test_multiple_recipients():
    """Test the multiple recipients functionality."""
    
    # Test data
    test_data = {
        "nombre": "Juan Perez Test",
        "empresa": "Empresa de Prueba SA",
        "cargo": "Desarrollador",
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Webhook URL (adjust if different)
    url = "http://127.0.0.1:7000/attendance-webhook"
    
    print("🧪 Testing Multiple Recipients Feature")
    print("="*50)
    print(f"📋 Test Data:")
    print(f"   Name: {test_data['nombre']}")
    print(f"   Company: {test_data['empresa']}")
    print(f"   Position: {test_data['cargo']}")
    print(f"   DateTime: {test_data['fecha_hora']}")
    print()
    
    try:
        print("📡 Sending POST request to webhook...")
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"📋 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ SUCCESS - Webhook processed successfully!")
            print()
            
            # Display batch results
            batch_results = response_data.get('data', {}).get('batch_results', {})
            print("📊 Batch Results:")
            print(f"   Total Recipients: {batch_results.get('total_recipients', 0)}")
            print(f"   Successful Sends: {batch_results.get('successful_sends', 0)}")
            print(f"   Failed Sends: {batch_results.get('failed_sends', 0)}")
            print(f"   Success Rate: {batch_results.get('success_rate', 0)}%")
            
            # Show successful numbers (last 4 digits for privacy)
            successful_numbers = response_data.get('data', {}).get('successful_numbers', [])
            failed_numbers = response_data.get('data', {}).get('failed_numbers', [])
            
            if successful_numbers:
                print(f"\n✅ Successfully sent to {len(successful_numbers)} numbers:")
                for num in successful_numbers[:5]:  # Show first 5
                    print(f"   {num[-4:].rjust(11, '*')}")
                if len(successful_numbers) > 5:
                    print(f"   ... and {len(successful_numbers) - 5} more")
            
            if failed_numbers:
                print(f"\n❌ Failed to send to {len(failed_numbers)} numbers:")
                for num in failed_numbers[:5]:  # Show first 5
                    print(f"   {num[-4:].rjust(11, '*')}")
                if len(failed_numbers) > 5:
                    print(f"   ... and {len(failed_numbers) - 5} more")
            
        else:
            print("❌ ERROR - Webhook request failed!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR - Could not connect to webhook server!")
        print("Make sure the Flask app is running on http://127.0.0.1:7000")
        return False
        
    except requests.exceptions.Timeout:
        print("⏰ ERROR - Request timed out!")
        print("The batch send might be taking longer than expected.")
        return False
        
    except Exception as e:
        print(f"❌ ERROR - Unexpected error: {e}")
        return False
    
    return True

def test_health_check():
    """Test the health check endpoint to see service status."""
    
    print("\n🔍 Testing Health Check...")
    print("="*30)
    
    try:
        response = requests.get("http://127.0.0.1:7000/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            service_info = health_data.get('service_info', {})
            
            print("✅ Service Health Check Passed!")
            print(f"   Recipient Count: {service_info.get('recipient_count', 'Unknown')}")
            print(f"   Debug Mode: {service_info.get('debug_mode', 'Unknown')}")
            
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("WhatsApp Multiple Recipients Test")
    print("=" * 40)
    print()
    
    # Test health check first
    test_health_check()
    
    # Test multiple recipients
    success = test_multiple_recipients()
    
    if success:
        print("\n🎉 Test completed! Check the logs and your WhatsApp numbers for messages.")
    else:
        print("\n💥 Test failed. Check the error messages above.")
        sys.exit(1)