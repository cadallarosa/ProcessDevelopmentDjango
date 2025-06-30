# Enhanced routing system for CLD Dashboard - Complete File with AKTA Integration

from dash import html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs
from ..shared.styles.common_styles import SIDEBAR_STYLE, ICONS
from ..config.app_urls import get_navigation_links, INTERNAL_ROUTES


def create_sidebar_navigation():
    """Create sidebar navigation component with hash links"""
    nav_links = get_navigation_links()

    sidebar_content = []

    # Dashboard header
    sidebar_content.extend([
        html.Div([
            html.H4("CLD Dashboard", className="text-primary mb-3"),
            html.Hr()
        ])
    ])

    # Main navigation - Updated for hash routing
    for section_name, links in nav_links.items():
        if section_name != "main":
            sidebar_content.append(
                html.P(section_name.replace("_", " ").upper(),
                       className="text-muted small fw-bold mb-1 mt-3")
            )

        nav_items = []
        for link in links:
            # Convert to hash-based URLs
            hash_url = f"#!/{link['url'].lstrip('/')}" if link['url'] != "/" else "#!/"
            nav_items.append(
                html.A([
                    html.I(className=f"fas {link['icon']} me-2"),
                    link['name']
                ],
                    href=hash_url,
                    className="nav-link",
                    style={
                        "color": "#212529",
                        "textDecoration": "none",
                        "padding": "0.5rem 0.75rem",
                        "borderRadius": "0.375rem",
                        "display": "block",
                        "marginBottom": "0.25rem"
                    })
            )

        sidebar_content.append(
            html.Div(nav_items, className="mb-2")
        )

        if section_name == "main":
            sidebar_content.append(html.Hr())

    return html.Div(sidebar_content, style=SIDEBAR_STYLE)


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
         Input("url", "href")],  # Add href to extract query params
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
            # Extract the query string from hash URL
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
            from ..core.dashboard_home import create_dashboard_layout
            return create_dashboard_layout()

        # Sample Sets - UPDATED ROUTING
        elif pathname == "/sample-sets":
            try:
                from ..samples.layouts.sample_sets import create_sample_sets_layout
                return create_sample_sets_layout()
            except ImportError as e:
                print(f"Error importing sample sets layout: {e}")
                return html.Div([
                    html.H2("Sample Sets"),
                    html.P("Error loading sample sets page"),
                    html.P(str(e), className="text-danger")
                ])

        elif pathname == "/sample-sets/table":
            try:
                from ..samples.layouts.sample_sets import create_sample_sets_table_layout
                return create_sample_sets_table_layout()
            except ImportError:
                # If table layout doesn't exist, use main layout
                try:
                    from ..samples.layouts.sample_sets import create_sample_sets_layout
                    return create_sample_sets_layout()
                except ImportError:
                    return html.Div([
                        html.H2("Sample Sets - Table View"),
                        html.P("Sample sets table page - placeholder")
                    ])

        elif pathname == "/sample-sets/view":
            try:
                from ..samples.layouts.sample_sets import create_sample_set_detail_layout
                return create_sample_set_detail_layout(query_params)
            except ImportError:
                return html.Div([
                    html.H2("Sample Set Details"),
                    html.P("Sample set detail page - placeholder")
                ])

        # Individual Samples
        elif pathname == "/samples/view":
            try:
                from ..samples.layouts.view_samples import create_view_samples_layout
                return create_view_samples_layout()
            except ImportError:
                return html.Div([
                    html.H2("View Samples"),
                    html.P("View samples page - placeholder")
                ])

        elif pathname == "/samples/create":
            try:
                from ..samples.layouts.create_samples import create_create_samples_layout
                return create_create_samples_layout()
            except ImportError:
                return html.Div([
                    html.H2("Create Samples"),
                    html.P("Create samples page - placeholder")
                ])

        # SEC Analysis Routes
        elif pathname == "/analysis/sec":
            try:
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_dashboard_layout
                return create_sec_dashboard_layout()
            except ImportError:
                return html.Div([
                    html.H2("SEC Analysis"),
                    html.P("SEC analysis page - placeholder")
                ])

        elif pathname == "/analysis/sec/sample-sets":
            try:
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_sample_sets_layout
                return create_sec_sample_sets_layout()
            except ImportError:
                return html.Div([
                    html.H2("SEC Sample Sets"),
                    html.P("SEC sample sets page - placeholder")
                ])

        elif pathname == "/analysis/sec/reports":
            try:
                from ..embedded_apps.sec_integration.sec_dashboard import create_sec_reports_layout
                return create_sec_reports_layout()
            except ImportError:
                return html.Div([
                    html.H2("SEC Reports"),
                    html.P("SEC reports page - placeholder")
                ])

        elif pathname == "/analysis/sec/report":
            try:
                print(f"🔍 Routing to SEC embed with params: {query_params}")
                from ..embedded_apps.sec_integration.sec_embedder import create_embedded_sec_report
                return create_embedded_sec_report(query_params)
            except ImportError as e:
                print(f"Error importing sec_embedder: {e}")
                return html.Div([
                    html.H2("SEC Report"),
                    html.P("Error loading SEC embedder module"),
                    html.P(str(e), className="text-danger")
                ])
            except Exception as e:
                print(f"Error creating SEC embed: {e}")
                import traceback
                traceback.print_exc()
                return html.Div([
                    html.H2("SEC Report"),
                    dbc.Alert([
                        html.P("Error loading SEC report"),
                        html.P(str(e), className="font-monospace small")
                    ], color="danger")
                ])

        # ✅ AKTA Analysis Routes (NEW)
        elif pathname == "/analysis/akta":
            try:
                from ..embedded_apps.akta_integration.akta_dashboard import create_akta_dashboard_layout
                return create_akta_dashboard_layout()
            except ImportError as e:
                print(f"Error importing akta_dashboard: {e}")
                return html.Div([
                    html.H2("AKTA Analysis"),
                    html.P("AKTA analysis dashboard - placeholder"),
                    html.P(str(e), className="text-danger")
                ])

        elif pathname == "/analysis/akta/sample-sets":
            try:
                from ..embedded_apps.akta_integration.akta_dashboard import create_akta_sample_sets_layout
                return create_akta_sample_sets_layout()
            except ImportError as e:
                print(f"Error importing akta sample sets: {e}")
                return html.Div([
                    html.H2("AKTA Sample Sets"),
                    html.P("AKTA sample sets page - placeholder"),
                    html.P(str(e), className="text-danger")
                ])

        elif pathname == "/analysis/akta/reports":
            try:
                from ..embedded_apps.akta_integration.akta_dashboard import create_akta_reports_layout
                return create_akta_reports_layout()
            except ImportError as e:
                print(f"Error importing akta reports: {e}")
                return html.Div([
                    html.H2("AKTA Reports"),
                    html.P("AKTA reports page - placeholder"),
                    html.P(str(e), className="text-danger")
                ])

        elif pathname == "/analysis/akta/report":
            try:
                print(f"🔍 Routing to AKTA embed with params: {query_params}")
                from ..embedded_apps.akta_integration.akta_embedder import create_embedded_akta_report
                return create_embedded_akta_report(query_params)
            except ImportError as e:
                print(f"Error importing akta_embedder: {e}")
                return html.Div([
                    html.H2("AKTA Report"),
                    html.P("Error loading AKTA embedder module"),
                    html.P(str(e), className="text-danger")
                ])
            except Exception as e:
                print(f"Error creating AKTA embed: {e}")
                import traceback
                traceback.print_exc()
                return html.Div([
                    html.H2("AKTA Report"),
                    dbc.Alert([
                        html.P("Error loading AKTA report"),
                        html.P(str(e), className="font-monospace small")
                    ], color="danger")
                ])

        # Test routes
        elif pathname == "/test/sec-embed":
            try:
                from ..embedded_apps.sec_integration.sec_embedder import create_sec_test_embed
                return create_sec_test_embed()
            except Exception as e:
                return html.Div([
                    html.H2("SEC Embed Test"),
                    dbc.Alert([
                        html.H5("Error loading test"),
                        html.P(str(e))
                    ], color="danger")
                ])

        elif pathname == "/test/akta-embed":
            try:
                # Test AKTA embed with sample data
                test_query_params = {'fb': ['1598,1599']}
                from ..embedded_apps.akta_integration.akta_embedder import create_embedded_akta_report
                return create_embedded_akta_report(test_query_params)
            except Exception as e:
                return html.Div([
                    html.H2("AKTA Embed Test"),
                    dbc.Alert([
                        html.H5("Error loading AKTA test"),
                        html.P(str(e))
                    ], color="danger")
                ])

        elif pathname == "/test/sec-iframe":
            # Direct iframe test
            report_id = "328"  # Replace with a real report ID
            sec_url = f"/plotly_integration/dash-app/app/SecReportApp2/?report_id={report_id}"

            return dbc.Container([
                html.H2("Direct SEC Iframe Test"),
                dbc.Alert([
                    html.P(f"Testing direct iframe with report_id: {report_id}"),
                    html.P(f"URL: {sec_url}", className="font-monospace small")
                ], color="info"),

                dbc.Card([
                    dbc.CardBody([
                        html.Iframe(
                            src=sec_url,
                            style={
                                "width": "100%",
                                "height": "800px",
                                "border": "none"
                            }
                        )
                    ], style={"padding": "0"})
                ], className="shadow")
            ], style={"padding": "20px"})

        elif pathname == "/test/akta-iframe":
            # Direct AKTA iframe test
            akta_url = "/plotly_integration/dash-app/app/AktaChromatogramApp/?fb=1598,1599&embed=true"

            return dbc.Container([
                html.H2("Direct AKTA Iframe Test"),
                dbc.Alert([
                    html.P("Testing direct iframe with sample FB numbers: 1598,1599"),
                    html.P(f"URL: {akta_url}", className="font-monospace small")
                ], color="warning"),

                dbc.Card([
                    dbc.CardBody([
                        html.Iframe(
                            src=akta_url,
                            style={
                                "width": "100%",
                                "height": "800px",
                                "border": "none"
                            }
                        )
                    ], style={"padding": "0"})
                ], className="shadow")
            ], style={"padding": "20px"})

        # Settings
        elif pathname == "/settings":
            from ..core.dashboard_home import create_settings_layout
            return create_settings_layout()

        # Help
        elif pathname == "/help":
            return create_help_layout()

        # Default case
        else:
            from ..core.dashboard_home import create_dashboard_layout
            return create_dashboard_layout()


