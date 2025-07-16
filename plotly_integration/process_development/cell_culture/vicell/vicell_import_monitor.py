# vicell_import_monitor.py - Dashboard to monitor ViCell imports
from datetime import datetime
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from plotly_integration.tasks import check_and_import_vicell_files, get_vicell_import_status
from django.core.cache import cache
import json

# Initialize the Dash app
app = DjangoDash('ViCellImportMonitorApp')

app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "padding": "20px",
        "maxWidth": "1400px",
        "margin": "0 auto",
        "backgroundColor": "#f4f7f6",
    },
    children=[
        html.Div(
            style={
                "backgroundColor": "white",
                "padding": "30px",
                "borderRadius": "10px",
                "boxShadow": "0 2px 10px rgba(0,0,0,0.1)",
            },
            children=[
                html.H1(
                    "ViCell Import Monitor",
                    style={
                        "textAlign": "center",
                        "color": "#0047b3",
                        "marginBottom": "30px"
                    }
                ),

                # Control buttons
                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "gap": "20px",
                        "marginBottom": "30px",
                    },
                    children=[
                        html.Button(
                            "▶ Run Import Now",
                            id="run-vicell-import-btn",
                            n_clicks=0,
                            style={
                                "backgroundColor": "#28a745",
                                "color": "white",
                                "padding": "12px 30px",
                                "border": "none",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontSize": "16px",
                                "fontWeight": "bold",
                            },
                        ),
                        html.Button(
                            "🔄 Refresh Status",
                            id="refresh-vicell-btn",
                            n_clicks=0,
                            style={
                                "backgroundColor": "#007bff",
                                "color": "white",
                                "padding": "12px 30px",
                                "border": "none",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontSize": "16px",
                                "fontWeight": "bold",
                            },
                        ),
                    ],
                ),

                # Status display
                html.Div(
                    id="vicell-status",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "padding": "20px",
                        "borderRadius": "5px",
                        "marginBottom": "20px",
                    }
                ),

                # File tracking table
                html.H3("File Tracking", style={"color": "#0047b3", "marginTop": "30px"}),
                html.Div(id="file-tracking-table"),

                # Last import details
                html.H3("Last Import Details", style={"color": "#0047b3", "marginTop": "30px"}),
                html.Div(
                    id="last-import-details",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "padding": "20px",
                        "borderRadius": "5px",
                    }
                ),

                # Hidden div for import trigger
                html.Div(id="import-trigger-vicell", style={"display": "none"}),

                # Auto-refresh
                dcc.Interval(
                    id="interval-vicell",
                    interval=10 * 1000,  # Update every 10 seconds
                    n_intervals=0
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("import-trigger-vicell", "children"),
    Input("run-vicell-import-btn", "n_clicks"),
    prevent_initial_call=True
)
def trigger_import(n_clicks):
    if n_clicks > 0:
        task = check_and_import_vicell_files.delay()
        return json.dumps({"task_id": task.id})
    return ""


@app.callback(
    [Output("vicell-status", "children"),
     Output("file-tracking-table", "children"),
     Output("last-import-details", "children")],
    [Input("interval-vicell", "n_intervals"),
     Input("refresh-vicell-btn", "n_clicks"),
     Input("import-trigger-vicell", "children")]
)
def update_dashboard(n_intervals, refresh_clicks, import_trigger):
    """Update dashboard with current status"""

    try:
        status = get_vicell_import_status()
    except Exception as e:
        status = {"error": str(e)}

    # Status display
    if status.get("is_locked"):
        status_text = "🔄 Import in progress..."
        status_color = "#ffc107"
    else:
        status_text = "✅ Ready"
        status_color = "#28a745"

    status_div = html.Div([
        html.H4(
            status_text,
            style={"color": status_color, "marginBottom": "10px"}
        ),
        html.P(f"Monitoring folder: {status.get('folder', 'N/A')}")
    ])

    # File tracking table
    tracked_files = status.get('tracked_files', {})
    if tracked_files:
        table_data = []
        for filename, file_info in tracked_files.items():
            table_data.append({
                'File': filename,
                'Current Size': f"{file_info['current_size']:,} bytes",
                'Last Import': file_info['last_imported'],
                'Rows Imported': file_info['last_imported_rows'],
                'Has Changes': '🟢 Yes' if file_info['has_changes'] else '⚪ No'
            })

        file_table = dash_table.DataTable(
            data=table_data,
            columns=[{"name": i, "id": i} for i in
                     ['File', 'Current Size', 'Last Import', 'Rows Imported', 'Has Changes']],
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#0047b3",
                "color": "white",
                "fontWeight": "bold"
            },
            style_cell={
                "padding": "10px",
                "textAlign": "left",
            },
            style_data={"backgroundColor": "white"},
        )
    else:
        file_table = html.P("No files being tracked", style={"color": "#666"})

    # Last import details
    last_import = status.get('last_import')
    if last_import:
        timestamp = datetime.fromisoformat(last_import['timestamp'])

        details_items = [
            html.H5(f"Last Import: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"),
            html.P(f"Total New Records: {last_import['total_new_records']}"),
            html.Hr(),
        ]

        for file_info in last_import['processed_files']:
            if 'error' in file_info:
                details_items.append(
                    html.Div([
                        html.Strong(file_info['file']),
                        html.P(f"❌ Error: {file_info['error']}", style={"color": "#dc3545"})
                    ], style={"marginBottom": "10px"})
                )
            else:
                details_items.append(
                    html.Div([
                        html.Strong(file_info['file']),
                        html.P(f"✅ Imported {file_info['new_rows']} new rows (Total: {file_info['total_rows']})")
                    ], style={"marginBottom": "10px"})
                )

        last_import_div = html.Div(details_items)
    else:
        last_import_div = html.P("No import history available", style={"color": "#666"})

    return status_div, file_table, last_import_div