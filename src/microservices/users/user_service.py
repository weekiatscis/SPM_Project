import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client, Client


SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
# Remove the hardcoded user ID requirement
CURRENT_USER_ID: Optional[str] = os.getenv("VITE_TASK_OWNER_ID")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

# CURRENT_USER_ID is now optional - we'll use session-based authentication

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)
CORS(app)

# Session timeout constant
SESSION_TIMEOUT = timedelta(minutes=15)


def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Validate session token and return user data if valid"""
    try:
        # Get session data
        session_response = supabase.table("user_sessions").select(
            "user_id, expires_at, last_activity"
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
            return user_response.data[0]
            
        return None
        
    except Exception as e:
        print(f"Session validation error: {e}")
        return None


def map_db_row_to_api(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user_id": row.get("user_id"),
        "name": row.get("name"),
        "email": row.get("email"),
        "role": row.get("role"),
        "department": row.get("department"),
        "is_active": row.get("is_active"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at")
    }


@app.get("/user")
def get_current_user():
    """Get the current authenticated user info using session token"""
    try:
        # Get session token from Authorization header
        session_token = request.headers.get('Authorization')
        
        if not session_token or not session_token.startswith('Bearer '):
            # Fallback: If no session token provided, use the hardcoded user ID for backward compatibility
            if CURRENT_USER_ID:
                response = supabase.table("user").select("*").eq("user_id", CURRENT_USER_ID).execute()
                
                if response.data and len(response.data) > 0:
                    user_row = response.data[0]
                    user_data = map_db_row_to_api(user_row)
                    return jsonify({"user": user_data})
                else:
                    return jsonify({"error": "User not found", "user_id": CURRENT_USER_ID}), 404
            else:
                return jsonify({"error": "No valid session token provided"}), 401
        
        # Extract session token
        session_token = session_token[7:]  # Remove 'Bearer ' prefix
        
        # Validate session and get user data
        user_data = validate_session(session_token)
        
        if not user_data:
            return jsonify({"error": "Invalid or expired session"}), 401
        
        # Map to API format
        user_info = map_db_row_to_api(user_data)
        return jsonify({"user": user_info})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)