import dash
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
from plotly_integration.models import ViCellData, ViCellReport
from datetime import datetime

# Initialize the app
app = DjangoDash("ViCellCreateReportApp")

# Define color scheme
COLORS = {
    'primary': '#0056b3',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'white': '#ffffff',
    'background': '#f5f5fa'
}

# Default data
default_data = []
default_columns = [
    {"name": "Sample ID", "id": "sample_id"},
    {"name": "Date", "id": "date_time"},
    {"name": "Experiment", "id": "experiment"},
    {"name": "Cell Count", "id": "cell_count", "type": "numeric", "format": {"specifier": ",.0f"}},
    {"name": "Viable Cells", "id": "viable_cells", "type": "numeric", "format": {"specifier": ",.0f"}},
    {"name": "Viability (%)", "id": "viability", "type": "numeric", "format": {"specifier": ".1f"}}
]

# Sample type mapping
SAMPLE_TYPE_MAP = {
    "1": "UP",
    "2": "CLD",
    "3": "Unorganized"
}

# Layout
app.layout = html.Div(
    style={
        "backgroundColor": COLORS['background'],
        "minHeight": "100vh",
        "padding": "20px",
        "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    },
    children=[
        # # Simple title
        # html.H3(
        #     "Create ViCell Report",
        #     style={
        #         "color": COLORS['primary'],
        #         "marginBottom": "20px",
        #         "fontWeight": "600",
        #         "textAlign": "center"
        #     }
        # ),

        # Filters Section
        html.Div(
            style={
                "backgroundColor": COLORS['white'],
                "borderRadius": "10px",
                "padding": "25px",
                "marginBottom": "20px",
                "boxShadow": "0 2px 10px rgba(0,0,0,0.1)"
            },
            children=[
                html.H4("Filter Samples", style={"marginBottom": "20px", "color": COLORS['dark']}),

                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                    children=[
                        # Sample Type Filter
                        html.Div([
                            html.Label(
                                "Sample Type",
                                style={
                                    "fontWeight": "500",
                                    "marginBottom": "8px",
                                    "display": "block",
                                    "color": COLORS['dark']
                                }
                            ),
                            dcc.Dropdown(
                                id="sample_type_filter",
                                placeholder="Select sample type...",
                                style={"width": "100%"}
                            )
                        ]),

                        # Experiment Number Filter
                        html.Div([
                            html.Label(
                                "Experiment Number",
                                style={
                                    "fontWeight": "500",
                                    "marginBottom": "8px",
                                    "display": "block",
                                    "color": COLORS['dark']
                                }
                            ),
                            dcc.Dropdown(
                                id="experiment_number_filter",
                                placeholder="Select experiment number(s)...",
                                multi=True,
                                style={"width": "100%"}
                            )
                        ])
                    ]
                )
            ]
        ),

        # Sample Table Section
        html.Div(
            style={
                "backgroundColor": COLORS['white'],
                "borderRadius": "10px",
                "padding": "25px",
                "marginBottom": "20px",
                "boxShadow": "0 2px 10px rgba(0,0,0,0.1)"
            },
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "20px"
                    },
                    children=[
                        html.H4("Available Samples", style={"margin": "0", "color": COLORS['dark']}),
                        html.Div([
                            html.Button(
                                "Select All",
                                id="select_all_button",
                                n_clicks=0,
                                style={
                                    "backgroundColor": COLORS['info'],
                                    "color": "white",
                                    "border": "none",
                                    "padding": "8px 16px",
                                    "borderRadius": "5px",
                                    "cursor": "pointer",
                                    "fontSize": "14px",
                                    "fontWeight": "500",
                                    "marginRight": "10px",
                                    "transition": "all 0.3s ease"
                                }
                            ),
                            html.Span(
                                id="selection_count",
                                style={
                                    "color": COLORS['secondary'],
                                    "fontSize": "14px"
                                }
                            )
                        ])
                    ]
                ),

                dash_table.DataTable(
                    id="sample_table",
                    columns=default_columns,
                    data=default_data,
                    row_selectable="multi",
                    selected_rows=[],
                    page_size=10,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    style_table={
                        "overflowX": "auto",
                        "borderRadius": "8px",
                        "border": "1px solid #dee2e6"
                    },
                    style_cell={
                        "padding": "12px",
                        "textAlign": "left",
                        "fontSize": "14px",
                        "borderRight": "1px solid #dee2e6"
                    },
                    style_header={
                        "fontWeight": "600",
                        "backgroundColor": COLORS['light'],
                        "color": COLORS['dark'],
                        "borderBottom": "2px solid #dee2e6"
                    },
                    style_data={
                        "backgroundColor": "white",
                        "color": COLORS['dark'],
                        "borderBottom": "1px solid #dee2e6"
                    },
                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": COLORS['light']
                        },
                        {
                            "if": {"state": "selected"},
                            "backgroundColor": "rgba(0, 123, 255, 0.1)",
                            "border": "1px solid #007bff"
                        }
                    ],
                    style_filter={
                        "backgroundColor": COLORS['light'],
                        "border": "1px solid #ced4da"
                    }
                )
            ]
        ),

        # Report Details Section
        html.Div(
            style={
                "backgroundColor": COLORS['white'],
                "borderRadius": "10px",
                "padding": "25px",
                "boxShadow": "0 2px 10px rgba(0,0,0,0.1)"
            },
            children=[
                html.H4("Report Details", style={"marginBottom": "20px", "color": COLORS['dark']}),

                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                    children=[
                        # Report Name
                        html.Div([
                            html.Label(
                                "Report Name *",
                                style={
                                    "fontWeight": "500",
                                    "marginBottom": "8px",
                                    "display": "block",
                                    "color": COLORS['dark']
                                }
                            ),
                            dcc.Input(
                                id="report_name_input",
                                type="text",
                                placeholder="Enter report name...",
                                style={
                                    "width": "100%",
                                    "padding": "10px",
                                    "borderRadius": "5px",
                                    "border": "1px solid #ced4da",
                                    "fontSize": "14px"
                                }
                            )
                        ]),

                        # Project ID
                        html.Div([
                            html.Label(
                                "Project ID",
                                style={
                                    "fontWeight": "500",
                                    "marginBottom": "8px",
                                    "display": "block",
                                    "color": COLORS['dark']
                                }
                            ),
                            dcc.Input(
                                id="project_id_input",
                                type="text",
                                placeholder="Enter project ID...",
                                style={
                                    "width": "100%",
                                    "padding": "10px",
                                    "borderRadius": "5px",
                                    "border": "1px solid #ced4da",
                                    "fontSize": "14px"
                                }
                            )
                        ])
                    ]
                ),

                # User ID
                html.Div(
                    style={"marginTop": "20px"},
                    children=[
                        html.Label(
                            "User ID",
                            style={
                                "fontWeight": "500",
                                "marginBottom": "8px",
                                "display": "block",
                                "color": COLORS['dark']
                            }
                        ),
                        dcc.Input(
                            id="user_id_input",
                            type="text",
                            placeholder="Enter user ID...",
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "borderRadius": "5px",
                                "border": "1px solid #ced4da",
                                "fontSize": "14px"
                            }
                        )
                    ]
                ),

                # Comments
                html.Div(
                    style={"marginTop": "20px"},
                    children=[
                        html.Label(
                            "Comments",
                            style={
                                "fontWeight": "500",
                                "marginBottom": "8px",
                                "display": "block",
                                "color": COLORS['dark']
                            }
                        ),
                        dcc.Textarea(
                            id="comments_input",
                            placeholder="Enter any additional comments...",
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "borderRadius": "5px",
                                "border": "1px solid #ced4da",
                                "fontSize": "14px",
                                "minHeight": "100px",
                                "resize": "vertical"
                            }
                        )
                    ]
                ),

                # Action Buttons
                html.Div(
                    style={
                        "marginTop": "30px",
                        "display": "flex",
                        "justifyContent": "flex-end",
                        "gap": "10px"
                    },
                    children=[
                        html.Button(
                            "Create Report",
                            id="create_report_button",
                            n_clicks=0,
                            style={
                                "backgroundColor": COLORS['success'],
                                "color": "white",
                                "border": "none",
                                "padding": "12px 24px",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontSize": "16px",
                                "fontWeight": "500",
                                "transition": "all 0.3s ease",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            }
                        )
                    ]
                ),

                # Status Message
                html.Div(
                    id="report_status",
                    style={
                        "marginTop": "20px",
                        "fontWeight": "bold"
                    }
                )
            ]
        )
    ]
)


