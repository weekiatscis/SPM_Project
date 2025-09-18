import os
from typing import Optional, Dict, Any

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from supabase import create_client, Client
except Exception as exc:
    raise RuntimeError(
        "Missing 'supabase' client. Run: pip install -r requirements.txt"
    ) from exc


SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)
CORS(app)


@app.route("/tasks", methods=["POST"])
def create_task():
    try:
        body = request.get_json(silent=True) or {}
        
        # Validate required fields
        if not body.get("title", "").strip():
            return jsonify({"error": "title is required"}), 400
        
        # Insert directly using Python Supabase client syntax
        response = supabase.table("task").insert(body).execute()
        
        if not response.data:
            return jsonify({"error": "insert failed"}), 500
            
        return jsonify({"task": response.data[0]}), 201
        
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)