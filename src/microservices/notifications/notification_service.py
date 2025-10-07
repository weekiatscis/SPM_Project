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

                # Check if we should send a reminder today
                for days in reminder_days:
                    if days_until_due == days:
                        # Check if we already sent this reminder
                        existing_notification = supabase.table("notifications").select("id").eq("task_id", task["task_id"]).eq("type", f"reminder_{days}_days").execute()

                        if not existing_notification.data:
                            # Create notification
                            notification_data = {
                                "user_id": task["owner_id"],
                                "title": f"Task Due in {days} Day{'s' if days > 1 else ''}",
                                "message": f"Task '{task['title']}' is due on {due_date.strftime('%B %d, %Y')}",
                                "type": f"reminder_{days}_days",
                                "task_id": task["task_id"],
                                "due_date": task["due_date"]
                            }

                            # Store in database
                            stored_notification = create_notification(notification_data)

                            if stored_notification:
                                # Send real-time notification via WebSocket
                                send_realtime_notification(task["owner_id"], stored_notification)

                                # Publish to RabbitMQ for real-time delivery
                                rabbitmq.publish_notification(
                                    f"task.reminder.{days}_days",
                                    {
                                        "notification_id": stored_notification["id"],
                                        "user_id": task["owner_id"],
                                        "task_id": task["task_id"],
                                        "title": notification_data["title"],
                                        "message": notification_data["message"],
                                        "type": notification_data["type"],
                                        "created_at": stored_notification["created_at"]
                                    }
                                )

                                print(f"Sent {days}-day reminder for task {task['task_id']}")
            except Exception as e:
                print(f"Error processing task {task.get('task_id', 'unknown')}: {e}")
    
    except Exception as e:
        print(f"Error checking due date reminders: {e}")

def reminder_scheduler():
    """Background thread to check for reminders every hour"""
    while True:
        check_due_date_reminders()
        time.sleep(3600)  # Check every hour

# Start background scheduler
scheduler_thread = threading.Thread(target=reminder_scheduler, daemon=True)
scheduler_thread.start()

# API Routes
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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8084))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)