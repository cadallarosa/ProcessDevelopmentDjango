import dash
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, MATCH, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
from plotly_integration.models import NovaFlex2, NovaReport
import json
from datetime import datetime
import re
import plotly.express as px

# Initialize the Dash app
app = DjangoDash("NovaDataReportApp")

# Define the variables and their corresponding labels
VARIABLES = {
    "gln": "Glutamine",
    "glu": "Glutamate",
    "gluc": "Glucose",
    "lac": "Lactate",
    "nh4": "Ammonium (NH4+)",
    "pH": "pH",
    "po2": "Partial Oxygen (PO2)",
    "do": "Dissolved Oxygen (DO)",
    "pco2": "Partial Carbon Dioxide (PCO2)",
    "osm": "Osmolality (Osm)"
}

UNITS = {
    "gln": "mmol/L",
    "glu": "mmol/L",
    "gluc": "g/L",
    "lac": "g/L",
    "nh4": "mmol/L",
    "pH": "-",  # No unit for pH
    "po2": "mmHg",
    "do": "mg/L",  # Assuming DO is in mg/L
    "pco2": "mmHg",
    "osm": "mOsm/kg"
}

# ✅ Define initial column structure
INITIAL_COLUMNS = [
    {"name": "Date", "id": "date_time"},
    {"name": "Sample Name", "id": "sample_id"},
    {"name": "Process Day", "id": "day"},
    {"name": "Glutamine (mmol/L)", "id": "gln"},
    {"name": "Glutamate (mmol/L)", "id": "glu"},
    {"name": "Glucose (g/L)", "id": "gluc"},
    {"name": "Lactate (g/L)", "id": "lac"},
    {"name": "Ammonium (mmol/L)", "id": "nh4"},
    {"name": "pH Level", "id": "pH"},
    {"name": "PO₂ (mmHg)", "id": "po2"},
    {"name": "DO", "id": "do"},
    {"name": "PCO₂ (mmHg)", "id": "pco2"},
    {"name": "Osmolality (mOsm/kg)", "id": "osm"}
]

app.layout = html.Div(
    style={"display": "flex", "flexDirection": "column", "height": "100vh", "padding": "20px"},
    children=[
        dcc.Store(id='selected-report', data=None),  # ✅ Store for selected report ID

        html.H1("Nova Flex 2 Report", style={"textAlign": "center", "color": "#0047b3", "marginBottom": "20px"}),

        # ✅ Report Selection Dropdown
        html.Label("Select a Report:", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id="report-dropdown",
            options=[],  # ✅ Populated dynamically
            placeholder="Select a report...",
            style={"width": "50%", "marginBottom": "20px"}
        ),

        # ✅ Tabs for variable selection
        dcc.Tabs(
            id="variable-tabs",
            value="gln",
            children=[dcc.Tab(label=label, value=var) for var, label in VARIABLES.items()]
                     + [  # ✅ Append extra tab
                         dcc.Tab(label="Summary", value="summary")
                     ]
        ),

        # ✅ Graph container that expands to fill remaining space
        html.Div(
            id="variable-graph-container",
            style={"flexGrow": 1, "display": "flex", "justifyContent": "center", "alignItems": "center"},
            children=[dcc.Graph(
                figure=[],
                style={"height": "90%", "width": "100%"},
                config={"responsive": True}
            )]
        ),
        # ✅ New dropdown & table container (only visible in "Summary" tab)
        html.Div(
            id="summary-container",
            style={
                "marginTop": "0px",  # ✅ Aligns container at the top
                "display": "none",  # ✅ Hide initially
                "position": "relative",  # ✅ Ensures it stays in the normal flow
                "width": "95%",  # ✅ Ensures it spans the full width
                "justifyContent": "flex-start",  # ✅ Aligns content at the top
                "alignItems": "flex-start",  # ✅ Ensures child elements start at the top
                "padding": "10px 0",  # ✅ Adds slight spacing for better layout
            },
            children=[
                dcc.Dropdown(
                    id="subset-dropdown",
                    placeholder="Select a Reactor Number",
                    style={"width": "50%", "marginBottom": "10px"}  # ✅ Adjust spacing
                ),
                html.Br(),

                # ✅ Initialize DataTable with column names & styles
                dash_table.DataTable(
                    id="subset-table",
                    data=[],  # ✅ Empty but structured data
                    columns=INITIAL_COLUMNS,  # ✅ Predefined columns
                    style_table={
                        "overflowX": "auto",  # ✅ Prevents horizontal scrolling
                        "width": "100%",  # ✅ Ensures it doesn't stretch too much
                        "maxWidth": "100%",  # ✅ Limits max width for better centering
                        "margin": "auto",  # ✅ Centers the table horizontally
                        "display": "flex",
                        "justifyContent": "center",
                        "borderRadius": "8px",
                        "table-layout": "fixed"
                    },
                    style_header={
                        "backgroundColor": "#e9f1fb",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "color": "#0047b3"
                    },
                    style_cell={
                        "textAlign": "center",
                        "padding": "10px",
                        "borderBottom": "1px solid #ccc",
                        "fontFamily": "Arial, sans-serif"
                    },
                    style_data={"backgroundColor": "white", "color": "#333"},
                    filter_action="native",
                    sort_action="native"
                ),
            ]
        ),
    ]
)


