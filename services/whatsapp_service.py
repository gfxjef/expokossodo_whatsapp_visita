"""
WhatsApp Service Module for Attendance Notifications.

This service handles all WhatsApp message operations including
message formatting, sending, and error handling using the
whatsapp-python library integration.

WHY: Separation of concerns - isolates WhatsApp API logic from
business logic and provides a clean interface for messaging operations.
"""

import logging
import sys
import os
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

# Add whatsapp-python to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'whatsapp-python'))

from whatsapp import WhatsApp, Message


class WhatsAppService:
    """
    Service class for managing WhatsApp message operations.
    
    Handles message formatting, sending, and error management
    with comprehensive logging and retry mechanisms.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize WhatsApp service with configuration.
        
        Args:
            config: Dictionary containing WhatsApp API configuration
                   - token: WhatsApp Business API token
                   - phone_number_id: Dict with phone number mapping
                   - verify_token: Webhook verification token
                   - recipient_numbers: List of recipient numbers
                   - logger: Enable/disable logging
                   - debug: Enable/disable debug mode
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        try:
            # WHY: Initialize WhatsApp client with error handling
            self.messenger = WhatsApp(
                token=config['token'],
                phone_number_id=config['phone_number_id'],
                logger=config.get('logger', True),
                debug=config.get('debug', False)
            )
            self.recipient_numbers = config['recipient_numbers']
            self.logger.info(f"WhatsApp service initialized successfully with {len(self.recipient_numbers)} recipients")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WhatsApp service: {e}")
            raise
    
    def format_attendance_message(self, attendance_data: Dict[str, str]) -> str:
        """
        Format attendance data into WhatsApp message.
        
        Args:
            attendance_data: Dictionary containing:
                - nombre: Employee name
                - empresa: Company name
                - cargo: Job position
                - fecha_hora: Date and time of attendance
        
        Returns:
            Formatted message string
            
        WHY: Centralized message formatting ensures consistency
        and makes template changes easier to maintain
        """
        try:
            # WHY: Validate required fields before formatting
            required_fields = ['nombre', 'empresa', 'cargo', 'fecha_hora']
            missing_fields = [field for field in required_fields 
                            if field not in attendance_data or not attendance_data[field]]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Format the message with emojis and structure
            message = f"""📋 *Nueva Asistencia Registrada*

👤 *Nombre:* {attendance_data['nombre']}
🏢 *Empresa:* {attendance_data['empresa']}
💼 *Cargo:* {attendance_data['cargo']}
📅 *Fecha/Hora:* {attendance_data['fecha_hora']}

