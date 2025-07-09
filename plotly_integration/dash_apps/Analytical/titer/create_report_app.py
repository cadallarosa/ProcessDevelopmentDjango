import pytz
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
from plotly_integration.models import SampleMetadata, Report
from datetime import datetime
import re
import pandas as pd
from django.utils.timezone import is_aware

# Initialize the Dash app
app = DjangoDash("ReportApp")


def get_default_columns_and_data():
    default_columns = ["sample_name", "result_id", "date_acquired", "sample_set_name", "column_name"]
    samples = SampleMetadata.objects.all()
    columns = [{"name": col.replace("_", " ").title(), "id": col} for col in default_columns]

    data = []
    for sample in samples:
        row = {col: getattr(sample, col, None) for col in default_columns}  # ✅ Use `None` instead of erroring out

        if "date_acquired" in row and row["date_acquired"]:
            dt_value = row["date_acquired"]

            # ✅ Convert string-based date to datetime
            if isinstance(dt_value, str):
                try:
                    dt_value = datetime.strptime(dt_value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt_value = None

            # ✅ Strip timezone info if datetime is aware
            if isinstance(dt_value, datetime) and is_aware(dt_value):
                dt_value = dt_value.replace(tzinfo=None)

            row["date_acquired"] = dt_value  # ✅ Store corrected value

        data.append(row)

    # ✅ Sort by `date_acquired` (most recent first) after stripping timezone
    data = sorted(
        data,
        key=lambda x: x["date_acquired"] if x["date_acquired"] else datetime.min,
        reverse=True
    )

    # ✅ Convert back to string for display
    for row in data:
        if row["date_acquired"]:
            row["date_acquired"] = row["date_acquired"].strftime("%m/%d/%Y %I:%M:%S %p")

    return columns, data


# Default columns and data for the table
default_columns, default_data = get_default_columns_and_data()

# Layout
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f4f7f6",
        "padding": "20px",
        "maxWidth": "1200px",
        "margin": "0 auto",
        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "borderRadius": "8px"
    },
    children=[
        html.H1(
            "Sample Report Submission",
            style={
                "textAlign": "center",
                "color": "#0047b3",
                "marginBottom": "20px"
            }
        ),

        # Filters Section
        html.Div(
            style={"marginBottom": "20px"},
            children=[
                html.Label("Select Analysis Type:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="analysis_type_filter",
                    options=[
                        {"label": "SEC", "value": "1"},
                        {"label": "Titer", "value": "2"}
                    ],
                    placeholder="Select analysis type",
                    multi=False,  # ✅ Only one option can be selected
                    clearable=False,  # ✅ Forces selection (prevents blank state)
                    style={"marginBottom": "10px"},
                    value='1',
                ),
                html.Label("Filter by Sample Type:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="sample_type_filter",
                    options=[
                        {"label": "PD", "value": "PD"},
                        {"label": "UP", "value": "UP"},
                        {"label": "FB", "value": "FB"}
                    ],
                    placeholder="Select sample type",
                    multi=True,
                    style={"marginBottom": "10px"}
                ),

                html.Label("Filter by Sample Set Name:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="sample_set_name_filter",
                    options=[],  # Dynamically populated
                    placeholder="Select sample set name",
                    multi=True,
                    style={"marginBottom": "20px"}
                )
            ]
        ),

        # Column Selection Section
        html.Div(
            style={"marginBottom": "20px"},
            children=[
                html.Label("Select Columns to Display in the Table:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="column_selection",
                    options=[
                        {"label": "Result ID", "value": "result_id"},
                        {"label": "System Name", "value": "system_name"},
                        {"label": "Project Name", "value": "project_name"},
                        {"label": "Sample Prefix", "value": "sample_prefix"},
                        {"label": "Sample Number", "value": "sample_number"},
                        {"label": "Sample Suffix", "value": "sample_suffix"},
                        {"label": "Sample Type", "value": "sample_type"},
                        {"label": "Sample Name", "value": "sample_name"},
                        {"label": "Sample Set ID", "value": "sample_set_id"},
                        {"label": "Sample Set Name", "value": "sample_set_name"},
                        {"label": "Date Acquired", "value": "date_acquired"},
                        {"label": "Acquired By", "value": "acquired_by"},
                        {"label": "Run Time", "value": "run_time"},
                        {"label": "Processing Method", "value": "processing_method"},
                        {"label": "Processed Channel Description", "value": "processed_channel_description"},
                        {"label": "Injection Volume", "value": "injection_volume"},
                        {"label": "Injection ID", "value": "injection_id"},
                        {"label": "Column Name", "value": "column_name"},
                        {"label": "Column Serial Number", "value": "column_serial_number"},
                        {"label": "Instrument Method ID", "value": "instrument_method_id"},
                        {"label": "Instrument Method Name", "value": "instrument_method_name"}
                    ],
                    value=["sample_name", "result_id", "date_acquired", "sample_set_name", "column_name"],
                    multi=True,
                    placeholder="Select columns to display",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px",
                        "backgroundColor": "white"
                    }
                )
            ]
        ),

        # Data Table Section
        html.Div(
            children=[
                html.Button(
                    "Select All",
                    id="select_all_button",
                    n_clicks=0,
                    style={
                        "marginBottom": "10px",
                        "backgroundColor": "#0047b3",
                        "color": "white",
                        "padding": "5px 10px",
                        "border": "none",
                        "borderRadius": "5px",
                        "cursor": "pointer"
                    }
                ),
                dash_table.DataTable(
                    id="sample_table",
                    columns=default_columns,
                    data=default_data,
                    row_selectable="multi",
                    selected_rows=[],
                    page_size=15,
                    filter_action="native",
                    sort_action="native",  # Enable sorting
                    sort_mode="multi",  # Allow multi-column sorting
                    style_table={
                        "overflowX": "auto",
                        "width": "100%",
                        "borderRadius": "5px",
                        "boxShadow": "0px 2px 6px rgba(0, 0, 0, 0.1)"
                    },
                    style_cell={
                        "padding": "10px",
                        "textAlign": "center",
                        "borderBottom": "1px solid #ccc"
                    },
                    style_header={
                        "fontWeight": "bold",
                        "backgroundColor": "#e9f1fb",
                        "color": "#0047b3"
                    },
                    style_data={
                        "backgroundColor": "white",
                        "color": "#333"
                    }
                )
            ],
            style={"marginBottom": "20px"}
        ),

        # Report Details
        html.Div(
            children=[
                html.Label("Report Name:", style={"fontWeight": "bold"}),
                dcc.Input(
                    id="report_name_input",
                    type="text",
                    placeholder="Enter report name",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px"
                    }
                ),
                html.Label("Project ID:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="project_id_dropdown",
                    placeholder="Select or enter a Project ID",
                    options=[],  # Dynamically populated
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px"
                    }
                ),
                dcc.Input(
                    id="new_project_id_input",
                    type="text",
                    placeholder="Enter new Project ID",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px",
                        "display": "none"
                    }
                ),
                html.Label("Comments:", style={"fontWeight": "bold"}),
                dcc.Input(
                    id="comments_input",
                    type="text",
                    placeholder="Enter comments",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px"
                    }
                ),
                html.Label("User ID:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="user_id_dropdown",
                    placeholder="Select or enter a User ID",
                    options=[],  # Dynamically populated
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px"
                    }
                ),
                dcc.Input(
                    id="new_user_id_input",
                    type="text",
                    placeholder="Enter new User ID",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "10px",
                        "border": "1px solid #ccc",
                        "borderRadius": "5px",
                        "display": "none"
                    }
                )
            ]
        ),

        # Submit Button
        html.Button(
            "Submit Report",
            id="submit_button",
            n_clicks=0,
            style={
                "backgroundColor": "#0047b3",
                "color": "white",
                "padding": "10px 20px",
                "border": "none",
                "borderRadius": "5px",
                "cursor": "pointer",
                "display": "block",
                "margin": "0 auto",
                "marginBottom": "20px"
            }
        ),

        # Submission Status
        html.Div(
            id="submission_status",
            style={
                "textAlign": "center",
                "color": "green",
                "fontWeight": "bold",
                "fontSize": "16px"
            }
        )
    ]
)