# Populate sample types
@app.callback(
    Output("sample_type_filter", "options"),
    Input("sample_type_filter", "value")  # Dummy input to trigger on load
)
def populate_sample_types(_):
    # Return mapped sample type options
    return [
        {"label": "UP", "value": "1"},
        {"label": "CLD", "value": "2"},
        {"label": "Unorganized", "value": "3"}
    ]


# Update experiment options based on sample type
@app.callback(
    Output("experiment_number_filter", "options"),
    Input("sample_type_filter", "value")
)
def update_experiment_options(selected_sample_type):
    if not selected_sample_type:
        return []

    experiment_numbers = (
        ViCellData.objects.filter(sample_type=selected_sample_type)
        .exclude(experiment__isnull=True)
        .values_list("experiment", flat=True)
        .distinct()
        .order_by("-experiment")
    )

    return [{"label": str(exp), "value": str(exp)} for exp in experiment_numbers]


# Update table based on filters
@app.callback(
    Output("sample_table", "data"),
    [Input("sample_type_filter", "value"),
     Input("experiment_number_filter", "value")]
)
def update_table(selected_sample_type, selected_experiment_numbers):
    query = ViCellData.objects.all().order_by("-date_time")

    if selected_sample_type:
        query = query.filter(sample_type=selected_sample_type)

    if selected_experiment_numbers:
        query = query.filter(experiment__in=selected_experiment_numbers)

    data = list(query.values(
        "id", "sample_id", "sample_type", "date_time",
        "cell_count", "viable_cells", "viability", "experiment"
    ))

    # Format datetime for display and add sample_type for internal use
    for row in data:
        if row["date_time"]:
            row["date_time"] = row["date_time"].strftime("%m/%d/%Y %I:%M %p")
        # Keep sample_type in data but it won't be displayed in the table

    return data


