import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
from django_plotly_dash import DjangoDash
from django.utils import timezone
import logging
import os
import glob

# Initialize the Dash app
app = DjangoDash("OctetImportApp", external_stylesheets=[
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
    dbc.themes.BOOTSTRAP
])

# Enhanced Styles
CARD_STYLE = {
    "margin": "20px 0",
    "padding": "25px",
    "border": "1px solid #dee2e6",
    "border-radius": "12px",
    "box-shadow": "0 4px 6px rgba(0,0,0,0.1)"
}

UPLOAD_STYLE = {
    'width': '100%',
    'height': '180px',
    'lineHeight': '180px',
    'borderWidth': '3px',
    'borderStyle': 'dashed',
    'borderRadius': '15px',
    'textAlign': 'center',
    'backgroundColor': '#f8f9fa',
    'border': '3px dashed #0056b3',
    'cursor': 'pointer',
    'margin': '15px 0'
}

TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "12px 15px",
    "fontSize": "14px",
    "border": "1px solid #dee2e6",
    "fontFamily": "Arial, sans-serif",
    "color": "#333",
    "minWidth": "120px"
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#0056b3",
    "fontWeight": "600",
    "color": "white",
    "textAlign": "center",
    "fontSize": "14px",
    "padding": "15px",
    "fontFamily": "Arial, sans-serif",
    "border": "1px solid #0056b3"
}

