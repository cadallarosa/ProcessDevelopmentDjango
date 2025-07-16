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
from plotly_integration.models import ViCellData

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
VICELL_FOLDER = "/mnt/fs2/Vi-Blue_Unsorted"
VICELL_TRACKING_FILE = os.path.join(settings.BASE_DIR, 'vicell_import_tracking.json')


# ========== AKTA TASKS ==========
@shared_task(name='plotly_integration.run_complete_pipeline')
def run_complete_import_pipeline():
    """
    Run the complete import pipeline:
    1. Start OPC UA traversal
    2. Wait for traversal to complete
    3. Run historical data import
    """
    results = {
        "start_time": dt.now().isoformat(),
        "traversal": {},
        "import": {},
        "status": "started"
    }

    # Step 1 & 2: Traversal
    try:
        # Start the traversal
        print("🚀 Starting OPC UA traversal...")
        start_response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/start-optimized",
            timeout=30
        )
        start_response.raise_for_status()

        if not start_response.json().get('success'):
            raise Exception("Failed to start traversal")

        results["traversal"]["started_at"] = dt.now().isoformat()
        print("✅ Traversal started successfully")

        # Wait for traversal to complete
        print("⏳ Waiting for traversal to complete...")
        elapsed = 0
        last_processed = 0

        while elapsed < MAX_WAIT_TIME:
            time.sleep(CHECK_INTERVAL)
            elapsed += CHECK_INTERVAL

            try:
                status_response = requests.get(
                    f"{NODEJS_SERVER}/api/traverse/stats",
                    timeout=10
                )
                status_response.raise_for_status()
                stats = status_response.json()

                is_active = stats.get('active', False)
                processed = stats.get('processedFolders', 0)
                total = stats.get('totalFolders', 0)
                errors = stats.get('errors', 0)
                inserted = stats.get('insertedRecords', 0)

                # Check if manually stopped
                if stats.get('manuallyStopped', False):
                    print("⚠️ Traversal was manually stopped")
                    results["traversal"]["manually_stopped"] = True
                    results["status"] = "stopped"
                    return results

                # Log progress
                if processed != last_processed:
                    print(f"📊 Progress: {processed}/{total} folders, {inserted} records inserted, {errors} errors")
                    last_processed = processed

                if not is_active:
                    # Traversal completed!
                    results["traversal"]["completed_at"] = dt.now().isoformat()
                    results["traversal"]["stats"] = stats
                    results["traversal"]["duration_seconds"] = elapsed
                    print(f"✅ Traversal completed! Processed {processed} folders, inserted {inserted} records")
                    break

            except Exception as e:
                print(f"⚠️ Error checking status: {e}")

        else:
            # Timeout reached
            results["error"] = f"Traversal did not complete within {MAX_WAIT_TIME} seconds"
            results["status"] = "timeout"
            return results

    except Exception as e:
        # Traversal failed
        print(f"❌ Traversal failed: {e}")
        results["traversal"]["error"] = str(e)
        results["status"] = "traversal_failed"
        return results

    # Step 3: Run the Python import
    print("\n🔄 Starting historical data import...")
    results["import"]["started_at"] = dt.now().isoformat()

    try:
        # Import and run the function directly
        from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import \
            process_opcua_node_ids

        start_time = "2013-01-01T00:00:00"
        end_time = dt.now().isoformat()

        # Run the import
        process_opcua_node_ids(start_time, end_time)

        results["import"]["completed_at"] = dt.now().isoformat()
        results["import"]["status"] = "success"
        results["status"] = "completed"
        print("✅ Historical data import completed successfully")

    except Exception as e:
        results["import"]["error"] = str(e)
        results["import"]["status"] = "failed"
        results["status"] = "import_failed"
        print(f"❌ Import failed: {e}")

    results["completed_at"] = dt.now().isoformat()

    # Log final summary
    duration = (dt.fromisoformat(results["completed_at"]) -
                dt.fromisoformat(results["start_time"])).total_seconds()
    print(f"\n{'=' * 60}")
    print(f"Pipeline completed in {duration:.1f} seconds")
    print(f"Status: {results['status']}")
    print(f"{'=' * 60}")

    return results


