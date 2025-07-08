# plotly_integration/pd_dashboard/home/cld/sample_sets/callbacks/app_integration.py
# Callbacks for integrating SEC and AKTA apps from sample set details

from dash import callback, Input, Output, State, clientside_callback, ClientsideFunction
import dash_bootstrap_components as dbc
from dash import html
from urllib.parse import urlencode

from plotly_integration.pd_dashboard.main_app import app
from plotly_integration.models import LimsSampleSet


@app.callback(
    Output("app-integration-notifications", "children"),
    [
        Input("open-sec-app-btn", "n_clicks"),
        Input("open-akta-app-btn", "n_clicks"),
    ],
    [State("current-sample-set-id", "data")],
    prevent_initial_call=True
)
def handle_app_integrations(sec_clicks, akta_clicks, sample_set_id):
    """Handle opening SEC and AKTA apps with sample set data"""

    if not sample_set_id:
        return dbc.Toast([
            html.P("No sample set selected")
        ], header="Error", color="danger", is_open=True, dismissable=True)

    try:
        # Get sample set details
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        member_samples = sample_set.members.all()
        sample_ids = [member.sample.sample_id for member in member_samples]

        if not sample_ids:
            return dbc.Toast([
                html.P("No samples found in this sample set")
            ], header="Error", color="warning", is_open=True, dismissable=True)

        # Determine which button was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_id == "open-sec-app-btn":
            # Build SEC app URL
            sec_url = build_sec_app_url(sample_ids, sample_set.set_name)
            return create_app_opened_notification("SEC", sec_url, len(sample_ids))

        elif triggered_id == "open-akta-app-btn":
            # Build AKTA app URL
            akta_url = build_akta_app_url(sample_ids, sample_set.set_name)
            return create_app_opened_notification("AKTA", akta_url, len(sample_ids))

        return dash.no_update

    except Exception as e:
        return dbc.Toast([
            html.P(f"Error: {str(e)}")
        ], header="App Integration Error", color="danger", is_open=True, dismissable=True)


def build_sec_app_url(sample_ids, set_name=""):
    """Build URL for SEC app with sample parameters"""
    base_url = "/plotly_integration/dash-app/app/SecReportEmbeddedApp/"

    # For SEC, we can pass sample IDs or report parameters
    # Check if there are existing SEC reports for these samples
    params = {}

    # Option 1: Pass sample list (if SEC app supports it)
    if len(sample_ids) == 1:
        params['sample_id'] = sample_ids[0]
    else:
        params['samples'] = ','.join(sample_ids)

    # Option 2: Add metadata
    if set_name:
        params['set_name'] = set_name

    params['embedded'] = 'true'

    if params:
        return f"{base_url}?{urlencode(params)}"
    return base_url


def build_akta_app_url(sample_ids, set_name=""):
    """Build URL for AKTA app with sample parameters"""
    base_url = "/plotly_integration/dash-app/app/AktaChromatogramApp/"

    # Clean FB sample IDs for AKTA (remove FB prefix)
    clean_fb_numbers = []
    for sample_id in sample_ids:
        if str(sample_id).startswith('FB'):
            clean_fb_numbers.append(str(sample_id)[2:])  # Remove FB prefix
        else:
            clean_fb_numbers.append(str(sample_id))

    params = {
        'fb': ','.join(clean_fb_numbers),
        'embed': 'true'
    }

    if set_name:
        params['set_name'] = set_name

    return f"{base_url}?{urlencode(params)}"


def create_app_opened_notification(app_name, app_url, sample_count):
    """Create notification when app is opened"""
    return dbc.Toast([
        html.Div([
            html.P([
                html.I(className="fas fa-external-link-alt me-2"),
                f"{app_name} app will open with {sample_count} samples"
            ]),
            html.A(
                "Click here if app doesn't open automatically",
                href=app_url,
                target="_blank",
                className="btn btn-outline-primary btn-sm"
            )
        ])
    ],
        header=f"{app_name} App Opening",
        color="success",
        is_open=True,
        dismissable=True,
        duration=5000
    )


