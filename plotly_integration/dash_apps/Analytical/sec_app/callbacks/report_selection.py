from datetime import datetime

import dash
from dash import Input, Output, State, html
from plotly_integration.models import Report, SampleMetadata
from ..app import app
from dash.dependencies import Input, Output
from urllib.parse import urlencode, parse_qs, urlparse


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

    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Initial load with URL params
    if triggered_id == "load-once" and url_params and url_params.get("report_id") and not embedded:
        report_id = url_params.get("report_id")
        try:
            # FIXED: Use filter() with report_id field instead of get() with id field
            report = Report.objects.filter(report_id=int(report_id)).first()
            if report:
                return current_style, f"Report: {report.report_name}"
            else:
                return current_style, f"Report ID {report_id} not found"
        except (ValueError, TypeError) as e:
            return current_style, f"Invalid report ID: {report_id}"

    # Handle button clicks
    if triggered_id == "select-create-report-btn":
        return {**current_style, "display": "block"}, dash.no_update

    elif triggered_id in ["close-report-modal-btn", "cancel-select-btn"]:
        return {**current_style, "display": "none"}, dash.no_update

    elif triggered_id == "confirm-report-selection" and selected_rows and table_data:
        selected_report_data = table_data[selected_rows[0]]
        report_name = selected_report_data.get("report_name", "Unknown Report")
        report_id = selected_report_data.get("report_id", "Unknown ID")
        return {**current_style, "display": "none"}, f"Report: {report_name} (ID: {report_id})"

    # Default display based on current selected report
    if selected_report:
        try:
            # FIXED: Use filter() with report_id field
            report = Report.objects.filter(report_id=int(selected_report)).first()
            if report:
                return current_style, f"Report: {report.report_name}"
            else:
                return current_style, f"Report ID {selected_report} not found"
        except (ValueError, TypeError):
            return current_style, f"Invalid report ID: {selected_report}"

    return current_style, "No report selected"


@app.callback(
    Output("report-selection-table", "data"),
    [Input("report-modal", "style"),
     Input("report-tabs", "value")],
    prevent_initial_call=True
)
def populate_report_table(modal_style, active_tab):
    """Populate the report selection table when the modal is opened and select tab is active"""

    # Only populate if modal is visible and we're on the select tab
    if modal_style.get("display") == "block" and active_tab == "select-tab":
        try:
            reports = Report.objects.filter(analysis_type=1, department=1).order_by("-report_id").values(
                "report_id", "report_name", "project_id", "user_id", "date_created"
            )
            data = []
            for report in reports:
                date = report["date_created"]
                date_str = date.strftime("%Y-%m-%d %H:%M:%S") if date else "N/A"
                data.append({
                    "report_id": report["report_id"],
                    "report_name": report["report_name"],
                    "project_id": report["project_id"],
                    "user_id": report["user_id"] or "N/A",
                    "date_created": date_str
                })
            return data
        except Exception as e:
            print(f"Error fetching reports: {e}")
            return []

    return dash.no_update