@shared_task(name='plotly_integration.run_import_only')
def run_import_only():
    """
    Run only the Python import script.
    Use this when you already have traversal data and just want to import unprocessed records.
    """
    try:
        print("🚀 Starting OPC UA historical data import...")
        from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import \
            process_opcua_node_ids
        from plotly_integration.models import AktaNodeIds

        # Check how many need import
        unimported_count = AktaNodeIds.objects.filter(imported=False).count()
        print(f"📊 Found {unimported_count} unimported records")

        if unimported_count == 0:
            return {
                "status": "success",
                "message": "No unimported records found",
                "timestamp": dt.now().isoformat()
            }

        start_time = "2013-01-01T00:00:00"
        end_time = dt.now().isoformat()

        # Run the import
        process_opcua_node_ids(start_time, end_time)

        # Check results
        still_unimported = AktaNodeIds.objects.filter(imported=False).count()
        imported_count = unimported_count - still_unimported

        return {
            "status": "success",
            "message": f"Imported {imported_count} records successfully",
            "processed": imported_count,
            "remaining": still_unimported,
            "timestamp": dt.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            "status": "error",
            "error": str(e),
            "timestamp": dt.now().isoformat()
        }


@shared_task(name='plotly_integration.run_traversal_only')
def run_traversal_only():
    """
    Run only the traversal part.
    Use this to discover new OPC UA nodes without importing historical data.
    """
    try:
        print("🚀 Starting OPC UA traversal...")

        response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/start-optimized",
            timeout=30
        )
        response.raise_for_status()

        if response.json().get('success'):
            print("✅ Traversal started successfully")
            return {
                "status": "started",
                "response": response.json(),
                "timestamp": dt.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "error": "Failed to start traversal",
                "response": response.json(),
                "timestamp": dt.now().isoformat()
            }

    except Exception as e:
        print(f"❌ Failed to start traversal: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": dt.now().isoformat()
        }


@shared_task(name='plotly_integration.check_traversal_status')
def check_traversal_status():
    """Check current traversal status"""
    try:
        response = requests.get(
            f"{NODEJS_SERVER}/api/traverse/stats",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "timestamp": dt.now().isoformat()}


@shared_task(name='plotly_integration.stop_traversal')
def stop_traversal():
    """Stop the currently running traversal"""
    try:
        response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/stop",
            timeout=10
        )
        response.raise_for_status()
        print("🛑 Traversal stop requested")
        return {"status": "stopped", "timestamp": dt.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "timestamp": dt.now().isoformat()}


@shared_task(name='plotly_integration.check_import_status')
def check_import_status():
    """
    Check how many records need import.
    Useful for monitoring and deciding when to run imports.
    """
    from plotly_integration.models import AktaNodeIds, AktaResult

    total_nodes = AktaNodeIds.objects.count()
    imported_nodes = AktaNodeIds.objects.filter(imported=True).count()
    unimported_nodes = AktaNodeIds.objects.filter(imported=False).count()
    total_results = AktaResult.objects.count()

    percentage = round((imported_nodes / total_nodes * 100), 2) if total_nodes > 0 else 0

    status_msg = f"📊 Import Status: {imported_nodes}/{total_nodes} imported ({percentage}%)"
    if unimported_nodes > 0:
        status_msg += f" - {unimported_nodes} remaining"

    print(status_msg)

    return {
        "total_nodes": total_nodes,
        "imported": imported_nodes,
        "unimported": unimported_nodes,
        "percentage": percentage,
        "total_results": total_results,
        "status_message": status_msg,
        "timestamp": dt.now().isoformat()
    }


@shared_task(name='plotly_integration.cleanup_old_results')
def cleanup_old_results(days_to_keep=30):
    """
    Optional task to clean up old task results from django_celery_results.
    Schedule this weekly to keep the database clean.
    """
    try:
        from django_celery_results.models import TaskResult

        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Count before deletion
        old_results = TaskResult.objects.filter(date_created__lt=cutoff_date)
        count = old_results.count()

        # Delete old results
        old_results.delete()

        print(f"🧹 Cleaned up {count} task results older than {days_to_keep} days")

        return {
            "status": "success",
            "deleted_count": count,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": dt.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": dt.now().isoformat()
        }


