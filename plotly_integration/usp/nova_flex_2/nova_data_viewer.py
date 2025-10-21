import pandas as pd
from dash import dash_table, html, dcc, Input, Output
from django_plotly_dash import DjangoDash
from plotly_integration.models import NovaFlex2
import dash_bootstrap_components as dbc

# Initialize the Dash app
app = DjangoDash('USPNovaFlex2DataViewerApp', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Nova Flex 2 Data Viewer", className="text-center mb-4"),
            html.Hr()
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Raw Data Results", className="mb-0")
                        ], md=6),
                        dbc.Col([
                            dbc.Button(
                                "🔄 Refresh Data",
                                id="refresh-button",
                                color="primary",
                                size="sm",
                                className="float-end"
                            )
                        ], md=6)
                    ])
                ]),
                dbc.CardBody([
                    # Filters row
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Filter by Experiment:"),
                            dcc.Dropdown(
                                id="experiment-filter",
                                placeholder="All Experiments",
                                multi=True,
                                style={"width": "100%"}
                            )
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Filter by Sample Type:"),
                            dcc.Dropdown(
                                id="sample-type-filter",
                                options=[
                                    {"label": "All Types", "value": "all"},
                                    {"label": "UP", "value": "1"},
                                    {"label": "CLD", "value": "2"},
                                    {"label": "Uncategorized", "value": "3"}
                                ],
                                value="all",
                                style={"width": "100%"}
                            )
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Date Range:"),
                            dcc.DatePickerRange(
                                id="date-range-filter",
                                display_format="YYYY-MM-DD",
                                style={"width": "100%"}
                            )
                        ], md=4),
                        dbc.Col([
                            dbc.Label("Records per page:"),
                            dcc.Dropdown(
                                id="page-size-dropdown",
                                options=[
                                    {"label": "25", "value": 25},
                                    {"label": "50", "value": 50},
                                    {"label": "100", "value": 100},
                                    {"label": "200", "value": 200}
                                ],
                                value=50,
                                clearable=False,
                                style={"width": "100%"}
                            )
                        ], md=2)
                    ], className="mb-3"),

                    # Summary stats
                    html.Div(id="summary-stats", className="mb-3"),

                    # Data table
                    dcc.Loading(
                        id="loading-table",
                        type="default",
                        children=[
                            html.Div(id="data-table-container")
                        ]
                    ),

                    # Export button
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="export-container", className="mt-3")
                        ])
                    ])
                ])
            ])
        ])
    ])
], fluid=True, className="p-4")


