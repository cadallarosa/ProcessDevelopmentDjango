from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
import base64
import io

from plotly_integration.models import UFDFMetadata, SartoflowTimeSeriesData

# Initialize the Dash app
app = DjangoDash("UFDFAnalysis")

# Available options
molecule_options = [{"label": "SI-50E15", "value": "SI-50E15"}]
cassette_options = [
    {"label": "Sartocon 30kD 0.02 m^2", "value": "0.02"},
]
# Define improved styling
input_style = {
    "width": "100%",
    "padding": "12px",
    "marginBottom": "15px",
    "borderRadius": "8px",
    "border": "1px solid #ddd",
    "fontSize": "14px",
    "fontFamily": "system-ui, -apple-system, sans-serif",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
    "transition": "border-color 0.3s, box-shadow 0.3s"
}

readonly_input_style = input_style.copy()
readonly_input_style["backgroundColor"] = "#f8f9fa"
readonly_input_style["color"] = "#6c757d"
readonly_input_style["border"] = "1px solid #e9ecef"

label_style = {
    "fontWeight": "600",
    "fontSize": "14px",
    "color": "#495057",
    "marginBottom": "8px",
    "display": "block"
}

section_style = {
    "marginBottom": "30px",
    "padding": "25px",
    "backgroundColor": "#ffffff",
    "borderRadius": "12px",
    "border": "1px solid #e9ecef",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.05)"
}

header_style = {
    "color": "#0047b3",
    "marginBottom": "20px",
    "fontSize": "20px",
    "fontWeight": "600",
    "borderBottom": "2px solid #e9ecef",
    "paddingBottom": "10px"
}

