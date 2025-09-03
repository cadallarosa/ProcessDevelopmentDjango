import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

# USP Sample field definitions
USP_SAMPLE_CREATE_FIELDS = [
    {"name": "Sample #", "id": "sample_number", "editable": True, "type": "numeric"},
    {"name": "Project", "id": "project", "editable": True},
    {"name": "Cell Line", "id": "cell_line", "editable": True},
    {"name": "Experiment #", "id": "experiment_number", "editable": True, "type": "numeric"},
    {"name": "Culture Duration", "id": "culture_duration", "editable": True, "type": "numeric"},
    {"name": "Vessel Type", "id": "vessel_type", "editable": True},
    {"name": "Description", "id": "description", "editable": True},
    {"name": "Dev Stage", "id": "development_stage", "editable": True},
    {"name": "Analyst", "id": "analyst", "editable": True},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Unifi Number", "id": "unifi_number", "editable": True}
]


def create_usp_create_samples_layout():
    """Create the USP sample creation layout"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-plus-circle text-success me-2"),
                    "Create USP Samples"
                ]),
                html.P("Add new upstream process samples for cell culture experiments",
                       className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-eye me-1"),
                        "View Samples"
                    ], href="#!/usp/samples/view", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-layer-group me-1"),
                        "Sample Sets"
                    ], href="#!/usp/sample-sets", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Creation method selection
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Sample Creation Method", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.RadioItems(
                                    id="usp-creation-method",
                                    options=[
                                        {"label": "Manual Entry", "value": "manual"},
                                        {"label": "Template Import", "value": "template"},
                                        {"label": "Bulk Upload", "value": "upload"}
                                    ],
                                    value="manual",
                                    inline=True
                                )
                            ])
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Dynamic content area
        dbc.Row([
            dbc.Col([
                html.Div(id="usp-creation-method-content")
            ])
        ]),

        # Download component for templates
        dcc.Download(id="usp-download-template-file"),
        
        # Store for upload preview
        dcc.Store(id="usp-upload-preview-store")

    ], fluid=True, style={"padding": "20px"})


def create_manual_entry_section():
    """Create manual entry form for USP samples"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Manual Sample Entry", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Form([
                # Row 1: Sample Number, Project, Cell Line
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Sample Number *", className="fw-bold"),
                        dbc.Input(
                            id="usp-sample-number-input",
                            type="number",
                            placeholder="Enter sample number...",
                            required=True
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Project *", className="fw-bold"),
                        dbc.Input(
                            id="usp-project-input",
                            placeholder="Enter project ID...",
                            required=True
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Cell Line", className="fw-bold"),
                        dbc.Input(
                            id="usp-cell-line-input",
                            placeholder="Enter cell line..."
                        )
                    ], md=4)
                ], className="mb-3"),

                # Row 2: Experiment Number, Culture Duration, Vessel Type
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Experiment Number", className="fw-bold"),
                        dbc.Input(
                            id="usp-experiment-number-input",
                            type="number",
                            placeholder="Enter experiment #..."
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Culture Duration (days)", className="fw-bold"),
                        dbc.Input(
                            id="usp-culture-duration-input",
                            type="number",
                            placeholder="Enter duration..."
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Vessel Type", className="fw-bold"),
                        dbc.Select(
                            id="usp-vessel-type-input",
                            options=[
                                {"label": "Bioreactor", "value": "Bioreactor"},
                                {"label": "Shake Flask", "value": "Shake Flask"},
                                {"label": "Ambr250", "value": "Ambr250"},
                                {"label": "Ambr15", "value": "Ambr15"},
                                {"label": "Other", "value": "Other"}
                            ],
                            placeholder="Select vessel type..."
                        )
                    ], md=4)
                ], className="mb-3"),

                # Row 3: Description, Development Stage
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Description", className="fw-bold"),
                        dbc.Textarea(
                            id="usp-description-input",
                            placeholder="Enter sample description..."
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Development Stage", className="fw-bold"),
                        dbc.Select(
                            id="usp-development-stage-input",
                            options=[
                                {"label": "Research", "value": "Research"},
                                {"label": "Development", "value": "Development"},
                                {"label": "Process Dev", "value": "Process Dev"},
                                {"label": "Scale-up", "value": "Scale-up"},
                                {"label": "Production", "value": "Production"}
                            ],
                            placeholder="Select development stage..."
                        )
                    ], md=6)
                ], className="mb-3"),

                # Row 4: Analyst, Harvest Date, Unifi Number
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Analyst", className="fw-bold"),
                        dbc.Input(
                            id="usp-analyst-input",
                            placeholder="Enter analyst name..."
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Harvest Date", className="fw-bold"),
                        dbc.Input(
                            id="usp-harvest-date-input",
                            type="date"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Unifi Number", className="fw-bold"),
                        dbc.Input(
                            id="usp-unifi-number-input",
                            placeholder="Enter Unifi number..."
                        )
                    ], md=4)
                ], className="mb-4"),

                # Submit button
                dbc.Row([
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-plus me-2"),
                            "Create Sample"
                        ], id="usp-create-manual-sample-btn", color="success", size="lg")
                    ], className="text-center")
                ])
            ]),

            # Status messages
            html.Div(id="usp-manual-creation-status", className="mt-3")
        ])
    ], className="shadow-sm")


