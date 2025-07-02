from collections import Counter
from datetime import datetime
import pandas as pd
from ..app import app
from dash import Input, Output, State, html, dcc
import dash

from plotly_integration.models import Report, SampleMetadata, PeakResults


@app.callback(
    Output("sec-results-header", "children"),  # Update the SEC Results header
    [Input("selected-report", "data")],
    prevent_initial_call=True
)
def update_sec_results_header(selected_report):
    report_id = selected_report
    report = Report.objects.filter(report_id=report_id).first()

    if not report:
        return "Report Not Found"

    # Format the SEC Results text
    return f"{report.project_id} - {report.report_name}"


@app.callback(
    Output("sample-details-table", "data"),
    Input("selected-report", "data"),
    prevent_initial_call=True
)
def update_sample_and_std_details(selected_report):
    # Default table data
    default_data = [
        {"field": "Sample Set Name", "value": ""},
        {"field": "Column Name", "value": ""},
        {"field": "Column Serial Number", "value": ""},
        {"field": "Instrument Method Name", "value": ""},
    ]
    report_id = selected_report

    if not report_id:
        return default_data

    report = Report.objects.filter(report_id=report_id).first()

    if not report:
        return default_data

    # Fetch the first sample name from the report's selected samples
    selected_result_ids = [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()]
    if not selected_result_ids:
        return default_data

    first_sample_name = selected_result_ids[0]
    sample_metadata = SampleMetadata.objects.filter(result_id=first_sample_name).first()

    if not sample_metadata:
        return default_data

    # Extract details from the `SampleMetadata` model
    sample_set_name = sample_metadata.sample_set_name or "N/A"
    column_name = sample_metadata.column_name or "N/A"
    column_serial_number = sample_metadata.column_serial_number or "N/A"
    system_name = sample_metadata.system_name or "N/A"
    instrument_method_name = sample_metadata.instrument_method_name or "N/A"

    # Return table data
    return [
        {"field": "Sample Set Name", "value": sample_set_name},
        {"field": "Column Name", "value": column_name},
        {"field": "Column Serial Number", "value": column_serial_number},
        {"field": "Instrument Method Name", "value": instrument_method_name},

    ]


@app.callback(
    [Output("download-hmw-data", "data")],
    [
        Input("export-button", "n_clicks"),
    ],
    [
        State("hmw-table", "data"),
        State('selected-report', 'data')
    ],  # Use the stored selected report
    prevent_initial_call=True
)
def export_to_xlsx(n_clicks, table_data, selected_report):
    if not table_data:
        return dash.no_update  # Do nothing if the table is empty

    print(selected_report)
    # Fetch report details from the database
    report = Report.objects.filter(report_id=int(selected_report)).first()
    print(report)
    print(report.project_id)
    print(report.report_name)

    if not report:
        return dash.no_update

    # Get current date
    current_date = datetime.now().strftime("%Y%m%d")

    # Build the file name
    file_name = f"{current_date}-{report.project_id}-{report.report_name}.xlsx"
    print(file_name)

    # Convert table data to a pandas DataFrame
    df = pd.DataFrame(table_data)

    # Use Dash's `send_data_frame` to export the DataFrame as an XLSX file
    return [dcc.send_data_frame(df.to_excel, file_name, index=False)]


# @app.callback(
#     [Output('main-peak-rt-store', 'data'),
#      Output('low-mw-cutoff-store', 'data')],
#     [Input('main-peak-rt-input', 'value'),
#      Input('low-mw-cutoff-input', 'value')],
#     prevent_initial_call=True
# )
# def update_cutoff_values(main_peak_rt, low_mw_cutoff):
#     print(f"Updated Main Peak RT: {main_peak_rt}, LMW Cutoff: {low_mw_cutoff}")
#     return main_peak_rt, low_mw_cutoff


# Project Info in Table Tab Logic
@app.callback(
    Output("project-id-display", "children"),
    Output("expected-mw-display", "children"),
    Input("selected-report", "data")
)
def update_project_info(report_id):
    from plotly_integration.models import Report, LimsProjectInformation

    if not report_id:
        print('No Report found')
        raise dash.exceptions.PreventUpdate

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


# Compute the most common peak retention time based on max height
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

        # Ensure 'height' and 'peak_retention_time' exist and convert 'height' to numeric
        if df.empty or 'height' not in df.columns or 'peak_retention_time' not in df.columns:
            continue

        df['height'] = pd.to_numeric(df['height'], errors='coerce')  # Convert to numeric, non-numeric -> NaN

        if df['height'].isna().all():  # If all values are NaN, skip this sample
            continue

        max_height_row = df.loc[df['height'].idxmax()]
        retention_times.append(max_height_row['peak_retention_time'])

    return Counter(retention_times).most_common(1)[0][0] if retention_times else 5.10


# @app.callback(
#     Output("main-peak-rt-input", "value"),  # Store the new RT value
#     Input("refresh-rt-btn", "n_clicks"),
#     Input("report-settings", "data"),
#     State("selected-report", "data"),
#     prevent_initial_call=True
# )
# def update_main_peak_rt(n_clicks, settings, selected_report):
#     if not selected_report:
#         print("No report selected.")
#         return dash.no_update  # Prevents unnecessary update
#
#     report = Report.objects.filter(report_id=selected_report).first()
#     if not report:
#         print("Report not found.")
#         return dash.no_update
#     selected_result_ids = [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()]
#     sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
#     if not selected_result_ids:
#         print("No samples found in the report.")
#         return dash.no_update
#     if settings:
#         main_peak_rt = settings.get("main_peak_rt", 7.85)
#         print(main_peak_rt)
#         return main_peak_rt
#
#     new_rt = compute_main_peak_rt(selected_result_ids)
#     print(f"Updated Main Peak RT: {new_rt}")  # Debugging Log
#
#     return new_rt  # This will update `dcc.Store(id="main-peak-rt-store")`


@app.callback(
    Output("main-peak-rt-input", "value"),
    Input("report-settings", "data"),           # Loads initially from JSON
    Input("refresh-rt-btn", "n_clicks"),        # Allows user to override
    State("selected-report", "data"),
    prevent_initial_call=True
)
def update_main_peak_rt(settings, n_clicks, selected_report):
    ctx = dash.callback_context

    if not ctx.triggered or not selected_report:
        raise dash.exceptions.PreventUpdate

    triggered_input = ctx.triggered[0]["prop_id"].split(".")[0]
    if not triggered_input:
        print("No triggered input.")

    if n_clicks:
        print("Compute Main Peak RT")

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
