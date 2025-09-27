import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json

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
    priority: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    collaborators: Optional[str] = None
    project_id: Optional[str] = None
    subtasks: Optional[str] = None


# Pydantic model for rescheduling a task
class RescheduleTask(BaseModel):
    actor_id: str
    new_due_date: str

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
    """Get a single task by ID with all fields"""
    try:
        response = supabase.table("task").select("*").eq("task_id", task_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
        return None

def to_yyyy_mm_dd(val):
    if val is None: return None
    if hasattr(val, "isoformat"):  # date/datetime
        return val.isoformat()[:10]
    s = str(val)
    return s[:10]

def map_db_row_to_api(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("task_id") or row.get("id"),
        "title": row.get("title"),
        "description": row.get("description", ""),
        "dueDate": to_yyyy_mm_dd(row.get("due_date")),  # normalize for FE
        "status": row.get("status"),
        "priority": row.get("priority") or "Medium",  # Default to Medium if null
        "owner_id": row.get("owner_id"),
        "project_id": row.get("project_id"),
        "collaborators": row.get("collaborators") or [],
        "subtasks": row.get("subtasks") or [],
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at", row.get("created_at")),
    }

def log_task_change(task_id: str, action: str, field: str, user_id: str,
                    old_value: Any, new_value: Any) -> Optional[Dict[str, Any]]:
    try:
        # Ensure values are JSON-serializable for JSONB storage
        def make_json_serializable(value):
            if value is None:
                return None
            elif isinstance(value, (str, int, float, bool)):
                return value
            elif isinstance(value, (dict, list)):
                return value
            else:
                return str(value)
        
        # Create proper JSON structure for JSONB columns
        old_json = {field: make_json_serializable(old_value)} if not isinstance(old_value, (dict, list)) else old_value
        new_json = {field: make_json_serializable(new_value)} if not isinstance(new_value, (dict, list)) else new_value
        
        log_data = {
            "task_id": task_id,
            "action": action,
            "field": field,
            "user_id": user_id,
            "old_value": old_json,
            "new_value": new_json,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("task_log").insert(log_data).execute()
        
        if not response.data:
            print(f"WARNING: No data returned from task_log insert for task {task_id}")
            return None
            
        return response.data[0]
    except Exception as exc:
        print(f"ERROR: Failed to log task change for {task_id}: {exc}")
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
    - project_id: Filter by project ID
    """
    try:
        # Parse query parameters
        limit_param = request.args.get("limit", default=None, type=int)
        owner_id = request.args.get("owner_id", default=None, type=str)
        task_id = request.args.get("task_id", default=None, type=str)
        status = request.args.get("status", default=None, type=str)
        priority = request.args.get("priority", default=None, type=str)
        project_id = request.args.get("project_id", default=None, type=str)

        # Build query - only select fields that definitely exist in the database
        query = (
            supabase
            .table("task")
            .select("task_id,title,due_date,status,priority,description,created_at,owner_id,project_id")
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
        if project_id:
            query = query.eq("project_id", project_id)

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

        created_task_data = response.data[0]
        task_id = created_task_data.get("task_id")
        
        # Log task creation for audit trail - single log entry with all created fields
        # Define all possible task fields for logging
        task_fields = ["title", "due_date", "status", "priority", "description", 
                      "collaborators", "project_id", "subtasks", "owner_id"]
        
        # Get owner_id for logging (could be from request or default)
        actor_id = db_data.get("owner_id", "system")
        
        # Collect all created field values into single log entry
        old_values = {}
        new_values = {}
        
        for field in task_fields:
            new_value = created_task_data.get(field)
            if new_value is not None:  # Only include fields that were actually set
                # Normalize date fields for consistency
                if field == "due_date" and new_value:
                    new_value = str(new_value)[:10]  # Normalize to YYYY-MM-DD
                
                old_values[field] = None  # No old value for creation
                new_values[field] = new_value
        
        # Create single log entry for task creation
        if new_values:  # Only log if there are values to log
            log_task_change(
                task_id=task_id,
                action="create",
                field="task",  # Use generic field name for creation
                user_id=actor_id,
                old_value=old_values,
                new_value=new_values
            )

        # Return created task
        created_task = map_db_row_to_api(created_task_data)
        return jsonify({"task": created_task, "message": "Task created successfully"}), 201

    except Exception as exc:
        return jsonify({"error": f"Failed to create task: {str(exc)}"}), 500

@app.route("/tasks/<task_id>/logs", methods=["GET"])
def get_task_logs(task_id: str):
    """
    GET /tasks/<task_id>/logs - Get change logs for a specific task
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        # Query task_log table for this task
        response = supabase.table("task_log").select(
            "log_id,task_id,action,user_id,old_value,new_value,created_at,field"
        ).eq("task_id", task_id).order("created_at", desc=False).execute()
        logs = response.data or []

        # Keep logs as JSON objects for frontend processing - do not stringify
        # The frontend will handle formatting the values appropriately
        return jsonify({"logs": logs, "count": len(logs)}), 200
    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve logs: {str(exc)}"}), 500
    
@app.route("/tasks/<task_id>", methods=["PUT", "PATCH"])
def update_task(task_id: str):
    """
    PUT/PATCH /tasks/<task_id> - Update an existing task
    Supports both regular updates and reschedule operations
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        # Check if task exists
        existing_task = get_task_by_id(task_id)
        if not existing_task:
            return jsonify({"error": "Task not found"}), 404

        body = request.get_json(silent=True) or {}
        
        # Check if this is a reschedule request (has actor_id and new_due_date)
        is_reschedule = "actor_id" in body and "new_due_date" in body
        
        if is_reschedule:
            # Handle reschedule operation
            try:
                reschedule_data = RescheduleTask(**body)
            except ValidationError as e:
                return jsonify({"error": "Invalid reschedule request data", "details": e.errors()}), 400

            # Check if user has permission to reschedule
            if existing_task.get("owner_id") != reschedule_data.actor_id:
                return jsonify({"error": "Only the task owner can reschedule the due date"}), 403

            # Validate new due date format
            try:
                new_date = datetime.strptime(reschedule_data.new_due_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
            # Check if date is not in the past
            if new_date < datetime.now(timezone.utc).date():
                return jsonify({"error": "Due date cannot be in the past"}), 400

            # Prepare update data for reschedule
            update_data = {"due_date": reschedule_data.new_due_date}
            actor_id = reschedule_data.actor_id
        else:
            # Handle regular update operation
            try:
                task_data = TaskUpdate(**body)
            except ValidationError as e:
                return jsonify({"error": "Invalid request data", "details": e.errors()}), 400

            # Prepare update data (only include non-None values)
            update_data = {k: v for k, v in task_data.dict().items() if v is not None}
            actor_id = existing_task.get("owner_id", "system")
        
        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Get complete existing task data with all fields for accurate comparison BEFORE update
        fresh_existing_data = supabase.table("task").select("*").eq("task_id", task_id).execute()
        if not fresh_existing_data.data:
            return jsonify({"error": "Task not found for logging"}), 404
        
        complete_existing_task = fresh_existing_data.data[0]

        # Update in database
        response = supabase.table("task").update(update_data).eq("task_id", task_id).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to update task"}), 500

        # Get updated task
        updated_task = map_db_row_to_api(response.data[0])
        
        # Log changes for audit trail - only log ACTUAL changes
        changes_made = False
        for field, new_value in update_data.items():
            # Get the actual OLD value from the complete task data (before update)
            old_value = complete_existing_task.get(field)
            
            # Normalize values for accurate comparison
            if field == "due_date":
                # Handle date comparison - normalize to YYYY-MM-DD format
                if old_value:
                    if isinstance(old_value, str):
                        old_value = old_value[:10]  # Take first 10 chars (YYYY-MM-DD)
                    else:
                        old_value = str(old_value)[:10]
                else:
                    old_value = None
                    
                if new_value:
                    new_value = str(new_value)[:10]  # Normalize to YYYY-MM-DD
                else:
                    new_value = None
            else:
                # For all other fields, handle None/empty string normalization
                # Convert empty strings to None for consistent comparison
                if old_value == "":
                    old_value = None
                if new_value == "":
                    new_value = None
                    
                # Special handling for description field - map API default to database null
                if field == "description":
                    if old_value is None and new_value == "No description available":
                        new_value = None  # Treat API default as null for comparison
                    elif old_value == "No description available" and new_value is None:
                        old_value = None  # Normalize API default in old value too
            
            # Only log if there's actually a change
            if old_value != new_value:
                log_task_change(
                    task_id=task_id,
                    action="update",
                    field=field,
                    user_id=actor_id,
                    old_value=old_value,
                    new_value=new_value
                )
                changes_made = True

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


@app.route("/users/<user_id>", methods=["GET"])
def get_user_by_id(user_id: str):
    """Get user info by user_id from Supabase user table"""
    try:
        response = supabase.table("user").select("user_id, name, email").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            user_row = response.data[0]
            return jsonify({"user": {
                "user_id": user_row.get("user_id"),
                "name": user_row.get("name"),
                "email": user_row.get("email")
            }}), 200
        else:
            return jsonify({"error": "User not found", "user_id": user_id}), 404

    except Exception as exc:
        return jsonify({"error": f"Failed to fetch user: {str(exc)}", "user_id": user_id}), 500


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

