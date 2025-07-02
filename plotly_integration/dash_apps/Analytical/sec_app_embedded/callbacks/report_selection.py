from datetime import datetime

import dash
from dash import Input, Output, State, html
from plotly_integration.models import Report, SampleMetadata
from ..app import app
from dash.dependencies import Input, Output
from urllib.parse import urlencode, parse_qs, urlparse


@app.callback(
    Output("report-selection-table", "data"),
    Input("main-tabs", "value")
)
def populate_report_table(tab):
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


@app.callback(
    Output("report-selection-table", "selected_rows"),
    Input("report-selection-table", "data"),  # trigger only after table data is loaded
    State("url", "search"),
    prevent_initial_call=True
)
def select_row_from_url(table_data, search):
    if not search or not table_data:
        return dash.no_update

    query = parse_qs(search.lstrip("?"))
    report_id = query.get("report_id", [None])[0]

    if not report_id:
        return dash.no_update

    try:
        report_id = int(report_id)
    except ValueError:
        return dash.no_update

    for i, row in enumerate(table_data):
        try:
            if int(row.get("report_id")) == report_id:
                return [i]
        except (TypeError, ValueError):
            continue

    return dash.no_update


@app.callback(
    Output("selected-report", "data"),
    Output("url", "search"),
    Output("lims-link-tab", "style"),
    Input("report-selection-table", "selected_rows"),
    Input("sample-selection-table", "selected_rows"),
    Input("view_mode", "value"),
    State("report-selection-table", "data"),
    State("sample-selection-table", "data"),

    State("url", "search"),
    prevent_initial_call=True
)
def handle_report_selection(report_selected_rows, sample_selected_rows, view_mode,
                            report_table_data, sample_table_data
                            , search):
    parsed_query = parse_qs(search.lstrip("?") if search else {})

    if view_mode == "samples":
        # Force report_id=1
        parsed_query["report_id"] = ["1"]
        new_search = f"?{urlencode(parsed_query, doseq=True)}"

        if not sample_selected_rows or not sample_table_data:
            return 1, new_search, {"display": "none"}

        selected = [sample_table_data[i] for i in sample_selected_rows if sample_table_data[i].get("result_id")]
        sample_names = [s["sample_name"] for s in selected]
        result_ids = [str(s["result_id"]) for s in selected]

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

        return 1, new_search, {"display": "none"}

    # Default behavior for Select Report mode
    if not report_selected_rows or not report_table_data:
        return dash.no_update, dash.no_update

    selected_row = report_table_data[report_selected_rows[0]]
    report_id = selected_row.get("report_id")

    try:
        report_id = int(report_id)
    except (ValueError, TypeError):
        return dash.no_update, dash.no_update

    parsed_query["report_id"] = [str(report_id)]
    new_search = f"?{urlencode(parsed_query, doseq=True)}"
    print(report_id)

    return report_id, new_search, {"display": "block"}


@app.callback(
    Output("sample-selection-table", "selected_rows"),
    Input("view_mode", "value"),
    prevent_initial_call=True
)
def clear_sample_selection_on_mode_change(view_mode):
    return []


# Simple callback that only responds to explicit URL parameter
@app.callback(
    Output("select-report-tab", "style"),
    Output("main-tabs", "value"),
    Output("main-tabs", "children"),
    Input("url", "search"),
    State("main-tabs", "children"),
)
def toggle_report_tab_from_url(search, current_tabs):
    if not search:
        return {"display": "block"}, dash.no_update, dash.no_update

    params = parse_qs(search.lstrip("?"))
    hide_tab = params.get("hide_report_tab", ["false"])[0].lower() == "true"

    if hide_tab:
        # Filter out the first tab
        filtered_tabs = [tab for tab in current_tabs if tab.props.get("value") != "tab-1"]
        return {"display": "none"}, "tab-2", filtered_tabs

    return {"display": "block"}, dash.no_update, current_tabs


@app.callback(
    Output("report-table-container", "style"),
    Output("sample-table-container", "style"),
    Output("sample_type_filter", "style"),
    Output("sample-type-label", "style"),
    Input("view_mode", "value")
)
def toggle_table_visibility(view_mode):
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
            {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
        )
    else:
        return (
            {
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
            }, {'display': 'block'}, {'display': 'block'}
        )


@app.callback(
    Output("sample-selection-table", "data"),
    Input("sample_type_filter", "value"),
    Input("view_mode", "value"),
    prevent_initial_call=True
)
def populate_sample_table(sample_type, view_mode):
    if view_mode != "samples" or not sample_type:
        return []

    samples = SampleMetadata.objects.filter(sample_type=1, sample_name__startswith=sample_type).order_by(
        "-date_acquired")[:500]

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


@app.callback(
    Output("submission_status", "children"),
    Input("sample-selection-table", "selected_rows"),
    State("sample-selection-table", "data"),
    State("view_mode", "value"),
    prevent_initial_call=True
)
def update_temp_report(selected_rows, sample_data, view_mode):
    if view_mode != "samples":
        return dash.no_update

    if not selected_rows:
        return "No samples selected."

    selected = [sample_data[i] for i in selected_rows if sample_data[i].get("result_id")]

    if not selected:
        return "No valid result IDs found."

    sample_names = [s["sample_name"] for s in selected]
    result_ids = [str(s["result_id"]) for s in selected]

    # Direct update without transaction
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
