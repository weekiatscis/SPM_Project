import os
import json
import pika
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from pydantic import BaseModel, ValidationError
import threading
import time
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
from email_service import send_notification_email

# Environment variables
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
RABBITMQ_URL: Optional[str] = os.getenv("RABBITMQ_URL", "amqp://localhost")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Store connected users
connected_users = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = None
    for uid, sid in connected_users.items():
        if sid == request.sid:
            user_id = uid
            break
    
    if user_id:
        del connected_users[user_id]
        print(f"User {user_id} disconnected")

@socketio.on('join_notifications')
def handle_join_notifications(data):
    """Join user to their notification room"""
    user_id = data.get('user_id')
    if user_id:
        connected_users[user_id] = request.sid
        join_room(f"user_{user_id}")
        print(f"User {user_id} joined notifications room")

def send_realtime_notification(user_id: str, notification_data: dict):
    """Send real-time notification to connected user"""
    if user_id in connected_users:
        socketio.emit('new_notification', notification_data, room=f"user_{user_id}")
        print(f"Sent real-time notification to user {user_id}")


# Pydantic models
class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str = "reminder"
    task_id: Optional[str] = None
    due_date: Optional[str] = None

class TaskReminderEvent(BaseModel):
    task_id: str
    user_id: str
    title: str
    due_date: str
    reminder_days: int

# RabbitMQ connection
class RabbitMQManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            self.channel = self.connection.channel()
            
            # Declare exchanges and queues
            self.channel.exchange_declare(exchange='task_notifications', exchange_type='topic')
            self.channel.queue_declare(queue='due_date_reminders', durable=True)
            self.channel.queue_bind(exchange='task_notifications', queue='due_date_reminders', routing_key='task.reminder.*')
            
            print("Connected to RabbitMQ successfully")
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
    
    def publish_notification(self, routing_key: str, message: dict):
        if not self.channel:
            self.connect()
        
        if self.channel:
            try:
                self.channel.basic_publish(
                    exchange='task_notifications',
                    routing_key=routing_key,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
                )
                print(f"Published notification: {routing_key}")
            except Exception as e:
                print(f"Failed to publish notification: {e}")

rabbitmq = RabbitMQManager()



