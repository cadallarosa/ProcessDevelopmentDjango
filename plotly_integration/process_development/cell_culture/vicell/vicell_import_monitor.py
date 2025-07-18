import os
import json
import re
import logging
import pandas as pd
import numpy as np
from datetime import datetime as dt
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import IntegrityError, transaction
from plotly_integration.models import ViCellData

# Dash imports for the monitoring UI
from dash import dcc, html, Input, Output, dash_table
from django_plotly_dash import DjangoDash

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
VICELL_FILE = r"S:\Shared\Vi-Blue_Unsorted\Summary_DECEMBER.csv"
VICELL_FOLDER = r"S:\Shared\Vi-Blue_Unsorted"
# VICELL_FILE = r"/mnt/fs2/Vi-Blue_Unsorted/Summary_DECEMBER.csv"
# VICELL_FOLDER = r"/mnt/fs2/Vi-Blue_Unsorted"
MAX_RETRIES = 3  # Maximum retry attempts per record


def parse_sample_name(sample_name):
    """Parse the sample ID into structured components for ViCell"""
    sample_name = str(sample_name)

    match = re.match(
        r"(?P<experiment>E\d{2})D(?P<day>\d{2})(?P<reactor_type>SF|BRX|BR)[-_]*(?P<reactor_number>\d+)\s*(?P<special>PREFEED|POSTFEED|PREINOC|POSTINOC)?",
        sample_name
    )

    if match:
        result = {
            'experiment': match.group('experiment'),
            'day': int(match.group('day')),
            'reactor_type': match.group('reactor_type'),
            'reactor_number': int(match.group('reactor_number')),
            'special': match.group('special') or ''
        }
        return result
    else:
        return {
            'experiment': '',
            'day': None,
            'reactor_type': '',
            'reactor_number': None,
            'special': ''
        }