@app.callback(
    Output("selected-report", "data"),
    [Input("url", "search"),  # URL changes
     Input("confirm-report-selection", "n_clicks"),  # Confirm button clicks
     Input("sample-selection-table", "selected_rows")],  # Sample selection
    [State("report-selection-table", "data"),  # Table data as state
     State("report-selection-table", "selected_rows"),  # Selected rows as state
     State("view_mode", "value"),
     State("sample-selection-table", "data"),
     State("selected-report", "data")],  # Add current selected report as state
    prevent_initial_call=False  # Important: Allow initial call for URL parsing
)
def handle_report_selection_and_url(search, confirm_clicks, sample_selected_rows, 
                                    table_data, report_selected_rows, view_mode, sample_table_data, current_selected_report):
    """Combined callback that handles both URL-based report selection and store updates"""

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print(f"DEBUG: Triggered by: {triggered_id}")

    # Handle URL-based selection with highest priority
    if triggered_id == "url" and search:
        query = parse_qs(search.lstrip("?"))
        report_id_list = query.get("report_id", [None])
        report_id = report_id_list[0] if report_id_list else None
        print(f"DEBUG: URL search: {search}")
        print(f"DEBUG: URL query parsed: {query}")
        print(f"DEBUG: URL report_id raw: {report_id_list}, extracted: {report_id}")

        if report_id and report_id != 'None':
            try:
                # Handle case where report_id might be a string representation of a list
                if isinstance(report_id, str) and report_id.startswith('[') and report_id.endswith(']'):
                    # Parse string like "['419']" to get '419'
                    import ast
                    parsed = ast.literal_eval(report_id)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        report_id = parsed[0]
                
                # Handle case where report_id might still be a list
                if isinstance(report_id, list):
                    report_id = report_id[0]
                    
                report_id = int(report_id)
                # Query database directly to check if report exists
                report = Report.objects.filter(report_id=report_id).first()

                if report:
                    print(f"DEBUG: Found report {report_id}, setting selected report")
                    return report_id
                else:
                    print(f"DEBUG: Report {report_id} not found in database")
                    return dash.no_update

            except (ValueError, TypeError):
                pass

    # Handle sample selection in sample mode
    elif triggered_id == "sample-selection-table" and view_mode == "samples":
        if sample_selected_rows and sample_table_data:
            selected = [sample_table_data[i] for i in sample_selected_rows
                        if sample_table_data[i].get("result_id")]

            if selected:
                sample_names = [s["sample_name"] for s in selected]
                result_ids = [str(s["result_id"]) for s in selected]

                # Create/update temporary report
                try:
                    Report.objects.update_or_create(
                        report_id=1,
                        defaults={
                            "report_name": "Temporary Sample View",
                            "project_id": "TEMP",
                            "user_id": "viewer",
                            "comments": "Auto-generated from sample view mode",
                            "selected_samples": ",".join(sample_names),
                            "selected_result_ids": ",".join(result_ids),
                            "date_created": datetime.now(),
                            "analysis_type": 1,
                            "department": 1
                        }
                    )
                    return 1  # Return report ID 1
                except Exception as e:
                    print(f"Error creating temporary report: {e}")
                    return dash.no_update

    # Handle confirm button clicks
    elif triggered_id == "confirm-report-selection" and confirm_clicks:
        if view_mode == "samples":
            return 1  # Return temporary report ID
        else:
            if report_selected_rows and table_data:
                selected_row = table_data[report_selected_rows[0]]
                report_id = selected_row.get("report_id")
                try:
                    return int(report_id)
                except (ValueError, TypeError):
                    return dash.no_update

    return dash.no_update


# @app.callback(
#     [Output("url", "search"),
#      Output("lims-link-tab", "style")],
#     [Input("confirm-report-selection", "n_clicks")],
#     [State("view_mode", "value"),
#      State("report-selection-table", "selected_rows"),
#      State("sample-selection-table", "selected_rows"),
#      State("report-selection-table", "data"),
#      State("sample-selection-table", "data"),
#      State("url", "search")],
#     prevent_initial_call=True
# )
# def handle_url_updates(confirm_clicks, view_mode, report_selected_rows, sample_selected_rows,
#                        report_table_data, sample_table_data, search):
#     """Handle URL updates and tab visibility when report is confirmed"""
#
#     # Don't process if no confirmation click
#     if not confirm_clicks:
#         return dash.no_update, dash.no_update
#
#     parsed_query = parse_qs(search.lstrip("?") if search else "")
#
#     if view_mode == "samples":
#         # Force report_id=1 for sample mode
#         parsed_query["report_id"] = ["1"]
#         new_search = f"?{urlencode(parsed_query, doseq=True)}"
#         return new_search, {"display": "none"}
#
#     # Default behavior for Select Report mode
#     if report_selected_rows and report_table_data:
#         selected_row = report_table_data[report_selected_rows[0]]
#         report_id = selected_row.get("report_id")
#
#         try:
#             report_id = int(report_id)
#             parsed_query["report_id"] = [str(report_id)]
#             new_search = f"?{urlencode(parsed_query, doseq=True)}"
#             return new_search, {"display": "block"}
#         except (ValueError, TypeError):
#             return dash.no_update, dash.no_update
#
#     return dash.no_update, dash.no_update


# Separate callback to handle table row highlighting (visual only, no store update)
@app.callback(
    Output("report-selection-table", "selected_rows"),
    [Input("report-selection-table", "data"),
     Input("url", "search")],
    [State("report-selection-table", "selected_rows")],
    prevent_initial_call=True
)
def update_table_selection_from_url(table_data, search, current_selection):
    """Update table row selection when URL changes"""
    
    if not search or not table_data:
        return dash.no_update
        
    query = parse_qs(search.lstrip("?"))
    url_report_id_list = query.get("report_id", [None])
    url_report_id = url_report_id_list[0] if url_report_id_list else None
    
    if url_report_id:
        try:
            # Handle string representation of list
            if isinstance(url_report_id, str) and url_report_id.startswith('[') and url_report_id.endswith(']'):
                import ast
                parsed = ast.literal_eval(url_report_id)
                if isinstance(parsed, list) and len(parsed) > 0:
                    url_report_id = parsed[0]
            
            url_report_id = int(url_report_id)
            
            # Find the row index for this report_id in the table data
            for i, row in enumerate(table_data):
                try:
                    if int(row.get("report_id")) == url_report_id:
                        print(f"DEBUG: Setting table selection to row {i} for report {url_report_id}")
                        return [i]
                except (TypeError, ValueError):
                    continue
                    
        except (ValueError, TypeError):
            pass
    
    return dash.no_update


