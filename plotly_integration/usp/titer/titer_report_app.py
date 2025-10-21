import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
import numpy as np
from plotly_integration.models import LimsTiterResult, LimsSampleAnalysis, USPExperiment
import re
import plotly.express as px

# Initialize the Dash app with Bootstrap theme
app = DjangoDash("USPTiterTrackingApp", external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define initial column structure
INITIAL_COLUMNS = [
    {"name": "Sample ID", "id": "sample_id"},
    {"name": "Process Day", "id": "day"},
    {"name": "Titer (g/L)", "id": "titer", "type": "numeric", "format": {"specifier": ".3f"}},
    {"name": "Sample Date", "id": "sample_date"},
    {"name": "QC Pass", "id": "qc_pass"}
]

# Analytics columns
ANALYTICS_COLUMNS = [
    {"name": "Group", "id": "group"},
    {"name": "Sample Count", "id": "sample_count", "type": "numeric"},
    {"name": "Final Titer (g/L)", "id": "final_titer", "type": "numeric", "format": {"specifier": ".3f"}},
    {"name": "Max Titer (g/L)", "id": "max_titer", "type": "numeric", "format": {"specifier": ".3f"}},
    {"name": "Day of Max", "id": "day_of_max", "type": "numeric"},
    {"name": "Growth Rate D9-D12 (g/L/day)", "id": "growth_rate_early", "type": "numeric", "format": {"specifier": ".3f"}},
    {"name": "Growth Rate D12-D15 (g/L/day)", "id": "growth_rate_late", "type": "numeric", "format": {"specifier": ".3f"}},
    {"name": "Avg Productivity (g/L/day)", "id": "avg_productivity", "type": "numeric", "format": {"specifier": ".3f"}}
]

# Main layout
app.layout = html.Div([
    # Stores for state management
    dcc.Store(id="selected-experiment", data=None),
    dcc.Store(id="embedded-mode", data=False),
    dcc.Store(id="url-params", data={}),
    dcc.Location(id="url", refresh=False),
    dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

    # Modal for Select Experiment
    dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle([html.I(className="bi bi-folder me-2"), "Select USP Experiment"]),
            close_button=True
        ),
        dbc.ModalBody([
            dbc.Spinner(
                dash_table.DataTable(
                    id="experiment-selection-table",
                    columns=[
                        {"name": "Experiment ID", "id": "experiment_id"},
                        {"name": "Name", "id": "name"},
                        {"name": "Start Date", "id": "start_date"}
                    ],
                    data=[],
                    row_selectable="single",
                    selected_rows=[],
                    page_size=10,
                    sort_action="native",
                    filter_action="native",
                    style_table={"overflowY": "auto", "maxHeight": "500px"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "12px",
                        "fontSize": "14px"
                    },
                    style_header={
                        "backgroundColor": "#f8f9fa",
                        "fontWeight": "bold",
                        "color": "#495057"
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
                        {"if": {"state": "selected"}, "backgroundColor": "#cfe2ff"}
                    ]
                ),
                color="primary"
            )
        ]),
        dbc.ModalFooter([
            dbc.Button(
                [html.I(className="bi bi-check-lg me-2"), "Select Experiment"],
                id="confirm-experiment-selection",
                color="primary"
            )
        ])
    ], id="select-experiment-modal", size="xl", is_open=False),

    # Top toolbar
    dbc.Container(
        fluid=True,
        className="p-3 bg-light border-bottom",
        children=[
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="bi bi-folder me-2"), "Select Experiment"],
                        id="change-experiment-btn",
                        color="secondary"
                    )
                ], width="auto"),
                dbc.Col([
                    html.Div(id="current-experiment-text", className="h5 mb-0")
                ], className="d-flex align-items-center justify-content-end")
            ], className="mb-2")
        ]
    ),

    # Main content
    dbc.Container(
        fluid=True,
        className="p-3",
        children=[
            dbc.Card([
                dbc.CardHeader(
                    dbc.Tabs(
                        id="variable-tabs",
                        active_tab="summary",
                        children=[
                            dbc.Tab(label="Plots", tab_id="plots"),
                            dbc.Tab(label="Analytics", tab_id="analytics"),
                            dbc.Tab(label="Summary", tab_id="summary")
                        ]
                    )
                ),
                dbc.CardBody([
                    # Summary container
                    html.Div(
                        id="summary-container",
                        style={"display": "block"},
                        children=[
                            dbc.Row([
                                dbc.Col([
                                    html.H4([html.I(className="bi bi-table me-2"), "Titer Data Summary"],
                                           className="text-primary mb-3")
                                ], width=8),
                                dbc.Col([
                                    dcc.Dropdown(
                                        id="subset-dropdown",
                                        placeholder="Select Sample Group",
                                        className="mb-3"
                                    )
                                ], width=4)
                            ]),
                            dbc.Spinner(
                                dash_table.DataTable(
                                    id="subset-table",
                                    columns=INITIAL_COLUMNS,
                                    data=[],
                                    page_size=15,
                                    style_table={"overflowX": "auto"},
                                    style_header={
                                        "backgroundColor": "#f8f9fa",
                                        "fontWeight": "bold",
                                        "textAlign": "center",
                                        "color": "#495057"
                                    },
                                    style_cell={
                                        "textAlign": "center",
                                        "padding": "12px",
                                        "fontSize": "13px"
                                    },
                                    style_data_conditional=[
                                        {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}
                                    ],
                                    filter_action="native",
                                    sort_action="native"
                                ),
                                color="primary"
                            )
                        ]
                    ),

                    # Analytics container
                    html.Div(
                        id="analytics-container",
                        style={"display": "none"},
                        children=[
                            html.H4([html.I(className="bi bi-graph-up me-2"), "Titer Analytics"],
                                   className="text-primary mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Spinner(
                                        dash_table.DataTable(
                                            id="analytics-table",
                                            columns=ANALYTICS_COLUMNS,
                                            data=[],
                                            style_table={"overflowX": "auto"},
                                            style_header={
                                                "backgroundColor": "#f8f9fa",
                                                "fontWeight": "bold",
                                                "textAlign": "center",
                                                "color": "#495057",
                                                "fontSize": "12px"
                                            },
                                            style_cell={
                                                "textAlign": "center",
                                                "padding": "10px",
                                                "fontSize": "12px"
                                            },
                                            style_data_conditional=[
                                                {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
                                                {
                                                    "if": {
                                                        "filter_query": "{max_titer} = {final_titer}",
                                                        "column_id": "final_titer"
                                                    },
                                                    "backgroundColor": "#d4edda",
                                                    "fontWeight": "bold"
                                                }
                                            ],
                                            sort_action="native"
                                        ),
                                        color="primary"
                                    )
                                ])
                            ], className="mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id="analytics-charts")
                                ])
                            ])
                        ]
                    ),

                    # Graph container
                    html.Div(
                        id="variable-graph-container",
                        style={"display": "none"}
                    )
                ])
            ], className="shadow-sm")
        ]
    )
])


