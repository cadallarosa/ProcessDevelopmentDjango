# cld_dashboard/samples/layouts/create_samples.py - Updated with vessel types and placeholders
import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from ...shared.styles.common_styles import (
    TABLE_STYLE_CELL, TABLE_STYLE_HEADER, CARD_STYLE,
    INPUT_STYLE, DROPDOWN_STYLE, BUTTON_STYLE_PRIMARY
)

# Field definitions for UP samples
UP_SAMPLE_CREATE_FIELDS = [
    {"name": "Sample #", "id": "sample_number", "editable": False, "type": "numeric"},
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa E Titer", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
    {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
    {"name": "HF Vol (mL)", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
    {"name": "Eluate Vol (mL)", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
    {"name": "ProA Recovery (%)", "id": "fast_pro_a_recovery", "editable": False, "type": "numeric"},
    {"name": "A280 Recovery (%)", "id": "purification_recovery_a280", "editable": False, "type": "numeric"},
    {"name": "Note", "id": "note", "editable": True}
]


def create_create_samples_layout():
    """Create the enhanced sample creation layout"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-plus-circle text-success me-2"),
                    "Create Fed Batch Samples"
                ]),
                html.P("Add new upstream process samples with automatic recovery calculations",
                       className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-eye me-1"),
                        "View Samples"
                    ], href="#!/samples/view", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Download Template"
                    ], id="download-template-btn", color="outline-info", size="sm")
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
                            id="creation-method",
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
        html.Div(id="creation-method-content"),

        # Hidden components
        dcc.Store(id="sample-creation-state", data={}),
        dcc.Download(id="download-template-file")

    ], fluid=True, style={"padding": "20px", "backgroundColor": "#fafbfc"})


def create_manual_entry_section():
    """Create manual entry section for samples"""
    return html.Div([
        # Project and Metadata Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-project-diagram me-2"),
                            "Project Information"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Row 1: Project and Vessel
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Project *", html_for="up-project-dropdown",
                                          className="fw-bold"),
                                dcc.Dropdown(
                                    id="up-project-dropdown",
                                    placeholder="Select or type project name...",
                                    style=DROPDOWN_STYLE
                                ),
                                html.Div(id="project-info-display", className="mt-2")
                            ], md=6),
                            dbc.Col([
                                dbc.Label("Vessel Type *", html_for="up-vessel-type",
                                          className="fw-bold"),
                                dcc.Dropdown(
                                    id="up-vessel-type",
                                    options=[
                                        {"label": "🧪 Ambr 250", "value": "Ambr250"},
                                        {"label": "🧪 DasGip", "value": "DasGip"},
                                        {"label": "🧪 2L", "value": "2L"},
                                        {"label": "🧪 5L", "value": "5L"},
                                        {"label": "🧪 24 Deep Well", "value": "24 Deep Well"},
                                        {"label": "🧪 Shake Flask", "value": "Shake Flask"},
                                        {"label": "🧪 Other", "value": "Other"}
                                    ],
                                    placeholder="Select vessel type...",
                                    style=DROPDOWN_STYLE
                                )
                            ], md=6)
                        ], className="mb-3"),

                        # Row 2: Development Stage and Analyst
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Development Stage", html_for="cld-dev-stage"),
                                dcc.Dropdown(
                                    id="cld-dev-stage",
                                    options=[
                                        {"label": "MP", "value": "MP"},
                                        {"label": "pMP", "value": "pMP"},
                                        {"label": "BP", "value": "BP"},
                                        {"label": "BP SCC", "value": "BP SCC"},
                                        {"label": "MP SCC", "value": "MP SCC"}
                                    ],
                                    placeholder="Select stage...",
                                    style=DROPDOWN_STYLE
                                )
                            ], md=6),
                            dbc.Col([
                                dbc.Label("Analyst", html_for="cld-analyst"),
                                dbc.Input(
                                    id="cld-analyst",
                                    placeholder="Enter analyst name...",
                                    style=INPUT_STYLE
                                ),
                                html.Div(id="analyst-suggestions", className="mt-1")
                            ], md=6)
                        ], className="mb-3"),

                        # Row 3: SIP and Unifi Numbers - Updated placeholders
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("SIP Number", html_for="sip-number"),
                                dbc.Input(
                                    id="sip-number",
                                    placeholder="001",  # Updated placeholder
                                    style=INPUT_STYLE
                                )
                            ], md=6),
                            dbc.Col([
                                dbc.Label("Unifi Number", html_for="unifi-number"),
                                dbc.Input(
                                    id="unifi-number",
                                    placeholder="12345",  # Updated placeholder
                                    style=INPUT_STYLE
                                )
                            ], md=6)
                        ])
                    ])
                ], className="shadow-sm mb-4")
            ])
        ]),

        # Status displays
        dbc.Row([
            dbc.Col([
                html.Div(id="save-up-status"),
                html.Div(id="recovery-calculation-status"),
                html.Div(id="sample-validation-results")
            ])
        ], className="mb-3"),

        # Sample Entry Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5([
                                html.I(className="fas fa-table me-2"),
                                "Sample Data Entry"
                            ], className="mb-0"),
                            html.Div([
                                dbc.ButtonGroup([
                                    dbc.Button([
                                        html.I(className="fas fa-plus me-1"),
                                        "Add Row"
                                    ], id="add-up-row", color="success", size="sm"),
                                    dbc.Button([
                                        html.I(className="fas fa-calculator me-1"),
                                        "Calculate Recoveries"
                                    ], id="calculate-recoveries-btn", color="info", size="sm"),
                                    dbc.Button([
                                        html.I(className="fas fa-trash me-1"),
                                        "Clear All"
                                    ], id="clear-up-table", color="outline-danger", size="sm")
                                ])
                            ], className="float-end")
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        # Quick tips
                        dbc.Alert([
                            html.I(className="fas fa-lightbulb me-2"),
                            "Tip: Recovery percentages are calculated automatically as you enter titer and volume data!"
                        ], color="info", dismissable=True, className="mb-3"),

                        # The data table
                        dash_table.DataTable(
                            id="up-sample-table",
                            columns=[
                                {
                                    "name": col["name"],
                                    "id": col["id"],
                                    "editable": col["editable"],
                                    "type": col.get("type", "text")
                                } for col in UP_SAMPLE_CREATE_FIELDS
                            ],
                            data=[],
                            editable=True,
                            row_deletable=True,

                            # Styling
                            style_cell={
                                **TABLE_STYLE_CELL,
                                'minWidth': '80px',
                                'width': '120px',
                                'maxWidth': '150px',
                            },
                            style_header=TABLE_STYLE_HEADER,
                            style_cell_conditional=[
                                {'if': {'column_id': 'sample_number'}, 'width': '90px'},
                                {'if': {'column_id': 'cell_line'}, 'width': '100px'},
                                {'if': {'column_id': 'harvest_date'}, 'width': '110px'},
                                {'if': {'column_id': 'note'}, 'width': '150px'},
                                # Calculated fields styling
                                {'if': {'column_id': 'fast_pro_a_recovery'},
                                 'backgroundColor': '#e3f2fd', 'fontStyle': 'italic'},
                                {'if': {'column_id': 'purification_recovery_a280'},
                                 'backgroundColor': '#e3f2fd', 'fontStyle': 'italic'},
                            ],
                            style_data_conditional=[
                                # Recovery value highlighting
                                {
                                    'if': {
                                        'column_id': 'fast_pro_a_recovery',
                                        'filter_query': '{fast_pro_a_recovery} > 80'
                                    },
                                    'backgroundColor': '#d4edda',
                                    'color': '#155724'
                                },
                                {
                                    'if': {
                                        'column_id': 'fast_pro_a_recovery',
                                        'filter_query': '{fast_pro_a_recovery} < 50'
                                    },
                                    'backgroundColor': '#f8d7da',
                                    'color': '#721c24'
                                }
                            ],
                            style_table={'overflowX': 'auto'}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ])
        ]),

        # Save Button Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            dbc.Button([
                                html.I(className="fas fa-save me-2"),
                                "Save All Samples"
                            ],
                                id="save-up-table",
                                color="success",
                                size="lg",
                                disabled=False,
                                className="me-2"),

                            dbc.Button([
                                html.I(className="fas fa-eye me-2"),
                                "Preview & Validate"
                            ],
                                id="preview-samples-btn",
                                color="info",
                                size="lg",
                                outline=True),

                            html.Span(
                                "* Required fields: Project, Vessel Type",
                                className="text-muted float-end mt-2"
                            )
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ])
        ])
    ])


def create_template_import_section():
    """Create template import section"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-file-excel me-2"),
                            "Import from Template"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("Download our Excel template, fill it with your sample data, and upload it back."),

                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Step 1: Download Template"),
                                        html.P("Get our pre-formatted Excel template", className="text-muted"),
                                        dbc.Button([
                                            html.I(className="fas fa-download me-2"),
                                            "Download Excel Template"
                                        ], id="download-excel-template-btn", color="primary")
                                    ])
                                ], className="text-center")
                            ], md=4),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Step 2: Fill Template"),
                                        html.P("Add your sample data to the template", className="text-muted"),
                                        html.I(className="fas fa-edit fa-3x text-info")
                                    ])
                                ], className="text-center")
                            ], md=4),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Step 3: Upload Template"),
                                        html.P("Upload the completed template", className="text-muted"),
                                        dcc.Upload(
                                            id="upload-template-file",
                                            children=dbc.Button([
                                                html.I(className="fas fa-upload me-2"),
                                                "Upload File"
                                            ], color="success"),
                                            multiple=False,
                                            accept=".xlsx,.xls"
                                        )
                                    ])
                                ], className="text-center")
                            ], md=4)
                        ], className="mb-4"),

                        html.Div(id="template-upload-status")
                    ])
                ], className="shadow-sm")
            ])
        ])
    ])


