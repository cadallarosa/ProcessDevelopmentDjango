"""Reusable table components for DN Assignment app."""
from dash import dash_table

# Table styling constants
TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "2px 4px",
    "fontSize": "11px",
    "border": "1px solid #ddd",
    "borderRight": "1px solid #ddd",
    "minWidth": "100px",
    "width": "100px",
    "maxWidth": "200px",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#0056b3",
    "fontWeight": "bold",
    "color": "white",
    "textAlign": "center",
    "fontSize": "11px",
    "padding": "2px 4px"
}

# Column definitions
COLUMN_ORDER = [
    ("dn", "DN"),
    ("link", "Chromatogram"),
    ("sm_id", "SM ID"),
    ("resulting_pd", "Resulting PD#"),
    ("project_id", "Project ID"),
    ("unit_operation", "Unit Op"),
    ("scouting_details", "Scouting Details"),
    ("notes", "Notes"),
    ("created_by", "Created By"),
    ("assigned_to", "Assigned To"),
    ("status", "Status"),
    ("date_created", "Date Created"),
    ("date_updated", "Date Updated")
]

UNIT_OPS = [
    "ProA", "AEX", "CEX", "CHT", "VI",
    "UFDF", "DF"
]


def create_dn_view_table(table_id: str = "dn-table"):
    """Create the main DN view table with modern styling."""
    return dash_table.DataTable(
        id=table_id,
        columns=[
            {
                "name": label,
                "id": key,
                "presentation": "markdown" if key == "link" else None,
                "type": "numeric" if key == "dn" else "text",
                "editable": False  # Inline editing disabled, use modal instead
            } for key, label in COLUMN_ORDER
        ],
        data=[],
        editable=False,
        row_selectable="single",
        page_action="native",
        page_current=0,
        page_size=25,
        style_table={
            "overflowX": "auto",
            "overflowY": "auto",
            "maxHeight": "calc(100vh - 320px)",
        },
        style_cell={
            "textAlign": "left",
            "padding": "12px",
            "fontSize": "13px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "border": "1px solid #e9ecef",
            "borderBottom": "1px solid #e9ecef",
        },
        style_header={
            "backgroundColor": "#0d6efd",
            "fontWeight": "600",
            "color": "#ffffff",
            "textAlign": "left",
            "fontSize": "12px",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "padding": "12px",
            "borderBottom": "2px solid #0a58ca",
            "position": "sticky",
            "top": 0,
            "zIndex": 1,
        },
        style_data={
            "backgroundColor": "#ffffff",
            "color": "#212529",
        },
        style_data_conditional=[
            # Completed rows - green highlight
            {
                "if": {"filter_query": '{status} = "Completed"'},
                "backgroundColor": "#d1e7dd",
                "color": "#0f5132",
            },
            # Hover effect
            {
                "if": {"state": "active"},
                "backgroundColor": "rgba(13, 110, 253, 0.1)",
                "border": "1px solid #0d6efd !important",
                "cursor": "pointer",
            },
            # Selected row
            {
                "if": {"state": "selected"},
                "backgroundColor": "#e7f1ff",
                "border": "1px solid #0d6efd",
            },
            # Status column badges
            {
                "if": {
                    "filter_query": '{status} = "Completed"',
                    "column_id": "status"
                },
                "backgroundColor": "#198754",
                "color": "#ffffff",
                "fontWeight": "600",
                "borderRadius": "4px",
                "padding": "4px 12px",
                "textAlign": "center",
            },
            {
                "if": {
                    "filter_query": '{status} = "Pending"',
                    "column_id": "status"
                },
                "backgroundColor": "#ffc107",
                "color": "#000000",
                "fontWeight": "600",
                "borderRadius": "4px",
                "padding": "4px 12px",
                "textAlign": "center",
            },
            {
                "if": {
                    "filter_query": '{status} = "In Progress"',
                    "column_id": "status"
                },
                "backgroundColor": "#0d6efd",
                "color": "#ffffff",
                "fontWeight": "600",
                "borderRadius": "4px",
                "padding": "4px 12px",
                "textAlign": "center",
            },
            # DN column styling
            {
                "if": {"column_id": "dn"},
                "fontWeight": "600",
                "color": "#0d6efd",
            },
            # SM ID column styling
            {
                "if": {"column_id": "sm_id"},
                "fontWeight": "500",
                "color": "#6c757d",
            },
            # PD column styling
            {
                "if": {"column_id": "resulting_pd"},
                "fontWeight": "500",
                "color": "#6c757d",
            },
        ],
        filter_action="native",
        sort_action="native",
        markdown_options={"link_target": "_blank"},
        css=[
            {
                "selector": "table",
                "rule": "table-layout: auto !important; width: 100% !important;"
            },
            {
                "selector": ".dash-spreadsheet-container .dash-spreadsheet-inner table",
                "rule": "border-collapse: separate !important; border-spacing: 0 4px !important;"
            },
            {
                "selector": ".dash-table-container .row",
                "rule": "transition: all 0.2s ease !important;"
            }
        ]
    )