@app.callback(
    Output("report-dropdown", "options"),  # ✅ Populate dropdown
    Output("report-dropdown", "value"),  # ✅ Select the most recent report by default
    Input("report-dropdown", "value")  # ✅ Trigger when the dropdown changes
)
def populate_report_dropdown(selected_report):
    reports = NovaReport.objects.all().order_by("-date_created")  # ✅ Sort reports from most recent to oldest

    if not reports:
        return [], None  # ✅ Return empty if no reports exist

    options = [
        {"label": f"{r.report_name} (Created: {r.date_created.strftime('%Y-%m-%d %H:%M:%S')})", "value": r.id}
        for r in reports
    ]

    default_value = selected_report if selected_report else reports[0].id  # ✅ Default to most recent report

    return options, default_value


def process_and_sort_samples(sample_names):
    """
    - Fetches parsed data from the database instead of re-parsing.
    - Groups by `sample_id` and queries `NovaFlex2` to get data.
    - Returns a separate DataFrame for each unique `sample_id`.
    """

    # ✅ Query `NovaFlex2` for multiple samples at once
    samples = NovaFlex2.objects.filter(sample_id__in=sample_names).values(
        "sample_id", "experiment", "day", "reactor_type", "reactor_number", "special",
        "date_time", "gln", "glu", "gluc", "lac", "nh4", "pH", "po2", "pco2", "osm"
    )

    df = pd.DataFrame(list(samples))

    if df.empty:
        print("⚠️ No valid samples found.")
        return {}

    df_sorted = df.sort_values(by=["reactor_number", "day", "special"],
                               ascending=[True, True, True])  # ✅ Sorted correctly
    sample_groups = df_sorted.groupby("reactor_number")["sample_id"].apply(list).to_dict()

    grouped_data = {}

    for reactor_number, result_names in sample_groups.items():
        print(f"🔍 Querying NovaFlex2 for Reactor Number: {reactor_number}, Samples: {result_names}")  # Debugging log

        nova_data = NovaFlex2.objects.filter(sample_id__in=result_names).values(
            "sample_id", "day", "date_time", "gln", "glu", "gluc", "lac", "nh4", "pH", "po2", "pco2", "osm",
            "reactor_type"
        )

        nova_df = pd.DataFrame(list(nova_data))

        if not nova_df.empty:
            # ✅ Add the new column `do` (Dissolved Oxygen) as `po2 / 1.6`
            nova_df["do"] = nova_df["po2"] / 1.6

            grouped_data[reactor_number] = nova_df  # ✅ Store the queried results
        else:
            print(f"⚠️ No matching data found for Reactor Number {reactor_number}")
            grouped_data[reactor_number] = pd.DataFrame(
                columns=["sample_id", "day", "date_time", "gln", "glu", "gluc", "lac", "nh4", "pH", "po2", "pco2",
                         "osm", "reactor_type"]
            )  # ✅ Empty DataFrame with column names

    return grouped_data  # ✅ `{reactor_number: DataFrame}`


