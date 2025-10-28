"""Table components for PD Samples Management app."""
from dash import dash_table

# PD Samples table column order
PD_COLUMN_ORDER = [
    ("sample_id", "PD#"),
    ("project_id", "Project ID"),
    ("dn", "Linked DN"),
    ("description", "Description"),
    ("sample_date", "Sample Date"),
    ("a280", "A280 (mg/mL)"),
    ("analyst", "Analyst"),
    ("status", "Status"),
    ("notes", "Notes"),
]


def create_pd_samples_table(table_id: str = "pd-samples-table"):
    """Create the main PD samples table with modern styling and inline editing."""
    # Define which columns are editable
    editable_columns = {"project_id", "description", "analyst", "notes", "status"}

    return dash_table.DataTable(
        id=table_id,
        columns=[
            {
                "name": label,
                "id": key,
                "editable": key in editable_columns,
                "presentation": "dropdown" if key == "status" else "input"
            } for key, label in PD_COLUMN_ORDER
        ],
        data=[],
        editable=True,  # Enable inline editing
        dropdown={
            "status": {
                "options": [
                    {"label": "In Progress", "value": "In Progress"},
                    {"label": "Complete", "value": "Complete"},
                    {"label": "Review", "value": "Review"},
                ]
            }
        },
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
            # Completed samples - green highlight
            {
                "if": {"filter_query": '{status} = "Complete"'},
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
                    "filter_query": '{status} = "Complete"',
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
            {
                "if": {
                    "filter_query": '{status} = "Review"',
                    "column_id": "status"
                },
                "backgroundColor": "#ffc107",
                "color": "#000000",
                "fontWeight": "600",
                "borderRadius": "4px",
                "padding": "4px 12px",
                "textAlign": "center",
            },
            # PD# column styling
            {
                "if": {"column_id": "sample_id"},
                "fontWeight": "600",
                "color": "#0d6efd",
            },
            # DN column styling
            {
                "if": {"column_id": "dn"},
                "fontWeight": "500",
                "color": "#6c757d",
            },
        ],
        filter_action="native",
        sort_action="native",
    )
