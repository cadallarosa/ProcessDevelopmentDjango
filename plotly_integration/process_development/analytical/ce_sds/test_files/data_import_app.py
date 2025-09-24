import os
import threading
from dash import dcc, html
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from .process_asc import save_asc_to_db, move_file_to_processed

# Global import status tracker
import_status = {
    "running": False,
    "total": 0,
    "current": 0,
    "filename": "",
    "finished": False,
    "error": ""
}

# Initialize the Dash app
app = DjangoDash('CeSdsImportManagerApp', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = html.Div([
    html.H2("CE SDS Import Manager", style={"textAlign": "center", "marginBottom": "20px"}),

    html.Div([
        html.Label("Incoming Folder (.asc files):"),
        dcc.Input(id="incoming-folder", type="text", value="S:\\Shared\\Chris Dallarosa\\CE_SDS", style={"width": "100%"}),

        html.Label("Processed Folder (move after import):", style={"marginTop": "15px"}),
        dcc.Input(id="processed-folder", type="text", value="S:\\Shared\\Chris Dallarosa\\CE SDS Imported", style={"width": "100%"}),

        html.Div([
            html.Button("Start Import", id="start-import-btn", style={
                "marginTop": "20px", "marginBottom": "10px",
                "backgroundColor": "#007bff", "color": "white",
                "padding": "10px 30px", "border": "none",
                "borderRadius": "5px", "cursor": "pointer", "fontSize": "16px"
            }),
            html.Button("Cancel Import", id="cancel-import-btn", style={
                "marginTop": "20px", "marginBottom": "10px", "marginLeft": "10px",
                "backgroundColor": "#dc3545", "color": "white",
                "padding": "10px 30px", "border": "none",
                "borderRadius": "5px", "cursor": "pointer", "fontSize": "16px"
            })
        ], style={"textAlign": "center"})
    ], style={"width": "60%", "margin": "auto"}),

    html.Hr(),

    dcc.Interval(id="progress-interval", interval=500, n_intervals=0),

    html.Div(id="current-filename", style={"textAlign": "center", "fontSize": "18px", "marginBottom": "10px"}),
    dbc.Progress(id="progress-bar", value=0, label="0%", striped=True, animated=True, style={"height": "30px", "margin": "0 20%"}),

    html.Div(id="final-message", style={"textAlign": "center", "fontSize": "20px", "marginTop": "20px", "color": "green"}),
    html.Div(id="final-message-2", style={"textAlign": "center", "fontSize": "20px", "marginTop": "20px", "color": "green"})
])

# Start import thread when button is clicked
@app.callback(
    Output("final-message-2", "children"),
    Input("start-import-btn", "n_clicks"),
    State("incoming-folder", "value"),
    State("processed-folder", "value"),
    prevent_initial_call=True
)
def start_import(n_clicks, incoming_folder, processed_folder):
    print(f"🔘 Button clicked. Folder: {incoming_folder}, Processed: {processed_folder}")
    def import_worker():
        global import_status
        try:
            processed_files = set(os.listdir(processed_folder))
            asc_files = [
                f for f in os.listdir(incoming_folder)
                if f.lower().endswith(".asc")
                and "dat-pda - 220nm" not in f.lower()

            ]
            print(f'ASC Files:{asc_files}')

            import_status.update({
                "running": True,
                "finished": False,
                "total": len(asc_files),
                "current": 0,
                "filename": "",
                "error": ""
            })

            for idx, f in enumerate(asc_files):
                file_path = os.path.join(incoming_folder, f)
                import_status["filename"] = f
                try:
                    save_asc_to_db(file_path)
                    move_file_to_processed(file_path, processed_folder)
                except Exception as e:
                    import_status["error"] = f"❌ Failed to import {f}: {e}"
                    break
                import_status["current"] = idx + 1

        finally:
            import_status["running"] = False
            import_status["finished"] = True

        print(f"Incoming folder: {incoming_folder}")
        print(f"Processed folder: {processed_folder}")
        print(f"Incoming files: {os.listdir(incoming_folder)}")
        print(f"Processed files: {os.listdir(processed_folder)}")

    # Start thread
    threading.Thread(target=import_worker, daemon=True).start()
    return "🔄 Import started..."


# Cancel button logic (optional safety switch)
@app.callback(
    Output("cancel-import-btn", "disabled"),
    Input("cancel-import-btn", "n_clicks"),
    prevent_initial_call=True
)
def cancel_import(n):
    global import_status
    import_status["running"] = False
    import_status["error"] = "⛔ Import canceled by user."
    return True


# Update progress bar and messages using dcc.Interval
@app.callback(
    [Output("progress-bar", "value"),
     Output("progress-bar", "label"),
     Output("current-filename", "children"),
     Output("final-message", "children")],
    Input("progress-interval", "n_intervals")
)
def update_progress(n_intervals):
    global import_status

    if not import_status["running"] and not import_status["finished"]:
        return 0, "0%", "", ""

    total = max(import_status["total"], 1)
    current = import_status["current"]
    progress = int((current / total) * 100)
    label = f"{progress}%"
    filename = f"📄 Importing: {import_status['filename']}" if import_status["filename"] else ""

    if import_status["error"]:
        return progress, label, filename, import_status["error"]
    elif import_status["finished"]:
        return progress, label, "", f"✅ Imported {import_status['total']} files"
    else:
        return progress, label, filename, ""
