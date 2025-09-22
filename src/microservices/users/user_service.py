import os
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client, Client


SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
CURRENT_USER_ID: Optional[str] = os.getenv("VITE_TASK_OWNER_ID")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

if not CURRENT_USER_ID:
    raise RuntimeError("VITE_TASK_OWNER_ID is required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)
CORS(app)


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
    """Get the current active user info using the userid from .env"""
    try:
        response = supabase.table("user").select("*").eq("user_id", CURRENT_USER_ID).execute()
        
        if response.data and len(response.data) > 0:
            user_row = response.data[0]
            user_data = map_db_row_to_api(user_row)
            return jsonify({"user": user_data})
        else:
            return jsonify({"error": "User not found", "user_id": CURRENT_USER_ID}), 404

    except Exception as exc:
        return jsonify({"error": str(exc), "user_id": CURRENT_USER_ID}), 500


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)