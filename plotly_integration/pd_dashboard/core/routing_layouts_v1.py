# plotly_integration/pd_dashboard/core/routing_layouts.py
# Clean routing system - Home + DSP AKTA only

from dash import html, Input, Output
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs
from ..core.sidebar_navigation import create_sidebar_navigation


def create_page_router(app):
    """
    Create page routing callbacks for hash-based routing

    Args:
        app: Dash app instance
    """

    @app.callback(
        Output("sidebar-nav", "children"),
        Input("parsed-pathname", "data"),
        prevent_initial_call='initial_duplicate'
    )
    def render_sidebar(pathname):
        """Render sidebar navigation - only render once"""
        return create_sidebar_navigation()

    @app.callback(
        Output("page-content", "children"),
        [Input("parsed-pathname", "data"),
         Input("url", "href")],
        prevent_initial_call=False
    )
    def route_pages(pathname, href):
        """
        Route to different pages based on URL pathname

        Args:
            pathname (str): URL pathname (extracted from hash)
            href (str): Full URL including query parameters

        Returns:
            Dash component for the requested page
        """
        # Extract query params from hash URL if present
        search = ""
        if href and '#!' in href and '?' in href:
            hash_part = href.split('#!')[1]
            if '?' in hash_part:
                search = '?' + hash_part.split('?')[1]

        # Parse query parameters
        query_params = parse_qs(search.lstrip('?')) if search else {}

        # Debug print to see what pathname we're getting
        print(f"Routing to pathname: '{pathname}'")
        if query_params:
            print(f"Query params: {query_params}")

        # Home/Dashboard - use iframe to avoid sidebar re-rendering issues
        if pathname == "/" or pathname == "/dashboard" or pathname == "/home" or pathname == "" or pathname is None:
            return create_full_screen_app("Dashboard", "/plotly_integration/dash-app/app/HomeDashboardApp/", "refresh-home")

        # Fullscreen app route mapping - organized by section
        # Format: pathname: (title, app_url, refresh_id, supports_query_params)
        fullscreen_route_map = {
            # Analytical routes
            "/analytical/report": ("SEC Analysis", "/plotly_integration/dash-app/app/ReportApp/", "refresh-analytical-sec", False),
            "/analytical/sec": ("SEC Analysis", "/plotly_integration/dash-app/app/SecReportApp/", "refresh-analytical-sec", True),
            "/analytical/sec/report": ("SEC Report", "/plotly_integration/dash-app/app/SecReportEmbeddedApp/", "refresh-sec-report", True),
            "/analytical/titer": ("Titer Analysis", "/plotly_integration/dash-app/app/TiterAnalysisApp/", "refresh-analytical-titer", True),
            "/analytical/ce-sds": ("CE SDS Analysis", "/plotly_integration/dash-app/app/CESDSReportViewerApp/", "refresh-analytical-cesds", True),
            "/analytical/cief": ("cIEF Analysis", "/plotly_integration/dash-app/app/cIEFReportViewerApp/", "refresh-analytical-cief", True),
            "/analytical/octet": ("Octet Analysis", "/plotly_integration/dash-app/app/OctetAnalysisApp/", "refresh-analytical-octet", False),

            # DSP routes
            "/dsp/akta": ("AKTA Analysis", "/plotly_integration/dash-app/app/AktaChromatogramApp/", "refresh-dsp-akta", False),
            "/dsp/create-dn": ("Create DN Assignment", "/plotly_integration/dash-app/app/DnAssignmentApp/", "refresh-dsp-dn", False),
            "/dsp/create-dn-pd": ("DN Assignment", "/plotly_integration/dash-app/app/DnAssignmentApp/", "refresh-dsp-dn-pd", False),
            "/dsp/ufdf": ("UFDF Process", "/plotly_integration/dash-app/app/UFDFApp/", "refresh-dsp-ufdf", False),
            "/dsp/vf": ("Viral Filtration", "/plotly_integration/dash-app/app/ViralFiltrationApp/", "refresh-dsp-vf", False),

            # USP routes
            "/usp/vicell": ("USP ViCell", "/plotly_integration/dash-app/app/USPViCellApp/", "refresh-usp-vicell", False),
            "/usp/nova": ("USP Nova", "/plotly_integration/dash-app/app/USPNovaFlexIIApp/", "refresh-usp-nova", False),
            "/usp/nova-data-table": ("USP Nova Data", "/plotly_integration/dash-app/app/USPNovaFlex2DataViewerApp/", "refresh-usp-nova-data", False),
            "/usp/brx": ("USP BioReactor", "/plotly_integration/dash-app/app/DasgipReportApp/", "refresh-usp-brx", False),
            "/usp/experiment-scheduler": ("USP Experiment Scheduler", "/plotly_integration/dash-app/app/USPExperimentSchedulerApp/", "refresh-usp-experiment-scheduler", False),
            "/usp/experiment-manager": ("USP Experiment Manager","/plotly_integration/dash-app/app/USPExperimentManagementApp/","refresh-usp-experiment-manager", False),
            "/usp/media-tracking": ("USP Media Tracking","/plotly_integration/dash-app/app/USPMediaTrackingApp/","refresh-usp-media-tracking", False),
            "/usp/titer-tracking": ("USP Titer Tracking", "/plotly_integration/dash-app/app/USPTiterTrackingApp/","refresh-usp-titer-tracking", False),

            # CLD routes
            "/cld/experiment-management": ("CLD Experiment Management", "/plotly_integration/dash-app/app/CLDProjectManagementApp/", "refresh-cld-experiment-management", False),
            "/cld/vicell": ("CLD ViCell", "/plotly_integration/dash-app/app/CLDViCellApp/", "refresh-cld-vicell", False),
            "/cld/nova": ("CLD Nova", "/plotly_integration/dash-app/app/CLDNovaFlexIIApp/", "refresh-cld-nova", False),

            # Formulation routes
            "/formulation/dashboard": ("Formulation Dashboard", "/plotly_integration/dash-app/app/FormulationDashboardApp/", "refresh-formulation-dashboard", False),
            "/formulation/create-experiment": ("Create New Experiment", "/plotly_integration/dash-app/app/ExperimentCreationApp/", "refresh-create-experiment", False),
            "/formulation/experiment-manager": ("Experiment Manager", "/plotly_integration/dash-app/app/FormulationExperimentManager/", "refresh-experiment-manager", False),
            "/formulation/design": ("Design Formulations", "/plotly_integration/dash-app/app/FormulationDesignApp/", "refresh-formulation-design", False),
            "/formulation/samples": ("Sample Management", "/plotly_integration/dash-app/app/SampleManagementApp/", "refresh-sample-management", False),
            "/formulation/data-entry": ("Analytical Data Entry", "/plotly_integration/dash-app/app/DataEntryApp/", "refresh-data-entry", False),
            "/formulation/stability": ("Formulation Stability Studies", "/plotly_integration/dash-app/app/FormulationStabilityApp/", "refresh-formulation-stability", False),
            "/formulation/visualization": ("Formulation Stability Visualization", "/plotly_integration/dash-app/app/FormulationVisualizationApp/", "refresh-formulation-visualization", False),

            # Formulation routes
            "/protein-engineering/octet-kinetics": ("Octet Kinetics", "/plotly_integration/dash-app/app/OctetKineticsDashboard/", "refresh-kinetics-dashboard", False),

            # Database Management routes
            "/database/import-empower": ("Import Empower Data", "/plotly_integration/dash-app/app/DatabaseManagerApp/", "refresh-db-empower", False),
            "/database/import-cesds": ("Import CE SDS Data", "/plotly_integration/dash-app/app/CeSdsImportManagerApp/", "refresh-db-cesds", False),
            "/database/import-cief": ("Import cIEF Data", "/plotly_integration/dash-app/app/cIEFImportManagerApp/", "refresh-db-cief", False),
            "/database/import-ufdf": ("Import UFDF Data", "/plotly_integration/dash-app/app/UFDFAnalysis/", "refresh-db-ufdf", False),
            "/database/import-vf": ("Import VF Data", "/plotly_integration/dash-app/app/ViralFiltrationExperimentImport/", "refresh-db-vf", False),
            "/database/import-nova-flex": ("Import Nova Flex Data", "/plotly_integration/dash-app/app/NovaFlex2DataUploadApp/", "refresh-db-nova-flex", False),
            "/database/import-vicell": ("Import ViCell Data", "/plotly_integration/dash-app/app/ViCellDataUploadApp/", "refresh-db-vicell", False),
        }

        # Custom layout route mapping (non-fullscreen)
        # Format: pathname: (import_path, layout_function_name)
        custom_layout_map = {
            "/cld/create-samples": ("plotly_integration.pd_dashboard.home.cld.create_samples.layouts.create_samples", "create_create_samples_layout"),
            "/cld/view-samples": ("plotly_integration.pd_dashboard.home.cld.view_samples.layouts.view_samples", "create_view_samples_layout"),
            "/cld/sample-sets": ("plotly_integration.pd_dashboard.home.cld.sample_sets.layouts.sample_sets", "create_sample_sets_main_layout"),
            "/cld/sample-sets/details": ("plotly_integration.pd_dashboard.home.cld.sample_sets.layouts.sample_set_details", "create_sample_set_detail_layout"),
            "/usp/create-samples": ("plotly_integration.pd_dashboard.home.usp.create_samples.layouts.create_samples", "create_create_samples_layout"),
            "/usp/sample-sets": ("plotly_integration.pd_dashboard.home.usp.sample_sets.layouts.sample_sets", "create_sample_sets_main_layout"),
        }

        # Check if pathname matches a fullscreen app route
        if pathname in fullscreen_route_map:
            title, base_url, refresh_id, supports_query = fullscreen_route_map[pathname]

            # Add query params if supported
            if supports_query and query_params.get('report_id'):
                report_id = query_params.get('report_id', ['0'])[0]
                app_url = f"{base_url}?report_id={report_id}"
                # Update title if it's a report with ID
                if "report" in pathname.lower():
                    title = f"{title} {report_id}"
            else:
                app_url = base_url

            return create_full_screen_app(title, app_url, refresh_id)

        # Check if pathname matches a custom layout route
        elif pathname in custom_layout_map:
            import_path, func_name = custom_layout_map[pathname]
            try:
                # Dynamically import the module and get the function
                from importlib import import_module
                module = import_module(import_path)
                layout_func = getattr(module, func_name)

                # Call with query_params if the route needs it
                if pathname.endswith("/details"):
                    return layout_func(query_params)
                else:
                    return layout_func()
            except ImportError as e:
                print(f"Error importing layout from {import_path}: {e}")
                route_name = pathname.split('/')[-1].replace('-', ' ').title()
                return html.Div([
                    html.H2(f"{route_name}"),
                    html.P("Error loading page"),
                    html.P(str(e), className="text-danger")
                ])
            except AttributeError as e:
                print(f"Error finding function {func_name} in {import_path}: {e}")
                return html.Div([
                    html.H2("Error"),
                    html.P(f"Layout function not found: {func_name}"),
                    html.P(str(e), className="text-danger")
                ])

        # Default case - redirect to home
        else:
            print(f"Warning: Unknown route: {pathname}, redirecting to home")
            from ..core.layout_manager import create_dashboard_layout
            return create_dashboard_layout()


def create_full_screen_app(title, app_url, refresh_id):
    """Helper function to create consistent full-screen app layouts"""
    return html.Div([
        html.Div([
            html.Div([
                html.H5(title, style={"margin": "0", "color": "#333"}),
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-home me-1"),
                        "Home"
                    ], href="#!/", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-external-link-alt me-1"),
                        "Open in New Tab"
                    ], href=app_url, target="_blank", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id=refresh_id, color="outline-info", size="sm")
                ])
            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "8px 16px",
                "backgroundColor": "#f8f9fa",
                "borderBottom": "1px solid #dee2e6"
            })
        ], style={"height": "50px", "flexShrink": "0"}),

        html.Iframe(
            src=app_url,
            style={
                "width": "100%",
                "height": "calc(100vh - 50px)",
                "border": "none",
                "display": "block",
                "overflow": "hidden"
            }
        )
    ], style={
        "position": "fixed",
        "top": "0",
        "left": "220px",
        "right": "20px",
        "bottom": "0",
        "height": "100vh",
        "width": "calc(100vw - 240px)",
        "overflow": "hidden",
        "display": "flex",
        "flexDirection": "column",
        "zIndex": "999"
    })