@app.callback(
    Output("sample-selection-table", "selected_rows"),
    Input("view_mode", "value"),
    prevent_initial_call=True
)
def clear_sample_selection_on_mode_change(view_mode):
    """Clear sample selection when mode changes"""
    return []


@app.callback(
    [Output("report-table-container", "style"),
     Output("sample-table-container", "style"),
     Output("sample_type_filter", "style"),
     Output("sample-type-label", "style")],
    Input("view_mode", "value")
)
def toggle_table_visibility(view_mode):
    """Toggle between report table and sample table based on mode"""
    if view_mode == "report":
        return (
            {
                'width': '98%',
                'margin': 'auto',
                'padding': '10px',
                'border': '2px solid #0056b3',
                'border-radius': '5px',
                'background-color': '#f7f9fc',
                'margin-bottom': '10px',
                'display': 'block'
            },
            {
                'width': '98%',
                'margin': 'auto',
                'padding': '10px',
                'border': '2px solid #0056b3',
                'border-radius': '5px',
                'background-color': '#f7f9fc',
                'margin-bottom': '10px',
                'display': 'none'
            },
            {'display': 'none'},
            {'display': 'none'}
        )
    else:
        return (
            {
                'width': '98%',
                'margin': 'auto',
                'padding': '10px',
                'border': '2px solid #0056b3',
                'border-radius': '5px',
                'background-color': '#f7f9fc',
                'margin-bottom': '10px',
                'display': 'none'
            },
            {
                'width': '98%',
                'margin': 'auto',
                'padding': '10px',
                'border': '2px solid #0056b3',
                'border-radius': '5px',
                'background-color': '#f7f9fc',
                'margin-bottom': '10px',
                'display': 'block'
            },
            {'display': 'block'},
            {'display': 'block'}
        )


@app.callback(
    Output("sample-selection-table", "data"),
    [Input("sample_type_filter", "value"),
     Input("view_mode", "value")],
    prevent_initial_call=True
)
def populate_sample_table(sample_type, view_mode):
    """Populate sample table when in sample mode"""
    if view_mode != "samples" or not sample_type:
        return []

    try:
        samples = SampleMetadata.objects.filter(
            sample_type=1,
            sample_name__startswith=sample_type
        ).order_by("-date_acquired")[:500]

        return [
            {
                "sample_name": s.sample_name,
                "result_id": s.result_id,
                "date_acquired": s.date_acquired.strftime("%m/%d/%Y %I:%M:%S %p") if s.date_acquired else "",
                "sample_set_name": s.sample_set_name,
                "column_name": s.column_name,
            }
            for s in samples
        ]
    except Exception as e:
        print(f"Error fetching samples: {e}")
        return []


@app.callback(
    Output("submission_status", "children"),
    [Input("sample-selection-table", "selected_rows")],
    [State("sample-selection-table", "data"),
     State("view_mode", "value")],
    prevent_initial_call=True
)
def update_temp_report(selected_rows, sample_data, view_mode):
    """Update temporary report status for sample mode"""
    if view_mode != "samples":
        return dash.no_update

    if not selected_rows:
        return "No samples selected."

    selected = [sample_data[i] for i in selected_rows if sample_data[i].get("result_id")]

    if not selected:
        return "No valid result IDs found."

    sample_names = [s["sample_name"] for s in selected]
    result_ids = [str(s["result_id"]) for s in selected]

    try:
        # Update temporary report
        Report.objects.update_or_create(
            report_id=1,
            defaults={
                "report_name": "Temporary Sample View",
                "project_id": "TEMP",
                "user_id": "viewer",
                "comments": "Auto-generated from sample view mode",
                "selected_samples": ",".join(sample_names),
                "selected_result_ids": ",".join(result_ids),
                "date_created": datetime.now(),
                "analysis_type": 1,
                "department": 1
            }
        )

        return f"Temporary report updated with {len(sample_names)} sample(s)."
    except Exception as e:
        print(f"Error updating temporary report: {e}")
        return "Error updating temporary report."