def process_vicell_file_from_end():
    """
    Process the ViCell CSV file with robust datetime handling.
    Assumes ViCell timestamps are already in the correct timezone.
    """

    if not os.path.exists(VICELL_FILE):
        logger.error(f"ViCell file not found: {VICELL_FILE}")
        return {
            'imported': 0,
            'failed': 0,
            'skipped_invalid': 0,
            'skipped_duplicates': 0,
            'datetime_errors': 0,
            'error': 'File not found',
            'message': f"ViCell file not found: {VICELL_FILE}"
        }

    try:
        # Read the CSV file
        df = pd.read_csv(VICELL_FILE)
        logger.info(f"Read {len(df)} rows from ViCell CSV file")

        # Define column mapping
        column_mapping = {
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
            "Analysis date/time": "date_time"
        }

        # Rename columns
        df_cleaned = df.rename(columns=column_mapping)

        # Process datetime column with robust parsing
        datetime_errors = []
        formatted_datetimes = []

        for idx, row in df_cleaned.iterrows():
            date_str = row.get('date_time')

            if pd.isna(date_str) or str(date_str).lower() in ['nan', 'nat', '', 'null', 'none']:
                formatted_datetimes.append(None)
                continue

            try:
                # Try to parse with pandas first (handles most formats)
                parsed_date = pd.to_datetime(str(date_str), errors='coerce')

                if pd.notna(parsed_date):
                    # DIRTY FIX: ViCell times are being interpreted incorrectly
                    # If the time is being shifted forward by ~7-8 hours, subtract it back
                    # This assumes ViCell is recording in Pacific Time but Django is interpreting it as UTC
                    from datetime import timedelta

                    # Subtract 7 hours to correct the timezone interpretation issue
                    corrected_date = parsed_date - timedelta(hours=7)

                    if hasattr(settings, 'USE_TZ') and settings.USE_TZ:
                        # Make timezone-aware using the default timezone
                        aware_date = timezone.make_aware(corrected_date.to_pydatetime(),
                                                         timezone.get_default_timezone())
                        formatted_datetimes.append(aware_date)
                    else:
                        # If not using timezones, use the datetime as-is
                        formatted_datetimes.append(corrected_date.to_pydatetime())
                    continue

            except Exception as e:
                logger.debug(f"Error parsing date {date_str}: {e}")

            # If pandas failed, try manual parsing with specific formats
            date_str_clean = str(date_str).strip()
            format_attempts = [
                '%m/%d/%Y %I:%M:%S %p',  # 12-hour format with seconds and AM/PM (YOUR FORMAT)
                '%m/%d/%Y %I:%M %p',  # 12-hour format with AM/PM
                '%m/%d/%Y %H:%M:%S',  # 24-hour format with seconds
                '%m/%d/%Y %H:%M',  # 24-hour format
                '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y%m%d %H:%M:%S',
                '%m-%d-%Y %H:%M:%S',
            ]

            parsed_successfully = False
            for fmt in format_attempts:
                try:
                    # Parse to datetime
                    manual_parsed = dt.strptime(date_str_clean, fmt)

                    # DIRTY FIX: Subtract 7 hours to correct timezone interpretation
                    from datetime import timedelta
                    corrected_date = manual_parsed - timedelta(hours=7)

                    # Make timezone-aware if Django requires it
                    if hasattr(settings, 'USE_TZ') and settings.USE_TZ:
                        aware_date = timezone.make_aware(corrected_date, timezone.get_default_timezone())
                        formatted_datetimes.append(aware_date)
                    else:
                        formatted_datetimes.append(corrected_date)

                    parsed_successfully = True
                    break
                except ValueError:
                    continue

            if not parsed_successfully:
                # Record the error and set to None
                sample_id = row.get('sample_id', f"Row {idx}")
                datetime_errors.append(sample_id)
                formatted_datetimes.append(None)
                logger.warning(f"Failed to parse datetime '{date_str}' for sample {sample_id}")

        # Assign the processed datetimes back to the dataframe
        df_cleaned['date_time'] = formatted_datetimes

        # Convert numeric columns
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

        # Get the last imported record from database
        latest_db_record = ViCellData.objects.order_by('-date_time').first()
        latest_db_datetime = latest_db_record.date_time if latest_db_record else None

        # Import the data
        imported_count = 0
        failed_count = 0
        duplicate_count = 0
        failed_records = []
        latest_imported = None

        with transaction.atomic():
            for idx, row in df_cleaned.iterrows():
                try:
                    # Skip if datetime is null
                    if pd.isna(row['date_time']):
                        continue

                    # Skip if we already have this record (based on datetime)
                    if latest_db_datetime and row['date_time'] and row['date_time'] <= latest_db_datetime:
                        duplicate_count += 1
                        continue

                    # Parse sample name
                    parsed = parse_sample_name(row.get('sample_id', ''))

                    # Create the ViCellData object
                    vicell_data = ViCellData(
                        sample_id=row.get('sample_id'),
                        cell_count=row.get('cell_count'),
                        viable_cells=row.get('viable_cells'),
                        total_cells_per_ml=row.get('total_cells_per_ml'),
                        viable_cells_per_ml=row.get('viable_cells_per_ml'),
                        viability=row.get('viability'),
                        average_diameter=row.get('average_diameter'),
                        average_viable_diameter=row.get('average_viable_diameter'),
                        average_circularity=row.get('average_circularity'),
                        average_viable_circularity=row.get('average_viable_circularity'),
                        date_time=row.get('date_time'),
                        sample_type=row.get('sample_type', 3),
                        experiment=parsed['experiment'],
                        day=parsed['day'],
                        reactor_type=parsed['reactor_type'],
                        reactor_number=parsed['reactor_number'],
                        special=parsed['special']
                    )

                    vicell_data.save()
                    imported_count += 1

                    # Track the latest imported datetime
                    if row['date_time']:
                        if latest_imported is None or row['date_time'] > latest_imported:
                            latest_imported = row['date_time']

                except IntegrityError as e:
                    if 'unique constraint' in str(e).lower():
                        duplicate_count += 1
                    else:
                        failed_count += 1
                        failed_records.append({
                            'row_index': idx,
                            'sample_id': row.get('sample_id', f'Row {idx}'),
                            'error': str(e)
                        })
                except Exception as e:
                    failed_count += 1
                    failed_records.append({
                        'row_index': idx,
                        'sample_id': row.get('sample_id', f'Row {idx}'),
                        'error': str(e)
                    })

        # Convert latest_imported to string if it exists
        if latest_imported:
            latest_imported = latest_imported.isoformat() if hasattr(latest_imported, 'isoformat') else str(
                latest_imported)

        logger.info(f"Import completed: {imported_count} imported, {failed_count} failed, {duplicate_count} duplicates")

        return {
            'imported': imported_count,
            'failed': failed_count,
            'skipped_invalid': 0,
            'skipped_duplicates': duplicate_count,
            'datetime_errors': len(datetime_errors),
            'datetime_error_samples': datetime_errors,
            'failed_records': failed_records[:10],  # Only first 10 failures for reporting
            'total_failures': len(failed_records),
            'latest_imported': latest_imported,
            'message': f"Successfully imported {imported_count} records, {failed_count} failed, {duplicate_count} duplicates skipped, {len(datetime_errors)} with NULL datetime"
        }

    except Exception as e:
        logger.error(f"Fatal error in process_vicell_file_from_end: {str(e)}")
        return {
            'imported': 0,
            'failed': 0,
            'skipped_invalid': 0,
            'skipped_duplicates': 0,
            'datetime_errors': 0,
            'error': str(e),
            'message': f"Fatal error: {str(e)}"
        }