@shared_task(name='plotly_integration.health_check')
def health_check():
    """
    Simple health check task to verify Celery is working.
    Can be scheduled every hour to ensure the system is running.
    """
    return {
        "status": "healthy",
        "timestamp": dt.now().isoformat(),
        "message": "Celery worker is running"
    }


# ========== EMPOWER HELPER FUNCTIONS ==========
def load_empower_processed_files():
    """Load list of already processed Empower files"""
    if os.path.exists(EMPOWER_PROCESSED_FILES_LOG):
        with open(EMPOWER_PROCESSED_FILES_LOG, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_empower_processed_file(filename):
    """Add a file to the processed list"""
    with open(EMPOWER_PROCESSED_FILES_LOG, 'a') as f:
        f.write(f"{filename}\n")


# ========== EMPOWER TASKS ==========
@shared_task(bind=True)
def check_and_import_empower_files(self):
    """
    Celery task that checks for new Empower files and imports them.
    """
    import plotly_integration.process_development.downstream_processing.empower.database.process_ars as process_ars
    import plotly_integration.process_development.downstream_processing.empower.database.process_arw as process_arw
    from plotly_integration.process_development.downstream_processing.empower.database.column_logbook import (
        populate_column_logbook,
        transfer_column_names,
        update_total_injections,
        assign_column_ids_to_samples,
        update_most_recent_injections,
        backfill_missing_pressure_data
    )

    lock_id = 'empower_import_lock'
    acquire_lock = lambda: cache.add(lock_id, 'locked', 300)
    release_lock = lambda: cache.delete(lock_id)

    if not acquire_lock():
        logger.info("Empower import task already running, skipping...")
        return "Task already running"

    try:
        if not os.path.isdir(EMPOWER_IMPORT_FOLDER):
            logger.error(f"Import folder not accessible: {EMPOWER_IMPORT_FOLDER}")
            return "Import folder not accessible"

        processed_files = load_empower_processed_files()

        all_files = os.listdir(EMPOWER_IMPORT_FOLDER)
        ars_files = [f for f in all_files if f.endswith('.ars') and f not in processed_files]
        arw_files = [f for f in all_files if f.endswith('.arw') and f not in processed_files]

        total_files = len(ars_files) + len(arw_files)

        if total_files == 0:
            logger.info("No new Empower files to process")
            return "No new files to process"

        logger.info(f"Found {total_files} new Empower files to process")

        self.update_state(
            state='PROCESSING',
            meta={'current': 0, 'total': total_files, 'status': 'Starting import...'}
        )

        processed_count = 0
        errors = []

        # Process .ars files
        for idx, file in enumerate(ars_files):
            try:
                logger.info(f"Processing .ars file: {file}")
                self.update_state(
                    state='PROCESSING',
                    meta={
                        'current': processed_count,
                        'total': total_files,
                        'status': f'Processing {file}...'
                    }
                )

                process_ars.process_files(
                    directory=EMPOWER_IMPORT_FOLDER,
                    reported_folder=EMPOWER_REPORTED_FOLDER
                )

                save_empower_processed_file(file)
                processed_count += 1

            except Exception as e:
                error_msg = f"Error processing {file}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Process .arw files
        for idx, file in enumerate(arw_files):
            try:
                logger.info(f"Processing .arw file: {file}")
                self.update_state(
                    state='PROCESSING',
                    meta={
                        'current': processed_count,
                        'total': total_files,
                        'status': f'Processing {file}...'
                    }
                )

                process_arw.process_files(
                    directory=EMPOWER_IMPORT_FOLDER,
                    reported_folder=EMPOWER_REPORTED_FOLDER
                )

                save_empower_processed_file(file)
                processed_count += 1

            except Exception as e:
                error_msg = f"Error processing {file}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Run column processing if files were processed
        if processed_count > 0:
            logger.info("Running column processing functions...")
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': processed_count,
                    'total': total_files,
                    'status': 'Running column processing...'
                }
            )

            populate_column_logbook()
            transfer_column_names()
            update_total_injections()
            assign_column_ids_to_samples()
            update_most_recent_injections()
            backfill_missing_pressure_data()

        # Store results in cache
        cache.set('empower_last_import', {
            'timestamp': dt.now().isoformat(),
            'processed': processed_count,
            'total': total_files,
            'errors': errors
        }, 3600)

        result_msg = f"Processed {processed_count}/{total_files} Empower files"
        if errors:
            result_msg += f" with {len(errors)} errors"

        logger.info(result_msg)
        return result_msg

    finally:
        release_lock()


