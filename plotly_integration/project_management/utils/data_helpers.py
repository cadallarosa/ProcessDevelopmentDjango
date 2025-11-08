"""
Data helper functions for Project Management Dashboard

Contains database query functions, data transformation, and filtering logic.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, F
from django.contrib.auth.models import User

from plotly_integration.models import Project, ProjectDecisionHistory, ProjectMetrics


# ========================================
# Project Retrieval Functions
# ========================================

def get_all_projects(status_filter: Optional[str] = None,
                     priority_filter: Optional[int] = None,
                     assigned_to: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all projects with optional filtering.

    Args:
        status_filter: Filter by status (Active, On Hold, Cancelled, Completed)
        priority_filter: Filter by priority set (1, 2, 3)
        assigned_to: Filter by assigned user ID

    Returns:
        List of project dictionaries with all fields
    """
    query = Project.objects.select_related('created_by', 'assigned_to', 'metrics')

    # Apply filters
    if status_filter and status_filter != 'all':
        query = query.filter(status=status_filter)

    if priority_filter:
        query = query.filter(priority_set=priority_filter)

    if assigned_to:
        query = query.filter(assigned_to_id=assigned_to)

    projects = []
    for project in query:
        # Get image URL
        image_url = project.get_image_url()

        # Format image as markdown for DataTable
        image_markdown = f"![{project.molecule_id}]({image_url})"

        # Format last volume update
        last_update_str = project.last_volume_update.strftime('%Y-%m-%d %H:%M') if project.last_volume_update else None

        project_dict = {
            'id': project.id,
            'molecule_id': project.molecule_id,
            'image': image_markdown,
            'image_url': image_url,
            'priority_set': project.priority_set,
            'status': project.status,
            'current_concentration': project.current_concentration,
            'current_volume': project.current_volume,
            'stock_status': project.get_stock_status(),
            'stock_location': project.stock_location,
            'last_volume_update': last_update_str,
            'last_updated_by': project.last_updated_by.username if project.last_updated_by else None,
            'creation_date': project.creation_date.strftime('%Y-%m-%d') if project.creation_date else None,
            'cloning_finish_date': project.cloning_finish_date.strftime('%Y-%m-%d') if project.cloning_finish_date else None,
            'purification_finish_date': project.purification_finish_date.strftime('%Y-%m-%d') if project.purification_finish_date else None,
            'lead_time': project.lead_time,
            'created_by': project.created_by.username if project.created_by else None,
            'assigned_to': project.assigned_to.username if project.assigned_to else None,
            'notes': project.notes,
            'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Add metrics if available
        if hasattr(project, 'metrics'):
            project_dict.update({
                'on_time_score': round(project.metrics.on_time_score, 1),
                'priority_score': round(project.metrics.priority_score, 1),
                'resource_score': round(project.metrics.resource_score, 1),
                'completion_score': round(project.metrics.completion_score, 1),
                'weighted_score': round(project.metrics.weighted_total, 1),
                'recommendation': project.metrics.recommendation,
                'recommendation_reason': project.metrics.recommendation_reason,
            })
        else:
            # Default values if no metrics
            project_dict.update({
                'on_time_score': 0,
                'priority_score': 0,
                'resource_score': 0,
                'completion_score': 0,
                'weighted_score': 0,
                'recommendation': 'MONITOR',
                'recommendation_reason': 'Metrics not yet calculated',
            })

        projects.append(project_dict)

    return projects


def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single project by ID with all related data.

    Args:
        project_id: Project ID

    Returns:
        Project dictionary or None if not found
    """
    try:
        project = Project.objects.select_related('created_by', 'assigned_to', 'metrics').get(id=project_id)
        projects = get_all_projects()
        return next((p for p in projects if p['id'] == project_id), None)
    except Project.DoesNotExist:
        return None


def get_projects_dataframe(status_filter: Optional[str] = None) -> pd.DataFrame:
    """
    Get all projects as a pandas DataFrame for analysis.

    Args:
        status_filter: Filter by status

    Returns:
        DataFrame with project data
    """
    projects = get_all_projects(status_filter=status_filter)
    if not projects:
        return pd.DataFrame()

    df = pd.DataFrame(projects)

    # Convert date columns to datetime
    date_cols = ['creation_date', 'cloning_finish_date', 'purification_finish_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    return df


# ========================================
# Summary Statistics
# ========================================

def get_summary_stats() -> Dict[str, Any]:
    """
    Get summary statistics for the dashboard.

    Returns:
        Dictionary with key metrics
    """
    total_projects = Project.objects.count()
    status_counts = Project.objects.values('status').annotate(count=Count('id'))

    # Convert to dictionary
    status_dict = {item['status']: item['count'] for item in status_counts}

    # Recommendation counts
    recommendation_counts = ProjectMetrics.objects.values('recommendation').annotate(count=Count('project'))
    recommendation_dict = {item['recommendation']: item['count'] for item in recommendation_counts}

    # Average scores
    avg_metrics = ProjectMetrics.objects.aggregate(
        avg_weighted=Avg('weighted_total'),
        avg_on_time=Avg('on_time_score'),
        avg_completion=Avg('completion_score')
    )

    # Completion rate
    completed_count = status_dict.get('Completed', 0)
    completion_rate = (completed_count / total_projects * 100) if total_projects > 0 else 0

    # On-time projects (those that finished purification on or before estimated date)
    on_time_count = Project.objects.filter(
        status='Completed',
        purification_finish_date__isnull=False,
        lead_time__lte=F('lead_time')  # Simplified check
    ).count()

    on_time_rate = (on_time_count / completed_count * 100) if completed_count > 0 else 0

    # Stock status counts
    low_stock_count = Project.objects.filter(
        current_volume__lt=10,
        current_volume__gt=0
    ).count()

    critical_stock_count = Project.objects.filter(
        current_volume__lt=5,
        current_volume__gt=0
    ).count()

    return {
        'total_projects': total_projects,
        'active_count': status_dict.get('Active', 0),
        'on_hold_count': status_dict.get('On Hold', 0),
        'cancelled_count': status_dict.get('Cancelled', 0),
        'completed_count': completed_count,
        'completion_rate': round(completion_rate, 1),
        'on_time_rate': round(on_time_rate, 1),
        'push_forward_count': recommendation_dict.get('PUSH FORWARD', 0),
        'monitor_count': recommendation_dict.get('MONITOR', 0),
        'review_count': recommendation_dict.get('REVIEW', 0),
        'cancel_consideration_count': recommendation_dict.get('CONSIDER CANCELLATION', 0),
        'avg_weighted_score': round(avg_metrics['avg_weighted'] or 0, 1),
        'avg_on_time_score': round(avg_metrics['avg_on_time'] or 0, 1),
        'avg_completion_score': round(avg_metrics['avg_completion'] or 0, 1),
        'low_stock_count': low_stock_count,
        'critical_stock_count': critical_stock_count,
    }


# ========================================
# Decision History Functions
# ========================================

def get_project_decision_history(project_id: int) -> List[Dict[str, Any]]:
    """
    Get decision history for a project.

    Args:
        project_id: Project ID

    Returns:
        List of decision history records
    """
    decisions = ProjectDecisionHistory.objects.filter(
        project_id=project_id
    ).select_related('decision_by').order_by('-decision_date')

    history = []
    for decision in decisions:
        history.append({
            'id': decision.id,
            'decision_date': decision.decision_date.strftime('%Y-%m-%d %H:%M:%S'),
            'decision_type': decision.decision_type,
            'decision_by': decision.decision_by.username if decision.decision_by else 'System',
            'previous_status': decision.previous_status,
            'new_status': decision.new_status,
            'rationale': decision.rationale,
            'system_recommendation': decision.system_recommendation,
        })

    return history


def add_decision_history(project_id: int,
                        decision_type: str,
                        decision_by_id: int,
                        rationale: str,
                        previous_status: str = '',
                        new_status: str = '',
                        system_recommendation: str = '') -> None:
    """
    Add a new decision history record.

    Args:
        project_id: Project ID
        decision_type: Type of decision
        decision_by_id: User ID who made the decision
        rationale: Reason for the decision
        previous_status: Previous status (if applicable)
        new_status: New status (if applicable)
        system_recommendation: System recommendation at time of decision
    """
    ProjectDecisionHistory.objects.create(
        project_id=project_id,
        decision_type=decision_type,
        decision_by_id=decision_by_id,
        rationale=rationale,
        previous_status=previous_status,
        new_status=new_status,
        system_recommendation=system_recommendation
    )


# ========================================
# User Management Functions
# ========================================

def get_all_users() -> List[Dict[str, Any]]:
    """
    Get all active users for assignment dropdowns.

    Returns:
        List of user dictionaries
    """
    users = User.objects.filter(is_active=True).order_by('username')
    return [
        {'label': user.username, 'value': user.id}
        for user in users
    ]


# ========================================
# Project CRUD Operations
# ========================================

def create_project(molecule_id: str,
                  priority_set: int,
                  status: str = 'Active',
                  creation_date: Optional[str] = None,
                  cloning_finish_date: Optional[str] = None,
                  purification_finish_date: Optional[str] = None,
                  created_by_id: Optional[int] = None,
                  assigned_to_id: Optional[int] = None,
                  notes: str = '') -> Project:
    """
    Create a new project.

    Args:
        molecule_id: Unique molecule identifier
        priority_set: Priority (1, 2, 3)
        status: Project status
        creation_date: Creation date (YYYY-MM-DD)
        cloning_finish_date: Cloning completion date
        purification_finish_date: Purification completion date
        created_by_id: User ID of creator
        assigned_to_id: User ID of assignee
        notes: Project notes

    Returns:
        Created Project instance
    """
    # Parse dates
    creation_dt = datetime.strptime(creation_date, '%Y-%m-%d').date() if creation_date else None
    cloning_dt = datetime.strptime(cloning_finish_date, '%Y-%m-%d').date() if cloning_finish_date else None
    purification_dt = datetime.strptime(purification_finish_date, '%Y-%m-%d').date() if purification_finish_date else None

    project = Project.objects.create(
        molecule_id=molecule_id,
        priority_set=priority_set,
        status=status,
        creation_date=creation_dt,
        cloning_finish_date=cloning_dt,
        purification_finish_date=purification_dt,
        created_by_id=created_by_id,
        assigned_to_id=assigned_to_id,
        notes=notes
    )

    # Create default metrics
    ProjectMetrics.objects.create(project=project)

    return project


def update_project(project_id: int, **kwargs) -> bool:
    """
    Update a project with provided fields.

    Args:
        project_id: Project ID
        **kwargs: Fields to update

    Returns:
        True if successful, False otherwise
    """
    try:
        project = Project.objects.get(id=project_id)

        # Handle date conversions
        date_fields = ['creation_date', 'cloning_finish_date', 'purification_finish_date']
        for field in date_fields:
            if field in kwargs and kwargs[field]:
                if isinstance(kwargs[field], str):
                    kwargs[field] = datetime.strptime(kwargs[field], '%Y-%m-%d').date()

        # Update fields
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.save()
        return True
    except Project.DoesNotExist:
        return False


def delete_project(project_id: int) -> bool:
    """
    Delete a project (use carefully - consider soft delete instead).

    Args:
        project_id: Project ID

    Returns:
        True if successful, False otherwise
    """
    try:
        project = Project.objects.get(id=project_id)
        project.delete()
        return True
    except Project.DoesNotExist:
        return False


# ========================================
# Filtering and Search
# ========================================

def search_projects(search_term: str) -> List[Dict[str, Any]]:
    """
    Search projects by molecule ID, notes, or assigned user.

    Args:
        search_term: Search string

    Returns:
        List of matching projects
    """
    if not search_term:
        return get_all_projects()

    query = Project.objects.select_related('created_by', 'assigned_to', 'metrics').filter(
        Q(molecule_id__icontains=search_term) |
        Q(notes__icontains=search_term) |
        Q(assigned_to__username__icontains=search_term)
    )

    projects = []
    for project in query:
        projects_list = get_all_projects()
        project_dict = next((p for p in projects_list if p['id'] == project.id), None)
        if project_dict:
            projects.append(project_dict)

    return projects


def filter_projects_by_date_range(start_date: Optional[str] = None,
                                  end_date: Optional[str] = None,
                                  date_field: str = 'creation_date') -> List[Dict[str, Any]]:
    """
    Filter projects by date range.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        date_field: Field to filter on (creation_date, cloning_finish_date, etc.)

    Returns:
        List of matching projects
    """
    query = Project.objects.all()

    if start_date:
        filter_kwargs = {f"{date_field}__gte": start_date}
        query = query.filter(**filter_kwargs)

    if end_date:
        filter_kwargs = {f"{date_field}__lte": end_date}
        query = query.filter(**filter_kwargs)

    return get_all_projects()


# ========================================
# Bulk Operations
# ========================================

def bulk_update_status(project_ids: List[int], new_status: str, user_id: int, rationale: str) -> int:
    """
    Update status for multiple projects at once.

    Args:
        project_ids: List of project IDs
        new_status: New status to set
        user_id: User making the change
        rationale: Reason for the change

    Returns:
        Number of projects updated
    """
    projects = Project.objects.filter(id__in=project_ids)
    count = 0

    for project in projects:
        old_status = project.status
        project.status = new_status
        project.save()

        # Log decision history
        add_decision_history(
            project_id=project.id,
            decision_type='Status Change',
            decision_by_id=user_id,
            rationale=rationale,
            previous_status=old_status,
            new_status=new_status
        )

        count += 1

    return count


def update_stock_levels(project_id: int,
                       concentration: Optional[float] = None,
                       volume: Optional[float] = None,
                       location: Optional[str] = None,
                       updated_by_id: Optional[int] = None) -> bool:
    """
    Update stock levels for a project.

    Args:
        project_id: Project ID
        concentration: New concentration (mg/mL)
        volume: New volume (mL)
        location: Storage location
        updated_by_id: User ID who made the update

    Returns:
        True if successful, False otherwise
    """
    try:
        project = Project.objects.get(id=project_id)

        if concentration is not None:
            project.current_concentration = concentration

        if volume is not None:
            project.current_volume = volume

        if location is not None:
            project.stock_location = location

        if updated_by_id is not None:
            project.last_updated_by_id = updated_by_id

        project.last_volume_update = datetime.now()
        project.save()

        return True
    except Project.DoesNotExist:
        return False
