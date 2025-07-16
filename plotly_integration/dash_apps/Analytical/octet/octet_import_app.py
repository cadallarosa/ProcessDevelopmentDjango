import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
from django_plotly_dash import DjangoDash
# from plotly_integration.models import OctetResult  # Commented out until model is created
from django.utils import timezone
import logging

# Initialize the Dash app
app = DjangoDash("OctetImportApp", external_stylesheets=[
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
    dbc.themes.BOOTSTRAP
])

# Enhanced Styles with better margins
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
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="file-data-store"),
    dcc.Store(id="preview-data-store"),
    dcc.Store(id="edited-data-store"),
    dcc.Store(id="import-status-store", data="idle"),

    html.Div([
        # Header Section
        html.Div([
            html.H2([
                html.I(className="fas fa-file-import me-3"),
                "Octet Data Import"
            ], style={"color": "#0056b3", "margin-bottom": "15px"}),
            html.P("Import Excel or CSV files containing Octet binding kinetics data",
                   style={"color": "#6c757d", "margin-bottom": "30px", "fontSize": "16px"})
        ], style={"margin-bottom": "25px"}),

        # Main Tabs
        dcc.Tabs(
            id="main-tabs",
            value="results-tab",
            children=[
                dcc.Tab(
                    label="Import Results",
                    value="results-tab",
                    style={"padding": "12px 24px", "fontWeight": "bold"},
                    selected_style={"padding": "12px 24px", "fontWeight": "bold", "backgroundColor": "#0056b3",
                                    "color": "white"}
                ),
                dcc.Tab(
                    label="Upload File",
                    value="upload-tab",
                    style={"padding": "12px 24px", "fontWeight": "bold"},
                    selected_style={"padding": "12px 24px", "fontWeight": "bold", "backgroundColor": "#0056b3",
                                    "color": "white"}
                ),
                dcc.Tab(
                    label="Data Validation",
                    value="validation-tab",
                    style={"padding": "12px 24px", "fontWeight": "bold"},
                    selected_style={"padding": "12px 24px", "fontWeight": "bold", "backgroundColor": "#0056b3",
                                    "color": "white"}
                )
            ],
            style={"margin-bottom": "30px"}
        ),

        # Tab Content
        html.Div(id="tab-content")

    ], style={"max-width": "1400px", "margin": "0 auto", "padding": "30px"})
])


# Callback: Handle tab switching
@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value')]
)
def render_tab_content(active_tab):
    if active_tab == 'upload-tab':
        return create_upload_tab()
    elif active_tab == 'validation-tab':
        return create_validation_tab()
    else:  # results-tab (default)
        return create_results_tab()


