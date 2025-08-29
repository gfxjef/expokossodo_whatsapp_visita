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
from typing import Dict, Any, Optional, Tuple
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
                   - recipient_number: Default recipient number
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
            self.recipient_number = config['recipient_number']
            self.logger.info("WhatsApp service initialized successfully")
            
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
        recipient: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Send attendance notification via WhatsApp.
        
        Args:
            attendance_data: Dictionary containing attendance information
                           - Can include optional 'photo' field with image URL
            recipient: Optional recipient number (uses default if None)
        
        Returns:
            Tuple of (success_status, response_data)
            
        WHY: Main business method that orchestrates message formatting
        and sending with comprehensive error handling. Now supports images.
        """
        try:
            # Use provided recipient or default from config
            target_number = recipient or self.recipient_number
            
            # WHY: Validate phone number format
            if not target_number:
                raise ValueError("No recipient number provided")
            
            # Check if photo is included in attendance data
            photo_url = attendance_data.get('photo')
            
            if photo_url:
                # Send image with caption
                caption = self.format_attendance_message(attendance_data)
                
                self.logger.info(f"Sending attendance notification with image to {target_number}")
                response = self.messenger.send_image(
                    image=photo_url,
                    recipient_id=target_number.replace('+', ''),  # Remove + prefix
                    caption=caption,
                    link=True  # URL-based image
                )
                
            else:
                # Send text-only message
                message_content = self.format_attendance_message(attendance_data)
                
                message = Message(
                    instance=self.messenger,
                    content=message_content,
                    to=target_number,
                    rec_type="individual"
                )
                
                self.logger.info(f"Sending attendance notification to {target_number}")
                response = message.send()
            
            # WHY: Check response status to determine success
            if response and 'messages' in response:
                image_status = "with image" if photo_url else "text only"
                self.logger.info(
                    f"Attendance notification ({image_status}) sent successfully to {target_number} "
                    f"for employee {attendance_data['nombre']}"
                )
                return True, response
            else:
                self.logger.error(f"Failed to send message. Response: {response}")
                return False, response
                
        except Exception as e:
            self.logger.error(
                f"Error sending attendance notification: {e}. "
                f"Data: {attendance_data}"
            )
            return False, {"error": str(e)}
    
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
            'recipient_number': self.recipient_number,
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