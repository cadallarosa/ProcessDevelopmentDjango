import os
import re
import shutil
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from dash import dcc, html
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash
from django.conf import settings
from django.db import transaction
from plotly_integration.models import NovaFlex2

# Get database name from settings
DB_NAME = settings.DATABASES['default']['NAME']

# Initialize the Dash app
app = DjangoDash('NovaFlex2DatabaseManagerApp')

# Define the layout
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f8f9fa",
        "padding": "20px",
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "center",
        "alignItems": "center",
    },
    children=[
        html.Div(
            style={
                "width": "70%",
                "backgroundColor": "white",
                "borderRadius": "10px",
                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
                "padding": "40px",
                "textAlign": "center",
            },
            children=[
                html.H1(
                    "Nova Flex 2 Database Manager",
                    style={"color": "#343a40", "marginBottom": "10px"}
                ),
                html.P(
                    "Import Nova Flex 2 data files from a specified folder",
                    style={"color": "#6c757d", "fontSize": "18px", "marginBottom": "30px"}
                ),
                html.Div(
                    [
                        dcc.Input(
                            id="folder-path-nova",
                            type="text",
                            placeholder="Enter folder path (e.g., C:/Data/NovaFlex2)",
                            style={
                                "width": "80%",
                                "padding": "12px",
                                "fontSize": "16px",
                                "border": "1px solid #ced4da",
                                "borderRadius": "5px",
                                "marginBottom": "20px",
                            },
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "🚀 Import Files",
                                    id="import-button-nova",
                                    n_clicks=0,
                                    style={
                                        "backgroundColor": "#28a745",
                                        "color": "white",
                                        "padding": "12px 30px",
                                        "fontSize": "16px",
                                        "border": "none",
                                        "borderRadius": "5px",
                                        "cursor": "pointer",
                                        "marginTop": "10px",
                                    },
                                ),
                            ]
                        ),
                    ]
                ),
                html.Div(
                    id="loading-container-nova",
                    style={"marginTop": "20px"},
                    children=[
                        dcc.Loading(
                            id="loading-nova",
                            type="circle",
                            children=[
                                html.Div(id="output-message-nova", style={"marginTop": "20px", "fontSize": "16px"}),
                                html.Div(id="file-status-nova", style={"marginTop": "10px", "fontSize": "14px"}),
                                html.Div(id="progress-bar-nova", style={"marginTop": "20px"}),
                            ],
                        ),
                    ],
                ),
                html.Hr(style={"margin": "30px 0"}),
                html.P(
                    f"Database: {DB_NAME}",
                    style={"color": "#6c757d", "fontSize": "14px"}
                ),
            ],
        ),
    ],
)


# Nova Flex 2 Data Processing Functions
def parse_sample_id(sample_id):
    """Parse sample ID to extract experiment, day, reactor info, and special markers"""
    patterns = {
        'experiment': r'SI\d+P\d+',
        'day': r'D(\d+)',
        'reactor_type': r'(BR|STR)',
        'reactor_number': r'(?:BR|STR)(\d+)',
        'special': r'(UP|CLD)'
    }

    parsed_info = {
        'experiment': None,
        'day': None,
        'reactor_type': None,
        'reactor_number': None,
        'special': None,
        'sample_type': 3  # Default to uncategorized
    }

    if pd.isna(sample_id) or not sample_id:
        return parsed_info

    sample_id_str = str(sample_id).strip()

    # Extract experiment
    exp_match = re.search(patterns['experiment'], sample_id_str)
    if exp_match:
        parsed_info['experiment'] = exp_match.group(0)

    # Extract day
    day_match = re.search(patterns['day'], sample_id_str)
    if day_match:
        parsed_info['day'] = int(day_match.group(1))

    # Extract reactor type
    reactor_type_match = re.search(patterns['reactor_type'], sample_id_str)
    if reactor_type_match:
        parsed_info['reactor_type'] = reactor_type_match.group(0)

    # Extract reactor number
    reactor_num_match = re.search(patterns['reactor_number'], sample_id_str)
    if reactor_num_match:
        parsed_info['reactor_number'] = int(reactor_num_match.group(1))

    # Extract special markers (UP/CLD)
    special_match = re.search(patterns['special'], sample_id_str)
    if special_match:
        parsed_info['special'] = special_match.group(0)
        if parsed_info['special'] == 'UP':
            parsed_info['sample_type'] = 1
        elif parsed_info['special'] == 'CLD':
            parsed_info['sample_type'] = 2

    return parsed_info