# JavaScript function to open apps in new window/tab
app.clientside_callback(
    """
    function(sec_clicks, akta_clicks, sample_set_id) {
        // This runs in the browser
        if (!sample_set_id) return;

        // Get the triggered component
        const triggered = dash_clientside.callback_context.triggered;
        if (!triggered || triggered.length === 0) return;

        const triggeredId = triggered[0].prop_id.split('.')[0];

        if (triggeredId === "open-sec-app-btn" && sec_clicks) {
            // We'll let the server-side callback handle URL building
            // Then we can open it via a separate mechanism
            return window.dash_clientside.no_update;
        }

        if (triggeredId === "open-akta-app-btn" && akta_clicks) {
            // Same for AKTA
            return window.dash_clientside.no_update;
        }

        return window.dash_clientside.no_update;
    }
    """,
    Output("clientside-dummy", "children"),  # Dummy output
    [
        Input("open-sec-app-btn", "n_clicks"),
        Input("open-akta-app-btn", "n_clicks"),
    ],
    [State("current-sample-set-id", "data")]
)


# Enhanced callback that also opens apps in new tab
@app.callback(
    [
        Output("open-sec-app-btn", "href"),
        Output("open-akta-app-btn", "href"),
        Output("open-sec-app-btn", "target"),
        Output("open-akta-app-btn", "target")
    ],
    [Input("current-sample-set-id", "data")]
)
def update_app_button_links(sample_set_id):
    """Update app button hrefs so they can open in new tabs"""

    if not sample_set_id:
        return "", "", "", ""

    try:
        # Get sample set details
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        member_samples = sample_set.members.all()
        sample_ids = [member.sample.sample_id for member in member_samples]

        if not sample_ids:
            return "", "", "", ""

        # Build URLs
        sec_url = build_sec_app_url(sample_ids, sample_set.set_name)
        akta_url = build_akta_app_url(sample_ids, sample_set.set_name)

        return sec_url, akta_url, "_blank", "_blank"

    except Exception as e:
        print(f"Error building app URLs: {e}")
        return "", "", "", ""


# Request analysis callback
@app.callback(
    Output("analysis-request-notifications", "children"),
    [
        Input("request-sec-btn", "n_clicks"),
        Input("request-akta-btn", "n_clicks"),
        Input("request-titer-btn", "n_clicks"),
        Input("request-ce_sds-btn", "n_clicks"),
        Input("request-cief-btn", "n_clicks"),
        Input("request-mass_check-btn", "n_clicks"),
        Input("request-glycan-btn", "n_clicks"),
        Input("request-hcp-btn", "n_clicks"),
        Input("request-proa-btn", "n_clicks"),
    ],
    [State("current-sample-set-id", "data")],
    prevent_initial_call=True
)
def handle_analysis_requests(*args):
    """Handle requests for various analysis types"""

    sample_set_id = args[-1]  # Last argument is the State

    if not sample_set_id:
        return dbc.Toast([
            html.P("No sample set selected")
        ], header="Error", color="danger", is_open=True, dismissable=True)

    # Determine which analysis was requested
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Extract analysis type from button ID
    analysis_type = triggered_id.replace('request-', '').replace('-btn', '').replace('_', '-').upper()

    try:
        # Create analysis request
        from plotly_integration.models import LimsAnalysisRequest
        from datetime import datetime

        sample_set = LimsSampleSet.objects.get(id=sample_set_id)

        # Check if request already exists
        existing_request = LimsAnalysisRequest.objects.filter(
            sample_set=sample_set,
            analysis_type=analysis_type
        ).first()

        if existing_request:
            return dbc.Toast([
                html.P(f"{analysis_type} analysis already requested for this sample set")
            ], header="Already Requested", color="warning", is_open=True, dismissable=True)

        # Create new request
        new_request = LimsAnalysisRequest.objects.create(
            sample_set=sample_set,
            analysis_type=analysis_type,
            requested_by='dashboard_user',  # TODO: Get actual user
            requested_at=datetime.now(),
            status='requested',
            priority=1
        )

        return dbc.Toast([
            html.P([
                html.I(className="fas fa-check me-2"),
                f"{analysis_type} analysis requested successfully"
            ])
        ], header="Analysis Requested", color="success", is_open=True, dismissable=True, duration=3000)

    except Exception as e:
        return dbc.Toast([
            html.P(f"Error requesting {analysis_type} analysis: {str(e)}")
        ], header="Request Failed", color="danger", is_open=True, dismissable=True)


print("App integration callbacks loaded")