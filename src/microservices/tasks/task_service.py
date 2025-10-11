import os
import sys
import json
import traceback
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

import pika
import requests
from dotenv import load_dotenv

# Add the notifications microservice to the path to import email_service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../notifications'))
try:
    from email_service import send_notification_email
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    print("Warning: email_service not available. Email notifications will be disabled.")
    EMAIL_SERVICE_AVAILABLE = False

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
    priority: Optional[int] = 5  # Priority from 1-10, default to 5 (medium)
    description: Optional[str] = None
    owner_id: Optional[str] = None
    collaborators: Optional[str] = None
    isSubtask: Optional[bool] = False
    parent_task_id: Optional[str] = None
    reminder_days: Optional[List[int]] = None  # Custom reminder days (e.g., [7, 3, 1])
    email_enabled: Optional[bool] = True  # Email notifications enabled
    in_app_enabled: Optional[bool] = True  # In-app notifications enabled
    created_by: Optional[str] = None  # NEW: Track who actually created the task (for manager assignments)

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None  # Priority from 1-10
    description: Optional[str] = None
    collaborators: Optional[str] = None
    project_id: Optional[str] = None
    owner_id: Optional[str] = None
    isSubtask: Optional[bool] = None
    parent_task_id: Optional[str] = None
    subtasks: Optional[str] = None
    reminder_days: Optional[List[int]] = None  # Custom reminder days
    email_enabled: Optional[bool] = None  # Email notifications enabled
    in_app_enabled: Optional[bool] = None  # In-app notifications enabled
    updated_by: Optional[str] = None  # Track who is making the update


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

def is_task_creator(task_id: str, user_id: str) -> bool:
    """Check if user is the creator of the task by looking at audit logs"""
    try:
        response = supabase.table("task_log").select("user_id").eq("task_id", task_id).eq("action", "create").execute()
        print(f"DEBUG is_task_creator: task_id={task_id}, user_id={user_id}")
        print(f"DEBUG is_task_creator: create logs={response.data}")
        if response.data and len(response.data) > 0:
            creator_id = response.data[0].get("user_id")
            is_creator = creator_id == user_id
            print(f"DEBUG is_task_creator: creator_id={creator_id}, is_creator={is_creator}")
            return is_creator
        print(f"DEBUG is_task_creator: no create logs found")
        return False
    except Exception as e:
        print(f"DEBUG is_task_creator: exception={e}")
        return False

def can_user_access_task(user_id: str, task_data: dict) -> dict:
    """Check what level of access a user has to a task"""
    if not user_id or not task_data:
        return {"can_view": False, "can_comment": False, "can_edit": False, "access_type": "none"}
    
    task_id = task_data.get("task_id")
    owner_id = task_data.get("owner_id")
    collaborators = task_data.get("collaborators", [])
    
    # Parse collaborators if it's a JSON string
    if isinstance(collaborators, str):
        try:
            collaborators = json.loads(collaborators)
        except:
            collaborators = []
    
    # Check if user is owner
    if user_id == owner_id:
        return {"can_view": True, "can_comment": True, "can_edit": True, "access_type": "owner"}
    
    # Check if user is collaborator (includes managers who created the task)
    if user_id in collaborators:
        # Check if this collaborator is also the creator (manager)
        is_creator = is_task_creator(task_id, user_id)
        if is_creator:
            return {"can_view": True, "can_comment": True, "can_edit": False, "access_type": "creator"}
        else:
            return {"can_view": True, "can_comment": True, "can_edit": False, "access_type": "collaborator"}
    
    # No access
    return {"can_view": False, "can_comment": False, "can_edit": False, "access_type": "none"}

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
        "priority": row.get("priority") or 5,  # Default to 5 (medium) if null
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

def get_user_email(user_id: str) -> Optional[str]:
    """Get user email from database"""
    try:
        response = supabase.table("user").select("email").eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("email")
        return None
    except Exception as e:
        print(f"Failed to get user email: {e}")
        return None

def get_notification_preferences(user_id: str, task_id: str) -> dict:
    """Get notification preferences for a user and task"""
    try:
        response = supabase.table("notification_preferences").select("*").eq("user_id", user_id).eq("task_id", task_id).execute()
        if response.data and len(response.data) > 0:
            prefs = response.data[0]
            print(f"✅ Found notification preferences for user {user_id}, task {task_id}: email={prefs.get('email_enabled')}, in_app={prefs.get('in_app_enabled')}")
            return prefs
        # Default: both email and in-app enabled (only when preferences don't exist)
        print(f"⚠️ No notification preferences found for user {user_id}, task {task_id}, using defaults")
        return {"email_enabled": True, "in_app_enabled": True}
    except Exception as e:
        print(f"❌ Failed to get notification preferences: {e}")
        return {"email_enabled": True, "in_app_enabled": True}

