# SEC embedder component - UPDATED for SecReportEmbeddedApp

from dash import html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs
from ...shared.components.embedded_iframe import create_embedded_iframe, create_loading_iframe, create_error_iframe
from plotly_integration.cld_dashboard.main_app import app


@app.callback(
    [Output("sec-embed-container", "children"),
     Output("open-sec-new-tab", "href")],
    [Input("url", "href"),  # Use href to get full URL with parameters
     Input("refresh-sec-report", "n_clicks")],
    [State("parsed-pathname", "data")]
)
def load_sec_embed(href, refresh_clicks, pathname):
    """Load the embedded SEC application with parameters"""
    print(f"🔄 SEC Embed Callback - pathname: {pathname}, href: {href}")

    if not pathname or not pathname.startswith("/analysis/sec/report"):
        return no_update, no_update

    try:
        # Extract query params from hash URL
        query_params = {}
        if href and '#!' in href and '?' in href:
            hash_part = href.split('#!')[1]
            if '?' in hash_part:
                search = '?' + hash_part.split('?')[1]
                query_params = parse_qs(search.lstrip('?'))

        report_id = query_params.get('report_id', [''])[0] if query_params.get('report_id') else ''

        print(f"📊 Building SEC URL - Report ID: {report_id}")

        # ✅ UPDATED: Use the SecReportEmbeddedApp URL
        base_sec_url = "/plotly_integration/dash-app/app/SecReportEmbeddedApp/"

        if report_id:
            sec_url = f"{base_sec_url}?report_id={report_id}"
        else:
            # Default to a test report ID if none provided
            sec_url = f"{base_sec_url}?report_id=320"

        print(f"✅ SEC URL: {sec_url}")

        # Create embedded iframe
        iframe_component = create_embedded_iframe(
            src_url=sec_url,
            title="SEC Analysis Report",
            height="900px",
            show_controls=True
        )

        return iframe_component, sec_url

    except Exception as e:
        print(f"❌ Error in load_sec_embed: {e}")
        import traceback
        traceback.print_exc()

        error_msg = f"Failed to load SEC application: {str(e)}"
        return create_error_iframe(error_msg), ""


# Keep the main layout function simple
def create_embedded_sec_report(query_params):
    """
    Create embedded SEC report layout with parameters
    """
    print(f"🔍 SEC EMBEDDER - create_embedded_sec_report called")
    print(f"   Query params received: {query_params}")

    # Extract parameters
    report_id = query_params.get('report_id', [''])[0] if query_params else ''
    print(f"   Extracted report_id: {report_id}")

    return dbc.Container([
        # Debug info at top (can remove in production)
        dbc.Alert([
            html.H6("SEC Report Debug Info:"),
            html.P(f"Query Params: {query_params}"),
            html.P(f"Report ID: {report_id}"),
            html.P(f"Will load: /plotly_integration/dash-app/app/SecReportEmbeddedApp/?report_id={report_id or '320'}")
        ], color="info", dismissable=True, id="debug-alert"),

        # Minimal header with just navigation
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-1"),
                        "Back"
                    ], href="#!/analysis/sec", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-external-link-alt me-1"),
                        "Open in New Tab"
                    ], id="open-sec-new-tab", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-sec-report", color="outline-info", size="sm")
                ], className="float-end")
            ])
        ], className="mb-3"),

        # Embedded SEC Application
        dbc.Row([
            dbc.Col([
                html.Div(id="sec-embed-container", children=[
                    create_loading_iframe("Loading SEC Application...", "900px")
                ])
            ])
        ])

    ], fluid=True, style={"padding": "20px"})