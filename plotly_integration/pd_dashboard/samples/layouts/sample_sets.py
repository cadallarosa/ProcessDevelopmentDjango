# cld_dashboard/samples/layouts/sample_sets.py - COMPLETE WITH SEC SELECTION MODAL

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

# Make sure this import path is correct for your project structure
try:
    from ...shared.styles.common_styles import CARD_STYLE, COLORS
except ImportError:
    # Fallback if import fails
    CARD_STYLE = {}
    COLORS = {}
    print("Warning: Could not import common_styles")


def create_sample_sets_layout():
    """Create the sample sets management page"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-layer-group text-primary me-2"),
                    "Sample Sets Analysis Management"
                ]),
                html.P("Manage analysis requests and track progress for grouped samples",
                       className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-sample-sets-btn", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-file-export me-1"),
                        "Export"
                    ], id="export-sample-sets-btn", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Metrics Row
        dbc.Row([
            dbc.Col([
                create_metric_card("Total Sets", "0", "fa-layer-group", "primary", "total-sets-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("Pending Analysis", "0", "fa-clock", "warning", "pending-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("In Progress", "0", "fa-spinner", "info", "in-progress-metric")
            ], md=3),
            dbc.Col([
                create_metric_card("Completed", "0", "fa-check-circle", "success", "completed-metric")
            ], md=3)
        ], className="mb-4"),

        # Filter Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Search", className="fw-bold small"),
                                dbc.Input(
                                    id="search-sample-sets",
                                    placeholder="Search by project, SIP, or stage...",
                                    type="text"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Project Filter", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="project-filter",
                                    options=[{"label": "All Projects", "value": "all"}],
                                    value="all",
                                    clearable=False
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Status Filter", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="status-filter",
                                    options=[
                                        {"label": "All Status", "value": "all"},
                                        {"label": "Has Pending", "value": "pending"},
                                        {"label": "All Complete", "value": "complete"},
                                        {"label": "No Analysis", "value": "none"}
                                    ],
                                    value="all",
                                    clearable=False
                                )
                            ], md=4)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Sample Sets Grid
        dbc.Row([
            dbc.Col([
                html.Div(id="sample-sets-grid", children=[
                    dbc.Spinner(
                        html.Div(style={"height": "200px"}),
                        color="primary"
                    )
                ])
            ])
        ]),

        # Analysis Request Modal
        create_analysis_request_modal(),

        # ✅ NEW: SEC Sample Selection Modal
        create_sec_sample_selection_modal(),

        # Sample Set Details Modal
        create_sample_set_details_modal(),

        # Toast notifications
        html.Div(id="sample-sets-notifications"),

        # Hidden stores
        dcc.Store(id="selected-sample-set", data={}),
        dcc.Store(id="available-projects", data=[]),

        # ✅ NEW: Stores for SEC report creation
        dcc.Store(id="sec-report-created", data={}),
        dcc.Store(id="sec-selected-sample-set", data={}),

        # Dummy output for callbacks that don't need real output
        html.Div(id="dummy-output", style={"display": "none"})

    ], fluid=True, style={"padding": "20px"})


def create_metric_card(title, metric_id, icon, color, card_id):
    """Create a metric display card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H3("0", id=card_id, className=f"text-{color} mb-0"),
                    html.P(title, className="text-muted mb-0 small")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color} opacity-75")
                ], className="align-self-center")
            ], className="d-flex")
        ])
    ], className="shadow-sm h-100")


