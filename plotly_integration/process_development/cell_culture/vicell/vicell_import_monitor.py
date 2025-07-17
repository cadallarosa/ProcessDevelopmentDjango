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
VICELL_FILE = r"S:\DjangoRawData\Vicell\Summary_DECEMBER.csv"
VICELL_FOLDER = r"S:\DjangoRawData\Vicell"
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


def get_latest_datetime_from_db():
    """Get the most recent datetime from the database"""
    try:
        latest_record = ViCellData.objects.order_by('-date_time').first()
        if latest_record:
            logger.info(f"Latest datetime in database: {latest_record.date_time}")
            return latest_record.date_time
        else:
            logger.info("No records in database - will import all data")
            return None
    except Exception as e:
        logger.error(f"Error getting latest datetime: {str(e)}")
        return None


def create_vicell_record(row_data):
    """Create a ViCellData object from row data"""
    parsed_sample = parse_sample_name(row_data.get("sample_id"))

    return ViCellData(
        sample_id=row_data.get("sample_id"),
        date_time=row_data.get("date_time"),
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
    """Process ViCell file starting from the end until we reach the latest DB datetime"""
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

        # Convert date column with multiple format support
        df_cleaned["date_time"] = pd.to_datetime(df_cleaned["date_time"], errors="coerce", infer_datetime_format=True)

        # Try additional date formats for any that failed
        date_mask = df_cleaned["date_time"].isna()
        if date_mask.any():
            logger.info(f"Attempting to parse {date_mask.sum()} dates with alternative formats")
            original_dates = df.loc[df_cleaned.index, "Analysis date/time"]

            for fmt in ['%m/%d/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                try:
                    df_cleaned.loc[date_mask, "date_time"] = pd.to_datetime(
                        original_dates[date_mask], format=fmt, errors='coerce'
                    )
                    date_mask = df_cleaned["date_time"].isna()
                    logger.info(f"After trying {fmt}: {date_mask.sum()} still unparseable")
                    if not date_mask.any():
                        break
                except Exception as e:
                    logger.debug(f"Format {fmt} failed: {e}")
                    continue

        # Make datetime timezone-aware
        df_cleaned["date_time"] = df_cleaned["date_time"].apply(
            lambda x: timezone.make_aware(x, timezone.get_default_timezone())
            if pd.notna(x) and x.tzinfo is None else x
        )

        # Remove rows with invalid dates or sample IDs
        valid_mask = (
                df_cleaned["date_time"].notna() &
                df_cleaned["sample_id"].notna() &
                (df_cleaned["sample_id"] != "")
        )
        df_valid = df_cleaned[valid_mask].copy()

        invalid_count = len(df_cleaned) - len(df_valid)
        logger.info(f"Rows with valid data: {len(df_valid)}")
        logger.info(f"Rows with invalid data (will skip): {invalid_count}")

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

        # Sort by datetime (newest first) to start from the end
        df_sorted = df_valid.sort_values('date_time', ascending=False)
        logger.info(f"Data range: {df_sorted['date_time'].min()} to {df_sorted['date_time'].max()}")

        # Get the latest datetime from database
        latest_db_datetime = get_latest_datetime_from_db()

        # Determine which records to import
        if latest_db_datetime:
            # Only import records newer than what's in the database
            new_records_df = df_sorted[df_sorted['date_time'] > latest_db_datetime]
            logger.info(f"Found {len(new_records_df)} records newer than {latest_db_datetime}")
        else:
            # No records in database, import all
            new_records_df = df_sorted
            logger.info(f"Database is empty, importing all {len(new_records_df)} records")

        if len(new_records_df) == 0:
            return {
                'imported': 0,
                'failed': 0,
                'skipped_invalid': invalid_count,
                'message': 'No new records to import'
            }

        # Import records one by one from newest to oldest
        imported_count = 0
        failed_count = 0
        failed_records = []

        logger.info(f"Starting import of {len(new_records_df)} records...")

        for idx, row in new_records_df.iterrows():
            try:
                # Create the record
                record = create_vicell_record(row.to_dict())

                # Try to save with retry logic
                success, error = save_record_with_retry(record)

                if success:
                    imported_count += 1
                    if imported_count % 100 == 0:  # Progress logging
                        logger.info(f"Imported {imported_count} records so far...")
                else:
                    failed_count += 1
                    failed_records.append({
                        'sample_id': record.sample_id,
                        'date_time': record.date_time,
                        'error': error
                    })
                    logger.error(f"Failed to import {record.sample_id} after {MAX_RETRIES} attempts: {error}")

            except Exception as e:
                failed_count += 1
                failed_records.append({
                    'sample_id': row.get('sample_id', 'Unknown'),
                    'date_time': row.get('date_time', 'Unknown'),
                    'error': str(e)
                })
                logger.error(f"Unexpected error processing row: {str(e)}")

        logger.info(f"Import completed: {imported_count} imported, {failed_count} failed")

        return {
            'imported': imported_count,
            'failed': failed_count,
            'skipped_invalid': invalid_count,
            'failed_records': failed_records[:10],  # Only first 10 failures for reporting
            'total_failures': len(failed_records),
            'latest_imported': new_records_df.iloc[0]['date_time'] if imported_count > 0 else None,
            'message': f"Successfully imported {imported_count} records, {failed_count} failed"
        }

    except Exception as e:
        logger.error(f"Fatal error in process_vicell_file_from_end: {str(e)}")
        return {
            'imported': 0,
            'failed': 0,
            'skipped_invalid': 0,
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

        # Process the file
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
            'method': 'database-based-reverse',
            'imported': result['imported'],
            'failed': result['failed'],
            'skipped_invalid': result['skipped_invalid'],
            'latest_imported': result.get('latest_imported').isoformat() if result.get('latest_imported') else None,
            'details': result
        }, 3600)

        return {
            "status": "success",
            "message": result['message'],
            "imported": result['imported'],
            "failed": result['failed'],
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

        status['database_info'] = {
            'total_records': total_records,
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
                html.H1("ViCell Import Monitor (Database-Based)", style={"color": "#0047b3", "margin": "0"}),
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
        logger.info("Running ViCell import (database-based)...")
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
            html.P(f"Records Imported: {last_import.get('imported', 0)}")
        ])
    else:
        last_import_div = html.P("No import history available", style={"color": "#666"})

    return status_div, db_info_div, last_import_div