def clean_numeric(value):
    """Clean numeric values, handling NaN and non-numeric strings"""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def process_excel_file(file_path):
    """Process Nova Flex 2 Excel file and return DataFrame with parsed data"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path, engine='xlrd' if file_path.endswith('.xls') else None)

        # Clean column names
        df.columns = df.columns.str.strip()

        # Expected columns mapping - handle both old and new formats
        if 'Date & Time' in df.columns:
            # New Nova analyzer format
            column_mapping = {
                'Date & Time': 'date_time',
                'Sample ID': 'sample_id',
                'Gln': 'gln',
                'Glu': 'glu',
                'Gluc': 'gluc',
                'Lac': 'lac',
                'NH4+': 'nh4',
                'pH': 'pH',
                'PO2': 'po2',
                'PCO2': 'pco2',
                'Osm': 'osm'
            }
        else:
            # Original format
            column_mapping = {
                'Date/Time': 'date_time',
                'Sample ID': 'sample_id',
                'Gln (mM)': 'gln',
                'Glu (g/L)': 'glu',
                'Gluc (g/L)': 'gluc',
                'Lac (g/L)': 'lac',
                'NH4+ (mM)': 'nh4',
                'pH': 'pH',
                'pO2 (%)': 'po2',
                'pCO2 (%)': 'pco2',
                'Osm (mOsm/kg)': 'osm'
            }

        # Rename columns
        df.rename(columns=column_mapping, inplace=True)

        # Keep only relevant columns
        relevant_cols = list(column_mapping.values())
        df = df[[col for col in relevant_cols if col in df.columns]]

        # Convert string values to numeric for new format
        numeric_columns = ['gln', 'glu', 'gluc', 'lac', 'nh4', 'pH', 'po2', 'pco2', 'osm']
        for col in numeric_columns:
            if col in df.columns:
                # Replace 'NS' and other non-numeric values with NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Convert date_time to datetime
        if 'date_time' in df.columns:
            df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')

        return df

    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")


def process_csv_file(file_path):
    """Process Nova Flex 2 CSV file"""
    try:
        # Read CSV file
        df = pd.read_csv(file_path)

        # Clean column names
        df.columns = df.columns.str.strip()

        # Check which CSV format this is based on columns
        if 'Date & Time' in df.columns:
            # New Nova analyzer format (SampleResults format)
            column_mapping = {
                'Date & Time': 'date_time',
                'Sample ID': 'sample_id',
                'Gln': 'gln',
                'Glu': 'glu',
                'Gluc': 'gluc',
                'Lac': 'lac',
                'NH4+': 'nh4',
                'pH': 'pH',
                'PO2': 'po2',
                'PCO2': 'pco2',
                'Osm': 'osm'
            }
        elif 'Viable cells' in df.columns:
            # Cell viability CSV - skip for now
            return None
        else:
            # Original format
            column_mapping = {
                'Date/Time': 'date_time',
                'Sample ID': 'sample_id',
                'Gln (mM)': 'gln',
                'Glu (g/L)': 'glu',
                'Gluc (g/L)': 'gluc',
                'Lac (g/L)': 'lac',
                'NH4+ (mM)': 'nh4',
                'pH': 'pH',
                'pO2 (%)': 'po2',
                'pCO2 (%)': 'pco2',
                'Osm (mOsm/kg)': 'osm'
            }

        df.rename(columns=column_mapping, inplace=True)

        # Convert string values to numeric
        numeric_columns = ['gln', 'glu', 'gluc', 'lac', 'nh4', 'pH', 'po2', 'pco2', 'osm']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'date_time' in df.columns:
            df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')

        return df

    except Exception as e:
        raise Exception(f"Error processing CSV file: {str(e)}")


def process_dataframe_and_import(df, file_name):
    """Process dataframe and import to database"""
    records_created = 0
    records_updated = 0
    errors = []

    for _, row in df.iterrows():
        if pd.isna(row.get('sample_id', None)):
            continue

        # Parse sample ID
        parsed_info = parse_sample_id(row['sample_id'])

        # Prepare data for database
        data = {
            'date_time': row.get('date_time'),
            'sample_id': row.get('sample_id'),
            'sample_type': parsed_info['sample_type'],
            'gln': clean_numeric(row.get('gln')),
            'glu': clean_numeric(row.get('glu')),
            'gluc': clean_numeric(row.get('gluc')),
            'lac': clean_numeric(row.get('lac')),
            'nh4': clean_numeric(row.get('nh4')),
            'pH': clean_numeric(row.get('pH')),
            'po2': clean_numeric(row.get('po2')),
            'pco2': clean_numeric(row.get('pco2')),
            'osm': clean_numeric(row.get('osm')),
            'experiment': parsed_info['experiment'],
            'day': parsed_info['day'],
            'reactor_type': parsed_info['reactor_type'],
            'reactor_number': parsed_info['reactor_number'],
            'special': parsed_info['special']
        }

        # Skip if no valid date_time or sample_id
        if pd.isna(data['date_time']) or pd.isna(data['sample_id']):
            continue

        try:
            # Use update_or_create for handling duplicates
            obj, created = NovaFlex2.objects.update_or_create(
                date_time=data['date_time'],
                sample_id=data['sample_id'],
                defaults=data
            )

            if created:
                records_created += 1
            else:
                records_updated += 1

        except Exception as e:
            error_msg = f"Error in {file_name} - Sample ID {row.get('sample_id')}: {str(e)}"
            errors.append(error_msg)

    return records_created, records_updated, errors


def process_files(directory, imported_folder):
    """Process all Excel and CSV files in the directory"""
    # Get all files
    excel_files = list(Path(directory).glob('*.xls')) + list(Path(directory).glob('*.xlsx'))
    csv_files = list(Path(directory).glob('*.csv'))

    all_files = excel_files + csv_files
    total_files = len(all_files)

    if total_files == 0:
        return "No Excel or CSV files found in the specified folder.", "", 0

    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'total_records_created': 0,
        'total_records_updated': 0,
        'errors': []
    }

    # Process each file
    for idx, file_path in enumerate(all_files):
        file_name = file_path.name

        try:
            # Process based on file type
            if file_path.suffix in ['.xls', '.xlsx']:
                df = process_excel_file(str(file_path))
            else:  # CSV
                df = process_csv_file(str(file_path))

            if df is None or df.empty:
                continue

            # Import to database
            with transaction.atomic():
                records_created, records_updated, errors = process_dataframe_and_import(df, file_name)

            results['processed'] += 1
            results['successful'] += 1
            results['total_records_created'] += records_created
            results['total_records_updated'] += records_updated
            results['errors'].extend(errors)

            # Move file to imported folder
            shutil.move(str(file_path), os.path.join(imported_folder, file_name))

        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{file_name}: {str(e)}")

    return results


# Callback for import button
@app.callback(
    [Output("output-message-nova", "children"),
     Output("file-status-nova", "children"),
     Output("progress-bar-nova", "children")],
    [Input("import-button-nova", "n_clicks")],
    [State("folder-path-nova", "value")]
)
def import_files(n_clicks, folder_path):
    if n_clicks == 0 or not folder_path:
        return "", "", ""

    # Validate folder path
    if not os.path.isdir(folder_path):
        return f"Error: Folder '{folder_path}' does not exist.", "", ""

    # Create imported folder
    imported_folder = os.path.join(folder_path, "imported")
    os.makedirs(imported_folder, exist_ok=True)

    try:
        # Process files
        results = process_files(folder_path, imported_folder)

        if isinstance(results, tuple):
            # No files found
            return results[0], "", ""

        # Generate output message
        output_message = html.Div([
            html.H4("Import Complete!", style={"color": "#28a745"}),
            html.P(f"Files processed: {results['processed']}"),
            html.P(f"Successful: {results['successful']}"),
            html.P(f"Failed: {results['failed']}"),
            html.Hr(),
            html.P(f"Records created: {results['total_records_created']}"),
            html.P(f"Records updated: {results['total_records_updated']}")
        ])

        # Generate file status
        if results['errors']:
            error_list = html.Div([
                html.H5("Errors:", style={"color": "#dc3545"}),
                html.Ul([html.Li(err) for err in results['errors'][:10]])
            ])
            if len(results['errors']) > 10:
                error_list.children.append(html.P(f"... and {len(results['errors']) - 10} more errors"))
        else:
            error_list = ""

        # Progress bar (100% when complete)
        progress_bar = html.Div(
            style={
                "width": "100%",
                "backgroundColor": "#e9ecef",
                "borderRadius": "5px",
                "overflow": "hidden"
            },
            children=[
                html.Div(
                    style={
                        "width": "100%",
                        "height": "20px",
                        "backgroundColor": "#28a745",
                        "transition": "width 0.5s ease-in-out"
                    }
                )
            ]
        )

        return output_message, error_list, progress_bar

    except Exception as e:
        return f"An error occurred: {str(e)}", "", ""