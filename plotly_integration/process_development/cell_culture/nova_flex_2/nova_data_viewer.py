import pandas as pd
from dash import dash_table, html, dcc, Input, Output
from django_plotly_dash import DjangoDash
from plotly_integration.models import NovaFlex2
import dash_bootstrap_components as dbc

# Initialize the Dash app
app = DjangoDash("NovaFlex2DataViewerApp", external_stylesheets=[dbc.themes.BOOTSTRAP])

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
                        ], md=8),
                        dbc.Col([
                            dbc.Label("Records per page:"),
                            dcc.Dropdown(
                                id="page-size-dropdown",
                                options=[
                                    {"label": "25", "value": 25},
                                    {"label": "50", "value": 50},
                                    {"label": "100", "value": 100},
                                    {"label": "200", "value": 200},
                                    {"label": "All", "value": 10000}
                                ],
                                value=100,
                                clearable=False,
                                style={"width": "100%"}
                            )
                        ], md=2),
                        dbc.Col([
                            dbc.Button(
                                "Refresh Data",
                                id="refresh-button",
                                color="primary",
                                size="sm",
                                className="float-end"
                            )
                        ], md=2)
                    ])
                ]),
                dbc.CardBody([
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


def get_all_data():
    """Get all data from database"""
    # Get all records ordered by date_time descending (newest first)
    queryset = NovaFlex2.objects.all().order_by("-date_time")

    # Convert to dataframe
    data = list(queryset.values())
    if data:
        df = pd.DataFrame(data)
        # Format date_time for display
        df["date_time"] = pd.to_datetime(df["date_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        return df
    else:
        return pd.DataFrame()


# Main callback to update table and stats
@app.callback(
    [Output("data-table-container", "children"),
     Output("summary-stats", "children"),
     Output("export-container", "children")],
    [Input("refresh-button", "n_clicks"),
     Input("page-size-dropdown", "value")]
)
def update_table(n_clicks, page_size):
    # Get all data
    df = get_all_data()

    if df.empty:
        return (
            html.Div("No data found.", className="text-center text-muted p-5"),
            html.Div(),
            html.Div()
        )

    # Create summary statistics
    total_records = len(df)
    date_range = f"{df['date_time'].min()} to {df['date_time'].max()}"

    summary_stats = dbc.Alert([
        dbc.Row([
            dbc.Col([
                html.Strong("Total Records: "),
                html.Span(f"{total_records:,}")
            ], md=4),
            dbc.Col([
                html.Strong("Date Range: "),
                html.Span(date_range)
            ], md=8)
        ])
    ], color="info", className="py-2")

    # Define columns for display (removed: Type, Experiment, Day, Reactor, Reactor #, Special)
    columns_config = [
        {"name": "ID", "id": "id", "type": "numeric"},
        {"name": "Date/Time", "id": "date_time", "type": "datetime"},
        {"name": "Sample ID", "id": "sample_id", "type": "text"},
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
        id="nova-data-table",
        columns=columns_config,
        data=df.to_dict("records"),

        # Styling
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "whiteSpace": "normal",
            "height": "auto",
            "minWidth": "80px"
        },
        style_header={
            "backgroundColor": "rgb(230, 230, 230)",
            "fontWeight": "bold",
            "textAlign": "center"
        },
        style_data={
            "backgroundColor": "white",
            "color": "black",
            "border": "1px solid grey"
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgb(248, 248, 248)"
            }
        ],

        # Features
        page_size=page_size,
        page_action="native",
        sort_action="native",
        filter_action="native",
        export_format="csv",
        export_headers="display",

        # Column widths
        style_cell_conditional=[
            {"if": {"column_id": "id"}, "width": "60px"},
            {"if": {"column_id": "date_time"}, "width": "150px"},
            {"if": {"column_id": "sample_id"}, "width": "250px"}
        ]
    )

    # Export button
    export_button = dbc.Button(
        "Export All Data to CSV",
        id="export-all-button",
        color="success",
        size="sm",
        href=f"data:text/csv;charset=utf-8,{df.to_csv(index=False, encoding='utf-8')}",
        download=f"nova_flex2_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        external_link=True
    )

    return data_table, summary_stats, export_button