def parse_sample_id_for_day(sample_id):
    """
    Parse sample ID to extract day number and group.
    Patterns:
    - UP447 D10 -> day=10, group=UP447
    - UPFB0001 D05 -> day=5, group=UPFB0001
    - UP448 D9 -> day=9, group=UP448
    """
    parsed_info = {
        'day': None,
        'group': None
    }

    if not sample_id:
        return parsed_info

    sample_id_str = str(sample_id).strip().upper()

    # Extract day: D## or D### pattern
    day_match = re.search(r'D(\d+)', sample_id_str)
    if day_match:
        parsed_info['day'] = int(day_match.group(1))

    # Extract base identifier (UP### or UPFB####)
    # First try UPFB pattern
    upfb_match = re.match(r'(UPFB\d+)', sample_id_str)
    if upfb_match:
        parsed_info['group'] = upfb_match.group(1)
    else:
        # Try UP pattern (with or without space)
        up_match = re.match(r'(UP\d+)', sample_id_str)
        if up_match:
            parsed_info['group'] = up_match.group(1)

    return parsed_info


def calculate_analytics(grouped_data):
    """
    Calculate analytics metrics for each group.

    Returns:
        List of dicts with analytics for each group
    """
    analytics_data = []

    for group, df in grouped_data.items():
        if df.empty or 'titer' not in df.columns or 'day' not in df.columns:
            continue

        # Sort by day
        df_sorted = df.sort_values('day')

        # Remove NaN titers
        df_clean = df_sorted.dropna(subset=['titer'])

        if df_clean.empty:
            continue

        # Basic metrics
        sample_count = len(df_clean)
        final_titer = df_clean.iloc[-1]['titer']  # Last measurement
        max_titer = df_clean['titer'].max()
        day_of_max = df_clean.loc[df_clean['titer'].idxmax(), 'day']

        # Growth rates
        growth_rate_early = None
        growth_rate_late = None

        # Early growth (D9-D12 or closest available)
        early_df = df_clean[(df_clean['day'] >= 9) & (df_clean['day'] <= 12)]
        if len(early_df) >= 2:
            early_sorted = early_df.sort_values('day')
            day_diff = early_sorted.iloc[-1]['day'] - early_sorted.iloc[0]['day']
            if day_diff > 0:
                titer_diff = early_sorted.iloc[-1]['titer'] - early_sorted.iloc[0]['titer']
                growth_rate_early = titer_diff / day_diff

        # Late growth (D12-D15 or closest available)
        late_df = df_clean[(df_clean['day'] >= 12) & (df_clean['day'] <= 15)]
        if len(late_df) >= 2:
            late_sorted = late_df.sort_values('day')
            day_diff = late_sorted.iloc[-1]['day'] - late_sorted.iloc[0]['day']
            if day_diff > 0:
                titer_diff = late_sorted.iloc[-1]['titer'] - late_sorted.iloc[0]['titer']
                growth_rate_late = titer_diff / day_diff

        # Average productivity (total titer / total days)
        max_day = df_clean['day'].max()
        avg_productivity = max_titer / max_day if max_day > 0 else None

        analytics_data.append({
            'group': group,
            'sample_count': sample_count,
            'final_titer': round(final_titer, 3) if final_titer else None,
            'max_titer': round(max_titer, 3) if max_titer else None,
            'day_of_max': int(day_of_max) if day_of_max else None,
            'growth_rate_early': round(growth_rate_early, 3) if growth_rate_early else None,
            'growth_rate_late': round(growth_rate_late, 3) if growth_rate_late else None,
            'avg_productivity': round(avg_productivity, 3) if avg_productivity else None
        })

    return analytics_data