def create_bulk_upload_section():
    """Create bulk upload section"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-upload me-2"),
                            "Bulk Upload"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Upload(
                            id="bulk-upload-area",
                            children=html.Div([
                                html.I(className="fas fa-cloud-upload-alt fa-3x mb-3"),
                                html.H5("Drag and Drop or Click to Upload"),
                                html.P("Supported formats: Excel (.xlsx, .xls), CSV (.csv)",
                                       className="text-muted")
                            ], className="text-center py-5"),
                            style={
                                'width': '100%',
                                'borderWidth': '2px',
                                'borderStyle': 'dashed',
                                'borderRadius': '10px',
                                'borderColor': '#dee2e6',
                                'backgroundColor': '#fafbfc'
                            },
                            multiple=False
                        ),

                        html.Div(id="bulk-upload-preview", className="mt-4"),
                        html.Div(id="bulk-upload-status")
                    ])
                ], className="shadow-sm")
            ])
        ])
    ])


# Helper function for creating preview modal
def create_sample_preview_modal():
    """Create modal for previewing samples before save"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4("Sample Preview & Validation", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div(id="sample-preview-content")
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-preview-modal", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-save me-2"),
                "Confirm & Save"
            ], id="confirm-save-btn", color="success")
        ])
    ], id="sample-preview-modal", size="xl", scrollable=True)