def save_notification_preferences(user_id: str, task_id: str, email_enabled: bool, in_app_enabled: bool):
    """Save notification preferences for a user and task"""
    try:
        existing = supabase.table("notification_preferences").select("user_id").eq("user_id", user_id).eq("task_id", task_id).execute()

        prefs_data = {
            "user_id": user_id,
            "task_id": task_id,
            "email_enabled": email_enabled,
            "in_app_enabled": in_app_enabled,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        if existing.data:
            print(f"📝 Updating notification preferences for user {user_id}, task {task_id}: email={email_enabled}, in_app={in_app_enabled}")
            response = supabase.table("notification_preferences").update(prefs_data).eq("user_id", user_id).eq("task_id", task_id).execute()
        else:
            print(f"➕ Creating notification preferences for user {user_id}, task {task_id}: email={email_enabled}, in_app={in_app_enabled}")
            response = supabase.table("notification_preferences").insert(prefs_data).execute()

        if response.data:
            print(f"✅ Successfully saved notification preferences")
            return True
        else:
            print(f"❌ Failed to save notification preferences - no data returned")
            return False
    except Exception as e:
        print(f"❌ Failed to save notification preferences: {e}")
        import traceback
        traceback.print_exc()
        return False

def notify_collaborators_due_date_change(task_data: dict, old_due_date: str, new_due_date: str):
    """Send notification to collaborators when due date changes"""
    try:
        collaborators = task_data.get("collaborators", [])
        if not collaborators or not isinstance(collaborators, list):
            return

        for collaborator_id in collaborators:
            if collaborator_id == task_data.get("owner_id"):
                continue  # Skip owner, they already get reminders

            notification_data = {
                "user_id": collaborator_id,
                "title": "Task Due Date Changed",
                "message": f"The due date for task '{task_data['title']}' has been changed from {old_due_date} to {new_due_date}",
                "type": "due_date_change",
                "task_id": task_data["task_id"],
                "due_date": new_due_date,
                "priority": task_data.get("priority", 5),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False
            }

            # Store notification
            response = supabase.table("notifications").insert(notification_data).execute()
            if response.data:
                print(f"Sent due date change notification to collaborator {collaborator_id}")

                # Try to send via notification service for real-time
                try:
                    notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                    requests.post(
                        f"{notification_service_url}/notifications/create",
                        json=notification_data,
                        timeout=5,
                        headers={'Content-Type': 'application/json'}
                    )
                except Exception as e:
                    print(f"Failed to notify collaborator via notification service: {e}")

                # Send email if enabled
                prefs = get_notification_preferences(collaborator_id, task_data["task_id"])
                if prefs.get("email_enabled", True) and EMAIL_SERVICE_AVAILABLE:
                    user_email = get_user_email(collaborator_id)
                    if user_email:
                        try:
                            send_notification_email(
                                user_email=user_email,
                                notification_type="due_date_change",
                                task_title=task_data["title"],
                                due_date=new_due_date,
                                priority=task_data.get("priority", 5),
                                task_id=task_data["task_id"],
                                old_due_date=old_due_date,
                                new_due_date=new_due_date
                            )
                            print(f"Email notification sent to collaborator {user_email}")
                        except Exception as e:
                            print(f"Failed to send email to collaborator: {e}")
    except Exception as e:
        print(f"Failed to notify collaborators: {e}")

def check_and_send_due_date_notifications(task_data: dict):
    """Check if task needs due date notifications and send them"""
    if not task_data.get("due_date") or not task_data.get("owner_id"):
        return

    # Don't send reminders for completed tasks
    if task_data.get("status") == "Completed":
        print(f"Task {task_data.get('task_id')} is completed, skipping reminders")
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

                # Check notification preferences
                prefs = get_notification_preferences(task_data["owner_id"], task_data["task_id"])
                print(f"Notification preferences for task {task_data.get('task_id')}: {prefs}")

                # Create notification directly in database first (only if in-app enabled)
                if prefs.get("in_app_enabled", True):
                    notification_data = {
                        "user_id": task_data["owner_id"],
                        "title": f"Task Due in {reminder_day} Day{'s' if reminder_day != 1 else ''}",
                        "message": f"Task '{task_data['title']}' is due on {due_date.strftime('%B %d, %Y')}",
                        "type": f"reminder_{reminder_day}_days",
                        "task_id": task_data["task_id"],
                        "due_date": task_data["due_date"],
                        "priority": task_data.get("priority", 5),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "is_read": False
                    }

                    # Store in notifications table directly
                    try:
                        response = supabase.table("notifications").insert(notification_data).execute()
                        if response.data:
                            print(f"Successfully stored {reminder_day}-day notification in database (in-app)")

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
                            print(f"Failed to store in-app notification in database")
                    except Exception as e:
                        print(f"Error storing in-app notification: {e}")
                else:
                    print(f"In-app notifications disabled for this task")

                # Send email if enabled (separate from in-app)
                if prefs.get("email_enabled", True):
                    if not EMAIL_SERVICE_AVAILABLE:
                        print(f"Email service not available, skipping email for task {task_data.get('task_id')}")
                    else:
                        user_email = get_user_email(task_data["owner_id"])
                        if user_email:
                            try:
                                print(f"Sending email notification to {user_email} for {reminder_day}-day reminder")
                                send_notification_email(
                                    user_email=user_email,
                                    notification_type=f"reminder_{reminder_day}_days",
                                    task_title=task_data["title"],
                                    due_date=due_date.strftime('%B %d, %Y'),
                                    priority=task_data.get("priority", 5),
                                    task_id=task_data["task_id"]
                                )
                                print(f"✅ Email notification sent successfully to {user_email}")
                            except Exception as e:
                                print(f"❌ Failed to send email notification: {e}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"No email found for user {task_data['owner_id']}")
                else:
                    print(f"Email notifications disabled for task {task_data.get('task_id')}")
    
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


@app.route("/debug/task/<task_id>", methods=["GET"])
def debug_task(task_id: str):
    """Debug endpoint to check task data"""
    try:
        task_data = get_task_by_id(task_id)
        if not task_data:
            return jsonify({"error": "Task not found"}), 404
        
        # Get audit logs for this task
        logs_response = supabase.table("task_log").select("*").eq("task_id", task_id).execute()
        logs = logs_response.data or []
        
        return jsonify({
            "task_data": task_data,
            "audit_logs": logs
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/<task_id>/access", methods=["GET"])
def check_task_access(task_id: str):
    """
    GET /tasks/<task_id>/access - Check user's access level to a specific task
    Query parameters:
    - user_id: User ID to check access for
    """
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        task_data = get_task_by_id(task_id)
        if not task_data:
            return jsonify({"error": "Task not found"}), 404

        print(f"DEBUG: Checking access for user {user_id} to task {task_id}")
        print(f"DEBUG: Task data: owner_id={task_data.get('owner_id')}, collaborators={task_data.get('collaborators')}")

        access_info = can_user_access_task(user_id, task_data)
        print(f"DEBUG: Access result: {access_info}")
        
        return jsonify({"task_id": task_id, "user_id": user_id, **access_info}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to check task access: {str(exc)}"}), 500


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


@app.route("/users/<user_id>/accessible-tasks", methods=["GET"])
def get_user_accessible_tasks(user_id: str):
    """
    GET /users/<user_id>/accessible-tasks - Get all tasks accessible to a user
    (owned, collaborated, or created by the user)
    """
    try:
        if not user_id or user_id.strip() == "":
            return jsonify({"error": "Invalid user ID"}), 400

        # Get tasks owned by the user
        owned_response = supabase.table("task").select("*").eq("owner_id", user_id).execute()
        owned_tasks = owned_response.data or []

        # Get tasks where user is a collaborator
        try:
            # Try multiple JSONB query approaches
            collaborated_tasks = []
            
            # Approach 1: Use @> (contains) operator for JSONB arrays
            try:
                collaborated_response = supabase.table("task").select("*").filter("collaborators", "cs", f'["{user_id}"]').execute()
                collaborated_tasks = collaborated_response.data or []
            except Exception as e:
                pass
            
            # Approach 2: If first approach didn't work, try contains operator
            if not collaborated_tasks:
                try:
                    collaborated_response = supabase.table("task").select("*").contains("collaborators", [user_id]).execute()
                    collaborated_tasks = collaborated_response.data or []
                except Exception as e:
                    pass
            
            # Approach 3: Manual filtering as fallback
            if not collaborated_tasks:
                all_tasks_response = supabase.table("task").select("*").execute()
                all_tasks = all_tasks_response.data or []
                
                for task in all_tasks:
                    try:
                        collaborators = task.get("collaborators", [])
                        
                        # Parse collaborators if it's a JSON string
                        if isinstance(collaborators, str):
                            try:
                                collaborators = json.loads(collaborators)
                            except:
                                collaborators = []
                        elif collaborators is None:
                            collaborators = []
                        
                        # Check if user is in collaborators list
                        if user_id in collaborators:
                            collaborated_tasks.append(task)
                    except Exception as e:
                        continue
        except Exception as e:
            collaborated_tasks = []

        # Get tasks created by the user (from audit logs)
        created_logs_response = supabase.table("task_log").select("task_id").eq("user_id", user_id).eq("action", "create").execute()
        created_task_ids = [log["task_id"] for log in (created_logs_response.data or [])]
        
        created_tasks = []
        if created_task_ids:
            created_response = supabase.table("task").select("*").in_("task_id", created_task_ids).execute()
            created_tasks = created_response.data or []

        # Combine all tasks and remove duplicates
        all_tasks = {}
        for task in owned_tasks + collaborated_tasks + created_tasks:
            task_id = task.get("task_id")
            if task_id not in all_tasks:
                all_tasks[task_id] = task

        # Map to API format
        tasks = [map_db_row_to_api(task) for task in all_tasks.values()]
        
        return jsonify({"tasks": tasks, "count": len(tasks)}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve accessible tasks: {str(exc)}"}), 500


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

        # Prepare data for database (exclude reminder_days, email_enabled, in_app_enabled, created_by from task table)
        db_data = task_data.dict(exclude={"reminder_days", "email_enabled", "in_app_enabled", "created_by"})
        db_data["created_at"] = datetime.utcnow().isoformat()

        # Handle automatic collaborator assignment when manager creates task for staff
        creator_id = task_data.created_by
        task_owner_id = db_data.get("owner_id")
        
        if creator_id and task_owner_id and creator_id != task_owner_id:
            # Manager is creating task for someone else - add manager as collaborator
            existing_collaborators = db_data.get("collaborators", [])
            
            # Parse existing collaborators if it's a JSON string
            if isinstance(existing_collaborators, str):
                try:
                    existing_collaborators = json.loads(existing_collaborators)
                except:
                    existing_collaborators = []
            elif existing_collaborators is None:
                existing_collaborators = []
            
            # Add creator as collaborator if not already in the list
            if creator_id not in existing_collaborators:
                existing_collaborators.append(creator_id)
                db_data["collaborators"] = json.dumps(existing_collaborators)
            else:
                pass

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

        # Save notification preferences FIRST (email/in-app toggles)
        if task_data.due_date and task_data.owner_id:
            email_enabled = task_data.email_enabled if task_data.email_enabled is not None else True
            in_app_enabled = task_data.in_app_enabled if task_data.in_app_enabled is not None else True

            save_notification_preferences(
                task_data.owner_id,
                task_id,
                email_enabled,
                in_app_enabled
            )

        # Save custom reminder preferences if provided
        if task_data.reminder_days and task_data.due_date:
            save_reminder_preferences(task_id, task_data.reminder_days)
        elif task_data.due_date:
            # Save default reminder days [7, 3, 1] if due date is set but no custom reminders
            save_reminder_preferences(task_id, [7, 3, 1])

        # Log task creation for audit trail
        # Get the actual creator ID (who created the task) vs owner_id (who owns/is assigned the task)
        creator_id = task_data.created_by or db_data.get("owner_id", "system")
        task_owner_id = db_data.get("owner_id")
        
        # First log entry: Task creation
        task_fields = ["title", "due_date", "status", "priority", "description", 
                      "collaborators", "project_id", "isSubtask", "parent_task_id"]
        
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
        
        # Log task creation (without owner_id)
        if new_values:
            log_task_change(
                task_id=task_id,
                action="create",
                field="task",
                user_id=creator_id,
                old_value=old_values,
                new_value=new_values
            )

        # Second log entry: Assignment (if creator is different from owner)
        if creator_id != task_owner_id and task_owner_id:
            log_task_change(
                task_id=task_id,
                action="assign_task",
                field="assignment",
                user_id=creator_id,  # Who did the assignment
                old_value={"assignee": None},
                new_value={"assignee": task_owner_id, "assigner": creator_id}  # Who was assigned and who assigned
            )
            
            # Third log entry: Auto-collaborate (manager added as collaborator)
            log_task_change(
                task_id=task_id,
                action="auto_add_collaborator",
                field="auto_collaboration",
                user_id=creator_id,  # Who was added as collaborator
                old_value={"collaborator": None},
                new_value={"collaborator": creator_id}  # The creator ID that was added
            )

        # Return created task
        created_task = map_db_row_to_api(created_task_data)

        # Check and send due date notifications AFTER preferences are saved
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

            # Prepare update data (only include non-None values, exclude reminder_days, email_enabled, in_app_enabled, updated_by)
            update_data = {k: v for k, v in task_data.dict(exclude={"reminder_days", "email_enabled", "in_app_enabled", "updated_by"}).items() if v is not None}
            actor_id = task_data.updated_by or existing_task.get("owner_id", "system")
            
            # IMPORTANT: Preserve collaborators unless explicitly being managed by someone with permission
            # If collaborators field is being updated, check if it should be preserved
            if "collaborators" in update_data:
                submitted_collaborators = update_data["collaborators"]
                existing_collaborators = existing_task.get("collaborators", [])
                
                # Parse both for comparison
                if isinstance(submitted_collaborators, str):
                    try:
                        submitted_collaborators = json.loads(submitted_collaborators)
                    except:
                        submitted_collaborators = []
                elif submitted_collaborators is None:
                    submitted_collaborators = []
                    
                if isinstance(existing_collaborators, str):
                    try:
                        existing_collaborators = json.loads(existing_collaborators)
                    except:
                        existing_collaborators = []
                elif existing_collaborators is None:
                    existing_collaborators = []
                
                # If submitted collaborators are empty but existing ones exist, preserve existing
                # This prevents accidental removal of collaborators by staff edits
                if not submitted_collaborators and existing_collaborators:
                    update_data["collaborators"] = json.dumps(existing_collaborators)
                else:
                    # Convert to JSON string for database storage
                    update_data["collaborators"] = json.dumps(submitted_collaborators)

            # Handle notification preferences separately
            reminder_days_update = task_data.reminder_days
            email_enabled_update = task_data.email_enabled
            in_app_enabled_update = task_data.in_app_enabled
        
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

        # Update notification preferences if provided
        owner_id = updated_task.get("owner_id") or existing_task.get("owner_id")
        if (email_enabled_update is not None or in_app_enabled_update is not None) and owner_id:
            current_prefs = get_notification_preferences(owner_id, task_id)
            save_notification_preferences(
                owner_id,
                task_id,
                email_enabled_update if email_enabled_update is not None else current_prefs.get("email_enabled", True),
                in_app_enabled_update if in_app_enabled_update is not None else current_prefs.get("in_app_enabled", True)
            )

        # Check and send due date notifications if due_date was changed
        if "due_date" in update_data:
            old_due_date = complete_existing_task.get("due_date")
            new_due_date = update_data.get("due_date")

            # Notify collaborators about due date change
            if old_due_date and old_due_date != new_due_date:
                notify_collaborators_due_date_change(response.data[0], old_due_date, new_due_date)

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


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "task-service"}), 200


@app.route("/users", methods=["GET"])
def get_all_users():
    """Get all users from Supabase user table"""
    try:
        response = supabase.table("user").select("user_id, name, email, department").execute()

        users = []
        if response.data:
            for user_row in response.data:
                users.append({
                    "user_id": user_row.get("user_id"),
                    "name": user_row.get("name"),
                    "email": user_row.get("email"),
                    "department": user_row.get("department")
                })

        return jsonify({"users": users}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to fetch users: {str(exc)}"}), 500

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
        
        # Parse collaborators if it's a JSON string
        if isinstance(collaborators, str):
            try:
                collaborators = json.loads(collaborators)
            except:
                collaborators = []
        
        # Check if user has permission to comment (owner or collaborator, including creators)
        # Creators (managers) are automatically added as collaborators, so they can comment
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


@app.route("/tasks/<task_id>/notification-preferences", methods=["GET"])
def get_task_notification_preferences(task_id: str):
    """Get notification preferences for a specific task and user"""
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        prefs = get_notification_preferences(user_id, task_id)
        return jsonify(prefs), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get notification preferences: {str(e)}"}), 500

@app.route("/tasks/<task_id>/reminder-preferences", methods=["GET"])
def get_task_reminder_preferences(task_id: str):
    """Get reminder days for a specific task"""
    try:
        response = supabase.table("task_reminder_preferences").select("reminder_days").eq("task_id", task_id).execute()

        if response.data and len(response.data) > 0:
            return jsonify({"reminder_days": response.data[0].get("reminder_days", [7, 3, 1])}), 200
        else:
            # Return defaults
            return jsonify({"reminder_days": [7, 3, 1]}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get reminder preferences: {str(e)}"}), 500

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

