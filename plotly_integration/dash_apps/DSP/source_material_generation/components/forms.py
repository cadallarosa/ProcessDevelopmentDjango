"""Reusable form components using DBC."""
import dash_bootstrap_components as dbc
from dash import dcc, html


def create_labeled_input(
    label: str,
    input_id: str,
    input_type: str = "text",
    placeholder: str = "",
    value=None,
    help_text: str = None,
    required: bool = False
) -> dbc.Row:
    """
    Create a labeled input field with optional help text.

    Args:
        label: Field label text
        input_id: Component ID
        input_type: Input type (text, number, etc.)
        placeholder: Placeholder text
        value: Initial value
        help_text: Optional help text below field
        required: Whether field is required
    """
    label_content = [label]
    if required:
        label_content.append(html.Span(" *", style={"color": "red"}))

    form_content = [
        dbc.Label(label_content, html_for=input_id),
        dbc.Input(
            id=input_id,
            type=input_type,
            placeholder=placeholder,
            value=value
        )
    ]

    if help_text:
        form_content.append(
            dbc.FormText(help_text, color="muted")
        )

    return dbc.Row([
        dbc.Col(form_content, width=12)
    ], className="mb-3")


def create_labeled_dropdown(
    label: str,
    dropdown_id: str,
    options: list = None,
    value=None,
    multi: bool = False,
    placeholder: str = "Select...",
    help_text: str = None,
    clearable: bool = True,
    required: bool = False
) -> dbc.Row:
    """
    Create a labeled dropdown with optional help text.

    Args:
        label: Field label text
        dropdown_id: Component ID
        options: Dropdown options
        value: Initial value(s)
        multi: Allow multiple selections
        placeholder: Placeholder text
        help_text: Optional help text
        clearable: Allow clearing selection
        required: Whether field is required
    """
    label_content = [label]
    if required:
        label_content.append(html.Span(" *", style={"color": "red"}))

    form_content = [
        dbc.Label(label_content, html_for=dropdown_id),
        dcc.Dropdown(
            id=dropdown_id,
            options=options or [],
            value=value,
            multi=multi,
            placeholder=placeholder,
            clearable=clearable
        )
    ]

    if help_text:
        form_content.append(
            dbc.FormText(help_text, color="muted")
        )

    return dbc.Row([
        dbc.Col(form_content, width=12)
    ], className="mb-3")


def create_labeled_radio(
    label: str,
    radio_id: str,
    options: list,
    value=None,
    inline: bool = True
) -> dbc.Row:
    """
    Create a labeled radio button group.

    Args:
        label: Field label text
        radio_id: Component ID
        options: List of dicts with 'label' and 'value' keys
        value: Initial value
        inline: Display inline or stacked
    """
    return dbc.Row([
        dbc.Col([
            dbc.Label(label, className="me-3"),
            dcc.RadioItems(
                id=radio_id,
                options=options,
                value=value,
                inline=inline,
                labelStyle={"marginRight": "20px"} if inline else {}
            )
        ], width=12)
    ], className="mb-3")


def create_info_display(
    label: str,
    display_id: str,
    value: str = ""
) -> dbc.Row:
    """
    Create a read-only info display field.

    Args:
        label: Field label
        display_id: Component ID
        value: Initial display value
    """
    return dbc.Row([
        dbc.Col([
            dbc.Label(label),
            html.Div(
                id=display_id,
                children=value,
                style={
                    "padding": "8px 12px",
                    "border": "1px solid #ced4da",
                    "borderRadius": "4px",
                    "backgroundColor": "#f8f9fa",
                    "fontSize": "14px",
                    "minHeight": "38px"
                }
            )
        ], width=12)
    ], className="mb-3")


def create_searchable_dropdown(
    label: str,
    dropdown_id: str,
    options: list = None,
    value=None,
    placeholder: str = "Select or type to create new...",
    help_text: str = None,
    required: bool = False
) -> dbc.Row:
    """
    Create a searchable dropdown that allows manual entry.

    Args:
        label: Field label text
        dropdown_id: Component ID
        options: Dropdown options
        value: Initial value
        placeholder: Placeholder text
        help_text: Optional help text
        required: Whether field is required
    """
    label_content = [label]
    if required:
        label_content.append(html.Span(" *", style={"color": "red"}))

    form_content = [
        dbc.Label(label_content, html_for=dropdown_id),
        dcc.Dropdown(
            id=dropdown_id,
            options=options or [],
            value=value,
            placeholder=placeholder,
            clearable=True,
            searchable=True,
            # Allow user to enter custom values not in dropdown
            optionHeight=35
        )
    ]

    if help_text:
        form_content.append(
            dbc.FormText(help_text, color="muted")
        )

    return dbc.Row([
        dbc.Col(form_content, width=12)
    ], className="mb-3")
