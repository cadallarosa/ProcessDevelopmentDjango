import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import pandas as pd
import base64
import io
import xlrd
from django_plotly_dash import DjangoDash
from datetime import datetime
import plotly.graph_objects as go
import numpy as np

# Initialize the Dash app
app = DjangoDash('OctetImportApp')


# Function to parse octet data with proper column mapping
def parse_octet_data(file_buffer):
    """
    Parse octet data from Excel file with proper column handling
    """
    # First, try to read the Excel file and check available sheets
    excel_file = pd.ExcelFile(file_buffer)

    # Look for Result sheet (case-insensitive)
    sheet_names = excel_file.sheet_names
    result_sheet = None

    for sheet in sheet_names:
        if 'result' in sheet.lower():
            result_sheet = sheet
            break

    # If no Result sheet found, use the first sheet
    if result_sheet is None:
        result_sheet = sheet_names[0]

    # Read from the Result sheet
    df = pd.read_excel(file_buffer, sheet_name=result_sheet)

    # Define expected octet columns
    octet_columns = [
        'Index', 'Flip Alert', 'Plate', 'Sensor', 'Sample',
        'Sample ID', 'Type', 'Binding Rate', 'Known Conc. (µg/ml)',
        'Well Conc.', 'Dilution Factor', 'Calc Conc.', 'Residual(%)',
        'R2', 'Information', 'Sensor Type', 'Replicate Group',
        'BR Avg', 'BR SD', 'BR CV', 'Conc. Avg', 'Conc. SD', 'Conc. CV',
        'Lot Number'
    ]

    # Check if we need to reformat the data
    if len(df.columns) < len(octet_columns):
        # Try to parse the data manually if columns don't match
        file_buffer.seek(0)
        raw_df = pd.read_excel(file_buffer, sheet_name=result_sheet, header=None)

        # Find the header row (contains "Index" or "Binding Rate")
        header_row = 0
        for idx, row in raw_df.iterrows():
            if 'Index' in str(row.values) or 'Binding Rate' in str(row.values):
                header_row = idx
                break

        # Reconstruct the dataframe with proper columns
        if header_row > 0:
            df = pd.read_excel(file_buffer, sheet_name=result_sheet, skiprows=header_row)

    # Clean up column names
    df.columns = df.columns.str.strip()

    # Handle special cases in octet data
    # Convert scientific notation
    numeric_columns = ['Binding Rate', 'Well Conc.', 'Calc Conc.', 'R2',
                       'BR Avg', 'BR SD', 'BR CV', 'Conc. Avg', 'Conc. SD', 'Conc. CV']

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Handle 'Too High' and 'Too Low' values
    if 'Well Conc.' in df.columns:
        df['Well Conc.'] = df['Well Conc.'].replace({'Too High': np.inf, 'Too Low': -np.inf})
    if 'Calc Conc.' in df.columns:
        df['Calc Conc.'] = df['Calc Conc.'].replace({'Too High': np.inf, 'Too Low': -np.inf})

    return df


# Define the app layout
app.layout = html.Div([
    html.Div([
        html.H1('OctetSync', style={'textAlign': 'center', 'marginBottom': '30px'}),

        # File upload section
        html.Div([
            html.H3('Step 1: Upload Excel File'),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px',
                    'cursor': 'pointer'
                },
                # Allow only xls/xlsx files
                accept='.xls,.xlsx'
            ),
            html.Div(id='output-data-upload'),
        ], style={'marginBottom': '30px'}),

        # Data table section
        html.Div([
            html.H3('Step 2: Review and Edit Data'),
            html.Div(id='output-data-table'),
        ], style={'marginBottom': '30px'}),

        # Action buttons
        html.Div([
            html.Button('Clear Data', id='clear-button', n_clicks=0,
                        style={'marginRight': '10px', 'padding': '10px 20px'}),
            html.Button('Import to Database', id='import-button', n_clicks=0,
                        style={'padding': '10px 20px', 'backgroundColor': '#4CAF50', 'color': 'white'}),
        ], id='action-buttons', style={'display': 'none', 'marginBottom': '30px'}),

        # Status messages
        html.Div(id='status-message', style={'marginTop': '20px'}),

        # Preview section
        html.Div(id='data-preview', style={'marginTop': '30px'})

    ], style={'maxWidth': '1200px', 'margin': 'auto', 'padding': '20px'})
])