# Dynamically update table data based on filters
@app.callback(
    [Output("sample_table", "columns"),
     Output("sample_table", "data")],
    [Input("sample_type_filter", "value"),
     Input("sample_set_name_filter", "value"),
     Input("column_selection", "value"),
     Input("analysis_type_filter", "value")]
)
def update_table(sample_types, sample_set_names, selected_columns, analysis_type):
    # Default columns
    if not selected_columns:
        selected_columns = ["sample_name", "result_id", "date_acquired", "sample_set_name", "column_name"]

    columns = [{"name": col.replace("_", " ").title(), "id": col} for col in selected_columns]

    # Filter data
    query = SampleMetadata.objects.all()
    if sample_types:
        query = query.filter(sample_prefix__in=sample_types)
    if sample_set_names:
        query = query.filter(sample_set_name__in=sample_set_names)
    if analysis_type:  # ✅ Apply filter based on selected Analysis Type
        query = query.filter(sample_type=analysis_type)

    data = []
    for sample in query:
        row = {col: getattr(sample, col, None) for col in selected_columns}  # ✅ Use `None` instead of erroring out

        if "date_acquired" in row and row["date_acquired"]:
            dt_value = row["date_acquired"]

            # ✅ Convert string-based date to datetime
            if isinstance(dt_value, str):
                try:
                    dt_value = datetime.strptime(dt_value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt_value = None

            # ✅ Strip timezone info if datetime is aware
            if isinstance(dt_value, datetime) and is_aware(dt_value):
                dt_value = dt_value.replace(tzinfo=None)

            row["date_acquired"] = dt_value  # ✅ Store corrected value

        data.append(row)

        # ✅ Sort by `date_acquired` (most recent first) after stripping timezone
    data = sorted(
        data,
        key=lambda x: x["date_acquired"] if x["date_acquired"] else datetime.min,
        reverse=True
    )

    # ✅ Convert back to string for display
    for row in data:
        if row["date_acquired"]:
            row["date_acquired"] = row["date_acquired"].strftime("%m/%d/%Y %I:%M:%S %p")

    return columns, data


# Dynamically populate Sample Set Name options based on Sample Type
@app.callback(
    Output("sample_set_name_filter", "options"),
    Input("sample_type_filter", "value"),
    Input("analysis_type_filter", "value")
)
def update_sample_set_options(sample_types, analysis_type):
    query = SampleMetadata.objects.all()
    if analysis_type:  # ✅ Filter based on selected analysis type
        query = query.filter(sample_type=analysis_type)
    if sample_types:
        query = query.filter(sample_prefix__in=sample_types)

    sample_set_names = list(query.values_list("sample_set_name", flat=True).distinct())

    # Extract the date prefix (YYMMDD) and convert to datetime for sorting
    def extract_date(sample_set):
        if not sample_set:  # ✅ Handle None values
            return datetime.min  # Assign the earliest possible date

        try:
            date_part = sample_set[:6]  # ✅ Safe slicing
            return datetime.strptime(date_part, "%y%m%d")  # Convert to YYYY-MM-DD format
        except ValueError:
            return datetime.min  # Assign the earliest date if invalid format

    # Sort sample sets by extracted date in descending order (most recent first)
    sample_set_names_sorted = sorted(sample_set_names, key=extract_date, reverse=True)

    return [{"label": name, "value": name} for name in sample_set_names_sorted if name]


# Select All Button
@app.callback(
    Output("sample_table", "selected_rows"),
    Input("select_all_button", "n_clicks"),
    State("sample_table", "data")
)
def select_all_rows(n_clicks, data):
    if n_clicks % 2 == 1:
        return list(range(len(data)))  # Select all rows
    return []  # Deselect all rows


@app.callback(
    [Output("project_id_dropdown", "options"),
     Output("new_project_id_input", "style")],
    [Input("project_id_dropdown", "value")]
)
def populate_project_ids(selected_project_id):
    # Fetch distinct project IDs
    project_ids = list(Report.objects.values_list("project_id", flat=True).distinct())

    # Function to extract sorting components
    def extract_sort_key(pid):
        """
        Extract numeric and letter components from project ID.
        Example: 'SI-11a11' -> (11, 'a', 11)
        """
        match = re.match(r"SI-(\d+)([a-zA-Z]?)(\d*)", pid)
        if match:
            num_part = int(match.group(1)) if match.group(1) else 0
            letter_part = match.group(2) if match.group(2) else ""
            suffix_part = int(match.group(3)) if match.group(3) else 0
            return (num_part, letter_part, suffix_part)
        return (float("inf"), "", float("inf"))  # Default for invalid formats

    # Sort the project IDs using extracted components
    sorted_project_ids = sorted(project_ids, key=extract_sort_key)

    # Generate dropdown options
    options = [{"label": pid, "value": pid} for pid in sorted_project_ids if pid]
    options.append({"label": "Enter New Project ID", "value": "new_project_id"})

    if selected_project_id == "new_project_id":
        return options, {"display": "block"}
    return options, {"display": "none"}


# Populate User ID options and toggle new User ID input
@app.callback(
    [Output("user_id_dropdown", "options"),
     Output("new_user_id_input", "style")],
    [Input("user_id_dropdown", "value")]
)
def populate_user_ids(selected_user_id):
    user_ids = Report.objects.values_list("user_id", flat=True).distinct()
    options = [{"label": uid, "value": uid} for uid in user_ids if uid]
    options.append({"label": "Enter New User ID", "value": "new_user_id"})

    if selected_user_id == "new_user_id":
        return options, {"display": "block"}
    return options, {"display": "none"}


@app.callback(
    Output("submission_status", "children"),
    Input("submit_button", "n_clicks"),
    Input("analysis_type_filter", "value"),
    [
        State("report_name_input", "value"),
        State("project_id_dropdown", "value"),
        State("new_project_id_input", "value"),
        State("user_id_dropdown", "value"),
        State("new_user_id_input", "value"),
        State("comments_input", "value"),
        State("sample_table", "data"),
        State("sample_table", "selected_rows"),

    ]
)
def submit_report(n_clicks, analysis_type, report_name, project_id, new_project_id, user_id, new_user_id, comments,
                  table_data,
                  selected_rows):
    if n_clicks > 0:
        if not selected_rows:
            return "No rows selected. Please select rows to include in the report."

        # Validate required fields
        if not report_name or (not project_id and not new_project_id) or (not user_id and not new_user_id):
            return "Please provide all required fields."

        final_project_id = new_project_id if project_id == "new_project_id" else project_id
        final_user_id = new_user_id if user_id == "new_user_id" else user_id

        # Collect selected rows into DataFrame
        data = []
        for i in selected_rows:
            row = table_data[i]
            sample_name = row.get("sample_name")
            result_id = table_data[i].get("result_id")
            if result_id:
                data.append((sample_name, str(result_id)))

        if not data:
            return "No matching result IDs found for selected samples."

        # Sort by sample name and extract lists
        df = pd.DataFrame(data, columns=["sample_name", "result_id"])
        df = df.sort_values(by="sample_name", ascending=True)
        sorted_samples = df["sample_name"].tolist()
        sorted_result_ids = df["result_id"].tolist()

        sample_names_str = ",".join(sorted_samples)
        result_ids_str = ",".join(sorted_result_ids)

        # Store report with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        Report.objects.create(
            report_name=report_name,
            project_id=final_project_id,
            user_id=final_user_id,
            comments=comments,
            selected_samples=sample_names_str,
            selected_result_ids=result_ids_str,
            date_created=timestamp,
            analysis_type=analysis_type,
            department=1
        )

        return f"Report '{report_name}' created successfully with {len(sorted_samples)} samples."

    return "No action performed."