# UFDF Layout with improved design
ufdf_layout = html.Div(
    style={
        "maxWidth": "900px",
        "margin": "0 auto",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "padding": "30px 20px"
    },
    children=[
        html.H1(
            "UFDF Experiment Creation", 
            style={
                "textAlign": "center",
                "color": "#0047b3",
                "marginBottom": "40px",
                "fontSize": "32px",
                "fontWeight": "700",
                "textShadow": "0 2px 4px rgba(0,0,0,0.1)"
            }
        ),
        
        # Progress indicator (could be enhanced later)
        html.Div(id="progress-indicator", style={"marginBottom": "30px"}),
        
        # Basic Information Section
        html.Div([
            html.H3("Basic Information", style=header_style),

            html.Label("Select Molecule:", style=label_style),
            dcc.Dropdown(
                id="molecule-select",
                options=molecule_options,
                placeholder="Choose a molecule",
                style=input_style
            ),
            
            html.Label("Experiment Name:", style=label_style),
            dcc.Input(
                id="experiment-name",
                type="text",
                placeholder="Enter a descriptive experiment name",
                style=input_style
            ),
            
            html.Label("Experimental Notes:", style=label_style),
            dcc.Textarea(
                id="experiment-notes",
                placeholder="Describe the experiment objectives, conditions, and any relevant details...",
                style={
                    **input_style,
                    "height": "120px",
                    "resize": "vertical",
                    "fontFamily": "system-ui, -apple-system, sans-serif"
                }
            ),
            
            html.Label("Select Cassette Type:", style=label_style),
            dcc.Dropdown(
                id="cassette-select",
                options=cassette_options,
                placeholder="Choose a cassette type",
                style=input_style
            ),
        ], style=section_style),
        
        # Load Information Section
        html.Div([
            html.H3("Load Information", style=header_style),

            html.Label("Load Concentration (mg/mL):", style=label_style),
            dcc.Input(
                id="load-concentration",
                type="number",
                placeholder="Enter initial concentration",
                style=input_style
            ),
            
            html.Label("Load Volume (mL):", style=label_style),
            dcc.Input(
                id="load-volume",
                type="number",
                placeholder="Enter initial volume",
                style=input_style
            ),
            
            html.Label("Load Mass (mg):", style=label_style),
            html.Div([
                dcc.Input(
                    id="load-mass",
                    type="number",
                    placeholder="Auto-calculated",
                    readOnly=True,
                    style=readonly_input_style
                ),
                html.Small("Automatically calculated: Concentration × Volume", 
                          style={"color": "#6c757d", "fontStyle": "italic"})
            ]),
        ], style=section_style),
        
        # Process Settings Section
        html.Div([
            html.H3("Process Settings", style=header_style),
            
            html.Label("Target Diafiltration Concentration:", style=label_style),
            dcc.Input(
                id="uf1-target-concentration",
                type="number",
                placeholder="Enter target concentration",
                style=input_style
            ),
            
            html.Label("UF1 Target Reservoir Mass (g):", style=label_style),
            html.Div([
                dcc.Input(
                    id="uf1-mass",
                    type="number",
                    placeholder="Auto-calculated",
                    readOnly=True,
                    style=readonly_input_style
                ),
                html.Small("Automatically calculated: Load Mass ÷ Target Concentration", 
                          style={"color": "#6c757d", "fontStyle": "italic"})
            ]),
            
            html.Label("Number of Diavolumes:", style=label_style),
            dcc.Input(
                id="diavolumes",
                type="number",
                placeholder="Enter number of diavolumes",
                style=input_style
            ),
            
            html.Label("Permeate Target Mass (g):", style=label_style),
            html.Div([
                dcc.Input(
                    id="permeate-mass",
                    type="number",
                    placeholder="Auto-calculated",
                    readOnly=True,
                    style=readonly_input_style
                ),
                html.Small("Automatically calculated: Diavolumes × UF1 Target Mass", 
                          style={"color": "#6c757d", "fontStyle": "italic"})
            ]),
        ], style=section_style),

        # Filtration Settings Section
        html.Div([
            html.H3("Filtration Settings", style=header_style),
            
            html.Label("LMH Target:", style=label_style),
            dcc.Input(
                id="lmh-target",
                type="number",
                placeholder="Enter target LMH",
                style=input_style
            ),
            
            html.Label("Target Flow Rate (mL/min):", style=label_style),
            html.Div([
                dcc.Input(
                    id="target-flow-rate",
                    type="number",
                    placeholder="Auto-calculated",
                    readOnly=True,
                    style=readonly_input_style
                ),
                html.Small("Automatically calculated based on LMH target and cassette area", 
                          style={"color": "#6c757d", "fontStyle": "italic"})
            ]),
            
            html.Label("Target P2500 Setpoint (%):", style=label_style),
            dcc.Input(
                id="p2500-setpoint",
                type="number",
                placeholder="Auto-calculated",
                readOnly=True,
                style=readonly_input_style
            ),
            
            html.Label("Target P3000 Setpoint:", style=label_style),
            dcc.Input(
                id="p3000-setpoint",
                type="number",
                placeholder="Auto-calculated",
                readOnly=True,
                style=readonly_input_style
            ),
        ], style=section_style),
        
        # Final Results Section
        html.Div([
            html.H3("Final Results", style=header_style),
            
            html.Label("Final Volume (mL):", style=label_style),
            dcc.Input(
                id="final-volume",
                type="number",
                placeholder="Enter final volume after process",
                style=input_style
            ),
            
            html.Label("Final Concentration (mg/mL):", style=label_style),
            dcc.Input(
                id="final-concentration",
                type="number",
                placeholder="Enter final concentration",
                style=input_style
            ),
            
            html.Label("Product Mass (mg):", style=label_style),
            html.Div([
                dcc.Input(
                    id="product-mass",
                    type="number",
                    placeholder="Auto-calculated",
                    readOnly=True,
                    style=readonly_input_style
                ),
                html.Small("Automatically calculated: Final Volume × Final Concentration", 
                          style={"color": "#6c757d", "fontStyle": "italic"})
            ]),
            
            html.Label("Yield (%):", style=label_style),
            html.Div([
                dcc.Input(
                    id="yield",
                    type="number",
                    placeholder="Auto-calculated",
                    readOnly=True,
                    style=readonly_input_style
                ),
                html.Small("Automatically calculated: (Product Mass ÷ Load Mass) × 100", 
                          style={"color": "#6c757d", "fontStyle": "italic"})
            ]),
        ], style=section_style),

        # File Upload Section
        html.Div([
            html.H3("Upload Process Step Data Files", style=header_style),
            
            html.Label("Number of Process Steps:", style=label_style),
            dcc.Dropdown(
                id="num-steps-dropdown",
                options=[
                    {"label": "1 Step", "value": 1},
                    {"label": "2 Steps", "value": 2},
                    {"label": "3 Steps", "value": 3},
                    {"label": "4 Steps", "value": 4},
                    {"label": "5 Steps", "value": 5}
                ],
                value=1,
                style=input_style
            ),
            
            html.Div(id="upload-steps-container", style={"marginTop": "20px"}),
            
            html.Div(
                id="upload-status",
                style={
                    "marginTop": "15px",
                    "padding": "10px",
                    "borderRadius": "8px",
                    "fontSize": "14px"
                }
            ),
        ], style=section_style),
        
        # Data Preview Section
        html.Div([
            html.H3("Data Preview", style=header_style),
            dash_table.DataTable(
                id="data-preview",
                columns=[],
                data=[],
                style_table={
                    "overflowX": "auto",
                    "marginTop": "10px",
                    "borderRadius": "8px",
                    "border": "1px solid #e9ecef"
                },
                style_cell={
                    "textAlign": "center",
                    "padding": "12px",
                    "fontSize": "14px",
                    "fontFamily": "system-ui, -apple-system, sans-serif"
                },
                style_header={
                    "fontWeight": "600",
                    "backgroundColor": "#f8f9fa",
                    "color": "#495057",
                    "border": "1px solid #dee2e6"
                },
                style_data={
                    "border": "1px solid #dee2e6"
                },
                page_size=10
            ),
        ], style=section_style),
        
        # Submit Section
        html.Div([
            html.Button(
                "Create Experiment",
                id="submit-report",
                n_clicks=0,
                style={
                    "backgroundColor": "#007bff",
                    "color": "white",
                    "border": "none",
                    "padding": "15px 30px",
                    "fontSize": "16px",
                    "fontWeight": "600",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "transition": "all 0.3s ease",
                    "width": "100%"
                }
            ),
            
            html.Div(
                id="final-status",
                style={
                    "marginTop": "20px",
                    "padding": "15px",
                    "borderRadius": "8px",
                    "fontSize": "14px",
                    "fontWeight": "500"
                }
            ),
        ], style={**section_style, "textAlign": "center"}),

    ]
)

