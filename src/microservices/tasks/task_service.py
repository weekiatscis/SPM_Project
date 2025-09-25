import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from pydantic import BaseModel, ValidationError

# Environment variables
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Initialize Flask app
app = Flask(__name__)
CORS(app)


# Pydantic models for request validation
class TaskCreate(BaseModel):
    title: str
    due_date: Optional[str] = None
    status: Optional[str] = "Unassigned"
    owner_id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None


# Helper functions
def map_db_row_to_api(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert database row to API response format"""
    return {
        "id": row.get("task_id") or row.get("id"),
        "title": row.get("title"),
        "description": row.get("description", "No description available"),  # Default if not in DB
        "dueDate": row.get("due_date"),
        "status": row.get("status"),
        "owner_id": row.get("owner_id"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at", row.get("created_at"))  # Use created_at if updated_at doesn't exist
    }

def validate_task_id(task_id: str) -> bool:
    """Validate task ID format"""
    return task_id and task_id.strip()

def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """Get a single task by ID"""
    try:
        response = supabase.table("task").select("task_id,title,due_date,status,created_at,owner_id").eq("task_id", task_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
        return None


# API Routes

@app.route("/tasks", methods=["GET"])
def get_tasks():
    """
    GET /tasks - Retrieve tasks with optional filtering
    Query parameters:
    - limit: Maximum number of tasks to return
    - owner_id: Filter by owner ID
    - task_id: Get specific task by ID
    - status: Filter by status
    - priority: Filter by priority
    """
    try:
        # Parse query parameters
        limit_param = request.args.get("limit", default=None, type=int)
        owner_id = request.args.get("owner_id", default=None, type=str)
        task_id = request.args.get("task_id", default=None, type=str)
        status = request.args.get("status", default=None, type=str)
        priority = request.args.get("priority", default=None, type=str)

        # Build query - only select fields that definitely exist in the database
        query = (
            supabase
            .table("task")
            .select("task_id,title,due_date,status,created_at,owner_id")
            .order("created_at", desc=True)
        )

        # Apply filters
        if limit_param:
            query = query.limit(limit_param)
        if owner_id:
            query = query.eq("owner_id", owner_id)
        if task_id:
            query = query.eq("task_id", task_id)
        if status:
            query = query.eq("status", status)
        if priority:
            query = query.eq("priority", priority)

        # Execute query
        response = query.execute()
        rows: List[Dict[str, Any]] = response.data or []
        
        # Map to API format
        tasks = [map_db_row_to_api(row) for row in rows]
        
        return jsonify({"tasks": tasks, "count": len(tasks)}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve tasks: {str(exc)}"}), 500


@app.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id: str):
    """
    GET /tasks/<task_id> - Get a specific task by ID
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        task_data = get_task_by_id(task_id)
        if not task_data:
            return jsonify({"error": "Task not found"}), 404

        task = map_db_row_to_api(task_data)
        return jsonify({"task": task}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve task: {str(exc)}"}), 500


@app.route("/tasks", methods=["POST"])
def create_task():
    """
    POST /tasks - Create a new task
    """
    try:
        body = request.get_json(silent=True) or {}
        
        # Validate request body
        try:
            task_data = TaskCreate(**body)
        except ValidationError as e:
            return jsonify({"error": "Invalid request data", "details": e.errors()}), 400

        # Prepare data for database
        db_data = task_data.dict()
        db_data["created_at"] = datetime.utcnow().isoformat()

        # Insert into database
        response = supabase.table("task").insert(db_data).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to create task"}), 500

        # Return created task
        created_task = map_db_row_to_api(response.data[0])
        return jsonify({"task": created_task, "message": "Task created successfully"}), 201

    except Exception as exc:
        return jsonify({"error": f"Failed to create task: {str(exc)}"}), 500


@app.route("/tasks/<task_id>", methods=["PUT"])
def update_task(task_id: str):
    """
    PUT /tasks/<task_id> - Update an existing task
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        # Check if task exists
        existing_task = get_task_by_id(task_id)
        if not existing_task:
            return jsonify({"error": "Task not found"}), 404

        body = request.get_json(silent=True) or {}
        
        # Validate request body
        try:
            task_data = TaskUpdate(**body)
        except ValidationError as e:
            return jsonify({"error": "Invalid request data", "details": e.errors()}), 400

        # Prepare update data (only include non-None values)
        update_data = {k: v for k, v in task_data.dict().items() if v is not None}

        # Update in database
        response = supabase.table("task").update(update_data).eq("task_id", task_id).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to update task"}), 500

        # Return updated task
        updated_task = map_db_row_to_api(response.data[0])
        return jsonify({"task": updated_task, "message": "Task updated successfully"}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to update task: {str(exc)}"}), 500


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    """
    DELETE /tasks/<task_id> - Delete a task
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        # Check if task exists
        existing_task = get_task_by_id(task_id)
        if not existing_task:
            return jsonify({"error": "Task not found"}), 404

        # Delete from database
        response = supabase.table("task").delete().eq("task_id", task_id).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to delete task"}), 500

        return jsonify({"message": "Task deleted successfully", "task_id": task_id}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to delete task: {str(exc)}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "task-service"}), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