# Parse URL parameters
@app.callback(
    [Output("url-params", "data"),
     Output("embedded-mode", "data")],
    Input("url", "search"),
    prevent_initial_call=False
)
def parse_url_params(search):
    if not search:
        return {}, False

    from urllib.parse import parse_qs
    params = parse_qs(search.lstrip("?"))

    url_params = {}
    embedded = params.get("embedded", ["false"])[0].lower() in ["true", "1", "yes"]
    url_params["embedded"] = embedded

    if "experiment" in params:
        url_params["experiment"] = params["experiment"][0]

    return url_params, embedded


# Toggle experiment modal
@app.callback(
    [Output("select-experiment-modal", "is_open"),
     Output("experiment-selection-table", "data"),
     Output("current-experiment-text", "children")],
    [Input("change-experiment-btn", "n_clicks"),
     Input("confirm-experiment-selection", "n_clicks"),
     Input("load-once", "n_intervals")],
    [State("select-experiment-modal", "is_open"),
     State("experiment-selection-table", "selected_rows"),
     State("experiment-selection-table", "data"),
     State("selected-experiment", "data")],
    prevent_initial_call=False
)
def toggle_select_modal(change_clicks, confirm_clicks, load_interval,
                        is_open, selected_rows, table_data, current_experiment):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # Fetch experiments
    experiments_query = USPExperiment.objects.all().order_by("-start_date")
    experiments_data = [{
        "experiment_id": exp.experiment_id,
        "name": exp.experiment_name,
        "start_date": exp.start_date.strftime("%Y-%m-%d") if exp.start_date else ""
    } for exp in experiments_query]

    # Current experiment badge
    if current_experiment:
        current_text = dbc.Badge(
            f"Experiment: {current_experiment}",
            color="info",
            className="fs-6 px-3 py-2"
        )
    else:
        current_text = dbc.Badge(
            "No experiment selected",
            color="secondary",
            className="fs-6 px-3 py-2"
        )

    # Handle modal
    if triggered_id == "change-experiment-btn":
        return not is_open, experiments_data, current_text
    elif triggered_id == "confirm-experiment-selection" and selected_rows and table_data:
        return False, experiments_data, current_text

    return is_open, experiments_data, current_text