# App Layout
app.layout = html.Div([
    dcc.Store(id="file-data-store"),
    dcc.Store(id="preview-data-store"),
    dcc.Store(id="multiple-files-store"),

    html.Div([
        # Header Section
        html.Div([
            html.H2([
                html.I(className="fas fa-file-import me-3"),
                "Octet Data Import"
            ], style={"color": "#0056b3", "margin-bottom": "15px"}),
            html.P("Import Excel files containing Octet binding kinetics data",
                   style={"color": "#6c757d", "margin-bottom": "10px", "fontSize": "16px"}),
            html.Div([
                html.I(className="fas fa-info-circle me-2"),
                "Note: This app will only read data from the 'Results' sheet in your Excel files"
            ], className="alert alert-info", style={"fontSize": "14px", "padding": "10px", "margin-bottom": "0"})
        ], style={"margin-bottom": "25px"}),

        # Import Mode Selection
        html.Div([
            html.Label("Import Mode:", style={"font-weight": "bold", "margin-bottom": "10px"}),
            dcc.RadioItems(
                id="import-mode",
                options=[
                    {"label": " Single File", "value": "single"},
                    {"label": " Multiple Files from Folder", "value": "multiple"}
                ],
                value="single",
                inline=True,
                style={"margin-bottom": "20px"}
            )
        ], style=CARD_STYLE),

        # Single File Upload Section
        html.Div([
            html.H4([
                html.I(className="fas fa-file-upload me-2"),
                "Upload Single File"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt fa-3x",
                           style={"color": "#0056b3", "margin-bottom": "15px"}),
                    html.Br(),
                    html.Strong("Drag and drop your Excel file here"),
                    html.Br(),
                    html.Span("or ", style={"color": "#6c757d"}),
                    html.A("browse", style={"color": "#0056b3", "text-decoration": "underline"})
                ]),
                style=UPLOAD_STYLE,
                multiple=False,
                accept='.xls,.xlsx'
            ),

            html.Div(id='upload-status')
        ], id="single-file-section", style=CARD_STYLE),

        # Multiple Files Section
        html.Div([
            html.H4([
                html.I(className="fas fa-folder-open me-2"),
                "Select Folder for Multiple Files"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            html.Div([
                html.Label("Folder Path:", style={"font-weight": "bold"}),
                dcc.Input(
                    id="folder-path-input",
                    type="text",
                    placeholder="Enter folder path (e.g., /path/to/octet/data)",
                    style={"width": "70%", "padding": "8px", "margin-right": "10px"}
                ),
                html.Button(
                    "Scan Folder",
                    id="scan-folder-btn",
                    className="btn btn-primary",
                    style={"padding": "8px 20px"}
                )
            ], style={"margin-bottom": "20px"}),

            html.Div(id="folder-scan-results")
        ], id="multiple-files-section", style={"display": "none", **CARD_STYLE}),

        # Import Options
        html.Div([
            html.H4([
                html.I(className="fas fa-cog me-2"),
                "Import Options"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            html.Div([
                html.Div([
                    html.Label("Sheet Name/Number (for Excel):",
                               style={"font-weight": "bold", "margin-bottom": "8px"}),
                    dcc.Input(
                        id='sheet-selector-input',
                        type="text",
                        value="Results",
                        placeholder="Sheet name or number (0-based)",
                        style={"width": "100%", "padding": "8px"},
                        disabled=True  # Lock to Results sheet
                    ),
                    html.Small("Locked to 'Results' sheet",
                               style={"color": "#6c757d", "display": "block", "margin-top": "5px"})
                ], style={"width": "30%", "display": "inline-block", "margin-right": "5%"}),

                html.Div([
                    html.Label("Header Row:",
                               style={"font-weight": "bold", "margin-bottom": "8px"}),
                    dcc.Input(
                        id='header-row-input',
                        type="number",
                        value=0,
                        min=0,
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"width": "30%", "display": "inline-block", "margin-right": "5%"}),

                html.Div([
                    html.Label("Skip Rows:",
                               style={"font-weight": "bold", "margin-bottom": "8px"}),
                    dcc.Input(
                        id='skip-rows-input',
                        type="number",
                        value=0,
                        min=0,
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"width": "30%", "display": "inline-block"})
            ], style={"margin-bottom": "20px"}),

            dcc.Checklist(
                id='import-options-checklist',
                options=[
                    {"label": " Skip empty rows", "value": "skip_empty"},
                    {"label": " Skip empty columns", "value": "skip_empty_cols"},
                    {"label": " Show preview before import", "value": "show_preview"}
                ],
                value=["skip_empty", "skip_empty_cols", "show_preview"],
                style={"margin": "15px 0"},
                labelStyle={"margin-right": "25px"}
            )
        ], id='import-options-card', style=CARD_STYLE),

        # Preview Section
        html.Div([
            html.H4([
                html.I(className="fas fa-eye me-2"),
                "Data Preview"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            html.Div(id='preview-table-container'),
            html.Div(id='validation-summary')
        ], id='preview-card', style={'display': 'none', **CARD_STYLE}),

        # Import Actions
        html.Div([
            html.Button([
                html.I(className="fas fa-database me-2"),
                "Import Data"
            ], id='import-btn',
                className="btn btn-success btn-lg",
                disabled=True),

            html.Button([
                html.I(className="fas fa-redo me-2"),
                "Reset"
            ], id='reset-btn',
                className="btn btn-outline-secondary btn-lg",
                style={"margin-left": "15px"})
        ], style={"text-align": "center", "margin": "25px 0"}),

        # Import Results
        html.Div(id='import-results')
    ], style={"max-width": "1200px", "margin": "0 auto", "padding": "20px"})
])


# Helper function to parse Excel file
def parse_excel_file(contents, filename, sheet="Results", header_row=0, skip_rows=0, options=[]):
    """Parse Excel file - specifically reads from Results sheet"""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # First, check if Results sheet exists
        excel_file = pd.ExcelFile(io.BytesIO(decoded))
        available_sheets = excel_file.sheet_names

        # Look for Results sheet (case-insensitive)
        results_sheet = None
        for sheet_name in available_sheets:
            if sheet_name.lower() == "results":
                results_sheet = sheet_name
                break

        if not results_sheet:
            # If no Results sheet found, return error with available sheets
            return None, f"No 'Results' sheet found. Available sheets: {', '.join(available_sheets)}"

        # Read Excel file from Results sheet
        df = pd.read_excel(
            io.BytesIO(decoded),
            sheet_name=results_sheet,
            header=header_row if header_row is not None else 0,
            skiprows=skip_rows if skip_rows > 0 else None
        )

        # Apply options
        if "skip_empty" in options:
            df = df.dropna(how='all')

        if "skip_empty_cols" in options:
            df = df.dropna(axis=1, how='all')

        # Clean column names
        df.columns = df.columns.str.strip()

        return df, None
    except Exception as e:
        return None, str(e)


# Callback: Toggle between single and multiple file modes
@app.callback(
    [Output("single-file-section", "style"),
     Output("multiple-files-section", "style")],
    Input("import-mode", "value")
)
def toggle_import_mode(mode):
    if mode == "single":
        return CARD_STYLE, {"display": "none"}
    else:
        return {"display": "none"}, CARD_STYLE


# Callback: Handle single file upload
@app.callback(
    [Output('upload-status', 'children'),
     Output('file-data-store', 'data'),
     Output('preview-card', 'style'),
     Output('preview-table-container', 'children'),
     Output('import-btn', 'disabled')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename'),
     State('sheet-selector-input', 'value'),
     State('header-row-input', 'value'),
     State('skip-rows-input', 'value'),
     State('import-options-checklist', 'value')]
)
def handle_file_upload(contents, filename, sheet, header_row, skip_rows, options):
    if contents is None:
        return "", None, {'display': 'none'}, "", True

    try:
        # Parse the file
        df, error = parse_excel_file(contents, filename, sheet, header_row, skip_rows, options)

        if error:
            error_msg = html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error reading file: {error}"
            ], className="alert alert-danger")
            return error_msg, None, {'display': 'none'}, "", True

        # Success message
        status_msg = html.Div([
            html.I(className="fas fa-check-circle me-2"),
            f"Successfully loaded '{filename}' - {len(df)} rows, {len(df.columns)} columns"
        ], className="alert alert-success")

        # Store file data
        file_data = {
            'filename': filename,
            'contents': contents,
            'data': df.to_dict('records'),
            'columns': df.columns.tolist()
        }

        # Create preview table if option selected
        preview_content = ""
        preview_style = {'display': 'none'}

        if "show_preview" in options and len(df) > 0:
            preview_style = CARD_STYLE

            # Show first 10 rows
            preview_df = df.head(10)

            preview_content = html.Div([
                html.P(f"Showing first {len(preview_df)} of {len(df)} rows",
                       style={"color": "#6c757d", "margin-bottom": "10px"}),
                dash_table.DataTable(
                    id='preview-table',
                    columns=[{"name": i, "id": i} for i in preview_df.columns],
                    data=preview_df.to_dict('records'),
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER,
                    style_table={'overflowX': 'auto'},
                    page_size=10
                )
            ])

        return status_msg, file_data, preview_style, preview_content, False

    except Exception as e:
        error_msg = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error processing file: {str(e)}"
        ], className="alert alert-danger")
        return error_msg, None, {'display': 'none'}, "", True


# Callback: Scan folder for multiple files
@app.callback(
    [Output("folder-scan-results", "children"),
     Output("multiple-files-store", "data")],
    [Input("scan-folder-btn", "n_clicks")],
    [State("folder-path-input", "value")]
)
def scan_folder(n_clicks, folder_path):
    if not n_clicks or not folder_path:
        return "", None

    try:
        # Check if folder exists
        if not os.path.exists(folder_path):
            return html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Folder not found: {folder_path}"
            ], className="alert alert-danger"), None

        # Find Excel files
        excel_files = []
        for ext in ['*.xls', '*.xlsx']:
            excel_files.extend(glob.glob(os.path.join(folder_path, ext)))

        if not excel_files:
            return html.Div([
                html.I(className="fas fa-info-circle me-2"),
                "No Excel files found in the specified folder"
            ], className="alert alert-info"), None

        # Create file list display
        file_list = html.Div([
            html.P(f"Found {len(excel_files)} Excel files:",
                   style={"font-weight": "bold", "margin-bottom": "10px"}),
            html.Ul([
                html.Li(os.path.basename(f)) for f in excel_files
            ])
        ])

        result = html.Div([
            html.Div([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully scanned folder"
            ], className="alert alert-success"),
            file_list
        ])

        return result, {"folder": folder_path, "files": excel_files}

    except Exception as e:
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error scanning folder: {str(e)}"
        ], className="alert alert-danger"), None