def create_upload_tab():
    return html.Div([
        # File Upload Card
        html.Div([
            html.H4([
                html.I(className="fas fa-upload me-3"),
                "File Upload"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.I(className="fas fa-file-excel",
                           style={"font-size": "56px", "color": "#28a745", "margin-bottom": "20px"}),
                    html.Br(),
                    html.Div("Drag and Drop or Click to Select Files",
                             style={"font-size": "18px", "font-weight": "bold", "margin-bottom": "8px"}),
                    html.Div("Supports .xlsx, .xls, and .csv files (Max 10MB)",
                             style={"font-size": "14px", "color": "#6c757d"})
                ]),
                style=UPLOAD_STYLE,
                multiple=False,
                accept='.xlsx,.xls,.csv'
            ),

            # Upload Status
            html.Div(id='upload-status', style={"margin": "20px 0"}),

            # Action buttons
            html.Div([
                html.Button([
                    html.I(className="fas fa-download me-2"),
                    "Download Template"
                ], id='download-template-btn',
                    className="btn btn-outline-primary btn-lg",
                    style={"margin": "15px 10px 15px 0"}),

                html.Button([
                    html.I(className="fas fa-question-circle me-2"),
                    "View Help"
                ], id='help-btn',
                    className="btn btn-outline-info btn-lg",
                    style={"margin": "15px 0"})
            ])
        ], style=CARD_STYLE),

        # Import Options Card
        html.Div([
            html.H4([
                html.I(className="fas fa-cog me-3"),
                "Import Configuration"
            ], style={"color": "#0056b3", "margin-bottom": "25px"}),

            html.Div([
                # Row 1: Main options
                html.Div([
                    html.Div([
                        html.Label("Select Sheet:",
                                   style={"font-weight": "bold", "margin-bottom": "8px", "display": "block"}),
                        dcc.Dropdown(
                            id='sheet-selector',
                            placeholder="Choose sheet to import",
                            style={"margin-bottom": "20px"}
                        )
                    ], style={"width": "30%", "display": "inline-block", "margin-right": "5%"}),

                    html.Div([
                        html.Label("Header Row:",
                                   style={"font-weight": "bold", "margin-bottom": "8px", "display": "block"}),
                        dcc.Input(
                            id='header-row-input',
                            type="number",
                            value=1,
                            min=1,
                            style={"width": "100%", "margin-bottom": "20px", "padding": "8px"}
                        )
                    ], style={"width": "30%", "display": "inline-block", "margin-right": "5%"}),

                    html.Div([
                        html.Label("Data Start Row:",
                                   style={"font-weight": "bold", "margin-bottom": "8px", "display": "block"}),
                        dcc.Input(
                            id='data-start-row-input',
                            type="number",
                            value=2,
                            min=2,
                            style={"width": "100%", "margin-bottom": "20px", "padding": "8px"}
                        )
                    ], style={"width": "30%", "display": "inline-block"})
                ], style={"margin-bottom": "25px"}),

                # Row 2: Options checkboxes
                html.Div([
                    html.Label("Import Options:",
                               style={"font-weight": "bold", "margin-bottom": "15px", "display": "block"}),
                    dcc.Checklist(
                        id='import-options-checklist',
                        options=[
                            {"label": " Skip empty rows", "value": "skip_empty"},
                            {"label": " Update existing records", "value": "update_existing"},
                            {"label": " Validate data types", "value": "validate_types"},
                            {"label": " Auto-generate missing IDs", "value": "auto_generate_ids"}
                        ],
                        value=["skip_empty", "validate_types"],
                        style={"margin": "15px 0"},
                        labelStyle={"margin-right": "25px", "margin-bottom": "10px"}
                    )
                ])
            ])
        ], id='import-options-card', style={'display': 'none', **CARD_STYLE})
    ])


