import os
from typing import Optional, Dict, Any, List

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
        "Missing 'supabase' client. Run: pip install -r microservices/requirements.txt"
    ) from exc


SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)
CORS(app)


def map_db_row_to_api(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("task_id") or row.get("id"),
        "title": row.get("title"),
        "dueDate": row.get("due_date"),
        "status": row.get("status"),
    }


@app.get("/tasks")
def get_tasks():
    try:
        limit_param = request.args.get("limit", default=None, type=int)
        owner_id = request.args.get("owner_id", default=None, type=str)
        task_id = request.args.get("task_id", default=None, type=str)
        query = (
            supabase
            .table("task")
            .select("task_id,title,due_date,status,created_at")
            .order("created_at", desc=True)
        )
        if limit_param:
            query = query.limit(limit_param)
        if owner_id:
            query = query.eq("owner_id", owner_id)
        if task_id:
            query = query.eq("task_id", task_id)

        response = query.execute()
        rows: List[Dict[str, Any]] = response.data or []
        tasks = [map_db_row_to_api(r) for r in rows]
        return jsonify({"tasks": tasks})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

