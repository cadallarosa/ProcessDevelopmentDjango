from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
import base64
import io

from plotly_integration.models import VFMetadata, VFTimeSeriesData

# Initialize the Dash app
app = DjangoDash("ViralFiltrationExperimentImport")

# Available options
molecule_options = [{"label": "SI-50E15", "value": "SI-50E15"}]
filter_options = [
    {"label": "Viresolve Pro 40", "value": "0.0003"},
    {"label": "Planova BioEX - 0.001m", "value": "0.001"},
    {"label": "Planova BioEX - 0.0003m", "value": "0.0003"},

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

# Viral Filtration Layout
viral_filtration_layout = html.Div(
    style={"maxWidth": "800px", "margin": "0 auto"},  # Centers content and limits width
    children=[
        html.H2("Viral Filtration Experiment Import",
                style={"textAlign": "center", "color": "#0047b3", "marginBottom": "20px"}),

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

        html.H3("Filtration Settings", style={"marginTop": "20px", "color": "#0047b3"}),

        html.Label("Target Pressure (bar):", style={"fontWeight": "bold"}),
        dcc.Input(id="pressure-target", type="number", placeholder="Enter pressure target",
                  style=input_style),

        # Cassette selection
        html.Label("Select Viral Filter Type:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Dropdown(id="filter-select", options=filter_options, placeholder="Choose a filter",
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

        html.Label("Water Flush File:", style={"fontWeight": "bold"}),
        dcc.Upload(
            id="upload-water-flush",
            children=html.Button("Upload Water Flush", id="button-water",
                                 style={"backgroundColor": "#0047b3", "color": "white", "border": "none",
                                        "padding": "10px 20px", "cursor": "pointer"}),
            multiple=False,
        ),

        html.Label("Buffer Flush File:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Upload(
            id="upload-buffer-flush",
            children=html.Button("Upload Buffer Flush", id="button-buffer",
                                 style={"backgroundColor": "#0047b3", "color": "white", "border": "none",
                                        "padding": "10px 20px", "cursor": "pointer"}),
            multiple=False,
        ),

        html.Label("Product Filtration File:", style={"fontWeight": "bold", "marginTop": "15px"}),
        dcc.Upload(
            id="upload-product-filtration",
            children=html.Button("Upload Product Filtration", id="button-product",
                                 style={"backgroundColor": "#0047b3", "color": "white", "border": "none",
                                        "padding": "10px 20px", "cursor": "pointer"}),
            multiple=False,
        ),

        html.Div(id="upload-status", style={"marginTop": "10px", "color": "green"}),
        # Data Table Preview
        html.H3("Uploaded Data Preview", style={"marginTop": "20px", "color": "#0047b3"}),
        dash_table.DataTable(
            id="data-preview",
            columns=[],
            data=[],
            style_table={"overflowX": "auto", "marginTop": "10px"},
            style_cell={"textAlign": "center", "padding": "5px"},
            style_header={"fontWeight": "bold", "backgroundColor": "#e9f1fb"},
            fixed_rows={"headers": True},
        ),
        html.Button("Import and Submit Report", id="submit-report", n_clicks=0,
                    style={"backgroundColor": "#28a745", "color": "white", "padding": "10px 20px",
                           "marginTop": "20px"}),

        html.Div(id="final-status", style={"marginTop": "10px", "color": "blue"}),

    ]
)

# Define layout
app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "padding": "20px"},
    children=[
        viral_filtration_layout
    ],
)


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
        load_mass = round(load_mass, 2)
        return load_mass
    except Exception as e:
        print(f"Error calculating Load Mass: {e}")
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
        recovery = round(recovery, 2)

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


