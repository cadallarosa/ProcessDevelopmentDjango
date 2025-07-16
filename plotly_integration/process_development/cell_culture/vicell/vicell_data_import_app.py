import base64
import io
import re
import pandas as pd
import numpy as np
from dash import dcc, html, Input, Output, State, dash_table
from django_plotly_dash import DjangoDash
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from plotly_integration.models import ViCellData
from datetime import datetime
from django.utils import timezone

# Initialize the Dash app
app = DjangoDash("ViCellDataImportApp")

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
        # Title
        html.H1("ViCell Data Import", style={"textAlign": "center", "color": "#0047b3", "marginBottom": "30px"}),

        # File Upload Section
        html.Div(
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0px 2px 5px rgba(0, 0, 0, 0.1)",
                "marginBottom": "20px"
            },
            children=[
                html.H3("Upload CSV or Excel File", style={"color": "#0047b3"}),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        '📁 Drag and Drop or ',
                        html.A('Select a File', style={"color": "#0047b3", "fontWeight": "bold"})
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px',
                        'cursor': 'pointer'
                    },
                    multiple=False
                ),
                html.Div(id='file-name', style={"marginTop": "10px", "fontWeight": "bold", "color": "green"})
            ]
        ),

        # Preview Data Table
        html.H3("Preview Data", style={"color": "#0047b3", "marginTop": "20px"}),
        dash_table.DataTable(
            id='data-preview',
            columns=[],  # Populated dynamically
            data=[],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#0047b3",
                "color": "white",
                "fontWeight": "bold"
            },
            style_cell={
                "padding": "10px",
                "textAlign": "center",
                "borderBottom": "1px solid #ccc"
            },
            style_data={"backgroundColor": "white", "color": "#333"}
        ),

        # Import and Clear Buttons
        html.Div(
            style={"textAlign": "center", "marginTop": "20px"},
            children=[
                html.Button(
                    "⬇️ Import Data to Database",
                    id="save-button",
                    n_clicks=0,
                    style={
                        "display": "none",
                        "backgroundColor": "#28a745",
                        "color": "white",
                        "padding": "10px 20px",
                        "border": "none",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "16px",
                        "marginRight": "10px"
                    }
                ),
                html.Button(
                    "🗑️ Clear All Data",
                    id="clear-button",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#dc3545",
                        "color": "white",
                        "padding": "10px 20px",
                        "border": "none",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "16px"
                    }
                )
            ]
        ),

        # Confirmation Dialog
        dcc.ConfirmDialog(
            id='confirm-clear',
            message='Are you sure you want to delete all ViCell data? This action cannot be undone.',
        ),

        # Import Status
        html.Div(
            id='save-status',
            style={
                "textAlign": "center",
                "marginTop": "20px",
                "fontSize": "18px",
                "fontWeight": "bold"
            }
        )
    ]
)