def create_sample_set_card(sample_set, analysis_status):
    """Create a card for a single sample set - with SEC MODAL CREATION"""
    # Determine overall status
    has_pending = any(status == 'requested' for status in analysis_status.values())
    has_in_progress = any(status == 'in_progress' for status in analysis_status.values())
    all_complete = all(status == 'completed' for status in analysis_status.values()
                       if status != 'not_requested')

    if has_pending:
        overall_status = {"color": "warning", "icon": "fa-clock", "text": "Pending"}
    elif has_in_progress:
        overall_status = {"color": "info", "icon": "fa-spinner", "text": "In Progress"}
    elif all_complete and any(status == 'completed' for status in analysis_status.values()):
        overall_status = {"color": "success", "icon": "fa-check-circle", "text": "Completed"}
    else:
        overall_status = {"color": "secondary", "icon": "fa-circle", "text": "No Analysis"}

    # Get sample IDs for this set
    sample_ids = [member.sample.sample_id for member in sample_set.members.all()]

    # ✅ Check for existing SEC reports for this sample set
    try:
        from plotly_integration.models import LimsSampleAnalysis, LimsSecResult

        sample_analyses = LimsSampleAnalysis.objects.filter(sample_id__in=sample_ids)
        sec_results = LimsSecResult.objects.filter(
            sample_id__in=sample_analyses,
            report__isnull=False
        ).select_related('report')

        # Get unique reports
        existing_sec_reports = []
        seen_report_ids = set()
        for result in sec_results:
            if result.report and result.report.report_id not in seen_report_ids:
                existing_sec_reports.append(result.report)
                seen_report_ids.add(result.report.report_id)

        # Sort by creation date (newest first)
        existing_sec_reports = sorted(existing_sec_reports, key=lambda r: r.date_created, reverse=True)

    except Exception as e:
        print(f"Error getting existing SEC reports: {e}")
        existing_sec_reports = []

    # ✅ UPDATED: Smart SEC button configuration with MODAL
    if existing_sec_reports:
        # Has existing reports - show latest + create new (modal) option
        latest_report = existing_sec_reports[0]  # Already sorted by date

        sec_buttons = dbc.ButtonGroup([
            # View latest report button - ✅ EMBEDDED VERSION
            html.A(
                dbc.Button([
                    html.I(className="fas fa-chart-line me-1"),
                    "Latest"
                ],
                    color="success",
                    size="sm",
                    title=f"View: {latest_report.report_name}"
                ),
                href=f"#!/analysis/sec/report?report_id={latest_report.report_id}",
                style={"textDecoration": "none"}
            ),

            # ✅ NEW: Create new report button (opens modal)
            dbc.Button([
                html.I(className="fas fa-plus me-1"),
                "New"
            ],
                id={"type": "open-sec-modal-btn", "index": sample_set.id},
                color="outline-success",
                size="sm",
                title=f"Create new SEC report - select samples"
            )
        ], size="sm")

    else:
        # ✅ NEW: No existing reports - create new (opens modal)
        sec_buttons = dbc.Button([
            html.I(className="fas fa-microscope me-1"),
            "Create SEC"
        ],
            id={"type": "open-sec-modal-btn", "index": sample_set.id},
            color="primary",
            size="sm",
            title=f"Create SEC report - select samples"
        )

    # ✅ AKTA button configuration for EMBEDDED viewing
    clean_fb_numbers = []
    for sid in sample_ids:
        if str(sid).startswith('FB'):
            clean_fb_numbers.append(str(sid)[2:])  # Remove FB prefix
        else:
            clean_fb_numbers.append(str(sid))

    akta_href = f"#!/analysis/akta/report?fb={','.join(clean_fb_numbers)}"
    akta_button_color = "warning" if analysis_status.get('AKTA') == 'completed' else "outline-warning"

    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Left section: Basic info
                dbc.Col([
                    html.Div([
                        html.H5(sample_set.set_name, className="mb-1"),
                        html.P([
                            html.I(className="fas fa-vial text-primary me-2"),
                            f"{sample_set.sample_count} samples",
                            html.Span(" | ", className="text-muted"),
                            html.I(className="fas fa-calendar text-info me-2"),
                            f"Created: {sample_set.created_at.strftime('%Y-%m-%d')}" if sample_set.created_at else "Unknown"
                        ], className="mb-2 text-muted small"),

                        # Show existing reports count and project info
                        html.P([
                            html.I(className="fas fa-project-diagram text-success me-2"),
                            f"Project: {sample_set.project_id}",
                            html.Span(" | ", className="text-muted") if sample_set.sip_number else "",
                            f"SIP: {sample_set.sip_number}" if sample_set.sip_number else "",
                            html.Span(" | ", className="text-muted") if existing_sec_reports else "",
                            f"📄 {len(existing_sec_reports)} SEC report(s)" if existing_sec_reports else ""
                        ], className="mb-0 text-muted small")
                    ])
                ], md=3),

                # Middle section: Analysis badges
                dbc.Col([
                    html.Div([
                        html.P("Analysis Status:", className="fw-bold small mb-2"),
                        html.Div([
                            create_analysis_badge(analysis_type, status)
                            for analysis_type, status in analysis_status.items()
                        ], className="d-flex flex-wrap gap-1")
                    ])
                ], md=5),

                # Right section: ✅ UPDATED Actions with SEC modal buttons
                dbc.Col([
                    html.Div([
                        # Overall status badge
                        dbc.Badge([
                            html.I(className=f"fas {overall_status['icon']} me-1"),
                            overall_status['text']
                        ], color=overall_status['color'], className="mb-2"),

                        # ✅ UPDATED: Button group with SEC modal options
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-microscope me-1"),
                                "Request"
                            ],
                                id={"type": "request-analysis-btn", "index": sample_set.id},
                                color="primary",
                                size="sm"),

                            # ✅ NEW: SEC buttons (latest + modal OR just modal)
                            sec_buttons,

                            # AKTA button (embedded viewing)
                            html.A(
                                dbc.Button([
                                    html.I(className="fas fa-chart-area me-1"),
                                    "AKTA"
                                ],
                                    color=akta_button_color,
                                    size="sm"
                                ),
                                href=akta_href,
                                style={"textDecoration": "none"},
                                title="View AKTA Results (Embedded)"
                            ),

                            dbc.Button([
                                html.I(className="fas fa-info-circle me-1"),
                                "Details"
                            ],
                                id={"type": "view-details-btn", "index": sample_set.id},
                                color="outline-info",
                                size="sm")
                        ], size="sm")
                    ], className="text-end")
                ], md=4)
            ])
        ])
    ], className="shadow-sm mb-3")


