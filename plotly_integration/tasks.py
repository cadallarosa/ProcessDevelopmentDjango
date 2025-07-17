# plotly_integration/tasks.py
# Combined Celery tasks for AKTA, Empower, and ViCell imports

import os
import hashlib
import json
import re
import logging
import requests
import time
from datetime import datetime as dt, timedelta
import pandas as pd
import numpy as np
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import IntegrityError, transaction
from plotly_integration.models import ViCellData
from plotly_integration.process_development.cell_culture.vicell.vicell_import_monitor import process_vicell_file_from_end

logger = logging.getLogger(__name__)

# ========== AKTA CONFIGURATION ==========
NODEJS_SERVER = "http://localhost:3000"
CHECK_INTERVAL = 30  # Check every 30 seconds
MAX_WAIT_TIME = 3600  # Maximum 1 hour wait for traversal

# ========== EMPOWER CONFIGURATION ==========
EMPOWER_IMPORT_FOLDER = "/mnt/fs2/Chris Dallarosa/Database Imports"
EMPOWER_REPORTED_FOLDER = "/mnt/fs2/Chris Dallarosa/Database Imported"
EMPOWER_PROCESSED_FILES_LOG = os.path.join(settings.BASE_DIR, 'empower_processed_files.txt')

# ========== VICELL CONFIGURATION ==========
VICELL_FOLDER = "/mnt/fs2/Vi-Blue_Unsorted/"
VICELL_FILE = "/mnt/fs2/Vi-Blue_Unsorted/Summary_DECEMBER.csv"  # Specific file path
MAX_RETRIES = 3  # Maximum retry attempts per record


# ========== AKTA TASKS ==========
@shared_task(name='plotly_integration.run_complete_pipeline')
def run_complete_import_pipeline():
    """
    Run the complete import pipeline:
    1. Start OPC UA traversal
    2. Wait for traversal to complete
    3. Import the results
    """
    try:
        # Start traversal
        logger.info("Starting OPC UA traversal...")
        response = requests.post(f"{NODEJS_SERVER}/start-traversal")

        if response.status_code != 200:
            return f"Failed to start traversal: {response.text}"

        result = response.json()

        if not result.get('success'):
            return f"Traversal failed: {result.get('message', 'Unknown error')}"

        # Wait for completion
        logger.info("Waiting for traversal to complete...")
        start_time = time.time()

        while time.time() - start_time < MAX_WAIT_TIME:
            response = requests.get(f"{NODEJS_SERVER}/status")
            if response.status_code == 200:
                status = response.json()
                if status.get('isTraversing') == False:
                    logger.info("Traversal completed!")
                    break

            time.sleep(CHECK_INTERVAL)
        else:
            return "Traversal timed out"

        # Import results
        logger.info("Importing traversal results...")
        response = requests.post(f"{NODEJS_SERVER}/import-to-database")

        if response.status_code != 200:
            return f"Import failed: {response.text}"

        import_result = response.json()
        return f"Pipeline completed: {import_result.get('message', 'Success')}"

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        return f"Pipeline error: {str(e)}"


