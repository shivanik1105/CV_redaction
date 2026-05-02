"""
JWT Authentication for API endpoints.
Protects sensitive operations like upload, search, and candidate access.
"""
import os
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.getenv('SECRET_KEY', 'change-me-in-production'))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

# API Key Configuration (simpler alternative to JWT)
API_KEY = os.getenv('API_KEY')
API_KEY_HEADER = 'X-API-Key'

# Authentication mode: 'jwt', 'api_key', or 'disabled'
AUTH_MODE = os.getenv('AUTH_MODE', 'disabled')


def generate_jwt_token(user_id: str, role: str = 'user', org_id: str = None) -> str:
    """
    Generate JWT token for user.
    
    Args:
        user_id: Unique user identifier
        role: User role (admin, recruiter, user)
        org_id: Organization ID (for multi-tenant)
        
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    
    if org_id:
        payload['org_id'] = org_id
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def get_token_from_request() -> Optional[str]:
    """
    Extract JWT token from request headers.
    Supports both 'Authorization: Bearer <token>' and 'X-Auth-Token: <token>'.
    
    Returns:
        Token string or None
    """
    # Check Authorization header (Bearer token)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    # Check X-Auth-Token header
    token = request.headers.get('X-Auth-Token')
    if token:
        return token
    
    return None


def get_api_key_from_request() -> Optional[str]:
    """
    Extract API key from request headers.
    
    Returns:
        API key string or None
    """
    return request.headers.get(API_KEY_HEADER)


def require_auth(roles: list = None):
    """
    Decorator to protect routes with JWT authentication.
    
    Args:
        roles: List of allowed roles (optional, defaults to any authenticated user)
        
    Usage:
        @app.route('/api/protected')
        @require_auth()
        def protected_route():
            return jsonify({'message': 'Access granted'})
        
        @app.route('/api/admin')
        @require_auth(roles=['admin'])
        def admin_route():
            return jsonify({'message': 'Admin access'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip auth if disabled
            if AUTH_MODE == 'disabled':
                return f(*args, **kwargs)
            
            # API Key authentication
            if AUTH_MODE == 'api_key':
                api_key = get_api_key_from_request()
                if not api_key or api_key != API_KEY:
                    return jsonify({
                        'error': 'Unauthorized',
                        'message': 'Invalid or missing API key'
                    }), 401
                return f(*args, **kwargs)
            
            # JWT authentication
            if AUTH_MODE == 'jwt':
                token = get_token_from_request()
                if not token:
                    return jsonify({
                        'error': 'Unauthorized',
                        'message': 'Missing authentication token'
                    }), 401
                
                payload = decode_jwt_token(token)
                if not payload:
                    return jsonify({
                        'error': 'Unauthorized',
                        'message': 'Invalid or expired token'
                    }), 401
                
                # Check role if specified
                if roles:
                    user_role = payload.get('role')
                    if user_role not in roles:
                        return jsonify({
                            'error': 'Forbidden',
                            'message': f'Insufficient permissions. Required roles: {roles}'
                        }), 403
                
                # Attach user info to request context
                request.user_id = payload.get('user_id')
                request.user_role = payload.get('role')
                request.org_id = payload.get('org_id')
                
                return f(*args, **kwargs)
            
            # Unknown auth mode
            return jsonify({
                'error': 'Server Error',
                'message': 'Invalid authentication configuration'
            }), 500
        
        return decorated_function
    return decorator


def require_api_key(f):
    """
    Simpler decorator for API key authentication only.
    
    Usage:
        @app.route('/api/protected')
        @require_api_key
        def protected_route():
            return jsonify({'message': 'Access granted'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not API_KEY:
            # API key not configured, allow access
            logger.warning("API_KEY not configured - endpoint unprotected")
            return f(*args, **kwargs)
        
        api_key = get_api_key_from_request()
        if not api_key or api_key != API_KEY:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid or missing API key'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def create_auth_routes(app):
    """
    Add authentication routes to Flask app.
    
    Args:
        app: Flask application instance
    """
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """
        Login endpoint - generates JWT token.
        
        Body:
            {
                "username": "user@example.com",
                "password": "password123",
                "org_id": "optional-org-id"
            }
        
        Returns:
            {
                "success": true,
                "token": "jwt-token-here",
                "expires_in": 86400
            }
        """
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        org_id = data.get('org_id')
        
        if not username or not password:
            return jsonify({
                'error': 'Bad Request',
                'message': 'username and password required'
            }), 400
        
        # TODO: Validate credentials against database
        # For now, use simple env-based auth
        valid_username = os.getenv('AUTH_USERNAME', 'admin')
        valid_password = os.getenv('AUTH_PASSWORD', 'admin123')
        
        if username != valid_username or password != valid_password:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid credentials'
            }), 401
        
        # Determine role (admin if username matches admin, else recruiter)
        role = 'admin' if username == valid_username else 'recruiter'
        
        # Generate token
        token = generate_jwt_token(
            user_id=username,
            role=role,
            org_id=org_id
        )
        
        return jsonify({
            'success': True,
            'token': token,
            'expires_in': JWT_EXPIRATION_HOURS * 3600,
            'user': {
                'username': username,
                'role': role,
                'org_id': org_id
            }
        })
    
    @app.route('/api/auth/verify', methods=['GET'])
    @require_auth()
    def verify_token():
        """
        Verify JWT token validity.
        
        Returns:
            {
                "valid": true,
                "user_id": "user@example.com",
                "role": "admin"
            }
        """
        return jsonify({
            'valid': True,
            'user_id': getattr(request, 'user_id', None),
            'role': getattr(request, 'user_role', None),
            'org_id': getattr(request, 'org_id', None)
        })
    
    @app.route('/api/auth/refresh', methods=['POST'])
    @require_auth()
    def refresh_token():
        """
        Refresh JWT token (extend expiration).
        
        Returns:
            {
                "success": true,
                "token": "new-jwt-token-here"
            }
        """
        user_id = getattr(request, 'user_id', None)
        role = getattr(request, 'user_role', None)
        org_id = getattr(request, 'org_id', None)
        
        if not user_id:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid token payload'
            }), 400
        
        # Generate new token
        token = generate_jwt_token(
            user_id=user_id,
            role=role,
            org_id=org_id
        )
        
        return jsonify({
            'success': True,
            'token': token,
            'expires_in': JWT_EXPIRATION_HOURS * 3600
        })
    
    logger.info("✓ Authentication routes registered")


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from request context.
    
    Returns:
        User info dict or None if not authenticated
    """
    if AUTH_MODE == 'disabled':
        return None
    
    return {
        'user_id': getattr(request, 'user_id', None),
        'role': getattr(request, 'user_role', None),
        'org_id': getattr(request, 'org_id', None)
    }


def init_auth(app):
    """
    Initialize authentication for Flask app.
    
    Args:
        app: Flask application instance
    """
    if AUTH_MODE == 'disabled':
        logger.warning("⚠️ Authentication DISABLED - all endpoints are public")
    elif AUTH_MODE == 'api_key':
        if not API_KEY:
            logger.warning("⚠️ API_KEY not set - endpoints unprotected")
        else:
            logger.info(f"✓ API Key authentication enabled (header: {API_KEY_HEADER})")
    elif AUTH_MODE == 'jwt':
        logger.info(f"✓ JWT authentication enabled (expiration: {JWT_EXPIRATION_HOURS}h)")
        create_auth_routes(app)
    else:
        logger.error(f"❌ Invalid AUTH_MODE: {AUTH_MODE}")
    
    return app

