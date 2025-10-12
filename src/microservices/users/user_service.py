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
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True,
        "max_age": 3600
    }
})


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
        "superior": row.get("superior"),
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


@app.get("/users")
def get_all_users():
    """Get all active users (for admin purposes or fallback)"""
    try:
        response = supabase.table("user").select(
            "user_id, name, email, role, department, superior"
        ).eq("is_active", True).order("name").execute()

        users = []
        for user in response.data or []:
            users.append({
                "user_id": user.get("user_id"),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role"),
                "department": user.get("department"),
                "superior": user.get("superior")
            })

        return jsonify({"users": users}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch users: {str(e)}"}), 500


@app.get("/users/<user_id>")
def get_user_by_id(user_id: str):
    """Get a specific user by their ID"""
    try:
        response = supabase.table("user").select(
            "user_id, name, email, role, department, superior, is_active, created_at, updated_at"
        ).eq("user_id", user_id).execute()

        if not response.data or len(response.data) == 0:
            return jsonify({"error": "User not found"}), 404

        user_data = response.data[0]
        user_info = map_db_row_to_api(user_data)

        return jsonify({"user": user_info}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch user: {str(e)}"}), 500


@app.get("/users/<user_id>/possible-superiors")
def get_possible_superiors(user_id: str):
    """Get possible superiors for a user based on role hierarchy and department"""
    try:
        # First get the user's info
        user_response = supabase.table("user").select("*").eq("user_id", user_id).execute()
        
        if not user_response.data:
            return jsonify({"error": "User not found"}), 404
        
        current_user = user_response.data[0]
        user_role = current_user.get("role")
        user_department = current_user.get("department")
        
        # Define role hierarchy (what roles can be superiors to what roles)
        superior_roles = {
            "Staff": ["Manager", "Director"],
            "Manager": ["Director"],
            "Director": [],  # Directors typically don't have superiors
            "Hr": ["Director"]  # HR reports to Director
        }
        
        possible_superior_roles = superior_roles.get(user_role, [])
        
        if not possible_superior_roles:
            return jsonify({"possible_superiors": []}), 200
        
        # Get users with superior roles in the same department
        superiors_response = supabase.table("user").select(
            "user_id, name, email, role, department"
        ).in_("role", possible_superior_roles).eq("department", user_department).eq("is_active", True).execute()
        
        superiors = []
        for user in superiors_response.data or []:
            # Don't include the user themselves
            if user.get("user_id") != user_id:
                superiors.append({
                    "user_id": user.get("user_id"),
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "role": user.get("role"),
                    "department": user.get("department")
                })
        
        return jsonify({"possible_superiors": superiors}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch possible superiors: {str(e)}"}), 500


@app.get("/users/departments/<department>")
def get_users_by_department(department: str):
    """Get all active users in a specific department"""
    try:
        response = supabase.table("user").select(
            "user_id, name, email, role, department, superior"
        ).eq("department", department).eq("is_active", True).order("role", desc=True).order("name").execute()
        
        users = []
        for user in response.data or []:
            users.append({
                "user_id": user.get("user_id"),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role"),
                "department": user.get("department"),
                "superior": user.get("superior")
            })
        
        return jsonify({"users": users, "department": department}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch users for department {department}: {str(e)}"}), 500


@app.get("/users/<user_id>/subordinates")
def get_user_subordinates(user_id: str):
    """Get subordinates for a Manager or Director user"""
    try:
        # First get the current user's info to determine their role and department
        user_response = supabase.table("user").select("*").eq("user_id", user_id).execute()
        
        if not user_response.data:
            return jsonify({"error": "User not found"}), 404
        
        current_user = user_response.data[0]
        user_role = current_user.get("role")
        user_department = current_user.get("department")
        
        # Only Manager and Director can have subordinates
        if user_role not in ["Manager", "Director"]:
            return jsonify({"subordinates": []}), 200
        
        # Define role hierarchy
        role_hierarchy = {
            "Director": ["Manager", "Staff"],
            "Manager": ["Staff"]
        }
        
        subordinate_roles = role_hierarchy.get(user_role, [])
        
        if not subordinate_roles:
            return jsonify({"subordinates": []}), 200
        
        # Get users who have the current user as their superior
        # This provides a more accurate hierarchy than just role + department matching
        direct_subordinates_response = supabase.table("user").select(
            "user_id, name, email, role, department, superior"
        ).eq("superior", user_id).eq("is_active", True).execute()
        
        # Also get users with subordinate roles in the same department as fallback
        # (for cases where superior relationships haven't been fully established)
        role_based_subordinates_response = supabase.table("user").select(
            "user_id, name, email, role, department, superior"
        ).in_("role", subordinate_roles).eq("department", user_department).eq("is_active", True).execute()
        
        # Combine both approaches: prioritize direct superior relationships, 
        # but include role-based matches as fallback
        subordinates_dict = {}
        
        # Add direct subordinates (highest priority)
        for user in direct_subordinates_response.data or []:
            subordinates_dict[user.get("user_id")] = {
                "user_id": user.get("user_id"),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role"),
                "department": user.get("department"),
                "superior": user.get("superior"),
                "relationship_type": "direct"
            }
        
        # Add role-based subordinates if they don't already exist
        for user in role_based_subordinates_response.data or []:
            user_id_key = user.get("user_id")
            if user_id_key not in subordinates_dict:
                subordinates_dict[user_id_key] = {
                    "user_id": user.get("user_id"),
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "role": user.get("role"),
                    "department": user.get("department"),
                    "superior": user.get("superior"),
                    "relationship_type": "role_based"
                }
        
        subordinates = list(subordinates_dict.values())
        
        return jsonify({"subordinates": subordinates}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch subordinates: {str(e)}"}), 500


@app.put("/users/<user_id>")
def update_user(user_id: str):
    """Update user information (currently supports updating name only)"""
    try:
        # Get session token from Authorization header
        session_token = request.headers.get('Authorization')

        if not session_token or not session_token.startswith('Bearer '):
            return jsonify({"error": "No valid session token provided"}), 401

        # Extract session token
        session_token = session_token[7:]  # Remove 'Bearer ' prefix

        # Validate session and get user data
        current_user = validate_session(session_token)

        if not current_user:
            return jsonify({"error": "Invalid or expired session"}), 401

        # Check if user is updating their own profile
        if current_user.get('user_id') != user_id:
            return jsonify({"error": "You can only update your own profile"}), 403

        # Get update data from request
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Only allow updating certain fields
        allowed_fields = ['name']
        update_data = {}

        for field in allowed_fields:
            if field in data:
                # Validate name
                if field == 'name':
                    name = data[field].strip() if data[field] else ''
                    if not name:
                        return jsonify({"error": "Name cannot be empty"}), 400
                    if len(name) > 20:
                        return jsonify({"error": "Name must not exceed 20 characters"}), 400
                    update_data[field] = name

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Add updated_at timestamp
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()

        # Update user in database
        response = supabase.table("user").update(update_data).eq("user_id", user_id).execute()

        if not response.data or len(response.data) == 0:
            return jsonify({"error": "User not found or update failed"}), 404

        updated_user = response.data[0]
        user_info = map_db_row_to_api(updated_user)

        return jsonify({"user": user_info, "message": "User updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update user: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)