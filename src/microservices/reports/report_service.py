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
from html import escape

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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Line, Rect, String
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
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '.env'),  # Absolute path version
        os.path.join(os.getcwd(), '.env'),  # Current working directory
        '.env',  # Current working directory (relative)
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
        print("⚠️  No .env file found in any location, using system environment variables")
        # List the paths that were tried for debugging
        print(f"Searched paths: {env_paths}")
        load_dotenv()  # Load from system environment
        
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")
    print("Using system environment variables instead")

# Environment variables
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8080")
PROJECT_SERVICE_URL = os.getenv("PROJECT_SERVICE_URL", "http://localhost:8082")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8081")
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


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Safely parse ISO-like datetime or date strings into timezone-aware datetimes."""
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            text = str(value).strip()
            if not text:
                return None
            if text.endswith('Z'):
                text = text[:-1] + '+00:00'
            dt = datetime.fromisoformat(text)
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def calculate_task_duration_metrics(task: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Compute duration-based metrics (in days and hours) for a normalized task record."""
    created_at = parse_datetime(task.get('created_at'))
    updated_at = parse_datetime(task.get('updated_at'))
    completion_ts = parse_datetime(task.get('completed_date')) or parse_datetime(task.get('completed_at'))

    status = (task.get('status') or '').lower()
    if completion_ts is None and status == 'completed':
        completion_ts = updated_at

    completion_time_hours: Optional[float] = None
    completion_time_days: Optional[float] = None
    if created_at and completion_ts:
        diff = (completion_ts - created_at).total_seconds()
        if diff >= 0:
            completion_time_hours = diff / 3600
            completion_time_days = diff / (3600 * 24)  # Convert to days

    time_in_progress_hours: Optional[float] = None
    if created_at:
        effective_end = completion_ts or updated_at or datetime.now(timezone.utc)
        if effective_end:
            diff = (effective_end - created_at).total_seconds()
            if diff >= 0:
                time_in_progress_hours = diff / 3600

    return {
        'completion_time_hours': completion_time_hours,
        'completion_time_days': completion_time_days,
        'time_in_progress_hours': time_in_progress_hours
    }


def sanitize_filename_component(value: Optional[str]) -> str:
    """Return a filesystem-safe slug for filenames."""
    if not value:
        return 'report'
    safe = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in value.strip())
    sanitized = safe.strip('_')
    return sanitized or 'report'