def create_results_tab():
    return html.Div([
        # Current Data Summary
        html.Div([
            html.H4([
                html.I(className="fas fa-database me-3"),
                "Current Database Summary"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            html.Div([
                html.Div([
                    html.H3("0", id="total-records", style={"color": "#0056b3", "margin": "0"}),
                    html.P("Total Records", style={"margin": "0", "font-size": "14px"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "23%", "display": "inline-block", "margin": "1%"}),

                html.Div([
                    html.H3("0", id="recent-imports", style={"color": "#28a745", "margin": "0"}),
                    html.P("Recent Imports", style={"margin": "0", "font-size": "14px"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "23%", "display": "inline-block", "margin": "1%"}),

                html.Div([
                    html.H3("0", id="validation-pending", style={"color": "#ffc107", "margin": "0"}),
                    html.P("Pending Validation", style={"margin": "0", "font-size": "14px"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "23%", "display": "inline-block", "margin": "1%"}),

                html.Div([
                    html.H3("95%", id="data-quality-score", style={"color": "#17a2b8", "margin": "0"}),
                    html.P("Quality Score", style={"margin": "0", "font-size": "14px"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "23%", "display": "inline-block", "margin": "1%"})
            ], style={"margin-bottom": "25px"})
        ], style=CARD_STYLE),

        # Recent Import History
        html.Div([
            html.H4([
                html.I(className="fas fa-history me-3"),
                "Recent Import History"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            html.Div(id='import-history-table', children=[
                html.P("No recent imports found. Upload a file to get started.",
                       style={"text-align": "center", "color": "#6c757d", "margin": "40px 0"})
            ])
        ], style=CARD_STYLE),

        # Quick Actions
        html.Div([
            html.H4([
                html.I(className="fas fa-tools me-3"),
                "Quick Actions"
            ], style={"color": "#0056b3", "margin-bottom": "20px"}),

            html.Div([
                html.Button([
                    html.I(className="fas fa-plus me-2"),
                    "New Import"
                ], className="btn btn-primary btn-lg",
                    style={"margin": "10px"}, id="new-import-btn"),

                html.Button([
                    html.I(className="fas fa-check-double me-2"),
                    "Bulk Validate"
                ], className="btn btn-success btn-lg",
                    style={"margin": "10px"}, id="bulk-validate-btn"),

                html.Button([
                    html.I(className="fas fa-download me-2"),
                    "Export Data"
                ], className="btn btn-info btn-lg",
                    style={"margin": "10px"}, id="export-data-btn"),

                html.Button([
                    html.I(className="fas fa-trash me-2"),
                    "Clear Invalid"
                ], className="btn btn-warning btn-lg",
                    style={"margin": "10px"}, id="clear-invalid-btn")
            ], style={"text-align": "center", "margin": "20px 0"})
        ], style=CARD_STYLE)
    ])


def create_validation_tab():
    return html.Div([
        # Data Preview Card
        html.Div([
            html.Div([
                html.H4([
                    html.I(className="fas fa-eye me-3"),
                    "Data Preview & Validation"
                ], style={"color": "#0056b3", "display": "inline-block"}),

                html.Div([
                    html.Button([
                        html.I(className="fas fa-chevron-up me-2"),
                        "Hide Preview"
                    ], id='toggle-preview-btn',
                        className="btn btn-outline-secondary",
                        style={"margin-left": "15px"}),

                    html.Button([
                        html.I(className="fas fa-magic me-2"),
                        "Auto-Fix Issues"
                    ], id='auto-fix-btn',
                        className="btn btn-outline-warning",
                        style={"margin-left": "10px"})
                ], style={"float": "right"})
            ], style={"margin-bottom": "25px", "overflow": "hidden"}),

            # Validation Summary
            html.Div(id='validation-summary', style={"margin-bottom": "20px"}),

            html.Div(id='preview-content', children=[
                html.Div(id='preview-table-container')
            ])
        ], id='preview-card', style={'display': 'none', **CARD_STYLE}),

        # Import Actions
        html.Div([
            html.Div([
                html.H5("Ready to Import", style={"color": "#28a745", "margin-bottom": "20px"}),

                html.Button([
                    html.I(className="fas fa-upload me-2"),
                    "Import Data to Database"
                ], id='import-btn',
                    className="btn btn-primary btn-lg",
                    style={"margin-right": "15px"}),

                html.Button([
                    html.I(className="fas fa-times me-2"),
                    "Cancel Import"
                ], id='cancel-btn',
                    className="btn btn-secondary btn-lg"),

                html.Button([
                    html.I(className="fas fa-save me-2"),
                    "Save as Draft"
                ], id='save-draft-btn',
                    className="btn btn-outline-info btn-lg",
                    style={"margin-left": "15px"})
            ], style={"text-align": "center", "margin": "25px 0"})
        ], id='import-actions', style={'display': 'none', **CARD_STYLE}),

        # Import Results Card
        html.Div(id='import-results')
    ])


# Callback: Handle file upload
@app.callback(
    [Output('upload-status', 'children'),
     Output('import-options-card', 'style'),
     Output('sheet-selector', 'options'),
     Output('sheet-selector', 'value'),
     Output('file-data-store', 'data')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def handle_file_upload(contents, filename):
    if contents is None:
        return "", {'display': 'none'}, [], None, None

    try:
        # Decode the file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Determine file type and read sheets
        if filename.endswith('.csv'):
            sheets = ['Sheet1']
        else:
            try:
                excel_file = pd.ExcelFile(io.BytesIO(decoded))
                sheets = excel_file.sheet_names
            except Exception as e:
                return html.Div([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error reading Excel file: {str(e)}"
                ], className="alert alert-danger", style={"margin": "20px 0"}), {'display': 'none'}, [], None, None

        # Create sheet options
        sheet_options = [{'label': sheet, 'value': sheet} for sheet in sheets]

        # Success message with file info
        file_size = len(decoded) / (1024 * 1024)  # MB
        status_msg = html.Div([
            html.I(className="fas fa-check-circle me-2"),
            html.Strong(f"File '{filename}' uploaded successfully!"),
            html.Br(),
            html.Small(f"Size: {file_size:.2f} MB | Sheets: {len(sheets)} | Type: {filename.split('.')[-1].upper()}")
        ], className="alert alert-success", style={"margin": "20px 0"})

        # Store file data
        file_data = {
            'filename': filename,
            'contents': contents,
            'sheets': sheets,
            'size': file_size
        }

        card_style = {'display': 'block', **CARD_STYLE}

        return status_msg, card_style, sheet_options, sheets[0], file_data

    except Exception as e:
        error_msg = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error processing file: {str(e)}"
        ], className="alert alert-danger", style={"margin": "20px 0"})
        return error_msg, {'display': 'none'}, [], None, None


# Callback: Update preview when options change (SHOW ALL ROWS)
@app.callback(
    [Output('preview-card', 'style'),
     Output('preview-table-container', 'children'),
     Output('validation-summary', 'children'),
     Output('import-actions', 'style'),
     Output('preview-data-store', 'data')],
    [Input('sheet-selector', 'value'),
     Input('header-row-input', 'value'),
     Input('data-start-row-input', 'value'),
     Input('import-options-checklist', 'value')],
    [State('file-data-store', 'data')]
)
def update_preview(selected_sheet, header_row, data_start_row, options, file_data):
    if not file_data or not selected_sheet:
        return {'display': 'none'}, "", "", {'display': 'none'}, None

    try:
        # Decode file
        content_type, content_string = file_data['contents'].split(',')
        decoded = base64.b64decode(content_string)

        # Read data with specified options
        skip_empty = "skip_empty" in (options or [])
        validate_types = "validate_types" in (options or [])

        if file_data['filename'].endswith('.csv'):
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                skiprows=max(0, data_start_row - 1)
            )
        else:
            df = pd.read_excel(
                io.BytesIO(decoded),
                sheet_name=selected_sheet,
                header=header_row - 1,
                skiprows=range(1, max(1, data_start_row - 1)) if data_start_row > 1 else None
            )

        if skip_empty:
            df = df.dropna(how='all')

        # Data validation
        validation_issues = []
        if validate_types:
            validation_issues = validate_data_quality(df)

        # Create validation summary
        validation_summary = create_validation_summary(df, validation_issues)

        # Store full dataframe info for import
        preview_data = {
            'columns': df.columns.tolist(),
            'row_count': len(df),
            'data': df.to_dict('records'),
            'validation_issues': validation_issues
        }

        # Create editable preview table (ALL ROWS)
        if len(df) > 0:
            # Make Sample ID column editable
            columns = []
            for col in df.columns:
                if any(sample_col in col.lower() for sample_col in ['sample_id', 'sampleid', 'sample id', 'id']):
                    columns.append({
                        "name": str(col),
                        "id": str(col),
                        "editable": True,
                        "type": "text"
                    })
                else:
                    columns.append({
                        "name": str(col),
                        "id": str(col),
                        "editable": False
                    })

            preview_table = dash_table.DataTable(
                id='editable-preview-table',
                data=df.to_dict('records'),
                columns=columns,
                style_cell=TABLE_STYLE_CELL,
                style_header=TABLE_STYLE_HEADER,
                style_table={'overflowX': 'auto', 'border': '1px solid #dee2e6', 'margin': '20px 0'},
                page_size=50,
                page_action='native',
                sort_action='native',
                filter_action='native',
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    },
                    {
                        'if': {'column_editable': True},
                        'backgroundColor': '#fff3cd',
                        'border': '2px solid #ffc107'
                    }
                ]
            )

            preview_content = html.Div([
                html.P(f"Showing all {len(df)} rows of data. Sample ID columns are editable (highlighted in yellow):",
                       style={"margin-bottom": "15px", "font-weight": "bold", "color": "#0056b3"}),
                preview_table
            ])
        else:
            preview_content = html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "No data found with current settings. Please adjust the import options."
            ], className="alert alert-warning", style={"margin": "20px 0"})

        card_style = {'display': 'block', **CARD_STYLE}
        actions_style = {'display': 'block', **CARD_STYLE}

        return card_style, preview_content, validation_summary, actions_style, preview_data

    except Exception as e:
        error_msg = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error previewing data: {str(e)}"
        ], className="alert alert-warning", style={"margin": "20px 0"})
        return {'display': 'block', **CARD_STYLE}, error_msg, "", {'display': 'none'}, None


# Callback: Store edited data
@app.callback(
    Output('edited-data-store', 'data'),
    [Input('editable-preview-table', 'data')],
    prevent_initial_call=True
)
def store_edited_data(table_data):
    return table_data


# Callback: Toggle preview visibility
@app.callback(
    [Output('preview-content', 'style'),
     Output('toggle-preview-btn', 'children')],
    [Input('toggle-preview-btn', 'n_clicks')],
    [State('preview-content', 'style')]
)
def toggle_preview(n_clicks, current_style):
    if n_clicks is None:
        return {'display': 'block'}, [html.I(className="fas fa-chevron-up me-2"), "Hide Preview"]

    if current_style and current_style.get('display') == 'none':
        return {'display': 'block'}, [html.I(className="fas fa-chevron-up me-2"), "Hide Preview"]
    else:
        return {'display': 'none'}, [html.I(className="fas fa-chevron-down me-2"), "Show Preview"]


# Callback: Handle navigation buttons
@app.callback(
    Output('main-tabs', 'value'),
    [Input('new-import-btn', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_to_upload(n_clicks):
    if n_clicks:
        return 'upload-tab'
    return 'results-tab'


# Callback: Handle data import (commented out database operations)
@app.callback(
    Output('import-results', 'children'),
    [Input('import-btn', 'n_clicks')],
    [State('edited-data-store', 'data'),
     State('file-data-store', 'data'),
     State('import-options-checklist', 'value')]
)
def import_data(n_clicks, edited_data, file_data, options):
    if not n_clicks or not edited_data:
        return ""

    try:
        # Use edited data if available
        df = pd.DataFrame(edited_data)

        # Process the data (DATABASE OPERATIONS COMMENTED OUT)
        results = process_octet_data_mock(df, options)

        # Create results display
        if results['successful_imports'] > 0:
            alert_class = "alert-success"
            icon_class = "fas fa-check-circle text-success"
        elif results['errors'] > 0:
            alert_class = "alert-warning"
            icon_class = "fas fa-exclamation-triangle text-warning"
        else:
            alert_class = "alert-danger"
            icon_class = "fas fa-times-circle text-danger"

        results_content = html.Div([
            html.H4([
                html.I(className=f"{icon_class} me-3"),
                "Import Results"
            ], style={"margin-bottom": "25px"}),

            # Statistics Cards
            html.Div([
                html.Div([
                    html.H3(str(results['total_rows']),
                            style={"color": "#0056b3", "margin": "0"}),
                    html.P("Total Rows", style={"margin": "0", "font-size": "14px"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "22%", "display": "inline-block", "margin": "1.5%"}),

                html.Div([
                    html.H3(str(results['successful_imports']),
                            style={"color": "#28a745", "margin": "0"}),
                    html.P("Successful", style={"margin": "0", "font-size": "14px"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "22%", "display": "inline-block", "margin": "1.5%"}),

                html.Div([
                    html.H3(str(results['errors']),
                            style={"color": "#dc3545", "margin": "0"}),
                    html.P("Errors", style={"margin": "0", "font-size": "14px"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "22%", "display": "inline-block", "margin": "1.5%"}),

                html.Div([
                    html.H3(str(results['warnings']),
                            style={"color": "#ffc107", "margin": "0"}),
                    html.P("Warnings", style={"margin": "0", "font-size": "14px"})
                ], style={"text-align": "center", "padding": "20px", "border": "1px solid #dee2e6",
                          "border-radius": "8px", "width": "22%", "display": "inline-block", "margin": "1.5%"})
            ], style={"margin": "25px 0"}),

            # Error details if any
            html.Div([
                html.H5("Issues Found:", style={"margin-top": "25px", "color": "#dc3545"}),
                html.Ul([
                    html.Li(error, style={"margin": "8px 0"})
                    for error in results.get('error_details', [])[:10]
                ])
            ]) if results.get('error_details') else "",

            # Action buttons
            html.Div([
                html.Button([
                    html.I(className="fas fa-plus me-2"),
                    "Import Another File"
                ], id='import-another-btn',
                    className="btn btn-primary btn-lg",
                    style={"margin": "15px"}),

                html.Button([
                    html.I(className="fas fa-table me-2"),
                    "View All Results"
                ], id='view-results-btn',
                    className="btn btn-outline-primary btn-lg",
                    style={"margin": "15px"}),

                html.Button([
                    html.I(className="fas fa-download me-2"),
                    "Export Results"
                ], id='export-results-btn',
                    className="btn btn-outline-success btn-lg",
                    style={"margin": "15px"})
            ], style={"text-align": "center", "margin-top": "25px"})

        ], className=f"alert {alert_class}", style={"margin-top": "25px"})

        return results_content

    except Exception as e:
        error_result = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Import failed: {str(e)}"
        ], className="alert alert-danger", style={"margin-top": "25px"})
        return error_result


# Callback: Reset form
@app.callback(
    [Output('upload-data', 'contents'),
     Output('file-data-store', 'data')],
    [Input('cancel-btn', 'n_clicks'),
     Input('import-another-btn', 'n_clicks')],
    prevent_initial_call=True
)
def reset_form(cancel_clicks, import_another_clicks):
    if cancel_clicks or import_another_clicks:
        return None, None
    return dash.no_update, dash.no_update


def validate_data_quality(df):
    """Validate data quality and return list of issues"""
    issues = []

    # Check for required columns
    required_cols = ['sample_id', 'sampleid', 'sample id', 'id']
    has_sample_id = any(any(req_col in col.lower() for req_col in required_cols) for col in df.columns)

    if not has_sample_id:
        issues.append("No Sample ID column found")

    # Check for empty sample IDs
    for col in df.columns:
        if any(req_col in col.lower() for req_col in required_cols):
            empty_ids = df[col].isna().sum()
            if empty_ids > 0:
                issues.append(f"{empty_ids} empty Sample IDs found")

    # Check for duplicate sample IDs
    sample_id_cols = [col for col in df.columns if any(req_col in col.lower() for req_col in required_cols)]
    for col in sample_id_cols:
        duplicates = df[col].duplicated().sum()
        if duplicates > 0:
            issues.append(f"{duplicates} duplicate Sample IDs found")

    # Check data types for numeric columns
    numeric_indicators = ['rate', 'kd', 'ka', 'response', 'chi', 'affinity']
    for col in df.columns:
        if any(indicator in col.lower() for indicator in numeric_indicators):
            try:
                pd.to_numeric(df[col], errors='raise')
            except:
                non_numeric = df[col].apply(
                    lambda x: not pd.isna(x) and not str(x).replace('.', '').replace('e', '').replace('+', '').replace(
                        '-', '').isdigit()).sum()
                if non_numeric > 0:
                    issues.append(f"{non_numeric} non-numeric values in {col}")

    return issues


def create_validation_summary(df, issues):
    """Create validation summary display"""
    if not issues:
        return html.Div([
            html.I(className="fas fa-check-circle me-2 text-success"),
            html.Strong("Data validation passed! "),
            f"Found {len(df)} valid records ready for import."
        ], className="alert alert-success", style={"margin": "20px 0"})
    else:
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
            html.Strong(f"Found {len(issues)} validation issues:"),
            html.Ul([html.Li(issue) for issue in issues], style={"margin-top": "10px"})
        ], className="alert alert-warning", style={"margin": "20px 0"})


def process_octet_data_mock(df, options=None):
    """Mock function for processing data (DATABASE OPERATIONS COMMENTED OUT)"""
    success_count = 0
    error_count = 0
    warning_count = 0
    error_details = []

    # Simulate processing
    for index, row in df.iterrows():
        try:
            # Basic validation
            sample_id_cols = [col for col in df.columns if
                              any(req_col in col.lower() for req_col in ['sample_id', 'sampleid', 'sample id', 'id'])]

            if not sample_id_cols:
                error_details.append(f"Row {index + 1}: No sample ID column found")
                error_count += 1
                continue

            sample_id = row[sample_id_cols[0]] if sample_id_cols else None
            if pd.isna(sample_id) or str(sample_id).strip() == '':
                error_details.append(f"Row {index + 1}: Missing or empty sample ID")
                error_count += 1
                continue

            # Mock database operation (COMMENTED OUT)
            # octet_data = prepare_octet_data(row, sample_id)
            # OctetResult.objects.create(**octet_data)

            success_count += 1

        except Exception as e:
            error_count += 1
            error_details.append(f"Row {index + 1}: {str(e)}")

    return {
        'total_rows': len(df),
        'successful_imports': success_count,
        'errors': error_count,
        'warnings': warning_count,
        'error_details': error_details
    }