# Update selected experiment
@app.callback(
    Output("selected-experiment", "data"),
    [Input("confirm-experiment-selection", "n_clicks"),
     Input("url-params", "data")],
    [State("experiment-selection-table", "selected_rows"),
     State("experiment-selection-table", "data")],
    prevent_initial_call=False
)
def update_selected_experiment(confirm_clicks, url_params, selected_rows, table_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return None

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "url-params" and "experiment" in url_params:
        return url_params["experiment"]
    elif triggered_id == "confirm-experiment-selection" and selected_rows and table_data:
        return table_data[selected_rows[0]]["experiment_id"]

    return None


def get_titer_data_for_experiment(experiment_id):
    """
    Fetch titer data for samples related to a specific USP experiment.
    Returns grouped data.
    """
    # Query all titer results with UP pattern
    # For now, get all UP samples - in future, link to experiment metadata
    titer_results = LimsTiterResult.objects.select_related('sample_id').filter(
        sample_id__sample_id__istartswith='UP'
    ).values(
        'sample_id__sample_id',
        'titer',
        'qc_pass',
        'sample_id__sample_date',
        'sample_id__project_id',
        'sample_id__description'
    )

    data_list = []
    for result in titer_results:
        sample_id = result['sample_id__sample_id']
        parsed = parse_sample_id_for_day(sample_id)

        if parsed['day'] is not None and parsed['group'] is not None:
            data_list.append({
                'sample_id': sample_id,
                'day': parsed['day'],
                'titer': result['titer'],
                'qc_pass': result['qc_pass'],
                'sample_date': result['sample_id__sample_date'],
                'project_id': result['sample_id__project_id'],
                'description': result['sample_id__description'],
                'group': parsed['group']
            })

    df = pd.DataFrame(data_list)

    if df.empty:
        return {}

    # Sort by group and day
    df_sorted = df.sort_values(by=["group", "day"], ascending=[True, True])

    # Group by sample group (UP### or UPFB####)
    grouped_data = {}
    for group in df_sorted["group"].unique():
        group_df = df_sorted[df_sorted["group"] == group].copy()
        if not group_df.empty:
            grouped_data[group] = group_df

    return grouped_data


# Toggle between tabs
@app.callback(
    [Output("summary-container", "style"),
     Output("analytics-container", "style"),
     Output("variable-graph-container", "style")],
    Input("variable-tabs", "active_tab")
)
def toggle_view(active_tab):
    if active_tab == "summary":
        return {"display": "block"}, {"display": "none"}, {"display": "none"}
    elif active_tab == "analytics":
        return {"display": "none"}, {"display": "block"}, {"display": "none"}
    elif active_tab == "plots":
        return {"display": "none"}, {"display": "none"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}, {"display": "none"}


# Update plots
@app.callback(
    Output("variable-graph-container", "children"),
    [Input("selected-experiment", "data"),
     Input("variable-tabs", "active_tab")],
    prevent_initial_call=True
)
def update_graph(selected_experiment, active_tab):
    """Updates the titer vs time graph."""

    if active_tab != 'plots':
        return None

    if not selected_experiment:
        return "⚠️ No experiment selected."

    # Get titer data
    grouped_data = get_titer_data_for_experiment(selected_experiment)

    if not grouped_data:
        return dbc.Alert(
            "⚠️ No titer data available for this experiment.",
            color="warning"
        )

    # Create plot
    fig = go.Figure()
    colors = px.colors.qualitative.Set1

    for idx, (group, df) in enumerate(grouped_data.items()):
        if df.empty or 'titer' not in df.columns:
            continue

        df_sorted = df.sort_values("day")
        df_sorted = df_sorted.dropna(subset=['titer'])

        if df_sorted.empty:
            continue

        # Add trace
        fig.add_trace(go.Scatter(
            x=df_sorted["day"],
            y=df_sorted["titer"],
            mode="lines+markers",
            name=group,
            line=dict(color=colors[idx % len(colors)], width=3),
            marker=dict(size=10),
            hovertemplate=f"{group}<br>" +
                          "Day: %{x}<br>" +
                          "Titer: %{y:.3f} g/L<br>" +
                          "<extra></extra>"
        ))

        # Add annotation for max titer
        max_idx = df_sorted['titer'].idxmax()
        max_row = df_sorted.loc[max_idx]
        fig.add_annotation(
            x=max_row['day'],
            y=max_row['titer'],
            text=f"Max: {max_row['titer']:.2f}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=colors[idx % len(colors)],
            ax=20,
            ay=-30,
            font=dict(size=10, color=colors[idx % len(colors)])
        )

    # Update layout
    fig.update_layout(
        title={
            'text': f"Titer vs Process Day - {selected_experiment}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Process Day",
        yaxis_title="Titer (g/L)",
        height=700,
        hovermode="x unified",
        template="plotly_white",
        plot_bgcolor='rgba(245, 245, 250, 0.5)',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255, 255, 255, 0.8)"
        ),
        font=dict(family="Arial, sans-serif", size=14),
        margin=dict(l=120, r=220, t=140, b=120)
    )

    fig.update_xaxes(gridcolor='rgba(128, 128, 128, 0.2)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(128, 128, 128, 0.2)', showgrid=True)

    return html.Div([
        dcc.Graph(
            figure=fig,
            style={"width": "100%", "height": "700px"},
            config={"displayModeBar": True, "responsive": True}
        )
    ], style={"width": "100%"})