@app.callback(
    Output("variable-graph-container", "children"),
    [Input("report-dropdown", "value"),
     Input("variable-tabs", "value")],
    prevent_initial_call=True
)
def update_graph(selected_report_id, selected_variable):
    """
    Updates the graph based on the selected variable tab.
    Each graph plots different `reactor_number` groups over time using `day` as the x-axis.
    """
    if selected_variable is None:
        return "⚠️ No variable selected."
    if selected_variable == 'summary':
        return None
    if not selected_report_id:
        return "⚠️ No report selected."

    report = NovaReport.objects.filter(id=selected_report_id).first()
    if not report:
        return "⚠️ Report not found."

    if not report.selected_result_ids:
        return "⚠️ No selected result IDs found in this report."

    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]
    sample_names = list(NovaFlex2.objects.filter(id__in=sample_ids).values_list("sample_id", flat=True))

    if not sample_names:
        return "⚠️ No valid sample names found."

    # ✅ Process and group by `reactor_number`
    sorted_groups = process_and_sort_samples(sample_names)

    fig = px.line()

    for reactor_number, df in sorted_groups.items():
        if not df.empty and selected_variable in df.columns:
            print(df)
            df_sorted = df

            # ✅ Drop NaN/None values for the selected variable
            df_sorted = df.dropna(subset=[selected_variable])

            # ✅ Ensure there's still data left after dropping NaN values
            if df_sorted.empty:
                print(f"⚠️ All values were NaN for {selected_variable} in Reactor {reactor_number}, skipping...")
                continue  # Skip this reactor if no data remains

            # ✅ Get the unique reactor type for this group
            reactor_type = df_sorted["reactor_type"].iloc[0] if "reactor_type" in df_sorted.columns else "Unknown"

            fig.add_scatter(
                x=df_sorted["day"],
                y=df_sorted[selected_variable],
                mode="lines+markers",
                text=df_sorted["sample_id"],  # ✅ Display sample name on each point
                textposition="top center",
                name=f"{reactor_type}{int(reactor_number)}"
            )

    fig.update_layout(
        title={
            "text": f"{VARIABLES[selected_variable]}",
            "x": 0.5,  # ✅ Centers the title
            "xanchor": "center",
            "yanchor": "top"
        },
        # xaxis=dict(range=[0, None]),  # ✅ Start x-axis at 0
        xaxis_title="Day",
        yaxis_title=f"{VARIABLES[selected_variable]} ({UNITS.get(selected_variable, '')})",
        legend_title="Reactor Number",

        # height=800,  # ✅ Dynamically adjust height
        # margin={"l": 40, "r": 40, "t": 60, "b": 40},  # ✅ Reduce margins to maximize space
        # autosize=True  # ✅ Allow figure to resize dynamically
    )

    return dcc.Graph(figure=fig, style={"height": "90%", "width": "100%"}, )


# Summary Tab Logic

@app.callback(
    [Output("summary-container", "style"),
     Output("variable-graph-container", "style")],
    [Input("variable-tabs", "value")]
)
def toggle_tabs(selected_tab):
    """ Show summary content only when 'Summary' tab is selected and hide graph container. """

    # ✅ When "Summary" is selected, show summary container & hide graph container
    if selected_tab == "summary":
        summary_style = {"marginTop": "20px", "display": "block"}
        graph_style = {"flexGrow": 1, "display": "none", "justifyContent": "center", "alignItems": "center"}

    # ✅ Otherwise, show graph container & hide summary container
    else:
        summary_style = {"marginTop": "20px", "display": "none"}
        graph_style = {"flexGrow": 1, "display": "flex", "justifyContent": "center", "alignItems": "center"}

    return summary_style, graph_style