# Define main app layout with improved styling
app.layout = html.Div(
    style={
        "fontFamily": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "backgroundColor": "#f8f9fa",
        "minHeight": "100vh",
        "margin": "0",
        "padding": "0"
    },
    children=[ufdf_layout],
)




# Callbacks

# Available step options
step_options = [
    {"label": "UF1", "value": "UF1"},
    {"label": "UF2", "value": "UF2"},
    {"label": "DF1", "value": "DF1"},
    {"label": "DF2", "value": "DF2"},
    {"label": "Rinse", "value": "Rinse"}
]

@app.callback(
    Output("upload-steps-container", "children"),
    Input("num-steps-dropdown", "value"),
    prevent_initial_call=False
)
def update_upload_steps(num_steps):
    if not num_steps:
        return []
    
    upload_components = []
    for i in range(num_steps):
        step_num = i + 1
        upload_components.extend([
            html.Div([
                html.Label(f"Step {step_num} Type:", style=label_style),
                dcc.Dropdown(
                    id=f"step-{step_num}-type",
                    options=step_options,
                    placeholder="Select step type",
                    style=input_style
                ),
                
                html.Label(f"Step {step_num} Data File:", style=label_style),
                dcc.Upload(
                    id=f"upload-step-{step_num}",
                    children=html.Div([
                        html.Button(
                            f"📁 Upload Step {step_num} Data",
                            id=f"button-step-{step_num}",
                            style={
                                "backgroundColor": "#007bff",
                                "color": "white",
                                "border": "none",
                                "padding": "12px 24px",
                                "borderRadius": "8px",
                                "cursor": "pointer",
                                "fontSize": "14px",
                                "fontWeight": "500",
                                "transition": "all 0.3s ease",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            }
                        ),
                        html.Div(id=f"upload-status-{step_num}", style={"marginTop": "8px", "fontSize": "13px"})
                    ]),
                    style={
                        "borderWidth": "2px",
                        "borderStyle": "dashed",
                        "borderRadius": "8px",
                        "borderColor": "#cccccc",
                        "textAlign": "center",
                        "padding": "20px",
                        "marginBottom": "15px",
                        "backgroundColor": "#fafafa",
                        "transition": "all 0.3s ease"
                    },
                    multiple=False
                ),
            ], style={"marginBottom": "25px", "padding": "20px", "backgroundColor": "#ffffff", "borderRadius": "8px", "border": "1px solid #e9ecef"})
        ])
    
    return upload_components

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
        # First, let's read and examine the structure
        lines = decoded.decode("utf-8-sig").split('\n')
        
        # Read the CSV starting from row 5 (index 4) where actual data begins
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8-sig")), delimiter=";", skiprows=4, header=None)
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Create correct headers based on the file structure analysis
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
        
        # Debug info
        print(f"DataFrame shape: {df.shape}")
        print(f"Expected headers: {len(correct_headers)}")
        print(f"First few rows:")
        print(df.head(3))
        
        # Ensure we have the right number of columns
        if len(df.columns) < len(correct_headers):
            # Pad with empty columns if needed
            for i in range(len(df.columns), len(correct_headers)):
                df[i] = None
        elif len(df.columns) > len(correct_headers):
            # Trim extra columns
            df = df.iloc[:, :len(correct_headers)]
        
        # Assign correct headers
        df.columns = correct_headers[:len(df.columns)]

        # Convert PDatTime to datetime format
        df["PDatTime"] = pd.to_datetime(df["PDatTime"], errors="coerce")
        
        # Convert ProcessTime to float
        df["ProcessTime"] = pd.to_numeric(df["ProcessTime"], errors="coerce")

        # Clean BatchId - remove NaN and ensure it's string
        df = df.dropna(subset=["BatchId"])
        df["BatchId"] = df["BatchId"].astype(str).str.strip()
        
        # Remove rows where BatchId is empty or whitespace
        df = df[df["BatchId"].str.len() > 0]

        # Replace NaN values with None for database insertion
        df = df.where(pd.notnull(df), None)

        print(f"Final DataFrame shape after cleaning: {df.shape}")
        return df
        
    except Exception as e:
        print(f"Error in parse_csv: {e}")
        return str(e)  # Return error message as string


