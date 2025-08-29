"""
Main Flask Application for Attendance Notifier.

This module implements a secure Flask application that receives attendance
data via webhooks and sends formatted notifications through WhatsApp.

WHY: Main application orchestrates all components with proper logging,
error handling, and security measures following Flask best practices.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config, Config
from services.whatsapp_service import WhatsAppService, WhatsAppServiceError
from handlers.webhook_handler import AttendanceWebhookHandler, create_webhook_routes


def create_app(environment: str = None) -> Flask:
    """
    Application factory function that creates and configures Flask app.
    
    Args:
        environment: Environment name (development/production/testing)
        
    Returns:
        Configured Flask application instance
        
    WHY: Factory pattern allows for different configurations per environment
    and easier testing with dependency injection
    """
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(environment)
    app.config.from_object(config)
    
    # Validate required configuration
    try:
        config.validate_required_config()
    except ValueError as e:
        app.logger.error(f"Configuration validation failed: {e}")
        raise
    
    return app


def setup_logging(app: Flask, config: Config) -> None:
    """
    Configure comprehensive logging for the application.
    
    Args:
        app: Flask application instance
        config: Configuration object
        
    WHY: Proper logging setup is essential for production monitoring,
    debugging, and security auditing
    """
    
    # Set logging level
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    app.logger.setLevel(log_level)
    
    # Remove default Flask handler
    if app.logger.handlers:
        app.logger.handlers.clear()
    
    # Create formatter for structured logging
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] [%(funcName)s:%(lineno)d] %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.LOG_FILE:
        file_handler = RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
    
    # Set root logger level
    logging.getLogger().setLevel(log_level)
    
    app.logger.info(f"Logging configured with level: {config.LOG_LEVEL}")


def setup_rate_limiting(app: Flask, config: Config) -> Limiter:
    """
    Configure rate limiting for API endpoints.
    
    Args:
        app: Flask application instance
        config: Configuration object
        
    Returns:
        Configured Limiter instance
        
    WHY: Rate limiting prevents abuse and ensures service availability
    """
    
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[config.RATE_LIMIT]
    )
    limiter.init_app(app)
    
    app.logger.info(f"Rate limiting configured: {config.RATE_LIMIT}")
    return limiter


def setup_error_handlers(app: Flask) -> None:
    """
    Configure global error handlers for the application.
    
    Args:
        app: Flask application instance
        
    WHY: Centralized error handling ensures consistent error responses
    and proper logging of all application errors
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f"Bad request from {request.remote_addr}: {error}")
        return {
            'success': False,
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server'
        }, 400
    
    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(f"404 request from {request.remote_addr}: {request.url}")
        return {
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }, 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        app.logger.warning(f"Method not allowed from {request.remote_addr}: {request.method} {request.url}")
        return {
            'success': False,
            'error': 'Method Not Allowed',
            'message': 'The request method is not allowed for this resource'
        }, 405
    
    @app.errorhandler(413)
    def payload_too_large(error):
        app.logger.warning(f"Payload too large from {request.remote_addr}")
        return {
            'success': False,
            'error': 'Payload Too Large',
            'message': 'The request payload is too large'
        }, 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        app.logger.warning(f"Rate limit exceeded from {request.remote_addr}")
        return {
            'success': False,
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.'
        }, 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return {
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }, 500
    
    @app.errorhandler(WhatsAppServiceError)
    def whatsapp_service_error(error):
        app.logger.error(f"WhatsApp service error: {error}")
        return {
            'success': False,
            'error': 'Service Unavailable',
            'message': 'WhatsApp service is currently unavailable'
        }, 503


def setup_request_logging(app: Flask) -> None:
    """
    Configure request/response logging middleware.
    
    Args:
        app: Flask application instance
        
    WHY: Request logging provides audit trail and helps with debugging
    """
    
    @app.before_request
    def log_request_info():
        if not request.path.startswith('/health'):  # Skip health check logs
            app.logger.info(
                f"Request: {request.method} {request.path} from {request.remote_addr} "
                f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
            )
    
    @app.after_request
    def log_response_info(response):
        if not request.path.startswith('/health'):  # Skip health check logs
            app.logger.info(
                f"Response: {response.status_code} for {request.method} {request.path} "
                f"to {request.remote_addr}"
            )
        return response


def initialize_services(app: Flask, config: Config) -> tuple:
    """
    Initialize and configure application services.
    
    Args:
        app: Flask application instance
        config: Configuration object
        
    Returns:
        Tuple of (whatsapp_service, webhook_handler)
        
    WHY: Service initialization with proper error handling and logging
    """
    
    try:
        # Initialize WhatsApp service
        whatsapp_config = config.get_whatsapp_config()
        whatsapp_service = WhatsAppService(whatsapp_config)
        
        # Initialize webhook handler
        webhook_handler = AttendanceWebhookHandler(whatsapp_service)
        
        app.logger.info("All services initialized successfully")
        return whatsapp_service, webhook_handler
        
    except Exception as e:
        app.logger.error(f"Failed to initialize services: {e}")
        raise


def main():
    """
    Main application entry point.
    
    WHY: Separate main function allows for proper application lifecycle
    management and easier testing
    """
    
    # Get environment from environment variable
    environment = os.environ.get('FLASK_ENV', 'development')
    
    try:
        # Create and configure Flask app
        app = create_app(environment)
        config = get_config(environment)
        
        # Setup logging
        setup_logging(app, config)
        
        # Setup rate limiting
        limiter = setup_rate_limiting(app, config)
        
        # Setup error handlers
        setup_error_handlers(app)
        
        # Setup request logging
        setup_request_logging(app)
        
        # Initialize services
        whatsapp_service, webhook_handler = initialize_services(app, config)
        
        # Create webhook routes
        create_webhook_routes(app, webhook_handler, config.WHATSAPP_VERIFY_TOKEN)
        
        app.logger.info(f"Starting Flask application in {environment} mode")
        app.logger.info(f"Server will run on {config.HOST}:{config.PORT}")
        
        # Run the application
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            threaded=True
        )
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)


# Create app instance for gunicorn
def create_gunicorn_app():
    """Create Flask app for gunicorn with full configuration."""
    environment = os.environ.get('FLASK_ENV', 'development')
    
    # Create and configure Flask app
    flask_app = create_app(environment)
    config = get_config(environment)
    
    # Setup logging
    setup_logging(flask_app, config)
    
    # Setup rate limiting
    limiter = setup_rate_limiting(flask_app, config)
    
    # Setup error handlers
    setup_error_handlers(flask_app)
    
    # Setup request logging
    setup_request_logging(flask_app)
    
    # Initialize services
    whatsapp_service, webhook_handler = initialize_services(flask_app, config)
    
    # Create webhook routes
    create_webhook_routes(flask_app, webhook_handler, config.WHATSAPP_VERIFY_TOKEN)
    
    return flask_app

# Create app instance for gunicorn
app = create_gunicorn_app()

if __name__ == '__main__':
    main()