# Update sample group dropdown
@app.callback(
    [Output("subset-dropdown", "options"),
     Output("subset-dropdown", "value")],
    Input("selected-experiment", "data")
)
def update_sample_group_dropdown(selected_experiment):
    """Populate dropdown with available sample groups."""
    if not selected_experiment:
        return [], None

    grouped_data = get_titer_data_for_experiment(selected_experiment)

    if not grouped_data:
        return [], None

    groups = sorted(grouped_data.keys())
    options = [{"label": group, "value": group} for group in groups]

    return options, (groups[0] if groups else None)


# Update summary table
@app.callback(
    Output("subset-table", "data"),
    [Input("subset-dropdown", "value"),
     Input("selected-experiment", "data")]
)
def update_summary_table(selected_group, selected_experiment):
    """Populate table with titer data for selected group."""
    if not selected_experiment or not selected_group:
        return []

    grouped_data = get_titer_data_for_experiment(selected_experiment)

    if selected_group not in grouped_data:
        return []

    df = grouped_data[selected_group].sort_values("day")

    data = []
    for _, row in df.iterrows():
        data.append({
            "sample_id": row['sample_id'],
            "day": row['day'],
            "titer": round(row['titer'], 3) if pd.notna(row['titer']) else None,
            "sample_date": row['sample_date'].strftime("%Y-%m-%d") if pd.notna(row['sample_date']) else "",
            "qc_pass": "Pass" if row['qc_pass'] else "Fail"
        })

    return data


# Update analytics table and charts
@app.callback(
    [Output("analytics-table", "data"),
     Output("analytics-charts", "children")],
    Input("selected-experiment", "data")
)
def update_analytics(selected_experiment):
    """Calculate and display analytics."""
    if not selected_experiment:
        return [], None

    grouped_data = get_titer_data_for_experiment(selected_experiment)

    if not grouped_data:
        return [], dbc.Alert("No data available for analytics", color="warning")

    # Calculate analytics
    analytics_data = calculate_analytics(grouped_data)

    if not analytics_data:
        return [], dbc.Alert("Could not calculate analytics", color="warning")

    # Create comparison charts
    analytics_df = pd.DataFrame(analytics_data)

    # Final titer comparison
    fig_final = go.Figure()
    fig_final.add_trace(go.Bar(
        x=analytics_df['group'],
        y=analytics_df['final_titer'],
        name='Final Titer',
        marker_color='rgb(55, 83, 109)',
        text=analytics_df['final_titer'].round(2),
        textposition='auto'
    ))

    fig_final.update_layout(
        title="Final Titer Comparison",
        xaxis_title="Group",
        yaxis_title="Titer (g/L)",
        height=400,
        template="plotly_white"
    )

    # Growth rate comparison
    fig_growth = go.Figure()
    fig_growth.add_trace(go.Bar(
        x=analytics_df['group'],
        y=analytics_df['growth_rate_early'],
        name='D9-D12',
        marker_color='rgb(26, 118, 255)'
    ))
    fig_growth.add_trace(go.Bar(
        x=analytics_df['group'],
        y=analytics_df['growth_rate_late'],
        name='D12-D15',
        marker_color='rgb(50, 171, 96)'
    ))

    fig_growth.update_layout(
        title="Growth Rate Comparison",
        xaxis_title="Group",
        yaxis_title="Growth Rate (g/L/day)",
        height=400,
        template="plotly_white",
        barmode='group'
    )

    charts = dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig_final)
        ], md=6),
        dbc.Col([
            dcc.Graph(figure=fig_growth)
        ], md=6)
    ])

    return analytics_data, charts