def create_analysis_badge(analysis_type, status):
    """Create a small badge showing analysis status"""
    status_config = {
        'not_requested': {'color': 'light', 'icon': 'fa-circle'},
        'requested': {'color': 'warning', 'icon': 'fa-clock'},
        'in_progress': {'color': 'info', 'icon': 'fa-spinner fa-spin'},
        'completed': {'color': 'success', 'icon': 'fa-check'}
    }

    config = status_config.get(status, status_config['not_requested'])

    return dbc.Badge([
        html.I(className=f"fas {config['icon']} me-1", style={"fontSize": "0.7rem"}),
        analysis_type
    ], color=config['color'], className="me-1", style={"fontSize": "0.75rem"})


def create_analysis_request_modal():
    """Create modal for requesting analyses"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Request Analysis", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div(id="modal-sample-set-info", className="mb-3"),
            html.Hr(),
            html.H6("Select Analyses to Request:"),
            dbc.Checklist(
                id="analysis-type-checklist",
                options=[
                    {"label": "SEC - Size Exclusion Chromatography", "value": "SEC"},
                    {"label": "AKTA - Chromatography Purification", "value": "AKTA"},
                    {"label": "Titer - Protein Concentration", "value": "Titer"},
                    {"label": "CE-SDS - Capillary Electrophoresis", "value": "CE-SDS"},
                    {"label": "cIEF - Isoelectric Focusing", "value": "cIEF"},
                    {"label": "Mass Check - Mass Spectrometry", "value": "Mass Check"},
                    {"label": "Glycan - Glycan Analysis", "value": "Glycan"},
                    {"label": "HCP - Host Cell Protein", "value": "HCP"},
                    {"label": "ProA - Protein A", "value": "ProA"}
                ],
                value=[],
                className="mb-3"
            ),
            html.Div([
                html.Label("Priority", className="fw-bold"),
                dbc.RadioItems(
                    id="analysis-priority",
                    options=[
                        {"label": "Normal", "value": 1},
                        {"label": "High", "value": 2},
                        {"label": "Urgent", "value": 3}
                    ],
                    value=1,
                    inline=True
                )
            ], className="mb-3"),
            html.Div([
                html.Label("Notes", className="fw-bold"),
                dbc.Textarea(
                    id="analysis-notes",
                    placeholder="Add any special instructions...",
                    rows=3
                )
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-analysis-request", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-paper-plane me-2"),
                "Submit Request"
            ], id="submit-analysis-request", color="primary")
        ])
    ], id="analysis-request-modal", size="lg")


# ✅ NEW: SEC Sample Selection Modal
def create_sec_sample_selection_modal():
    """Create modal for SEC sample selection and report creation"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5([
                html.I(className="fas fa-microscope text-primary me-2"),
                "Create SEC Report"
            ], className="text-primary")
        ]),
        dbc.ModalBody([
            # Sample set info
            html.Div(id="sec-modal-sample-set-info", className="mb-3"),
            html.Hr(),

            # Report configuration
            dbc.Row([
                dbc.Col([
                    dbc.Label("Report Name (optional)", className="fw-bold"),
                    dbc.Input(
                        id="sec-report-name",
                        placeholder="Auto-generated if left blank...",
                        type="text"
                    )
                ], md=8),
                dbc.Col([
                    dbc.Label("Department", className="fw-bold"),
                    dbc.Select(
                        id="sec-department",
                        options=[
                            {"label": "Process Development", "value": 1},
                            {"label": "Protein Engineering", "value": 2}
                        ],
                        value=1
                    )
                ], md=4)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Comments", className="fw-bold"),
                    dbc.Textarea(
                        id="sec-report-comments",
                        placeholder="Add any comments about this report...",
                        rows=2
                    )
                ])
            ], className="mb-3"),

            html.Hr(),

            # Sample selection
            html.H6("Select Samples for SEC Report:"),
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Only samples with SEC data available can be selected. Disabled samples have no SEC results."
            ], color="info", className="mb-3"),

            dbc.Checklist(
                id="sec-sample-checklist",
                options=[],  # Populated by callback
                value=[],  # Populated by callback
                className="mb-3",
                style={"maxHeight": "300px", "overflowY": "auto"}
            ),

            # Status area
            html.Div(id="sec-selection-status", className="mb-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-sec-creation", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-chart-line me-2"),
                "Create SEC Report"
            ], id="create-sec-report-with-samples", color="primary", disabled=False)
        ])
    ], id="sec-sample-selection-modal", size="lg", scrollable=True)


