"""
Logging configuration for the application.
Production-safe logging with proper log rotation and sensitive data filtering.
"""

import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(app):
    """
    Setup application logging based on environment.
    
    Production:
    - Logs to file with rotation
    - No sensitive data logged
    - INFO level and above
    
    Development:
    - Logs to console
    - DEBUG level and above
    """
    env = os.environ.get('ENV', 'development')
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Base logging configuration
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if env == 'production':
        # Production: File-based logging with rotation
        log_file = os.path.join(logs_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
        
        # Rotating file handler - 10MB max size, keep 30 backups
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        
        # Also log errors to a separate error log
        error_log_file = os.path.join(logs_dir, 'error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(log_format))
        app.logger.addHandler(error_handler)
        
    else:
        # Development: Console logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)
    
    # Log startup message
    app.logger.info(f'Logging configured for {env} environment')
    
    return app


class SensitiveDataFilter(logging.Filter):
    """
    Filter to prevent sensitive data from being logged.
    Removes passwords, tokens, and other sensitive information.
    """
    
    SENSITIVE_PATTERNS = [
        'password',
        'token',
        'secret',
        'key',
        'credential',
        'credit_card',
        'ssn',
        'api_key',
    ]
    
    def filter(self, record):
        """
        Filter out sensitive data from log records.
        Returns True to allow the record, False to block it.
        """
        # Check if the message contains sensitive patterns
        message = str(record.getMessage()).lower()
        
        # If it contains sensitive data, redact it
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # Redact the entire message or sensitive parts
                record.msg = '[REDACTED - SENSITIVE DATA]'
                record.args = ()
                break
        
        return True


def add_sensitive_filter(logger):
    """Add sensitive data filter to a logger."""
    sensitive_filter = SensitiveDataFilter()
    logger.addFilter(sensitive_filter)
    return logger
