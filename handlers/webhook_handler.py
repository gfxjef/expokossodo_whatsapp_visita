"""
Webhook Handler Module for Attendance Notifications.

This module handles incoming webhook requests, validates attendance data,
and orchestrates the WhatsApp notification process with comprehensive
error handling and logging.

WHY: Separation of HTTP request handling from business logic ensures
clean architecture and easier testing of webhook endpoints.
"""

import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from flask import request, jsonify, Response
import json

from services.whatsapp_service import WhatsAppService, WhatsAppServiceError


class AttendanceWebhookHandler:
    """
    Handler class for processing attendance webhook requests.
    
    Manages HTTP request validation, data processing, and response
    generation with comprehensive error handling and security measures.
    """
    
    def __init__(self, whatsapp_service: WhatsAppService):
        """
        Initialize webhook handler with WhatsApp service.
        
        Args:
            whatsapp_service: Configured WhatsAppService instance
        """
        self.whatsapp_service = whatsapp_service
        self.logger = logging.getLogger(__name__)
    
    def handle_attendance_webhook(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle incoming attendance webhook POST requests.
        
        Processes JSON payload containing attendance data, validates it,
        and sends WhatsApp notification.
        
        Returns:
            Tuple of (response_data, http_status_code)
            
        WHY: Main entry point for webhook processing that orchestrates
        all validation, processing, and notification steps
        """
        try:
            # WHY: Log incoming request for debugging and monitoring
            self.logger.info(f"Received attendance webhook request from {request.remote_addr}")
            
            # Validate request method
            if request.method != 'POST':
                self.logger.warning(f"Invalid request method: {request.method}")
                return {
                    'success': False,
                    'error': 'Method not allowed',
                    'message': 'Only POST requests are accepted'
                }, 405
            
            # Validate content type
            if not request.is_json:
                self.logger.warning("Request is not JSON")
                return {
                    'success': False,
                    'error': 'Invalid content type',
                    'message': 'Content-Type must be application/json'
                }, 400
            
            # Parse JSON payload
            try:
                attendance_data = request.get_json()
                if not attendance_data:
                    raise ValueError("Empty JSON payload")
                    
            except (ValueError, json.JSONDecodeError) as e:
                self.logger.warning(f"Invalid JSON payload: {e}")
                return {
                    'success': False,
                    'error': 'Invalid JSON',
                    'message': 'Request body must contain valid JSON'
                }, 400
            
            # Log received data (exclude sensitive information)
            self.logger.debug(f"Received attendance data: {self._sanitize_log_data(attendance_data)}")
            
            # Validate attendance data structure and content
            is_valid, validation_error = self.whatsapp_service.validate_attendance_data(attendance_data)
            if not is_valid:
                self.logger.warning(f"Attendance data validation failed: {validation_error}")
                return {
                    'success': False,
                    'error': 'Validation error',
                    'message': validation_error
                }, 400
            
            # Send WhatsApp notification
            success, response_data = self.whatsapp_service.send_attendance_notification(attendance_data)
            
            if success:
                # WHY: Return success response with relevant information
                response = {
                    'success': True,
                    'message': 'Attendance notification sent successfully',
                    'data': {
                        'employee_name': attendance_data['nombre'],
                        'company': attendance_data['empresa'],
                        'timestamp': datetime.now().isoformat(),
                        'message_id': response_data.get('messages', [{}])[0].get('id'),
                        'has_photo': 'photo' in attendance_data and bool(attendance_data['photo']),
                        'photo_url': attendance_data.get('photo', None) if 'photo' in attendance_data else None
                    }
                }
                
                photo_status = " with photo" if attendance_data.get('photo') else ""
                self.logger.info(
                    f"Successfully processed attendance{photo_status} for {attendance_data['nombre']} "
                    f"from {attendance_data['empresa']}"
                )
                
                return response, 200
            else:
                # WHY: Handle notification sending failure
                error_msg = response_data.get('error', 'Unknown error occurred')
                self.logger.error(f"Failed to send WhatsApp notification: {error_msg}")
                
                return {
                    'success': False,
                    'error': 'Notification failed',
                    'message': f'Failed to send WhatsApp notification: {error_msg}'
                }, 500
        
        except WhatsAppServiceError as e:
            self.logger.error(f"WhatsApp service error: {e}")
            return {
                'success': False,
                'error': 'Service error',
                'message': 'WhatsApp service is currently unavailable'
            }, 503
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing attendance webhook: {e}")
            return {
                'success': False,
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing the request'
            }, 500
    
    def handle_health_check(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle health check requests.
        
        Returns:
            Tuple of (health_status, http_status_code)
            
        WHY: Provides endpoint for monitoring service health and status
        """
        try:
            service_status = self.whatsapp_service.get_service_status()
            
            return {
                'success': True,
                'status': 'healthy',
                'service_info': service_status,
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'success': False,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, 503
    
    def handle_webhook_verification(self, verify_token: str) -> Response:
        """
        Handle webhook verification requests (GET method).
        
        Used by WhatsApp to verify webhook endpoint during setup.
        
        Args:
            verify_token: Expected verification token
            
        Returns:
            Flask Response object
            
        WHY: Required for WhatsApp webhook verification process
        """
        try:
            # Get verification parameters from query string
            hub_mode = request.args.get('hub.mode')
            hub_verify_token = request.args.get('hub.verify_token')
            hub_challenge = request.args.get('hub.challenge')
            
            # Validate verification request
            if hub_mode == 'subscribe' and hub_verify_token == verify_token:
                self.logger.info("Webhook verification successful")
                return Response(hub_challenge, status=200, mimetype='text/plain')
            else:
                self.logger.warning(
                    f"Webhook verification failed. Mode: {hub_mode}, "
                    f"Token match: {hub_verify_token == verify_token}"
                )
                return Response('Verification failed', status=403)
                
        except Exception as e:
            self.logger.error(f"Error during webhook verification: {e}")
            return Response('Verification error', status=500)
    
    def _sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize sensitive data for logging.
        
        Args:
            data: Original data dictionary
            
        Returns:
            Sanitized data dictionary
            
        WHY: Prevents sensitive information from being logged while
        maintaining useful debugging information
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        sensitive_fields = ['phone', 'email', 'id', 'token']
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def format_error_response(
        self, 
        error_code: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format standardized error response.
        
        Args:
            error_code: Error code identifier
            message: Human-readable error message
            details: Optional additional error details
            
        Returns:
            Formatted error response dictionary
            
        WHY: Standardizes error responses for consistent API behavior
        """
        response = {
            'success': False,
            'error': error_code,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            response['details'] = details
            
        return response


def create_webhook_routes(app, webhook_handler: AttendanceWebhookHandler, verify_token: str):
    """
    Create Flask routes for webhook handling.
    
    Args:
        app: Flask application instance
        webhook_handler: Configured webhook handler
        verify_token: Token for webhook verification
        
    WHY: Factory function to create routes with proper dependency injection
    """
    
    @app.route('/attendance-webhook', methods=['POST'])
    def attendance_webhook():
        """Handle attendance notification webhook."""
        response_data, status_code = webhook_handler.handle_attendance_webhook()
        return jsonify(response_data), status_code
    
    @app.route('/attendance-webhook', methods=['GET'])
    def webhook_verification():
        """Handle webhook verification."""
        return webhook_handler.handle_webhook_verification(verify_token)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Handle health check requests."""
        response_data, status_code = webhook_handler.handle_health_check()
        return jsonify(response_data), status_code
    
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with basic service information."""
        return jsonify({
            'service': 'WhatsApp Attendance Notifier',
            'version': '1.0.0',
            'status': 'active',
            'endpoints': {
                'attendance_webhook': '/attendance-webhook',
                'health_check': '/health',
                'webhook_verification': '/attendance-webhook?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE'
            },
            'timestamp': datetime.now().isoformat()
        })