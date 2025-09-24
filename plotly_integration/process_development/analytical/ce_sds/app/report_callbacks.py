from .app import app
from dash import Input, Output, State
import dash
from plotly_integration.models import CESDSReport
from plotly_integration.process_development.analytical.ce_sds.app.database_funcs import get_metadata_from_source


# Combined URL parsing and report selection
@app.callback(
    [Output('url-params', 'data'),
     Output('embedded-mode', 'data'),
     Output('selected-report', 'data'),
     Output("selected-result-ids", "data")],
    [Input('url', 'search'),
     Input("confirm-report-selection", "n_clicks")],
    [State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data")],
    prevent_initial_call=False
)
def parse_url_and_handle_report_selection(search, confirm_clicks, selected_rows, table_data):
    ctx = dash.callback_context

    # Parse URL parameters
    url_params = {}
    embedded = False
    report_id = None
    result_ids = []

    if search:
        # Parse query parameters
        from urllib.parse import parse_qs
        params = parse_qs(search.lstrip('?'))

        # Extract parameters
        if 'embedded' in params:
            embedded = params['embedded'][0].lower() in ['true', '1', 'yes']
            url_params['embedded'] = embedded

        if 'report_id' in params:
            try:
                report_id = int(params['report_id'][0])
                url_params['report_id'] = report_id
            except:
                pass

    # Get the ID of the component that triggered the callback
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Handle report selection confirmation
    if triggered_id == "confirm-report-selection" and selected_rows and confirm_clicks:
        row = table_data[selected_rows[0]]
        report = CESDSReport.objects.filter(id=row["report_id"]).first()
        if report:
            report_id = report.id
            result_ids = [r.strip() for r in report.selected_result_ids.split(",")]

    # Handle URL-based report selection
    elif report_id and not triggered_id == "confirm-report-selection":
        try:
            report = CESDSReport.objects.get(id=int(report_id))
            result_ids = [r.strip() for r in report.selected_result_ids.split(",")]
        except CESDSReport.DoesNotExist:
            result_ids = []

    return url_params, embedded, report_id, result_ids


@app.callback(
    [Output("report-modal", "style"),
     Output("current-report-text", "children")],
    [Input("select-create-report-btn", "n_clicks"),
     Input("close-report-modal-btn", "n_clicks"),
     Input("cancel-select-btn", "n_clicks"),
     Input("confirm-report-selection", "n_clicks"),
     Input("load-once", "n_intervals"),
     Input("url-params", "data")],
    [State("report-modal", "style"),
     State("selected-report", "data"),
     State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data"),
     State("embedded-mode", "data")],
    prevent_initial_call=False
)
def toggle_report_modal(open_clicks, close_clicks, cancel_clicks, confirm_clicks, load_interval,
                        url_params, current_style, selected_report, selected_rows,
                        table_data, embedded):
    ctx = dash.callback_context

    # Get the ID of the component that triggered the callback
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Initial load with URL params
    if triggered_id == "load-once" and url_params.get("report_id") and not embedded:
        report_id = url_params.get("report_id")
        try:
            report = CESDSReport.objects.get(id=int(report_id))
            return current_style, f"{report.report_name}"
        except CESDSReport.DoesNotExist:
            return current_style, "Invalid report ID"

    # Handle button clicks
    if triggered_id == "select-create-report-btn":
        return {**current_style, "display": "block"}, dash.no_update

    elif triggered_id in ["close-report-modal-btn", "cancel-select-btn"]:
        return {**current_style, "display": "none"}, dash.no_update

    elif triggered_id == "confirm-report-selection" and selected_rows:
        selected_report_data = table_data[selected_rows[0]]
        report_name = selected_report_data.get("report_name", "Unknown Report")
        return {**current_style, "display": "none"}, f"{report_name}"

    # Default: show report name if selected
    if selected_report:
        try:
            report = CESDSReport.objects.get(report_id=int(selected_report))
            return current_style, f"{report.report_name}"
        except CESDSReport.DoesNotExist:
            return current_style, "Invalid report"

    return current_style, "No report selected"


@app.callback(
    Output("report-selection-table", "data"),
    [Input("report-modal", "style"),
     Input("report-tabs", "value")],  # Trigger when modal opens or tab changes
    prevent_initial_call=True
)
def populate_report_table(modal_style, active_tab):
    """Populate the report selection table when the modal is opened and select tab is active"""

    # Only populate if modal is visible and we're on the select tab
    if modal_style.get("display") == "block" and active_tab == "select-tab":
        try:
            # Fetch all reports with analysis_type=2 for Titer
            reports = CESDSReport.objects.all().order_by('-date_created')

            report_data = []
            for report in reports:
                report_data.append({
                    "report_id": report.id,
                    "report_name": report.report_name,
                    "project_id": report.project_id,
                    "user_id": report.user_id,
                    "date_created": report.date_created.strftime("%Y-%m-%d %H:%M") if report.date_created else ""
                })

            return report_data
        except Exception as e:
            print(f"Error fetching reports: {e}")
            return []

    return dash.no_update


@app.callback(
    [Output("reduced-result-ids", "data"),
     Output("nonreduced-result-ids", "data")],
    Input("selected-result-ids", "data")
)
def split_result_ids_by_prefix(result_ids):
    if not result_ids:
        return [], []

    # Always get metadata from unified tables
    metas = get_metadata_from_source(result_ids)
    # Filter out samples with 'STD' in the sample name (case insensitive)
    metas = [m for m in metas if not (m.sample_id_full and "std" in m.sample_id_full.lower())]

    reduced = [m.id for m in metas if m.sample_prefix and m.sample_prefix.lower() == "r"]
    nonreduced = [m.id for m in metas if m.sample_prefix and m.sample_prefix.lower() == "nr"]
    return reduced, nonreduced
