import os
import io
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from collections import Counter

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

# Environment variables
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8080")
PROJECT_SERVICE_URL = os.getenv("PROJECT_SERVICE_URL", "http://localhost:8082")

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


def fetch_project_report_data(project_id: str) -> Dict[str, Any]:
    """
    Fetch and prepare project report data for preview or PDF generation.

    Args:
        project_id: The project ID to generate report for

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

        logger.info(f"Fetched project {project_id} with {len(tasks)} tasks")

        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get('status', '').lower() == 'completed'])
        ongoing_tasks = len([t for t in tasks if t.get('status', '').lower() == 'ongoing'])
        under_review_tasks = len([t for t in tasks if t.get('status', '').lower() == 'under review'])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Count tasks by team member
        tasks_by_member = {}
        completed_by_member = {}

        for task in tasks:
            assignee = task.get('assignee_name', task.get('owner_name', 'Unassigned'))
            tasks_by_member[assignee] = tasks_by_member.get(assignee, 0) + 1

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
                'total': total,
                'completed': completed,
                'rate': round(rate, 1)
            })

        # Return structured report data
        return {
            'project': {
                'id': project_data.get('project_id'),
                'name': project_data.get('project_name', 'Untitled Project'),
                'description': project_data.get('project_description', 'No description'),
                'owner': project_data.get('created_by_name', 'Unknown'),
                'status': project_data.get('status', 'Active'),
                'created_date': created_date,
                'due_date': due_date,
                'collaborators': project_data.get('collaborators', [])
            },
            'summary': {
                'total_tasks': total_tasks,
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
    if os.path.exists(logo_path):
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
        ['Status:', project['status'] or 'N/A'],
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

    # Summary statistics
    summary = report_data['summary']
    summary_heading = Paragraph("Project Performance Summary", heading_style)
    elements.append(summary_heading)
    elements.append(Spacer(1, 8))

    summary_data = [
        ['Total Tasks', 'Completed', 'In Progress', 'Under Review', 'Completion Rate'],
        [
            str(summary['total_tasks']),
            str(summary['completed_tasks']),
            str(summary['ongoing_tasks']),
            str(summary['under_review_tasks']),
            f"{summary['completion_rate']}%"
        ]
    ]

    summary_table = Table(summary_data, colWidths=[1.2*inch]*5)
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

    # Team performance
    if report_data['team_performance']:
        team_heading = Paragraph("Team Member Performance", heading_style)
        elements.append(team_heading)
        elements.append(Spacer(1, 8))

        team_data = [['Team Member', 'Total Tasks', 'Completed', 'Completion Rate']]
        for member in report_data['team_performance']:
            team_data.append([
                member['member'],
                str(member['total']),
                str(member['completed']),
                f"{member['rate']}%"
            ])

        team_table = Table(team_data, colWidths=[2.5*inch, 1.3*inch, 1.3*inch, 1.5*inch])
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

        # Alternating row colors
        for row_idx in range(1, len(team_data)):
            bg_color = colors.white if row_idx % 2 == 1 else HexColor('#f8fafc')
            team_table.setStyle(TableStyle([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color)
            ]))

        elements.append(team_table)
        elements.append(Spacer(1, 20))

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


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "report-service"}), 200


@app.route("/generate-report", methods=["POST"])
def generate_report():
    """
    Generate a PDF report for a user's tasks.

    Request body:
    {
        "user_id": "user-uuid",
        "user_name": "User Name",
        "start_date": "2025-01-01",  // Optional
        "end_date": "2025-12-31",    // Optional
        "status_filter": ["Ongoing", "Completed"]   // Optional: List of statuses or ['All']
    }

    Returns:
        PDF file stream
    """
    try:
        data = request.get_json()

        # Validate required fields
        user_id = data.get('user_id')
        user_name = data.get('user_name', 'Unknown User')

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Optional filters
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        status_filter = data.get('status_filter', ['All'])

        # Ensure status_filter is a list
        if isinstance(status_filter, str):
            status_filter = [status_filter]

        # Validate date formats if provided
        if start_date:
            try:
                datetime.fromisoformat(start_date)
            except ValueError:
                return jsonify({"error": "start_date must be in ISO format (YYYY-MM-DD)"}), 400

        if end_date:
            try:
                datetime.fromisoformat(end_date)
            except ValueError:
                return jsonify({"error": "end_date must be in ISO format (YYYY-MM-DD)"}), 400

        # Fetch tasks
        logger.info(f"Generating report for user {user_id}")
        tasks = fetch_tasks_for_user(user_id, start_date, end_date, status_filter)

        # Generate PDF
        pdf_buffer = generate_pdf_report(user_id, user_name, tasks, start_date, end_date, status_filter)

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"task_report_{user_name.replace(' ', '_')}_{timestamp}.pdf"

        # Return PDF as response
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
        "project_id": "project-uuid"
    }

    Returns:
        JSON with report data
    """
    try:
        data = request.get_json()
        project_id = data.get('project_id')

        if not project_id:
            return jsonify({"error": "project_id is required"}), 400

        logger.info(f"Generating preview for project {project_id}")
        report_data = fetch_project_report_data(project_id)

        return jsonify(report_data), 200

    except requests.RequestException as e:
        logger.error(f"Error communicating with services: {e}")
        return jsonify({"error": "Failed to fetch project data", "details": str(e)}), 503

    except Exception as e:
        logger.error(f"Error generating project report preview: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate preview", "details": str(e)}), 500


@app.route("/generate-project-report", methods=["POST"])
def generate_project_report():
    """
    Generate a PDF report for a project.

    Request body:
    {
        "project_id": "project-uuid"
    }

    Returns:
        PDF file stream
    """
    try:
        data = request.get_json()
        project_id = data.get('project_id')

        if not project_id:
            return jsonify({"error": "project_id is required"}), 400

        logger.info(f"Generating PDF report for project {project_id}")

        # Fetch project report data
        report_data = fetch_project_report_data(project_id)

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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8090))
    logger.info(f"Starting Report Service on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