def filter_high_priority_tasks(tasks: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    """Filter and return the highest priority tasks, up to the specified limit."""
    if not tasks:
        return []
    
    # Sort tasks by priority (higher priority number = higher priority)
    # Handle cases where priority might be None, string, or invalid values
    def get_priority_score(task):
        priority = task.get('priority')
        try:
            return int(priority) if priority is not None else 0
        except (ValueError, TypeError):
            return 0
    
    # Sort by priority descending (highest first), then by created date (newest first)
    sorted_tasks = sorted(tasks, key=lambda t: (
        get_priority_score(t) or 0,
        parse_datetime(t.get('created_at')) or datetime.min.replace(tzinfo=timezone.utc)
    ), reverse=True)
    
    return sorted_tasks[:limit]


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
                'priority': task.get('priority', 5),  # Default priority if not set
                'project_id': task.get('project_id'),
                'collaborators': task.get('collaborators', []),
                'completed_date': task.get('completed_date') or task.get('completedDate'),
                'completed_at': task.get('completed_at') or task.get('completedAt'),
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
            duration_metrics = calculate_task_duration_metrics(normalized_task)
            normalized_task.update(duration_metrics)
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
    status_counts = Counter(task.get('status') or 'Unknown' for task in tasks)

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


def generate_bar_chart(data_dict: Dict[str, int], title: str = "Bar Chart", 
                      max_width: int = 450, max_height: int = 250) -> Drawing:
    """Generate a horizontal bar chart with labels and values."""
    from reportlab.graphics.shapes import Rect, String, Line
    
    if not data_dict:
        # Create empty chart
        drawing = Drawing(max_width, max_height)
        text = String(max_width/2, max_height/2, "No data available")
        text.fontName = 'Helvetica'
        text.fontSize = 12
        text.fillColor = colors.grey
        text.textAnchor = 'middle'
        drawing.add(text)
        return drawing
    
    # Prepare data
    labels = list(data_dict.keys())
    values = list(data_dict.values())
    max_value = max(values) if values else 1
    
    # Calculate dimensions
    bar_height = 25
    bar_spacing = 35
    left_margin = 120  # Space for labels
    right_margin = 60  # Space for values
    top_margin = 30
    bottom_margin = 20
    
    chart_width = max_width - left_margin - right_margin
    chart_height = len(labels) * bar_spacing + top_margin + bottom_margin
    
    # Create drawing
    drawing = Drawing(max_width, max(chart_height, max_height))
    
    # Define colors for bars
    colors_list = [
        HexColor("#3b82f6"), HexColor("#22c55e"), HexColor("#f59e0b"),
        HexColor("#a855f7"), HexColor("#ef4444"), HexColor("#06b6d4"),
        HexColor("#84cc16"), HexColor("#f97316")
    ]
    
    # Draw bars
    for i, (label, value) in enumerate(zip(labels, values)):
        y_pos = chart_height - top_margin - (i + 1) * bar_spacing
        
        # Calculate bar width
        bar_width = (value / max_value) * chart_width if max_value > 0 else 0
        
        # Draw bar
        bar_color = colors_list[i % len(colors_list)]
        bar = Rect(left_margin, y_pos, bar_width, bar_height)
        bar.fillColor = bar_color
        bar.strokeColor = HexColor("#ffffff")
        bar.strokeWidth = 1
        drawing.add(bar)
        
        # Draw label (left side)
        label_text = String(left_margin - 10, y_pos + bar_height/2 - 4, str(label))
        label_text.fontName = 'Helvetica'
        label_text.fontSize = 10
        label_text.fillColor = colors.black
        label_text.textAnchor = 'end'
        drawing.add(label_text)
        
        # Draw value (right side of bar)
        value_text = String(left_margin + bar_width + 5, y_pos + bar_height/2 - 4, str(value))
        value_text.fontName = 'Helvetica-Bold'
        value_text.fontSize = 10
        value_text.fillColor = colors.black
        drawing.add(value_text)
    
    # Draw title if provided
    if title:
        title_text = String(max_width/2, chart_height - 15, title)
        title_text.fontName = 'Helvetica-Bold'
        title_text.fontSize = 12
        title_text.fillColor = colors.black
        title_text.textAnchor = 'middle'
        drawing.add(title_text)
    
    return drawing


def generate_team_member_bar_chart(team_members_data: List[Dict[str, Any]]) -> Drawing:
    """Generate a bar chart showing task completion by team member."""
    from reportlab.graphics.shapes import Rect, String

    if not team_members_data:
        return generate_bar_chart({}, "Task Status by Team Member")

    # Prepare data for stacked bar chart
    member_names = []
    completed_data = []
    total_data = []
    
    for member in team_members_data:
        name = member.get('name', 'Unknown')
        completed = member.get('completed', 0)
        total = member.get('total_tasks', 0)
        
        member_names.append(name)
        completed_data.append(completed)
        total_data.append(total)
    
    # Create drawing
    drawing = Drawing(500, 300)
    
    if not member_names:
        text = String(250, 150, "No team member data available")
        text.fontName = 'Helvetica'
        text.fontSize = 12
        text.fillColor = colors.grey
        text.textAnchor = 'middle'
        drawing.add(text)
        return drawing
    
    # Calculate dimensions
    bar_width = 40
    bar_spacing = 60
    left_margin = 60
    bottom_margin = 60
    top_margin = 40
    
    max_value = max(total_data) if total_data else 1
    chart_height = 200
    
    # Draw bars for each member
    for i, (name, completed, total) in enumerate(zip(member_names, completed_data, total_data)):
        x_pos = left_margin + i * bar_spacing
        
        # Calculate heights
        total_height = (total / max_value) * chart_height if max_value > 0 else 0
        completed_height = (completed / max_value) * chart_height if max_value > 0 else 0
        
        # Draw total tasks bar (background)
        total_bar = Rect(x_pos, bottom_margin, bar_width, total_height)
        total_bar.fillColor = HexColor("#e5e7eb")
        total_bar.strokeColor = colors.white
        total_bar.strokeWidth = 1
        drawing.add(total_bar)
        
        # Draw completed tasks bar (foreground)
        completed_bar = Rect(x_pos, bottom_margin, bar_width, completed_height)
        completed_bar.fillColor = HexColor("#22c55e")
        completed_bar.strokeColor = colors.white
        completed_bar.strokeWidth = 1
        drawing.add(completed_bar)
        
        # Draw member name (rotated)
        name_text = String(x_pos + bar_width/2, bottom_margin - 10, name)
        name_text.fontName = 'Helvetica'
        name_text.fontSize = 8
        name_text.fillColor = colors.black
        name_text.textAnchor = 'middle'
        drawing.add(name_text)
        
        # Draw values above bar
        value_text = String(x_pos + bar_width/2, bottom_margin + total_height + 5, f"{completed}/{total}")
        value_text.fontName = 'Helvetica-Bold'
        value_text.fontSize = 9
        value_text.fillColor = colors.black
        value_text.textAnchor = 'middle'
        drawing.add(value_text)
    
    # Add title
    title_text = String(250, 280, "Task Status by Team Member")
    title_text.fontName = 'Helvetica-Bold'
    title_text.fontSize = 14
    title_text.fillColor = colors.black
    title_text.textAnchor = 'middle'
    drawing.add(title_text)
    
    # Add legend
    legend_y = 260
    
    # Completed legend
    completed_legend = Rect(left_margin, legend_y, 15, 10)
    completed_legend.fillColor = HexColor("#22c55e")
    completed_legend.strokeColor = colors.white
    drawing.add(completed_legend)
    
    completed_text = String(left_margin + 20, legend_y + 2, "Completed")
    completed_text.fontName = 'Helvetica'
    completed_text.fontSize = 10
    completed_text.fillColor = colors.black
    drawing.add(completed_text)
    
    # Total legend
    total_legend = Rect(left_margin + 100, legend_y, 15, 10)
    total_legend.fillColor = HexColor("#e5e7eb")
    total_legend.strokeColor = colors.white
    drawing.add(total_legend)
    
    total_text = String(left_margin + 120, legend_y + 2, "Total")
    total_text.fontName = 'Helvetica'
    total_text.fontSize = 10
    total_text.fillColor = colors.black
    drawing.add(total_text)
    
    return drawing


def _darken_color(color: colors.Color, factor: float = 0.82) -> colors.Color:
    """Return a slightly darker variant of a ReportLab color."""
    try:
        r = max(0.0, min(color.red * factor, 1.0))
        g = max(0.0, min(color.green * factor, 1.0))
        b = max(0.0, min(color.blue * factor, 1.0))
        return colors.Color(r, g, b)
    except Exception:
        return color


def build_preview_pie_chart(chart_title: str, data_dict: Dict[str, Any]) -> Optional[Drawing]:
    """Build a pie chart drawing from preview chart data."""
    from reportlab.graphics.shapes import Rect, String

    if not isinstance(data_dict, dict):
        return None

    numeric_items = [
        (str(label), float(value))
        for label, value in data_dict.items()
        if isinstance(value, (int, float)) and float(value) > 0
    ]

    if not numeric_items:
        return None

    labels, values = zip(*numeric_items)
    total = sum(values) or 1

    drawing = Drawing(440, 260)

    pie = Pie()
    pie.x = 120
    pie.y = 55
    pie.width = 180
    pie.height = 180
    pie.data = list(values)
    pie.labels = list(labels)
    pie.simpleLabels = 0
    pie.sideLabels = 0
    pie.slices.strokeWidth = 2
    pie.slices.strokeColor = colors.white

    palette = [
        HexColor("#3b82f6"), HexColor("#22c55e"), HexColor("#f59e0b"),
        HexColor("#a855f7"), HexColor("#ef4444"), HexColor("#06b6d4"),
        HexColor("#8b5cf6"), HexColor("#f97316")
    ]

    for index, (_, value) in enumerate(numeric_items):
        color = palette[index % len(palette)]
        pie.slices[index].fillColor = color
        pie.slices[index].strokeColor = _darken_color(color)

    drawing.add(pie)

    legend_x = 320
    legend_y = 220
    box_size = 12
    spacing = 22

    for idx, (label, value) in enumerate(numeric_items):
        y = legend_y - idx * spacing
        color = palette[idx % len(palette)]

        rect = Rect(legend_x, y - box_size / 2, box_size, box_size)
        rect.fillColor = color
        rect.strokeColor = colors.white
        rect.strokeWidth = 0.5
        drawing.add(rect)

        percentage = (value / total) * 100
        text = String(
            legend_x + box_size + 8,
            y - 3,
            f"{label}: {value:.1f} ({percentage:.1f}%)"
        )
        text.fontName = "Helvetica"
        text.fontSize = 10
        text.fillColor = HexColor("#1f2937")
        drawing.add(text)

    return drawing


def build_preview_vertical_bar_chart(chart_title: str, data_dict: Dict[str, Any]) -> Optional[Drawing]:
    """Build a vertical bar chart drawing from preview chart data."""
    from reportlab.graphics.shapes import Rect, String, Line

    if not isinstance(data_dict, dict):
        return None

    numeric_items = []
    for label, value in data_dict.items():
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        numeric_items.append((str(label), numeric_value))

    if not numeric_items:
        return None

    labels, raw_values = zip(*numeric_items)
    max_value = max(abs(v) for v in raw_values) or 1

    drawing_width = 480
    drawing_height = 300
    drawing = Drawing(drawing_width, drawing_height)

    left_margin = 60
    right_margin = 40
    bottom_margin = 60
    top_margin = 40

    available_width = drawing_width - left_margin - right_margin
    bar_count = len(labels)
    if bar_count == 0:
        return None

    min_bar_width = 24
    spacing_ratio = 0.5
    total_spacing = (bar_count - 1) * spacing_ratio
    bar_width = available_width / (bar_count + total_spacing)
    bar_width = min(40, max(min_bar_width, bar_width))

    spacing = bar_width * spacing_ratio
    chart_height = drawing_height - top_margin - bottom_margin

    axis = Line(left_margin, bottom_margin, left_margin, bottom_margin + chart_height)
    axis.strokeColor = HexColor("#cbd5f5")
    axis.strokeWidth = 1
    drawing.add(axis)

    baseline = Line(left_margin, bottom_margin, drawing_width - right_margin, bottom_margin)
    baseline.strokeColor = HexColor("#cbd5f5")
    baseline.strokeWidth = 1
    drawing.add(baseline)

    palette = [
        HexColor("#3b82f6"), HexColor("#22c55e"), HexColor("#f59e0b"),
        HexColor("#a855f7"), HexColor("#ef4444"), HexColor("#06b6d4"),
        HexColor("#8b5cf6"), HexColor("#f97316")
    ]

    current_x = left_margin
    for index, (label, value) in enumerate(numeric_items):
        bar_height = 0 if max_value == 0 else (abs(value) / max_value) * chart_height
        color = palette[index % len(palette)]

        bar = Rect(current_x, bottom_margin, bar_width, bar_height)
        bar.fillColor = color
        bar.strokeColor = HexColor("#ffffff")
        bar.strokeWidth = 0.8
        drawing.add(bar)

        value_text = String(
            current_x + bar_width / 2,
            bottom_margin + bar_height + 8,
            f"{value:.1f}" if abs(value) < 1000 else f"{value:,.0f}"
        )
        value_text.fontName = "Helvetica-Bold"
        value_text.fontSize = 10
        value_text.fillColor = HexColor("#1f2937")
        value_text.textAnchor = "middle"
        drawing.add(value_text)

        label_text = String(current_x + bar_width / 2, bottom_margin - 12, label)
        label_text.fontName = "Helvetica"
        label_text.fontSize = 9
        label_text.fillColor = HexColor("#1f2937")
        label_text.textAnchor = "middle"
        drawing.add(label_text)

        current_x += bar_width + spacing

    tick_count = min(4, int(max_value) if max_value > 1 else 1)
    for tick in range(1, tick_count + 1):
        fraction = tick / (tick_count + 1)
        y = bottom_margin + fraction * chart_height
        grid = Line(left_margin, y, drawing_width - right_margin, y)
        grid.strokeColor = HexColor("#e2e8f0")
        grid.strokeWidth = 0.5
        drawing.add(grid)

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

    # Summary section - keep together
    summary_section = []
    summary_heading = Paragraph("Summary", heading_style)
    summary_section.append(summary_heading)
    summary_section.append(Spacer(1, 8))

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
    summary_section.append(summary_table)
    summary_section.append(Spacer(1, 20))
    
    elements.append(KeepTogether(summary_section))

    # Add charts if there are tasks - keep charts together with headers
    if tasks:
        # First chart section
        chart1_section = []
        chart_heading = Paragraph("Task Status Distribution", heading_style)
        chart1_section.append(chart_heading)
        chart1_section.append(Spacer(1, 8))

        pie_chart = generate_pie_chart(tasks)
        chart1_section.append(pie_chart)
        chart1_section.append(Spacer(1, 16))
        
        elements.append(KeepTogether(chart1_section))
        
        # Second chart section - separate to allow page break between charts if needed
        chart2_section = []
        bar_chart_heading = Paragraph("Task Status Analysis", heading_style)
        chart2_section.append(bar_chart_heading)
        chart2_section.append(Spacer(1, 8))
        
        # Prepare data for bar chart
        status_counts = Counter(task.get('status') or 'Unknown' for task in tasks)
        bar_chart = generate_bar_chart(dict(status_counts), "Tasks by Status")
        chart2_section.append(bar_chart)
        chart2_section.append(Spacer(1, 24))
        
        elements.append(KeepTogether(chart2_section))

    # Task details table - add space for better flow
    elements.append(Spacer(1, 16))
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

    # Summary statistics with pie chart - keep together
    summary_section = []
    summary = report_data['summary']
    summary_heading = Paragraph("Project Performance Summary", heading_style)
    summary_section.append(summary_heading)
    summary_section.append(Spacer(1, 12))

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

    # Create pie chart with legend below
    pie_drawing = Drawing(240, 280)  # Increased height to accommodate legend below
    pie = Pie()
    pie.x = 50  # Centered horizontally
    pie.y = 130  # Moved up to make room for legend below
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

    # Add legend below the pie chart
    legend_x = 20  # Left aligned
    legend_start_y = 100  # Below the pie chart
    box_size = 10
    spacing = 20

    for i, (label, count) in enumerate(zip(pie_labels, pie_data)):
        y_pos = legend_start_y - (i * spacing)

        # Color box
        rect = Rect(legend_x, y_pos - box_size/2, box_size, box_size)
        rect.fillColor = pie_colors[i]
        rect.strokeColor = colors.whitesmoke
        rect.strokeWidth = 0.5
        pie_drawing.add(rect)

        # Label text
        text = String(legend_x + box_size + 5, y_pos - 3, f"{label}: {count}")
        text.fontSize = 9
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

    summary_section.append(summary_combined)
    summary_section.append(Spacer(1, 20))
    
    elements.append(KeepTogether(summary_section))

    # Team performance - keep together
    if report_data['team_performance']:
        team_section = []
        team_heading = Paragraph("Team Member Performance", heading_style)
        team_section.append(team_heading)
        team_section.append(Spacer(1, 8))

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
    task_breakdown_section.append(tasks_heading)
    task_breakdown_section.append(Spacer(1, 8))
    
    elements.append(KeepTogether(task_breakdown_section))

    # Iterate through task groups - each status group separately
    task_groups = report_data['task_groups']
    for status, tasks in task_groups.items():
        if not tasks:
            continue

        task_status_section = []
        # Status section header
        status_para = Paragraph(f"<b>{status}</b> ({len(tasks)} tasks)",
                               ParagraphStyle('StatusHeader', fontSize=12, textColor=HexColor('#1e293b'), spaceAfter=8))
        task_status_section.append(status_para)

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

        task_status_section.append(task_table)
        task_status_section.append(Spacer(1, 16))
        
        # Keep each status section together, but allow page breaks between different status sections
        elements.append(KeepTogether(task_status_section))    # Footer
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
    if not user_id or user_id == 'None':
        logger.warning(f"Invalid user_id provided: {user_id}")
        return None
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
        response = supabase.table('user').select('department').eq('is_active', True).execute()
        # Filter out empty, null, or None departments
        departments = list(set([
            user['department'] for user in response.data 
            if user.get('department') and user['department'].strip()
        ]))
        return sorted(departments)  # Return sorted list for consistency
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
    logger.info(f"User details: {requesting_user}")
    logger.info(f"Report data: {report_data}")
    
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

    # Handle case where user might not have a role set or has an unknown role
    elif not user_role:
        logger.warning("User has no role defined - checking if it's a basic individual report")
        # Allow individual reports if the user is requesting their own data
        if report_type == ReportType.INDIVIDUAL.value:
            target_user_id = report_data.get('user_id')
            if target_user_id == requesting_user.get('user_id'):
                logger.info("User with no role generating own individual report - access granted")
                return True
        logger.warning("User with no role cannot generate reports except their own individual report")
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

def generate_report_preview_data(requesting_user: Dict[str, Any], report_type: str, 
                               data: Dict[str, Any], start_date: Optional[str] = None,
                               end_date: Optional[str] = None, 
                               status_filter: Optional[List[str]] = None) -> Dict[str, Any]:
    """Generate preview data for reports with enhanced chart information."""
    
    user_role = requesting_user.get('role')
    requesting_user_id = requesting_user.get('user_id')
    
    preview_data = {
        'report_type': report_type,
        'user_role': user_role,
        'generated_by': requesting_user.get('name', 'Unknown'),
        'generated_at': datetime.now().isoformat(),
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'status_filter': status_filter
        },
        'charts': [],
        'summary': {},
        'detailed_data': {}
    }
    
    trend_granularity = data.get('trend_granularity', 'monthly')
    if trend_granularity not in {'daily', 'weekly', 'monthly'}:
        trend_granularity = 'monthly'
    preview_data['filters']['trend_granularity'] = trend_granularity

    if report_type == ReportType.INDIVIDUAL.value:
        # Individual report
        target_user_id = data.get('user_id', requesting_user_id)
        if not target_user_id:
            target_user_id = requesting_user_id
        target_user = get_user_details(target_user_id) if target_user_id != requesting_user_id else requesting_user
        
        tasks = fetch_tasks_for_user(target_user_id, start_date, end_date, status_filter)
        
        # Calculate individual metrics
        task_status_count = Counter([task.get('status') or 'Unknown' for task in tasks])
        raw_priority_count = Counter([task.get('priority') or 'Unknown' for task in tasks])

        # Normalise priority distribution on a 1–10 scale
        priority_distribution = {str(i): 0 for i in range(1, 11)}
        unspecified_priority = 0

        for priority_value, count in raw_priority_count.items():
            try:
                priority_int = int(priority_value)
            except (TypeError, ValueError):
                priority_int = None

            if priority_int is not None and 1 <= priority_int <= 10:
                priority_distribution[str(priority_int)] += count
            else:
                unspecified_priority += count

        completion_hours = [
            task.get('completion_time_hours') for task in tasks
            if task.get('completion_time_hours') is not None
        ]
        avg_completion_time_hours = (
            sum(completion_hours) / len(completion_hours)
            if completion_hours else 0
        )
        total_time_spent_hours = sum(completion_hours)
        
        # Convert to days
        avg_completion_time_days = avg_completion_time_hours / 24
        total_time_spent_days = total_time_spent_hours / 24

        preview_data['summary'] = {
            'target_user': target_user.get('name', 'Unknown') if target_user else 'Unknown',
            'total_tasks': len(tasks),
            'completed_tasks': task_status_count.get('Completed', 0),
            'in_progress_tasks': task_status_count.get('Ongoing', 0),  # Fixed: Ongoing status
            'pending_tasks': task_status_count.get('Under Review', 0),  # Fixed: Under Review status
            'overdue_tasks': len([t for t in tasks if is_task_overdue(t)]),
            'avg_completion_time_days': avg_completion_time_days,
            'total_time_spent_days': total_time_spent_days
        }
        
        # Charts for individual report
        preview_data['charts'] = [
            {
                'type': 'pie',
                'title': 'Task Status Distribution',
                'data': dict(task_status_count)
            },
            {
                'type': 'bar_vertical',
                'title': 'Task Priority Distribution (1 = Low, 10 = High)',
                'data': priority_distribution
            }
        ]
        
        preview_data['detailed_data']['tasks'] = tasks[:20]  # Up to 20 tasks for detailed report
        
    elif report_type == ReportType.TEAM.value:
        # Team report with member analysis
        tasks_by_scope: Dict[str, List[Dict[str, Any]]] = {}
        team_members_data: List[Dict[str, Any]] = []
        team_comparison_data: List[Dict[str, Any]] = []
        team_summaries: List[Dict[str, Any]] = []

        def append_member_snapshot(member_id: str, team_label: str):
            member_details = get_user_details(member_id)
            if not member_details:
                return

            member_tasks = fetch_tasks_for_user(member_id, start_date, end_date, status_filter)
            status_counts = Counter([task.get('status') or 'Unknown' for task in member_tasks])

            team_members_data.append({
                'user_id': member_id,
                'name': member_details.get('name', 'Unknown'),
                'team_name': team_label,
                'total_tasks': len(member_tasks),
                'completed': status_counts.get('Completed', 0),
                'in_progress': status_counts.get('In Progress', 0),
                'pending': status_counts.get('Pending', 0),
                'overdue': len([t for t in member_tasks if is_task_overdue(t)])
            })

        if user_role == UserRole.MANAGER.value:
            team_label = f"{requesting_user.get('name', 'Unknown')}'s Team"
            department = requesting_user.get('department')
            team_members = get_team_members(department, requesting_user_id) or []

            member_ids = {requesting_user_id}
            member_ids.update({member.get('user_id') for member in team_members if member.get('user_id')})
            member_ids.discard(None)

            team_tasks = fetch_tasks_for_multiple_users(list(member_ids), start_date, end_date, status_filter)
            tasks_by_scope[team_label] = team_tasks

            metrics = calculate_team_metrics(team_tasks)
            team_summaries.append({
                'team_id': requesting_user_id,
                'team_name': team_label,
                'department': department,
                'metrics': metrics
            })
            team_comparison_data.append({
                'team_name': team_label,
                'total_tasks': metrics['total_tasks'],
                'completed_tasks': metrics['completed_tasks'],
                'completion_rate': metrics['completion_rate'],
                'overdue_tasks': metrics['overdue_tasks'],
                'avg_completion_time_hours': metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0)),
                'avg_completion_time': metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0)),
                'time_spent_hours': metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0))
            })

            for member_id in member_ids:
                append_member_snapshot(member_id, team_label)

        elif user_role in (UserRole.DIRECTOR.value, UserRole.HR.value):
            selected_teams = data.get('teams', [])
            if isinstance(selected_teams, str):
                selected_teams = [selected_teams]

            if not selected_teams:
                raise ValueError("Team selection is required")

            for team_id in selected_teams:
                manager = get_user_details(team_id)
                if not manager or manager.get('role') != UserRole.MANAGER.value:
                    logger.info(f"Skipping team {team_id} - not a manager or not found")
                    continue

                if user_role == UserRole.DIRECTOR.value and manager.get('department') != requesting_user.get('department'):
                    logger.info(f"Director cannot access team {team_id} outside their department")
                    continue

                department = manager.get('department')
                team_label = f"{manager.get('name', 'Unknown')}'s Team"

                team_members = get_team_members(department, manager.get('user_id')) if department else []
                member_ids = {member.get('user_id') for member in team_members if member.get('user_id')}
                member_ids.add(manager.get('user_id'))
                member_ids.discard(None)

                if not member_ids:
                    logger.info(f"No members found for team {team_label}")
                    continue

                team_tasks = fetch_tasks_for_multiple_users(list(member_ids), start_date, end_date, status_filter)
                tasks_by_scope[team_label] = team_tasks

                metrics = calculate_team_metrics(team_tasks)
                team_summaries.append({
                    'team_id': manager.get('user_id'),
                    'team_name': team_label,
                    'department': department,
                    'metrics': metrics
                })
                team_comparison_data.append({
                    'team_name': team_label,
                    'total_tasks': metrics['total_tasks'],
                    'completed_tasks': metrics['completed_tasks'],
                    'completion_rate': metrics['completion_rate'],
                    'overdue_tasks': metrics['overdue_tasks'],
                    'avg_completion_time_hours': metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0)),
                    'avg_completion_time': metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0)),
                    'time_spent_hours': metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0))
                })

                for member_id in member_ids:
                    append_member_snapshot(member_id, team_label)
        else:
            raise ValueError("Unsupported role for team report")

        total_completed = sum(summary['metrics']['completed_tasks'] for summary in team_summaries)
        total_tasks = sum(len(tasks) for tasks in tasks_by_scope.values())
        avg_completion_rate = (
            sum(summary['metrics']['completion_rate'] for summary in team_summaries) / len(team_summaries)
            if team_summaries else 0
        )

        completion_time_values = [
            summary['metrics'].get('avg_completion_time_hours')
            for summary in team_summaries
            if summary['metrics'].get('avg_completion_time_hours') is not None
        ]
        avg_completion_time_hours = (
            sum(completion_time_values) / len(completion_time_values)
            if completion_time_values else 0
        )
        total_time_spent_hours = sum(
            summary['metrics'].get('total_time_spent_hours', summary['metrics'].get('total_time_spent', 0))
            for summary in team_summaries
        )
        
        # Convert to days
        avg_completion_time_days = avg_completion_time_hours / 24
        total_time_spent_days = total_time_spent_hours / 24

        preview_data['summary'] = {
            'team_name': team_summaries[0]['team_name'] if len(team_summaries) == 1 else f"{len(team_summaries)} teams selected",
            'selected_teams': [summary['team_name'] for summary in team_summaries],
            'total_teams': len(team_summaries),
            'total_members': len(team_members_data),
            'total_tasks': total_tasks,
            'total_completed': total_completed,
            'avg_completion_rate': avg_completion_rate,
            'avg_completion_time_days': avg_completion_time_days,
            'total_time_spent_days': total_time_spent_days
        }

        completion_by_team = {summary['team_name']: summary['metrics']['completed_tasks'] for summary in team_summaries}
        total_tasks_by_team = {summary['team_name']: summary['metrics']['total_tasks'] for summary in team_summaries}
        overdue_by_team = {summary['team_name']: summary['metrics']['overdue_tasks'] for summary in team_summaries}
        completion_rate_by_team = {
            summary['team_name']: round(summary['metrics']['completion_rate'], 2) for summary in team_summaries
        }

        pie_source = completion_by_team if sum(completion_by_team.values()) > 0 else total_tasks_by_team

        preview_data['charts'] = [
            {
                'type': 'pie',
                'title': 'Team Contribution (Completed Tasks)',
                'data': pie_source
            },
            {
                'type': 'bar_vertical',
                'title': 'Completion Rate by Team (%)',
                'data': completion_rate_by_team
            },
            {
                'type': 'bar_vertical',
                'title': 'Overdue Tasks by Team',
                'data': overdue_by_team
            }
        ]

        preview_data['detailed_data'] = {
            'team_members': team_members_data,
            'team_comparison': team_comparison_data,
            'tasks_by_scope': {scope: filter_high_priority_tasks(tasks, 8) for scope, tasks in tasks_by_scope.items()}  # Top 8 high priority tasks per team
        }
        
    elif report_type == ReportType.DEPARTMENT.value:
        # Department report with team comparisons
        if user_role == UserRole.DIRECTOR.value:
            department = requesting_user.get('department')
            teams = data.get('teams', [])
            
            team_comparison_data = []
            tasks_by_team = {}
            
            if teams:
                # Specific teams requested
                all_users = supabase.table('user').select('*').execute().data or []
                
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
                    
                    # Only include team lead if they are a manager (not director)
                    if team_lead_user and team_lead_user.get('user_id') and team_lead_user.get('role') == 'Manager':
                        unique_members[team_lead_user['user_id']] = team_lead_user
                    
                    user_ids = list(unique_members.keys())
                    
                    if user_ids:
                        team_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
                        tasks_by_team[team] = team_tasks
                        
                        metrics = calculate_team_metrics(team_tasks)
                        avg_completion_time_hours = metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0))
                        time_spent_hours = metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0))
                        
                        team_comparison_data.append({
                            'team_name': team,
                            'total_tasks': metrics['total_tasks'],
                            'completed_tasks': metrics['completed_tasks'],
                            'completion_rate': metrics['completion_rate'],
                            'overdue_tasks': metrics['overdue_tasks'],
                            'avg_completion_time_hours': avg_completion_time_hours,
                            'avg_completion_time_days': avg_completion_time_hours / 24,
                            'avg_completion_time': avg_completion_time_hours,
                            'time_spent_hours': time_spent_hours,
                            'time_spent_days': time_spent_hours / 24
                        })
            else:
                # All teams in department
                all_dept_members = get_team_members(department)
                teams_dict = {}
                
                # Filter out directors - they don't belong to teams, only managers have teams
                logger.info(f"🔍 Building teams for department: {department}")
                for member in all_dept_members:
                    # Skip directors - they manage departments, not teams
                    if member.get('role') == UserRole.DIRECTOR.value:
                        logger.info(f"🔍 Skipping director: {member.get('name', 'Unknown')} (role: {member.get('role')})")
                        continue
                        
                    superior = member.get('superior', 'No Team')
                    if superior not in teams_dict:
                        teams_dict[superior] = []
                    teams_dict[superior].append(member)
                    logger.info(f"🔍 Added member {member.get('name', 'Unknown')} to team under {superior}")
                
                logger.info(f"🔍 Processing {len(teams_dict)} teams in department {department}")
                for team_lead, members in teams_dict.items():
                    logger.info(f"🔍 Processing team led by: {team_lead}, members: {len(members)}")
                    unique_ids = {member['user_id'] for member in members if member.get('user_id')}
                    
                    if team_lead != 'No Team':
                        team_lead_user = get_user_details(team_lead)
                        logger.info(f"🔍 Team lead details - name: {team_lead_user.get('name') if team_lead_user else 'None'}, role: {team_lead_user.get('role') if team_lead_user else 'None'}")
                        # Only include team lead if they are a manager (not director) and in the same department
                        if (team_lead_user and 
                            team_lead_user.get('department') == department and 
                            team_lead_user.get('role') == UserRole.MANAGER.value):
                            unique_ids.add(team_lead_user['user_id'])
                            logger.info(f"🔍 Added manager {team_lead_user.get('name')} as team lead")
                        elif team_lead_user and team_lead_user.get('role') == UserRole.DIRECTOR.value:
                            logger.info(f"🔍 Skipping director {team_lead_user.get('name')} as team lead")
                    
                    user_ids = list(unique_ids)
                    
                    if user_ids:
                        team_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
                        team_lead_name = 'Unassigned'
                        
                        if team_lead != 'No Team':
                            team_lead_user = get_user_details(team_lead)
                            # Only show team name if team lead is a manager (not director)
                            if team_lead_user and team_lead_user.get('role') == UserRole.MANAGER.value:
                                team_lead_name = team_lead_user.get('name', team_lead)
                                logger.info(f"🔍 Setting team name to manager: {team_lead_name}")
                            else:
                                # Skip this team if the lead is a director
                                logger.info(f"🔍 Skipping team because lead is not a manager: {team_lead_user.get('role') if team_lead_user else 'Unknown'}")
                                continue
                        
                        tasks_by_team[team_lead_name] = team_tasks
                        
                        metrics = calculate_team_metrics(team_tasks)
                        avg_completion_time_hours = metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0))
                        time_spent_hours = metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0))
                        
                        team_comparison_data.append({
                            'team_name': team_lead_name,
                            'total_tasks': metrics['total_tasks'],
                            'completed_tasks': metrics['completed_tasks'],
                            'completion_rate': metrics['completion_rate'],
                            'overdue_tasks': metrics['overdue_tasks'],
                            'avg_completion_time_hours': avg_completion_time_hours,
                            'avg_completion_time_days': avg_completion_time_hours / 24,
                            'avg_completion_time': avg_completion_time_hours,
                            'time_spent_hours': time_spent_hours,
                            'time_spent_days': time_spent_hours / 24
                        })
            
            # Generate department charts
            completion_rates = {
                team['team_name']: round(team['completion_rate'], 2) for team in team_comparison_data
            }
            completed_workload = {
                team['team_name']: team['completed_tasks'] for team in team_comparison_data
            }
            overdue_work = {
                team['team_name']: team['overdue_tasks'] for team in team_comparison_data
            }
            total_tasks_map = {
                team['team_name']: team['total_tasks'] for team in team_comparison_data
            }

            # Calculate overall department analytics
            total_dept_tasks = sum(team['total_tasks'] for team in team_comparison_data)
            total_dept_completed = sum(team['completed_tasks'] for team in team_comparison_data)
            total_dept_overdue = sum(team['overdue_tasks'] for team in team_comparison_data)
            
            # Calculate time metrics in days
            total_time_days = sum(team['time_spent_days'] for team in team_comparison_data)
            
            avg_completion_time_days = (
                sum(team['avg_completion_time_days'] for team in team_comparison_data) / len(team_comparison_data)
                if team_comparison_data else 0
            )
            
            dept_completion_rate = (total_dept_completed / total_dept_tasks * 100) if total_dept_tasks > 0 else 0
            dept_overdue_rate = (total_dept_overdue / total_dept_tasks * 100) if total_dept_tasks > 0 else 0

            preview_data['summary'] = {
                'department': department,
                'scope_type': 'Department',
                'total_teams': len(team_comparison_data),
                'total_tasks': total_dept_tasks,
                'completed_tasks': total_dept_completed,
                'overdue_tasks': total_dept_overdue,
                'completion_rate': dept_completion_rate,
                'overdue_rate': dept_overdue_rate,
                'total_time_spent_days': total_time_days,
                'avg_completion_time_days': avg_completion_time_days,
                'avg_completion_rate': (
                    sum(team['completion_rate'] for team in team_comparison_data) / len(team_comparison_data)
                    if team_comparison_data else 0
                )
            }

            # Create additional analytics for department overview
            team_workload = {
                team['team_name']: round(team['time_spent_days'], 1) for team in team_comparison_data
            }
            
            team_efficiency = {
                team['team_name']: round(team['avg_completion_time_days'], 1) for team in team_comparison_data
            }

            # Collect all tasks from all teams for department-wide status distribution
            all_dept_tasks = []
            for team_tasks in tasks_by_team.values():
                all_dept_tasks.extend(team_tasks)
            
            # Create task status distribution for the entire department
            dept_status_counter = Counter([task.get('status') or 'Unknown' for task in all_dept_tasks])
            dept_status_distribution = dict(dept_status_counter)

            pie_source = completed_workload if sum(completed_workload.values()) > 0 else total_tasks_map

            preview_data['charts'] = [
                {
                    'type': 'pie',
                    'title': f'{department} Department - Task Status Distribution',
                    'data': dept_status_distribution
                },
                {
                    'type': 'pie',
                    'title': f'{department} Department - Task Distribution by Team',
                    'data': pie_source
                },
                {
                    'type': 'bar_vertical',
                    'title': 'Team Completion Rates (%)',
                    'data': completion_rates
                },
                {
                    'type': 'bar_vertical',
                    'title': 'Overdue Tasks by Team',
                    'data': overdue_work
                },
                {
                    'type': 'bar_vertical',
                    'title': 'Team Workload (days)',
                    'data': team_workload
                },
                {
                    'type': 'bar_vertical',
                    'title': 'Average Task Duration by Team (days)',
                    'data': team_efficiency
                }
            ]

            preview_data['detailed_data'] = {
                'team_comparison': team_comparison_data,
                'tasks_by_team': {team: filter_high_priority_tasks(tasks, 8) for team, tasks in tasks_by_team.items()}
            }
            
        elif user_role == UserRole.HR.value:
            # HR department report
            selected_departments = data.get('departments') or []
            if isinstance(selected_departments, str):
                selected_departments = [selected_departments]
                
            dept_comparison_data = []
            data_by_scope = {}
            
            for dept in selected_departments:
                dept_members = get_team_members(dept)
                member_ids = {member['user_id'] for member in dept_members if member.get('user_id')}
                
                if member_ids:
                    dept_tasks = fetch_tasks_for_multiple_users(list(member_ids), start_date, end_date, status_filter)
                    data_by_scope[dept] = dept_tasks
                    
                    metrics = calculate_team_metrics(dept_tasks)
                    dept_comparison_data.append({
                        'department': dept,
                        'total_tasks': metrics['total_tasks'],
                        'completed_tasks': metrics['completed_tasks'],
                        'completion_rate': metrics['completion_rate'],
                        'overdue_tasks': metrics['overdue_tasks'],
                        'total_time_spent_hours': metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0)),
                        'total_time_spent': metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0)),
                        'avg_completion_time_hours': metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0))
                    })
            
            # Generate HR department charts based on number of departments
            if len(selected_departments) > 1:
                # Multiple departments - pie chart shows proportion of completed tasks
                completed_tasks_by_dept = {dept['department']: dept['completed_tasks'] for dept in dept_comparison_data}
                
                # Comparison across departments
                completion_rates = {
                    dept['department']: round(dept['completion_rate'], 2) for dept in dept_comparison_data
                }
                overdue_percentages = {
                    dept['department']: (
                        round((dept['overdue_tasks'] / dept['total_tasks']) * 100, 2)
                        if dept['total_tasks'] > 0 else 0
                    ) for dept in dept_comparison_data
                }
                time_spent_by_dept = {
                    dept['department']: round(dept['total_time_spent'], 2) for dept in dept_comparison_data
                }
                avg_completion_time_hours_map = {
                    dept['department']: round(dept['avg_completion_time_hours'], 2) for dept in dept_comparison_data
                }
                
                preview_data['charts'] = [
                    {
                        'type': 'pie',
                        'title': 'Completed Tasks Distribution Across Departments',
                        'data': completed_tasks_by_dept
                    },
                    {
                        'type': 'bar_vertical',
                        'title': 'Department Completion Rates (%)',
                        'data': completion_rates
                    },
                    {
                        'type': 'bar_vertical', 
                        'title': 'Department Overdue Percentages (%)',
                        'data': overdue_percentages
                    },
                    {
                        'type': 'bar_vertical',
                        'title': 'Time Spent on Tasks by Department (hrs)',
                        'data': time_spent_by_dept
                    },
                    {
                        'type': 'bar_vertical',
                        'title': 'Average Completion Time by Department (hrs)',
                        'data': avg_completion_time_hours_map
                    }
                ]
            else:
                # Single department - compare teams within department
                single_dept = selected_departments[0] if selected_departments else 'Unknown'
                dept_tasks = data_by_scope.get(single_dept, [])
                
                # Get teams within the department for comparison
                all_users = supabase.table('user').select('*').eq('department', single_dept).execute().data or []
                teams_in_dept = {}
                
                for user in all_users:
                    superior_id = user.get('superior')
                    if superior_id:
                        superior_user = get_user_details(superior_id)
                        if superior_user and superior_user.get('role') == 'Manager':
                            team_name = f"{superior_user.get('name', 'Unknown')}'s Team"
                            if team_name not in teams_in_dept:
                                teams_in_dept[team_name] = []
                            teams_in_dept[team_name].append(user)
                
                # Calculate team metrics within the department
                team_metrics = []
                for team_name, members in teams_in_dept.items():
                    member_ids = [member['user_id'] for member in members if member.get('user_id')]
                    if member_ids:
                        team_tasks = fetch_tasks_for_multiple_users(member_ids, start_date, end_date, status_filter)
                        metrics = calculate_team_metrics(team_tasks)
                        team_metrics.append({
                            'team_name': team_name,
                            'completion_rate': metrics['completion_rate'],
                            'overdue_tasks': metrics['overdue_tasks'],
                            'avg_completion_time_hours': metrics.get('avg_completion_time_hours', 0),
                            'avg_completion_time': metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0)),
                            'time_spent_hours': metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0))
                        })
                
                preview_data['charts'] = [
                    {
                        'type': 'bar_vertical',
                        'title': f'Team Completion Rates in {single_dept} (%)',
                        'data': {team['team_name']: round(team['completion_rate'], 2) for team in team_metrics}
                    },
                    {
                        'type': 'bar_vertical',
                        'title': f'Team Overdue Tasks in {single_dept}',
                        'data': {team['team_name']: team['overdue_tasks'] for team in team_metrics}
                    },
                    {
                        'type': 'bar_vertical',
                        'title': f'Team Avg Completion Time in {single_dept} (hrs)',
                        'data': {team['team_name']: round(team['avg_completion_time_hours'], 2) for team in team_metrics}
                    },
                    {
                        'type': 'bar_vertical',
                        'title': f'Time Spent on Tasks in {single_dept} (hrs)',
                        'data': {team['team_name']: round(team.get('time_spent_hours', 0), 2) for team in team_metrics}
                    }
                ]
            
            preview_data['summary'] = {
                'scope': 'Multi-Department' if len(selected_departments) > 1 else f'Single Department ({selected_departments[0] if selected_departments else "Unknown"})',
                'total_departments': len(dept_comparison_data),
                'total_tasks': sum(dept['total_tasks'] for dept in dept_comparison_data),
                'avg_completion_rate': (
                    sum(dept['completion_rate'] for dept in dept_comparison_data) / len(dept_comparison_data)
                    if dept_comparison_data else 0
                ),
                'avg_completion_time_hours': (
                    sum(dept.get('avg_completion_time_hours', 0) for dept in dept_comparison_data) / len(dept_comparison_data)
                    if dept_comparison_data else 0
                ),
                'total_time_spent_hours': sum(dept.get('total_time_spent_hours', dept.get('total_time_spent', 0)) for dept in dept_comparison_data)
            }
            
            preview_data['detailed_data'] = {
                'department_comparison': dept_comparison_data
            }
    
    elif report_type == ReportType.ORGANIZATION.value and user_role == UserRole.HR.value:
        # HR organization-wide report - focused on high-level metrics with fixed scope
        departments = get_all_departments()

        dept_metrics: List[Dict[str, Any]] = []
        all_org_tasks: List[Dict[str, Any]] = []
        total_employees = 0
        total_time_logged_hours = 0.0
        total_completed_tasks = 0

        for dept in departments:
            dept_members = get_team_members(dept)
            user_ids = [member['user_id'] for member in dept_members if member.get('user_id')]

            if not user_ids:
                continue

            dept_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
            all_org_tasks.extend(dept_tasks)

            metrics = calculate_team_metrics(dept_tasks)

            time_logged_hours = sum(
                task.get('time_spent', 0) for task in dept_tasks
                if isinstance(task.get('time_spent', 0), (int, float))
            )
            if time_logged_hours == 0:
                time_logged_hours = metrics.get('total_time_spent', 0) * 24

            # Convert hours to days for organizational report
            time_logged_days = time_logged_hours / 24

            total_tasks_dept = metrics['total_tasks']
            completed_tasks = metrics['completed_tasks']
            overdue_percentage = (metrics['overdue_tasks'] / total_tasks_dept * 100) if total_tasks_dept > 0 else 0

            employee_count = len(user_ids)
            avg_tasks_per_employee = (total_tasks_dept / employee_count) if employee_count else 0
            avg_time_per_employee_days = (time_logged_days / employee_count) if employee_count else 0
            avg_time_per_task_days = (time_logged_days / total_tasks_dept) if total_tasks_dept else 0

            dept_metrics.append({
                'department': dept,
                'total_tasks': total_tasks_dept,
                'completed_tasks': completed_tasks,
                'completion_rate': metrics['completion_rate'],
                'overdue_percentage': overdue_percentage,
                'time_logged_days': time_logged_days,  # Changed to days
                'time_logged_hours': time_logged_hours,  # Keep hours for backward compatibility
                'employee_count': employee_count,
                'avg_tasks_per_employee': avg_tasks_per_employee,
                'avg_time_per_employee_days': avg_time_per_employee_days,  # Changed to days
                'avg_time_per_task_days': avg_time_per_task_days  # Changed to days
            })

            total_employees += employee_count
            total_time_logged_hours += time_logged_hours
            total_completed_tasks += completed_tasks

        def group_completed_tasks(tasks: List[Dict[str, Any]], granularity: str) -> Dict[str, int]:
            buckets: Dict[str, int] = {}
            for task in tasks:
                if task.get('status', '').lower() != 'completed':
                    continue

                timestamp = (
                    task.get('completed_at')
                    or task.get('completion_date')
                    or task.get('updated_at')
                )
                if not timestamp:
                    continue

                try:
                    completion_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except Exception:
                    continue

                if granularity == 'daily':
                    key = completion_dt.strftime('%Y-%m-%d')
                elif granularity == 'weekly':
                    year, week, _ = completion_dt.isocalendar()
                    key = f"{year}-W{week:02d}"
                else:
                    key = completion_dt.strftime('%Y-%m')

                buckets[key] = buckets.get(key, 0) + 1

            return dict(sorted(buckets.items()))

        trend_data = group_completed_tasks(all_org_tasks, trend_granularity)

        total_tasks = len(all_org_tasks)
        # Convert to days for organizational report
        total_time_logged_days = total_time_logged_hours / 24
        avg_time_per_employee_days = (
            total_time_logged_days / total_employees if total_employees else 0
        )
        avg_tasks_per_employee = (
            total_tasks / total_employees if total_employees else 0
        )
        avg_time_per_task_days = (
            total_time_logged_days / total_tasks if total_tasks else 0
        )

        granularity_title = {
            'daily': 'Day',
            'weekly': 'Week',
            'monthly': 'Month'
        }.get(trend_granularity, 'Month')

        completed_tasks_by_department = {
            metric['department']: metric['completed_tasks'] for metric in dept_metrics
        }
        completion_rate_by_department = {
            metric['department']: round(metric['completion_rate'], 2) for metric in dept_metrics
        }
        overdue_percentage_by_department = {
            metric['department']: round(metric['overdue_percentage'], 2) for metric in dept_metrics
        }
        time_logged_by_department = {
            metric['department']: round(metric['time_logged_days'], 2) for metric in dept_metrics
        }
        workload_per_employee_by_department = {
            metric['department']: round(metric['avg_time_per_employee_days'], 2) for metric in dept_metrics
        }
        time_per_task_by_department = {
            metric['department']: round(metric['avg_time_per_task_days'], 2) for metric in dept_metrics
        }

        pie_source = completed_tasks_by_department or {metric['department']: metric['total_tasks'] for metric in dept_metrics}
        if not pie_source:
            pie_source = {'No Data': 1}

        preview_data['summary'] = {
            'scope_type': 'Organization',
            'total_departments': len(departments),
            'total_employees': total_employees,
            'total_tasks': total_tasks,
            'total_completed_tasks': total_completed_tasks,
            'completed_tasks': total_completed_tasks,
            'total_time_logged_days': total_time_logged_days,
            'trend_granularity': trend_granularity,
            'avg_time_per_employee_days': avg_time_per_employee_days,
            'avg_tasks_per_employee': avg_tasks_per_employee,
            'avg_time_per_task_days': avg_time_per_task_days,
            'avg_completion_rate': (
                sum(metric['completion_rate'] for metric in dept_metrics) / len(dept_metrics)
                if dept_metrics else 0
            )
        }

        preview_data['charts'] = [
            {
                'type': 'pie',
                'title': 'Completed Tasks by Department',
                'data': pie_source
            },
            {
                'type': 'bar_vertical',
                'title': 'Department Completion Rate (%)',
                'data': completion_rate_by_department
            },
            {
                'type': 'bar_vertical',
                'title': 'Department Overdue Percentage (%)',
                'data': overdue_percentage_by_department
            },
            {
                'type': 'bar_vertical',
                'title': 'Time Logged by Department (days)',
                'data': time_logged_by_department
            },
            {
                'type': 'bar_vertical',
                'title': f'Tasks Completed per {granularity_title}',
                'data': trend_data
            },
            {
                'type': 'bar_vertical',
                'title': 'Average Workload per Employee (days)',
                'data': workload_per_employee_by_department
            },
            {
                'type': 'bar_vertical',
                'title': 'Average Time per Task by Department (days)',
                'data': time_per_task_by_department
            }
        ]

        preview_data['detailed_data'] = {
            'department_metrics': dept_metrics,
            'trend': trend_data,
            'workload_analysis': {
                'total_employees': total_employees,
                'avg_time_per_employee_days': avg_time_per_employee_days,
                'avg_tasks_per_employee': avg_tasks_per_employee,
                'avg_time_per_task_days': avg_time_per_task_days
            }
        }
    
    return preview_data

