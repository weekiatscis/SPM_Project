import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from project root .env
    env_path = os.path.join(os.path.dirname(__file__), '../../..', '.env')
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
except ImportError:
    print("python-dotenv not installed. Using system environment variables only.")

# Email configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "Task Manager")

# Frontend URL for task links
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def create_email_template(notification_type: str, data: dict) -> str:
    """Create HTML email template based on notification type"""

    task_title = data.get("task_title", "Untitled Task")
    due_date = data.get("due_date", "")
    priority = data.get("priority", 5)
    task_id = data.get("task_id", "")
    task_link = f"{FRONTEND_URL}/tasks?taskId={task_id}" if task_id else FRONTEND_URL

    # Convert priority to number if it's a string (for backwards compatibility)
    if isinstance(priority, str):
        priority = int(priority) if priority.isdigit() else 5
    
    # Priority colors based on 1-10 scale
    # 1-4: Low priority (green)
    # 5-7: Medium priority (orange)
    # 8-10: High priority (red)
    if priority >= 8:
        priority_color = "#cf1322"  # Red for high priority
        priority_label = f"Priority: {priority}/10 (High)"
    elif priority >= 5:
        priority_color = "#d46b08"  # Orange for medium priority
        priority_label = f"Priority: {priority}/10 (Medium)"
    else:
        priority_color = "#389e0d"  # Green for low priority
        priority_label = f"Priority: {priority}/10 (Low)"

    # Base HTML template
    base_style = """
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
        .task-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {priority_color}; }
        .priority-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; background: {priority_color}; color: white; }
        .button { display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }
        .button:hover { background: #5568d3; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; }
    </style>
    """.replace("{priority_color}", priority_color)

    if notification_type.startswith("reminder_"):
        days = notification_type.split("_")[1]
        subject = f"⏰ Task Reminder: {task_title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">⏰ Task Reminder</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p>This is a friendly reminder about your upcoming task:</p>

                    <div class="task-card">
                        <h2 style="margin-top: 0; color: #333;">{task_title}</h2>
                        <p><strong>Due Date:</strong> {due_date}</p>
                        <p><strong>Priority:</strong> <span class="priority-badge">{priority_label}</span></p>
                        <p style="color: #666; margin-top: 15px;">This task is due in <strong>{days} day(s)</strong>. Make sure to complete it on time!</p>
                    </div>

                    <center>
                        <a href="{task_link}" class="button">View Task Details</a>
                    </center>

                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        💡 <strong>Tip:</strong> Click the button above to view full task details and update its status.
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this because you have email notifications enabled for this task.</p>
                    <p>Task Manager • Helping you stay productive</p>
                </div>
            </div>
        </body>
        </html>
        """

    elif notification_type == "due_date_change":
        old_due_date = data.get("old_due_date", "")
        new_due_date = data.get("new_due_date", "")
        subject = f"📅 Due Date Changed: {task_title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📅 Due Date Changed</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p>The due date for a task you're collaborating on has been changed:</p>

                    <div class="task-card">
                        <h2 style="margin-top: 0; color: #333;">{task_title}</h2>
                        <p><strong>Priority:</strong> <span class="priority-badge">{priority_label}</span></p>
                        <div style="background: #fff7e6; padding: 15px; border-radius: 6px; margin: 15px 0;">
                            <p style="margin: 5px 0;"><strong>Previous Due Date:</strong> <span style="text-decoration: line-through; color: #999;">{old_due_date}</span></p>
                            <p style="margin: 5px 0;"><strong>New Due Date:</strong> <span style="color: #d46b08; font-weight: bold;">{new_due_date}</span></p>
                        </div>
                    </div>

                    <center>
                        <a href="{task_link}" class="button">View Task Details</a>
                    </center>

                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        Please adjust your schedule accordingly.
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this as a collaborator on this task.</p>
                    <p>Task Manager • Helping you stay productive</p>
                </div>
            </div>
        </body>
        </html>
        """

    elif notification_type == "task_comment":
        comment_text = data.get("comment_text", "")
        commenter_name = data.get("commenter_name", "Someone")
        subject = f"💬 New Comment: {task_title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">💬 New Comment</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p><strong>{commenter_name}</strong> commented on a task you're collaborating on:</p>

                    <div class="task-card">
                        <h2 style="margin-top: 0; color: #333;">{task_title}</h2>
                        <p><strong>Priority:</strong> <span class="priority-badge">{priority}</span></p>
                        {f'<p><strong>Due Date:</strong> {due_date}</p>' if due_date else ''}
                        <div style="background: #f0f5ff; padding: 15px; border-radius: 6px; margin: 15px 0; border-left: 3px solid #1890ff;">
                            <p style="margin: 0; color: #555; font-style: italic;">"{comment_text}"</p>
                        </div>
                    </div>

                    <center>
                        <a href="{task_link}" class="button">View Comment & Reply</a>
                    </center>

                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        💡 <strong>Tip:</strong> Stay engaged with your team by responding to comments promptly.
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this as a collaborator on this task.</p>
                    <p>Task Manager • Helping you stay productive</p>
                </div>
            </div>
        </body>
        </html>
        """

    elif notification_type == "project_comment":
        comment_text = data.get("comment_text", "")
        commenter_name = data.get("commenter_name", "Someone")
        project_name = data.get("project_name", "Untitled Project")
        project_id = data.get("project_id", "")
        project_link = f"{FRONTEND_URL}/projects?projectId={project_id}" if project_id else FRONTEND_URL
        subject = f"💬 New Comment on Project: {project_name}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">💬 New Project Comment</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p><strong>{commenter_name}</strong> commented on a project you're collaborating on:</p>

                    <div class="task-card">
                        <h2 style="margin-top: 0; color: #333;">{project_name}</h2>
                        <div style="background: #f0f5ff; padding: 15px; border-radius: 6px; margin: 15px 0; border-left: 3px solid #1890ff;">
                            <p style="margin: 0; color: #555; font-style: italic;">"{comment_text}"</p>
                        </div>
                    </div>

                    <center>
                        <a href="{project_link}" class="button">View Comment & Reply</a>
                    </center>

                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        💡 <strong>Tip:</strong> Stay engaged with your team by responding to comments promptly.
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this as a collaborator on this project.</p>
                    <p>Task Manager • Helping you stay productive</p>
                </div>
            </div>
        </body>
        </html>
        """

    elif notification_type == "project_created":
        subject = f"📁 New Project Created: {task_title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📁 Project Created</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p>You have successfully created a new project:</p>

                    <div class="task-card">
                        <h2 style="margin-top: 0; color: #333;">{task_title}</h2>
                        {f'<p><strong>Due Date:</strong> {due_date}</p>' if due_date else ''}
                        <p><strong>Priority:</strong> <span class="priority-badge">{priority}</span></p>
                    </div>

                    <center>
                        <a href="{task_link}" class="button">View Project Details</a>
                    </center>

                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        💡 <strong>Tip:</strong> You can now add tasks, collaborate with team members, and track progress.
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this as the project creator.</p>
                    <p>Task Manager • Helping you stay productive</p>
                </div>
            </div>
        </body>
        </html>
        """

    elif notification_type == "project_assigned":
        subject = f"📁 New Project Assigned: {task_title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📁 Project Assigned</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p>You have been assigned to a new project:</p>

                    <div class="task-card">
                        <h2 style="margin-top: 0; color: #333;">{task_title}</h2>
                        {f'<p><strong>Due Date:</strong> {due_date}</p>' if due_date else ''}
                        <p><strong>Priority:</strong> <span class="priority-badge">{priority}</span></p>
                    </div>

                    <center>
                        <a href="{task_link}" class="button">View Project Details</a>
                    </center>

                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        💡 <strong>Tip:</strong> Check the project details and start collaborating with your team.
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this as a project collaborator.</p>
                    <p>Task Manager • Helping you stay productive</p>
                </div>
            </div>
        </body>
        </html>
        """

    else:
        # Generic notification - but only if we have a valid message
        message = data.get("message", "")
        if not message or message.strip() == "":
            # Don't send email if message is empty
            return None, None
            
        subject = f"📬 Notification: {task_title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📬 Notification</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p>{message}</p>

                    <div class="task-card">
                        <h2 style="margin-top: 0; color: #333;">{task_title}</h2>
                        <p><strong>Priority:</strong> <span class="priority-badge">{priority_label}</span></p>
                    </div>

                    <center>
                        <a href="{task_link}" class="button">View Task Details</a>
                    </center>
                </div>
                <div class="footer">
                    <p>Task Manager • Helping you stay productive</p>
                </div>
            </div>
        </body>
        </html>
        """

    return subject, html_content


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email using SMTP"""

    if not SMTP_USER or not SMTP_PASSWORD:
        print("Email credentials not configured. Skipping email send.")
        return False

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        message["To"] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)

        print(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False


def send_notification_email(
    user_email: str,
    notification_type: str,
    task_title: str = None,
    due_date: str = None,
    priority: str = "Medium",
    task_id: Optional[str] = None,
    old_due_date: Optional[str] = None,
    new_due_date: Optional[str] = None,
    message: Optional[str] = None,
    comment_text: Optional[str] = None,
    commenter_name: Optional[str] = None,
    project_name: Optional[str] = None,
    project_id: Optional[str] = None
) -> bool:
    """
    Send notification email for a task or project

    Args:
        user_email: Recipient email address
        notification_type: Type of notification (e.g., 'reminder_7_days', 'due_date_change', 'task_comment', 'project_comment')
        task_title: Title of the task
        due_date: Due date of the task
        priority: Task priority (High, Medium, Low, Lowest)
        task_id: Task ID for linking
        old_due_date: Old due date (for due_date_change notifications)
        new_due_date: New due date (for due_date_change notifications)
        message: Custom message (for generic notifications)
        comment_text: Comment text (for comment notifications)
        commenter_name: Name of person who commented (for comment notifications)
        project_name: Project name (for project comment notifications)
        project_id: Project ID (for project comment notifications)

    Returns:
        bool: True if email sent successfully, False otherwise
    """

    # Prepare data for template
    data = {
        "task_title": task_title,
        "due_date": due_date,
        "priority": priority,
        "task_id": task_id,
        "old_due_date": old_due_date,
        "new_due_date": new_due_date,
        "message": message,
        "comment_text": comment_text,
        "commenter_name": commenter_name,
        "project_name": project_name,
        "project_id": project_id
    }

    # Create email content
    subject, html_content = create_email_template(notification_type, data)

    # Don't send email if template returns None (empty message)
    if subject is None or html_content is None:
        print(f"Skipping email send for {notification_type} - empty message")
        return False

    # Send email
    return send_email(user_email, subject, html_content)


if __name__ == "__main__":
    # Test email sending
    print("=" * 60)
    print("TESTING EMAIL SERVICE")
    print("=" * 60)

    # Check if credentials are configured
    if not SMTP_USER or not SMTP_PASSWORD:
        print("❌ ERROR: Email credentials not configured!")
        print("Please set SMTP_USER and SMTP_PASSWORD in your .env file")
        print("\nExample:")
        print("SMTP_USER=yourname@gmail.com")
        print("SMTP_PASSWORD=your_16_char_app_password")
        exit(1)

    print(f"✓ SMTP configured")
    print(f"  Host: {SMTP_HOST}:{SMTP_PORT}")
    print(f"  User: {SMTP_USER}")
    print(f"  From: {FROM_NAME} <{FROM_EMAIL}>")
    print()

    # Get test email from user
    test_email = input("Enter YOUR email address to receive test email: ").strip()

    if not test_email:
        print("❌ No email provided. Exiting.")
        exit(1)

    print(f"\n📧 Sending test email to: {test_email}")
    print("This may take a few seconds...")
    print()

    test_result = send_notification_email(
        user_email=test_email,
        notification_type="reminder_3_days",
        task_title="Complete Project Documentation",
        due_date="January 18, 2025",
        priority="High",
        task_id="test-123"
    )

    print()
    print("=" * 60)
    if test_result:
        print("✅ SUCCESS! Email sent successfully!")
        print(f"Check your inbox at: {test_email}")
        print("(Also check your spam/junk folder)")
    else:
        print("❌ FAILED! Email could not be sent.")
        print("\nCommon issues:")
        print("1. Gmail App Password incorrect")
        print("2. 2-Factor Authentication not enabled")
        print("3. Network/firewall blocking SMTP")
    print("=" * 60)
