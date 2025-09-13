"""
API error handling and response formatting.
"""
from flask import jsonify, request, current_app
from flask_restx import fields
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
import traceback
from datetime import datetime


class APIError(Exception):
    """Custom API exception class."""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


class ErrorResponse:
    """Standardized error response format."""
    
    @staticmethod
    def format_error(message, status_code=400, details=None, error_code=None):
        """Format error response."""
        response = {
            'error': {
                'message': message,
                'status_code': status_code,
                'timestamp': datetime.utcnow().isoformat(),
                'path': request.path if request else None
            }
        }
        
        if details:
            response['error']['details'] = details
        
        if error_code:
            response['error']['code'] = error_code
        
        # Add request ID for tracing
        if hasattr(request, 'id'):
            response['error']['request_id'] = request.id
        
        return response, status_code
    
    @staticmethod
    def validation_error(errors):
        """Format validation error response."""
        return ErrorResponse.format_error(
            message="Validation failed",
            status_code=400,
            details=errors,
            error_code="VALIDATION_ERROR"
        )
    
    @staticmethod
    def authentication_error():
        """Format authentication error response."""
        return ErrorResponse.format_error(
            message="Authentication required",
            status_code=401,
            error_code="AUTHENTICATION_REQUIRED"
        )
    
    @staticmethod
    def authorization_error():
        """Format authorization error response."""
        return ErrorResponse.format_error(
            message="Access denied",
            status_code=403,
            error_code="ACCESS_DENIED"
        )
    
    @staticmethod
    def not_found_error(resource="Resource"):
        """Format not found error response."""
        return ErrorResponse.format_error(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def conflict_error(message="Resource already exists"):
        """Format conflict error response."""
        return ErrorResponse.format_error(
            message=message,
            status_code=409,
            error_code="CONFLICT"
        )
    
    @staticmethod
    def rate_limit_error():
        """Format rate limit error response."""
        return ErrorResponse.format_error(
            message="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED"
        )
    
    @staticmethod
    def internal_error():
        """Format internal server error response."""
        return ErrorResponse.format_error(
            message="Internal server error",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )


def register_error_handlers(api):
    """Register error handlers with Flask-RESTX API."""
    
    @api.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle Marshmallow validation errors."""
        return ErrorResponse.validation_error(error.messages)
    
    @api.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        return ErrorResponse.format_error(
            message=error.message,
            status_code=error.status_code,
            details=error.payload
        )
    
    @api.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        return ErrorResponse.not_found_error()
    
    @api.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 errors."""
        return ErrorResponse.authorization_error()
    
    @api.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 errors."""
        return ErrorResponse.authentication_error()
    
    @api.errorhandler(409)
    def handle_conflict(error):
        """Handle 409 errors."""
        return ErrorResponse.conflict_error()
    
    @api.errorhandler(429)
    def handle_rate_limit(error):
        """Handle 429 errors."""
        return ErrorResponse.rate_limit_error()
    
    @api.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 errors."""
        # Log the error
        current_app.logger.error(f"Internal server error: {str(error)}")
        current_app.logger.error(traceback.format_exc())
        
        return ErrorResponse.internal_error()
    
    @api.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        # Log the error
        current_app.logger.error(f"Unexpected error: {str(error)}")
        current_app.logger.error(traceback.format_exc())
        
        return ErrorResponse.internal_error()


# Flask-RESTX error models for documentation
def create_error_models(api):
    """Create error models for API documentation."""
    
    error_model = api.model('Error', {
        'message': fields.String(description='Error message'),
        'status_code': fields.Integer(description='HTTP status code'),
        'timestamp': fields.String(description='Error timestamp'),
        'path': fields.String(description='Request path'),
        'code': fields.String(description='Error code'),
        'details': fields.Raw(description='Additional error details'),
        'request_id': fields.String(description='Request ID for tracing')
    })
    
    error_response_model = api.model('ErrorResponse', {
        'error': fields.Nested(error_model, description='Error information')
    })
    
    validation_error_model = api.model('ValidationError', {
        'error': fields.Nested(error_model, description='Validation error information')
    })
    
    return {
        'error': error_model,
        'error_response': error_response_model,
        'validation_error': validation_error_model
    }