def run_vicell_import():
    """Main function to run ViCell import process"""
    lock_id = 'vicell_import_lock'

    # Try to acquire lock
    if not cache.add(lock_id, 'locked', 300):  # 5 minute timeout
        logger.info("ViCell import task already running")
        return {
            "status": "error",
            "message": "ViCell import task already running"
        }

    try:
        # Verify file exists
        if not os.path.exists(VICELL_FILE):
            logger.error(f"ViCell file not found: {VICELL_FILE}")
            return {
                "status": "error",
                "message": f"ViCell file not found: {VICELL_FILE}"
            }

        filename = os.path.basename(VICELL_FILE)
        logger.info(f"Processing file: {filename}")

        # Process the file using the updated robust function
        result = process_vicell_file_from_end()

        if 'error' in result:
            return {
                "status": "error",
                "message": result['message'],
                "details": result
            }

        # Store detailed results in cache
        cache.set('vicell_last_import', {
            'timestamp': dt.now().isoformat(),
            'method': 'robust-sample-id-based',
            'imported': result['imported'],
            'failed': result['failed'],
            'skipped_invalid': result['skipped_invalid'],
            'skipped_duplicates': result.get('skipped_duplicates', 0),
            'datetime_errors': result.get('datetime_errors', 0),
            'latest_imported': result.get('latest_imported'),  # Already converted to string in the function
            'details': result
        }, 3600)

        return {
            "status": "success",
            "message": result['message'],
            "imported": result['imported'],
            "failed": result['failed'],
            "datetime_errors": result.get('datetime_errors', 0),
            "details": result
        }

    except Exception as e:
        error_msg = f"Fatal error in ViCell import: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

    finally:
        # Release lock
        cache.delete(lock_id)


def get_vicell_import_status():
    """Get current import status"""
    status = {
        'file_path': VICELL_FILE,
        'file_exists': os.path.exists(VICELL_FILE),
        'last_import': cache.get('vicell_last_import'),
        'is_locked': cache.get('vicell_import_lock') is not None,
        'database_info': {}
    }

    try:
        # Get database info
        total_records = ViCellData.objects.count()
        latest_record = ViCellData.objects.order_by('-date_time').first()
        null_datetime_count = ViCellData.objects.filter(date_time__isnull=True).count()

        status['database_info'] = {
            'total_records': total_records,
            'null_datetime_records': null_datetime_count,
            'latest_datetime': latest_record.date_time.isoformat() if latest_record else None
        }

        # Get file info
        if os.path.exists(VICELL_FILE):
            df = pd.read_csv(VICELL_FILE)
            status['file_info'] = {
                'total_rows': len(df)
            }

    except Exception as e:
        status['database_info'] = {'error': str(e)}

    return status


# Initialize the Dash app
app = DjangoDash("ViCellImportMonitorSimplified")

# Layout
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f4f7f6",
        "padding": "20px",
        "maxWidth": "1400px",
        "margin": "0 auto",
        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "borderRadius": "8px"
    },
    children=[
        # Header
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "marginBottom": "30px"
            },
            children=[
                html.H1("ViCell Import Monitor (Robust DateTime Handling)", style={"color": "#0047b3", "margin": "0"}),
                html.Div(
                    children=[
                        html.Button(
                            "Refresh",
                            id="refresh-vicell-btn",
                            style={
                                "backgroundColor": "#0047b3",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "5px",
                                "padding": "10px 20px",
                                "fontSize": "16px",
                                "cursor": "pointer",
                                "marginRight": "10px"
                            }
                        ),
                        html.Button(
                            "Run Import",
                            id="run-vicell-import-btn",
                            style={
                                "backgroundColor": "#28a745",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "5px",
                                "padding": "10px 20px",
                                "fontSize": "16px",
                                "cursor": "pointer"
                            }
                        )
                    ]
                )
            ]
        ),

        # Main content
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
                "gap": "20px",
                "marginBottom": "30px"
            },
            children=[
                # Status Card
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "borderRadius": "8px",
                        "padding": "20px",
                        "boxShadow": "0px 2px 5px rgba(0, 0, 0, 0.1)"
                    },
                    children=[
                        html.H3("Status", style={"color": "#0047b3", "marginBottom": "15px"}),
                        html.Div(id="vicell-status")
                    ]
                ),

                # Database Info Card
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "borderRadius": "8px",
                        "padding": "20px",
                        "boxShadow": "0px 2px 5px rgba(0, 0, 0, 0.1)"
                    },
                    children=[
                        html.H3("Database Info", style={"color": "#0047b3", "marginBottom": "15px"}),
                        html.Div(id="database-info")
                    ]
                ),

                # Last Import Card
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "borderRadius": "8px",
                        "padding": "20px",
                        "boxShadow": "0px 2px 5px rgba(0, 0, 0, 0.1)"
                    },
                    children=[
                        html.H3("Last Import", style={"color": "#0047b3", "marginBottom": "15px"}),
                        html.Div(id="last-import-details")
                    ]
                ),
            ]
        ),

        # Hidden div for import trigger
        html.Div(id="import-trigger-vicell", style={"display": "none"}),

        # Auto-refresh
        dcc.Interval(
            id="interval-vicell",
            interval=10 * 1000,  # Update every 10 seconds
            n_intervals=0
        ),
    ]
)


