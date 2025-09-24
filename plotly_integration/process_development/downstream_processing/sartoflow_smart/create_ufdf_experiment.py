from dash import dcc, html, Input, Output, State, dash_table, ALL, callback_context
import dash
from django_plotly_dash import DjangoDash
import pandas as pd
import base64
import io
import json

from plotly_integration.models import UFDFMetadata, SartoflowTimeSeriesData

# Initialize the Dash app
app = DjangoDash("UFDFAnalysis")

# Available options
molecule_options = [{"label": "SI-50E15", "value": "SI-50E15"}]
cassette_options = [
    {"label": "Sartocon 30kD 0.02 m^2", "value": "0.02"},
]

# Process step options
process_steps = [
    {"label": "UF1 - Ultrafiltration 1", "value": 1},
    {"label": "DF1 - Diafiltration 1", "value": 2},
    {"label": "UF2 - Ultrafiltration 2", "value": 3},
    {"label": "DF2 - Diafiltration 2", "value": 4},
    {"label": "Rinse", "value": 5},
]
# Define common input box styles
input_style = {
    "width": "100%",  # Ensure all inputs have full width
    "padding": "10px",  # Consistent padding inside input boxes
    "marginBottom": "15px",  # Same spacing between inputs
    "borderRadius": "5px",  # Slight rounded corners for aesthetics
    "border": "1px solid #ccc"  # Subtle border for all inputs
}

# Define read-only input style (calculated values)
readonly_input_style = input_style.copy()
readonly_input_style["backgroundColor"] = "#e9f1fb"  # Light blue background for calculated fields
readonly_input_style["border"] = "1px solid #bbb"  # Slightly darker border for contrast