# Dynamic callback for button styles based on number of steps
def create_upload_feedback_callbacks(max_steps=5):
    # Create callback for button styles and upload status
    button_outputs = []
    status_outputs = []
    inputs = []
    
    for i in range(1, max_steps + 1):
        button_outputs.append(Output(f"button-step-{i}", "style"))
        status_outputs.append(Output(f"upload-status-{i}", "children"))
        inputs.append(Input(f"upload-step-{i}", "contents"))
    
    @app.callback(
        button_outputs + status_outputs + [Output("data-preview", "data"), Output("data-preview", "columns")],
        inputs,
        prevent_initial_call=True
    )
    def update_upload_feedback(*args):
        print("\n" + "="*50)
        print("🔍 DEBUG: update_upload_feedback callback triggered!")
        print(f"Number of inputs: {len(args)}")
        print(f"Input args: {[type(arg).__name__ if arg else 'None' for arg in args]}")
        
        uploaded_style = {
            "backgroundColor": "#28a745",
            "color": "white",
            "border": "none",
            "padding": "12px 24px",
            "borderRadius": "8px",
            "cursor": "pointer",
            "fontSize": "14px",
            "fontWeight": "500",
            "transition": "all 0.3s ease",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
        }
        
        default_style = {
            "backgroundColor": "#007bff",
            "color": "white",
            "border": "none",
            "padding": "12px 24px",
            "borderRadius": "8px",
            "cursor": "pointer",
            "fontSize": "14px",
            "fontWeight": "500",
            "transition": "all 0.3s ease",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
        }
        
        # Prepare return values
        button_styles = []
        status_messages = []
        preview_data = []
        preview_columns = []
        
        for i, content in enumerate(args):
            print(f"\n📁 Processing upload {i+1}:")
            print(f"Content exists: {content is not None}")
            
            if content:
                print(f"Content type: {type(content)}")
                print(f"Content length: {len(content) if content else 0}")
                print(f"Content preview: {content[:100] if content else 'None'}...")
                
                button_styles.append(uploaded_style)
                print("✅ Button style set to green (uploaded)")
                
                # Try to parse and preview the uploaded file
                try:
                    print("🔄 Attempting to parse CSV...")
                    df = parse_csv(content)
                    print(f"Parse result type: {type(df)}")
                    
                    if isinstance(df, pd.DataFrame):
                        print(f"✅ DataFrame created successfully!")
                        print(f"DataFrame shape: {df.shape}")
                        print(f"DataFrame empty: {df.empty}")
                        print(f"DataFrame columns: {list(df.columns)}")
                        
                        if not df.empty:
                            status_messages.append(html.Div([
                                html.Span("✓ File uploaded successfully", style={"color": "#28a745", "fontWeight": "500"}),
                                html.Br(),
                                html.Small(f"Parsed {len(df)} rows with {len(df.columns)} columns", 
                                         style={"color": "#6c757d", "fontStyle": "italic"})
                            ]))
                            
                            # Use the latest uploaded file for preview
                            preview_data = df.head(10).to_dict('records')
                            preview_columns = [{"name": col, "id": col} for col in df.columns]
                            print(f"📊 Preview data created: {len(preview_data)} rows, {len(preview_columns)} columns")
                            print(f"First row preview: {preview_data[0] if preview_data else 'No data'}")
                        else:
                            print("⚠️ DataFrame is empty")
                            status_messages.append(html.Div([
                                html.Span("⚠️ File uploaded but no data found", style={"color": "#ffc107", "fontWeight": "500"})
                            ]))
                    else:
                        print(f"❌ Parsing failed. Result: {df}")
                        status_messages.append(html.Div([
                            html.Span(f"⚠️ Parsing failed: {df}", style={"color": "#ffc107", "fontWeight": "500"})
                        ]))
                except Exception as e:
                    print(f"💥 Exception during parsing: {e}")
                    import traceback
                    traceback.print_exc()
                    status_messages.append(html.Div([
                        html.Span(f"❌ Error parsing file: {str(e)[:50]}...", style={"color": "#dc3545", "fontWeight": "500"})
                    ]))
            else:
                print("❌ No content - setting default style")
                button_styles.append(default_style)
                status_messages.append("")
        
        print(f"\n📤 Returning:")
        print(f"Button styles: {len(button_styles)}")
        print(f"Status messages: {len(status_messages)}")
        print(f"Preview data rows: {len(preview_data)}")
        print(f"Preview columns: {len(preview_columns)}")
        print("="*50 + "\n")
        
        return button_styles + status_messages + [preview_data, preview_columns]

