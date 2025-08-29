"""
Configuration module for Attendance Notifier Flask application.

This module defines configuration classes for different environments
(development, testing, production) with security best practices.

WHY: Centralized configuration management ensures consistent settings
across environments and proper separation of secrets.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Base configuration class with common settings.
    
    Provides default configuration values and environment variable
    loading with strict validation for critical parameters.
    """
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # WhatsApp API Configuration
    WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN')
    WHATSAPP_RECIPIENT_NUMBER = os.environ.get('WHATSAPP_RECIPIENT_NUMBER')
    
    # Application Configuration
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'attendance_notifier.log')
    
    # Request Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))
    
    # Rate Limiting Configuration
    RATE_LIMIT = os.environ.get('RATE_LIMIT', '100 per hour')
    
    @classmethod
    def validate_required_config(cls) -> None:
        """
        Validate that all required configuration variables are set.
        
        Raises:
            ValueError: If any required configuration variable is missing
        """
        required_vars = [
            ('WHATSAPP_TOKEN', cls.WHATSAPP_TOKEN),
            ('WHATSAPP_PHONE_NUMBER_ID', cls.WHATSAPP_PHONE_NUMBER_ID),
            ('WHATSAPP_VERIFY_TOKEN', cls.WHATSAPP_VERIFY_TOKEN),
            ('WHATSAPP_RECIPIENT_NUMBER', cls.WHATSAPP_RECIPIENT_NUMBER),
        ]
        
        missing_vars = [name for name, value in required_vars if not value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
    
    @classmethod
    def get_whatsapp_config(cls) -> Dict[str, Any]:
        """
        Get WhatsApp-specific configuration as a dictionary.
        
        Returns:
            Dict containing WhatsApp API configuration
        """
        return {
            'token': cls.WHATSAPP_TOKEN,
            'phone_number_id': {1: cls.WHATSAPP_PHONE_NUMBER_ID},
            'verify_token': cls.WHATSAPP_VERIFY_TOKEN,
            'recipient_number': cls.WHATSAPP_RECIPIENT_NUMBER,
            'logger': True,
            'debug': cls.DEBUG
        }


class DevelopmentConfig(Config):
    """Development configuration with debug features enabled."""
    
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # WHY: Development environment needs detailed logging for debugging
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """
    Production configuration with security hardening.
    
    Enforces strict security settings and optimized performance
    configurations for production deployment.
    """
    
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # WHY: Production environment requires strict security measures
    FLASK_ENV = 'production'
    
    @classmethod
    def validate_required_config(cls) -> None:
        """Enhanced validation for production environment."""
        super().validate_required_config()
        
        # WHY: Production requires strong secret key
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError(
                "SECRET_KEY must be set to a strong random value in production"
            )


class TestingConfig(Config):
    """Testing configuration for unit and integration tests."""
    
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # WHY: Testing environment uses mock values to avoid API calls
    WHATSAPP_TOKEN = 'test_token'
    WHATSAPP_PHONE_NUMBER_ID = 'test_phone_id'
    WHATSAPP_VERIFY_TOKEN = 'test_verify_token'
    WHATSAPP_RECIPIENT_NUMBER = '+1234567890'


# Configuration mapping for easy environment selection
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(environment: str = None) -> Config:
    """
    Get configuration class for specified environment.
    
    Args:
        environment: Environment name (development/production/testing)
        
    Returns:
        Configuration class instance
        
    WHY: Factory pattern allows dynamic configuration selection
    based on runtime environment
    """
    env = environment or os.environ.get('FLASK_ENV', 'default')
    return config_map.get(env, config_map['default'])