# Function to parse and clean uploaded CSV file
def parse_csv_contents(contents, filename):
    """Parse CSV file uploaded through the browser"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    # Read CSV file
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    # The CSV column mapping based on the document info
    column_mapping = {
        "Sample ID": "sample_id",
        "Analysis date/time": "date_time",
        "Cell count": "cell_count",
        "Viable cells": "viable_cells",
        "Total (x10^6) cells/mL": "total_cells_per_ml",
        "Viable (x10^6) cells/mL": "viable_cells_per_ml",
        "Viability (%)": "viability",
        "Average diameter (µm)": "average_diameter",
        "Average viable diameter (µm)": "average_viable_diameter",
        "Average circularity": "average_circularity",
        "Average viable circularity": "average_viable_circularity"
    }

    # Select only the columns we need
    relevant_columns = list(column_mapping.keys())
    available_columns = [col for col in relevant_columns if col in df.columns]
    df_cleaned = df[available_columns].copy()

    # Rename columns to match Django model fields
    df_cleaned.rename(columns=column_mapping, inplace=True)

    # Convert date column to datetime with timezone awareness
    df_cleaned["date_time"] = pd.to_datetime(df_cleaned["date_time"], errors="coerce")

    # Make datetime timezone-aware (Django requires this when USE_TZ=True)
    from django.utils import timezone
    df_cleaned["date_time"] = df_cleaned["date_time"].apply(
        lambda x: timezone.make_aware(x, timezone.get_default_timezone()) if pd.notna(x) and x.tzinfo is None else x
    )

    # Ensure numeric columns are properly converted
    numeric_columns = [
        "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
        "viability", "average_diameter", "average_viable_diameter",
        "average_circularity", "average_viable_circularity"
    ]
    for col in numeric_columns:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")

    # Assign sample_type based on predefined categories
    def assign_sample_type(sample_id):
        if isinstance(sample_id, str):
            if sample_id.startswith("E"):
                return 1  # UP
            elif sample_id.startswith("S"):
                return 2  # CLD
        return 3  # Uncategorized

    df_cleaned["sample_type"] = df_cleaned["sample_id"].apply(assign_sample_type)

    return df_cleaned


# Function to parse and clean uploaded Excel file
def parse_excel_contents(contents, filename):
    """Parse Excel file uploaded through the browser"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    file_path = default_storage.save(f"uploads/{filename}", ContentFile(decoded))

    # Read the first sheet of Excel file
    xls = pd.ExcelFile(default_storage.path(file_path))
    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

    # Remove first row if it contains units
    df_cleaned = df.iloc[0:].reset_index(drop=True)

    # Select relevant columns for database import
    relevant_columns = [
        "Analysis date/time", "Sample ID", "Cell count", "Viable cells",
        "Total (x10^6) cells/mL", "Viable (x10^6) cells/mL", "Viability (%)",
        "Average diameter (µm)", "Average viable diameter (µm)",
        "Average circularity", "Average viable circularity"
    ]

    available_columns = [col for col in relevant_columns if col in df_cleaned.columns]
    df_cleaned = df_cleaned[available_columns]

    # Rename columns to match Django model fields
    df_cleaned.rename(columns={
        "Analysis date/time": "date_time",
        "Sample ID": "sample_id",
        "Cell count": "cell_count",
        "Viable cells": "viable_cells",
        "Total (x10^6) cells/mL": "total_cells_per_ml",
        "Viable (x10^6) cells/mL": "viable_cells_per_ml",
        "Viability (%)": "viability",
        "Average diameter (µm)": "average_diameter",
        "Average viable diameter (µm)": "average_viable_diameter",
        "Average circularity": "average_circularity",
        "Average viable circularity": "average_viable_circularity",
    }, inplace=True)

    # Convert date column to datetime with timezone awareness
    df_cleaned["date_time"] = pd.to_datetime(df_cleaned["date_time"], errors="coerce")

    # Make datetime timezone-aware (Django requires this when USE_TZ=True)
    from django.utils import timezone
    df_cleaned["date_time"] = df_cleaned["date_time"].apply(
        lambda x: timezone.make_aware(x, timezone.get_default_timezone()) if pd.notna(x) and x.tzinfo is None else x
    )

    # Ensure numeric columns are properly converted
    numeric_columns = [
        "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
        "viability", "average_diameter", "average_viable_diameter",
        "average_circularity", "average_viable_circularity"
    ]
    for col in numeric_columns:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")

    # Assign sample_type based on predefined categories
    def assign_sample_type(sample_id):
        if isinstance(sample_id, str):
            if sample_id.startswith("E"):
                return 1  # UP
            elif sample_id.startswith("S"):
                return 2  # CLD
        return 3  # Uncategorized

    df_cleaned["sample_type"] = df_cleaned["sample_id"].apply(assign_sample_type)

    return df_cleaned


