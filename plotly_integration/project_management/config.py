"""
Configuration constants for the Project Management Dashboard
"""
from typing import Dict, List

# ========================================
# Project Status Configuration
# ========================================

PROJECT_STATUSES: List[str] = ['Active', 'On Hold', 'Cancelled', 'Completed']

STATUS_COLORS: Dict[str, str] = {
    'Active': '#28a745',        # Green
    'On Hold': '#ffc107',       # Yellow
    'Cancelled': '#dc3545',     # Red
    'Completed': '#17a2b8',     # Blue
}

STATUS_ICONS: Dict[str, str] = {
    'Active': 'bi-play-circle-fill',
    'On Hold': 'bi-pause-circle-fill',
    'Cancelled': 'bi-x-circle-fill',
    'Completed': 'bi-check-circle-fill',
}

# ========================================
# Priority Configuration
# ========================================

PRIORITY_SETS: List[int] = [1, 2, 3]  # 1 = Highest priority

PRIORITY_COLORS: Dict[int, str] = {
    1: '#28a745',    # Green - High priority
    2: '#ffc107',    # Yellow - Medium priority
    3: '#fd7e14',    # Orange - Low priority
}

PRIORITY_LABELS: Dict[int, str] = {
    1: 'High Priority (Set 1)',
    2: 'Medium Priority (Set 2)',
    3: 'Low Priority (Set 3)',
}

# ========================================
# Recommendation Configuration
# ========================================

RECOMMENDATIONS: List[str] = [
    'PUSH FORWARD',
    'MONITOR',
    'REVIEW',
    'CONSIDER CANCELLATION'
]

RECOMMENDATION_COLORS: Dict[str, str] = {
    'PUSH FORWARD': '#28a745',             # Green
    'MONITOR': '#17a2b8',                  # Blue
    'REVIEW': '#ffc107',                   # Yellow
    'CONSIDER CANCELLATION': '#dc3545',   # Red
}

RECOMMENDATION_ICONS: Dict[str, str] = {
    'PUSH FORWARD': 'bi-arrow-up-circle-fill',
    'MONITOR': 'bi-eye-fill',
    'REVIEW': 'bi-exclamation-triangle-fill',
    'CONSIDER CANCELLATION': 'bi-x-circle-fill',
}

# ========================================
# Decision Types
# ========================================

DECISION_TYPES: List[str] = [
    'Status Change',
    'Priority Change',
    'Assignment Change',
    'Push Forward',
    'Hold',
    'Cancel',
    'Reactivate',
]

# ========================================
# Scoring Weights
# ========================================

SCORE_WEIGHTS: Dict[str, float] = {
    'priority': 0.40,      # 40% weight
    'on_time': 0.30,       # 30% weight
    'completion': 0.20,    # 20% weight
    'resource': 0.10,      # 10% weight
}

# Score thresholds for recommendations
SCORE_THRESHOLDS: Dict[str, float] = {
    'push_forward': 75.0,     # >= 75 = Push Forward
    'monitor': 50.0,          # 50-75 = Monitor
    'review': 30.0,           # 30-50 = Review
    # < 30 = Consider Cancellation
}

# ========================================
# Timeline Phase Configuration
# ========================================

PHASES: List[str] = ['Creation', 'Cloning', 'Purification', 'Complete']

PHASE_COLORS: Dict[str, str] = {
    'Creation': '#FF6B6B',
    'Cloning': '#4ECDC4',
    'Purification': '#45B7D1',
    'Complete': '#98D8C8',
}

# ========================================
# Application Settings
# ========================================

APP_TITLE: str = "Project Management Dashboard"
APP_NAME: str = "ProjectManagementApp"  # DjangoDash app name
DEBUG_MODE: bool = True

# ========================================
# Data Source Configuration
# ========================================

EXCEL_FILE_PATH: str = r"S:\Shared\DjangoRawData\ProjectManagement\PE_coformulation_production_forecast.xlsx"

# Excel column mappings
EXCEL_COLUMNS: Dict[str, str] = {
    'molecule_id': 'Molecule ID',
    'priority_set': 'Priority Set',
    'creation_date': 'Molecule Creation Date',
    'cloning_finish_date': 'Cloning Finish Date',
    'purification_finish_date': 'Finish Purification',
    'lead_time': 'Lead Time',
}

# ========================================
# Table Configuration
# ========================================

TABLE_PAGE_SIZE: int = 20
GANTT_CHART_HEIGHT: int = 800

# Table columns to display
TABLE_COLUMNS: List[Dict[str, str]] = [
    {'id': 'molecule_id', 'name': 'Molecule ID'},
    {'id': 'priority_set', 'name': 'Priority'},
    {'id': 'status', 'name': 'Status'},
    {'id': 'assigned_to', 'name': 'Assigned To'},
    {'id': 'creation_date', 'name': 'Creation Date'},
    {'id': 'cloning_finish_date', 'name': 'Cloning Finish'},
    {'id': 'purification_finish_date', 'name': 'Purification Finish'},
    {'id': 'lead_time', 'name': 'Lead Time (days)'},
    {'id': 'weighted_score', 'name': 'Score'},
    {'id': 'recommendation', 'name': 'Recommendation'},
]

# ========================================
# Chart Configuration
# ========================================

# Priority Matrix quadrant definitions
PRIORITY_MATRIX_QUADRANTS: Dict[str, Dict] = {
    'push_forward': {
        'label': 'Push Forward',
        'color': '#d4edda',
        'x_range': [0, 50],
        'y_range': [1, 1.5],
    },
    'monitor': {
        'label': 'Monitor',
        'color': '#d1ecf1',
        'x_range': [50, 100],
        'y_range': [1, 1.5],
    },
    'review': {
        'label': 'Review',
        'color': '#fff3cd',
        'x_range': [0, 50],
        'y_range': [1.5, 3],
    },
    'cancel': {
        'label': 'Consider Cancellation',
        'color': '#f8d7da',
        'x_range': [50, 100],
        'y_range': [1.5, 3],
    },
}

# ========================================
# Date Range Filters
# ========================================

DATE_FILTER_OPTIONS: List[Dict[str, str]] = [
    {'label': 'This Month', 'value': 'this_month'},
    {'label': 'Next Month', 'value': 'next_month'},
    {'label': 'This Quarter', 'value': 'this_quarter'},
    {'label': 'Next Quarter', 'value': 'next_quarter'},
    {'label': 'This Year', 'value': 'this_year'},
    {'label': 'All Time', 'value': 'all_time'},
]

# ========================================
# UI Theme Configuration
# ========================================

CARD_STYLE: Dict[str, str] = {
    'borderRadius': '10px',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
    'marginBottom': '20px',
}

BUTTON_STYLE: Dict[str, str] = {
    'borderRadius': '5px',
    'fontWeight': '500',
}

# ========================================
# Export Configuration
# ========================================

EXPORT_FILENAME_TEMPLATE: str = "project_management_export_{date}.xlsx"
EXPORT_SHEET_NAME: str = "Projects"
