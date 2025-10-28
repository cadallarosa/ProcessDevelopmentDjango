"""Table components for PD Analytics Dashboard."""
from dash import dash_table

# Analytics table column order
ANALYTICS_COLUMN_ORDER = [
    ("sample_id", "PD#"),
    ("project_id", "Project"),
    ("dn", "DN"),
    ("sample_date", "Date"),
    ("a280", "A280"),
    ("sec_main_peak", "SEC Main%"),
    ("sec_hmw", "HMW%"),
    ("sec_lmw", "LMW%"),
    ("sec_qc", "SEC QC"),
    ("titer", "Titer (g/L)"),
    ("titer_qc", "Titer QC"),
    ("mass_expected", "Mass Exp"),
    ("mass_observed", "Mass Obs"),
    ("glycan", "Glycan"),
    ("ce_sds", "CE-SDS"),
    ("cief", "cIEF"),
    ("hcp", "HCP"),
    ("proa", "ProA"),
    ("analyst", "Analyst"),
    ("status", "Status"),
]


def create_analytics_table(table_id: str = "analytics-table"):
    """Create the analytics table with all LIMS results."""
    return dash_table.DataTable(
        id=table_id,
        columns=[
            {
                "name": label,
                "id": key,
                "editable": False
            } for key, label in ANALYTICS_COLUMN_ORDER
        ],
        data=[],
        editable=False,
        row_selectable=False,
        page_action="native",
        page_current=0,
        page_size=50,
        style_table={
            "overflowX": "auto",
            "overflowY": "auto",
            "maxHeight": "calc(100vh - 280px)",
        },
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "fontSize": "12px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "border": "1px solid #e9ecef",
            "borderBottom": "1px solid #e9ecef",
            "minWidth": "80px",
            "maxWidth": "150px",
            "whiteSpace": "normal"
        },
        style_header={
            "backgroundColor": "#0d6efd",
            "fontWeight": "600",
            "color": "#ffffff",
            "textAlign": "center",
            "fontSize": "11px",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "padding": "10px",
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
            # QC Pass - green
            {
                "if": {"filter_query": '{sec_qc} = "Pass"', "column_id": "sec_qc"},
                "backgroundColor": "#198754",
                "color": "#ffffff",
                "fontWeight": "600",
            },
            {
                "if": {"filter_query": '{titer_qc} = "Pass"', "column_id": "titer_qc"},
                "backgroundColor": "#198754",
                "color": "#ffffff",
                "fontWeight": "600",
            },
            # QC Fail - red
            {
                "if": {"filter_query": '{sec_qc} = "Fail"', "column_id": "sec_qc"},
                "backgroundColor": "#dc3545",
                "color": "#ffffff",
                "fontWeight": "600",
            },
            {
                "if": {"filter_query": '{titer_qc} = "Fail"', "column_id": "titer_qc"},
                "backgroundColor": "#dc3545",
                "color": "#ffffff",
                "fontWeight": "600",
            },
            # PD# styling
            {
                "if": {"column_id": "sample_id"},
                "fontWeight": "600",
                "color": "#0d6efd",
            },
            # Status styling
            {
                "if": {"filter_query": '{status} = "Complete"', "column_id": "status"},
                "backgroundColor": "#d1e7dd",
                "color": "#0f5132",
                "fontWeight": "600",
            },
        ],
        filter_action="native",
        sort_action="native",
        export_format="xlsx",
        export_headers="display",
    )