✅ Ingreso confirmado al evento"""
            
            self.logger.debug(f"Formatted attendance message for {attendance_data['nombre']}")
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting attendance message: {e}")
            raise
    
    def send_attendance_notification(
        self, 
        attendance_data: Dict[str, str],
        recipients: Optional[List[str]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Send attendance notification via WhatsApp to multiple recipients.
        
        Args:
            attendance_data: Dictionary containing attendance information
                           - Can include optional 'photo' field with image URL
            recipients: Optional list of recipient numbers (uses default if None)
        
        Returns:
            Tuple of (overall_success_status, detailed_response_data)
            
        WHY: Main business method that orchestrates message formatting
        and sending to multiple recipients with comprehensive error handling.
        """
        try:
            # Use provided recipients or default from config
            target_numbers = recipients or self.recipient_numbers
            
            # WHY: Validate phone numbers list
            if not target_numbers:
                raise ValueError("No recipient numbers provided")
            
            # Initialize tracking variables
            successful_sends = []
            failed_sends = []
            total_recipients = len(target_numbers)
            
            # Check if photo is included in attendance data
            photo_url = attendance_data.get('photo')
            message_content = self.format_attendance_message(attendance_data)
            
            self.logger.info(f"Starting batch send to {total_recipients} recipients for employee {attendance_data['nombre']}")
            
            # Send to each recipient
            for i, target_number in enumerate(target_numbers, 1):
                try:
                    self.logger.debug(f"Sending to recipient {i}/{total_recipients}: {target_number}")
                    
                    if photo_url:
                        # Send image with caption
                        response = self.messenger.send_image(
                            image=photo_url,
                            recipient_id=target_number.replace('+', ''),  # Remove + prefix
                            caption=message_content,
                            link=True  # URL-based image
                        )
                    else:
                        # Send text-only message
                        message = Message(
                            instance=self.messenger,
                            content=message_content,
                            to=target_number,
                            rec_type="individual"
                        )
                        response = message.send()
                    
                    # Check if send was successful
                    if response and 'messages' in response:
                        message_id = response.get('messages', [{}])[0].get('id', 'unknown')
                        successful_sends.append({
                            'number': target_number,
                            'message_id': message_id,
                            'response': response
                        })
                        self.logger.debug(f"Successfully sent to {target_number} (ID: {message_id})")
                    else:
                        failed_sends.append({
                            'number': target_number,
                            'error': f"Invalid response: {response}",
                            'response': response
                        })
                        self.logger.warning(f"Failed to send to {target_number}: Invalid response")
                        
                except Exception as send_error:
                    failed_sends.append({
                        'number': target_number,
                        'error': str(send_error),
                        'response': None
                    })
                    self.logger.error(f"Error sending to {target_number}: {send_error}")
            
            # Calculate success metrics
            success_count = len(successful_sends)
            failure_count = len(failed_sends)
            success_rate = (success_count / total_recipients) * 100 if total_recipients > 0 else 0
            
            # Determine overall success (successful if at least 50% sent successfully)
            overall_success = success_count > 0 and success_rate >= 50
            
            # Log summary
            image_status = "with image" if photo_url else "text only"
            self.logger.info(
                f"Batch send completed ({image_status}) for {attendance_data['nombre']}: "
                f"{success_count}/{total_recipients} successful ({success_rate:.1f}%)"
            )
            
            # Prepare detailed response
            response_data = {
                'batch_summary': {
                    'total_recipients': total_recipients,
                    'successful_sends': success_count,
                    'failed_sends': failure_count,
                    'success_rate': round(success_rate, 2)
                },
                'successful_sends': successful_sends,
                'failed_sends': failed_sends,
                'has_photo': bool(photo_url),
                'photo_url': photo_url if photo_url else None
            }
            
            return overall_success, response_data
                
        except Exception as e:
            self.logger.error(
                f"Critical error in batch send for {attendance_data.get('nombre', 'unknown')}: {e}. "
                f"Data: {attendance_data}"
            )
            return False, {
                "error": str(e),
                "batch_summary": {
                    "total_recipients": len(target_numbers) if 'target_numbers' in locals() else 0,
                    "successful_sends": 0,
                    "failed_sends": 0,
                    "success_rate": 0
                }
            }
    
    def validate_attendance_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate attendance data format and content.
        
        Args:
            data: Raw attendance data to validate
                 - Can include optional 'photo' field with image URL
            
        Returns:
            Tuple of (is_valid, error_message)
            
        WHY: Input validation prevents errors and ensures data quality
        before processing and message sending. Now includes photo validation.
        """
        try:
            # Check required fields
            required_fields = ['nombre', 'empresa', 'cargo', 'fecha_hora']
            optional_fields = ['photo']  # New optional field
            
            if not isinstance(data, dict):
                return False, "Attendance data must be a dictionary"
            
            missing_fields = []
            empty_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                elif not data[field] or str(data[field]).strip() == '':
                    empty_fields.append(field)
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            if empty_fields:
                return False, f"Empty required fields: {', '.join(empty_fields)}"
            
            # WHY: Validate date format if it's a string
            fecha_hora = data['fecha_hora']
            if isinstance(fecha_hora, str):
                try:
                    # Try to parse common date formats
                    datetime.strptime(fecha_hora, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        datetime.strptime(fecha_hora, '%d/%m/%Y %H:%M')
                    except ValueError:
                        return False, "Invalid date format. Expected 'YYYY-MM-DD HH:MM:SS' or 'DD/MM/YYYY HH:MM'"
            
            # WHY: Validate field lengths to prevent message truncation
            max_lengths = {
                'nombre': 100,
                'empresa': 100,
                'cargo': 100
            }
            
            for field, max_length in max_lengths.items():
                if len(str(data[field])) > max_length:
                    return False, f"Field '{field}' exceeds maximum length of {max_length} characters"
            
            # WHY: Validate photo URL if provided
            if 'photo' in data and data['photo']:
                photo_url = str(data['photo']).strip()
                if not photo_url.startswith(('http://', 'https://')):
                    return False, "Photo field must be a valid URL starting with http:// or https://"
                
                # Basic URL validation
                if len(photo_url) > 2000:
                    return False, "Photo URL exceeds maximum length of 2000 characters"
                
                # Optional: Validate image file extensions
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                if not any(photo_url.lower().endswith(ext) for ext in valid_extensions):
                    # Allow URLs without extensions (some services don't show extensions)
                    self.logger.warning(f"Photo URL doesn't have a common image extension: {photo_url}")
            
            return True, "Valid"
            
        except Exception as e:
            self.logger.error(f"Error validating attendance data: {e}")
            return False, f"Validation error: {str(e)}"
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status and configuration info.
        
        Returns:
            Dictionary with service status information
            
        WHY: Provides diagnostic information for monitoring
        and troubleshooting service health
        """
        return {
            'service': 'WhatsApp Attendance Notifier',
            'status': 'active',
            'phone_number_id': list(self.config['phone_number_id'].values())[0],
            'recipient_count': len(self.recipient_numbers),
            'recipient_numbers': [num[-4:].rjust(4, '*') + num[-4:] for num in self.recipient_numbers],  # Masked numbers
            'debug_mode': self.config.get('debug', False),
            'logger_enabled': self.config.get('logger', True),
            'timestamp': datetime.now().isoformat()
        }


class WhatsAppServiceError(Exception):
    """
    Custom exception for WhatsApp service errors.
    
    WHY: Specific exception type allows for better error handling
    and distinguishes service errors from other application errors
    """
    pass