from dash import html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs

# Try to import the URL builder, with fallback
try:
    from ...shared.utils.url_helpers import build_akta_report_url
except ImportError:
    print("Warning: Could not import build_akta_report_url, using fallback")


    def build_akta_report_url(sample_ids=None, embed=True):
        from urllib.parse import urlencode
        base_url = "/plotly_integration/dash-app/app/AktaChromatogramApp/"
        params = {}
        if sample_ids:
            if isinstance(sample_ids, list):
                clean_ids = []
                for sid in sample_ids:
                    if str(sid).startswith('FB'):
                        clean_ids.append(str(sid)[2:])
                    else:
                        clean_ids.append(str(sid))
                params["fb"] = ",".join(clean_ids)
            else:
                # Single sample ID
                if str(sample_ids).startswith('FB'):
                    params["fb"] = str(sample_ids)[2:]
                else:
                    params["fb"] = str(sample_ids)
        if embed:
            params["embed"] = "true"
        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url

try:
    from ...shared.components.embedded_iframe import create_embedded_iframe, create_loading_iframe, create_error_iframe
except ImportError:
    print("Warning: Could not import iframe components, using fallback")


    def create_embedded_iframe(src_url, title="Embedded App", height="900px", show_controls=True):
        return dbc.Card([
            dbc.CardHeader([
                html.H5(title),
                html.A("Open in New Tab", href=src_url, target="_blank",
                       className="btn btn-outline-primary btn-sm float-end")
            ]) if show_controls else None,
            dbc.CardBody([
                html.Iframe(
                    src=src_url,
                    style={"width": "100%", "height": height, "border": "none"}
                )
            ], style={"padding": "0"})
        ], className="shadow")


    def create_error_iframe(error_msg, height="900px"):
        return dbc.Alert([
            html.H5("Error Loading AKTA App"),
            html.P(error_msg)
        ], color="danger")

from plotly_integration.cld_dashboard.main_app import app


def create_embedded_akta_report(query_params):
    """
    Create embedded AKTA report layout with parameters - CLEAN VERSION
    """
    print(f"🔍 AKTA embedder called with query_params: {query_params}")

    # Extract parameters - but don't show debug info to user
    sample_ids = []
    if 'fb' in query_params:
        fb_param = query_params['fb'][0] if isinstance(query_params['fb'], list) else query_params['fb']
        sample_ids = fb_param.split(',') if fb_param else []

    # Clean up sample IDs
    sample_ids = [sid.strip() for sid in sample_ids if sid.strip()]

    print(f"🔍 Extracted sample_ids: {sample_ids}")

    return dbc.Container([
        # ✅ MINIMAL header - no title, just navigation
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-1"),
                        "Back"
                    ], href="#!/sample-sets", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-external-link-alt me-1"),
                        "Open in New Tab"
                    ], id="open-akta-new-tab", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-akta-report", color="outline-info", size="sm")
                ], className="float-end")
            ])
        ], className="mb-3"),

        # ✅ NO sample information banner
        # ✅ NO debug info

        # Embedded AKTA Application - Full height iframe
        dbc.Row([
            dbc.Col([
                html.Div(id="akta-embed-container")
            ])
        ], style={"flex": "1", "minHeight": "0"})  # Take remaining space

    ], fluid=True, style={
        "padding": "20px",
        "height": "100vh",  # Full viewport height
        "overflow": "visible",  # No container scrolling
        "display": "flex",
        "flexDirection": "column"
    })


# ✅ UPDATED callback to use minimal iframe with no extra headers
@app.callback(
    [Output("akta-embed-container", "children"),
     Output("open-akta-new-tab", "href")],
    [Input("url", "href"),
     Input("refresh-akta-report", "n_clicks")],
    prevent_initial_call=False
)
def load_akta_embed(href, refresh_clicks):
    """Load the embedded AKTA application with parameters - CLEAN VERSION"""
    print(f"🔍 AKTA embed callback triggered - href: {href}")

    if not href:
        return html.Div(), ""

    # Parse pathname directly from href
    parsed_pathname = "/"
    if '#!' in href:
        try:
            hash_part = href.split('#!')[1]
            if hash_part:
                pathname = hash_part.split('?')[0]
                parsed_pathname = '/' + pathname.lstrip('/')
        except Exception as e:
            print(f"   ❌ Error parsing href: {e}")
            return html.Div(), ""

    print(f"   parsed_pathname: {parsed_pathname}")

    if not parsed_pathname.startswith("/analysis/akta/report"):
        print(f"   ❌ Wrong pathname")
        return html.Div(), ""

    try:
        # Extract query params
        sample_ids = []
        if href and '#!' in href and '?' in href:
            hash_part = href.split('#!')[1]
            if '?' in hash_part:
                search = '?' + hash_part.split('?')[1]
                query_params = parse_qs(search.lstrip('?'))
                print(f"   📋 Parsed query_params: {query_params}")

                if 'fb' in query_params:
                    fb_param = query_params['fb'][0] if isinstance(query_params['fb'], list) else query_params['fb']
                    sample_ids = fb_param.split(',') if fb_param else []

        # Clean up sample IDs
        sample_ids = [sid.strip() for sid in sample_ids if sid.strip()]
        print(f"   🎯 Final sample_ids: {sample_ids}")

        # Build AKTA report URL
        akta_url = build_akta_report_url(
            sample_ids=sample_ids,
            embed=True
        )

        print(f"   🔗 Generated AKTA URL: {akta_url}")

        # ✅ Create MINIMAL iframe with NO scrollable container
        iframe_component = html.Div([
            html.Iframe(
                src=akta_url,
                style={
                    "width": "100%",
                    "height": "calc(100vh - 120px)",  # Full viewport height minus header space
                    "border": "none",
                    "borderRadius": "5px",
                    "overflow": "visible"  # Let content overflow naturally
                }
            )
        ], style={
            "width": "100%",
            "overflow": "visible",  # No container scrolling
            "height": "auto"
        })

        print(f"   ✅ Clean iframe created successfully")
        return iframe_component, akta_url

    except Exception as e:
        error_msg = f"Failed to load AKTA application: {str(e)}"
        print(f"   ❌ Error: {error_msg}")
        return create_error_iframe(error_msg), ""