@app.callback(
    [Output("subset-dropdown", "options"),
     Output("subset-dropdown", "value")],  # ✅ Auto-select first option
    Input("report-dropdown", "value")
)
def update_reactor_number_dropdown(selected_report_id):
    """ Populate dropdown with available reactor numbers from the selected report. """
    if not selected_report_id:
        return []

    report = NovaReport.objects.filter(id=selected_report_id).first()
    if not report or not report.selected_result_ids:
        return []

    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]

    # ✅ Query all distinct reactor numbers, ignoring NULL values
    reactors = list(
        NovaFlex2.objects.filter(id__in=sample_ids, reactor_number__isnull=False)
        .values_list("reactor_number", flat=True)
        .distinct()
    )

    reactor_type = list(
        NovaFlex2.objects.filter(id__in=sample_ids, reactor_number__isnull=False)
        .values_list("reactor_type", flat=True)
        .distinct()
    )

    # ✅ Debugging: Check if reactors were retrieved
    print("Retrieved Reactors:", reactors)

    # ✅ Ensure reactors are sorted numerically
    sorted_reactors = sorted(filter(lambda x: x is not None, reactors))

    if not sorted_reactors:
        print("⚠️ No reactor numbers found!")

    # ✅ Create dropdown options
    options = [{"label": f"Reactor {reactor}", "value": reactor} for reactor in sorted_reactors]

    return options, sorted_reactors[0]


@app.callback(
    Output("subset-table", "data"),
    [Input("subset-dropdown", "value"),
     Input("report-dropdown", "value")]
)
def update_summary_table(selected_reactor, selected_report_id):
    """ Populate table with data when a reactor number is selected from the selected report. """
    if not selected_report_id or not selected_reactor:
        print("⚠️ No reactor or report selected.")
        return []

    # ✅ Fetch the selected report
    report = NovaReport.objects.filter(id=selected_report_id).first()
    if not report or not report.selected_result_ids:
        print("⚠️ Report not found or contains no selected results.")
        return []

    # ✅ Extract sample IDs associated with the report
    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]
    print(f"🔍 Selected Sample IDs: {sample_ids}")

    if not sample_ids:
        print("⚠️ No sample IDs found in the selected report.")
        return []

    # ✅ Ensure `selected_reactor` is an integer
    try:
        selected_reactor = int(selected_reactor)
    except ValueError:
        print(f"⚠️ Reactor number '{selected_reactor}' is not a valid integer.")
        return []

    # ✅ Query by `reactor_number` and `sample_id`
    subset_data = NovaFlex2.objects.filter(id__in=sample_ids, reactor_number=selected_reactor).values(
        "date_time", "sample_id", "day", "gln", "glu", "gluc", "lac", "nh4", "pH", "po2", "pco2", "osm"
    )

    subset_data_list = list(subset_data)

    # ✅ Debugging: Check if data was retrieved
    print(f"✅ Found {len(subset_data_list)} rows for Reactor {selected_reactor}.")
    print(subset_data_list[:5])  # Print first 5 rows to verify structure

    if not subset_data_list:
        print(f"⚠️ No data found for Reactor {selected_reactor} in the selected report.")
        return []

    # ✅ Convert to DataFrame for better formatting
    df = pd.DataFrame(subset_data_list)

    # ✅ Add the new column `do` (Dissolved Oxygen) as `po2 / 1.6`
    df["do"] = round(df["po2"] / 1.6, 1)

    if df.empty:
        print("⚠️ DataFrame is empty after conversion.")
        return []

    # ✅ Convert datetime column to string for display
    if "date_time" in df.columns:
        df["date_time"] = df["date_time"].astype(str)

    # ✅ Return updated data and column headers
    return df.to_dict("records")
