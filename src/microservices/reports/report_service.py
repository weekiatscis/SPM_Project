import os
import io
import sys
import json
import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from collections import Counter
from enum import Enum

# Configure logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Now import other packages
from supabase import create_client, Client
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.colors import HexColor

# Add this import
try:
    from svglib.svglib import svg2rlg
except ImportError:
    svg2rlg = None
    logger.warning("svglib not available - logo will be text-based")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    # Try multiple possible .env locations
    env_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'),  # Original path
        os.path.join(os.path.dirname(__file__), '.env'),  # Same directory
        '.env',  # Current working directory
        '/app/.env'  # Docker working directory
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
            print(f"✅ Loaded environment from: {env_path}")
            env_loaded = True
            break
    
    if not env_loaded:
        print("⚠️  No .env file found, using system environment variables")
        load_dotenv()  # Load from system environment
        
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")
    print("Using system environment variables instead")

# Environment variables
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://task-service:8080")
PROJECT_SERVICE_URL = os.getenv("PROJECT_SERVICE_URL", "http://project-service:8082")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8081")
# Add after TASK_SERVICE_URL line
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logger.error("Missing required environment variables:")
    logger.error(f"SUPABASE_URL: {'✓' if SUPABASE_URL else '✗ MISSING'}")
    logger.error(f"SUPABASE_SERVICE_ROLE_KEY: {'✓' if SUPABASE_SERVICE_ROLE_KEY else '✗ MISSING'}")
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Initialize Flask app
app = Flask(__name__)
CORS(app)


