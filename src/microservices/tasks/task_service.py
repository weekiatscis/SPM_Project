import os
import json
import traceback
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

import pika
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from pydantic import BaseModel, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

# Environment variables
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

RABBITMQ_URL: Optional[str] = os.getenv("RABBITMQ_URL", "amqp://localhost")

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
    collaborators: Optional[str] = None
    isSubtask: Optional[bool] = False
    parent_task_id: Optional[str] = None
    reminder_days: Optional[List[int]] = None  # Custom reminder days (e.g., [7, 3, 1])

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    collaborators: Optional[str] = None
    project_id: Optional[str] = None
    owner_id: Optional[str] = None
    isSubtask: Optional[bool] = None
    parent_task_id: Optional[str] = None
    subtasks: Optional[str] = None
    reminder_days: Optional[List[int]] = None  # Custom reminder days


# Pydantic model for rescheduling a task
class RescheduleTask(BaseModel):
    actor_id: str
    new_due_date: str


# Pydantic models for comments
class CommentCreate(BaseModel):
    comment_text: str


class NotificationPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange='task_notifications', exchange_type='topic')
            logger.info("Connected to RabbitMQ for notifications")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
    
    def publish_due_date_notification(self, task_data: dict, days_until_due: int):
        if not self.channel:
            self.connect()
        
        if self.channel:
            try:
                message = {
                    "task_id": task_data.get("task_id"),
                    "user_id": task_data.get("owner_id"),
                    "title": f"Task Due in {days_until_due} Day{'s' if days_until_due != 1 else ''}",
                    "message": f"Task '{task_data.get('title')}' is due in {days_until_due} day{'s' if days_until_due != 1 else ''}",
                    "type": f"reminder_{days_until_due}_days",
                    "due_date": task_data.get("due_date"),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.channel.basic_publish(
                    exchange='task_notifications',
                    routing_key=f'task.reminder.{days_until_due}_days',
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                print(f"Published due date notification for task {task_data.get('task_id')}")
            except Exception as e:
                print(f"Failed to publish notification: {e}")

notification_publisher = NotificationPublisher()

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

def get_subtasks_count(task_id: str) -> int:
    """Helper function to get subtasks count for a task"""
    try:
        response = supabase.table("task").select("task_id", count="exact").eq("parent_task_id", task_id).eq("isSubtask", True).execute()
        return response.count if response.count is not None else 0
    except:
        return 0

def map_db_row_to_api(row: Dict[str, Any], include_subtasks_count: bool = False) -> Dict[str, Any]:
    task_data = {
        "id": row.get("task_id") or row.get("id"),
        "title": row.get("title"),
        "description": row.get("description", ""),
        "dueDate": to_yyyy_mm_dd(row.get("due_date")),  # normalize for FE
        "status": row.get("status"),
        "priority": row.get("priority") or "Medium",  # Default to Medium if null
        "owner_id": row.get("owner_id"),
        "project_id": row.get("project_id"),
        "collaborators": row.get("collaborators") or [],
        "isSubtask": row.get("isSubtask", False),
        "parent_task_id": row.get("parent_task_id"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at", row.get("created_at")),
    }
    
    # Optionally include subtasks count for parent tasks
    if include_subtasks_count and not task_data["isSubtask"]:
        task_data["subtasks_count"] = get_subtasks_count(task_data["id"])
    
    return task_data

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

def validate_reminder_days(reminder_days: List[int]) -> bool:
    """Validate reminder days: must be between 1-10, max 5 reminders"""
    if not reminder_days or len(reminder_days) > 5:
        return False
    return all(1 <= day <= 10 for day in reminder_days)

def save_reminder_preferences(task_id: str, reminder_days: List[int]):
    """Save custom reminder preferences for a task"""
    try:
        if not validate_reminder_days(reminder_days):
            print(f"Invalid reminder days: {reminder_days}")
            return False

        # Check if preferences already exist
        existing = supabase.table("task_reminder_preferences").select("task_id").eq("task_id", task_id).execute()

        if existing.data:
            # Update existing preferences
            response = supabase.table("task_reminder_preferences").update({
                "reminder_days": reminder_days,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("task_id", task_id).execute()
        else:
            # Insert new preferences
            response = supabase.table("task_reminder_preferences").insert({
                "task_id": task_id,
                "reminder_days": reminder_days
            }).execute()

        return bool(response.data)
    except Exception as e:
        print(f"Failed to save reminder preferences: {e}")
        return False

def delete_old_notifications(task_id: str):
    """Delete old reminder notifications for a task (when due date changes)"""
    try:
        supabase.table("notifications").delete().eq("task_id", task_id).like("type", "reminder_%").execute()
        print(f"Deleted old notifications for task {task_id}")
    except Exception as e:
        print(f"Failed to delete old notifications: {e}")

def check_and_send_due_date_notifications(task_data: dict):
    """Check if task needs due date notifications and send them"""
    if not task_data.get("due_date") or not task_data.get("owner_id"):
        return

    try:
        # Handle different date formats
        due_date_str = task_data["due_date"]
        if isinstance(due_date_str, str):
            # Handle both YYYY-MM-DD and full timestamp formats
            due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d").date()
        else:
            due_date = due_date_str

        today = datetime.now(timezone.utc).date()
        days_until_due = (due_date - today).days

        print(f"Task {task_data.get('task_id')}: Due date {due_date}, days until due: {days_until_due}")

        # Get custom reminder days from task_reminder_preferences or use default [7, 3, 1]
        reminder_days = [7, 3, 1]  # Default
        try:
            prefs_response = supabase.table("task_reminder_preferences").select("reminder_days").eq("task_id", task_data["task_id"]).execute()
            if prefs_response.data and len(prefs_response.data) > 0:
                reminder_days = prefs_response.data[0].get("reminder_days", [7, 3, 1])
                print(f"Using custom reminder days for task {task_data.get('task_id')}: {reminder_days}")
        except Exception as e:
            print(f"Failed to fetch custom reminder days, using default: {e}")

        for reminder_day in reminder_days:
            if days_until_due == reminder_day:
                print(f"Sending {reminder_day}-day reminder for task {task_data.get('task_id')}")

                # Check if we already sent this reminder - FIXED: Check in notifications table
                try:
                    existing_check = supabase.table("notifications").select("id").eq("task_id", task_data["task_id"]).eq("type", f"reminder_{reminder_day}_days").execute()
                    if existing_check.data:
                        print(f"Reminder already sent for task {task_data.get('task_id')}")
                        continue
                except Exception as e:
                    print(f"Error checking existing notifications: {e}")
                
                # Create notification directly in database first
                notification_data = {
                    "user_id": task_data["owner_id"],
                    "title": f"Task Due in {reminder_day} Day{'s' if reminder_day != 1 else ''}",
                    "message": f"Task '{task_data['title']}' is due in {reminder_day} day{'s' if reminder_day != 1 else ''}",
                    "type": f"reminder_{reminder_day}_days",
                    "task_id": task_data["task_id"],
                    "due_date": task_data["due_date"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "is_read": False
                }
                
                # Store in notifications table directly
                try:
                    response = supabase.table("notifications").insert(notification_data).execute()
                    if response.data:
                        print(f"Successfully stored {reminder_day}-day notification in database")
                        
                        # Publish to RabbitMQ for real-time delivery
                        notification_publisher.publish_due_date_notification(task_data, reminder_day)
                        
                        # Also try to notify the notification service for real-time delivery
                        try:
                            notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                            notif_response = requests.post(
                                f"{notification_service_url}/notifications/create",
                                json=notification_data,
                                timeout=5,
                                headers={'Content-Type': 'application/json'}
                            )
                            if notif_response.ok:
                                print(f"Successfully notified notification service via HTTP")
                            else:
                                print(f"Notification service returned status {notif_response.status_code}")
                        except requests.exceptions.RequestException as e:
                            print(f"Failed to notify notification service: {e}")
                            # Continue anyway since we stored in DB
                    else:
                        print(f"Failed to store notification in database")
                except Exception as e:
                    print(f"Error storing notification: {e}")
    
    except Exception as e:
        print(f"Error checking due date notifications: {e}")

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


@app.route("/tasks/<task_id>/subtasks/count", methods=["GET"])
def get_task_subtasks_count(task_id: str):
    """
    GET /tasks/<task_id>/subtasks/count - Get the count of subtasks for a specific parent task
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        # Check if parent task exists
        parent_task = get_task_by_id(task_id)
        if not parent_task:
            return jsonify({"error": "Task not found"}), 404

        # Query for count of tasks that have this task as their parent
        response = supabase.table("task").select("task_id", count="exact").eq("parent_task_id", task_id).eq("isSubtask", True).execute()
        
        count = response.count if response.count is not None else 0
        
        return jsonify({"task_id": task_id, "subtasks_count": count}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve subtasks count: {str(exc)}"}), 500


@app.route("/tasks/<task_id>/subtasks", methods=["GET"])
def get_task_subtasks(task_id: str):
    """
    GET /tasks/<task_id>/subtasks - Get all subtasks for a specific parent task
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        # Check if parent task exists
        parent_task = get_task_by_id(task_id)
        if not parent_task:
            return jsonify({"error": "Task not found"}), 404

        # Query for all tasks that have this task as their parent
        response = supabase.table("task").select("*").eq("parent_task_id", task_id).eq("isSubtask", True).execute()
        
        if not response.data:
            return jsonify({"subtasks": [], "count": 0}), 200
        
        rows: List[Dict[str, Any]] = response.data or []
        
        # Map to API format
        subtasks = [map_db_row_to_api(row) for row in rows]
        
        return jsonify({"subtasks": subtasks, "count": len(subtasks)}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve subtasks: {str(exc)}"}), 500


@app.route("/tasks/main", methods=["GET"])
def get_main_tasks():
    """
    GET /tasks/main - Get all main tasks (excluding subtasks)
    """
    try:
        # Query tasks where isSubtask is false or null
        response = supabase.table("task").select("*").or_("isSubtask.is.null,isSubtask.eq.false").execute()
        
        if not response.data:
            return jsonify({"tasks": [], "count": 0}), 200
        
        rows: List[Dict[str, Any]] = response.data or []
        
        # Map to API format with subtasks count
        tasks = [map_db_row_to_api(row, include_subtasks_count=True) for row in rows]
        
        return jsonify({"tasks": tasks, "count": len(tasks)}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve main tasks: {str(exc)}"}), 500


@app.route("/tasks/user/<user_id>", methods=["GET"])
def get_tasks_by_user(user_id: str):
    """
    GET /tasks/user/<user_id> - Get all tasks owned by a specific user
    """
    try:
        if not user_id or user_id.strip() == "":
            return jsonify({"error": "Invalid user ID"}), 400

        # Query tasks owned by the user
        response = supabase.table("task").select("*").eq("owner_id", user_id).execute()
        
        if not response.data:
            return jsonify({"tasks": [], "count": 0}), 200
        
        rows: List[Dict[str, Any]] = response.data or []
        
        # Map to API format
        tasks = [map_db_row_to_api(row) for row in rows]
        
        return jsonify({"tasks": tasks, "count": len(tasks)}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve user tasks: {str(exc)}"}), 500


@app.route("/tasks", methods=["POST"])
def create_task():
    """
    POST /tasks - Create a new task or subtask
    """
    try:
        body = request.get_json(silent=True) or {}
        
        # Validate request body
        try:
            task_data = TaskCreate(**body)
        except ValidationError as e:
            return jsonify({"error": "Invalid request data", "details": e.errors()}), 400

        # Prepare data for database
        db_data = task_data.dict(exclude={"reminder_days"})  # Exclude reminder_days from task table
        db_data["created_at"] = datetime.utcnow().isoformat()

        # If this is a subtask, validate that the parent task exists
        if db_data.get("isSubtask") and db_data.get("parent_task_id"):
            parent_task = get_task_by_id(db_data["parent_task_id"])
            if not parent_task:
                return jsonify({"error": "Parent task not found"}), 404
            
            # Ensure parent task is not itself a subtask
            if parent_task.get("isSubtask"):
                return jsonify({"error": "Cannot create subtask of another subtask"}), 400

        # Insert into database
        response = supabase.table("task").insert(db_data).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to create task"}), 500

        created_task_data = response.data[0]
        task_id = created_task_data.get("task_id")

        # Save custom reminder preferences if provided
        if task_data.reminder_days and task_data.due_date:
            save_reminder_preferences(task_id, task_data.reminder_days)
        elif task_data.due_date:
            # Save default reminder days [7, 3, 1] if due date is set but no custom reminders
            save_reminder_preferences(task_id, [7, 3, 1])

        # Log task creation for audit trail - single log entry with all created fields
        # Define all possible task fields for logging
        task_fields = ["title", "due_date", "status", "priority", "description", 
                      "collaborators", "project_id", "owner_id", "isSubtask", "parent_task_id"]
        
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

        # Check and send due date notifications
        check_and_send_due_date_notifications(created_task_data)

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

            # Prepare update data (only include non-None values, exclude reminder_days)
            update_data = {k: v for k, v in task_data.dict(exclude={"reminder_days"}).items() if v is not None}
            actor_id = existing_task.get("owner_id", "system")

            # Handle reminder_days separately
            reminder_days_update = task_data.reminder_days
        
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

        # Update reminder preferences if provided
        if reminder_days_update and "due_date" in update_data:
            save_reminder_preferences(task_id, reminder_days_update)

        # Check and send due date notifications if due_date was changed
        if "due_date" in update_data:
            # Delete old notifications when due date changes
            delete_old_notifications(task_id)
            check_and_send_due_date_notifications(response.data[0])

                
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

@app.route("/tasks/<task_id>/delete-preview", methods=["GET"])
def get_delete_preview(task_id: str):
    """
    GET /tasks/<task_id>/delete-preview - Preview what tasks will be deleted
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        # Check if task exists
        existing_task = get_task_by_id(task_id)
        if not existing_task:
            return jsonify({"error": "Task not found"}), 404

        tasks_to_delete = []
        
        # Add the main task
        tasks_to_delete.append({
            "task_id": task_id,
            "title": existing_task.get("title", "Unknown"),
            "type": "subtask" if existing_task.get("isSubtask") else "main_task",
            "description": existing_task.get("description", ""),
            "status": existing_task.get("status", ""),
            "due_date": existing_task.get("due_date", "")
        })
        
        # If this is not a subtask, get all subtasks that will be deleted
        if not existing_task.get("isSubtask"):
            try:
                subtasks_response = supabase.table("task").select("task_id, title, description, status, due_date").eq("parent_task_id", task_id).eq("isSubtask", True).execute()
                
                if subtasks_response.data:
                    for subtask in subtasks_response.data:
                        tasks_to_delete.append({
                            "task_id": subtask["task_id"],
                            "title": subtask.get("title", "Unknown"),
                            "type": "subtask",
                            "description": subtask.get("description", ""),
                            "status": subtask.get("status", ""),
                            "due_date": subtask.get("due_date", "")
                        })
                        
            except Exception as e:
                print(f"Warning: Failed to fetch subtasks for preview: {e}")
        
        return jsonify({
            "task_id": task_id,
            "tasks_to_delete": tasks_to_delete,
            "total_count": len(tasks_to_delete),
            "has_subtasks": len(tasks_to_delete) > 1,
            "subtasks_count": len(tasks_to_delete) - 1
        }), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to get delete preview: {str(exc)}"}), 500


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    """
    DELETE /tasks/<task_id> - Delete a task and all its subtasks (cascading delete)
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        # Check if task exists
        existing_task = get_task_by_id(task_id)
        if not existing_task:
            return jsonify({"error": "Task not found"}), 404

        deleted_tasks = []
        
        # If this is not a subtask, check for and delete all subtasks first
        if not existing_task.get("isSubtask"):
            try:
                # Get all subtasks for this parent task
                subtasks_response = supabase.table("task").select("task_id, title").eq("parent_task_id", task_id).eq("isSubtask", True).execute()
                
                if subtasks_response.data:
                    subtask_ids = [subtask["task_id"] for subtask in subtasks_response.data]
                    
                    # Delete all subtasks
                    if subtask_ids:
                        delete_subtasks_response = supabase.table("task").delete().in_("task_id", subtask_ids).execute()
                        
                        if delete_subtasks_response.data:
                            deleted_tasks.extend([{
                                "task_id": subtask["task_id"], 
                                "title": subtask["title"],
                                "type": "subtask"
                            } for subtask in subtasks_response.data])
                            
                            print(f"Deleted {len(subtask_ids)} subtasks for parent task {task_id}")
                        
            except Exception as e:
                print(f"Warning: Failed to delete subtasks for task {task_id}: {e}")
                # Continue with parent deletion even if subtask deletion fails
        
        # Delete the main task
        response = supabase.table("task").delete().eq("task_id", task_id).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to delete task"}), 500
        
        # Add the main task to deleted tasks list
        deleted_tasks.append({
            "task_id": task_id,
            "title": existing_task.get("title", "Unknown"),
            "type": "subtask" if existing_task.get("isSubtask") else "main_task"
        })
        
        # Log the deletion for audit trail
        try:
            log_task_change(
                task_id=task_id,
                action="delete",
                field="task",
                user_id=existing_task.get("owner_id", "system"),
                old_value=existing_task,
                new_value=None
            )
        except Exception as e:
            print(f"Warning: Failed to log task deletion: {e}")
        
        return jsonify({
            "message": "Task deleted successfully",
            "task_id": task_id,
            "deleted_tasks": deleted_tasks,
            "total_deleted": len(deleted_tasks)
        }), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to delete task: {str(exc)}"}), 500


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
    
@app.route("/check-all-tasks-notifications", methods=["POST"])
def check_all_tasks_notifications():
    """Check all existing tasks for due date notifications"""
    try:
        # Get all tasks with due dates
        response = supabase.table("task").select("*").not_.is_("due_date", "null").execute()
        tasks = response.data or []
        
        notification_count = 0
        for task in tasks:
            check_and_send_due_date_notifications(task)
            notification_count += 1
        
        return jsonify({
            "message": f"Checked {len(tasks)} tasks for notifications",
            "tasks_processed": notification_count
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to check tasks: {str(e)}"}), 500
    

# ALSO ADD: Function to manually trigger notifications for existing tasks
@app.route("/tasks/<task_id>/check-notifications", methods=["POST"])
def check_task_notifications(task_id: str):
    """Manually check and create notifications for a specific task"""
    try:
        task_data = get_task_by_id(task_id)
        if not task_data:
            return jsonify({"error": "Task not found"}), 404
        
        check_and_send_due_date_notifications(task_data)
        
        return jsonify({"message": "Notifications checked and created if needed"}), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to check notifications: {str(e)}"}), 500
    
@app.route("/test-notifications/<user_id>", methods=["POST"])
def test_create_notification(user_id: str):
    """Test endpoint to create a sample notification"""
    try:
        notification_data = {
            "user_id": user_id,
            "title": "Test Notification",
            "message": "This is a test notification to verify the system works",
            "type": "test",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_read": False
        }
        
        # Store directly in database
        response = supabase.table("notifications").insert(notification_data).execute()
        
        if response.data:
            print(f"Test notification created: {response.data[0]}")
            
            # Also try to send via notification service
            try:
                notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                resp = requests.post(f"{notification_service_url}/notifications/create", 
                                   json=notification_data, timeout=5)
                if resp.ok:
                    print("Also sent via notification service")
            except Exception as e:
                print(f"Failed to send via notification service: {e}")
            
            return jsonify({
                "notification": response.data[0], 
                "message": "Test notification created"
            }), 201
        else:
            return jsonify({"error": "Failed to create test notification"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Failed to create test notification: {str(e)}"}), 500

@app.route("/notifications/debug/<user_id>", methods=["GET"])
def debug_notifications(user_id: str):
    """Debug endpoint to check notifications for a user"""
    try:
        response = supabase.table("notifications").select("*").eq("user_id", user_id).execute()
        notifications = response.data or []
        
        return jsonify({
            "user_id": user_id,
            "total_notifications": len(notifications),
            "notifications": notifications
        }), 200
        
    except Exception as e:
        print(f"ERROR: Failed to fetch notifications for user {user_id}: {e}")
        return jsonify({"error": "Failed to fetch notifications"}), 500


# Comments API Routes

@app.route("/tasks/<task_id>/comments", methods=["GET"])
def get_task_comments(task_id: str):
    """Get all comments for a specific task"""
    
    if not validate_task_id(task_id):
        return jsonify({"error": "Invalid task ID"}), 400
    
    try:
        # Query task_comments table
        response = supabase.table("task_comments")\
            .select("comment_id, comment_text, user_id, created_at, updated_at")\
            .eq("task_id", task_id)\
            .order("created_at", desc=False)\
            .execute()
        
        if not response.data:
            return jsonify({
                "success": True,
                "comments": []
            }), 200
        
        comments = []
        for comment in response.data:
            # Get user info for each comment
            user_name = "Unknown User"
            try:
                user_response = supabase.table("user")\
                    .select("first_name, last_name")\
                    .eq("user_id", comment["user_id"])\
                    .execute()
                
                if user_response.data:
                    user = user_response.data[0]
                    user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                    if not user_name:
                        user_name = f"User-{comment['user_id'][:8]}"
                else:
                    user_name = f"User-{comment['user_id'][:8]}"
            except Exception:
                user_name = f"User-{comment['user_id'][:8]}"
            
            comments.append({
                "comment_id": comment["comment_id"],
                "comment_text": comment["comment_text"],
                "user_id": comment["user_id"],
                "user_name": user_name,
                "created_at": comment["created_at"],
                "updated_at": comment.get("updated_at")
            })
        
        return jsonify({
            "success": True,
            "comments": comments
        }), 200
        
    except Exception as e:
        print(f"Exception in get_task_comments: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to fetch comments: {str(e)}"}), 500


@app.route("/tasks/<task_id>/comments", methods=["POST"])
def add_task_comment(task_id: str):
    """Add a new comment to a task"""
    if not validate_task_id(task_id):
        return jsonify({"error": "Invalid task ID"}), 400
    
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        comment_data = CommentCreate(**data)
        
        # Get user_id from request body (adjust based on your auth setup)
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Verify the task exists and user has access
        task_response = supabase.table("task").select("task_id, owner_id, collaborators").eq("task_id", task_id).execute()
        if not task_response.data:
            return jsonify({"error": "Task not found"}), 404
        
        task = task_response.data[0]
        collaborators = task.get("collaborators", [])
        
        # Check if user has permission to comment (owner or collaborator)
        if task["owner_id"] != user_id and user_id not in collaborators:
            return jsonify({"error": "You don't have permission to comment on this task"}), 403
        
        # Insert the comment
        comment_insert_data = {
            "task_id": task_id,
            "user_id": user_id,
            "comment_text": comment_data.comment_text,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("task_comments").insert(comment_insert_data).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to create comment"}), 500
        
        comment = response.data[0]
        
        # Get user information for the response
        user_response = supabase.table("user").select("first_name, last_name").eq("user_id", user_id).execute()
        user_name = "Unknown User"
        if user_response.data:
            user = user_response.data[0]
            user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            if not user_name:  # If the name is empty after stripping
                user_name = "Unknown User"
        
        # Log the comment activity
        try:
            log_task_change(
                task_id=task_id,
                action="comment",
                field="comments",
                user_id=user_id,
                old_value=None,
                new_value=comment_data.comment_text
            )
        except Exception as log_error:
            # Don't fail the entire request if logging fails
            pass
        
        response_data = {
            "success": True,
            "comment": {
                "comment_id": comment["comment_id"],
                "comment_text": comment["comment_text"],
                "user_id": comment["user_id"],
                "user_name": user_name,
                "created_at": comment["created_at"],
                "updated_at": comment.get("updated_at")
            }
        }
        
        return jsonify(response_data), 201
        
    except ValidationError as e:
        return jsonify({"error": "Invalid data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Failed to add comment"}), 500


# Health check endpoint (no authentication required)
@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint for Docker and CI/CD"""
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

