import os
import json
import requests
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Try to import email service
EMAIL_SERVICE_AVAILABLE = False
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../notifications'))
    from email_service import send_notification_email
    EMAIL_SERVICE_AVAILABLE = True
    print("✅ Email service loaded successfully")
except Exception as e:
    print(f"⚠️  Email service not available: {e}")
    EMAIL_SERVICE_AVAILABLE = False

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


# Helper functions
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

def get_project_stakeholders(project_data: dict) -> List[str]:
    """Get all stakeholders for a project (creator + collaborators)"""
    stakeholders = set()

    # Add creator
    created_by = project_data.get("created_by")
    if created_by:
        stakeholders.add(created_by)

    # Add collaborators
    collaborators = project_data.get("collaborators", [])
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

def notify_project_comment(project_data: dict, comment_text: str, commenter_id: str, commenter_name: str):
    """Send notification to all stakeholders when a comment is added to a project"""
    try:
        # Get all stakeholders (creator + collaborators)
        stakeholders = get_project_stakeholders(project_data)

        if not stakeholders:
            print("No stakeholders found for project comment notification")
            return

        print(f"Notifying {len(stakeholders)} stakeholder(s) about new comment on project {project_data.get('project_id')}")

        for stakeholder_id in stakeholders:
            # Skip the person who made the comment
            if stakeholder_id == commenter_id:
                print(f"Skipping notification for user {stakeholder_id} (they made the comment)")
                continue

            # Truncate comment for notification if too long
            truncated_comment = comment_text[:100] + "..." if len(comment_text) > 100 else comment_text

            notification_data = {
                "user_id": stakeholder_id,
                "title": f"New comment on project '{project_data['project_name']}'",
                "message": f"{commenter_name} commented: {truncated_comment}",
                "type": "project_comment",
                "task_id": None,  # This is a project comment, not a task comment
                "project_id": project_data.get("project_id"),  # Add project_id for navigation
                "due_date": project_data.get("due_date"),
                "priority": "Medium",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False
            }

            # Check for existing notification to prevent duplicates (check within last 2 minutes)
            try:
                existing_check = supabase.table("notifications").select("id").eq("user_id", stakeholder_id).eq("type", "project_comment").gte("created_at", (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()).execute()
                
                if existing_check.data and len(existing_check.data) > 0:
                    print(f"⏭️  Duplicate project comment notification detected for user {stakeholder_id}, skipping...")
                    continue
            except Exception as e:
                print(f"Error checking existing notifications: {e}")
                # Continue anyway to avoid blocking notifications

            # Store in-app notification (project comments don't have individual notification preferences)
            response = supabase.table("notifications").insert(notification_data).execute()
            if response.data:
                print(f"✅ Sent project comment notification to stakeholder {stakeholder_id}")

                # Send real-time notification via WebSocket (without creating duplicate database entry)
                try:
                    notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")
                    realtime_data = {
                        "user_id": stakeholder_id,
                        "title": notification_data["title"],
                        "message": notification_data["message"],
                        "type": notification_data["type"],
                        "project_id": notification_data.get("project_id"),
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

            # Send email notification (always enabled for project comments)
            if EMAIL_SERVICE_AVAILABLE:
                user_email = get_user_email(stakeholder_id)
                if user_email:
                    try:
                        print(f"📧 Sending email to {user_email} about project comment...")
                        send_notification_email(
                            user_email=user_email,
                            notification_type="project_comment",
                            project_name=project_data.get("project_name", "Untitled Project"),
                            project_id=project_data.get("project_id"),
                            comment_text=truncated_comment,
                            commenter_name=commenter_name
                        )
                        print(f"✅ Email sent successfully to {user_email}")
                    except Exception as e:
                        print(f"❌ Failed to send email to stakeholder: {e}")
                else:
                    print(f"⚠️  No email found for stakeholder {stakeholder_id}")

    except Exception as e:
        print(f"Failed to notify stakeholders about project comment: {e}")
        import traceback
        traceback.print_exc()

def is_valid_uuid(value: str) -> bool:
    """Validate if a string is a valid UUID"""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


@app.route("/projects", methods=["POST"])
def create_project():
    try:
        body = request.get_json(silent=True) or {}

        # Validate required fields
        if not body.get("project_name", "").strip():
            return jsonify({"error": "project_name is required"}), 400

        # Validate collaborators (now mandatory)
        collaborators = body.get("collaborators", [])
        print(f"DEBUG: Received collaborators from request: {collaborators}")

        if not collaborators or not isinstance(collaborators, list) or len(collaborators) == 0:
            return jsonify({"error": "At least one collaborator is required"}), 400

        # Prepare project data according to your Supabase schema
        # Fields: project_id (auto), created_at (auto), created_by, project_description, project_name, due_date, collaborators (jsonb)
        # Use owner_id as created_by to identify user ownership

        project_data = {
            "project_name": body.get("project_name").strip(),
            "project_description": body.get("project_description", "").strip(),
            "created_by": body.get("owner_id") or body.get("created_by", "").strip() or "Unknown",
            "due_date": body.get("due_date"),
            "collaborators": collaborators if isinstance(collaborators, list) else []
        }

        print(f"DEBUG: Inserting project with collaborators: {project_data.get('collaborators')}")

        # Insert directly using Python Supabase client syntax
        response = supabase.table("project").insert(project_data).execute()

        if not response.data:
            return jsonify({"error": "insert failed"}), 500

        created_project = response.data[0]
        print(f"DEBUG: Project created successfully! Collaborators saved: {created_project.get('collaborators')}")

        # Send project assignment notifications to all stakeholders
        try:
            stakeholders = get_project_stakeholders(created_project)
            project_creator = created_project.get("created_by")
            
            for stakeholder_id in stakeholders:
                # Determine notification type based on role
                if stakeholder_id == project_creator:
                    # This is the creator - they get "created" notification
                    notification_data = {
                        "user_id": stakeholder_id,
                        "title": f"New project created: '{created_project['project_name']}'",
                        "message": f"You have created a new project: '{created_project['project_name']}'",
                        "type": "project_created",
                        "task_id": None,
                        "due_date": created_project.get("due_date"),
                        "priority": "Medium",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "is_read": False
                    }
                else:
                    # This is a collaborator - they get "assigned" notification
                    notification_data = {
                        "user_id": stakeholder_id,
                        "title": f"New project assigned: '{created_project['project_name']}'",
                        "message": f"You have been assigned to a new project: '{created_project['project_name']}'",
                        "type": "project_assigned",
                        "task_id": None,
                        "due_date": created_project.get("due_date"),
                        "priority": "Medium",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "is_read": False
                    }
                
                # Store in-app notification
                supabase.table("notifications").insert(notification_data).execute()
                
                # Send email notification if enabled
                if EMAIL_SERVICE_AVAILABLE:
                    user_email = get_user_email(stakeholder_id)
                    if user_email:
                        notification_type = "project_created" if stakeholder_id == project_creator else "project_assigned"
                        send_notification_email(
                            user_email=user_email,
                            notification_type=notification_type,
                            project_name=created_project["project_name"],
                            project_id=created_project.get("project_id"),
                            due_date=created_project.get("due_date")
                        )
        except Exception as e:
            print(f"Failed to send project assignment notifications: {e}")

        return jsonify({"project": created_project}), 201

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

def map_db_row_to_api(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "project_id": row.get("project_id"),
        "project_name": row.get("project_name"),
        "project_description": row.get("project_description"),
        "created_at": row.get("created_at"),
        "created_by": row.get("created_by"),
        "due_date": row.get("due_date"),
        "collaborators": row.get("collaborators", [])
    }


@app.get("/projects")
def get_projects():
    try:
        limit_param = request.args.get("limit", default=None, type=int)
        user_id = request.args.get("created_by", default=None, type=str)  # Renamed for clarity
        project_id = request.args.get("project_id", default=None, type=str)

        query = (
            supabase
            .table("project")
            .select("project_id,project_name,project_description,created_at,created_by,due_date,collaborators")
            .order("created_at", desc=True)
        )

        if project_id:
            query = query.eq("project_id", project_id)

        response = query.execute()
        rows: List[Dict[str, Any]] = response.data or []

        # Filter by user_id: include projects where user is creator OR collaborator
        if user_id:
            filtered_rows = []
            for row in rows:
                # Check if user is the creator
                if row.get("created_by") == user_id:
                    filtered_rows.append(row)
                # Check if user is in collaborators array
                elif user_id in (row.get("collaborators") or []):
                    filtered_rows.append(row)
            rows = filtered_rows

        if limit_param:
            rows = rows[:limit_param]

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

        # Get the user making the request
        requesting_user_id = body.get("user_id", "").strip()
        if not requesting_user_id:
            return jsonify({"error": "user_id is required for authorization"}), 400

        # Check if project exists and get current project data
        project_response = supabase.table("project").select("*").eq("project_id", project_id).execute()
        if not project_response.data:
            return jsonify({"error": "Project not found"}), 404

        current_project = project_response.data[0]

        # Verify ownership - only the creator can edit the project
        if current_project.get("created_by") != requesting_user_id:
            return jsonify({"error": "Only the project owner can edit this project"}), 403

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

        if "collaborators" in body:
            collaborators = body["collaborators"]
            update_data["collaborators"] = collaborators if isinstance(collaborators, list) else []

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
        # Get the user making the request from query parameter
        requesting_user_id = request.args.get("user_id", "").strip()
        if not requesting_user_id:
            return jsonify({"error": "user_id is required for authorization"}), 400

        # Check if project exists and get current project data
        project_response = supabase.table("project").select("*").eq("project_id", project_id).execute()
        if not project_response.data:
            return jsonify({"error": "Project not found"}), 404

        current_project = project_response.data[0]

        # Verify ownership - only the creator can delete the project
        if current_project.get("created_by") != requesting_user_id:
            return jsonify({"error": "Only the project owner can delete this project"}), 403

        # Delete the project from Supabase
        response = supabase.table("project").delete().eq("project_id", project_id).execute()

        if not response.data:
            return jsonify({"error": "Project not found"}), 404

        return jsonify({"message": "Project deleted successfully"}), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# Project Comments API Routes (Read and Create only)

@app.route("/projects/<project_id>/comments", methods=["GET"])
def get_project_comments(project_id):
    """
    GET /projects/<project_id>/comments - Get all comments for a specific project
    """
    try:
        # Validate project exists
        project_response = supabase.table("project").select("project_id").eq("project_id", project_id).execute()
        if not project_response.data:
            return jsonify({"error": "Project not found"}), 404

        # Get comments for the project
        response = supabase.table("project_comment").select(
            "comment_id, project_id, user_id, comment_text, created_at"
        ).eq("project_id", project_id).order("created_at", desc=False).execute()

        comments = response.data or []
        
        return jsonify({"comments": comments, "count": len(comments)}), 200

    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve comments: {str(exc)}"}), 500


@app.route("/projects/<project_id>/comments", methods=["POST"])
def add_project_comment(project_id):
    """
    POST /projects/<project_id>/comments - Add a new comment to a project
    """
    try:
        # Validate project exists and get project data
        project_response = supabase.table("project").select("*").eq("project_id", project_id).execute()
        if not project_response.data:
            return jsonify({"error": "Project not found"}), 404

        project = project_response.data[0]

        body = request.get_json(silent=True) or {}

        # Validate required fields
        comment_text = body.get("comment_text", "").strip()
        user_id = body.get("user_id", "").strip()

        if not comment_text:
            return jsonify({"error": "comment_text is required"}), 400

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Get user information for the commenter
        user_response = supabase.table("user").select("name").eq("user_id", user_id).execute()
        user_name = "Unknown User"
        if user_response.data:
            user = user_response.data[0]
            user_name = user.get('name', '').strip()
            if not user_name:
                user_name = "Unknown User"

        # Prepare comment data
        comment_data = {
            "project_id": project_id,
            "user_id": user_id,
            "comment_text": comment_text,
            "created_at": datetime.utcnow().isoformat()
        }

        # Insert comment
        response = supabase.table("project_comment").insert(comment_data).execute()

        if not response.data:
            return jsonify({"error": "Failed to add comment"}), 500

        created_comment = response.data[0]

        # Send notifications to all stakeholders (creator + collaborators) except the commenter
        try:
            notify_project_comment(
                project_data=project,
                comment_text=comment_text,
                commenter_id=user_id,
                commenter_name=user_name
            )
            print(f"✅ Project comment notifications sent for project {project_id}")
        except Exception as notification_error:
            print(f"⚠️ Failed to send project comment notifications: {notification_error}")
            # Don't fail the request if notifications fail

        return jsonify({
            "success": True,
            "comment": created_comment,
            "message": "Comment added successfully"
        }), 201

    except Exception as exc:
        return jsonify({"error": f"Failed to add comment: {str(exc)}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8082))
    app.run(host="0.0.0.0", port=port)