def fetch_tasks_for_user(user_id: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         status_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch tasks from the task service for a specific user.

    Args:
        user_id: The user ID to fetch tasks for
        start_date: Optional start date filter (ISO format: YYYY-MM-DD)
        end_date: Optional end date filter (ISO format: YYYY-MM-DD)
        status_filter: Optional list of status filters (e.g., ['Ongoing', 'Completed'])

    Returns:
        List of task dictionaries
    """
    try:
        # Call task service API
        url = f"{TASK_SERVICE_URL}/tasks?owner_id={user_id}"
        logger.info(f"Fetching tasks from: {url}")
        logger.info(f"🔍 TASK_SERVICE_URL: {TASK_SERVICE_URL}")

        response = requests.get(url, timeout=10)
        logger.info(f"🔍 Response status: {response.status_code}")
        
        response.raise_for_status()

        data = response.json()
        tasks = data.get('tasks', [])
        logger.info(f"🔍 Raw tasks received: {len(tasks)}")
        logger.info(f"🔍 First few tasks: {tasks[:2] if tasks else 'No tasks'}")
        logger.info(f"🔍 Status filter: {status_filter}")
        logger.info(f"🔍 Date filters - start: {start_date}, end: {end_date}")

        # Apply filters
        filtered_tasks = []
        for task in tasks:
            # Normalize task fields to match expected format
            normalized_task = {
                'id': task.get('id'),
                'title': task.get('title', task.get('name', 'Untitled')),
                'status': task.get('status', 'Unknown'),
                'created_at': task.get('created_at'),
                'updated_at': task.get('updated_at'),
                'due_date': task.get('due_date', task.get('dueDate')),  # Handle both formats
                'description': task.get('description', ''),
                'owner_id': task.get('owner_id', task.get('ownerId')),
            }
            
            # Status filter - check if task status is in the list of selected statuses
            if status_filter and len(status_filter) > 0 and 'All' not in status_filter:
                task_status = normalized_task.get('status', '').lower()
                logger.info(f"🔍 Checking task {normalized_task.get('title', 'Unknown')} - status: '{task_status}' against filter: {[s.lower() for s in status_filter]}")
                if not any(status.lower() == task_status for status in status_filter):
                    logger.info(f"🔍 Task filtered out due to status")
                    continue
                logger.info(f"🔍 Task passed status filter")

            # Date range filter (based on assigned date - created_at)
            if start_date or end_date:
                created_at = normalized_task.get('created_at')
                if created_at:
                    try:
                        # Parse the date (handle both ISO format and date-only)
                        if 'T' in created_at:
                            task_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                        else:
                            task_date = datetime.fromisoformat(created_at).date()

                        if start_date:
                            start = datetime.fromisoformat(start_date).date()
                            if task_date < start:
                                continue

                        if end_date:
                            end = datetime.fromisoformat(end_date).date()
                            if task_date > end:
                                continue
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Could not parse date for task {normalized_task.get('id')}: {e}")
                        continue

            logger.info(f"🔍 Task '{normalized_task.get('title', 'Unknown')}' passed all filters")
            filtered_tasks.append(normalized_task)

        logger.info(f"🔍 FINAL: Filtered {len(filtered_tasks)} tasks from {len(tasks)} for user {user_id}")
        logger.info(f"🔍 Filtered task titles: {[t.get('title', 'Unknown') for t in filtered_tasks[:5]]}")
        return filtered_tasks

    except requests.RequestException as e:
        logger.error(f"Error fetching tasks from task service: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching tasks: {e}")
        raise


def fetch_user_info(user_id: str) -> Dict[str, str]:
    """
    Fetch user information from user service.

    Args:
        user_id: The user ID (UUID)

    Returns:
        Dictionary with user's name and department or defaults if not found
    """
    try:
        # Use the user-service endpoint which has full user info including department
        user_url = f"{USER_SERVICE_URL}/users/{user_id}"
        response = requests.get(user_url, timeout=5)

        if response.ok:
            user_data = response.json().get('user', {})
            return {
                'name': user_data.get('name', 'Unknown'),
                'department': user_data.get('department', 'N/A')
            }
        else:
            logger.warning(f"Could not fetch user {user_id}: HTTP {response.status_code}")
            return {'name': 'Unknown', 'department': 'N/A'}
    except Exception as e:
        logger.warning(f"Error fetching user {user_id}: {e}")
        return {'name': 'Unknown', 'department': 'N/A'}


def fetch_project_report_data(project_id: str, requesting_user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch and prepare project report data for preview or PDF generation.

    Args:
        project_id: The project ID to generate report for
        requesting_user_id: The user ID of the person generating the report

    Returns:
        Dictionary containing all report data
    """
    try:
        # Fetch project details
        project_url = f"{PROJECT_SERVICE_URL}/projects"
        logger.info(f"Fetching project from: {project_url}")

        project_response = requests.get(project_url, timeout=10)
        project_response.raise_for_status()
        all_projects = project_response.json().get('projects', [])

        # Find the specific project
        project_data = None
        for proj in all_projects:
            if proj.get('project_id') == project_id:
                project_data = proj
                break

        if not project_data:
            raise Exception(f"Project {project_id} not found")

        # Fetch tasks for this project (tasks with matching project_id)
        tasks_url = f"{TASK_SERVICE_URL}/tasks?project_id={project_id}"
        logger.info(f"Fetching project tasks from: {tasks_url}")

        tasks_response = requests.get(tasks_url, timeout=10)
        tasks_response.raise_for_status()
        tasks = tasks_response.json().get('tasks', [])

        # Enrich tasks with user names and departments
        # Collect all unique user IDs
        user_ids = set()
        for task in tasks:
            if task.get('owner_id'):
                user_ids.add(task.get('owner_id'))

        # Fetch user info in batch
        user_info_cache = {}
        for user_id in user_ids:
            user_info_cache[user_id] = fetch_user_info(user_id)

        # Add user names and departments to tasks
        for task in tasks:
            owner_id = task.get('owner_id')
            if owner_id and owner_id in user_info_cache:
                task['owner_name'] = user_info_cache[owner_id]['name']
                task['assignee_name'] = user_info_cache[owner_id]['name']
                task['owner_department'] = user_info_cache[owner_id]['department']
            else:
                task['owner_name'] = 'Unassigned'
                task['assignee_name'] = 'Unassigned'
                task['owner_department'] = 'N/A'

        # Fetch project owner info
        project_owner_id = project_data.get('created_by')
        project_owner_name = 'Unknown'
        if project_owner_id:
            project_owner_info = fetch_user_info(project_owner_id)
            project_owner_name = project_owner_info['name']

        logger.info(f"Fetched project {project_id} with {len(tasks)} tasks")

        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get('status', '').lower() == 'completed'])
        ongoing_tasks = len([t for t in tasks if t.get('status', '').lower() == 'ongoing'])
        under_review_tasks = len([t for t in tasks if t.get('status', '').lower() == 'under review'])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Count tasks by team member with department info
        tasks_by_member = {}
        completed_by_member = {}
        member_departments = {}

        for task in tasks:
            assignee = task.get('assignee_name', task.get('owner_name', 'Unassigned'))
            department = task.get('owner_department', 'N/A')

            tasks_by_member[assignee] = tasks_by_member.get(assignee, 0) + 1
            member_departments[assignee] = department

            if task.get('status', '').lower() == 'completed':
                completed_by_member[assignee] = completed_by_member.get(assignee, 0) + 1

        # Group tasks by status with overdue calculation
        today = datetime.now(timezone.utc).date()
        task_groups = {
            'Overdue': [],
            'Ongoing': [],
            'Under Review': [],
            'Completed': [],
            'Unassigned': []
        }

        for task in tasks:
            status = task.get('status', 'Unassigned')
            due_date_str = task.get('dueDate', task.get('due_date', ''))

            # Check if task is overdue
            is_overdue = False
            if due_date_str and status.lower() != 'completed':
                try:
                    if 'T' in due_date_str:
                        task_due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
                    else:
                        task_due_date = datetime.fromisoformat(due_date_str).date()

                    if task_due_date < today:
                        is_overdue = True
                except:
                    pass

            # Categorize task
            if is_overdue:
                task_groups['Overdue'].append(task)
            elif status in task_groups:
                task_groups[status].append(task)
            else:
                status_lower = status.lower()
                if 'ongoing' in status_lower or 'progress' in status_lower:
                    task_groups['Ongoing'].append(task)
                elif 'review' in status_lower:
                    task_groups['Under Review'].append(task)
                elif 'completed' in status_lower:
                    task_groups['Completed'].append(task)
                else:
                    task_groups['Unassigned'].append(task)

        # Format dates
        created_date = project_data.get('created_at', 'N/A')
        due_date = project_data.get('due_date', 'N/A')

        if created_date and created_date != 'N/A':
            try:
                if 'T' in created_date:
                    created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00')).strftime('%B %d, %Y')
                else:
                    created_date = datetime.fromisoformat(created_date).strftime('%B %d, %Y')
            except:
                created_date = 'N/A'

        if due_date and due_date != 'N/A':
            try:
                if 'T' in due_date:
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%B %d, %Y')
                else:
                    due_date = datetime.fromisoformat(due_date).strftime('%B %d, %Y')
            except:
                due_date = 'N/A'

        # Build team member performance list
        team_performance = []
        for member, total in sorted(tasks_by_member.items(), key=lambda x: x[1], reverse=True):
            completed = completed_by_member.get(member, 0)
            rate = (completed / total * 100) if total > 0 else 0
            team_performance.append({
                'member': member,
                'department': member_departments.get(member, 'N/A'),
                'total': total,
                'completed': completed,
                'rate': round(rate, 1)
            })

        # Calculate overdue count
        overdue_count = len(task_groups.get('Overdue', []))

        # Separate tasks into "My Tasks" and "Other Tasks" if requesting_user_id is provided
        my_tasks = []
        other_tasks = []
        requesting_user_name = None

        if requesting_user_id:
            # Get requesting user info
            requesting_user_info = fetch_user_info(requesting_user_id)
            requesting_user_name = requesting_user_info['name']

            # Parse collaborators if they're JSON string
            for task in tasks:
                task_owner_id = task.get('owner_id')
                task_collaborators = task.get('collaborators', [])

                # Handle collaborators as JSON string
                if isinstance(task_collaborators, str):
                    try:
                        task_collaborators = json.loads(task_collaborators)
                    except:
                        task_collaborators = []

                # Check if user owns or collaborates on this task
                is_user_task = (
                    task_owner_id == requesting_user_id or
                    requesting_user_id in task_collaborators
                )

                if is_user_task:
                    my_tasks.append(task)
                else:
                    other_tasks.append(task)

        # Return structured report data
        return {
            'project': {
                'id': project_data.get('project_id'),
                'name': project_data.get('project_name', 'Untitled Project'),
                'description': project_data.get('project_description', 'No description'),
                'owner': project_owner_name,
                'status': project_data.get('status', 'Active'),
                'created_date': created_date,
                'due_date': due_date,
                'collaborators': project_data.get('collaborators', [])
            },
            'summary': {
                'total_tasks': total_tasks,
                'overdue_tasks': overdue_count,
                'completed_tasks': completed_tasks,
                'ongoing_tasks': ongoing_tasks,
                'under_review_tasks': under_review_tasks,
                'completion_rate': round(completion_rate, 1)
            },
            'team_performance': team_performance,
            'task_groups': {
                'Overdue': task_groups['Overdue'],
                'Ongoing': task_groups['Ongoing'],
                'Under Review': task_groups['Under Review'],
                'Completed': task_groups['Completed'],
                'Unassigned': task_groups['Unassigned']
            },
            'my_tasks': my_tasks,
            'other_tasks': other_tasks,
            'requesting_user_name': requesting_user_name,
            'requesting_user_id': requesting_user_id,
            'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }

    except requests.RequestException as e:
        logger.error(f"Error fetching project data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error preparing project report data: {e}")
        raise


def calculate_duration(assigned_date: Optional[str], completion_date: Optional[str]) -> str:
    """Calculate duration between assigned and completion dates."""
    if not completion_date or not assigned_date:
        return "Ongoing"

    try:
        # Parse dates
        if 'T' in assigned_date:
            start = datetime.fromisoformat(assigned_date.replace('Z', '+00:00'))
        else:
            start = datetime.fromisoformat(assigned_date)

        if 'T' in completion_date:
            end = datetime.fromisoformat(completion_date.replace('Z', '+00:00'))
        else:
            end = datetime.fromisoformat(completion_date)

        duration = (end - start).days

        # Handle negative durations (shouldn't happen, but guard against bad data)
        if duration < 0:
            return "< 1 day"
        elif duration == 0:
            return "< 1 day"
        elif duration == 1:
            return "1 day"
        else:
            return f"{duration} days"
    except (ValueError, AttributeError):
        return "N/A"


def generate_pie_chart(tasks: List[Dict[str, Any]]) -> Drawing:
    """Generate a pie chart showing task status distribution with legend."""
    from reportlab.graphics.shapes import Rect, String

    # Count tasks by status
    status_counts = Counter(task.get('status', 'Unknown') for task in tasks)

    # Prepare data for pie chart
    labels = list(status_counts.keys())
    data = list(status_counts.values())

    # Define colors for different statuses
    color_map = {
        'Ongoing': HexColor("#3b82f6"),      # Blue
        'Completed': HexColor("#22c55e"),    # Green
        'Unassigned': HexColor('#94a3b8'),   # Gray
        'In Progress': HexColor("#f59e0b"),  # Orange
        'Under Review': HexColor("#a855f7"), # Purple
        'Blocked': HexColor('#ef4444'),      # Red
    }

    chart_colors = [color_map.get(label, HexColor('#d9d9d9')) for label in labels]

    # Create drawing with more space
    drawing = Drawing(500, 250)

    # Create pie chart
    pie = Pie()
    pie.x = 80
    pie.y = 50
    pie.width = 170
    pie.height = 170
    pie.data = data

    # Style the pie chart
    pie.slices.strokeWidth = 2
    pie.slices.strokeColor = colors.white
    pie.simpleLabels = 0  # Don't show labels on slices for cleaner look
    pie.sideLabels = 0

    # Apply colors
    for i, color in enumerate(chart_colors):
        pie.slices[i].fillColor = color

    drawing.add(pie)

    # Add legend manually with better formatting
    legend_x = 280
    legend_y = 200
    box_size = 12
    spacing = 22

    for i, (label, count) in enumerate(zip(labels, data)):
        y_pos = legend_y - (i * spacing)

        # Color box
        rect = Rect(legend_x, y_pos - box_size/2, box_size, box_size)
        rect.fillColor = chart_colors[i]
        rect.strokeColor = colors.whitesmoke
        rect.strokeWidth = 0.5
        drawing.add(rect)

        # Label text with count
        percentage = count/sum(data)*100 if sum(data) > 0 else 0
        text = String(legend_x + box_size + 8, y_pos - 3,
                     f"{label}: {count} ({percentage:.1f}%)")
        text.fontSize = 10
        text.fillColor = HexColor('#262626')
        text.fontName = 'Helvetica'
        drawing.add(text)

    return drawing


def generate_pdf_report(user_id: str, user_name: str, tasks: List[Dict[str, Any]],
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None,
                       status_filter: Optional[List[str]] = None) -> io.BytesIO:
    """
    Generate a PDF report for the given tasks.

    Args:
        user_id: User ID
        user_name: User's display name
        tasks: List of task dictionaries
        start_date: Optional start date filter
        end_date: Optional end date filter
        status_filter: Optional list of status filters

    Returns:
        BytesIO buffer containing the PDF
    """
    # Create a buffer to hold the PDF
    buffer = io.BytesIO()

    # Create the PDF document with better margins
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=50, leftMargin=50,
                           topMargin=50, bottomMargin=50)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()

    # Enhanced title style with modern look - bold and prominent
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#0f172a'),
        spaceAfter=10,
        spaceBefore=0,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        leading=28,
        leftIndent=0,
        rightIndent=0
    )

    # Section heading style - bold with more prominent appearance
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        leftIndent=0,
        rightIndent=0,
        borderPadding=(0, 0, 6, 0)  # Bottom padding for visual separation
    )

    # Info text style
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#475569'),
        spaceAfter=8,
        fontName='Helvetica',
        leading=14
    )

    # Branded header with logo (shared across reports)
    elements.extend(build_report_header("Task Progress Report", styles))

    # Report metadata in a clean info box
    metadata_data = [
        ['Staff Member:', user_name],
        ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')]
    ]

    if start_date and end_date:
        metadata_data.append(['Date Range:', f"{start_date} to {end_date}"])
    elif start_date:
        metadata_data.append(['Date Range:', f"From {start_date}"])
    elif end_date:
        metadata_data.append(['Date Range:', f"Until {end_date}"])
    else:
        metadata_data.append(['Date Range:', 'All time'])

    if status_filter and len(status_filter) > 0 and 'All' not in status_filter:
        metadata_data.append(['Status Filter:', ', '.join(status_filter)])

    # Create metadata table with clean styling
    metadata_table = Table(metadata_data, colWidths=[1.5*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#475569')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#1e293b')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 20))

    # Summary statistics in a modern card-style layout
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get('status', '').lower() == 'completed'])
    ongoing_tasks = len([t for t in tasks if t.get('status', '').lower() == 'ongoing'])
    completion_rate = (completed_tasks/total_tasks*100) if total_tasks > 0 else 0

    # Summary section heading
    summary_heading = Paragraph("Summary", heading_style)
    elements.append(summary_heading)
    elements.append(Spacer(1, 8))

    # Summary statistics in a grid layout
    summary_data = [
        ['Total Tasks', 'Completed', 'In Progress', 'Completion Rate'],
        [str(total_tasks), str(completed_tasks), str(ongoing_tasks), f"{completion_rate:.1f}%"]
    ]

    summary_table = Table(summary_data, colWidths=[1.3*inch, 1.3*inch, 1.3*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        # Header row
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#64748b')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        # Data row
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 18),
        ('TEXTCOLOR', (0, 1), (-1, 1), HexColor('#1e293b')),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('TOPPADDING', (0, 1), (-1, 1), 5),

        # Styling
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#f1f5f9')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Add pie chart if there are tasks
    if tasks:
        chart_heading = Paragraph("Task Status Distribution", heading_style)
        elements.append(chart_heading)
        elements.append(Spacer(1, 8))

        pie_chart = generate_pie_chart(tasks)
        elements.append(pie_chart)
        elements.append(Spacer(1, 20))

    # Task details table - start on new page for cleaner layout
    elements.append(PageBreak())
    table_heading = Paragraph("Task Details", heading_style)
    elements.append(table_heading)
    elements.append(Spacer(1, 8))

    if tasks:
        # Table headers
        table_data = [
            ['Task Title', 'Created Date', 'Status', 'Time on Task']
        ]

        # Track completed task row indices for styling
        completed_rows = []

        # Add task rows
        for idx, task in enumerate(tasks, start=1):  # start=1 because row 0 is header
            # Get created date (assigned date)
            created_date = task.get('created_at', 'N/A')
            if created_date and created_date != 'N/A':
                try:
                    if 'T' in created_date:
                        created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    else:
                        created_date = datetime.fromisoformat(created_date).strftime('%Y-%m-%d')
                except:
                    created_date = 'N/A'

            # Calculate duration - for completed tasks, use updated_at as completion date
            # For ongoing tasks, calculate from created to now
            task_status = task.get('status', '').lower()
            if task_status == 'completed':
                duration = calculate_duration(
                    task.get('created_at'),
                    task.get('updated_at')
                )
                # Track this row as completed for styling
                completed_rows.append(idx)
            else:
                # For ongoing tasks, calculate duration from creation to now
                try:
                    created_at_str = task.get('created_at')
                    if created_at_str:
                        if 'T' in created_at_str:
                            created_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        else:
                            created_dt = datetime.fromisoformat(created_at_str)

                        days_elapsed = (datetime.now(timezone.utc) - created_dt).days
                        if days_elapsed == 0:
                            duration = "< 1 day"
                        elif days_elapsed == 1:
                            duration = "1 day"
                        else:
                            duration = f"{days_elapsed} days"
                    else:
                        duration = "N/A"
                except:
                    duration = "N/A"

            table_data.append([
                task.get('title', 'Untitled')[:40],  # Truncate long titles
                created_date,
                task.get('status', 'Unknown'),
                duration
            ])

        # Create table with better proportions (4 columns now)
        table = Table(table_data, colWidths=[3.2*inch, 1.3*inch, 1.1*inch, 1.2*inch])

        # Build table style with conditional formatting
        table_style = [
            # Header row - modern blue gradient look
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Status column centered
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),  # Time on Task column centered
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),

            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#1e293b')),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),

            # Border styling
            ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, HexColor('#2563eb')),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, HexColor('#e2e8f0')),

            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Apply alternating row colors for non-completed tasks and green for completed
        for row_idx in range(1, len(table_data)):
            if row_idx in completed_rows:
                # Light green background for completed tasks
                table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), HexColor('#d1fae5')))
            else:
                # Alternating white/light gray for other tasks
                bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
                table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color))

        table.setStyle(TableStyle(table_style))

        elements.append(table)
    else:
        # No tasks message with better styling
        no_tasks_style = ParagraphStyle(
            'NoTasks',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#64748b'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        no_tasks_text = Paragraph("No tasks found matching the selected criteria.", no_tasks_style)
        elements.append(Spacer(1, 20))
        elements.append(no_tasks_text)
        elements.append(Spacer(1, 20))

    # Build PDF
    doc.build(elements)

    # Reset buffer position to beginning
    buffer.seek(0)

    return buffer


def generate_project_pdf_report(report_data: Dict[str, Any]) -> io.BytesIO:
    """
    Generate a PDF report for a project.

    Args:
        report_data: Dictionary containing project report data

    Returns:
        BytesIO buffer containing the PDF
    """
    # Create a buffer to hold the PDF
    buffer = io.BytesIO()

    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=50, leftMargin=50,
                           topMargin=50, bottomMargin=50)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()

    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#0f172a'),
        spaceAfter=10,
        spaceBefore=0,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        leading=28,
        leftIndent=0,
        rightIndent=0
    )

    # Heading style
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        leftIndent=0,
        rightIndent=0,
        borderPadding=(0, 0, 6, 0)
    )

    # Load logo
    from reportlab.graphics.shapes import Line, Drawing as ShapeDrawing
    from svglib.svglib import svg2rlg

    logo_path = os.path.join(os.path.dirname(__file__), 'taskio-logo.svg')
    logo = None
    if os.path.exists(logo_path):
        try:
            logo_drawing = svg2rlg(logo_path)
            scale_factor = 0.35
            logo_drawing.width = logo_drawing.width * scale_factor
            logo_drawing.height = logo_drawing.height * scale_factor
            logo_drawing.scale(scale_factor, scale_factor)
            logo = logo_drawing
        except Exception as e:
            logger.warning(f"Could not load logo: {e}")

    # Create header table
    if logo:
        header_data = [[
            Paragraph("Project Report", title_style),
            logo
        ]]
        header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
    else:
        header_data = [[
            Paragraph("Project Report", title_style),
            Paragraph('<font name="Helvetica-Bold" size="16" color="#3b82f6">TASKIO</font><br/><font name="Helvetica" size="10" color="#64748b">PROJECT MANAGEMENT</font>',
                     ParagraphStyle('Logo', alignment=TA_RIGHT, leading=14))
        ]]
        header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

    elements.append(header_table)
    elements.append(Spacer(1, 8))

    # Horizontal line
    line_drawing = ShapeDrawing(500, 3)
    line = Line(0, 0, 500, 0)
    line.strokeColor = HexColor('#3b82f6')
    line.strokeWidth = 3
    line_drawing.add(line)
    elements.append(line_drawing)
    elements.append(Spacer(1, 18))

    # Project Overview
    project = report_data['project']
    overview_data = [
        ['Project Name:', project['name']],
        ['Project Owner:', project['owner']],
        ['Start Date:', project['created_date']],
        ['Due Date:', project['due_date']],
        ['Description:', project['description'] or 'No description']
    ]

    overview_table = Table(overview_data, colWidths=[1.5*inch, 4.5*inch])
    overview_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#475569')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#1e293b')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 20))

    # Summary statistics with pie chart
    summary = report_data['summary']
    summary_heading = Paragraph("Project Performance Summary", heading_style)
    elements.append(summary_heading)
    elements.append(Spacer(1, 12))

    # Calculate overdue count from task groups
    overdue_count = len(report_data['task_groups'].get('Overdue', []))

    # Create pie chart for task distribution
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.shapes import Drawing, Rect, String

    # Prepare pie chart data
    pie_labels = []
    pie_data = []
    pie_colors = []

    if overdue_count > 0:
        pie_labels.append('Overdue')
        pie_data.append(overdue_count)
        pie_colors.append(HexColor('#ef4444'))

    if summary['completed_tasks'] > 0:
        pie_labels.append('Completed')
        pie_data.append(summary['completed_tasks'])
        pie_colors.append(HexColor('#22c55e'))

    if summary['ongoing_tasks'] > 0:
        pie_labels.append('In Progress')
        pie_data.append(summary['ongoing_tasks'])
        pie_colors.append(HexColor('#3b82f6'))

    if summary['under_review_tasks'] > 0:
        pie_labels.append('Under Review')
        pie_data.append(summary['under_review_tasks'])
        pie_colors.append(HexColor('#a855f7'))

    # Create pie chart
    pie_drawing = Drawing(240, 200)
    pie = Pie()
    pie.x = 40
    pie.y = 30
    pie.width = 140
    pie.height = 140
    pie.data = pie_data if pie_data else [1]  # Show single slice if no data
    pie.slices.strokeWidth = 2
    pie.slices.strokeColor = colors.white
    pie.simpleLabels = 0
    pie.sideLabels = 0

    # Apply colors
    if pie_data:
        for i, color in enumerate(pie_colors):
            pie.slices[i].fillColor = color
    else:
        pie.slices[0].fillColor = HexColor('#e5e7eb')

    pie_drawing.add(pie)

    # Add legend to pie chart
    legend_x = 190
    legend_y = 150
    box_size = 10
    spacing = 20

    for i, (label, count) in enumerate(zip(pie_labels, pie_data)):
        y_pos = legend_y - (i * spacing)

        # Color box
        rect = Rect(legend_x, y_pos - box_size/2, box_size, box_size)
        rect.fillColor = pie_colors[i]
        rect.strokeColor = colors.whitesmoke
        rect.strokeWidth = 0.5
        pie_drawing.add(rect)

        # Label text
        text = String(legend_x + box_size + 5, y_pos - 3, f"{label}: {count}")
        text.fontSize = 8
        text.fillColor = HexColor('#1e293b')
        text.fontName = 'Helvetica'
        pie_drawing.add(text)

    # Statistics table
    stats_data = [
        ['Total Tasks', str(summary['total_tasks'])],
        ['Overdue', str(overdue_count)],
        ['Completed', str(summary['completed_tasks'])],
        ['In Progress', str(summary['ongoing_tasks'])],
        ['Under Review', str(summary['under_review_tasks'])],
        ['Completion Rate', f"{summary['completion_rate']}%"]
    ]

    stats_table = Table(stats_data, colWidths=[1.6*inch, 1*inch])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#475569')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#1e293b')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('LINEAFTER', (0, 0), (0, -1), 0.5, HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ]))

    # Combine pie chart and stats in a single row
    summary_combined = Table([[pie_drawing, stats_table]], colWidths=[2.8*inch, 2.8*inch])
    summary_combined.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(summary_combined)
    elements.append(Spacer(1, 20))

    # Team performance
    if report_data['team_performance']:
        team_heading = Paragraph("Team Member Performance", heading_style)
        elements.append(team_heading)
        elements.append(Spacer(1, 8))

        requesting_user_name = report_data.get('requesting_user_name')
        team_data = [['Team Member', 'Department', 'Total Tasks', 'Completed', 'Completion Rate']]

        for member in report_data['team_performance']:
            member_name = member['member']
            # Add (me) if this is the requesting user
            if requesting_user_name and member_name == requesting_user_name:
                member_name = f"{member_name} (me)"

            team_data.append([
                member_name,
                member.get('department', 'N/A'),
                str(member['total']),
                str(member['completed']),
                f"{member['rate']}%"
            ])

        team_table = Table(team_data, colWidths=[1.8*inch, 1.4*inch, 1*inch, 1*inch, 1.2*inch])
        team_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#1e293b')),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, HexColor('#2563eb')),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        # Alternating row colors and highlight current user
        for row_idx in range(1, len(team_data)):
            member_in_row = report_data['team_performance'][row_idx - 1]['member']

            # Highlight the requesting user's row in blue
            if requesting_user_name and member_in_row == requesting_user_name:
                team_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, row_idx), (-1, row_idx), HexColor('#dbeafe')),
                    ('TEXTCOLOR', (0, row_idx), (-1, row_idx), HexColor('#1e40af')),
                    ('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'),
                ]))
            else:
                bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
                team_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
                ]))

        elements.append(team_table)
        elements.append(Spacer(1, 20))

    # My Tasks and Other Tasks sections - new page
    if report_data.get('requesting_user_id') and (report_data.get('my_tasks') or report_data.get('other_tasks')):
        elements.append(PageBreak())

        # Helper function to create task table
        def create_task_table(task_list, title):
            if not task_list:
                return None

            section_heading = Paragraph(title, heading_style)
            task_data = [['Task Title', 'Assignee', 'Status', 'Priority', 'Due Date']]

            for task in task_list:
                priority = task.get('priority', 'N/A')
                if priority != 'N/A':
                    try:
                        priority = f"{int(priority)}/10"
                    except:
                        priority = 'N/A'

                due_date = task.get('due_date') or task.get('dueDate') or 'N/A'
                if due_date != 'N/A':
                    try:
                        if 'T' in due_date:
                            due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%b %d, %Y')
                        else:
                            due_date = datetime.fromisoformat(due_date).strftime('%b %d, %Y')
                    except:
                        due_date = 'N/A'

                task_data.append([
                    task.get('title', 'Untitled')[:40],  # Truncate long titles
                    (task.get('assignee_name') or task.get('owner_name') or 'Unassigned')[:20],
                    task.get('status', 'Unknown'),
                    priority,
                    due_date
                ])

            task_table = Table(task_data, colWidths=[2.2*inch, 1.3*inch, 1*inch, 0.8*inch, 1.1*inch])
            task_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#1e293b')),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
                ('LINEBELOW', (0, 0), (-1, 0), 1.5, HexColor('#2563eb')),
                ('INNERGRID', (0, 1), (-1, -1), 0.5, HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            # Alternating row colors
            for row_idx in range(1, len(task_data)):
                bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
                task_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
                ]))

            return [section_heading, Spacer(1, 8), task_table, Spacer(1, 20)]

        # Add My Tasks section
        my_tasks = report_data.get('my_tasks', [])
        if my_tasks:
            my_tasks_elements = create_task_table(my_tasks, f"My Tasks ({len(my_tasks)})")
            if my_tasks_elements:
                for elem in my_tasks_elements:
                    elements.append(elem)

        # Add Other Tasks section
        other_tasks = report_data.get('other_tasks', [])
        if other_tasks:
            other_tasks_elements = create_task_table(other_tasks, f"Other Tasks ({len(other_tasks)})")
            if other_tasks_elements:
                for elem in other_tasks_elements:
                    elements.append(elem)

    # Task breakdown - new page
    elements.append(PageBreak())
    tasks_heading = Paragraph("Task Breakdown by Status", heading_style)
    elements.append(tasks_heading)
    elements.append(Spacer(1, 8))

    # Iterate through task groups
    task_groups = report_data['task_groups']
    for status, tasks in task_groups.items():
        if not tasks:
            continue

        # Status section header
        status_para = Paragraph(f"<b>{status}</b> ({len(tasks)} tasks)",
                               ParagraphStyle('StatusHeader', fontSize=12, textColor=HexColor('#1e293b'), spaceAfter=8))
        elements.append(status_para)

        # Tasks table
        task_data = [['Task Title', 'Assignee', 'Priority', 'Due Date']]
        for task in tasks:
            assignee = task.get('assignee_name') or task.get('owner_name') or 'Unassigned'
            priority = task.get('priority', 'N/A')
            if priority != 'N/A':
                try:
                    priority = f"{int(priority)} / 10"
                except:
                    pass

            due_date = task.get('dueDate') or task.get('due_date') or 'N/A'
            if due_date != 'N/A':
                try:
                    if 'T' in due_date:
                        due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    else:
                        due_date = datetime.fromisoformat(due_date).strftime('%Y-%m-%d')
                except:
                    pass

            task_data.append([
                task.get('title', 'Untitled')[:40],
                assignee,
                priority,
                due_date
            ])

        task_table = Table(task_data, colWidths=[3*inch, 1.5*inch, 1*inch, 1.1*inch])
        task_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#1e293b')),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#f1f5f9')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        # Alternating row colors
        for row_idx in range(1, len(task_data)):
            bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
            task_table.setStyle(TableStyle([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
            ]))

        elements.append(task_table)
        elements.append(Spacer(1, 16))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#6b7280'),
        alignment=TA_CENTER
    )
    footer_text = Paragraph(f"Report generated at: {report_data['generated_at']}", footer_style)
    elements.append(Spacer(1, 20))
    elements.append(footer_text)

    # Build PDF
    doc.build(elements)

    # Reset buffer position
    buffer.seek(0)

    return buffer

