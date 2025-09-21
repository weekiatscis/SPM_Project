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
        "project_id": row.get("project_id"),
        "project_name": row.get("project_name"),
        "project_description": row.get("project_description"),
        "created_at": row.get("created_at"),
        "created_by": row.get("created_by")
    }


@app.get("/projects")
def get_projects():
    try:
        limit_param = request.args.get("limit", default=None, type=int)
        owner_id = request.args.get("owner_id", default=None, type=str)
        project_id = request.args.get("project_id", default=None, type=str)

        query = (
            supabase
            .table("project")
            .select("project_id,project_name,project_description,created_at,created_by")
            .order("created_at", desc=True)
        )

        if limit_param:
            query = query.limit(limit_param)
        if owner_id:
            query = query.eq("created_by", owner_id)  # Use created_by instead of owner_id
        if project_id:
            query = query.eq("project_id", project_id)

        response = query.execute()
        rows: List[Dict[str, Any]] = response.data or []
        projects = [map_db_row_to_api(r) for r in rows]
        return jsonify({"projects": projects})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8083)