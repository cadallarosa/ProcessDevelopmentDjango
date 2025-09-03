# USP create_samples layout - Adapted for Upstream Processing samples
import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from plotly_integration.pd_dashboard.shared.styles.common_styles import (
    TABLE_STYLE_CELL, TABLE_STYLE_HEADER, CARD_STYLE,
    INPUT_STYLE, DROPDOWN_STYLE, BUTTON_STYLE_PRIMARY
)

# Field definitions for USP samples - specific to upstream processing
USP_SAMPLE_CREATE_FIELDS = [
    {"name": "Sample #", "id": "sample_number", "editable": True, "type": "numeric"},
    {"name": "Project ID", "id": "project_id", "editable": True},
    {"name": "Reactor Type", "id": "reactor_type", "editable": True, 
     "presentation": "dropdown"},  # Will be dropdown with options like "Bioreactor", "Flask", "Wave"
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "Run Date", "id": "run_date", "editable": True, "type": "datetime"},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Culture Duration (days)", "id": "culture_duration", "editable": True, "type": "numeric"},
    {"name": "Max VCD (cells/mL)", "id": "max_vcd", "editable": True, "type": "numeric"},
    {"name": "Viability (%)", "id": "viability", "editable": True, "type": "numeric"},
    {"name": "Final Titer (g/L)", "id": "final_titer", "editable": True, "type": "numeric"},
    {"name": "Culture Volume (L)", "id": "culture_volume", "editable": True, "type": "numeric"},
    {"name": "pH", "id": "ph", "editable": True, "type": "numeric"},
    {"name": "DO (%)", "id": "do_percent", "editable": True, "type": "numeric"},
    {"name": "Temperature (°C)", "id": "temperature", "editable": True, "type": "numeric"},
    {"name": "Feed Strategy", "id": "feed_strategy", "editable": True},
    {"name": "Note", "id": "note", "editable": True}
]

# Reactor type options
REACTOR_TYPE_OPTIONS = [
    {"label": "Bioreactor", "value": "bioreactor"},
    {"label": "Flask", "value": "flask"},
    {"label": "Wave Bag", "value": "wave"},
    {"label": "AMBR", "value": "ambr"},
    {"label": "DasGip", "value": "dasgip"},
    {"label": "Other", "value": "other"}
]


def create_create_samples_layout():
    """Create the USP sample creation layout"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-plus-circle text-success me-2"),
                    "Create USP Samples"
                ]),
                html.P("Add new upstream process samples with project and reactor grouping",
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
                    ], href="#!/usp/samples/sets", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Download Template"
                    ], id="usp-download-template-btn", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Creation Method Selection
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Creation Method", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.RadioItems(
                            id="usp-creation-method",
                            options=[
                                {
                                    "label": html.Span([
                                        html.I(className="fas fa-keyboard me-2"),
                                        "Manual Entry"
                                    ]),
                                    "value": "manual"
                                },
                                {
                                    "label": html.Span([
                                        html.I(className="fas fa-file-excel me-2"),
                                        "Import from Template"
                                    ]),
                                    "value": "template"
                                },
                                {
                                    "label": html.Span([
                                        html.I(className="fas fa-upload me-2"),
                                        "Bulk Upload"
                                    ]),
                                    "value": "upload"
                                }
                            ],
                            value="manual",
                            inline=True,
                            className="custom-radio"
                        )
                    ])
                ], className="shadow-sm mb-4")
            ])
        ]),

        # Dynamic content area based on method
        html.Div(id="usp-creation-method-content"),

        # Hidden components
        dcc.Store(id="usp-sample-creation-state", data={}),
        dcc.Download(id="usp-download-template-file"),
        html.Div(id="usp-hidden-div", style={"display": "none"})
    ], fluid=True)


def create_manual_entry_section():
    """Create the manual entry section for USP samples"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-keyboard text-primary me-2"),
                "Manual Sample Entry"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            # Project and Reactor Information
            dbc.Row([
                dbc.Col([
                    dbc.Label("Project ID", html_for="usp-project-id"),
                    dbc.Input(
                        id="usp-project-id",
                        placeholder="Enter project identifier",
                        style=INPUT_STYLE
                    )
                ], md=4),
                dbc.Col([
                    dbc.Label("Reactor Type", html_for="usp-reactor-type"),
                    dcc.Dropdown(
                        id="usp-reactor-type",
                        options=REACTOR_TYPE_OPTIONS,
                        placeholder="Select reactor type",
                        style=DROPDOWN_STYLE
                    )
                ], md=4),
                dbc.Col([
                    dbc.Label("Number of Samples", html_for="usp-num-samples"),
                    dbc.Input(
                        id="usp-num-samples",
                        type="number",
                        min=1,
                        max=50,
                        value=1,
                        style=INPUT_STYLE
                    )
                ], md=4)
            ], className="mb-4"),

            # Sample table
            html.Div(id="usp-sample-table-container"),

            # Action buttons
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-calculator me-1"),
                            "Calculate Metrics"
                        ], id="usp-calculate-btn", color="info", disabled=True),
                        dbc.Button([
                            html.I(className="fas fa-save me-1"),
                            "Save Samples"
                        ], id="usp-save-samples-btn", color="success", disabled=True),
                        dbc.Button([
                            html.I(className="fas fa-undo me-1"),
                            "Reset"
                        ], id="usp-reset-btn", color="secondary")
                    ])
                ])
            ], className="mt-3")
        ])
    ], className="shadow-sm")


def create_template_import_section():
    """Create the template import section for USP samples"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-file-excel text-success me-2"),
                "Import from Template"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                html.Span([
                    "Download the template, fill it with your USP sample data, and upload it back. ",
                    "The template includes fields for project ID, reactor type, and all culture parameters."
                ])
            ], color="info", className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Download Excel Template"
                    ], id="usp-download-excel-template-btn", color="success", className="mb-3")
                ])
            ]),

            dcc.Upload(
                id="usp-template-upload",
                children=dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-cloud-upload-alt fa-3x text-muted mb-3"),
                        html.H5("Drag and Drop or Click to Select Files"),
                        html.P("Supported formats: .xlsx, .xls", className="text-muted")
                    ], className="text-center py-5")
                ], style={"border": "2px dashed #dee2e6", "cursor": "pointer"}),
                multiple=False
            ),

            # Preview area
            html.Div(id="usp-template-preview", className="mt-4")
        ])
    ], className="shadow-sm")


def create_bulk_upload_section():
    """Create the bulk upload section for USP samples"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-upload text-warning me-2"),
                "Bulk Upload"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Upload multiple USP sample files. Files should contain project ID and reactor type information."
            ], color="warning", className="mb-3"),

            dcc.Upload(
                id="usp-bulk-upload",
                children=dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-cloud-upload-alt fa-3x text-muted mb-3"),
                        html.H5("Drag and Drop Multiple Files"),
                        html.P("Supported formats: .xlsx, .xls, .csv", className="text-muted"),
                        html.P("You can select multiple files at once", className="text-muted small")
                    ], className="text-center py-5")
                ], style={"border": "2px dashed #dee2e6", "cursor": "pointer"}),
                multiple=True
            ),

            # Upload status
            html.Div(id="usp-bulk-upload-status", className="mt-4")
        ])
    ], className="shadow-sm")