@shared_task
def get_empower_import_status():
    """Get current Empower import status"""
    status = {
        'import_folder': EMPOWER_IMPORT_FOLDER,
        'processed_folder': EMPOWER_REPORTED_FOLDER,
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
def load_vicell_import_tracking():
    """Load tracking data for ViCell imports"""
    if os.path.exists(VICELL_TRACKING_FILE):
        with open(VICELL_TRACKING_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_vicell_import_tracking(tracking_data):
    """Save tracking data for ViCell imports"""
    with open(VICELL_TRACKING_FILE, 'w') as f:
        json.dump(tracking_data, f, indent=2)


def get_file_hash(filepath, num_bytes=1024 * 1024):
    """Get hash of first MB of file to detect changes"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        hasher.update(f.read(num_bytes))
    return hasher.hexdigest()


def parse_sample_name(sample_name):
    """Parses the sample ID into structured components for ViCell"""
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


import os
import json
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime as dt
from celery import shared_task
from django.core.cache import cache
from django.db import IntegrityError, transaction
import logging

# Set up logging
logger = logging.getLogger(__name__)


# ========== TIMESTAMP-BASED VICELL IMPORT TASK ==========
@shared_task(bind=True)
def check_and_import_vicell_files(self):
    """
    Celery task that imports ViCell data using timestamp-based tracking.
    Only imports rows with timestamps newer than the last imported timestamp.
    """
    lock_id = 'vicell_import_lock'
    acquire_lock = lambda: cache.add(lock_id, 'locked', 300)
    release_lock = lambda: cache.delete(lock_id)

    if not acquire_lock():
        logger.info("ViCell import task already running")
        return "ViCell import task already running"

    try:
        # Verify folder exists
        if not os.path.isdir(VICELL_FOLDER):
            logger.error(f"ViCell folder not accessible: {VICELL_FOLDER}")
            return f"ViCell folder not accessible: {VICELL_FOLDER}"

        # Load timestamp tracking
        tracking_file = os.path.join(VICELL_FOLDER, '.vicell_timestamp_tracking.json')

        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                tracking = json.load(f)
        else:
            tracking = {}
            logger.info("No existing tracking file found. Starting fresh.")

        # Find all Excel/CSV files
        files = [f for f in os.listdir(VICELL_FOLDER)
                 if f.endswith(('.csv', '.xlsx', '.xls')) and not f.startswith('~')]

        if not files:
            logger.info("No ViCell files found to process")
            return "No ViCell files found to process"

        # Process statistics
        total_new_records = 0
        total_skipped = 0
        total_errors = 0
        processed_files = []

        # Required columns
        relevant_columns = [
            "Analysis date/time", "Sample ID", "Cell count", "Viable cells",
            "Total (x10^6) cells/mL", "Viable (x10^6) cells/mL", "Viability (%)",
            "Average diameter (µm)", "Average viable diameter (µm)",
            "Average circularity", "Average viable circularity"
        ]

        for filename in files:
            filepath = os.path.join(VICELL_FOLDER, filename)
            logger.info(f"Processing file: {filename}")

            try:
                # Read file based on type
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)

                logger.info(f"Read {len(df)} rows from {filename}")

                # Verify required columns exist
                missing_columns = [col for col in relevant_columns if col not in df.columns]
                if missing_columns:
                    error_msg = f"Missing required columns in {filename}: {missing_columns}"
                    logger.error(error_msg)
                    processed_files.append({
                        'file': filename,
                        'error': error_msg
                    })
                    continue

                # Convert datetime column
                df['Analysis date/time'] = pd.to_datetime(df['Analysis date/time'], errors='coerce')

                # Remove rows with invalid timestamps
                valid_df = df[df['Analysis date/time'].notna()].copy()
                invalid_count = len(df) - len(valid_df)

                if invalid_count > 0:
                    logger.warning(f"Skipped {invalid_count} rows with invalid timestamps in {filename}")

                if len(valid_df) == 0:
                    processed_files.append({
                        'file': filename,
                        'status': 'No valid timestamps found',
                        'invalid_rows': invalid_count
                    })
                    continue

                # Get last imported timestamp for this file
                file_tracking = tracking.get(filename, {})
                last_timestamp_str = file_tracking.get('last_timestamp')

                if last_timestamp_str:
                    last_timestamp = pd.to_datetime(last_timestamp_str)
                    # Only get rows newer than last timestamp
                    new_rows = valid_df[valid_df['Analysis date/time'] > last_timestamp]
                    logger.info(f"Found {len(new_rows)} new rows after {last_timestamp} in {filename}")
                else:
                    # First time processing this file
                    new_rows = valid_df
                    logger.info(f"First time processing {filename}, importing all {len(new_rows)} valid rows")

                if len(new_rows) == 0:
                    processed_files.append({
                        'file': filename,
                        'status': 'No new records',
                        'last_timestamp': last_timestamp_str
                    })
                    continue

                # Update task state
                self.update_state(
                    state='PROCESSING',
                    meta={
                        'current_file': filename,
                        'new_rows': len(new_rows),
                        'progress': f'{files.index(filename) + 1}/{len(files)}'
                    }
                )

                # Process new rows
                success_count = 0
                error_count = 0
                duplicate_count = 0
                max_timestamp = pd.to_datetime(last_timestamp_str) if last_timestamp_str else pd.Timestamp.min

                # Process in batches for better performance
                batch_size = 100
                records_to_create = []

                for idx, row in new_rows.iterrows():
                    try:
                        # Skip rows with missing sample ID
                        if pd.isna(row["Sample ID"]):
                            total_skipped += 1
                            continue

                        # Parse sample information
                        parsed = parse_sample_name(row["Sample ID"])
                        sample_type = assign_sample_type(row["Sample ID"])

                        # Create record object
                        record = ViCellData(
                            sample_id=row["Sample ID"],
                            date_time=row["Analysis date/time"],
                            cell_count=pd.to_numeric(row["Cell count"], errors='coerce'),
                            viable_cells=pd.to_numeric(row["Viable cells"], errors='coerce'),
                            total_cells_per_ml=pd.to_numeric(row["Total (x10^6) cells/mL"], errors='coerce'),
                            viable_cells_per_ml=pd.to_numeric(row["Viable (x10^6) cells/mL"], errors='coerce'),
                            viability=pd.to_numeric(row["Viability (%)"], errors='coerce'),
                            average_diameter=pd.to_numeric(row["Average diameter (µm)"], errors='coerce'),
                            average_viable_diameter=pd.to_numeric(row["Average viable diameter (µm)"], errors='coerce'),
                            average_circularity=pd.to_numeric(row["Average circularity"], errors='coerce'),
                            average_viable_circularity=pd.to_numeric(row["Average viable circularity"],
                                                                     errors='coerce'),
                            experiment=parsed["experiment"],
                            day=parsed["day"],
                            reactor_type=parsed["reactor_type"],
                            reactor_number=parsed["reactor_number"],
                            special=parsed["special"],
                            sample_type=sample_type
                        )

                        records_to_create.append(record)

                        # Update max timestamp
                        if row["Analysis date/time"] > max_timestamp:
                            max_timestamp = row["Analysis date/time"]

                        # Batch insert when we reach batch_size
                        if len(records_to_create) >= batch_size:
                            created_count = bulk_create_with_duplicates(records_to_create)
                            success_count += created_count
                            duplicate_count += len(records_to_create) - created_count
                            records_to_create = []

                    except Exception as e:
                        logger.error(f"Error processing row {idx} in {filename}: {str(e)}")
                        error_count += 1
                        total_errors += 1

                # Insert any remaining records
                if records_to_create:
                    created_count = bulk_create_with_duplicates(records_to_create)
                    success_count += created_count
                    duplicate_count += len(records_to_create) - created_count

                # Update tracking with latest timestamp
                tracking[filename] = {
                    'last_timestamp': max_timestamp.isoformat(),
                    'last_import': dt.now().isoformat(),
                    'total_rows_in_file': len(df),
                    'rows_imported': success_count,
                    'duplicates_found': duplicate_count,
                    'errors': error_count
                }

                total_new_records += success_count

                # Record file processing results
                processed_files.append({
                    'file': filename,
                    'new_rows_found': len(new_rows),
                    'successfully_imported': success_count,
                    'duplicates': duplicate_count,
                    'errors': error_count,
                    'latest_timestamp': max_timestamp.isoformat()
                })

                logger.info(
                    f"Completed {filename}: {success_count} imported, {duplicate_count} duplicates, {error_count} errors")

            except Exception as e:
                error_msg = f"Failed to process {filename}: {str(e)}"
                logger.error(error_msg)
                processed_files.append({
                    'file': filename,
                    'error': error_msg
                })

        # Save updated tracking
        with open(tracking_file, 'w') as f:
            json.dump(tracking, f, indent=2)

        # Store detailed results in cache
        cache.set('vicell_last_import', {
            'timestamp': dt.now().isoformat(),
            'total_new_records': total_new_records,
            'total_skipped': total_skipped,
            'total_errors': total_errors,
            'processed_files': processed_files
        }, 3600)  # Cache for 1 hour

        summary = (f"Import completed: {total_new_records} new records imported from {len(files)} files. "
                   f"Skipped {total_skipped} invalid rows, encountered {total_errors} errors.")

        logger.info(summary)
        return summary

    except Exception as e:
        error_msg = f"Fatal error in ViCell import: {str(e)}"
        logger.error(error_msg)
        return error_msg

    finally:
        release_lock()


def bulk_create_with_duplicates(records):
    """
    Bulk create records, handling duplicates gracefully.
    Returns the number of records actually created.
    """
    try:
        # Try bulk create with ignore_conflicts
        ViCellData.objects.bulk_create(records, ignore_conflicts=True)

        # Check how many were actually created
        # This is approximate - for exact count, would need to check each record
        return len(records)
    except Exception as e:
        logger.error(f"Bulk create failed, falling back to individual inserts: {str(e)}")

        # Fallback to individual inserts
        created = 0
        for record in records:
            try:
                record.save()
                created += 1
            except IntegrityError:
                # Duplicate - skip
                pass
            except Exception as e:
                logger.error(f"Failed to save record {record.sample_id}: {str(e)}")

        return created


# ========== UTILITY FUNCTIONS ==========
def get_vicell_import_status():
    """Get current import status and tracking information."""
    tracking_file = os.path.join(VICELL_FOLDER, '.vicell_timestamp_tracking.json')

    status = {
        'tracking_file_exists': os.path.exists(tracking_file),
        'last_import_results': cache.get('vicell_last_import'),
        'files_tracked': {}
    }

    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as f:
            tracking = json.load(f)

        for filename, info in tracking.items():
            status['files_tracked'][filename] = {
                'last_timestamp': info.get('last_timestamp'),
                'last_import': info.get('last_import'),
                'rows_imported': info.get('rows_imported', 0)
            }

    return status


def reset_vicell_import_tracking(filename=None):
    """
    Reset import tracking to re-import data.
    If filename is provided, only reset that file's tracking.
    Otherwise, reset all tracking.
    """
    tracking_file = os.path.join(VICELL_FOLDER, '.vicell_timestamp_tracking.json')

    if not os.path.exists(tracking_file):
        return "No tracking file exists"

    if filename:
        # Reset specific file
        with open(tracking_file, 'r') as f:
            tracking = json.load(f)

        if filename in tracking:
            del tracking[filename]
            with open(tracking_file, 'w') as f:
                json.dump(tracking, f, indent=2)
            return f"Reset tracking for {filename}"
        else:
            return f"No tracking found for {filename}"
    else:
        # Reset all tracking
        os.remove(tracking_file)
        return "All ViCell import tracking reset"


def get_vicell_file_preview(filename, num_rows=10):
    """Preview the latest rows from a ViCell file."""
    filepath = os.path.join(VICELL_FOLDER, filename)

    if not os.path.exists(filepath):
        return f"File not found: {filename}"

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        # Convert datetime
        df['Analysis date/time'] = pd.to_datetime(df['Analysis date/time'], errors='coerce')

        # Sort by timestamp and get latest rows
        df_sorted = df.sort_values('Analysis date/time', ascending=False)

        return df_sorted.head(num_rows).to_dict('records')

    except Exception as e:
        return f"Error reading file: {str(e)}"