# Define layout
app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "padding": "20px", "maxWidth": "900px", "margin": "0 auto"},
    children=[
        html.H2("UFDF Experiment Analysis", style={"textAlign": "center", "color": "#0047b3", "marginBottom": "20px"}),

        # Molecule selection
        html.Label("Select Molecule:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Dropdown(id="molecule-select", options=molecule_options, placeholder="Choose a molecule",
                     style=input_style),

        # Experiment Name
        html.Label("Experiment Name:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Input(id="experiment-name", type="text", placeholder="Enter experiment name",
                  style=input_style),

        # Experimental Notes
        html.Label("Experimental Notes:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Textarea(id="experiment-notes", placeholder="Enter experimental details...",
                     style={"width": "100%", "height": "100px", "padding": "10px", "marginBottom": "20px"}),

        # Cassette selection
        html.Label("Select Cassette Type:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Dropdown(id="cassette-select", options=cassette_options, placeholder="Choose a cassette",
                     style=input_style),

        # Load inputs
        html.Label("Load Concentration (mg/mL):", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Input(id="load-concentration", type="number", placeholder="Enter load concentration",
                  style=input_style),

        html.Label("Load Volume (mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="load-volume", type="number", placeholder="Enter load volume",
                  style=input_style),

        html.Label("Load Mass (mg):", style={"fontWeight": "bold"}),
        dcc.Input(id="load-mass", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("UF1 Target Concentration:", style={"fontWeight": "bold"}),
        dcc.Input(id="uf1-target-concentration", type="number", placeholder="Enter load volume",
                  style=input_style),

        # Process Inputs
        html.Label("UF1 Target Reservoir Mass (g):"),
        dcc.Input(id="uf1-mass", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("#Diavolumes:", style={"fontWeight": "bold"}),
        dcc.Input(id="diavolumes", type="number", placeholder="Enter number of diavolumes",
                  style=input_style),

        html.Label("Permeate Target Mass (g):", style={"fontWeight": "bold"}),
        dcc.Input(id="permeate-mass", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        #
        html.H3("Filtration Settings", style={"marginTop": "20px", "color": "#0047b3"}),

        html.Label("LMH Target:", style={"fontWeight": "bold"}),
        dcc.Input(id="lmh-target", type="number", placeholder="Enter LMH target",
                  style=input_style),

        html.Label("Target Flow Rate (mL/min):", style={"fontWeight": "bold"}),
        dcc.Input(id="target-flow-rate", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("Target P2500 Setpoint (%):", style={"fontWeight": "bold"}),
        dcc.Input(id="p2500-setpoint", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("Target P3000 Setpoint:", style={"fontWeight": "bold"}),
        dcc.Input(id="p3000-setpoint", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.H3("Final Results", style={"marginTop": "20px", "color": "#0047b3"}),

        html.Label("Final Volume (mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="final-volume", type="number", placeholder="Enter final volume",
                  style=input_style),

        html.Label("Final Concentration (mg/mL):", style={"fontWeight": "bold"}),
        dcc.Input(id="final-concentration", type="number", placeholder="Enter final concentration",
                  style=input_style),

        html.Label("Product Mass (mg):", style={"fontWeight": "bold"}),
        dcc.Input(id="product-mass", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.Label("Yield (%):", style={"fontWeight": "bold"}),
        dcc.Input(id="yield", type="number", placeholder="Calculated value", readOnly=True,
                  style=readonly_input_style),

        html.H3("Upload Data Files", style={"marginTop": "20px", "color": "#0047b3"}),
        
        html.Div([
            html.P("Upload CSV files for each process step. You can upload multiple files at once or individually.", 
                   style={"color": "#666", "marginBottom": "20px"}),
            
            # Container for file uploads
            html.Div(id="file-upload-container", children=[
                # Initial file upload section
                html.Div([
                    html.Div([
                        html.Label("Select Process Step:", style={"fontWeight": "bold", "marginRight": "10px"}),
                        dcc.Dropdown(
                            id={"type": "step-select", "index": 0},
                            options=process_steps,
                            placeholder="Choose process step",
                            style={"width": "250px", "display": "inline-block", "marginRight": "20px"}
                        ),
                        dcc.Upload(
                            id={"type": "upload-data", "index": 0},
                            children=html.Button("Choose File", 
                                               style={"backgroundColor": "#0047b3", "color": "white", 
                                                     "border": "none", "padding": "8px 16px", 
                                                     "cursor": "pointer", "borderRadius": "4px"}),
                            multiple=False,
                            style={"display": "inline-block", "marginRight": "10px"}
                        ),
                        html.Span(id={"type": "filename-display", "index": 0}, 
                                 style={"marginLeft": "10px", "color": "#666"}),
                    ], style={"marginBottom": "15px", "padding": "10px", "border": "1px solid #ddd", 
                             "borderRadius": "5px", "backgroundColor": "#f9f9f9"}),
                ], id={"type": "upload-section", "index": 0}),
            ]),
            
            html.Button("Add Another File", id="add-file-button", n_clicks=0,
                       style={"backgroundColor": "#6c757d", "color": "white", "border": "none",
                             "padding": "8px 16px", "cursor": "pointer", "marginTop": "10px",
                             "borderRadius": "4px"}),
            
            html.Div(id="upload-status", style={"marginTop": "20px"}),
            
            # Store for uploaded files data
            dcc.Store(id="uploaded-files-store", data={}),
            dcc.Store(id="removed-indices", data=[]),
        ]),
        
        # Data Table Preview
        html.Div(id="preview-container", children=[], style={"marginTop": "20px"}),
        html.Button("Import and Submit Report", id="submit-report", n_clicks=0,
                    style={"backgroundColor": "#28a745", "color": "white", "padding": "10px 20px",
                           "marginTop": "20px", "fontSize": "16px", "borderRadius": "4px",
                           "border": "none", "cursor": "pointer"}),

        html.Div(id="final-status", style={"marginTop": "10px", "color": "blue"}),
    ]
)


# Callback to add more file upload sections
@app.callback(
    Output("file-upload-container", "children"),
    [Input("add-file-button", "n_clicks"),
     Input({"type": "remove-button", "index": ALL}, "n_clicks")],
    State("file-upload-container", "children"),
    State("removed-indices", "data"),
    prevent_initial_call=True
)
def manage_file_uploads(add_clicks, remove_clicks, current_children, removed_indices):
    ctx = callback_context
    if not ctx.triggered:
        return current_children
    
    trigger_id = ctx.triggered[0]["prop_id"]
    
    # Handle adding a new upload section
    if "add-file-button" in trigger_id:
        if add_clicks and add_clicks > 0:
            # Find next available index
            existing_indices = []
            for child in current_children:
                if isinstance(child, dict) and "props" in child:
                    child_id = child["props"].get("id", {})
                    if isinstance(child_id, dict) and child_id.get("type") == "upload-section":
                        existing_indices.append(child_id.get("index", 0))
            
            new_index = max(existing_indices, default=-1) + 1
            
            new_upload = html.Div([
                html.Div([
                    html.Label("Select Process Step:", style={"fontWeight": "bold", "marginRight": "10px"}),
                    dcc.Dropdown(
                        id={"type": "step-select", "index": new_index},
                        options=process_steps,
                        placeholder="Choose process step",
                        style={"width": "250px", "display": "inline-block", "marginRight": "20px"}
                    ),
                    dcc.Upload(
                        id={"type": "upload-data", "index": new_index},
                        children=html.Button("Choose File", 
                                           style={"backgroundColor": "#0047b3", "color": "white", 
                                                 "border": "none", "padding": "8px 16px", 
                                                 "cursor": "pointer", "borderRadius": "4px"}),
                        multiple=False,
                        style={"display": "inline-block", "marginRight": "10px"}
                    ),
                    html.Span(id={"type": "filename-display", "index": new_index}, 
                             style={"marginLeft": "10px", "color": "#666"}),
                    html.Button("Remove", 
                               id={"type": "remove-button", "index": new_index},
                               style={"backgroundColor": "#dc3545", "color": "white", "border": "none",
                                     "padding": "6px 12px", "cursor": "pointer", "marginLeft": "10px",
                                     "borderRadius": "4px"}),
                ], style={"marginBottom": "15px", "padding": "10px", "border": "1px solid #ddd", 
                         "borderRadius": "5px", "backgroundColor": "#f9f9f9"}),
            ], id={"type": "upload-section", "index": new_index})
            
            current_children.insert(-2, new_upload)  # Insert before the stores
    
    # Handle removing an upload section
    elif "remove-button" in trigger_id:
        import json
        button_id = json.loads(trigger_id.split(".")[0])
        index_to_remove = button_id["index"]
        
        # Remove the section with matching index
        current_children = [
            child for child in current_children
            if not (isinstance(child, dict) and 
                   "props" in child and 
                   child["props"].get("id", {}).get("index") == index_to_remove)
        ]
    
    return current_children


# Callbacks

@app.callback(
    Output("load-mass", "value"),
    Input("load-concentration", "value"),
    Input("load-volume", "value"),
)
def calculate_load_mass(load_concentration, load_volume):
    try:
        load_concentration = load_concentration or 0
        load_volume = load_volume or 0

        load_mass = load_concentration * load_volume
        load_mass = round(load_mass,2)
        return load_mass
    except Exception as e:
        print(f"Error calculating Load Mass: {e}")
        return ""


@app.callback(
    Output("uf1-mass", "value"),
    Input("load-mass", "value"),
    Input("uf1-target-concentration", "value"),
)
def calculate_target_reservoir_mass(load_mass, target_concentration):
    try:
        load_mass = load_mass or 0
        target_concentration = target_concentration or 1
        target_reservoir_mass = load_mass / target_concentration
        target_reservoir_mass = round(target_reservoir_mass,2)
        return target_reservoir_mass
    except Exception as e:
        print(f"Error calculating Target Reservoir Mass: {e}")
        return ""


@app.callback(
    Output("permeate-mass", "value"),
    Input("diavolumes", "value"),
    Input("uf1-mass", "value"),
    prevent_initial_call=True
)
def calculate_target_permeate_mass(diavolumes, target_reservoir_mass):
    try:
        diavolumes = diavolumes or 0
        target_reservoir_mass = target_reservoir_mass or 0
        target_permeate_mass = diavolumes * target_reservoir_mass
        return target_permeate_mass
    except Exception as e:
        print(f"Error calculating Target Permeate Mass: {e}")
        return ""


@app.callback(
    Output("target-flow-rate", "value"),
    Output("p2500-setpoint", "value"),
    Output("p3000-setpoint", "value"),
    Input("lmh-target", "value"),
    Input("cassette-select", "value"),
    prevent_initial_call=True
)
def calculate_flow_rate(lmh_target, cassette):
    try:
        filter_area = float(cassette) or 0
        print(filter_area)
        lmh_target = lmh_target or 0

        flow_rate = (lmh_target * filter_area) * 1000 / 60
        flow_rate = round(flow_rate, 2
                          )
        target_p2500_setpoint = (flow_rate / 1667) * 100
        target_p2500_setpoint = round(target_p2500_setpoint, 2
                                      )
        target_p3000_setpoint = (target_p2500_setpoint / 200) * 100
        target_p3000_setpoint = round(target_p3000_setpoint, 2)

        print(f'flowrate{flow_rate},target p 2500{target_p2500_setpoint},target p 3000{target_p3000_setpoint}')
        return flow_rate, target_p2500_setpoint, target_p3000_setpoint
    except Exception as e:
        print(f"Error calculating Target Permeate Mass: {e}")
        return ""


@app.callback(
    Output("product-mass", "value"),
    Output("yield", "value"),
    Input("final-volume", "value"),
    Input("final-concentration", "value"),
    Input("load-mass", "value"),

    prevent_initial_call=True
)
def calculate_flow_rate(final_volume, final_concentration, load_mass):
    try:
        final_volume = final_volume or 0
        final_concentration = final_concentration or 0
        load_mass = load_mass or 1

        product_mass = final_volume * final_concentration
        product_mass = round(product_mass, 2)

        recovery = product_mass / load_mass * 100
        recovery = round(recovery,2)

        return product_mass, recovery
    except Exception as e:
        print(f"Error calculating Target Permeate Mass: {e}")
        return ""


# Define a function to parse CSV file
def parse_csv(contents):
    """
    Parses uploaded CSV file, assigns correct headers, and returns a DataFrame.
    """
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    try:
        # Read CSV, skipping first 4 rows (since data starts on row 5)
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8-sig")), delimiter=";", skiprows=4, header=None)

        # Define correct headers (36 headers for 36 columns)
        correct_headers = [
            "BatchId", "PDatTime", "ProcessTime",
            "AG2100_Value", "AG2100_Setpoint", "AG2100_Mode", "AG2100_Output",
            "DPRESS_Value", "DPRESS_Output", "DPRESS_Mode", "DPRESS_Setpoint",
            "F_PERM_Value",
            "P2500_Setpoint", "P2500_Value", "P2500_Output", "P2500_Mode",
            "P3000_Setpoint", "P3000_Mode", "P3000_Output", "P3000_Value", "P3000_T",
            "PIR2600", "PIR2700",
            "PIRC2500_Output", "PIRC2500_Value", "PIRC2500_Setpoint", "PIRC2500_Mode",
            "QIR2000", "QIR2100",
            "TIR2100", "TMP",
            "WIR2700",
            "WIRC2100_Value", "WIRC2100_Output", "WIRC2100_Setpoint", "WIRC2100_Mode"
        ]

        # Ensure correct number of columns before assigning headers
        if len(df.columns) != len(correct_headers):
            raise ValueError(f"Column mismatch! Expected {len(correct_headers)} columns, but found {len(df.columns)}.")

        # Assign correct headers
        df.columns = correct_headers

        # Convert PDatTime to datetime format
        df["PDatTime"] = pd.to_datetime(df["PDatTime"], errors="coerce")

        # Drop rows where `BatchId` is NaN
        df = df.dropna(subset=["BatchId"])

        # Ensure `BatchId` is always a string and non-null
        df["BatchId"] = df["BatchId"].astype(str).str.strip()

        # Remove completely empty rows
        df = df.dropna(how="all")

        # Replace NaN values with None for database insertion
        df = df.where(pd.notnull(df), None)

        return df
    except Exception as e:
        return str(e)  # Return error message as string


# Callback to handle file uploads and store data
@app.callback(
    [Output("uploaded-files-store", "data"),
     Output({"type": "filename-display", "index": ALL}, "children"),
     Output("upload-status", "children"),
     Output("preview-container", "children")],
    [Input({"type": "upload-data", "index": ALL}, "contents")],
    [State({"type": "upload-data", "index": ALL}, "filename"),
     State({"type": "step-select", "index": ALL}, "value"),
     State("uploaded-files-store", "data")],
    prevent_initial_call=True
)
def handle_file_uploads(contents_list, filenames_list, steps_list, stored_data):
    if not contents_list or all(c is None for c in contents_list):
        return stored_data, [""] * len(contents_list), "", []
    
    # Initialize stored_data if empty
    if not stored_data:
        stored_data = {}
    
    status_messages = []
    preview_sections = []
    filename_displays = []
    
    for idx, (content, filename, step) in enumerate(zip(contents_list, filenames_list, steps_list)):
        if content and step:
            # Parse the file
            df = parse_csv(content)
            
            if isinstance(df, str):  # Error occurred
                status_messages.append(f"Error parsing {filename}: {df}")
                filename_displays.append(f"❌ {filename}" if filename else "")
            else:
                # Store the parsed data
                step_name = next((s["label"] for s in process_steps if s["value"] == step), f"Step {step}")
                stored_data[str(step)] = {
                    "filename": filename,
                    "step_name": step_name,
                    "data": df.to_dict("records"),
                    "content": content
                }
                status_messages.append(f"✅ {filename} uploaded for {step_name}")
                filename_displays.append(f"✅ {filename}" if filename else "")
                
                # Create preview section for this file
                preview_sections.append(
                    html.Div([
                        html.H4(f"{step_name} - {filename}", style={"color": "#0047b3", "marginTop": "15px"}),
                        dash_table.DataTable(
                            columns=[{"name": col, "id": col} for col in df.columns[:10]],  # Show first 10 columns
                            data=df.head(5).to_dict("records"),  # Show first 5 rows
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "center", "padding": "5px", "fontSize": "12px"},
                            style_header={"fontWeight": "bold", "backgroundColor": "#e9f1fb"},
                        )
                    ])
                )
        else:
            filename_displays.append(filename if filename else "")
    
    # Create status summary
    if status_messages:
        status_div = html.Div([
            html.H4("Upload Status:", style={"color": "#0047b3"}),
            html.Ul([html.Li(msg) for msg in status_messages])
        ])
    else:
        status_div = ""
    
    # Add preview header if there are previews
    if preview_sections:
        preview_container = [
            html.H3("Data Preview", style={"color": "#0047b3", "marginTop": "20px"}),
            *preview_sections
        ]
    else:
        preview_container = []
    
    return stored_data, filename_displays, status_div, preview_container


@app.callback(
    Output("final-status", "children"),
    Input("submit-report", "n_clicks"),
    State("uploaded-files-store", "data"),
    State("molecule-select", "value"),
    State("experiment-name", "value"),
    State("experiment-notes", "value"),
    State("cassette-select", "value"),
    State("load-concentration", "value"),
    State("load-volume", "value"),
    State("load-mass", "value"),
    State("uf1-target-concentration", "value"),
    State("uf1-mass", "value"),
    State("diavolumes", "value"),
    State("permeate-mass", "value"),
    State("lmh-target", "value"),
    State("target-flow-rate", "value"),
    State("p2500-setpoint", "value"),
    State("p3000-setpoint", "value"),
    State("final-volume", "value"),
    State("final-concentration", "value"),
    State("product-mass", "value"),
    State("yield", "value"),
    prevent_initial_call=True
)
def handle_import(n_clicks, uploaded_files, molecule_name, experiment_name, experiment_notes,
                  cassette_type, load_concentration, load_volume, load_mass, uf1_target_concentration,
                  uf1_target_mass, diavolumes, target_permeate_mass, target_lmh, target_flowrate, p2500_setpoint,
                  p3000_setpoint, final_volume, final_concentration, product_mass, recovery):
    
    if not uploaded_files:
        return "No files uploaded. Please upload at least one data file."
    
    if not experiment_name:
        return "Please enter an experiment name."
    
    try:
        # Step 1: Create UFDFMetadata entry
        ufdf_metadata = UFDFMetadata.objects.create(
            molecule_name=molecule_name,
            experiment_name=experiment_name,
            experimental_notes=experiment_notes,
            cassette_type=cassette_type,
            load_concentration=load_concentration,
            load_volume=load_volume,
            load_mass=load_mass,
            target_diafiltration_concentration=uf1_target_concentration,
            uf1_target_reservoir_mass=uf1_target_mass,
            diavolumes=diavolumes,
            permeate_target_mass=target_permeate_mass,
            diafiltration_volume_required=target_permeate_mass * 1.25 if target_permeate_mass else None,
            lmh_target=target_lmh,
            target_flow_rate=target_flowrate,
            target_p2500_setpoint=p2500_setpoint,
            target_p3000_setpoint=p3000_setpoint,
            final_volume=final_volume,
            final_concentration=final_concentration,
            product_mass=product_mass,
            yield_percentage=recovery
        )
        
        # Step 2: Process each uploaded file
        total_records = 0
        import_summary = []
        
        for step_key, file_info in uploaded_files.items():
            step_value = int(step_key)
            step_name = file_info['step_name']
            filename = file_info['filename']
            
            # Parse the CSV content again
            df = parse_csv(file_info['content'])
            
            if isinstance(df, str):  # Error occurred
                import_summary.append(f"❌ Error processing {filename}: {df}")
                continue
            
            # Create time series records for this step
            time_series_records = []
            for _, row in df.iterrows():
                time_series_records.append(SartoflowTimeSeriesData(
                    result_id=ufdf_metadata,
                    unit_step=step_value,  # Set the unit_step based on selected process step
                    batch_id=row.get('BatchId'),
                    pdat_time=pd.to_datetime(row.get('PDatTime'), errors='coerce'),
                    process_time=row.get('ProcessTime', 0),
                    ag2100_value=row.get('AG2100_Value'),
                    ag2100_setpoint=row.get('AG2100_Setpoint'),
                    ag2100_mode=row.get('AG2100_Mode'),
                    ag2100_output=row.get('AG2100_Output'),
                    dpress_value=row.get('DPRESS_Value'),
                    dpress_output=row.get('DPRESS_Output'),
                    dpress_mode=row.get('DPRESS_Mode'),
                    dpress_setpoint=row.get('DPRESS_Setpoint'),
                    f_perm_value=row.get('F_PERM_Value'),
                    p2500_setpoint=row.get('P2500_Setpoint'),
                    p2500_value=row.get('P2500_Value'),
                    p2500_output=row.get('P2500_Output'),
                    p2500_mode=row.get('P2500_Mode'),
                    p3000_setpoint=row.get('P3000_Setpoint'),
                    p3000_mode=row.get('P3000_Mode'),
                    p3000_output=row.get('P3000_Output'),
                    p3000_value=row.get('P3000_Value'),
                    p3000_t=row.get('P3000_T'),
                    pir2600=row.get('PIR2600'),
                    pir2700=row.get('PIR2700'),
                    pirc2500_value=row.get('PIRC2500_Value'),
                    pirc2500_output=row.get('PIRC2500_Output'),
                    pirc2500_setpoint=row.get('PIRC2500_Setpoint'),
                    pirc2500_mode=row.get('PIRC2500_Mode'),
                    qir2000=row.get('QIR2000'),
                    qir2100=row.get('QIR2100'),
                    tir2100=row.get('TIR2100'),
                    tmp=row.get('TMP'),
                    wir2700=row.get('WIR2700'),
                    wirc2100_value=row.get('WIRC2100_Value'),
                    wirc2100_output=row.get('WIRC2100_Output'),
                    wirc2100_setpoint=row.get('WIRC2100_Setpoint'),
                    wirc2100_mode=row.get('WIRC2100_Mode'),
                ))
            
            # Bulk create records for this step
            SartoflowTimeSeriesData.objects.bulk_create(time_series_records)
            records_count = len(time_series_records)
            total_records += records_count
            import_summary.append(f"✅ {step_name}: {records_count} records from {filename}")
        
        # Create success message
        success_message = html.Div([
            html.H4(f"✅ Successfully created experiment (ID: {ufdf_metadata.result_id})", 
                   style={"color": "green"}),
            html.P(f"Total records imported: {total_records}"),
            html.Ul([html.Li(msg) for msg in import_summary])
        ])
        
        return success_message
        
    except Exception as e:
        return html.Div([
            html.H4("❌ Import failed", style={"color": "red"}),
            html.P(f"Error: {str(e)}")
        ])
