from collections import Counter
from datetime import datetime
import pandas as pd
from ..app import app
from dash import Input, Output, State, html, dcc
import dash

from plotly_integration.models import Report, SampleMetadata, PeakResults


@app.callback(
    Output("sec-results-header", "children"),
    [Input("selected-report", "data")],
    prevent_initial_call=True
)
def update_sec_results_header(selected_report):
    if not selected_report:
        return "No Report Selected"

    try:
        report_id = int(selected_report)
    except (ValueError, TypeError):
        return "Invalid Report ID"

    report = Report.objects.filter(report_id=report_id).first()

    if not report:
        return "Report Not Found"

    return f"{report.project_id} - {report.report_name}"


@app.callback(
    Output("sample-details-table", "data"),
    Input("selected-report", "data"),
    prevent_initial_call=True
)
def update_sample_and_std_details(selected_report):
    default_data = [
        {"field": "Sample Set Name", "value": ""},
        {"field": "Column Name", "value": ""},
        {"field": "Column Serial Number", "value": ""},
        {"field": "Instrument Method Name", "value": ""},
    ]

    if not selected_report:
        return default_data

    try:
        report_id = int(selected_report)
    except (ValueError, TypeError):
        return default_data

    report = Report.objects.filter(report_id=report_id).first()

    if not report:
        return default_data

    selected_result_ids = [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()]
    if not selected_result_ids:
        return default_data

    first_sample_name = selected_result_ids[0]
    sample_metadata = SampleMetadata.objects.filter(result_id=first_sample_name).first()

    if not sample_metadata:
        return default_data

    sample_set_name = sample_metadata.sample_set_name or "N/A"
    column_name = sample_metadata.column_name or "N/A"
    column_serial_number = sample_metadata.column_serial_number or "N/A"
    system_name = sample_metadata.system_name or "N/A"
    instrument_method_name = sample_metadata.instrument_method_name or "N/A"

    return [
        {"field": "Sample Set Name", "value": sample_set_name},
        {"field": "Column Name", "value": column_name},
        {"field": "Column Serial Number", "value": column_serial_number},
        {"field": "Instrument Method Name", "value": instrument_method_name},
    ]


@app.callback(
    [Output("download-hmw-data", "data")],
    [Input("export-button", "n_clicks")],
    [State("hmw-table", "data"),
     State('selected-report', 'data')],
    prevent_initial_call=True
)
def export_to_xlsx(n_clicks, table_data, selected_report):
    if not table_data or not selected_report:
        return dash.no_update

    try:
        report_id = int(selected_report)
    except (ValueError, TypeError):
        return dash.no_update

    report = Report.objects.filter(report_id=report_id).first()

    if not report:
        return dash.no_update

    current_date = datetime.now().strftime("%Y%m%d")
    file_name = f"{current_date}-{report.project_id}-{report.report_name}.xlsx"

    df = pd.DataFrame(table_data)
    return [dcc.send_data_frame(df.to_excel, file_name, index=False)]


@app.callback(
    Output("project-id-display", "children"),
    Output("expected-mw-display", "children"),
    Input("selected-report", "data")
)
def update_project_info(report_id):
    from plotly_integration.models import Report, LimsProjectInformation

    if not report_id:
        raise dash.exceptions.PreventUpdate

    try:
        report_id = int(report_id)
    except (ValueError, TypeError):
        return "❌ Invalid Report ID", ""

    report = Report.objects.filter(report_id=report_id).first()
    if not report:
        return "❌ Report not found", ""

    project_id = report.project_id
    project = LimsProjectInformation.objects.filter(protein=project_id).first()
    mw = project.molecular_weight if project else None

    return (
        f"Project ID: {project_id}",
        f"Expected Molecular Weight: {mw / 1000} kDa" if mw else "Expected Molecular Weight: N/A"
    )


def compute_main_peak_rt(selected_result_ids):
    retention_times = []
    for result_id in selected_result_ids:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            continue

        peak_results = PeakResults.objects.filter(result_id=sample.result_id)
        if not peak_results.exists():
            continue

        df = pd.DataFrame.from_records(peak_results.values())

        if df.empty or 'height' not in df.columns or 'peak_retention_time' not in df.columns:
            continue

        df['height'] = pd.to_numeric(df['height'], errors='coerce')

        if df['height'].isna().all():
            continue

        max_height_row = df.loc[df['height'].idxmax()]
        retention_times.append(max_height_row['peak_retention_time'])

    return Counter(retention_times).most_common(1)[0][0] if retention_times else 5.10


@app.callback(
    Output("main-peak-rt-input", "value"),
    [Input("report-settings", "data"),
     Input("refresh-rt-btn", "n_clicks")],
    [State("selected-report", "data")],
    prevent_initial_call=True
)
def update_main_peak_rt(settings, n_clicks, selected_report):
    import dash

    ctx = dash.callback_context
    if not ctx.triggered or not selected_report:
        raise dash.exceptions.PreventUpdate

    triggered_input = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        selected_report = int(selected_report)
    except (ValueError, TypeError):
        return dash.no_update

    from plotly_integration.models import Report
    report = Report.objects.filter(report_id=selected_report).first()
    if not report:
        return dash.no_update

    selected_result_ids = [
        sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()
    ]
    if not selected_result_ids:
        return dash.no_update

    if triggered_input == "report-settings" and settings:
        main_peak_rt = settings.get("main_peak_rt", 7.85)
        print(f"⚙️ Loaded Main Peak RT from settings: {main_peak_rt}")
        return main_peak_rt

    if triggered_input == "refresh-rt-btn":
        new_rt = compute_main_peak_rt(selected_result_ids)
        print(f"🔄 Refreshed Main Peak RT from data: {new_rt}")
        return new_rt

    return dash.no_update