# Update selection count
@app.callback(
    Output("selection_count", "children"),
    [Input("sample_table", "selected_rows")],
    [State("sample_table", "data")]
)
def update_selection_count(selected_rows, data):
    if not selected_rows:
        return "0 samples selected"
    return f"{len(selected_rows)} of {len(data)} samples selected"


# Select all button
@app.callback(
    Output("sample_table", "selected_rows"),
    Input("select_all_button", "n_clicks"),
    State("sample_table", "data"),
    prevent_initial_call=True
)
def select_all_rows(n_clicks, data):
    if not data:
        return []

    # Toggle logic: Select all if odd clicks, Deselect all if even
    if n_clicks % 2 == 1:
        return list(range(len(data)))
    return []


# Create report
@app.callback(
    Output("report_status", "children"),
    Input("create_report_button", "n_clicks"),
    [State("report_name_input", "value"),
     State("project_id_input", "value"),
     State("user_id_input", "value"),
     State("comments_input", "value"),
     State("sample_table", "data"),
     State("sample_table", "selected_rows")],
    prevent_initial_call=True
)
def create_report(n_clicks, report_name, project_id, user_id, comments, table_data, selected_rows):
    if not report_name or not selected_rows:
        return html.Div([
            "❌ Please provide a report name and select at least one sample."
        ], style={"color": COLORS['danger']})

    try:
        selected_sample_ids = [table_data[i]["id"] for i in selected_rows]

        ViCellReport.objects.create(
            report_name=report_name,
            project_id=project_id,
            user_id=user_id,
            comments=comments,
            selected_result_ids=",".join(map(str, selected_sample_ids))
        )

        return html.Div([
            f"✅ Report '{report_name}' created successfully with {len(selected_sample_ids)} samples!"
        ], style={"color": COLORS['success']})

    except Exception as e:
        return html.Div([
            f"❌ Error creating report: {str(e)}"
        ], style={"color": COLORS['danger']})