# Callback for file upload and data table display
@app.callback(
    [Output('output-data-upload', 'children'),
     Output('output-data-table', 'children'),
     Output('action-buttons', 'style'),
     Output('data-preview', 'children')],
    [Input('upload-data', 'contents'),
     Input('clear-button', 'n_clicks')],
    [State('upload-data', 'filename'),
     State('upload-data', 'last_modified')]
)
def update_output(contents, clear_clicks, filename, date):
    ctx = dash.callback_context

    # Check if clear button was clicked
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'clear-button.n_clicks':
        return '', '', {'display': 'none'}, ''

    if contents is None:
        return '', '', {'display': 'none'}, ''

    # Parse the uploaded file
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        # Read Excel file
        if 'xls' in filename:
            # Check for sheet names
            excel_file = pd.ExcelFile(io.BytesIO(decoded))
            sheet_names = excel_file.sheet_names

            # Look for Result sheet
            result_sheet = None
            for sheet in sheet_names:
                if 'result' in sheet.lower():
                    result_sheet = sheet
                    break

            # Use Result sheet if found, otherwise use first sheet
            sheet_to_read = result_sheet if result_sheet else sheet_names[0]

            # Read from the appropriate sheet
            df = pd.read_excel(io.BytesIO(decoded), sheet_name=sheet_to_read)

            # Check if this is octet data by looking for specific columns
            octet_indicators = ['Binding Rate', 'Sensor Type', 'Well Conc.', 'Calc Conc.']
            is_octet_data = any(col in str(df.columns) for col in octet_indicators)

            # If we detect octet data structure, parse it with special handling
            if is_octet_data:
                # Re-read with octet parsing
                df = parse_octet_data(io.BytesIO(decoded))
        else:
            return html.Div([
                'Error: Please upload an Excel file (.xls or .xlsx)'
            ], style={'color': 'red'}), '', {'display': 'none'}, ''

        # Create upload confirmation message
        upload_message = html.Div([
            html.H5(f'File uploaded successfully: {filename}'),
            html.P(f'Sheet: {sheet_to_read}'),
            html.P(f'Shape: {df.shape[0]} rows × {df.shape[1]} columns'),
            html.Hr()
        ])

        # Create editable data table with conditional formatting
        data_table = dash_table.DataTable(
            id='editable-table',
            data=df.to_dict('records'),
            columns=[
                {"name": str(i), "id": str(i), "deletable": True, "renamable": True,
                 "editable": True, "type": "numeric" if df[i].dtype in ['float64', 'int64'] else "text"}
                for i in df.columns
            ],
            editable=True,
            row_deletable=True,
            filter_action="native",
            sort_action="native",
            page_action="native",
            page_current=0,
            page_size=20,
            style_cell={
                'textAlign': 'left',
                'minWidth': '100px',
                'maxWidth': '300px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
                # Highlight Too High/Too Low values
                {
                    'if': {
                        'filter_query': '{Well Conc.} = inf || {Calc Conc.} = inf',
                    },
                    'backgroundColor': '#ffcccc',
                },
                {
                    'if': {
                        'filter_query': '{Well Conc.} = -inf || {Calc Conc.} = -inf',
                    },
                    'backgroundColor': '#ccccff',
                }
            ],
            export_format='xlsx',
            export_headers='display',
            merge_duplicate_headers=True,
            tooltip_data=[
                {
                    column: {'value': str(value), 'type': 'markdown'}
                    for column, value in row.items()
                } for row in df.to_dict('records')
            ],
            tooltip_duration=None
        )

        # Create data preview with basic statistics and octet-specific info
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        preview_components = [
            html.H3('Data Preview'),
            html.Div([
                html.H4('Column Information:'),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th('Column Name'),
                            html.Th('Data Type'),
                            html.Th('Non-Null Count'),
                            html.Th('Unique Values')
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(col),
                            html.Td(str(df[col].dtype)),
                            html.Td(str(df[col].count())),
                            html.Td(str(df[col].nunique()))
                        ]) for col in df.columns
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse', 'border': '1px solid #ddd'})
            ])
        ]

        # Add octet-specific summary if relevant columns exist
        if 'Sensor Type' in df.columns:
            preview_components.append(html.Div([
                html.H4('Octet Data Summary:'),
                html.Ul([
                    html.Li(f"Sensor Types: {', '.join(df['Sensor Type'].unique())}"),
                    html.Li(f"Sample Types: {', '.join(df['Type'].unique() if 'Type' in df.columns else [])}"),
                    html.Li(f"Plates: {', '.join(df['Plate'].unique() if 'Plate' in df.columns else [])}"),
                    html.Li(f"Number of Samples: {df['Sample'].nunique() if 'Sample' in df.columns else 'N/A'}")
                ])
            ]))

        # Add statistics for numeric columns
        if numeric_cols:
            stats_data = []
            for col in numeric_cols:
                if col in df.columns and df[col].count() > 0:
                    stats_data.append({
                        'Column': col,
                        'Mean': f"{df[col].mean():.4f}" if df[col].dtype != 'object' else 'N/A',
                        'Std Dev': f"{df[col].std():.4f}" if df[col].dtype != 'object' else 'N/A',
                        'Min': f"{df[col].min():.4f}" if df[col].dtype != 'object' else 'N/A',
                        'Max': f"{df[col].max():.4f}" if df[col].dtype != 'object' else 'N/A'
                    })

            if stats_data:
                preview_components.append(html.Div([
                    html.H4('Numeric Column Statistics:'),
                    html.Table([
                        html.Thead([
                            html.Tr([html.Th(col) for col in ['Column', 'Mean', 'Std Dev', 'Min', 'Max']])
                        ]),
                        html.Tbody([
                            html.Tr([html.Td(stats[col]) for col in ['Column', 'Mean', 'Std Dev', 'Min', 'Max']])
                            for stats in stats_data
                        ])
                    ], style={'width': '100%', 'borderCollapse': 'collapse', 'border': '1px solid #ddd'})
                ]))

        preview = html.Div(preview_components)

        # Show action buttons
        button_style = {'display': 'block', 'marginBottom': '30px'}

        return upload_message, data_table, button_style, preview

    except Exception as e:
        error_message = html.Div([
            'There was an error processing this file: ',
            html.Br(),
            str(e)
        ], style={'color': 'red'})
        return error_message, '', {'display': 'none'}, ''


