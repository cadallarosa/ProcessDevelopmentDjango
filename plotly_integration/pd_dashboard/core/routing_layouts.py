# plotly_integration/pd_dashboard/core/routing_layouts.py
# Clean routing system - Home + DSP AKTA only

from dash import html, Input, Output, State, callback
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
        prevent_initial_call=False
    )
    def render_sidebar(pathname):
        """Render sidebar navigation"""
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

        # Home/Dashboard
        if pathname == "/" or pathname == "/dashboard" or pathname == "" or pathname is None:
            from ..core.layout_manager import create_dashboard_layout
            return create_dashboard_layout()

        # DSP AKTA Route - Full screen, non-scrollable
        elif pathname == "/dsp/akta":
            # Display full AKTA app taking up entire viewport
            akta_url = "/plotly_integration/dash-app/app/AktaChromatogramApp/"

            # Return a special full-screen layout that bypasses normal content container
            return html.Div([
                # Minimal header with controls - fixed height
                html.Div([
                    html.Div([
                        html.H5("AKTA Analysis", style={"margin": "0", "color": "#333"}),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-home me-1"),
                                "Home"
                            ], href="#!/", color="outline-secondary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-external-link-alt me-1"),
                                "Open in New Tab"
                            ], href=akta_url, target="_blank", color="outline-primary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-1"),
                                "Refresh"
                            ], id="refresh-dsp-akta", color="outline-info", size="sm")
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

                # Full-height iframe - no scrolling
                html.Iframe(
                    src=akta_url,
                    style={
                        "width": "100%",
                        "height": "calc(100vh - 50px)",  # Full viewport height minus header
                        "border": "none",
                        "display": "block",
                        "overflow": "hidden"  # Prevent iframe scrolling
                    }
                )
            ], style={
                "position": "fixed",  # Fixed positioning to bypass normal layout
                "top": "0",
                "left": "220px",  # Account for sidebar width + left margin
                "right": "20px",  # Right margin
                "bottom": "0",
                "height": "100vh",
                "width": "calc(100vw - 240px)",  # Full width minus sidebar and margins
                "overflow": "hidden",  # Prevent any scrolling
                "display": "flex",
                "flexDirection": "column",
                "zIndex": "999"  # Ensure it's above other content
            })

        # Analytical SEC Route - Full screen, non-scrollable
        elif pathname == "/analytical/sec":
            # Display full SEC app taking up entire viewport
            sec_url = "/plotly_integration/dash-app/app/SecReportApp2/"

            # Return a special full-screen layout that bypasses normal content container
            return html.Div([
                # Minimal header with controls - fixed height
                html.Div([
                    html.Div([
                        html.H5("SEC Analysis", style={"margin": "0", "color": "#333"}),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-home me-1"),
                                "Home"
                            ], href="#!/", color="outline-secondary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-external-link-alt me-1"),
                                "Open in New Tab"
                            ], href=sec_url, target="_blank", color="outline-primary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-1"),
                                "Refresh"
                            ], id="refresh-analytical-sec", color="outline-info", size="sm")
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

                # Full-height iframe - no scrolling
                html.Iframe(
                    src=sec_url,
                    style={
                        "width": "100%",
                        "height": "calc(100vh - 50px)",  # Full viewport height minus header
                        "border": "none",
                        "display": "block",
                        "overflow": "hidden"  # Prevent iframe scrolling
                    }
                )
            ], style={
                "position": "fixed",  # Fixed positioning to bypass normal layout
                "top": "0",
                "left": "220px",  # Account for sidebar width + left margin
                "right": "20px",  # Right margin
                "bottom": "0",
                "height": "100vh",
                "width": "calc(100vw - 240px)",  # Full width minus sidebar and margins
                "overflow": "hidden",  # Prevent any scrolling
                "display": "flex",
                "flexDirection": "column",
                "zIndex": "999"  # Ensure it's above other content
            })

        # Analytical Titer Route - Full screen, non-scrollable
        elif pathname == "/analytical/titer":
            titer_url = "/plotly_integration/dash-app/app/TiterReportApp/"

            return html.Div([
                html.Div([
                    html.Div([
                        html.H5("Titer Analysis", style={"margin": "0", "color": "#333"}),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-home me-1"),
                                "Home"
                            ], href="#!/", color="outline-secondary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-external-link-alt me-1"),
                                "Open in New Tab"
                            ], href=titer_url, target="_blank", color="outline-primary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-1"),
                                "Refresh"
                            ], id="refresh-analytical-titer", color="outline-info", size="sm")
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
                    src=titer_url,
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

        # Analytical CE SDS Route - Full screen, non-scrollable
        elif pathname == "/analytical/ce-sds":
            cesds_url = "/plotly_integration/dash-app/app/CESDSReportViewerApp/"

            return html.Div([
                html.Div([
                    html.Div([
                        html.H5("CE SDS Analysis", style={"margin": "0", "color": "#333"}),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-home me-1"),
                                "Home"
                            ], href="#!/", color="outline-secondary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-external-link-alt me-1"),
                                "Open in New Tab"
                            ], href=cesds_url, target="_blank", color="outline-primary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-1"),
                                "Refresh"
                            ], id="refresh-analytical-cesds", color="outline-info", size="sm")
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
                    src=cesds_url,
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

        # Analytical cIEF Route - Full screen, non-scrollable
        elif pathname == "/analytical/cief":
            cief_url = "/plotly_integration/dash-app/app/cIEFReportViewerApp/"

            return html.Div([
                html.Div([
                    html.Div([
                        html.H5("cIEF Analysis", style={"margin": "0", "color": "#333"}),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-home me-1"),
                                "Home"
                            ], href="#!/", color="outline-secondary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-external-link-alt me-1"),
                                "Open in New Tab"
                            ], href=cief_url, target="_blank", color="outline-primary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-1"),
                                "Refresh"
                            ], id="refresh-analytical-cief", color="outline-info", size="sm")
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
                    src=cief_url,
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

        # DSP UFDF Route - Full screen, non-scrollable
        elif pathname == "/dsp/ufdf":
            ufdf_url = "/plotly_integration/dash-app/app/UFDFApp/"

            return html.Div([
                html.Div([
                    html.Div([
                        html.H5("UFDF Process", style={"margin": "0", "color": "#333"}),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-home me-1"),
                                "Home"
                            ], href="#!/", color="outline-secondary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-external-link-alt me-1"),
                                "Open in New Tab"
                            ], href=ufdf_url, target="_blank", color="outline-primary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-1"),
                                "Refresh"
                            ], id="refresh-dsp-ufdf", color="outline-info", size="sm")
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
                    src=ufdf_url,
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

        # DSP VF Route - Full screen, non-scrollable
        elif pathname == "/dsp/vf":
            vf_url = "/plotly_integration/dash-app/app/ViralFiltrationApp/"

            return html.Div([
                html.Div([
                    html.Div([
                        html.H5("Viral Filtration", style={"margin": "0", "color": "#333"}),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-home me-1"),
                                "Home"
                            ], href="#!/", color="outline-secondary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-external-link-alt me-1"),
                                "Open in New Tab"
                            ], href=vf_url, target="_blank", color="outline-primary", size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-1"),
                                "Refresh"
                            ], id="refresh-dsp-vf", color="outline-info", size="sm")
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
                    src=vf_url,
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

        # USP Routes - Full screen, non-scrollable
        elif pathname == "/usp/view-samples":
            usp_samples_url = "/plotly_integration/dash-app/app/UPSampleManagementApp/"
            return create_full_screen_app("USP Sample Management", usp_samples_url, "refresh-usp-samples")

        elif pathname == "/usp/vicell":
            usp_vicell_url = "/plotly_integration/dash-app/app/ViCellReportApp/"
            return create_full_screen_app("USP ViCell", usp_vicell_url, "refresh-usp-vicell")

        elif pathname == "/usp/nova":
            usp_nova_url = "/plotly_integration/dash-app/app/NovaDataReportApp/"
            return create_full_screen_app("USP Nova", usp_nova_url, "refresh-usp-nova")

        # DSP Create DN Route
        elif pathname == "/dsp/create-dn":
            dn_url = "/plotly_integration/dash-app/app/DnAssignmentApp/"
            return create_full_screen_app("Create DN Assignment", dn_url, "refresh-dsp-dn")

        elif pathname == "/cld/create-samples":
            try:
                from ..samples.layouts.create_samples import create_create_samples_layout
                return create_create_samples_layout()
            except ImportError as e:
                print(f"Error importing create samples layout: {e}")
                return html.Div([
                    html.H2("Create CLD Samples"),
                    html.P("Error loading create samples page"),
                    html.P(str(e), className="text-danger")
                ])

        elif pathname == "/cld/view-samples":
            try:
                from ..samples.layouts.view_samples import create_view_samples_layout
                return create_view_samples_layout()
            except ImportError as e:
                print(f"Error importing view samples layout: {e}")
                return html.Div([
                    html.H2("View CLD Samples"),
                    html.P("Error loading view samples page"),
                    html.P(str(e), className="text-danger")
                ])

        elif pathname == "/cld/sample-sets":
            try:
                from ..samples.layouts.sample_sets import create_sample_sets_layout
                return create_sample_sets_layout()
            except ImportError as e:
                print(f"Error importing sample sets layout: {e}")
                return html.Div([
                    html.H2("CLD Sample Sets"),
                    html.P("Error loading sample sets page"),
                    html.P(str(e), className="text-danger")
                ])

        # CLD Routes - Full screen, non-scrollable
        elif pathname == "/cld/vicell":
            cld_vicell_url = "/plotly_integration/dash-app/app/ViCellReportApp/"
            return create_full_screen_app("CLD ViCell", cld_vicell_url, "refresh-cld-vicell")

        elif pathname == "/cld/nova":
            cld_nova_url = "/plotly_integration/dash-app/app/NovaDataReportApp/"
            return create_full_screen_app("CLD Nova", cld_nova_url, "refresh-cld-nova")

        # Database Management Routes - Full screen, non-scrollable
        elif pathname == "/database/import-empower":
            empower_url = "/plotly_integration/dash-app/app/DatabaseManagerApp/"
            return create_full_screen_app("Import Empower Data", empower_url, "refresh-db-empower")

        elif pathname == "/database/import-cesds":
            cesds_import_url = "/plotly_integration/dash-app/app/CeSdsImportManagerApp/"
            return create_full_screen_app("Import CE SDS Data", cesds_import_url, "refresh-db-cesds")

        elif pathname == "/database/import-cief":
            cief_import_url = "/plotly_integration/dash-app/app/cIEFImportManagerApp/"
            return create_full_screen_app("Import cIEF Data", cief_import_url, "refresh-db-cief")

        elif pathname == "/database/import-ufdf":
            ufdf_import_url = "/plotly_integration/dash-app/app/UFDFAnalysis/"
            return create_full_screen_app("Import UFDF Data", ufdf_import_url, "refresh-db-ufdf")

        elif pathname == "/database/import-vf":
            vf_import_url = "/plotly_integration/dash-app/app/ViralFiltrationExperimentImport/"
            return create_full_screen_app("Import VF Data", vf_import_url, "refresh-db-vf")

        elif pathname == "/database/import-nova-flex":
            nova_flex_url = "/plotly_integration/dash-app/app/NovaFlex2DataUploadApp/"
            return create_full_screen_app("Import Nova Flex Data", nova_flex_url, "refresh-db-nova-flex")

        elif pathname == "/database/import-vicell":
            vicell_import_url = "/plotly_integration/dash-app/app/ViCellDataUploadApp/"
            return create_full_screen_app("Import ViCell Data", vicell_import_url, "refresh-db-vicell")

        # Default case - redirect to home
        else:
            print(f"⚠️ Unknown route: {pathname}, redirecting to home")
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