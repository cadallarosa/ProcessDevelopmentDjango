"""Form components for DN Assignment app."""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_labeled_input(
    label: str,
    input_id: str,
    input_type: str = "text",
    placeholder: str = "",
    value=None,
    required: bool = False,
    disabled: bool = False
) -> html.Div:
    """Create a labeled input field with DBC styling."""
    label_content = [label]
    if required:
        label_content.append(html.Span(" *", style={"color": "red"}))

    return html.Div([
        dbc.Label(label_content, style={"marginRight": "10px"}),
        dbc.Input(
            id=input_id,
            type=input_type,
            placeholder=placeholder,
            value=value,
            disabled=disabled,
            style={"flex": 1}
        )
    ], style={"display": "flex", "alignItems": "center"})


def create_labeled_dropdown(
    label: str,
    dropdown_id: str,
    options: list = None,
    value=None,
    placeholder: str = "Select...",
    multi: bool = False,
    clearable: bool = True
) -> html.Div:
    """Create a labeled dropdown with DBC styling."""
    return html.Div([
        dbc.Label(label, style={"marginRight": "10px"}),
        dcc.Dropdown(
            id=dropdown_id,
            options=options or [],
            value=value,
            placeholder=placeholder,
            multi=multi,
            clearable=clearable,
            style={"flex": 1}
        )
    ], style={"display": "flex", "alignItems": "center"})


def create_mode_selector(radio_id: str, default_value: str = "existing") -> html.Div:
    """Create a mode selector radio buttons."""
    return html.Div([
        dbc.Label("Mode", style={"marginRight": "20px"}),
        dcc.RadioItems(
            id=radio_id,
            options=[
                {"label": "Use Existing", "value": "existing"},
                {"label": "Create New", "value": "new"}
            ],
            value=default_value,
            inline=True,
            labelStyle={"marginRight": "25px"}
        )
    ], style={"display": "flex", "alignItems": "center"})
