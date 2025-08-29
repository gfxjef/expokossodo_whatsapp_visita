"""
WSGI entry point for gunicorn deployment.

This module provides the WSGI application object that gunicorn expects.
It creates a properly configured Flask application without interfering
with the main application entry point.
"""

import os
from app import create_app, get_config, setup_logging, setup_rate_limiting
from app import setup_error_handlers, setup_request_logging, initialize_services
from handlers.webhook_handler import create_webhook_routes


def create_wsgi_app():
    """Create Flask application for WSGI deployment."""
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


# Create the WSGI application
application = create_wsgi_app()

# For gunicorn compatibility
app = application