# Function to parse sample name
def parse_sample_name(sample_name):
    """
    Parses the sample ID into structured components.

    Example mappings:
    - E47D00SF-1 -> {'experiment': 'E47', 'day': 0, 'reactor_type': 'SF', 'reactor_number': 1, 'special': ''}
    - E47D01BRX02 PREFEED -> {'experiment': 'E47', 'day': 1, 'reactor_type': 'BRX', 'reactor_number': 2, 'special': 'PRE'}
    """
    sample_name = str(sample_name)  # Convert to string if it's an integer

    match = re.match(
        r"(?P<experiment>E\d{2})D(?P<day>\d{2})(?P<reactor_type>SF|BRX|BR)[-_]*(?P<reactor_number>\d+)\s*(?P<special>PREFEED|POSTFEED|PREINOC|POSTINOC)?",
        sample_name, re.IGNORECASE
    )

    # If first pattern fails, try alternate format
    if not match:
        match = re.match(
            r"(?P<experiment>E\d{2})D(?P<day>\d{2})(?P<reactor_type>SF|BRX|BR)\s*(?P<special>PREFEED|POSTFEED|PREINOC|POSTINOC)[-_]*(?P<reactor_number>\d+)",
            sample_name, re.IGNORECASE
        )

    # If still no match, return defaults
    if not match:
        print(f"⚠️ Could not parse sample: {sample_name}")
        return {
            "experiment": None,
            "day": None,
            "reactor_type": None,
            "reactor_number": None,
            "special": ""
        }

    parsed_data = match.groupdict()

    # Convert numeric fields
    parsed_data["day"] = int(parsed_data["day"]) if parsed_data["day"] else None
    parsed_data["reactor_number"] = int(parsed_data["reactor_number"]) if parsed_data["reactor_number"] else None

    # Normalize `special` field (PRE/POST labels)
    pre_post_map = {
        "PREFEED": "PRE",
        "PREINOC": "PRE",
        "POSTFEED": "POST",
        "POSTINOC": "POST"
    }
    parsed_data["special"] = pre_post_map.get(parsed_data["special"].upper(), "") if parsed_data["special"] else ""

    return parsed_data


