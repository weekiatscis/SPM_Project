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

def generate_director_report(tasks_by_team: Dict[str, List[Dict[str, Any]]], 
                           requesting_user: Dict[str, Any],
                           filters: Dict[str, Any]) -> io.BytesIO:
    """Generate director-level department/team comparison report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title and header
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, 
                                textColor=HexColor('#0f172a'), spaceAfter=20, fontName='Helvetica-Bold')
    
    elements.append(Paragraph("Department Performance Report", title_style))
    elements.append(Spacer(1, 20))
    
    # Report metadata
    metadata_data = [
        ['Generated by:', requesting_user.get('name', 'Unknown')],
        ['Role:', requesting_user.get('role', 'Unknown')],
        ['Department:', requesting_user.get('department', 'Unknown')],
        ['Report Date:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ['Teams Analyzed:', ', '.join(tasks_by_team.keys())]
    ]
    
    metadata_table = Table(metadata_data, colWidths=[1.5*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 30))
    
    # Team comparison table
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=16, 
                                  textColor=HexColor('#1e40af'), fontName='Helvetica-Bold')
    
    elements.append(Paragraph("Team Performance Comparison", heading_style))
    elements.append(Spacer(1, 15))
    
    # Calculate metrics for each team
    comparison_data = [
        ['Team/Department', 'Total Tasks', 'Completion Rate', 'Overdue %', 'Avg. Completion Time', 'Total Time Spent']
    ]
    
    for team_name, tasks in tasks_by_team.items():
        metrics = calculate_team_metrics(tasks)
        comparison_data.append([
            team_name,
            str(metrics['total_tasks']),
            f"{metrics['completion_rate']:.1f}%",
            f"{metrics['overdue_percentage']:.1f}%",
            f"{metrics['avg_completion_time']:.1f} days",
            f"{metrics['total_time_spent']} days"
        ])
    
    comparison_table = Table(comparison_data, colWidths=[1.2*inch, 0.8*inch, 1*inch, 0.8*inch, 1.2*inch, 1*inch])
    comparison_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Borders
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    # Alternate row colors
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
    """Generate HR-level organization-wide report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, 
                                textColor=HexColor('#0f172a'), spaceAfter=20, fontName='Helvetica-Bold')
    
    elements.append(Paragraph("Organization Performance Report", title_style))
    elements.append(Spacer(1, 20))
    
    # Report metadata
    scope_type = filters.get('scope_type', 'organization')
    metadata_data = [
        ['Generated by:', requesting_user.get('name', 'Unknown')],
        ['Role:', requesting_user.get('role', 'Unknown')],
        ['Report Scope:', scope_type.title()],
        ['Report Date:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ['Analysis Level:', ', '.join(data_by_scope.keys())]
    ]
    
    metadata_table = Table(metadata_data, colWidths=[1.5*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 30))
    
    # Summary tables for each scope
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=16, 
                                  textColor=HexColor('#1e40af'), fontName='Helvetica-Bold')
    
    for scope_name, tasks in data_by_scope.items():
        elements.append(Paragraph(f"{scope_name} Summary", heading_style))
        elements.append(Spacer(1, 10))
        
        metrics = calculate_team_metrics(tasks)
        
        # Summary table for this scope
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
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Borders
            ('BOX', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Alternate row colors
        for row_idx in range(1, len(summary_data)):
            bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
            ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
    
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
            # Team report
            if user_role == UserRole.MANAGER.value:
                # Manager's team report
                team_members = get_team_members(requesting_user.get('department'), requesting_user_id)
                team_name = f"{requesting_user.get('name', 'Unknown')}'s Team"
                
            elif user_role == UserRole.DIRECTOR.value:
                # Director selecting a specific team
                teams = data.get('teams', [])
                if not teams:
                    return jsonify({"error": "Team selection is required for Directors"}), 400
                
                selected_team = teams[0] if isinstance(teams, list) else teams
                
                # Find team members by team name (assuming team name is the superior's name)
                all_users_response = supabase.table('user').select('*').execute()
                team_members = []
                
                for user in all_users_response.data:
                    if user.get('superior'):
                        superior_user = get_user_details(user.get('superior'))
                        if superior_user and superior_user.get('name') == selected_team:
                            team_members.append(user)
                
                team_name = selected_team
                
            elif user_role == UserRole.HR.value:
                # HR selecting any team
                teams = data.get('teams', [])
                if not teams:
                    return jsonify({"error": "Team selection is required"}), 400
                
                selected_team = teams[0] if isinstance(teams, list) else teams
                
                # Find team members by team name
                all_users_response = supabase.table('user').select('*').execute()
                team_members = []
                
                for user in all_users_response.data:
                    if user.get('superior'):
                        superior_user = get_user_details(user.get('superior'))
                        if superior_user and superior_user.get('name') == selected_team:
                            team_members.append(user)
                
                team_name = selected_team
            else:
                return jsonify({"error": "Unauthorized for team reports"}), 403
            
            if not team_members:
                return jsonify({"error": f"No team members found for team: {team_name}"}), 404
            
            user_ids = [member['user_id'] for member in team_members]
            team_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
            
            # Generate team report using director report function with single team
            tasks_by_team = {team_name: team_tasks}
            pdf_buffer = generate_director_report(tasks_by_team, requesting_user, data)
            filename = f"team_report_{team_name.replace(' ', '_')}_{timestamp}.pdf"
            
        elif report_type == ReportType.DEPARTMENT.value:
            # Department report
            if user_role == UserRole.DIRECTOR.value:
                # Director department/team comparison report
                department = requesting_user.get('department')
                teams = data.get('teams', [])
                
                tasks_by_team = {}
                
                if teams:
                    # Specific teams requested
                    for team in teams:
                        # Find team members by superior name
                        all_users_response = supabase.table('user').select('*').execute()
                        team_members = []
                        
                        for user in all_users_response.data:
                            if user.get('superior'):
                                superior_user = get_user_details(user.get('superior'))
                                if superior_user and superior_user.get('name') == team and user.get('department') == department:
                                    team_members.append(user)
                        
                        if team_members:
                            user_ids = [member['user_id'] for member in team_members]
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
                        user_ids = [member['user_id'] for member in members]
                        team_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
                        
                        # Get team lead name
                        team_lead_name = 'Unassigned'
                        if team_lead != 'No Team':
                            team_lead_user = get_user_details(team_lead)
                            team_lead_name = team_lead_user.get('name', team_lead) if team_lead_user else team_lead
                        
                        tasks_by_team[team_lead_name] = team_tasks
                
                pdf_buffer = generate_director_report(tasks_by_team, requesting_user, data)
                filename = f"department_report_{department}_{timestamp}.pdf"
                
            elif user_role == UserRole.HR.value:
                # HR department report
                department = data.get('department')
                if not department:
                    return jsonify({"error": "Department selection is required"}), 400
                
                dept_members = get_team_members(department)
                user_ids = [member['user_id'] for member in dept_members]
                dept_tasks = fetch_tasks_for_multiple_users(user_ids, start_date, end_date, status_filter)
                
                # Generate as single department analysis
                data_by_scope = {department: dept_tasks}
                pdf_buffer = generate_hr_report(data_by_scope, requesting_user, data)
                filename = f"hr_department_report_{department}_{timestamp}.pdf"
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
