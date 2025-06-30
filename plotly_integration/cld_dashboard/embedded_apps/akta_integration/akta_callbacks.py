from dash import Input, Output, callback, no_update
from plotly_integration.cld_dashboard.main_app import app


@app.callback(
    Output("akta-analysis-status", "children"),
    Input("url", "pathname")
)
def update_akta_analysis_status(pathname):
    """Update AKTA analysis status indicators"""
    if not pathname.startswith("/analysis/akta"):
        return no_update
    return "AKTA status updated"


print("✅ AKTA integration callbacks registered successfully")


# Fix 3: Create a simple test to check if AKTA URL building works
# Add this function to your url_helpers.py file (if it's missing):

def build_akta_report_url(sample_ids=None, embed=True):
    """
    Build URL for AKTA analysis with specific parameters

    Args:
        sample_ids (list): List of sample IDs to analyze (FB numbers)
        embed (bool): Whether to show in embedded mode

    Returns:
        str: Complete AKTA analysis URL
    """
    from urllib.parse import urlencode

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