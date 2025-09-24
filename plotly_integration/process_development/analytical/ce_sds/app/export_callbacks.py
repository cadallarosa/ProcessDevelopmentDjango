from .app import app
import pandas as pd
from dash import Input, Output, State, dcc
import io
from plotly_integration.models import CESDSReport


@app.callback(
    Output("download-nonreduced-xlsx", "data"),
    Input("export-nonreduced-btn", "n_clicks"),
    State("nonreduced-table", "data"),
    State("selected-report", "data"),
    prevent_initial_call=True
)
def export_nonreduced_table(n_clicks, table_data, selected_report):
    report_name = CESDSReport.objects.filter(
        id=selected_report).first().report_name if selected_report else "CESDS_Report"
    filename = f"{report_name}_NonReduced.xlsx"
    df = pd.DataFrame(table_data)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, startrow=1)
        worksheet = writer.sheets["Sheet1"]
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
        worksheet.cell(row=1, column=1).value = "Non-Reduced Results"

    buffer.seek(0)

    def write_buffer(out_io):
        out_io.write(buffer.getvalue())

    return dcc.send_bytes(write_buffer, filename)

@app.callback(
    Output("download-reduced-xlsx", "data"),
    Input("export-reduced-btn", "n_clicks"),
    State("reduced-table", "data"),
    State("selected-report", "data"),
    prevent_initial_call=True
)
def export_nonreduced_table(n_clicks, table_data, selected_report):
    report_name = CESDSReport.objects.filter(
        id=selected_report).first().report_name if selected_report else "CESDS_Report"
    filename = f"{report_name}_Reduced.xlsx"
    df = pd.DataFrame(table_data)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, startrow=1)
        worksheet = writer.sheets["Sheet1"]
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
        worksheet.cell(row=1, column=1).value = "Reduced Results"

    buffer.seek(0)

    def write_buffer(out_io):
        out_io.write(buffer.getvalue())

    return dcc.send_bytes(write_buffer, filename)