@app.callback(
    [
        Output("button-water", "style"),
        Output("button-buffer", "style"),
        Output("button-product", "style"),
    ],
    [
        Input("upload-water-flush", "contents"),
        Input("upload-buffer-flush", "contents"),
        Input("upload-product-filtration", "contents"),
    ],
    prevent_initial_call=True
)
def update_button_styles(water_contents, buffer_contents, product_contents):
    uploaded_style = {
        "backgroundColor": "#28a745",  # Green to indicate success
        "color": "white",
        "border": "none",
        "padding": "10px 20px",
        "cursor": "pointer"
    }

    default_style = {
        "backgroundColor": "#0047b3",  # Default blue
        "color": "white",
        "border": "none",
        "padding": "10px 20px",
        "cursor": "pointer"
    }

    return (
        uploaded_style if water_contents else default_style,
        uploaded_style if buffer_contents else default_style,
        uploaded_style if product_contents else default_style
    )


@app.callback(
    Output("final-status", "children"),
    Input("submit-report", "n_clicks"),  # Now triggered by submit button
    [
        State("upload-water-flush", "contents"),
        State("upload-buffer-flush", "contents"),
        State("upload-product-filtration", "contents"),
        State("upload-water-flush", "filename"),
        State("upload-buffer-flush", "filename"),
        State("upload-product-filtration", "filename"),
        State("experiment-name", "value"),
        State("molecule-select", "value"),
        State("experiment-notes", "value"),
        State("filter-select", "value"),
        State("load-concentration", "value"),
        State("load-volume", "value"),
        State("load-mass", "value"),
        State("final-volume", "value"),
        State("final-concentration", "value"),
        State("product-mass", "value"),
        State("yield", "value"),
        State("pressure-target", "value"),
    ],
    prevent_initial_call=True  # Prevents running on page load
)
def process_uploaded_files(n_clicks,
                           water_contents, buffer_contents, product_contents,
                           water_filename, buffer_filename, product_filename,
                           experiment_name, molecule_name, experiment_notes, filter_type,
                           load_concentration, load_volume, load_mass, final_volume, final_concentration,
                           product_mass, recovery, target_pressure):
    # Mapping unit step numbers
    unit_step_mapping = {
        "water_flush": (water_contents, water_filename, 1),
        "buffer_flush": (buffer_contents, buffer_filename, 2),
        "product_filtration": (product_contents, product_filename, 3),
    }

    if not any([water_contents, buffer_contents, product_contents]):
        return "No files uploaded."

    # Step 1: Create a single metadata entry for this experiment
    vf_metadata = VFMetadata.objects.create(
        molecule_name=molecule_name,
        experiment_name=experiment_name,
        experimental_notes=experiment_notes,
        filter_type=filter_type,
        target_pressure=target_pressure,
        load_concentration=load_concentration,
        load_volume=load_volume,
        load_mass=load_mass,
        final_volume=final_volume,
        final_concentration=final_concentration,
        product_mass=product_mass,
        yield_percentage=recovery
    )

    records_created = 0

    # Step 2: Process each uploaded file
    for step_name, (contents, filename, unit_step) in unit_step_mapping.items():
        if contents:
            df = parse_csv(contents)  # Parse CSV file

            if isinstance(df, str):  # If parsing failed, return error
                return f"Error parsing {step_name} file: {df}"

            # Step 3: Insert time-series data
            time_series_records = [
                VFTimeSeriesData(
                    result_id=vf_metadata,
                    batch_id=row.get('BatchId'),
                    pdat_time=pd.to_datetime(row.get('PDatTime'), errors='coerce'),
                    process_time=row.get('ProcessTime', 0),
                    unit_step=unit_step,  # Assign correct unit step
                    f_perm_value=row.get('F_PERM_Value'),
                    pir2700=row.get('PIR2700'),
                    wir2700=row.get('WIR2700'),
                ) for _, row in df.iterrows()
            ]

            VFTimeSeriesData.objects.bulk_create(time_series_records)
            records_created += len(time_series_records)

    return f"Successfully imported {records_created} records for Experiment: {vf_metadata.experiment_name} (Result ID {vf_metadata.result_id})"
