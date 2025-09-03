import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash

# Create the main USP samples app
app = DjangoDash('USPSamplesApp', external_stylesheets=[dbc.themes.BOOTSTRAP])

def create_usp_samples_main_layout():
    """Create the main USP samples homepage layout"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-flask text-primary me-3"),
                    "USP Sample Management"
                ], className="display-4"),
                html.P("Manage upstream process samples and sample sets", 
                       className="lead text-muted")
            ])
        ], className="mb-5"),

        # Navigation Cards
        dbc.Row([
            # Create Samples
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-plus-circle fa-3x text-success mb-3"),
                            html.H4("Create Samples", className="card-title"),
                            html.P("Add new USP samples manually or via bulk upload",
                                   className="card-text text-muted"),
                            dbc.Button([
                                html.I(className="fas fa-plus me-2"),
                                "Create New Samples"
                            ], href="#!/usp/samples/create", color="success", className="w-100")
                        ], className="text-center")
                    ])
                ], className="shadow-sm h-100 border-0")
            ], md=4),

            # View Samples
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-eye fa-3x text-info mb-3"),
                            html.H4("View Samples", className="card-title"),
                            html.P("Browse, search, and manage existing USP samples",
                                   className="card-text text-muted"),
                            dbc.Button([
                                html.I(className="fas fa-eye me-2"),
                                "View All Samples"
                            ], href="#!/usp/samples/view", color="info", className="w-100")
                        ], className="text-center")
                    ])
                ], className="shadow-sm h-100 border-0")
            ], md=4),

            # Sample Sets
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-layer-group fa-3x text-warning mb-3"),
                            html.H4("Sample Sets", className="card-title"),
                            html.P("Organize samples by project and reactor type",
                                   className="card-text text-muted"),
                            dbc.Button([
                                html.I(className="fas fa-layer-group me-2"),
                                "Manage Sample Sets"
                            ], href="#!/usp/sample-sets", color="warning", className="w-100")
                        ], className="text-center")
                    ])
                ], className="shadow-sm h-100 border-0")
            ], md=4)
        ], className="mb-4"),

        # Quick Stats Row (placeholder for future metrics)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Quick Stats", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.H3("0", className="text-primary mb-0", id="usp-total-samples"),
                                    html.Small("Total USP Samples", className="text-muted")
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.H3("0", className="text-success mb-0", id="usp-active-sets"),
                                    html.Small("Active Sample Sets", className="text-muted")
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.H3("0", className="text-info mb-0", id="usp-pending-analysis"),
                                    html.Small("Pending Analysis", className="text-muted")
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.H3("0", className="text-warning mb-0", id="usp-recent-samples"),
                                    html.Small("Recent Samples", className="text-muted")
                                ], className="text-center")
                            ], md=3)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Recent Activity (placeholder)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Recent Activity", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("Recent sample creation and analysis activities will appear here...", 
                               className="text-muted text-center py-4")
                    ])
                ], className="shadow-sm")
            ])
        ])

    ], fluid=True, style={"padding": "20px"})

# Set the layout
app.layout = create_usp_samples_main_layout()

# Import and register callbacks
try:
    from .create_samples.callbacks.create_samples import register_callbacks as register_create_callbacks
    register_create_callbacks(app)
    print("✅ USP Create Samples callbacks registered")
except ImportError as e:
    print(f"⚠️ Could not import create samples callbacks: {e}")

try:
    from .view_samples.callbacks.view_samples import register_callbacks as register_view_callbacks
    register_view_callbacks(app)
    print("✅ USP View Samples callbacks registered")
except ImportError as e:
    print(f"⚠️ Could not import view samples callbacks: {e}")

try:
    from .sample_sets.callbacks.sample_sets import register_callbacks as register_sets_callbacks
    register_sets_callbacks(app)
    print("✅ USP Sample Sets callbacks registered")
except ImportError as e:
    print(f"⚠️ Could not import sample sets callbacks: {e}")

print("🚀 USP Samples App initialized successfully")