# ========== EMPOWER TASKS ==========
def load_empower_processed_files():
    """Load list of already processed Empower files"""
    if os.path.exists(EMPOWER_PROCESSED_FILES_LOG):
        with open(EMPOWER_PROCESSED_FILES_LOG, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_empower_processed_file(filename):
    """Mark an Empower file as processed"""
    with open(EMPOWER_PROCESSED_FILES_LOG, 'a') as f:
        f.write(f"{filename}\n")


@shared_task(name='plotly_integration.import_empower_files')
def import_empower_files():
    """Import Empower .ars and .arw files"""
    # Keep existing EMPOWER implementation
    pass


def get_empower_import_status():
    """Get current Empower import status"""
    status = {
        'folder': EMPOWER_IMPORT_FOLDER,
        'last_import': cache.get('empower_last_import'),
        'is_locked': cache.get('empower_import_lock') is not None
    }

    if os.path.isdir(EMPOWER_IMPORT_FOLDER):
        processed_files = load_empower_processed_files()
        all_files = os.listdir(EMPOWER_IMPORT_FOLDER)

        status['pending_ars'] = len([f for f in all_files if f.endswith('.ars') and f not in processed_files])
        status['pending_arw'] = len([f for f in all_files if f.endswith('.arw') and f not in processed_files])
        status['total_processed'] = len(processed_files)
    else:
        status['error'] = 'Import folder not accessible'

    return status


# ========== VICELL HELPER FUNCTIONS ==========
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


def process_vicell_files_from_folder():
    """Process all CSV files in the ViCell folder, starting from the end until we reach the latest DB datetime"""
    try:
        # Verify folder exists
        if not os.path.isdir(VICELL_FOLDER):
            logger.error(f"ViCell folder not accessible: {VICELL_FOLDER}")
            return {
                'imported': 0,
                'failed': 0,
                'skipped_invalid': 0,
                'error': f"Folder not accessible: {VICELL_FOLDER}",
                'message': f"Folder not accessible: {VICELL_FOLDER}"
            }

        # Find all CSV files directly in the folder
        files = [f for f in os.listdir(VICELL_FOLDER)
                 if f.endswith('.csv') and not f.startswith('~') and os.path.isfile(os.path.join(VICELL_FOLDER, f))]

        if not files:
            logger.info("No CSV files found to process")
            return {
                'imported': 0,
                'failed': 0,
                'skipped_invalid': 0,
                'message': 'No CSV files found to process'
            }

        logger.info(f"Found {len(files)} CSV files to process: {files}")

        # Get the latest datetime from database once
        latest_db_datetime = get_latest_datetime_from_db()

        # Process statistics across all files
        total_imported = 0
        total_failed = 0
        total_skipped_invalid = 0
        processed_files = []
        all_failed_records = []

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

        # Process each file
        for filename in files:
            filepath = os.path.join(VICELL_FOLDER, filename)
            logger.info(f"Processing file: {filename}")

            try:
                # Read the CSV file
                df = pd.read_csv(filepath)
                logger.info(f"Read {len(df)} rows from {filename}")

                # Check if required columns exist
                relevant_columns = list(column_mapping.keys())
                available_columns = [col for col in relevant_columns if col in df.columns]

                if len(available_columns) < 3:  # Need at least basic columns
                    logger.warning(f"Skipping {filename} - insufficient columns. Available: {available_columns}")
                    processed_files.append({
                        'file': filename,
                        'imported': 0,
                        'failed': 0,
                        'skipped_invalid': len(df),
                        'error': f"Insufficient columns. Available: {available_columns}"
                    })
                    total_skipped_invalid += len(df)
                    continue

                # Select and rename columns
                df_cleaned = df[available_columns].copy()
                df_cleaned.rename(columns=column_mapping, inplace=True)

                # Convert date column with multiple format support
                df_cleaned["date_time"] = pd.to_datetime(df_cleaned["date_time"], errors="coerce",
                                                         infer_datetime_format=True)

                # Try additional date formats for any that failed
                date_mask = df_cleaned["date_time"].isna()
                if date_mask.any():
                    logger.info(f"Attempting to parse {date_mask.sum()} dates with alternative formats in {filename}")
                    original_dates = df.loc[df_cleaned.index, "Analysis date/time"]

                    for fmt in ['%m/%d/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                        try:
                            df_cleaned.loc[date_mask, "date_time"] = pd.to_datetime(
                                original_dates[date_mask], format=fmt, errors='coerce'
                            )
                            date_mask = df_cleaned["date_time"].isna()
                            if not date_mask.any():
                                break
                        except Exception as e:
                            logger.debug(f"Format {fmt} failed for {filename}: {e}")
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
                logger.info(f"{filename}: {len(df_valid)} valid rows, {invalid_count} invalid rows")

                if len(df_valid) == 0:
                    logger.warning(f"No valid rows in {filename}")
                    processed_files.append({
                        'file': filename,
                        'imported': 0,
                        'failed': 0,
                        'skipped_invalid': len(df),
                        'message': 'No valid rows'
                    })
                    total_skipped_invalid += len(df)
                    continue

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
                logger.info(f"{filename} date range: {df_sorted['date_time'].min()} to {df_sorted['date_time'].max()}")

                # Determine which records to import
                if latest_db_datetime:
                    # Only import records newer than what's in the database
                    new_records_df = df_sorted[df_sorted['date_time'] > latest_db_datetime]
                    logger.info(f"{filename}: Found {len(new_records_df)} records newer than {latest_db_datetime}")
                else:
                    # No records in database, import all
                    new_records_df = df_sorted
                    logger.info(f"{filename}: Database is empty, importing all {len(new_records_df)} records")

                # Import records from this file
                file_imported = 0
                file_failed = 0
                file_failed_records = []

                if len(new_records_df) > 0:
                    logger.info(f"Starting import of {len(new_records_df)} records from {filename}...")

                    for idx, row in new_records_df.iterrows():
                        try:
                            # Create the record
                            record = create_vicell_record(row.to_dict())

                            # Try to save with retry logic
                            success, error = save_record_with_retry(record)

                            if success:
                                file_imported += 1
                                total_imported += 1
                                if total_imported % 100 == 0:  # Progress logging
                                    logger.info(f"Imported {total_imported} records so far...")
                            else:
                                file_failed += 1
                                total_failed += 1
                                file_failed_records.append({
                                    'sample_id': record.sample_id,
                                    'date_time': record.date_time,
                                    'error': error,
                                    'file': filename
                                })
                                logger.error(
                                    f"Failed to import {record.sample_id} from {filename} after {MAX_RETRIES} attempts: {error}")

                        except Exception as e:
                            file_failed += 1
                            total_failed += 1
                            file_failed_records.append({
                                'sample_id': row.get('sample_id', 'Unknown'),
                                'date_time': row.get('date_time', 'Unknown'),
                                'error': str(e),
                                'file': filename
                            })
                            logger.error(f"Unexpected error processing row in {filename}: {str(e)}")

                # Record file processing results
                processed_files.append({
                    'file': filename,
                    'total_rows': len(df),
                    'valid_rows': len(df_valid),
                    'new_rows': len(new_records_df),
                    'imported': file_imported,
                    'failed': file_failed,
                    'skipped_invalid': invalid_count
                })

                total_skipped_invalid += invalid_count
                all_failed_records.extend(file_failed_records[:5])  # Limit failed records per file

                logger.info(f"Completed {filename}: {file_imported} imported, {file_failed} failed")

            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                processed_files.append({
                    'file': filename,
                    'imported': 0,
                    'failed': 0,
                    'skipped_invalid': 0,
                    'error': str(e)
                })

        logger.info(f"All files completed: {total_imported} total imported, {total_failed} total failed")

        return {
            'imported': total_imported,
            'failed': total_failed,
            'skipped_invalid': total_skipped_invalid,
            'failed_records': all_failed_records[:20],  # Only first 20 failures for reporting
            'total_failures': len(all_failed_records),
            'processed_files': processed_files,
            'files_processed': len(processed_files),
            'message': f"Successfully processed {len(files)} files: {total_imported} imported, {total_failed} failed"
        }

    except Exception as e:
        logger.error(f"Fatal error in process_vicell_files_from_folder: {str(e)}")
        return {
            'imported': 0,
            'failed': 0,
            'skipped_invalid': 0,
            'error': str(e),
            'message': f"Fatal error: {str(e)}"
        }


# ========== VICELL TASKS ==========
@shared_task(name='plotly_integration.import_vicell_data', bind=True)
def import_vicell_data(self):
    """
    Celery task to import ViCell data using the simplified database-based approach.
    Scans folder for CSV files and imports until it reaches the latest DB datetime.
    """
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

        # Update task state
        self.update_state(state='PROGRESS', meta={'message': 'Starting import...'})

        # Process the file using monitor logic
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
            'task_id': self.request.id,
            'method': 'database-based-single-file',
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


# Legacy task name for backward compatibility
@shared_task(name='plotly_integration.check_and_import_vicell_files', bind=True)
def check_and_import_vicell_files(self):
    """Legacy task name - redirects to new simplified import"""
    return import_vicell_data.apply_async()


# ========== UTILITY FUNCTIONS ==========
def get_vicell_import_status():
    """Get current ViCell import status"""
    status = {
        'folder_path': VICELL_FOLDER,
        'folder_exists': os.path.isdir(VICELL_FOLDER),
        'last_import': cache.get('vicell_last_import'),
        'is_locked': cache.get('vicell_import_lock') is not None,
        'database_info': {},
        'folder_info': {}
    }

    try:
        # Get database info
        total_records = ViCellData.objects.count()
        latest_record = ViCellData.objects.order_by('-date_time').first()

        status['database_info'] = {
            'total_records': total_records,
            'latest_datetime': latest_record.date_time.isoformat() if latest_record else None
        }

        # Get folder info
        if os.path.isdir(VICELL_FOLDER):
            csv_files = [f for f in os.listdir(VICELL_FOLDER)
                         if f.endswith('.csv') and not f.startswith('~') and os.path.isfile(
                    os.path.join(VICELL_FOLDER, f))]

            status['folder_info'] = {
                'total_csv_files': len(csv_files),
                'csv_files': csv_files[:10] if csv_files else []  # Show first 10 files
            }

    except Exception as e:
        status['database_info'] = {'error': str(e)}

    return status


def reset_vicell_import_tracking():
    """
    Reset ViCell import tracking.
    For the simplified approach, this just clears the cache.
    """
    cache.delete('vicell_last_import')
    cache.delete('vicell_import_lock')
    return "ViCell import tracking reset"


def get_vicell_file_preview(num_rows=10):
    """Preview the latest rows from CSV files in the ViCell folder."""
    if not os.path.isdir(VICELL_FOLDER):
        return f"Folder not found: {VICELL_FOLDER}"

    try:
        # Find CSV files in the folder
        csv_files = [f for f in os.listdir(VICELL_FOLDER)
                     if f.endswith('.csv') and not f.startswith('~') and os.path.isfile(os.path.join(VICELL_FOLDER, f))]

        if not csv_files:
            return "No CSV files found in folder"

        # Read the first CSV file for preview
        sample_file = csv_files[0]
        filepath = os.path.join(VICELL_FOLDER, sample_file)
        df = pd.read_csv(filepath)

        # Convert datetime
        if 'Analysis date/time' in df.columns:
            df['Analysis date/time'] = pd.to_datetime(df['Analysis date/time'], errors='coerce')
            # Sort by timestamp and get latest rows
            df_sorted = df.sort_values('Analysis date/time', ascending=False)
            return {
                'file': sample_file,
                'total_files': len(csv_files),
                'preview': df_sorted.head(num_rows).to_dict('records')
            }
        else:
            return {
                'file': sample_file,
                'total_files': len(csv_files),
                'preview': df.head(num_rows).to_dict('records')
            }

    except Exception as e:
        return f"Error reading files: {str(e)}"