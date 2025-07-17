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
VICELL_FILE = r"/mnt/fs2/Vi-Blue_Unsorted/Summary_DECEMBER.csv"
VICELL_FOLDER = r"/mnt/fs2/Vi-Blue_Unsorted"
MAX_RETRIES = 3  # Maximum retry attempts per record


def parse_sample_name(sample_name):
    """Parse the sample ID into structured components for ViCell"""
    sample_name = str(sample_name)

    match = re.match(
        r"(?P<experiment>E\d{2})D(?P<day>\d{2})(?P<reactor_type>SF|BRX|BR)[-_]*(?P<reactor_number>\d+)\s*(?P<special>PREFEED|POSTFEED|PREINOC|POSTINOC)?",
        sample_name, re.IGNORECASE
    )

    if not match:
        match = re.match(
            r"(?P<experiment>E\d{2})D(?P<day>\d{2})(?P<reactor_type>SF|BRX|BR)\s*(?P<special>PREFEED|POSTFEED|PREINOC|POSTINOC)[-_]*(?P<reactor_number>\d+)",
            sample_name, re.IGNORECASE
        )

    if not match:
        return {
            "experiment": None,
            "day": None,
            "reactor_type": None,
            "reactor_number": None,
            "special": ""
        }

    parsed_data = match.groupdict()
    parsed_data["day"] = int(parsed_data["day"]) if parsed_data["day"] else None
    parsed_data["reactor_number"] = int(parsed_data["reactor_number"]) if parsed_data["reactor_number"] else None

    pre_post_map = {
        "PREFEED": "PRE",
        "PREINOC": "PRE",
        "POSTFEED": "POST",
        "POSTINOC": "POST"
    }
    parsed_data["special"] = pre_post_map.get(parsed_data["special"].upper(), "") if parsed_data["special"] else ""

    return parsed_data


def assign_sample_type(sample_id):
    """Assign sample type based on sample ID prefix"""
    if isinstance(sample_id, str):
        if sample_id.startswith("E"):
            return 1  # UP
        elif sample_id.startswith("S"):
            return 2  # CLD
    return 3  # Uncategorized


def create_vicell_record(row_data):
    """Create a ViCellData object from row data - handles NULL datetime gracefully"""
    parsed_sample = parse_sample_name(row_data.get("sample_id"))

    # Handle datetime - use None if it's NaT or invalid
    date_time = row_data.get("date_time")
    if pd.isna(date_time):
        date_time = None

    return ViCellData(
        sample_id=row_data.get("sample_id"),
        date_time=date_time,  # Can be None/NULL
        cell_count=row_data.get("cell_count"),
        viable_cells=row_data.get("viable_cells"),
        total_cells_per_ml=row_data.get("total_cells_per_ml"),
        viable_cells_per_ml=row_data.get("viable_cells_per_ml"),
        viability=row_data.get("viability"),
        average_diameter=row_data.get("average_diameter"),
        average_viable_diameter=row_data.get("average_viable_diameter"),
        average_circularity=row_data.get("average_circularity"),
        average_viable_circularity=row_data.get("average_viable_circularity"),
        experiment=parsed_sample["experiment"],
        day=parsed_sample["day"],
        reactor_type=parsed_sample["reactor_type"],
        reactor_number=parsed_sample["reactor_number"],
        special=parsed_sample["special"],
        sample_type=assign_sample_type(row_data.get("sample_id"))
    )


def save_record_with_retry(record, max_retries=MAX_RETRIES):
    """Try to save a record with retry logic"""
    for attempt in range(max_retries):
        try:
            record.save()
            return True, None
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {record.sample_id}: {str(e)}")
            if attempt == max_retries - 1:
                return False, str(e)
    return False, "Max retries exceeded"


