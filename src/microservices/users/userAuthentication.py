import os
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import bcrypt

load_dotenv()

# Supabase configuration
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)
CORS(app, resources={r"/auth/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}}, supports_credentials=True)

# Constants
MAX_FAILED_ATTEMPTS = 5
ACCOUNT_LOCK_DURATION = timedelta(minutes=15)  # 15 minutes lockout
SESSION_TIMEOUT = timedelta(minutes=15)  # 15 minutes session timeout


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)


def is_account_locked(user_data: Dict[str, Any]) -> bool:
    """Check if account is currently locked"""
    if user_data.get('is_locked') and user_data.get('locked_until'):
        lock_until = datetime.fromisoformat(user_data['locked_until'].replace('Z', '+00:00'))
        if datetime.now(lock_until.tzinfo) < lock_until:
            return True
        else:
            # Unlock account if lock period has passed
            supabase.table("user").update({
                "is_locked": False,
                "locked_until": None
            }).eq("user_id", user_data['user_id']).execute()
            return False
    return user_data.get('is_locked', False)


def increment_failed_attempts(user_id: str, current_attempts: int):
    """Increment failed login attempts and lock account if necessary"""
    new_attempts = current_attempts + 1

    if new_attempts >= MAX_FAILED_ATTEMPTS:
        # Lock the account
        lock_until = datetime.now(timezone.utc) + ACCOUNT_LOCK_DURATION
        supabase.table("user").update({
            "failed_attempts": new_attempts,
            "is_locked": True,
            "locked_until": lock_until.isoformat()
        }).eq("user_id", user_id).execute()
    else:
        # Just increment attempts
        supabase.table("user").update({
            "failed_attempts": new_attempts
        }).eq("user_id", user_id).execute()


def reset_failed_attempts(user_id: str):
    """Reset failed login attempts after successful login"""
    supabase.table("user").update({
        "failed_attempts": 0,
        "is_locked": False,
        "locked_until": None,
        "last_login": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user_id).execute()


def create_session(user_id: str) -> Dict[str, str]:
    """Create a new session for the user and return session info"""
    session_token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + SESSION_TIMEOUT

    # Clean up any existing sessions for this user (optional - allow multiple sessions)
    # supabase.table("user_sessions").delete().eq("user_id", user_id).execute()

    # Create new session
    response = supabase.table("user_sessions").insert({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "last_activity": datetime.now(timezone.utc).isoformat()
    }).execute()

    # Return both session_token and session_id
    session_id = response.data[0]['session_id'] if response.data else None

    return {
        "session_token": session_token,
        "session_id": session_id
    }


def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Validate session token and return user data if valid"""
    try:
        # Get session data including session_id
        session_response = supabase.table("user_sessions").select(
            "session_id, user_id, expires_at, last_activity"
        ).eq("session_token", session_token).execute()
        
        if not session_response.data:
            return None
            
        session_data = session_response.data[0]
        
        # Check if session has expired
        expires_at = datetime.fromisoformat(session_data['expires_at'].replace('Z', '+00:00'))
        last_activity = datetime.fromisoformat(session_data['last_activity'].replace('Z', '+00:00'))
        
        now = datetime.now(expires_at.tzinfo)
        
        # Check both absolute expiration and inactivity timeout
        if now > expires_at or (now - last_activity.replace(tzinfo=expires_at.tzinfo)) > SESSION_TIMEOUT:
            # Session expired, clean it up
            supabase.table("user_sessions").delete().eq("session_token", session_token).execute()
            return None
        
        # Update last activity
        supabase.table("user_sessions").update({
            "last_activity": datetime.now(timezone.utc).isoformat()
        }).eq("session_token", session_token).execute()
        
        # Get user data
        user_response = supabase.table("user").select("*").eq("user_id", session_data['user_id']).execute()

        if user_response.data:
            user_data = user_response.data[0]
            # Add session_id to user data for audit logging
            user_data['session_id'] = session_data['session_id']
            return user_data

        return None
        
    except Exception as e:
        print(f"Session validation error: {e}")
        return None


@app.route("/auth/login", methods=["POST"])
def login():
    """Login endpoint with security features"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password are required"}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Get user by email
        user_response = supabase.table("user").select("*").eq("email", email).execute()
        
        if not user_response.data:
            return jsonify({"error": "Invalid email or password"}), 401
        
        user_data = user_response.data[0]
        
        # Check if account is locked
        if is_account_locked(user_data):
            return jsonify({
                "error": "Account temporarily locked due to multiple failed login attempts. Please try again later."
            }), 423  # 423 Locked status code
        
        # Check if account is active
        if not user_data.get('is_active', True):
            return jsonify({"error": "Account is deactivated"}), 401
        
        # Verify password
        if not verify_password(password, user_data['password']):
            # Increment failed attempts
            increment_failed_attempts(user_data['user_id'], user_data.get('failed_attempts', 0))
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Successful login - reset failed attempts
        reset_failed_attempts(user_data['user_id'])

        # Create session
        session_info = create_session(user_data['user_id'])

        # Return user data (excluding sensitive information)
        user_info = {
            "user_id": user_data['user_id'],
            "email": user_data['email'],
            "name": user_data['name'],
            "role": user_data.get('role'),
            "department": user_data.get('department'),
            "superior": user_data.get('superior'),
            "session_id": session_info['session_id']
        }

        return jsonify({
            "message": "Login successful",
            "user": user_info,
            "session_token": session_info['session_token']
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "An error occurred during login"}), 500


@app.route("/auth/logout", methods=["POST"])
def logout():
    """Logout endpoint"""
    try:
        session_token = request.headers.get('Authorization')
        
        if session_token and session_token.startswith('Bearer '):
            session_token = session_token[7:]  # Remove 'Bearer ' prefix
            
            # Delete the session
            supabase.table("user_sessions").delete().eq("session_token", session_token).execute()
        
        return jsonify({"message": "Logout successful"}), 200
        
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({"error": "An error occurred during logout"}), 500


@app.route("/auth/validate", methods=["GET"])
def validate_session_endpoint():
    """Validate session endpoint"""
    try:
        session_token = request.headers.get('Authorization')
        
        if not session_token or not session_token.startswith('Bearer '):
            return jsonify({"error": "No valid session token provided"}), 401
        
        session_token = session_token[7:]  # Remove 'Bearer ' prefix
        
        user_data = validate_session(session_token)
        
        if not user_data:
            return jsonify({"error": "Invalid or expired session"}), 401
        
        # Return user info (excluding sensitive data)
        user_info = {
            "user_id": user_data['user_id'],
            "email": user_data['email'],
            "name": user_data['name'],
            "role": user_data.get('role'),
            "department": user_data.get('department'),
            "superior": user_data.get('superior'),
            "session_id": user_data.get('session_id')
        }

        return jsonify({"user": user_info}), 200
        
    except Exception as e:
        print(f"Session validation error: {e}")
        return jsonify({"error": "An error occurred during session validation"}), 500


@app.route("/auth/audit-log", methods=["POST"])
def audit_log():
    """Log audit events for session management and security"""
    try:
        session_token = request.headers.get('Authorization')

        if not session_token or not session_token.startswith('Bearer '):
            return jsonify({"error": "No valid session token provided"}), 401

        session_token = session_token[7:]  # Remove 'Bearer ' prefix

        # Validate session and get user
        user_data = validate_session(session_token)

        if not user_data:
            return jsonify({"error": "Invalid or expired session"}), 401

        # Get request data
        data = request.get_json()

        if not data or not data.get('event_type'):
            return jsonify({"error": "event_type is required"}), 400

        event_type = data['event_type']
        event_description = data.get('event_description', '')
        metadata = data.get('metadata', {})

        # Get client information
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')

        # Insert audit log with session_id
        supabase.table("audit_logs").insert({
            "user_id": user_data['user_id'],
            "session_id": user_data.get('session_id'),  # Now using session_id instead of session_token
            "event_type": event_type,
            "event_description": event_description,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": metadata
        }).execute()

        return jsonify({"message": "Audit log created successfully"}), 201

    except Exception as e:
        print(f"Audit log error: {e}")
        return jsonify({"error": "An error occurred while creating audit log"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Simple check - just return 200 if service is responding
        return jsonify({"status": "healthy", "service": "auth-service"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.route("/auth/register", methods=["POST"])
def register():
    """Register new user (for testing purposes)"""
    try:
        data = request.get_json()
        
        required_fields = ['email', 'password', 'name']
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "Email, password, and name are required"}), 400
        
        email = data['email'].lower().strip()
        
        # Check if user already exists
        existing_user = supabase.table("user").select("email").eq("email", email).execute()
        
        if existing_user.data:
            return jsonify({"error": "User already exists"}), 409
        
        # Hash password
        password_hash = hash_password(data['password'])
        
        # Create user
        user_data = {
            "email": email,
            "password": password_hash,
            "name": data['name'],
            "role": data.get('role', 'user'),
            "department": data.get('department'),
            "superior": data.get('superior'),
            "is_active": True
        }
        
        response = supabase.table("user").insert(user_data).execute()
        
        if response.data:
            return jsonify({"message": "User registered successfully"}), 201
        else:
            return jsonify({"error": "Failed to register user"}), 500
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"error": "An error occurred during registration"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8086, debug=True)