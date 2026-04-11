"""
Secure Flask Web UI for CV Intelligence System with Authentication
Production-ready version with login, rate limiting, and security features
"""
import os
import sys

# Add authentication and security
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# Import the original app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import *  # Import all from original app
from auth import UserManager, User

# Initialize authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://"
)

# Enable CORS for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize user manager
user_manager = UserManager()

# Update secret key for production
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

# Security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return user_manager.get_user_by_id(user_id)


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        user = user_manager.authenticate(username, password)
        
        if user:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page"""
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not old_password or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('change_password.html')
        
        if user_manager.change_password(current_user.id, old_password, new_password):
            flash('Password changed successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Current password is incorrect', 'error')
    
    return render_template('change_password.html')


@app.route('/admin/users')
@login_required
def admin_users():
    """Admin page to manage users"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    users = user_manager.list_users()
    return render_template('admin_users.html', users=users)


@app.route('/admin/create-user', methods=['POST'])
@login_required
def admin_create_user():
    """Create a new user (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'user')
    
    if not username or not email or not password:
        flash('All fields are required', 'error')
        return redirect(url_for('admin_users'))
    
    if len(password) < 8:
        flash('Password must be at least 8 characters long', 'error')
        return redirect(url_for('admin_users'))
    
    user = user_manager.create_user(username, email, password, role)
    
    if user:
        flash(f'User {username} created successfully', 'success')
    else:
        flash(f'Username {username} already exists', 'error')
    
    return redirect(url_for('admin_users'))


@app.route('/admin/delete-user/<user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Delete a user (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    if user_id == current_user.id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    if user_manager.delete_user(user_id):
        flash('User deleted successfully', 'success')
    else:
        flash('Cannot delete user (last admin or not found)', 'error')
    
    return redirect(url_for('admin_users'))


# ============================================================================
# PROTECTED ROUTES - Add @login_required to all existing routes
# ============================================================================

# Override index route to require login
@app.route('/')
@login_required
def index():
    """Main page - redirect to redactor"""
    mode = request.args.get('mode', 'redactor')
    if mode == 'upload':
        return redirect(url_for('upload_page'))
    return redirect(url_for('redactor_page'))


@app.route('/redactor')
@login_required
def redactor_page():
    """CV Redactor page (requires login)"""
    return render_template('redactor.html')


@app.route('/upload')
@login_required
def upload_page():
    """Upload & Process page (requires login)"""
    return render_template('upload.html')


@app.route('/search')
@login_required
def search_page():
    """Search page (requires login)"""
    return render_template('search.html')


@app.route('/dashboard')
@login_required
def dashboard_page():
    """Dashboard page (requires login)"""
    return render_template('dashboard.html')


# Add rate limiting to API endpoints
@app.route('/api/redact', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_redact():
    """API endpoint for CV redaction (protected)"""
    # Original implementation from app.py
    return redact_cv()


@app.route('/api/upload', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def api_upload():
    """API endpoint for CV upload (protected)"""
    # Original implementation from app.py
    return upload_cv()


@app.route('/api/search', methods=['POST'])
@login_required
@limiter.limit("60 per minute")
def api_search():
    """API endpoint for candidate search (protected)"""
    # Original implementation from app.py
    return search_candidates()


# Health check endpoint (no auth required)
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'features': {
            'authentication': True,
            'rate_limiting': True,
            'supabase': is_supabase_configured(),
            'llm': bool(os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY'))
        }
    })


if __name__ == '__main__':
    # Production mode
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    if debug:
        print("=" * 60)
        print("CV INTELLIGENCE SYSTEM - SECURE VERSION")
        print("=" * 60)
        print(f"Running on: http://localhost:{port}")
        print("Default login: admin / admin123")
        print("⚠️  Change the admin password immediately!")
        print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
