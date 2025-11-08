"""
Scoring Engine for Project Management Dashboard

Contains algorithms for calculating project scores and generating recommendations.
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from plotly_integration.models import Project, ProjectMetrics
from ..config import SCORE_WEIGHTS, SCORE_THRESHOLDS


# ========================================
# Individual Score Calculations
# ========================================

def calculate_priority_score(priority_set: int) -> float:
    """
    Calculate score based on priority set.
    Priority 1 = 100, Priority 2 = 66, Priority 3 = 33

    Args:
        priority_set: Priority value (1, 2, or 3)

    Returns:
        Score from 0-100
    """
    priority_scores = {
        1: 100.0,
        2: 66.7,
        3: 33.3,
    }
    return priority_scores.get(priority_set, 50.0)


def calculate_on_time_score(project: Project) -> float:
    """
    Calculate score based on timeline adherence.

    Scoring logic:
    - If no dates set: 50 (neutral)
    - Compare actual vs expected timeline
    - Early completion: bonus points
    - On time: 100
    - Slightly late (< 10 days): 75
    - Moderately late (10-20 days): 50
    - Very late (> 20 days): 25

    Args:
        project: Project instance

    Returns:
        Score from 0-100
    """
    if not project.creation_date:
        return 50.0  # Neutral score if no dates

    if not project.purification_finish_date:
        # Project in progress - check if overdue
        if project.cloning_finish_date:
            # Estimate: cloning + 30 days for purification
            expected_purification = project.cloning_finish_date + timedelta(days=30)
            today = datetime.now().date()

            if today <= expected_purification:
                return 100.0  # On track
            else:
                days_overdue = (today - expected_purification).days
                if days_overdue < 10:
                    return 75.0
                elif days_overdue < 20:
                    return 50.0
                else:
                    return 25.0
        else:
            # Only creation date - estimate cloning should be done in 30 days
            expected_cloning = project.creation_date + timedelta(days=30)
            today = datetime.now().date()

            if today <= expected_cloning:
                return 100.0
            else:
                days_overdue = (today - expected_cloning).days
                if days_overdue < 10:
                    return 75.0
                elif days_overdue < 20:
                    return 50.0
                else:
                    return 25.0

    # Project completed - use actual lead time
    if project.lead_time:
        # Typical lead time benchmark: 50 days
        benchmark_lead_time = 50

        if project.lead_time <= benchmark_lead_time:
            # Early or on time - bonus for being faster
            days_ahead = benchmark_lead_time - project.lead_time
            return min(100.0, 100.0 + (days_ahead * 2))  # Cap at 100
        else:
            # Late
            days_late = project.lead_time - benchmark_lead_time
            if days_late < 10:
                return 75.0
            elif days_late < 20:
                return 50.0
            else:
                return 25.0

    return 50.0  # Default neutral score


def calculate_completion_score(project: Project) -> float:
    """
    Calculate score based on project completion progress.

    Completion stages:
    - Creation only: 25%
    - Creation + Cloning: 50%
    - Creation + Cloning + Purification: 100%
    - Completed status: 100%

    Args:
        project: Project instance

    Returns:
        Score from 0-100
    """
    if project.status == 'Completed':
        return 100.0

    if project.status == 'Cancelled':
        return 0.0

    # Count completed milestones
    milestones_completed = 0

    if project.creation_date:
        milestones_completed += 1

    if project.cloning_finish_date:
        milestones_completed += 1

    if project.purification_finish_date:
        milestones_completed += 1

    # Calculate percentage (3 milestones total)
    completion_percentage = (milestones_completed / 3.0) * 100
    return completion_percentage


def calculate_resource_score(project: Project) -> float:
    """
    Calculate score based on resource utilization.

    For now, this is a placeholder that considers:
    - Whether project has an assigned owner (good for accountability)
    - Project status (active projects score higher)

    Args:
        project: Project instance

    Returns:
        Score from 0-100
    """
    score = 50.0  # Base score

    # Has assigned owner
    if project.assigned_to:
        score += 25.0

    # Status-based scoring
    if project.status == 'Active':
        score += 25.0
    elif project.status == 'On Hold':
        score += 10.0
    elif project.status == 'Completed':
        score += 25.0
    # Cancelled gets no bonus

    return min(100.0, score)


# ========================================
# Weighted Score Calculation
# ========================================

def calculate_weighted_score(priority_score: float,
                             on_time_score: float,
                             completion_score: float,
                             resource_score: float) -> float:
    """
    Calculate weighted total score.

    Weights:
    - Priority: 40%
    - On-time: 30%
    - Completion: 20%
    - Resource: 10%

    Args:
        priority_score: Priority score (0-100)
        on_time_score: On-time score (0-100)
        completion_score: Completion score (0-100)
        resource_score: Resource score (0-100)

    Returns:
        Weighted total score (0-100)
    """
    weighted_total = (
        priority_score * SCORE_WEIGHTS['priority'] +
        on_time_score * SCORE_WEIGHTS['on_time'] +
        completion_score * SCORE_WEIGHTS['completion'] +
        resource_score * SCORE_WEIGHTS['resource']
    )
    return round(weighted_total, 2)


# ========================================
# Recommendation Generation
# ========================================

def generate_recommendation(weighted_score: float, project: Project) -> tuple[str, str]:
    """
    Generate recommendation based on weighted score and project status.

    Returns:
        Tuple of (recommendation, reason)
    """
    status = project.status

    # Handle special cases first
    if status == 'Cancelled':
        return ('CONSIDER CANCELLATION', 'Project already cancelled')

    if status == 'Completed':
        return ('PUSH FORWARD', 'Project completed successfully')

    if status == 'On Hold':
        if weighted_score >= SCORE_THRESHOLDS['monitor']:
            return ('REVIEW', f'Good score ({weighted_score:.1f}) but project on hold - review to reactivate')
        else:
            return ('CONSIDER CANCELLATION', f'Low score ({weighted_score:.1f}) and on hold - consider cancellation')

    # Active projects - score-based recommendations
    if weighted_score >= SCORE_THRESHOLDS['push_forward']:
        return ('PUSH FORWARD', f'High score ({weighted_score:.1f}) indicates strong performance')

    if weighted_score >= SCORE_THRESHOLDS['monitor']:
        return ('MONITOR', f'Moderate score ({weighted_score:.1f}) - continue monitoring')

    if weighted_score >= SCORE_THRESHOLDS['review']:
        return ('REVIEW', f'Low score ({weighted_score:.1f}) - management review recommended')

    return ('CONSIDER CANCELLATION', f'Very low score ({weighted_score:.1f}) - consider cancellation')


# ========================================
# Full Score Update
# ========================================

def calculate_and_update_metrics(project: Project) -> ProjectMetrics:
    """
    Calculate all scores and update the ProjectMetrics for a project.

    Args:
        project: Project instance

    Returns:
        Updated ProjectMetrics instance
    """
    # Calculate individual scores
    priority_score = calculate_priority_score(project.priority_set)
    on_time_score = calculate_on_time_score(project)
    completion_score = calculate_completion_score(project)
    resource_score = calculate_resource_score(project)

    # Calculate weighted total
    weighted_total = calculate_weighted_score(
        priority_score,
        on_time_score,
        completion_score,
        resource_score
    )

    # Generate recommendation
    recommendation, reason = generate_recommendation(weighted_total, project)

    # Get or create metrics
    metrics, created = ProjectMetrics.objects.get_or_create(project=project)

    # Update metrics
    metrics.priority_score = priority_score
    metrics.on_time_score = on_time_score
    metrics.completion_score = completion_score
    metrics.resource_score = resource_score
    metrics.weighted_total = weighted_total
    metrics.recommendation = recommendation
    metrics.recommendation_reason = reason
    metrics.save()

    return metrics


def recalculate_all_project_metrics():
    """
    Recalculate metrics for all projects.
    Useful for batch updates or when scoring logic changes.

    Returns:
        Number of projects updated
    """
    projects = Project.objects.all()
    count = 0

    for project in projects:
        calculate_and_update_metrics(project)
        count += 1

    return count


# ========================================
# Score Analysis Helpers
# ========================================

def get_score_breakdown(project: Project) -> Dict[str, float]:
    """
    Get detailed score breakdown for a project.

    Args:
        project: Project instance

    Returns:
        Dictionary with all score components
    """
    priority_score = calculate_priority_score(project.priority_set)
    on_time_score = calculate_on_time_score(project)
    completion_score = calculate_completion_score(project)
    resource_score = calculate_resource_score(project)

    weighted_total = calculate_weighted_score(
        priority_score,
        on_time_score,
        completion_score,
        resource_score
    )

    recommendation, reason = generate_recommendation(weighted_total, project)

    return {
        'priority_score': round(priority_score, 1),
        'on_time_score': round(on_time_score, 1),
        'completion_score': round(completion_score, 1),
        'resource_score': round(resource_score, 1),
        'weighted_total': round(weighted_total, 1),
        'recommendation': recommendation,
        'recommendation_reason': reason,
        # Include weights for transparency
        'weights': {
            'priority': SCORE_WEIGHTS['priority'] * 100,
            'on_time': SCORE_WEIGHTS['on_time'] * 100,
            'completion': SCORE_WEIGHTS['completion'] * 100,
            'resource': SCORE_WEIGHTS['resource'] * 100,
        }
    }


def compare_project_scores(project_id_1: int, project_id_2: int) -> Dict:
    """
    Compare scores between two projects.

    Args:
        project_id_1: First project ID
        project_id_2: Second project ID

    Returns:
        Dictionary with comparison data
    """
    project1 = Project.objects.get(id=project_id_1)
    project2 = Project.objects.get(id=project_id_2)

    breakdown1 = get_score_breakdown(project1)
    breakdown2 = get_score_breakdown(project2)

    return {
        'project1': {
            'molecule_id': project1.molecule_id,
            'scores': breakdown1
        },
        'project2': {
            'molecule_id': project2.molecule_id,
            'scores': breakdown2
        },
        'differences': {
            'priority_score_diff': breakdown1['priority_score'] - breakdown2['priority_score'],
            'on_time_score_diff': breakdown1['on_time_score'] - breakdown2['on_time_score'],
            'completion_score_diff': breakdown1['completion_score'] - breakdown2['completion_score'],
            'resource_score_diff': breakdown1['resource_score'] - breakdown2['resource_score'],
            'weighted_total_diff': breakdown1['weighted_total'] - breakdown2['weighted_total'],
        }
    }