# Callback to read and preview the uploaded file
@app.callback(
    [Output('data-preview', 'columns'),
     Output('data-preview', 'data'),
     Output('file-name', 'children'),
     Output('save-button', 'style')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_output(contents, filename):
    if contents:
        try:
            # Determine file type and parse accordingly
            if filename.lower().endswith('.csv'):
                df_cleaned = parse_csv_contents(contents, filename)
            elif filename.lower().endswith(('.xls', '.xlsx')):
                df_cleaned = parse_excel_contents(contents, filename)
            else:
                return [], [], f"❌ Unsupported file type. Please upload CSV or Excel file.", {'display': 'none'}

            # Convert dataframe to DataTable format
            columns = [{"name": i, "id": i} for i in df_cleaned.columns]
            data = df_cleaned.to_dict('records')

            # Show save button
            button_style = {
                'display': 'inline-block',
                "backgroundColor": "#28a745",
                "color": "white",
                "padding": "10px 20px",
                "border": "none",
                "borderRadius": "5px",
                "cursor": "pointer",
                "fontSize": "16px",
                "marginRight": "10px"
            }

            return columns, data, f"✅ File Uploaded: {filename}", button_style

        except Exception as e:
            return [], [], f"❌ Error reading file: {str(e)}", {'display': 'none'}

    return [], [], "No file uploaded.", {'display': 'none'}


# Callback to trigger confirmation dialog
@app.callback(
    Output('confirm-clear', 'displayed'),
    Input('clear-button', 'n_clicks'),
    prevent_initial_call=True
)
def display_confirm(n_clicks):
    if n_clicks:
        return True
    return False


# Callback to clear all data
@app.callback(
    Output('save-status', 'children', allow_duplicate=True),
    Input('confirm-clear', 'submit_n_clicks'),
    prevent_initial_call=True
)
def clear_all_data(submit_n_clicks):
    if submit_n_clicks:
        try:
            # Delete all ViCellData records
            count = ViCellData.objects.all().count()
            ViCellData.objects.all().delete()
            return f"✅ Successfully deleted {count} records from the database!"
        except Exception as e:
            return f"❌ Error clearing data: {str(e)}"
    return ""


# Callback to save data to database
@app.callback(
    Output('save-status', 'children'),
    Input('save-button', 'n_clicks'),
    State('data-preview', 'data'),
    prevent_initial_call=True
)
def save_to_db(n_clicks, data):
    if not data:
        return "No data to import."

    try:
        df = pd.DataFrame(data)

        # Convert date_time to proper format and make timezone-aware
        df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')

        # Make datetimes timezone-aware
        df['date_time'] = df['date_time'].apply(
            lambda x: timezone.make_aware(x, timezone.get_default_timezone())
            if pd.notna(x) and x.tzinfo is None else x
        )

        # Check for rows with missing date_time
        missing_dates = df[df['date_time'].isna()]
        if not missing_dates.empty:
            print(f"Warning: {len(missing_dates)} rows have invalid date_time values")
            print("Sample IDs with missing dates:", missing_dates['sample_id'].tolist())

        # Replace NaN values with None (NULL) for MySQL compatibility
        df = df.replace({np.nan: None})

        new_records = []
        skipped_records = []

        for idx, row in df.iterrows():
            # Skip rows without valid date_time
            if pd.isna(row["date_time"]) or row["date_time"] is None:
                skipped_records.append(row["sample_id"])
                continue

            parsed_sample = parse_sample_name(row["sample_id"])  # Parse sample ID

            new_records.append(ViCellData(
                sample_id=row["sample_id"],
                date_time=row["date_time"],
                cell_count=row.get("cell_count"),
                viable_cells=row.get("viable_cells"),
                total_cells_per_ml=row.get("total_cells_per_ml"),
                viable_cells_per_ml=row.get("viable_cells_per_ml"),
                viability=row.get("viability"),
                average_diameter=row.get("average_diameter"),
                average_viable_diameter=row.get("average_viable_diameter"),
                average_circularity=row.get("average_circularity"),
                average_viable_circularity=row.get("average_viable_circularity"),

                # Parsed fields
                experiment=parsed_sample["experiment"],
                day=parsed_sample["day"],
                reactor_type=parsed_sample["reactor_type"],
                reactor_number=parsed_sample["reactor_number"],
                special=parsed_sample["special"],
                sample_type=row.get("sample_type")
            ))

        # Perform bulk insert for new records
        created_count = 0
        duplicate_samples = []

        if new_records:
            # Get existing sample IDs to check for duplicates
            existing_sample_ids = set(ViCellData.objects.values_list('sample_id', flat=True))

            # Separate new and duplicate records
            records_to_create = []
            for record in new_records:
                if record.sample_id in existing_sample_ids:
                    duplicate_samples.append(record.sample_id)
                else:
                    records_to_create.append(record)

            # Bulk create only truly new records
            if records_to_create:
                created_records = ViCellData.objects.bulk_create(records_to_create, ignore_conflicts=True)
                created_count = len(created_records)

        # Build detailed status message
        status_message = f"📊 Import Summary:\n"
        status_message += f"✅ Successfully created {created_count} new records\n"
        status_message += f"📋 Total records processed: {len(new_records)}\n"

        if duplicate_samples:
            status_message += f"⚠️ {len(duplicate_samples)} duplicate records skipped\n"
            if len(duplicate_samples) <= 5:
                status_message += f"   Duplicate samples: {', '.join(duplicate_samples[:5])}\n"
            else:
                status_message += f"   Duplicate samples include: {', '.join(duplicate_samples[:5])} and {len(duplicate_samples) - 5} more...\n"

        if skipped_records:
            status_message += f"❌ {len(skipped_records)} records skipped due to missing date/time\n"
            if len(skipped_records) <= 5:
                status_message += f"   Skipped samples: {', '.join(skipped_records)}"
            else:
                status_message += f"   Skipped samples include: {', '.join(skipped_records[:5])} and {len(skipped_records) - 5} more..."

        # Log summary for debugging
        print(f"\nIMPORT SUMMARY:")
        print(f"  Total rows in uploaded file: {len(df)}")
        print(f"  Records with valid dates: {len(new_records)}")


    except Exception as e:
        return f"❌ Error importing data: {str(e)}"