def build_report_header(title: str, styles) -> List[Any]:
    """Construct a reusable report header with logo branding."""
    header_elements: List[Any] = []

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#0f172a'),
        spaceAfter=10,
        spaceBefore=0,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        leading=28
    )

    logo_path = os.path.join(os.path.dirname(__file__), 'taskio-logo.svg')
    logo = None
    if os.path.exists(logo_path) and svg2rlg:
        try:
            logo_drawing = svg2rlg(logo_path)
            scale_factor = 0.35
            logo_drawing.width = logo_drawing.width * scale_factor
            logo_drawing.height = logo_drawing.height * scale_factor
            logo_drawing.scale(scale_factor, scale_factor)
            logo = logo_drawing
        except Exception as exc:
            logger.warning(f"Could not load logo: {exc}")

    if logo:
        header_data = [[Paragraph(title, title_style), logo]]
    else:
        fallback_style = ParagraphStyle('LogoFallback', parent=styles['Normal'], alignment=TA_RIGHT, leading=14)
        fallback_markup = (
            '<font name="Helvetica-Bold" size="16" color="#3b82f6">TASKIO</font>'
            '<br/><font name="Helvetica" size="10" color="#64748b">PROJECT MANAGEMENT</font>'
        )
        header_data = [[Paragraph(title, title_style), Paragraph(fallback_markup, fallback_style)]]

    header_table = Table(header_data, colWidths=[4 * inch, 2.5 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    header_elements.append(header_table)
    header_elements.append(Spacer(1, 8))

    line_drawing = Drawing(500, 3)
    header_line = Line(0, 0, 500, 0)
    header_line.strokeColor = HexColor('#3b82f6')
    header_line.strokeWidth = 3
    line_drawing.add(header_line)

    header_elements.append(line_drawing)
    header_elements.append(Spacer(1, 18))

    return header_elements

class UserRole(Enum):
    STAFF = "Staff"
    MANAGER = "Manager"
    DIRECTOR = "Director"
    HR = "HR"

class ReportType(Enum):
    INDIVIDUAL = "individual"
    TEAM = "team"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"

def get_user_details(user_id: str) -> Dict[str, Any]:
    """Fetch user details from Supabase."""
    try:
        response = supabase.table('user').select('*').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching user details: {e}")
        return None

def get_team_members(department: str, superior_id: str = None) -> List[Dict[str, Any]]:
    """Fetch team members based on department and/or superior."""
    try:
        query = supabase.table('user').select('*').eq('department', department)
        if superior_id:
            query = query.eq('superior', superior_id)
        response = query.execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching team members: {e}")
        return []

def get_all_departments() -> List[str]:
    """Fetch all unique departments."""
    try:
        response = supabase.table('user').select('department').execute()
        departments = list(set([user['department'] for user in response.data]))
        return departments
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        return []

def validate_report_access(requesting_user: Dict[str, Any], report_data: Dict[str, Any]) -> bool:
    """
    Validate if user has access to generate the requested report type.
    Hierarchical access: HR > Director > Manager > Staff
    """
    user_role = requesting_user.get('role')
    report_type = report_data.get('report_type', 'individual')
    
    logger.info(f"Validating access - User: {requesting_user.get('name')} ({user_role}), Report: {report_type}")
    
    # HR has access to ALL report types and can generate reports for anyone
    if user_role == UserRole.HR.value:
        logger.info("HR user - access granted to all reports")
        return True
    
    # Director can generate: individual, team, department reports
    elif user_role == UserRole.DIRECTOR.value:
        if report_type == ReportType.INDIVIDUAL.value:
            # Directors can generate individual reports for themselves or anyone in their department
            target_user_id = report_data.get('user_id')
            if target_user_id == requesting_user.get('user_id'):
                logger.info("Director generating own individual report - access granted")
                return True
            
            # Check if target user is in director's department
            target_user = get_user_details(target_user_id)
            if target_user and target_user.get('department') == requesting_user.get('department'):
                logger.info("Director generating individual report for department member - access granted")
                return True
            
            logger.warning(f"Director cannot generate individual report for user outside department")
            return False
            
        elif report_type == ReportType.TEAM.value:
            # Directors can generate team reports for teams in their department
            logger.info("Director generating team report - access granted")
            return True
            
        elif report_type == ReportType.DEPARTMENT.value:
            # Directors can generate department reports for their own department
            target_department = report_data.get('department')
            if not target_department or target_department == requesting_user.get('department'):
                logger.info("Director generating department report - access granted")
                return True
            
            logger.warning(f"Director cannot generate department report for other departments")
            return False
            
        elif report_type == ReportType.ORGANIZATION.value:
            logger.warning("Director cannot generate organization reports")
            return False
    
    # Manager can generate: individual, team reports
    elif user_role == UserRole.MANAGER.value:
        if report_type == ReportType.INDIVIDUAL.value:
            # Managers can generate individual reports for themselves or their direct reports
            target_user_id = report_data.get('user_id')
            if target_user_id == requesting_user.get('user_id'):
                logger.info("Manager generating own individual report - access granted")
                return True
            
            # Check if target user reports to this manager
            target_user = get_user_details(target_user_id)
            if target_user and target_user.get('superior') == requesting_user.get('user_id'):
                logger.info("Manager generating individual report for subordinate - access granted")
                return True
            
            logger.warning(f"Manager cannot generate individual report for non-subordinate")
            return False
            
        elif report_type == ReportType.TEAM.value:
            # Managers can generate team reports for their own team
            logger.info("Manager generating team report - access granted")
            return True
            
        elif report_type in [ReportType.DEPARTMENT.value, ReportType.ORGANIZATION.value]:
            logger.warning(f"Manager cannot generate {report_type} reports")
            return False
    
    # Staff can only generate individual reports for themselves
    elif user_role == UserRole.STAFF.value:
        if report_type == ReportType.INDIVIDUAL.value:
            target_user_id = report_data.get('user_id')
            if target_user_id == requesting_user.get('user_id'):
                logger.info("Staff generating own individual report - access granted")
                return True
            
            logger.warning("Staff can only generate their own individual reports")
            return False
            
        else:
            logger.warning(f"Staff cannot generate {report_type} reports")
            return False
    
    logger.warning(f"Unknown role or unauthorized access: {user_role}")
    return False

def fetch_tasks_for_multiple_users(user_ids: List[str], start_date: Optional[str] = None,
                                   end_date: Optional[str] = None,
                                   status_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Fetch tasks for multiple users."""
    all_tasks = []
    for user_id in user_ids:
        try:
            tasks = fetch_tasks_for_user(user_id, start_date, end_date, status_filter)
            all_tasks.extend(tasks)
        except Exception as e:
            logger.warning(f"Failed to fetch tasks for user {user_id}: {e}")
    return all_tasks

def calculate_team_metrics(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate team-level metrics for director reports."""
    total_tasks = len(tasks)
    if total_tasks == 0:
        return {
            'total_tasks': 0,
            'completed_tasks': 0,
            'completion_rate': 0,
            'overdue_tasks': 0,
            'overdue_percentage': 0,
            'total_time_spent': 0,
            'avg_completion_time': 0
        }
    
    completed_tasks = [t for t in tasks if t.get('status', '').lower() == 'completed']
    overdue_tasks = []
    total_time_spent = 0
    completion_times = []
    
    current_date = datetime.now(timezone.utc)
    
    for task in tasks:
        # Check for overdue tasks
        due_date = task.get('due_date')
        if due_date and task.get('status', '').lower() != 'completed':
            try:
                due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                if due_dt < current_date:
                    overdue_tasks.append(task)
            except:
                pass
        
        # Calculate time spent
        created_at = task.get('created_at')
        updated_at = task.get('updated_at', datetime.now().isoformat())
        
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                time_spent = (updated_dt - created_dt).days
                total_time_spent += max(time_spent, 0)
                
                if task.get('status', '').lower() == 'completed':
                    completion_times.append(time_spent)
            except:
                pass
    
    completion_rate = (len(completed_tasks) / total_tasks) * 100
    overdue_percentage = (len(overdue_tasks) / total_tasks) * 100
    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': len(completed_tasks),
        'completion_rate': completion_rate,
        'overdue_tasks': len(overdue_tasks),
        'overdue_percentage': overdue_percentage,
        'total_time_spent': total_time_spent,
        'avg_completion_time': avg_completion_time
    }

def generate_director_report(tasks_by_scope: Dict[str, List[Dict[str, Any]]],
                             requesting_user: Dict[str, Any],
                             filters: Dict[str, Any]) -> io.BytesIO:
    """Generate comparative report for directors/managers/HR with branded layout."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    elements: List[Any] = []
    styles = getSampleStyleSheet()

    report_type = filters.get('report_type')
    report_title = filters.get('report_title')
    if not report_title:
        if report_type == ReportType.TEAM.value:
            report_title = "Team Performance Report"
        elif report_type == ReportType.DEPARTMENT.value:
            report_title = "Department Performance Report"
        else:
            report_title = "Performance Comparison Report"

    elements.extend(build_report_header(report_title, styles))

    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    status_filter = filters.get('status_filter') or []

    metadata_rows: List[List[str]] = [
        ['Generated by:', requesting_user.get('name', 'Unknown')],
        ['Role:', requesting_user.get('role', 'Unknown')],
        ['Report Date:', datetime.now().strftime('%B %d, %Y at %I:%M %p')]
    ]

    departments = filters.get('departments') or []
    if isinstance(departments, str):
        departments = [departments]
    if not departments and filters.get('department'):
        departments = [filters.get('department')]
    if departments:
        metadata_rows.append(['Departments:', ', '.join(departments)])
    elif requesting_user.get('department'):
        metadata_rows.append(['Department:', requesting_user.get('department')])

    scope_label = 'Scopes Analyzed:'
    if report_type == ReportType.TEAM.value:
        scope_label = 'Teams Analyzed:'
    elif report_type == ReportType.DEPARTMENT.value:
        scope_label = 'Teams Compared:' if len(tasks_by_scope) != 1 else 'Team Analyzed:'
    scope_value = ', '.join(tasks_by_scope.keys()) if tasks_by_scope else 'None'
    metadata_rows.append([scope_label, scope_value])

    if start_date and end_date:
        metadata_rows.append(['Date Range:', f"{start_date} to {end_date}"])
    elif start_date:
        metadata_rows.append(['Date Range:', f"From {start_date}"])
    elif end_date:
        metadata_rows.append(['Date Range:', f"Until {end_date}"])

    if status_filter and 'All' not in status_filter:
        metadata_rows.append(['Status Filter:', ', '.join(status_filter)])

    metadata_table = Table(metadata_rows, colWidths=[1.8 * inch, 3.7 * inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#475569')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#1e293b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 24))

    heading_style = ParagraphStyle(
        'ComparisonHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#1e40af'),
        fontName='Helvetica-Bold'
    )

    elements.append(Paragraph("Performance Comparison", heading_style))
    elements.append(Spacer(1, 15))

    comparison_data: List[List[str]] = [
        ['Scope', 'Total Tasks', 'Completed', 'Completion Rate', 'Overdue %', 'Avg. Duration (days)', 'Total Time (days)']
    ]

    for scope_name, scope_tasks in tasks_by_scope.items():
        metrics = calculate_team_metrics(scope_tasks)
        comparison_data.append([
            scope_name,
            str(metrics['total_tasks']),
            str(metrics['completed_tasks']),
            f"{metrics['completion_rate']:.1f}%",
            f"{metrics['overdue_percentage']:.1f}%",
            f"{metrics['avg_completion_time']:.1f}",
            str(metrics['total_time_spent'])
        ])

    if len(comparison_data) == 1:
        comparison_data.append(['No data available', '-', '-', '-', '-', '-', '-'])

    comparison_table = Table(
        comparison_data,
        colWidths=[1.6 * inch, 0.9 * inch, 0.9 * inch, 1.1 * inch, 0.9 * inch, 1.2 * inch, 1.0 * inch]
    )
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),

        ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    for row_idx in range(1, len(comparison_data)):
        bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
        comparison_table.setStyle(TableStyle([
            ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
        ]))

    elements.append(comparison_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_hr_report(data_by_scope: Dict[str, List[Dict[str, Any]]],
                      requesting_user: Dict[str, Any],
                      filters: Dict[str, Any]) -> io.BytesIO:
    """Generate HR-level organization-wide report with comparison insights."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    elements: List[Any] = []
    styles = getSampleStyleSheet()

    report_title = filters.get('report_title') or "Organization Performance Report"
    elements.extend(build_report_header(report_title, styles))

    scope_type = filters.get('scope_type', 'organization')
    scope_values = filters.get('scope_values') or list(data_by_scope.keys())
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    status_filter = filters.get('status_filter') or []

    scope_label_map = {
        'departments': 'Departments Included:',
        'teams': 'Teams Included:',
        'individuals': 'Individuals Included:'
    }

    metadata_rows: List[List[str]] = [
        ['Generated by:', requesting_user.get('name', 'Unknown')],
        ['Role:', requesting_user.get('role', 'Unknown')],
        ['Scope Type:', scope_type.replace('_', ' ').title()],
        ['Report Date:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        [scope_label_map.get(scope_type, 'Scopes Analyzed:'), ', '.join(scope_values) if scope_values else 'Organization-wide']
    ]

    if start_date and end_date:
        metadata_rows.append(['Date Range:', f"{start_date} to {end_date}"])
    elif start_date:
        metadata_rows.append(['Date Range:', f"From {start_date}"])
    elif end_date:
        metadata_rows.append(['Date Range:', f"Until {end_date}"])

    if status_filter and 'All' not in status_filter:
        metadata_rows.append(['Status Filter:', ', '.join(status_filter)])

    metadata_table = Table(metadata_rows, colWidths=[1.8 * inch, 3.7 * inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#475569')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#1e293b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 24))

    heading_style = ParagraphStyle(
        'ScopeHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#1e40af'),
        fontName='Helvetica-Bold'
    )

    # Comparison overview
    elements.append(Paragraph("Scope Comparison Overview", heading_style))
    elements.append(Spacer(1, 15))

    comparison_data: List[List[str]] = [
        ['Scope', 'Total Tasks', 'Completed', 'Completion Rate', 'Overdue %', 'Avg. Duration (days)', 'Total Time (days)']
    ]

    for scope_name, tasks in data_by_scope.items():
        metrics = calculate_team_metrics(tasks)
        comparison_data.append([
            scope_name,
            str(metrics['total_tasks']),
            str(metrics['completed_tasks']),
            f"{metrics['completion_rate']:.1f}%",
            f"{metrics['overdue_percentage']:.1f}%",
            f"{metrics['avg_completion_time']:.1f}",
            str(metrics['total_time_spent'])
        ])

    if len(comparison_data) == 1:
        comparison_data.append(['No data available', '-', '-', '-', '-', '-', '-'])

    comparison_table = Table(
        comparison_data,
        colWidths=[1.6 * inch, 0.9 * inch, 0.9 * inch, 1.1 * inch, 0.9 * inch, 1.2 * inch, 1.0 * inch]
    )
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),

        ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    for row_idx in range(1, len(comparison_data)):
        bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
        comparison_table.setStyle(TableStyle([
            ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
        ]))

    elements.append(comparison_table)
    elements.append(Spacer(1, 24))

    # Detailed summaries per scope
    for scope_name, tasks in data_by_scope.items():
        elements.append(Paragraph(f"{scope_name} Summary", heading_style))
        elements.append(Spacer(1, 10))

        metrics = calculate_team_metrics(tasks)
        summary_data = [
            ['Metric', 'Value'],
            ['Total Tasks', str(metrics['total_tasks'])],
            ['Completed Tasks', str(metrics['completed_tasks'])],
            ['Completion Rate', f"{metrics['completion_rate']:.1f}%"],
            ['Overdue Tasks', str(metrics['overdue_tasks'])],
            ['Overdue Percentage', f"{metrics['overdue_percentage']:.1f}%"],
            ['Total Time Spent', f"{metrics['total_time_spent']} days"],
            ['Average Completion Time', f"{metrics['avg_completion_time']:.1f} days"]
        ]

        summary_table = Table(summary_data, colWidths=[2.5 * inch, 2.0 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        for row_idx in range(1, len(summary_data)):
            bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
            ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 18))

    if not data_by_scope:
        no_data_style = ParagraphStyle(
            'NoData',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#64748b'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph("No data available for the selected scope and filters.", no_data_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "report-service"}), 200

@app.route("/available-users", methods=["GET"])
def get_available_users():
    """Get all users available for HR individual analysis."""
    try:
        response = supabase.table('user').select('user_id, name, department, role').execute()
        users = response.data
        
        # Sort by department, then by name
        users.sort(key=lambda x: (x.get('department', ''), x.get('name', '')))
        
        return jsonify(users), 200
        
    except Exception as e:
        logger.error(f"Error fetching available users: {e}")
        return jsonify({"error": "Failed to fetch available users"}), 500

@app.route("/report-options", methods=["GET"])
def get_report_options():
    """Get available report options based on user role."""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        user = get_user_details(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        role = user.get('role')
        department = user.get('department')
        
        options = {
            'user_role': role,
            'available_report_types': [],
            'departments': [],
            'teams': []
        }
        
        if role == UserRole.STAFF.value:
            options['available_report_types'] = ['individual']
            
        elif role == UserRole.MANAGER.value:
            options['available_report_types'] = ['individual', 'team']
            # Teams is just their own team (managed by them)
            options['teams'] = [f"{user.get('name', 'Unknown')}'s Team"]
            
        elif role == UserRole.DIRECTOR.value:
            options['available_report_types'] = ['individual', 'team', 'department']
            options['departments'] = [department]
            
            # Get teams in their department (by finding all unique superiors in the department)
            dept_members = get_team_members(department)
            superiors = list(set([member.get('superior') for member in dept_members if member.get('superior')]))
            team_names = []
            
            for superior_id in superiors:
                superior_user = get_user_details(superior_id)
                if superior_user:
                    team_names.append(superior_user.get('name', superior_id))
            
            options['teams'] = team_names
            
        elif role == UserRole.HR.value:
            options['available_report_types'] = ['individual', 'team', 'department', 'organization']
            options['departments'] = get_all_departments()
            
            # Get all teams across organization
            all_users = supabase.table('user').select('*').execute().data
            superiors = list(set([user.get('superior') for user in all_users if user.get('superior')]))
            team_names = []
            
            for superior_id in superiors:
                superior_user = get_user_details(superior_id)
                if superior_user:
                    team_names.append(superior_user.get('name', superior_id))
            
            options['teams'] = team_names
            
        return jsonify(options), 200
        
    except Exception as e:
        logger.error(f"Error fetching report options: {e}")
        return jsonify({"error": "Failed to fetch report options"}), 500

@app.route("/generate-report", methods=["POST"])
def generate_report():
    """
    Enhanced report generation supporting different roles and hierarchies.
    """
    try:
        logger.info("=== GENERATE REPORT START ===")
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        # Get requesting user details
        requesting_user_id = data.get('requesting_user_id') or data.get('user_id')
        logger.info(f"Requesting user ID: {requesting_user_id}")
        
        if not requesting_user_id:
            logger.error("No requesting_user_id provided")
            return jsonify({"error": "requesting_user_id is required"}), 400
            
        requesting_user = get_user_details(requesting_user_id)
        logger.info(f"Requesting user details: {requesting_user}")
        
        if not requesting_user:
            logger.error(f"User not found for ID: {requesting_user_id}")
            return jsonify({"error": "User not found"}), 404
        
        report_type = data.get('report_type', 'individual')
        logger.info(f"Report type: {report_type}")
        
        # Validate access
        if not validate_report_access(requesting_user, data):
            logger.error("Access validation failed")
            return jsonify({"error": "Unauthorized to generate this report type"}), 403
        
        # Common parameters
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        status_filter = data.get('status_filter', ['All'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        user_role = requesting_user.get('role')
        logger.info(f"Processing {report_type} report for {user_role}")
        
        if report_type == ReportType.INDIVIDUAL.value:
            # Individual report
            target_user_id = data.get('user_id', requesting_user_id)
            
            # Get the target user's name
            if target_user_id == requesting_user_id:
                user_name = requesting_user.get('name', 'Unknown User')
            else:
                target_user = get_user_details(target_user_id)
                user_name = target_user.get('name', 'Unknown User') if target_user else 'Unknown User'
            
            logger.info(f"Generating individual report for user_id: {target_user_id}, name: {user_name}")
            
            tasks = fetch_tasks_for_user(target_user_id, start_date, end_date, status_filter)
            pdf_buffer = generate_pdf_report(target_user_id, user_name, tasks, start_date, end_date, status_filter)
            filename = f"individual_report_{user_name.replace(' ', '_')}_{timestamp}.pdf"
            
        elif report_type == ReportType.TEAM.value:
            tasks_by_scope: Dict[str, List[Dict[str, Any]]] = {}

            if user_role == UserRole.MANAGER.value:
                team_members = get_team_members(requesting_user.get('department'), requesting_user_id) or []
                member_ids = {requesting_user_id}
                member_ids.update({member['user_id'] for member in team_members if member.get('user_id')})

                team_label = f"{requesting_user.get('name', 'Unknown')}'s Team"
                team_tasks = fetch_tasks_for_multiple_users(list(member_ids), start_date, end_date, status_filter)
                tasks_by_scope[team_label] = team_tasks

            elif user_role in (UserRole.DIRECTOR.value, UserRole.HR.value):
                selected_teams = data.get('teams', [])
                if isinstance(selected_teams, str):
                    selected_teams = [selected_teams]

                if not selected_teams:
                    message = "Team selection is required for Directors" if user_role == UserRole.DIRECTOR.value else "At least one team must be selected"
                    return jsonify({"error": message}), 400

                try:
                    all_users_response = supabase.table('user').select('*').execute()
                    all_users = all_users_response.data or []
                except Exception as exc:
                    logger.error(f"Error fetching users for team report: {exc}")
                    all_users = []

                for team_name in selected_teams:
                    team_members = []
                    team_lead_id = None

                    for user in all_users:
                        superior_id = user.get('superior')
                        if not superior_id:
                            continue

                        superior_user = get_user_details(superior_id)
                        if not superior_user or superior_user.get('name') != team_name:
                            continue

                        if user_role == UserRole.DIRECTOR.value and user.get('department') != requesting_user.get('department'):
                            continue

                        team_members.append(user)
                        team_lead_id = superior_id

                    if team_lead_id:
                        lead_user = get_user_details(team_lead_id)
                        if lead_user and (user_role != UserRole.DIRECTOR.value or lead_user.get('department') == requesting_user.get('department')):
                            team_members.append(lead_user)

                    unique_members = {member['user_id']: member for member in team_members if member.get('user_id')}
                    user_ids = list(unique_members.keys())

                    if user_ids:
                        team_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
                        tasks_by_scope[team_name] = team_tasks

                if not tasks_by_scope:
                    return jsonify({"error": "No team members found for the selected teams"}), 404

                if user_role == UserRole.HR.value:
                    data.setdefault('scope_type', 'teams')
                    data.setdefault('scope_values', selected_teams)

            else:
                return jsonify({"error": "Unauthorized for team reports"}), 403

            data['report_title'] = "Team Performance Report"
            if user_role == UserRole.DIRECTOR.value:
                data.setdefault('departments', [requesting_user.get('department')])

            scope_key = next(iter(tasks_by_scope)) if tasks_by_scope else 'team'
            raw_scope = 'comparison' if len(tasks_by_scope) > 1 else scope_key
            safe_scope = ''.join(ch for ch in raw_scope.replace(' ', '_') if ch.isalnum() or ch in ('_', '-')).lower()
            filename = f"team_report_{safe_scope}_{timestamp}.pdf"
            pdf_buffer = generate_director_report(tasks_by_scope, requesting_user, data)
            
        elif report_type == ReportType.DEPARTMENT.value:
            # Department report
            if user_role == UserRole.DIRECTOR.value:
                # Director department/team comparison report
                department = requesting_user.get('department')
                teams = data.get('teams', [])
                
                tasks_by_team = {}
                
                if teams:
                    # Specific teams requested
                    all_users_response = supabase.table('user').select('*').execute()
                    all_users = all_users_response.data if all_users_response.data else []

                    for team in teams:
                        team_members = []
                        team_lead_user = None

                        for user in all_users:
                            superior_id = user.get('superior')
                            if not superior_id:
                                continue

                            superior_user = get_user_details(superior_id)
                            if superior_user and superior_user.get('name') == team and user.get('department') == department:
                                team_members.append(user)
                                team_lead_user = superior_user

                        unique_members = {member['user_id']: member for member in team_members if member.get('user_id')}

                        if team_lead_user and team_lead_user.get('user_id'):
                            unique_members[team_lead_user['user_id']] = team_lead_user

                        user_ids = list(unique_members.keys())

                        if user_ids:
                            team_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
                            tasks_by_team[team] = team_tasks
                else:
                    # All teams in department
                    all_dept_members = get_team_members(department)
                    # Group by superior (team lead)
                    teams_dict = {}
                    for member in all_dept_members:
                        superior = member.get('superior', 'No Team')
                        if superior not in teams_dict:
                            teams_dict[superior] = []
                        teams_dict[superior].append(member)
                    
                    for team_lead, members in teams_dict.items():
                        unique_ids = {member['user_id'] for member in members if member.get('user_id')}
                        team_lead_user = None

                        if team_lead != 'No Team':
                            team_lead_user = get_user_details(team_lead)
                            if team_lead_user and team_lead_user.get('department') == department and team_lead_user.get('user_id'):
                                unique_ids.add(team_lead_user['user_id'])

                        user_ids = list(unique_ids)

                        if not user_ids:
                            continue

                        team_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)

                        # Get team lead name
                        team_lead_name = 'Unassigned'
                        if team_lead != 'No Team':
                            team_lead_user = get_user_details(team_lead)
                            team_lead_name = team_lead_user.get('name', team_lead) if team_lead_user else team_lead

                        tasks_by_team[team_lead_name] = team_tasks
                
                if not tasks_by_team:
                    return jsonify({"error": "No team data found for the selected department"}), 404

                data.setdefault('departments', [department])
                data['report_title'] = "Department Performance Report"

                scope_key = next(iter(tasks_by_team)) if tasks_by_team else department
                raw_scope = 'comparison' if len(tasks_by_team) > 1 else scope_key
                safe_scope = ''.join(ch for ch in raw_scope.replace(' ', '_') if ch.isalnum() or ch in ('_', '-')).lower()

                pdf_buffer = generate_director_report(tasks_by_team, requesting_user, data)
                filename = f"department_report_{safe_scope}_{timestamp}.pdf"
                
            elif user_role == UserRole.HR.value:
                # HR department report with multi-department comparison support
                selected_departments = data.get('departments') or []
                if isinstance(selected_departments, str):
                    selected_departments = [selected_departments]

                legacy_department = data.get('department')
                if legacy_department and legacy_department not in selected_departments:
                    selected_departments.append(legacy_department)

                if not selected_departments:
                    return jsonify({"error": "Please select at least one department"}), 400

                data_by_scope: Dict[str, List[Dict[str, Any]]] = {}
                for dept in selected_departments:
                    dept_members = get_team_members(dept)
                    member_ids = {member['user_id'] for member in dept_members if member.get('user_id')}
                    if not member_ids:
                        logger.info(f"No members found for department {dept}")
                        continue

                    dept_tasks = fetch_tasks_for_multiple_users(list(member_ids), start_date, end_date, status_filter)
                    data_by_scope[dept] = dept_tasks

                if not data_by_scope:
                    return jsonify({"error": "No task data found for the selected departments"}), 404

                data['scope_type'] = 'departments'
                data['scope_values'] = list(data_by_scope.keys())
                data['report_title'] = "Department Performance Report"

                scope_key = 'comparison' if len(data_by_scope) > 1 else next(iter(data_by_scope))
                safe_scope = ''.join(ch for ch in scope_key.replace(' ', '_') if ch.isalnum() or ch in ('_', '-')).lower()

                pdf_buffer = generate_hr_report(data_by_scope, requesting_user, data)
                filename = f"hr_department_report_{safe_scope}_{timestamp}.pdf"
            else:
                return jsonify({"error": "Unauthorized for department reports"}), 403
                
        elif report_type == ReportType.ORGANIZATION.value and user_role == UserRole.HR.value:
            # HR organization-wide report
            scope_type = data.get('scope_type', 'departments')
            scope_values = data.get('scope_values', [])
            
            data_by_scope = {}
            
            logger.info(f"HR organization report - scope: {scope_type}, values: {scope_values}")
            
            if scope_type == 'departments':
                departments = scope_values if scope_values else get_all_departments()
                logger.info(f"Processing departments: {departments}")
                
                for dept in departments:
                    dept_members = get_team_members(dept)
                    user_ids = [member['user_id'] for member in dept_members]
                    dept_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
                    data_by_scope[dept] = dept_tasks
                    
            elif scope_type == 'teams':
                if scope_values:
                    teams = scope_values
                else:
                    # Get all teams (all unique superiors)
                    all_users = supabase.table('user').select('*').execute().data
                    superiors = list(set([user.get('superior') for user in all_users if user.get('superior')]))
                    teams = []
                    for superior_id in superiors:
                        superior_user = get_user_details(superior_id)
                        if superior_user:
                            teams.append(superior_user.get('name', superior_id))
                
                logger.info(f"Processing teams: {teams}")
                
                for team in teams:
                    # Find team members by superior name
                    all_users = supabase.table('user').select('*').execute().data
                    team_members = []
                    
                    for user in all_users:
                        if user.get('superior'):
                            superior_user = get_user_details(user.get('superior'))
                            if superior_user and superior_user.get('name') == team:
                                team_members.append(user)
                    
                    user_ids = [member['user_id'] for member in team_members]
                    team_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
                    data_by_scope[team] = team_tasks
                        
            elif scope_type == 'individuals':
                individuals = scope_values if scope_values else []
                logger.info(f"Processing individuals: {individuals}")
                
                for user_id in individuals:
                    user = get_user_details(user_id)
                    if user:
                        user_tasks = fetch_tasks_for_user(user_id, start_date, end_date, status_filter)
                        data_by_scope[user.get('name', user_id)] = user_tasks
            
            logger.info(f"Generated data for {len(data_by_scope)} scopes")
            pdf_buffer = generate_hr_report(data_by_scope, requesting_user, data)
            filename = f"organization_report_{scope_type}_{timestamp}.pdf"
            
        else:
            return jsonify({"error": f"Invalid report type '{report_type}' for user role '{user_role}'"}), 400
        
        logger.info(f"Report generated successfully: {filename}")
        
        # Return PDF
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except requests.RequestException as e:
        logger.error(f"Error communicating with task service: {e}")
        return jsonify({"error": "Failed to fetch tasks from task service", "details": str(e)}), 503
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate report", "details": str(e)}), 500


@app.route("/preview-project-report", methods=["POST"])
def preview_project_report():
    """
    Generate project report data for preview (returns JSON).

    Request body:
    {
        "project_id": "project-uuid",
        "user_id": "user-uuid" (optional)
    }

    Returns:
        JSON with report data
    """
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        user_id = data.get('user_id')

        if not project_id:
            return jsonify({"error": "project_id is required"}), 400

        logger.info(f"Generating preview for project {project_id} (user: {user_id})")
        report_data = fetch_project_report_data(project_id, user_id)

        return jsonify(report_data), 200

    except requests.RequestException as e:
        logger.error(f"Error communicating with services: {e}")
        return jsonify({"error": "Failed to fetch project data", "details": str(e)}), 503

    except Exception as e:
        logger.error(f"Error generating project report preview: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate preview", "details": str(e)}), 500


@app.route("/generate-project-report", methods=["POST"])
def generate_project_report_endpoint():
    """
    Generate a PDF report for a project.

    Request body:
    {
        "project_id": "project-uuid",
        "user_id": "user-uuid" (optional)
    }

    Returns:
        PDF file stream
    """
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        user_id = data.get('user_id')

        if not project_id:
            return jsonify({"error": "project_id is required"}), 400

        logger.info(f"Generating PDF report for project {project_id} (user: {user_id})")

        # Fetch project report data
        report_data = fetch_project_report_data(project_id, user_id)

        # Generate PDF
        pdf_buffer = generate_project_pdf_report(report_data)

        # Generate filename
        project_name = report_data['project']['name'].replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"project_report_{project_name}_{timestamp}.pdf"

        # Return PDF as response
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except requests.RequestException as e:
        logger.error(f"Error communicating with services: {e}")
        return jsonify({"error": "Failed to fetch project data", "details": str(e)}), 503

    except Exception as e:
        logger.error(f"Error generating project report PDF: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate PDF", "details": str(e)}), 500

@app.route("/debug-users", methods=["GET"])
def debug_users():
    """Debug user relationships."""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
            
        user = get_user_details(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        result = {
            "user": user,
            "department_members": [],
            "subordinates": []
        }
        
        # Get all users in same department
        dept_members = get_team_members(user.get('department'))
        result["department_members"] = dept_members
        
        # Get direct subordinates
        subordinates = get_team_members(user.get('department'), user_id)
        result["subordinates"] = subordinates
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in debug: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/debug-tasks", methods=["GET"])
def debug_tasks():
    """Debug task fetching and filtering."""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status_filter = request.args.getlist('status_filter') or ['All']
        
        logger.info(f"🔍 DEBUG TASKS: user_id={user_id}, start={start_date}, end={end_date}, status={status_filter}")
        
        # Fetch tasks directly
        tasks = fetch_tasks_for_user(user_id, start_date, end_date, status_filter)
        
        result = {
            "user_id": user_id,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "status_filter": status_filter
            },
            "task_count": len(tasks),
            "tasks": tasks[:3]  # Only return first 3 for debugging
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in debug tasks: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, debug=True)