def create_template_import_section():
    """Create template import section for USP samples"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Template Import", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Download the template, fill it with your USP sample data, then upload it back."
            ], color="info", className="mb-3"),

            dbc.Row([
                dbc.Col([
                    html.H6("Step 1: Download Template"),
                    html.P("Choose your preferred template format:", className="text-muted"),
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-file-csv me-2"),
                            "Download CSV Template"
                        ], id="usp-download-template-btn", color="primary"),
                        dbc.Button([
                            html.I(className="fas fa-file-excel me-2"),
                            "Download Excel Template"
                        ], id="usp-download-excel-template-btn", color="success")
                    ])
                ], md=6),
                dbc.Col([
                    html.H6("Step 2: Upload Completed Template"),
                    html.P("Upload your filled template file:", className="text-muted"),
                    dcc.Upload(
                        id="usp-template-upload",
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                            html.Br(),
                            "Drag and drop or click to select file"
                        ], className="text-center py-3"),
                        style={
                            'width': '100%',
                            'height': '80px',
                            'lineHeight': '80px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '10px',
                            'borderColor': '#ccc',
                            'textAlign': 'center',
                            'backgroundColor': '#fafafa'
                        },
                        multiple=False,
                        accept='.csv,.xlsx,.xls'
                    )
                ], md=6)
            ]),

            html.Div(id="usp-template-import-status", className="mt-3")
        ])
    ], className="shadow-sm")


def create_bulk_upload_section():
    """Create bulk upload section for USP samples"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Bulk Upload", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Upload a CSV or Excel file with your USP sample data. Required columns: sample_number, project"
            ], color="info", className="mb-3"),

            dcc.Upload(
                id="usp-upload-data",
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt fa-3x mb-3 text-primary"),
                    html.H5("Drag and Drop or Click to Select File"),
                    html.P("Supports CSV and Excel files", className="text-muted")
                ], className="text-center py-4"),
                style={
                    'width': '100%',
                    'height': '150px',
                    'lineHeight': '150px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '10px',
                    'borderColor': '#007bff',
                    'textAlign': 'center',
                    'backgroundColor': '#f8f9fa'
                },
                multiple=False,
                accept='.csv,.xlsx,.xls'
            ),

            # Upload status and preview
            html.Div(id="usp-upload-status", className="mt-3"),
            html.Div(id="usp-upload-preview", className="mt-3")
        ])
    ], className="shadow-sm")


print("✅ USP Create Samples Layout loaded successfully")