def generate_preview_pdf(preview_data: Dict[str, Any], requesting_user: Dict[str, Any]) -> io.BytesIO:
    """Build a report PDF that mirrors the preview payload."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    styles = getSampleStyleSheet()
    elements: List[Any] = []

    report_labels = {
        ReportType.INDIVIDUAL.value: 'Individual',
        ReportType.TEAM.value: 'Team',
        ReportType.DEPARTMENT.value: 'Department',
        ReportType.ORGANIZATION.value: 'Organization'
    }
    report_type = preview_data.get('report_type', 'report')
    report_label = report_labels.get(report_type, 'Report')
    title = preview_data.get('report_title') or f"{report_label} Report"

    elements.extend(build_report_header(title, styles))
    elements.append(Spacer(1, 12))

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#1e40af'),
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    subheading_style = ParagraphStyle(
        'Subheading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=HexColor('#1f2937'),
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    metadata_key_style = ParagraphStyle(
        'MetadataKey',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#475569'),
        fontName='Helvetica-Bold',
        leading=12
    )
    metadata_value_style = ParagraphStyle(
        'MetadataValue',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#0f172a'),
        leading=12
    )

    def format_datetime_display(value: Optional[str]) -> str:
        dt = parse_datetime(value)
        if not dt:
            return 'N/A'
        return dt.astimezone(timezone.utc).strftime('%d %b %Y %H:%M %Z')

    def format_cell_value(value: Any) -> str:
        if value is None:
            return '-'
        if isinstance(value, (int, float)):
            if abs(value) >= 100:
                return f"{value:.0f}"
            if abs(value) >= 10:
                return f"{value:.1f}"
            return f"{value:.2f}"
        if isinstance(value, list):
            return ', '.join(str(item) for item in value)
        if isinstance(value, dict):
            return json.dumps(value, default=str)
        return str(value)

    def humanize_key(key: str) -> str:
        return key.replace('_', ' ').title()

    filters = preview_data.get('filters', {}) or {}
    summary = preview_data.get('summary', {}) or {}

    metadata_rows = [
        ('Report Type', escape(report_label)),
        ('Generated By', escape(preview_data.get('generated_by', requesting_user.get('name', 'Unknown')))),
        ('User Role', escape(preview_data.get('user_role', requesting_user.get('role', 'Unknown')))),
        ('Generated At', escape(format_datetime_display(preview_data.get('generated_at'))))
    ]

    target_text = None
    if summary.get('selected_teams'):
        target_text = ', '.join(summary['selected_teams'])
    target_text = target_text or summary.get('target_user') or summary.get('team_name') or summary.get('department') or summary.get('scope')
    if target_text:
        metadata_rows.append(('Target', escape(target_text)))

    trend = summary.get('trend_granularity') or filters.get('trend_granularity')
    if trend:
        metadata_rows.append(('Trend Interval', escape(str(trend).title())))

    filter_parts: List[str] = []
    if filters.get('start_date') and filters.get('end_date'):
        filter_parts.append(escape(f"{filters['start_date']} to {filters['end_date']}"))
    elif filters.get('start_date'):
        filter_parts.append(escape(f"From {filters['start_date']}"))
    elif filters.get('end_date'):
        filter_parts.append(escape(f"Until {filters['end_date']}"))

    status_filter = filters.get('status_filter') or []
    if status_filter and 'All' not in status_filter:
        filter_parts.append(escape(f"Status: {', '.join(status_filter)}"))

    if filter_parts:
        filters_text = '<br/>'.join(filter_parts)
        metadata_rows.append(('Applied Filters', filters_text))
    formatted_metadata_rows = [
        [
            Paragraph(str(label), metadata_key_style),
            Paragraph(value if isinstance(value, str) else str(value), metadata_value_style)
        ]
        for label, value in metadata_rows
    ]

    metadata_table = Table(formatted_metadata_rows, colWidths=[1.9 * inch, 3.6 * inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#475569')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#0f172a')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK')
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 18))

    summary_fields = [
        ('total_tasks', 'Total Tasks', lambda v: f"{int(v)}"),
        ('completed_tasks', 'Completed Tasks', lambda v: f"{int(v)}"),
        ('in_progress_tasks', 'In Progress Tasks', lambda v: f"{int(v)}"),
        ('pending_tasks', 'Pending Tasks', lambda v: f"{int(v)}"),
        ('overdue_tasks', 'Overdue Tasks', lambda v: f"{int(v)}"),
        ('total_members', 'Team Members', lambda v: f"{int(v)}"),
        ('total_teams', 'Total Teams', lambda v: f"{int(v)}"),
        ('total_departments', 'Total Departments', lambda v: f"{int(v)}"),
        ('total_completed_tasks', 'Completed Tasks', lambda v: f"{int(v)}"),  # Added after Total Departments
        ('total_employees', 'Total Employees', lambda v: f"{int(v)}"),
        ('total_completed', 'Total Completed Tasks', lambda v: f"{int(v)}"),
        ('avg_completion_rate', 'Avg Completion Rate (%)', lambda v: f"{round(v, 1)}%"),
        ('avg_completion_time_days', 'Avg Completion Time (days)', lambda v: f"{v:.1f} days" if v else "0 days"),
        ('total_time_spent_days', 'Total Time Spent (days)', lambda v: f"{v:.1f} days"),
        ('avg_time_per_employee_days', 'Avg Days per Employee', lambda v: f"{v:.1f} days"),
        ('avg_tasks_per_employee', 'Avg Tasks per Employee', lambda v: f"{v:.1f}"),
        ('avg_time_per_task_days', 'Avg Days per Task', lambda v: f"{v:.1f} days"),
        ('trend_granularity', 'Trend Interval', lambda v: str(v).title())
    ]

    summary_rows: List[List[str]] = []
    seen_keys = set()
    for key, label, formatter in summary_fields:
        if key in seen_keys:
            continue
        if key not in summary:
            continue
        value = summary.get(key)
        if value is None:
            continue
        if isinstance(value, list) and not value:
            continue
        seen_keys.add(key)
        try:
            display = formatter(value) if callable(formatter) else format_cell_value(value)
        except Exception:
            display = format_cell_value(value)
        summary_rows.append([label, display])

    if summary_rows:
        elements.append(Paragraph('Summary', section_heading))
        elements.append(Spacer(1, 8))
        summary_table = Table(summary_rows, colWidths=[2.8 * inch, 2.7 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#111827')),
            ('LINEBEFORE', (1, 0), (1, -1), 0.3, HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 18))

    charts = preview_data.get('charts') or []
    chart_blocks_on_page = 0
    analytics_started = False

    def build_chart_drawing(chart: Dict[str, Any]) -> Optional[Drawing]:
        chart_type = str(chart.get('type', '')).lower()
        data = chart.get('data')

        if chart_type == 'pie' and isinstance(data, dict):
            return build_preview_pie_chart(chart.get('title', ''), data)
        if chart_type in {'bar_vertical', 'bar'} and isinstance(data, dict):
            return build_preview_vertical_bar_chart(chart.get('title', ''), data)
        return None

    def build_chart_rows(chart: Dict[str, Any]) -> List[List[str]]:
        data = chart.get('data')
        if isinstance(data, dict):
            if all(isinstance(v, (int, float, type(None))) for v in data.values()):
                rows = [['Label', 'Value']]
                for key, value in data.items():
                    rows.append([str(key), format_cell_value(value)])
                return rows
            if all(isinstance(v, list) for v in data.values()):
                keys = list(data.keys())
                primary = keys[0]
                columns = [humanize_key(primary)] + [humanize_key(k) for k in keys[1:]]
                rows = [columns]
                max_len = max(len(data[k]) for k in keys)
                for idx in range(max_len):
                    row = []
                    for key in keys:
                        series = data[key]
                        value = series[idx] if idx < len(series) else None
                        row.append(format_cell_value(value))
                    rows.append(row)
                return rows
        elif isinstance(data, list):
            rows = [['Index', 'Value']]
            for idx, value in enumerate(data, start=1):
                rows.append([str(idx), format_cell_value(value)])
            return rows
        return [['Details'], [format_cell_value(data)]]

    if charts:
        # Only add analytics section if there are charts
        elements.append(Spacer(1, 20))  # Space instead of page break
        elements.append(Paragraph('Analytics', section_heading))
        elements.append(Spacer(1, 12))
        analytics_started = True
        chart_blocks_on_page = 0

    for chart_index, chart in enumerate(charts):
        chart_section = []
        chart_title = chart.get('title') or 'Chart'
        chart_section.append(Paragraph(chart_title, subheading_style))
        chart_section.append(Spacer(1, 4))
        
        drawing = build_chart_drawing(chart)
        if drawing:
            chart_section.append(drawing)
        else:
            table_rows = build_chart_rows(chart)
            chart_table = Table(table_rows, repeatRows=1)
            chart_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            chart_section.append(chart_table)
        
        chart_section.append(Spacer(1, 12))
        
        # Keep each chart with its title together
        elements.append(KeepTogether(chart_section))
        
        chart_blocks_on_page += 1
        # Only add page break if we have 2 charts on page AND there are more charts coming
        if chart_blocks_on_page >= 2 and chart_index < len(charts) - 1:
            elements.append(PageBreak())
            elements.append(Paragraph('Analytics (cont.)', section_heading))
            elements.append(Spacer(1, 8))
            chart_blocks_on_page = 0

    detailed_data = preview_data.get('detailed_data') or {}

    def add_records_table(title: str, records: List[Dict[str, Any]], column_labels: Optional[Dict[str, str]] = None, limit: Optional[int] = None, col_widths: Optional[List[float]] = None):
        if not records:
            return
        if column_labels:
            keys = list(column_labels.keys())
        else:
            keys = list(records[0].keys())
        header = [column_labels.get(key, humanize_key(key)) if column_labels else humanize_key(key) for key in keys]
        rows = [header]
        sample = records if limit is None else records[:limit]
        for record in sample:
            row = []
            for key in keys:
                value = record.get(key)
                if key.endswith('_rate') or key.endswith('_percentage'):
                    if isinstance(value, (int, float)):
                        row.append(f"{round(value, 1)}%")
                    else:
                        row.append(format_cell_value(value))
                elif key.endswith('_hours'):
                    if isinstance(value, (int, float)):
                        row.append(f"{value:.1f} h")
                    else:
                        row.append(format_cell_value(value))
                else:
                    row.append(format_cell_value(value))
            rows.append(row)
            
        # Keep table with its title together
        table_section = []
        table_section.append(Paragraph(title, subheading_style))
        table_section.append(Spacer(1, 4))
        
        table = Table(rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        table_section.append(table)
        table_section.append(Spacer(1, 14))
        
        elements.append(KeepTogether(table_section))

    if detailed_data.get('team_members'):
        column_map = {
            'name': 'Name',
            'team_name': 'Team',
            'total_tasks': 'Total Tasks',
            'completed': 'Completed',
            'in_progress': 'In Progress',
            'pending': 'Pending',
            'overdue': 'Overdue'
        }
        add_records_table('Team Members', detailed_data['team_members'], column_map)

    if detailed_data.get('team_comparison'):
        column_map = {
            'team_name': 'Team',
            'total_tasks': 'Total Tasks',
            'completed_tasks': 'Completed',
            'completion_rate': 'Completion Rate (%)',
            'overdue_tasks': 'Overdue',
            'avg_completion_time_hours': 'Avg Completion (hrs)',
            'time_spent_hours': 'Time Spent (hrs)'
        }
        add_records_table('Team Comparison', detailed_data['team_comparison'], column_map)

    if detailed_data.get('department_comparison'):
        column_map = {
            'department': 'Department',
            'total_tasks': 'Total Tasks',
            'completed_tasks': 'Completed',
            'completion_rate': 'Completion Rate (%)',
            'overdue_tasks': 'Overdue',
            'overdue_percentage': 'Overdue (%)',
            'total_time_spent': 'Time Spent (hrs)'
        }
        add_records_table('Department Comparison', detailed_data['department_comparison'], column_map)

    if detailed_data.get('department_metrics'):
        # Department Metrics - properly transposed format for print compatibility
        dept_section = []
        dept_section.append(Paragraph("Department Metrics", subheading_style))
        dept_section.append(Spacer(1, 4))

        dept_metrics = detailed_data['department_metrics']
        
        if dept_metrics:
            # Create transposed table with metrics as rows and departments as columns
            departments = [dept['department'] for dept in dept_metrics]
            
            # Create table data with metrics as rows (left column)
            table_data = []
            
            # Header row: Metric name, then department names
            header_row = ['Metric'] + departments
            table_data.append(header_row)
            
            # Data rows - each metric becomes a row
            metrics_to_show = [
                ('completion_rate', 'Completion Rate (%)'),
                ('overdue_percentage', 'Overdue (%)'),
                ('time_logged_days', 'Time Logged (days)'),
                ('employee_count', 'Employees'),
                ('avg_tasks_per_employee', 'Avg Tasks/Employee'),
                ('avg_time_per_employee_days', 'Avg Days/Employee'),
                ('avg_time_per_task_days', 'Avg Days/Task')
            ]
            
            for metric_key, metric_label in metrics_to_show:
                row = [metric_label]  # Start with metric name
                for dept in dept_metrics:
                    value = dept.get(metric_key, 0)
                    # Format values appropriately
                    if metric_key in ['completion_rate', 'overdue_percentage']:
                        row.append(f"{value:.1f}%" if isinstance(value, (int, float)) else str(value))
                    elif metric_key in ['time_logged_days', 'avg_time_per_employee_days', 'avg_time_per_task_days']:
                        row.append(f"{value:.1f} h" if isinstance(value, (int, float)) else str(value))
                    elif metric_key in ['avg_tasks_per_employee']:
                        row.append(f"{value:.2f}" if isinstance(value, (int, float)) else str(value))
                    else:
                        row.append(str(value))
                table_data.append(row)
            
            # Calculate column widths for transposed table - make more compact
            num_cols = len(header_row)
            if num_cols <= 4:
                col_width = 1.2 * inch
            elif num_cols <= 6:
                col_width = 0.9 * inch
            else:
                col_width = 0.7 * inch
            
            col_widths = [1.4 * inch] + [col_width] * (num_cols - 1)
            
            dept_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            dept_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f1f5f9')),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            dept_section.append(dept_table)
        else:
            dept_section.append(Paragraph("No department metrics available", styles['Normal']))
        
        dept_section.append(Spacer(1, 6))
        elements.append(KeepTogether(dept_section))

    if detailed_data.get('scope_comparison'):
        add_records_table('Scope Comparison', detailed_data['scope_comparison'])

    tasks_sample = detailed_data.get('tasks')
    if tasks_sample:
        column_map = {
            'title': 'Task',
            'status': 'Status',
            'priority': 'Priority',
            'due_date': 'Due Date',
            'completed_date': 'Completed Date',
            'completion_time_hours': 'Completion (hrs)'
        }
        add_records_table('Task Details', tasks_sample, column_map, limit=20)

    tasks_by_scope = detailed_data.get('tasks_by_scope') or {}
    for scope_name, scope_tasks in tasks_by_scope.items():
        column_map = {
            'title': 'Task',
            'status': 'Status',
            'priority': 'Priority',
            'due_date': 'Due Date',
            'completed_date': 'Completed Date',
            'completion_time_hours': 'Completion (hrs)'
        }
        add_records_table(f"{scope_name} Tasks", scope_tasks, column_map, limit=20)

    workload_analysis = detailed_data.get('workload_analysis')
    if isinstance(workload_analysis, dict) and workload_analysis:
        rows = []
        for key, value in workload_analysis.items():
            label = humanize_key(key)
            if 'hours' in key and isinstance(value, (int, float)):
                display = f"{value:.1f} h"
            else:
                display = format_cell_value(value)
            rows.append([label, display])
        if rows:
            elements.append(Paragraph('Workload Analysis', subheading_style))
            elements.append(Spacer(1, 4))
            analysis_table = Table(rows, colWidths=[2.8 * inch, 2.7 * inch])
            analysis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#1f2937')),
                ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#111827')),
                ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(analysis_table)
            elements.append(Spacer(1, 14))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def is_task_overdue(task: Dict[str, Any]) -> bool:
    """Check if a task is overdue."""
    try:
        due_date_str = task.get('due_date')
        if not due_date_str:
            return False
            
        # Parse due date
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        current_date = datetime.now(timezone.utc)
        
        # Task is overdue if due date has passed and status is not completed
        status = task.get('status', '').lower()
        return due_date < current_date and status != 'completed'
    except Exception:
        return False

def get_options_for_report_type(requesting_user: Dict[str, Any], report_type: str):
    """Get specific options based on report type."""
    try:
        role = requesting_user.get('role')
        department = requesting_user.get('department')
        user_id = requesting_user.get('user_id')
        
        options = []
        
        if report_type == 'individual':
            # Get users that this role can generate reports for
            if role == UserRole.MANAGER.value:
                # Manager can report on their team members + themselves
                team_members = get_team_members(department, user_id) or []
                # Add self
                options.append({
                    'value': user_id,
                    'label': f"{requesting_user.get('name', 'Unknown')} (You)"
                })
                # Add team members
                for member in team_members:
                    if member.get('user_id') != user_id:  # Don't duplicate self
                        options.append({
                            'value': member.get('user_id'),
                            'label': member.get('name', 'Unknown User')
                        })
                        
            elif role == UserRole.DIRECTOR.value:
                # Director can report on anyone in their department
                dept_users_response = supabase.table('user').select('user_id, name, email').eq('department', department).eq('is_active', True).execute()
                dept_users = dept_users_response.data or []
                
                for user in dept_users:
                    label = user.get('name', 'Unknown User')
                    if user.get('user_id') == user_id:
                        label += " (You)"
                    options.append({
                        'value': user.get('user_id'),
                        'label': label
                    })
                    
            elif role == UserRole.HR.value:
                # HR can report on anyone
                all_users_response = supabase.table('user').select('user_id, name, email, department').eq('is_active', True).execute()
                all_users = all_users_response.data or []
                
                for user in all_users:
                    label = f"{user.get('name', 'Unknown User')}"
                    if user.get('department'):
                        label += f" ({user.get('department')})"
                    if user.get('user_id') == user_id:
                        label += " (You)"
                    options.append({
                        'value': user.get('user_id'),
                        'label': label
                    })
                    
        elif report_type == 'team':
            # Get teams that this role can generate reports for
            if role == UserRole.DIRECTOR.value:
                # Director can report on manager teams in their department
                dept_users_response = supabase.table('user').select('*').eq('department', department).eq('is_active', True).execute()
                dept_users = dept_users_response.data or []
                
                # Find managers in the department who have team members
                managers_with_teams = []
                for user in dept_users:
                    superior_id = user.get('superior')
                    if superior_id:  # This user has a superior
                        superior_user = get_user_details(superior_id)
                        if (superior_user and 
                            superior_user.get('role') == 'Manager' and 
                            superior_user.get('department') == department):
                            managers_with_teams.append(superior_user)
                
                # Remove duplicates and create options
                seen_managers = set()
                for manager in managers_with_teams:
                    manager_id = manager.get('user_id')
                    if manager_id and manager_id not in seen_managers:
                        seen_managers.add(manager_id)
                        options.append({
                            'value': manager_id,
                            'label': f"{manager.get('name', 'Unknown')}'s Team"
                        })
                        
            elif role == UserRole.HR.value:
                # HR can report on any manager's team (managers have teams, not directors)
                all_users_response = supabase.table('user').select('*').eq('is_active', True).execute()
                all_users = all_users_response.data or []
                
                # Get all users who have subordinates (are superiors) and are managers
                managers_with_teams = []
                for user in all_users:
                    superior_id = user.get('superior')
                    if superior_id:  # This user has a superior, so their superior might be a manager with a team
                        superior_user = get_user_details(superior_id)
                        if superior_user and superior_user.get('role') == 'Manager':
                            managers_with_teams.append(superior_user)
                
                # Remove duplicates and create options
                seen_managers = set()
                for manager in managers_with_teams:
                    manager_id = manager.get('user_id')
                    if manager_id and manager_id not in seen_managers:
                        seen_managers.add(manager_id)
                        options.append({
                            'value': manager_id,
                            'label': f"{manager.get('name', 'Unknown')}'s Team ({manager.get('department', 'Unknown Dept')})"
                        })
                        
        elif report_type == 'department':
            # Only HR can generate department reports
            if role == UserRole.HR.value:
                departments = get_all_departments()
                for dept in departments:
                    options.append({
                        'value': dept,
                        'label': dept
                    })
        
        return jsonify({'options': options}), 200
        
    except Exception as e:
        logger.error(f"Error getting options for report type {report_type}: {e}")
        return jsonify({"error": "Failed to get report options"}), 500


def get_options_for_scope_type(requesting_user: Dict[str, Any], scope_type: str):
    """Get options for HR organization report scope types."""
    try:
        role = requesting_user.get('role')
        
        # Only HR can access organization reports
        if role != UserRole.HR.value:
            return jsonify({"error": "Unauthorized"}), 403
            
        options = []
        
        if scope_type == 'departments':
            departments = get_all_departments()
            for dept in departments:
                options.append({
                    'value': dept,
                    'label': dept
                })
                
        elif scope_type == 'teams':
            # Get all teams (only managers with subordinates, not directors)
            all_users_response = supabase.table('user').select('*').execute()
            all_users = all_users_response.data or []
            superiors = list(set([user.get('superior') for user in all_users if user.get('superior')]))
            
            for superior_id in superiors:
                superior_user = get_user_details(superior_id)
                if superior_user and superior_user.get('role') == UserRole.MANAGER.value:
                    # Only include managers as team leads (directors manage departments, not teams)
                    options.append({
                        'value': superior_id,
                        'label': f"{superior_user.get('name', 'Unknown')}'s Team ({superior_user.get('department', 'Unknown Dept')})"
                    })
                    
        elif scope_type == 'individuals':
            # Get all users
            all_users_response = supabase.table('user').select('user_id, name, email, department').eq('is_active', True).execute()
            all_users = all_users_response.data or []
            
            for user in all_users:
                label = f"{user.get('name', 'Unknown User')}"
                if user.get('department'):
                    label += f" ({user.get('department')})"
                options.append({
                    'value': user.get('user_id'),
                    'label': label
                })
        
        return jsonify({'options': options}), 200
        
    except Exception as e:
        logger.error(f"Error getting options for scope type {scope_type}: {e}")
        return jsonify({"error": "Failed to get scope options"}), 500


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
            'total_time_spent_hours': 0,
            'avg_completion_time': 0,
            'avg_completion_time_hours': 0,
            'avg_active_time_hours': 0
        }
    
    completed_tasks = [t for t in tasks if t.get('status', '').lower() == 'completed']
    overdue_tasks = []
    total_time_spent_hours = 0.0
    completion_times_hours: List[float] = []
    active_times_hours: List[float] = []
    
    current_date = datetime.now(timezone.utc)
    
    for task in tasks:
        # Check for overdue tasks
        due_date = task.get('due_date')
        if due_date and task.get('status', '').lower() != 'completed':
            due_dt = parse_datetime(due_date)
            if due_dt and due_dt < current_date:
                overdue_tasks.append(task)
        
        completion_hours = task.get('completion_time_hours')
        if completion_hours is not None:
            total_time_spent_hours += max(completion_hours, 0)
            completion_times_hours.append(max(completion_hours, 0))
        else:
            in_progress = task.get('time_in_progress_hours')
            if in_progress is not None:
                active_times_hours.append(max(in_progress, 0))
    
    completion_rate = (len(completed_tasks) / total_tasks) * 100
    overdue_percentage = (len(overdue_tasks) / total_tasks) * 100
    avg_completion_time_hours = sum(completion_times_hours) / len(completion_times_hours) if completion_times_hours else 0
    avg_active_time_hours = sum(active_times_hours) / len(active_times_hours) if active_times_hours else 0
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': len(completed_tasks),
        'completion_rate': completion_rate,
        'overdue_tasks': len(overdue_tasks),
        'overdue_percentage': overdue_percentage,
        'total_time_spent': total_time_spent_hours,
        'total_time_spent_hours': total_time_spent_hours,
        'avg_completion_time': avg_completion_time_hours,
        'avg_completion_time_hours': avg_completion_time_hours,
        'avg_active_time_hours': avg_active_time_hours
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

    # Performance comparison section - keep together
    comparison_section = []
    comparison_section.append(Paragraph("Performance Comparison", heading_style))
    comparison_section.append(Spacer(1, 15))

    comparison_data: List[List[str]] = [
        ['Scope', 'Total Tasks', 'Completed', 'Completion Rate', 'Overdue %', 'Avg. Duration (days)', 'Total Time (days)']
    ]

    for scope_name, scope_tasks in tasks_by_scope.items():
        metrics = calculate_team_metrics(scope_tasks)
        # Convert hours to days for display
        avg_duration_hours = metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0))
        total_time_hours = metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0))
        avg_duration_days = avg_duration_hours / 24
        total_time_days = total_time_hours / 24
        
        comparison_data.append([
            scope_name,
            str(metrics['total_tasks']),
            str(metrics['completed_tasks']),
            f"{metrics['completion_rate']:.1f}%",
            f"{metrics['overdue_percentage']:.1f}%",
            f"{avg_duration_days:.1f}",
            f"{total_time_days:.1f}"
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

    comparison_section.append(comparison_table)
    comparison_section.append(Spacer(1, 20))
    
    elements.append(KeepTogether(comparison_section))
    
    # Add comparison bar chart - separate section
    chart_section = []
    chart_heading = Paragraph("Performance Comparison Chart", heading_style)
    chart_section.append(chart_heading)
    chart_section.append(Spacer(1, 8))
    
    # Prepare data for comparison bar chart
    completion_rates = {}
    for scope_name, scope_tasks in tasks_by_scope.items():
        metrics = calculate_team_metrics(scope_tasks)
        completion_rates[scope_name] = int(metrics['completion_rate'])
    
    comparison_bar_chart = generate_bar_chart(completion_rates, "Completion Rates by Team/Department")
    chart_section.append(comparison_bar_chart)
    chart_section.append(Spacer(1, 20))
    
    elements.append(KeepTogether(chart_section))

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

    # Check if this is organization metrics data
    if 'organization_metrics' in data_by_scope:
        org_metrics = data_by_scope['organization_metrics']
        dept_metrics = org_metrics['dept_metrics']
        
        # Organization Summary - keep together
        overview_section = []
        overview_section.append(Paragraph("Organization Overview", heading_style))
        overview_section.append(Spacer(1, 15))
        
        overview_data = [
            ['Metric', 'Value'],
            ['Total Departments', str(len(dept_metrics))],
            ['Total Employees', str(org_metrics['total_employees'])],
            ['Total Tasks', str(org_metrics['total_tasks'])],
            ['Avg. Workload (Days/Employee)', f"{org_metrics['avg_workload_time_per_employee']:.1f}"],
            ['Avg. Tasks/Employee', f"{org_metrics['avg_workload_tasks_per_employee']:.1f}"],
            ['Avg. Days/Task', f"{org_metrics.get('avg_time_per_task_days', 0):.1f}"],
            ['Trend Interval', org_metrics.get('trend_granularity', 'Monthly').title()]
        ]
        
        overview_table = Table(overview_data, colWidths=[3.0 * inch, 2.0 * inch])
        overview_table.setStyle(TableStyle([
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
        
        for row_idx in range(1, len(overview_data)):
            bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
            ]))

        overview_section.append(overview_table)
        overview_section.append(Spacer(1, 24))
        
        elements.append(KeepTogether(overview_section))
        
        # Department Metrics - properly transposed format for print compatibility
        dept_section = []
        dept_section.append(Paragraph("Department Metrics", heading_style))
        dept_section.append(Spacer(1, 6))

        # Create truly transposed table: metrics as rows, departments as columns
        # First, collect all department names (handle empty case)
        if not dept_metrics:
            dept_section.append(Paragraph("No department data available", styles['Normal']))
            dept_section.append(Spacer(1, 24))
            elements.append(KeepTogether(dept_section))
        else:
            dept_names = [escape(dept.get('department', 'Unknown'))[:12] for dept in dept_metrics]  # Shorter names
            
            # Create table with metrics as rows and departments as columns
            dept_table_data = [
                ['Metric'] + dept_names  # Header row
            ]
        
            # Add each metric as a row
            metrics_to_show = [
                ('Completion Rate (%)', lambda d: f"{d.get('completion_rate', 0):.1f}%"),
                ('Overdue (%)', lambda d: f"{d.get('overdue_percentage', 0):.1f}%"),
                ('Employees', lambda d: str(d.get('employee_count', 0))),
                ('Time Logged (days)', lambda d: f"{d.get('time_logged_days', 0):.1f}"),
                ('Avg Tasks/Emp', lambda d: f"{d.get('avg_tasks_per_employee', d['total_tasks'] / d.get('employee_count', 1) if d.get('employee_count', 0) > 0 else 0):.1f}"),
                ('Avg Days/Emp', lambda d: f"{d.get('avg_time_per_employee_days', d.get('time_logged_days', 0) / d.get('employee_count', 1) if d.get('employee_count', 0) > 0 else 0):.1f}"),
                ('Avg Days/Task', lambda d: f"{d.get('avg_time_per_task_days', 0):.1f}")
            ]
            
            for metric_name, value_func in metrics_to_show:
                row = [metric_name]
                for dept in dept_metrics:
                    try:
                        row.append(value_func(dept))
                    except:
                        row.append('N/A')
                dept_table_data.append(row)

            # Calculate dynamic column widths based on number of departments - more compact
            num_depts = len(dept_names)
            if num_depts <= 4:
                # For 4 or fewer departments, use smaller columns
                metric_col_width = 1.1 * inch
                dept_col_width = (6.0 * inch - metric_col_width) / max(num_depts, 1)
            else:
                # For more departments, use even narrower columns
                metric_col_width = 1.0 * inch
                dept_col_width = min(0.7 * inch, (6.0 * inch - metric_col_width) / num_depts)
            
            col_widths = [metric_col_width] + [dept_col_width] * num_depts

            dept_table = Table(dept_table_data, colWidths=col_widths)
            dept_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 6),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),      # Metric column header left
                ('ALIGN', (1, 0), (-1, 0), 'CENTER'),  # Department headers center
                ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
                ('TOPPADDING', (0, 0), (-1, 0), 3),

                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # Metric names left
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'), # Data values center
                ('TOPPADDING', (0, 1), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                # Styling
                ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Metric column background
                ('BACKGROUND', (0, 1), (0, -1), HexColor('#f8fafc')),
            ]))

            # Alternating row colors for data rows
            for row_idx in range(1, len(dept_table_data)):
                if row_idx % 2 == 0:  # Even rows (starting from 1)
                    dept_table.setStyle(TableStyle([
                        ('BACKGROUND', (1, row_idx), (-1, row_idx), HexColor('#f8fafc'))
                    ]))

            dept_section.append(dept_table)
            dept_section.append(Spacer(1, 8))
            
            elements.append(KeepTogether(dept_section))
        
        # Trend section
        trend_data = org_metrics.get('trend') or org_metrics.get('monthly_completions') or {}
        if trend_data:
            trend_section = []
            trend_label = org_metrics.get('trend_granularity', 'Monthly').title()
            trend_section.append(Paragraph(f"{trend_label} Task Completion Trend", heading_style))
            trend_section.append(Spacer(1, 15))
            
            trend_rows = [[trend_label, 'Tasks Completed']]
            for period, count in sorted(trend_data.items()):
                trend_rows.append([period, str(count)])
            
            monthly_table = Table(trend_rows, colWidths=[2.5 * inch, 2.0 * inch])
            monthly_table.setStyle(TableStyle([
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
            
            for row_idx in range(1, len(trend_rows)):
                bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
                monthly_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
                ]))

            trend_section.append(monthly_table)
            trend_section.append(Spacer(1, 18))
            
            elements.append(KeepTogether(trend_section))
        
    else:
        # Legacy format for other report types
        # Comparison overview
        elements.append(Paragraph("Scope Comparison Overview", heading_style))
        elements.append(Spacer(1, 15))

        comparison_data: List[List[str]] = [
            ['Scope', 'Total Tasks', 'Completed', 'Completion Rate', 'Overdue %', 'Avg. Duration (hrs)', 'Total Time (hrs)']
        ]

        for scope_name, tasks in data_by_scope.items():
            metrics = calculate_team_metrics(tasks)
            comparison_data.append([
                scope_name,
                str(metrics['total_tasks']),
                str(metrics['completed_tasks']),
                f"{metrics['completion_rate']:.1f}%",
                f"{metrics['overdue_percentage']:.1f}%",
                f"{metrics.get('avg_completion_time_hours', metrics.get('avg_completion_time', 0)):.1f}",
                f"{metrics.get('total_time_spent_hours', metrics.get('total_time_spent', 0)):.1f}"
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
    """Get available report options based on user role and report type."""
    try:
        user_id = request.args.get('user_id')
        report_type = request.args.get('report_type')
        scope_type = request.args.get('scope_type')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        user = get_user_details(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        role = user.get('role')
        department = user.get('department')
        
        # Handle specific report type requests
        logger.info(f"Debug: report_type={report_type}, scope_type={scope_type}")
        if report_type:
            logger.info(f"Calling get_options_for_report_type with user={user.get('name')} and report_type={report_type}")
            return get_options_for_report_type(user, report_type)
            
        # Handle scope type requests for HR organization reports
        if scope_type:
            logger.info(f"Calling get_options_for_scope_type with user={user.get('name')} and scope_type={scope_type}")
            return get_options_for_scope_type(user, scope_type)
        
        # Default: return available report types and general options
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
            
            # Get all teams across organization (only managers, not directors)
            all_users_response = supabase.table('user').select('*').execute()
            all_users = all_users_response.data or []
            superiors = list(set([user.get('superior') for user in all_users if user.get('superior')]))
            team_names = []
            
            for superior_id in superiors:
                superior_user = get_user_details(superior_id)
                if superior_user and superior_user.get('role') == UserRole.MANAGER.value:
                    # Only include managers as team leads (directors manage departments, not teams)
                    team_names.append(superior_user.get('name', superior_id))
            
            options['teams'] = team_names
            
        return jsonify(options), 200
        
    except Exception as e:
        logger.error(f"Error fetching report options: {e}")
        return jsonify({"error": "Failed to fetch report options"}), 500
    """Get specific options based on report type."""

@app.route("/generate-report", methods=["POST"])
def generate_report():
    try:
        logger.info("=== GENERATE REPORT START ===")
        data = request.get_json()
        logger.info(f"Request data: {data}")

        requesting_user_id = data.get('requesting_user_id') or data.get('user_id')
        if not requesting_user_id:
            return jsonify({"error": "user_id is required"}), 400

        requesting_user = get_user_details(requesting_user_id)
        if not requesting_user:
            return jsonify({"error": "User not found"}), 404

        report_type = data.get('report_type', 'individual')

        validation_data = {
            'report_type': report_type,
            'user_id': requesting_user_id,
            'department': requesting_user.get('department'),
            'teams': data.get('teams', [])
        }

        if not validate_report_access(requesting_user, validation_data):
            logger.error("Access validation failed")
            return jsonify({"error": "Unauthorized to generate this report type"}), 403

        start_date = data.get('start_date')
        end_date = data.get('end_date')
        status_filter = data.get('status_filter', ['All'])

        try:
            preview_data = generate_report_preview_data(
                requesting_user, report_type, data, start_date, end_date, status_filter
            )
        except ValueError as exc:
            logger.error(f"Validation error while preparing report preview: {exc}")
            return jsonify({"error": str(exc)}), 400

        report_labels = {
            ReportType.INDIVIDUAL.value: 'Individual',
            ReportType.TEAM.value: 'Team',
            ReportType.DEPARTMENT.value: 'Department',
            ReportType.ORGANIZATION.value: 'Organization'
        }
        report_label = report_labels.get(report_type, 'Report')
        preview_data['report_title'] = data.get('report_title') or f"{report_label} Performance Report"

        summary = preview_data.setdefault('summary', {})
        if report_type == ReportType.INDIVIDUAL.value and not summary.get('target_user'):
            summary['target_user'] = requesting_user.get('name', 'Unknown')

        pdf_buffer = generate_preview_pdf(preview_data, requesting_user)

        summary_targets = [
            summary.get('target_user'),
            ', '.join(summary.get('selected_teams', [])) if summary.get('selected_teams') else None,
            summary.get('team_name'),
            summary.get('department'),
            summary.get('scope'),
            summary.get('scope_type')
        ]
        filename_seed = next((value for value in summary_targets if value), report_label)
        safe_slug = sanitize_filename_component(filename_seed)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_report_{safe_slug}_{timestamp}.pdf"

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


def clean_data_for_json(data):
    """Clean data structure to ensure JSON serializability by removing None keys and converting None values."""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # Skip None keys
            if key is None:
                continue
            # Convert None keys to string
            clean_key = str(key) if key is not None else 'null'
            # Recursively clean values
            cleaned[clean_key] = clean_data_for_json(value)
        return cleaned
    elif isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif data is None:
        return 'null'
    else:
        return data


@app.route("/preview-report", methods=["POST"])
def preview_report():
    """
    Generate regular report data for preview (returns JSON).
    
    Request body - same format as generate-report endpoint
    
    Returns:
        JSON with report data and chart information
    """
    try:
        logger.info("=== PREVIEW REPORT START ===")
        data = request.get_json()
        logger.info(f"Preview request data: {data}")
        
        # Get requesting user details
        requesting_user_id = data.get('requesting_user_id') or data.get('user_id')
        
        if not requesting_user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        requesting_user = get_user_details(requesting_user_id)
        
        if not requesting_user:
            return jsonify({"error": "User not found"}), 404
        
        report_type = data.get('report_type', 'individual')
        
        # Validate access
        validation_data = {
            'report_type': report_type,
            'user_id': requesting_user_id,
            'department': requesting_user.get('department'),
            'teams': data.get('teams', [])
        }
        
        if not validate_report_access(requesting_user, validation_data):
            return jsonify({"error": "Unauthorized to generate this report type"}), 403
        
        # Common parameters
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        status_filter = data.get('status_filter', ['All'])
        user_role = requesting_user.get('role')
        
        # Generate preview data based on report type
        preview_data = generate_report_preview_data(
            requesting_user, report_type, data, start_date, end_date, status_filter
        )
        
        # Clean data to ensure JSON serializability
        cleaned_data = clean_data_for_json(preview_data)
        
        return jsonify(cleaned_data), 200
        
    except Exception as e:
        logger.error(f"Error generating report preview: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate preview", "details": str(e)}), 500

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
    """Debug endpoint to check user data and report permissions."""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            # Return sample users if no user_id provided
            response = supabase.table('user').select('user_id, name, role, department').limit(5).execute()
            return jsonify({
                "message": "Provide user_id parameter to test specific user",
                "sample_users": response.data or [],
                "environment": {
                    'SUPABASE_URL': bool(SUPABASE_URL),
                    'TASK_SERVICE_URL': TASK_SERVICE_URL,
                    'USER_SERVICE_URL': USER_SERVICE_URL
                }
            }), 200
            
        user = get_user_details(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Test validation for individual report
        test_data = {
            'report_type': 'individual',
            'user_id': user_id,
            'department': user.get('department'),
            'teams': []
        }
        
        has_access = validate_report_access(user, test_data)
        
        result = {
            "user": user,
            "can_generate_individual_report": has_access,
            "test_validation_data": test_data,
            "role_enum_values": [role.value for role in UserRole],
            "user_role_match": user.get('role') in [role.value for role in UserRole]
        }
        
        # Get department members if applicable
        if user.get('department'):
            dept_members = get_team_members(user.get('department'))
            result["department_members_count"] = len(dept_members) if dept_members else 0
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
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