# Create the callback
create_upload_feedback_callbacks()

# Add a simple test callback to verify components exist
@app.callback(
    Output("upload-status", "children"),
    Input("num-steps-dropdown", "value")
)
def debug_upload_status(num_steps):
    print(f"🔧 DEBUG: Number of steps selected: {num_steps}")
    return html.Div([
        html.Small(f"Debug: {num_steps} step(s) configured", style={"color": "#6c757d", "fontStyle": "italic"})
    ])


# Step type to unit_step mapping  
step_type_mapping = {
    "UF1": 1,
    "UF2": 2, 
    "DF1": 3,
    "DF2": 4,
    "Rinse": 5
}

@app.callback(
    [Output("final-status", "children"), Output("submit-report", "style")],
    Input("submit-report", "n_clicks"),
    [
        State("num-steps-dropdown", "value"),
        State("upload-step-1", "contents"), State("step-1-type", "value"),
        State("upload-step-2", "contents"), State("step-2-type", "value"),
        State("upload-step-3", "contents"), State("step-3-type", "value"),
        State("upload-step-4", "contents"), State("step-4-type", "value"),
        State("upload-step-5", "contents"), State("step-5-type", "value"),
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
    ],
    prevent_initial_call=True
)
def handle_import(n_clicks, num_steps, 
                  step1_content, step1_type, step2_content, step2_type, 
                  step3_content, step3_type, step4_content, step4_type,
                  step5_content, step5_type, molecule_name, experiment_name, 
                  experiment_notes, cassette_type, load_concentration, load_volume, 
                  load_mass, uf1_target_concentration, uf1_target_mass, diavolumes, 
                  target_permeate_mass, target_lmh, target_flowrate, p2500_setpoint,
                  p3000_setpoint, final_volume, final_concentration, product_mass, recovery):
    
    # Collect step data
    step_data = [
        (step1_content, step1_type),
        (step2_content, step2_type), 
        (step3_content, step3_type),
        (step4_content, step4_type),
        (step5_content, step5_type)
    ]
    
    # Filter only uploaded steps
    uploaded_steps = [(content, step_type) for content, step_type in step_data[:num_steps] 
                      if content is not None and step_type is not None]
    
    default_button_style = {
        "backgroundColor": "#007bff",
        "color": "white",
        "border": "none",
        "padding": "15px 30px",
        "fontSize": "16px",
        "fontWeight": "600",
        "borderRadius": "8px",
        "cursor": "pointer",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "transition": "all 0.3s ease",
        "width": "100%"
    }
    
    if not uploaded_steps:
        return html.Div(
            "⚠️ No files uploaded. Please upload at least one step file before creating the experiment.",
            style={"color": "#dc3545", "fontWeight": "500", "textAlign": "center"}
        ), default_button_style

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

    records_created = 0

    # Step 2: Process each uploaded file
    for content, step_type in uploaded_steps:
        if content:
            df = parse_csv(content)

            if isinstance(df, str):  # If parsing failed, return error
                return html.Div(
                    f"❌ Error parsing {step_type} file: {df}",
                    style={"color": "#dc3545", "fontWeight": "500", "textAlign": "center"}
                ), default_button_style

            unit_step = step_type_mapping.get(step_type, 1)

            # Step 3: Insert time-series data with unit_step
            time_series_records = []
            for _, row in df.iterrows():
                time_series_records.append(SartoflowTimeSeriesData(
                    result_id=ufdf_metadata,
                    unit_step=unit_step,
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
                    wirc2100_output=row.get('WIRC2100_Output'),
                    wirc2100_setpoint=row.get('WIRC2100_Setpoint'),
                    wirc2100_mode=row.get('WIRC2100_Mode'),
                ))

            SartoflowTimeSeriesData.objects.bulk_create(time_series_records)
            records_created += len(time_series_records)

    success_button_style = {
        "backgroundColor": "#28a745",
        "color": "white",
        "border": "none",
        "padding": "15px 30px",
        "fontSize": "16px",
        "fontWeight": "600",
        "borderRadius": "8px",
        "cursor": "pointer",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "transition": "all 0.3s ease",
        "width": "100%"
    }
    
    success_message = html.Div([
        html.H4("🎉 Experiment Created Successfully!", 
               style={"color": "#28a745", "marginBottom": "15px", "textAlign": "center"}),
        html.Div([
            html.Strong("Experiment: "), ufdf_metadata.experiment_name
        ], style={"marginBottom": "10px"}),
        html.Div([
            html.Strong("Result ID: "), str(ufdf_metadata.result_id)
        ], style={"marginBottom": "10px"}),
        html.Div([
            html.Strong("Records Created: "), f"{records_created:,}"
        ], style={"marginBottom": "10px"}),
        html.Div([
            html.Strong("Steps Processed: "), str(len(uploaded_steps))
        ], style={"marginBottom": "15px"}),
        html.Hr(style={"border": "1px solid #28a745", "margin": "15px 0"}),
        html.P("Your experiment data has been successfully uploaded and is ready for analysis!", 
               style={"fontStyle": "italic", "textAlign": "center", "marginBottom": "0"})
    ], style={
        "backgroundColor": "#d4edda",
        "border": "1px solid #c3e6cb",
        "color": "#155724",
        "padding": "20px",
        "borderRadius": "8px",
        "textAlign": "left"
    })
    
    return success_message, success_button_style