# Callback for import button
@app.callback(
    Output('status-message', 'children'),
    [Input('import-button', 'n_clicks')],
    [State('editable-table', 'data'),
     State('editable-table', 'columns')]
)
def import_to_database(n_clicks, data, columns):
    if n_clicks == 0 or data is None:
        return ''

    try:
        # Convert the edited data back to DataFrame
        df = pd.DataFrame(data)

        # Here you would add your database import logic
        # For now, we'll just show a success message

        success_message = html.Div([
            html.H4('Import Successful!', style={'color': 'green'}),
            html.P(f'Successfully prepared {len(df)} rows for import.'),
            html.P('Database import functionality would be implemented here.'),
            html.Hr(),
            html.H5('Data Summary:'),
            html.Ul([
                html.Li(f'Total Rows: {len(df)}'),
                html.Li(f'Total Columns: {len(df.columns)}'),
                html.Li(f'Columns: {", ".join(df.columns)}')
            ]),
            html.Hr(),
            html.P('Ready to import to database. Add your database connection here.',
                   style={'fontStyle': 'italic'})
        ], style={'backgroundColor': '#f0f9ff', 'padding': '20px', 'borderRadius': '5px'})

        return success_message

    except Exception as e:
        error_message = html.Div([
            html.H4('Import Failed', style={'color': 'red'}),
            html.P(f'Error: {str(e)}')
        ], style={'backgroundColor': '#fff0f0', 'padding': '20px', 'borderRadius': '5px'})

        return error_message