def get_filtered_data(experiment_filter, sample_type_filter, start_date, end_date):
    """Get filtered data from database"""
    # Start with all records
    queryset = NovaFlex2.objects.all()

    # Apply filters
    if experiment_filter and len(experiment_filter) > 0:
        queryset = queryset.filter(experiment__in=experiment_filter)

    if sample_type_filter != "all":
        queryset = queryset.filter(sample_type=int(sample_type_filter))

    if start_date:
        queryset = queryset.filter(date_time__gte=start_date)

    if end_date:
        queryset = queryset.filter(date_time__lte=end_date)

    # Order by date_time descending (newest first)
    queryset = queryset.order_by('-date_time')

    # Convert to dataframe
    data = list(queryset.values())
    if data:
        df = pd.DataFrame(data)
        # Format date_time for display
        df['date_time'] = pd.to_datetime(df['date_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        # Map sample_type to readable values
        sample_type_map = {1: 'UP', 2: 'CLD', 3: 'Uncategorized', None: ''}
        df['sample_type_display'] = df['sample_type'].map(sample_type_map).fillna('')
        return df
    else:
        return pd.DataFrame()


# Callback to populate experiment dropdown
@app.callback(
    Output("experiment-filter", "options"),
    Input("refresh-button", "n_clicks")
)
def update_experiment_options(n_clicks):
    # Get unique experiments
    experiments = NovaFlex2.objects.values_list('experiment', flat=True).distinct()
    experiments = [exp for exp in experiments if exp is not None]
    experiments.sort()

    return [{"label": exp, "value": exp} for exp in experiments]


# Main callback to update table and stats
@app.callback(
    [Output("data-table-container", "children"),
     Output("summary-stats", "children"),
     Output("export-container", "children")],
    [Input("refresh-button", "n_clicks"),
     Input("experiment-filter", "value"),
     Input("sample-type-filter", "value"),
     Input("date-range-filter", "start_date"),
     Input("date-range-filter", "end_date"),
     Input("page-size-dropdown", "value")]
)
def update_table(n_clicks, experiment_filter, sample_type_filter, start_date, end_date, page_size):
    # Get filtered data
    df = get_filtered_data(experiment_filter, sample_type_filter, start_date, end_date)

    if df.empty:
        return (
            html.Div("No data found with the selected filters.", className="text-center text-muted p-5"),
            html.Div(),
            html.Div()
        )

    # Create summary statistics
    total_records = len(df)
    unique_experiments = df['experiment'].nunique()
    date_range = f"{df['date_time'].min()} to {df['date_time'].max()}"

    summary_stats = dbc.Alert([
        dbc.Row([
            dbc.Col([
                html.Strong("Total Records: "),
                html.Span(f"{total_records:,}")
            ], md=3),
            dbc.Col([
                html.Strong("Unique Experiments: "),
                html.Span(str(unique_experiments))
            ], md=3),
            dbc.Col([
                html.Strong("Date Range: "),
                html.Span(date_range)
            ], md=6)
        ])
    ], color="info", className="py-2")

    # Define columns for display
    columns_config = [
        {"name": "ID", "id": "id", "type": "numeric"},
        {"name": "Date/Time", "id": "date_time", "type": "datetime"},
        {"name": "Sample ID", "id": "sample_id", "type": "text"},
        {"name": "Type", "id": "sample_type_display", "type": "text"},
        {"name": "Experiment", "id": "experiment", "type": "text"},
        {"name": "Day", "id": "day", "type": "numeric"},
        {"name": "Reactor", "id": "reactor_type", "type": "text"},
        {"name": "Reactor #", "id": "reactor_number", "type": "numeric"},
        {"name": "Special", "id": "special", "type": "text"},
        {"name": "Gln", "id": "gln", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "Glu", "id": "glu", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "Gluc", "id": "gluc", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "Lac", "id": "lac", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "NH4", "id": "nh4", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "pH", "id": "pH", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "pO2", "id": "po2", "type": "numeric", "format": {"specifier": ".1f"}},
        {"name": "pCO2", "id": "pco2", "type": "numeric", "format": {"specifier": ".1f"}},
        {"name": "Osm", "id": "osm", "type": "numeric", "format": {"specifier": ".0f"}}
    ]

    # Create data table
    data_table = dash_table.DataTable(
        id='nova-data-table',
        columns=columns_config,
        data=df.to_dict('records'),

        # Styling
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'whiteSpace': 'normal',
            'height': 'auto',
            'minWidth': '80px'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_data={
            'backgroundColor': 'white',
            'color': 'black',
            'border': '1px solid grey'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },
            {
                'if': {'column_id': 'sample_type_display', 'filter_query': '{sample_type_display} = "UP"'},
                'backgroundColor': '#d4edda',
                'color': 'black',
            },
            {
                'if': {'column_id': 'sample_type_display', 'filter_query': '{sample_type_display} = "CLD"'},
                'backgroundColor': '#cce5ff',
                'color': 'black',
            }
        ],

        # Features
        page_size=page_size,
        page_action='native',
        sort_action='native',
        filter_action='native',
        export_format='csv',
        export_headers='display',

        # Column widths
        style_cell_conditional=[
            {'if': {'column_id': 'id'}, 'width': '60px'},
            {'if': {'column_id': 'date_time'}, 'width': '150px'},
            {'if': {'column_id': 'sample_id'}, 'width': '200px'},
            {'if': {'column_id': 'sample_type_display'}, 'width': '80px'},
            {'if': {'column_id': 'experiment'}, 'width': '100px'},
            {'if': {'column_id': 'day'}, 'width': '60px'},
            {'if': {'column_id': 'reactor_type'}, 'width': '80px'},
            {'if': {'column_id': 'reactor_number'}, 'width': '80px'},
            {'if': {'column_id': 'special'}, 'width': '80px'},
        ]
    )

    # Export button
    export_button = dbc.Button(
        "📥 Export All Data to CSV",
        id="export-all-button",
        color="success",
        size="sm",
        href=f"data:text/csv;charset=utf-8,{df.to_csv(index=False, encoding='utf-8')}",
        download=f"nova_flex2_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        external_link=True
    )

    return data_table, summary_stats, export_button