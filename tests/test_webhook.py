#!/usr/bin/env python3
"""
Test Script for Attendance Webhook.

This script simulates multiple attendance notifications by sending
POST requests to the webhook endpoint with fictional employee data.
Useful for testing and demonstration purposes.

Usage:
    python test_webhook.py [--host localhost] [--port 5000] [--count 5]

WHY: Automated testing with realistic data helps validate the complete
notification workflow and provides examples for integration.
"""

import json
import sys
import time
import argparse
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random


class AttendanceWebhookTester:
    """
    Test client for attendance webhook endpoint.
    
    Generates realistic test data and sends it to the webhook
    endpoint to validate functionality.
    """
    
    def __init__(self, base_url: str):
        """
        Initialize test client.
        
        Args:
            base_url: Base URL of the Flask application
        """
        self.base_url = base_url.rstrip('/')
        self.webhook_url = f"{self.base_url}/attendance-webhook"
        self.health_url = f"{self.base_url}/health"
        
    def generate_test_data(self, count: int = 5) -> List[Dict[str, str]]:
        """
        Generate fictional attendance data for testing.
        
        Args:
            count: Number of test records to generate
            
        Returns:
            List of attendance data dictionaries
            
        WHY: Realistic test data helps validate formatting and
        ensures the system handles various input scenarios
        """
        
        # Fictional employee data
        nombres = [
            "Ana García López", "Carlos Rodríguez Martín", "María José Fernández",
            "Pedro Antonio Silva", "Isabel Morales Castro", "Jorge Luis Vega",
            "Carmen Elena Ruiz", "Fernando José Díaz", "Patricia Hernández",
            "Ricardo Andrés Torres", "Sofía Alejandra Reyes", "Miguel Ángel Ramos",
            "Lucía Beatriz Jiménez", "Alejandro David Castro", "Natalia Cristina Vargas"
        ]
        
        empresas = [
            "TechSolutions S.A.", "Innovación Digital Ltda.", "Consultoría Empresarial Pro",
            "Desarrollo Software Corp", "Servicios Integrales Plus", "Tecnología Avanzada S.R.L.",
            "Sistemas Corporativos", "Global Business Solutions", "Automatización Industrial",
            "Gestión Moderna S.A.", "Ingeniería y Desarrollo", "Soluciones Tecnológicas 360"
        ]
        
        cargos = [
            "Desarrollador Senior", "Analista de Sistemas", "Gerente de Proyectos",
            "Arquitecto de Software", "Especialista en DevOps", "Líder Técnico",
            "Consultor Senior", "Ingeniero de Datos", "Product Owner",
            "Scrum Master", "Analista de Negocio", "Coordinador de TI",
            "Especialista en Seguridad", "Administrador de Sistemas", "QA Engineer"
        ]
        
        # Sample photo URLs for testing
        photo_urls = [
            "https://iaap.org/wp-content/uploads/2022/11/Image_001-8.jpg",
            "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
            "https://images.unsplash.com/photo-1494790108755-2616b2e9b863?w=400",
            "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400",
            None,  # Some records without photos
            None,
            "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400"
        ]
        
        test_data = []
        base_time = datetime.now()
        
        for i in range(count):
            # Generate random time within the last hour
            random_minutes = random.randint(0, 60)
            attendance_time = base_time - timedelta(minutes=random_minutes)
            
            record = {
                "nombre": random.choice(nombres),
                "empresa": random.choice(empresas),
                "cargo": random.choice(cargos),
                "fecha_hora": attendance_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add photo to some records (60% chance)
            if random.random() < 0.6:
                photo_url = random.choice([url for url in photo_urls if url is not None])
                record["photo"] = photo_url
            
            test_data.append(record)
            
        return test_data
    
    def test_health_endpoint(self) -> bool:
        """
        Test the health endpoint to verify service is running.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            print("🔍 Testing health endpoint...")
            response = requests.get(self.health_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data.get('status', 'Unknown')}")
                return True
            else:
                print(f"❌ Health check failed: Status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to service. Is the Flask app running?")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def send_attendance_notification(self, attendance_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Send a single attendance notification to the webhook.
        
        Args:
            attendance_data: Attendance record to send
            
        Returns:
            Response data from the webhook
        """
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AttendanceWebhookTester/1.0'
            }
            
            response = requests.post(
                self.webhook_url,
                json=attendance_data,
                headers=headers,
                timeout=30
            )
            
            return {
                'status_code': response.status_code,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'success': response.status_code == 200
            }
            
        except requests.exceptions.Timeout:
            return {
                'status_code': 0,
                'response_data': {'error': 'Request timeout'},
                'success': False
            }
        except Exception as e:
            return {
                'status_code': 0,
                'response_data': {'error': str(e)},
                'success': False
            }
    
    def run_test_suite(self, count: int = 5, delay: float = 2.0) -> Dict[str, Any]:
        """
        Run complete test suite with multiple attendance notifications.
        
        Args:
            count: Number of notifications to send
            delay: Delay between notifications in seconds
            
        Returns:
            Test results summary
        """
        print(f"\n🚀 Starting Attendance Webhook Test Suite")
        print(f"📍 Target URL: {self.webhook_url}")
        print(f"📊 Test count: {count}")
        print(f"⏱️ Delay between tests: {delay}s")
        print("-" * 60)
        
        # Check service health first
        if not self.test_health_endpoint():
            return {
                'success': False,
                'error': 'Service health check failed',
                'results': []
            }
        
        # Generate test data
        test_data = self.generate_test_data(count)
        results = []
        successful_tests = 0
        
        # Send notifications
        for i, attendance_record in enumerate(test_data, 1):
            has_photo = 'photo' in attendance_record
            photo_indicator = " 📸" if has_photo else ""
            
            print(f"\n📨 Test {i}/{count}: Sending notification for {attendance_record['nombre']}{photo_indicator}")
            print(f"   Company: {attendance_record['empresa']}")
            print(f"   Position: {attendance_record['cargo']}")
            print(f"   Time: {attendance_record['fecha_hora']}")
            if has_photo:
                print(f"   Photo: {attendance_record['photo']}")
            
            result = self.send_attendance_notification(attendance_record)
            results.append({
                'test_number': i,
                'attendance_data': attendance_record,
                'result': result
            })
            
            if result['success']:
                print(f"   ✅ Success: {result['response_data'].get('message', 'Notification sent')}")
                successful_tests += 1
            else:
                print(f"   ❌ Failed: Status {result['status_code']}")
                if isinstance(result['response_data'], dict):
                    error_msg = result['response_data'].get('message', result['response_data'].get('error', 'Unknown error'))
                    print(f"      Error: {error_msg}")
            
            # Delay between requests (except for the last one)
            if i < count and delay > 0:
                print(f"   ⏳ Waiting {delay}s before next test...")
                time.sleep(delay)
        
        # Summary
        print("\n" + "=" * 60)
        print("📈 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total tests run: {count}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {count - successful_tests}")
        print(f"Success rate: {(successful_tests/count*100):.1f}%")
        
        if successful_tests == count:
            print("🎉 All tests passed successfully!")
        elif successful_tests > 0:
            print("⚠️ Some tests failed. Check the logs above for details.")
        else:
            print("🚨 All tests failed. Check service configuration and status.")
        
        return {
            'success': successful_tests == count,
            'total_tests': count,
            'successful_tests': successful_tests,
            'failed_tests': count - successful_tests,
            'success_rate': successful_tests / count * 100,
            'results': results
        }
    
    def test_invalid_data(self) -> None:
        """
        Test webhook with invalid data to verify error handling.
        
        WHY: Validation testing ensures the system handles edge cases
        and malformed input properly
        """
        print(f"\n🧪 Testing error handling with invalid data...")
        
        invalid_test_cases = [
            # Missing required fields
            {
                'name': 'Missing nombre field',
                'data': {
                    'empresa': 'Test Company',
                    'cargo': 'Test Position',
                    'fecha_hora': '2023-01-01 10:00:00'
                }
            },
            # Empty values
            {
                'name': 'Empty nombre field',
                'data': {
                    'nombre': '',
                    'empresa': 'Test Company',
                    'cargo': 'Test Position', 
                    'fecha_hora': '2023-01-01 10:00:00'
                }
            },
            # Invalid date format
            {
                'name': 'Invalid date format',
                'data': {
                    'nombre': 'Test User',
                    'empresa': 'Test Company',
                    'cargo': 'Test Position',
                    'fecha_hora': 'invalid-date'
                }
            },
            # Non-dictionary data
            {
                'name': 'Non-dictionary data',
                'data': "invalid string data"
            },
            # Invalid photo URL
            {
                'name': 'Invalid photo URL',
                'data': {
                    'nombre': 'Test User',
                    'empresa': 'Test Company',
                    'cargo': 'Test Position',
                    'fecha_hora': '2023-01-01 10:00:00',
                    'photo': 'not-a-valid-url'
                }
            },
            # Valid data with photo URL (should succeed)
            {
                'name': 'Valid data with photo',
                'data': {
                    'nombre': 'Test User With Photo',
                    'empresa': 'Test Company',
                    'cargo': 'Test Position',
                    'fecha_hora': '2023-01-01 10:00:00',
                    'photo': 'https://iaap.org/wp-content/uploads/2022/11/Image_001-8.jpg'
                }
            }
        ]
        
        for test_case in invalid_test_cases:
            print(f"\n   Testing: {test_case['name']}")
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(
                    self.webhook_url,
                    json=test_case['data'],
                    headers=headers,
                    timeout=10
                )
                
                if test_case['name'] == 'Valid data with photo':
                    # This should succeed (200) or fail gracefully (400-500)
                    if response.status_code == 200:
                        print(f"   ✅ Successfully sent with photo: {response.status_code}")
                        try:
                            success_data = response.json()
                            print(f"      Response: {success_data.get('message', 'N/A')}")
                        except:
                            pass
                    elif 400 <= response.status_code < 600:
                        print(f"   ⚠️ Failed as expected (service may be unavailable): {response.status_code}")
                    else:
                        print(f"   ❌ Unexpected status code: {response.status_code}")
                else:
                    # These should be rejected
                    if 400 <= response.status_code < 500:
                        print(f"   ✅ Correctly rejected with status {response.status_code}")
                        try:
                            error_data = response.json()
                            print(f"      Error message: {error_data.get('message', 'N/A')}")
                        except:
                            pass
                    else:
                        print(f"   ❌ Unexpected status code: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Test error: {e}")


def main():
    """Main function to run the test suite."""
    parser = argparse.ArgumentParser(description='Test Attendance Webhook')
    parser.add_argument('--host', default='localhost', help='Flask app host')
    parser.add_argument('--port', type=int, default=5000, help='Flask app port')
    parser.add_argument('--count', type=int, default=5, help='Number of test notifications')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between tests (seconds)')
    parser.add_argument('--test-errors', action='store_true', help='Also test error handling')
    
    args = parser.parse_args()
    
    # Build base URL
    base_url = f"http://{args.host}:{args.port}"
    
    # Create tester instance
    tester = AttendanceWebhookTester(base_url)
    
    try:
        # Run main test suite
        results = tester.run_test_suite(args.count, args.delay)
        
        # Test error handling if requested
        if args.test_errors:
            tester.test_invalid_data()
        
        # Exit with appropriate code
        sys.exit(0 if results['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n🚨 Test suite error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()