def create_sample_set_details_modal():
    """Create modal for viewing sample set details"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Sample Set Details", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div(id="modal-sample-set-details")
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-details-modal", color="secondary")
        ])
    ], id="sample-set-details-modal", size="xl")


def create_sample_sets_table_layout():
    """Create table view layout for sample sets"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-table text-primary me-2"),
                    "Sample Sets - Table View"
                ]),
                html.P("Tabular view of all sample sets", className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-th-large me-1"),
                        "Card View"
                    ], href="#!/sample-sets", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-table-btn", color="outline-secondary", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Sample Sets Table
        dbc.Row([
            dbc.Col([
                html.Div(id="sample-sets-table", children=[
                    dbc.Spinner(
                        html.Div(style={"height": "400px"}),
                        color="primary"
                    )
                ])
            ])
        ])

    ], fluid=True, style={"padding": "20px"})


def create_sample_set_detail_layout(query_params):
    """Create detailed view layout for a specific sample set"""
    sample_set_id = query_params.get('id', [None])[0] if query_params else None

    if not sample_set_id:
        return dbc.Container([
            dbc.Alert("No sample set ID provided", color="warning")
        ])

    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-info-circle text-primary me-2"),
                    f"Sample Set Details"
                ]),
                html.P(f"Detailed view for sample set ID: {sample_set_id}", className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-1"),
                        "Back to Sets"
                    ], href="#!/sample-sets", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-edit me-1"),
                        "Edit"
                    ], color="outline-primary", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Sample Set Details Content
        dbc.Row([
            dbc.Col([
                html.Div(id="sample-set-detail-content", children=[
                    dbc.Spinner(
                        html.Div(style={"height": "400px"}),
                        color="primary"
                    )
                ])
            ])
        ])

    ], fluid=True, style={"padding": "20px"})


print("✅ sample_sets layout components with SEC modal loaded successfully")