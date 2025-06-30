import dash
from dash import Input, Output, State, html
from urllib.parse import parse_qs
from plotly_integration.models import Report
from ..app import app


@app.callback(
    [Output("selected-report", "data"),
     Output('loading-overlay', 'style')],
    [Input("url", "search")],
    prevent_initial_call=False
)
def load_report_from_url(search):
    """
    Load report automatically from URL parameters in embedded mode
    Expected URL format: /sec-embedded/?report_id=123
    """

    if not search:
        print("❌ No URL search parameters found")
        # Show loading overlay if no params
        return dash.no_update, {
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'right': 0,
            'bottom': 0,
            'backgroundColor': 'rgba(255,255,255,0.9)',
            'zIndex': 9999,
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center'
        }

    try:
        # Parse URL parameters
        params = parse_qs(search.lstrip("?"))
        report_id = params.get('report_id', [None])[0]

        if not report_id:
            print("❌ No report_id found in URL parameters")
            return dash.no_update, {
                'position': 'fixed',
                'top': 0,
                'left': 0,
                'right': 0,
                'bottom': 0,
                'backgroundColor': 'rgba(255,255,255,0.9)',
                'zIndex': 9999,
                'display': 'flex',
                'justifyContent': 'center',
                'alignItems': 'center'
            }

        # Convert to integer and validate
        report_id = int(report_id)
        print(f"🔍 Looking for report ID: {report_id}")

        # Check if report exists in database
        report = Report.objects.filter(report_id=report_id).first()

        if report:
            print(f"✅ Successfully loaded report: {report.report_name} (ID: {report_id})")
            # Hide loading overlay
            return report_id, {'display': 'none'}
        else:
            print(f"❌ Report {report_id} not found in database")
            # Keep loading overlay but show error
            return dash.no_update, {
                'position': 'fixed',
                'top': 0,
                'left': 0,
                'right': 0,
                'bottom': 0,
                'backgroundColor': 'rgba(255,255,255,0.9)',
                'zIndex': 9999,
                'display': 'flex',
                'justifyContent': 'center',
                'alignItems': 'center'
            }

    except (ValueError, TypeError) as e:
        print(f"❌ Error parsing report_id: {e}")
        return dash.no_update, {
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'right': 0,
            'bottom': 0,
            'backgroundColor': 'rgba(255,255,255,0.9)',
            'zIndex': 9999,
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center'
        }


# Error handling callback - updates loading overlay content based on errors
@app.callback(
    Output('loading-overlay', 'children'),
    [Input("selected-report", "data"),
     Input("url", "search")],
    prevent_initial_call=False
)
def update_loading_content(selected_report, search):
    """Update loading overlay content based on loading state"""

    if selected_report:
        # Report loaded successfully, this won't be visible anyway
        return []

    if not search:
        return [
            html.Div([
                html.H3("Missing URL Parameters", style={'color': '#d9534f', 'textAlign': 'center'}),
                html.Div("Please provide a report_id parameter in the URL",
                         style={'marginTop': '10px', 'textAlign': 'center'}),
                html.Div("Example: /sec-embedded/?report_id=123",
                         style={'marginTop': '5px', 'textAlign': 'center', 'fontStyle': 'italic'})
            ], style={
                'position': 'absolute',
                'top': '50%',
                'left': '50%',
                'transform': 'translate(-50%, -50%)',
                'padding': '20px',
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
            })
        ]

    # Check for specific error conditions
    try:
        params = parse_qs(search.lstrip("?"))
        report_id = params.get('report_id', [None])[0]

        if not report_id:
            return [
                html.Div([
                    html.H3("Missing Report ID", style={'color': '#d9534f', 'textAlign': 'center'}),
                    html.Div("No report_id found in URL parameters", style={'marginTop': '10px', 'textAlign': 'center'})
                ], style={
                    'position': 'absolute',
                    'top': '50%',
                    'left': '50%',
                    'transform': 'translate(-50%, -50%)',
                    'padding': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                })
            ]

        # Try to validate report_id
        report_id = int(report_id)
        report = Report.objects.filter(report_id=report_id).first()

        if not report:
            return [
                html.Div([
                    html.H3("Report Not Found", style={'color': '#d9534f', 'textAlign': 'center'}),
                    html.Div(f"Report ID {report_id} does not exist",
                             style={'marginTop': '10px', 'textAlign': 'center'})
                ], style={
                    'position': 'absolute',
                    'top': '50%',
                    'left': '50%',
                    'transform': 'translate(-50%, -50%)',
                    'padding': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                })
            ]

    except (ValueError, TypeError):
        return [
            html.Div([
                html.H3("Invalid Report ID", style={'color': '#d9534f', 'textAlign': 'center'}),
                html.Div("Report ID must be a valid number", style={'marginTop': '10px', 'textAlign': 'center'})
            ], style={
                'position': 'absolute',
                'top': '50%',
                'left': '50%',
                'transform': 'translate(-50%, -50%)',
                'padding': '20px',
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
            })
        ]

    # Default loading message
    return [
        html.Div([
            html.H3("Loading Report...", style={'color': '#0056b3', 'textAlign': 'center'}),
            html.Div("Please wait while we load your data...", style={'marginTop': '10px', 'textAlign': 'center'})
        ], style={
            'position': 'absolute',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
        })
    ]