# Callback: Handle data import
@app.callback(
    Output('import-results', 'children'),
    [Input('import-btn', 'n_clicks')],
    [State('file-data-store', 'data'),
     State('multiple-files-store', 'data'),
     State('import-mode', 'value')]
)
def import_data(n_clicks, single_file_data, multiple_files_data, import_mode):
    if not n_clicks:
        return ""

    try:
        results = []

        if import_mode == "single" and single_file_data:
            # Process single file
            df = pd.DataFrame(single_file_data['data'])
            results.append({
                'filename': single_file_data['filename'],
                'rows': len(df),
                'status': 'success'
            })

            # Here you would normally save to database
            # For now, just show success message

        elif import_mode == "multiple" and multiple_files_data:
            # Process multiple files
            for file_path in multiple_files_data['files']:
                try:
                    # First check if Results sheet exists
                    excel_file = pd.ExcelFile(file_path)
                    available_sheets = excel_file.sheet_names

                    results_sheet = None
                    for sheet_name in available_sheets:
                        if sheet_name.lower() == "results":
                            results_sheet = sheet_name
                            break

                    if not results_sheet:
                        results.append({
                            'filename': os.path.basename(file_path),
                            'rows': 0,
                            'status': 'error',
                            'error': f"No 'Results' sheet found. Available: {', '.join(available_sheets)}"
                        })
                        continue

                    # Read from Results sheet
                    df = pd.read_excel(file_path, sheet_name=results_sheet)
                    df = df.dropna(how='all')  # Remove empty rows
                    df = df.dropna(axis=1, how='all')  # Remove empty columns

                    results.append({
                        'filename': os.path.basename(file_path),
                        'rows': len(df),
                        'status': 'success'
                    })
                except Exception as e:
                    results.append({
                        'filename': os.path.basename(file_path),
                        'rows': 0,
                        'status': 'error',
                        'error': str(e)
                    })

        # Create results summary
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        total_rows = sum(r['rows'] for r in results if r['status'] == 'success')

        summary = html.Div([
            html.H4([
                html.I(className="fas fa-chart-bar me-2"),
                "Import Summary"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            html.Div([
                html.Div([
                    html.H3(str(len(results)), style={"color": "#0056b3", "margin": "0"}),
                    html.P("Files Processed", style={"margin": "0"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "30%", "display": "inline-block", "margin": "1%"}),

                html.Div([
                    html.H3(str(success_count), style={"color": "#28a745", "margin": "0"}),
                    html.P("Successful", style={"margin": "0"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "30%", "display": "inline-block", "margin": "1%"}),

                html.Div([
                    html.H3(str(total_rows), style={"color": "#17a2b8", "margin": "0"}),
                    html.P("Total Rows", style={"margin": "0"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "30%", "display": "inline-block", "margin": "1%"})
            ]),

            # Detail table
            html.Div([
                html.H5("File Details:", style={"margin-top": "20px", "margin-bottom": "10px"}),
                dash_table.DataTable(
                    columns=[
                        {"name": "Filename", "id": "filename"},
                        {"name": "Rows", "id": "rows"},
                        {"name": "Status", "id": "status"}
                    ],
                    data=results,
                    style_cell=TABLE_STYLE_CELL,
                    style_header=TABLE_STYLE_HEADER,
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'status', 'filter_query': '{status} = success'},
                            'color': 'green',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'column_id': 'status', 'filter_query': '{status} = error'},
                            'color': 'red',
                            'fontWeight': 'bold'
                        }
                    ]
                )
            ], style={"margin-top": "20px"})
        ], style=CARD_STYLE)

        return summary

    except Exception as e:
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error during import: {str(e)}"
        ], className="alert alert-danger", style={"margin": "20px 0"})


# Callback: Reset the form
@app.callback(
    [Output('upload-data', 'contents'),
     Output('folder-path-input', 'value')],
    [Input('reset-btn', 'n_clicks')]
)
def reset_form(n_clicks):
    if n_clicks:
        return None, ""
    return dash.no_update, dash.no_update


if __name__ == '__main__':
    app.run_server(debug=True)