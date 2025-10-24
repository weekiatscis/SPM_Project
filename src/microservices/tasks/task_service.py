import os
import sys
import json
import traceback
import logging
import uuid
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
    project_id: Optional[str] = None  # Project association
    project: Optional[str] = None  # Project name (for display purposes)
    isSubtask: Optional[bool] = False
    parent_task_id: Optional[str] = None
    reminder_days: Optional[List[int]] = None  # Custom reminder days (e.g., [7, 3, 1])
    email_enabled: Optional[bool] = True  # Email notifications enabled
    in_app_enabled: Optional[bool] = True  # In-app notifications enabled
    created_by: Optional[str] = None  # NEW: Track who actually created the task (for manager assignments)
    recurrence: Optional[str] = None  # e.g., 'daily', 'weekly', 'monthly'

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
    recurrence: Optional[str] = None
    completed_date: Optional[str] = None  # Date when task was marked as completed


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
def is_valid_uuid(value: str) -> bool:
    """Validate if a string is a valid UUID"""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False

def map_db_row_to_api(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert database row to API response format"""
    # Parse collaborators if it's a JSON string
    collaborators = row.get("collaborators")
    if isinstance(collaborators, str):
        try:
            collaborators = json.loads(collaborators)
        except:
            collaborators = []
    elif collaborators is None:
        collaborators = []
    
    return {
        "id": row.get("task_id") or row.get("id"),
        "title": row.get("title"),
        "description": row.get("description", "No description available"),  # Default if not in DB
        "dueDate": row.get("due_date"),
        "status": row.get("status"),
        "owner_id": row.get("owner_id"),
        "assignee": row.get("owner_id"),  # For now, assignee is the owner_id
        "collaborators": collaborators,
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at", row.get("created_at")),  # Use created_at if updated_at doesn't exist
        "completedDate": row.get("completed_date")  # Date when task was marked as completed
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
    # Parse collaborators to ensure it's always an array
    collaborators = row.get("collaborators") or []
    if isinstance(collaborators, str):
        try:
            collaborators = json.loads(collaborators)
        except:
            collaborators = []
    elif collaborators is None:
        collaborators = []
    
    task_data = {
        "id": row.get("task_id") or row.get("id"),
        "title": row.get("title"),
        "description": row.get("description", ""),
        "dueDate": to_yyyy_mm_dd(row.get("due_date")),  # normalize for FE
        "status": row.get("status"),
        "priority": row.get("priority") or 5,  # Default to 5 (medium) if null
        "owner_id": row.get("owner_id"),
        "project_id": row.get("project_id"),
        "collaborators": collaborators,  # Always an array
        "isSubtask": row.get("isSubtask", False),
        "parent_task_id": row.get("parent_task_id"),
        "recurrence": row.get("recurrence"),  # Add recurrence field
        "completedDate": row.get("completed_date"),  # Date when task was marked as completed
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

def get_user_role(user_id: str) -> Optional[str]:
    """Get user role from database"""
    try:
        response = supabase.table("user").select("role").eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("role")
        return None
    except Exception as e:
        print(f"Failed to get user role: {e}")
        return None

def is_staff_member(user_id: str) -> bool:
    """Check if user is a staff member (not Manager or Director)"""
    role = get_user_role(user_id)
    # Staff members are those who are NOT 'Manager' or 'Director'
    # Return True only if role is 'Staff' or any other non-management role
    return role is not None and role not in ['Manager', 'Director']

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

def get_task_stakeholders(task_data: dict) -> List[str]:
    """Get all stakeholders for a task (owner + collaborators)"""
    stakeholders = set()

    # Add owner
    owner_id = task_data.get("owner_id")
    if owner_id:
        stakeholders.add(owner_id)

    # Add collaborators
    collaborators = task_data.get("collaborators", [])
    if isinstance(collaborators, str):
        try:
            collaborators = json.loads(collaborators)
        except:
            collaborators = []

    if isinstance(collaborators, list):
        for collaborator_id in collaborators:
            if collaborator_id:
                stakeholders.add(collaborator_id)

    return list(stakeholders)

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

def notify_comment_mentions(task_data: dict, comment_text: str, commenter_id: str, commenter_name: str):
    """Send notifications to users mentioned in a comment"""
    print("="*80)
    print("🔔 NOTIFY_COMMENT_MENTIONS CALLED")
    print("="*80)
    print(f"📋 Task Data: {task_data}")
    print(f"💬 Comment Text: {comment_text}")
    print(f"👤 Commenter ID: {commenter_id}")
    print(f"👤 Commenter Name: {commenter_name}")

    try:
        # Extract @mentions from comment text using a simple approach
        import re
        # Find all @mentions by looking for @ followed by word characters
        # This handles @zenia, @zenia2, @john, etc.
        mention_pattern = r'@(\w+)'
        mentioned_names = re.findall(mention_pattern, comment_text)
        
        # For usernames with spaces like "zenia 2", we need special handling
        # Look for patterns like @zenia 2, @john doe, etc.
        space_mention_pattern = r'@([a-zA-Z]+)\s+(\d+|[a-zA-Z]+)'
        space_mentions = re.findall(space_mention_pattern, comment_text)
        
        # Add space mentions to the list
        for space_mention in space_mentions:
            if len(space_mention) == 2:
                # Handle @zenia 2 -> "zenia 2"
                combined_name = f"{space_mention[0]} {space_mention[1]}"
                if combined_name not in mentioned_names:
                    mentioned_names.append(combined_name)
        
        print(f"🔍 DEBUG: Comment text: '{comment_text}'")
        print(f"🔍 DEBUG: Regex pattern: {mention_pattern}")
        print(f"🔍 DEBUG: Found mentions: {mentioned_names}")
        
        if not mentioned_names:
            print("ℹ️  No mentions found in comment")
            return
        
        print(f"📝 Found {len(mentioned_names)} mention(s): {mentioned_names}")
        
        # Get all users from database to match names
        all_users_response = supabase.table("user").select("user_id, name").execute()
        if not all_users_response.data:
            print("❌ Could not fetch users from database")
            return
        
        # Create a mapping of names to user IDs (case-insensitive)
        name_to_user_id = {}
        print(f"🔍 DEBUG: All users in database:")
        for user in all_users_response.data:
            user_name = user.get('name', '').strip()
            if user_name:
                name_to_user_id[user_name.lower()] = user['user_id']
                print(f"   - User: '{user_name}' (ID: {user['user_id']})")
        
        print(f"🔍 DEBUG: Name mapping: {name_to_user_id}")
        
        # Find user IDs for mentioned names
        mentioned_user_ids = []
        for mentioned_name in mentioned_names:
            # Try exact match first, then case-insensitive
            user_id = name_to_user_id.get(mentioned_name.lower())
            if user_id:
                mentioned_user_ids.append(user_id)
                print(f"✅ Matched mention '@{mentioned_name}' to user ID: {user_id}")
            else:
                print(f"⚠️  Could not find user for mention '@{mentioned_name}'")
                print(f"🔍 DEBUG: Available names: {list(name_to_user_id.keys())}")
        
        if not mentioned_user_ids:
            print("ℹ️  No valid user IDs found for mentions")
            return
        
        # Remove duplicates
        mentioned_user_ids = list(set(mentioned_user_ids))
        print(f"👥 Sending mention notifications to {len(mentioned_user_ids)} user(s)")
        
        notifications_created = 0
        for mentioned_user_id in mentioned_user_ids:
            # Skip if user mentioned themselves
            if mentioned_user_id == commenter_id:
                print(f"⏭️  Skipping self-mention for user {mentioned_user_id}")
                continue
            
            # Truncate comment for notification
            truncated_comment = comment_text[:100] + "..." if len(comment_text) > 100 else comment_text
            
            notification_data = {
                "user_id": mentioned_user_id,
                "title": f"You were mentioned in '{task_data['title']}'",
                "message": f"{commenter_name} mentioned you: {truncated_comment}",
                "type": "task_mention",
                "task_id": task_data["task_id"],
                "due_date": task_data.get("due_date"),
                "priority": "High",  # Mentions are high priority
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False
            }
            
            print(f"📝 Creating mention notification for user {mentioned_user_id}")
            
            # Check notification preferences
            prefs = get_notification_preferences(mentioned_user_id, task_data["task_id"])
            
            # Store in-app notification if enabled
            if prefs.get("in_app_enabled", True):
                try:
                    # Check for duplicate within last 2 minutes
                    existing_check = supabase.table("notifications").select("id").eq(
                        "user_id", mentioned_user_id
                    ).eq("task_id", task_data["task_id"]).eq("type", "task_mention").gte(
                        "created_at", (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
                    ).execute()
                    
                    if existing_check.data and len(existing_check.data) > 0:
                        print(f"⏭️  Duplicate mention notification detected, skipping...")
                        continue
                    
                    response = supabase.table("notifications").insert(notification_data).execute()
                    
                    if response.data:
                        notifications_created += 1
                        print(f"✅ Mention notification created! ID: {response.data[0].get('id')}")
                        
                        # Send real-time notification
                        try:
                            notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                            realtime_data = {
                                "user_id": mentioned_user_id,
                                "title": notification_data["title"],
                                "message": notification_data["message"],
                                "type": notification_data["type"],
                                "task_id": notification_data.get("task_id"),
                                "created_at": notification_data["created_at"]
                            }
                            notif_response = requests.post(
                                f"{notification_service_url}/notifications/realtime",
                                json=realtime_data,
                                timeout=5,
                                headers={'Content-Type': 'application/json'}
                            )
                            print(f"   Real-time mention notification sent: {notif_response.status_code}")
                        except Exception as e:
                            print(f"⚠️  Failed to send real-time notification: {e}")
                
                except Exception as insert_error:
                    print(f"❌ Error creating mention notification: {insert_error}")
                    import traceback
                    traceback.print_exc()
            
            # Send email if enabled
            if prefs.get("email_enabled", True) and EMAIL_SERVICE_AVAILABLE:
                user_email = get_user_email(mentioned_user_id)
                if user_email:
                    try:
                        print(f"📧 Sending mention email to {user_email}...")
                        send_notification_email(
                            user_email=user_email,
                            notification_type="mention",
                            task_title=task_data["title"],
                            comment_text=truncated_comment,
                            commenter_name=commenter_name,
                            task_id=task_data["task_id"],
                            due_date=task_data.get("due_date"),
                            priority=task_data.get("priority", "Medium")
                        )
                        print(f"✅ Mention email sent to {user_email}")
                    except Exception as e:
                        print(f"❌ Failed to send mention email: {e}")
        
        print(f"\n{'='*80}")
        print(f"📊 SUMMARY: Created {notifications_created} mention notification(s)")
        print(f"{'='*80}\n")
    
    except Exception as e:
        print(f"❌❌❌ CRITICAL ERROR in notify_comment_mentions: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")

def notify_task_comment(task_data: dict, comment_text: str, commenter_id: str, commenter_name: str):
    """Send notification to all stakeholders when a comment is added to a task"""
    print("="*80)
    print("🔔 NOTIFY_TASK_COMMENT CALLED")
    print("="*80)
    print(f"📋 Task Data: {task_data}")
    print(f"💬 Comment Text: {comment_text}")
    print(f"👤 Commenter ID: {commenter_id}")
    print(f"👤 Commenter Name: {commenter_name}")

    try:
        # Validate required task fields
        required_fields = ['task_id', 'title', 'owner_id']
        missing_fields = [field for field in required_fields if field not in task_data or not task_data[field]]
        if missing_fields:
            print(f"❌ ERROR: Missing required task fields: {missing_fields}")
            print(f"Task data received: {task_data}")
            return

        # Get all stakeholders (owner + collaborators)
        print(f"🔍 Getting stakeholders for task {task_data.get('task_id')}...")
        stakeholders = get_task_stakeholders(task_data)
        print(f"👥 Stakeholders found: {stakeholders} (count: {len(stakeholders) if stakeholders else 0})")

        if not stakeholders:
            print("❌ No stakeholders found for comment notification")
            print(f"   Task owner_id: {task_data.get('owner_id')}")
            print(f"   Task collaborators: {task_data.get('collaborators')}")
            return

        print(f"✅ Notifying {len(stakeholders)} stakeholder(s) about new comment on task {task_data.get('task_id')}")

        notifications_created = 0
        for stakeholder_id in stakeholders:
            print(f"\n--- Processing stakeholder: {stakeholder_id} ---")

            # Skip the person who made the comment
            if stakeholder_id == commenter_id:
                print(f"⏭️  Skipping notification for user {stakeholder_id} (they made the comment)")
                continue

            # Truncate comment for notification if too long
            truncated_comment = comment_text[:100] + "..." if len(comment_text) > 100 else comment_text

            notification_data = {
                "user_id": stakeholder_id,
                "title": f"New comment on '{task_data['title']}'",
                "message": f"{commenter_name} commented: {truncated_comment}",
                "type": "task_comment",
                "task_id": task_data["task_id"],
                "due_date": task_data.get("due_date"),
                "priority": task_data.get("priority", "Medium"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False
            }

            print(f"📝 Notification data prepared: {notification_data}")

            # Check notification preferences
            prefs = get_notification_preferences(stakeholder_id, task_data["task_id"])
            print(f"⚙️  Notification preferences: email={prefs.get('email_enabled')}, in_app={prefs.get('in_app_enabled')}")

            # Store in-app notification if enabled
            if prefs.get("in_app_enabled", True):
                try:
                    # Check for existing notification to prevent duplicates (check within last 2 minutes)
                    existing_check = supabase.table("notifications").select("id").eq("user_id", stakeholder_id).eq("task_id", task_data["task_id"]).eq("type", "task_comment").gte("created_at", (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()).execute()
                    
                    if existing_check.data and len(existing_check.data) > 0:
                        print(f"⏭️  Duplicate comment notification detected for user {stakeholder_id}, skipping...")
                        continue
                    
                    print(f"💾 Inserting notification into database for user {stakeholder_id}...")
                    response = supabase.table("notifications").insert(notification_data).execute()

                    if response.data:
                        notifications_created += 1
                        print(f"✅ SUCCESS: Notification inserted! ID: {response.data[0].get('id')}")
                        print(f"   Notification title: {notification_data['title']}")
                        print(f"   For user: {stakeholder_id}")

                        # Send real-time notification via WebSocket (if notification service is available)
                        try:
                            notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                            print(f"📡 Sending real-time notification via WebSocket")
                            # Only send real-time notification, don't create another database entry
                            realtime_data = {
                                "user_id": stakeholder_id,
                                "title": notification_data["title"],
                                "message": notification_data["message"],
                                "type": notification_data["type"],
                                "task_id": notification_data.get("task_id"),
                                "created_at": notification_data["created_at"]
                            }
                            # Send via WebSocket without creating duplicate database entry
                            notif_response = requests.post(
                                f"{notification_service_url}/notifications/realtime",
                                json=realtime_data,
                                timeout=5,
                                headers={'Content-Type': 'application/json'}
                            )
                            print(f"   Real-time notification response: {notif_response.status_code}")
                        except Exception as e:
                            print(f"⚠️  Failed to send real-time notification: {e}")
                    else:
                        print(f"❌ ERROR: Supabase insert returned no data!")
                        print(f"   Response: {response}")

                except Exception as insert_error:
                    print(f"❌ EXCEPTION during database insert: {insert_error}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⏭️  In-app notifications disabled for stakeholder {stakeholder_id}")

            # Send email if enabled
            if prefs.get("email_enabled", True) and EMAIL_SERVICE_AVAILABLE:
                user_email = get_user_email(stakeholder_id)
                if user_email:
                    try:
                        print(f"📧 Sending email to {user_email}...")
                        send_notification_email(
                            user_email=user_email,
                            notification_type="task_comment",
                            task_title=task_data["title"],
                            comment_text=truncated_comment,
                            commenter_name=commenter_name,
                            task_id=task_data["task_id"],
                            due_date=task_data.get("due_date"),
                            priority=task_data.get("priority", "Medium")
                        )
                        print(f"✅ Email sent successfully to {user_email}")
                    except Exception as e:
                        print(f"❌ Failed to send email: {e}")
                else:
                    print(f"⚠️  No email found for stakeholder {stakeholder_id}")

        print(f"\n{'='*80}")
        print(f"📊 SUMMARY: Created {notifications_created} notification(s) for task comment")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"❌❌❌ CRITICAL ERROR in notify_task_comment: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")

def calculate_next_due_date(current_due_date: str, recurrence: str) -> Optional[str]:
    """Calculate the next due date based on recurrence pattern"""
    try:
        # Parse current due date
        if isinstance(current_due_date, str):
            current_date = datetime.strptime(current_due_date[:10], "%Y-%m-%d").date()
        else:
            current_date = current_due_date

        # Calculate next date based on recurrence type
        if recurrence == "daily":
            next_date = current_date + timedelta(days=1)
        elif recurrence == "weekly":
            next_date = current_date + timedelta(weeks=1)
        elif recurrence == "biweekly":
            next_date = current_date + timedelta(weeks=2)
        elif recurrence == "monthly":
            # Add one month (handle month overflow)
            month = current_date.month
            year = current_date.year
            if month == 12:
                next_date = current_date.replace(year=year + 1, month=1)
            else:
                try:
                    next_date = current_date.replace(month=month + 1)
                except ValueError:
                    # Handle day overflow (e.g., Jan 31 -> Feb 28/29)
                    next_month = month + 1
                    next_year = year
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                    # Get last day of next month
                    if next_month == 12:
                        last_day = 31
                    else:
                        last_day = (datetime(next_year, next_month + 1, 1) - timedelta(days=1)).day
                    next_date = current_date.replace(year=next_year, month=next_month, day=min(current_date.day, last_day))
        elif recurrence == "quarterly":
            # Add 3 months
            month = current_date.month
            year = current_date.year
            new_month = month + 3
            new_year = year
            while new_month > 12:
                new_month -= 12
                new_year += 1
            try:
                next_date = current_date.replace(year=new_year, month=new_month)
            except ValueError:
                # Handle day overflow
                last_day = (datetime(new_year, new_month + 1 if new_month < 12 else 1, 1) - timedelta(days=1)).day
                next_date = current_date.replace(year=new_year, month=new_month, day=min(current_date.day, last_day))
        elif recurrence == "yearly":
            next_date = current_date.replace(year=current_date.year + 1)
        else:
            return None

        return next_date.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error calculating next due date: {e}")
        return None

def create_recurring_task_instance(original_task: dict) -> Optional[dict]:
    """Create a new instance of a recurring task with the next due date"""
    try:
        recurrence = original_task.get("recurrence")
        if not recurrence:
            return None

        current_due_date = original_task.get("due_date")
        if not current_due_date:
            return None

        # Calculate next due date
        next_due_date = calculate_next_due_date(current_due_date, recurrence)
        if not next_due_date:
            return None

        # Create new task data (copy from original but with new due date and reset status)
        new_task_data = {
            "title": original_task.get("title"),
            "description": original_task.get("description"),
            "due_date": next_due_date,
            "status": "Unassigned",  # Reset status for new instance
            "priority": original_task.get("priority", 5),
            "owner_id": original_task.get("owner_id"),
            "project_id": original_task.get("project_id"),
            "collaborators": original_task.get("collaborators"),
            "recurrence": recurrence,  # Preserve recurrence pattern
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Insert new task instance
        response = supabase.table("task").insert(new_task_data).execute()
        
        if response.data:
            created_task = response.data[0]
            task_id = created_task.get("task_id")
            
            print(f"✅ Created recurring task instance: {task_id} with due date {next_due_date}")
            
            # Copy notification preferences from original task
            try:
                original_prefs = get_notification_preferences(
                    original_task.get("owner_id"), 
                    original_task.get("task_id")
                )
                save_notification_preferences(
                    original_task.get("owner_id"),
                    task_id,
                    original_prefs.get("email_enabled", True),
                    original_prefs.get("in_app_enabled", True)
                )
            except Exception as e:
                print(f"Failed to copy notification preferences: {e}")
            
            # Copy reminder preferences from original task
            try:
                reminder_response = supabase.table("task_reminder_preferences").select("reminder_days").eq("task_id", original_task.get("task_id")).execute()
                if reminder_response.data:
                    reminder_days = reminder_response.data[0].get("reminder_days", [7, 3, 1])
                    save_reminder_preferences(task_id, reminder_days)
            except Exception as e:
                print(f"Failed to copy reminder preferences: {e}")
            
            # Log the creation
            log_task_change(
                task_id=task_id,
                action="create",
                field="recurring_instance",
                user_id="system",
                old_value=None,
                new_value={
                    "parent_recurrence_id": original_task.get("task_id"),
                    "recurrence_type": recurrence,
                    "due_date": next_due_date
                }
            )
            
            # Check and send due date notifications for the new instance
            check_and_send_due_date_notifications(created_task)
            
            # Copy subtasks from original task to the new recurring instance
            try:
                original_task_id = original_task.get("task_id")
                if original_task_id:
                    # Fetch all subtasks of the original task
                    subtasks_response = supabase.table("task").select("*").eq("parent_task_id", original_task_id).eq("isSubtask", True).execute()
                    
                    if subtasks_response.data:
                        print(f"📋 Found {len(subtasks_response.data)} subtask(s) to copy from task {original_task_id}")
                        
                        for original_subtask in subtasks_response.data:
                            # Calculate new due date for subtask (if it has one)
                            subtask_due_date = None
                            if original_subtask.get("due_date"):
                                # Calculate the offset from the original parent's due date
                                try:
                                    original_parent_due = datetime.fromisoformat(current_due_date.replace('Z', '+00:00'))
                                    original_subtask_due = datetime.fromisoformat(original_subtask.get("due_date").replace('Z', '+00:00'))
                                    
                                    # Calculate the time difference
                                    time_offset = original_subtask_due - original_parent_due
                                    
                                    # Apply the same offset to the new parent's due date
                                    new_parent_due = datetime.fromisoformat(next_due_date.replace('Z', '+00:00'))
                                    new_subtask_due = new_parent_due + time_offset
                                    subtask_due_date = new_subtask_due.strftime("%Y-%m-%d")
                                except Exception as e:
                                    print(f"⚠️  Could not calculate subtask due date offset: {e}")
                                    subtask_due_date = next_due_date  # Fallback to parent's due date
                            
                            # Create new subtask data
                            new_subtask_data = {
                                "title": original_subtask.get("title"),
                                "description": original_subtask.get("description"),
                                "due_date": subtask_due_date,
                                "status": "Unassigned",  # Reset status
                                "priority": original_subtask.get("priority", 5),
                                "owner_id": original_subtask.get("owner_id"),
                                "project_id": original_subtask.get("project_id"),
                                "collaborators": original_subtask.get("collaborators"),
                                "parent_task_id": task_id,  # Link to the new parent task
                                "isSubtask": True,
                                "created_at": datetime.now(timezone.utc).isoformat()
                            }
                            
                            # Insert the new subtask
                            subtask_response = supabase.table("task").insert(new_subtask_data).execute()
                            
                            if subtask_response.data:
                                new_subtask = subtask_response.data[0]
                                new_subtask_id = new_subtask.get("task_id")
                                print(f"  ✅ Copied subtask: {new_subtask.get('title')} (ID: {new_subtask_id})")
                                
                                # Copy notification preferences for the subtask
                                try:
                                    original_subtask_prefs = get_notification_preferences(
                                        original_subtask.get("owner_id"),
                                        original_subtask.get("task_id")
                                    )
                                    save_notification_preferences(
                                        original_subtask.get("owner_id"),
                                        new_subtask_id,
                                        original_subtask_prefs.get("email_enabled", True),
                                        original_subtask_prefs.get("in_app_enabled", True)
                                    )
                                except Exception as e:
                                    print(f"  ⚠️  Failed to copy subtask notification preferences: {e}")
                                
                                # Copy reminder preferences for the subtask
                                try:
                                    subtask_reminder_response = supabase.table("task_reminder_preferences").select("reminder_days").eq("task_id", original_subtask.get("task_id")).execute()
                                    if subtask_reminder_response.data:
                                        subtask_reminder_days = subtask_reminder_response.data[0].get("reminder_days", [7, 3, 1])
                                        save_reminder_preferences(new_subtask_id, subtask_reminder_days)
                                except Exception as e:
                                    print(f"  ⚠️  Failed to copy subtask reminder preferences: {e}")
                                
                                # Send due date notifications for the subtask
                                if subtask_due_date:
                                    check_and_send_due_date_notifications(new_subtask)
                            else:
                                print(f"  ❌ Failed to copy subtask: {original_subtask.get('title')}")
                    else:
                        print(f"ℹ️  No subtasks found for task {original_task_id}")
            except Exception as e:
                print(f"⚠️  Error copying subtasks: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the entire operation if subtask copying fails
            
            return created_task
        
        return None
    except Exception as e:
        print(f"Error creating recurring task instance: {e}")
        import traceback
        traceback.print_exc()
        return None

def notify_collaborators_due_date_change(task_data: dict, old_due_date: str, new_due_date: str, updated_by: str = None):
    """Send notification to all stakeholders (owner + collaborators) when due date changes"""
    try:
        # Validate required task fields
        required_fields = ['task_id', 'title', 'owner_id']
        missing_fields = [field for field in required_fields if field not in task_data or not task_data[field]]
        if missing_fields:
            print(f"❌ ERROR: Missing required task fields: {missing_fields}")
            print(f"Task data received: {task_data}")
            return

        # Get all stakeholders (owner + collaborators)
        print(f"🔍 Getting stakeholders for task {task_data.get('task_id')}...")
        stakeholders = get_task_stakeholders(task_data)
        print(f"👥 Stakeholders found: {stakeholders} (count: {len(stakeholders) if stakeholders else 0})")

        if not stakeholders:
            print("❌ No stakeholders found for comment notification")
            print(f"   Task owner_id: {task_data.get('owner_id')}")
            print(f"   Task collaborators: {task_data.get('collaborators')}")
            return

        print(f"✅ Notifying {len(stakeholders)} stakeholder(s) about new comment on task {task_data.get('task_id')}")

        notifications_created = 0
        for stakeholder_id in stakeholders:
            print(f"\n--- Processing stakeholder: {stakeholder_id} ---")

            # Skip the person who made the comment
            if stakeholder_id == commenter_id:
                print(f"⏭️  Skipping notification for user {stakeholder_id} (they made the comment)")
                continue

            # Truncate comment for notification if too long
            truncated_comment = comment_text[:100] + "..." if len(comment_text) > 100 else comment_text

            notification_data = {
                "user_id": stakeholder_id,
                "title": f"New comment on '{task_data['title']}'",
                "message": f"{commenter_name} commented: {truncated_comment}",
                "type": "task_comment",
                "task_id": task_data["task_id"],
                "due_date": task_data.get("due_date"),
                "priority": task_data.get("priority", "Medium"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False
            }

            print(f"📝 Notification data prepared: {notification_data}")

            # Check notification preferences
            prefs = get_notification_preferences(stakeholder_id, task_data["task_id"])
            print(f"⚙️  Notification preferences: email={prefs.get('email_enabled')}, in_app={prefs.get('in_app_enabled')}")

            # Store in-app notification if enabled
            if prefs.get("in_app_enabled", True):
                try:
                    # Check for existing notification to prevent duplicates (check within last 2 minutes)
                    existing_check = supabase.table("notifications").select("id").eq("user_id", stakeholder_id).eq("task_id", task_data["task_id"]).eq("type", "task_comment").gte("created_at", (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()).execute()
                    
                    if existing_check.data and len(existing_check.data) > 0:
                        print(f"⏭️  Duplicate comment notification detected for user {stakeholder_id}, skipping...")
                        continue
                    
                    print(f"💾 Inserting notification into database for user {stakeholder_id}...")
                    response = supabase.table("notifications").insert(notification_data).execute()

                    if response.data:
                        notifications_created += 1
                        print(f"✅ SUCCESS: Notification inserted! ID: {response.data[0].get('id')}")
                        print(f"   Notification title: {notification_data['title']}")
                        print(f"   For user: {stakeholder_id}")

                        # Send real-time notification via WebSocket (if notification service is available)
                        try:
                            notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                            print(f"📡 Sending real-time notification via WebSocket")
                            # Only send real-time notification, don't create another database entry
                            realtime_data = {
                                "user_id": stakeholder_id,
                                "title": notification_data["title"],
                                "message": notification_data["message"],
                                "type": notification_data["type"],
                                "task_id": notification_data.get("task_id"),
                                "created_at": notification_data["created_at"]
                            }
                            # Send via WebSocket without creating duplicate database entry
                            notif_response = requests.post(
                                f"{notification_service_url}/notifications/realtime",
                                json=realtime_data,
                                timeout=5,
                                headers={'Content-Type': 'application/json'}
                            )
                            print(f"   Real-time notification response: {notif_response.status_code}")
                        except Exception as e:
                            print(f"⚠️  Failed to send real-time notification: {e}")
                    else:
                        print(f"❌ ERROR: Supabase insert returned no data!")
                        print(f"   Response: {response}")

                except Exception as insert_error:
                    print(f"❌ EXCEPTION during database insert: {insert_error}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⏭️  In-app notifications disabled for stakeholder {stakeholder_id}")

            # Send email if enabled
            if prefs.get("email_enabled", True) and EMAIL_SERVICE_AVAILABLE:
                user_email = get_user_email(stakeholder_id)
                if user_email:
                    try:
                        print(f"📧 Sending email to {user_email}...")
                        send_notification_email(
                            user_email=user_email,
                            notification_type="task_comment",
                            task_title=task_data["title"],
                            comment_text=truncated_comment,
                            commenter_name=commenter_name,
                            task_id=task_data["task_id"],
                            due_date=task_data.get("due_date"),
                            priority=task_data.get("priority", "Medium")
                        )
                        print(f"✅ Email sent successfully to {user_email}")
                    except Exception as e:
                        print(f"❌ Failed to send email: {e}")
                else:
                    print(f"⚠️  No email found for stakeholder {stakeholder_id}")

        print(f"\n{'='*80}")
        print(f"📊 SUMMARY: Created {notifications_created} notification(s) for task comment")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"❌❌❌ CRITICAL ERROR in notify_task_comment: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")

def notify_collaborators_due_date_change(task_data: dict, old_due_date: str, new_due_date: str, updated_by: str = None):
    """Send notification to all stakeholders (owner + collaborators) when due date changes"""
    try:
        # Get all stakeholders (owner + collaborators)
        stakeholders = get_task_stakeholders(task_data)

        if not stakeholders:
            print("No stakeholders found for due date change notification")
            return

        print(f"Notifying {len(stakeholders)} stakeholder(s) about due date change for task {task_data.get('task_id')}")

        for stakeholder_id in stakeholders:
            # Skip the person who made the change
            if updated_by and stakeholder_id == updated_by:
                print(f"Skipping notification for user {stakeholder_id} (they made the change)")
                continue

            notification_data = {
                "user_id": stakeholder_id,
                "title": "Task Due Date Changed",
                "message": f"The due date for task '{task_data['title']}' has been changed from {old_due_date} to {new_due_date}",
                "type": "due_date_change",
                "task_id": task_data["task_id"],
                "due_date": new_due_date,
                "priority": task_data.get("priority", 5),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False
            }

            # Check notification preferences
            prefs = get_notification_preferences(stakeholder_id, task_data["task_id"])

            # Store in-app notification if enabled
            if prefs.get("in_app_enabled", True):
                response = supabase.table("notifications").insert(notification_data).execute()
                if response.data:
                    print(f"✅ Sent due date change notification to stakeholder {stakeholder_id}")

                    # Send real-time notification via WebSocket (without creating duplicate database entry)
                    try:
                        notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                        realtime_data = {
                            "user_id": stakeholder_id,
                            "title": notification_data["title"],
                            "message": notification_data["message"],
                            "type": notification_data["type"],
                            "task_id": notification_data.get("task_id"),
                            "created_at": notification_data["created_at"]
                        }
                        requests.post(
                            f"{notification_service_url}/notifications/realtime",
                            json=realtime_data,
                            timeout=5,
                            headers={'Content-Type': 'application/json'}
                        )
                    except Exception as e:
                        print(f"Failed to send real-time notification: {e}")

            # Send email if enabled
            if prefs.get("email_enabled", True) and EMAIL_SERVICE_AVAILABLE:
                user_email = get_user_email(stakeholder_id)
                if user_email:
                    try:
                        send_notification_email(
                            user_email=user_email,
                            notification_type="due_date_change",
                            task_title=task_data["title"],
                            due_date=new_due_date,
                            priority=task_data.get("priority", "Medium"),
                            task_id=task_data["task_id"],
                            old_due_date=old_due_date,
                            new_due_date=new_due_date
                        )
                        print(f"📧 Email notification sent to stakeholder {user_email}")
                    except Exception as e:
                        print(f"Failed to send email to stakeholder: {e}")
    except Exception as e:
        print(f"Failed to notify stakeholders: {e}")
        import traceback
        traceback.print_exc()

def check_and_send_due_date_notifications(task_data: dict):
    """Check if task needs due date notifications and send them to ALL stakeholders"""
    if not task_data.get("due_date"):
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

        # Get ALL stakeholders (owner + collaborators)
        stakeholders = get_task_stakeholders(task_data)
        if not stakeholders:
            print(f"No stakeholders found for task {task_data.get('task_id')}")
            return

        print(f"Will send reminders to {len(stakeholders)} stakeholder(s): {stakeholders}")

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

                # Send reminder to EACH stakeholder
                for stakeholder_id in stakeholders:
                    # Check if we already sent this reminder to this specific user (with multiple checks to prevent race conditions)
                    try:
                        # Check for existing notifications within the last 24 hours to prevent duplicates
                        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
                        existing_check = supabase.table("notifications").select("id").eq("task_id", task_data["task_id"]).eq("user_id", stakeholder_id).eq("type", f"reminder_{reminder_day}_days").gte("created_at", yesterday.isoformat()).execute()
                        if existing_check.data and len(existing_check.data) > 0:
                            print(f"⏭️  Reminder already exists for stakeholder {stakeholder_id} for task {task_data.get('task_id')} within last 24 hours - skipping to prevent duplicate")
                            continue
                    except Exception as e:
                        print(f"Error checking existing notifications: {e}")
                        # If check fails, skip to be safe and avoid duplicates
                        continue

                    # Check notification preferences for this stakeholder
                    prefs = get_notification_preferences(stakeholder_id, task_data["task_id"])
                    print(f"Notification preferences for stakeholder {stakeholder_id}, task {task_data.get('task_id')}: {prefs}")

                    # Create notification directly in database first (only if in-app enabled)
                    if prefs.get("in_app_enabled", True):
                        notification_data = {
                            "user_id": stakeholder_id,
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
                                print(f"✅ Successfully stored {reminder_day}-day notification for stakeholder {stakeholder_id}")

                                # Publish to RabbitMQ for real-time delivery
                                notification_publisher.publish_due_date_notification(task_data, reminder_day)

                                # Send real-time notification via WebSocket (without creating duplicate database entry)
                                try:
                                    notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                                    realtime_data = {
                                        "user_id": stakeholder_id,
                                        "title": notification_data["title"],
                                        "message": notification_data["message"],
                                        "type": notification_data["type"],
                                        "task_id": notification_data.get("task_id"),
                                        "created_at": notification_data["created_at"]
                                    }
                                    notif_response = requests.post(
                                        f"{notification_service_url}/notifications/realtime",
                                        json=realtime_data,
                                        timeout=5,
                                        headers={'Content-Type': 'application/json'}
                                    )
                                    if notif_response.ok:
                                        print(f"Successfully sent real-time notification for stakeholder {stakeholder_id}")
                                    else:
                                        print(f"Real-time notification service returned status {notif_response.status_code}")
                                except requests.exceptions.RequestException as e:
                                    print(f"Failed to send real-time notification: {e}")
                                    # Continue anyway since we stored in DB
                            else:
                                print(f"Failed to store in-app notification in database for stakeholder {stakeholder_id}")
                        except Exception as e:
                            print(f"Error storing in-app notification: {e}")
                    else:
                        print(f"In-app notifications disabled for stakeholder {stakeholder_id}")

                    # Send email if enabled (separate from in-app)
                    if prefs.get("email_enabled", True):
                        if not EMAIL_SERVICE_AVAILABLE:
                            print(f"Email service not available, skipping email for stakeholder {stakeholder_id}")
                        else:
                            user_email = get_user_email(stakeholder_id)
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
                                print(f"No email found for stakeholder {stakeholder_id}")
                    else:
                        print(f"Email notifications disabled for stakeholder {stakeholder_id}")
    
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

        # Build query - select all necessary fields including recurrence
        query = (
            supabase
            .table("task")
            .select("task_id,title,due_date,status,priority,description,created_at,updated_at,owner_id,project_id,collaborators,isSubtask,parent_task_id,recurrence,completed_date")
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

        # Map to API format - removed include_subtasks_count to prevent N+1 query problem
        # Subtask counts can be fetched separately via /tasks/<task_id>/subtasks/count if needed
        tasks = [map_db_row_to_api(row) for row in rows]

        return jsonify({"tasks": tasks, "count": len(tasks)}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve main tasks: {str(exc)}"}), 500


@app.route("/users/<user_id>/accessible-tasks", methods=["GET"])
def get_user_accessible_tasks(user_id: str):
    """
    GET /users/<user_id>/accessible-tasks - Get all tasks accessible to a user
    Business Logic: Show tasks where user is owner_id OR user is in collaborators array
    - When a manager assigns a task to staff, the staff becomes owner_id and manager is added as collaborator
    - The task will appear in staff's "All Tasks" (they are owner)
    - The task will appear in manager's "All Tasks" (they are collaborator)
    - If staff reassigns the task to someone else, staff is no longer owner, task disappears from their "All Tasks"
    """
    try:
        if not user_id or user_id.strip() == "":
            return jsonify({"error": "Invalid user ID"}), 400

        # Get tasks owned by the user (owner_id = user_id)
        owned_response = supabase.table("task").select("*").eq("owner_id", user_id).execute()
        owned_tasks = owned_response.data or []

        # Get tasks where user is a collaborator (user_id is in collaborators array)
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

        # Combine owned and collaborated tasks and remove duplicates
        # IMPORTANT: Only include owned tasks and collaborated tasks
        # Do NOT include tasks just because the user created them
        all_tasks = {}
        for task in owned_tasks + collaborated_tasks:
            task_id = task.get("task_id")
            if task_id not in all_tasks:
                all_tasks[task_id] = task

        # Filter out parent tasks if user only has access to subtasks
        # If user is a collaborator on a subtask but NOT on the parent task,
        # only the subtask should appear (not the parent)
        filtered_tasks = {}
        
        # Create a set of task IDs the user has direct access to (as owner or collaborator)
        user_accessible_task_ids = set(t.get("task_id") for t in owned_tasks + collaborated_tasks)
        
        logger.info(f"User {user_id} has direct access to {len(user_accessible_task_ids)} tasks")
        
        for task_id, task in all_tasks.items():
            parent_task_id = task.get("parent_task_id")
            
            # If this is a subtask, always include it (user has access to it)
            if parent_task_id:
                logger.info(f"Including subtask {task_id} (parent: {parent_task_id})")
                filtered_tasks[task_id] = task
            else:
                # This is a parent task or standalone task
                # Check if there are any subtasks that user has access to
                user_subtasks = [
                    t for t in all_tasks.values() 
                    if t.get("parent_task_id") == task_id
                ]
                
                # Only include the parent task if:
                # 1. User has direct access to this parent task (owner or collaborator), OR
                # 2. User has no subtasks under this parent (meaning they have access to parent only)
                if task_id in user_accessible_task_ids:
                    # User has direct access to parent task - include it
                    logger.info(f"Including parent task {task_id} (user has direct access)")
                    filtered_tasks[task_id] = task
                elif user_subtasks:
                    # User has subtasks but no direct access to parent - exclude parent
                    logger.info(f"Excluding parent task {task_id} (user only has access to {len(user_subtasks)} subtask(s))")
                # If user_subtasks exists but user doesn't have direct access to parent,
                # exclude the parent (user only sees the subtasks)

        # Map to API format
        tasks = [map_db_row_to_api(task) for task in filtered_tasks.values()]
        
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

        # Check if a task with the same title already exists for this user
        title = task_data.title.strip()
        owner_id = task_data.owner_id
        
        if owner_id:
            existing_task_response = supabase.table("task").select("task_id, title").eq("owner_id", owner_id).eq("title", title).execute()
            
            if existing_task_response.data and len(existing_task_response.data) > 0:
                return jsonify({
                    "error": "A task with this title already exists",
                    "message": f"You already have a task titled '{title}'. Please use a different title."
                }), 409

        # Prepare data for database (exclude reminder_days, email_enabled, in_app_enabled, created_by, project from task table)
        # Note: 'project' is just the project name for display, not stored in DB. Only 'project_id' is stored.
        db_data = task_data.dict(exclude={"reminder_days", "email_enabled", "in_app_enabled", "created_by", "project"})
        db_data["created_at"] = datetime.utcnow().isoformat()

        # BUSINESS LOGIC: When a task is created and assigned to a STAFF member (not Manager/Director),
        # automatically set status to "Ongoing" instead of "Unassigned"
        # This only applies to Manager -> Staff assignments, not Director -> Manager assignments
        if db_data.get("owner_id") and db_data.get("status") == "Unassigned":
            if is_staff_member(db_data["owner_id"]):
                db_data["status"] = "Ongoing"
                print(f"✅ Task creation: Automatically setting status to 'Ongoing' since task is assigned to staff member {db_data['owner_id']}")
            else:
                print(f"ℹ️  Task creation: Keeping status as 'Unassigned' since assignee {db_data['owner_id']} is not a staff member (likely Manager/Director)")

        # Manager should NOT be automatically added as collaborator when assigning tasks to staff
        # Collaborators should only be those explicitly selected by the manager
        
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
        # The duplicate check inside the function will prevent duplicates
        check_and_send_due_date_notifications(created_task_data)
        
        # Send task creation notifications to stakeholders
        try:
            stakeholders = get_task_stakeholders(created_task_data)
            task_owner_id = created_task_data.get("owner_id")
            creator_id = task_data.created_by or db_data.get("owner_id", "system")
            
            for stakeholder_id in stakeholders:
                # Determine notification type based on role
                if stakeholder_id == task_owner_id:
                    # This is the assignee - they get "assigned" notification
                    notification_data = {
                        "user_id": stakeholder_id,
                        "title": f"New task assigned: '{created_task_data['title']}'",
                        "message": f"You have been assigned to a new task: '{created_task_data['title']}'",
                        "type": "task_assigned",
                        "task_id": task_id,
                        "due_date": created_task_data.get("due_date"),
                        "priority": created_task_data.get("priority", "Medium"),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "is_read": False
                    }
                else:
                    # This is a collaborator (like the manager who created it) - they get "created" notification
                    notification_data = {
                        "user_id": stakeholder_id,
                        "title": f"New task created: '{created_task_data['title']}'",
                        "message": f"A new task has been created and you are collaborating on it: '{created_task_data['title']}'",
                        "type": "task_created",
                        "task_id": task_id,
                        "due_date": created_task_data.get("due_date"),
                        "priority": created_task_data.get("priority", "Medium"),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "is_read": False
                    }
                
                # Store in-app notification
                supabase.table("notifications").insert(notification_data).execute()
                
                # Send email notification if enabled
                if EMAIL_SERVICE_AVAILABLE:
                    user_email = get_user_email(stakeholder_id)
                    if user_email:
                        notification_type = "task_assigned" if stakeholder_id == task_owner_id else "task_created"
                        send_notification_email(
                            user_email=user_email,
                            notification_type=notification_type,
                            task_title=created_task_data["title"],
                            due_date=created_task_data.get("due_date"),
                            priority=created_task_data.get("priority", "Medium"),
                            task_id=task_id
                        )
        except Exception as e:
            print(f"Failed to send task creation notifications: {e}")

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
        ).eq("task_id", task_id).order("created_at", desc=True).execute()
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

            # Prepare update data (only include non-None values, exclude fields that are handled automatically)
            # Note: completed_date and approval fields are excluded because they're handled automatically
            exclude_fields = {
                "reminder_days", "email_enabled", "in_app_enabled", "updated_by", "completed_date"
            }
            update_data = {k: v for k, v in task_data.dict(exclude=exclude_fields).items() if v is not None}
            actor_id = task_data.updated_by or existing_task.get("owner_id", "system")
            
            # BUSINESS LOGIC: Handle owner_id change (task reassignment)
            # When a manager/user reassigns a task to someone else:
            # 1. The new assignee becomes the owner_id
            # 2. The previous owner should be added as a collaborator (so they can still see/track the task)
            # 3. The person who did the reassignment should remain as collaborator if they were one
            # 4. The task status should automatically change to "Ongoing" ONLY if assigned to staff (not Manager/Director)
            if "owner_id" in update_data:
                new_owner_id = update_data["owner_id"]
                old_owner_id = existing_task.get("owner_id")
                
                # Only process if owner actually changed
                if new_owner_id and old_owner_id and new_owner_id != old_owner_id:
                    # Automatically set status to "Ongoing" when task is reassigned to a STAFF member
                    # This ensures Manager -> Staff assignments start with "Ongoing" status
                    # But Director -> Manager assignments remain "Unassigned"
                    current_status = existing_task.get("status", "Unassigned")
                    if current_status != "Completed":  # Don't change status if task is already completed
                        if is_staff_member(new_owner_id):
                            update_data["status"] = "Ongoing"
                            print(f"✅ Task reassignment: Automatically setting status to 'Ongoing' for staff member (was '{current_status}')")
                        else:
                            print(f"ℹ️  Task reassignment: Keeping status as '{current_status}' since assignee is not a staff member (likely Manager/Director)")
                    
                    # Get existing collaborators
                    existing_collaborators = existing_task.get("collaborators", [])
                    if isinstance(existing_collaborators, str):
                        try:
                            existing_collaborators = json.loads(existing_collaborators)
                        except:
                            existing_collaborators = []
                    elif existing_collaborators is None:
                        existing_collaborators = []
                    
                    # Make a copy to modify
                    new_collaborators = list(existing_collaborators)
                    
                    # Add the old owner as a collaborator if they aren't already
                    # Do NOT add the actor (the person performing the reassignment) as a collaborator.
                    # This prevents managers from being automatically added as collaborators when
                    # they reassign their own tasks to staff.
                    if old_owner_id not in new_collaborators and old_owner_id != actor_id:
                        new_collaborators.append(old_owner_id)
                        print(f"✅ Task reassignment: Adding previous owner {old_owner_id} as collaborator")
                    
                    # Remove the new owner from collaborators (if they were a collaborator)
                    # since they are now the owner
                    if new_owner_id in new_collaborators:
                        new_collaborators.remove(new_owner_id)
                        print(f"✅ Task reassignment: Removing new owner {new_owner_id} from collaborators list")
                    
                    # Update the collaborators in the update_data
                    update_data["collaborators"] = json.dumps(new_collaborators)
                    print(f"📋 Updated collaborators list: {new_collaborators}")
            
            # IMPORTANT: Preserve collaborators unless explicitly being managed by someone with permission
            # If collaborators field is being updated, check if it should be preserved
            elif "collaborators" in update_data:
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
        
        # BUSINESS LOGIC: Handle completed_date and approval workflow based on status changes
        if "status" in update_data:
            old_status = complete_existing_task.get("status")
            new_status = update_data["status"]
            
            # If task is being marked as completed
            if new_status == "Completed" and old_status != "Completed":
                from datetime import date
                
                # Set completed_date when task is marked as completed
                update_data["completed_date"] = date.today().isoformat()  # YYYY-MM-DD format
                print(f"✅ Task {task_id} marked as completed, setting completed_date to {update_data['completed_date']}")
            
            # If task status is changed FROM completed to something else, clear completed_date
            elif old_status == "Completed" and new_status != "Completed":
                update_data["completed_date"] = None
                print(f"🔄 Task {task_id} status changed from Completed to {new_status}, clearing completed_date")

        # Update in database
        response = supabase.table("task").update(update_data).eq("task_id", task_id).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to update task"}), 500
        

        # Get updated task
        updated_task = map_db_row_to_api(response.data[0])

        # BUSINESS LOGIC: When a parent task is assigned to a project, update all subtasks too
        if "project_id" in update_data:
            new_project_id = update_data["project_id"]

            # Check if this task is a parent task (has subtasks)
            # Find all subtasks that have this task as their parent
            subtasks_response = supabase.table("task").select("task_id").eq("parent_task_id", task_id).execute()

            if subtasks_response.data and len(subtasks_response.data) > 0:
                subtask_ids = [subtask["task_id"] for subtask in subtasks_response.data]
                print(f"📋 Parent task {task_id} assigned to project {new_project_id}. Updating {len(subtask_ids)} subtask(s)...")

                # Update all subtasks with the same project_id
                for subtask_id in subtask_ids:
                    try:
                        supabase.table("task").update({"project_id": new_project_id}).eq("task_id", subtask_id).execute()
                        print(f"✅ Updated subtask {subtask_id} with project_id {new_project_id}")
                    except Exception as subtask_error:
                        print(f"❌ Failed to update subtask {subtask_id}: {str(subtask_error)}")

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

            # Notify all stakeholders about due date change
            if old_due_date and old_due_date != new_due_date:
                notify_collaborators_due_date_change(response.data[0], old_due_date, new_due_date, updated_by=actor_id)

            # Delete old notifications when due date changes
            delete_old_notifications(task_id)
            check_and_send_due_date_notifications(response.data[0])

        # Check if task was just completed and has recurrence - create next instance
        if "status" in update_data and update_data["status"] == "Completed":
            task_recurrence = response.data[0].get("recurrence")
            if task_recurrence:
                print(f"Task {task_id} completed with recurrence '{task_recurrence}' - creating next instance")
                new_instance = create_recurring_task_instance(response.data[0])
                if new_instance:
                    print(f"✅ Created recurring task instance: {new_instance.get('task_id')}")
                else:
                    print(f"❌ Failed to create recurring task instance")
                
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
        response = supabase.table("user").select("user_id, name, email, department").eq("user_id", user_id).execute()

        if response.data and len(response.data) > 0:
            user_row = response.data[0]
            return jsonify({"user": {
                "user_id": user_row.get("user_id"),
                "name": user_row.get("name"),
                "email": user_row.get("email"),
                "department": user_row.get("department")
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
            .order("created_at", desc=True)\
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
                    .select("name")\
                    .eq("user_id", comment["user_id"])\
                    .execute()

                if user_response.data:
                    user = user_response.data[0]
                    user_name = user.get('name', '').strip()
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
        
        # Verify the task exists and user has access - get ALL task data for notifications
        task_response = supabase.table("task").select("*").eq("task_id", task_id).execute()
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
        user_response = supabase.table("user").select("name").eq("user_id", user_id).execute()
        user_name = "Unknown User"
        if user_response.data:
            user = user_response.data[0]
            user_name = user.get('name', '').strip()
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

        # Send notifications to all stakeholders (owner + collaborators) except the commenter
        print(f"\n🔔 Attempting to send comment notifications for task {task_id}...")
        print(f"   Task object keys: {list(task.keys())}")
        print(f"   Task title: {task.get('title')}")
        print(f"   Task owner_id: {task.get('owner_id')}")
        print(f"   Task collaborators: {task.get('collaborators')}")
        print(f"   Comment by: {user_id} ({user_name})")

        try:
            notify_task_comment(
                task_data=task,
                comment_text=comment_data.comment_text,
                commenter_id=user_id,
                commenter_name=user_name
            )
            print(f"✅ Task comment notifications function completed for task {task_id}")
        except Exception as notification_error:
            print(f"❌❌❌ EXCEPTION in comment notification: {notification_error}")
            import traceback
            traceback.print_exc()
            # Don't fail the request if notifications fail
        
        # Send mention notifications
        try:
            notify_comment_mentions(
                task_data=task,
                comment_text=comment_data.comment_text,
                commenter_id=user_id,
                commenter_name=user_name
            )
            print(f"✅ Mention notifications function completed for task {task_id}")
        except Exception as mention_error:
            print(f"❌❌❌ EXCEPTION in mention notification: {mention_error}")
            import traceback
            traceback.print_exc()
            # Don't fail the request if mention notifications fail

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

@app.route("/tasks/<task_id>/recurring-preview", methods=["GET"])
def get_recurring_preview(task_id: str):
    """Preview the next N instances of a recurring task"""
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        task_data = get_task_by_id(task_id)
        if not task_data:
            return jsonify({"error": "Task not found"}), 404

        recurrence = task_data.get("recurrence")
        if not recurrence:
            return jsonify({"error": "Task is not recurring"}), 400

        due_date = task_data.get("due_date")
        if not due_date:
            return jsonify({"error": "Task has no due date"}), 400

        # Generate next 5 instances
        instances = []
        current_date = due_date
        count = int(request.args.get("count", 5))  # Default to 5 instances

        for i in range(count):
            next_date = calculate_next_due_date(current_date, recurrence)
            if not next_date:
                break

            instances.append({
                "instance_number": i + 1,
                "due_date": next_date,
                "recurrence_type": recurrence
            })
            current_date = next_date

        return jsonify({
            "task_id": task_id,
            "title": task_data.get("title"),
            "recurrence": recurrence,
            "current_due_date": due_date,
            "next_instances": instances
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to generate recurring preview: {str(e)}"}), 500

@app.route("/tasks/<task_id>/stop-recurrence", methods=["POST"])
def stop_task_recurrence(task_id: str):
    """Stop recurrence for a task"""
    try:
        if not validate_task_id(task_id):
            return jsonify({"error": "Invalid task ID"}), 400

        task_data = get_task_by_id(task_id)
        if not task_data:
            return jsonify({"error": "Task not found"}), 404

        if not task_data.get("recurrence"):
            return jsonify({"error": "Task is not recurring"}), 400

        # Update task to remove recurrence
        response = supabase.table("task").update({"recurrence": None}).eq("task_id", task_id).execute()

        if not response.data:
            return jsonify({"error": "Failed to stop recurrence"}), 500

        # Log the change
        log_task_change(
            task_id=task_id,
            action="update",
            field="recurrence",
            user_id=request.json.get("user_id", "system") if request.json else "system",
            old_value=task_data.get("recurrence"),
            new_value=None
        )

        return jsonify({
            "message": "Recurrence stopped successfully",
            "task_id": task_id
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to stop recurrence: {str(e)}"}), 500

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

