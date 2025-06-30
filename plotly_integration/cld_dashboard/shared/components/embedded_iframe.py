import dash_bootstrap_components as dbc
from dash import html


def create_embedded_iframe(src_url, title="Embedded Application", height="800px", show_controls=True):
    """
    Create an embedded iframe component - NO HORIZONTAL SCROLLING
    """
    header_content = [html.H5(title, className="mb-0")]

    if show_controls:
        header_content.append(
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-external-link-alt me-1"),
                    "Open in New Tab"
                ],
                    href=src_url,
                    target="_blank",
                    color="outline-primary",
                    size="sm"),
                dbc.Button([
                    html.I(className="fas fa-sync-alt me-1"),
                    "Refresh"
                ],
                    id={"type": "iframe-refresh", "index": title},
                    color="outline-secondary",
                    size="sm")
            ], className="float-end")
        )

    return dbc.Card([
        dbc.CardHeader(header_content) if show_controls else None,
        dbc.CardBody([
            html.Iframe(
                id={"type": "embedded-iframe", "index": title},
                src=src_url,
                style={
                    "width": "100%",
                    "height": height,
                    "border": "none",
                    "borderRadius": "5px" if not show_controls else "0 0 5px 5px",
                    "overflowX": "hidden",  # 🎯 NO horizontal scrolling
                    "overflowY": "auto"     # 🎯 Allow vertical scrolling only
                }
            )
        ], style={
            "padding": "0",
            "overflowX": "hidden",  # 🎯 Also prevent card body from horizontal scrolling
            "width": "100%"
        })
    ], className="shadow", style={
        "overflowX": "hidden",  # 🎯 Prevent card from horizontal scrolling
        "width": "100%"
    })


def create_loading_iframe(title="Loading Application...", height="800px"):
    """
    Create a loading placeholder for iframe content

    Args:
        title (str): Loading message
        height (str): Height of the loading area

    Returns:
        dbc.Card: Card with loading spinner
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                dbc.Spinner(
                    html.Div(id="loading-content"),
                    size="lg",
                    color="primary",
                    type="border"
                ),
                html.H5(title, className="mt-3 text-muted")
            ],
                style={
                    "height": height,
                    "display": "flex",
                    "flex-direction": "column",
                    "justify-content": "center",
                    "align-items": "center",
                    "text-align": "center"
                })
        ])
    ], className="shadow")


def create_error_iframe(error_message="Application failed to load", height="800px"):
    """
    Create an error display for failed iframe loading

    Args:
        error_message (str): Error message to display
        height (str): Height of the error area

    Returns:
        dbc.Card: Card with error message
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-exclamation-triangle fa-3x text-danger mb-3"),
                html.H5("Application Error", className="text-danger"),
                html.P(error_message, className="text-muted"),
                dbc.Button([
                    html.I(className="fas fa-redo me-1"),
                    "Retry"
                ],
                    color="outline-primary",
                    id="retry-iframe-btn")
            ],
                style={
                    "height": height,
                    "display": "flex",
                    "flex-direction": "column",
                    "justify-content": "center",
                    "align-items": "center",
                    "text-align": "center"
                })
        ])
    ], className="shadow")


def create_minimal_embedded_iframe(src_url, height="900px"):
    """
    Create a minimal embedded iframe with no dashboard headers

    Args:
        src_url (str): URL of the app to embed
        height (str): Height of the iframe

    Returns:
        html.Iframe: Minimal iframe with no wrapper
    """
    return html.Iframe(
        src=src_url,
        style={
            "width": "max-content%",
            "overflowX": "hidden",
            "height": height,
            "border": "none",
            "margin": "0",
            "padding": "0"
        }
    )