@app.callback(
    Output("import-trigger-vicell", "children"),
    Input("run-vicell-import-btn", "n_clicks"),
    prevent_initial_call=True
)
def trigger_import(n_clicks):
    if n_clicks > 0:
        logger.info("Running ViCell import (robust datetime handling)...")
        result = run_vicell_import()
        cache.set('vicell_direct_import_result', result, 300)
        return json.dumps({"status": "direct", "result": result})
    return ""


@app.callback(
    [Output("vicell-status", "children"),
     Output("database-info", "children"),
     Output("last-import-details", "children")],
    [Input("interval-vicell", "n_intervals"),
     Input("refresh-vicell-btn", "n_clicks"),
     Input("import-trigger-vicell", "children")]
)
def update_dashboard(n_intervals, refresh_clicks, import_trigger):
    """Update dashboard with current status"""
    try:
        status = get_vicell_import_status()
    except Exception as e:
        status = {"error": str(e)}

    # Check if we just triggered an import
    if import_trigger:
        try:
            trigger_data = json.loads(import_trigger)
            if trigger_data.get("status") == "direct":
                direct_result = cache.get('vicell_direct_import_result')
                if direct_result:
                    status['last_import'] = direct_result
        except:
            pass

    # Status display
    if status.get("is_locked"):
        status_text = "Import in progress..."
        status_color = "#ffc107"
    else:
        status_text = "Ready"
        status_color = "#28a745"

    status_div = html.Div([
        html.H4(
            status_text,
            style={"color": status_color, "marginBottom": "10px"}
        ),
        html.P(f"Monitoring file: {status.get('file_path', 'N/A')}"),
        html.P(f"File exists: {'Yes' if status.get('file_exists') else 'No'}")
    ])

    # Database info
    db_info = status.get('database_info', {})
    if 'error' in db_info:
        db_info_div = html.P(f"Error reading database: {db_info['error']}", style={"color": "#dc3545"})
    elif db_info:
        latest_dt = db_info.get('latest_datetime')
        if latest_dt:
            try:
                latest_formatted = dt.fromisoformat(latest_dt).strftime('%Y-%m-%d %H:%M:%S')
            except:
                latest_formatted = latest_dt
        else:
            latest_formatted = "No records"

        db_info_div = html.Div([
            html.P(f"Total records in database: {db_info.get('total_records', 0):,}"),
            html.P(f"Records with NULL datetime: {db_info.get('null_datetime_records', 0):,}"),
            html.P(f"Latest record datetime: {latest_formatted}"),
            html.P(f"File total rows: {status.get('file_info', {}).get('total_rows', 'Unknown'):,}")
        ])
    else:
        db_info_div = html.P("No database information available", style={"color": "#666"})

    # Last import details
    last_import = status.get('last_import')
    if last_import and 'timestamp' in last_import:
        timestamp = dt.fromisoformat(last_import['timestamp'])

        details_items = [
            html.H5(f"Last Import: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"),
            html.P(f"Method: {last_import.get('method', 'Unknown')}"),
            html.P(f"Records Imported: {last_import.get('imported', 0)}"),
            html.P(f"Failed Imports: {last_import.get('failed', 0)}"),
            html.P(f"Invalid Records Skipped: {last_import.get('skipped_invalid', 0)}"),
            html.P(f"Duplicate Records Skipped: {last_import.get('skipped_duplicates', 0)}"),
            html.P(f"DateTime Errors (set to NULL): {last_import.get('datetime_errors', 0)}"),
        ]

        if last_import.get('latest_imported'):
            try:
                latest_imported_dt = dt.fromisoformat(last_import['latest_imported'])
                details_items.append(
                    html.P(f"Latest Imported: {latest_imported_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                )
            except:
                pass

        last_import_div = html.Div(details_items)
    elif last_import:
        # Handle case where last_import exists but doesn't have timestamp
        last_import_div = html.Div([
            html.P(f"Status: {last_import.get('status', 'Unknown')}"),
            html.P(f"Message: {last_import.get('message', 'No message')}"),
            html.P(f"Records Imported: {last_import.get('imported', 0)}"),
            html.P(f"DateTime Errors: {last_import.get('datetime_errors', 0)}")
        ])
    else:
        last_import_div = html.P("No import history available", style={"color": "#666"})

    return status_div, db_info_div, last_import_div