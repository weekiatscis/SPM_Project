import os
import io
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from collections import Counter
from enum import Enum

# Configure logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Now import other packages
from supabase import create_client, Client
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
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
# Add after TASK_SERVICE_URL line
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
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

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        tasks = data.get('tasks', [])

        # Apply filters
        filtered_tasks = []
        for task in tasks:
            # Status filter - check if task status is in the list of selected statuses
            if status_filter and len(status_filter) > 0 and 'All' not in status_filter:
                task_status = task.get('status', '').lower()
                if not any(status.lower() == task_status for status in status_filter):
                    continue

            # Date range filter (based on assigned date - created_at)
            if start_date or end_date:
                created_at = task.get('created_at')
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
                        logger.warning(f"Could not parse date for task {task.get('id')}: {e}")
                        continue

            filtered_tasks.append(task)

        logger.info(f"Fetched {len(filtered_tasks)} tasks for user {user_id}")
        return filtered_tasks

    except requests.RequestException as e:
        logger.error(f"Error fetching tasks from task service: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching tasks: {e}")
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

    # Subtitle style
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#64748b'),
        spaceAfter=20,
        alignment=TA_LEFT,
        fontName='Helvetica'
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

    # Header with Title and Logo
    from reportlab.graphics.shapes import Line, Drawing as ShapeDrawing
    from svglib.svglib import svg2rlg

    # Load logo
    logo_path = os.path.join(os.path.dirname(__file__), 'taskio-logo.svg')
    logo = None
    if os.path.exists(logo_path) and svg2rlg:
        try:
            logo_drawing = svg2rlg(logo_path)
            # Scale logo to reasonable size
            scale_factor = 0.35  # Adjust this to make logo smaller/larger
            logo_drawing.width = logo_drawing.width * scale_factor
            logo_drawing.height = logo_drawing.height * scale_factor
            logo_drawing.scale(scale_factor, scale_factor)
            logo = logo_drawing
        except Exception as e:
            logger.warning(f"Could not load logo: {e}")

    # Create header table with title on left and logo on right
    if logo:
        header_data = [[
            Paragraph("Task Progress Report", title_style),
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
        # Fallback to text if logo not found
        header_data = [[
            Paragraph("Task Progress Report", title_style),
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

    # Add a horizontal line under header
    line_drawing = ShapeDrawing(500, 3)
    line = Line(0, 0, 500, 0)
    line.strokeColor = HexColor('#3b82f6')
    line.strokeWidth = 3
    line_drawing.add(line)
    elements.append(line_drawing)
    elements.append(Spacer(1, 18))

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
    """Validate if user has access to generate the requested report type."""
    user_role = requesting_user.get('role')
    report_type = report_data.get('report_type', 'individual')
    
    # Staff can only generate individual reports for themselves
    if user_role == UserRole.STAFF.value:
        return (report_type == ReportType.INDIVIDUAL.value and 
                report_data.get('user_id') == requesting_user.get('user_id'))
    
    # Manager can generate team reports for their subordinates
    elif user_role == UserRole.MANAGER.value:
        if report_type == ReportType.INDIVIDUAL.value:
            target_user_id = report_data.get('user_id')
            if target_user_id == requesting_user.get('user_id'):
                return True
            target_user = get_user_details(target_user_id)
            return target_user and target_user.get('superior') == requesting_user.get('user_id')
        elif report_type == ReportType.TEAM.value:
            return True
        return False
    
    # Director can generate department reports
    elif user_role == UserRole.DIRECTOR.value:
        if report_type in [ReportType.INDIVIDUAL.value, ReportType.TEAM.value, ReportType.DEPARTMENT.value]:
            target_department = report_data.get('department')
            return target_department == requesting_user.get('department')
        return False
    
    # HR can generate organization-wide reports
    elif user_role == UserRole.HR.value:
        return True
    
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
            'completion_rate': 0,
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
            options['teams'] = [member['name'] for member in get_team_members(department, user_id)]
            
        elif role == UserRole.DIRECTOR.value:
            options['available_report_types'] = ['individual', 'team', 'department']
            options['departments'] = [department]
            # Get teams in their department
            dept_members = get_team_members(department)
            superiors = list(set([member.get('superior') for member in dept_members if member.get('superior')]))
            options['teams'] = superiors
            
        elif role == UserRole.HR.value:
            options['available_report_types'] = ['individual', 'team', 'department', 'organization']
            options['departments'] = get_all_departments()
            # Get all teams across organization
            all_users = supabase.table('user').select('superior').execute().data
            all_superiors = list(set([user.get('superior') for user in all_users if user.get('superior')]))
            options['teams'] = all_superiors
            
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
        data = request.get_json()
        
        # Get requesting user details
        requesting_user_id = data.get('requesting_user_id') or data.get('user_id')
        if not requesting_user_id:
            return jsonify({"error": "requesting_user_id is required"}), 400
            
        requesting_user = get_user_details(requesting_user_id)
        if not requesting_user:
            return jsonify({"error": "User not found"}), 404
        
        report_type = data.get('report_type', 'individual')
        
        # Validate access
        if not validate_report_access(requesting_user, data):
            return jsonify({"error": "Unauthorized to generate this report type"}), 403
        
        # Handle different report types based on user role
        user_role = requesting_user.get('role')
        
        if report_type == ReportType.INDIVIDUAL.value:
            # Individual report (existing functionality)
            user_id = data.get('user_id', requesting_user_id)
            user_name = data.get('user_name') or requesting_user.get('name', 'Unknown User')
            
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            status_filter = data.get('status_filter', ['All'])
            
            tasks = fetch_tasks_for_user(user_id, start_date, end_date, status_filter)
            pdf_buffer = generate_pdf_report(user_id, user_name, tasks, start_date, end_date, status_filter)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"individual_report_{user_name.replace(' ', '_')}_{timestamp}.pdf"
            
            # Return PDF
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        else:
            return jsonify({"error": "Report type not implemented yet"}), 400
        
    except requests.RequestException as e:
        logger.error(f"Error communicating with task service: {e}")
        return jsonify({"error": "Failed to fetch tasks from task service", "details": str(e)}), 503
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate report", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, debug=True)
