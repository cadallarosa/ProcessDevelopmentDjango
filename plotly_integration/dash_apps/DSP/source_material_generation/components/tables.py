"""DataTable configurations and styling."""
from dash import dash_table

# Common process step options
COMMON_PROCESS_STEPS = [
    {"label": "Concentration", "value": "Concentration"},
    {"label": "Pooling", "value": "Pooling"},
    {"label": "pH Adjustment", "value": "pH Adjustment"},
    {"label": "Conductivity Adjustment", "value": "Conductivity Adjustment"},
    {"label": "Dilution", "value": "Dilution"},
    {"label": "Buffer Exchange", "value": "Buffer Exchange"},
    {"label": "Formulation", "value": "Formulation"},
    {"label": "Other", "value": "Other"}
]

# Shared table styling
TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "8px 12px",
    "fontSize": "13px",
    "border": "1px solid #dee2e6",
    "borderRight": "1px solid #dee2e6",
    "minWidth": "100px",
    "maxWidth": "300px",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#0d6efd",
    "fontWeight": "600",
    "color": "white",
    "textAlign": "center",
    "fontSize": "13px",
    "padding": "10px 12px",
    "border": "1px solid #0d6efd"
}

TABLE_STYLE_DATA = {
    "backgroundColor": "white",
    "color": "#212529"
}

TABLE_STYLE_DATA_CONDITIONAL = [
    {
        "if": {"row_index": "odd"},
        "backgroundColor": "#f8f9fa"
    }
]


def create_process_steps_table(table_id: str, data: list = None):
    """
    Create the process steps DataTable with dropdown for common processes.

    Args:
        table_id: Component ID
        data: Initial table data
    """
    if data is None:
        data = [{"step": 1, "process": "", "notes": ""}]

    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": "Step", "id": "step", "editable": False, "type": "numeric"},
            {
                "name": "Process",
                "id": "process",
                "editable": True,
                "presentation": "dropdown"
            },
            {"name": "Notes", "id": "notes", "editable": True}
        ],
        data=data,
        editable=True,
        row_deletable=True,
        dropdown={
            "process": {
                "options": COMMON_PROCESS_STEPS,
                "clearable": True
            }
        },
        dropdown_conditional=[
            {
                "if": {"column_id": "process"},
                "options": COMMON_PROCESS_STEPS,
                "clearable": True
            }
        ],
        style_cell=TABLE_STYLE_CELL,
        style_header=TABLE_STYLE_HEADER,
        style_data=TABLE_STYLE_DATA,
        style_data_conditional=TABLE_STYLE_DATA_CONDITIONAL,
        style_table={
            "overflowX": "auto",
            "border": "1px solid #dee2e6",
            "borderRadius": "4px"
        },
        css=[
            {
                "selector": ".Select-menu-outer",
                "rule": "display: block !important; z-index: 9999 !important;"
            },
            {
                "selector": ".Select",
                "rule": "z-index: 9999 !important;"
            }
        ]
    )


def create_sm_management_table(table_id: str, data: list = None):
    """
    Create the source materials management table.

    Args:
        table_id: Component ID
        data: Table data
    """
    if data is None:
        data = []

    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": "SM ID", "id": "sm_id", "type": "numeric"},
            {"name": "Name", "id": "name"},
            {"name": "Project", "id": "project_id"},
            {"name": "DN", "id": "dn", "type": "numeric"},
            {"name": "PD Sample", "id": "pd_sample"},
            {"name": "Created", "id": "created_date"},
            {"name": "Status", "id": "status"}
        ],
        data=data,
        editable=False,
        row_selectable="single",
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=20,
        filter_action="native",
        sort_action="native",
        style_cell=TABLE_STYLE_CELL,
        style_header=TABLE_STYLE_HEADER,
        style_data=TABLE_STYLE_DATA,
        style_data_conditional=TABLE_STYLE_DATA_CONDITIONAL + [
            {
                "if": {"column_id": "sm_id"},
                "fontWeight": "600",
                "color": "#0d6efd"
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "#d1ecf1",
                "border": "1px solid #0d6efd"
            }
        ],
        style_table={
            "overflowX": "auto",
            "border": "1px solid #dee2e6",
            "borderRadius": "4px"
        }
    )


def create_pooling_sample_table(table_id: str = "sm-gen-pooling-table"):
    """
    Create the sample pooling table with selectable rows.

    Args:
        table_id: Component ID

    Returns:
        DataTable for sample selection
    """
    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": "Sample ID", "id": "sample_id"},
            {"name": "Type", "id": "sample_type_label"},
            {"name": "DN", "id": "dn"},
            {"name": "Project", "id": "project_id"},
            {"name": "Description", "id": "description"},
            {"name": "Date", "id": "sample_date"},
            {"name": "A280 (mg/mL)", "id": "a280"},
        ],
        data=[],
        row_selectable="multi",
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=15,
        filter_action="native",
        sort_action="native",
        style_cell={
            "textAlign": "left",
            "padding": "10px 12px",
            "fontSize": "12px",
            "border": "1px solid #dee2e6",
            "borderRight": "1px solid #dee2e6",
            "minWidth": "80px",
            "maxWidth": "250px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_header={
            "backgroundColor": "#0d6efd",
            "fontWeight": "600",
            "color": "white",
            "textAlign": "left",
            "fontSize": "12px",
            "padding": "10px 12px",
            "border": "1px solid #0d6efd"
        },
        style_data={
            "backgroundColor": "white",
            "color": "#212529"
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f8f9fa"
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "#cfe2ff",
                "border": "1px solid #0d6efd"
            },
            {
                "if": {"column_id": "sample_id"},
                "fontWeight": "600",
                "color": "#0d6efd"
            }
        ],
        style_table={
            "overflowX": "auto",
            "border": "1px solid #dee2e6",
            "borderRadius": "4px"
        },
        tooltip_data=[],
        tooltip_duration=None
    )