# Notification storage functions
def create_notification(notification_data: dict) -> Optional[Dict[str, Any]]:
    """Store notification in database"""
    try:
        notification_data["created_at"] = datetime.now(timezone.utc).isoformat()
        notification_data["is_read"] = False
        
        response = supabase.table("notifications").insert(notification_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Failed to create notification: {e}")
        return None

def get_user_notifications(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get notifications for a user"""
    try:
        response = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return response.data or []
    except Exception as e:
        print(f"Failed to get notifications: {e}")
        return []

def mark_notification_read(notification_id: str, user_id: str) -> bool:
    """Mark notification as read"""
    try:
        response = supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Failed to mark notification as read: {e}")
        return False

# Due date reminder logic
def check_project_due_date_reminders():
    """Check for projects that need reminders and send notifications"""
    try:
        now = datetime.now(timezone.utc)
        today = now.date()

        # Get all projects with due dates
        response = supabase.table("project").select("*").not_.is_("due_date", "null").execute()
        projects = response.data or []

        for project in projects:
            # Get custom reminder preferences for this project
            try:
                prefs_response = supabase.table("project_reminder_preferences").select("reminder_days").eq("project_id", project["project_id"]).execute()
                if prefs_response.data and len(prefs_response.data) > 0:
                    reminder_days = prefs_response.data[0].get("reminder_days", [7, 3, 1])
                else:
                    reminder_days = [7, 3, 1]  # Default
            except Exception as e:
                print(f"Failed to fetch reminder preferences for project {project['project_id']}: {e}")
                reminder_days = [7, 3, 1]  # Default

            # Calculate days until due
            try:
                due_date_str = project["due_date"]
                if isinstance(due_date_str, str):
                    due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d").date()
                else:
                    due_date = due_date_str

                days_until_due = (due_date - today).days

                # Get all stakeholders (creator + collaborators)
                stakeholder_ids = [project["created_by"]]
                collaborators = project.get("collaborators", [])
                if collaborators:
                    # Ensure collaborators is a list
                    if isinstance(collaborators, str):
                        try:
                            collaborators = json.loads(collaborators)
                        except:
                            collaborators = []
                    if isinstance(collaborators, list):
                        stakeholder_ids.extend(collaborators)
                stakeholder_ids = list(set(filter(None, stakeholder_ids)))  # Remove duplicates and None

                # Check if we should send a reminder today
                for days in reminder_days:
                    if days_until_due == days:
                        # Send notification to all stakeholders
                        for user_id in stakeholder_ids:
                            # Check if we already sent this reminder to this user
                            existing_notification = supabase.table("notifications").select("id").eq(
                                "user_id", user_id
                            ).eq("task_id", project["project_id"]).eq(
                                "type", f"project_reminder_{days}_days"
                            ).gte("created_at", today.isoformat()).execute()

                            if not existing_notification.data:
                                # Get notification preferences for this user
                                prefs_response = supabase.table("project_notification_preferences").select(
                                    "email_enabled, in_app_enabled"
                                ).eq("user_id", user_id).eq("project_id", project["project_id"]).execute()

                                email_enabled = True
                                in_app_enabled = True
                                if prefs_response.data and len(prefs_response.data) > 0:
                                    email_enabled = prefs_response.data[0].get("email_enabled", True)
                                    in_app_enabled = prefs_response.data[0].get("in_app_enabled", True)

                                # Create notification
                                notification_data = {
                                    "user_id": user_id,
                                    "title": f"Project Due in {days} Day{'s' if days > 1 else ''}",
                                    "message": f"Project '{project['project_name']}' is due on {due_date.strftime('%B %d, %Y')}",
                                    "type": f"project_reminder_{days}_days",
                                    "task_id": project["project_id"],  # Using task_id field for project_id
                                    "due_date": project["due_date"]
                                }

                                # Store in database if in-app enabled
                                if in_app_enabled:
                                    stored_notification = create_notification(notification_data)

                                    if stored_notification:
                                        # Send real-time notification via WebSocket
                                        send_realtime_notification(user_id, stored_notification)

                                        # Publish to RabbitMQ for real-time delivery
                                        rabbitmq.publish_notification(
                                            f"project.reminder.{days}_days",
                                            {
                                                "notification_id": stored_notification["id"],
                                                "user_id": user_id,
                                                "project_id": project["project_id"],
                                                "title": notification_data["title"],
                                                "message": notification_data["message"],
                                                "type": notification_data["type"],
                                                "created_at": stored_notification["created_at"]
                                            }
                                        )

                                        print(f"Sent {days}-day in-app reminder for project {project['project_id']} to user {user_id}")

                                # Send email if enabled
                                if email_enabled:
                                    try:
                                        # Get user email
                                        user_response = supabase.table("user").select("email").eq("user_id", user_id).execute()
                                        if user_response.data and len(user_response.data) > 0:
                                            user_email = user_response.data[0].get("email")
                                            if user_email:
                                                send_notification_email(
                                                    user_email=user_email,
                                                    notification_type=f"project_reminder_{days}_days",
                                                    task_title=project["project_name"],
                                                    comment_text="",
                                                    commenter_name="",
                                                    task_id=project["project_id"],
                                                    due_date=project.get("due_date"),
                                                    priority="",
                                                    project_name=project["project_name"],
                                                    project_id=project["project_id"]
                                                )
                                                print(f"Sent {days}-day email reminder for project {project['project_id']} to {user_email}")
                                    except Exception as email_error:
                                        print(f"Failed to send email reminder: {email_error}")
            except Exception as e:
                print(f"Error processing project {project.get('project_id', 'unknown')}: {e}")

    except Exception as e:
        print(f"Error checking project due date reminders: {e}")

def check_due_date_reminders():
    """Check for tasks that need reminders and send notifications"""
    try:
        now = datetime.now(timezone.utc)
        today = now.date()

        # Get all tasks with due dates
        response = supabase.table("task").select("*").not_.is_("due_date", "null").execute()
        tasks = response.data or []

        for task in tasks:
            # Get custom reminder preferences for this task
            try:
                prefs_response = supabase.table("task_reminder_preferences").select("reminder_days").eq("task_id", task["task_id"]).execute()
                if prefs_response.data and len(prefs_response.data) > 0:
                    reminder_days = prefs_response.data[0].get("reminder_days", [7, 3, 1])
                else:
                    reminder_days = [7, 3, 1]  # Default
            except Exception as e:
                print(f"Failed to fetch reminder preferences for task {task['task_id']}: {e}")
                reminder_days = [7, 3, 1]  # Default

            # Calculate days until due
            try:
                due_date_str = task["due_date"]
                if isinstance(due_date_str, str):
                    due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d").date()
                else:
                    due_date = due_date_str

                days_until_due = (due_date - today).days

                # Get all stakeholders (owner + collaborators)
                stakeholder_ids = [task["owner_id"]]
                collaborators = task.get("collaborators", [])
                if collaborators:
                    # Ensure collaborators is a list
                    if isinstance(collaborators, str):
                        try:
                            collaborators = json.loads(collaborators)
                        except:
                            collaborators = []
                    if isinstance(collaborators, list):
                        stakeholder_ids.extend(collaborators)
                stakeholder_ids = list(set(filter(None, stakeholder_ids)))  # Remove duplicates and None

                # Check if we should send a reminder today
                for days in reminder_days:
                    if days_until_due == days:
                        # Send notification to all stakeholders
                        for user_id in stakeholder_ids:
                            # Check if we already sent this reminder to this user TODAY
                            existing_notification = supabase.table("notifications").select("id").eq(
                                "user_id", user_id
                            ).eq("task_id", task["task_id"]).eq(
                                "type", f"reminder_{days}_days"
                            ).gte("created_at", today.isoformat()).execute()

                            if not existing_notification.data:
                                # Get notification preferences for this user
                                prefs_response = supabase.table("notification_preferences").select(
                                    "email_enabled, in_app_enabled"
                                ).eq("user_id", user_id).eq("task_id", task["task_id"]).execute()

                                email_enabled = True
                                in_app_enabled = True
                                if prefs_response.data and len(prefs_response.data) > 0:
                                    email_enabled = prefs_response.data[0].get("email_enabled", True)
                                    in_app_enabled = prefs_response.data[0].get("in_app_enabled", True)

                                # Create notification
                                notification_data = {
                                    "user_id": user_id,
                                    "title": f"Task Due in {days} Day{'s' if days > 1 else ''}",
                                    "message": f"Task '{task['title']}' is due on {due_date.strftime('%B %d, %Y')}",
                                    "type": f"reminder_{days}_days",
                                    "task_id": task["task_id"],
                                    "due_date": task["due_date"],
                                    "priority": task.get("priority", "Medium")
                                }

                                # Store in database if in-app enabled
                                if in_app_enabled:
                                    stored_notification = create_notification(notification_data)

                                    if stored_notification:
                                        # Send real-time notification via WebSocket
                                        send_realtime_notification(user_id, stored_notification)

                                        # Publish to RabbitMQ for real-time delivery
                                        rabbitmq.publish_notification(
                                            f"task.reminder.{days}_days",
                                            {
                                                "notification_id": stored_notification["id"],
                                                "user_id": user_id,
                                                "task_id": task["task_id"],
                                                "title": notification_data["title"],
                                                "message": notification_data["message"],
                                                "type": notification_data["type"],
                                                "created_at": stored_notification["created_at"]
                                            }
                                        )

                                        print(f"Sent {days}-day in-app reminder for task {task['task_id']} to user {user_id}")

                                # Send email if enabled
                                if email_enabled:
                                    try:
                                        # Get user email
                                        user_response = supabase.table("user").select("email").eq("user_id", user_id).execute()
                                        if user_response.data and len(user_response.data) > 0:
                                            user_email = user_response.data[0].get("email")
                                            if user_email:
                                                send_notification_email(
                                                    user_email=user_email,
                                                    notification_type=f"reminder_{days}_days",
                                                    task_title=task["title"],
                                                    due_date=due_date.strftime('%B %d, %Y'),
                                                    priority=task.get("priority", "Medium"),
                                                    task_id=task["task_id"]
                                                )
                                                print(f"Sent {days}-day email reminder for task {task['task_id']} to {user_email}")
                                    except Exception as email_error:
                                        print(f"Failed to send email reminder: {email_error}")
            except Exception as e:
                print(f"Error processing task {task.get('task_id', 'unknown')}: {e}")
    
    except Exception as e:
        print(f"Error checking due date reminders: {e}")

def check_overdue_tasks():
    """
    Check for overdue tasks and send daily summary notifications.
    Sends ONE notification per user per day with count of overdue tasks.
    """
    try:
        today = datetime.now(timezone.utc).date()
        print(f"\n{'='*60}")
        print(f"🔍 Checking for overdue tasks (Date: {today})")
        print(f"{'='*60}")

        # Get ALL tasks that are overdue (due_date < today AND not completed)
        response = supabase.table("task").select("*").lt(
            "due_date", today.isoformat()
        ).neq("status", "Completed").execute()

        overdue_tasks = response.data or []
        print(f"📊 Found {len(overdue_tasks)} total overdue task(s)")

        if not overdue_tasks:
            print("✅ No overdue tasks - nothing to do")
            return

        # Group overdue tasks by owner AND collaborators
        user_tasks = {}
        for task in overdue_tasks:
            # Add owner
            owner_id = task.get("owner_id")
            if owner_id:
                if owner_id not in user_tasks:
                    user_tasks[owner_id] = []
                user_tasks[owner_id].append(task)

            # Add collaborators (handle both array and stringified JSON)
            collaborators = task.get("collaborators", [])
            if collaborators:
                # Ensure collaborators is a list
                if isinstance(collaborators, str):
                    try:
                        collaborators = json.loads(collaborators)
                    except:
                        collaborators = []

                if isinstance(collaborators, list):
                    for collab_id in collaborators:
                        if collab_id and collab_id != owner_id:  # Don't duplicate for owner
                            if collab_id not in user_tasks:
                                user_tasks[collab_id] = []
                            user_tasks[collab_id].append(task)

        print(f"👥 Grouped into {len(user_tasks)} user(s)")

        # Send notification to each user
        for user_id, tasks in user_tasks.items():
            count = len(tasks)
            print(f"\n--- Processing user {user_id} ({count} overdue task(s)) ---")

            # Check if already notified today
            existing = supabase.table("notifications").select("id").eq(
                "user_id", user_id
            ).eq("type", "overdue_tasks").gte(
                "created_at", today.isoformat()
            ).execute()

            if existing.data:
                print(f"⏭️  Already sent overdue notification today - skipping")
                continue

            # Separate owned vs collaborated tasks
            owned_tasks = [t for t in tasks if t.get("owner_id") == user_id]
            collaborated_tasks = [t for t in tasks if t.get("owner_id") != user_id]
            
            # Create notification message
            task_word = "task" if count == 1 else "tasks"
            if owned_tasks and collaborated_tasks:
                message = f"You have {len(owned_tasks)} overdue {('task' if len(owned_tasks) == 1 else 'tasks')} you own and {len(collaborated_tasks)} overdue {('task' if len(collaborated_tasks) == 1 else 'tasks')} you're collaborating on"
            elif owned_tasks:
                message = f"You have {len(owned_tasks)} overdue {('task' if len(owned_tasks) == 1 else 'tasks')} past their due date"
            else:
                message = f"You have {len(collaborated_tasks)} overdue {('task' if len(collaborated_tasks) == 1 else 'tasks')} you're collaborating on that are past their due date"
            
            notification_data = {
                "user_id": user_id,
                "title": f"⚠️ {count} Overdue {task_word.title()}",
                "message": message,
                "type": "overdue_tasks",
                "task_id": None,
                "due_date": None,
                "priority": "High"
            }

            # Save to database
            stored = create_notification(notification_data)
            if stored:
                print(f"✅ In-app notification created (ID: {stored['id']})")

                # Send real-time
                try:
                    send_realtime_notification(user_id, stored)
                    print(f"📡 Real-time notification sent")
                except Exception as e:
                    print(f"⚠️  Real-time send failed: {e}")

            # Send email
            try:
                user_response = supabase.table("user").select("email, name").eq(
                    "user_id", user_id
                ).execute()

                if user_response.data:
                    email = user_response.data[0].get("email")
                    name = user_response.data[0].get("name", "there")

                    if email:
                        print(f"📧 Sending email to {email}...")
                        # Build task list with ownership info
                        task_list_parts = []
                        if owned_tasks:
                            task_list_parts.append("Tasks you own:")
                            for t in owned_tasks[:3]:  # Show first 3 owned
                                task_list_parts.append(f"• {t.get('title', 'Untitled')} (Due: {t.get('due_date', 'N/A')})")
                            if len(owned_tasks) > 3:
                                task_list_parts.append(f"...and {len(owned_tasks) - 3} more owned tasks")
                        
                        if collaborated_tasks:
                            task_list_parts.append("Tasks you're collaborating on:")
                            for t in collaborated_tasks[:3]:  # Show first 3 collaborated
                                task_list_parts.append(f"• {t.get('title', 'Untitled')} (Due: {t.get('due_date', 'N/A')})")
                            if len(collaborated_tasks) > 3:
                                task_list_parts.append(f"...and {len(collaborated_tasks) - 3} more collaborated tasks")
                        
                        task_list = "\n".join(task_list_parts)

                        # Send email (will use generic template for now)
                        from email_service import send_notification_email
                        send_notification_email(
                            user_email=email,
                            notification_type="overdue_tasks",
                            task_title=f"{count} Overdue {task_word.title()}",
                            message=f"Hi {name},\n\nYou have {count} {task_word} past their due date:\n\n{task_list}",
                            priority="High"
                        )
                        print(f"✅ Email sent to {email}")
            except Exception as e:
                print(f"❌ Email failed: {e}")

        print(f"\n{'='*60}")
        print(f"✅ Overdue task check complete")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ ERROR in check_overdue_tasks: {e}")
        import traceback
        traceback.print_exc()

def check_overdue_projects():
    """
    Check for overdue projects and send daily summary notifications.
    Sends ONE notification per user per day with count of overdue projects.
    """
    try:
        today = datetime.now(timezone.utc).date()
        print(f"\n{'='*60}")
        print(f"🔍 Checking for overdue projects (Date: {today})")
        print(f"{'='*60}")

        # Get ALL projects that are overdue
        response = supabase.table("project").select("*").lt(
            "due_date", today.isoformat()
        ).neq("status", "Completed").execute()

        overdue_projects = response.data or []
        print(f"📊 Found {len(overdue_projects)} total overdue project(s)")

        if not overdue_projects:
            print("✅ No overdue projects - nothing to do")
            return

        # Group by stakeholders (creator + collaborators)
        user_projects = {}
        for project in overdue_projects:
            # Get all stakeholders
            stakeholders = [project.get("created_by")]
            collabs = project.get("collaborators", [])
            if collabs:
                # Ensure collabs is a list
                if isinstance(collabs, str):
                    try:
                        collabs = json.loads(collabs)
                    except:
                        collabs = []
                if isinstance(collabs, list):
                    stakeholders.extend(collabs)
            stakeholders = list(set(filter(None, stakeholders)))

            for user_id in stakeholders:
                if user_id not in user_projects:
                    user_projects[user_id] = []
                user_projects[user_id].append(project)

        print(f"👥 Grouped into {len(user_projects)} user(s)")

        # Send notification to each user
        for user_id, projects in user_projects.items():
            count = len(projects)
            print(f"\n--- Processing user {user_id} ({count} overdue project(s)) ---")

            # Check if already notified today
            existing = supabase.table("notifications").select("id").eq(
                "user_id", user_id
            ).eq("type", "overdue_projects").gte(
                "created_at", today.isoformat()
            ).execute()

            if existing.data:
                print(f"⏭️  Already sent overdue notification today - skipping")
                continue

            # Create notification
            project_word = "project" if count == 1 else "projects"
            notification_data = {
                "user_id": user_id,
                "title": f"⚠️ {count} Overdue {project_word.title()}",
                "message": f"You have {count} {project_word} past their due date",
                "type": "overdue_projects",
                "task_id": None,
                "due_date": None,
                "priority": "High"
            }

            # Save to database
            stored = create_notification(notification_data)
            if stored:
                print(f"✅ In-app notification created (ID: {stored['id']})")

                # Send real-time
                try:
                    send_realtime_notification(user_id, stored)
                    print(f"📡 Real-time notification sent")
                except Exception as e:
                    print(f"⚠️  Real-time send failed: {e}")

            # Send email
            try:
                user_response = supabase.table("user").select("email, name").eq(
                    "user_id", user_id
                ).execute()

                if user_response.data:
                    email = user_response.data[0].get("email")
                    name = user_response.data[0].get("name", "there")

                    if email:
                        print(f"📧 Sending email to {email}...")
                        # Build project list
                        project_list = "\n".join([
                            f"• {p.get('project_name', 'Untitled')} (Due: {p.get('due_date', 'N/A')})"
                            for p in projects[:5]  # Show first 5
                        ])
                        if count > 5:
                            project_list += f"\n...and {count - 5} more"

                        # Send email
                        from email_service import send_notification_email
                        send_notification_email(
                            user_email=email,
                            notification_type="overdue_projects",
                            task_title=f"{count} Overdue {project_word.title()}",
                            message=f"Hi {name},\n\nYou have {count} {project_word} past their due date:\n\n{project_list}",
                            priority="High"
                        )
                        print(f"✅ Email sent to {email}")
            except Exception as e:
                print(f"❌ Email failed: {e}")

        print(f"\n{'='*60}")
        print(f"✅ Overdue project check complete")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ ERROR in check_overdue_projects: {e}")
        import traceback
        traceback.print_exc()

def reminder_scheduler():
    """Background thread to check for reminders every hour"""
    while True:
        check_due_date_reminders()
        check_project_due_date_reminders()
        check_overdue_tasks()
        check_overdue_projects()
        time.sleep(3600)  # Check every hour

# Start background scheduler
scheduler_thread = threading.Thread(target=reminder_scheduler, daemon=True)
scheduler_thread.start()

# API Routes
@app.route("/check-overdue", methods=["POST"])
def trigger_overdue_check():
    """Manually trigger overdue task and project checks"""
    try:
        print("🔍 Manual overdue check triggered")
        check_overdue_tasks()
        check_overdue_projects()
        return jsonify({"message": "Overdue check completed successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to check overdue items: {str(e)}"}), 500

@app.route("/notifications", methods=["GET"])
def get_notifications():
    """Get notifications for a user"""
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        limit = request.args.get("limit", 50, type=int)
        notifications = get_user_notifications(user_id, limit)
        
        # Count unread notifications
        unread_count = len([n for n in notifications if not n.get("is_read", True)])
        
        return jsonify({
            "notifications": notifications,
            "unread_count": unread_count,
            "total": len(notifications)
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to get notifications: {str(e)}"}), 500

@app.route("/notifications/<notification_id>/read", methods=["PATCH"])
def mark_read(notification_id: str):
    """Mark notification as read"""
    try:
        user_id = request.json.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        success = mark_notification_read(notification_id, user_id)
        if success:
            return jsonify({"message": "Notification marked as read"}), 200
        else:
            return jsonify({"error": "Failed to mark notification as read"}), 400
    
    except Exception as e:
        return jsonify({"error": f"Failed to mark notification as read: {str(e)}"}), 500

@app.route("/notifications/mark-all-read", methods=["PATCH"])
def mark_all_read():
    """Mark all notifications as read for a user"""
    try:
        user_id = request.json.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        response = supabase.table("notifications").update({"is_read": True}).eq("user_id", user_id).eq("is_read", False).execute()
        
        return jsonify({"message": f"Marked {len(response.data or [])} notifications as read"}), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to mark all notifications as read: {str(e)}"}), 500

@app.route("/notifications/create", methods=["POST"])
def create_notification_endpoint():
    """Create a new notification"""
    try:
        body = request.get_json()
        notification_data = NotificationCreate(**body)
        
        stored_notification = create_notification(notification_data.dict())
        
        if stored_notification:
            # Send real-time notification via WebSocket
            send_realtime_notification(notification_data.user_id, stored_notification)
            
            # Also publish to RabbitMQ for reliability
            rabbitmq.publish_notification(
                f"notification.{notification_data.type}",
                {
                    "notification_id": stored_notification["id"],
                    "user_id": notification_data.user_id,
                    "title": notification_data.title,
                    "message": notification_data.message,
                    "type": notification_data.type,
                    "created_at": stored_notification["created_at"]
                }
            )
            
            return jsonify({"notification": stored_notification}), 201
        else:
            return jsonify({"error": "Failed to create notification"}), 500
    
    except ValidationError as e:
        return jsonify({"error": "Invalid notification data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create notification: {str(e)}"}), 500

@app.route("/notifications/realtime", methods=["POST"])
def send_realtime_notification_endpoint():
    """Send real-time notification via WebSocket without creating database entry"""
    try:
        body = request.get_json()
        user_id = body.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Send real-time notification via WebSocket
        send_realtime_notification(user_id, body)
        
        return jsonify({"message": "Real-time notification sent"}), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to send real-time notification: {str(e)}"}), 500

@app.route("/test-notifications/<user_id>", methods=["POST"])
def test_notifications(user_id: str):
    """Test endpoint to create a sample notification"""
    try:
        notification_data = {
            "user_id": user_id,
            "title": "Test Notification",
            "message": "This is a test notification to verify the system works",
            "type": "test",
            "task_id": None,
            "due_date": None
        }

        stored_notification = create_notification(notification_data)

        if stored_notification:
            # Send real-time notification via WebSocket
            send_realtime_notification(user_id, stored_notification)
            return jsonify({"notification": stored_notification, "message": "Test notification sent"}), 201
        else:
            return jsonify({"error": "Failed to create test notification"}), 500

    except Exception as e:
        return jsonify({"error": f"Failed to create test notification: {str(e)}"}), 500


@app.route("/send-password-reset-email", methods=["POST"])
def send_password_reset_email_endpoint():
    """Send password reset email via HTTP endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('user_email'):
            return jsonify({"error": "user_email is required"}), 400
        
        user_email = data['user_email']
        user_name = data.get('user_name', 'User')
        reset_link = data.get('reset_link', '')
        expiry_minutes = data.get('expiry_minutes', 15)
        
        # Import and call the email service function
        from email_service import send_password_reset_email
        
        result = send_password_reset_email(
            user_email=user_email,
            user_name=user_name,
            reset_link=reset_link,
            expiry_minutes=expiry_minutes
        )
        
        if result:
            return jsonify({"message": "Password reset email sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send password reset email"}), 500
            
    except Exception as e:
        print(f"Password reset email endpoint error: {e}")
        return jsonify({"error": f"Failed to send password reset email: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint for Docker and CI/CD"""
    return jsonify({"status": "healthy", "service": "notification-service"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8084))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)