def create_help_layout():
    """Create help page layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Help & Documentation"),
                html.Hr(),

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Getting Started", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P(
                            "Welcome to the CLD Dashboard v3. This application uses hash-based routing for better URL handling."),
                        html.Ul([
                            html.Li("All URLs use hash routing (#!/path/to/page)"),
                            html.Li("URLs are now shareable and reloadable"),
                            html.Li("Use the sidebar to navigate between sections"),
                            html.Li("Bookmark any page - they all work!")
                        ])
                    ])
                ], className="mb-4"),

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Hash-Based URLs", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("This dashboard uses hash-based routing for better URL persistence:"),
                        html.Ul([
                            html.Li("#!/samples/view - View all samples"),
                            html.Li("#!/samples/create - Create new samples"),
                            html.Li("#!/sample-sets - Sample sets management"),
                            html.Li("#!/sample-sets/table - Sample sets table view"),
                            html.Li("#!/analysis/sec - SEC analysis dashboard"),
                            html.Li("#!/analysis/akta - AKTA analysis dashboard"),  # ✅ NEW
                            html.Li("#!/analysis/sec/report?samples=FB1598,FB1599 - Embedded SEC report"),
                            html.Li("#!/analysis/akta/report?fb=1598,1599 - Embedded AKTA report")  # ✅ NEW
                        ]),
                        html.P("These URLs can be bookmarked, shared, and reloaded safely!", className="text-success")
                    ])
                ], className="mb-4"),

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Test Routes", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("Development and testing routes:"),
                        html.Ul([
                            html.Li([
                                html.A("SEC Embed Test", href="#!/test/sec-embed"),
                                " - Test SEC embedding functionality"
                            ]),
                            html.Li([
                                html.A("AKTA Embed Test", href="#!/test/akta-embed"),
                                " - Test AKTA embedding functionality"
                            ]),
                            html.Li([
                                html.A("SEC Iframe Test", href="#!/test/sec-iframe"),
                                " - Direct SEC iframe test"
                            ]),
                            html.Li([
                                html.A("AKTA Iframe Test", href="#!/test/akta-iframe"),
                                " - Direct AKTA iframe test"
                            ])
                        ])
                    ])
                ])
            ])
        ])
    ], style={"padding": "20px"})