def create_dn_bulk_table(table_id: str = "dn-bulk-table"):
    """Create the bulk DN creation table."""
    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": label, "id": key, "editable": True, "presentation": "dropdown"}
            if key in ("created_by", "assigned_to")
            else {"name": label, "id": key, "editable": True}
            for key, label in COLUMN_ORDER
            if key not in ("dn", "date_created", "date_updated", "id", "source_material_status", "link")
        ],
        data=[{col: "" for col in [
            "dn",
            "project_id",
            "study_name",
            "assigned_to",
            "created_by",
            "scouting_details",
            "unit_operation",
            "notes",
            "status"
        ]}],
        editable=True,
        row_deletable=True,
        style_cell=TABLE_STYLE_CELL,
        style_header=TABLE_STYLE_HEADER,
        style_table={"overflowX": "auto"},
        dropdown={
            "created_by": {"options": []},
            "assigned_to": {"options": []}
        }
    )


def create_dn_edit_table(table_id: str = "edit-dn-table"):
    """Create the single DN edit table."""
    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": label, "id": key, "editable": True, "presentation": "dropdown"}
            if key in ("created_by", "assigned_to")
            else {"name": label, "id": key, "editable": True}
            for key, label in COLUMN_ORDER
            if key not in ("date_created", "date_updated", "id", "source_material_status", "link")
        ],
        data=[],
        editable=True,
        style_cell=TABLE_STYLE_CELL,
        style_header=TABLE_STYLE_HEADER,
        style_table={"overflowX": "auto"},
        dropdown={
            "created_by": {"options": []},
            "assigned_to": {"options": []}
        }
    )


def create_pd_sample_table(table_id: str = "view-pd-table"):
    """Create the PD sample view/edit table."""
    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": "PD#", "id": "sample_id", "editable": False},
            {"name": "Project ID", "id": "project_id", "editable": True},
            {"name": "Linked DN", "id": "dn", "editable": True, "type": "numeric"},
            {"name": "Description", "id": "description", "editable": True},
            {"name": "Sample Date (YYYY-MM-DD)", "id": "sample_date", "editable": True},
            {"name": "A280 (mg/mL)", "id": "a280", "editable": True, "type": "numeric"},
            {"name": "Analyst", "id": "analyst", "editable": True},
            {"name": "Notes", "id": "notes", "editable": True},
        ],
        data=[],
        editable=True,
        style_cell=TABLE_STYLE_CELL,
        style_header=TABLE_STYLE_HEADER,
        style_table={"overflowX": "auto"},
        page_size=40,
        page_current=0,
        filter_action="native",
        sort_action="native",
    )


def create_pd_bulk_table(table_id: str = "pd-bulk-table"):
    """Create the bulk PD sample creation table."""
    from datetime import datetime

    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": "Project ID", "id": "project_id", "editable": True},
            {"name": "Linked DN", "id": "dn", "editable": True},
            {"name": "Description", "id": "description", "editable": True},
            {"name": "Sample Date (YYYY-MM-DD)", "id": "sample_date", "editable": True},
            {"name": "A280", "id": "a280", "editable": True},
            {"name": "Analyst", "id": "analyst", "editable": True},
            {"name": "Notes", "id": "notes", "editable": True},
        ],
        data=[{
            "sample_id": "",
            "sample_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "",
            "a280": "",
            "notes": "",
            "dn": "",
            "project_id": "",
            "analyst": ""
        }],
        editable=True,
        row_deletable=True,
        style_cell=TABLE_STYLE_CELL,
        style_header=TABLE_STYLE_HEADER,
        style_table={"overflowX": "auto"}
    )


def create_sample_info_existing_table(table_id: str = "existing-sample-table"):
    """Create the existing samples table for Sample Info tab."""
    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": "Sample ID", "id": "sample_id", "editable": False},
            {"name": "Sample Date (YYYY-MM-DD)", "id": "sample_date", "editable": True, "type": "datetime"},
            {"name": "Description", "id": "description", "editable": True},
            {"name": "A280", "id": "a280_result", "editable": True, "type": "numeric"},
            {"name": "Notes", "id": "notes", "editable": True}
        ],
        data=[],
        editable=True,
        style_cell=TABLE_STYLE_CELL,
        style_header=TABLE_STYLE_HEADER,
        style_table={"overflowX": "auto"}
    )


def create_sample_info_new_table(table_id: str = "new-sample-table"):
    """Create the new samples table for Sample Info tab."""
    return dash_table.DataTable(
        id=table_id,
        columns=[
            {"name": "Sample ID", "id": "sample_id", "editable": False},
            {"name": "Sample Date (YYYY-MM-DD)", "id": "sample_date", "editable": True, "type": "datetime"},
            {"name": "Description", "id": "description", "editable": True},
            {"name": "A280", "id": "a280_result", "editable": True, "type": "numeric"},
            {"name": "Notes", "id": "notes", "editable": True}
        ],
        data=[],
        editable=True,
        row_deletable=True,
        style_cell=TABLE_STYLE_CELL,
        style_header=TABLE_STYLE_HEADER,
        style_table={"overflowX": "auto"}
    )
