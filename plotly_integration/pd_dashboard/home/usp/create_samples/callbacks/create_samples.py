# USP create_samples callbacks - Adapted for Upstream Processing
from dash import Input, Output, State, no_update, html, dcc, ctx, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, LimsProjectInformation
import json
import base64
import io
from dash.exceptions import PreventUpdate
from django.db.models import Max
from datetime import datetime
from plotly_integration.pd_dashboard.main_app import app

print("Configuring USP create_samples callbacks...")

# MAIN CALLBACK FOR CREATION METHOD CONTENT
@app.callback(
    Output("usp-creation-method-content", "children"),
    Input("usp-creation-method", "value"),
    prevent_initial_call=False
)
def update_usp_creation_method_content(method):
    """Update content based on selected creation method for USP"""
    print(f"USP Creation method changed to: {method}")

    if method == "manual":
        from ..layouts.create_samples import create_manual_entry_section
        return create_manual_entry_section()
    elif method == "template":
        from ..layouts.create_samples import create_template_import_section
        return create_template_import_section()
    elif method == "upload":
        from ..layouts.create_samples import create_bulk_upload_section
        return create_bulk_upload_section()

    # Default fallback
    return html.Div([
        dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Please select a creation method to continue."
        ], color="info")
    ])


# TEMPLATE DOWNLOAD CALLBACK FOR USP
@app.callback(
    Output("usp-download-template-file", "data"),
    [Input("usp-download-template-btn", "n_clicks"),
     Input("usp-download-excel-template-btn", "n_clicks")],
    prevent_initial_call=True
)
def download_usp_sample_template(download_btn_clicks, excel_btn_clicks):
    """Generate and download Excel template for USP sample creation"""
    if not download_btn_clicks and not excel_btn_clicks:
        return no_update

    try:
        print(f"Generating USP template download")

        # Create template dataframe with USP-specific fields
        template_data = {
            "Project ID": ["PRJ-2025-001", "PRJ-2025-001", "PRJ-2025-002", "", ""],
            "Reactor Type": ["bioreactor", "bioreactor", "dasgip", "", ""],
            "Clone": ["CHO-K1-001", "CHO-K1-002", "CHO-DG44-003", "", ""],
            "Run Date": ["2025-01-01", "2025-01-02", "2025-01-03", "", ""],
            "Harvest Date": ["2025-01-15", "2025-01-16", "2025-01-17", "", ""],
            "Culture Duration (days)": [14, 14, 14, "", ""],
            "Max VCD (cells/mL)": [25.5e6, 24.8e6, 26.2e6, "", ""],
            "Viability (%)": [92.5, 91.8, 93.2, "", ""],
            "Final Titer (g/L)": [5.2, 4.8, 5.5, "", ""],
            "Culture Volume (L)": [3.0, 3.0, 1.0, "", ""],
            "pH": [7.0, 7.1, 6.9, "", ""],
            "DO (%)": [40, 45, 38, "", ""],
            "Temperature (C)": [37.0, 37.0, 36.5, "", ""],
            "Feed Strategy": ["Fed-batch A", "Fed-batch A", "Fed-batch B", "", ""],
            "Note": ["Standard run", "pH drift observed", "New feed tested", "", ""]
        }

        df = pd.DataFrame(template_data)

        # Create Excel file in memory
        output = io.BytesIO()
        
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write sample data sheet
                df.to_excel(writer, sheet_name='USP_Sample_Data', index=False)

                # Get workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['USP_Sample_Data']

                # Create formats
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#1976d2',
                    'font_color': 'white',
                    'border': 1,
                    'align': 'center'
                })

                example_format = workbook.add_format({
                    'bg_color': '#e3f2fd',
                    'border': 1
                })

                # Format header row
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Format example rows
                for row in range(1, 4):  # First 3 data rows are examples
                    for col in range(len(df.columns)):
                        worksheet.write(row, col, df.iloc[row - 1, col], example_format)

                # Set column widths
                worksheet.set_column('A:B', 15)  # Project ID, Reactor Type
                worksheet.set_column('C:C', 15)  # Clone
                worksheet.set_column('D:E', 15)  # Dates
                worksheet.set_column('F:N', 18)  # Numeric columns
                worksheet.set_column('O:O', 20)  # Feed Strategy
                worksheet.set_column('P:P', 30)  # Note

                # Add instructions sheet
                instructions_data = [
                    ["USP Sample Creation Template - Instructions", ""],
                    ["", ""],
                    ["IMPORTANT NOTES:", ""],
                    ["1. Project ID", "Required - Use your project identifier"],
                    ["2. Reactor Type", "Choose from: bioreactor, flask, wave, ambr, dasgip, other"],
                    ["3. Sample Numbers", "Will be auto-generated - do not include them"],
                    ["4. Date Format", "Use YYYY-MM-DD format for all dates"],
                    ["5. Scientific Notation", "Acceptable for VCD (e.g., 2.5e7 for 25 million)"],
                    ["", ""],
                    ["COLUMN DESCRIPTIONS:", ""],
                    ["Project ID", "Project identifier for grouping samples (required)"],
                    ["Reactor Type", "Type of reactor used (required)"],
                    ["Clone", "Cell line or clone identifier (required)"],
                    ["Run Date", "Date culture was started (YYYY-MM-DD)"],
                    ["Harvest Date", "Date of harvest (YYYY-MM-DD)"],
                    ["Culture Duration (days)", "Total days in culture"],
                    ["Max VCD (cells/mL)", "Maximum viable cell density achieved"],
                    ["Viability (%)", "Final viability percentage"],
                    ["Final Titer (g/L)", "Final product titer"],
                    ["Culture Volume (L)", "Working volume in liters"],
                    ["pH", "Final pH value"],
                    ["DO (%)", "Dissolved oxygen percentage"],
                    ["Temperature (C)", "Culture temperature in Celsius"],
                    ["Feed Strategy", "Feeding protocol used"],
                    ["Note", "Any additional notes or comments"],
                    ["", ""],
                    ["EXAMPLE DATA:", ""],
                    ["The first 3 rows contain example data", "Delete these before adding your real data"],
                    ["", ""],
                    ["GROUPING:", ""],
                    ["Samples will be grouped by:", "Project ID and Reactor Type"]
                ]

                instructions_df = pd.DataFrame(instructions_data, columns=["Field", "Description"])
                instructions_df.to_excel(writer, sheet_name='Instructions', index=False)

                # Format instructions sheet
                inst_worksheet = writer.sheets['Instructions']
                inst_worksheet.set_column('A:A', 30)
                inst_worksheet.set_column('B:B', 60)

                # Add header format to instructions
                for col_num, value in enumerate(instructions_df.columns.values):
                    inst_worksheet.write(0, col_num, value, header_format)

            output.seek(0)
            content = base64.b64encode(output.read()).decode()
            return dict(
                content=content,
                filename=f"USP_Sample_Template_{datetime.now().strftime('%Y%m%d')}.xlsx",
                type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except ImportError:
            # Fallback to CSV if xlsxwriter not available
            output = io.StringIO()
            df.to_csv(output, index=False)
            content = output.getvalue()
            
            return dict(
                content=content,
                filename=f"USP_Sample_Template_{datetime.now().strftime('%Y%m%d')}.csv",
                type="text/csv"
            )

    except Exception as e:
        print(f"Error generating USP template: {e}")
        return no_update


# SAMPLE TABLE GENERATION CALLBACK FOR USP
@app.callback(
    Output("usp-sample-table-container", "children"),
    [Input("usp-num-samples", "value"),
     Input("usp-project-id", "value"),
     Input("usp-reactor-type", "value")],
    prevent_initial_call=True
)
def generate_usp_sample_table(num_samples, project_id, reactor_type):
    """Generate the sample entry table for USP samples"""
    if not num_samples or num_samples < 1:
        return html.Div()

    # Create columns for the data table
    columns = [
        {"name": "Sample #", "id": "sample_number", "type": "numeric"},
        {"name": "Clone", "id": "cell_line", "type": "text"},
        {"name": "Run Date", "id": "run_date", "type": "datetime"},
        {"name": "Harvest Date", "id": "harvest_date", "type": "datetime"},
        {"name": "Culture Duration", "id": "culture_duration", "type": "numeric"},
        {"name": "Max VCD", "id": "max_vcd", "type": "numeric"},
        {"name": "Viability %", "id": "viability", "type": "numeric"},
        {"name": "Titer (g/L)", "id": "final_titer", "type": "numeric"},
        {"name": "Volume (L)", "id": "culture_volume", "type": "numeric"},
        {"name": "pH", "id": "ph", "type": "numeric"},
        {"name": "DO %", "id": "do_percent", "type": "numeric"},
        {"name": "Temp (°C)", "id": "temperature", "type": "numeric"},
        {"name": "Feed Strategy", "id": "feed_strategy", "type": "text"},
        {"name": "Note", "id": "note", "type": "text"}
    ]

    # Generate initial data with sample numbers
    data = []
    for i in range(num_samples):
        row = {
            "sample_number": i + 1,
            "cell_line": "",
            "run_date": "",
            "harvest_date": "",
            "culture_duration": "",
            "max_vcd": "",
            "viability": "",
            "final_titer": "",
            "culture_volume": "",
            "ph": "",
            "do_percent": "",
            "temperature": "",
            "feed_strategy": "",
            "note": ""
        }
        data.append(row)

    return html.Div([
        # Show project and reactor info
        dbc.Alert([
            html.Strong("Project: "), project_id or "Not specified",
            html.Br(),
            html.Strong("Reactor Type: "), reactor_type or "Not specified"
        ], color="info", className="mb-3") if project_id or reactor_type else None,
        
        # Data table
        dash_table.DataTable(
            id="usp-sample-data-table",
            columns=columns,
            data=data,
            editable=True,
            row_deletable=True,
            style_cell={
                'textAlign': 'left',
                'fontSize': '14px',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': '#1976d2',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'fontSize': '14px'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
                {
                    'if': {'state': 'selected'},
                    'backgroundColor': 'rgb(230, 240, 255)',
                    'border': '1px solid rgb(100, 150, 255)'
                }
            ],
            page_size=20
        )
    ])


# SAVE SAMPLES CALLBACK FOR USP
@app.callback(
    [Output("usp-save-samples-btn", "disabled"),
     Output("usp-calculate-btn", "disabled")],
    [Input("usp-sample-data-table", "data")],
    prevent_initial_call=True
)
def enable_usp_action_buttons(data):
    """Enable/disable action buttons based on data presence"""
    if data and len(data) > 0:
        # Check if at least one row has some data
        has_data = any(
            row.get("cell_line") or row.get("final_titer") 
            for row in data
        )
        return not has_data, not has_data
    return True, True


# SAVE SAMPLES TO DATABASE CALLBACK FOR USP
@app.callback(
    Output("usp-sample-creation-state", "data"),
    [Input("usp-save-samples-btn", "n_clicks")],
    [State("usp-sample-data-table", "data"),
     State("usp-project-id", "value"),
     State("usp-reactor-type", "value")],
    prevent_initial_call=True
)
def save_usp_samples(n_clicks, table_data, project_id, reactor_type):
    """Save USP samples to database"""
    if not n_clicks or not table_data:
        return no_update

    try:
        saved_samples = []
        
        for row in table_data:
            if row.get("cell_line"):  # Only save rows with data
                sample = LimsUpstreamSamples(
                    project_id=project_id,
                    reactor_type=reactor_type,
                    cell_line=row.get("cell_line"),
                    run_date=row.get("run_date") if row.get("run_date") else None,
                    harvest_date=row.get("harvest_date") if row.get("harvest_date") else None,
                    culture_duration=row.get("culture_duration") if row.get("culture_duration") else None,
                    max_vcd=row.get("max_vcd") if row.get("max_vcd") else None,
                    viability=row.get("viability") if row.get("viability") else None,
                    final_titer=row.get("final_titer") if row.get("final_titer") else None,
                    culture_volume=row.get("culture_volume") if row.get("culture_volume") else None,
                    ph=row.get("ph") if row.get("ph") else None,
                    do_percent=row.get("do_percent") if row.get("do_percent") else None,
                    temperature=row.get("temperature") if row.get("temperature") else None,
                    feed_strategy=row.get("feed_strategy"),
                    note=row.get("note"),
                    created_date=datetime.now()
                )
                sample.save()
                saved_samples.append(sample.sample_name)

        return {
            "status": "success",
            "message": f"Saved {len(saved_samples)} USP samples",
            "samples": saved_samples,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error saving USP samples: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


print("USP create_samples callbacks configured successfully")