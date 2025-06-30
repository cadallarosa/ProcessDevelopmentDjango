from urllib.parse import urlencode, quote
import json


def build_sec_report_url(sample_ids=None, report_id=None, mode="samples", hide_report_tab=True, embedded=True):
    """
    Build URL for SEC analysis with specific parameters

    Args:
        sample_ids (list): List of sample IDs to analyze
        report_id (int): Specific report to view
        mode (str): Analysis mode ('samples', 'report', 'create')
        hide_report_tab (bool): Hide the report selection tab
        embedded (bool): Use embedded app version (default: True)

    Returns:
        str: Complete SEC analysis URL
    """
    # ✅ UPDATED: Choose between embedded and full app
    if embedded:
        base_url = "/plotly_integration/dash-app/app/SecReportEmbeddedApp/"
    else:
        base_url = "/plotly_integration/dash-app/app/SecReportApp2/"

    params = {}

    if report_id:
        params["report_id"] = str(report_id)
    if sample_ids:
        if isinstance(sample_ids, list):
            params["samples"] = ",".join(str(sid) for sid in sample_ids)
        else:
            params["samples"] = str(sample_ids)
    if mode:
        params["mode"] = mode
    if hide_report_tab:
        params["hide_report_tab"] = "true"

    if params:
        return f"{base_url}?{urlencode(params)}"
    return base_url


def build_sec_embedded_url(report_id=None, **params):
    """
    Build URL specifically for the embedded SEC app

    Args:
        report_id (str): Report ID to display
        **params: Additional parameters

    Returns:
        str: Complete embedded SEC URL
    """
    base_url = "/plotly_integration/dash-app/app/SecReportEmbeddedApp/"

    if report_id:
        params['report_id'] = report_id

    if params:
        return f"{base_url}?{urlencode(params)}"
    return base_url


def build_sec_full_url(report_id=None, **params):
    """
    Build URL specifically for the full SEC app

    Args:
        report_id (str): Report ID to display
        **params: Additional parameters

    Returns:
        str: Complete full SEC URL
    """
    base_url = "/plotly_integration/dash-app/app/SecReportApp2/"

    if report_id:
        params['report_id'] = report_id

    if params:
        return f"{base_url}?{urlencode(params)}"
    return base_url


def build_sample_set_url(project, sip_number=None, development_stage=None):
    """
    Build URL for sample set view

    Args:
        project (str): Project identifier
        sip_number (str): SIP number (optional)
        development_stage (str): Development stage (optional)

    Returns:
        str: Sample set view URL
    """
    params = {'project': project}

    if sip_number:
        params['sip'] = sip_number
    if development_stage:
        params['stage'] = development_stage

    return f"/sample-sets/view?{urlencode(params)}"


def build_analysis_request_url(analysis_type, sample_set_id=None, request_id=None):
    """
    Build URL for analysis request management

    Args:
        analysis_type (str): Type of analysis (SEC, TITER, etc.)
        sample_set_id (int): Sample set ID (optional)
        request_id (int): Analysis request ID (optional)

    Returns:
        str: Analysis request URL
    """
    base_path = f"/analysis/{analysis_type.lower()}"
    params = {}

    if sample_set_id:
        params['sample_set_id'] = str(sample_set_id)
    if request_id:
        params['request_id'] = str(request_id)

    if params:
        return f"{base_path}?{urlencode(params)}"
    return base_path


def encode_sample_set_data(project, sip_number, development_stage, sample_ids):
    """
    Encode sample set data for URL transmission

    Args:
        project (str): Project name
        sip_number (str): SIP number
        development_stage (str): Development stage
        sample_ids (list): List of sample IDs

    Returns:
        str: URL-encoded sample set data
    """
    sample_set_data = {
        "project": project,
        "sip": sip_number,
        "development_stage": development_stage,
        "sample_ids": sample_ids
    }

    return quote(json.dumps(sample_set_data))


def decode_sample_set_data(encoded_data):
    """
    Decode sample set data from URL

    Args:
        encoded_data (str): URL-encoded sample set data

    Returns:
        dict: Decoded sample set data
    """
    try:
        return json.loads(encoded_data)
    except (json.JSONDecodeError, TypeError):
        return {}


def build_dashboard_url(page_name, **params):
    """
    Build internal dashboard URLs

    Args:
        page_name (str): Name of the dashboard page
        **params: Additional URL parameters

    Returns:
        str: Dashboard page URL
    """
    page_routes = {
        'home': '/',
        'samples_view': '/samples/view',
        'samples_create': '/samples/create',
        'sample_sets': '/sample-sets',
        'sample_sets_table': '/sample-sets/table',
        'sec_dashboard': '/analysis/sec',
        'sec_reports': '/analysis/sec/reports',
        'settings': '/settings'
    }

    base_url = page_routes.get(page_name, '/')

    if params:
        return f"{base_url}?{urlencode(params)}"
    return base_url


def extract_url_params(search_string):
    """
    Extract parameters from URL search string

    Args:
        search_string (str): URL search string (e.g., "?param1=value1&param2=value2")

    Returns:
        dict: Dictionary of URL parameters
    """
    if not search_string:
        return {}

    # Remove leading '?' if present
    if search_string.startswith('?'):
        search_string = search_string[1:]

    params = {}
    for param_pair in search_string.split('&'):
        if '=' in param_pair:
            key, value = param_pair.split('=', 1)
            params[key] = value

    return params


def build_akta_report_url(sample_ids=None, embed=True):
    """
    Build URL for AKTA analysis with specific parameters

    Args:
        sample_ids (list): List of sample IDs to analyze (FB numbers)
        embed (bool): Whether to show in embedded mode

    Returns:
        str: Complete AKTA analysis URL
    """
    base_url = "/plotly_integration/dash-app/app/AktaChromatogramApp/"
    params = {}

    if sample_ids:
        if isinstance(sample_ids, list):
            # Convert FB1598 to 1598 if needed, or keep as is
            clean_ids = []
            for sid in sample_ids:
                if str(sid).startswith('FB'):
                    clean_ids.append(str(sid)[2:])  # Remove 'FB' prefix
                else:
                    clean_ids.append(str(sid))
            params["fb"] = ",".join(clean_ids)
        else:
            # Single sample
            if str(sample_ids).startswith('FB'):
                params["fb"] = str(sample_ids)[2:]
            else:
                params["fb"] = str(sample_ids)

    if embed:
        params["embed"] = "true"

    if params:
        return f"{base_url}?{urlencode(params)}"
    return base_url