def process_vicell_file_from_end():
    """Process ViCell file with robust datetime handling - properly formats all datetime values"""
    try:
        # Read the file
        df = pd.read_csv(VICELL_FILE)
        logger.info(f"Total rows in file: {len(df)}")

        # Column mapping
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

        # Select and rename columns
        relevant_columns = list(column_mapping.keys())
        available_columns = [col for col in relevant_columns if col in df.columns]
        df_cleaned = df[available_columns].copy()
        df_cleaned.rename(columns=column_mapping, inplace=True)

        # ROBUST DATETIME PROCESSING - Standardize all datetime values
        datetime_errors = []
        original_datetime_col = "Analysis date/time" if "Analysis date/time" in df.columns else None

        if "date_time" in df_cleaned.columns and original_datetime_col:
            logger.info("Processing datetime column with complete standardization...")

            # Reset the column to object type to avoid dtype conflicts
            df_cleaned["date_time"] = df_cleaned["date_time"].astype(str)

            # Create a new column for properly formatted datetimes
            formatted_datetimes = []

            for idx, date_str in enumerate(df_cleaned["date_time"]):
                try:
                    # Skip obvious non-dates
                    if pd.isna(date_str) or str(date_str).lower() in ['nan', 'nat', '', 'null', 'none']:
                        formatted_datetimes.append(None)
                        continue

                    # Try to parse with pandas first (handles most formats)
                    parsed_date = pd.to_datetime(str(date_str), errors='coerce')

                    if pd.notna(parsed_date):
                        # Convert to timezone-naive datetime, then make timezone-aware consistently
                        if parsed_date.tzinfo is not None:
                            # If already timezone-aware, convert to naive first
                            naive_date = parsed_date.tz_convert('UTC').tz_localize(None)
                        else:
                            naive_date = parsed_date

                        # Make timezone-aware with the default timezone
                        aware_date = timezone.make_aware(naive_date, timezone.get_default_timezone())
                        formatted_datetimes.append(aware_date)
                        continue

                    # If pandas failed, try manual parsing with specific formats
                    date_str_clean = str(date_str).strip()
                    format_attempts = [
                        '%m/%d/%Y %H:%M',
                        '%Y-%m-%d %H:%M:%S',
                        '%m/%d/%Y %H:%M:%S',
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
                            manual_parsed = dt.strptime(date_str_clean, fmt)
                            aware_date = timezone.make_aware(manual_parsed, timezone.get_default_timezone())
                            formatted_datetimes.append(aware_date)
                            parsed_successfully = True
                            break
                        except ValueError:
                            continue

                    if not parsed_successfully:
                        # Record the error and set to None
                        sample_id = df_cleaned.iloc[idx][
                            'sample_id'] if 'sample_id' in df_cleaned.columns else f"Row {idx}"
                        datetime_errors.append(sample_id)
                        formatted_datetimes.append(None)
                        logger.warning(f"Could not parse datetime '{date_str}' for sample {sample_id}")

                except Exception as e:
                    # Record the error and set to None
                    sample_id = df_cleaned.iloc[idx]['sample_id'] if 'sample_id' in df_cleaned.columns else f"Row {idx}"
                    datetime_errors.append(sample_id)
                    formatted_datetimes.append(None)
                    logger.warning(f"Error parsing datetime '{date_str}' for sample {sample_id}: {str(e)}")

            # Replace the column with properly formatted datetimes
            df_cleaned["date_time"] = formatted_datetimes

            # Log results
            valid_dates = [d for d in formatted_datetimes if d is not None]
            null_dates = len(formatted_datetimes) - len(valid_dates)

            logger.info(f"Datetime processing complete:")
            logger.info(f"  - Successfully parsed: {len(valid_dates)} datetimes")
            logger.info(f"  - Set to NULL: {null_dates} datetimes")

            if datetime_errors:
                datetime_errors = datetime_errors[:10]  # Keep first 10 for reporting
                logger.warning(f"Sample IDs with datetime issues: {datetime_errors}")
        else:
            logger.warning("No datetime column found - all records will have NULL datetime")
            df_cleaned["date_time"] = None

        # Remove rows with invalid sample IDs (but keep datetime NULL rows)
        valid_mask = (
                df_cleaned["sample_id"].notna() &
                (df_cleaned["sample_id"] != "") &
                (df_cleaned["sample_id"] != "nan")
        )
        df_valid = df_cleaned[valid_mask].copy()

        invalid_count = len(df_cleaned) - len(df_valid)
        datetime_null_count = sum(1 for d in df_valid["date_time"] if d is None)

        logger.info(f"Rows with valid sample IDs: {len(df_valid)}")
        logger.info(f"Rows with invalid sample IDs (will skip): {invalid_count}")
        logger.info(f"Rows with NULL datetime (will import anyway): {datetime_null_count}")

        # Ensure numeric columns are properly converted
        numeric_columns = [
            "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
            "viability", "average_diameter", "average_viable_diameter",
            "average_circularity", "average_viable_circularity"
        ]
        for col in numeric_columns:
            if col in df_valid.columns:
                df_valid[col] = pd.to_numeric(df_valid[col], errors="coerce")

        # Replace NaN values with None
        df_valid = df_valid.replace({np.nan: None})

        # Sort by datetime (nulls will go to end) - handle None values properly
        def safe_sort_key(x):
            if x is None or pd.isna(x):
                return dt.min.replace(tzinfo=timezone.get_default_timezone())
            return x

        df_sorted = df_valid.copy()
        df_sorted['sort_key'] = df_sorted['date_time'].apply(safe_sort_key)
        df_sorted = df_sorted.sort_values('sort_key', ascending=False).drop('sort_key', axis=1)

        # Log date range for non-null dates
        valid_dates = [d for d in df_sorted['date_time'] if d is not None]
        if len(valid_dates) > 0:
            logger.info(f"Date range for valid dates: {min(valid_dates)} to {max(valid_dates)}")
        else:
            logger.info("No valid dates found in file")

        # ===== FIXED: Use sample_id checking instead of timestamp comparison =====
        logger.info("Checking for existing sample IDs in database (no timestamp filtering)...")

        # Get all existing sample IDs from database
        existing_sample_ids = set(ViCellData.objects.values_list('sample_id', flat=True))
        logger.info(f"Found {len(existing_sample_ids)} existing sample IDs in database")

        # Filter out records that already exist (by sample_id, not timestamp)
        new_records_df = df_sorted[~df_sorted['sample_id'].isin(existing_sample_ids)]
        duplicate_count = len(df_sorted) - len(new_records_df)

        logger.info(f"Found {len(new_records_df)} new records to import")
        logger.info(f"Found {duplicate_count} duplicate sample IDs to skip")

        if len(new_records_df) == 0:
            return {
                'imported': 0,
                'failed': 0,
                'skipped_invalid': invalid_count,
                'skipped_duplicates': duplicate_count,
                'datetime_errors': len(datetime_errors),
                'message': 'No new records to import - all sample IDs already exist'
            }

        # Import records using bulk_create (much faster than one-by-one)
        logger.info(f"Starting bulk import of {len(new_records_df)} records...")

        records_to_create = []
        record_creation_errors = []

        for idx, row in new_records_df.iterrows():
            try:
                record = create_vicell_record(row.to_dict())
                records_to_create.append(record)

                if len(records_to_create) % 1000 == 0:
                    logger.info(f"Prepared {len(records_to_create)} records for import...")

            except Exception as e:
                record_creation_errors.append({
                    'sample_id': row.get('sample_id', 'Unknown'),
                    'error': str(e)
                })
                logger.error(f"Error creating record for {row.get('sample_id', 'Unknown')}: {str(e)}")
                continue

        # Bulk create all records
        imported_count = 0
        failed_count = len(record_creation_errors)
        failed_records = record_creation_errors.copy()

        if records_to_create:
            try:
                created_records = ViCellData.objects.bulk_create(records_to_create, ignore_conflicts=True)
                imported_count = len(created_records)
                logger.info(f"Successfully bulk created {imported_count} records")
            except Exception as e:
                logger.error(f"Bulk create failed, falling back to individual saves: {str(e)}")

                # Fallback to individual saves if bulk create fails
                for record in records_to_create:
                    try:
                        record.save()
                        imported_count += 1
                        if imported_count % 100 == 0:
                            logger.info(f"Imported {imported_count} records so far...")
                    except Exception as save_error:
                        failed_count += 1
                        failed_records.append({
                            'sample_id': record.sample_id,
                            'date_time': str(record.date_time) if record.date_time else 'NULL',
                            'error': str(save_error)
                        })
                        logger.error(f"Failed to save {record.sample_id}: {str(save_error)}")

        logger.info(f"Import completed: {imported_count} imported, {failed_count} failed")

        # Convert latest_imported to string for JSON serialization
        latest_imported = None
        if imported_count > 0 and len(new_records_df) > 0:
            latest_date = new_records_df.iloc[0]['date_time']
            if latest_date is not None:
                latest_imported = latest_date.isoformat() if hasattr(latest_date, 'isoformat') else str(latest_date)

        return {
            'imported': imported_count,
            'failed': failed_count,
            'skipped_invalid': invalid_count,
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

# Layout (same as before)
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
                                "marginRight": "10px",
                                "padding": "10px 20px",
                                "backgroundColor": "#0047b3",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "5px",
                                "cursor": "pointer"
                            }
                        ),
                        html.Button(
                            "Run Import",
                            id="run-vicell-import-btn",
                            style={
                                "padding": "10px 20px",
                                "backgroundColor": "#28a745",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "5px",
                                "cursor": "pointer"
                            }
                        ),
                    ]
                ),
            ]
        ),

        # Status Section
        html.Div(
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0px 2px 5px rgba(0, 0, 0, 0.1)",
                "marginBottom": "20px"
            },
            children=[
                html.H3("Import Status", style={"color": "#0047b3", "marginBottom": "20px"}),
                html.Div(id="vicell-status"),
            ]
        ),

        # Database Info Section
        html.Div(
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0px 2px 5px rgba(0, 0, 0, 0.1)",
                "marginBottom": "20px"
            },
            children=[
                html.H3("Database Status", style={"color": "#0047b3", "marginBottom": "20px"}),
                html.Div(id="database-info"),
            ]
        ),

        # Last Import Details
        html.Div(
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0px 2px 5px rgba(0, 0, 0, 0.1)",
            },
            children=[
                html.H3("Last Import Details", style={"color": "#0047b3", "marginBottom": "20px"}),
                html.Div(id="last-import-details"),

                # Hidden div for import trigger
                html.Div(id="import-trigger-vicell", style={"display": "none"}),

                # Auto-refresh
                dcc.Interval(
                    id="interval-vicell",
                    interval=10 * 1000,  # Update every 10 seconds
                    n_intervals=0
                ),
            ],
        ),
    ],
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