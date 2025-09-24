# Analysis type constants and configurations - UPDATED for SecReportEmbeddedApp

ANALYSIS_TYPES = {
    'SEC': {
        'name': 'Size Exclusion Chromatography',
        'code': 'SEC',
        'app_name': 'SecReportEmbeddedApp',  # ✅ UPDATED: Changed from SecReportApp2
        'app_name_full': 'SecReportApp2',  # ✅ NEW: Keep original for full-screen access
        'icon': 'fa-microscope',
        'color': 'primary',
        'description': 'Protein size and aggregation analysis',
        'data_table': 'sec_metadata',
        'supports_embedding': True,
        'typical_turnaround': '2-3 days',
        'embedded_url': '/plotly_integration/dash-app/app/SecReportEmbeddedApp/',  # ✅ NEW
        'full_url': '/plotly_integration/dash-app/app/SecReportApp2/'  # ✅ NEW
    },
    'TITER': {
        'name': 'Titer Analysis',
        'code': 'TITER',
        'app_name': 'TiterReportApp',
        'icon': 'fa-flask',
        'color': 'success',
        'description': 'Protein concentration measurement',
        'data_table': 'titer_metadata',
        'supports_embedding': True,
        'typical_turnaround': '1-2 days'
    },
    'AKTA': {
        'name': 'AKTA Analysis',
        'code': 'AKTA',
        'app_name': 'AktaChromatogramApp',
        'icon': 'fa-chart-area',
        'color': 'info',
        'description': 'Chromatography purification analysis',
        'data_table': 'akta_metadata',
        'supports_embedding': True,
        'typical_turnaround': '1 day'
    },
    'CE_SDS': {
        'name': 'CE-SDS Analysis',
        'code': 'CE_SDS',
        'app_name': 'CESDSReportApp',
        'icon': 'fa-chart-line',
        'color': 'warning',
        'description': 'Capillary electrophoresis purity analysis',
        'data_table': 'ce_sds_metadata',
        'supports_embedding': True,
        'typical_turnaround': '2-3 days'
    },
    'CIEF': {
        'name': 'cIEF Analysis',
        'code': 'CIEF',
        'app_name': 'CIEFReportApp',
        'icon': 'fa-wave-square',
        'color': 'danger',
        'description': 'Isoelectric focusing charge analysis',
        'data_table': 'cief_metadata',
        'supports_embedding': True,
        'typical_turnaround': '2-3 days'
    }
}

# Status configurations
STATUS_COLORS = {
    'REQUESTED': 'warning',
    'DATA_AVAILABLE': 'info',
    'REPORT_CREATED': 'success',
    'COMPLETED': 'success',
    'ERROR': 'danger',
    'PENDING': 'secondary',
    'CANCELLED': 'dark'
}

STATUS_ICONS = {
    'REQUESTED': 'fa-clock',
    'DATA_AVAILABLE': 'fa-database',
    'REPORT_CREATED': 'fa-file-alt',
    'COMPLETED': 'fa-check-circle',
    'ERROR': 'fa-exclamation-triangle',
    'PENDING': 'fa-hourglass-half',
    'CANCELLED': 'fa-times-circle'
}

STATUS_DESCRIPTIONS = {
    'REQUESTED': 'Analysis has been requested',
    'DATA_AVAILABLE': 'Sample data is available for analysis',
    'REPORT_CREATED': 'Analysis report has been generated',
    'COMPLETED': 'Analysis is complete and reviewed',
    'ERROR': 'Error occurred during analysis',
    'PENDING': 'Waiting for sample or data',
    'CANCELLED': 'Analysis request was cancelled'
}

# Priority levels for analysis requests
PRIORITY_LEVELS = {
    'LOW': {
        'name': 'Low Priority',
        'color': 'secondary',
        'icon': 'fa-arrow-down',
        'order': 3
    },
    'NORMAL': {
        'name': 'Normal Priority',
        'color': 'primary',
        'icon': 'fa-minus',
        'order': 2
    },
    'HIGH': {
        'name': 'High Priority',
        'color': 'warning',
        'icon': 'fa-arrow-up',
        'order': 1
    },
    'URGENT': {
        'name': 'Urgent',
        'color': 'danger',
        'icon': 'fa-exclamation',
        'order': 0
    }
}

# Sample type configurations
SAMPLE_TYPES = {
    'FB': {
        'name': 'Fed-Batch',
        'code': 'FB',
        'icon': 'fa-flask',
        'color': 'primary',
        'description': 'Cell line development samples'
    },
    'UP': {
        'name': 'Upstream',
        'code': 'UP',
        'icon': 'fa-arrow-up',
        'color': 'success',
        'description': 'Upstream process samples'
    },
    'PD': {
        'name': 'Process Development',
        'code': 'PD',
        'icon': 'fa-cogs',
        'color': 'info',
        'description': 'Process development samples'
    }
}


def get_analysis_config(analysis_type):
    """
    Get configuration for a specific analysis type

    Args:
        analysis_type (str): Analysis type code

    Returns:
        dict: Analysis configuration or None if not found
    """
    return ANALYSIS_TYPES.get(analysis_type.upper())


def get_sec_embedded_url(report_id=None):
    """
    Get the embedded SEC URL with optional report ID

    Args:
        report_id (str): Optional report ID

    Returns:
        str: SEC embedded URL
    """
    base_url = ANALYSIS_TYPES['SEC']['embedded_url']
    if report_id:
        return f"{base_url}?report_id={report_id}"
    return base_url


def get_sec_full_url(report_id=None):
    """
    Get the full SEC URL with optional report ID

    Args:
        report_id (str): Optional report ID

    Returns:
        str: SEC full URL
    """
    base_url = ANALYSIS_TYPES['SEC']['full_url']
    if report_id:
        return f"{base_url}?report_id={report_id}"
    return base_url


def get_status_badge_props(status):
    """
    Get badge properties for a status

    Args:
        status (str): Status code

    Returns:
        dict: Badge properties (color, icon, description)
    """
    return {
        'color': STATUS_COLORS.get(status, 'secondary'),
        'icon': STATUS_ICONS.get(status, 'fa-question'),
        'description': STATUS_DESCRIPTIONS.get(status, 'Unknown status')
    }


def get_available_analysis_types():
    """
    Get list of available analysis types

    Returns:
        list: List of analysis type configurations
    """
    return list(ANALYSIS_TYPES.values())


def supports_embedding(analysis_type):
    """
    Check if analysis type supports embedding

    Args:
        analysis_type (str): Analysis type code

    Returns:
        bool: True if embedding is supported
    """
    config = get_analysis_config(analysis_type)
    return config.get('supports_embedding', False) if config else False