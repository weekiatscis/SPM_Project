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


@app.route("/projects", methods=["POST"])
def create_project():
    try:
        body = request.get_json(silent=True) or {}

        # Validate required fields
        if not body.get("project_name", "").strip():
            return jsonify({"error": "project_name is required"}), 400

        # Prepare project data according to your Supabase schema
        # Fields: project_id (auto), created_at (auto), created_by, project_description, project_name, due_date
        # Use owner_id as created_by to identify user ownership
        project_data = {
            "project_name": body.get("project_name").strip(),
            "project_description": body.get("project_description", "").strip(),
            "created_by": body.get("owner_id") or body.get("created_by", "").strip() or "Unknown",
            "due_date": body.get("due_date")
        }

        # Insert directly using Python Supabase client syntax
        response = supabase.table("project").insert(project_data).execute()

        if not response.data:
            return jsonify({"error": "insert failed"}), 500

        return jsonify({"project": response.data[0]}), 201

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

def map_db_row_to_api(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "project_id": row.get("project_id"),
        "project_name": row.get("project_name"),
        "project_description": row.get("project_description"),
        "created_at": row.get("created_at"),
        "created_by": row.get("created_by"),
        "due_date": row.get("due_date")
    }


@app.get("/projects")
def get_projects():
    try:
        limit_param = request.args.get("limit", default=None, type=int)
        created_by = request.args.get("created_by", default=None, type=str)
        project_id = request.args.get("project_id", default=None, type=str)

        query = (
            supabase
            .table("project")
            .select("project_id,project_name,project_description,created_at,created_by,due_date")
            .order("created_at", desc=True)
        )

        if limit_param:
            query = query.limit(limit_param)
        if created_by:
            query = query.eq("created_by", created_by)
        if project_id:
            query = query.eq("project_id", project_id)

        response = query.execute()
        rows: List[Dict[str, Any]] = response.data or []
        projects = [map_db_row_to_api(r) for r in rows]
        return jsonify({"projects": projects})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    try:
        body = request.get_json(silent=True) or {}

        # Validate required fields
        if not body.get("project_name", "").strip():
            return jsonify({"error": "project_name is required"}), 400

        # Prepare update data
        update_data = {}

        if "project_name" in body:
            update_data["project_name"] = body["project_name"].strip()

        if "project_description" in body:
            update_data["project_description"] = body["project_description"].strip()

        if "due_date" in body:
            update_data["due_date"] = body["due_date"]

        if "created_by" in body:
            update_data["created_by"] = body["created_by"].strip()

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Update the project in Supabase
        response = supabase.table("project").update(update_data).eq("project_id", project_id).execute()

        if not response.data:
            return jsonify({"error": "Project not found or update failed"}), 404

        return jsonify({"project": response.data[0]}), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    try:
        # Delete the project from Supabase
        response = supabase.table("project").delete().eq("project_id", project_id).execute()

        if not response.data:
            return jsonify({"error": "Project not found"}), 404

        return jsonify({"message": "Project deleted successfully"}), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8082))
    app.run(host="0.0.0.0", port=port)