# External application URLs and configurations

EXTERNAL_APPS = {
    "sec_report": {
        "url": "/plotly_integration/dash-app/app/SecReportApp2/",
        "name": "SEC Analysis",
        "supports_embedding": True,
        "parameters": ["samples", "report_id", "mode", "hide_report_tab"],
        "file_location": "plotly_integration/process_development/downstream_processing/empower/sec_report_app/",
        "description": "Size Exclusion Chromatography analysis and reporting"
    },
    "database_manager": {
        "url": "/plotly_integration/dash-app/app/DatabaseManagerApp/",
        "name": "Database Manager",
        "supports_embedding": False,
        "parameters": [],
        "file_location": "plotly_integration/database_manager/",
        "description": "Database import and management tools"
    },
    "report_creator": {
        "url": "/plotly_integration/dash-app/app/ReportApp/",
        "name": "Report Creator",
        "supports_embedding": False,
        "parameters": [],
        "file_location": "plotly_integration/report_creator/",
        "description": "General report creation and management"
    },
    "dn_assignment": {
        "url": "/plotly_integration/dash-app/app/DnAssignmentApp/",
        "name": "DN Assignment",
        "supports_embedding": False,
        "parameters": [],
        "file_location": "plotly_integration/dn_assignment/",
        "description": "Downstream experiment assignment management"
    }
}

# Internal routes for the dashboard
INTERNAL_ROUTES = {
    "dashboard_home": "/",
    "sample_sets_view": "/sample-sets",
    "sample_sets_table": "/sample-sets/table",
    "sample_sets_analytics": "/sample-sets/analytics",
    "samples_view": "/samples/view",
    "samples_create": "/samples/create",
    "sec_dashboard": "/analysis/sec",
    "sec_sample_sets": "/analysis/sec/sample-sets",
    "sec_reports": "/analysis/sec/reports",
    "sec_embed": "/analysis/sec/report",
    "settings": "/settings",
    "help": "/help",
    "about": "/about"
}

# API endpoints for data integration
API_ENDPOINTS = {
    "sec_results": "/api/sec-results/",
    "sample_analysis": "/api/sample-analysis/",
    "reports": "/api/reports/",
    "samples": "/api/samples/",
    "sample_sets": "/api/sample-sets/",
    "analysis_status": "/api/analysis-status/",
    "analysis_requests": "/api/analysis-requests/"
}


def get_app_url(app_name: str, **params) -> str:
    """
    Get URL for an external application with parameters

    Args:
        app_name (str): Application name from EXTERNAL_APPS
        **params: Parameters to append to URL

    Returns:
        str: Complete application URL
    """
    app_config = EXTERNAL_APPS.get(app_name, {})
    base_url = app_config.get("url", "")

    if not base_url:
        return ""

    # Filter parameters to only supported ones
    supported_params = app_config.get("parameters", [])
    filtered_params = {k: v for k, v in params.items() if k in supported_params}

    if filtered_params:
        from urllib.parse import urlencode
        query_string = urlencode(filtered_params)
        return f"{base_url}?{query_string}"

    return base_url


def get_internal_route(route_name: str) -> str:
    """
    Get internal dashboard route

    Args:
        route_name (str): Route name from INTERNAL_ROUTES

    Returns:
        str: Internal route path
    """
    return INTERNAL_ROUTES.get(route_name, "/")


def get_api_url(endpoint_name: str, resource_id: str = None) -> str:
    """
    Get API endpoint URL

    Args:
        endpoint_name (str): Name of the API endpoint
        resource_id (str): Optional resource ID

    Returns:
        str: Complete API URL
    """
    base_url = API_ENDPOINTS.get(endpoint_name, "")

    if resource_id:
        return f"{base_url}{resource_id}/"

    return base_url


def get_apps_by_category(category: str = None) -> dict:
    """
    Get applications filtered by category or embedding support

    Args:
        category (str): Filter by category or 'embeddable' for embedding support

    Returns:
        dict: Filtered applications
    """
    if category == "embeddable":
        return {
            name: config for name, config in EXTERNAL_APPS.items()
            if config.get("supports_embedding", False)
        }

    # For future: add category field to EXTERNAL_APPS if needed
    return EXTERNAL_APPS


def validate_app_parameters(app_name: str, **params) -> dict:
    """
    Validate parameters for an application

    Args:
        app_name (str): Application name
        **params: Parameters to validate

    Returns:
        dict: Valid parameters only
    """
    app_config = EXTERNAL_APPS.get(app_name, {})
    supported_params = app_config.get("parameters", [])

    return {k: v for k, v in params.items() if k in supported_params}


def get_navigation_links():
    """
    Get navigation links for the dashboard

    Returns:
        dict: Navigation structure for sidebar
    """
    return {
        "main": [
            {"name": "Dashboard", "url": INTERNAL_ROUTES["dashboard_home"], "icon": "fa-tachometer-alt"},
        ],
        "samples": [
            {"name": "View All Samples", "url": INTERNAL_ROUTES["samples_view"], "icon": "fa-vial"},
            {"name": "Sample Sets", "url": INTERNAL_ROUTES["sample_sets_view"], "icon": "fa-layer-group"},
            {"name": "Add Samples", "url": INTERNAL_ROUTES["samples_create"], "icon": "fa-plus"},
        ],
        "sec_analytics": [
            {"name": "SEC Overview", "url": INTERNAL_ROUTES["sec_dashboard"], "icon": "fa-chart-bar"},
            {"name": "SEC Sample Sets", "url": INTERNAL_ROUTES["sec_sample_sets"], "icon": "fa-microscope"},
            {"name": "SEC Reports", "url": INTERNAL_ROUTES["sec_reports"], "icon": "fa-chart-line"},
        ],
        "external_apps": [
            {"name": "Database Manager", "url": get_app_url("database_manager"), "icon": "fa-database"},
            {"name": "Report Creator", "url": get_app_url("report_creator"), "icon": "fa-file-alt"},
            {"name": "DN Assignment", "url": get_app_url("dn_assignment"), "icon": "fa-tasks"},
        ],
        "system": [
            {"name": "Settings", "url": INTERNAL_ROUTES["settings"], "icon": "fa-cogs"},
            {"name": "Help", "url": INTERNAL_ROUTES["help"], "icon": "fa-question-circle"},
        ]
    }